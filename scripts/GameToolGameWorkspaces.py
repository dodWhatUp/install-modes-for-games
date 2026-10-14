"""Game-scoped coordination over the existing mod jobs and approval service.

No new installer, cloud client, automatic scan, or general-purpose executor.
The public AI router can read or propose only; approval is a local UI method.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import queue
import tempfile
import threading
import time
import uuid
from typing import Callable
from GameToolAutomation import AutomationService, RECIPE, capabilities, SHA
from GameToolOverlay import Store
from game_mod_ops.recipes import load_recipe, validate_recipe, plan
from game_mod_ops.safety import (ModError, require, no_links, contained, regular,
    read_json, json_new, write_new, copy_new, digest, object_hash, slug, local_lock)
from game_mod_ops.workflow import Job, acquire, import_archive, stage
from game_mod_ops.network import Budget
from game_mod_ops.umm import inventory
from game_mod_ops.support import SupportRegistry, read_pack, describe, scaffold, schema as support_schema
from game_mod_ops.definitions import validate_mode
from game_mod_ops.managers import inspect_game as inspect_defined_game, compare_installed, capabilities as adapter_capabilities
from game_mod_ops.handoff import export_handoff
from GameToolKeybindIntegration import KeybindAutomationMixin, OPERATIONS as KEYBIND_OPERATIONS
from GameToolInstances import InstanceRegistry
from game_keybind_ops.core import Service as KeybindService
from game_keybind_ops.packs import list_packs as list_keybind_packs
from game_keybind_ops.effective import list_instances as list_keybind_instances
from game_keybind_ops.deps import Error as KeybindError

VERSION = "0.2.1"
BASE = Path(__file__).resolve().parents[1]
MAX_GAMES = 64
MAX_JOBS = 128
MANUAL_CHECKS = {
    'manager_lists_mod': 'Manager lists the expected mod and version',
    'game_starts': 'Game starts with the selected mod set',
    'feature_works': 'The requested feature works in the game',
}
GOOD_FILES = {'ACQUIRED', 'STAGED_NOT_INSTALLED', 'FILES_INSTALLED_RUNTIME_UNVERIFIED'}
WAITING = {'PLANNED', 'WAITING_NEXUS_AUTH', 'WAITING_USER_DOWNLOAD',
           'WAITING_MANUAL_DOWNLOAD', 'FILE_PIN_REQUIRED'}
STATE_LABELS = {'PLANNED':'Not downloaded', 'ACQUIRED':'Downloaded',
    'STAGED_NOT_INSTALLED':'Prepared', 'FILES_INSTALLED_RUNTIME_UNVERIFIED':'Files copied; untested',
    'WAITING_NEXUS_AUTH':'Sign-in needed', 'WAITING_MANUAL_DOWNLOAD':'Manual download needed',
    'WAITING_USER_DOWNLOAD':'Website action needed', 'FILE_PIN_REQUIRED':'Choose exact version',
    'DOWNLOADING':'Transfer in progress', 'STAGING':'Preparing files',
    'AWAITING_LOCAL_APPROVAL':'Needs your approval', 'COMPLETED':'Completed',
    'REJECTED':'Rejected', 'EXPIRED':'Expired', 'RUNNING':'Running'}


def bounded_files(folder: Path, pattern: str, limit: int):
    if not folder.exists(): return []
    no_links(folder)
    result=[]
    for p in folder.glob(pattern):
        require(len(result) < limit, 'RECORD_LIMIT', 'Record limit reached; no records were silently omitted.')
        result.append(no_links(p))
    return sorted(result)


class RecipeCatalog:
    """Explicit local recipe registration; preserves originals, refuses implicit upgrades."""
    def __init__(self, data_dir: Path, builtin: Path = RECIPE):
        self.data_dir=no_links(data_dir)
        self.builtin=no_links(builtin)
        self.folder=self.data_dir/'mod-workflows'/'recipes'
        self.support=SupportRegistry(self.data_dir)
        self.use_shipped=self.builtin==no_links(RECIPE)

    def recipes(self):
        shipped=(bounded_files(self.builtin.parent,'*.json',MAX_GAMES) if self.use_shipped else [self.builtin])
        paths=shipped+bounded_files(self.folder, '*.json', MAX_GAMES)
        rows={}
        for path in paths:
            recipe=load_recipe(path); ident=recipe['game_id']; revision=object_hash(recipe)
            require(ident==ident.lower(),'INVALID_ID','Game IDs must be lowercase to avoid filesystem aliases.')
            if ident in rows:
                require(rows[ident]['revision']==revision, 'RECIPE_CONFLICT', 'Two different recipes own the same game; reconcile them first.')
                continue
            rows[ident]={'id':ident,'name':str(recipe.get('name',ident))[:160],
                'path':path, 'revision':revision, 'recipe':recipe,
                'kind':'builtin' if path==self.builtin else 'locally_registered'}
        for ident,row in self.support.rows().items():
            if row['pack']['recipe'] is None:continue
            if row['source']=='shipped' and not self.use_shipped:continue
            path=self.support.recipe_path(ident);recipe=load_recipe(path)
            rows[ident]={'id':ident,'name':row['pack']['definition']['name'],'path':path,
                'revision':object_hash(recipe),'recipe':recipe,'kind':'game_support_pack'}
        return rows

    def game_rows(self):
        rows={i:{'id':i,'name':v['name'],'recipe_available':True,'recipe_revision':v['revision'],
                 'manager':v['recipe']['manager_id'],'installation':'unknown','source':v['kind']}
              for i,v in self.recipes().items()}
        path=BASE/'examples/game-tool-hub/catalog.example.json'
        if path.exists():
            for game in read_json(path).get('games',[]):
                ident=slug(game['id'])
                rows.setdefault(ident,{'id':ident,'name':str(game.get('name',ident))[:160],
                    'recipe_available':False,'recipe_revision':None,'manager':None,
                    'installation':'unknown','source':'saved_catalog_not_live_inventory'})
        for ident,support in self.support.rows().items():
            if support['source']=='shipped' and not self.use_shipped:continue
            d=support['pack']['definition']
            rows.setdefault(ident,{'id':ident,'name':d['name'],'recipe_available':False,
                'recipe_revision':None,'manager':d['manager_id'],'installation':'unknown','source':support['source']})
            rows[ident]['manager']=d['manager_id']
            rows[ident]['support_revision']=support['revision']
            rows[ident]['adapter_capabilities']=adapter_capabilities(d)
            for op in ('plan','download','stage','import_archive','manager_handoff'):
                rows[ident]['adapter_capabilities'][op]=rows[ident]['recipe_available']
        return sorted(rows.values(),key=lambda r:(r['id']!='pathfinder-kingmaker',r['name'].casefold()))

    def get(self, game_id):
        ident=slug(game_id)
        rows=self.recipes()
        require(ident in rows,'RECIPE_REQUIRED','This game has no reviewed mod recipe. Import one before creating plans.')
        return rows[ident]

    def import_support(self,source,*,reviewed_sha256,expected_revision=None,expected_recipe_revision=None,confirmed=False):
        pack,_=read_pack(source);ident=pack['definition']['game_id']
        old=self.recipes().get(ident)
        require((old['revision'] if old else None)==expected_recipe_revision,
                'CONCURRENT_CHANGE','The existing recipe changed; review before replacing game support.')
        return self.support.import_pack(source,reviewed_sha256=reviewed_sha256,
                    expected_revision=expected_revision,confirmed=confirmed)

    def import_local(self, source: Path, *, confirmed: bool = False):
        require(confirmed,'REVIEW_REQUIRED','Review and confirm the recipe before registering it.')
        source=regular(source,512*1024); raw=source.read_bytes(); recipe=load_recipe(source)
        ident=recipe['game_id']; revision=object_hash(recipe)
        require(ident==ident.lower(),'INVALID_ID','Game IDs must be lowercase.')
        existing=self.recipes().get(ident)
        if existing:
            require(existing['revision']==revision,'RECIPE_CONFLICT','A different recipe already owns this game. It was not replaced.')
            return {'game_id':ident,'status':'ALREADY_REGISTERED','recipe_revision':revision}
        require(len(self.recipes())<MAX_GAMES,'RECORD_LIMIT','Too many registered recipes.')
        # Source metadata is not authority to run code; recipe validation is data-only.
        with local_lock(self.folder):
            target=contained(self.folder,ident+'.json')
            write_new(target,raw)
            require(object_hash(load_recipe(target))==revision,'SOURCE_CHANGED','Source changed during registration.')
        return {'game_id':ident,'status':'REGISTERED_NOT_INSTALLED','recipe_revision':revision}


class ScopedAutomation(AutomationService):
    """Same schema/approval checks; separate request namespaces, same canonical jobs."""
    def __init__(self,data_dir,recipe_path,builtin_id='pathfinder-kingmaker'):
        super().__init__(data_dir,recipe_path)
        self.game_id=self.recipe['game_id']
        if self.game_id!=builtin_id:
            self.root=self.data_dir/'automation'/'game-scopes'/slug(self.game_id)
            self.requests=self.root/'requests'
        # Reports/overlays still belong to existing global services. Not copied.

    def propose(self,operation,arguments,*,request_id=None):
        require(operation in {'mods.create_plan','mods.download','mods.stage'},'USE_ORIGINAL_WORKSPACE',
                'Use the existing overlay workspace for display actions.')
        return super().propose(operation,arguments,request_id=request_id)


class KeybindScopedAutomation(KeybindAutomationMixin, ScopedAutomation):
    """A reviewed mod recipe and keybind owner share one scoped mailbox."""
    pass


class KeybindOnlyAutomation(KeybindAutomationMixin, AutomationService):
    """Keybind-only scope using the host recipe solely for mailbox transport."""
    keybind_only=True
    def __init__(self,data_dir,game_id,bootstrap_recipe=RECIPE,**kwargs):
        super().__init__(data_dir,bootstrap_recipe,**kwargs)
        self.game_id=slug(game_id)
        self.root=self.data_dir/'automation'/'game-scopes'/self.game_id
        self.requests=self.root/'requests'
    def propose(self,operation,arguments,*,request_id=None):
        require(operation in KEYBIND_OPERATIONS,'CAPABILITY_UNAVAILABLE',
                'This scope has reviewed keybind data but no reviewed mod recipe.')
        return super().propose(operation,arguments,request_id=request_id)
    def preview_plan(self,*args,**kwargs):
        raise ModError('MOD_RECIPE_REQUIRED','No mod recipe is registered for this game. Keybinding operations remain available.')


def activity_outcome(result):
    if type(result) is not dict:return 'RETURNED_REVIEW_RESULT'
    if 'new_job' in result or result.get('status')=='PLANNED':return 'PLAN_SAVED'
    if result.get('evidence')=='filesystem_metadata_not_runtime':return 'FILES_INSPECTED'
    if result.get('status') in {'STOPPED_RECONCILE','UNKNOWN_EFFECTS_RECONCILE'}:return 'STOPPED_REVIEW'
    if result.get('status')=='RETURNED_WITH_PENDING_ITEMS':return 'NEEDS_INPUT'
    if 'items' in result:
        states={r['status'] for r in result['items']}
        if states-GOOD_FILES-WAITING:return 'STOPPED_REVIEW'
        if states & WAITING:return 'NEEDS_INPUT'
        return 'PREPARED' if 'STAGED_NOT_INSTALLED' in states else 'DOWNLOADED'
    if type(result.get('result')) is dict:return activity_outcome(result['result'])
    return 'RETURNED_REVIEW_RESULT'


class ActivityRunner:
    """Two independent game tasks; a single transfer slot; no automatic queue/retry.

    The callable is supplied by trusted UI code, never parsed from an AI request.
    Existing Job locks/journals still protect actual file operations.
    """
    def __init__(self):
        self._guard=threading.Lock(); self._running={}; self.events=queue.Queue()
        self.history=[]

    def active(self):
        with self._guard:
            return [{k:v for k,v in row.items() if k not in {'thread','cancel'}}
                    for row in self._running.values()]

    def can_start(self,game_id,network=False):
        with self._guard:
            if game_id in self._running: return False,'This game already has an active operation.'
            if len(self._running)>=2:return False,'Two operations are active. Review other games while they finish.'
            if network and any(r['network'] for r in self._running.values()):
                return False,'Another download owns the transfer slot. Local review/preparation remain available.'
        return True,''

    def start(self,game_id,label,fn:Callable,*,network=False,job_id=None,cancel=None):
        game_id=slug(game_id)
        with self._guard:
            require(game_id not in self._running,'GAME_BUSY','An operation already owns this game.')
            require(len(self._running)<2,'WORKER_LIMIT','Two operations are active.')
            require(not network or not any(r['network'] for r in self._running.values()),
                    'TRANSFER_BUSY','A download is already active. No transfer was queued or retried.')
            cancel=cancel or threading.Event()
            token=uuid.uuid4().hex
            record={'activity_id':token,'game_id':game_id,'job_id':job_id,'label':label,
                    'status':'RUNNING','network':network,'started':time.time(),'cancel':cancel}
            def work():
                try:
                    require(not cancel.is_set(),'CANCELLED','Cancelled before dispatch.')
                    result=fn(cancel); status=activity_outcome(result)
                except ModError as error:result=error.record();status='STOPPED_REVIEW'
                except Exception:result={'status':'UNKNOWN_EFFECTS','message':'Inspect the existing operation before trying again.'};status='STOPPED_REVIEW'
                with self._guard:
                    self._running.pop(game_id,None)
                    done={k:v for k,v in record.items() if k not in {'thread','cancel'}}
                    done.update(status=status,result=result,finished=time.time())
                    self.history.append(done);self.history=self.history[-64:]
                self.events.put(done)
            thread=threading.Thread(target=work,name='GameTools-'+game_id,daemon=False)
            record['thread']=thread;self._running[game_id]=record
            try:thread.start()
            except Exception:self._running.pop(game_id,None);raise
        return token

    def stop(self,game_id=None):
        with self._guard:
            for ident,row in self._running.items():
                if game_id is None or ident==game_id:row['cancel'].set();row['status']='STOP_REQUESTED'


class GameWorkspaces:
    def __init__(self,data_dir,builtin=RECIPE):
        self.data_dir=no_links(data_dir);self.catalog=RecipeCatalog(self.data_dir,builtin)
        self.mods_root=self.data_dir/'mod-workflows';self.runner=ActivityRunner();self._services={}
        self.builtin_id=load_recipe(builtin)['game_id']
        self.keybinds=KeybindService(self.data_dir)
        self.instances=InstanceRegistry(self.data_dir,self)

    def game_rows(self):
        """Compose support-pack and keybind-pack capabilities without merging schemas."""
        rows={r['id']:{**r,'keybind_pack_available':False,'keybind_pack_revision':None}
              for r in self.catalog.game_rows()}
        for pin in list_keybind_packs(self.keybinds):
            ident=pin.get('game_id')
            if not ident:continue
            row=rows.setdefault(ident,{'id':ident,'name':ident,'recipe_available':False,
                'recipe_revision':None,'manager':None,'installation':'unknown',
                'source':'locally_imported_keybind_data_pack','keybind_pack_available':False,
                'keybind_pack_revision':None})
            row['keybind_pack_available']=True
            row['keybind_pack_revision']=(pin.get('pin') or {}).get('sha256')
        return sorted(rows.values(),key=lambda r:(r['id']!='pathfinder-kingmaker',r['name'].casefold()))

    def _new_service(self,game_id,row,has_keybind):
        if row and has_keybind:
            return KeybindScopedAutomation(self.data_dir,row['path'],self.builtin_id,keybind_service=self.keybinds)
        if row:return ScopedAutomation(self.data_dir,row['path'],self.builtin_id)
        return KeybindOnlyAutomation(self.data_dir,game_id,self.catalog.builtin,keybind_service=self.keybinds)

    def service(self,game_id):
        game_id=slug(game_id);row=self.catalog.recipes().get(game_id)
        has_keybind=any(r['id']==game_id and r.get('keybind_pack_available') for r in self.game_rows())
        require(row is not None or has_keybind,'PACK_REQUIRED',
                'Import a reviewed mod recipe or keybind data pack before opening this game scope.')
        if game_id not in self._services:
            self._services[game_id]=self._new_service(game_id,row,has_keybind)
        service=self._services[game_id]
        require(bool(getattr(service,'keybind_only',False))==(row is None) and hasattr(service,'keybinds')==has_keybind,
                'SOURCE_CHANGED','Game capabilities changed. Reopen the workbench and reconcile pending requests.')
        # A recipe-only revision keeps the same capability shape. Refresh the scoped
        # service as A 0.24 did so new plans use the new immutable recipe while old
        # jobs and requests retain their recorded bytes. Adding/removing keybind or
        # mod capability still requires an explicit Workbench reopen above.
        if row and service.recipe_hash!=row['revision']:
            service=self._new_service(game_id,row,has_keybind);self._services[game_id]=service
        return service

    def jobs(self,game_id=None):
        rows=[]
        for path in bounded_files(self.mods_root/'jobs','*',MAX_JOBS):
            if not path.is_dir():continue
            try:
                j=Job(path)
                if game_id is not None and j.plan['game_id']!=game_id:continue
                rows.append({'job_id':path.name,'game_id':j.plan['game_id'],
                    'plan_sha256':j.plan['plan_sha256'],'revision':self.revision(j),
                    'mode':j.plan['mode'],'items':len(j.items),
                    'prepared':sum(j.latest(i)['status']=='STAGED_NOT_INSTALLED' for i in j.items),
                    'status':'AVAILABLE'})
            except (ModError,OSError,ValueError):
                if game_id is None:rows.append({'job_id':path.name,'game_id':None,'status':'INVALID_JOB_REVIEW'})
        return sorted(rows,key=lambda r:r['job_id'],reverse=True)

    @staticmethod
    def revision(job):return object_hash({'plan':job.plan,'events':job.events()})

    def job(self,game_id,job_id):
        j=Job(contained(self.mods_root,'jobs/'+slug(job_id)))
        require(j.plan['game_id']==game_id,'GAME_MISMATCH','This job belongs to another game. No action was performed.')
        return j

    def new_plan(self,game_id,selected=None,mode=None):
        # Check at dispatch as well as in UI. No network/installation.
        service=self.service(game_id)
        mode=mode or ('default' if 'default' in service.recipe.get('presets',{}) else 'real-time')
        p=service.preview_plan(selected,mode)
        return Job.create(self.mods_root,p)

    def item_rows(self,game_id,job_id):
        j=self.job(game_id,job_id);events=j.events();rows=[]
        for ident,item in j.items.items():
            last=next((e for e in reversed(events) if e['item_id']==ident),{'status':'PLANNED'})
            acquired=next((e for e in reversed(events) if e['item_id']==ident and e['status']=='ACQUIRED'),None)
            rows.append({'id':ident,'name':item['name'],'version':item.get('display_version','Unknown'),
                'kind':item['kind'],'state':last['status'],
                'label':STATE_LABELS.get(last['status'],'Needs review'),
                'integrity':acquired.get('integrity') if acquired else None,
                'archive_sha256':acquired.get('sha256') if acquired else None,
                'runtime':'Not verified','next':self.next_action(last['status'],item['kind'])})
        return rows

    @staticmethod
    def next_action(state,kind='mod'):
        if state in WAITING:return 'Import ZIP' if state!='PLANNED' else 'Download plan'
        if state=='ACQUIRED':return 'Prepare files' if kind=='mod' else 'Use official installer'
        if state=='STAGED_NOT_INSTALLED':return 'Install with manager'
        if state=='FILES_INSTALLED_RUNTIME_UNVERIFIED':return 'Check in game'
        return 'Review existing effects'

    def _writable_job(self,game_id,job_id,revision):
        j=self.job(game_id,job_id)
        require(self.revision(j)==revision,'CONCURRENT_CHANGE','The job changed since review. Refresh before acting.')
        return j

    def import_zip(self,game_id,job_id,revision,item_id,source,confirmed=False):
        j=self._writable_job(game_id,job_id,revision)
        return import_archive(j,item_id,Path(source),confirmed_source=confirmed)

    def prepare(self,game_id,job_id,revision,item_ids,cancel=None):
        j=self._writable_job(game_id,job_id,revision)
        require(type(item_ids) is list and 0<len(item_ids)<=16 and len(set(item_ids))==len(item_ids),
                'INVALID_ARGUMENTS','Select 1–16 different mod items.')
        for ident in item_ids:
            require(j.item(ident)['kind']=='mod','MANAGER_NOT_MOD','A mod manager is not a mod. Use its official installer.')
            j.reconcile_gate(ident);j.acquired(ident)
        for ident in item_ids:
            require(not cancel or not cancel.is_set(),'CANCELLED','Stopped between items; inspect completed preparations.')
            stage(j,ident)
        return j.summary()

    def download(self,game_id,job_id,revision,cancel=None):
        j=self._writable_job(game_id,job_id,revision)
        return acquire(j,allow_network=True,budget=Budget(),
                       nexus_key=os.environ.get('NEXUS_MODS_API_KEY'),cancel=cancel)

    def record_check(self,game_id,job_id,revision,item_id,check,outcome,note=''):
        j=self._writable_job(game_id,job_id,revision);j.item(item_id)
        require(check in MANUAL_CHECKS and outcome in {'passed','failed','not_tested'},
                'INVALID_CHECK','Use a known check and outcome.')
        require(type(note) is str and len(note)<=1000 and '\x00' not in note,'INVALID_NOTE','Note is too long or invalid.')
        with local_lock(j.path,'manual-review.lock'):
            require(self.revision(j)==revision,'CONCURRENT_CHANGE','Job changed while recording the check.')
            folder=j.path/'manual-checks'
            require(len(bounded_files(folder,'*.json',128))<128,'RECORD_LIMIT','Manual-check limit reached.')
            value={'schema_version':1,'game_id':game_id,'job_id':job_id,'job_revision':revision,
                'item_id':item_id,'check':check,'outcome':outcome,'note':note,
                'timestamp':time.time(),'evidence':'operator_reported_not_machine_verified'}
            value['sha256']=object_hash(value)
            json_new(folder/(uuid.uuid4().hex+'.json'),value)
        return value

    def checks(self,game_id,job_id,public=False):
        j=self.job(game_id,job_id);revision=self.revision(j);rows=[]
        for p in bounded_files(j.path/'manual-checks','*.json',128):
            value=read_json(p,8192)
            require(type(value) is dict and set(value)=={'schema_version','game_id','job_id','job_revision','item_id','check','outcome','note','timestamp','evidence','sha256'},
                    'INVALID_CHECK','Unexpected manual-check fields.')
            require(value['evidence']=='operator_reported_not_machine_verified' and value['schema_version']==1,
                    'INVALID_CHECK','Manual evidence cannot claim machine verification.')
            j.item(value['item_id'])
            require(value.get('sha256')==object_hash({k:v for k,v in value.items() if k!='sha256'}),
                    'EVIDENCE_CHANGED','A manual check was modified; it is not accepted.')
            require(value.get('game_id')==game_id and value.get('job_id')==job_id,
                    'GAME_MISMATCH','A manual record belongs to another scope.')
            require(value.get('check') in MANUAL_CHECKS and value.get('outcome') in {'passed','failed','not_tested'},
                    'INVALID_CHECK','Invalid manual evidence.')
            if public:value={k:v for k,v in value.items() if k!='note'}
            rows.append({**value,'stale':value['job_revision']!=revision})
        return sorted(rows,key=lambda r:r['timestamp'],reverse=True)

    def inspect_installed(self,game_id,job_id,revision,game_dir):
        j=self._writable_job(game_id,job_id,revision) if job_id else None
        definition=j.plan.get('game_definition') if j else None
        row=self.catalog.support.rows().get(game_id)
        if definition is None and row:definition=row['pack']['definition']
        if definition is not None:
            result=inspect_defined_game(Path(game_dir),definition)
        else:
            require(game_id=='pathfinder-kingmaker','ADAPTER_UNAVAILABLE','Import a support pack with a folder-inspection adapter.')
            result=inventory(Path(game_dir))
        record={'schema_version':1,'job_revision':revision,'observed_unix':time.time(),
            'game_id':game_id,'evidence':'filesystem_metadata_not_runtime','result':result}
        if j and definition:record['comparison']=compare_installed(j.plan,result)
        record['sha256']=object_hash(record)
        folder=(j.path/'installed-inspections') if j else self.mods_root/'support-inspections'/slug(game_id)
        require(len(bounded_files(folder,'*.json',32))<32,'RECORD_LIMIT','Inspection limit reached.')
        json_new(folder/(uuid.uuid4().hex+'.json'),record)
        return record

    def export_for_manager(self,game_id,job_id,revision,destination,confirmed=False):
        return export_handoff(self._writable_job(game_id,job_id,revision),destination,
                              reviewed_revision=revision,confirmed=confirmed)

    def approve_request(self,game_id,request_id,expected_hash,cancel):
        service=self.service(game_id)
        req=service._read_request(request_id)
        allowed={'mods.create_plan','mods.download','mods.stage'} | set(KEYBIND_OPERATIONS)
        require(req['operation'] in allowed,'USE_ORIGINAL_WORKSPACE',
                'Review this operation in its original workspace.')
        service.cancel=cancel
        return service.approve_local(request_id,expected_hash)

    def compare_plans(self,game_id,older_id,newer_id):
        a=self.job(game_id,older_id).items;b=self.job(game_id,newer_id).items
        return {'game_id':game_id,'from_job':older_id,'to_job':newer_id,
                'added':sorted(set(b)-set(a)),'removed':sorted(set(a)-set(b)),
                'changed':sorted(i for i in set(a)&set(b) if a[i]!=b[i]),
                'compares':'intended_plans_not_installed_state','writes_game_files':False}

    def request_review(self,game_id,request_id):
        service=self.service(game_id);row=service.request_status(slug(request_id))
        req=service._read_request(request_id);reason=None;op=row['operation'];a=row['arguments']
        allowed={'mods.create_plan','mods.download','mods.stage'} | set(KEYBIND_OPERATIONS)
        if op not in allowed:reason='This existing request belongs in the original overlay workspace.'
        try:service._check_current(req)
        except (ModError,KeybindError) as e:reason=getattr(e,'message',str(e))
        items=[]
        if op=='mods.create_plan':items=[i['id'] for i in service.preview_plan(a['selected'],a['mode'])['items']] if reason is None else list(a['selected'] or [])
        elif op=='mods.stage':items=a['item_ids']
        elif op=='mods.download':items=list(service._job(a['job_id']).items)
        elif op=='keybinds.prepare':items=[i['target_id'] for i in a['items']]
        elif op in {'keybinds.apply','keybinds.prepare_rollback'}:
            try:items=[i['target_id'] for i in service.keybinds.plan(a['plan_id'])['items']]
            except (KeybindError,OSError,KeyError,ValueError):items=[]
        effects={'mods.create_plan':'Create one new immutable plan; no downloads or game changes.',
                 'mods.download':'Download original archives privately; no installation.',
                 'mods.stage':'Prepare selected files privately; no game-folder writes.',
                 'keybinds.prepare':'Stage immutable native copies; no game configuration changes.',
                 'keybinds.apply':'Replace only the exact approved plan files; original bytes are retained.',
                 'keybinds.prepare_rollback':'Stage inverse copies; no game change until separate approval.',
                 'keybinds.edit_draft':'Save an immutable child draft; preserve its base and write no game file.',
                 'keybinds.draft_pack':'Save an unreviewed draft definition; no import, activation or game change.'}
        return {**row,'game_id':game_id,
                'game_name':service.recipe.get('name',game_id) if not getattr(service,'keybind_only',False) else game_id,
                'items':items,'current':reason is None,'blocking_reason':reason,
                'effect':effects.get(op,'Unavailable here'),
                'limit':'128 MiB / 40 requests / 5 minutes' if op=='mods.download' else 'Local data only',
                'manual_approval_required':True,'gameplay_verified':False}

    def create_samples_local(self, *, confirmed=False):
        """Opt-in, text-only sample jobs. Never evidence about an installed game."""
        require(confirmed,'REVIEW_REQUIRED','Confirm creation of the local sample workflow.')
        import io, zipfile
        rows=[]
        for suffix in ('alpha','beta'):
            ident='workflow-sample-'+suffix
            folder=self.data_dir/'workbench-samples'/suffix
            recipe={'schema_version':1,'kind':'game_mod_recipe','game_id':ident,
                'name':'Sample '+suffix.title()+' · not a real game','manager_id':'manual',
                'presets':{'real-time':['sample-content'],'turn-based':['sample-content']},
                'warnings':['Text-only sample workflow. No installed game or real mod.'],
                'items':[{'id':'sample-content','name':'Text-only sample file','kind':'mod',
                    'display_version':'sample-1','max_download_bytes':1048576,'sha256':None,
                    'download_page':'https://example.invalid/sample',
                    'source':{'kind':'manual'},'requires':[],'conflicts':[]}]}
            source=folder/'recipe.json'
            if source.exists():
                require(object_hash(load_recipe(source))==object_hash(recipe),'SOURCE_CHANGED','An existing sample recipe changed; review it.')
            else:json_new(source,recipe)
            self.catalog.import_local(source,confirmed=True)
            existing=self.jobs(ident)
            if existing:
                rows.append({'game_id':ident,'job_id':existing[0]['job_id'],'reused':True});continue
            j=self.new_plan(ident)
            archive=folder/'text-only-sample.zip'
            if not archive.exists():
                buf=io.BytesIO()
                with zipfile.ZipFile(buf,'w') as z:
                    z.writestr('SAMPLE.txt','Fictional sample '+suffix+'. No game or mod binary.\n')
                write_new(archive,buf.getvalue())
            import_archive(j,'sample-content',archive,confirmed_source=True)
            if suffix=='alpha':stage(j,'sample-content')
            rows.append({'game_id':ident,'job_id':j.path.name,'reused':False})
        return {'status':'SAMPLES_READY_NOT_GAME_EVIDENCE','jobs':rows,'network_used':False}

    def keybind_context(self,game_id=None,known_revision=None):
        value={'games':[{'game_id':r['id'],'pack_available':r.get('keybind_pack_available',False),
                         'pack_revision':r.get('keybind_pack_revision')}
                        for r in self.game_rows() if game_id is None or r['id']==game_id],
               'instances':list_keybind_instances(self.keybinds,game_id=game_id),
               'native_game_tested':False,'mod_recipe_required_for_keybinds':False}
        revision=object_hash(value)
        return {'revision':revision,'unchanged':revision==known_revision,**({} if revision==known_revision else value)}

    def context(self,game_id=None,known_revisions=None):
        known_revisions=known_revisions or {}
        require(type(known_revisions) is dict and len(known_revisions)<=4 and
                all(type(k) is str and type(v) is str and SHA.fullmatch(v) for k,v in known_revisions.items()),
                'INVALID_ARGUMENTS','Expected a bounded revision map.')
        rows=self.game_rows()
        if game_id is not None:
            slug(game_id)
            require(game_id in {r['id'] for r in rows},'UNKNOWN_GAME','Unknown game scope.')
        games=[{'game_id':r['id'],'recipe_available':r['recipe_available'],
                'recipe_revision':r['recipe_revision'],'installation':'unknown',
                'support_revision':r.get('support_revision'),
                'adapter_capabilities':r.get('adapter_capabilities',{}),
                'keybind_pack_available':r.get('keybind_pack_available',False),
                'keybind_pack_revision':r.get('keybind_pack_revision')}
               for r in rows if game_id is None or r['id']==game_id]
        jobs=[]
        for row in self.jobs(game_id):
            if row['status']!='AVAILABLE':jobs.append(row);continue
            j=self.job(row['game_id'],row['job_id'])
            jobs.append({'job_id':row['job_id'],'game_id':row['game_id'],'job_revision':row['revision'],
                'plan_sha256':j.plan['plan_sha256'],'mode':j.plan['mode'],
                'items':[{'id':i,'status':j.latest(i)['status']} for i in j.items],
                'runtime_acceptance':False,'manual_checks':self.checks(row['game_id'],row['job_id'],True)})
        keybinds=self.keybind_context(game_id)
        sections={'games':games,'jobs':jobs,'keybinds':keybinds,
                  'capabilities':{'requestable':['mods.create_plan','mods.download','mods.stage',*KEYBIND_OPERATIONS],
                  'local_approval_required':True,'max_local_workers':2,'max_transfers':1,
                  'installed_game_control':False,'automatic_cloud_send':False,
                  'keybind_gameplay_verified':False}}
        revisions={k:object_hash(v) for k,v in sections.items()}
        out={'schema_version':1,'kind':'game_workspace_context','game_id':game_id,'revisions':revisions,
             'sections':{k:v for k,v in sections.items() if known_revisions.get(k)!=revisions[k]},
             'unchanged':[k for k in sections if known_revisions.get(k)==revisions[k]],
             'evidence_not_instructions':True,'privacy':'No private paths, source URLs, raw logs or manual notes.'}
        require(len(json.dumps(out).encode())<=256*1024,'OUTPUT_LIMIT','Context exceeds its bound; select one game.')
        return out


class WorkspaceAI:
    """Game-aware facade for the existing stdio Endpoint; no approval method exposed."""
    multi_game=True
    def __init__(self,data_dir):
        self.workspaces=GameWorkspaces(data_dir)
        self.keybinds=self.workspaces.keybinds
    def games(self):return self.workspaces.context()['sections']['games']
    def support_schema(self):return support_schema()
    def validate_support(self,pack):
        return self.workspaces.catalog.support.review(pack)
    def support_template(self,game_id,name,adapter='directory',executable='Game.exe'):
        return {'pack':scaffold(game_id,name,adapter,executable),'registered':False,'installed':False}
    def game_support(self,game_id):
        row=self.workspaces.catalog.support.get(game_id)
        # Exact relative layout is public game metadata, not the chosen local path.
        return {'summary':describe(row['pack']),'definition':{k:v for k,v in row['pack']['definition'].items() if k!='review_note'},
                'preset_names':list((row['pack']['recipe'] or {}).get('presets',{})),
                'data_not_instructions':True}

    def context(self,game_id=None,known_revisions=None):return self.workspaces.context(game_id,known_revisions)
    def preview_plan(self,game_id,selected=None,mode=None):
        service=self.workspaces.service(game_id)
        if mode is None:mode='default' if 'default' in service.recipe.get('presets',{}) else 'real-time'
        p=service.preview_plan(selected,mode)
        return {k:p[k] for k in ('schema_version','game_id','mode','recipe_sha256','plan_sha256')} | {
            'items':[{'id':i['id'],'kind':i['kind'],'requires':i.get('requires',[])} for i in p['items']],
            'network_authorized':False,'installation_authorized':False,
            'notice':'Sources and free-text recipe fields stay local; preview is not execution.'}
    def propose(self,game_id,operation,arguments,request_id=None):
        allowed={'mods.create_plan','mods.download','mods.stage'} | set(KEYBIND_OPERATIONS)
        require(operation in allowed,'CAPABILITY_UNAVAILABLE','Not a workbench mod/keybind action.')
        return {'game_id':game_id,**self.workspaces.service(game_id).propose(operation,arguments,request_id=request_id)}
    def request_status(self,request_id,game_id):
        return {'game_id':game_id,**self.workspaces.service(game_id).request_status(request_id)}


class ViewState:
    """Independent presentation/drafts; compare before save; no installed settings."""
    DEFAULT={'schema_version':1,'active_game':'pathfinder-kingmaker','zoom':100,'density':'Compact','theme':'Dark','games':{}}
    def __init__(self,path):
        self.path=no_links(path);self.raw=self.path.read_bytes() if self.path.exists() else None
        self.value=copy.deepcopy(self.DEFAULT)
        if self.raw is not None:
            require(len(self.raw)<=64*1024,'SIZE_LIMIT','Workbench view file is too large.')
            value=read_json(self.path,64*1024);self.validate(value);self.value=value
    @staticmethod
    def validate(v):
        require(type(v) is dict and set(v)==set(ViewState.DEFAULT) and type(v['schema_version']) is int and v['schema_version']==1,'VIEW_SCHEMA','Unsupported view schema.')
        slug(v['active_game'])
        require(type(v['zoom']) is int and v['zoom'] in range(80,201,10),'VIEW_SCHEMA','Zoom must be 80–200%.')
        require(v['density'] in {'Compact','Comfortable'} and v['theme'] in {'Dark','Light'},'VIEW_SCHEMA','Invalid appearance.')
        require(type(v['games']) is dict and len(v['games'])<=MAX_GAMES,'VIEW_SCHEMA','Too many draft workspaces.')
        for game,draft in v['games'].items():
            slug(game)
            require(type(draft) is dict and set(draft)<= {'mode','selected','job_id','filter','item_id'},'VIEW_SCHEMA','Invalid draft fields.')
            validate_mode(draft.get('mode','real-time'))
            require(type(draft.get('selected',[])) is list and len(draft.get('selected',[]))<=100,'VIEW_SCHEMA','Invalid draft selection.')
            for ident in draft.get('selected',[]):slug(ident)
            require(len(set(draft.get('selected',[])))==len(draft.get('selected',[])),'VIEW_SCHEMA','Repeated draft item.')
            for field in ('job_id','item_id'):
                if draft.get(field):slug(draft[field])
            require(type(draft.get('filter','')) is str and len(draft.get('filter',''))<=200,'VIEW_SCHEMA','Invalid filter.')
    def save(self):
        self.validate(self.value);self.path=no_links(self.path)
        require((self.path.read_bytes() if self.path.exists() else None)==self.raw,'CONCURRENT_CHANGE','Another window changed the workbench view. It was not overwritten.')
        raw=(json.dumps(self.value,indent=2,ensure_ascii=False)+'\n').encode()
        if raw==self.raw:return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with local_lock(self.path.parent,'workbench-view.lock'):
            require((self.path.read_bytes() if self.path.exists() else None)==self.raw,'CONCURRENT_CHANGE','View changed during save.')
            fd,temp=tempfile.mkstemp(dir=self.path.parent,prefix='.workbench-')
            try:
                with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
                os.replace(temp,self.path);self.raw=raw
            finally:
                if os.path.exists(temp):os.unlink(temp)
