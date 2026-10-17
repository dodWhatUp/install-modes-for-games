"""Stable front door; version pointer changes on explicit update, not reinstall."""
import importlib.util
import json
import re
from pathlib import Path
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

def main():
    root = Path(__file__).resolve().parent
    try:
        if len(sys.argv) > 1:
            if len(sys.argv) != 3 or sys.argv[1] != "--wait-pid" or not sys.argv[2].isdigit():
                raise ValueError("Unsupported launcher arguments")
            import ctypes
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.OpenProcess(0x100000, False, int(sys.argv[2]))
            if handle:
                try:
                    if kernel.WaitForSingleObject(handle, 30000) != 0:
                        raise ValueError("Previous Hub is still closing; restart again after it exits")
                finally:
                    kernel.CloseHandle(handle)
        # Bootstrap uses no configurable module/command path; exact entry point.
        state = json.loads((root / "install.json").read_text(encoding="utf-8"))
        tag = state["current"]
        if not isinstance(tag, str) or not re.fullmatch(r"hub-[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)?-[a-f0-9]{12}", tag):
            raise ValueError("Invalid version pointer")
        if (root / "update.lock").exists():
            raise ValueError("Interrupted update requires inspection before launch")
        module = root / "versions" / tag / "scripts/GameToolUnified.py"
        # Check the captured updater against the root source inventory before exec.
        import hashlib
        manifest = json.loads((module.parent.parent / "MANIFEST.json").read_text(encoding="utf-8"))
        row = next(r for r in manifest["files"] if r["path"] == "scripts/GameToolUnified.py")
        raw = module.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"].lower():
            raise ValueError("Installed updater changed; inspect the recovery copy")
        api = type(sys)("unified_bootstrap")
        exec(compile(raw, str(module), "exec"), api.__dict__)
        subprocess.Popen(api.launch_command(root), cwd=str(root))
    except Exception as e:
        ui = tk.Tk(); ui.withdraw()
        messagebox.showerror("Unified Game Tools", str(e)); ui.destroy()

if __name__ == "__main__":
    main()
