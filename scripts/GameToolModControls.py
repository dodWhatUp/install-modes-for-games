"""Multi-game mod controls over existing workspaces, identities and approvals.

No model API, game launcher, arbitrary reader, downloaded code or manager deployer.
"""
from __future__ import annotations
import configparser,copy,csv,hashlib,importlib.util,io,json,math,os,re,subprocess,sys,tempfile,uuid,zipfile
from pathlib import Path
from GameToolAutomation import AutomationService
from GameToolInstances import InstanceRegistry,KNOWN_READ_ADAPTERS,_assert_public_metadata
from GameToolUnified import atomic_json
from game_mod_ops.safety import ModError,contained,digest,json_new,local_lock,no_links,object_hash,read_json,require,safe_relative,slug
from GameToolJournal import Journal

VERSION='2.0.0'
ROOT=Path(__file__).resolve().parents[1]
PACKS=ROOT/'examples/game-tool-hub/game-support/controls'
SHADOW=ROOT/'examples/shadow-of-war-controls'
OPERATIONS={'controls.apply','controls.save_profile','controls.prepare_manager'}
TOOLS={'rhi':'RHI','vortex':'Vortex','mod-organizer-2':'Mod Organizer 2','steam':'Steam'}

def shadow_module():
    name='_game_tools_reviewed_shadow'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,SHADOW/'__init__.py',submodule_search_locations=[str(SHADOW)])
        package=importlib.util.module_from_spec(spec);sys.modules[name]=package;spec.loader.exec_module(package)
    name+='.'+'control_service'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,SHADOW/'control_service.py');module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name]

def validate_pack(pack):
    require(type(pack) is dict and set(pack)=={'schema_version','kind','game_id','adapter','files','fields','sources','notes'},'CONTROL_SCHEMA','Unexpected control-pack fields.')
    require(pack['schema_version']==1 and pack['kind']=='game-mod-controls','CONTROL_SCHEMA','Expected control-pack schema 1.')
    slug(pack['game_id']);require(pack['adapter'] in {'ini','shadow-reviewed'},'ADAPTER_UNAVAILABLE','Control packs select reviewed adapters, never executable code.')
    require(type(pack['files']) is dict and len(pack['files'])<=8,'CONTROL_SCHEMA','Choose at most eight game-local configuration files.')
    for ident,path in pack['files'].items():
        slug(ident);safe_relative(path);require(Path(path).suffix.lower() in {'.ini','.cfg','.conf'},'CONTROL_SCHEMA','Only declared configuration files may be edited.')
    require(len({p.casefold() for p in pack['files'].values()})==len(pack['files']),'CONTROL_SCHEMA','Configuration file paths collide.')
    require(type(pack['fields']) is list and len(pack['fields'])<=32,'CONTROL_SCHEMA','At most 32 typed controls are supported.')
    seen=set()
    targets=set()
    for f in pack['fields']:
        require(type(f) is dict and {'id','label','type','file','section','key'}<=set(f) and set(f)<={'id','label','type','file','section','key','min','max','choices'},'CONTROL_SCHEMA','Invalid control field.')
        slug(f['id']);require(f['id'] not in seen,'CONTROL_SCHEMA','Duplicate control ID.');seen.add(f['id'])
        require(f['type'] in {'bool','int','number','enum'} and f['file'] in pack['files'],'CONTROL_SCHEMA','Choose a supported type and declared file.')
        for key in ('label','section','key'):
            require(type(f[key]) is str and 0<len(f[key])<=120 and not any(c in f[key] for c in '\r\n=[]'),'CONTROL_SCHEMA','Use short printable field labels and INI keys.')
        target=(f['file'],f['section'].casefold(),f['key'].casefold());require(target not in targets,'CONTROL_SCHEMA','Control keys collide.');targets.add(target)
        if f['type'] in {'int','number'}:
            require(all(type(f.get(k)) in (int,float) and math.isfinite(f[k]) and abs(f[k])<=1e12 for k in ('min','max')) and f['min']<=f['max'],'CONTROL_SCHEMA','Numeric controls require finite bounds.')
        if f['type']=='enum':require(type(f.get('choices')) is list and 1<=len(f['choices'])<=32 and all(type(x) is str and re.fullmatch(r'[A-Za-z0-9 _.+-]{1,64}',x) for x in f['choices']),'CONTROL_SCHEMA','Choose bounded text options.')
    if pack['adapter']=='ini':require(bool(seen),'CONTROL_SCHEMA','An INI pack needs at least one control.')
    else:require(not pack['files'] and not pack['fields'],'CONTROL_SCHEMA','The reviewed controller owns its setting schema.')
    require(type(pack['sources']) is list and len(pack['sources'])<=16 and all(type(x) is str and x.startswith('https://') and '@' not in x and len(x)<=500 for x in pack['sources']),'CONTROL_SCHEMA','Sources must be public HTTPS links.')
    require(type(pack['notes']) is str and len(pack['notes'])<=1000,'CONTROL_SCHEMA','Notes are too long.')
    _assert_public_metadata(pack)
    return copy.deepcopy(pack)

def ini_template(game_id):
    return {'schema_version':1,'kind':'game-mod-controls','game_id':slug(game_id),'adapter':'ini',
        'files':{'settings':'Mods/Example/settings.ini'},
        'fields':[{'id':'enabled','label':'Enable example mod','type':'bool','file':'settings','section':'General','key':'Enabled'}],
        'sources':[],'notes':'Template only. Replace the example path and key with the original mod documentation, then review locally.'}

def _replace(path,raw):
    fd,name=tempfile.mkstemp(prefix=path.name+'.controls-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

class ModControls:
    def __init__(self,data_dir,workspaces=None):
        if workspaces is None:
            from GameToolGameWorkspaces import GameWorkspaces
            workspaces=GameWorkspaces(data_dir)
        self.data_dir=no_links(Path(data_dir));self.root=self.data_dir/'mod-controls';self.workspaces=workspaces
        self.instances=InstanceRegistry(self.data_dir,workspaces,accepted_adapters=KNOWN_READ_ADAPTERS)
        self._requests={}
    def games(self):
        instances=self.instances.list_public(limit=64)['instances'];result=[]
        for row in self.workspaces.game_rows():
            own=[r for r in instances if r.get('game_id')==row['id']]
            result.append({'game_id':row['id'],'name':row['name'],'manager':row.get('manager'),'instances':own,
                'control_pack_available':(PACKS/(row['id']+'.json')).is_file(),'recipe_available':row['recipe_available'],
                'keybind_pack_available':row.get('keybind_pack_available',False)})
        return {'version':VERSION,'games':result,'registration':'local game-folder selection','game_files_written':False}
    def register_local(self,game_id,game_dir,instance_id=None):
        return self.instances.register_local(instance_id=instance_id or ('game-'+uuid.uuid4().hex[:12]),game_id=game_id,game_dir=Path(game_dir),confirmed=True)
    def _record(self,instance_id):
        record=self.instances._read(instance_id)
        # Reconcile the public definition before using its locally selected path.
        self.instances.inspect(instance_id)
        return record
    def binding_path(self,instance_id):return contained(self.root,'bindings/'+slug(instance_id)+'.json')
    def _binding(self,instance_id):
        path=self.binding_path(instance_id)
        require(path.is_file(),'CONTROL_CONNECTION_REQUIRED','Connect a reviewed controller or control pack for this installation.')
        b=read_json(path,131072);record=self._record(instance_id)
        require(type(b) is dict and b.get('schema_version')==1 and b.get('instance_id')==instance_id and b.get('instance_revision')==record['revision'],'CONTROL_BINDING_STALE','Review this installation connection again.')
        b['pack']=validate_pack(b['pack']);require(b['pack']['game_id']==record['body']['game_id'],'GAME_MISMATCH','Control pack belongs to another game.')
        return b
    def connect_local(self,instance_id,*,workspace=None,pack=None,writes_enabled=False):
        record=self._record(instance_id);game_id=record['body']['game_id']
        if pack is None:pack=read_json(PACKS/(game_id+'.json'),131072)
        pack=validate_pack(pack);require(pack['game_id']==game_id,'GAME_MISMATCH','Control pack belongs to another game.')
        b={'schema_version':1,'instance_id':instance_id,'instance_revision':record['revision'],'pack':pack,'writes_enabled':bool(writes_enabled)}
        if pack['adapter']=='shadow-reviewed':
            require(workspace is not None,'CONTROL_WORKSPACE_REQUIRED','Choose the existing reviewed controller workspace.')
            workspace=no_links(Path(workspace));require(digest(workspace/'graphics_profiles.py')==digest(SHADOW/'graphics_profiles.py'),'UNREVIEWED_CONTROLLER','The controller engine differs from its reviewed source.')
            metadata=read_json(workspace/'graphics-profiles.json',131072);game=no_links(Path(metadata['game_path']));root=Path(record['body']['game_dir'])
            require(game==root or root in game.parents,'GAME_MISMATCH','Controller workspace belongs to another installation.')
            b['workspace']=str(workspace);shadow_module().ControlService(workspace).read()
        else:self._ini_snapshot(record,b)
        path=self.binding_path(instance_id);path.parent.mkdir(parents=True,exist_ok=True)
        with local_lock(self.root,'.connections.lock'):
            if path.exists():
                backup=contained(self.root,'connection-recovery/'+uuid.uuid4().hex+'.json');backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(path.read_bytes())
            atomic_json(path,b)
        return self.inspect(instance_id)
    def _shadow(self,b):
        workspace=no_links(Path(b['workspace']))
        require(digest(workspace/'graphics_profiles.py')==digest(SHADOW/'graphics_profiles.py'),'UNREVIEWED_CONTROLLER','Reviewed controller engine changed.')
        try:return shadow_module().ControlService(workspace)
        except (RuntimeError,ValueError,OSError) as error:raise ModError('CONTROL_STATE_UNAVAILABLE','Open the local controller to resolve its settings location or ownership state.') from error
    def _schema(self,b):
        if b['pack']['adapter']=='ini':return b['pack']['fields']
        legacy=shadow_module();fields=[]
        bounds={'duration':(0,10),'regen':(-1,1),'fov_min':(40,70),'fov_max':(40,70),'width':(640,8192),'height':(640,8192)}
        labels={'profile':'Graphics profile','graphics':'Enable graphics','gameplay':'Enable gameplay loader','multi-skills':'Multi Equip Skills','elven-speed':'Elven Speed','fov':'FOV Extender','dlaa':'Experimental Luma DLAA','nr':'Experimental neural rendering','duration':'Ability duration','regen':'Focus regeneration','fov_min':'Minimum FOV','fov_max':'Maximum FOV','modifier':'Multi-equip modifier','toggle':'Press to toggle','sound':'Equip sound','width':'Render width','height':'Render height'}
        for ident,value in legacy.DEFAULTS.items():
            f={'id':ident,'label':labels[ident],'type':'bool' if type(value) is bool else 'int' if ident in ('width','height') else 'number' if ident in bounds else 'enum'}
            if ident in bounds:f.update(min=bounds[ident][0],max=bounds[ident][1])
            if ident=='profile':f['choices']=['previous','luma']
            if ident=='modifier':f['choices']=list(legacy.KEYS.values())
            fields.append(f)
        return fields
    def _values(self,b,values):
        schema=self._schema(b);require(type(values) is dict and set(values)=={f['id'] for f in schema},'CONTROL_VALUES','Profile settings do not match this control pack.')
        if b['pack']['adapter']=='shadow-reviewed':return shadow_module().validate_values(values)
        out={}
        for f in schema:
            v=values[f['id']];kind=f['type']
            if kind=='bool':require(type(v) is bool,'CONTROL_VALUES','Choose true or false.')
            elif kind in ('int','number'):
                require(type(v) in (int,float) and math.isfinite(v) and f['min']<=v<=f['max'] and (kind!='int' or type(v) is int),'CONTROL_VALUES','Numeric value is outside its declared bounds.')
            else:require(v in f['choices'],'CONTROL_VALUES','Choose a declared setting option.')
            out[f['id']]=v
        return out
    def _ini_snapshot(self,record,b):
        values={};hashes={};raws={};root=Path(record['body']['game_dir'])
        for ident,relative in b['pack']['files'].items():
            path=contained(root,relative);require(path.is_file() and path.stat().st_size<=1048576,'CONFIG_REQUIRED','A declared configuration file is missing or too large.')
            raw=path.read_bytes();require(len(raw)<=1048576,'CONFIG_REQUIRED','Configuration file exceeds its bound.')
            cfg=configparser.ConfigParser(interpolation=None,strict=True);cfg.read_string(raw.decode('utf-8-sig'));raws[ident]=raw;hashes[ident]=hashlib.sha256(raw).hexdigest()
            for f in b['pack']['fields']:
                if f['file']!=ident:continue
                require(cfg.has_option(f['section'],f['key']),'CONFIG_KEY_REQUIRED','A declared control key is absent; no default was invented.')
                v=cfg.get(f['section'],f['key'])
                if f['type']=='bool':v=cfg.getboolean(f['section'],f['key'])
                elif f['type']=='int':v=int(v)
                elif f['type']=='number':v=float(v)
                values[f['id']]=v
        return {'values':self._values(b,values),'hashes':hashes,'raws':raws}
    def _snapshot(self,instance_id):
        record=self._record(instance_id);b=self._binding(instance_id)
        if b['pack']['adapter']=='shadow-reviewed':
            controller=self._shadow(b)
            try:native=controller.read()
            except (RuntimeError,ValueError,OSError) as error:raise ModError('CONTROL_STATE_UNAVAILABLE','Review the local game/controller state before reading settings.') from error
            values=native['values'];hashes={k:v for k,v in native['fingerprint'].items() if k!='native-location'}
            detail={'controller':controller,'native':native};blocked=native['blocked']
        else:
            ini=self._ini_snapshot(record,b);values=ini['values'];hashes=ini['hashes'];detail=ini;blocked=[]
        schema=self._schema(b);schema_revision=object_hash({'adapter':b['pack'],'version':VERSION,'schema':schema})
        revision=object_hash({'instance':record['revision'],'binding':b,'schema':schema_revision,'values':values,'hashes':hashes})
        return {'record':record,'binding':b,'schema':schema,'schema_revision':schema_revision,'revision':revision,'values':values,'hashes':hashes,'detail':detail,'blocked':blocked}
    def inspect(self,instance_id):
        record=self._record(instance_id);inventory=self.instances.inspect(instance_id)
        if not self.binding_path(instance_id).exists():
            return {'instance':inventory['instance'],'inventory':inventory['inventory'],'status':'CONTROL_CONNECTION_REQUIRED','schema':[],'values':{},'revision':object_hash(inventory),'capabilities':{'inspect':True,'profiles':False,'apply':False},'paths_included':False,'evidence_not_instructions':True}
        s=self._snapshot(instance_id);b=s['binding']
        result={'version':VERSION,'instance':inventory['instance'],'inventory':inventory['inventory'],'status':'READY','adapter':b['pack']['adapter'],'schema':s['schema'],'schema_revision':s['schema_revision'],'revision':s['revision'],'values':s['values'],'file_hashes':s['hashes'],'sources':b['pack']['sources'],'notes':b['pack']['notes'],'blocked':s['blocked'],
            'capabilities':{'inspect':True,'profiles':True,'apply':b['writes_enabled'],'manager_handoff':True,'ai_proposals':True},'profiles':[{'profile_id':r['profile_id']} for r in self.profile_rows(instance_id)],'paths_included':False,'game_files_written':False,'runtime_verified':False,'evidence_not_instructions':True}
        _assert_public_metadata(result);return result
    def preview(self,instance_id,changes,revision=None):
        s=self._snapshot(instance_id)
        if revision is not None:require(revision==s['revision'],'CONCURRENT_CHANGE','Applied files changed; refresh and review again.')
        require(type(changes) is dict and len(changes)<=32 and set(changes)<=set(s['values']),'CONTROL_VALUES','Unknown or excessive setting changes.')
        desired=self._values(s['binding'],s['values']|changes)
        return {'instance_id':instance_id,'game_id':s['record']['body']['game_id'],'revision':s['revision'],'desired':desired,'changes':[{'id':k,'before':s['values'][k],'after':v} for k,v in desired.items() if v!=s['values'][k]],'game_files_written':False,'execution':'preview'}
    def _closed(self,s):
        markers=self.instances._definition(s['record']['body']['game_id'])[0]['executable_any']
        names={Path(p).name.casefold() for p in markers}|{'vortex.exe','modorganizer.exe','rhi.exe'}
        if os.name=='nt':
            run=subprocess.run(['tasklist.exe','/FO','CSV','/NH'],capture_output=True,text=True,timeout=8,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
            active={row[0].casefold() for row in csv.reader(io.StringIO(run.stdout)) if row}
        else:
            run=subprocess.run(['ps','-A','-o','comm='],capture_output=True,text=True,timeout=8,check=True);active={Path(x.strip()).name.casefold() for x in run.stdout.splitlines()}
        require(not names&active,'GAME_OR_MANAGER_OPEN','Close the selected game and its mod manager before applying files.')
    def apply_local(self,instance_id,changes,revision):
        s=self._snapshot(instance_id);preview=self.preview(instance_id,changes,revision)
        require(s['binding']['writes_enabled'],'WRITER_NOT_SELECTED','This connection is read-only. Review file ownership locally before enabling writes.')
        if not preview['changes']:return {'status':'NO_CHANGES','game_files_written':False}
        if s['binding']['pack']['adapter']=='shadow-reviewed':
            result=s['detail']['controller'].apply(preview['desired'],s['detail']['native'])
            return {'status':'APPLIED_FILE_VERIFIED','game_files_written':bool(result['changed']),'recovery_available':True,'runtime_verified':False}
        self._closed(s);ident=uuid.uuid4().hex;target=contained(self.root,'transactions/'+ident);target.mkdir(parents=True)
        with local_lock(self.root,'.control-writer.lock'):
            require(self._snapshot(instance_id)['revision']==revision,'CONCURRENT_CHANGE','Files changed before the write lease.')
            written=[]
            with Journal.create(target/'audit.jsonl',{'owner':'ModControls','instance_id':instance_id}) as journal:
                journal.append('operation_intent',{'operation':'controls.apply','revision':revision})
                try:
                    for file_id,raw in s['detail']['raws'].items():
                        backup=target/(file_id+'.before');backup.write_bytes(raw)
                        groups={}
                        for f in s['binding']['pack']['fields']:
                            if f['file']==file_id and f['id'] in {c['id'] for c in preview['changes']}:groups.setdefault(f['section'],{})[f['key']]=str(preview['desired'][f['id']]).lower() if f['type']=='bool' else str(preview['desired'][f['id']])
                        new=raw
                        for section,values in groups.items():new=shadow_module().patch_ini(new,section,values)
                        if new!=raw:
                            path=contained(Path(s['record']['body']['game_dir']),s['binding']['pack']['files'][file_id]);_replace(path,new);written.append((path,raw,hashlib.sha256(new).hexdigest()))
                    require(self._snapshot(instance_id)['values']==preview['desired'],'READBACK_MISMATCH','File readback differs from the requested settings.')
                    result={'status':'APPLIED_FILE_VERIFIED','receipt_id':ident,'game_files_written':bool(written),'recovery_available':True,'runtime_verified':False}
                    journal.append('operation_result',{'result_sha256':object_hash(result)});journal.append('session_closed',{'reason':'completed'});json_new(target/'result.json',result)
                    return result
                except Exception:
                    for path,raw,written_hash in reversed(written):
                        require(digest(path)==written_hash,'RECOVERY_REVIEW_REQUIRED','An external writer changed the file; preserve recovery and review locally.')
                        _replace(path,raw)
                    journal.append('session_cancelled',{'reason':'failed_write_restored'});raise
    def _profile_root(self,instance_id,b=None):
        b=b or self._binding(instance_id)
        return no_links(Path(b['workspace'])/'saved-profiles') if b['pack']['adapter']=='shadow-reviewed' else contained(self.root,'profiles/'+slug(instance_id))
    def profile_rows(self,instance_id):
        root=self._profile_root(instance_id);rows=[]
        if not root.exists():return rows
        paths=sorted(root.glob('*.json'));require(len(paths)<=128,'PROFILE_LIMIT','At most 128 profiles are exposed per installation.')
        for path in paths:
            no_links(path);rows.append({'profile_id':object_hash({'name':path.name,'sha256':digest(path)})[:24],'label':path.stem,'path':path})
        return rows
    def profile(self,instance_id,profile_id):
        rows=[r for r in self.profile_rows(instance_id) if r['profile_id']==profile_id];require(len(rows)==1,'PROFILE_NOT_FOUND','Profile changed or was not found.')
        data=read_json(rows[0]['path'],65536);s=self._snapshot(instance_id)
        require(type(data) is dict and type(data.get('values')) is dict,'CONTROL_VALUES','Unsupported profile format.')
        if s['binding']['pack']['adapter']=='ini':
            require(data.get('kind')=='mod-controls-profile' and data.get('game_id')==s['record']['body']['game_id'] and data.get('instance_id')==instance_id and data.get('schema_revision')==s['schema_revision'],'GAME_MISMATCH','Profile belongs to a different game, installation or control schema.')
        else:require(data.get('kind')=='shadow-war-mod-profile','CONTROL_VALUES','Unsupported legacy controller profile.')
        return {'profile_id':profile_id,'values':self._values(s['binding'],data['values']),'schema_revision':s['schema_revision'],'game_files_written':False}
    def save_profile_local(self,instance_id,profile_name,changes,revision):
        slug(profile_name);s=self._snapshot(instance_id);preview=self.preview(instance_id,changes,revision)
        if s['binding']['pack']['adapter']=='shadow-reviewed':s['detail']['controller'].save_profile(profile_name,preview['desired'])
        else:
            root=self._profile_root(instance_id,s['binding']);root.mkdir(parents=True,exist_ok=True);path=contained(root,profile_name+'.json')
            if path.exists():backup=contained(self.root,'profile-recovery/'+uuid.uuid4().hex+'.json');backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(path.read_bytes())
            atomic_json(path,{'schema_version':1,'kind':'mod-controls-profile','game_id':s['record']['body']['game_id'],'instance_id':instance_id,'schema_revision':s['schema_revision'],'values':preview['desired']})
        return {'status':'PROFILE_SAVED','profiles':[{'profile_id':r['profile_id']} for r in self.profile_rows(instance_id)],'game_files_written':False}
    def prepare_manager_local(self,instance_id,revision):
        s=self._snapshot(instance_id);require(s['revision']==revision,'CONCURRENT_CHANGE','Files changed before export.')
        if s['binding']['pack']['adapter']=='shadow-reviewed':target=s['detail']['controller'].export_vortex(s['detail']['native'])
        else:
            target=contained(self.root,'manager-exports/'+slug(instance_id)+'/'+uuid.uuid4().hex);target.mkdir(parents=True)
            for key,raw in s['detail']['raws'].items():(target/(key+'.config-copy')).write_bytes(raw)
            atomic_json(target/'profile.json',{'schema_version':1,'game_id':s['record']['body']['game_id'],'values':s['values']})
            (target/'READ-ME-FIRST.txt').write_text('Configuration handoff only. Review paths and manager ownership. This is not an automatically deployable mod; no binaries or saves are included.',encoding='utf-8')
            files=list(target.iterdir())
            with zipfile.ZipFile(target/'Manager Files.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
                for path in files:archive.write(path,path.name)
        pointer=contained(self.root,'exports/'+slug(instance_id)+'.json');pointer.parent.mkdir(parents=True,exist_ok=True);atomic_json(pointer,{'path':str(target),'instance_id':instance_id})
        return {'status':'MANAGER_FILES_PREPARED','export_id':object_hash({'instance':instance_id,'path':str(target)})[:24],'game_files_written':False,'manager_deployed':False}
    def export_path_local(self,instance_id):
        pointer=contained(self.root,'exports/'+slug(instance_id)+'.json');require(pointer.is_file(),'EXPORT_REQUIRED','Prepare manager files first.')
        path=no_links(Path(read_json(pointer,8192)['path']));b=self._binding(instance_id)
        allowed=no_links(Path(b['workspace'])/'manager-exports') if b['pack']['adapter']=='shadow-reviewed' else no_links(self.root/'manager-exports'/instance_id)
        require(allowed in path.parents and path.is_dir(),'EXPORT_CHANGED','Prepared export location is unavailable.');return path
    def locations_local(self,instance_id):
        record=self._record(instance_id);root=Path(record['body']['game_dir']);locations={'Game folder':root,'Controller data':self.root}
        if self.binding_path(instance_id).exists():
            b=self._binding(instance_id)
            if b['pack']['adapter']=='shadow-reviewed':
                locations['Saved profiles']=Path(b['workspace'])/'saved-profiles';locations['Controller workspace']=Path(b['workspace']);locations['Mod files']=Path(read_json(Path(b['workspace'])/'graphics-profiles.json',131072)['game_path'])/'plugins'
            else:
                for key,relative in b['pack']['files'].items():locations['Settings: '+key]=contained(root,relative).parent
                locations['Saved profiles']=self._profile_root(instance_id,b)
        return locations
    def requests(self,instance_id):
        slug(instance_id)
        if instance_id not in self._requests:self._requests[instance_id]=ControlAutomation(self,instance_id)
        return self._requests[instance_id]
    def tools_local(self):
        paths={}
        registry=self.data_dir/'tools.json'
        if registry.is_file():
            rows=read_json(registry,1048576)
            if type(rows) is list:
                for row in rows[:256]:
                    if type(row) is dict and row.get('id') in TOOLS and row.get('open_allowed') is True:paths[row['id']]=row.get('path','')
        private=self.root/'tools.json'
        if private.is_file():paths.update(read_json(private,32768).get('paths',{}))
        program=Path(os.environ.get('ProgramFiles','C:/Program Files'));local=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))
        defaults={'rhi':program/'RHI/RHI.exe','vortex':local/'Programs/Vortex/Vortex.exe','mod-organizer-2':program/'Mod Organizer 2/ModOrganizer.exe','steam':Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Steam/steam.exe'}
        return [{'tool_id':key,'name':name,'path':Path(paths.get(key,defaults[key])),'installed':Path(paths.get(key,defaults[key])).is_file(),'interface':'open existing app; deployment remains with its owner'} for key,name in TOOLS.items()]
    def tools_public(self):return {'tools':[{k:v for k,v in row.items() if k!='path'} for row in self.tools_local()],'game_files_written':False}
    def set_tool_local(self,tool_id,path):
        require(tool_id in TOOLS,'CAPABILITY_UNAVAILABLE','Choose a supported connection.')
        path=no_links(Path(path));require(path.is_absolute() and path.is_file() and path.suffix.lower()=='.exe','TOOL_REQUIRED','Choose an existing installed Windows application.')
        target=contained(self.root,'tools.json');target.parent.mkdir(parents=True,exist_ok=True);data=read_json(target,32768) if target.exists() else {'schema_version':1,'paths':{}}
        data['paths'][tool_id]=str(path);atomic_json(target,data);return self.tools_public()
    def client_setup_local(self):
        executable=Path(sys.executable)
        if executable.name.lower()=='pythonw.exe':executable=executable.with_name('python.exe')
        install=ROOT.parent.parent if ROOT.parent.name=='versions' else None
        if install is not None and (install/'Game-Mod-Controls.pyw').is_file():arguments=[str(install/'Game-Mod-Controls.pyw'),'--ai']
        else:arguments=[str(ROOT/'scripts/GameToolAI.py'),'--data-dir',str(self.data_dir),'--workspaces','--allow-requests','stdio']
        return {'mcpServers':{'game-tools-mods':{'command':str(executable),'args':arguments}}}

class ControlAutomation(AutomationService):
    """Existing approval, expiry, idempotency and journal owner; new typed actions."""
    def __init__(self,controls,instance_id):
        super().__init__(controls.data_dir);self.controls=controls;self.instance_id=instance_id
        self.root=contained(self.data_dir,'automation/mod-controls/'+instance_id);self.requests=self.root/'requests'
        self.recipe_hash=self._source_revision()
    def _source_revision(self):return object_hash({'controls':VERSION,'pack':self.controls._binding(self.instance_id)['pack']})
    def _fresh_recipe(self):require(self._source_revision()==self.recipe_hash,'SOURCE_CHANGED','The control pack changed; reopen its requests before continuing.')
    def _normalize(self,operation,arguments):
        require(operation in OPERATIONS,'CAPABILITY_UNAVAILABLE','Unknown mod-control action.')
        fields={'revision'} if operation=='controls.prepare_manager' else {'revision','changes'}|({'profile_name'} if operation=='controls.save_profile' else set())
        require(type(arguments) is dict and set(arguments)==fields,'INVALID_ARGUMENTS','Unexpected mod-control arguments.')
        require(type(arguments['revision']) is str and bool(re.fullmatch('[a-f0-9]{64}',arguments['revision'])),'INVALID_ARGUMENTS','Expected the current observation revision.')
        if 'changes' in arguments:
            require(type(arguments['changes']) is dict and len(arguments['changes'])<=32,'INVALID_ARGUMENTS','Use a bounded setting-change object.')
            for key,value in arguments['changes'].items():
                slug(key);require(type(value) in (bool,int,float,str) and (not isinstance(value,str) or len(value)<=120) and (type(value) is not float or math.isfinite(value)),'INVALID_ARGUMENTS','Only bounded finite scalar setting values are supported.')
        if 'profile_name' in arguments:slug(arguments['profile_name'])
        return copy.deepcopy(arguments)
    def _check_current(self,request):
        self._fresh_recipe();require(request['recipe_sha256']==self.recipe_hash,'SOURCE_CHANGED','Control definition changed.')
        self.controls.preview(self.instance_id,request['arguments'].get('changes',{}),request['arguments']['revision'])
    def _execute(self,request):
        require(not self.cancel.is_set(),'CANCELLED','Cancelled before mod-control dispatch.');a=request['arguments']
        if request['operation']=='controls.apply':return self.controls.apply_local(self.instance_id,a['changes'],a['revision'])
        if request['operation']=='controls.save_profile':return self.controls.save_profile_local(self.instance_id,a['profile_name'],a['changes'],a['revision'])
        return self.controls.prepare_manager_local(self.instance_id,a['revision'])
