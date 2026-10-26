"""App-owned Windows identity, icons and restore requests; no game/input owner."""
from __future__ import annotations
import ctypes,hashlib,os
from pathlib import Path

VERSION='0.1.0'
APPS={
    'unified':('GameTools.Unified','Unified Game Tools','unified'),
    'preview-files':('GameTools.UiPreview.Files','Game Tools UI Preview','preview-files'),
    'preview-mods':('GameTools.UiPreview.Mods','Mod Controls UI Preview','preview-mods'),
    'mod-controls':('GameTools.ModControls','Game Mod Controls','mod-controls'),
    'shadow':('GameTools.ShadowOfWar','Shadow of War Mods','shadow'),
    'wicked':('GameTools.NoRestForTheWicked','No Rest for the Wicked Mods','wicked'),
}

def icon_path(key,extension='ico'):
    return Path(__file__).with_name('app-icons')/(APPS[key][2]+'.'+extension)

def names(key,scope):
    identity=APPS[key][0]
    token=hashlib.sha256(str(Path(scope).resolve()).casefold().encode('utf-8')).hexdigest()
    # Preserve the existing Unified ownership name across this source update.
    mutex='Local\\GameToolsUnified-'+token if key=='unified' else 'Local\\'+identity+'-'+token
    return mutex,mutex+'-ShowWindow'

def kernel_api():
    from ctypes import wintypes as w
    api=ctypes.WinDLL('kernel32',use_last_error=True)
    for name,args,result in [
        ('CreateMutexW',[ctypes.c_void_p,w.BOOL,w.LPCWSTR],w.HANDLE),
        ('CreateEventW',[ctypes.c_void_p,w.BOOL,w.BOOL,w.LPCWSTR],w.HANDLE),
        ('OpenEventW',[w.DWORD,w.BOOL,w.LPCWSTR],w.HANDLE),
        ('CreateFileMappingW',[w.HANDLE,ctypes.c_void_p,w.DWORD,w.DWORD,w.DWORD,w.LPCWSTR],w.HANDLE),
        ('OpenFileMappingW',[w.DWORD,w.BOOL,w.LPCWSTR],w.HANDLE),
        ('MapViewOfFile',[w.HANDLE,w.DWORD,w.DWORD,w.DWORD,ctypes.c_size_t],ctypes.c_void_p),
        ('UnmapViewOfFile',[ctypes.c_void_p],w.BOOL),
        ('SetEvent',[w.HANDLE],w.BOOL),('WaitForSingleObject',[w.HANDLE,w.DWORD],w.DWORD),
        ('CloseHandle',[w.HANDLE],w.BOOL)]:
        fn=getattr(api,name);fn.argtypes=args;fn.restype=result
    return api

def request_existing(key,scope):
    """Request only this app's existing window, without opening an editor/game."""
    if os.name!='nt':return False
    api=kernel_api();handle=api.OpenEventW(2,False,names(key,scope)[1])
    if not handle:return False
    try:
        owner=api.OpenFileMappingW(4,False,names(key,scope)[1]+'-Owner')
        if owner:
            try:
                view=api.MapViewOfFile(owner,4,0,0,4)
                if view:
                    try:pid=ctypes.c_uint32.from_address(view).value
                    finally:api.UnmapViewOfFile(view)
                    if pid:
                        user=ctypes.WinDLL('user32',use_last_error=True)
                        user.AllowSetForegroundWindow.argtypes=[ctypes.c_uint32]
                        user.AllowSetForegroundWindow(pid)
            finally:api.CloseHandle(owner)
        if not api.SetEvent(handle):raise ctypes.WinError(ctypes.get_last_error())
        return True
    finally:api.CloseHandle(handle)

class Session:
    def __init__(self,key,scope):
        self.key=key;self.primary=True;self.restored=False;self.closed=False
        self.root=None;self.job=None;self.mutex=self.event=self.owner=None;self.api=None
        if os.name!='nt':return
        from ctypes import wintypes as w
        shell=ctypes.WinDLL('shell32',use_last_error=True)
        shell.SetCurrentProcessExplicitAppUserModelID.argtypes=[w.LPCWSTR]
        shell.SetCurrentProcessExplicitAppUserModelID.restype=ctypes.c_long
        result=shell.SetCurrentProcessExplicitAppUserModelID(APPS[key][0])
        if result<0:raise OSError('Windows app identity failed: '+hex(result&0xffffffff))
        self.api=kernel_api();mutex,event=names(key,scope)
        ctypes.set_last_error(0);self.mutex=self.api.CreateMutexW(None,False,mutex)
        error=ctypes.get_last_error()
        if not self.mutex:raise ctypes.WinError(error)
        if error==183:
            self.primary=False
            try:self.restored=request_existing(key,scope)
            finally:self.close()
            return
        self.owner=self.api.CreateFileMappingW(ctypes.c_void_p(-1),None,4,0,4,event+'-Owner')
        if not self.owner:
            error=ctypes.get_last_error();self.close();raise ctypes.WinError(error)
        view=self.api.MapViewOfFile(self.owner,2,0,0,4)
        if not view:
            error=ctypes.get_last_error();self.close();raise ctypes.WinError(error)
        try:ctypes.c_uint32.from_address(view).value=os.getpid()
        finally:self.api.UnmapViewOfFile(view)
        self.event=self.api.CreateEventW(None,False,False,event)
        if not self.event:
            error=ctypes.get_last_error();self.close();raise ctypes.WinError(error)
    def attach(self,root):
        if not self.primary:raise RuntimeError('An existing window owns this app session')
        self.root=root;root.game_tools_app_session=self
        if os.name=='nt':root.iconbitmap(default=str(icon_path(self.key)))
        else:
            import tkinter as tk
            self.icon=tk.PhotoImage(master=root,file=str(icon_path(self.key,'png')))
            root.iconphoto(True,self.icon)
        root.bind('<Destroy>',self.destroyed,add='+')
        if self.api:self.job=root.after(100,self.poll)
    def poll(self):
        self.job=None
        if self.closed:return
        result=self.api.WaitForSingleObject(self.event,0)
        if result==0:self.show()
        elif result!=258:raise OSError('Window restore event failed: '+str(result))
        self.job=self.root.after(100,self.poll)
    def show(self):
        if self.root is None or self.closed:return
        # Restore the existing editor, including its unsaved draft and dialogs.
        self.root.deiconify();self.root.lift()
        modal=self.root.grab_current()
        if modal:modal.lift();modal.focus_set()
        else:self.root.focus_force()
    def destroyed(self,event):
        if event.widget is self.root:self.close()
    def close(self):
        if self.closed:return
        self.closed=True
        if self.job is not None and self.root:
            try:self.root.after_cancel(self.job)
            except Exception:pass
        for handle in (self.event,self.owner,self.mutex):
            if handle:self.api.CloseHandle(handle)
        self.event=self.owner=self.mutex=None

def close_window(root):
    """Use the app's current close guard, draft preservation and normal shutdown."""
    command=root.protocol('WM_DELETE_WINDOW')
    if command:root.tk.call(command)
    else:root.destroy()

def add_window_controls(parent,root,tools_menu,*,pack=True):
    """Small visible controls; no protocol replacement or background-owner action."""
    from tkinter import ttk
    frame=ttk.Frame(parent)
    if pack:frame.pack(side='right',padx=(4,0))
    ttk.Style(root).configure('AppWindow.TButton',padding=(3,2),font=('Segoe UI',10))
    for text,label,callback in [('−','Hide window · reopen from taskbar',root.iconify),('×','Close application',lambda:close_window(root))]:
        button=ttk.Button(frame,text=text,width=2,style='AppWindow.TButton',command=callback)
        button.pack(side='left',padx=(2,0));button.app_window_label=label
        def tip(event,b=button,caption=label):
            import tkinter as tk
            clear(None,b)
            win=tk.Toplevel(root);win.overrideredirect(True);b.app_window_tip=win
            ttk.Label(win,text=caption,padding=5).pack()
            win.geometry('+%d+%d'%(b.winfo_rootx(),b.winfo_rooty()+b.winfo_height()+3))
        def clear(event,b=button):
            win=getattr(b,'app_window_tip',None)
            if win is not None:
                try:win.destroy()
                except Exception:pass
                b.app_window_tip=None
        button.bind('<Enter>',tip);button.bind('<Leave>',clear);button.bind('<ButtonPress>',clear,add='+')
    tools_menu.add_separator()
    tools_menu.add_command(label='Hide window · reopen from taskbar',command=root.iconify)
    tools_menu.add_command(label='Close application',command=lambda:close_window(root))
    return frame
