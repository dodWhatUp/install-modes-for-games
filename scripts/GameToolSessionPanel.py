"""Explicit offline session controls, not a game or desktop action controller.

The constructor performs no data read, dialog, write, capture or replay. Only
fixed saved-data Coordinator capabilities are exposed. Journal recovery copies
evidence to a new destination; it never replays events or resumes ownership.
"""
from __future__ import annotations

import json
import math
import re

VERSION = "0.4.0"
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}\Z")
_PHASE = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
_HASH = re.compile(r"[a-fA-F0-9]{64}\Z")


def _label(value):
    """Do not copy arbitrary exceptions, provider text, paths or raw payloads."""
    return value if isinstance(value, str) and _LABEL.fullmatch(value) else None


def _number(value):
    try:
        return value if type(value) in (int, float) and math.isfinite(value) else None
    except OverflowError:
        return None


def _digest(value):
    return value.lower() if isinstance(value, str) and _HASH.fullmatch(value) else None


class SessionPanel:
    """Embedded ttk view; all file operations require an explicit callback."""

    def __init__(self, parent, coordinator_factory, journal_api, status_callback=None, evidence_factory=None, workflow_factory=None, readiness_factory=None):
        import tkinter as tk
        from tkinter import ttk

        self.tk, self.ttk = tk, ttk
        self.parent = parent
        self.coordinator_factory = coordinator_factory
        self.journal_api = journal_api
        self.status_callback = status_callback
        self.evidence_factory = evidence_factory
        self.workflow_factory = workflow_factory
        self.readiness_factory = readiness_factory
        self.evidence_windows = []
        self.coordinator = None
        self.closed = False
        self.close_result = None
        self.current_status = {"state": "idle"}
        self.inspected_path = None
        self.inspected_sha256 = None
        self.journal_summary = None
        self.last_error = None
        self.last_result = None
        self.phase = tk.StringVar(master=parent, value="review")
        self.owner_state = tk.StringVar(master=parent, value="No offline session has been started.")
        self.journal_state = tk.StringVar(master=parent, value="No journal inspected. Existing journals are never resumed.")
        self.operation_state = tk.StringVar(master=parent, value="No saved-data operation requested.")

        ttk.Label(parent, text="OFFLINE SESSIONS • Saved files and durable checkpoints only").pack(anchor="w")
        ttk.Label(parent, text="No games, benchmarks, recording, input or profile changes. Recovery preserves a verified journal prefix; it is not crash-cause analysis or a guarantee against every storage failure.",
                  wraplength=1040).pack(anchor="w", pady=4)
        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=3)
        self.buttons = {}
        for index, (name, command) in enumerate((
                ("New offline session", self.new_session),
                ("Inspect saved report", self.inspect_saved_report),
                ("Inspect comparison", self.inspect_comparison),
                ("Finish", self.finish), ("Cancel session", self.cancel),
                ("Refresh status", self.reload), ("Inspect journal", self.choose_journal),
                ("Recover verified prefix", self.recover), ("Copy summary", self.copy_summary),
                ("Saved crash evidence", self.open_evidence),
                ("Workflow dry-runs", self.open_workflow),
                ("Provider / scenario contracts", self.open_readiness))):
            button = ttk.Button(actions, text=name, command=command)
            button.grid(row=index // 3, column=index % 3, sticky="w", padx=3, pady=2)
            self.buttons[name] = button
        phases = ttk.Frame(parent)
        phases.pack(fill="x", pady=4)
        ttk.Label(phases, text="Phase identifier (not paths or typed payloads)").pack(side="left")
        self.phase_entry = ttk.Entry(phases, textvariable=self.phase, width=30)
        self.phase_entry.pack(side="left", padx=8)
        self.buttons["Checkpoint"] = ttk.Button(phases, text="Checkpoint", command=self.checkpoint)
        self.buttons["Checkpoint"].pack(side="left")
        for variable in (self.owner_state, self.journal_state, self.operation_state):
            ttk.Label(parent, textvariable=variable, wraplength=1040).pack(anchor="w", pady=4)
        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True)
        self.summary_text = tk.Text(body, wrap="none", state="disabled", height=17,
                                    font=("Consolas", 9))
        self.summary_text.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(body, command=self.summary_text.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(body, orient="horizontal", command=self.summary_text.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.summary_text.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        try:
            self.coordinator = coordinator_factory(owner="Hub", lifetime_seconds=900)
        except Exception:
            self.last_error = "coordinator_unavailable"
            self.operation_state.set("Offline coordination unavailable; existing Hub features are unaffected.")
        self._render()

    def _status(self, message):
        try:
            if hasattr(self.status_callback, "set"):
                self.status_callback.set(message)
            elif callable(self.status_callback):
                self.status_callback(message)
        except Exception:
            pass  # An optional status sink must not break other Hub features.

    def _dialog(self, kind, **options):
        from tkinter import filedialog
        try:
            return getattr(filedialog, kind)(parent=self.parent.winfo_toplevel(), **options)
        except Exception:
            self._fail("dialog_unavailable", "File selection unavailable; no operation was requested.")
            return None

    def _selection_cancelled(self):
        self.last_error = None
        self.last_result = None
        self.operation_state.set("File selection cancelled. No new operation was requested.")
        self._render()
        return False

    def _fail(self, code, message):
        self.last_error = code
        self.last_result = None
        self.operation_state.set(message)
        self._status(message)
        self._refresh_status()
        return False

    def _refresh_status(self):
        if self.coordinator is not None:
            try:
                observed = self.coordinator.status()
                if not isinstance(observed, dict):
                    raise ValueError("Invalid status")
                self.current_status = observed
            except Exception:
                self.current_status = {"state": "unavailable"}
                self.last_error = "status_unavailable"
        self._render()

    def _safe_status(self):
        source = self.current_status
        result = {"scope": "offline_saved_data", "execution": "offline_only", "runtime_verification": False}
        for key in ("schema_version", "lifetime_seconds", "remaining_seconds", "journal_records"):
            result[key] = _number(source.get(key))
        for key in ("coordinator_version", "state", "session_id", "owner_id", "owner", "label", "phase", "failure_code"):
            result[key] = _label(source.get(key))
        result["writer_open"] = source.get("writer_open") if type(source.get("writer_open")) is bool else None
        action = source.get("latest_action")
        if isinstance(action, dict):
            result["latest_action"] = {key: _label(action.get(key)) for key in
                                       ("id", "capability", "state", "verdict", "error_code")}
            result["latest_action"]["source_sha256"] = _digest(action.get("source_sha256"))
        else:
            result["latest_action"] = None
        return result

    def summary(self):
        """Sanitized allowlist: no selected paths, journal data or report payloads."""
        return {"panel_version": VERSION, "session": self._safe_status(),
                "journal_inspection": self.journal_summary,
                "last_operation": self.last_result, "last_error": _label(self.last_error),
                "limitations": ["No automatic replay or session resume", "Offline saved-data evidence only",
                                "No game input or capture", "Prefix recovery does not identify a crash cause"]}

    def _render(self):
        state = _label(self.current_status.get("state")) or "unavailable"
        active = state == "active" and not self.closed
        usable = self.coordinator is not None and not self.closed
        for name in ("Inspect saved report", "Inspect comparison", "Finish", "Checkpoint"):
            self.buttons[name].configure(state="normal" if usable and active else "disabled")
        self.buttons["Cancel session"].configure(state="normal" if usable and state in
                                                  ("active", "expired") else "disabled")
        self.buttons["New offline session"].configure(state="normal" if usable and not active else "disabled")
        self.buttons["Recover verified prefix"].configure(state="normal" if not self.closed and
                    self.inspected_path is not None and self.inspected_sha256 is not None and
                    self.journal_summary and (self.journal_summary.get("verified_records") or 0) > 0 else "disabled")
        for name in ("Refresh status", "Inspect journal", "Copy summary"):
            self.buttons[name].configure(state="disabled" if self.closed else "normal")
        self.buttons["Saved crash evidence"].configure(state="normal" if not self.closed and self.evidence_factory is not None else "disabled")
        self.buttons["Workflow dry-runs"].configure(state="normal" if not self.closed and self.workflow_factory is not None else "disabled")
        self.buttons["Provider / scenario contracts"].configure(state="normal" if not self.closed and self.readiness_factory is not None else "disabled")
        safe = self._safe_status()
        remaining = safe.get("remaining_seconds")
        self.owner_state.set("Owner: {} | State: {} | Phase: {} | Remaining: {} | Journal records: {}".format(
            safe.get("owner") or "none", state, safe.get("phase") or "none",
            "unavailable" if remaining is None else f"{remaining:.1f}s",
            safe.get("journal_records") if safe.get("journal_records") is not None else "unavailable"))
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", json.dumps(self.summary(), indent=2, ensure_ascii=False, allow_nan=False))
        self.summary_text.configure(state="disabled")

    def new_session(self):
        if self.closed or self.coordinator is None:
            return False
        self._refresh_status()
        if self.current_status.get("state") == "active":
            return self._fail("session_already_active", "Finish or cancel the owned offline session first.")
        path = self._dialog("asksaveasfilename",
                title="Create NEW offline journal (existing files will not be overwritten)",
                defaultextension=".jsonl", filetypes=(("Journal JSONL", "*.jsonl"),))
        if path is None:
            return False
        if not path:
            return self._selection_cancelled()
        try:
            if self.current_status.get("state") != "idle":
                observed_close = self.coordinator.close()
                if not isinstance(observed_close, dict) or observed_close.get("writer_open") is True:
                    raise ValueError("Owned writer cleanup must be retried before replacement")
                self.coordinator = self.coordinator_factory(owner="Hub", lifetime_seconds=900)
            observed = self.coordinator.start(path, label="Hub offline task")
            if not isinstance(observed, dict) or observed.get("state") != "active":
                raise ValueError("Session creation not acknowledged")
        except Exception:
            return self._fail("session_start_failed", "Offline session was not started. Existing files are not overwritten.")
        self.last_error = None
        self.last_result = {"operation": "session_start", "state": "observed"}
        self.operation_state.set("Offline session started explicitly. Only saved-file reads and checkpoints are available.")
        self._status("Offline session started; no game or recording activity.")
        self._refresh_status()
        return True

    def _require_active(self):
        self._refresh_status()
        return not self.closed and self.coordinator is not None and self.current_status.get("state") == "active"

    def checkpoint(self):
        if not self._require_active():
            return self._fail("session_not_active", "An active offline session is required for a checkpoint.")
        phase = self.phase.get()
        if not _PHASE.fullmatch(phase):
            return self._fail("invalid_phase", "Use a phase identifier of 1–64 letters, digits, dot, underscore or hyphen, starting with a letter.")
        try:
            observed = self.coordinator.checkpoint(phase)
            if not isinstance(observed, dict) or observed.get("state") != "active" or observed.get("phase") != phase:
                raise ValueError("Checkpoint not acknowledged")
        except Exception:
            return self._fail("checkpoint_failed", "Checkpoint was not acknowledged. Inspect the journal before retrying.")
        self.last_error = None
        self.last_result = {"operation": "checkpoint", "state": "observed", "phase": phase}
        self.operation_state.set("Checkpoint acknowledged by the journal writer.")
        self._refresh_status()
        return True

    def _inspect_saved(self, comparison):
        if not self._require_active():
            return self._fail("session_not_active", "Start an explicit offline session before inspecting saved data.")
        path = self._dialog("askopenfilename",
                title="Inspect existing comparison JSON" if comparison else "Inspect existing supported saved report",
                filetypes=(("JSON", "*.json"),) if comparison else (("Saved reports", "*.json *.csv"),))
        if path is None:
            return False
        if not path:
            return self._selection_cancelled()
        self.last_result = None
        self.last_error = None
        try:
            result = self.coordinator.inspect_comparison(path) if comparison else self.coordinator.inspect_saved_report(path)
            if not isinstance(result, dict):
                raise ValueError("Invalid inspection result")
            if comparison and result.get("status") not in ("COMPARABLE", "PARTIAL", "BLOCKED"):
                raise ValueError("Comparison has no declared verdict")
            if not comparison and _label(result.get("adapter")) is None:
                raise ValueError("Report has no declared adapter")
        except Exception:
            return self._fail("saved_inspection_failed", "Saved-data inspection failed or became stale. No success or runtime verification is claimed.")
        self.last_result = {"operation": "comparison_inspection" if comparison else "saved_report_inspection",
                            "state": "observed", "runtime_verification": False}
        for key in ("adapter", "adapter_revision", "status", "provider_outcome"):
            if _label(result.get(key)) is not None:
                self.last_result[key] = result[key]
        self.operation_state.set("Saved data inspected read-only. Imported declarations do not verify runtime FG, memory or a game's result.")
        self._status("Saved-data inspection complete; runtime verification remains unavailable.")
        self._refresh_status()
        return True

    def inspect_saved_report(self):
        return self._inspect_saved(False)

    def inspect_comparison(self):
        return self._inspect_saved(True)

    def finish(self):
        if not self._require_active():
            return self._fail("session_not_active", "No active offline session to finish.")
        try:
            observed = self.coordinator.finish()
            if not isinstance(observed, dict) or observed.get("state") != "finished":
                raise ValueError("Session finish not acknowledged")
        except Exception:
            return self._fail("session_finish_failed", "Session finish was not acknowledged; inspect preserved journal evidence.")
        self.last_error = None
        self.last_result = {"operation": "session_finish", "state": "observed"}
        self.operation_state.set("Owned offline session finished. No external process was stopped.")
        self._refresh_status()
        return True

    def cancel(self):
        if self.closed or self.coordinator is None:
            return False
        self._refresh_status()
        if self.current_status.get("state") not in ("active", "expired"):
            return self._fail("session_not_active", "No owned active or expired session to cancel. A failed journal cannot acknowledge cancellation.")
        try:
            observed = self.coordinator.cancel(reason="user")
            if not isinstance(observed, dict) or observed.get("state") not in ("cancelled", "expired"):
                raise ValueError("Session cancellation not acknowledged")
        except Exception:
            return self._fail("session_cancel_failed", "Cancellation was not acknowledged; no other process was affected.")
        self.last_error = None
        self.last_result = {"operation": "session_cancel", "state": "observed", "owned_state": observed["state"]}
        self.operation_state.set("Owned session ended ({}). Its evidence is preserved and nothing will be replayed.".format(observed["state"]))
        self._refresh_status()
        return True

    def choose_journal(self):
        if self.closed:
            return False
        path = self._dialog("askopenfilename", title="Inspect existing journal without replay",
                                          filetypes=(("Journal JSONL", "*.jsonl"),))
        if path is None:
            return False
        return self.inspect_journal(path) if path else self._selection_cancelled()

    def inspect_journal(self, path):
        if self.closed:
            return False
        self.inspected_path = path
        self.inspected_sha256 = None
        self.journal_summary = None
        self.last_result = None
        try:
            result = self.journal_api.inspect_journal(path)
            self.journal_summary = self._safe_journal(result)
            self.inspected_sha256 = self.journal_summary["sha256"]
            if self.inspected_sha256 is None:
                raise ValueError("Journal inspection did not return a source identity")
        except Exception:
            self.journal_summary = None
            self.inspected_sha256 = None
            self.journal_state.set("Journal inspection unavailable. No prefix recovery or replay is enabled.")
            return self._fail("journal_inspection_failed", "Journal inspection failed; no stale recovery authority is retained.")
        self.last_error = None
        self.last_result = {"operation": "journal_inspection", "state": "observed"}
        self.journal_state.set("Verified records: {} | Recovery required: {} | No replay or resumed ownership".format(
            self.journal_summary.get("verified_records"), self.journal_summary.get("recovery_required")))
        self._refresh_status()
        return True

    @staticmethod
    def _safe_journal(result):
        if not isinstance(result, dict):
            raise ValueError("Invalid journal inspection")
        summary = {"sha256": _digest(result.get("source_sha256")),
                   "verified_records": _number(result.get("verified_count")),
                   "verified_bytes": _number(result.get("verified_bytes")),
                   "total_bytes": _number(result.get("source_bytes")),
                   "replay_allowed": False}
        for key in ("valid", "clean_end", "recovery_required"):
            value = result.get(key)
            summary[key] = value if type(value) is bool else None
        summary["state"] = "clean_end" if summary["clean_end"] else "open_or_interrupted" if summary["valid"] else "invalid_tail"
        # Provider text and event bodies are deliberately not copied to the UI
        # summary. An invalid tail is not by itself evidence of a game crash.
        summary["issue"] = "unverified_tail" if result.get("error") else None
        if summary["sha256"] is None or type(summary["verified_records"]) is not int or \
                summary["verified_records"] < 0 or type(summary["verified_bytes"]) is not int or \
                type(summary["total_bytes"]) is not int or not 0 <= summary["verified_bytes"] <= summary["total_bytes"] or \
                any(type(summary[key]) is not bool for key in ("valid", "clean_end", "recovery_required")):
            raise ValueError("Journal inspection contract is incomplete")
        return summary

    def recover(self):
        if self.closed or self.inspected_path is None or self.inspected_sha256 is None or \
                not self.journal_summary or (self.journal_summary.get("verified_records") or 0) < 1:
            return self._fail("journal_not_inspected", "Inspect a journal with a verified complete prefix before creating a recovery copy.")
        destination = self._dialog("asksaveasfilename",
                title="Create NEW verified-prefix copy (original will be retained)", defaultextension=".jsonl",
                filetypes=(("Journal JSONL", "*.jsonl"),))
        if destination is None:
            return False
        if not destination:
            return self._selection_cancelled()
        self.last_result = None
        try:
            receipt = self.journal_api.recover_journal(self.inspected_path, destination,
                                                     expected_sha256=self.inspected_sha256)
            if not isinstance(receipt, dict) or receipt.get("source_sha256") != self.inspected_sha256 or \
                    _digest(receipt.get("destination_sha256")) is None or receipt.get("replay_allowed") is not False or \
                    type(receipt.get("verified_count")) is not int or receipt["verified_count"] < 1:
                raise ValueError("Invalid recovery receipt")
        except Exception:
            self.inspected_sha256 = None
            self.journal_summary = None
            self.journal_state.set("Recovery source identity must be reinspected. No stale recovery authority is retained.")
            return self._fail("journal_recovery_failed", "Recovery copy was not acknowledged. Original evidence is retained; source drift or existing destinations are refused.")
        self.last_error = None
        self.last_result = {"operation": "prefix_recovery", "state": "observed", "evidence_only": True,
                            "source_sha256": self.inspected_sha256}
        self.last_result["verified_records"] = _number(receipt.get("verified_count"))
        for key in ("verified_bytes", "discarded_tail_bytes"):
            self.last_result[key] = _number(receipt.get(key))
        self.last_result["destination_sha256"] = _digest(receipt.get("destination_sha256"))
        self.operation_state.set("Verified-prefix evidence copy created without overwriting the original. No actions replayed or session resumed.")
        self._status("Journal prefix copied as evidence only; no automatic replay.")
        self._refresh_status()
        return True

    def reload(self):
        if self.closed:
            return False
        self._refresh_status()
        return self.inspect_journal(self.inspected_path) if self.inspected_path is not None else True

    def copy_summary(self):
        if self.closed:
            return False
        self._refresh_status()
        try:
            payload = json.dumps(self.summary(), indent=2, ensure_ascii=False, allow_nan=False)
            root = self.parent.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(payload)
        except Exception:
            return self._fail("clipboard_unavailable", "Sanitized summary could not be copied.")
        self._status("Copied sanitized offline session summary; no paths or raw payloads.")
        return payload

    def open_evidence(self):
        if self.closed or self.evidence_factory is None:
            return False
        window = self.tk.Toplevel(self.parent.winfo_toplevel())
        window.title("Saved crash evidence — offline only")
        window.geometry("940x620")
        try:
            panel = self.evidence_factory(window, self._status)
        except Exception:
            window.destroy()
            return self._fail("evidence_unavailable", "Optional saved-evidence view unavailable; existing session features remain usable.")
        self.evidence_windows.append((window, panel))
        feedback = getattr(self.parent.winfo_toplevel(),"game_tools_feedback",None)
        if feedback is not None: feedback.register_panel(window,"UI-302",panel)
        def close_window():
            panel.close()
            window.destroy()
        window.protocol("WM_DELETE_WINDOW", close_window)
        return panel

    def open_workflow(self):
        if self.closed or self.workflow_factory is None:
            return False
        window = self.tk.Toplevel(self.parent.winfo_toplevel())
        window.title("Workflow dry-runs — no execution")
        window.geometry("940x650")
        try:
            panel = self.workflow_factory(window, self._status)
        except Exception:
            window.destroy()
            return self._fail("workflow_unavailable", "Optional workflow preview unavailable; existing session features remain usable.")
        self.evidence_windows.append((window, panel))
        feedback = getattr(self.parent.winfo_toplevel(),"game_tools_feedback",None)
        if feedback is not None: feedback.register_panel(window,"UI-303",panel)
        def close_window():
            panel.close()
            window.destroy()
        window.protocol("WM_DELETE_WINDOW", close_window)
        return panel

    def open_readiness(self):
        if self.closed or self.readiness_factory is None:
            return False
        window = self.tk.Toplevel(self.parent.winfo_toplevel())
        window.title("Provider health / editable scenarios — offline only")
        window.geometry("1000x760")
        try:
            panel = self.readiness_factory(window, self._status)
        except Exception:
            window.destroy()
            return self._fail("readiness_unavailable", "Optional contract view unavailable; existing session features remain usable.")
        self.evidence_windows.append((window, panel))
        feedback = getattr(self.parent.winfo_toplevel(),"game_tools_feedback",None)
        if feedback is not None: feedback.register_panel(window,"UI-304",panel)
        def close_window():
            panel.close()
            window.destroy()
        window.protocol("WM_DELETE_WINDOW", close_window)
        return panel

    def close(self):
        """Only owned coordinator resources; no external process or profile action."""
        if self.closed and self.close_result is True:
            return True
        for window, panel in self.evidence_windows:
            try:
                panel.close()
                if window.winfo_exists():
                    window.destroy()
            except Exception:
                pass
        self.evidence_windows = []
        succeeded = True
        if self.coordinator is not None:
            try:
                observed = self.coordinator.close()
                if not isinstance(observed, dict) or observed.get("state") == "failed" or observed.get("writer_open") is True:
                    raise ValueError("Terminal session evidence not acknowledged")
            except Exception:
                succeeded = False
                self.last_error = "session_close_unacknowledged"
                self.last_result = None
        self.closed = True
        self.close_result = succeeded
        self._refresh_status()
        return succeeded
