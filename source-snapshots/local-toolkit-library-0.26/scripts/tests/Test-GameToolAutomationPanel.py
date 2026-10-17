"""Headless native-widget integration checks, without screenshots or host input."""
import importlib.util, inspect, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
import GameToolAutomation as api
import GameToolModIntegration as integration
import GameToolWorkspace as workspace
import GameToolAppearance as appearance

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
old_tests=load('previous_hub_gui_fixture',S/'tests/Test-GameToolHubCatalog.py')
class WidgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.data=Path(self.tmp.name)/'new'
        self.root=tk.Tk();self.root.withdraw();self.errors=[];self.root.report_callback_exception=lambda *a:self.errors.append(str(a[1]));self.addCleanup(self.root.destroy)
        self.book=ttk.Notebook(self.root);self.old=ttk.Frame(self.book);self.book.add(self.old,text='Existing Tools')
        self.status=tk.StringVar(self.root);self.i=integration.Integration(self.book,self.data,self.status);self.root.update_idletasks()
    def tearDown(self):self.i.close();self.assertEqual(self.errors,[])
    def proposal(self):return self.i.service.propose('mods.create_plan',{'selected':['unity-mod-manager'],'mode':'real-time'},request_id='widget')
    def test_mount_preserves_old_tab(self):self.assertEqual([self.book.tab(t,'text') for t in self.book.tabs()],['Existing Tools','Mods','AI & automation'])
    def test_construction_no_data_mutation(self):self.assertFalse(self.data.exists())
    def test_watch_off_default(self):self.assertFalse(self.i.automation.watch.get());self.assertIsNone(self.i.automation._poll)
    def test_refresh_does_not_approve(self):
        self.proposal();self.i.automation.refresh();self.assertTrue(self.i.automation.tree.exists('widget'));self.assertFalse(self.i.service.mods_root.exists())
    def test_rejection_keeps_existing_data(self):
        self.proposal();self.i.automation.refresh();self.i.automation.tree.selection_set('widget');self.i.automation.reject()
        self.assertEqual(self.i.service.request_status('widget')['status'],'REJECTED');self.assertFalse(self.i.service.mods_root.exists())
    def test_approval_cancelled_at_dialog_does_nothing(self):
        self.proposal();self.i.automation.refresh();self.i.automation.tree.selection_set('widget')
        with patch('GameToolAutomationPanel.messagebox.askyesno',return_value=False):self.i.automation.approve()
        self.assertFalse(self.i.automation.busy);self.assertFalse(self.i.service.mods_root.exists())
    def test_approval_uses_same_jobs(self):
        self.proposal();p=self.i.automation;p.refresh();p.tree.selection_set('widget')
        with patch('GameToolAutomationPanel.messagebox.askyesno',return_value=True):p.approve()
        p.worker.join(3);self.assertFalse(p.busy);p.poll()
        job=self.i.service.request_status('widget')['result']['result']['job_id'];self.assertTrue((self.i.mods.data_root/'jobs'/job/'plan.json').exists())
    def test_copy_no_transmission(self):
        p=self.i.automation
        with patch.object(p,'clipboard_clear') as clear,patch.object(p,'clipboard_append') as append:
            p.copy_context();clear.assert_called_once();raw=append.call_args[0][0];self.assertEqual(json.loads(raw)['kind'],'ai_context')
        self.assertFalse(self.data.exists())
    def test_client_setup_read_only_by_default(self):
        value=self.i.automation.client_setup()['mcpServers']['unified-game-tools']
        self.assertEqual(value['args'][-1],'stdio');self.assertNotIn('--allow-requests',value['args'])
        self.assertIn(str(self.data),value['args']);self.assertFalse(self.data.exists())
    def test_proposal_client_setup_does_not_approve(self):
        self.i.automation.allow_client_requests.set(True)
        self.assertIn('--allow-requests',self.i.automation.client_setup()['mcpServers']['unified-game-tools']['args'])
        self.assertFalse(self.data.exists())
    def test_client_setup_not_in_ai_context(self):
        self.i.automation.client_setup();self.assertNotIn(str(self.data),json.dumps(self.i.service.context()))
    def test_close_cancels_worker_without_kill(self):
        class Busy:
            def is_alive(self):return True
        self.i.automation.worker=Busy();self.assertFalse(self.i.can_close());self.assertTrue(self.i.service.cancel.is_set())
    def test_mod_worker_blocks_ai_approval(self):
        class Busy:
            def is_alive(self):return True
        self.i.mods.worker=Busy();self.i.automation.approve();self.assertIn('active',self.i.automation.state.get())
    def test_ai_worker_blocks_mod_action(self):
        class Busy:
            def is_alive(self):return True
        self.i.automation.worker=Busy()
        with patch('game_mod_ops.panel.messagebox.showinfo'):self.i.mods.create_plan()
        self.assertIsNone(self.i.mods.job)
    def test_visibility_does_not_rebuild_or_create_jobs(self):
        refs=self.book.tabs()
        for _ in range(5):self.book.select(self.i.mods);self.book.select(self.i.automation);self.book.select(self.old)
        self.assertEqual(refs,self.book.tabs());self.assertFalse(self.data.exists())
    def test_adaptive_controls_and_field_ids(self):
        self.assertTrue(hasattr(self.i.mods.tree,'game_tools_column_layout'));self.assertTrue(hasattr(self.i.automation.tree,'game_tools_column_layout'))
    def test_navigation_extends_original_registry(self):
        r=integration.navigation_registry(workspace);self.assertEqual(r.features[:len(workspace.DEFAULT_FEATURES)],workspace.DEFAULT_FEATURES)
        self.assertEqual(r.goals[:len(workspace.DEFAULT_GOALS)],workspace.DEFAULT_GOALS);self.assertEqual(r.get('page.mods')['route'],'mods');self.assertEqual(r.get('page.automation')['route'],'automation')
    def test_request_draft_preserved_across_modes(self):
        self.proposal();self.i.automation.refresh();before=(self.i.service.requests/'widget/request.json').read_bytes()
        shell=workspace.Workspace(self.root,self.status,registry=integration.navigation_registry(workspace))
        shell.attach(self.book,{'tools':self.old,**self.i.routes})
        header=ttk.Frame(self.root);a=appearance.Appearance(self.root,header,shell,self.status,self.data/'ui-test.json','fixture')
        try:
            for mode in ('Modern','Classic','Modern'):
                a.preview(mode);self.root.update_idletasks()
            self.assertEqual((self.i.service.requests/'widget/request.json').read_bytes(),before)
            self.assertTrue(self.i.automation.tree.exists('widget'))
        finally:a.preview_only=True;a.close();shell.close()

class FullHubTests(old_tests.FullGUIContracts):
    def test_actual_hub_mounts_two_workspaces(self):
        self.build_gui();i=self.root.game_tools_mod_integration;self.assertIsNotNone(i);self.assertIn(str(i.mods),self.tabs.tabs());self.assertIn(str(i.automation),self.tabs.tabs())
        self.assertEqual([self.tabs.tab(t,'text') for t in self.tabs.tabs()][-2:],['Mods','AI & automation'])
    def test_new_tabs_isolate_legacy_shortcuts(self):
        self.build_gui();i=self.root.game_tools_mod_integration
        for page in (i.mods,i.automation):
            self.tabs.select(page);self.focus=page
            for key in ('o','s','i','e','t'):
                with patch.dict(self.shortcuts,{key:lambda:(_ for _ in ()).throw(AssertionError('leaked original action'))}):
                    self.assertEqual(self.send_callback(key),'break')
    def test_hub_close_has_operation_preflight(self):
        self.build_gui();i=self.root.game_tools_mod_integration
        class Busy:
            def is_alive(self):return True
        i.automation.worker=Busy();command=self.root.protocol('WM_DELETE_WINDOW');self.root.tk.call(command)
        self.assertTrue(self.root.winfo_exists());self.assertTrue(i.service.cancel.is_set())
    def test_actual_hub_tool_state_not_automatically_shared(self):
        self.build_gui();i=self.root.game_tools_mod_integration;self.assertEqual(i.service.context()['sections']['tool_status'],[])
        self.assertEqual(i.automation.tool_snapshot()['mode'],'learning')

if __name__=='__main__':
    suite=unittest.TestLoader().loadTestsFromTestCase(WidgetTests)
    suite.addTests(FullHubTests(n) for n in FullHubTests.__dict__ if n.startswith('test_'))
    r=unittest.TextTestRunner(verbosity=2).run(suite);raise SystemExit(not r.wasSuccessful())
