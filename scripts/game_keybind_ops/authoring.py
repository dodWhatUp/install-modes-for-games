"""Repeatable adapter-author workflow on explicit local copies. Never certifies gameplay."""
from __future__ import annotations
import copy,json,os,time
from pathlib import Path
from .deps import require,contained,no_links,json_new,object_hash,local_lock,slug
from .core import snapshot,sha
from .documents import Document
from .adapter_registry import adapter_info,capabilities
from .packs import validate_pack,inspect_pack,validate_intent


def scaffold(folder:Path,game_id:str,title:str,adapter:str='json')->dict:
    slug(game_id);adapter_info(adapter);folder=no_links(folder)
    require(not folder.exists(),'DEST_EXISTS','A new authoring directory is required; existing drafts are never overwritten.')
    p={'schema_version':1,'kind':'game-keybind-pack','id':game_id,'version':'0.1.0','game_id':game_id,'title':title,
       'keymaps':{'keyboard':{'Space':'Space','F':'F','E':'E','R':'R','MouseLeft':'MouseLeft','MouseRight':'MouseRight','WheelUp':'WheelUp','WheelDown':'WheelDown'}},
       'files':[{'id':'input','adapter':adapter,'locations':[{'root':'GAME_CONFIG','pattern':'input'+adapter_info(adapter).extensions[0]}],
                 'fields':[],'inventory_complete':False,'stopped_processes':[],'writable':True,'priority':100,'fingerprints':[]}],
       'variants':[{'id':'keyboard','files':['input']}],'presets':[],
       'evidence':{'stage':'draft','notes':'Unreviewed scaffold. Fill actual selectors, encodings, build/writer policy and context inventory from current originals.','sources':[]},'fixtures':[]}
    validate_pack(p);folder.mkdir(parents=True,exist_ok=False);json_new(folder/'pack.json',p)
    text='''# New game adapter\n\nThis is a DRAFT, not native-game support.\n1. Inspect a current original with the inventory tool.\n2. Compare two copies with exactly one known in-game rebind using learn-diff.\n3. Fill actual native fields/keymap, schema fingerprints and stopped processes.\n4. Declare effective file precedence, complete overlapping contexts and alternate variants.\n5. Add sanitized before/expected fixtures and run pack-check.\n6. Local review imports one immutable revision; explicitly bind an instance to current files.\n7. Preview the complete change, use the existing approval/backups/rollback, then separately test the game.\n\nDo not rename sample key codes as evidence. Use the SDK for genuinely new formats.\n'''
    (folder/'AUTHORING.md').write_text(text,encoding='utf-8')
    return {'status':'DRAFT_CREATED','game_id':game_id,'format':adapter,'native_support':False,'needs':['actual_native_selectors','reviewed_key_codes','complete_contexts','writers','fixtures']}


def inventory(path:Path,adapter:str,offset=0,limit=50,include_values=False,encoding=None):
    require(type(offset) is int and offset>=0 and type(limit) is int and 1<=limit<=100,'PAGE_INVALID','Use offset >=0 and limit 1–100.')
    raw=snapshot(path);d=Document(raw,adapter,encoding);items=[]
    for cell in d.cells[offset:offset+limit]:
        r={'selector':cell.selector,'type':type(cell.value).__name__}
        if include_values:r['native_value']=cell.value
        items.append(r)
    return {'source_sha256':sha(raw),'adapter':adapter,'total':len(d.cells),'items':items,
            'next_offset':offset+limit if offset+limit<len(d.cells) else None,'review_status':'UNREVIEWED_LOCAL_INVENTORY','private_values_included':include_values}


def learn_difference(before:Path,after:Path,adapter:str,*,encoding=None,include_values=False):
    """Observe differences; attribution to game actions is an operator/research task."""
    a,b=snapshot(before),snapshot(after);da,db=Document(a,adapter,encoding),Document(b,adapter,encoding)
    ia={object_hash(c.selector):c for c in da.cells};ib={object_hash(c.selector):c for c in db.cells}
    common=ia.keys()&ib.keys();changes=[]
    for k in sorted(common):
        x,y=ia[k],ib[k]
        if type(x.value) is type(y.value) and x.value==y.value:continue
        row={'selector':x.selector,'before_type':type(x.value).__name__,'after_type':type(y.value).__name__,'status':'CANDIDATE_REQUIRES_SEMANTIC_REVIEW'}
        if include_values:row.update(before=x.value,after=y.value)
        changes.append(row)
    require(len(changes)<=512,'DIFF_BUDGET','Narrow the experiment to one controlled keybinding change.')
    return {'before_sha256':sha(a),'after_sha256':sha(b),'candidate_changes':changes,
            'added_selectors':[ib[k].selector for k in sorted(ib.keys()-ia.keys())][:100],
            'removed_selectors':[ia[k].selector for k in sorted(ia.keys()-ib.keys())][:100],
            'structure_changed':ia.keys()!=ib.keys(),'action_attribution':'NOT_INFERRED',
            'private_values_included':include_values,'files_modified':False,'gameplay_verified':False}


def save_draft(service,pack,request_id):
    """Called by the existing local approval controller, never an auto-approval path."""
    p=copy.deepcopy(pack);p['evidence']['stage']='draft';validate_pack(p);ident=slug(request_id)
    folder=contained(service.root,'authoring/'+ident);path=folder/'pack.json';expected=object_hash(p)
    with local_lock(service.root,'.keybind-ops.lock'):
        if path.exists():
            from .deps import read_json
            require(object_hash(read_json(path,4*1024*1024))==expected,'DRAFT_CONFLICT','This draft ID belongs to different contents.')
            return {'draft_id':ident,'pack_sha256':expected,'status':'DRAFT_ALREADY_SAVED','activated':False}
        require(not folder.exists(),'DRAFT_INCOMPLETE','Inspect the same incomplete draft; no overwrite or blind retry.')
        service._budget(len(json.dumps(p).encode('utf-8'))+4096);folder.mkdir(parents=True,exist_ok=False);json_new(path,p)
    return {'draft_id':ident,'pack_sha256':expected,'status':'DRAFT_SAVED_NOT_REVIEWED','activated':False}


def planner_bridge(extracted_variant:dict,crosswalk:list[dict])->dict:
    """Translate only exact reviewed source labels + canonical key aliases.
    Each crosswalk row: source_action, action, context, slot, keys {planner_label:canonical}.
    Never split a bundled label or infer Ctrl -> LCtrl.
    """
    require(type(crosswalk) is list and len(crosswalk)<=512,'CROSSWALK_INVALID','Use bounded explicit source/native links.')
    index={}
    for c in crosswalk:
        require(type(c) is dict and set(c)=={'source_action','action','context','slot','keys'},'CROSSWALK_INVALID','Unknown crosswalk fields.')
        require(type(c['keys']) is dict,'CROSSWALK_INVALID','Explicit planner-to-native key names are required.')
        require(c['source_action'] not in index,'CROSSWALK_AMBIGUOUS','One source action per variant crosswalk.');index[c['source_action']]=c
    rows=extracted_variant.get('assignments',[])
    if type(rows) is dict:rows=[dict(v,target_output=k) for k,v in rows.items()]
    require(type(rows) is list,'PLANNER_SCHEMA','Expected extracted assignment records.')
    intents=[];unresolved=[];seen={}
    for r in rows:
        name=r.get('label',r.get('en',r.get('action',r.get('search_name'))));key=r.get('target_key',r.get('target_output',r.get('output')))
        c=index.get(name)
        if c is None or key not in c['keys']:
            unresolved.append({'source_action':name,'source_key':key,'status':'ACTION_OR_KEY_CROSSWALK_REQUIRED'});continue
        v={'action':c['action'],'context':c['context'],'slot':c['slot'],'key':c['keys'][key]};validate_intent(v)
        ident=(v['action'],v['context'],v['slot'])
        require(ident not in seen or seen[ident]==v['key'],'CROSSWALK_AMBIGUOUS','Two planner actions give conflicting native targets.')
        if ident not in seen:intents.append(v);seen[ident]=v['key']
    return {'intents':intents,'unresolved':unresolved,'source_not_mutated':True,'gameplay_verified':False,'auto_apply':False}


def troubleshoot(code:str)->dict:
    steps={
      'SOURCE_CHANGED':('Inspect the SAME plan and current hashes; prepare a new preview only after reconciling the later edit.','inspection'),
      'DEPENDENCY_CHANGED':('Inspect the related defaults/override file and regenerate the complete instance preview.','instance-context'),
      'CROSS_FILE_COLLISION':('Request both effective actions and resolve the complete swap; do not suppress the conflict.','intent-preview'),
      'KEY_COLLISION':('Include the displaced action in the same reviewed change, or choose a different supported key.','preview'),
      'BUILD_MISMATCH':('Review current schema/build against the pinned pack. Add a new pack revision rather than edit the pin.','pack-check'),
      'ADAPTER_UNSUPPORTED':('Implement a reviewed text adapter using adapter_registry.register_adapter; data packs cannot execute code.','adapter-sdk'),
      'INVENTORY_INCOMPLETE':('Complete native fields and context ownership using controlled samples; do not set the flag without evidence.','learn-diff'),
      'SELECTOR_AMBIGUOUS':('Use a unique native identity or explicit occurrence; never select the newest or first match.','inventory'),
      'PACK_CHANGED':('Stop affected effects and obtain the intact exact pack; never reconstruct expected bytes.','integrity-stop'),
      'BACKUP_CORRUPT':('Stop affected effects. Preserve the damaged record and recover from independently verified originals.','integrity-stop'),
      'RECONCILIATION_REQUIRED':('Read the same operation journal and reconcile actual file effects before any new proposal.','reconcile'),
      'PROCESS_RUNNING':('Close the identified game/config writer normally; the helper does not kill processes.','operator-action'),
      'SPARSE_REMOVE_COMMENT':('Review the commented sparse entry locally; exact rollback is available only when current bytes still match the applied copy.','local-review'),
      'FILE_ALREADY_OWNED':('Reconcile the existing target/instance; a second scope must not compete for the same native file.','owner-review'),
    }
    instruction,operation=steps.get(code,('Inspect the exact typed error and current operation; do not retry unknown effects or lower protections.','inspection'))
    return {'code':code,'next_action':instruction,'suggested_tool':operation,'automatic_retry':False,'effects':'NONE'}


def draft_context(service,draft_id,section='overview',file_id=None,offset=0,limit=50):
    """Previously operator-approved DRAFT data only; never reads game source files."""
    from .deps import read_json
    slug(draft_id);require(type(offset) is int and offset>=0 and type(limit) is int and 1<=limit<=100,'PAGE_INVALID','Use bounded draft pages.')
    p=validate_pack(read_json(contained(service.root,'authoring/'+draft_id+'/pack.json'),4*1024*1024))
    common={'draft_id':draft_id,'draft_sha256':object_hash(p),'game_id':p['game_id'],'stage':p['evidence']['stage'],'activated':False}
    if section=='overview':
        return {**common,'title':p['title'],'version':p['version'],'files':[{'id':f['id'],'adapter':f['adapter'],'field_count':len(f['fields']),'inventory_complete':f['inventory_complete']} for f in p['files']],
                'keymap_ids':sorted(p['keymaps']),'variants':p['variants'],'fixture_count':len(p['fixtures'])}
    require(section in {'fields','keymaps','presets','evidence'},'DRAFT_SECTION','Unknown draft section.')
    if section=='fields':
        matches=[f for f in p['files'] if f['id']==file_id];require(len(matches)==1,'DRAFT_FILE','Select one exact draft file ID.');rows=matches[0]['fields']
    elif section=='keymaps':rows=[{'id':k,'values':v} for k,v in p['keymaps'].items()]
    elif section=='presets':rows=p['presets']
    else:rows=[p['evidence']]
    return {**common,'section':section,'items':rows[offset:offset+limit],'total':len(rows),
            'next_offset':offset+limit if offset+limit<len(rows) else None}


def draft_edit_preview(service,draft_id,expected_sha256,edits):
    """A bounded RFC6902-like add/replace/remove subset on immutable DRAFT JSON.
    Object/array semantics only. Exact base hash prevents positional array drift.
    Identity/schema fields remain fixed; output is forced to draft and revalidated.
    """
    from .deps import read_json
    from .format_extensions import _pointer
    slug(draft_id);p=read_json(contained(service.root,'authoring/'+draft_id+'/pack.json'),4*1024*1024);validate_pack(p)
    require(object_hash(p)==expected_sha256,'DRAFT_STALE','The draft differs from the reviewed base.')
    require(type(edits) is list and 0<len(edits)<=64,'DRAFT_EDIT','Use 1–64 bounded draft edits per request.')
    original=copy.deepcopy(p)
    for e in edits:
        require(type(e) is dict and e.get('op') in {'add','replace','remove'} and set(e)==({'op','path'} if e['op']=='remove' else {'op','path','value'}),'DRAFT_EDIT','Use exact add/replace/remove data fields.')
        pointer=e['path'];require(type(pointer) is str and pointer.startswith('/') and len(pointer)<=1024,'DRAFT_EDIT','Use a bounded draft JSON pointer, not a filesystem path.')
        parts=pointer.split('/')[1:]
        require(parts[0] not in {'schema_version','kind','id','game_id'} and parts[0] in p,'DRAFT_IDENTITY','Draft identity is immutable; create a separate game draft instead.')
        import re
        require(all(not re.search(r'~(?![01])',x) for x in parts),'DRAFT_EDIT','Invalid JSON pointer escape.')
        parent=_pointer(p,'/'.join(pointer.split('/')[:-1]));name=parts[-1].replace('~1','/').replace('~0','~')
        if type(parent) is list:
            require(name=='-' and e['op']=='add' or name.isdigit() and (name=='0' or not name.startswith('0')),'DRAFT_EDIT','Invalid array index.')
            idx=len(parent) if name=='-' else int(name)
            require(0<=idx<=len(parent) if e['op']=='add' else 0<=idx<len(parent),'DRAFT_EDIT','Array index outside the draft.')
            if e['op']=='add':parent.insert(idx,copy.deepcopy(e['value']))
            elif e['op']=='replace':parent[idx]=copy.deepcopy(e['value'])
            else:parent.pop(idx)
        else:
            require(type(parent) is dict,'DRAFT_EDIT','The target parent is not an object or array.')
            require(name not in parent if e['op']=='add' else name in parent,'DRAFT_EDIT','Add must be new; replace/remove must target an existing member.')
            if e['op']=='remove':del parent[name]
            else:parent[name]=copy.deepcopy(e['value'])
    p['evidence']['stage']='draft';validate_pack(p)
    require(p!=original,'NO_CHANGES','This draft edit makes no change.')
    return {'parent_draft_id':draft_id,'parent_sha256':expected_sha256,'draft_sha256':object_hash(p),'pack':p,'activated':False}


def edit_draft_local(service,draft_id,expected_sha256,edits,new_draft_id):
    """Use through the existing approved controller or trusted local operator API."""
    value=draft_edit_preview(service,draft_id,expected_sha256,edits)
    result=save_draft(service,value['pack'],new_draft_id)
    path=contained(service.root,'authoring/'+slug(new_draft_id)+'/PARENT.json')
    from .deps import read_json
    parent={k:value[k] for k in ('parent_draft_id','parent_sha256','draft_sha256')}
    with local_lock(service.root,'.keybind-ops.lock'):
        if path.exists():require(read_json(path)==parent,'DRAFT_CONFLICT','Draft parent lineage changed.')
        else:json_new(path,parent)
    return {**result,**parent}
