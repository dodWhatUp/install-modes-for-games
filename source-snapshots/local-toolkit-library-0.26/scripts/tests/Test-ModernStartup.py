"""Bounded saved-Modern startup regression; private desktop UI, no live tools."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True

def child():
    import tkinter as tk
    from tkinter import ttk
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import GameToolWorkspace as workspace_api
    import GameToolAppearance as appearance_api
    with tempfile.TemporaryDirectory(prefix="GameTools-ModernStartup-") as private:
        path = Path(private) / "ui-preferences.json"
        raw = b'{"schema_version":1,"mode":"Modern","views":{}}'
        path.write_bytes(raw)
        root = tk.Tk()
        root.title("ISOLATED DESKTOP TEST — saved Modern startup")
        root.geometry("960x740")
        status = tk.StringVar(root, "Offline fixture")
        header = ttk.Frame(root); header.pack(fill="x")
        workspace = workspace_api.Workspace(root, status)
        workspace.frame.pack(fill="both", expand=True)
        tabs = ttk.Notebook(workspace.content); tabs.pack(fill="both", expand=True)
        pages = {}
        for record in workspace.registry.features:
            page = ttk.Frame(tabs)
            tabs.add(page, text=record["route"])
            pages[record["route"]] = page
        workspace.attach(tabs, pages)
        appearance = appearance_api.Appearance(root, header, workspace, status, path, "fixture")
        errors = []
        root.report_callback_exception = lambda *args: errors.append(str(args[1]))
        result = {}
        def finish():
            result.update(viewable=bool(root.winfo_viewable()), width=root.winfo_width(),
                          height=root.winfo_height(), modern=workspace.modern.active,
                          cards=len(workspace.modern.cards), errors=errors)
            appearance.preview_only = True
            appearance.close(); workspace.close(); root.destroy()
        root.after(1200, finish)
        # Mirrors native-host startup's idle flush. The parent's deadline
        # catches a starvation loop rather than hanging the entire test runner.
        root.after(100, root.update_idletasks)
        root.deiconify(); root.mainloop()
        result["preferences_unchanged"] = path.read_bytes() == raw
        print(json.dumps(result))

class Startup(unittest.TestCase):
    def test_saved_modern_startup_settles_and_timers_run(self):
        process = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--child"],
                                 capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertTrue(result["viewable"])
        self.assertEqual((result["width"], result["height"]), (960, 740))
        self.assertTrue(result["modern"])
        self.assertEqual(result["cards"], 4)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["preferences_unchanged"])

if __name__ == "__main__":
    if sys.argv[1:] == ["--child"]:
        child()
    else:
        unittest.main(verbosity=2)
