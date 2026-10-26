"""Guest-only Tk acceptance. No host input, native apply, game or Overlay write."""
import json,os,runpy,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tkinter as tk
import GameToolControllerKeymaps as api
from GameToolControllerKeymapsUI import KeymapsPanel


class ControllerGUI(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name)
        self.native=self.base/'native';self.file=self.native/'GENERAL/Controller/Fixture.rewasd';self.file.parent.mkdir(parents=True)
        fixture=runpy.run_path(str(Path(__file__).with_name('Test-ControllerKeymaps.py')))['native_fixture']()
        self.file.write_text(json.dumps(fixture));self.native_bytes=self.file.read_bytes()
        self.native_patch=patch.object(api.rewasd,'native_root',return_value=self.native);self.native_patch.start();self.addCleanup(self.native_patch.stop)
        self.root=tk.Tk();self.root.geometry('1000x780+20+20');self.errors=[];self.root.report_callback_exception=lambda *a:self.errors.append(a)
        self.panel=KeymapsPanel(self.root,self.base/'data');self.panel.set_source('doom-the-dark-ages','DOOM: The Dark Ages',self.file)
        self.root.update();self.root.focus_force();self.root.update();self.addCleanup(self.root.destroy);self.addCleanup(self.panel.close)
    def tearDown(self):self.assertEqual(self.errors,[]);self.assertEqual(self.file.read_bytes(),self.native_bytes)
    def test_source_labels_hide_private_path_and_hash(self):
        self.assertEqual(self.panel.source.get(),'Fixture');self.assertNotIn(str(self.base),self.panel.source.get())
        self.assertNotIn(self.panel.draft['source']['sha256'],self.panel.source.get())
        self.assertEqual(self.panel.game.get(),'DOOM: The Dark Ages')
    def test_draft_annotation_and_save_are_explicit(self):
        identity=self.panel.table.get_children()[0];self.panel.table.selection_set(identity);self.root.update()
        self.panel.action.set('My game action');self.panel.icon.select('use');self.root.update()
        self.assertFalse(self.panel.library.path(self.panel.draft['id']).exists())
        self.panel.update_row();self.assertFalse(self.panel.library.path(self.panel.draft['id']).exists())
        self.panel.save();saved=self.panel.library.load(self.panel.draft['id'])
        binding=next(x for x in saved['bindings'] if x['id']==identity)
        self.assertEqual(binding['annotations']['gameplay']['label'],'My game action')
        self.assertEqual(binding['annotations']['gameplay']['icon'],'use')
    def test_open_list_keeps_typing_caret_without_saving(self):
        combo=self.panel.action;combo.event_generate('<ButtonPress-1>',x=12,y=10);self.root.update()
        combo.delete(0,'end');combo.insert(0,'custom');combo.event_generate('<KeyRelease-m>');self.root.update()
        self.assertTrue(combo.game_tools_editable_list.visible);self.assertEqual(combo.index('insert'),6)
        self.assertIs(self.root.focus_get(),combo);self.assertFalse(self.panel.library.path(self.panel.draft['id']).exists())
        combo.event_generate('<Escape>');self.root.update();self.assertFalse(combo.game_tools_editable_list.visible)
    def test_icons_visibility_is_draft_presentation_only(self):
        old=json.loads(json.dumps(self.panel.draft['bindings']));self.panel.show_icons.set(False);self.panel.change_icon_visibility()
        self.assertEqual(old,self.panel.draft['bindings']);self.assertFalse(self.panel.draft['presentation']['show_icons'])
        self.assertFalse(self.panel.library.path(self.panel.draft['id']).exists())
    def test_narrow_window_preserves_short_controls_and_scope(self):
        self.root.geometry('560x780+20+20');self.root.update()
        self.assertLessEqual(self.panel.game.winfo_rootx()+self.panel.game.winfo_width(),self.root.winfo_rootx()+self.root.winfo_width())
        self.assertLessEqual(self.panel.source.winfo_width(),350)
        self.assertEqual(len(self.panel.table.get_children()),2)
        if os.environ.get('CONTROLLER_KEYMAP_GUI_SCREENSHOT') and os.name!='nt':
            import subprocess
            subprocess.run(['import','-window','root',os.environ['CONTROLLER_KEYMAP_GUI_SCREENSHOT']],check=True)


if __name__=='__main__':unittest.main(verbosity=2)
