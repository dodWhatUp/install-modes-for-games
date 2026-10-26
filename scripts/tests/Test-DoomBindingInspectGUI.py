"""Isolated-guest Tk acceptance with generated fixtures; no host/game input."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolDoomBindingInspectUI as ui

spec = importlib.util.spec_from_file_location('doom_inspect_gui_fixtures', Path(__file__).with_name('Test-DoomBindingInspect.py'))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


@unittest.skipIf(fixtures.AESGCM is None, 'Reviewed cryptography runtime unavailable')
class InspectorGUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = tk.Tk()
        self.root.geometry('960x760')
        self.addCleanup(self.root.destroy)
        self.errors = []
        self.root.report_callback_exception = lambda kind, value, trace: self.errors.append(str(value))
        self.messages = []
        self.panel = ui.InspectPanel(self.root, status=self.messages.append)
        self.addCleanup(self.panel.close)
        self.first = self.fixture('first', [[('K', '_throw', 1), ('MOUSE3', '_throw', 1)],
                                             [('JOY1', '_jump', 1), ('P', '_use', 1)]])
        self.second = self.fixture('second', [[('U', '_throw', 1), ('MOUSE3', '_throw', 1)],
                                               [('JOY1', '_jump', 1), ('P', '_use', 1)]])
        self.root.update()

    def tearDown(self):
        self.panel.close()
        self.root.update_idletasks()
        self.assertEqual(self.errors, [], 'Tk callback errors occurred')

    def fixture(self, folder, rows, identity=fixtures.IDENTITY):
        directory = Path(self.temp.name) / folder
        directory.mkdir()
        path = directory / 'profile.bin'
        path.write_bytes(fixtures.wrap(fixtures.plaintext(rows), identity))
        return path

    def wait(self, predicate, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.root.update()
            if predicate():
                return
            time.sleep(0.005)
        self.fail('Timed out waiting for isolated Tk worker/result')

    def load(self):
        self.panel.load_snapshot(self.first, fixtures.IDENTITY)
        self.wait(lambda: not self.panel.busy)
        self.assertIsNotNone(self.panel.current)

    def test_worker_load_completes_without_changing_selected_file(self):
        original = ui.read_selected_snapshot
        worker_threads = []
        main_thread = threading.get_ident()
        before = hashlib.sha256(self.first.read_bytes()).hexdigest()
        def observed(*args, **kwargs):
            worker_threads.append(threading.get_ident())
            return original(*args, **kwargs)
        with patch.object(ui, 'read_selected_snapshot', side_effect=observed):
            self.load()
        self.assertTrue(worker_threads)
        self.assertNotIn(main_thread, worker_threads)
        self.assertEqual(self.panel.current['binding_count'], 4)
        self.assertEqual(len(self.panel.table.get_children()), 4)
        self.assertEqual(hashlib.sha256(self.first.read_bytes()).hexdigest(), before)
        self.assertFalse(self.panel.current['capabilities']['binary_game_write'])
        self.assertIn('unverified', self.panel.feedback.get())

    def test_search_context_and_input_filters_are_read_only(self):
        self.load()
        before = json.dumps(self.panel.current, sort_keys=True)
        self.panel.context.select('0')
        self.panel.family.select('keyboard')
        self.panel.render()
        self.assertEqual(len(self.panel.table.get_children()), 1)
        self.panel.term.set('_jump')
        self.root.update()
        self.assertEqual(len(self.panel.table.get_children()), 0)
        self.assertIn('0 of', self.panel.count_text.get())
        self.panel.term.set('')
        self.root.update()
        self.assertEqual(len(self.panel.table.get_children()), 1)
        self.assertEqual(json.dumps(self.panel.current, sort_keys=True), before)

    def test_context_dropdown_stays_open_and_keeps_editable_caret(self):
        self.load()
        control = self.panel.context
        control.focus_force()
        control.event_generate('<Button-1>', x=18, y=8)
        self.root.update()
        popup = control.game_tools_editable_list
        self.assertTrue(popup.visible)
        control.delete(0, 'end')
        control.insert(0, 'Context 1')
        control.icursor(3)
        control.insert('insert', 'x')
        self.root.update()
        self.assertTrue(popup.visible)
        self.assertEqual(control.index('insert'), 4)
        self.assertIs(self.root.focus_get(), control)
        self.assertEqual(control.selected_id, 'all')
        self.assertEqual(len(self.panel.table.get_children()), 4)
        control.event_generate('<Escape>')
        self.root.update()
        self.assertFalse(popup.visible)
        self.assertEqual(control.selected_id, 'all')

    def test_failed_comparison_preserves_first_snapshot_and_table(self):
        self.load()
        current = self.panel.current
        wrong = self.fixture('wrong-owner', [[('U', '_throw', 1)]], str(int(fixtures.IDENTITY) + 1))
        self.panel.load_snapshot(wrong, fixtures.IDENTITY, kind='comparison')
        self.wait(lambda: not self.panel.busy)
        self.assertIs(self.panel.current, current)
        self.assertIsNone(self.panel.comparison)
        self.assertEqual(len(self.panel.table.get_children()), 4)
        self.assertIn('AUTHENTICATION_FAILED', self.panel.feedback.get())

    def test_successful_comparison_displays_only_added_and_removed_rows(self):
        self.load()
        current = self.panel.current
        self.panel.load_snapshot(self.second, fixtures.IDENTITY, kind='comparison')
        self.wait(lambda: not self.panel.busy)
        self.assertIs(self.panel.current, current)
        self.assertEqual(self.panel.view.selected_id, 'diff')
        rows = [self.panel.table.item(item, 'values') for item in self.panel.table.get_children()]
        self.assertEqual(len(rows), 2)
        self.assertEqual({row[2] for row in rows}, {'K', 'U'})
        self.assertEqual({row[4] for row in rows}, {'Added', 'Removed'})

    def test_export_menu_creates_only_new_reference_and_preserves_existing_file(self):
        self.load()
        destination = Path(self.temp.name) / 'reference.json'
        with patch.object(ui.filedialog, 'asksaveasfilename', return_value=str(destination)):
            self.panel.export('json')
            self.wait(lambda: not self.panel.busy)
        self.assertEqual(json.loads(destination.read_text())['kind'], 'doom_binary_binding_evidence')
        before = destination.read_bytes()
        with patch.object(ui.filedialog, 'asksaveasfilename', return_value=str(destination)):
            self.panel.export('json')
            self.wait(lambda: not self.panel.busy)
        self.assertEqual(destination.read_bytes(), before)
        self.assertIn('Existing file preserved', self.panel.feedback.get())
        self.assertEqual(len(self.panel.table.get_children()), 4)

    def test_close_invalidates_late_worker_without_tk_callback(self):
        entered, release = threading.Event(), threading.Event()
        original = ui.read_selected_snapshot
        def delayed(*args, **kwargs):
            entered.set()
            release.wait(4)
            return original(*args, **kwargs)
        self.addCleanup(release.set)
        with patch.object(ui, 'read_selected_snapshot', side_effect=delayed):
            self.panel.load_snapshot(self.first, fixtures.IDENTITY)
            self.wait(entered.is_set)
            self.panel.close()
            self.assertIsNone(self.panel.timer)
            release.set()
            self.wait(lambda: not self.panel.results.empty())
        self.root.update()
        self.assertTrue(self.panel.closed)
        self.assertIsNone(self.panel.current)
        self.assertEqual(len(self.panel.table.get_children()), 0)
        self.assertEqual(self.errors, [])

    def test_narrow_large_text_keeps_controls_and_scrolling_reachable(self):
        self.load()
        for name in ('TkDefaultFont', 'TkTextFont'):
            tkfont.nametofont(name, root=self.root).configure(size=16)
        self.root.geometry('420x520')
        self.root.update()
        self.assertGreater(self.panel.search_entry.winfo_width(), 100)
        self.assertLessEqual(self.panel.search_entry.winfo_rootx() + self.panel.search_entry.winfo_width(),
                             self.panel.scroll.body.winfo_rootx() + self.panel.scroll.body.winfo_width() + 2)
        self.assertLessEqual(int(self.panel.source.cget('wraplength')), self.panel.scroll.body.winfo_width())
        self.assertTrue(self.panel.scroll.scrollbar.winfo_ismapped())
        self.panel.scroll.canvas.yview_moveto(1)
        self.root.update()
        self.assertGreater(self.panel.scroll.canvas.yview()[0], 0)
        if os.environ.get('DOOM_INSPECT_SCREENSHOT'):
            import subprocess
            subprocess.run(['import', '-window', str(self.root.winfo_id()), os.environ['DOOM_INSPECT_SCREENSHOT']], check=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
