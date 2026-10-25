"""Real Tk interaction on disposable installations; run in the isolated GUI lab."""
import importlib.util,json,sys,tkinter as tk,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolModControlsPanel import ModControlsPanel
spec=importlib.util.spec_from_file_location('controls_fixture',Path(__file__).with_name('Test-GameToolModControls.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class Tests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.Tests();self.fixture.setUp();self.root=tk.Tk();self.root.geometry('1000x740')
        self.root.report_callback_exception=lambda typ,value,trace:(_ for _ in ()).throw(value)
        self.panel=ModControlsPanel(self.root,self.fixture.data,service=self.fixture.controls,initial_game='fixture-one');self.panel.pack(fill='both',expand=True);self.root.update()
    def tearDown(self):
        self.panel.close();self.root.destroy();self.fixture.tearDown()
    def test_applied_state_is_visible_and_preview_does_not_write(self):
        self.assertEqual(self.panel.current,'fixture-one');self.assertEqual(self.panel.variables['amount'].get(),'2.0')
        self.panel.variables['amount'].set('4.5');self.panel.preview();self.assertIn('4.5',self.panel.preview_text.get('1.0','end'));self.assertEqual(self.fixture.path('fixture-one').read_bytes(),self.fixture.initial['fixture-one'])
    def test_floating_editor_shares_draft_and_survives_narrow_layout(self):
        self.panel.float_settings();self.root.update();self.assertEqual(len(self.panel.floating),1)
        self.panel.variables['enabled'].set(False);self.root.geometry('640x430');self.root.update()
        self.assertTrue(self.panel.floating[0].winfo_exists());self.assertFalse(self.panel.desired()['enabled']);self.assertEqual(self.fixture.path('fixture-one').read_bytes(),self.fixture.initial['fixture-one'])
    def test_switch_and_reopen_keep_drafts_per_installation(self):
        self.panel.variables['amount'].set('3.25');self.panel.instance.set('fixture-two');self.panel.load_instance();self.assertEqual(self.panel.variables['amount'].get(),'2.0')
        self.panel.instance.set('fixture-one');self.panel.load_instance();self.assertEqual(self.panel.variables['amount'].get(),'3.25')
        self.panel.close();self.panel.destroy();self.panel=ModControlsPanel(self.root,self.fixture.data,service=self.fixture.controls,initial_game='fixture-one');self.panel.pack(fill='both',expand=True)
        self.assertEqual(self.panel.variables['amount'].get(),'3.25')
    def test_saved_profile_loads_into_preview(self):
        self.panel.variables['amount'].set('6.5')
        with patch('GameToolModControlsPanel.simpledialog.askstring',return_value='my-profile'):self.panel.save_profile()
        self.panel.variables['amount'].set('1');self.panel.profile.set(next(iter(self.panel.profile_rows)));self.panel.load_profile();self.assertEqual(self.panel.desired()['amount'],6.5)
        self.assertEqual(self.fixture.path('fixture-one').read_bytes(),self.fixture.initial['fixture-one'])
    def test_apply_confirmation_uses_same_service_and_refreshes_state(self):
        self.panel.variables['enabled'].set(False)
        with patch('GameToolModControlsPanel.messagebox.askyesno',return_value=True):self.panel.apply()
        self.assertFalse(self.panel.observation['values']['enabled']);self.assertNotIn('fixture-one',self.panel.drafts)
        self.assertEqual(self.fixture.path('fixture-two').read_bytes(),self.fixture.initial['fixture-two'])
    def test_cancelled_apply_keeps_bytes_and_draft(self):
        self.panel.variables['amount'].set('8')
        with patch('GameToolModControlsPanel.messagebox.askyesno',return_value=False):self.panel.apply()
        self.assertEqual(self.panel.desired()['amount'],8);self.assertEqual(self.fixture.path('fixture-one').read_bytes(),self.fixture.initial['fixture-one'])
    def test_prepare_manager_and_inspector_are_separate_from_apply(self):
        self.panel.prepare_manager();self.assertTrue(self.fixture.controls.export_path_local('fixture-one').is_dir())
        data=json.loads(self.panel.inspect_text.get('1.0','end'));self.assertTrue(data['schema']);self.assertNotIn(str(self.fixture.base),json.dumps(data));self.assertEqual(self.fixture.path('fixture-one').read_bytes(),self.fixture.initial['fixture-one'])
    def test_ai_tab_uses_selected_installation_and_has_no_model_approval_tool(self):
        self.assertEqual(self.panel.ai.service.instance_id,'fixture-one');self.panel.instance.set('fixture-two');self.panel.load_instance();self.assertEqual(self.panel.ai.service.instance_id,'fixture-two')
        self.assertIn('mod_controls_inspect',{r['name'] for r in fixture.Endpoint(type('Facade',(),{'multi_game':True,'controls':self.fixture.controls})(),True).call.__globals__['tools'](True,True)})
    def test_folder_registration_selects_new_identity_without_editing_game(self):
        root=self.fixture.base/'second-copy';root.mkdir();(root/'Fixture.exe').write_bytes(b'never executed')
        with patch('GameToolModControlsPanel.filedialog.askdirectory',return_value=str(root)):self.panel.register()
        self.assertNotIn(self.panel.current,{'fixture-one','fixture-two'});self.assertEqual(self.panel.observation['status'],'CONTROL_CONNECTION_REQUIRED')
        self.assertEqual(list(root.iterdir()),[root/'Fixture.exe'])

if __name__=='__main__':unittest.main(verbosity=2)
