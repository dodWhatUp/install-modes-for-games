"""Isolated Tk acceptance: ranked choices, explicit connection and editable list."""
import importlib.util,json,sys,time,threading,tkinter as tk,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolModControlsPanel import ModControlsPanel
from GameToolModDiscoveryUI import LocationChooser
spec=importlib.util.spec_from_file_location('discovery_ui_fixture',Path(__file__).with_name('Test-GameToolModDiscovery.py'))
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class Tests(unittest.TestCase):
    def setUp(self):
        self.fx=fixture.Tests();self.fx.setUp();self.root=tk.Tk();self.root.geometry('1040x750')
        self.errors=[];self.root.report_callback_exception=lambda typ,value,trace:self.errors.append(value)
        self.panel=ModControlsPanel(self.root,self.fx.fx.data,service=self.fx.fx.controls,initial_game=fixture.GAME)
        self.panel.pack(fill='both',expand=True);self.root.update()
        self.dialog=LocationChooser(self.panel,discovery=self.fx.discovery,auto_scan=False)
        self.panel.location_choosers.append(self.dialog);self.report=self.fx.discovery.scan(fixture.GAME)
        self.dialog.present(self.report);self.root.update()
    def tearDown(self):
        self.panel.close();self.root.destroy();self.fx.tearDown();self.assertEqual(self.errors,[])
    def test_ranked_results_show_reasons_paths_and_remain_unconnected(self):
        self.assertEqual(self.dialog.tree.selection(),('0',));self.assertFalse(self.dialog.closed)
        self.assertIn(str(self.fx.work),self.dialog.details.get('1.0','end'))
        self.assertIn('AppID 1371980',self.dialog.details.get('1.0','end'))
        self.assertEqual(len(self.panel.controls.instances.list_public(limit=64)['instances']),1)
        self.assertIsNone(self.dialog.window.grab_current())
    def test_cancel_ownership_keeps_registry_and_chooser_unchanged(self):
        before=self.panel.controls.instances.list_public(limit=64)
        with patch('GameToolModControlsPanel.messagebox.askyesnocancel',return_value=None):self.dialog.use_selected()
        self.assertEqual(before,self.panel.controls.instances.list_public(limit=64));self.assertFalse(self.dialog.closed)
    def test_use_selected_can_explicitly_connect_read_only(self):
        with patch('GameToolModControlsPanel.messagebox.askyesnocancel',return_value=False):self.dialog.use_selected()
        self.assertTrue(self.dialog.closed)
        binding=self.panel.controls._binding(self.panel.current)
        self.assertFalse(binding['writes_enabled']);self.assertEqual(binding['workspace'],str(self.fx.work))
        self.assertEqual(self.fx.fx.config.read_bytes(),self.fx.fx.original)
    def test_stale_result_does_not_reach_local_connection(self):
        self.fx.write_manifest('Changed')
        with patch.object(self.panel,'use_discovered') as use:
            with self.assertRaisesRegex(Exception,'changed'):self.dialog.use_selected()
            use.assert_not_called()
    def test_background_scan_does_not_auto_select_a_connection(self):
        with patch.object(self.panel,'use_discovered') as use:
            self.dialog.scan();deadline=time.monotonic()+10
            while self.dialog.report is None and time.monotonic()<deadline:self.root.update();time.sleep(.02)
            self.assertIsNotNone(self.dialog.report);use.assert_not_called()
        with patch.object(self.panel,'register') as browse:self.dialog.manual(False);browse.assert_called_once_with()
    def test_editable_choices_click_typing_escape_and_keyboard_commit(self):
        box=self.panel.game_box;helper=self.panel.game_choices
        original=box.get();events=[];box.bind('<<ComboboxSelected>>',lambda _:events.append(box.get()))
        box.event_generate('<Button-1>',x=25,y=8);self.root.update()
        self.assertTrue(helper.visible);self.assertIs(self.root.focus_get(),box)
        self.assertLessEqual(box.index('insert'),len(original))
        self.panel.game.set('Wicked');self.root.update()
        self.assertTrue(helper.visible);self.assertTrue(all('wicked' in x.casefold() for x in helper.rows));self.assertEqual(events,[])
        box.event_generate('<Escape>');self.root.update();self.assertEqual(box.get(),original);self.assertFalse(helper.visible);self.assertEqual(events,[])
        box.event_generate('<Button-1>',x=35,y=8);self.root.update();self.panel.game.set('Wicked');self.root.update()
        box.event_generate('<Down>');box.event_generate('<Return>');self.root.update()
        self.assertEqual(events,[original]);self.assertFalse(helper.visible)
    def test_narrow_dialog_keeps_actions_visible(self):
        self.dialog.window.geometry('590x450');self.root.update()
        for widget in (self.dialog.use,self.dialog.refresh,self.dialog.details):
            self.assertLessEqual(widget.winfo_rootx()+widget.winfo_width(),self.dialog.window.winfo_rootx()+self.dialog.window.winfo_width())
        self.assertEqual(self.dialog.tree.column('location','stretch'),1)
    def test_escape_restores_selection_after_typing_with_the_list_closed(self):
        helper=self.panel.game_choices;original=self.panel.game.get()
        self.panel.game.set('Wick');helper.open();self.root.update();self.panel.game_box.event_generate('<Escape>');self.root.update()
        self.assertEqual(self.panel.game.get(),original)
    def test_closing_during_scan_cancels_its_pending_ui_callback(self):
        gate=threading.Event()
        with patch.object(self.fx.discovery,'scan',side_effect=lambda _:(gate.wait(2),self.report)[1]):
            self.dialog.scan();self.assertIsNotNone(self.dialog.pending_poll)
            self.dialog.close();gate.set();self.root.update()
        self.assertIsNone(self.dialog.pending_poll);self.assertTrue(self.dialog.closed)

if __name__=='__main__':unittest.main(verbosity=2)
