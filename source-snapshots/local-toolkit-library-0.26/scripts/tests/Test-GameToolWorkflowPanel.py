"""Withdrawn test-owned Tk roots, mocked dialogs/clipboard; no desktop control."""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location("workflow_panel_" + name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


API, PANEL, SESSIONS, CORE, JOURNAL = (load(n) for n in ("GameToolWorkflow", "GameToolWorkflowPanel", "GameToolSessionPanel", "GameToolCoordinator", "GameToolJournal"))


class PanelContracts(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk(); self.root.withdraw(); self.addCleanup(self.root.destroy)
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-widget-"); self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "recipe.json"
        self.source.write_bytes((ROOT / "examples/game-tool-hub/workflow-installation.example.json").read_bytes())
        self.panel = PANEL.WorkflowPanel(self.root, API)
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        self.dialog = self.stack.enter_context(patch.object(self.panel, "_dialog"))
        self.clipboard = []
        self.stack.enter_context(patch.object(self.root, "clipboard_clear", side_effect=self.clipboard.clear))
        self.stack.enter_context(patch.object(self.root, "clipboard_append", side_effect=self.clipboard.append))

    def select(self):
        self.dialog.return_value = str(self.source)
        self.assertTrue(self.panel.select())

    def test_inert_constructor(self):
        with patch.object(API, "preview_source", side_effect=AssertionError("unexpected read")) as read:
            other = PANEL.WorkflowPanel(self.root, API)
        read.assert_not_called(); self.dialog.assert_not_called()
        self.assertIsNone(other.report); self.assertEqual(self.clipboard, [])
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_no_execution_buttons_and_initial_actions_disabled(self):
        self.assertEqual(set(self.panel.buttons), {"Choose recipe", "Reload preview", "Copy portable plan", "Export portable plan"})
        for name in ("Reload preview", "Copy portable plan", "Export portable plan"):
            self.assertEqual(str(self.panel.buttons[name]["state"]), "disabled")
        self.assertFalse(self.panel.copy_summary()); self.assertFalse(self.panel.export())

    def test_selection_renders_private_and_portable_separately(self):
        self.select()
        self.assertIn("PRIVATE LOCAL CHANGE LIST", self.panel.text.get("1.0", "end"))
        self.assertIn("example-layer.ini", self.panel.text.get("1.0", "end"))
        self.assertNotIn("example-layer.ini", json.dumps(self.panel.summary()))
        self.assertEqual(self.panel.report["status"], "BLOCKED")

    def test_copy_portable_rechecks_hash_without_paths(self):
        self.select(); payload = self.panel.copy_summary()
        self.assertEqual(self.clipboard, [payload])
        for token in ("example-layer.ini", "ExampleLayer", str(self.directory)):
            self.assertNotIn(token, payload)
        self.assertFalse(json.loads(payload)["runtime_verification"])

    def test_copy_drift_clears_stale_success(self):
        self.select(); self.source.write_bytes(self.source.read_bytes() + b' ')
        self.assertFalse(self.panel.copy_summary()); self.assertEqual(self.clipboard, [])
        self.assertIsNone(self.panel.report); self.assertEqual(self.panel.local_changes, [])
        self.assertFalse(self.panel.export())

    def test_reload_accepts_explicit_new_source_revision(self):
        self.select(); digest = self.panel.report["source_sha256"]
        self.source.write_bytes(self.source.read_bytes() + b' ')
        self.assertTrue(self.panel.reload()); self.assertNotEqual(self.panel.report["source_sha256"], digest)

    def test_cancel_selection_leaves_current_valid_preview(self):
        self.select(); digest = self.panel.report["source_sha256"]
        self.dialog.return_value = ""
        self.assertFalse(self.panel.select()); self.assertEqual(self.panel.report["source_sha256"], digest)

    def test_error_is_fixed_and_clears_stale_success(self):
        self.select()
        with patch.object(API, "preview_source", side_effect=ValueError("PRIVATE_EXCEPTION")):
            self.assertFalse(self.panel.reload())
        self.assertIsNone(self.panel.report)
        self.assertNotIn("PRIVATE_EXCEPTION", self.panel.text.get("1.0", "end"))

    def test_new_portable_export(self):
        self.select(); output = self.directory / "portable.json"
        self.dialog.return_value = str(output)
        self.assertTrue(self.panel.export()); self.assertTrue(output.exists())
        self.assertNotIn("example-layer.ini", output.read_text())
        self.assertFalse(self.panel.receipt["restore_tested"])

    def test_cancel_export_does_not_write(self):
        self.select(); self.dialog.return_value = ""
        self.assertFalse(self.panel.export())
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_source_drift_during_dialog_blocks_and_clears_preview(self):
        self.select(); output = self.directory / "portable.json"
        def dialog(*args, **kw):
            self.source.write_bytes(self.source.read_bytes() + b' '); return str(output)
        self.dialog.side_effect = dialog
        self.assertFalse(self.panel.export()); self.assertFalse(output.exists()); self.assertIsNone(self.panel.report)

    def test_close_during_export_dialog_does_not_publish(self):
        self.select(); output = self.directory / "portable.json"
        def dialog(*args, **kw):
            self.panel.close(); return str(output)
        self.dialog.side_effect = dialog
        self.assertFalse(self.panel.export()); self.assertFalse(output.exists())

    def test_source_selection_change_during_export_dialog_blocks(self):
        self.select(); output = self.directory / "portable.json"
        def dialog(*args, **kw):
            self.panel.source = str(self.directory / "other.json"); return str(output)
        self.dialog.side_effect = dialog
        self.assertFalse(self.panel.export()); self.assertFalse(output.exists())

    def test_existing_export_retained(self):
        self.select(); output = self.directory / "existing.json"; output.write_bytes(b"EXISTING")
        self.dialog.return_value = str(output)
        self.assertFalse(self.panel.export()); self.assertEqual(output.read_bytes(), b"EXISTING")

    def test_close_only_panel_disables_actions(self):
        self.select(); self.assertTrue(self.panel.close()); self.assertTrue(self.panel.close())
        self.assertFalse(self.panel.reload()); self.assertFalse(self.panel.copy_summary())
        self.assertTrue(self.source.exists())
        for button in self.panel.buttons.values(): self.assertEqual(str(button["state"]), "disabled")

    def test_status_callback_failure_is_contained(self):
        self.select(); self.panel.callback = Mock(side_effect=ValueError("PRIVATE"))
        self.assertTrue(self.panel.copy_summary())

    def test_sessions_optional_button_disabled_without_factory(self):
        view = SESSIONS.SessionPanel(self.root, CORE.Coordinator, JOURNAL); self.addCleanup(view.close)
        self.assertEqual(str(view.buttons["Workflow dry-runs"]["state"]), "disabled")
        self.assertFalse(view.open_workflow()); self.assertEqual(view.current_status["state"], "idle")

    def test_sessions_opens_explicit_child_and_closes_only_owned(self):
        children = []
        def factory(parent, callback):
            panel = PANEL.WorkflowPanel(parent, API, callback); children.append(panel); return panel
        view = SESSIONS.SessionPanel(self.root, CORE.Coordinator, JOURNAL, workflow_factory=factory)
        self.addCleanup(view.close)
        self.assertEqual(children, []); panel = view.open_workflow()
        self.assertIs(panel, children[0]); self.assertIsNone(panel.report)
        self.assertEqual(view.current_status["state"], "idle")
        view.close(); self.assertTrue(panel.closed); self.assertTrue(self.source.exists())

    def test_optional_workflow_failure_preserves_sessions(self):
        view = SESSIONS.SessionPanel(self.root, CORE.Coordinator, JOURNAL,
                 workflow_factory=Mock(side_effect=ImportError("PRIVATE_EXCEPTION")))
        self.addCleanup(view.close)
        self.assertFalse(view.open_workflow()); self.assertEqual(view.current_status["state"], "idle")
        self.assertNotIn("PRIVATE_EXCEPTION", view.operation_state.get())
        self.assertEqual(str(view.buttons["New offline session"]["state"]), "normal")

    def test_invalid_preview_not_accepted(self):
        self.select()
        with patch.object(API, "preview_source", return_value={"portable": {"status": "PASS"}, "local_changes": []}):
            self.assertFalse(self.panel.reload())
        self.assertIsNone(self.panel.report)

    def test_unknown_portable_result_fields_not_copied(self):
        self.select(); report = dict(self.panel.report); report["private_payload"] = "PRIVATE_UNREVIEWED_FIELD"
        with patch.object(API, "preview_source", return_value={"portable": report, "local_changes": []}):
            self.assertFalse(self.panel.copy_summary())
        self.assertEqual(self.clipboard, []); self.assertIsNone(self.panel.report)

    def test_invalid_export_receipt_not_accepted(self):
        self.select(); self.dialog.return_value = str(self.directory / "not-created.json")
        with patch.object(API, "export_plan", return_value={"runtime_verification": True}):
            self.assertFalse(self.panel.export())
        self.assertIsNone(self.panel.receipt); self.assertIsNone(self.panel.report)

    def test_clipboard_failure_is_fixed_and_stale_result_cleared(self):
        self.select()
        with patch.object(self.root, "clipboard_clear", side_effect=RuntimeError("PRIVATE_CLIPBOARD_ERROR")):
            self.assertFalse(self.panel.copy_summary())
        self.assertIsNone(self.panel.report); self.assertNotIn("PRIVATE_CLIPBOARD_ERROR", self.panel.state.get())


if __name__ == "__main__":
    unittest.main()
