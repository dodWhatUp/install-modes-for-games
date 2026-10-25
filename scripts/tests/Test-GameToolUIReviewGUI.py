"""Real Tk interactions on fictional installations in the isolated lab."""
import importlib.util,json,sys,time,tkinter as tk,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolUIReview import ReviewApp
spec=importlib.util.spec_from_file_location('review_test',Path(__file__).with_name('Test-GameToolUIReview.py'));test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)

class Tests(unittest.TestCase):
    def setUp(self):
        self.f=test.Tests();self.f.setUp();self.root=tk.Tk();self.errors=[];self.root.report_callback_exception=lambda typ,value,trace:self.errors.append(str(value));self.app=ReviewApp(self.root,self.f.model);self.pump()
    def pump(self):
        until=time.monotonic()+15
        while time.monotonic()<until:
            self.root.update()
            if not self.app.busy and self.app.events.empty() and not self.app.pending:break
            time.sleep(.02)
        self.root.update();self.assertFalse(self.app.busy);self.assertEqual(self.errors,[])
    def tearDown(self):
        self.pump();self.app.close();self.f.tearDown()
    def test_initial_selection_loads_real_typed_fields_without_writes(self):
        self.assertEqual(self.app.instance,'fixture-one');self.assertEqual(self.app.values()['amount'],2.0);self.assertEqual(self.f.f.path('fixture-one').read_bytes(),self.f.f.initial['fixture-one'])
    def test_hiding_settings_preserves_enabled_state_and_can_restore(self):
        self.app.variables['enabled'].set(False);key=next(k for k in self.app.sections if k.startswith('settings-'));self.app.hide_section(key,True);self.root.update();self.assertFalse(self.app.sections[key][0].winfo_ismapped());self.assertFalse(self.app.values()['enabled']);self.app.visibility.restore();self.root.update();self.assertTrue(self.app.sections[key][0].winfo_ismapped());self.assertFalse(self.app.values()['enabled'])
    def test_refresh_and_page_switch_keep_draft(self):
        self.app.variables['amount'].set('4.5');self.app.refresh();self.pump();self.assertEqual(self.app.values()['amount'],4.5);self.app.navigate('files');self.pump();self.app.navigate('mods');self.pump();self.assertEqual(self.app.values()['amount'],4.5)
    def test_switch_games_does_not_mix_drafts(self):
        self.app.variables['amount'].set('4.5');self.app.game.select('fixture-two');self.app.choose_game('fixture-two');self.pump();self.assertEqual(self.app.values()['amount'],2.0);self.app.game.select('fixture-one');self.app.choose_game('fixture-one');self.pump();self.assertEqual(self.app.values()['amount'],4.5)
    def test_float_and_hide_share_draft(self):
        self.app.floating_editor();self.app.variables['amount'].set('6');self.root.update();self.assertTrue(self.app.floating[0].winfo_exists());self.assertEqual(self.app.preview()['desired']['amount'],6.0)
    def test_cancelled_apply_does_not_write(self):
        self.app.variables['enabled'].set(False)
        with patch('GameToolUIReview.messagebox.askyesno',return_value=False):self.app.apply()
        self.assertEqual(self.f.f.path('fixture-one').read_bytes(),self.f.f.initial['fixture-one'])
    def test_manager_selector_prepares_chosen_program_and_keeps_game(self):
        self.app.destination.select('mod-organizer-2');self.app.choose_manager('mod-organizer-2');self.app.export();self.pump();manifest=json.loads((self.f.model.latest_export/'HANDOFF-MANIFEST.json').read_text());self.assertEqual(manifest['manager'],'mod-organizer-2');self.assertEqual(self.f.f.path('fixture-one').read_bytes(),self.f.f.initial['fixture-one'])
    def test_all_general_pages_and_zoom_dark_are_usable(self):
        for page in ['tools','profiles','reports','files','review','mods']:self.app.navigate(page);self.pump()
        self.app.dark.set(True);self.app.zoom.set('125');self.app.restyle();self.root.geometry('760x520');self.root.update();self.assertEqual(self.errors,[]);self.assertEqual(self.f.model.view['zoom'],125)
    def test_visibility_and_notes_survive_reopening_model(self):
        self.app.hide_section('locations',True);self.app.navigate('review');self.pump();self.app.notes.insert('1.0','I like the location controls');self.app.verdict.set('Like this direction');self.app.save_notes();self.assertFalse(json.loads((self.f.model.root/'feedback.json').read_text())['adopted']);self.app.navigate('mods');self.pump();self.assertTrue(self.app.hidden('locations'))
    def test_quick_locations_reveals_hidden_panel_and_targets_match_page(self):
        self.app.hide_section('locations',True);self.app.jump_section('locations');self.root.update();self.assertFalse(self.app.hidden('locations'))
        self.app.navigate('reports');self.pump();self.assertIn('spreadsheet',self.app.destination.records);self.assertNotIn('vortex',self.app.destination.records)
        self.app.navigate('profiles');self.pump();self.assertIn('azeron',self.app.destination.records)

if __name__=='__main__':unittest.main(verbosity=2)
