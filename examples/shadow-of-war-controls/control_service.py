"""Thin file/settings UI adapter over the existing reviewed profile controller.

No game launch, resident injector, external-manager database edit or save restore.
"""
from __future__ import annotations
from pathlib import Path
import configparser, contextlib, copy, datetime, hashlib, importlib.util, json, math
import os, re, shutil, subprocess, tempfile, zipfile
from mod_resources import resources

VERSION='1.1.0'
MODS={'multi-skills':('Multi Equip Skills','Multi Equip Skills.dll'),
      'elven-speed':('Elven Speed','Elven Speed.dll'),'fov':('FOV Extender','FOV Extender.dll')}
KEYS={'Left Ctrl':'527 0 0','Right Ctrl':'531 0 0','Left Shift':'528 0 0',
      'Right Shift':'532 0 0','Left Alt':'529 0 0','Right Alt':'533 0 0'}
DEFAULTS={'profile':'previous','graphics':True,'gameplay':True,'multi-skills':True,
          'elven-speed':True,'fov':True,'dlaa':False,'nr':False,'duration':2.0,
          'regen':0.0,'fov_min':45.0,'fov_max':60.0,'modifier':'527 0 0',
          'toggle':False,'sound':True,'width':3840,'height':2160}
SETTINGS={'multi-skills':'plugins/config/Multi Equip Skills.ini',
          'elven-speed':'plugins/config/Elven Speed.ini','fov':'plugins/config/FOV Extender.ini',
          'loader':'modloader/Mod Loader.ini','reshade':'ReShade.ini'}

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
def sha(p):
    if not p.is_file():return None
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest().upper()
def read_json(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def json_bytes(v):return (json.dumps(v,indent=2,ensure_ascii=False)+'\n').encode('utf-8')

def native_settings_path(workspace,override=None):
    """Reuse a reviewed physical file across packaged and Desktop launches."""
    binding=Path(workspace)/'control-panel-paths.json'
    if override is not None:
        candidate=Path(override)
    elif binding.is_file():
        if binding.stat().st_size>65536:raise ValueError('The local settings-path binding is too large.')
        obj=read_json(binding)
        if type(obj) is not dict or obj.get('schema')!=1 or not isinstance(obj.get('native_config_path'),str):
            raise ValueError('The local settings-path binding needs review.')
        candidate=Path(obj['native_config_path'])
        if not candidate.is_absolute() or candidate.name.casefold()!='render.cfg':
            raise ValueError('The local settings-path binding must name an absolute render.cfg file.')
    else:
        root=os.environ.get('LOCALAPPDATA')
        if not root:raise RuntimeError('Windows did not provide a local app-data folder. Review the local settings-path binding.')
        candidate=Path(root)/'WB Games/Shadow of War/render.cfg'
    if not candidate.is_file():
        raise RuntimeError('Shadow of War settings were not found at '+str(candidate)+
            '. Review control-panel-paths.json in the controller workspace. No settings file was created or reset.')
    return candidate
def atomic(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix=p.name+'.',suffix='.tmp',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(name,p)
    finally:
        if os.path.exists(name):os.unlink(name)

def private_child(base,relative):
    p=base/relative
    if not p.resolve().is_relative_to(base.resolve()):raise ValueError('Private output leaves the control workspace.')
    for part in [p,*p.parents]:
        if part==base.parent:break
        if part.is_symlink() or (hasattr(part,'is_junction') and part.is_junction()):raise ValueError('Linked private outputs are refused.')
    return p

def validate_values(values):
    if type(values) is not dict or set(values)!=set(DEFAULTS):raise ValueError('Profile fields do not match this control version.')
    v=copy.deepcopy(values)
    if v['profile'] not in ('previous','luma'):raise ValueError('Choose RenoDX or the Luma trial.')
    for k in ('graphics','gameplay','multi-skills','elven-speed','fov','dlaa','nr','toggle','sound'):
        if type(v[k]) is not bool:raise ValueError(f'{k}: use an On/Off value.')
    for k,lo,hi in [('duration',0,10),('regen',-1,1),('fov_min',40,70),('fov_max',40,70)]:
        try:n=float(v[k])
        except (TypeError,ValueError):raise ValueError(f'{k}: enter a number.')
        if isinstance(v[k],bool) or not math.isfinite(n) or not lo<=n<=hi:raise ValueError(f'{k}: use {lo} to {hi}.')
        v[k]=n
    if v['fov_min']>v['fov_max']:raise ValueError('Minimum FOV must not exceed maximum FOV.')
    if v['modifier'] not in KEYS.values():raise ValueError('Choose one of the supported modifier keys.')
    for k in ('width','height'):
        try:n=int(v[k])
        except (TypeError,ValueError):raise ValueError(f'{k}: enter a whole number.')
        if str(v[k])!=str(n) or not 640<=n<=8192:raise ValueError(f'{k}: use a whole number from 640 to 8192.')
        v[k]=n
    if v['profile']=='previous' and (v['dlaa'] or v['nr']):raise ValueError('DLAA and DLSS 5 require the Luma profile.')
    if v['nr'] and not v['dlaa']:raise ValueError('DLSS 5 requires Luma DLAA enabled.')
    return v

def patch_ini(raw,section,changes):
    """Change only selected keys; retain unknown keys, comments, BOM and newlines."""
    bom=raw.startswith(b'\xef\xbb\xbf');text=raw.decode('utf-8-sig')
    lines=text.splitlines(keepends=True);newline='\r\n' if '\r\n' in text else '\n'
    found={k:0 for k in changes};active=False;end=None
    for i,line in enumerate(lines):
        header=re.fullmatch(r'\s*\[([^]]+)\]\s*(?:\r?\n)?',line)
        if header:
            if active:end=i
            active=header[1].casefold()==section.casefold()
            if active and end is not None:raise ValueError('Duplicate settings section: '+section)
            continue
        if not active:continue
        end=i+1
        for key,val in changes.items():
            m=re.match(r'^([ \t]*'+re.escape(key)+r'[ \t]*=[ \t]*)(.*?)(\r?\n)?$',line,re.I)
            if m:
                found[key]+=1
                comment=re.search(r'\s+[;#].*$',m[2])
                lines[i]=m[1]+str(val)+(comment[0] if comment else '')+(m[3] or '')
    if any(n>1 for n in found.values()):raise ValueError('Duplicate controlled INI key.')
    missing=[f'{k} = {changes[k]}{newline}' for k,n in found.items() if not n]
    if missing:
        if end is None:
            if lines and not lines[-1].endswith(('\n','\r')):lines[-1]+=newline
            lines.extend([f'{newline}[{section}]{newline}',*missing])
        else:
            if end and not lines[end-1].endswith(('\n','\r')):lines[end-1]+=newline
            lines[end:end]=missing
    return (b'\xef\xbb\xbf' if bom else b'')+''.join(lines).encode('utf-8')

class ControlService:
    def __init__(self,workspace,backend=None,native=None):
        self.base=Path(workspace).resolve()
        if backend is None:
            if os.name!='nt':raise RuntimeError('The real game controller requires Windows; use --demo for isolated UI checks.')
            p=self.base/'graphics_profiles.py'
            spec=importlib.util.spec_from_file_location('shadow_reviewed_profiles',p)
            backend=importlib.util.module_from_spec(spec);spec.loader.exec_module(backend)
        self.b=backend
        self.native=native_settings_path(self.base,native)

    def files(self):
        result={k:self.b.path(p) for k,p in SETTINGS.items()}
        result.update({'native':self.native,'state':self.base/'graphics-profile-state.json',
            'previous-config':self.base/'profile-configs/previous/ReShade.ini',
            'luma-config':self.base/'profile-configs/luma/ReShade.ini'})
        return result

    def fingerprint(self):
        result={k:sha(p) for k,p in self.files().items()}
        result['loader-enabled']=self.b.loader_state()
        for component in self.b.M['components']:
            result['component-'+component['id']]=self.b.module_state(component)
        result['ownership-manifest']=sha(self.base/'graphics-profiles.json')
        result['native-path-binding']=sha(self.base/'control-panel-paths.json')
        result['native-location']=str(self.native)
        return result

    def read(self):
        b=self.b;b.validate()
        cfg={k:b.config_read(p) for k,p in self.files().items() if k in SETTINGS}
        loader=cfg['loader'];v=copy.deepcopy(DEFAULTS)
        v.update({'profile':b.state()['profile'],'graphics':b.module_state(b.module('graphics')),
            'gameplay':b.loader_state(),'duration':cfg['elven-speed'].getfloat('General','DurationMult',fallback=2),
            'regen':cfg['elven-speed'].getfloat('General','RegenRateMult',fallback=0),
            'fov_min':cfg['fov'].getfloat('General','MinFOV',fallback=45),
            'fov_max':cfg['fov'].getfloat('General','MaxFOV',fallback=60),
            'modifier':cfg['multi-skills'].get('General','ToggleSkillEquip',fallback='527 0 0'),
            'toggle':cfg['multi-skills'].getboolean('General','ToggleBehavior',fallback=False),
            'sound':cfg['multi-skills'].getboolean('General','PlaySound',fallback=True)})
        for key,(_,dll) in MODS.items():
            v[key]=b.module_state(b.module(key)) and loader.getboolean('Plugins',dll,fallback=True)
        v['dlaa']=v['profile']=='luma' and cfg['reshade'].get('Luma','SRUserType',fallback='0')=='2'
        v['nr']=v['profile']=='luma' and b.module_state(b.module('nr'))
        native=self.native.read_text(encoding='utf-8-sig')
        for k,key in [('width','ScreenWidth16by9'),('height','ScreenHeight16by9')]:
            m=re.search(r'"'+key+r'"\s+"([0-9.]+)"',native)
            if not m:raise ValueError('Missing native render size: '+key)
            v[k]=int(float(m[1]))
        blockers=[]
        try:b.closed()
        except RuntimeError as e:blockers.append(str(e))
        return {'values':v,'fingerprint':self.fingerprint(),
            'blocked':blockers,'workspace':str(self.base),'game':str(b.G),
            'graphics_owner':'RHI + reviewed local profiles','gameplay_owner':'Reviewed local controller',
            'runtime_warning':'Luma crashed in the NVIDIA driver on exit; trial and neural delivery remain unverified.'}

    def preview(self,desired,snapshot):
        v=validate_values(desired);current=snapshot['values']
        return [f'{key}: {current[key]} -> {v[key]}' for key in DEFAULTS if current[key]!=v[key]]

    def apply(self,desired,snapshot):
        v=validate_values(desired);b=self.b;b.UNDO=[]
        if not self.preview(v,snapshot):return {'changed':False,'message':'No changes to apply.'}
        with open(self.base/'profile-switch.lock','a+b') as lock:
            lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
            b.msvcrt.locking(lock.fileno(),b.msvcrt.LK_NBLCK,1)
            try:
                b.closed();b.validate()
                actual=self.fingerprint()
                if actual!=snapshot['fingerprint']:raise RuntimeError('Files changed since Refresh. Refresh and review before applying.')
                saved=b.snapshot()
                # The legacy engine snapshots its own LOCALAPPDATA view. A Desktop
                # launch may use a different view from the reviewed native file.
                native_backup=saved/'controller-native-settings'
                atomic(native_backup/'render.cfg',self.native.read_bytes())
                atomic(native_backup/'location.json',json_bytes({'source':str(self.native)}))
                b.select_profile(v['profile'])
                b.enable('graphics',v['graphics']);b.gameplay(v['gameplay'])
                changed_mods={k for k in MODS if v[k]!=snapshot['values'][k]}
                for key in changed_mods:b.enable(key,v[key])
                def ini(key,section,changes):
                    p=self.files()[key];old=p.read_bytes() if p.exists() else b''
                    new=patch_ini(old,section,changes)
                    if new!=old:b.write(p,new)
                if changed_mods:ini('loader','Plugins',{MODS[k][1]:str(v[k]).lower() for k in changed_mods})
                ini('elven-speed','General',{'RegenRateMult':format(v['regen'],'.6f'),'DurationMult':format(v['duration'],'.6f')})
                ini('fov','General',{'MinFOV':format(v['fov_min'],'.6f'),'MaxFOV':format(v['fov_max'],'.6f')})
                ini('multi-skills','General',{'ToggleSkillEquip':v['modifier'],'ToggleBehavior':str(v['toggle']).lower(),'PlaySound':str(v['sound']).lower()})
                if v['profile']=='luma':
                    b.enable('nr',v['nr']);ini('reshade','Luma',{'SRUserType':2 if v['dlaa'] else 0})
                    ini('reshade','ADDON',{'LoadFromDllMain':'renodx-dlss5.addon64' if v['nr'] else ''})
                    ini('reshade','RenoDX.DLSS5',{'NR':1 if v['nr'] else 0})
                old=self.native.read_bytes();new=old
                for key,n in [('ScreenWidth16by9',v['width']),('ScreenHeight16by9',v['height'])]:
                    new,count=re.subn(rb'("'+key.encode()+rb'"\s+")[0-9.]+(")',lambda m:m[1]+f'{n:.6f}'.encode()+m[2],new)
                    if count!=1:raise ValueError('Ambiguous native render setting: '+key)
                if old!=new:b.write(self.native,new)
                b.validate()
                after=self.read()['values']
                if after!=v:raise RuntimeError('Readback does not match requested settings; restoring transaction.')
                receipt={'schema':1,'kind':'shadow-war-mod-profile','values':v,'applied_utc':now(),'recovery':str(saved)}
                b.write(self.base/'last-applied-profile.json',json_bytes(receipt))
                history=self.base/'control-panel-history.jsonl'
                b.write(history,(history.read_bytes() if history.exists() else b'')+json.dumps(receipt).encode()+b'\n')
                b.UNDO=[]
                return {'changed':True,'recovery':str(saved),'message':'Applied and verified. Settings remain after this window closes.'}
            except Exception:
                failures=[]
                for undo in reversed(b.UNDO):
                    try:undo()
                    except Exception as e:failures.append(str(e))
                b.UNDO=[]
                if failures:raise RuntimeError('Recovery needs review: '+'; '.join(failures))
                raise
            finally:b.msvcrt.locking(lock.fileno(),b.msvcrt.LK_UNLCK,1)

    def profile_names(self):return sorted(p.stem for p in (self.base/'saved-profiles').glob('*.json'))
    def profile_path(self,name):
        name=name.strip()
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _.-]{0,63}',name) or '..' in name or name.endswith(('.', ' ')):
            raise ValueError('Use a profile name with letters, numbers, spaces, dash or underscore.')
        if name.upper().split('.')[0] in {'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}:
            raise ValueError('That name is reserved by Windows.')
        return private_child(self.base,Path('saved-profiles')/f'{name}.json')
    def save_profile(self,name,values):
        v=validate_values(values);p=self.profile_path(name)
        if p.exists():
            backup=self.base/'profile-file-recovery'/stamp()/p.name;backup.parent.mkdir(parents=True);shutil.copy2(p,backup)
        atomic(p,json_bytes({'schema':1,'kind':'shadow-war-mod-profile','values':v,'saved_utc':now()}))
        return p
    def load_profile(self,name):
        p=self.profile_path(name)
        if p.stat().st_size>65536:raise ValueError('Profile is too large.')
        obj=read_json(p)
        if obj.get('schema')!=1 or obj.get('kind')!='shadow-war-mod-profile':raise ValueError('Unsupported profile file.')
        return validate_values(obj['values'])

    def mod_resources(self):return resources(self.b.G,self.base,self.native)

    def manager_executable(self):
        saved=self.base/'manager-tools.json'
        if saved.is_file():
            obj=read_json(saved);candidate=Path(obj.get('manager_executable',''))
            if candidate.is_absolute() and candidate.suffix.casefold()=='.exe' and candidate.is_file():return candidate
        for root,relative in [('LOCALAPPDATA','Programs/Vortex/Vortex.exe'),
                              ('ProgramFiles','Black Tree Gaming Ltd/Vortex/Vortex.exe'),
                              ('ProgramFiles','Vortex/Vortex.exe')]:
            if os.environ.get(root):
                candidate=Path(os.environ[root])/relative
                if candidate.is_file():return candidate
        return None

    def set_manager_executable(self,path):
        path=Path(path)
        if not path.is_absolute() or path.suffix.casefold()!='.exe' or not path.is_file():
            raise ValueError('Choose an existing installed manager .exe file.')
        target=private_child(self.base,'manager-tools.json')
        obj=read_json(target) if target.exists() else {'schema':1}
        obj['manager_executable']=str(path);atomic(target,json_bytes(obj));return path

    def latest_manager_export(self):
        root=private_child(self.base,'manager-exports')
        if not root.exists():return None
        candidates=[]
        for path in root.glob('Vortex-handoff-*'):
            if path.is_dir() and not path.is_symlink() and not (path/'INCOMPLETE.txt').exists():
                private_child(self.base,path.relative_to(self.base))
                if (path/'handoff-manifest.json').is_file():candidates.append(path)
        return max(candidates,key=lambda p:p.name) if candidates else None

    def export_vortex(self,snapshot):
        """Private handoff of pinned original archives, never deployment or migration."""
        specs=read_json(self.base/'control-export-sources.json')
        if type(specs) is not list or len(specs)!=4:raise ValueError('Export source list needs review.')
        sources=[]
        for entry in specs:
            name=entry['file']
            if Path(name).name!=name or '/' in name or '\\' in name:raise ValueError('Invalid source archive name.')
            source=private_child(self.base,Path('downloads')/name)
            if source.is_symlink() or not source.resolve().is_relative_to((self.base/'downloads').resolve()):raise ValueError('Linked export source refused.')
            if sha(source)!=entry['sha256']:raise ValueError('Original archive changed: '+name)
            sources.append((entry,source))
        if self.fingerprint()!=snapshot['fingerprint']:raise RuntimeError('Files changed; Refresh before exporting.')
        root=private_child(self.base,'manager-exports')
        if root.is_symlink():raise ValueError('Linked export directory refused.')
        root.mkdir(exist_ok=True)
        target=root/('Vortex-handoff-'+stamp());target.mkdir()
        try:
            archive_dir=target/'original-archives';archive_dir.mkdir()
            for i,(entry,source) in enumerate(sources,1):
                copy=archive_dir/f'{i:02d}-{source.name}';shutil.copy2(source,copy)
                if sha(copy)!=entry['sha256']:raise RuntimeError('Archive copy verification failed.')
            for key in ('loader','multi-skills','elven-speed','fov'):
                p=self.files()[key];q=target/'current-settings'/SETTINGS[key]
                q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
            atomic(target/'profile.json',json_bytes({'schema':1,'kind':'shadow-war-mod-profile','values':snapshot['values']}))
            atomic(target/'handoff-manifest.json',json_bytes({'schema':1,'exported_utc':now(),
                'mode':'prepared-only-no-deployment','game':'Middle-earth: Shadow of War',
                'archives':[e for e,_ in sources],'values':snapshot['values'],
                'graphics_owner':'Keep graphics in RHI/reviewed local profile; no graphics binaries exported',
                'proprietary_game_files_included':False,'campaign_saves_included':False,
                'vortex_import_tested':False,'existing_game_changed':False}))
            guide='''SHADOW OF WAR - VORTEX HANDOFF (PREPARED, NOT DEPLOYED)

This folder preserves four original mod archives, their hashes, the current
gameplay INIs and a portable profile.json. It does not install Vortex, import
into Vortex, modify its database, purge the game or activate another loader.
No game EXE, original Bink runtime, UHD texture pack or campaign save is included.

1. Use Vortex with ChemBoy1's Shadow of War extension (Steam/GOG support).
   https://www.nexusmods.com/site/mods/375
2. Back up/review the existing game before choosing Vortex ownership. The
   extension can auto-install DLL/Packet loaders. Keep ONLY one DLL loader.
   Preserve the pinned ReaperAnon loaderfix version and original Bink forwarder.
3. Original archives are numbered loader, Multi Equip Skills, Elven Speed, FOV.
   Import from file, inspect the extension's selected mod type and destination,
   and verify x64 / plugins / plugins/config paths before deployment.
4. Current INIs are recovery/reference files, not a blindly installable mod.
   Reconcile them after the original mods are deployed. Do not package/overwrite
   the game's original bink2w64.dll from another computer or another version.
5. Graphics stay under RHI and the reviewed local profile. Do not let Vortex
   overwrite dxgi.dll, ReShade.ini, RenoDX, Luma or neural components.
6. A real handover must retire the local controller's writing ownership for
   migrated components. Until then, do not apply changes from both managers.

This handoff is export-verified, NOT a tested Vortex import or one-click migration.
Installed disabled trials remain disabled. The Luma exit fault is unresolved.
Keep this private: original authors retain their binaries and licenses.
'''
            guide+='\nPACKAGE ZIP: the outer ZIP is a transport/backup container. Extract it and import the four original archives individually; do not deploy the outer ZIP as a mod.\n'
            (target/'READ-ME-FIRST.txt').write_text(guide,encoding='utf-8')
            if self.fingerprint()!=snapshot['fingerprint']:raise RuntimeError('Files changed during export; Refresh and prepare again.')
            package=target/'Shadow of War Manager Files.zip'
            payload=[p for p in target.rglob('*') if p.is_file()]
            with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                for p in payload:archive.write(p,p.relative_to(target))
            with zipfile.ZipFile(package) as archive:
                if archive.testzip() is not None:raise RuntimeError('Manager package verification failed.')
            return target
        except Exception as e:
            (target/'INCOMPLETE.txt').write_text(str(e),encoding='utf-8')
            raise

class DemoService:
    """Isolated UI fixture: no game/controller paths or external process actions."""
    def __init__(self,base):self.base=Path(base);self.base.mkdir(parents=True,exist_ok=True);self.values=copy.deepcopy(DEFAULTS)
    def read(self):return {'values':copy.deepcopy(self.values),'fingerprint':{},'blocked':[],
        'workspace':str(self.base),'game':'Isolated fixture — no real game','runtime_warning':'Luma exit failure recorded; experimental features are off.'}
    preview=ControlService.preview
    profile_names=ControlService.profile_names
    profile_path=ControlService.profile_path
    save_profile=ControlService.save_profile
    load_profile=ControlService.load_profile
    manager_executable=ControlService.manager_executable
    set_manager_executable=ControlService.set_manager_executable
    latest_manager_export=ControlService.latest_manager_export
    def mod_resources(self):return resources(self.base/'fixture-game/x64',self.base,self.base/'fixture-native/render.cfg')
    def apply(self,v,snapshot):self.values=validate_values(v);atomic(self.base/'demo-applied.json',json_bytes(self.values));return {'changed':True,'message':'Fixture applied; no real game was modified.'}
    def export_vortex(self,snapshot):
        p=self.base/'manager-exports'/('Vortex-handoff-'+stamp());p.mkdir(parents=True)
        atomic(p/'profile.json',json_bytes(snapshot['values']))
        atomic(p/'handoff-manifest.json',json_bytes({'mode':'isolated-demo-no-real-mods'}))
        (p/'READ-ME-FIRST.txt').write_text('Isolated demo only. No real mod archives or game files.')
        with zipfile.ZipFile(p/'Shadow of War Manager Files.zip','w') as archive:
            archive.write(p/'profile.json','profile.json')
        return p
