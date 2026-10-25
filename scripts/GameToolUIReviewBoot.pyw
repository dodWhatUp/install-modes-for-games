"""Verified parallel entry; never changes the current unified installation."""
import hashlib,json,sys
from pathlib import Path

def main():
    root=Path(__file__).resolve().parent;source=root/'source';config=root/'review-config.json'
    raw=(source/'MANIFEST.json').read_bytes();settings=json.loads(config.read_text(encoding='utf-8'))
    if hashlib.sha256(raw).hexdigest()!=settings['source_manifest_sha256']:raise ValueError('The parallel source manifest changed.')
    manifest=json.loads(raw);rows=manifest['files']
    if not 1<=len(rows)<=1024:raise ValueError('The parallel source inventory exceeds its bound.')
    total=0
    for row in rows:
        relative=Path(row['path']);path=source/relative
        if relative.is_absolute() or '..' in relative.parts or path.resolve()!=path.absolute() or source.resolve() not in path.resolve().parents:raise ValueError('Invalid reviewed source path.')
        content=path.read_bytes();total+=len(content)
        if total>32*1024*1024 or len(content)!=row['bytes'] or hashlib.sha256(content).hexdigest()!=row['sha256']:raise ValueError('Parallel source byte verification failed.')
    sys.path.insert(0,str(source/'scripts'))
    from GameToolUIReview import main as run
    return run(['--config',str(config)]+sys.argv[1:])

if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as error:
        import tkinter as tk
        from tkinter import messagebox
        root=tk.Tk();root.withdraw();messagebox.showerror('Parallel UI preview needs attention',str(error),parent=root);root.destroy()
