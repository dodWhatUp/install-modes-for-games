"""Presentation ownership and restore behavior; fictional Tk roots only."""
import json,sys,tempfile,tkinter as tk,unittest
from pathlib import Path
from tkinter import ttk
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolWindowsApp as app

class Tests(unittest.TestCase):
    def test_identities_are_unique_stable_and_have_authored_assets(self):
        ids=[row[0]for row in app.APPS.values()]
        self.assertEqual(len(ids),len(set(ids)))
        for key in app.APPS:
            self.assertLess(len(app.APPS[key][0]),128);self.assertNotIn(' ',app.APPS[key][0])
            for suffix in ('ico','png','svg'):self.assertTrue(app.icon_path(key,suffix).is_file())
    def test_instance_scopes_do_not_overlap_and_unified_keeps_existing_mutex(self):
        with tempfile.TemporaryDirectory()as p:
            self.assertEqual(app.names('unified',p)[0].split('-')[0],'Local\\GameToolsUnified')
            self.assertNotEqual(app.names('shadow',p),app.names('wicked',p))
            self.assertNotEqual(app.names('shadow',p),app.names('shadow',Path(p)/'another'))
    def test_restore_request_is_inert_outside_windows(self):
        with patch.object(app.os,'name','posix'):self.assertFalse(app.request_existing('unified',Path.cwd()))

class GUI(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.root.geometry('600x400');self.root.update()
        self.errors=[];self.root.report_callback_exception=lambda *a:self.errors.append(str(a[1]))
    def tearDown(self):
        try:self.root.destroy()
        except tk.TclError:pass
        self.assertEqual(self.errors,[])
    def test_close_button_calls_current_guard_once_and_retains_rejected_draft(self):
        draft=tk.StringVar(self.root,'unsaved');calls=[]
        self.root.protocol('WM_DELETE_WINDOW',lambda:calls.append(draft.get()))
        header=ttk.Frame(self.root);header.pack();menu=tk.Menu(self.root,tearoff=False)
        controls=app.add_window_controls(header,self.root,menu)
        close=controls.winfo_children()[1];close.invoke();self.root.update()
        self.assertEqual(calls,['unsaved']);self.assertEqual(draft.get(),'unsaved');self.assertTrue(self.root.winfo_exists())
        menu.invoke('Close application');self.assertEqual(calls,['unsaved','unsaved'])
    def test_hide_control_only_minimizes_and_never_calls_close_guard(self):
        calls=[];self.root.protocol('WM_DELETE_WINDOW',lambda:calls.append('close'))
        with patch.object(self.root,'iconify')as hide:
            header=ttk.Frame(self.root);header.pack();menu=tk.Menu(self.root,tearoff=False)
            controls=app.add_window_controls(header,self.root,menu);controls.winfo_children()[0].invoke()
            hide.assert_called_once();self.assertEqual(calls,[])
    def test_restoring_session_keeps_same_root_selection_and_draft(self):
        with patch.object(app.os,'name','posix'):
            session=app.Session('unified',Path.cwd());session.attach(self.root)
        draft=tk.StringVar(self.root,'retain this draft');self.root.withdraw();session.show();self.root.update()
        self.assertEqual(self.root.state(),'normal');self.assertIs(session.root,self.root);self.assertEqual(draft.get(),'retain this draft')
        session.close();self.assertTrue(self.root.winfo_exists())
    def test_controls_support_grid_parent_without_mixing_managers(self):
        header=ttk.Frame(self.root);header.pack();ttk.Entry(header).grid(row=0,column=0)
        menu=tk.Menu(self.root,tearoff=False);controls=app.add_window_controls(header,self.root,menu,pack=False)
        controls.grid(row=0,column=1);self.root.update();self.assertEqual(controls.winfo_manager(),'grid')

if __name__=='__main__':unittest.main(verbosity=2)
