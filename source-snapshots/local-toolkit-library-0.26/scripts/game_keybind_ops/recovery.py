"""Explicit local recovery of this module's dead cooperating lock; never a replay.

Does not remove integrity, permission, unknown-owner or live-writer blocks. The
original lock is archived byte-for-byte. AI has read-only inspection, no retire.
"""
from __future__ import annotations
import os,stat,uuid
from pathlib import Path
from .core import snapshot,sha
from .deps import require,contained,read_json,json_new,local_lock,no_links,object_hash


def pid_state(pid:int)->str:
    if type(pid) is not int or pid<=0:return 'UNKNOWN'
    if os.name=='nt':
        import ctypes
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        k.OpenProcess.argtypes=[ctypes.c_uint32,ctypes.c_int,ctypes.c_uint32];k.OpenProcess.restype=ctypes.c_void_p
        k.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_uint32];k.WaitForSingleObject.restype=ctypes.c_uint32
        k.CloseHandle.argtypes=[ctypes.c_void_p];k.CloseHandle.restype=ctypes.c_int
        h=k.OpenProcess(0x00100000,False,pid)
        if not h:return 'DEAD' if ctypes.get_last_error()==87 else 'UNKNOWN'
        try:r=k.WaitForSingleObject(h,0);return 'DEAD' if r==0 else 'ALIVE' if r==258 else 'UNKNOWN'
        finally:k.CloseHandle(h)
    try:os.kill(pid,0);return 'ALIVE'
    except ProcessLookupError:return 'DEAD'
    except OSError:return 'UNKNOWN'


def inspect_lock(service,pid_reader=pid_state,lock_kind='operations')->dict:
    require(lock_kind in {'operations','registration'},'LOCK_UNRECOGNIZED',"Only this module's known lock roles may be inspected.")
    name='.keybind-ops.lock' if lock_kind=='operations' else '.keybind-registration.lock'
    path=service.root/name
    if not path.exists():return {'status':'NO_LOCK','retirement_available':False}
    raw=snapshot(path);value=read_json(path)
    require(type(value) is dict and set(value)=={'pid','created_unix','kind'} and value['kind']=='cooperative-only',
            'LOCK_UNRECOGNIZED','Do not retire an unknown owner lock.')
    state=pid_reader(value['pid'])
    plans=[]
    for p in service._list(service.plans,1024):
        status=service.status(p.name)  # a corrupt/incomplete plan is not bypassed by retiring its lock
        current=service.reconcile(p.name)
        plans.append({'plan_id':p.name,'status':status['status'],'files':current['files']})
    safe=all(f['state'] in ('BEFORE','AFTER') for p in plans for f in p['files'])
    result={'status':'LOCK_PRESENT','lock_kind':lock_kind,'owner_pid':value['pid'],'owner_state':state,'lock_sha256':sha(raw),
            'plans':plans,'retirement_available':state=='DEAD' and safe,'automatic_replay':False,
            'notice':'Retirement archives only a verified dead lock. Interrupted plans cannot be replayed.'}
    result['inspection_sha256']=object_hash(result);return result


def retire_lock_local(service,expected_inspection:str,*,authorize,pid_reader=pid_state,lock_kind='operations')->dict:
    inspection=inspect_lock(service,pid_reader,lock_kind)
    require(inspection.get('inspection_sha256')==expected_inspection,'LOCK_CHANGED','Inspect the same dead-lock state again.')
    require(inspection['retirement_available'],'OWNER_UNKNOWN','Only a verified dead owner with known before/after files is eligible.')
    require(callable(authorize) and authorize(inspection) is True,'LOCAL_APPROVAL_REQUIRED','Local explicit dead-lock retirement approval is required.')
    with local_lock(service.root,'.keybind-recovery.lock'):
        current=inspect_lock(service,pid_reader,lock_kind)
        require(current==inspection,'LOCK_CHANGED','Owner/files changed while recovery was reviewed.')
        original=service.root/('.keybind-ops.lock' if lock_kind=='operations' else '.keybind-registration.lock');raw=snapshot(original)
        require(pid_reader(inspection['owner_pid'])=='DEAD','OWNER_UNKNOWN','Owner no longer verified dead.')
        folder=contained(service.root,'retired-locks/'+uuid.uuid4().hex);folder.mkdir(parents=True,exist_ok=False)
        receipt={'schema_version':1,'inspection':inspection,'action':'archive_dead_lock_only_no_plan_replay'}
        json_new(folder/'receipt.json',receipt)
        # Exclusive destination in a newly created directory; never overwrites an earlier lock.
        require(sha(snapshot(original))==inspection['lock_sha256'],'LOCK_CHANGED','Lock bytes changed.')
        os.rename(original,folder/'original-lock.json')
        require(snapshot(folder/'original-lock.json')==raw,'LOCK_CHANGED','Archived lock failed byte verification.')
        if os.name!='nt':
            for directory in (folder,service.root):
                fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY)
                try:os.fsync(fd)
                finally:os.close(fd)
    return {'status':'DEAD_LOCK_ARCHIVED','lock_sha256':inspection['lock_sha256'],
            'next_action':'Inspect the existing plan; prepare a NEW inverse transaction if appropriate. No replay.',
            'game_files_modified':False,'automatic_replay':False}
