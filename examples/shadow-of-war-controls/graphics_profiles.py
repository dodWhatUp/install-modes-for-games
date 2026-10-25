"""Closed-game, hash-owned profile switching. This module never launches a game."""
from pathlib import Path
import argparse, configparser, contextlib, datetime, hashlib, json, msvcrt, os, shutil, subprocess, sys

BASE=Path(__file__).parent
M=json.loads((BASE/'graphics-profiles.json').read_text(encoding='utf-8-sig'))
G=Path(M['game_path'])
OFF='.gametools-off'
UNDO=[]
HASHCACHE={}

def digest(p):
    if not p.is_file():return None
    st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
    if key not in HASHCACHE:
        h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
        HASHCACHE[key]=h.hexdigest().upper()
    return HASHCACHE[key]
def safe_path(root,rel):
    p=root/rel
    if not p.resolve().is_relative_to(root.resolve()): raise RuntimeError('Managed path leaves game folder')
    for item in [p,*p.parents]:
        if item==root.parent: break
        if item.is_symlink() or (hasattr(item,'is_junction') and item.is_junction()): raise RuntimeError('Linked game paths are refused')
    return p
def path(rel):return safe_path(G,rel)
def component_path(c):return safe_path(G.parent if c.get('root')=='install' else G,c['file'])
def state(): return json.loads((BASE/'graphics-profile-state.json').read_text())
def atomic_write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.switch-tmp')
    if tmp.exists(): raise RuntimeError(f'Temporary path already exists: {tmp.name}')
    tmp.write_bytes(data)
    os.replace(tmp,p)
def write(p,data):
    previous=p.read_bytes() if p.exists() else None
    atomic_write(p,data)
    UNDO.append(lambda: atomic_write(p,previous) if previous is not None else p.unlink())
def move(a,b):
    if b.exists(): raise RuntimeError(f'Destination already exists: {b.name}')
    a.rename(b)
    UNDO.append(lambda:b.rename(a))
def module_state(c):
    a=component_path(c); b=Path(str(a)+OFF)
    if a.exists() and b.exists(): raise RuntimeError(f'Both enabled and disabled copies exist: {c["name"]}')
    candidate=a if a.exists() else b
    if not candidate.exists(): raise RuntimeError(f'Missing file: {c["name"]}')
    if digest(candidate) not in c.get('allowed_hashes',[c['sha256']]): raise RuntimeError(f'Changed binary: {c["name"]}. Review the update before switching.')
    return a.exists()
def module(id): return next(c for c in M['components'] if c['id']==id)
def enable(id,on):
    c=module(id); before=module_state(c)
    if before!=on:
        a=component_path(c); b=Path(str(a)+OFF)
        move(b,a) if on else move(a,b)
def loader_state():
    a=path('bink2w64.dll'); real=path('bink2w64_.dll'); b=path('bink2w64.dll'+OFF)
    if digest(a)==M['loader_sha256'] and digest(real)==M['original_bink_sha256'] and not b.exists(): return True
    if digest(a)==M['original_bink_sha256'] and digest(b)==M['loader_sha256'] and not real.exists(): return False
    raise RuntimeError('Original Bink/loader ownership changed')
def gameplay(on):
    if loader_state()==on:return
    a=path('bink2w64.dll'); real=path('bink2w64_.dll'); b=path('bink2w64.dll'+OFF)
    if on: move(a,real); move(b,a)
    else: move(a,b); move(real,a)
def config_read(p):
    c=configparser.ConfigParser(interpolation=None,strict=False)
    c.optionxform=str
    if p.exists(): c.read(p,encoding='utf-8-sig')
    return c
def config_bytes(c):
    import io
    f=io.StringIO();c.write(f,space_around_delimiters=False)
    return f.getvalue().replace('\n','\r\n').encode('utf-8')
def config_set(section,key,value):
    c=config_read(path('ReShade.ini'))
    if section not in c:c.add_section(section)
    c[section][key]=str(value)
    write(path('ReShade.ini'),config_bytes(c))
def closed():
    cmd="Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(ShadowOfWar|steam|steamwebhelper|RHI|EpicGamesLauncher|GalaxyClient|ShaderCompileWorker|ReShade_Setup.*)$' } | Select-Object -ExpandProperty ProcessName"
    r=subprocess.run(['powershell.exe','-NoLogo','-NoProfile','-Command',cmd],capture_output=True,text=True,timeout=20)
    names=sorted(set(r.stdout.split()))
    if names:raise RuntimeError('Close game, Steam, RHI and helpers first: '+', '.join(names))
    if digest(path('ShadowOfWar.exe'))!=M['exe_sha256']:raise RuntimeError('Game executable changed; review compatibility first')
def validate():
    loader_state()
    for c in M['components']:module_state(c)
    for c in M['payloads']:
        if digest(BASE/c['file'])!=c['sha256']:raise RuntimeError('Profile recovery payload changed: '+c['file'])
    active=state()['profile']
    host=path('dxgi.dll') if module_state(module('graphics')) else path('dxgi.dll'+OFF)
    if active not in ('previous','luma') or digest(host)!=digest(BASE/'payloads'/active/'dxgi.dll'):raise RuntimeError('Graphics host and selected profile differ')
    if active=='previous' and (module_state(module('luma')) or module_state(module('nr'))):raise RuntimeError('A trial component is active in the previous graphics profile')
    if active=='luma' and (module_state(module('renodx')) or not module_state(module('luma'))):raise RuntimeError('Conflicting or missing HDR owner in the Luma profile')
def snapshot():
    dest=BASE/'profile-snapshots'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    dest.mkdir(parents=True)
    for f in ['ReShade.ini','modloader/Mod Loader.ini','plugins/config/Multi Equip Skills.ini','plugins/config/Elven Speed.ini','plugins/config/FOV Extender.ini']:
        p=path(f)
        if p.exists():
            q=dest/'settings'/f;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    shutil.copytree(BASE/'profile-configs',dest/'profile-configs')
    shutil.copy2(BASE/'graphics-profile-state.json',dest/'graphics-profile-state.json')
    if Path(M['save_path']).exists():shutil.copytree(M['save_path'],dest/'steam-save')
    native=Path(os.environ['LOCALAPPDATA'])/'WB Games/Shadow of War'
    if native.exists():shutil.copytree(native,dest/'native-settings')
    positions={c['id']:{'enabled':module_state(c),'sha256':digest(component_path(c)) or digest(Path(str(component_path(c))+OFF))} for c in M['components']}
    (dest/'positions.json').write_text(json.dumps({'components':positions,'gameplay':loader_state(),'state':state()},indent=2))
    return dest
def select_profile(which):
    current=state()['profile']
    if current!=which:
        write(BASE/'profile-configs'/current/'ReShade.ini',path('ReShade.ini').read_bytes())
        host=path('dxgi.dll') if module_state(module('graphics')) else path('dxgi.dll'+OFF)
        source=BASE/'payloads'/which/'dxgi.dll'
        write(host,source.read_bytes())
        write(path('ReShade.ini'),(BASE/'profile-configs'/which/'ReShade.ini').read_bytes())
        write(BASE/'graphics-profile-state.json',json.dumps({'profile':which},indent=2).encode())
    if which=='previous':
        enable('nr',False);enable('luma',False);enable('renodx',True)
    else:
        enable('renodx',False);enable('luma',True)
    enable('graphics',True)
def apply(action,mod=None):
    global UNDO
    UNDO=[]
    with open(BASE/'profile-switch.lock','a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        try:
            closed();validate();snap=snapshot()
            if action in ('Previous','Recommended'):select_profile('previous')
            elif action=='LumaOn':select_profile('luma')
            elif action=='LumaOff':select_profile('previous')
            elif action=='Stock':enable('graphics',False);gameplay(False)
            elif action=='GraphicsOn':enable('graphics',True)
            elif action=='GraphicsOff':enable('graphics',False)
            elif action=='GameplayOn':gameplay(True)
            elif action=='GameplayOff':gameplay(False)
            elif action in ('DlaaOn','DlaaOff'):
                if state()['profile']!='luma':raise RuntimeError('Select the Luma profile first')
                if action=='DlaaOff':
                    enable('nr',False);config_set('ADDON','LoadFromDllMain','')
                config_set('Luma','SRUserType',2 if action=='DlaaOn' else 0)
            elif action in ('NrOn','NrOff'):
                if action=='NrOn':
                    select_profile('luma');config_set('Luma','SRUserType',2)
                    config_set('RenoDX.DLSS5','NR',1)
                    config_set('ADDON','LoadFromDllMain','renodx-dlss5.addon64');enable('nr',True)
                else:
                    enable('nr',False)
                    if state()['profile']=='luma':config_set('ADDON','LoadFromDllMain','')
            elif action in ('ModOn','ModOff'):
                if mod not in ('multi-skills','elven-speed','fov'):raise RuntimeError('Choose one of the three gameplay mods')
                enable(mod,action=='ModOn')
            else:raise RuntimeError('Unknown action')
            if action=='Recommended':
                gameplay(True)
                for id in ('multi-skills','elven-speed','fov'):enable(id,True)
            validate()
            row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':action,'mod':mod,'snapshot':str(snap),'state':state(),'result':'file-verified','gameplay_tested':False}
            with (BASE/'profile-switch-history.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
            print('Applied:',action)
        except Exception:
            for undo in reversed(UNDO):undo()
            raise
        finally:msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
def status():
    validate()
    active=state()['profile']; graphics=module_state(module('graphics'))
    print('\nSHADOW OF WAR - GRAPHICS AND GAMEPLAY')
    print('Profile:', 'Previous RenoDX setup' if active=='previous' else 'Luma trial (100% DLAA; true SR unavailable)')
    print('Graphics:', 'ON' if graphics else 'OFF')
    print('Gameplay loader:', 'ON' if loader_state() else 'OFF')
    c=config_read(path('ReShade.ini'))
    print('Luma/DLAA:', 'ON (requires in-game TAA + 100% resolution)' if active=='luma' and graphics and c.get('Luma','SRUserType',fallback='0')=='2' else 'OFF')
    print('DLSS 5:', 'ENABLED FOR TEST; runtime confirmation required' if active=='luma' and graphics and module_state(module('nr')) else 'OFF')
    for id in ('multi-skills','elven-speed','fov'):print(module(id)['name']+':', 'available' if module_state(module(id)) else 'OFF')
    print('Official UHD texture pack: installed; use Steam DLC for its independent on/off switch')
    print('Delete: graphics | F12: gameplay | F10: neural toggle in the Luma trial')
    runtime_receipt=BASE/'runtime-20261024/RUNTIME-RECEIPT.json'
    if runtime_receipt.exists() and json.loads(runtime_receipt.read_text()).get('luma_shutdown_fault'):
        print('Trial warning: Luma crashed on exit in the menu test; keep Luma/DLSS 5 OFF pending diagnosis.')
def menu():
    actions={'1':'Recommended','2':'Stock','3':'GraphicsOn','4':'GraphicsOff','5':'GameplayOn','6':'GameplayOff','9':'LumaOn','10':'Previous','11':'NrOn','12':'NrOff','13':'DlaaOn','14':'DlaaOff'}
    while True:
        try:status()
        except Exception as e:print('STATE CHECK:',e)
        print('\n1 Previous recommended ON   2 All third-party mods OFF\n3 Graphics ON              4 Graphics OFF\n5 Gameplay ON              6 Gameplay OFF\n7 Individual mods          8 Guide\n9 Luma trial (HDR startup restart)   10 Previous graphics\n11 DLSS 5 ON              12 DLSS 5 OFF\n13 Luma DLAA ON           14 Luma DLAA OFF\n15 Texture-pack controls in Steam       0 Close')
        choice=input('Choose: ').strip()
        if choice=='0':return
        try:
            if choice in actions:apply(actions[choice])
            elif choice=='7':
                ids=['multi-skills','elven-speed','fov']
                print('1 Multi Equip Skills  2 Elven Speed  3 FOV Extender')
                pick=input('Mod (Enter cancels): ').strip()
                if pick in ('1','2','3'):
                    id=ids[int(pick)-1];apply('ModOff' if module_state(module(id)) else 'ModOn',id)
            elif choice=='8':subprocess.Popen(['notepad.exe',str(BASE/'LUMA-START-HERE.txt')])
            elif choice=='15':subprocess.Popen([r'C:\Program Files (x86)\Steam\steam.exe','steam://gameproperties/356190/dlc'])
        except Exception as e:print('Not applied:',e)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--action',default='Menu');parser.add_argument('--mod');a=parser.parse_args()
    try:
        if a.action=='Menu':menu()
        elif a.action=='Status':status()
        else:apply(a.action,a.mod);status()
    except Exception as e:print('Not applied:',e);sys.exit(1)
