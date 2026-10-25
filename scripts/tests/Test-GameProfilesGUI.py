"""Isolated guest Tk verification; no host input or native engines."""
import importlib.util,os,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolGameProfiles as api
import GameToolGameProfilesUI as ui
spec=importlib.util.spec_from_file_location('profiles_gui_fixture',Path(__file__).with_name('Test-GameProfiles.py'))
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)

@unittest.skipUnless(os.environ.get('DISPLAY'),'Requires the isolated guest display')
class GUI(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from tkinter import ttk
        fixtures.Profiles.setUp(self)
        self.root_ui=tk.Tk();self.root_ui.geometry('900x720');self.addCleanup(self.root_ui.destroy)
        self.engine=SimpleNamespace(start=mock.Mock(),readiness=lambda:{'fresh':True,'enabled':True,'triggers':1,
          'overlay_trigger':True,'route_enabled':True,'route_path':str(self.service.directory/'overlay-selection.ini')})
        self.overlay=SimpleNamespace(follow_layer=tk.BooleanVar(),result={'layer_state':'Event-tracked','reason':'Fixture'},
          foreground=lambda:{'exe':self.before['manifest']['associations'][0]['executables'][0]},tick=mock.Mock())
        self.unified=SimpleNamespace(engine=self.engine,install_root=self.root,tabs=mock.Mock())
        self.panel=ui.ProfilesPanel(ttk.Frame(self.root_ui),self.service.directory,self.unified,self.overlay,autostart=False)
        self.panel.parent.pack(fill='both',expand=True);self.root_ui.update();self.addCleanup(self.panel.close)
        self.service.put(self.profile,self.service.load()[1]);self.panel.game.select('game');self.panel.refresh()
    def test_save_selection_is_inert_and_activate_deactivate_are_distinct(self):
        self.assertEqual(self.library.store.load()[1],self.overlay_pin)
        self.panel.activate();self.root_ui.update()
        self.engine.start.assert_called_with(reveal=False)
        self.assertEqual(self.service.load()[0]['active_profile_id'],self.profile['id'])
        self.panel.deactivate();self.panel.tick()
        self.assertFalse(self.service.load()[0]['options']['enabled'])
        self.assertEqual(self.engine.start.call_count,1)
    def test_automatic_restore_and_options_survive_new_panel_read(self):
        self.panel.activate();self.panel.restore.set(True);self.panel.automatic.set(True);self.panel.save_options()
        self.panel.restore_profile();self.assertEqual(self.engine.start.call_count,2)
        self.panel.refresh();self.assertTrue(self.panel.restore.get());self.assertTrue(self.panel.automatic.get())
    def test_bad_native_readiness_is_visible_not_false_ready(self):
        self.panel.activate()
        self.engine.readiness=lambda:{'fresh':True,'enabled':True,'triggers':0,'overlay_trigger':False,'route_enabled':False}
        self.panel.refresh_status();self.assertIn('Needs attention',self.panel.summary.get())
        rows=[self.panel.table.item(x,'values')for x in self.panel.table.get_children()]
        self.assertEqual(next(x for x in rows if x[0]=='Overlay trigger')[1],'Needs attention')
    def test_manual_profile_is_not_overridden_for_same_focused_game(self):
        self.panel.activate();other=self.service.capture('game','Other default');self.service.put(other,self.service.load()[1])
        self.panel.automatic.set(True);self.panel.save_options();self.panel.tick()
        self.assertEqual(self.service.load()[0]['active_profile_id'],self.profile['id'])
    def test_narrow_scaled_page_keeps_controls_and_status_available(self):
        self.root_ui.geometry('720x620');self.root_ui.tk.call('tk','scaling',1.5);self.root_ui.update()
        self.assertTrue(self.panel.table.winfo_ismapped());self.assertTrue(self.panel.profile.winfo_ismapped())
        self.assertGreater(self.panel.table.winfo_width(),400)
        if os.environ.get('PROFILES_SCREENSHOT'):
            import subprocess
            subprocess.run(['import','-window',str(self.root_ui.winfo_id()),os.environ['PROFILES_SCREENSHOT']],check=True)
    def controller(self):
        import GameToolRewasd as native
        root=self.root/'native';config=root/'GENERAL/Controller/Config 1.rewasd';config.parent.mkdir(parents=True)
        config.write_bytes(api.overlay.encode({'schemaVersion':3.0,'appVersion':'9.5.0','devices':{'hardware':[],'virtual':{'gamepads':[{'type':'360'}]}}}))
        self.panel.service.rewasd=native.Native(self.service.directory,root,self.root)
        (self.root/'reWASDCommandLine.exe').write_bytes(b'fixture')
        p=self.panel.service.capture_rewasd('game','Fixture game','Controller setup',config,'Test controller','123',1)
        self.service.put(p,self.service.load()[1]);self.panel.refresh();self.panel.profile.select(p['id']);self.panel.refresh_status()
        return p
    def test_controller_selection_restore_never_starts_azeron_or_native_command(self):
        p=self.controller()
        with mock.patch('GameToolRewasd.subprocess.run')as run:
            self.panel.activate();self.panel.restore.set(True);self.panel.save_options();self.panel.restore_profile()
            run.assert_not_called();self.engine.start.assert_not_called()
        self.assertEqual(self.service.load()[0]['active_profile_id'],p['id'])
        self.assertIn('unverified',self.panel.summary.get())
        self.assertFalse(self.service.store.load()[0]['preferences']['display'])
    def test_controller_review_cancel_and_changed_selection_cannot_execute(self):
        p=self.controller()
        with mock.patch.object(self.panel.service.rewasd,'execute_reviewed')as execute, mock.patch.object(ui.messagebox,'askokcancel',return_value=False)as ask:
            self.panel.review_native(p,'apply');ask.assert_called_once();execute.assert_not_called()
            self.panel.profile.select(self.profile['id']);self.panel.review_native(p,'apply');execute.assert_not_called()
            self.assertIn('selection changed',self.panel.summary.get())
    def test_native_error_feedback_survives_periodic_status_refresh(self):
        self.controller();self.panel.activate();self.panel.native_results.put('Command failed; review reWASD')
        self.panel.tick();self.assertEqual(self.panel.native_feedback.get(),'Command failed; review reWASD')
    def test_controller_editor_cancel_then_save_preserves_native_file(self):
        from tkinter import ttk
        p=self.controller();before=self.service.load()[1];raw=Path(p['native']['config_path']).read_bytes()
        def descendants(w):
            return [child for c in w.winfo_children()for child in [c,*descendants(c)]]
        self.panel.edit_native(p);win=next(w for w in descendants(self.root_ui)if w.winfo_class()=='Toplevel')
        if os.environ.get('PROFILES_REWASD_EDITOR_SCREENSHOT'):
            self.root_ui.update()
            import subprocess
            subprocess.run(['import','-window',str(win.winfo_id()),os.environ['PROFILES_REWASD_EDITOR_SCREENSHOT']],check=True)
        next(w for w in descendants(win)if isinstance(w,ttk.Button)and w.cget('text')=='Cancel').invoke()
        self.assertEqual(self.service.load()[1],before)
        self.panel.edit_native(p);win=next(w for w in descendants(self.root_ui)if w.winfo_class()=='Toplevel')
        entry=next(w for w in descendants(win)if isinstance(w,ttk.Entry)and w.get()=='Test controller')
        entry.delete(0,'end');entry.insert(0,'Reviewed controller alias')
        next(w for w in descendants(win)if isinstance(w,ttk.Button)and w.cget('text')=='Save setup').invoke()
        saved=next(x for x in self.service.load()[0]['profiles']if x['id']==p['id'])
        self.assertEqual(saved['native']['device_name'],'Reviewed controller alias')
        self.assertEqual(Path(p['native']['config_path']).read_bytes(),raw)
    def test_narrow_controller_page_shows_native_state_without_azeron_readiness(self):
        self.controller();self.root_ui.geometry('720x620');self.root_ui.tk.call('tk','scaling',1.5)
        self.root_ui.update();self.panel.refresh_status()
        rows=[self.panel.table.item(x,'values')for x in self.panel.table.get_children()]
        self.assertIn('reWASD',[x[1]for x in rows]);self.assertNotIn('Studio',[x[0]for x in rows])
        if os.environ.get('PROFILES_REWASD_SCREENSHOT'):
            import subprocess
            subprocess.run(['import','-window',str(self.root_ui.winfo_id()),os.environ['PROFILES_REWASD_SCREENSHOT']],check=True)
    def test_unlisted_game_cancel_is_inert_and_saved_controller_keeps_its_game_name(self):
        before=self.service.load()[1]
        with mock.patch.object(ui.simpledialog,'askstring',return_value=None):self.panel.add_game()
        self.assertEqual(self.service.load()[1],before)
        with mock.patch.object(ui.simpledialog,'askstring',return_value='Unlisted Controller Game'):self.panel.add_game()
        self.assertEqual(self.panel.game.selected_id,'unlisted-controller-game');self.assertEqual(self.service.load()[1],before)
        self.assertTrue(self.panel.kind.get().startswith('reWASD'))

if __name__=='__main__':unittest.main()
