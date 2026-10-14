"""Prepare/verify/apply/undo bounded binding transactions through existing safety.

The filesystem journal is a work receipt, not a project queue. Whole-file
replacement is per-file; a multi-file operation is recoverable, not globally
atomic. No silent retry, force overwrite, launch, cloud toggle or code execution.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time
from threading import Event
from typing import Callable
import uuid
from . import __version__
from .deps import (Error, require, no_links, contained, slug, object_hash,
                   read_json, json_new, Journal, inspect_journal, local_lock)
from .documents import Document, MAX_BYTES

MAX_TARGETS = 1024
MAX_PLANS = 1024
MAX_FILES = 16
MAX_TOTAL = 32 * 1024 * 1024
MAX_STORAGE = 256 * 1024 * 1024
MIN_FREE = 32 * 1024 * 1024
PROTECTED = {'MouseLeft','MouseRight','WheelUp','WheelDown','WheelLeft','WheelRight','MouseMove'}
MIDDLE = 'MouseMiddle'
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.+ -]{0,63}\Z')


def sha(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def same(a,b): return type(a) is type(b) and a==b

def snapshot(path: Path) -> bytes:
    path = no_links(path)
    a = path.stat()
    require(stat.S_ISREG(a.st_mode),'NOT_REGULAR','Target must be a regular file.')
    require(a.st_nlink == 1,'HARDLINK_BLOCKED','Hard-linked configs are not supported.')
    require(0 < a.st_size <= MAX_BYTES,'SIZE_LIMIT','Config must be nonempty and at most 8 MiB.')
    def identity(s): return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns
    def read():
        with path.open('rb') as f:
            x=os.fstat(f.fileno()); raw=f.read(MAX_BYTES+1);y=os.fstat(f.fileno())
        require(identity(x)==identity(y)==identity(a),'SOURCE_CHANGED','File identity changed during read.')
        return raw
    first, second = read(),read()
    b=no_links(path).stat()
    require(identity(a)==identity(b) and first==second and len(first)<=MAX_BYTES,
            'SOURCE_CHANGED','File changed during inspection. Inspect the same operation; no retry.')
    return first

def process_names() -> set[str]:
    """Read executable names only; no process stop or command-line capture."""
    if os.name=='nt':
        exe=Path(os.environ.get('SystemRoot',r'C:\Windows'))/'System32'/'tasklist.exe'
        r=subprocess.run([str(exe),'/fo','csv','/nh'],capture_output=True,timeout=10,check=False)
        require(r.returncode==0,'PROCESS_STATE_UNKNOWN','Process enumeration failed.')
        text=r.stdout.decode('utf-8',errors='replace')
        return {row[0].casefold() for row in csv.reader(io.StringIO(text)) if row}
    r=subprocess.run(['/bin/ps','-A','-o','comm='],capture_output=True,text=True,timeout=10,check=False)
    require(r.returncode==0,'PROCESS_STATE_UNKNOWN','Process enumeration failed.')
    return {Path(v.strip()).name.casefold() for v in r.stdout.splitlines() if v.strip()}

def replace_existing(path: Path, data: bytes) -> None:
    """One same-directory staged replace. Failures have unknown effects until readback."""
    path=no_links(path);s=path.stat()
    require(bool(s.st_mode & stat.S_IWUSR) and not getattr(s,'st_file_attributes',0)&1,
            'READ_ONLY','Read-only config will not have its attributes changed.')
    fd,name=tempfile.mkstemp(prefix='.gt-keybind-',suffix='.tmp',dir=path.parent)
    temp=Path(name)
    try:
        with os.fdopen(fd,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(temp,stat.S_IMODE(s.st_mode))
        require(snapshot(temp)==data,'STAGE_CORRUPT','Sibling staging file failed readback.')
        if os.name=='nt':
            import ctypes
            fn=ctypes.WinDLL('kernel32',use_last_error=True).ReplaceFileW
            fn.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_void_p]
            fn.restype=ctypes.c_int
            if not fn(str(path),str(temp),None,0,None,None):
                raise OSError(ctypes.get_last_error(),'ReplaceFileW failed; inspect current bytes before any recovery.')
        else:
            os.replace(temp,path)
            directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(directory)
            finally:os.close(directory)
    finally:
        # Delete only the exact sibling temporary file we created, never game data.
        if temp.exists(): temp.unlink()


def validate_spec(value: dict) -> dict:
    required={'schema_version','target_id','game_id','root','relative','adapter','fields',
              'inventory_complete','stopped_processes','evidence'}
    allowed=required|{'encoding','notes','allow_middle','live_tested','scope_id'}
    require(type(value) is dict and required<=set(value)<=allowed,'INVALID_SPEC','Missing or unexpected recipe fields.')
    require(value['schema_version']==1,'SCHEMA_UNSUPPORTED','Expected target schema 1.')
    slug(value['target_id']);slug(value['game_id'])
    from .adapter_registry import adapter_info
    info=adapter_info(value['adapter'])
    if 'scope_id' in value:slug(value['scope_id'])
    require(type(value['root']) is str and Path(value['root']).is_absolute(),'UNSAFE_PATH','A local operator must select an absolute root.')
    require(not value['root'].startswith(('\\\\','//')),'UNSAFE_PATH','Network/device namespace targets require separate filesystem acceptance.')
    p=contained(Path(value['root']),value['relative'])
    require(p.suffix.casefold() in info.extensions,'FILE_ROLE_UNSUPPORTED','The adapter does not support this file role; no saves/scripts/executables.')
    require(type(value['inventory_complete']) is bool,'INVALID_SPEC','Inventory completeness must be explicit.')
    require(type(value['evidence']) is str and 1<=len(value['evidence'])<=1000,'EVIDENCE_REQUIRED','Record the native-schema/action-mapping evidence.')
    require(type(value['stopped_processes']) is list and 0<len(value['stopped_processes'])<=32,
            'PROCESS_GUARD_REQUIRED','Declare the game and relevant launcher/cloud processes that must be stopped.')
    for p in value['stopped_processes']:
        require(type(p) is str and re.fullmatch(r'[A-Za-z0-9_. -]{1,100}',p),'INVALID_SPEC','Use executable basenames, not commands or paths.')
    fields=value['fields']
    require(type(fields) is list and 0<len(fields)<=512,'INVALID_SPEC','Declare 1–512 reviewed native binding fields.')
    ids=set();selectors=set()
    for f in fields:
        require(type(f) is dict and {'id','selector','keys','collision_group'}<=set(f)<=
                {'id','selector','keys','collision_group','locked','linked_group','fallback_key'},'INVALID_SPEC','Unknown or missing native field fields.')
        ident=slug(f['id']);require(ident not in ids,'INVALID_SPEC','Duplicate field ID.');ids.add(ident)
        require(type(f['selector']) is dict,'INVALID_SPEC','A precise selector is required.')
        sk=object_hash(f['selector']);require(sk not in selectors,'INVALID_SPEC','Duplicate scalar selector.');selectors.add(sk)
        require(type(f['keys']) is dict and 1<=len(f['keys'])<=256,'INVALID_SPEC','An explicit canonical-to-native key vocabulary is required.')
        seen=[]
        for k,v in f['keys'].items():
            require(type(k) is str and TOKEN.fullmatch(k),'INVALID_SPEC','Invalid canonical key name.')
            require(type(v) in (str,int) or value['adapter']=='ue-chord' and type(v) is dict,'INVALID_SPEC','Native keyboard codes must be explicit scalar codes or complete Unreal chord records.')
            if type(v) is dict:
                require(set(v)=={'key','shift','ctrl','alt','cmd'} and type(v['key']) is str and all(type(v[k]) is bool for k in ('shift','ctrl','alt','cmd')),'INVALID_SPEC','Invalid native chord record.')
            require(not any(same(v,s) for s in seen),'INVALID_SPEC','Ambiguous canonical aliases for one native code.');seen.append(v)
        require(type(f['collision_group']) is str and len(f['collision_group'])<=128,'INVALID_SPEC','A reviewed collision/context group is required.')
        require(type(f.get('locked',False)) is bool,'INVALID_SPEC','locked must be boolean.')
        require(type(f.get('linked_group','')) is str,'INVALID_SPEC','linked_group must be text.')
        if f['selector'].get('optional'):
            require(value['adapter']=='ini-sparse' and f.get('fallback_key') in f['keys'] and f.get('fallback_key')!='Inherit' and f['keys'].get('Inherit')=='__GT_INHERIT__','SPARSE_DEFAULT_REQUIRED','Sparse entries need explicit Inherit and a reviewed effective fallback.')
    return value


def native_key(field:dict,value):
    keys=[k for k,v in field['keys'].items() if same(v,value)]
    require(len(keys)==1,'NATIVE_KEY_UNKNOWN','A binding value is outside the reviewed key vocabulary; review the schema, do not infer it.')
    return keys[0]

def compile_changes(raw:bytes,spec:dict,changes:dict) -> tuple[bytes,list[dict]]:
    require(spec['inventory_complete'],'INVENTORY_INCOMPLETE','A complete binding/context inventory is required before staging replacements.')
    require(type(changes) is dict and 0<len(changes)<=512,'INVALID_CHANGE','Expected a bounded field-ID to canonical-key map.')
    doc=Document(raw,spec['adapter'],spec.get('encoding'))
    fields={f['id']:f for f in spec['fields']}
    require(set(changes)<=set(fields),'UNREVIEWED_FIELD','Changes may only use locally reviewed native binding fields.')
    before={i:native_key(f,doc.select(f['selector']).value) for i,f in fields.items()}
    after=dict(before);patch=[];diff=[]
    for ident,key in changes.items():
        f=fields[ident]
        require(type(key) is str and key in f['keys'],'KEY_UNSUPPORTED','The requested key is not in this native field vocabulary.')
        if key==before[ident]:continue
        require(not f.get('locked',False),'FIELD_PROTECTED','This binding/context is protected.')
        from .key_codec import key_parts
        require(not (key_parts(key)|key_parts(before[ident])|key_parts(f.get('fallback_key',''))).intersection(PROTECTED),'MOUSE_PROTECTED','Left/right mouse and scrolling are never reassigned.')
        require(MIDDLE not in (key_parts(key)|key_parts(before[ident])) or spec.get('allow_middle') is True,
                'MIDDLE_REVIEW_REQUIRED','Middle-click changes need explicit local recipe approval.')
        patch.append((f['selector'],f['keys'][key]));after[ident]=key
        diff.append({'field_id':ident,'from':before[ident],'to':key,'context':f['collision_group']})
    require(diff,'NO_CHANGES','This plan makes no native binding changes.')
    # Compare pair identities, not just counts: old conflicts are not mistaken for newly introduced ones.
    def conflicts(values):
        rows={}
        for i,k in values.items():
            if k=='Inherit':k=fields[i].get('fallback_key','Inherit')
            group=fields[i]['collision_group']
            if not group:continue
            rows.setdefault((group,k),[]).append(i)
        return {(a,b) for ids in rows.values() for n,a in enumerate(ids) for b in ids[n+1:]}
    require(not (conflicts(after)-conflicts(before)),'KEY_COLLISION','The target key is occupied in a reviewed overlapping context. Resolve the entire swap together.')
    groups={}
    for i,f in fields.items():
        if f.get('linked_group'):groups.setdefault(f['linked_group'],[]).append(i)
    for ids in groups.values():
        changed={i for i in ids if before[i]!=after[i]}
        if changed: require(changed==set(ids),'LINKED_ACTIONS','A native linked-action group must be changed together.')
    result=doc.render(patch)
    # Key-to-command formats need a document-wide duplicate-key audit, including unlisted entries.
    updated=Document(result,spec['adapter'],spec.get('encoding'))
    def key_duplicates(d):
        seen={};out=set()
        for c in d.cells:
            if c.writer in {'ini-key','token'}:
                tag=(c.group,str(c.value).casefold());seen[tag]=seen.get(tag,0)+1
        return {k:n for k,n in seen.items() if n>1}
    previous=key_duplicates(doc)
    require(all(n<=previous.get(k,1) for k,n in key_duplicates(updated).items()),
            'KEY_COLLISION','A native key collision was found outside the declared patch.')
    # A lossless re-key must keep scalar count; all non-selected bytes are retained by render.
    if spec['adapter']!='ini-sparse':
        require(len(updated.cells)==len(doc.cells),'STRUCTURE_CHANGED','Binding edit changed the parsed file structure.')
    # Re-select every reviewed field after generation; adapters cannot quietly redirect identity.
    for i,f in fields.items():
        require(native_key(f,updated.select(f['selector']).value)==after[i],'PATCH_VERIFY_FAILED','Regenerated binding did not match intended value.')
    return result,diff

class Service:
    """Inert constructor. The host supplies its SAME private data directory."""
    def __init__(self,data_dir:Path,process_reader:Callable[[],set[str]]|None=None,
                 replacer:Callable[[Path,bytes],None]|None=None):
        self.data_dir=no_links(data_dir);self.root=self.data_dir/'keybinds'
        self.targets=self.root/'targets';self.plans=self.root/'plans'
        self.process_reader=process_reader or process_names
        self.replacer=replacer or replace_existing

    def _list(self,root:Path,limit:int) -> list[Path]:
        if not root.exists():return []
        no_links(root);rows=[]
        for p in root.iterdir():
            require(len(rows)<limit,'RECORD_LIMIT','Archive reviewed private records through the host before adding more.')
            no_links(p);rows.append(p)
        return sorted(rows)

    def _budget(self,additional:int):
        total,count=0,0
        if self.root.exists():
            for base,ds,fs in os.walk(self.root,followlinks=False):
                for name in ds+fs:
                    p=no_links(Path(base)/name);count+=1
                    require(count<=8192,'RECORD_LIMIT','Private workspace inventory exceeds its bounded limit.')
                    if p.is_file():total+=p.stat().st_size
        require(total+additional<=MAX_STORAGE,'STORAGE_BUDGET','Backup quota would be exceeded. Existing backups are not deleted automatically.')
        parent=self.root
        while not parent.exists():parent=parent.parent
        require(shutil.disk_usage(parent).free>=additional+MIN_FREE,'DISK_SPACE','Insufficient free space for backups and recovery margin.')

    def register_local(self,spec:dict) -> dict:
        """Local operator only. Never exposed as an AI tool; registration is not installation."""
        spec=validate_spec(spec);path=contained(Path(spec['root']),spec['relative'])
        raw=snapshot(path);doc=Document(raw,spec['adapter'],spec.get('encoding'))
        for f in spec['fields']: native_key(f,doc.select(f['selector']).value)
        record={'spec':spec,'spec_sha256':object_hash(spec),'registered_sha256':sha(raw),'created_unix':time.time()}
        dest=contained(self.targets,spec['target_id']+'.json')
        if dest.exists():
            old=self.target(spec['target_id']);require(old['spec']==spec,'TARGET_CONFLICT','Existing target definition differs. Preserve it; use a new reviewed target ID.')
            return self.inspect_target(spec['target_id'])
        require(len(self._list(self.targets,MAX_TARGETS))<MAX_TARGETS,'RECORD_LIMIT','Target limit reached.')
        self._budget(len(json.dumps(record).encode('utf-8')))
        with local_lock(self.root,'.keybind-ops.lock'):json_new(dest,record)
        return self.inspect_target(spec['target_id'])

    def target(self,ident:str) -> dict:
        r=read_json(contained(self.targets,slug(ident)+'.json'))
        spec=validate_spec(r['spec'])
        require(spec['target_id']==ident and object_hash(spec)==r['spec_sha256'],'TARGET_CORRUPT','Target registry changed unexpectedly.')
        return r

    def inspect_target(self,ident:str) -> dict:
        r=self.target(ident);s=r['spec'];raw=snapshot(contained(Path(s['root']),s['relative']))
        d=Document(raw,s['adapter'],s.get('encoding'))
        return {'target_id':ident,'game_id':s['game_id'],'target_revision':r['spec_sha256'],
                'current_sha256':sha(raw),'adapter':s['adapter'],'inventory_complete':s['inventory_complete'],
                'bindings':[{'id':f['id'],'key':native_key(f,d.select(f['selector']).value),
                    'context':f['collision_group'],'locked':f.get('locked',False)} for f in s['fields']],
                'collision_coverage':'locally reviewed file and context groups; native cross-file overrides require separate recipe review',
                'gameplay_verified':False}

    def context(self,known_revision:str|None=None,target_id:str|None=None) -> dict:
        rows=[]
        for p in self._list(self.targets,MAX_TARGETS):
            if target_id is not None and p.stem!=slug(target_id):continue
            try:rows.append(self.inspect_target(p.stem))
            except (Error,OSError) as e:rows.append({'target_id':p.stem,'status':getattr(e,'code','READ_FAILED')})
        summary={'targets':rows,'history':self.history()};revision=object_hash(summary)
        if len(json.dumps(summary).encode('utf-8'))>256*1024:
            summary['targets']=[{**{k:v for k,v in row.items() if k!='bindings'},'bindings_count':len(row.get('bindings',[]))} for row in rows]
            summary['detail_truncated']=True;summary['next_action']='Request context for one target_id.'
        return {'revision':revision,'unchanged':revision==known_revision,
                **({} if revision==known_revision else summary),'private_paths_included':False}

    def _build(self,items:list[dict]) -> tuple[list[dict],list[tuple[bytes,bytes]]]:
        require(type(items) is list and 0<len(items)<=MAX_FILES,'INVALID_CHANGE','Choose 1–16 distinct registered config targets.')
        rows=[];buffers=[];seen=set();paths=set();total=0
        for item in items:
            require(type(item) is dict and set(item)=={'target_id','target_revision','changes'},'INVALID_CHANGE','Expected target_id, target_revision and changes only.')
            ident=slug(item['target_id']);r=self.target(ident);s=r['spec']
            require(ident not in seen,'DUPLICATE_TARGET','One target per transaction.');seen.add(ident)
            require(item['target_revision']==r['spec_sha256'],'TARGET_CHANGED','The native recipe changed; reload the target.')
            path=contained(Path(s['root']),s['relative']);key=str(path).casefold()
            require(key not in paths,'DUPLICATE_TARGET','Two target IDs refer to the same file.');paths.add(key)
            before=snapshot(path);after,diff=compile_changes(before,s,item['changes'])
            total+=len(before)+len(after);require(total<=MAX_TOTAL,'SIZE_LIMIT','Transaction exceeds the 32 MiB staging limit.')
            rows.append({'target_id':ident,'game_id':s['game_id'],'target_revision':r['spec_sha256'],
                         'before_sha256':sha(before),'after_sha256':sha(after),'bytes_before':len(before),
                         'bytes_after':len(after),'changes':item['changes'],'diff':diff})
            buffers.append((before,after))
        from .effective import enrich_rows
        enrich_rows(self,rows,buffers)
        return rows,buffers

    def preview(self,items:list[dict]) -> dict:
        rows,_=self._build(items)
        body={'schema_version':1,'items':rows,'gameplay_verified':False}
        return {**body,'preview_sha256':object_hash(body),'status':'PREVIEW_NOT_INSTALLED'}

    def prepare(self,items:list[dict],expected_preview_hash:str,*,plan_id:str|None=None,parent_plan:str|None=None) -> dict:
        rows,buffers=self._build(items)
        body={'schema_version':1,'items':rows,'gameplay_verified':False}
        require(object_hash(body)==expected_preview_hash,'PREVIEW_STALE','Originals or recipe differ from the reviewed preview; nothing was installed.')
        return self._stage(rows,buffers,expected_preview_hash,plan_id=plan_id,parent_plan=parent_plan)

    def _stage(self,rows,buffers,expected_preview_hash,*,plan_id=None,parent_plan=None,operation='apply_bindings'):
        ident=slug(plan_id or uuid.uuid4().hex);directory=contained(self.plans,ident)
        with local_lock(self.root,'.keybind-ops.lock'):
            if directory.exists():
                p=self.plan(ident);require(p['items']==rows and p['parent_plan']==parent_plan and p['operation']==operation,'PLAN_ID_CONFLICT','This plan ID already belongs to different bytes or intent.')
                return self.status(ident)
            require(len(self._list(self.plans,MAX_PLANS))<MAX_PLANS,'RECORD_LIMIT','Plan limit reached.')
            self._budget(sum(len(a)+len(b) for a,b in buffers)+65536)
            directory.mkdir(parents=True,exist_ok=False)
            for n,(a,b) in enumerate(buffers):
                for kind,data in (('before',a),('after',b)):
                    path=directory/f'{n:02d}-{kind}.bin'
                    with path.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
                    require(snapshot(path)==data,'BACKUP_CORRUPT','Staged backup failed byte readback.')
            plan={'schema_version':1,'version':__version__,'plan_id':ident,'parent_plan':parent_plan,
                  'operation':operation,'created_unix':time.time(),'preview_sha256':expected_preview_hash,'items':rows}
            plan['plan_sha256']=object_hash(plan);json_new(directory/'plan.json',plan)
        return self.status(ident)

    def plan(self,ident:str) -> dict:
        p=read_json(contained(self.plans,slug(ident)+'/plan.json'))
        require(p['plan_id']==ident and p['plan_sha256']==object_hash({k:v for k,v in p.items() if k!='plan_sha256'}),
                'PLAN_CORRUPT','Plan hash/identity does not match. Stop affected effects.')
        require(0<len(p['items'])<=MAX_FILES,'PLAN_CORRUPT','Invalid plan item count.')
        return p

    def status(self,ident:str) -> dict:
        p=self.plan(ident);directory=contained(self.plans,ident);state='STAGED_NOT_INSTALLED';result=None
        journal=directory/'apply.jsonl'
        if journal.exists():
            audit=inspect_journal(journal)
            require(audit['valid'],'JOURNAL_CORRUPT','Journal integrity failed. No replay or writes are allowed.')
            records=audit['verified_records']
            require(records and records[0]['kind']=='journal_created' and records[0]['data']==
                    {'owner':'GameToolsKeybinds','plan_id':ident,'plan_sha256':p['plan_sha256']},
                    'JOURNAL_CORRUPT','Journal belongs to another operation. Stop affected effects.')
            end=[r for r in audit['verified_records'] if r['kind']=='keybind_result']
            if audit['clean_end'] and end:
                require(len(end)==1,'JOURNAL_CORRUPT','Multiple terminal results are ambiguous.')
                state=end[0]['data']['status']
                require(state in {'APPLIED_FILES_RUNTIME_UNVERIFIED','STOPPED_RECONCILE'},'JOURNAL_CORRUPT','Unknown terminal result.')
                if state=='APPLIED_FILES_RUNTIME_UNVERIFIED':
                    verified=[x['data'] for x in records if x['kind']=='keybind_file_verified']
                    expected=[{'index':n,'target_id':i['target_id']} for n,i in enumerate(p['items'])]
                    require(verified==expected and end[0]['data']['verified_files']==len(expected),
                            'JOURNAL_CORRUPT','Success receipt lacks complete per-file verification.')
            else:state='INTERRUPTED_RECONCILE'
        return {'plan_id':ident,'plan_sha256':p['plan_sha256'],'parent_plan':p['parent_plan'],
                'status':state,'items':p['items'],'gameplay_verified':False,'automatic_replay':False}

    def history(self) -> list[dict]:
        result=[]
        for path in self._list(self.plans,MAX_PLANS):
            try:
                p=self.status(path.name);result.append({k:v for k,v in p.items() if k!='items'})
            except (Error,OSError,KeyError,ValueError):result.append({'plan_id':path.name,'status':'INCOMPLETE_OR_CORRUPT_RECONCILE'})
        return result

    def reconcile(self,ident:str) -> dict:
        p=self.plan(ident);states=[]
        for n,item in enumerate(p['items']):
            # Backup corruption is an integrity failure, not a candidate for repair/retry.
            for kind in ('before','after'):
                require(sha(snapshot(contained(self.plans,f'{ident}/{n:02d}-{kind}.bin')))==item[kind+'_sha256'],
                        'BACKUP_CORRUPT','Stored recovery bytes changed; affected writes are stopped.')
            r=self.target(item['target_id']);s=r['spec']
            require(r['spec_sha256']==item['target_revision'],'TARGET_CHANGED','Recovery target definition differs from the plan.')
            try:
                current=sha(snapshot(contained(Path(s['root']),s['relative'])))
                state='BEFORE' if current==item['before_sha256'] else 'AFTER' if current==item['after_sha256'] else 'DIVERGED'
            except FileNotFoundError:current=None;state='MISSING'
            states.append({'target_id':item['target_id'],'state':state,'current_sha256':current})
        return {'plan_id':ident,'files':states,'action':'inspect_only_no_retry','gameplay_verified':False}

    def _preflight(self,p):
        from .effective import validate_guards
        validate_guards(self,p)
        running=self.process_reader()
        require(type(running) is set,'PROCESS_STATE_UNKNOWN','Host process guard returned an unknown result.')
        running={s.casefold() for s in running}
        for item in p['items']:
            r=self.target(item['target_id']);s=r['spec']
            require(r['spec_sha256']==item['target_revision'],'TARGET_CHANGED','Native recipe changed after staging.')
            require(not running.intersection(x.casefold() for x in s['stopped_processes']),
                    'PROCESS_RUNNING','A game/launcher/cloud process in this target policy is still running. No process is stopped automatically.')
            path=contained(Path(s['root']),s['relative']);current=snapshot(path)
            require(sha(current)==item['before_sha256'],'SOURCE_CHANGED','Live config differs from the staged baseline. Preview against its current version.')
            st=path.stat();require(bool(st.st_mode & stat.S_IWUSR) and not getattr(st,'st_file_attributes',0)&1,
                                  'READ_ONLY','Read-only config is not modified.')

    def apply_local(self,ident:str,expected_plan_hash:str,*,authorize:Callable[[dict],bool],cancel:Event|None=None) -> dict:
        """Trusted visible operator/controller only; authorize is NEVER a JSON field."""
        p=self.plan(ident)
        require(p['plan_sha256']==expected_plan_hash,'PLAN_CHANGED','Review the exact plan hash.')
        require(callable(authorize) and authorize(self.status(ident)) is True,'LOCAL_APPROVAL_REQUIRED','This exact operation needs trusted local approval.')
        with local_lock(self.root,'.keybind-ops.lock'):
            state=self.status(ident)['status']
            if state=='APPLIED_FILES_RUNTIME_UNVERIFIED':
                r=self.reconcile(ident);require(all(x['state']=='AFTER' for x in r['files']),'SOURCE_CHANGED','Previously applied files have drifted. Do not reapply blindly.')
                return self.status(ident)  # exact repeat is a no-op, not a new backup/apply
            require(state=='STAGED_NOT_INSTALLED','RECONCILIATION_REQUIRED','An attempted operation is not replayable; inspect its existing journal and bytes.')
            self.reconcile(ident);self._preflight(p);self._budget(65536)
            directory=contained(self.plans,ident)
            with Journal.create(directory/'apply.jsonl',{'owner':'GameToolsKeybinds','plan_id':ident,'plan_sha256':expected_plan_hash}) as journal:
                completed=0
                try:
                    for n,item in enumerate(p['items']):
                        require(not cancel or not cancel.is_set(),'CANCELLED','Stopped at a safe file boundary; partial history is retained.')
                        # Recheck all remaining source files and processes before each boundary.
                        self._preflight({'items':p['items'][n:],'all_items':p['items'],'completed':n})
                        spec=self.target(item['target_id'])['spec'];path=contained(Path(spec['root']),spec['relative'])
                        before=snapshot(directory/f'{n:02d}-before.bin');after=snapshot(directory/f'{n:02d}-after.bin')
                        if p.get('operation')=='restore_exact':
                            parent=self.plan(p['parent_plan'])
                            prior=next((i for i in parent['items'] if i['target_id']==item['target_id']),None)
                            require(prior is not None and item['after_sha256']==prior['before_sha256']
                                    and item['before_sha256']==prior['after_sha256'],'PLAN_CORRUPT','Invalid inverse transaction.')
                            index=parent['items'].index(prior)
                            regenerated=snapshot(contained(self.plans,f'{p["parent_plan"]}/{index:02d}-before.bin'))
                        else:
                            regenerated,_=compile_changes(before,spec,item['changes'])
                        require(sha(after)==item['after_sha256'] and regenerated==after,'BACKUP_CORRUPT','Staged candidate no longer matches the binding-only edit.')
                        journal.append('keybind_file_intent',{'index':n,'target_id':item['target_id'],
                                       'before_sha256':item['before_sha256'],'after_sha256':item['after_sha256']})
                        self.replacer(path,after)
                        require(sha(snapshot(path))==item['after_sha256'],'WRITE_VERIFY_FAILED','Replacement did not persist. Stop and reconcile.')
                        journal.append('keybind_file_verified',{'index':n,'target_id':item['target_id']});completed+=1
                    state='APPLIED_FILES_RUNTIME_UNVERIFIED'
                except (Exception,) as exc:
                    # Never automatically overwrite an ambiguous/third-party current version.
                    state='STOPPED_RECONCILE'
                    journal.append('keybind_failure',{'reason':getattr(exc,'code','UNKNOWN_EFFECTS'),'verified_files':completed})
                journal.append('keybind_result',{'status':state,'verified_files':completed})
                journal.append('session_closed',{'reason':'operation_returned_no_replay'})
            return self.status(ident)

    def rollback_preview(self,ident:str,*,selective:bool=False) -> dict:
        p=self.plan(ident);status=self.status(ident)['status']
        require(status!='STAGED_NOT_INSTALLED','NOT_APPLIED','A staged plan has not been installed.')
        r=self.reconcile(ident);items=[]
        for entry,observed in zip(p['items'],r['files']):
            if observed['state']=='BEFORE':continue
            require(observed['state']=='AFTER' or selective and observed['state']=='DIVERGED','ROLLBACK_CONFLICT',
                    'Current bytes are not the applied version. A separately reviewed selective undo may preserve later unrelated work.')
            s=self.target(entry['target_id'])['spec'];current=snapshot(contained(Path(s['root']),s['relative']))
            d=Document(current,s['adapter'],s.get('encoding'));fields={f['id']:f for f in s['fields']}
            undo={}
            for delta in entry['diff']:
                identf=delta['field_id'];f=fields[identf]
                require(native_key(f,d.select(f['selector']).value)==delta['to'],'ROLLBACK_CONFLICT',
                        'A changed binding was edited again; refusing to erase later work.')
                undo[identf]=delta['from']
            items.append({'target_id':entry['target_id'],'target_revision':entry['target_revision'],'changes':undo})
        require(items,'NOTHING_TO_ROLLBACK','All current files already match their originals.')
        result=self.preview(items);return {**result,'rollback_of':ident,'rollback_items':items,'mode':'selective' if selective else 'exact-compatible'}

    def exact_rollback_preview(self,ident:str) -> dict:
        p=self.plan(ident)
        require(self.status(ident)['status']!='STAGED_NOT_INSTALLED','NOT_APPLIED','The plan was never installed.')
        current=self.reconcile(ident);rows=[];buffers=[]
        for n,(item,state) in enumerate(zip(p['items'],current['files'])):
            if state['state']=='BEFORE':continue
            require(state['state']=='AFTER','ROLLBACK_CONFLICT','Exact undo refuses later changes. Inspect selective undo instead.')
            a=snapshot(contained(self.plans,f'{ident}/{n:02d}-after.bin'))
            b=snapshot(contained(self.plans,f'{ident}/{n:02d}-before.bin'))
            inverse={**item,'before_sha256':sha(a),'after_sha256':sha(b),'bytes_before':len(a),'bytes_after':len(b),
                     'changes':{d['field_id']:d['from'] for d in item['diff']},
                     'diff':[{**d,'from':d['to'],'to':d['from']} for d in item['diff']]}
            rows.append(inverse);buffers.append((a,b))
        require(rows,'NOTHING_TO_ROLLBACK','Files already match their originals.')
        from .effective import enrich_rows
        enrich_rows(self,rows,buffers)
        body={'schema_version':1,'items':rows,'gameplay_verified':False,'rollback_of':ident,'mode':'exact'}
        return {**body,'preview_sha256':object_hash(body),'status':'PREVIEW_NOT_INSTALLED'}

    def prepare_rollback(self,ident:str,expected_preview_hash:str,*,selective:bool=False,plan_id:str|None=None) -> dict:
        if selective:
            preview=self.rollback_preview(ident,selective=True)
            require(preview['preview_sha256']==expected_preview_hash,'PREVIEW_STALE','Undo preview changed.')
            return self.prepare(preview['rollback_items'],expected_preview_hash,plan_id=plan_id,parent_plan=ident)
        preview=self.exact_rollback_preview(ident)
        require(preview['preview_sha256']==expected_preview_hash,'PREVIEW_STALE','Undo preview changed.')
        original=self.plan(ident);buffers=[]
        for item in preview['items']:
            n=next(n for n,i in enumerate(original['items']) if i['target_id']==item['target_id'])
            buffers.append((snapshot(contained(self.plans,f'{ident}/{n:02d}-after.bin')),
                            snapshot(contained(self.plans,f'{ident}/{n:02d}-before.bin'))))
        return self._stage(preview['items'],buffers,expected_preview_hash,plan_id=plan_id,parent_plan=ident,operation='restore_exact')

    def replacement_preview_local(self,target_id:str,replacement:Path) -> dict:
        """Validate a supplied full file against original allowed deltas; no wholesale unreviewed replace."""
        r=self.target(target_id);s=r['spec'];a=snapshot(contained(Path(s['root']),s['relative']));b=snapshot(replacement)
        da,db=Document(a,s['adapter'],s.get('encoding')),Document(b,s['adapter'],s.get('encoding'))
        changes={}
        for f in s['fields']:
            old,new=da.select(f['selector']).value,db.select(f['selector']).value
            if not same(old,new):changes[f['id']]=native_key(f,new)
        require(changes,'NO_CHANGES','No allowed binding edits were found.')
        compiled,_=compile_changes(a,s,changes)
        require(compiled==b,'UNRELATED_CHANGE','Replacement changes unreviewed bytes/formatting or settings. Use a binding patch generated from the current original.')
        items=[{'target_id':target_id,'target_revision':r['spec_sha256'],'changes':changes}]
        return {**self.preview(items),'items_request':items}
