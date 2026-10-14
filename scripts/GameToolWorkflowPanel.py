"""Optional inert data-only recipe preview. No execution controls or target writes."""
import json
import re

VERSION = "0.1.0"
_HASH = re.compile(r"[a-fA-F0-9]{64}\Z")
_STATES = {"BLOCKED", "PREPARED_NOT_AUTHORIZED", "EVIDENCE_REQUEST_ONLY"}
_PLAN_FIELDS = set("schema_version workflow_version kind source_sha256 source_bytes status declaration_blockers execution execution_authorized runtime_verification fg_preflight root_cause_verified sequence change_list rollback_status rollback_blockers rollback_steps required_live_evidence stop_conditions diagnostic_hypotheses observation_count hypothesis_ranking limitations".split())


class WorkflowPanel:
    def __init__(self, parent, workflow_api, status_callback=None):
        import tkinter as tk
        from tkinter import ttk
        self.parent, self.api, self.callback = parent, workflow_api, status_callback
        self.source = self.report = self.receipt = None
        self.local_changes = []
        self.closed = False
        self.state = tk.StringVar(master=parent, value="No recipe selected; no target inspection or action.")
        ttk.Label(parent, text="INSTALLATION / DIAGNOSTIC DRY-RUN • DATA ONLY").pack(anchor="w", padx=8, pady=4)
        ttk.Label(parent, text="Imported facts are declarations. No Install, Apply, Launch or Rollback execution is available. Local targets below are private; Copy/Export omit them.", wraplength=880).pack(anchor="w", padx=8)
        actions = ttk.Frame(parent)
        actions.pack(fill="x", padx=8, pady=6)
        self.buttons = {}
        for index, (name, action) in enumerate((("Choose recipe", self.select), ("Reload preview", self.reload),
                ("Copy portable plan", self.copy_summary), ("Export portable plan", self.export))):
            self.buttons[name] = ttk.Button(actions, text=name, command=action)
            self.buttons[name].grid(row=index // 2, column=index % 2, padx=4, pady=3, sticky="w")
        ttk.Label(parent, textvariable=self.state, wraplength=880).pack(anchor="w", padx=8, pady=4)
        self.text = tk.Text(parent, wrap="word", height=20, state="disabled")
        self.text.pack(fill="both", expand=True, padx=8, pady=8)
        self._render()

    def _dialog(self, kind, **options):
        from tkinter import filedialog
        return getattr(filedialog, kind)(parent=self.parent.winfo_toplevel(), **options)

    def _status(self, value):
        try:
            if callable(self.callback):
                self.callback(value)
            elif hasattr(self.callback, "set"):
                self.callback.set(value)
        except Exception:
            pass

    def _fail(self):
        self.report = self.receipt = None
        self.local_changes = []
        self.state.set("Workflow preview/export refused or stale. Originals retained; no live action or runtime verification.")
        self._status(self.state.get())
        self._render()
        return False

    def summary(self):
        return {"panel_version": VERSION, "plan": self.report, "export_receipt": self.receipt,
                "execution": "none", "runtime_verification": False}

    def _render(self):
        for name in self.buttons:
            enabled = not self.closed and (name == "Choose recipe" or name == "Reload preview" and self.source is not None or self.report is not None)
            self.buttons[name].configure(state="normal" if enabled else "disabled")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        if self.local_changes:
            self.text.insert("end", "PRIVATE LOCAL CHANGE LIST — not included in Copy/Export\n")
            for change in self.local_changes:
                self.text.insert("end", f"{change['action']}: {change['target']} (declared owner: {change['owner']})\n")
            self.text.insert("end", "\n")
        self.text.insert("end", json.dumps(self.summary(), indent=2, ensure_ascii=True, allow_nan=False))
        self.text.configure(state="disabled")

    def _read(self, pinned=False):
        expected = self.report["source_sha256"] if pinned and self.report else None
        result = self.api.preview_source(self.source, expected_sha256=expected)
        if type(result) is not dict or set(result) != {"portable", "local_changes"}:
            raise ValueError("Unsupported preview")
        report = result["portable"]
        if type(report) is not dict or set(report) != _PLAN_FIELDS or report.get("status") not in _STATES or report.get("execution") != "none" or \
                report.get("runtime_verification") is not False or report.get("execution_authorized") is not False or \
                type(report.get("source_sha256")) is not str or not _HASH.fullmatch(report["source_sha256"]) or \
                type(result["local_changes"]) is not list:
            raise ValueError("Unsupported preview")
        self.report, self.local_changes = result["portable"], result["local_changes"]
        self.receipt = None
        self.state.set(self.report["status"] + " • declaration analysis only; current live preflight not performed.")
        self._render()

    def select(self):
        if self.closed:
            return False
        try:
            source = self._dialog("askopenfilename", title="Select data-only workflow recipe", filetypes=(("Recipe JSON", "*.json"),))
            if not source:
                return False
            self.source = source
            self._read()
            return True
        except Exception:
            return self._fail()

    def reload(self):
        if self.closed or self.source is None:
            return False
        try:
            self._read()
            return True
        except Exception:
            return self._fail()

    def copy_summary(self):
        if self.closed or self.report is None:
            return False
        try:
            self._read(pinned=True)
            payload = json.dumps(self.summary(), indent=2, ensure_ascii=True, allow_nan=False)
            root = self.parent.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(payload)
            self._status("Copied portable declared workflow plan; private targets excluded.")
            return payload
        except Exception:
            return self._fail()

    def export(self):
        if self.closed or self.report is None:
            return False
        try:
            expected = self.report["source_sha256"]
            source = self.source
            output = self._dialog("asksaveasfilename", title="Create NEW portable plan outside repository", defaultextension=".json", filetypes=(("Portable plan JSON", "*.json"),))
            if not output:
                return False
            if self.closed or self.source != source or self.report is None or self.report["source_sha256"] != expected:
                return self._fail()
            # Pin the preview hash across the native dialog's nested event loop.
            receipt = self.api.export_plan(source, output, expected_sha256=expected)
            fields = {"workflow_version", "source_sha256", "export_sha256", "export_bytes", "status", "execution", "runtime_verification", "coverage", "restore_tested"}
            if type(receipt) is not dict or not fields <= receipt.keys() or receipt["source_sha256"] != expected or \
                    type(receipt["export_sha256"]) is not str or not _HASH.fullmatch(receipt["export_sha256"]) or \
                    type(receipt["export_bytes"]) is not int or not 0 < receipt["export_bytes"] <= 1024 * 1024 or \
                    receipt["status"] != self.report["status"] or receipt["execution"] != "none" or \
                    receipt["runtime_verification"] is not False or receipt["restore_tested"] is not False or \
                    receipt["coverage"] != "portable_plan_only" or receipt["workflow_version"] != "0.1.0":
                raise ValueError("Unacknowledged export")
            self.receipt = {key: receipt[key] for key in fields}
            self.state.set("Portable plan exported and byte-verified; no recipe execution or restore test.")
            self._render()
            return True
        except Exception:
            return self._fail()

    def close(self):
        self.closed = True
        self._render()
        return True
