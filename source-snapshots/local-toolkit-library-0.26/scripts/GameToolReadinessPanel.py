"""Optional private JSON draft editor and mock checks; never sends input/runs."""
import hashlib
import json

VERSION = "0.1.0"


class ReadinessPanel:
    def __init__(self, parent, api, status_callback=None):
        import tkinter as tk
        from tkinter import ttk
        self.parent, self.api, self.callback = parent, api, status_callback
        self.source = self.source_hash = self.loaded_raw = None
        self.report = self.receipt = None
        self.closed = self.dirty = self._loading = False
        self.location = tk.StringVar(master=parent)
        self.state = tk.StringVar(master=parent, value="No contract loaded. No provider or scenario is running.")
        ttk.Label(parent, text="PROVIDER HEALTH / SCENARIO CONTRACTS • OFFLINE DECLARATIONS ONLY").pack(anchor="w", padx=8, pady=4)
        ttk.Label(parent, text="Editor content is private. Load an authored mock or scenario JSON; edit, Preview, then Save NEW scenario outside the repository. Original files are never overwritten. No capture or execution controls.", wraplength=940).pack(anchor="w", padx=8)
        path_row = ttk.Frame(parent); path_row.pack(fill="x", padx=8, pady=4)
        ttk.Entry(path_row, textvariable=self.location).pack(side="left", fill="x", expand=True)
        self.buttons = {}
        for name, action in (("Load path", self.load), ("Browse", self.browse),
                ("Discard edits and load", self.discard_load), ("Preview draft", self.preview),
                ("Save NEW scenario", self.save), ("Copy checked summary", self.copy_summary)):
            self.buttons[name] = ttk.Button(path_row, text=name, command=action)
            self.buttons[name].pack(side="left", padx=2)
        ttk.Label(parent, textvariable=self.state, wraplength=940).pack(anchor="w", padx=8)
        ttk.Label(parent, text="PRIVATE EDITOR — imported identifiers/metadata are not included in copied summary").pack(anchor="w", padx=8)
        self.editor = tk.Text(parent, height=15, wrap="none", undo=True)
        self.editor.pack(fill="both", expand=True, padx=8, pady=4)
        self.editor.bind("<<Modified>>", self._edited)
        self.text = tk.Text(parent, height=13, wrap="word", state="disabled")
        self.text.pack(fill="both", expand=True, padx=8, pady=4)
        self._render()

    def _dialog(self, kind, **options):
        from tkinter import filedialog
        return getattr(filedialog, kind)(parent=self.parent.winfo_toplevel(), **options)

    def _status(self):
        try:
            if callable(self.callback):
                self.callback(self.state.get())
        except Exception:
            pass

    def _edited(self, event=None):
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            if not self._loading and not self.closed:
                self.dirty = self.loaded_raw is None or self._raw() != self.loaded_raw
                self.report = self.receipt = None
                self.state.set("Draft changed; Preview again. Source was not modified.")
                self._render()

    def _raw(self):
        return self.editor.get("1.0", "end-1c").encode("utf-8")

    def _fail(self):
        self.report = self.receipt = None
        self.state.set("Contract invalid, stale or operation refused. Draft/original retained; no live action.")
        self._render(); self._status()
        return False

    def _render(self):
        for name, button in self.buttons.items():
            enabled = not self.closed
            if name == "Save NEW scenario":
                enabled = enabled and self.report is not None and self.report["kind"] == "scenario" and self.source is not None
            if name == "Copy checked summary":
                enabled = enabled and self.report is not None
            button.configure(state="normal" if enabled else "disabled")
        self.text.configure(state="normal"); self.text.delete("1.0", "end")
        self.text.insert("end", json.dumps(self.report or {"execution": "none", "runtime_verification": False}, indent=2, allow_nan=False))
        self.text.configure(state="disabled")

    def load(self):
        if self.closed:
            return False
        if self.dirty:
            self.state.set("Unsaved edits retained. Save NEW scenario or explicitly discard edits before loading.")
            return False
        try:
            source = self.location.get().strip()
            raw, report = self.api.read_source(source)
            self.source, self.source_hash = source, report["source_sha256"]
            self._loading = True
            self.editor.delete("1.0", "end"); self.editor.insert("1.0", raw.decode("utf-8-sig"))
            self.editor.edit_modified(False); self._loading = False
            self.loaded_raw = self._raw(); self.dirty = False
            self.report, self.receipt = self.api.plan_bytes(self.loaded_raw), None
            self.state.set(report["status"] + " • declared/mock evidence, never live verification.")
            self._render(); self._status()
            return True
        except Exception:
            self._loading = False
            self.source = self.source_hash = None
            return self._fail()

    def browse(self):
        if self.closed or self.dirty:
            return False
        try:
            path = self._dialog("askopenfilename", title="Select offline contract JSON", filetypes=(("JSON", "*.json"),))
            if not path:
                return False
            self.location.set(path)
            return self.load()
        except Exception:
            return self._fail()

    def discard_load(self):
        if self.closed:
            return False
        from tkinter import messagebox
        try:
            if self.dirty and not messagebox.askyesno("Discard unsaved draft?", "Discard this editor draft and load the path shown? Original files remain unchanged.", parent=self.parent.winfo_toplevel()):
                return False
            self.dirty = False
            return self.load()
        except Exception:
            return self._fail()

    def preview(self):
        if self.closed:
            return False
        try:
            self.report = self.api.plan_bytes(self._raw())
            self.receipt = None
            self.state.set(self.report["status"] + " • draft only; execution and runtime verification unavailable.")
            self._render(); self._status()
            return True
        except Exception:
            return self._fail()

    def _checked(self):
        if self.report is None or self.report["source_sha256"] != hashlib.sha256(self._raw()).hexdigest():
            raise ValueError("Draft changed")
        if self.source is not None:
            self.api.inspect_source(self.source, expected_sha256=self.source_hash)
        return self.api.plan_bytes(self._raw())

    def copy_summary(self):
        if self.closed or self.report is None:
            return False
        try:
            report = self._checked()
            root = self.parent.winfo_toplevel()
            payload = json.dumps(report, indent=2, allow_nan=False)
            root.clipboard_clear(); root.clipboard_append(payload)
            return payload
        except Exception:
            return self._fail()

    def save(self):
        if self.closed or self.source is None or self.report is None or self.report["kind"] != "scenario":
            return False
        try:
            raw, source, expected = self._raw(), self.source, self.source_hash
            self._checked()
            output = self._dialog("asksaveasfilename", title="NEW private scenario outside repository", defaultextension=".json", filetypes=(("Scenario JSON", "*.json"),))
            if not output:
                return False
            if self.closed or self._raw() != raw or self.source != source or self.source_hash != expected:
                return self._fail()
            self.receipt = self.api.save_scenario(source, output, raw, expected)
            self.state.set("NEW private scenario saved and byte-verified. Original retained; no scenario execution.")
            self._status()
            return True
        except Exception:
            return self._fail()

    def close(self):
        self.closed = True
        self.editor.configure(state="disabled")
        self._render()
        return True
