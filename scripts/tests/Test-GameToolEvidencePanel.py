"""Withdrawn test-owned Tk widgets; mocked dialogs/clipboard, authored files only."""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location("evidence_panel_test_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api, panel_module, sessions = (load(name) for name in ("GameToolCrashEvidence", "GameToolEvidencePanel", "GameToolSessionPanel"))


class EvidencePanelContracts(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        self.tk = tk
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.temp = tempfile.TemporaryDirectory(prefix="evidence-panel-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "opaque.log"
        self.source.write_text("PRIVATE_MESSAGE", encoding="utf-8")
        self.panel = panel_module.EvidencePanel(self.root, api)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.dialog = self.stack.enter_context(mock.patch.object(self.panel, "_dialog"))
        self.clipboard = []
        self.stack.enter_context(mock.patch.object(self.root, "clipboard_clear", side_effect=self.clipboard.clear))
        self.stack.enter_context(mock.patch.object(self.root, "clipboard_append", side_effect=self.clipboard.append))

    def select(self):
        self.dialog.return_value = (str(self.source),)
        self.assertTrue(self.panel.select_files())

    def test_constructor_no_source_read_write_dialog_or_clipboard(self):
        with mock.patch.object(api, "build_packet", side_effect=AssertionError("read")) as read:
            other = panel_module.EvidencePanel(self.root, api)
        read.assert_not_called()
        self.assertIsNone(other.report)
        self.assertEqual(list(self.directory.iterdir()), [self.source])
        self.dialog.assert_not_called()
        self.assertEqual(self.clipboard, [])

    def test_initial_copy_export_disabled(self):
        for name in ("Copy portable summary", "Create private packet"):
            self.assertEqual(str(self.panel.buttons[name]["state"]), "disabled")
        self.assertFalse(self.panel.export())
        self.assertFalse(self.panel.copy_summary())

    def test_selection_loads_real_backend_without_private_payload(self):
        self.select()
        self.assertEqual(self.panel.report["status"], "EVIDENCE_ONLY")
        summary = json.dumps(self.panel.summary())
        self.assertNotIn("PRIVATE_MESSAGE", summary)
        self.assertNotIn(str(self.directory), summary)

    def test_selection_cancel_has_no_new_read(self):
        self.dialog.return_value = ()
        with mock.patch.object(api, "build_packet") as read:
            self.assertFalse(self.panel.select_files())
        read.assert_not_called()
        self.assertIsNone(self.panel.report)

    def test_copy_revalidates_pinned_hash_and_is_portable(self):
        self.select()
        payload = self.panel.copy_summary()
        self.assertEqual(self.clipboard, [payload])
        self.assertNotIn("PRIVATE_MESSAGE", payload)
        self.assertNotIn(str(self.directory), payload)
        self.assertFalse(json.loads(payload)["runtime_verification"])

    def test_unannounced_source_drift_blocks_copy_and_stale_export(self):
        self.select()
        self.source.write_text("PRIVATE_CHANGED", encoding="utf-8")
        self.assertFalse(self.panel.copy_summary())
        self.assertEqual(self.clipboard, [])
        self.assertIsNone(self.panel.report)
        self.assertFalse(self.panel.export())

    def test_explicit_reload_accepts_new_source(self):
        self.select()
        old = self.panel.report["sources"][0]["source_sha256"]
        self.source.write_text("new saved bytes", encoding="utf-8")
        self.assertTrue(self.panel.reload())
        self.assertNotEqual(self.panel.report["sources"][0]["source_sha256"], old)

    def test_explicit_export_creates_private_original_and_manifest(self):
        self.select()
        target = self.directory / "packet"
        self.dialog.return_value = str(target)
        self.assertTrue(self.panel.export())
        self.assertEqual((target / "source-001.txt").read_bytes(), self.source.read_bytes())
        self.assertTrue((target / "manifest.json").exists())
        self.assertNotIn(str(target), json.dumps(self.panel.summary()))

    def test_export_cancel_writes_nothing(self):
        self.select()
        self.dialog.return_value = ""
        self.assertFalse(self.panel.export())
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_export_refuses_existing_path_clears_stale_success(self):
        self.select()
        self.dialog.return_value = str(self.source)
        self.assertFalse(self.panel.export())
        self.assertIsNone(self.panel.receipt)
        self.assertIsNone(self.panel.report)
        self.assertEqual(self.source.read_text(encoding="utf-8"), "PRIVATE_MESSAGE")

    def test_drift_after_dialog_before_export_is_refused(self):
        self.select()
        target = self.directory / "packet"
        def change(*args, **kwargs):
            self.source.write_text("PRIVATE_CHANGED", encoding="utf-8")
            return str(target)
        self.dialog.side_effect = change
        self.assertFalse(self.panel.export())
        self.assertFalse(target.exists())

    def test_new_failed_selection_clears_previous_report(self):
        self.select()
        self.dialog.return_value = (str(self.directory / "missing.xml"),)
        self.assertFalse(self.panel.select_files())
        self.assertIsNone(self.panel.report)
        self.assertFalse(self.panel.copy_summary())

    def test_dialog_error_is_fixed_message_not_exception_text(self):
        self.dialog.side_effect = OSError("PRIVATE_MESSAGE")
        self.assertFalse(self.panel.select_files())
        self.assertNotIn("PRIVATE_MESSAGE", self.panel.state.get())
        self.assertNotIn("PRIVATE_MESSAGE", json.dumps(self.panel.summary()))

    def test_invalid_backend_result_not_accepted(self):
        self.dialog.return_value = (str(self.source),)
        with mock.patch.object(api, "build_packet", return_value={"status": "runtime_verified"}):
            self.assertFalse(self.panel.select_files())
        self.assertIsNone(self.panel.report)

    def test_bad_export_receipt_not_accepted(self):
        self.select()
        self.dialog.return_value = str(self.directory / "packet")
        with mock.patch.object(api, "export_packet", return_value={"status": "not_acknowledged"}):
            self.assertFalse(self.panel.export())
        self.assertIsNone(self.panel.receipt)

    def test_clipboard_failure_disables_stale_copy(self):
        self.select()
        with mock.patch.object(self.root, "clipboard_append", side_effect=OSError("private")):
            self.assertFalse(self.panel.copy_summary())
        self.assertIsNone(self.panel.report)

    def test_optional_status_sink_does_not_break_acknowledged_export(self):
        self.select()
        self.panel.status_callback = mock.Mock(side_effect=ValueError("private"))
        self.dialog.return_value = str(self.directory / "packet")
        self.assertTrue(self.panel.export())
        self.assertIsNotNone(self.panel.receipt)

    def test_close_is_inert_and_disables_future_actions(self):
        self.select()
        self.assertTrue(self.panel.close())
        self.assertFalse(self.panel.reload())
        self.assertFalse(self.panel.select_files())
        self.assertFalse(self.panel.copy_summary())
        self.assertFalse(self.panel.export())
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_old_sessions_without_optional_factory_still_available(self):
        coordinator = load("GameToolCoordinator")
        journal = load("GameToolJournal")
        view = sessions.SessionPanel(self.root, coordinator.Coordinator, journal)
        self.assertEqual(str(view.buttons["Saved crash evidence"]["state"]), "disabled")
        self.assertFalse(view.open_evidence())
        self.assertTrue(view.close())

    def test_session_embedded_evidence_window_inert_and_closes_with_host(self):
        coordinator, journal = load("GameToolCoordinator"), load("GameToolJournal")
        windows = []
        def factory(parent, callback):
            parent.withdraw()  # Test-owned window only, no foreground/live app test.
            windows.append(parent)
            return panel_module.EvidencePanel(parent, api, callback)
        view = sessions.SessionPanel(self.root, coordinator.Coordinator, journal, evidence_factory=factory)
        child = view.open_evidence()
        self.assertIsNone(child.report)
        self.assertEqual(view.coordinator.status()["state"], "idle")
        self.assertEqual(list(self.directory.iterdir()), [self.source])
        self.assertTrue(view.close())
        self.assertTrue(child.closed)
        self.assertFalse(windows[0].winfo_exists())

    def test_optional_evidence_failure_does_not_break_sessions(self):
        coordinator, journal = load("GameToolCoordinator"), load("GameToolJournal")
        view = sessions.SessionPanel(self.root, coordinator.Coordinator, journal,
              evidence_factory=mock.Mock(side_effect=ImportError("PRIVATE_MESSAGE")))
        self.assertFalse(view.open_evidence())
        self.assertEqual(view.coordinator.status()["state"], "idle")
        self.assertNotIn("PRIVATE_MESSAGE", json.dumps(view.summary()))
        self.assertTrue(view.close())


if __name__ == "__main__":
    unittest.main(verbosity=2)
