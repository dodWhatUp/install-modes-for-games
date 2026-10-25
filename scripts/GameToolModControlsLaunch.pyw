"""Stable installed GUI/MCP entry. Resolve and verify the selected release first."""
from pathlib import Path
import hashlib,importlib.util,json,sys

def main():
    install=Path(__file__).resolve().parent
    state=json.loads((install/'install.json').read_text(encoding='utf-8'))
    tag=state['current'];versions=(install/'versions').resolve();root=(versions/tag).resolve()
    if root.parent!=versions or not root.is_dir():raise ValueError('Invalid installed version pointer.')
    manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8'))
    updater=root/'scripts/GameToolUnified.py'
    records=manifest['files']
    expected=next(r['sha256'] for r in records if r['path']=='scripts/GameToolUnified.py')
    if hashlib.sha256(updater.read_bytes()).hexdigest()!=expected:raise ValueError('Installed updater integrity differs.')
    spec=importlib.util.spec_from_file_location('_mod_controls_installed_updater',updater);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    module.verify_current(install,state)
    sys.path.insert(0,str(root/'scripts'))
    if '--ai' in sys.argv[1:]:
        from GameToolAI import main as run
        return run(['--data-dir',state['data_dir'],'--workspaces','--allow-requests','stdio'])
    from GameToolModControlsPanel import main as run
    return run(['--data-dir',state['data_dir']]+sys.argv[1:])

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        if '--ai' in sys.argv[1:]:raise
        import tkinter as tk
        from tkinter import messagebox
        root=tk.Tk();root.withdraw();messagebox.showerror('Game Mod Controls needs attention',str(error),parent=root);root.destroy()
