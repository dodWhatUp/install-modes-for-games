"""Isolated UI checks for module rows, shared drafts and local connection review."""
import importlib.util,json,sys,tkinter as tk,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolModControlsPanel import ModControlsPanel
spec=importlib.util.spec_from_file_location('wicked_fixture',Path(__file__).with_name('Test-GameToolWickedControls.py'))
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class Tests(unittest.TestCase):
    def setUp(self):
        self.fixture=fixture.Tests();self.fixture.setUp();self.root=tk.Tk();self.root.geometry('1000x760')
        self.root.report_callback_exception=lambda typ,value,trace:(_ for _ in ()).throw(value)
        self.panel=ModControlsPanel(self.root,self.fixture.data,service=self.fixture.controls,initial_game='no-rest-for-the-wicked')
        self.panel.pack(fill='both',expand=True);self.root.update()
    def tearDown(self):
        self.panel.close();self.root.destroy();self.fixture.tearDown()
    def test_modules_are_inside_existing_page_and_sources_are_exact(self):
        self.assertEqual(len(self.panel.row_actions),4)
        self.assertEqual([self.panel.module_tabs.tab(i,'text') for i in range(2)],['Game mods','Graphics tools'])
        self.assertIn('Coordination',[self.panel.pages.tab(i,'text') for i in range(len(self.panel.pages.tabs()))])
        for ident,buttons in self.panel.row_actions.items():
            mod=self.panel._module(ident)
            for source in ('github','nexus'):
                with patch('GameToolModControlsPanel.webbrowser.open') as opened:
                    buttons[source].invoke()
                    if mod.get(source):opened.assert_called_once_with(mod[source])
                    else:opened.assert_not_called();self.assertIn('disabled',buttons[source].state())
        self.assertEqual(self.fixture.config.read_bytes(),self.fixture.original)
    def test_options_use_shared_draft_and_reopen_near_the_pointer(self):
        with patch.object(self.panel,'winfo_pointerxy',return_value=(100,100)):first=self.panel.module_options('wicked-menu')
        self.panel.variables['wm-hotkey'].set('F10');first.withdraw()
        with patch.object(self.panel,'winfo_pointerxy',return_value=(650,450)):second=self.panel.module_options('wicked-menu')
        self.root.update();self.assertIs(first,second);self.assertIsNone(first.grab_current())
        self.assertEqual(self.panel.desired()['wm-hotkey'],'F10')
        self.assertNotEqual(first.winfo_x(),112)
        self.assertEqual(self.fixture.config.read_bytes(),self.fixture.original)
        self.panel._stash();self.assertEqual(json.loads(self.panel.view_path.read_text())['drafts']['fixture-wicked']['wm-hotkey'],'F10')
    def test_preview_and_graphics_share_selected_context_without_game_writes(self):
        with patch.object(self.panel,'winfo_pointerxy',return_value=(100,100)):view=self.panel.module_preview('rune-details')
        self.root.update();self.assertTrue(view.window.winfo_exists());self.assertEqual(view.detail['id'],'rune-details')
        self.panel.variables['build-liberator'].set(True);preview=self.panel.preview()
        self.assertTrue(preview['coordination']['blocked'])
        self.assertIn('requires MelonLoader',self.panel.coordination_text.get('1.0','end'))
        self.assertIn('Graphics tools',self.panel.coordination_text.get('1.0','end'))
        self.assertEqual(self.fixture.config.read_bytes(),self.fixture.original)
    def test_cancelled_local_connection_does_not_register_a_path(self):
        before=self.fixture.controls.instances.list_public(limit=64)
        with patch('GameToolModControlsPanel.filedialog.askdirectory',return_value=str(self.fixture.work)),patch('GameToolModControlsPanel.messagebox.askyesnocancel',return_value=None):
            self.panel.connect_prepared()
        self.assertEqual(self.fixture.controls.instances.list_public(limit=64),before)
        self.assertEqual(self.fixture.config.read_bytes(),self.fixture.original)
    def test_compact_rows_fit_narrow_width_without_growing(self):
        box=self.panel.module_rows_frames[0]
        self.root.update();before=[box.grid_bbox(row=i,column=0,col2=5,row2=i)[3] for i in range(4)]
        self.root.geometry('700x520');self.root.update()
        self.assertEqual(before,[box.grid_bbox(row=i,column=0,col2=5,row2=i)[3] for i in range(4)])
        for i in range(4):
            checkbox=box.grid_slaves(row=i,column=0)[0];state=box.grid_slaves(row=i,column=1)[0]
            self.assertLessEqual(checkbox.winfo_x()+checkbox.winfo_width(),state.winfo_x())
        for buttons in self.panel.row_actions.values():
            for button in buttons.values():self.assertLessEqual(button.winfo_x()+button.winfo_width(),box.winfo_width())

if __name__=='__main__':unittest.main(verbosity=2)
