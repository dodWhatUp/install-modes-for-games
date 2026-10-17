"""Headless Tk widget behavior only; no screenshots or host desktop access."""
import json,sys,time,unittest,threading,gc
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).absolute().parents[1]))
import tkinter as tk
from tkinter import ttk
from test_keybinds import Fixtures,BASE
from game_keybind_ops.panel import Panel,attach
class PanelTests(Fixtures):
    def setUp(self):
        super().setUp();self.window=tk.Tk();self.window.withdraw();self.p=Panel(self.window,self.root/'data',self.s);self.p.pack()
    def tearDown(self):
        if self.p.working:self.p.cancel.set();self.wait()
        self.window.destroy();self.p=None;self.window=None;gc.collect();super().tearDown()
    def wait(self):
        end=time.monotonic()+4
        while self.p.working and time.monotonic()<end:self.window.update();time.sleep(.015)
        self.assertFalse(self.p.working)
    def test_initial_disabled_apply(self):self.assertIn('disabled',self.p.apply_button.state());self.assertEqual(self.path.read_bytes(),BASE)
    def test_worker_response(self):
        out=[];self.p.start(lambda:{'answer':7},out.append);self.wait();self.assertEqual(out,[{'answer':7}])
    def test_worker_error_returns_to_ui(self):
        def bad():raise ValueError('synthetic')
        with patch('game_keybind_ops.panel.messagebox.showerror') as report:self.p.start(bad,lambda _:None);self.wait();self.assertTrue(report.called)
    def test_other_host_busy_stops_work(self):
        self.p.busy_guard=lambda:True;self.fails('ACTION_BUSY',lambda:self.p.start(lambda:None,lambda _:None))
    def test_patch_stage_apply_undo_flow(self):
        e=self.edits();self.p.items=e;self.p.preview=self.s.preview(e);self.p.stage();self.wait();self.assertEqual(self.path.read_bytes(),BASE)
        with patch('game_keybind_ops.panel.messagebox.askyesno',return_value=True):self.p.apply();self.wait()
        self.assertNotEqual(self.path.read_bytes(),BASE);self.p.undo();self.wait();self.assertNotEqual(self.path.read_bytes(),BASE)
        with patch('game_keybind_ops.panel.messagebox.askyesno',return_value=True):self.p.apply();self.wait()
        self.assertEqual(self.path.read_bytes(),BASE)
    def test_denied_dialog_no_apply(self):
        self.p.plan=self.stage()
        with patch('game_keybind_ops.panel.messagebox.askyesno',return_value=False):self.p.apply()
        self.assertFalse(self.p.working);self.assertEqual(self.path.read_bytes(),BASE)
    def test_history_can_reopen_after_restart(self):
        self.stage();self.p.history();self.wait();self.p.saved.set('plan');self.p.open_saved();self.wait();self.assertEqual(self.p.plan['plan_id'],'plan');self.assertNotIn('disabled',self.p.apply_button.state())
    def test_stop_is_a_signal_not_process_kill(self):
        seen=[]
        def wait_cancel():self.p.cancel.wait(2);return self.p.cancel.is_set()
        self.p.start(wait_cancel,seen.append);self.p.stop_button.invoke();self.wait();self.assertEqual(seen,[True]);self.assertEqual(self.path.read_bytes(),BASE)
    def test_attach_preserves_existing_tab(self):
        nb=ttk.Notebook(self.window);old=ttk.Frame(nb);nb.add(old,text='Existing');new=attach(nb,self.root/'data',service=self.s)
        self.assertEqual(len(nb.tabs()),2);self.assertEqual(nb.tab(0,'text'),'Existing');new.destroy();nb.destroy()
if __name__=='__main__':unittest.main(verbosity=2)
