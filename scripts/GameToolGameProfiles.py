"""Saved game runtime setups over existing Overlay/Studio owners.

Activation selects already published assets. No native/game writer, game launch,
input injection, rendering, mod application or provider auto-arm exists here.
"""
from __future__ import annotations
import configparser, copy, ctypes, hashlib, json, os
from pathlib import Path
import time, uuid
import GameToolOverlay as overlay

VERSION = "0.2.0"
LAUNCHER = 'Unified Game Tools APP LAUNCHER.cmd'

def fingerprint(value): return overlay.sha(overlay.encode(value))

def resolved_file(path):
    """Resolve the existing opened file, including packaged-app redirection."""
    path=overlay.no_links(path)
    if os.name!='nt': return path.resolve(strict=True)
    from ctypes import wintypes as w
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    k.CreateFileW.restype=w.HANDLE
    k.GetFinalPathNameByHandleW.argtypes=[w.HANDLE,w.LPWSTR,w.DWORD,w.DWORD]
    k.GetFinalPathNameByHandleW.restype=w.DWORD;k.CloseHandle.argtypes=[w.HANDLE]
    h=k.CreateFileW(str(path),0x80000000,7,None,3,0,None)
    if h==ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
    try:
        b=ctypes.create_unicode_buffer(32768);n=k.GetFinalPathNameByHandleW(h,b,len(b),0)
        overlay.require(0<n<len(b),'Cannot resolve existing settings file')
        return overlay.no_links(b.value[4:] if b.value.startswith('\\\\?\\') else b.value)
    finally:k.CloseHandle(h)

def ini(path):
    raw=overlay.read(path,65536)
    text=raw.decode('utf-16') if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else raw.decode('utf-8-sig')
    result=configparser.ConfigParser(interpolation=None,strict=True);result.read_string(text)
    return result

def studio_settings(path):
    file=resolved_file(path);c=ini(file);slots=[]
    for n in range(1,min(12,c.getint('General','SlotCount',fallback=4))+1):
        s='Slot'+str(n)
        if c.getboolean(s,'Enabled',fallback=False):
            slots.append({'slot':n,'key':c.get(s,'Key',fallback=''),'mode':c.get(s,'Mode',fallback=''),
                          'source':c.get(s,'Source',fallback=''),'file':c.get(s,'File',fallback='')})
    return {'file':str(file),'sha256':overlay.sha(overlay.read(file,65536)),
            'enabled':c.getboolean('General','Enabled',fallback=True),'slots':slots}

def runtime_status(settings_path,pid,now=None):
    """Accept only a fresh receipt from the exact app-owned native process."""
    try:
        c=ini(Path(settings_path).parent/'runtime-status.ini')['Runtime']
        now=time.time() if now is None else now
        overlay.require(c.getint('Schema')==1 and c.getint('PID')==pid,'Different Studio owner')
        overlay.require(0<=now-c.getfloat('AtUnix')<=4,'Studio heartbeat expired')
        overlay.require(c.get('SettingsSHA256')==overlay.sha(overlay.read(settings_path,65536)),'Saved settings changed; restart Studio')
        overlay.require(os.path.normcase(c.get('SettingsFile'))==os.path.normcase(str(settings_path)),'Different settings owner')
        return {'fresh':True,'enabled':c.getboolean('Enabled'),'triggers':c.getint('BoundTriggers'),
          'overlay_trigger':c.getboolean('OverlayTrigger'),'route_enabled':c.getboolean('RouteEnabled'),
          'settings_file':c.get('SettingsFile'),'settings_sha256':c.get('SettingsSHA256'),
          'route_path':c.get('RoutePath'),'load_error':c.get('LoadError','')}
    except (OSError,ValueError,KeyError,configparser.Error)as error:
        return {'fresh':False,'reason':'Studio readiness not confirmed: '+str(error)}

def empty():
    return {'schema_version':1,'revision':0,'profiles':[],
      'options':{'enabled':False,'restore_on_open':False,'automatic_game_switch':False},'active_profile_id':None}

def validate(v):
    overlay.fields(v,'schema_version revision profiles options active_profile_id')
    overlay.require(v['schema_version']==1 and type(v['revision'])is int and v['revision']>=0,'Profile schema')
    overlay.fields(v['options'],'enabled restore_on_open automatic_game_switch')
    overlay.require(all(type(x)is bool for x in v['options'].values()),'Automatic options must be booleans')
    overlay.require(type(v['profiles'])is list and len(v['profiles'])<=128,'Profile count limit')
    ids=set()
    for p in v['profiles']:
        overlay.require(type(p)is dict,'Invalid saved profile')
        if p.get('provider')=='rewasd':
            import GameToolRewasd as rewasd
            overlay.fields(p,'id name game_id game_name provider native automatic saved_at')
            for k in ('id','game_id'):overlay.token(p[k])
            overlay.label(p['name']);overlay.label(p['game_name']);rewasd.validate(p['native'])
            overlay.require(p['automatic']is False,'Native automatic switching is owned by reWASD Autodetect')
            overlay.require(p['id']not in ids and type(p['saved_at'])is int,'Duplicate profile or invalid date')
            ids.add(p['id']);continue
        overlay.fields(p,'id name game_id group_id keymap_id keymap_revision source_sha256 selection appearance_sha256 automatic saved_at')
        for k in ['id','game_id','group_id','keymap_id']:overlay.token(p[k])
        overlay.label(p['name']);overlay.require(p['id']not in ids,'Duplicate profile');ids.add(p['id'])
        for k in ['keymap_revision','source_sha256','appearance_sha256']:overlay.digest(p[k])
        overlay.fields(p['selection'],'layer context view')
        overlay.token(p['selection']['layer']);overlay.token(p['selection']['context'])
        overlay.require(p['selection']['view']in overlay.VIEWS and type(p['automatic'])is bool,'Profile selection')
        overlay.require(type(p['saved_at'])is int,'Profile date')
    autos=[p['game_id']for p in v['profiles']if p['automatic']]
    overlay.require(len(autos)==len(set(autos)),'One automatic profile per game')
    overlay.require(v['active_profile_id']is None or v['active_profile_id']in ids,'Active profile missing')
    return v

class Profiles:
    def __init__(self,directory):
        self.directory=overlay.no_links(directory);self.root=overlay.no_links(self.directory/'runtime-profiles')
        self.path=self.root/'profiles.json';self.store=overlay.Store(directory)
        from GameToolRewasd import Native
        self.rewasd=Native(directory)
    def games(self):
        value,_=self.store.load();idx=overlay.validate_store(value)
        rows={g['id']:g['label']for g in idx['games'].values()}
        from GameToolGameWorkspaces import RecipeCatalog
        for g in RecipeCatalog(self.directory).game_rows():rows.setdefault(g['id'],g['name'])
        for p in self.load()[0]['profiles']:
            if p.get('provider')=='rewasd':rows.setdefault(p['game_id'],p['game_name'])
        return rows
    def capture_rewasd(self,game,game_name,name,path,device_name,device_id='',slot=1,profile_id=None):
        p={'id':profile_id or 'profile-'+uuid.uuid4().hex,'name':name,'game_id':game,'game_name':game_name,
          'provider':'rewasd','native':self.rewasd.capture(path,device_name,device_id,slot),
          'automatic':False,'saved_at':int(time.time())}
        candidate=empty();candidate['profiles']=[p];validate(candidate)
        return p
    def load(self):
        v=validate(overlay.decode(overlay.read(self.path)))if self.path.exists()else empty()
        return v,fingerprint(v)
    def save(self,value,expected):
        validate(value);self.root.mkdir(parents=True,exist_ok=True)
        lock=overlay.no_links(self.root/'edit.lock')
        with lock.open('xb'):pass
        pending=None
        try:
            old,current=self.load();overlay.require(current==expected,'Profiles changed; refresh before saving')
            value=copy.deepcopy(value);value['revision']=old['revision']+1;validate(value)
            if self.path.exists():
                history=overlay.no_links(self.root/'history');history.mkdir(exist_ok=True)
                backup=history/(current+'.json')
                if not backup.exists():
                    with backup.open('xb')as out:out.write(overlay.read(self.path))
            pending=self.path.with_name('profiles.pending-'+uuid.uuid4().hex)
            with pending.open('xb')as out:out.write(overlay.encode(value));out.flush();os.fsync(out.fileno())
            overlay.require(self.load()[1]==expected,'Concurrent profile change')
            os.replace(pending,self.path);pending=None
            overlay.require(self.load()[0]==value,'Profile readback mismatch')
            return value
        finally:
            if pending and pending.exists():pending.unlink()
            lock.unlink()
    def capture(self,game,name,profile_id=None):
        from GameToolKeymapBuilder import SourceLibrary
        from GameToolKeymapDocument import fingerprint as map_hash
        from GameToolOverlayAppearance import effective,policy
        value,_=self.store.load();idx=overlay.validate_store(value)
        overlay.require(game in idx['games'],'Select an existing game')
        assoc=sorted((a for a in idx['associations'].values()if a['game_id']==game),key=lambda a:(-a['priority'],a['id']))
        overlay.require(bool(assoc),'Connect the gameplay executable in Overlays first')
        group=idx['groups'][value['preferences']['overrides'].get(game,assoc[0]['default_group'])]
        doc=SourceLibrary(self.directory).current(game);overlay.require(doc is not None,'Publish this game map first')
        selection=copy.deepcopy(value['preferences']['selections'].get(game,{'layer':'Unknown','context':'gameplay','view':'Combined'}))
        return {'id':profile_id or 'profile-'+uuid.uuid4().hex,'name':name,'game_id':game,'group_id':group['id'],
          'keymap_id':group['keymap_id'],'keymap_revision':idx['keymaps'][group['keymap_id']]['revision'],
          'source_sha256':map_hash(doc),'selection':selection,'appearance_sha256':fingerprint(effective(policy(value,SourceLibrary(self.directory).documents()),game)),
          'automatic':True,'saved_at':int(time.time())}
    def put(self,profile,expected):
        v,_=self.load()
        # Selecting a new default for one game preserves its other named setups.
        for p in v['profiles']:
            if profile['automatic']and p['game_id']==profile['game_id']:p['automatic']=False
        v['profiles']=[p for p in v['profiles']if p['id']!=profile['id']]+[copy.deepcopy(profile)]
        return self.save(v,expected)
    def check(self,profile):
        if profile.get('provider')=='rewasd':
            try:self.rewasd.check(profile['native']);return []
            except (OSError,ValueError)as error:return [str(error)]
        from GameToolKeymapBuilder import SourceLibrary
        from GameToolKeymapDocument import fingerprint as map_hash
        from GameToolOverlayAppearance import effective,policy
        from GameToolControlsPlanner import native_status
        problems=[];value,_=self.store.load();idx=overlay.validate_store(value);p=profile
        group=idx['groups'].get(p['group_id']);lib=SourceLibrary(self.directory);doc=lib.current(p['game_id'])
        if not group or (group['game_id'],group['keymap_id'])!=(p['game_id'],p['keymap_id']):problems.append('Saved Overlay group no longer matches')
        keymap=idx['keymaps'].get(p['keymap_id'])
        if not keymap or keymap['revision']!=p['keymap_revision']:problems.append('Native contract changed; review this profile')
        if not doc or map_hash(doc)!=p['source_sha256']:problems.append('Published map source changed; save an updated profile')
        if fingerprint(effective(policy(value,lib.documents()),p['game_id']))!=p['appearance_sha256']:problems.append('Appearance changed; save an updated profile')
        if group:
            assets=[idx['assets'][x]for x in group['asset_ids']]
            if not any(x['context']==p['selection']['context']and x['view']==p['selection']['view']for x in assets):problems.append('Saved context/view has no published images')
            for asset in assets:self.store.asset(asset)
        if keymap and os.name=='nt':
            rows=native_status(keymap,Path(os.environ['APPDATA'])/'Azeron Software/Storage/DevicesStorage')
            if not rows or any(x['state']!='match'for x in rows):problems.append('Azeron profile files differ or are unavailable; open Azeron to review')
        return problems
    def activate(self,profile_id,expected):
        v,current=self.load();overlay.require(current==expected,'Profiles changed; refresh')
        p=next(x for x in v['profiles']if x['id']==profile_id)
        problems=self.check(p);overlay.require(not problems,'; '.join(problems))
        if p.get('provider')=='rewasd':
            # Selecting/restoring a controller setup never applies native input
            # or displays an Azeron map for an unrelated device.
            before,pin=self.store.load()
            before['preferences'].update(enabled=False,display=False);self.store.write(before,pin)
            v['active_profile_id']=profile_id;v['options']['enabled']=True
            return self.save(v,expected)
        before,pin=self.store.load();value=copy.deepcopy(before);prefs=value['preferences']
        prefs.update(enabled=True,display=True,display_target='studio')
        prefs['overrides'][p['game_id']]=p['group_id'];prefs['selections'][p['game_id']]=copy.deepcopy(p['selection'])
        # Appearance is pinned, not re-rendered or overwritten by activation.
        self.store.write(value,pin)
        v['active_profile_id']=profile_id
        v['options']['enabled']=True
        try:return self.save(v,expected)
        except Exception:
            # Outcome is explicit. Do not blind-restore over another owner.
            raise overlay.OverlayError('Overlay selection changed, but saving active profile failed; refresh status before retrying')
    def deactivate(self,expected):
        v,pin=self.load();overlay.require(pin==expected,'Profiles changed; refresh')
        value,revision=self.store.load();value['preferences'].update(enabled=False,display=False)
        self.store.write(value,revision);v['active_profile_id']=None;v['options']['enabled']=False
        return self.save(v,expected)
    def match(self,exe):
        import ntpath
        value,_=self.store.load();idx=overlay.validate_store(value)
        # Reuse exact foreground matching/ambiguity rules, without native data.
        shadow=copy.deepcopy(value);shadow['preferences']['enabled']=True
        chosen=overlay.choose(shadow,{'exe':exe,'at':time.monotonic(),'own':False})
        if chosen.get('selection_scope')!='association':return None
        v,_=self.load()
        return next((p for p in v['profiles']if p['automatic']and p['game_id']==chosen.get('game_id')),None)

def launcher_bytes(install):
    import GameToolUnified as unified
    value=unified.read_install(install);unified.verify_current(install,value)
    def quote(p):
        s=str(p);overlay.require(not any(c in s for c in '"%!\r\n'),'Unsupported launcher path')
        return '"'+s+'"'
    return ('@echo off\r\nsetlocal DisableDelayedExpansion\r\nstart "" '+quote(value['pythonw'])+' -B '+quote(Path(install)/'Start-UnifiedTools.pyw')+'\r\n').encode('utf-8')

def startup_entry(install,enabled,folder):
    """One fixed, owned Startup entry. Never changes other startup programs."""
    directory=overlay.no_links(folder);target=directory/LAUNCHER;raw=launcher_bytes(install)
    if target.exists():overlay.require(overlay.read(target)==raw,'Existing Startup entry has another owner; preserve it')
    if enabled and not target.exists():
        with target.open('xb')as out:out.write(raw)
    elif not enabled and target.exists():target.unlink()
    return target.exists()

def startup_folder():
    overlay.require(os.name=='nt','Windows startup is unavailable in this environment')
    b=ctypes.create_unicode_buffer(32768)
    overlay.require(ctypes.windll.shell32.SHGetFolderPathW(None,7,None,0,b)==0,'Startup folder unavailable')
    return overlay.no_links(b.value)
