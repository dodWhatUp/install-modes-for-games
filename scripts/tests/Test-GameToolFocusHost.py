"""Full Hub routing with the Focus view; native/provider effects are forbidden fixtures."""
import importlib.util,inspect,json,sys,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('focus_host_fixture',S/'tests/Test-GameToolHubCatalog.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
from GameToolFocusPanels import FocusModPanel,FocusAutomationPanel
class FocusHost(fixture.NativeTkFixtures):
 def build(self):
  original=fixture.hub.gui
  with mock.patch.object(fixture.hub,'gui',side_effect=lambda *a,**kw:original(*a,**kw,interface_preview='Focus')):
   fixture.FullGUIContracts.build_gui(self)
  self.surface=self.root.game_tools_focus;self.integration=self.root.game_tools_mod_integration
  self.addCleanup(self.close_panels)
  self.root.update_idletasks()
 def close_panels(self):
  self.surface.close();self.integration.close();self.surface.appearance.preview_only=True;self.surface.appearance.close();self.surface.w.close()
  if self.session_panel:self.session_panel.close()
  if self.panel:self.panel.close()
 def test_full_host_mounts_real_focus_classes(self):
  self.build();self.assertTrue(self.surface.active);self.assertIsInstance(self.integration.mods,FocusModPanel);self.assertIsInstance(self.integration.automation,FocusAutomationPanel)
 def test_all_original_routes_preserved(self):
  self.build();self.assertEqual(len(self.tabs.tabs()),11)
  self.assertEqual([self.tabs.tab(t,'text') for t in self.tabs.tabs()],['Tools','Sensors','RTSS','Reports','How to use','Catalog','Comparison','Sessions','Overlays','Mods','AI & automation'])
 def test_same_backend_and_no_client_activation(self):
  self.build();self.assertIs(self.integration.automation.service,self.integration.service);self.assertFalse(self.integration.service.mods_root.exists());self.assertFalse(self.integration.automation.allow_client_requests.get())
 def test_find_control_has_visible_label(self):
  self.build();self.assertEqual(self.surface.search_label.cget('text'),'Find')
 def test_ctrl_k_uses_focus_search(self):
  self.build();self.focus=self.integration.mods
  with mock.patch.object(self.surface,'focus_search',return_value='break') as spy:
   fixture.FullGUIContracts.send_callback(self,'k');spy.assert_called_once()
 def test_cancelled_approval_uses_original_policy(self):
  self.build();self.surface.navigate('automation');a=self.integration.automation
  a.service.propose('mods.create_plan',{'selected':['unity-mod-manager'],'mode':'real-time'},request_id='host-focus');a.refresh();a.tree.selection_set('host-focus')
  with mock.patch('GameToolAutomationPanel.messagebox.askyesno',return_value=False):a.approve()
  self.assertFalse(a.busy);self.assertFalse(a.service.mods_root.exists())
 def test_navigation_and_zoom_do_not_change_plan(self):
  self.build();p=self.integration.mods;before={k:v.get() for k,v in p.checks.items()}
  for route in ('reports','comparison','catalog','mods'):
   self.assertTrue(self.surface.navigate(route));self.surface.zoom.set(150);self.surface.apply_display()
  self.assertEqual(before,{k:v.get() for k,v in p.checks.items()});self.assertIsNone(p.job)
 def test_stop_tracks_the_actual_active_channel(self):
  self.build();worker=mock.Mock();worker.is_alive.return_value=True;self.integration.mods.worker=worker
  self.integration.mods.status.set('Downloading chosen plan')
  self.root.update_idletasks();self.assertFalse(self.surface.stop.instate(['disabled']))
  self.surface.stop.invoke();self.assertTrue(self.integration.mods.cancel_event.is_set())
  worker.is_alive.return_value=False;self.integration.mods.status.set('Stopped');self.root.update_idletasks();self.assertTrue(self.surface.stop.instate(['disabled']))
 def test_manual_narrow_navigation_can_open(self):
  self.build();self.root.deiconify();self.root.geometry('660x640');self.surface.layout()
  self.surface.nav.set(True);self.surface.apply_navigation();self.surface.layout()
  self.assertTrue(self.surface.w.show_navigation.get())
 def test_original_navigation_switch_keeps_new_view_drafts(self):
  self.build();p=self.integration.mods;p.mode.set('turn-based');ids=self.tabs.tabs()
  self.surface.deactivate();self.surface.activate();self.assertEqual(ids,self.tabs.tabs());self.assertEqual(p.mode.get(),'turn-based')
if __name__=='__main__':unittest.main(verbosity=2)
