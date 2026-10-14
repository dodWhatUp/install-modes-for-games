"""Withdrawn, test-owned Tk fixtures with deferred mocked worker threads.

All files are synthetic temporary data. No live desktop control, application
launch, games, recording, native profile activation or network upload.
"""
from __future__ import annotations

from contextlib import ExitStack
import importlib.util
import json
import sys
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
sys.dont_write_bytecode = True


def load(name):
    spec = importlib.util.spec_from_file_location("user_data_panel_fixture_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CORE, UI = load("GameToolUserData"), load("GameToolUserDataPanel")
METHODS = ("preview_export", "export_archive", "inspect_archive", "restore_new_copy",
           "inspect_envelope", "save_migrated_copy")


class PanelFixtures(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk(); self.root.withdraw()
        self.temp = tempfile.TemporaryDirectory(prefix="GameTools-UserDataPanelFixture-")
        self.folder = Path(self.temp.name)
        self.source = self.folder / "settings.ini"
        self.source.write_bytes(b"[Fixture]\nF7=LocalHold\nProfile=keep-original\n")
        self.before = self.source.read_bytes()
        self.api = SimpleNamespace(MAX_FILES=CORE.MAX_FILES,
            **{name: Mock(wraps=getattr(CORE, name)) for name in METHODS},
            launch_game=Mock(), activate_profile=Mock(), upload=Mock(), record=Mock(), benchmark=Mock())
        self.status = tk.StringVar()
        self.jobs = []
        self.stack = ExitStack()
        self.thread_factory = self.stack.enter_context(patch.object(UI.threading, "Thread", side_effect=self.defer))
        self.confirm = self.stack.enter_context(patch.object(UI.messagebox, "askyesno", return_value=True))
        self.browse = self.stack.enter_context(patch.object(UI.filedialog, "askopenfilename", return_value=""))
        self.frame = UI.ttk.Frame(self.root); self.frame.pack(fill="both", expand=True)
        self.panel = UI.UserDataPanel(self.frame, self.api, self.status, app_version="fixture-0.13.0")

    def tearDown(self):
        self.assertEqual(self.source.read_bytes(), self.before)
        for name in ("launch_game", "activate_profile", "upload", "record", "benchmark"):
            getattr(self.api, name).assert_not_called()
        self.panel.busy = False
        self.panel.close()
        self.root.destroy()
        self.stack.close()
        self.temp.cleanup()

    def defer(self, target, daemon):
        self.assertTrue(daemon)
        return SimpleNamespace(start=lambda: self.jobs.append(target))

    def drain(self):
        self.assertEqual(len(self.jobs), 1)
        self.jobs.pop(0)()
        # Simulate a main-loop polling callback without sleeping, real workers,
        # raising a visible window or sending input to another application.
        self.root.after_cancel(self.panel.timer)
        self.panel.tick()

    def select(self):
        self.panel.source.set(str(self.source))
        self.panel.logical.set("studio/settings.ini")
        self.panel.destination.set(str(self.folder / "private.zip"))
        self.panel.add_file()

    def preview_export(self):
        self.select(); self.panel.inspect(); self.drain()
        self.assertIsNotNone(self.panel.preview)

    def fixture_archive(self):
        archive = self.folder / "import.zip"
        preview = CORE.preview_export([{"path": str(self.source), "logical_path": "studio/settings.ini"}])
        exported = CORE.export_archive(archive, preview)
        return archive, exported["sha256"]

    def restore_preview(self):
        archive, expected = self.fixture_archive()
        self.panel.mode.set(UI.MODES[1]); self.panel.mode_changed()
        self.panel.source.set(str(archive)); self.panel.expected.set(expected)
        self.panel.destination.set(str(self.folder / "recovered"))
        self.panel.inspect(); self.drain()
        self.assertIsNotNone(self.panel.preview)
        return archive, expected

    def envelope_preview(self, future=False):
        source = self.folder / "old-record.json"
        envelope = {"schema_version": 1, "data_version": 9 if future else 1,
                    "record_id": "retained-record", "kind": "fixture.profile", "source": {"revision": "r9"},
                    "payload": {"original": [1, 2], "unknown": "keep"}, "future_extension": {"a": 5}}
        source.write_text(json.dumps(envelope), encoding="utf-8")
        self.panel.mode.set(UI.MODES[2]); self.panel.mode_changed()
        self.panel.source.set(str(source)); self.panel.destination.set(str(self.folder / "new-record.json"))
        self.panel.inspect(); self.drain()
        return source, envelope

    def disabled(self, widget):
        return str(widget.cget("state")) == "disabled"

    def text(self):
        return self.panel.details.get("1.0", "end-1c")

    def test_startup_inert_no_api_worker_dialog_or_file(self):
        self.assertEqual(self.panel.selections, [])
        self.assertIsNone(self.panel.preview); self.assertFalse(self.panel.busy)
        self.assertEqual(self.panel.mode.get(), UI.MODES[0])
        self.assertTrue(self.disabled(self.panel.commit_button))
        self.thread_factory.assert_not_called(); self.confirm.assert_not_called(); self.browse.assert_not_called()
        for name in METHODS:
            getattr(self.api, name).assert_not_called()
        self.assertEqual(list(self.folder.iterdir()), [self.source])
        self.assertIn("Future formats stay read-only", self.text())

    def test_mode_switch_changes_context_only_preserving_selection(self):
        self.select(); rows = list(self.panel.selections)
        for mode, source_label, destination_label in (
            (UI.MODES[1], "Private backup ZIP", "NEW restore directory"),
            (UI.MODES[2], "Shared-envelope JSON", "NEW migrated JSON path"),
            (UI.MODES[0], "Selected source file", "New ZIP path")):
            with self.subTest(mode=mode):
                self.panel.mode.set(mode); self.panel.mode_changed()
                self.assertEqual(self.panel.source_label.cget("text"), source_label)
                self.assertEqual(self.panel.dest_label.cget("text"), destination_label)
                self.assertEqual(bool(self.panel.logical_control.winfo_manager()), mode == UI.MODES[0])
                self.assertEqual(bool(self.panel.sha_control.winfo_manager()), mode == UI.MODES[1])
                self.assertTrue(self.disabled(self.panel.commit_button))
                self.assertEqual(self.panel.selections, rows)
        self.assertEqual(self.jobs, [])
        self.api.preview_export.assert_not_called()

    def test_editable_source_selection_direct_entry_no_auto_add(self):
        self.assertNotEqual(str(self.panel.source_control.cget("state")), "readonly")
        self.panel.source.set(str(self.source))
        self.panel.logical.set("typed/explicit.ini")
        self.assertEqual(self.panel.selections, [])
        self.api.preview_export.assert_not_called()
        self.assertEqual(self.jobs, [])

    def test_browse_cancel_preserves_typed_fields(self):
        self.panel.source.set("existing typed source"); self.panel.logical.set("existing-name.ini")
        self.panel.browse_source()
        self.assertEqual(self.panel.source.get(), "existing typed source")
        self.assertEqual(self.panel.logical.get(), "existing-name.ini")
        self.assertEqual(self.panel.selections, [])

    def test_browse_sets_filename_only_when_logical_blank(self):
        self.browse.return_value = str(self.source)
        self.panel.browse_source()
        self.assertEqual(self.panel.source.get(), str(self.source))
        self.assertEqual(self.panel.logical.get(), self.source.name)
        self.assertEqual(self.panel.selections, [])
        self.panel.logical.set("preserve/custom.ini"); self.panel.browse_source()
        self.assertEqual(self.panel.logical.get(), "preserve/custom.ini")

    def test_add_remove_are_explicit_memory_only_and_invalidate_preview(self):
        self.preview_export()
        self.assertFalse(self.disabled(self.panel.commit_button))
        self.panel.table.selection_set(self.panel.table.get_children()[0])
        self.panel.remove_file()
        self.assertEqual(self.panel.selections, [])
        self.assertIsNone(self.panel.preview)
        self.assertTrue(self.disabled(self.panel.commit_button))
        self.assertEqual(list(self.folder.iterdir()), [self.source])

    def test_missing_selection_and_file_limit_feedback(self):
        self.panel.add_file(); self.assertEqual(self.panel.selections, [])
        self.assertIn("Enter a source", self.status.get())
        self.api.MAX_FILES = 0; self.select()
        self.assertEqual(self.panel.selections, [])
        self.assertIn("limit", self.status.get())

    def test_worker_queue_is_deferred_until_polled(self):
        self.select(); self.panel.inspect()
        self.assertTrue(self.panel.busy); self.assertTrue(self.disabled(self.panel.inspect_button))
        self.assertTrue(self.disabled(self.panel.commit_button)); self.assertEqual(len(self.jobs), 1)
        self.api.preview_export.assert_not_called()
        self.assertIsNone(self.panel.preview)
        self.drain()
        self.assertFalse(self.panel.busy)
        self.assertEqual(self.panel.preview["result"]["state"], "EXPORT_PREVIEW")
        self.assertIn("studio/settings.ini", self.text())
        self.api.preview_export.assert_called_once_with(self.panel.selections, app_version="fixture-0.13.0")

    def test_busy_blocks_duplicate_workers_browse_and_selection_mutation(self):
        self.select(); self.panel.inspect(); rows = list(self.panel.selections)
        self.panel.inspect(); self.panel.commit(); self.panel.add_file()
        self.panel.table.selection_set(self.panel.table.get_children()[0]); self.panel.remove_file(); self.panel.browse_source()
        self.assertEqual(len(self.jobs), 1); self.assertEqual(self.panel.selections, rows)
        self.confirm.assert_not_called(); self.browse.assert_not_called()
        self.drain()

    def test_fields_changed_during_worker_discard_result(self):
        self.select(); self.panel.inspect(); self.panel.destination.set(str(self.folder / "changed.zip"))
        self.drain()
        self.assertIsNone(self.panel.preview); self.assertTrue(self.disabled(self.panel.commit_button))
        self.assertIn("Fields changed", self.status.get())

    def test_mode_changed_during_worker_discard_result(self):
        self.select(); self.panel.inspect(); self.panel.mode.set(UI.MODES[1]); self.panel.mode_changed()
        self.drain()
        self.assertIsNone(self.panel.preview); self.assertTrue(self.disabled(self.panel.commit_button))
        self.assertEqual(self.panel.source_label.cget("text"), "Private backup ZIP")

    def test_inspection_failure_clears_previous_result_no_dialog(self):
        self.preview_export()
        self.api.preview_export.side_effect = CORE.UserDataError("SOURCE_CHANGED")
        self.panel.inspect(); self.drain()
        self.assertIsNone(self.panel.preview); self.assertTrue(self.disabled(self.panel.commit_button))
        self.assertIn("blocked", self.status.get()); self.confirm.assert_not_called()

    def test_changed_selection_signature_blocks_commit_before_confirmation(self):
        self.preview_export(); self.panel.selections[0]["logical_path"] = "different.ini"
        self.panel.commit()
        self.assertEqual(self.jobs, []); self.confirm.assert_not_called()
        self.assertIn("Inspect these exact", self.status.get())

    def test_changed_fields_after_preview_block_commit(self):
        self.preview_export(); self.panel.destination.set(str(self.folder / "other.zip"))
        self.panel.commit()
        self.assertEqual(self.jobs, []); self.confirm.assert_not_called()
        self.api.export_archive.assert_not_called()

    def test_cancel_confirmation_preserves_preview_no_export(self):
        self.preview_export(); preview = self.panel.preview; self.confirm.return_value = False
        self.panel.commit()
        self.assertIs(self.panel.preview, preview); self.assertEqual(self.jobs, [])
        self.api.export_archive.assert_not_called(); self.assertFalse((self.folder / "private.zip").exists())

    def test_export_confirmation_worker_and_receipt_new_copy_only(self):
        self.preview_export(); preview = self.panel.preview["result"]
        self.panel.commit(); self.confirm.assert_called_once()
        self.assertTrue(self.panel.busy); self.assertFalse((self.folder / "private.zip").exists())
        self.drain()
        self.api.export_archive.assert_called_once_with(self.folder / "private.zip", preview)
        self.assertTrue((self.folder / "private.zip").is_file())
        self.assertIsNone(self.panel.preview)
        self.assertIn("EXPORTED_NEW_ARCHIVE", self.text())
        self.assertIn("existing profiles remain unchanged", self.status.get())

    def test_source_drift_after_preview_blocks_export_no_zip(self):
        self.preview_export(); self.source.write_bytes(b"fixture concurrent source edit"); self.before = self.source.read_bytes()
        self.panel.commit(); self.drain()
        self.assertFalse((self.folder / "private.zip").exists())
        self.assertIsNone(self.panel.preview); self.assertIn("blocked", self.status.get())

    def test_existing_destination_not_overwritten_by_panel(self):
        destination = self.folder / "private.zip"; destination.write_bytes(b"existing preserve")
        self.preview_export(); self.panel.commit(); self.drain()
        self.assertEqual(destination.read_bytes(), b"existing preserve")
        self.assertIsNone(self.panel.preview); self.assertIn("blocked", self.status.get())

    def test_restore_inspects_explicit_sha_and_new_copy_callbacks(self):
        archive, expected = self.restore_preview()
        self.api.inspect_archive.assert_called_once_with(archive, expected)
        value = self.panel.preview["result"]
        self.panel.commit(); self.drain()
        self.api.restore_new_copy.assert_called_once_with(archive, self.folder / "recovered",
                                                        value["archive_sha256"], value["preview_sha256"])
        self.assertEqual((self.folder / "recovered/data/studio/settings.ini").read_bytes(), self.before)
        self.assertIn("RESTORED_NEW_COPY", self.text())
        self.api.save_migrated_copy.assert_not_called(); self.api.export_archive.assert_not_called()

    def test_restore_blank_expected_still_pins_inspected_hash_on_commit(self):
        archive, _ = self.fixture_archive()
        self.panel.mode.set(UI.MODES[1]); self.panel.mode_changed(); self.panel.source.set(str(archive))
        self.panel.destination.set(str(self.folder / "recovered")); self.panel.inspect(); self.drain()
        self.api.inspect_archive.assert_called_once_with(archive, None)
        value = self.panel.preview["result"]; self.panel.commit(); self.drain()
        self.assertEqual(self.api.restore_new_copy.call_args.args[2], value["archive_sha256"])

    def test_restore_future_read_only_no_confirmation_or_worker(self):
        archive, expected = self.fixture_archive()
        self.panel.mode.set(UI.MODES[1]); self.panel.mode_changed()
        self.panel.source.set(str(archive)); self.panel.expected.set(expected)
        self.api.inspect_archive.return_value = {"state": "BLOCKED_FUTURE_VERSION", "read_only": True,
            "archive_sha256": expected, "preview_sha256": "0" * 64, "files": 1, "bytes": 30, "migrations": []}
        self.panel.inspect(); self.drain(); self.assertTrue(self.disabled(self.panel.commit_button))
        self.panel.commit(); self.confirm.assert_not_called(); self.assertEqual(self.jobs, [])
        self.api.restore_new_copy.assert_not_called(); self.assertIn("read-only", self.status.get())

    def test_restore_archive_drift_after_preview_no_destination(self):
        archive, _ = self.restore_preview(); archive.write_bytes(archive.read_bytes() + b"changed")
        self.panel.commit(); self.drain()
        self.assertFalse((self.folder / "recovered").exists())
        self.assertIsNone(self.panel.preview); self.assertIn("blocked", self.status.get())

    def test_cancel_restore_confirmation_keeps_read_only_preview(self):
        self.restore_preview(); preview = self.panel.preview; self.confirm.return_value = False
        self.panel.commit()
        self.assertIs(self.panel.preview, preview)
        self.assertEqual(self.jobs, []); self.api.restore_new_copy.assert_not_called()
        self.assertFalse((self.folder / "recovered").exists())

    def test_envelope_migrate_is_previewed_then_new_copy_preserving_unknowns(self):
        source, original = self.envelope_preview(); before = source.read_bytes()
        self.api.inspect_envelope.assert_called_once_with(source)
        self.assertIn("Automatic supported conversion preview", self.text())
        value = self.panel.preview["result"]; self.panel.commit(); self.drain()
        self.api.save_migrated_copy.assert_called_once_with(source, self.folder / "new-record.json",
                                                            value["file_sha256"], value["preview_sha256"])
        self.assertEqual(source.read_bytes(), before)
        migrated = json.loads((self.folder / "new-record.json").read_text())
        self.assertEqual(migrated["data_version"], 2)
        self.assertEqual(migrated["record_id"], original["record_id"])
        self.assertEqual(migrated["future_extension"], original["future_extension"])
        self.api.restore_new_copy.assert_not_called(); self.api.export_archive.assert_not_called()

    def test_future_envelope_read_only_does_not_migrate(self):
        source, original = self.envelope_preview(future=True)
        self.assertTrue(self.disabled(self.panel.commit_button)); self.panel.commit()
        self.confirm.assert_not_called(); self.api.save_migrated_copy.assert_not_called()
        self.assertEqual(self.jobs, []); self.assertEqual(json.loads(source.read_text()), original)
        self.assertFalse((self.folder / "new-record.json").exists())

    def test_cancel_migration_confirmation_original_unchanged(self):
        source, original = self.envelope_preview(); self.confirm.return_value = False
        self.panel.commit()
        self.assertEqual(self.jobs, []); self.api.save_migrated_copy.assert_not_called()
        self.assertEqual(json.loads(source.read_text()), original)
        self.assertFalse((self.folder / "new-record.json").exists())

    def test_envelope_drift_after_preview_no_new_record(self):
        source, _ = self.envelope_preview(); source.write_bytes(source.read_bytes() + b" ")
        self.panel.commit(); self.drain()
        self.assertFalse((self.folder / "new-record.json").exists())
        self.assertIsNone(self.panel.preview); self.assertIn("blocked", self.status.get())

    def test_close_busy_gate_then_completion_allows_close(self):
        self.select(); self.panel.inspect()
        self.assertFalse(self.panel.close()); self.assertFalse(self.panel.closed)
        self.drain(); self.assertTrue(self.panel.close()); self.assertTrue(self.panel.closed)
        self.panel.tick(); self.assertFalse(self.panel.busy)

    def test_closed_panel_no_confirmation_browse_or_worker(self):
        self.preview_export(); self.assertTrue(self.panel.close())
        self.panel.commit(); self.panel.browse_source(); self.panel.inspect()
        self.confirm.assert_not_called(); self.browse.assert_not_called()
        self.api.export_archive.assert_not_called(); self.assertEqual(self.jobs, [])

    def test_closed_panel_does_not_mutate_selection(self):
        self.select(); self.assertTrue(self.panel.close()); rows = list(self.panel.selections)
        self.panel.add_file(); self.panel.table.selection_set(self.panel.table.get_children()[0]); self.panel.remove_file()
        self.assertEqual(self.panel.selections, rows)

    def test_nested_confirmation_field_drift_refuses_commit(self):
        self.preview_export()
        def changed(*args, **kwargs):
            self.panel.destination.set(str(self.folder / "changed-during-confirmation.zip"))
            return True
        self.confirm.side_effect = changed
        self.panel.commit()
        self.assertEqual(self.jobs, [])
        self.api.export_archive.assert_not_called()
        self.assertFalse((self.folder / "private.zip").exists())

    def test_detail_panel_read_only_preserves_empty_and_error_states(self):
        self.assertEqual(str(self.panel.details.cget("state")), "disabled")
        self.panel.display("Fixture failure · no active data changed.")
        self.assertEqual(str(self.panel.details.cget("state")), "disabled")
        self.assertIn("Fixture failure", self.text())
        self.assertFalse(self.panel.busy); self.assertIsNone(self.panel.preview)


if __name__ == "__main__":
    unittest.main(verbosity=2)
