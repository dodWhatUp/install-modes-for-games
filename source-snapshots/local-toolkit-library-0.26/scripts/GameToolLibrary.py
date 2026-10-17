"""Local game-library metadata. Readers never launch games or modify launchers.

Library settings/tags are owned here; mod recipes, native controls and approvals
retain their existing owners. Unknown launcher history remains unknown.
"""
from __future__ import annotations
import copy
import ctypes
import json
import os
from pathlib import Path
import re
import tempfile
import time
from game_mod_ops.safety import local_lock, no_links, require

VERSION = '0.1.0'
MAX_GAMES = 4096
MAX_BYTES = 4 * 1024 * 1024
SORTS = ('Name', 'Last played', 'Last used in Game Tools', 'Last changed in Game Tools', 'Launcher')
PRESENCE = ('All games', 'Installed', 'Not detected', 'Favorites')

def title_key(value):
    return ''.join(c for c in str(value).casefold() if c.isalnum())

def timestamp(value):
    try:
        result = float(value)
        return result if 0 < result <= time.time() + 86400 else None
    except (ValueError, TypeError, OverflowError):
        return None

def safe_id(value):
    return bool(isinstance(value, str) and re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,119}', value))

def read_text(path, limit=MAX_BYTES):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Metadata file is missing, linked or too large: ' + path.name)
    raw = path.read_bytes()
    if len(raw) > limit: raise ValueError('Metadata grew during reading: ' + path.name)
    return raw.decode('utf-8-sig', errors='strict')

def keyvalues(text):
    """Bounded Valve KeyValues reader; braces/escapes are data, never commands."""
    if len(text) > MAX_BYTES: raise ValueError('Valve metadata is too large')
    tokens = []
    pattern = re.compile(r'\s+|//[^\r\n]*|"(?:\\.|[^"\\])*"|[{}]|[^\s{}"]+')
    pos = 0
    for match in pattern.finditer(text):
        if match.start() != pos: raise ValueError('Invalid Valve metadata token')
        pos = match.end(); token = match.group()
        if token.isspace() or token.startswith('//'): continue
        if token.startswith('"'):
            token = re.sub(r'\\([\\"])', r'\1', token[1:-1])
        tokens.append(token)
        if len(tokens) > 150000: raise ValueError('Valve metadata token limit')
    if pos != len(text): raise ValueError('Invalid Valve metadata ending')
    index = 0
    def block(depth=0, nested=False):
        nonlocal index
        if depth > 24: raise ValueError('Valve metadata nesting limit')
        out = {}
        while index < len(tokens):
            key = tokens[index]; index += 1
            if key == '}':
                if not nested: raise ValueError('Unexpected closing brace')
                return out
            if key == '{' or index == len(tokens): raise ValueError('Missing Valve value')
            value = tokens[index]; index += 1
            if value == '{': value = block(depth + 1, True)
            elif value == '}': raise ValueError('Missing Valve value')
            out[key] = value
        if nested: raise ValueError('Unclosed Valve block')
        return out
    return block()

def value_ci(obj, key, default=None):
    return next((v for k, v in obj.items() if str(k).casefold() == key.casefold()), default) if isinstance(obj, dict) else default

def registry_value(hive, subkey, name):
    if os.name != 'nt': return None
    import winreg
    try:
        with winreg.OpenKey(getattr(winreg, hive), subkey) as key:
            return winreg.QueryValueEx(key, name)[0]
    except OSError:
        return None

def registered_games():
    """Fixed native launcher keys, not a recursive scan of personal folders."""
    if os.name != 'nt': return []
    import winreg
    result = []
    for launcher, root in [('GOG', r'SOFTWARE\GOG.com\Games'),
                           ('GOG', r'SOFTWARE\WOW6432Node\GOG.com\Games'),
                           ('Ubisoft Connect', r'SOFTWARE\Ubisoft\Launcher\Installs'),
                           ('Ubisoft Connect', r'SOFTWARE\WOW6432Node\Ubisoft\Launcher\Installs')]:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root) as parent:
                for i in range(min(winreg.QueryInfoKey(parent)[0], MAX_GAMES)):
                    ident = winreg.EnumKey(parent, i)
                    with winreg.OpenKey(parent, ident) as child:
                        def get(name):
                            try: return winreg.QueryValueEx(child, name)[0]
                            except OSError: return None
                        folder = get('path') or get('InstallDir')
                        if isinstance(folder, str):
                            result.append(dict(launcher=launcher, app_id=ident, path=folder,
                                               name=get('gameName') or Path(folder).name,
                                               executable=get('exe'), evidence='launcher_registry'))
        except OSError: pass
    for root in (r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
                 r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'):
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, root) as parent:
                for i in range(min(winreg.QueryInfoKey(parent)[0], 2048)):
                    ident = winreg.EnumKey(parent, i)
                    with winreg.OpenKey(parent, ident) as child:
                        def get(name):
                            try: return winreg.QueryValueEx(child, name)[0]
                            except OSError: return None
                        name, publisher, folder = get('DisplayName'), get('Publisher'), get('InstallLocation')
                        if (isinstance(folder, str) and isinstance(name, str) and
                            str(publisher).casefold() in {'electronic arts', 'electronic arts, inc.', 'ea'} and
                            name.casefold() not in {'ea app', 'ea desktop', 'origin', 'ea anticheat'}):
                            result.append(dict(launcher='EA / Origin', app_id=ident, path=folder,
                                               name=name, evidence='installed_game_registry'))
        except OSError: pass
    return result

class Discovery:
    def __init__(self, *, steam_roots=None, epic_roots=None, registered=None, xbox_roots=None):
        steam = registry_value('HKEY_CURRENT_USER', r'Software\Valve\Steam', 'SteamPath')
        self.steam_roots = list(steam_roots if steam_roots is not None else
            ([Path(steam)] if steam else [Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'))/'Steam'] if os.name == 'nt' else []))
        self.epic_roots = list(epic_roots if epic_roots is not None else
            [Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData'))/'Epic/EpicGamesLauncher/Data/Manifests'] if os.name == 'nt' else [])
        self.registered = registered
        self.xbox_roots = list(xbox_roots if xbox_roots is not None else
            [Path(letter + ':/XboxGames') for letter in 'CDEFG'] if os.name == 'nt' else [])
    def scan(self, cancel=None):
        self.records=[];self.warnings=[];self.coverage={};self.deadline=time.monotonic()+15
        def ready():
            if cancel is not None and cancel.is_set(): raise InterruptedError('Library refresh cancelled')
            if time.monotonic() > self.deadline: raise TimeoutError('Library refresh reached its time limit')
            if len(self.records) >= MAX_GAMES: raise ValueError('Library record limit reached')
        self.ready=ready
        for launcher, fn in [('Steam',self.steam),('Epic Games',self.epic),('GOG / Ubisoft / EA',self.registry),('Xbox',self.xbox)]:
            try:
                ready();fn();self.coverage[launcher]='checked'
            except InterruptedError: raise
            except (OSError,ValueError,TimeoutError) as exc:
                self.coverage[launcher]='incomplete';self.warnings.append(launcher+': '+str(exc))
        return dict(records=self.records,warnings=self.warnings,coverage=self.coverage,scanned_at=time.time())
    def add(self, launcher, app_id, name, path, *, played=None, evidence='launcher_manifest', executable=None):
        self.ready()
        if not all(isinstance(v,str) and v.strip() for v in (str(app_id),name,str(path))): return
        folder=Path(path)
        if not folder.is_absolute() or str(folder).startswith(('\\\\','//')): return
        key=launcher.casefold()+':'+str(app_id)
        if any(r['key']==key for r in self.records): return
        self.records.append(dict(key=key,launcher=launcher,app_id=str(app_id)[:160],name=name[:200],
            path=str(folder),present=folder.is_dir(),last_played=timestamp(played),
            last_played_source='launcher' if timestamp(played) else None,evidence=evidence,
            executable=str(executable) if executable else None))
    def steam(self):
        libraries=set()
        for root in self.steam_roots:
            root=Path(root)
            if not root.is_dir(): continue
            libraries.add(root)
            file=root/'steamapps/libraryfolders.vdf'
            if file.is_file():
                values=value_ci(keyvalues(read_text(file)),'libraryfolders',{})
                for entry in values.values():
                    folder=value_ci(entry,'path') if isinstance(entry,dict) else entry
                    if isinstance(folder,str) and Path(folder).is_absolute(): libraries.add(Path(folder))
        for library in sorted(libraries):
            for index,file in enumerate(sorted((library/'steamapps').glob('appmanifest_*.acf'))):
                self.ready()
                if index>=MAX_GAMES: raise ValueError('Steam manifest limit')
                try:
                    app=value_ci(keyvalues(read_text(file,512*1024)),'AppState',{})
                    ident=value_ci(app,'appid'); name=value_ci(app,'name'); relative=value_ci(app,'installdir')
                    if str(ident) in {'228980','1070560'}: continue  # shared redistributables
                    if not isinstance(relative,str) or Path(relative).is_absolute() or '..' in Path(relative).parts: continue
                    self.add('Steam',str(ident),name,library/'steamapps/common'/relative,played=value_ci(app,'LastPlayed'))
                except (OSError,ValueError) as exc:
                    self.warnings.append('Steam metadata skipped: '+file.name+' ('+str(exc)+')')
    def epic(self):
        for root in self.epic_roots:
            for index,file in enumerate(sorted(Path(root).glob('*.item'))):
                self.ready()
                if index>=MAX_GAMES: raise ValueError('Epic manifest limit')
                try:
                    app=json.loads(read_text(file,512*1024))
                    if not isinstance(app,dict) or app.get('bIsIncompleteInstall'): continue
                    if app.get('MainGameAppName') and app['MainGameAppName']!=app.get('AppName'): continue
                    self.add('Epic Games',str(app.get('AppName','')),app.get('DisplayName'),app.get('InstallLocation',''),
                             executable=app.get('LaunchExecutable'))
                except (OSError,ValueError) as exc: self.warnings.append('Epic metadata skipped: '+file.name)
    def registry(self):
        for app in self.registered if self.registered is not None else registered_games():
            self.add(app['launcher'],str(app['app_id']),app['name'],app['path'],
                     executable=app.get('executable'),evidence=app.get('evidence','launcher_registry'))
    def xbox(self):
        import xml.etree.ElementTree as ET
        for root in self.xbox_roots:
            if not Path(root).is_dir(): continue
            for index,folder in enumerate(sorted(Path(root).iterdir())):
                self.ready()
                if index>=MAX_GAMES: raise ValueError('Xbox folder limit')
                config=folder/'Content/MicrosoftGame.config'
                if not config.is_file(): continue
                try:
                    xml=ET.fromstring(read_text(config,512*1024)); identity=xml.find('Identity')
                    ident=identity.get('Name') if identity is not None else folder.name
                    exe=xml.find('ExecutableList/Executable')
                    self.add('Xbox',ident,folder.name,folder/'Content',
                             executable=exe.get('Name') if exe is not None else None)
                except (OSError,ValueError,ET.ParseError): self.warnings.append('Xbox metadata skipped: '+folder.name)

class GameLibrary:
    def __init__(self,data_dir):
        self.path=no_links(Path(data_dir)/'game-library.json')
        self.raw=self.path.read_bytes() if self.path.exists() else None
        self.value=json.loads(self.raw.decode('utf-8-sig')) if self.raw is not None else dict(schema_version=1,games={},view={},manual=[],scan={})
        self.validate(self.value)
        self.value.setdefault('view',{});self.value.setdefault('manual',[]);self.value.setdefault('scan',{})
    @staticmethod
    def validate(value):
        require(isinstance(value,dict) and value.get('schema_version')==1,'LIBRARY_SCHEMA','Unsupported game-library format; original retained.')
        require(isinstance(value.get('games'),dict) and len(value['games'])<=MAX_GAMES,'LIBRARY_SCHEMA','Invalid or oversized game library.')
        for ident,row in value['games'].items():
            require(safe_id(ident) and isinstance(row,dict),'LIBRARY_SCHEMA','Invalid game record.')
            require(isinstance(row.get('tags',[]),list) and len(row.get('tags',[]))<=32 and
                    all(isinstance(t,str) and 0<len(t)<=60 for t in row.get('tags',[])),'LIBRARY_SCHEMA','Invalid game tags.')
            require(isinstance(row.get('installations',[]),list) and len(row.get('installations',[]))<=32,'LIBRARY_SCHEMA','Invalid game installations.')
            for install in row.get('installations',[]):
                require(isinstance(install,dict) and all(isinstance(install.get(k),str) for k in ('key','launcher','path')),
                        'LIBRARY_SCHEMA','Invalid installation metadata.')
        require(isinstance(value.get('view',{}),dict) and isinstance(value.get('manual',[]),list),'LIBRARY_SCHEMA','Invalid library preferences.')
    def save(self):
        self.validate(self.value)
        raw=(json.dumps(self.value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        require(len(raw)<=MAX_BYTES,'SIZE_LIMIT','Game library is too large; original retained.')
        if raw==self.raw:return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with local_lock(self.path.parent,'game-library.lock'):
            require((self.path.read_bytes() if self.path.exists() else None)==self.raw,'CONCURRENT_CHANGE','Another window changed the game library. Reopen before editing.')
            fd,temp=tempfile.mkstemp(dir=self.path.parent,prefix='.game-library-')
            try:
                with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
                os.replace(temp,self.path);self.raw=raw
            finally:
                if os.path.exists(temp):os.unlink(temp)
    def edit(self,ident,**changes):
        require(safe_id(ident),'LIBRARY_SCHEMA','Invalid game identifier.')
        old=copy.deepcopy(self.value)
        try:
            row=self.value['games'].setdefault(ident,{})
            row.update(changes);self.save()
        except Exception:
            self.value=old;raise
    def touch(self,ident,kind,when=None):
        require(kind in {'last_used','last_changed','last_seen_running'},'LIBRARY_SCHEMA','Invalid activity type.')
        current=self.value['games'].get(ident,{}).get(kind)
        when=timestamp(when) or time.time()
        if not current or when>current:self.edit(ident,**{kind:when})
    def merge(self,report,catalog_rows):
        old=copy.deepcopy(self.value)
        try:
            games=self.value['games']; known={}
            for row in list(catalog_rows)+[dict(id=i,name=g.get('name',i)) for i,g in games.items() if g.get('name')]:
                known.setdefault(title_key(row['name']),set()).add(row['id'])
            key_owner={v['key']:ident for ident,game in games.items() for v in game.get('installations',[])}
            seen=set()
            for install in report['records']+self.value['manual']:
                key=install['key'];seen.add(key);matches=known.get(title_key(install['name']),set())
                ident=key_owner.get(key)
                if ident is None:
                    ident=next(iter(matches)) if len(matches)==1 else re.sub(r'[^a-z0-9._-]','-',key.casefold())[:119]
                require(safe_id(ident),'LIBRARY_SCHEMA','Invalid launcher game identifier.')
                game=games.setdefault(ident,dict(name=install['name'],tags=[],favorite=False,installations=[]))
                game.setdefault('name',install['name']); previous={v['key']:v for v in game.setdefault('installations',[])}
                # Preserve cached historical launch times if the launcher omits them later.
                prior=previous.get(key,{})
                new={**prior,**install}
                if not new.get('last_played') and prior.get('last_played'):
                    new['last_played']=prior['last_played'];new['last_played_source']=prior.get('last_played_source')
                previous[key]=new;game['installations']=list(previous.values())
                key_owner[key]=ident;known.setdefault(title_key(game['name']),set()).add(ident)
            complete=not report.get('warnings') and all(v=='checked' for v in report['coverage'].values())
            if complete:
                for game in games.values():
                    for install in game.get('installations',[]):
                        if install['key'] not in seen and install.get('evidence')!='manual_folder':install['present']=False
            self.value['scan']={k:copy.deepcopy(v) for k,v in report.items() if k!='records'}
            self.save()
        except Exception:
            self.value=old;raise
    def rows(self,catalog_rows):
        rows={r['id']:copy.deepcopy(r) for r in catalog_rows}
        for ident,record in self.value['games'].items():
            row=rows.setdefault(ident,dict(id=ident,name=record.get('name',ident),recipe_available=False,
                recipe_revision=None,manager=None,source='local_game_library',keybind_pack_available=False))
            row.update({k:copy.deepcopy(v) for k,v in record.items() if k not in {'name'}})
        for row in rows.values():
            installs=row.get('installations',[])
            row['launchers']=sorted({v['launcher'] for v in installs})
            row['installed']=any(v.get('present') for v in installs)
            row['installation']='metadata_detected' if row['installed'] else 'not_detected'
            times=[timestamp(v.get('last_played')) for v in installs]+[timestamp(row.get('last_seen_running'))]
            row['last_played']=max((v for v in times if v),default=None)
            row.setdefault('tags',[]);row.setdefault('favorite',False)
        return list(rows.values())
    @staticmethod
    def query(rows,*,text='',launcher='All launchers',tag='All tags',presence='All games',sort='Name'):
        words=text.casefold().split(); result=[]
        for row in rows:
            hay=' '.join([row['name'],row['id'],*row.get('tags',[]),*row.get('launchers',[])]).casefold()
            if any(word not in hay for word in words):continue
            if launcher!='All launchers' and launcher not in row.get('launchers',[]):continue
            if tag!='All tags' and tag not in row.get('tags',[]):continue
            if presence=='Installed' and not row.get('installed'):continue
            if presence=='Not detected' and row.get('installed'):continue
            if presence=='Favorites' and not row.get('favorite'):continue
            result.append(row)
        field={'Last played':'last_played','Last used in Game Tools':'last_used','Last changed in Game Tools':'last_changed'}.get(sort)
        if field:result.sort(key=lambda r:(-(timestamp(r.get(field)) or 0),r['name'].casefold(),r['id']))
        elif sort=='Launcher':result.sort(key=lambda r:(', '.join(r.get('launchers',[])),r['name'].casefold(),r['id']))
        else:result.sort(key=lambda r:(r['name'].casefold(),r['id']))
        return result
    def add_manual(self,name,folder,launcher='Other'):
        folder=no_links(Path(folder));require(folder.is_dir(),'LIBRARY_SCHEMA','Choose an existing local game folder.')
        require(isinstance(name,str) and bool(name.strip()) and len(name)<=200,'LIBRARY_SCHEMA','Enter a game name.')
        require(isinstance(launcher,str) and 0<len(launcher)<=60,'LIBRARY_SCHEMA','Enter a launcher name.')
        import hashlib
        ident='manual-'+hashlib.sha256(str(folder).casefold().encode()).hexdigest()[:16]
        record=dict(key=ident,launcher=launcher,name=name.strip(),app_id=ident,path=str(folder),
                    present=True,evidence='manual_folder',last_played=None,last_played_source=None,executable=None)
        old=copy.deepcopy(self.value)
        try:
            require(not any(v['key']==ident for v in self.value['manual']),'LIBRARY_SCHEMA','This folder is already in your library.')
            self.value['manual'].append(record);self.merge(dict(records=[],coverage={},warnings=['Manual addition; other detections retained'],scanned_at=time.time()),[])
        except Exception:self.value=old;raise

def foreground_game(rows):
    """Current foreground executable path only; no titles, keys, capture or hooks."""
    if os.name!='nt':return None
    from ctypes import wintypes as W
    u=ctypes.WinDLL('user32',use_last_error=True);k=ctypes.WinDLL('kernel32',use_last_error=True)
    u.GetForegroundWindow.restype=W.HWND;u.GetWindowThreadProcessId.argtypes=[W.HWND,ctypes.POINTER(W.DWORD)]
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
    k.CloseHandle.argtypes=[W.HANDLE]
    pid=W.DWORD();u.GetWindowThreadProcessId(u.GetForegroundWindow(),ctypes.byref(pid))
    handle=k.OpenProcess(0x1000,False,pid.value)
    if not handle:return None
    try:
        buf=ctypes.create_unicode_buffer(32768);size=W.DWORD(len(buf))
        if not k.QueryFullProcessImageNameW(handle,0,buf,ctypes.byref(size)):return None
        exe=Path(buf.value)
    finally:k.CloseHandle(handle)
    if exe.name.casefold() in {'steam.exe','steamwebhelper.exe','epicgameslauncher.exe','upc.exe','eadesktop.exe',
                               'origin.exe','galaxyclient.exe','unitymodmanager.exe','crashreportclient.exe','crashhandler.exe',
                               'crashhandler64.exe','crashpad_handler.exe','launcher.exe','uninstall.exe','setup.exe'}:return None
    candidates=[]
    for row in rows:
        for install in row.get('installations',[]):
            if not install.get('present'):continue
            folder=Path(install['path'])
            try:exe.relative_to(folder)
            except ValueError:continue
            candidates.append((len(str(folder)),row['id']))
    # Nested installs are attributed to the most specific known game folder.
    if not candidates:return None
    length=max(v[0] for v in candidates);ids={i for n,i in candidates if n==length}
    return next(iter(ids)) if len(ids)==1 else None
