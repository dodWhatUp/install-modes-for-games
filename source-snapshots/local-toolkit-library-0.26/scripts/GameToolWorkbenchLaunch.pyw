"""Launch the game-first or original interface over one separate preview profile.

Reuses the existing source verifier and OS-released preview lease. No deployment.
"""
from __future__ import annotations
import argparse,importlib.machinery,importlib.util,os,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PROFILE='GameToolHub-Workbench-Preview-0.24'

def load_module(name,path):
    loader=importlib.machinery.SourceFileLoader(name,str(path))
    spec=importlib.util.spec_from_loader(name,loader)
    module=importlib.util.module_from_spec(spec);loader.exec_module(module);return module

def verify(root):
    original=load_module('existing_preview_contract',root/'scripts/GameToolFocusLaunch.pyw')
    manifest=original.verify_source(root)
    required={'scripts/GameToolWorkbench.py','scripts/GameToolGameWorkspaces.py',
              'scripts/GameToolWorkbenchLaunch.pyw','scripts/GameToolAI.py',
              'scripts/game_mod_ops/support.py','scripts/game_mod_ops/definitions.py',
              'scripts/game_mod_ops/managers.py','scripts/game_mod_ops/handoff.py'}
    if not required<={r['path'] for r in manifest['files']}:
        raise ValueError('The workbench source is incomplete. Extract the whole package.')
    return original,manifest

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--layout',choices=['Workbench','Original','Focus'],default='Workbench')
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--install-root',type=Path)
    parser.add_argument('--verify-only',action='store_true');args=parser.parse_args(argv)
    if sys.version_info<(3,10):raise ValueError('Python 3.10+ with Tkinter is required. No runtime was installed.')
    original,manifest=verify(ROOT)
    if args.verify_only:return 0
    sys.path.insert(0,str(ROOT/'scripts'))
    data=args.data_dir or Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/PROFILE
    if args.install_root:
        import GameToolUnified as api
        installed=api.read_install(args.install_root)
        api.verify_current(args.install_root,installed)
        if ROOT != args.install_root/'versions'/installed['current'] or data != Path(installed['data_dir']):
            raise ValueError('Installed source/data pointer differs from this launch.')
    with original.PreviewLease(data):
        next_mode=[]
        if args.layout=='Workbench':
            from GameToolWorkbench import gui
            gui(data,on_original=lambda:next_mode.append('Original'))
        if args.layout in ('Original','Focus') or next_mode:
            hub=load_module('game_tools_original_workbench_profile',ROOT/'scripts/Game-Tool-Hub.py')
            hub.gui(data,interface_preview='Focus' if args.layout=='Focus' else (None if args.install_root else 'Original'),
                    unified_install=args.install_root)
    return 0

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        try:
            import tkinter as tk
            from tkinter import messagebox
            ui=tk.Tk();ui.withdraw();messagebox.showerror('Game Tools — unable to open',str(error),parent=ui);ui.destroy()
        except Exception:
            if os.name=='nt':
                import ctypes;ctypes.windll.user32.MessageBoxW(None,str(error),'Game Tools — unable to open',0x10)
            else:print('Unable to open Game Tools: '+str(error),file=sys.stderr)
        raise SystemExit(2)
