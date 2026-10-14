"""Inert saved-evidence view; explicit selection/read/export, no live collection."""
from __future__ import annotations
import json

VERSION = "0.1.0"


class EvidencePanel:
    def __init__(self, parent, evidence_api, status_callback=None):
        import tkinter as tk
        from tkinter import ttk
        self.parent, self.api, self.status_callback = parent, evidence_api, status_callback
        self.paths, self.report, self.receipt = [], None, None
        self.closed = False
        self.last_error = None
        self.state = tk.StringVar(master=parent, value="No saved evidence selected.")
        ttk.Label(parent, text="SAVED CRASH EVIDENCE • OFFLINE ONLY").pack(anchor="w")
        ttk.Label(parent, wraplength=860, text="Select existing Windows event XML, Hub journal JSONL or opaque text/log files. No games, recording or live log queries. A timestamp or faulting module is not a cause. Private originals must be reviewed before sharing.").pack(anchor="w", pady=5)
        actions = ttk.Frame(parent)
        actions.pack(fill="x")
        self.buttons = {}
        for name, command in (("Select saved files", self.select_files), ("Refresh preview", self.reload),
                              ("Create private packet", self.export), ("Copy portable summary", self.copy_summary)):
            self.buttons[name] = ttk.Button(actions, text=name, command=command)
            self.buttons[name].pack(side="left", padx=3, pady=3)
        ttk.Label(parent, textvariable=self.state, wraplength=860).pack(anchor="w", pady=5)
        box = ttk.Frame(parent)
        box.pack(fill="both", expand=True)
        self.text = tk.Text(box, height=19, wrap="none", state="disabled")
        self.text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(box, command=self.text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(box, orient="horizontal", command=self.text.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.text.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        box.rowconfigure(0, weight=1)
        box.columnconfigure(0, weight=1)
        self._render()

    def _dialog(self, kind, **options):
        from tkinter import filedialog
        return getattr(filedialog, kind)(parent=self.parent.winfo_toplevel(), **options)

    def _status(self, message):
        try:
            if callable(self.status_callback):
                self.status_callback(message)
        except Exception:
            pass  # Optional status sinks do not turn an acknowledged export into failure.

    def _fail(self):
        self.report, self.receipt, self.last_error = None, None, "evidence_request_failed"
        self.state.set("Saved evidence unavailable or changed. Select/reload explicitly; no stale export/copy or diagnosis is enabled.")
        self._render()
        return False

    def summary(self):
        # Only backend portable allowlist data; no selections, originals or exception text.
        return {"panel_version": VERSION, "report": self.report, "export_receipt": self.receipt,
                "last_error": self.last_error, "execution": "none", "runtime_verification": False}

    def _render(self):
        for name in ("Create private packet", "Copy portable summary"):
            self.buttons[name].configure(state="normal" if self.report is not None and not self.closed else "disabled")
        self.buttons["Refresh preview"].configure(state="normal" if self.paths and not self.closed else "disabled")
        self.buttons["Select saved files"].configure(state="disabled" if self.closed else "normal")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", json.dumps(self.summary(), indent=2, ensure_ascii=False, allow_nan=False))
        self.text.configure(state="disabled")

    def _assignments(self, pinned=False):
        if not pinned:
            return [{"path": path} for path in self.paths]
        return [{"path": path, "expected_sha256": source["source_sha256"], "adapter": source["adapter"]}
                for path, source in zip(self.paths, self.report["sources"])]

    def select_files(self):
        if self.closed:
            return False
        try:
            paths = self._dialog("askopenfilenames", title="Select existing saved evidence (maximum eight files)",
                                 filetypes=(("Saved evidence", "*.xml *.jsonl *.txt *.log"),))
        except Exception:
            return self._fail()
        if not paths:
            self.state.set("Selection cancelled; no new operation requested.")
            return False
        self.paths, self.report, self.receipt = list(paths), None, None
        return self.reload()

    def _read(self, pinned=False):
        report = self.api.build_packet(self._assignments(pinned))
        if not isinstance(report, dict) or report.get("status") != "EVIDENCE_ONLY" or \
                report.get("runtime_verification") is not False or len(report.get("sources", [])) != len(self.paths):
            raise ValueError("Unsupported evidence result")
        self.report = report
        self.last_error = None
        return report

    def reload(self):
        if self.closed or not self.paths:
            return False
        self.receipt = None
        try:
            report = self._read()
        except Exception:
            return self._fail()
        self.state.set("{} selected sources; {} timestamped/untimed entries. Evidence only, not a crash diagnosis.".format(
                       len(report["sources"]), len(report["timeline"])))
        self._render()
        return True

    def copy_summary(self):
        if self.closed or self.report is None:
            return False
        try:
            self._read(pinned=True)
            payload = json.dumps(self.summary(), indent=2, ensure_ascii=False, allow_nan=False)
            root = self.parent.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(payload)
        except Exception:
            return self._fail()
        self.state.set("Portable evidence summary copied; private names, paths, original logs and messages are excluded.")
        self._status("Copied saved-evidence summary only; no runtime verification.")
        self._render()
        return payload

    def export(self):
        if self.closed or self.report is None:
            return False
        try:
            self._read(pinned=True)
            target = self._dialog("asksaveasfilename", title="Create NEW private packet directory outside the repository", filetypes=())
            if not target:
                self.state.set("Export selection cancelled; no packet written.")
                return False
            receipt = self.api.export_packet(self._assignments(pinned=True), target)
            if not isinstance(receipt, dict) or receipt.get("status") != "EVIDENCE_ONLY" or \
                    receipt.get("source_count") != len(self.paths) or receipt.get("runtime_verification") is not False:
                raise ValueError("Export not acknowledged")
        except Exception:
            return self._fail()
        self.receipt = receipt
        self.state.set("Private packet created at your selected location: evidence.json/html, exact originals, private receipt and completion manifest. Not uploaded; not restore-tested.")
        self._status("Saved private evidence packet created; originals retained. Review before sharing.")
        self._render()
        return True

    def close(self):
        self.closed = True
        self._render()
        return True
