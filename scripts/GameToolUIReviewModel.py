"""Parallel UI review model. Private review writes; explicit Apply reuses its owner."""
from __future__ import annotations
import copy,hashlib,json,os,re,shutil,uuid,zipfile
from datetime import datetime,timezone
from pathlib import Path
from GameToolModControls import ModControls
from GameToolUnified import atomic_json
from game_mod_ops.safety import ModError,contained,digest,no_links,read_json,require,slug,copy_new

VERSION='0.2.0'
MANAGERS={'vortex':'Vortex','mod-organizer-2':'Mod Organizer 2','rhi':'RHI','azeron':'Azeron Software','rewasd':'reWASD','rtss':'RTSS','obs':'OBS Studio','spreadsheet':'Spreadsheet app','custom':'Another installed app','folder':'Portable folder'}
TARGETS={'mods':['vortex','mod-organizer-2','rhi','custom','folder'],'tools':['folder','custom'],
         'profiles':['azeron','rewasd','rtss','vortex','mod-organizer-2','custom','folder'],
         'reports':['spreadsheet','obs','custom','folder'],'files':['folder','custom']}
PAGES={'mods':'Mod Controls','tools':'Programs & connections','profiles':'Profiles & overlays','reports':'Reports & diagnostics','files':'App files & recovery','review':'Compare & feedback'}

def utc():return datetime.now(timezone.utc).isoformat()
def folder_snapshot(path,limit=128):
    path=no_links(Path(path));require(path.is_dir(),'LOCATION_UNAVAILABLE','The selected folder is unavailable.')
    rows=[];truncated=False
    with os.scandir(path) as entries:
        for entry in entries:
            if len(rows)>=limit:truncated=True;break
            if entry.is_symlink():continue
            info=entry.stat(follow_symlinks=False)
            if getattr(info,'st_file_attributes',0)&0x400:continue
            rows.append({'name':entry.name,'kind':'folder' if entry.is_dir(follow_symlinks=False) else 'file','bytes':None if entry.is_dir(follow_symlinks=False) else info.st_size,'modified_ns':info.st_mtime_ns})
    return {'entries':sorted(rows,key=lambda r:(r['kind']!='folder',r['name'].casefold())),'truncated':truncated,'observed_utc':utc(),'recursive':False}

def file_delta(before,after):
    left={r['name']:r for r in (before or {}).get('entries',[])};right={r['name']:r for r in after['entries']}
    return {'added':sorted(set(right)-set(left)),'removed':sorted(set(left)-set(right)),
        'changed':sorted(k for k in set(left)&set(right) if left[k]!=right[k]),'partial':bool(after['truncated'] or (before or {}).get('truncated'))}

class ReviewModel:
    def __init__(self,source_data,review_root,install_root=None,controls=None,view_name='view.json'):
        self.source_data=no_links(Path(source_data));self.root=no_links(Path(review_root));self.install_root=no_links(Path(install_root)) if install_root else None
        require(self.root!=self.source_data and self.source_data not in self.root.parents and self.root not in self.source_data.parents,'SEPARATE_ROOT_REQUIRED','Choose a separate parallel-review data folder.')
        require(view_name in {'view.json','view-mods.json','view-files.json'},'REVIEW_STATE','Choose a known preview entry scope.')
        self.controls=controls or ModControls(self.source_data);self.view_path=self.root/view_name
        for row in self.controls.instances.list_public(limit=64)['instances']:
            if 'game_id' not in row:continue
            record=self.controls.instances._read(row['instance_id']);paths=[Path(record['body']['game_dir'])]
            if self.controls.binding_path(row['instance_id']).is_file():
                binding=self.controls._binding(row['instance_id'])
                if binding.get('workspace'):paths.append(Path(binding['workspace']))
            for path in paths:
                require(self.root!=path and self.root not in path.parents and path not in self.root.parents,'SEPARATE_ROOT_REQUIRED','Parallel files must stay outside existing game and controller folders.')
        self.view=read_json(self.view_path,262144) if self.view_path.is_file() else {'schema_version':1,'page':'mods','game_id':None,'instance_id':None,'hidden':{},'drafts':{},'manager':'vortex','theme':'Light'}
        require(type(self.view) is dict and self.view.get('schema_version')==1,'REVIEW_STATE','Review state requires version 1.')
        for key,value in {'page':'mods','hidden':{},'drafts':{},'manager':'vortex','theme':'Light'}.items():self.view.setdefault(key,value)
        self.snapshots={};self.latest_export=None
    def save_view(self):
        self.root.mkdir(parents=True,exist_ok=True);atomic_json(self.view_path,self.view)
    def games(self):return self.controls.games()['games']
    def instances(self,game_id):return next((r['instances'] for r in self.games() if r['game_id']==game_id),[])
    def inspect(self,instance):return self.controls.inspect(instance)
    def preview(self,instance,changes,revision):return self.controls.preview(instance,changes,revision)
    def apply_current(self,instance,changes,revision):return self.controls.apply_local(instance,changes,revision)
    def save_profile(self,instance,name,changes,revision):
        name=slug(name);preview=self.preview(instance,changes,revision);state=self.inspect(instance)
        folder=contained(self.root,'profiles/'+slug(instance));folder.mkdir(parents=True,exist_ok=True);target=contained(folder,name+'.json')
        if target.exists():copy_new(target,folder/(name+'.previous-'+uuid.uuid4().hex[:8]+'.json'),digest(target))
        atomic_json(target,{'schema_version':1,'kind':'game-tools-ui-review-profile','instance_id':instance,'game_id':state['instance']['game_id'],'schema_revision':state['schema_revision'],'values':preview['desired'],'saved_utc':utc(),'applied':False})
        return target
    def profile_rows(self,instance):
        rows=[{'id':'source:'+r['profile_id'],'label':r['label']+' (current app)','source':True,'profile_id':r['profile_id']} for r in self.controls.profile_rows(instance)]
        root=contained(self.root,'profiles/'+slug(instance))
        if root.is_dir():
            for p in sorted(root.glob('*.json'))[:128]:
                if '.previous-' not in p.name:rows.append({'id':'review:'+p.stem,'label':p.stem+' (parallel preview)','source':False,'path':p})
        return rows
    def load_profile(self,instance,profile_id):
        row=next((r for r in self.profile_rows(instance) if r['id']==profile_id),None);require(row is not None,'PROFILE_REQUIRED','Select an available profile.')
        if row['source']:return self.controls.profile(instance,row['profile_id'])['values']
        value=read_json(row['path'],65536);state=self.inspect(instance)
        require(value.get('instance_id')==instance and value.get('game_id')==state['instance']['game_id'] and value.get('schema_revision')==state['schema_revision'],'PROFILE_MISMATCH','The profile belongs to another installation or schema.')
        return self.preview(instance,value['values'],state['revision'])['desired']
    def tools(self):
        rows=self.controls.tools_local();saved=self.root/'programs.json'
        overrides=read_json(saved,32768) if saved.is_file() else {}
        program=Path(os.environ.get('ProgramFiles','C:/Program Files'));program86=Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))
        defaults={'azeron':program/'Azeron/Azeron Software/Azeron Software.exe','rewasd':program/'reWASD/reWASD.exe','rtss':program86/'RivaTuner Statistics Server/RTSS.exe','obs':program/'obs-studio/bin/64bit/obs64.exe','spreadsheet':program/'Microsoft Office/root/Office16/EXCEL.EXE'}
        for key,path in defaults.items():rows.append({'tool_id':key,'name':MANAGERS[key],'path':path,'installed':path.is_file(),'interface':'open existing app; native file support stays with its owner'})
        if 'custom' in overrides:rows.append({'tool_id':'custom','name':MANAGERS['custom'],'path':Path(overrides['custom']),'installed':Path(overrides['custom']).is_file(),'interface':'explicitly located existing program'})
        for row in rows:
            if row['tool_id'] in overrides:row['path']=no_links(Path(overrides[row['tool_id']]));row['installed']=row['path'].is_file()
        return rows
    def locate_program(self,tool_id,path):
        require(tool_id in MANAGERS and tool_id!='folder','PROGRAM_REQUIRED','Choose a supported program.')
        path=no_links(Path(path));require(path.is_absolute() and path.is_file() and path.suffix.lower()=='.exe','PROGRAM_REQUIRED','Choose an existing installed Windows application.')
        target=self.root/'programs.json';self.root.mkdir(parents=True,exist_ok=True);saved=read_json(target,32768) if target.exists() else {};saved[tool_id]=str(path);atomic_json(target,saved)
    def resources(self,page,instance=None):
        rows=[]
        def add(ident,label,path,origin='Current app'):
            p=no_links(Path(path));rows.append({'id':ident,'label':label,'path':p,'exists':p.exists(),'kind':'folder' if p.is_dir() else 'file','origin':origin})
        if page=='mods' and instance:
            for i,(label,path) in enumerate(self.controls.locations_local(instance).items()):add('mod-'+str(i),label,path)
        elif page=='tools':
            for row in self.tools():add(row['tool_id'],row['name'],row['path'],'Installed program')
            add('source-programs','Shared tool connections',self.source_data/'tools.json')
        elif page=='profiles':
            for ident,label,relative in [('keymaps','Keymap documents','keymap-documents'),('overlays','Overlay assets','overlay-assets'),('keybinds','Game keybindings','keybinds'),('maps','Overlay groups','overlay-groups.json'),('selection','Overlay selection','overlay-selection.ini')]:add(ident,label,self.source_data/relative)
            if instance:
                for i,(label,path) in enumerate(self.controls.locations_local(instance).items()):
                    if 'profile' in label.casefold():add('profile-'+str(i),label,path)
            add('parallel-profiles','Parallel preview profiles',self.root/'profiles','Parallel preview')
        elif page=='reports':
            for ident,label,relative in [('reports','Saved reports','reports'),('sessions','Session records','sessions'),('crashes','Crash evidence','crash-evidence'),('diagnostics','Diagnostics','diagnostics')]:add(ident,label,self.source_data/relative)
        elif page=='files':
            add('source-data','Current shared data',self.source_data)
            if self.install_root:
                add('current-app','Current app and launchers',self.install_root);add('recovery','Current app recovery',self.install_root/'recovery');add('install-record','Current installation record',self.install_root/'install.json')
            add('parallel-data','Parallel preview data',self.root,'Parallel preview');add('exports','Parallel exports',self.root/'exports','Parallel preview')
        else:add('feedback','Saved review feedback',self.root/'feedback.json','Parallel preview')
        saved=self.root/'locations.json'
        if saved.is_file():
            for row in read_json(saved,32768).get(page,[]):add(row['id'],row['label'],row['path'],'Parallel preview connection')
        return rows
    def add_location(self,page,path):
        require(page in PAGES,'LOCATION_SCOPE','Choose a known page.');path=no_links(Path(path));require(path.is_absolute() and path.is_dir(),'LOCATION_REQUIRED','Choose an existing folder.')
        saved=self.root/'locations.json';self.root.mkdir(parents=True,exist_ok=True);value=read_json(saved,32768) if saved.is_file() else {};rows=value.setdefault(page,[])
        require(len(rows)<32,'LOCATION_LIMIT','At most 32 selected extra locations per page are supported.')
        rows.append({'id':'custom-'+uuid.uuid4().hex[:12],'label':path.name or str(path),'path':str(path)});atomic_json(saved,value)
    def refresh_files(self,resource):
        path=no_links(resource['path']);folder=path if path.is_dir() else path.parent
        observation=folder_snapshot(folder);key=str(folder);delta=file_delta(self.snapshots.get(key),observation);self.snapshots[key]=observation
        return {'resource':resource['label'],'folder':str(folder),'observation':observation,'delta':delta,'game_files_written':False}
    def _sources(self,instance,state):
        binding=self.controls._binding(instance);snapshot=self.controls._snapshot(instance);sources=[]
        if binding['pack']['adapter']=='shadow-reviewed':
            workspace=no_links(Path(binding['workspace']));specs=read_json(workspace/'control-export-sources.json',65536)
            require(type(specs) is list and len(specs)==4,'EXPORT_SOURCE_REVIEW','The reviewed four original archives are required.')
            for i,row in enumerate(specs,1):
                name=row['file'];require(Path(name).name==name and '/' not in name and '\\' not in name,'EXPORT_SOURCE_REVIEW','Invalid reviewed archive name.')
                path=contained(workspace,'downloads/'+name);require(digest(path).upper()==row['sha256'].upper(),'SOURCE_CHANGED','A reviewed original archive changed.')
                sources.append(('original-archives/'+f'{i:02d}-'+name,path,digest(path)))
            for key in ('loader','multi-skills','elven-speed','fov'):
                path=snapshot['detail']['controller'].files()[key];sources.append(('applied-settings/'+key+'.ini',path,digest(path)))
        else:
            record=snapshot['record']['body']
            for key,relative in binding['pack']['files'].items():
                path=contained(Path(record['game_dir']),relative);sources.append(('applied-settings/'+key+Path(relative).suffix,path,digest(path)))
        return sources
    def export_settings(self,instance,manager,changes,revision):
        require(manager in TARGETS['mods'],'MANAGER_REQUIRED','Choose a supported mod handoff destination.')
        preview=self.preview(instance,changes,revision);state=self.inspect(instance);sources=self._sources(instance,state)
        require(sum(p.stat().st_size for _,p,_ in sources)<=512*1024*1024,'EXPORT_LIMIT','The selected local export exceeds its copy bound.')
        target=contained(self.root,'exports/'+slug(instance)+'/'+uuid.uuid4().hex);target.mkdir(parents=True)
        try:
            for relative,path,sha in sources:copy_new(path,contained(target,relative),sha)
            atomic_json(target/'DRAFT-PROFILE.json',{'kind':'game-tools-ui-review-profile','game_id':state['instance']['game_id'],'instance_id':instance,'schema_revision':state['schema_revision'],'values':preview['desired'],'applied':False})
            guide=('Prepared for '+MANAGERS[manager]+'.\n\nOriginal archives and current settings are separate from DRAFT-PROFILE.json.\n'
                'Import original archives individually using the selected program and exact game support.\n'
                'This outer ZIP is a transport container, not an installable mod. No automatic deployment or manager database edit.\n'
                'Graphics remain with their existing RHI/reviewed-profile owner. Do not activate another loader or overwrite a proxy.\n'
                'The draft is not applied. Review manager support and ownership before a real handover.\n')
            (target/'READ-ME-FIRST.txt').write_text(guide,encoding='utf-8')
            require(self.inspect(instance)['revision']==revision,'CONCURRENT_CHANGE','Source files changed during export. Preserve this folder and refresh before using it.')
            entries=[{'path':p.relative_to(target).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size} for p in target.rglob('*') if p.is_file()]
            manifest={'kind':'parallel-ui-review-handoff','game_id':state['instance']['game_id'],'manager':manager,'created_utc':utc(),'source_revision':revision,'files':entries,'applied':False,'manager_deployed':False,'saves_included':False}
            atomic_json(target/'HANDOFF-MANIFEST.json',manifest)
            package=target/'Manager Files.zip'
            with zipfile.ZipFile(package,'x',compression=zipfile.ZIP_DEFLATED) as archive:
                for p in target.rglob('*'):
                    if p.is_file() and p!=package:archive.write(p,p.relative_to(target).as_posix())
            with zipfile.ZipFile(package) as archive:
                require(archive.testzip() is None,'EXPORT_READBACK','Export ZIP verification failed.')
                for row in entries:require(hashlib.sha256(archive.read(row['path'])).hexdigest()==row['sha256'],'EXPORT_READBACK','Export bytes differ.')
            self.latest_export=target;atomic_json(self.root/'latest-export.json',{'path':str(target),'manager':manager,'instance_id':instance});return {'folder':str(target),'files':len(entries),'manager':MANAGERS[manager],'deployed':False}
        except Exception:
            (target/'INCOMPLETE.txt').write_text('Preparation did not complete. Refresh and inspect before use.',encoding='utf-8');raise
    def export_resource(self,resource,manager):
        require(manager in MANAGERS,'MANAGER_REQUIRED','Choose a destination program.')
        path=no_links(resource['path']);require(path.is_file() and path.suffix.casefold() in {'.json','.ini','.cfg','.csv','.md','.txt','.html'} and path.stat().st_size<=8*1024*1024,'EXPORT_SCOPE','Select one supported saved file of at most eight MiB; folders and program binaries are not exported.')
        require(path.name.casefold() not in {'config.toml','.env','auth.json','credentials.json','install.json','tools.json'},'EXPORT_SCOPE','This application/connection file is available through its folder link, not manager export.')
        target=contained(self.root,'exports/resource-'+uuid.uuid4().hex);target.mkdir(parents=True);sha=digest(path);copy_new(path,target/path.name,sha)
        atomic_json(target/'HANDOFF-MANIFEST.json',{'source_label':resource['label'],'manager':manager,'sha256':sha,'native_import_supported':False,'deployed':False});self.latest_export=target;return {'folder':str(target),'manager':MANAGERS[manager],'native_import_supported':False,'deployed':False}
    def feedback(self,text,verdict):
        require(verdict in {'Undecided','Like this direction','Needs changes'} and type(text) is str and len(text)<=16000,'REVIEW_NOTE','Use a short review note.')
        self.root.mkdir(parents=True,exist_ok=True);target=self.root/'feedback.json'
        atomic_json(target,{'version':VERSION,'verdict':verdict,'notes':text,'saved_utc':utc(),'adopted':False,'page':self.view.get('page'),'game_id':self.view.get('game_id')});return target
