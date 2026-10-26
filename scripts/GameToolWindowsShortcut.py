"""Explicit .lnk creation/readback with a matching AppUserModelID; Windows only."""
import ctypes,os,uuid
from pathlib import Path
from ctypes import wintypes as w

class GUID(ctypes.Structure):
    _fields_=[('bytes',ctypes.c_ubyte*16)]
    def __init__(self,value):super().__init__();self.bytes[:]=uuid.UUID(value).bytes_le
class KEY(ctypes.Structure):_fields_=[('fmtid',GUID),('pid',w.DWORD)]
class VALUE(ctypes.Union):_fields_=[('text',ctypes.c_wchar_p),('storage',ctypes.c_void_p*2)]
class VARIANT(ctypes.Structure):_fields_=[('vt',ctypes.c_ushort),('reserved',ctypes.c_ushort*3),('value',VALUE)]
IID_LINK=GUID('000214f9-0000-0000-c000-000000000046')
IID_PERSIST=GUID('0000010b-0000-0000-c000-000000000046')
IID_STORE=GUID('886d8eeb-8cf2-4446-8d02-cdba1dbdcf99')
APP_ID=KEY(GUID('9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3'),5)

def checked(result):
    if result<0:raise OSError('Windows shortcut operation failed: '+hex(result&0xffffffff))
def call(pointer,index,types,*args):
    function=ctypes.cast(pointer,ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents[index]
    return ctypes.WINFUNCTYPE(ctypes.c_long,ctypes.c_void_p,*types)(function)(pointer,*args)

class Link:
    def __init__(self,path=None,*,writable=False):
        if os.name!='nt':raise OSError('Windows shortcuts require Windows')
        self.ole=ctypes.OleDLL('ole32');self.ptrs=[]
        self.ole.CoInitializeEx.argtypes=[ctypes.c_void_p,w.DWORD];self.ole.CoInitializeEx.restype=ctypes.c_long
        result=self.ole.CoInitializeEx(None,2);checked(result);self.initialized=True
        try:
            self.ole.CoCreateInstance.argtypes=[ctypes.POINTER(GUID),ctypes.c_void_p,w.DWORD,ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)]
            self.ole.CoCreateInstance.restype=ctypes.c_long
            self.link=ctypes.c_void_p()
            checked(self.ole.CoCreateInstance(ctypes.byref(GUID('00021401-0000-0000-c000-000000000046')),None,1,ctypes.byref(IID_LINK),ctypes.byref(self.link)))
            self.ptrs.append(self.link)
            self.persist=self.query(IID_PERSIST);self.store=self.query(IID_STORE)
            if path:checked(call(self.persist,5,[w.LPCWSTR,w.DWORD],str(Path(path).absolute()),2 if writable else 0))
        except Exception:self.close();raise
    def query(self,iid):
        result=ctypes.c_void_p();checked(call(self.link,0,[ctypes.POINTER(GUID),ctypes.POINTER(ctypes.c_void_p)],ctypes.byref(iid),ctypes.byref(result)))
        self.ptrs.append(result);return result
    def close(self):
        for ptr in reversed(self.ptrs):call(ptr,2,[])
        self.ptrs=[]
        if getattr(self,'initialized',False):self.ole.CoUninitialize();self.initialized=False
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def text(self,index):
        buffer=ctypes.create_unicode_buffer(32768)
        checked(call(self.link,index,[w.LPWSTR,ctypes.c_int],buffer,len(buffer)));return buffer.value
    def read(self):
        target=ctypes.create_unicode_buffer(32768)
        checked(call(self.link,3,[w.LPWSTR,ctypes.c_int,ctypes.c_void_p,w.DWORD],target,len(target),None,4))
        icon=ctypes.create_unicode_buffer(32768);number=ctypes.c_int()
        checked(call(self.link,16,[w.LPWSTR,ctypes.c_int,ctypes.POINTER(ctypes.c_int)],icon,len(icon),ctypes.byref(number)))
        value=VARIANT();checked(call(self.store,5,[ctypes.POINTER(KEY),ctypes.POINTER(VARIANT)],ctypes.byref(APP_ID),ctypes.byref(value)))
        try:app_id=value.value.text if value.vt==31 else ''
        finally:
            self.ole.PropVariantClear.argtypes=[ctypes.POINTER(VARIANT)];self.ole.PropVariantClear(ctypes.byref(value))
        return {'target':target.value,'arguments':self.text(10),'working_directory':self.text(8),
                'description':self.text(6),'icon':icon.value,'icon_index':number.value,'app_id':app_id}
    def configure(self,target,arguments,working_directory,description,icon,app_id):
        for index,value in [(20,target),(11,arguments),(9,working_directory),(7,description)]:
            checked(call(self.link,index,[w.LPCWSTR],str(value)))
        checked(call(self.link,17,[w.LPCWSTR,ctypes.c_int],str(icon),0))
        value=VARIANT();value.vt=31;value.value.text=app_id
        checked(call(self.store,6,[ctypes.POINTER(KEY),ctypes.POINTER(VARIANT)],ctypes.byref(APP_ID),ctypes.byref(value)))
        checked(call(self.store,7,[]))
    def save(self,path):checked(call(self.persist,6,[w.LPCWSTR,w.BOOL],str(path),True))

def read(path):
    with Link(path)as link:return link.read()

def write(path,*,target,arguments,working_directory,description,icon,app_id,expected=None):
    path=Path(path).absolute();old=path.read_bytes()if path.exists()else None
    if old is not None:
        if expected is None or read(path)!=expected:raise ValueError('Existing shortcut requires its exact reviewed baseline')
    if not Path(target).is_file()or not Path(icon).is_file()or not Path(working_directory).is_dir():
        raise ValueError('Shortcut runtime, icon and working folder must exist')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.stem+'.pending-'+uuid.uuid4().hex+'.lnk')
    try:
        # A writable clone preserves unmodeled link properties and keeps every
        # PropertyStore commit away from the live shortcut until CAS succeeds.
        if old is not None:
            with temporary.open('xb')as stream:stream.write(old)
        with Link(temporary if old is not None else None,writable=True)as link:
            link.configure(target,arguments,working_directory,description,icon,app_id);link.save(temporary)
        result=read(temporary)
        wanted={'target':str(target),'arguments':arguments,'working_directory':str(working_directory),
                'description':description,'icon':str(icon),'icon_index':0,'app_id':app_id}
        if result!=wanted:raise ValueError('Shortcut readback differs: '+repr(result))
        if (path.read_bytes()if path.exists()else None)!=old:raise ValueError('Shortcut changed during review')
        os.replace(temporary,path)
        return read(path)
    finally:
        if temporary.exists():temporary.unlink()
