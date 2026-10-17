#!/usr/bin/env python3
"""Headless widget contracts. No screenshots, desktop input, game or network calls."""
import sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tkinter as tk
from tkinter import ttk
from game_mod_ops.panel import attach
class PanelTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=tk.Tk(); self.root.withdraw()
        self.book=ttk.Notebook(self.root); self.old=ttk.Frame(self.book); self.book.add(self.old,text='Existing Tools')
        self.pane=attach(self.book,data_root=Path(self.tmp.name));self.root.update()
    def tearDown(self):
        self.root.destroy();self.tmp.cleanup()
    def test_additive_mount_keeps_existing_tab(self):
        self.assertEqual(self.book.tab(self.old,'text'),'Existing Tools');self.assertEqual(len(self.book.tabs()),2)
    def test_construct_does_not_create_job(self):self.assertFalse(list(Path(self.tmp.name).iterdir()))
    def test_plan_no_network(self):
        with patch('game_mod_ops.panel.acquire',side_effect=AssertionError('must not acquire')):
            self.pane.create_plan();self.assertIsNotNone(self.pane.job)
            self.assertEqual(self.pane.job.latest('kingmaker-tactics')['status'],'PLANNED')
    def test_mode_preset_excludes_tactics(self):
        self.pane.mode.set('turn-based');self.pane.use_preset();self.assertFalse(self.pane.checks['kingmaker-tactics'].get())
    def test_checkbox_changes_not_existing_job(self):
        self.pane.create_plan();sha=self.pane.job.plan['plan_sha256'];self.pane.checks['buff-bot'].set(False)
        self.assertEqual(self.pane.job.plan['plan_sha256'],sha)
    def test_close_no_worker(self):self.assertTrue(self.pane.can_close())
    def test_close_requests_cancellation(self):
        class Running:
            def is_alive(self):return True
        self.pane.worker=Running();self.assertFalse(self.pane.can_close());self.assertTrue(self.pane.cancel_event.is_set())
    def test_no_install_button(self):
        labels=[]
        def walk(w):
            for c in w.winfo_children():
                if isinstance(c,ttk.Button):labels.append(c.cget('text'))
                walk(c)
        walk(self.pane);self.assertNotIn('Install',labels);self.assertIn('Stage selected',labels)
if __name__=='__main__':unittest.main(verbosity=2)
