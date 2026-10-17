"""Withdrawn test-owned widgets; dialogs and clipboard mocked, no live control."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
def load(name):
    spec = importlib.util.spec_from_file_location('readiness_widget_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
API, UI, SESSIONS, CORE, JOURNAL = (load(n) for n in ('GameToolReadiness','GameToolReadinessPanel','GameToolSessionPanel','GameToolCoordinator','GameToolJournal'))


class Widgets(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        self.root = tk.Tk(); self.root.withdraw(); self.addCleanup(self.root.destroy)
        self.temp = tempfile.TemporaryDirectory(prefix='readiness-widget-'); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name); self.source = self.folder / 'scenario.json'
        self.source.write_bytes((ROOT / 'examples/game-tool-hub/scenario.example.json').read_bytes())
        self.panel = UI.ReadinessPanel(self.root, API)
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        self.dialog = self.stack.enter_context(patch.object(self.panel, '_dialog'))
        self.clipboard = []; self.stack.enter_context(patch.object(self.root, 'clipboard_clear', side_effect=self.clipboard.clear))
        self.stack.enter_context(patch.object(self.root, 'clipboard_append', side_effect=self.clipboard.append))

    def loaded(self):
        self.panel.location.set(str(self.source)); self.assertTrue(self.panel.load()); self.root.update()

    def edited(self):
        data = json.loads(self.panel.editor.get('1.0','end-1c')); data['revision'] = 2; data['repeat_count'] = 5
        self.panel.editor.delete('1.0','end'); self.panel.editor.insert('1.0',json.dumps(data)); self.root.update()
        return data

    def test_constructor_inert_no_read_dialog_or_write(self):
        with patch.object(API, 'read_source', side_effect=AssertionError('read')) as reader:
            other = UI.ReadinessPanel(self.root, API)
        reader.assert_not_called(); self.dialog.assert_not_called()
        self.assertIsNone(other.report); self.assertEqual(list(self.folder.iterdir()), [self.source])

    def test_no_run_capture_or_apply_controls(self):
        self.assertEqual(set(self.panel.buttons), {'Load path','Browse','Discard edits and load','Preview draft','Save NEW scenario','Copy checked summary'})
        self.assertFalse(self.panel.save()); self.assertFalse(self.panel.copy_summary())

    def test_bom_source_anchor_and_normalized_editor_hash_are_distinct(self):
        self.source.write_bytes(b'\xef\xbb\xbf' + self.source.read_bytes())
        self.loaded(); payload = self.panel.copy_summary()
        self.assertTrue(payload); self.assertEqual(self.panel.source_hash, hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(json.loads(payload)['source_sha256'], hashlib.sha256(self.panel._raw()).hexdigest())

    def test_failed_new_load_clears_old_source_association(self):
        self.loaded(); self.panel.location.set(str(self.folder / 'missing.json'))
        self.assertFalse(self.panel.load()); self.assertIsNone(self.panel.source)
        self.assertIn('MockScenario', self.panel.editor.get('1.0','end')); self.assertFalse(self.panel.save())

    def test_load_renders_declared_status_and_private_editor(self):
        self.loaded(); self.assertIn('MockScenario', self.panel.editor.get('1.0','end'))
        self.assertNotIn('MockScenario', self.panel.text.get('1.0','end'))
        self.assertIn('PREPARED_NOT_AUTHORIZED', self.panel.state.get())

    def test_unsaved_preview_changes_no_files(self):
        self.loaded(); original = self.source.read_bytes(); self.edited()
        self.assertIsNone(self.panel.report); self.assertTrue(self.panel.preview())
        self.assertEqual(self.panel.report['details']['repeat_count'], 5)
        self.assertEqual(self.source.read_bytes(), original); self.assertEqual(list(self.folder.iterdir()), [self.source])

    def test_dirty_draft_cannot_be_silently_replaced(self):
        self.loaded(); self.edited(); draft = self.panel._raw()
        self.assertFalse(self.panel.load()); self.assertFalse(self.panel.browse())
        self.assertEqual(self.panel._raw(), draft)
        with patch('tkinter.messagebox.askyesno', return_value=False): self.assertFalse(self.panel.discard_load())
        self.assertEqual(self.panel._raw(), draft)

    def test_explicit_discard_reload(self):
        self.loaded(); self.edited()
        with patch('tkinter.messagebox.askyesno', return_value=True): self.assertTrue(self.panel.discard_load())
        self.assertEqual(self.panel.report['details']['revision'], 1)

    def test_save_new_retains_original(self):
        self.loaded(); original = self.source.read_bytes(); data = self.edited(); self.panel.preview()
        output = self.folder / 'new.json'; self.dialog.return_value = str(output)
        self.assertTrue(self.panel.save()); self.assertEqual(json.loads(output.read_text()), data)
        self.assertEqual(self.source.read_bytes(), original)

    def test_cancel_save_writes_nothing(self):
        self.loaded(); self.dialog.return_value = ''
        self.assertFalse(self.panel.save()); self.assertEqual(list(self.folder.iterdir()), [self.source])

    def test_source_drift_before_copy_or_save_clears_result(self):
        self.loaded(); self.source.write_bytes(self.source.read_bytes() + b' ')
        self.assertFalse(self.panel.copy_summary()); self.assertEqual(self.clipboard, [])
        self.assertIsNone(self.panel.report); self.assertFalse(self.panel.save())

    def test_source_drift_during_dialog_refuses_new_copy(self):
        self.loaded(); output = self.folder / 'new.json'
        def dialog(*args, **kwargs):
            self.source.write_bytes(self.source.read_bytes() + b' '); return str(output)
        self.dialog.side_effect = dialog
        self.assertFalse(self.panel.save()); self.assertFalse(output.exists())

    def test_edit_during_nested_dialog_refused(self):
        self.loaded(); output = self.folder / 'new.json'
        def dialog(*args, **kwargs): self.panel.editor.insert('end',' '); return str(output)
        self.dialog.side_effect = dialog
        self.assertFalse(self.panel.save()); self.assertFalse(output.exists())

    def test_copy_checked_alias_summary_not_private_contract(self):
        self.loaded(); payload = self.panel.copy_summary(); self.assertEqual(self.clipboard, [payload])
        self.assertNotIn('MockScenario', payload); self.assertNotIn(str(self.source), payload)
        self.assertFalse(json.loads(payload)['runtime_verification'])

    def test_malformed_edit_preview_clears_old_result_retains_draft(self):
        self.loaded(); self.panel.editor.insert('end','BROKEN'); self.root.update()
        self.assertFalse(self.panel.preview()); self.assertIsNone(self.panel.report)
        self.assertIn('BROKEN', self.panel.editor.get('1.0','end'))

    def test_closed_view_has_no_callbacks_or_writes(self):
        self.loaded(); self.assertTrue(self.panel.close())
        self.assertFalse(self.panel.load()); self.assertFalse(self.panel.preview()); self.assertFalse(self.panel.save())
        self.assertFalse(self.panel.copy_summary()); self.dialog.assert_not_called()

    def test_provider_preview_cannot_save_scenario(self):
        self.source.write_bytes((ROOT / 'examples/game-tool-hub/provider-health.example.json').read_bytes())
        self.loaded(); self.assertEqual(self.panel.report['status'], 'MOCK_HEALTHY')
        self.assertFalse(self.panel.save())

    def test_optional_session_factory_missing_is_disabled(self):
        panel = SESSIONS.SessionPanel(self.root, CORE.Coordinator, JOURNAL)
        self.addCleanup(panel.close)
        self.assertEqual(str(panel.buttons['Provider / scenario contracts']['state']), 'disabled')
        self.assertFalse(panel.open_readiness())

    def test_optional_session_child_cleanup_and_no_journal(self):
        import tkinter as tk
        original = tk.Toplevel
        def hidden(*args, **kwargs):
            win = original(*args, **kwargs); win.withdraw(); return win
        panel = SESSIONS.SessionPanel(self.root, CORE.Coordinator, JOURNAL,
            readiness_factory=lambda parent, callback: UI.ReadinessPanel(parent, API, callback))
        with patch.object(panel.tk, 'Toplevel', side_effect=hidden): child = panel.open_readiness()
        self.assertIsNotNone(child); self.assertIsNone(child.source); self.assertTrue(panel.close()); self.assertTrue(child.closed)
        self.assertEqual(list(self.folder.iterdir()), [self.source])


if __name__ == '__main__': unittest.main(verbosity=2)
