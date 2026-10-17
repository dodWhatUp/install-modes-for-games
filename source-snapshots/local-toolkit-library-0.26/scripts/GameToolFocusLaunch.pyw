"""One obvious launcher per interface; run the same source with shared preview data.

No installation/update, game launch, native input or cloud connection occurs here.
Existing production bootstrap and data are deliberately not touched.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,sys
from pathlib import Path,PurePosixPath
sys.dont_write_bytecode=True


def verify_source(root):
    raw=(root/'MANIFEST.json').read_bytes()
    if len(raw)>2*1024*1024:raise ValueError('Source manifest is too large')
    m=json.loads(raw);seen=set()
    for row in m['files']:
        rel=PurePosixPath(row['path'])
        if rel.is_absolute() or '..' in rel.parts or '\\' in row['path'] or row['path'] in seen:raise ValueError('Invalid source manifest path')
        seen.add(row['path']);p=root.joinpath(*rel.parts)
        if p.is_symlink() or p.resolve()!=p.absolute():raise ValueError('Linked source path was not accepted')
        data=p.read_bytes()
        if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256'].lower():raise ValueError('A packaged source file changed: '+row['path'])
    if not {'scripts/Game-Tool-Hub.py','scripts/GameToolFocusUI.py','scripts/GameToolFocusPanels.py'}<=seen:raise ValueError('This is not the complete Focus source package')
    return m


class PreviewLease:
    """OS-released local lock for the two preview launchers, not a game lock."""
    def __init__(self,root):self.path=root/'.ui-preview.lock';self.handle=None
    def __enter__(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        if self.path.is_symlink():raise ValueError('Preview lock is not a regular file')
        self.handle=self.path.open('a+b')
        if self.path.stat().st_size==0:self.handle.write(b'0');self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name=='nt':
                import msvcrt;msvcrt.locking(self.handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl;fcntl.flock(self.handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except (OSError,BlockingIOError):
            self.handle.close();self.handle=None;raise ValueError('A Game Tools preview is already open. Close it before opening the other interface.')
        return self
    def __exit__(self,*_):
        if self.handle:self.handle.close();self.handle=None


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--layout',choices=['Focus','Original'],required=True)
    parser.add_argument('--verify-only',action='store_true')
    args=parser.parse_args(argv);root=Path(__file__).resolve().parents[1]
    if sys.version_info<(3,10):raise ValueError('Python 3.10 or later with Tkinter is required. No runtime was installed.')
    verify_source(root)
    if args.verify_only:return 0
    sys.path.insert(0,str(root/'scripts'))
    spec=importlib.util.spec_from_file_location('game_tools_preview',root/'scripts/Game-Tool-Hub.py');hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)
    data=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'GameToolHub-Interface-Preview-0.22'
    with PreviewLease(data):
        hub.gui(data,interface_preview=args.layout)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        try:
            import tkinter as tk
            from tkinter import messagebox
            ui=tk.Tk();ui.withdraw();messagebox.showerror('Game Tools — preview',str(error),parent=ui);ui.destroy()
        except Exception:
            if os.name=='nt':
                import ctypes;ctypes.windll.user32.MessageBoxW(None,str(error),'Game Tools — unable to open',0x10)
            else:print('Unable to open Game Tools: '+str(error),file=sys.stderr)
        raise SystemExit(2)
