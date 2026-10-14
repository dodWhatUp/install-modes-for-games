"""Data-only game packs, immutable revision pins and local instance registration.
Adding a game with supported text semantics needs data/fixtures, not core edits.
"""
from __future__ import annotations
import copy,fnmatch,hashlib,json,os,re,stat,tempfile,time,zipfile
from pathlib import Path
from .deps import Error,require,slug,no_links,contained,read_json,json_new,object_hash,local_lock,strict_json
from .adapter_registry import adapter_info,capabilities
from .core import Service,snapshot,sha,validate_spec,native_key,compile_changes
from .documents import Document
from .discovery import walk_pattern

MAX_PACK_BYTES=4*1024*1024
MAX_PACK_FILES=128
EXTS={'.json','.jsonc','.ini','.cfg','.xml','.vdf','.acf','.conf','.properties','.txt','.md'}
VERSION=re.compile(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[A-Za-z0-9.-]+)?\Z')

def _obj(v,required,optional=(),code='PACK_INVALID'):
    require(type(v) is dict and set(required)<=set(v)<=set(required)|set(optional),code,'Missing or unexpected data fields.')

def _text(v,limit=256):
    require(type(v) is str and 0<len(v)<=limit and not any(ord(c)<32 for c in v),'PACK_INVALID','Expected bounded single-line text.')

def validate_pack(p:dict)->dict:
    _obj(p,{'schema_version','kind','id','version','game_id','title','keymaps','files','variants','presets','evidence','fixtures'}, {'exclusive_contexts'})
    require(type(p['schema_version']) is int and p['schema_version']==1 and p['kind']=='game-keybind-pack','PACK_SCHEMA','Expected game-keybind-pack schema 1.')
    slug(p['id']);slug(p['game_id']);_text(p['title'])
    require(type(p['version']) is str and VERSION.fullmatch(p['version']),'PACK_VERSION','Expected a semantic version.')
    require(type(p['keymaps']) is dict and 0<len(p['keymaps'])<=32,'PACK_INVALID','Declare bounded reusable key encodings.')
    for name,k in p['keymaps'].items():slug(name);require(type(k) is dict and 0<len(k)<=256,'PACK_INVALID','Keymap limit is 256 entries.')
    ev=p['evidence'];_obj(ev,{'stage','notes','sources'})
    require(ev['stage'] in {'draft','source-reviewed','fixture-tested'},'PACK_INVALID','In-game acceptance is never inferred from pack metadata.')
    _text(ev['notes'],1000);require(type(ev['sources']) is list and len(ev['sources'])<=32,'PACK_INVALID','Sources must be bounded.')
    for source in ev['sources']:
        _obj(source,{'url','note'});_text(source['url'],1000);_text(source['note'],1000)
        require(source['url'].startswith(('https://','source:')),'PACK_INVALID','Use source locators, not executable commands.')
    require(type(p['files']) is list and 0<len(p['files'])<=16,'PACK_INVALID','A game pack defines 1–16 config files.')
    file_ids=set()
    for f in p['files']:
        _obj(f,{'id','adapter','locations','fields','inventory_complete','stopped_processes','writable','priority','fingerprints'}, {'encoding','allow_middle'})
        slug(f['id']);require(f['id'] not in file_ids,'PACK_INVALID','Duplicate file ID.');file_ids.add(f['id'])
        require(type(f['priority']) is int and 0<=f['priority']<=10000,'PACK_INVALID','Priority is an explicit scalar-override rank.')
        require(type(f['writable']) is bool and type(f['inventory_complete']) is bool,'PACK_INVALID','Permissions/completeness are explicit booleans.')
        # Unknown adapter is a visible capability gap, never a pass-through writer.
        _text(f['adapter']);require(type(f['locations']) is list and 0<len(f['locations'])<=12,'PACK_INVALID','Declare bounded discovery rules.')
        for loc in f['locations']:
            _obj(loc,{'root','pattern'});require(re.fullmatch(r'[A-Z][A-Z0-9_]{0,47}',loc['root']) is not None,'PACK_INVALID','Invalid root alias.')
            pat=loc['pattern'];_text(pat,300)
            require(not pat.startswith('/') and '\\' not in pat and '**' not in pat and len(pat.split('/'))<=12 and all(x not in {'','.','..'} and ':' not in x for x in pat.split('/')),'UNSAFE_PATTERN','Only bounded relative path components.')
        require(type(f['fields']) is list and len(f['fields'])<=512,'PACK_INVALID','At most 512 fields per file.')
        ids=set()
        for field in f['fields']:
            _obj(field,{'id','selector','keymap','action','contexts'}, {'slot','locked','linked_group','fallback_key','modifier_match'})
            slug(field['id']);slug(field['action']);require(field['id'] not in ids,'PACK_INVALID','Duplicate field ID.');ids.add(field['id'])
            require(field['keymap'] in p['keymaps'],'PACK_INVALID','Unknown key encoding.')
            require(type(field['selector']) is dict and len(json.dumps(field['selector']))<=4096,'PACK_INVALID','Bounded exact selector required.')
            require(type(field['contexts']) is list and 0<len(field['contexts'])<=16 and len(field['contexts'])==len(set(field['contexts'])),'PACK_INVALID','Declare distinct runtime contexts.')
            for c in field['contexts']:slug(c)
            slug(field.get('slot','primary'));require(field.get('modifier_match','subset') in {'exact','subset'},'PACK_INVALID','Unknown modifier interpretation.')
        require(type(f['fingerprints']) is list and len(f['fingerprints'])<=32,'PACK_INVALID','Bounded schema fingerprint checks required.')
        for fp in f['fingerprints']:_obj(fp,{'selector','equals'})
        require(type(f['stopped_processes']) is list and len(f['stopped_processes'])<=32,'PACK_INVALID','Invalid writer policy.')
        for name in f['stopped_processes']:require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_. -]{1,100}',name),'PACK_INVALID','Executable basenames only.')
    require(type(p['variants']) is list and 0<len(p['variants'])<=32,'PACK_INVALID','Declare at least one variant.')
    variants=set();counts={f['id']:sum(len(x['contexts']) for x in f['fields']) for f in p['files']}
    for v in p['variants']:
        _obj(v,{'id','files'});slug(v['id']);require(v['id'] not in variants,'PACK_INVALID','Duplicate variant.');variants.add(v['id'])
        require(type(v['files']) is list and 0<len(v['files'])==len(set(v['files'])) and set(v['files'])<=file_ids,'PACK_INVALID','Variant file selection is invalid.')
        require(sum(counts[x] for x in v['files'])<=2048,'GRAPH_BUDGET','Limit each reviewed variant to 2048 native context bindings.')
    require(type(p['presets']) is list and len(p['presets'])<=64,'PACK_INVALID','Preset limit exceeded.')
    preset_ids=set()
    for ps in p['presets']:
        _obj(ps,{'id','variant','changes'});slug(ps['id']);require(ps['id'] not in preset_ids,'PACK_INVALID','Duplicate preset.');preset_ids.add(ps['id'])
        require(ps['variant'] in variants and type(ps['changes']) is list and len(ps['changes'])<=512,'PACK_INVALID','Invalid preset variant/changes.')
        for change in ps['changes']:validate_intent(change)
    require(type(p['fixtures']) is list and len(p['fixtures'])<=64,'PACK_INVALID','Fixture limit exceeded.')
    for fix in p['fixtures']:
        _obj(fix,{'file_id','before','after','changes'})
        require(fix['file_id'] in file_ids and type(fix['changes']) is dict,'PACK_INVALID','Invalid fixture.')
        for k in ('before','after'):portable_path(fix[k])
    ex=p.get('exclusive_contexts',[]);require(type(ex) is list and len(ex)<=64,'PACK_INVALID','Context exclusions must be bounded.')
    for pair in ex:
        require(type(pair) is list and len(pair)==2 and pair[0]!=pair[1],'PACK_INVALID','Declare context pairs, not inferred exclusivity.')
        for c in pair:slug(c)
    return p

def validate_intent(c):
    _obj(c,{'action','context','key'}, {'slot'})
    for k in ('action','context'):slug(c[k])
    slug(c.get('slot','primary'));_text(c['key'],64)

def portable_path(path:str)->str:
    require(type(path) is str and len(path)<=240 and not path.startswith('/') and '\\' not in path and not any(c in path for c in ':*?<>|') and not any(ord(c)<32 or ord(c)==127 for c in path),'UNSAFE_PATH','Pack payloads use relative portable paths.')
    parts=path.split('/');require(all(x not in {'','.','..'} and not x.endswith((' ','.')) for x in parts),'UNSAFE_PATH','Unsafe payload path.')
    require(Path(path).suffix.lower() in EXTS,'PACK_EXECUTABLE_BLOCKED','Only data, text fixtures and documentation belong in a game pack.')
    for x in parts:
        require(x.split('.')[0].upper() not in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]},'UNSAFE_PATH','Windows reserved name.')
    return path

def payloads(folder:Path)->dict[str,bytes]:
    folder=no_links(folder);require(folder.is_dir(),'PACK_NOT_FOUND','A game-pack directory is required.')
    out={};total=0;names=set();entries=0
    for base,dirs,files in os.walk(folder,followlinks=False):
        entries+=len(dirs)+len(files);require(entries<=512,'PACK_BUDGET','Pack directory-entry budget exceeded.')
        for dn in dirs:no_links(Path(base)/dn)
        for name in files:
            file=no_links(Path(base)/name);rel=file.relative_to(folder).as_posix();portable_path(rel)
            require(rel.casefold() not in names,'PACK_DUPLICATE','Case-aliased pack files are not portable.');names.add(rel.casefold())
            raw=snapshot(file);total+=len(raw);require(len(out)<MAX_PACK_FILES and total<=MAX_PACK_BYTES,'PACK_BUDGET','Pack file/byte budget exceeded.');out[rel]=raw
    require('pack.json' in out,'PACK_NOT_FOUND','pack.json is required.')
    return out

def fingerprint(doc,checks):
    for c in checks:
        v=doc.select(c['selector']).value
        require(type(v) is type(c['equals']) and v==c['equals'],'BUILD_MISMATCH','Native schema/build fingerprint did not match this pack.')

def spec_for(pack,file,root,relative,target_id,scope_id=None):
    spec={'schema_version':1,'target_id':target_id,'game_id':pack['game_id'],'root':str(root),'relative':relative,
          'adapter':file['adapter'],'fields':[],'inventory_complete':file['inventory_complete'],
          'stopped_processes':file['stopped_processes'],'evidence':pack['evidence']['notes'],
          'allow_middle':file.get('allow_middle',False),'live_tested':False}
    if scope_id:spec['scope_id']=scope_id
    if file.get('encoding'):spec['encoding']=file['encoding']
    for f in file['fields']:
        x={'id':f['id'],'selector':f['selector'],'keys':pack['keymaps'][f['keymap']],
           'collision_group':'|'.join(f['contexts']),'locked':f.get('locked',False) or not file['writable']}
        for k in ('linked_group','fallback_key'):
            if k in f:x[k]=f[k]
        spec['fields'].append(x)
    return spec

def inspect_pack(folder:Path)->dict:
    blobs=payloads(folder);pack=validate_pack(strict_json(blobs['pack.json']))
    manifest=[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in sorted(blobs.items())]
    missing=[];results=[]
    for f in pack['files']:
        try:adapter_info(f['adapter'])
        except Error:missing.append(f['adapter']);continue
        if f['fields'] and f['stopped_processes']:
            # Validate native vocabularies without fabricating a game source file.
            ext=adapter_info(f['adapter']).extensions[0]
            validate_spec(spec_for(pack,f,Path(folder).absolute(),'fixture'+ext,'check'))
    for fix in pack['fixtures']:
        f=next(x for x in pack['files'] if x['id']==fix['file_id'])
        require(fix['before'] in blobs and fix['after'] in blobs,'FIXTURE_MISSING','Both fixture files must be included.')
        if f['adapter'] in missing:results.append({'file_id':f['id'],'status':'ADAPTER_UNAVAILABLE'});continue
        spec=spec_for(pack,f,Path(folder).absolute(),fix['before'],'fixture')
        before,expected=blobs[fix['before']],blobs[fix['after']]
        fingerprint(Document(before,f['adapter'],f.get('encoding')),f['fingerprints'])
        actual,diff=compile_changes(before,spec,fix['changes'])
        require(actual==expected,'FIXTURE_FAILED','Generated bytes differ from the expected native fixture.')
        # Exact undo uses original bytes; semantic inverse may intentionally retain formatting.
        inv={x['field_id']:x['from'] for x in diff};reversed_bytes,_=compile_changes(actual,spec,inv)
        da,db=Document(before,f['adapter'],f.get('encoding')),Document(reversed_bytes,f['adapter'],f.get('encoding'))
        require(all(da.select(x['selector']).value==db.select(x['selector']).value for x in spec['fields']),'FIXTURE_FAILED','Semantic inverse failed.')
        results.append({'file_id':f['id'],'status':'PASS','exact_expected_bytes':True,'semantic_inverse':True,'gameplay_verified':False})
    digest=object_hash(manifest)
    ready=not missing and pack['evidence']['stage']!='draft' and all(f['fields'] and f['inventory_complete'] and f['stopped_processes'] for f in pack['files'])
    return {'pack_id':pack['id'],'version':pack['version'],'game_id':pack['game_id'],'title':pack['title'],
            'pack_sha256':digest,'files':manifest,'fixtures':results,'missing_adapters':sorted(set(missing)),
            'schema_review_claim':pack['evidence']['stage'],'eligible_for_local_review':bool(ready),
            'native_tested':False,'gameplay_verified':False,'automatic_activation':False}

def stored_folder(service:Service,pin:dict)->Path:
    _obj(pin,{'pack_id','version','sha256'})
    slug(pin['pack_id']);require(type(pin['version']) is str and VERSION.fullmatch(pin['version']),'PACK_VERSION','Invalid pinned version.')
    require(type(pin['sha256']) is str and re.fullmatch('[a-f0-9]{64}',pin['sha256']),'PACK_INVALID','Invalid pinned digest.')
    return contained(service.root,'packs/'+pin['pack_id']+'/'+pin['version'])

def load_pin(service:Service,pin:dict)->dict:
    root=stored_folder(service,pin);manifest=read_json(root/'receipt.json',256*1024)
    require(manifest['pack_sha256']==pin['sha256'],'PACK_CHANGED','Pinned game-pack identity changed.')
    blobs=payloads(root/'payload');actual=[{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in sorted(blobs.items())]
    require(object_hash(actual)==pin['sha256'],'PACK_CHANGED','Game-pack bytes changed after import.')
    return validate_pack(strict_json(blobs['pack.json']))

def import_pack_local(service:Service,folder:Path,expected_sha256:str,*,authorize)->dict:
    report=inspect_pack(folder);require(report['pack_sha256']==expected_sha256,'PACK_CHANGED','Pack changed after review.')
    require(callable(authorize) and authorize(report) is True,'LOCAL_APPROVAL_REQUIRED','Import requires explicit local review; AI cannot approve itself.')
    pin={'pack_id':report['pack_id'],'version':report['version'],'sha256':report['pack_sha256']}
    dest=stored_folder(service,pin)
    with local_lock(service.root,'.keybind-ops.lock'):
        if dest.exists():load_pin(service,pin);return {'pin':pin,'status':'ALREADY_IMPORTED_NOT_ACTIVATED'}
        blobs=payloads(folder)
        require(object_hash([{'path':p,'bytes':len(b),'sha256':sha(b)} for p,b in sorted(blobs.items())])==expected_sha256,'PACK_CHANGED','Pack changed during import.')
        service._budget(sum(len(v) for v in blobs.values())+32768)
        # Interrupted imports stay explicit incomplete directories; no implicit retry.
        (dest/'payload').mkdir(parents=True,exist_ok=False)
        for name,data in blobs.items():
            out=contained(dest/'payload',name);out.parent.mkdir(parents=True,exist_ok=True)
            with out.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
            require(snapshot(out)==data,'PACK_CHANGED','Imported payload did not round-trip.')
        json_new(dest/'receipt.json',report)
    load_pin(service,pin)
    return {'pin':pin,'status':'IMPORTED_NOT_ACTIVATED','gameplay_verified':False}

def list_packs(service:Service)->list[dict]:
    base=service.root/'packs'
    if not base.exists():return []
    rows=[]
    for g in sorted(no_links(base).iterdir()):
        for v in sorted(no_links(g).iterdir()):
            require(len(rows)<1024,'PACK_BUDGET','Pack revision limit exceeded.')
            try:
                r=read_json(no_links(v)/'receipt.json',256*1024)
                pin={'pack_id':r['pack_id'],'version':r['version'],'sha256':r['pack_sha256']};load_pin(service,pin)
                rows.append({'pin':pin,'game_id':r['game_id'],'eligible_for_local_review':r['eligible_for_local_review'],'status':'PINNED_DATA_ONLY'})
            except (Error,OSError,KeyError,ValueError):rows.append({'pack_id':g.name,'version':v.name,'status':'INCOMPLETE_OR_CORRUPT'})
    return rows

def discover_pack(pack:dict,roots:dict[str,Path])->dict:
    validate_pack(pack);require(type(roots) is dict and len(roots)<=24,'ROOTS_INVALID','Use scoped root aliases.')
    out=[];warnings=[]
    for f in pack['files']:
        seen=set()
        for loc in f['locations']:
            alias=loc['root']
            if alias not in roots:warnings.append({'file_id':f['id'],'root':alias,'status':'ROOT_UNRESOLVED'});continue
            try:found=walk_pattern(no_links(roots[alias]),loc['pattern'])
            except (Error,OSError) as e:warnings.append({'file_id':f['id'],'root':alias,'status':getattr(e,'code','READ_FAILED')});continue
            for file in found:
                if not file.is_file() or str(file).casefold() in seen:continue
                seen.add(str(file).casefold());root=no_links(roots[alias])
                status='CANDIDATE_NOT_ACTIVE';digest=None
                try:
                    data=snapshot(file);digest=sha(data);doc=Document(data,f['adapter'],f.get('encoding'));fingerprint(doc,f['fingerprints'])
                    for field in f['fields']:native_key({'keys':pack['keymaps'][field['keymap']]},doc.select(field['selector']).value)
                except (Error,OSError) as e:status=getattr(e,'code','READ_FAILED')
                out.append({'file_id':f['id'],'candidate_id':object_hash([pack['id'],f['id'],str(file)])[:24],
                            'root_alias':alias,'relative':file.relative_to(root).as_posix(),'private_path':str(file),
                            'sha256':digest,'status':status,'active_verified':False})
                require(len(out)<=256,'DISCOVERY_LIMIT','Narrow roots; do not guess the active config.')
    return {'game_id':pack['game_id'],'candidates':out,'warnings':warnings,'files_modified':False,'selection':'LOCAL_OPERATOR_REQUIRED'}

def bind_instance_local(service:Service,pin:dict,instance_id:str,variant_id:str,bindings:dict,expected_files:dict,*,authorize,evidence:str)->dict:
    """Register one reviewed game installation. All files must already exist.
    bindings: {file_id: {root:absolute, relative:portable}}. No AI exposure.
    """
    slug(instance_id);pack=load_pin(service,pin);variant=next((x for x in pack['variants'] if x['id']==variant_id),None)
    require(variant is not None,'VARIANT_UNKNOWN','Select one exact variant; never merge alternatives.')
    require(pack['evidence']['stage']!='draft','PACK_DRAFT','Complete native mapping review before binding a draft.')
    require(type(bindings) is dict and set(bindings)==set(variant['files'])==set(expected_files),'INSTANCE_FILES','Select every file in this variant once.')
    _text(evidence,1000);specs=[];members=[];paths=set()
    for f in pack['files']:
        if f['id'] not in bindings:continue
        require(f['inventory_complete'] and f['fields'] and f['stopped_processes'],'INVENTORY_INCOMPLETE','Review this file and effective contexts first.')
        b=bindings[f['id']];_obj(b,{'root','relative'})
        spec=spec_for(pack,f,Path(b['root']),b['relative'],instance_id+'-'+f['id'],instance_id);validate_spec(spec)
        path=contained(Path(b['root']),b['relative']);key=str(path).casefold()
        require(key not in paths,'DUPLICATE_TARGET','Two file definitions refer to the same native file.');paths.add(key)
        raw=snapshot(path);require(sha(raw)==expected_files[f['id']],'SOURCE_CHANGED','Source changed since instance review.')
        d=Document(raw,f['adapter'],f.get('encoding'));fingerprint(d,f['fingerprints'])
        for field in spec['fields']:native_key(field,d.select(field['selector']).value)
        specs.append(spec);members.append({'file_id':f['id'],'target_id':spec['target_id'],'target_revision':object_hash(spec),
                                         'priority':f['priority'],'writable':f['writable'],'fields':f['fields'],'fingerprints':f['fingerprints']})
    body={'schema_version':1,'instance_id':instance_id,'game_id':pack['game_id'],'variant_id':variant_id,'pin':pin,
          'members':members,'exclusive_contexts':pack.get('exclusive_contexts',[]),'evidence':evidence}
    revision=object_hash(body);record={'body':body,'revision':revision}
    report={'instance_id':instance_id,'game_id':pack['game_id'],'variant_id':variant_id,'files':expected_files,'revision':revision,'gameplay_verified':False}
    require(callable(authorize) and authorize(report) is True,'LOCAL_APPROVAL_REQUIRED','Approve this exact local file/schema selection.')
    dest=contained(service.root,'instances/'+instance_id+'.json')
    if dest.exists():
        require(read_json(dest)==record,'INSTANCE_CONFLICT','Preserve existing instance; register a distinct reviewed instance ID.')
        from .effective import inspect_instance
        return inspect_instance(service,instance_id)
    # Registration writes metadata only. A durable intent makes an interrupted
    # registration inspectable, and allows the SAME exact request to finish only
    # after a new local review and unchanged originals. Never reclaim another owner.
    pending=contained(service.root,'instance-intakes/'+instance_id+'.json')
    intake={'instance_revision':revision,'source_hashes':expected_files}
    with local_lock(service.root,'.keybind-registration.lock'):
        if pending.exists():require(read_json(pending)==intake,'INSTANCE_CONFLICT','An interrupted registration has a different identity. Inspect it; no automatic replacement.')
        else:
            with local_lock(service.root,'.keybind-ops.lock'):
                for t in service._list(service.targets,1024):
                    old=service.target(t.stem)['spec']
                    require(str(contained(Path(old['root']),old['relative'])).casefold() not in paths,'FILE_ALREADY_OWNED','A registered target already owns a selected file. Reconcile that owner.')
                json_new(pending,intake)
        proposed={x['target_id']:x for x in specs}
        for t in service._list(service.targets,1024):
            old=service.target(t.stem)['spec']
            if str(contained(Path(old['root']),old['relative'])).casefold() in paths:
                require(old['target_id'] in proposed and old==proposed[old['target_id']],'FILE_ALREADY_OWNED','A competing target owns one of the selected files.')
        for spec in specs:service.register_local(spec)
        with local_lock(service.root,'.keybind-ops.lock'):
            for f,s in zip([f for f in pack['files'] if f['id'] in bindings],specs):
                require(sha(snapshot(contained(Path(s['root']),s['relative'])))==expected_files[f['id']],'SOURCE_CHANGED','Files changed during registration. No game-file edit occurred.')
            json_new(dest,record)
    from .effective import inspect_instance
    return inspect_instance(service,instance_id)

def compare_packs(before:dict,after:dict)->dict:
    validate_pack(before);validate_pack(after)
    require(before['game_id']==after['game_id'] and before['id']==after['id'],'PACK_IDENTITY','Only compare revisions of the same game pack.')
    a={f['id']:f for f in before['files']};b={f['id']:f for f in after['files']}
    return {'added_files':sorted(b.keys()-a.keys()),'removed_files':sorted(a.keys()-b.keys()),
            'changed_files':sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]),'keymaps_changed':before['keymaps']!=after['keymaps'],
            'variants_changed':before['variants']!=after['variants'],'automatic_upgrade':False,
            'existing_instances':'remain pinned to their original exact pack bytes'}


def registration_status(service:Service,instance_id:str)->dict:
    slug(instance_id)
    target=contained(service.root,'instances/'+instance_id+'.json')
    pending=contained(service.root,'instance-intakes/'+instance_id+'.json')
    if target.exists():
        from .effective import instance
        r=instance(service,instance_id)
        return {'instance_id':instance_id,'status':'REGISTERED','instance_revision':r['revision'],'native_config_effects':'NONE_FROM_REGISTRATION'}
    if pending.exists():
        r=read_json(pending)
        return {'instance_id':instance_id,'status':'REGISTRATION_INCOMPLETE','instance_revision':r['instance_revision'],
                'native_config_effects':'NONE_FROM_REGISTRATION','next_action':'Review the same intake and unchanged source hashes, then explicitly finish the identical registration. No automatic retry.'}
    return {'instance_id':instance_id,'status':'NOT_REGISTERED','native_config_effects':'NONE_FROM_REGISTRATION'}
