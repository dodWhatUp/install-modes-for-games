"""Bounded discovery of existing native settings, independent of launch context."""
from pathlib import Path
import contextlib,datetime,hashlib,json,math,os,re,tempfile

RELATIVE=Path('WB Games/Shadow of War/render.cfg')
BINDING='control-panel-paths.json'

class SettingsLocationError(RuntimeError):
    def __init__(self,message,report=None):super().__init__(message);self.report=report or {}

def physical_file(path):
    path=Path(path)
    if os.name!='nt':return path.resolve(strict=True)
    import ctypes
    from ctypes import wintypes as w
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
    kernel.CreateFileW.restype=w.HANDLE
    kernel.GetFinalPathNameByHandleW.argtypes=[w.HANDLE,w.LPWSTR,w.DWORD,w.DWORD]
    kernel.GetFinalPathNameByHandleW.restype=w.DWORD
    kernel.CloseHandle.argtypes=[w.HANDLE]
    handle=kernel.CreateFileW(str(path),0,7,None,3,0,None)
    if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    try:
        buffer=ctypes.create_unicode_buffer(32768)
        length=kernel.GetFinalPathNameByHandleW(handle,buffer,len(buffer),0)
        if not length or length>=len(buffer):raise OSError('Cannot resolve the physical settings location.')
        name=buffer.value
    finally:kernel.CloseHandle(handle)
    if name.startswith('\\\\?\\UNC\\'):name='\\\\'+name[8:]
    elif name.startswith('\\\\?\\'):name=name[4:]
    return Path(name)

def inspect_settings(path):
    path=Path(path)
    if not path.is_absolute() or path.name.casefold()!='render.cfg':raise ValueError('Choose an absolute render.cfg file.')
    if not path.is_file():raise ValueError('File not found.')
    if not 1<=path.stat().st_size<=1048576:raise ValueError('The file is empty or too large.')
    actual=physical_file(path)
    with actual.open('rb') as stream:raw=stream.read(1048577)
    if not 1<=len(raw)<=1048576:raise ValueError('The file is empty or too large.')
    text=raw.decode('utf-8-sig');values={}
    for key in ['ScreenWidth16by9','ScreenHeight16by9','HDROut']:
        matches=re.findall(r'^\s*"'+key+r'"\s+"([^"\r\n]+)"\s*$',text,re.M)
        if len(matches)!=1:raise ValueError('Missing or duplicate native setting: '+key)
        value=float(matches[0])
        if not math.isfinite(value):raise ValueError('Invalid native setting: '+key)
        values[key]=value
    for key in ['ScreenWidth16by9','ScreenHeight16by9']:
        if values[key]!=int(values[key]) or not 640<=values[key]<=8192:raise ValueError('Unsupported native render size.')
    if values['HDROut'] not in (0,1):raise ValueError('Invalid native HDR setting.')
    return {'path':str(actual),'sha256':hashlib.sha256(raw).hexdigest(),
            'width':int(values['ScreenWidth16by9']),'height':int(values['ScreenHeight16by9'])}

def local_roots():
    roots=[]
    if os.environ.get('LOCALAPPDATA'):roots.append(Path(os.environ['LOCALAPPDATA']))
    if os.environ.get('USERPROFILE'):roots.append(Path(os.environ['USERPROFILE'])/'AppData/Local')
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
                value,_=winreg.QueryValueEx(key,'Local AppData');roots.append(Path(os.path.expandvars(value)))
        except OSError:pass
    return list(dict.fromkeys(p for p in roots if p.is_absolute() and not str(p).startswith('\\\\')))

def bound_data(workspace):
    path=Path(workspace)/BINDING
    if not path.exists():return None,{},None
    if path.is_symlink() or (hasattr(path,'is_junction') and path.is_junction()):
        raise SettingsLocationError('The settings-location binding is linked; review it before setup.')
    raw=path.read_bytes()
    try:
        if len(raw)>65536:raise ValueError('The saved mapping is too large.')
        obj=json.loads(raw.decode('utf-8-sig'))
        if type(obj) is not dict or obj.get('schema')!=1:raise ValueError('Unsupported saved mapping.')
        return raw,obj,None
    except (ValueError,UnicodeError) as e:return raw,{},str(e)

def scan_settings(workspace,roots=None):
    workspace=Path(workspace);raw,obj,issue=bound_data(workspace)
    report={'status':'searching','candidates':[],'binding_issue':issue,'missing_count':0}
    seen=set()
    def add(path,source):
        path=Path(path)
        try:
            info=inspect_settings(path);identity=os.path.normcase(info['path'])
            if identity in seen:return
            seen.add(identity);report['candidates'].append(dict(info,source=source,valid=True))
        except (OSError,ValueError,UnicodeError) as e:
            if path.exists():report['candidates'].append({'path':str(path),'source':source,'valid':False,'reason':str(e)})
            else:report['missing_count']+=1
    saved=obj.get('native_config_path')
    if isinstance(saved,str):add(saved,'Saved location')
    elif obj:report['binding_issue']='The saved mapping has no native_config_path.'
    for root in (local_roots() if roots is None else roots):
        root=Path(root);add(root/RELATIVE,'Windows local app-data')
        packages=root/'Packages'
        if packages.is_dir():
            # Only the exact game-relative file, one level of package folders.
            # No recursive drive/profile search or reading other app contents.
            try:children=sorted(packages.iterdir(),key=lambda p:p.name)[:512]
            except OSError:children=[]
            for package in children:
                if package.is_symlink() or (hasattr(package,'is_junction') and package.is_junction()):continue
                candidate=package/'LocalCache/Local'/RELATIVE
                if candidate.is_file():add(candidate,'Redirected app-data')
    valid=[c for c in report['candidates'] if c['valid']]
    selected=next((c for c in valid if c['source']=='Saved location'),None)
    if selected is None:
        # Prefer a real standard file. A virtual standard spelling resolving into
        # Packages is not a second independent standard file.
        standard=[c for c in valid if c['source']=='Windows local app-data' and 'packages' not in [p.casefold() for p in Path(c['path']).parts]]
        if len(standard)==1:selected=standard[0]
        elif len(standard)>1:valid=standard
        if selected is None and valid and len({c['sha256'] for c in valid})==1:selected=valid[0]
    if selected:
        report.update(status='found',selected=selected,path=selected['path'])
    else:report['status']='ambiguous' if len(valid)>1 else 'missing'
    return report

def private_output(workspace,relative):
    workspace=Path(workspace).resolve();path=workspace/relative
    if not path.resolve().is_relative_to(workspace):raise ValueError('Setup output leaves the controller workspace.')
    for part in [path,*path.parents]:
        if part==workspace.parent:break
        if part.is_symlink() or (hasattr(part,'is_junction') and part.is_junction()):raise ValueError('Linked setup output refused.')
    return path

def write_atomic(path,data):
    fd,name=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

@contextlib.contextmanager
def mapping_lock(workspace):
    path=private_output(workspace,'settings-location.lock')
    with path.open('a+b') as lock:
        lock.seek(0);lock.write(b'0');lock.flush();lock.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:yield
        finally:
            if os.name=='nt':msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)

def save_location(workspace,path):
    workspace=Path(workspace).resolve();info=inspect_settings(path)
    with mapping_lock(workspace):
        target=private_output(workspace,BINDING);raw,obj,issue=bound_data(workspace)
        if obj.get('native_config_path')==info['path'] and not issue:return info
        stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
        recovery=private_output(workspace,Path('settings-location-recovery')/stamp);recovery.mkdir(parents=True)
        if raw is not None:(recovery/BINDING).write_bytes(raw)
        obj.update(schema=1,native_config_path=info['path'])
        receipt={'selected':info,'previous_binding_preserved':raw is not None,'binding_issue':issue,'native_file_changed':False}
        (recovery/'selection.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        write_atomic(target,(json.dumps(obj,indent=2)+'\n').encode('utf-8'))
        check=json.loads(target.read_text(encoding='utf-8'))
        if check['native_config_path']!=info['path']:raise RuntimeError('Settings-location readback failed.')
    return info

def resolve_settings(workspace,override=None,roots=None):
    if override is not None:
        try:return {'status':'explicit','path':inspect_settings(override)['path'],'candidates':[]}
        except (ValueError,OSError,UnicodeError) as e:raise SettingsLocationError(str(e)) from e
    report=scan_settings(workspace,roots)
    if report['status']=='found':
        save_location(workspace,report['path']);return report
    message=('Several different valid settings files were found. Choose the game settings file in Settings location.' if report['status']=='ambiguous' else
             'No valid Shadow of War render.cfg was found. Use Settings location to search again or choose an existing file. No settings file was created or reset.')
    if report.get('binding_issue'):message+=' Saved mapping: '+report['binding_issue']
    raise SettingsLocationError(message,report)
