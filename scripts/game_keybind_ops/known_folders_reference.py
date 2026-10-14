#!/usr/bin/env python3
"""Copy-only Windows collection for the 17-game V3 task. Python 3.10+, stdlib.

Never edits games, profiles, registry values, cloud settings or source files.
No network, package installation, capture, game launch, background job or registry import.
Output is a NEW directory and ZIP of ORIGINALS, not an installation package.
NieR progression-bearing SlotData files are excluded without --include-nier-slots.
"""
from __future__ import annotations
import argparse
import ctypes
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid
import zipfile

MAX_FILE = 32 * 1024 * 1024
MAX_TOTAL = 192 * 1024 * 1024
MAX_MATCHES = 500
FOLDERS = {
 1:'01_Bayonetta_PC',2:'02_BioShock_2_Remastered',3:'03_BioShock_Infinite',
 4:'04_BioShock_Remastered',5:'05_Control',6:'06_Cyberpunk_2077',7:'07_Devil_May_Cry_5',
 8:'08_DOOM_The_Dark_Ages',9:'09_God_of_War_Ragnarok',10:'10_GTA_V_Enhanced',
 11:'11_Hogwarts_Legacy',12:'12_Middle_earth_Shadow_of_War',13:'13_NieR_Automata',
 14:'14_Path_of_Exile_2',15:'15_Pathfinder_Kingmaker',16:'16_Red_Dead_Redemption_2',17:'17_V_Rising'}
GUIDS = {'documents':'FDD39AD0-238F-46AF-ADB4-6C85480369C7',
 'saved_games':'4C5C32FF-BB9D-43b0-B5B4-2D72E54EAAA4',
 'local':'F1B32785-6FBA-4FCF-9D55-7B8E7F157091',
 'roaming':'3EB685DB-65F9-4CF6-A03A-E3EF65729F3D',
 'locallow':'A520A1A4-1780-4FF6-BD18-167343C5AF16'}
REG_BRANCH = r'HKCU\Software\Owlcat Games\Pathfinder Kingmaker'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def known_folder(guid: str) -> Path:
    """Read the actual Windows Known Folder, including redirected Documents."""
    class GUID(ctypes.Structure):
        _fields_ = [('a',ctypes.c_uint32),('b',ctypes.c_uint16),('c',ctypes.c_uint16),('d',ctypes.c_ubyte*8)]
    g = GUID.from_buffer_copy(uuid.UUID(guid).bytes_le)
    out = ctypes.c_wchar_p()
    shell = ctypes.WinDLL('shell32', use_last_error=True)
    ole = ctypes.WinDLL('ole32', use_last_error=True)
    shell.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID),ctypes.c_uint32,ctypes.c_void_p,ctypes.POINTER(ctypes.c_wchar_p)]
    shell.SHGetKnownFolderPath.restype = ctypes.c_long
    ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole.CoTaskMemFree.restype = None
    hr = shell.SHGetKnownFolderPath(ctypes.byref(g),0,None,ctypes.byref(out))
    if hr != 0:
        raise OSError(f'SHGetKnownFolderPath failed: {hr:#x}')
    try:
        if not out.value:
            raise OSError('Known Folder returned an empty path')
        return Path(out.value)
    finally:
        ole.CoTaskMemFree(ctypes.cast(out,ctypes.c_void_p))


def read_reg_string(subkey: str, name: str):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,subkey,0,winreg.KEY_READ) as key:
        return winreg.QueryValueEx(key,name)[0]


def stable_read(path: Path, limit: int = MAX_FILE) -> bytes:
    """Refuse oversized, special or observably changing source files; never repair."""
    a = path.stat()
    if not stat.S_ISREG(a.st_mode):
        raise ValueError('Not a regular file')
    if a.st_size > limit:
        raise ValueError(f'File exceeds {limit} byte collection limit')
    with path.open('rb') as f:
        first = f.read(limit+1)
    b = path.stat()
    with path.open('rb') as f:
        second = f.read(limit+1)
    c = path.stat()
    identity = lambda s: (s.st_size,s.st_mtime_ns,s.st_ino)
    if len(first)>limit or identity(a)!=identity(b) or identity(b)!=identity(c) or first!=second:
        raise ValueError('Source changed during inspection; no retry or accepted copy')
    return first


def no_link_path(root: Path, path: Path) -> bool:
    """Do not cross links/junctions BELOW an explicitly selected root."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return False
    here = root
    for part in rel.parts:
        here = here / part
        s = here.lstat()
        attrs = getattr(s,'st_file_attributes',0)
        # Cloud placeholders can be reparse points too: skip rather than hydrate/bypass.
        if here.is_symlink() or attrs & getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400):
            return False
    return True


def bounded_glob(root: Path, pattern: str) -> list[Path]:
    """Only bounded, component-wise patterns. No **, recursion or drive-wide scan."""
    if '**' in pattern or any(p in ('..','') for p in pattern.split('/')) or Path(pattern).is_absolute():
        raise ValueError('Unsafe collection pattern')
    paths=[root]
    for component in pattern.split('/'):
        next_paths=[]
        for parent in paths:
            if not parent.is_dir():
                continue
            if any(c in component for c in '*?['):
                # Windows filesystem names are case-insensitive.
                matches=[p for p in parent.iterdir() if fnmatch.fnmatchcase(p.name.casefold(),component.casefold())]
            else:
                exact=parent/component
                matches=[exact] if exact.exists() else []
            for p in matches:
                if no_link_path(root,p):
                    next_paths.append(p)
                else:
                    raise ValueError(f'Link/reparse point below selected root: {p}')
                if len(next_paths)>MAX_MATCHES:
                    raise ValueError('Too many matches; bounded scan stopped')
        paths=next_paths
    return sorted(paths,key=lambda p:str(p).casefold())


class Collector:
    def __init__(self, output_parent: Path, enabled: set[int] | None = None):
        self.enabled=set(FOLDERS) if enabled is None else set(enabled)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        self.output=output_parent/f'V3_Originals_{stamp}_{uuid.uuid4().hex[:8]}'
        # Parent must exist; never create an unexpected user/drive root.
        if not output_parent.is_dir():
            raise ValueError('Output parent does not exist')
        self.output.mkdir(exist_ok=False)
        self.valid: list[Path]=[]
        self.records: list[dict]=[]
        self.total=0
        self.seen=set()
        self.metadata={'kind':'private_originals_not_installable_V3_configs','created_utc':stamp,
           'source_files_modified':False,'registry_values_modified':False,'network_used':False,
           'capture_used':False,'games_launched':False,'include_nier_slots':False,'platform':sys.platform,
           'notice':'Review this private archive before attaching. It can contain account IDs, paths and non-binding preferences.'}

    def note(self,game:int,status:str,**kwargs):
        self.records.append({'game':FOLDERS[game],'status':status,**kwargs})

    def collect(self,game:int,alias:str,root:Path|None,pattern:str):
        if game not in self.enabled:
            return
        if root is None:
            self.note(game,'ROOT_UNRESOLVED',root_alias=alias,pattern=pattern)
            return
        try:
            matches=bounded_glob(root,pattern)
        except (OSError,ValueError) as e:
            self.note(game,'STOPPED_AFFECTED_PATH',root_alias=alias,pattern=pattern,error=str(e))
            return
        if not matches:
            self.note(game,'NOT_FOUND',root_alias=alias,pattern=pattern)
        for path in matches:
            if not path.is_file():
                self.note(game,'NOT_A_FILE',source=str(path));continue
            key=(game,str(path.absolute()).casefold())
            if key in self.seen:
                continue
            self.seen.add(key)
            try:
                data=stable_read(path)
                if self.total+len(data)>MAX_TOTAL:
                    raise ValueError('Total collection byte limit would be exceeded')
                dest=self.output/FOLDERS[game]/'original'/alias/path.relative_to(root)
                dest.parent.mkdir(parents=True,exist_ok=True)
                with dest.open('xb') as f:
                    f.write(data)
                if dest.read_bytes()!=data or stable_read(path)!=data:
                    raise ValueError('Post-copy verification failed; file excluded from ZIP')
                self.valid.append(dest);self.total+=len(data)
                self.note(game,'COPIED_VERIFIED',source=str(path),destination=dest.relative_to(self.output).as_posix(),bytes=len(data),sha256=digest(data))
            except (OSError,ValueError) as e:
                self.note(game,'STOPPED_AFFECTED_FILE',source=str(path),error=str(e))

    def inventory(self,game:int,alias:str,root:Path|None,pattern:str):
        """List ONLY direct filenames/sizes of specific unresolved game folders."""
        if game not in self.enabled:return
        if root is None:
            self.note(game,'ROOT_UNRESOLVED',root_alias=alias,pattern=pattern);return
        try:
            directories=bounded_glob(root,pattern)
            if not directories:self.note(game,'NOT_FOUND',root_alias=alias,pattern=pattern)
            for directory in directories:
                items=[]
                for p in sorted(directory.iterdir(),key=lambda x:x.name.casefold()):
                    if len(items)>=MAX_MATCHES:raise ValueError('Inventory limit exceeded')
                    s=p.lstat()
                    items.append({'name':p.name,'bytes':s.st_size,'modified_ns':s.st_mtime_ns,
                                  'type':'directory' if stat.S_ISDIR(s.st_mode) else 'file_or_link'})
                self.note(game,'DIRECTORY_LIST_ONLY',source_directory=str(directory),items=items,contents_copied=False)
        except (OSError,ValueError) as e:
            self.note(game,'STOPPED_AFFECTED_PATH',root_alias=alias,pattern=pattern,error=str(e))

    def registry(self):
        if 15 not in self.enabled:return
        exe=Path(os.environ['WINDIR'])/'System32'/'reg.exe'
        dest=self.output/FOLDERS[15]/'original'/'Pathfinder_Kingmaker_original.reg'
        verify=dest.with_name('verification_snapshot.reg')
        dest.parent.mkdir(parents=True,exist_ok=True)
        try:
            # Two independent read-only exports detect observable changes. No /y, no import.
            for target in (dest,verify):
                if target.exists():raise ValueError('Refusing existing registry export target')
                result=subprocess.run([str(exe),'export',REG_BRANCH,str(target)],capture_output=True,timeout=15,check=False)
                if result.returncode != 0:
                    self.note(15,'REGISTRY_EXPORT_NOT_AVAILABLE',returncode=result.returncode)
                    return
            data=stable_read(dest)
            if data != stable_read(verify):raise ValueError('Registry changed across snapshots; neither export accepted')
            if not data.decode('utf-16').startswith('Windows Registry Editor Version 5.00'):
                raise ValueError('Unexpected export header')
            if self.total+len(data)>MAX_TOTAL:raise ValueError('Total collection byte limit exceeded')
            self.valid.append(dest);self.total+=len(data)
            self.note(15,'REGISTRY_EXPORTED_VERIFIED',source=REG_BRANCH,destination=dest.relative_to(self.output).as_posix(),bytes=len(data),sha256=digest(data),read_only=True)
        except (OSError,ValueError,subprocess.TimeoutExpired) as e:
            self.note(15,'STOPPED_REGISTRY_EXPORT_NO_RETRY',error=str(e))

    def finish(self) -> Path:
        self.metadata.update({'total_copied_bytes':self.total,'accepted_files':len(self.valid),'records':self.records})
        manifest=self.output/'COLLECTION_MANIFEST.json'
        manifest.write_text(json.dumps(self.metadata,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        readme=self.output/'READ_ME_ORIGINALS.txt'
        readme.write_text('ORIGINAL FILE COPIES ONLY. Do not install or import these as V3 changes.\n'
          'No source file, registry value, device profile or game setting was changed.\n'
          'Check COLLECTION_MANIFEST.json for missing/unresolved/skipped paths.\n'
          'NieR SlotData files are excluded unless explicit opt-in was selected.\n'
          'The registry export may contain non-binding preferences. Keep the bundle private.\n',encoding='utf8')
        accepted=self.valid+[manifest,readme]
        zip_path=self.output.with_suffix('.zip')
        with zipfile.ZipFile(zip_path,'x',compression=zipfile.ZIP_DEFLATED) as z:
            for p in accepted:z.write(p,p.relative_to(self.output).as_posix())
        with zipfile.ZipFile(zip_path) as z:
            if z.testzip() is not None:raise ValueError('Output ZIP CRC test failed')
            for p in accepted:
                if z.read(p.relative_to(self.output).as_posix()) != p.read_bytes():
                    raise ValueError('ZIP byte readback failed')
        return zip_path


def game_roots(steam:Path|None,collector:Collector) -> dict[int,Path]:
    """Read only two game manifests in registered Steam libraries; no whole-drive scan."""
    if steam is None:return {}
    libraries=[steam]
    vdf=steam/'steamapps'/'libraryfolders.vdf'
    if vdf.exists():
        try:
            text=stable_read(vdf,2*1024*1024).decode('utf-8-sig')
            libraries += [Path(p.replace('\\\\','\\')) for p in re.findall(r'"path"\s+"([^"]+)"',text)]
        except (OSError,ValueError,UnicodeError) as e:
            collector.metadata['steam_library_discovery_warning']=str(e)
    found={}
    for appid,game in ((1091500,6),(601150,7)):
        candidates=[]
        for lib in dict.fromkeys(libraries):
            manifest=lib/'steamapps'/f'appmanifest_{appid}.acf'
            if not manifest.is_file():continue
            try:
                text=stable_read(manifest,2*1024*1024).decode('utf-8-sig')
                names=re.findall(r'"installdir"\s+"([^"]+)"',text)
                if len(names)!=1 or '/' in names[0] or '\\' in names[0] or names[0] in ('','.','..'):
                    raise ValueError('Ambiguous or unsafe installdir')
                target=lib/'steamapps'/'common'/names[0]
                if not target.is_dir():continue
                candidates.append(target)
                collector.note(game,'STEAM_MANIFEST_METADATA',appid=appid,build_ids=re.findall(r'"buildid"\s+"([0-9]+)"',text),game_root=str(target))
            except (OSError,ValueError,UnicodeError) as e:
                collector.note(game,'STEAM_MANIFEST_UNRESOLVED',source=str(manifest),error=str(e))
        candidates=list(dict.fromkeys(candidates))
        if len(candidates)==1:found[game]=candidates[0]
        elif len(candidates)>1:collector.note(game,'MULTIPLE_INSTALLS_NO_AUTO_SELECTION',candidates=[str(p) for p in candidates])
    return found


def collect_files(c:Collector,r:dict[str,Path|None],nier:bool=False):
    c.metadata['include_nier_slots']=bool(nier)
    specs=[
      (1,'documents','Bayonetta/system_data'),(1,'steam_user','460790/remote/system_data'),
      (2,'roaming','BioshockHD/Bioshock2/User.ini'),(2,'roaming','My Games/Bioshock Epic HD/Bioshock2/User.ini'),
      (3,'documents','My Games/BioShock Infinite/XGame/Config/XUserOptions.ini'),
      (4,'roaming','BioshockHD/Bioshock/User.ini'),
      (5,'steam_user','870780/remote/preferences_data'),(5,'documents','My Games/Control/Saves/preferences_data'),
      (5,'local','Remedy/Control/Default-Epic-User/preferences/data.chunk'),
      (5,'local','Remedy/Control/Default-Generic-User/preferences/data.chunk'),
      (6,'local','CD Projekt Red/Cyberpunk 2077/UserSettings.json'),
      (6,'cyberpunk','r6/config/inputUserMappings.xml'),(6,'cyberpunk','r6/config/inputContexts.xml'),
      (6,'cyberpunk','engine/config/platform/pc/input_loader.ini'),
      (6,'cyberpunk','r6/cache/inputUserMappings.xml'),(6,'cyberpunk','r6/cache/inputContexts.xml'),
      (6,'cyberpunk','r6/input/*.xml'),(7,'dmc5','dmc5config.ini'),
      (8,'saved_games','id Software/DOOMTheDarkAges/base/DOOMTheDarkAgesConfig.cfg'),
      (8,'saved_games','id Software/DOOMTheDarkAges/base/DOOMTheDarkAgesConfig.local'),
      (9,'saved_games','God of War Ragnarök/*/userpreferences'),
      (9,'saved_games','God of War Ragnarok/*/userpreferences'),
      (10,'documents','Rockstar Games/GTAV Enhanced/Profiles/*/control/user.xml'),
      (10,'documents','Rockstar Games/GTAV Enhanced/Profiles/*/control/user.autosave'),
      (11,'local','Hogwarts Legacy/Saved/Config/WindowsNoEditor/Input.ini'),
      (13,'documents','My Games/NieR_Automata/SystemData.dat'),
      (14,'documents','My Games/Path of Exile 2/poe2_production_Config.ini'),
      (16,'documents','Rockstar Games/Red Dead Redemption 2/Profiles/*/KeyMappings'),
      (17,'locallow','Stunlock Studios/VRising/Settings/v*/InputSettings.json')]
    for game,alias,pattern in specs:c.collect(game,alias,r.get(alias),pattern)
    c.inventory(7,'steam_user',r.get('steam_user'),'601150/remote/win64_save')
    c.inventory(12,'local',r.get('local'),'WB Games/Shadow of War')
    if nier:
        for n in range(3):c.collect(13,'documents',r.get('documents'),f'My Games/NieR_Automata/SlotData_{n}.dat')
    elif 13 in c.enabled:
        c.note(13,'EMBEDDED_SAVE_CONTENT_NOT_COLLECTED',reason='SlotData includes progression; explicit opt-in or manual attachment required.')
        c.inventory(13,'documents',r.get('documents'),'My Games/NieR_Automata')


def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--output-parent',type=Path,default=Path.cwd())
    p.add_argument('--documents',type=Path);p.add_argument('--saved-games',type=Path)
    p.add_argument('--steam-root',type=Path);p.add_argument('--steam-account',help='Explicit numeric Steam userdata folder. Default: active account only, never all accounts.')
    p.add_argument('--cyberpunk-root',type=Path);p.add_argument('--dmc5-root',type=Path)
    p.add_argument('--include-nier-slots',action='store_true',help='Explicitly include all existing SlotData_0/1/2.dat files; these contain gameplay progress.')
    p.add_argument('--no-registry',action='store_true');p.add_argument('--only',help='Optional game numbers, e.g. 6,14,17')
    args=p.parse_args(argv)
    if os.name!='nt':p.error('Run collection on Windows. Non-Windows use is limited to the provided fixture tests.')
    enabled=set(FOLDERS)
    if args.only:
        try:enabled={int(s) for s in args.only.split(',')}
        except ValueError:p.error('--only must contain comma-separated numbers')
        if not enabled or not enabled<=set(FOLDERS):p.error('Game numbers must be 1 through 17')
    if args.steam_account and not args.steam_account.isdigit():p.error('--steam-account must be numeric')
    c=Collector(args.output_parent.absolute(),enabled)
    roots={}
    for alias,guid in GUIDS.items():
        override=args.documents if alias=='documents' else args.saved_games if alias=='saved_games' else None
        try:roots[alias]=override if override else known_folder(guid)
        except OSError as e:roots[alias]=None;c.metadata.setdefault('root_errors',{})[alias]=str(e)
    steam=args.steam_root
    if steam is None:
        try:steam=Path(read_reg_string(r'Software\Valve\Steam','SteamPath'))
        except OSError:pass
    account=args.steam_account
    if account is None:
        try:
            n=int(read_reg_string(r'Software\Valve\Steam\ActiveProcess','ActiveUser'))
            if n>0:account=str(n)
        except (OSError,ValueError):pass
    roots['steam_user']=steam/'userdata'/account if steam and account else None
    installs=game_roots(steam,c)
    roots['cyberpunk']=args.cyberpunk_root or installs.get(6)
    roots['dmc5']=args.dmc5_root or installs.get(7)
    c.metadata['resolved_roots']={k:str(v) if v else None for k,v in roots.items()}
    collect_files(c,roots,args.include_nier_slots)
    if not args.no_registry:c.registry()
    else:c.note(15,'REGISTRY_EXPORT_SKIPPED_BY_OPTION')
    archive=c.finish()
    print(f'Original files copied and verified: {len(c.valid)}')
    print(f'Archive: {archive}')
    print('These are ORIGINALS, not V3 replacements. No source settings were changed.')
    print('Review the private archive and COLLECTION_MANIFEST.json before attaching it.')
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except (OSError,ValueError) as e:
        print(f'Collection stopped: {e}. Existing sources are unchanged; no automatic retry.',file=sys.stderr)
        raise SystemExit(1)
