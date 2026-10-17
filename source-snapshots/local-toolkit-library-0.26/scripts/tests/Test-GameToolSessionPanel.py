"""Withdrawn Tk offline-session contracts; no live desktop or game control.

Dialogs/clipboard are mocked. Files are authored temporary fixtures. These
tests verify widget callbacks, not game acceptance, crash causes or profiles.
"""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]


def load_source(name):
    spec = importlib.util.spec_from_file_location("session_panel_contract_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


panel_module = load_source("GameToolSessionPanel")


class FixtureCoordinator:
    def __init__(self, owner, lifetime_seconds):
        self.calls = []
        self.failure = None
        self.path = None
        self.state = {"schema_version": 1, "coordinator_version": "fixture-only", "state": "idle",
                      "owner": owner, "owner_id": "fixture-owner", "session_id": None, "phase": None,
                      "lifetime_seconds": lifetime_seconds, "remaining_seconds": None,
                      "journal_records": 0, "latest_action": None, "execution": "offline_only", "writer_open": False}

    def _call(self, name, *arguments):
        self.calls.append((name, *arguments))
        if self.failure == name:
            raise ValueError("private fixture error C:/private/report.json TOKEN_TYPED_PAYLOAD")

    def status(self):
        self._call("status")
        return dict(self.state)

    def start(self, path, label):
        self._call("start", path, label)
        self.path = Path(path)
        with self.path.open("xb") as handle:
            handle.write(b"authored fixture journal\n")
        self.state.update(state="active", label=label, session_id="fixture-session",
                          remaining_seconds=900, journal_records=1, writer_open=True)
        return self.status()

    def checkpoint(self, phase):
        self._call("checkpoint", phase)
        self.state.update(phase=phase, journal_records=self.state["journal_records"] + 1)
        return self.status()

    def inspect_saved_report(self, source, adapter="auto", expected_sha256=None):
        self._call("saved_report", source, adapter, expected_sha256)
        digest = hashlib.sha256(Path(source).read_bytes()).hexdigest()
        self.state["latest_action"] = {"id": "fixture-action", "capability": "saved_report", "state": "observed",
                                       "source_sha256": digest, "verdict": "unverified"}
        return {"adapter": "fixture", "adapter_revision": "0.0.0", "provider_outcome": "not_reported",
                "private_source": {"path": str(source)}, "raw_metadata": {"secret": "TOKEN_TYPED_PAYLOAD"}}

    def inspect_comparison(self, source, metric=None, expected_sha256=None):
        self._call("comparison", source, metric, expected_sha256)
        return {"status": "BLOCKED", "raw_runs": [{"payload": "TOKEN_TYPED_PAYLOAD"}]}

    def finish(self):
        self._call("finish")
        self.state.update(state="finished", remaining_seconds=0, writer_open=False)
        return self.status()

    def cancel(self, reason="user"):
        self._call("cancel", reason)
        self.state.update(state="cancelled", remaining_seconds=0, writer_open=False)
        return self.status()

    def close(self):
        self._call("close")
        if self.state["state"] == "active":
            self.state.update(state="cancelled", remaining_seconds=0, writer_open=False)
        return self.status()


class FixtureJournal:
    def __init__(self):
        self.calls = []
        self.failure = None
        self.valid = True
        self.clean = False
        self.count = 1

    def inspect_journal(self, source):
        self.calls.append(("inspect", source))
        if self.failure == "inspect":
            raise ValueError("private source C:/private/journal.jsonl")
        raw = Path(source).read_bytes()
        return {"valid": self.valid, "clean_end": self.clean,
                "verified_records": [{"data": {"private": "TOKEN_TYPED_PAYLOAD"}}],
                "verified_count": self.count, "verified_bytes": len(raw), "source_bytes": len(raw),
                "source_sha256": hashlib.sha256(raw).hexdigest(), "error": None if self.valid else "private error",
                "recovery_required": not self.valid, "replay_allowed": False, "source_path": str(source)}

    def recover_journal(self, source, destination, expected_sha256=None):
        self.calls.append(("recover", source, destination, expected_sha256))
        if self.failure == "recover":
            raise ValueError("private recovery error")
        raw = Path(source).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected_sha256:
            raise ValueError("Source drift")
        with Path(destination).open("xb") as handle:
            handle.write(raw)
        return {"source_sha256": digest, "destination_sha256": digest,
                "verified_count": self.count, "verified_bytes": len(raw), "discarded_tail_bytes": 0,
                "replay_allowed": False, "private_source": str(source)}


class PanelContracts(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from tkinter import ttk
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Native Tk unavailable; widget acceptance not established: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.temp = tempfile.TemporaryDirectory(prefix="session-panel-fixtures-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "private-fixture.json"
        self.source.write_bytes(b'{"fixture":"not measured"}')
        self.journal_path = self.directory / "owned-new.jsonl"
        self.parent = ttk.Frame(self.root)
        self.parent.pack()
        self.status = tk.StringVar(master=self.root)
        self.factory_calls = []
        self.coordinators = []

        def factory(**options):
            self.factory_calls.append(options)
            value = FixtureCoordinator(**options)
            self.coordinators.append(value)
            return value

        self.factory = factory
        self.journal = FixtureJournal()
        self.safety = ExitStack()
        self.addCleanup(self.safety.close)
        self.clipboard = []
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_clear", side_effect=self.clipboard.clear))
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_append", side_effect=self.clipboard.append))
        self.panel = panel_module.SessionPanel(self.parent, self.factory, self.journal, self.status)
        self.addCleanup(self.panel.close)

    @property
    def core(self):
        return self.panel.coordinator

    def start(self):
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(self.journal_path)):
            self.assertTrue(self.panel.new_session())

    def choose_saved(self, comparison=False):
        with mock.patch("tkinter.filedialog.askopenfilename", return_value=str(self.source)):
            return self.panel.inspect_comparison() if comparison else self.panel.inspect_saved_report()

    def recover_to(self, destination):
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(destination)):
            return self.panel.recover()

    def real_coordinator(self, **options):
        """Fixed sibling implementation, still only authored temporary data."""
        module = load_source("GameToolCoordinator")
        self.panel.coordinator.close()
        self.panel.coordinator = module.Coordinator(owner="Hub", **options)
        self.panel.coordinator_factory = module.Coordinator
        self.panel.journal_api = load_source("GameToolJournal")
        self.panel.current_status = self.panel.coordinator.status()
        return self.panel.coordinator

    def test_constructor_is_inert_and_withdrawn(self):
        self.assertEqual(self.root.state(), "withdrawn")
        self.assertEqual(self.factory_calls, [{"owner": "Hub", "lifetime_seconds": 900}])
        self.assertEqual(self.core.calls, [])
        self.assertEqual(self.journal.calls, [])
        self.assertEqual(self.clipboard, [])
        self.assertFalse(self.journal_path.exists())

    def test_controls_are_explicit_offline_only(self):
        self.assertEqual(set(self.panel.buttons), {"Workflow dry-runs", "Saved crash evidence", "New offline session", "Inspect saved report", "Inspect comparison",
                         "Finish", "Cancel session", "Refresh status", "Inspect journal", "Recover verified prefix",
                         "Copy summary", "Checkpoint", "Provider / scenario contracts"})
        self.assertEqual(str(self.panel.buttons["New offline session"].cget("state")), "normal")
        for key in ("Inspect saved report", "Inspect comparison", "Finish", "Cancel session", "Checkpoint", "Recover verified prefix"):
            self.assertEqual(str(self.panel.buttons[key].cget("state")), "disabled")

    def test_summary_is_readonly_and_scrollable(self):
        self.assertEqual(self.panel.summary_text.cget("state"), "disabled")
        self.assertEqual(self.panel.summary_text.cget("wrap"), "none")
        self.assertTrue(self.panel.summary_text.cget("yscrollcommand"))
        self.assertTrue(self.panel.summary_text.cget("xscrollcommand"))

    def test_start_dialog_cancel_creates_nothing(self):
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=""):
            self.assertFalse(self.panel.new_session())
        self.assertFalse(self.journal_path.exists())
        self.assertFalse(any(call[0] == "start" for call in self.core.calls))

    def test_start_dialog_failure_is_contained_without_action(self):
        with mock.patch("tkinter.filedialog.asksaveasfilename", side_effect=RuntimeError("private path")):
            self.assertFalse(self.panel.new_session())
        self.assertEqual(self.panel.last_error, "dialog_unavailable")
        self.assertFalse(self.journal_path.exists())

    def test_start_creates_only_selected_new_file_and_shows_owner(self):
        self.start()
        self.assertEqual(self.journal_path.read_bytes(), b"authored fixture journal\n")
        self.assertEqual(self.core.state["state"], "active")
        self.assertIn("Owner: Hub", self.panel.owner_state.get())
        self.assertEqual(str(self.panel.buttons["New offline session"].cget("state")), "disabled")
        self.assertEqual(str(self.panel.buttons["Inspect saved report"].cget("state")), "normal")

    def test_active_session_refuses_second_start_without_dialog(self):
        self.start()
        with mock.patch("tkinter.filedialog.asksaveasfilename", side_effect=AssertionError("must not ask")):
            self.assertFalse(self.panel.new_session())
        self.assertEqual(len(self.coordinators), 1)
        self.assertEqual(self.core.state["state"], "active")

    def test_existing_destination_preserved_and_no_stale_start_success(self):
        self.journal_path.write_bytes(b"preserved prior journal")
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(self.journal_path)):
            self.assertFalse(self.panel.new_session())
        self.assertEqual(self.journal_path.read_bytes(), b"preserved prior journal")
        self.assertIsNone(self.panel.last_result)
        self.assertEqual(self.panel.last_error, "session_start_failed")

    def test_start_failure_exception_does_not_leak(self):
        self.core.failure = "start"
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(self.journal_path)):
            self.assertFalse(self.panel.new_session())
        self.assertNotIn("C:/private", self.panel.summary_text.get("1.0", "end"))
        self.assertNotIn("TOKEN_TYPED_PAYLOAD", self.status.get())

    def test_checkpoint_requires_owned_active_session(self):
        self.assertFalse(self.panel.checkpoint())
        self.assertFalse(any(call[0] == "checkpoint" for call in self.core.calls))

    def test_checkpoint_fixed_phase_updates_owned_state(self):
        self.start()
        self.panel.phase.set("saved_data.review-1")
        self.panel.buttons["Checkpoint"].invoke()
        self.assertEqual(self.core.state["phase"], "saved_data.review-1")
        self.assertEqual(self.panel.last_result["operation"], "checkpoint")

    def test_invalid_phase_and_paths_never_dispatch(self):
        self.start()
        for phase in ("", "C:/private/file", "typed text payload", "x" * 65, "1starts-number", "phase\nnext"):
            self.panel.phase.set(phase)
            self.assertFalse(self.panel.checkpoint())
        self.assertFalse(any(call[0] == "checkpoint" for call in self.core.calls))

    def test_checkpoint_failure_clears_old_success(self):
        self.start()
        self.core.failure = "checkpoint"
        self.assertFalse(self.panel.checkpoint())
        self.assertIsNone(self.panel.last_result)
        self.assertEqual(self.panel.last_error, "checkpoint_failed")

    def test_no_saved_inspection_without_session_or_dialog(self):
        with mock.patch("tkinter.filedialog.askopenfilename", side_effect=AssertionError("must not ask")):
            self.assertFalse(self.panel.inspect_saved_report())
            self.assertFalse(self.panel.inspect_comparison())
        self.assertFalse(any(call[0] in ("saved_report", "comparison") for call in self.core.calls))

    def test_saved_report_is_read_only_and_copies_no_payload(self):
        self.start()
        before = self.source.read_bytes()
        self.assertTrue(self.choose_saved())
        self.assertEqual(self.source.read_bytes(), before)
        text = self.panel.copy_summary()
        self.assertNotIn(str(self.source), text)
        self.assertNotIn("TOKEN_TYPED_PAYLOAD", text)
        self.assertEqual(json.loads(text)["last_operation"]["adapter"], "fixture")
        self.assertFalse(json.loads(text)["session"]["runtime_verification"])

    def test_comparison_blocked_is_inspection_not_runtime_pass(self):
        self.start()
        self.assertTrue(self.choose_saved(comparison=True))
        self.assertEqual(self.panel.last_result["status"], "BLOCKED")
        self.assertFalse(self.panel.last_result["runtime_verification"])
        self.assertNotIn("TOKEN_TYPED_PAYLOAD", self.panel.copy_summary())

    def test_saved_dialog_cancel_clears_old_operation(self):
        self.start()
        with mock.patch("tkinter.filedialog.askopenfilename", return_value=""):
            self.assertFalse(self.panel.inspect_saved_report())
        self.assertIsNone(self.panel.last_result)
        self.assertIn("cancelled", self.panel.operation_state.get())

    def test_saved_inspection_failure_clears_success_and_keeps_source(self):
        self.start()
        self.assertTrue(self.choose_saved())
        before = self.source.read_bytes()
        self.core.failure = "saved_report"
        self.assertFalse(self.choose_saved())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertIsNone(self.panel.last_result)
        self.assertEqual(self.panel.last_error, "saved_inspection_failed")

    def test_malformed_saved_result_cannot_claim_observation(self):
        self.start()
        with mock.patch.object(self.core, "inspect_saved_report", return_value={}), \
                mock.patch("tkinter.filedialog.askopenfilename", return_value=str(self.source)):
            self.assertFalse(self.panel.inspect_saved_report())
        with mock.patch.object(self.core, "inspect_comparison", return_value={}), \
                mock.patch("tkinter.filedialog.askopenfilename", return_value=str(self.source)):
            self.assertFalse(self.panel.inspect_comparison())

    def test_finish_stops_only_owned_session(self):
        self.start()
        before = self.source.read_bytes()
        self.assertTrue(self.panel.finish())
        self.assertEqual(self.core.state["state"], "finished")
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(str(self.panel.buttons["Inspect comparison"].cget("state")), "disabled")

    def test_cancel_is_scoped_and_no_replay(self):
        self.start()
        self.assertTrue(self.panel.cancel())
        self.assertIn(("cancel", "user"), self.core.calls)
        self.assertEqual(self.core.state["state"], "cancelled")
        self.assertIn("nothing will be replayed", self.panel.operation_state.get())

    def test_cancel_without_active_session_does_not_dispatch(self):
        self.assertFalse(self.panel.cancel())
        self.assertFalse(any(call[0] == "cancel" for call in self.core.calls))

    def test_finish_failure_does_not_claim_success(self):
        self.start()
        self.core.failure = "finish"
        self.assertFalse(self.panel.finish())
        self.assertIsNone(self.panel.last_result)
        self.assertEqual(self.panel.last_error, "session_finish_failed")

    def test_terminal_restart_uses_fresh_inert_coordinator_and_new_file(self):
        self.start()
        old = self.core
        self.assertTrue(self.panel.finish())
        newer = self.directory / "another-new.jsonl"
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(newer)):
            self.assertTrue(self.panel.new_session())
        self.assertIsNot(old, self.core)
        self.assertTrue(any(call[0] == "close" for call in old.calls))
        self.assertTrue(newer.exists())
        self.assertEqual(len(self.coordinators), 2)

    def test_expiry_disables_actions_without_replaying_or_writing(self):
        self.start()
        self.core.state.update(state="expired", remaining_seconds=0)
        self.core.calls.clear()
        self.assertTrue(self.panel.reload())
        self.assertEqual(self.core.calls, [("status",)])
        self.assertEqual(str(self.panel.buttons["Checkpoint"].cget("state")), "disabled")
        self.assertFalse(self.panel.checkpoint())
        self.assertFalse(any(call[0] == "checkpoint" for call in self.core.calls))

    def test_expired_session_cancel_still_releases_only_owner(self):
        self.start()
        self.core.state.update(state="expired", remaining_seconds=0)
        self.assertTrue(self.panel.cancel())
        self.assertIn(("cancel", "user"), self.core.calls)

    def test_initial_reload_reads_no_unspecified_file(self):
        self.assertTrue(self.panel.reload())
        self.assertEqual(self.core.calls, [("status",)])
        self.assertEqual(self.journal.calls, [])

    def test_journal_selection_cancel_does_not_read_any_source(self):
        with mock.patch("tkinter.filedialog.askopenfilename", return_value=""):
            self.assertFalse(self.panel.choose_journal())
        self.assertEqual(self.journal.calls, [])

    def test_explicit_journal_inspection_keeps_open_state_separate_from_crash(self):
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        summary = self.panel.journal_summary
        self.assertEqual(summary["verified_records"], 1)
        self.assertEqual(summary["state"], "open_or_interrupted")
        self.assertFalse(summary["recovery_required"])
        self.assertFalse(summary["replay_allowed"])
        self.assertEqual(self.core.calls, [("status",)])
        self.assertNotIn("TOKEN_TYPED_PAYLOAD", self.panel.copy_summary())

    def test_clean_journal_summary_is_not_resumed(self):
        self.journal.clean = True
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        self.assertEqual(self.panel.journal_summary["state"], "clean_end")
        self.assertFalse(any(call[0] == "start" for call in self.core.calls))

    def test_invalid_tail_displays_need_for_prefix_recovery(self):
        self.journal.valid = False
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        self.assertEqual(self.panel.journal_summary["state"], "invalid_tail")
        self.assertTrue(self.panel.journal_summary["recovery_required"])
        self.assertEqual(self.panel.journal_summary["issue"], "unverified_tail")

    def test_journal_load_failure_drops_previous_recovery_authority(self):
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        self.journal.failure = "inspect"
        self.assertFalse(self.panel.inspect_journal(str(self.source)))
        self.assertIsNone(self.panel.inspected_sha256)
        self.assertIsNone(self.panel.journal_summary)
        self.assertEqual(str(self.panel.buttons["Recover verified prefix"].cget("state")), "disabled")

    def test_malformed_journal_inspection_is_not_accepted(self):
        with mock.patch.object(self.journal, "inspect_journal", return_value={"source_sha256": "a" * 64}):
            self.assertFalse(self.panel.inspect_journal(str(self.source)))
        self.assertIsNone(self.panel.inspected_sha256)

    def test_recovery_requires_previous_bound_inspection(self):
        with mock.patch("tkinter.filedialog.asksaveasfilename", side_effect=AssertionError("must not ask")):
            self.assertFalse(self.panel.recover())
        self.assertFalse(any(call[0] == "recover" for call in self.journal.calls))

    def test_recovery_copy_passes_bound_hash_and_preserves_original(self):
        before = self.source.read_bytes()
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        digest = self.panel.inspected_sha256
        destination = self.directory / "verified-copy.jsonl"
        self.assertTrue(self.recover_to(destination))
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(destination.read_bytes(), before)
        self.assertIn(("recover", str(self.source), str(destination), digest), self.journal.calls)
        self.assertTrue(self.panel.last_result["evidence_only"])
        self.assertFalse(any(call[0] == "start" for call in self.core.calls))

    def test_recovery_source_drift_fails_without_new_file(self):
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        self.source.write_bytes(b"changed after inspection")
        destination = self.directory / "should-not-exist.jsonl"
        self.assertFalse(self.recover_to(destination))
        self.assertFalse(destination.exists())
        self.assertIsNone(self.panel.last_result)
        self.assertIsNone(self.panel.inspected_sha256)
        self.assertIsNone(self.panel.journal_summary)
        self.assertEqual(str(self.panel.buttons["Recover verified prefix"].cget("state")), "disabled")

    def test_recovery_existing_destination_is_never_overwritten(self):
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        destination = self.directory / "preserved.jsonl"
        destination.write_bytes(b"prior unrelated evidence")
        self.assertFalse(self.recover_to(destination))
        self.assertEqual(destination.read_bytes(), b"prior unrelated evidence")
        self.assertIsNone(self.panel.last_result)

    def test_recovery_dialog_cancel_clears_prior_success(self):
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=""):
            self.assertFalse(self.panel.recover())
        self.assertIsNone(self.panel.last_result)
        self.assertFalse(any(call[0] == "recover" for call in self.journal.calls))

    def test_recovery_incomplete_receipt_is_not_acknowledged(self):
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        with mock.patch.object(self.journal, "recover_journal", return_value={}):
            self.assertFalse(self.recover_to(self.directory / "copy.jsonl"))
        self.assertEqual(self.panel.last_error, "journal_recovery_failed")

    def test_reload_only_selected_journal_and_updates_hash(self):
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        old = self.panel.inspected_sha256
        self.source.write_bytes(b"explicit fixture change")
        self.assertTrue(self.panel.reload())
        self.assertNotEqual(self.panel.inspected_sha256, old)
        self.assertEqual(self.journal.calls, [("inspect", str(self.source)), ("inspect", str(self.source))])

    def test_sanitized_clipboard_omits_unknown_fields_paths_and_nonfinite(self):
        self.core.state.update(owner="C:/private/owner", phase="typed\npayload", remaining_seconds=float("nan"),
                               private_payload="TOKEN_TYPED_PAYLOAD", latest_action={"id": "normal-id", "state": "observed",
                               "error_code": "secret/private/path", "source_sha256": "invalid", "secret": "TOKEN_TYPED_PAYLOAD"})
        payload = self.panel.copy_summary()
        self.assertEqual(self.clipboard, [payload])
        self.assertNotIn("C:/private", payload)
        self.assertNotIn("TOKEN_TYPED_PAYLOAD", payload)
        self.assertNotIn("secret/private", payload)
        self.assertIsNone(json.loads(payload)["session"]["remaining_seconds"])

    def test_clipboard_failure_is_contained(self):
        with mock.patch.object(self.root, "clipboard_append", side_effect=RuntimeError("private")):
            self.assertFalse(self.panel.copy_summary())
        self.assertEqual(self.panel.last_error, "clipboard_unavailable")

    def test_status_failure_disables_owned_actions(self):
        self.start()
        self.core.failure = "status"
        self.panel.reload()
        self.assertEqual(self.panel.current_status["state"], "unavailable")
        self.assertEqual(str(self.panel.buttons["Checkpoint"].cget("state")), "disabled")
        self.assertEqual(self.panel.last_error, "status_unavailable")
        self.core.failure = None

    def test_close_is_idempotent_and_only_owned_resource(self):
        self.start()
        self.assertTrue(self.panel.close())
        self.assertTrue(self.panel.close())
        self.assertEqual(sum(call[0] == "close" for call in self.core.calls), 1)
        self.assertTrue(self.panel.closed)
        self.assertFalse(self.panel.reload())
        self.assertFalse(self.panel.copy_summary())
        self.assertFalse(self.panel.new_session())

    def test_close_failure_does_not_claim_acknowledgement(self):
        self.start()
        self.core.failure = "close"
        self.assertFalse(self.panel.close())
        self.assertTrue(self.panel.closed)
        self.assertEqual(self.panel.last_error, "session_close_unacknowledged")
        self.assertIsNone(self.panel.last_result)

    def test_factory_failure_is_contained_and_journal_inspection_still_available(self):
        def unavailable(**options):
            raise RuntimeError("C:/private/factory")
        other = panel_module.SessionPanel(self.parent, unavailable, self.journal, self.status)
        self.addCleanup(other.close)
        self.assertIsNone(other.coordinator)
        self.assertEqual(other.last_error, "coordinator_unavailable")
        self.assertTrue(other.inspect_journal(str(self.source)))
        self.assertFalse(other.new_session())

    def test_failed_session_cancel_is_disabled_and_never_claimed(self):
        self.start()
        self.core.state["state"] = "failed"
        self.panel.reload()
        self.assertEqual(str(self.panel.buttons["Cancel session"].cget("state")), "disabled")
        self.assertFalse(self.panel.cancel())
        self.assertFalse(any(call[0] == "cancel" for call in self.core.calls))
        self.assertIsNone(self.panel.last_result)

    def test_wrong_creation_state_cannot_claim_success(self):
        with mock.patch.object(self.core, "start", return_value={"state": "failed"}), \
                mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(self.journal_path)):
            self.assertFalse(self.panel.new_session())
        self.assertEqual(self.panel.last_error, "session_start_failed")
        self.assertIsNone(self.panel.last_result)

    def test_wrong_finish_state_cannot_claim_terminal_event(self):
        self.start()
        with mock.patch.object(self.core, "finish", return_value={"state": "failed"}):
            self.assertFalse(self.panel.finish())
        self.assertEqual(self.panel.last_error, "session_finish_failed")
        self.assertIsNone(self.panel.last_result)

    def test_wrong_cancel_state_cannot_claim_terminal_event(self):
        self.start()
        with mock.patch.object(self.core, "cancel", return_value={"state": "failed"}):
            self.assertFalse(self.panel.cancel())
        self.assertEqual(self.panel.last_error, "session_cancel_failed")
        self.assertIsNone(self.panel.last_result)

    def test_zero_verified_prefix_does_not_offer_recovery_dialog(self):
        self.journal.count = 0
        self.journal.valid = False
        self.assertTrue(self.panel.inspect_journal(str(self.source)))
        with mock.patch("tkinter.filedialog.asksaveasfilename", side_effect=AssertionError("must not ask")):
            self.assertFalse(self.panel.recover())
        self.assertEqual(str(self.panel.buttons["Recover verified prefix"].cget("state")), "disabled")

    def test_genuine_coordinator_saved_data_lifecycle_preserves_sources(self):
        core = self.real_coordinator()
        fixture = SCRIPTS.parent / "examples/game-tool-hub/import-fixtures/cyberpunk-summary.example.json"
        self.source.write_bytes(fixture.read_bytes())
        before = self.source.read_bytes()
        self.start()
        self.assertTrue(self.panel.checkpoint())
        self.assertTrue(self.choose_saved())
        self.assertEqual(self.panel.last_result["adapter"], "cyberpunk_benchmark_summary")
        self.assertFalse(self.panel.last_result["runtime_verification"])
        comparison = self.directory / "comparison-fixture.json"
        comparison.write_bytes((SCRIPTS.parent / "examples/game-tool-hub/comparison-fixture.example.json").read_bytes())
        with mock.patch("tkinter.filedialog.askopenfilename", return_value=str(comparison)):
            self.assertTrue(self.panel.inspect_comparison())
        self.assertTrue(self.panel.finish())
        self.assertEqual(core.status()["state"], "finished")
        self.assertEqual(self.source.read_bytes(), before)
        inspected = self.panel.journal_api.inspect_journal(self.journal_path)
        self.assertTrue(inspected["valid"])
        self.assertTrue(inspected["clean_end"])
        self.assertEqual(inspected["verified_count"], 8)
        self.assertNotIn(str(self.source), self.panel.copy_summary())

    def test_genuine_creation_failure_preserves_existing_journal_and_cannot_cancel(self):
        self.real_coordinator()
        self.journal_path.write_bytes(b"preserve existing unrelated journal")
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(self.journal_path)):
            self.assertFalse(self.panel.new_session())
        self.assertEqual(self.journal_path.read_bytes(), b"preserve existing unrelated journal")
        self.assertEqual(self.core.status()["state"], "failed")
        self.assertEqual(str(self.panel.buttons["Cancel session"].cget("state")), "disabled")
        self.assertFalse(self.panel.cancel())
        self.assertIsNone(self.panel.last_result)

    def test_genuine_terminal_journal_failure_is_not_finish_or_cancel_success(self):
        self.real_coordinator()
        self.start()
        with mock.patch.object(self.core._journal, "append", side_effect=OSError("fixture storage failure")):
            self.assertFalse(self.panel.finish())
        self.assertEqual(self.core.status()["state"], "failed")
        self.assertEqual(self.panel.last_error, "session_finish_failed")
        self.assertIsNone(self.panel.last_result)
        self.assertFalse(self.panel.cancel())
        self.assertEqual(str(self.panel.buttons["Cancel session"].cget("state")), "disabled")
        evidence = self.panel.journal_api.inspect_journal(self.journal_path)
        self.assertTrue(evidence["valid"])
        self.assertFalse(evidence["clean_end"])
        self.assertFalse(self.panel.close())

    def test_genuine_cancel_storage_failure_is_not_acknowledged(self):
        self.real_coordinator()
        self.start()
        with mock.patch.object(self.core._journal, "append", side_effect=OSError("fixture storage failure")):
            self.assertFalse(self.panel.cancel())
        self.assertEqual(self.core.status()["state"], "failed")
        self.assertEqual(self.panel.last_error, "session_cancel_failed")
        self.assertIsNone(self.panel.last_result)
        self.assertFalse(self.panel.journal_api.inspect_journal(self.journal_path)["clean_end"])

    def test_genuine_expiry_is_readonly_until_explicit_cancel(self):
        current = [100.0]
        self.real_coordinator(lifetime_seconds=1, clock=lambda: current[0])
        self.start()
        before = self.journal_path.read_bytes()
        current[0] = 102.0
        self.assertTrue(self.panel.reload())
        self.assertEqual(self.panel.current_status["state"], "expired")
        self.assertEqual(self.journal_path.read_bytes(), before)
        self.assertTrue(self.panel.cancel())
        self.assertEqual(self.panel.last_result["owned_state"], "expired")
        self.assertIn("ended (expired)", self.panel.operation_state.get())
        self.assertTrue(self.panel.journal_api.inspect_journal(self.journal_path)["clean_end"])

    def test_genuine_writer_cleanup_failure_preserves_owner_until_retry(self):
        core = self.real_coordinator()
        self.start()
        writer = core._journal
        with mock.patch.object(writer, "close", side_effect=OSError("fixture cleanup failure")):
            self.assertFalse(self.panel.cancel())
            self.assertTrue(core.status()["writer_open"])
            destination = self.directory / "not-created-before-release.jsonl"
            with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(destination)):
                self.assertFalse(self.panel.new_session())
            self.assertIs(self.panel.coordinator, core)
            self.assertIs(core._journal, writer)
            self.assertFalse(destination.exists())
        with mock.patch("tkinter.filedialog.asksaveasfilename", return_value=str(destination)):
            self.assertTrue(self.panel.new_session())
        self.assertIsNot(self.panel.coordinator, core)
        self.assertFalse(core.status()["writer_open"])
        self.assertTrue(destination.exists())

    def test_genuine_failed_close_retries_owned_handle_without_false_acknowledgment(self):
        core = self.real_coordinator()
        self.start()
        writer = core._journal
        with mock.patch.object(writer, "close", side_effect=OSError("fixture cleanup failure")):
            self.assertFalse(self.panel.close())
            self.assertTrue(core.status()["writer_open"])
            self.assertFalse(self.panel.close())
        self.assertFalse(self.panel.close())  # Cleanup succeeds; missing terminal acceptance stays failed.
        self.assertFalse(core.status()["writer_open"])
        self.assertEqual(self.panel.last_error, "session_close_unacknowledged")

    def test_oversized_integer_is_omitted_in_compact_ui(self):
        self.core.state["remaining_seconds"] = 10 ** 1000
        payload = self.panel.copy_summary()
        self.assertIsNone(json.loads(payload)["session"]["remaining_seconds"])

    def test_status_callback_failure_does_not_break_valid_inspection(self):
        def broken_status(message):
            raise RuntimeError("Optional sink failed")
        self.panel.status_callback = broken_status
        self.assertTrue(self.panel.inspect_journal(str(self.source)))

    def test_genuine_journal_prefix_recovery_without_replay(self):
        journal_api = load_source("GameToolJournal")
        genuine = self.directory / "genuine-interrupted.jsonl"
        writer = journal_api.Journal.create(genuine, {"fixture": "offline only"})
        writer.append("phase_marker", {"phase": "review"})
        writer.close()
        with genuine.open("ab") as handle:
            handle.write(b'{"incomplete_tail":')
        original = genuine.read_bytes()
        self.panel.journal_api = journal_api
        self.assertTrue(self.panel.inspect_journal(str(genuine)))
        self.assertEqual(self.panel.journal_summary["state"], "invalid_tail")
        destination = self.directory / "genuine-recovered.jsonl"
        self.assertTrue(self.recover_to(destination))
        self.assertEqual(genuine.read_bytes(), original)
        inspection = journal_api.inspect_journal(destination)
        self.assertTrue(inspection["valid"])
        self.assertEqual(inspection["verified_count"], 2)
        self.assertFalse(inspection["clean_end"])
        self.assertFalse(inspection["replay_allowed"])
        self.assertGreater(self.panel.last_result["discarded_tail_bytes"], 0)


if __name__ == "__main__":
    unittest.main()
