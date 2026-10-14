"""Owned headless-widget checks; no host input, screenshot or provider operation."""
import importlib.util,json,sys,tempfile,unittest,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
from GameToolFocusUI import FocusPreferences,FocusSurface,DEFAULT
from GameToolFocusPanels import FocusModPanel,FocusAutomationPanel,concise_result
from GameToolModIntegration import Integration,navigation_registry
import GameToolWorkspace as wa
from GameToolAppearance import Appearance

class SettingsTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'focus-view.json'
 def test_default_read_has_no_write(self):self.assertEqual(FocusPreferences(self.path).value,DEFAULT);self.assertFalse(self.path.exists())
 def test_save_read(self):
  p=FocusPreferences(self.path);p.save(dict(DEFAULT,zoom=150));self.assertEqual(FocusPreferences(self.path).value['zoom'],150)
 def test_compare_and_swap(self):
  a=FocusPreferences(self.path);b=FocusPreferences(self.path);a.save(dict(DEFAULT,zoom=120))
  with self.assertRaises(ValueError):b.save(dict(DEFAULT,zoom=110))
 def test_invalid_zoom(self):
  for v in (79,81,210,True,'100'):
   with self.assertRaises(ValueError):FocusPreferences.validate(dict(DEFAULT,zoom=v))
 def test_corrupt_file_preserved(self):
  self.path.write_text('{broken');p=FocusPreferences(self.path)
  with self.assertRaises(ValueError):p.save(DEFAULT)
  self.assertEqual(self.path.read_text(),'{broken')
 def test_unknown_keys(self):
  with self.assertRaises(ValueError):FocusPreferences.validate(dict(DEFAULT,approve=True))
 def test_invalid_route(self):
  with self.assertRaises(ValueError):FocusPreferences.validate(dict(DEFAULT,route='exec'))
 def test_exact_failure_code(self):self.assertIn('DENIED',concise_result({'status':'DENIED','message':'Keep current job.'}))

class PanelTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.data=Path(self.tmp.name)/'private'
  self.root=tk.Tk();self.root.withdraw();self.errors=[];self.root.report_callback_exception=lambda *e:self.errors.append(str(e[1]));self.addCleanup(self.root.destroy)
  self.book=ttk.Notebook(self.root);self.book.pack(fill='both',expand=True);self.status=tk.StringVar(self.root)
  self.i=Integration(self.book,self.data,self.status,focus=True);self.root.update_idletasks()
 def tearDown(self):self.i.close();self.assertEqual(self.errors,[])
 def test_alternative_classes(self):self.assertIsInstance(self.i.mods,FocusModPanel);self.assertIsInstance(self.i.automation,FocusAutomationPanel)
 def test_no_storage_on_open(self):self.assertFalse(self.data.exists())
 def test_technical_details_collapsed(self):self.assertFalse(self.i.mods.technical.opened)
 def test_optional_choices_preserved(self):
  p=self.i.mods;before={k:v.get() for k,v in p.checks.items()};p.choose_box.toggle();p.choose_box.toggle();self.assertEqual(before,{k:v.get() for k,v in p.checks.items()})
 def test_columns_full_and_essential(self):
  p=self.i.mods;rows=p.tree.get_children();p.columns.preset.set('Full');p.columns.apply();self.assertEqual(len(p.tree['displaycolumns']),4);self.assertEqual(p.tree.get_children(),rows)
 def test_search_does_not_edit_plan(self):
  p=self.i.mods;p.query.set('Tactics');self.assertEqual(p.tree.get_children(),('kingmaker-tactics',));self.assertIsNone(p.job);p.query.set('');self.assertEqual(len(p.tree.get_children()),len(p.recipe['items']))
 def test_column_filter(self):
  p=self.i.mods;p.query.set('name:Tactics');self.assertEqual(p.tree.get_children(),('kingmaker-tactics',))
 def test_sort_is_not_install_order(self):
  p=self.i.mods;before=[i['id'] for i in p.recipe['items']];p.columns.set_sort('name',True);self.assertEqual(before,[i['id'] for i in p.recipe['items']])
 def test_create_plan_same_backend(self):
  p=self.i.mods;p.create_plan();self.assertTrue((p.job.path/'plan.json').exists());self.assertTrue(p.job.path.is_relative_to(self.i.service.mods_root))
 def test_mode_change_not_implicit(self):
  p=self.i.mods;p.mode.set('turn-based');self.assertTrue(p.checks['kingmaker-tactics'].get());p.use_preset();self.assertFalse(p.checks['kingmaker-tactics'].get())
 def test_failure_not_success(self):
  p=self.i.mods;p.messages.put({'status':'ACCESS_DENIED','message':'No retry.'});p.poll();self.assertIn('ACCESS_DENIED',p.status.get());self.assertNotIn('finished',p.status.get().lower())
 def test_ai_default_no_refresh_or_proposals(self):self.assertFalse(self.i.automation.watch.get());self.assertFalse(self.i.automation.allow_client_requests.get());self.assertIsNone(self.i.automation._poll)
 def test_ai_exact_request_visible(self):
  a=self.i.automation;a.service.propose('mods.create_plan',{'selected':['unity-mod-manager'],'mode':'real-time'},request_id='focus-test');a.refresh();a.tree.selection_set('focus-test');a.show_selected()
  self.assertIn('unity-mod-manager',a.output.get('1.0','end'));self.assertIn('AWAITING_LOCAL_APPROVAL',a.output.get('1.0','end'))
 def test_ai_cancelled_approval(self):
  a=self.i.automation;a.service.propose('mods.create_plan',{'selected':['unity-mod-manager'],'mode':'real-time'},request_id='focus-test');a.refresh();a.tree.selection_set('focus-test')
  with patch('GameToolAutomationPanel.messagebox.askyesno',return_value=False):a.approve()
  self.assertFalse(a.busy);self.assertFalse(a.service.mods_root.exists())
 def test_same_approval_method(self):
  from GameToolAutomationPanel import AutomationPanel
  self.assertIs(FocusAutomationPanel.approve,AutomationPanel.approve)
 def test_same_network_method(self):
  from game_mod_ops.panel import ModWorkflowPanel
  self.assertIs(FocusModPanel.download,ModWorkflowPanel.download)
 def test_stop_retains_requests(self):
  a=self.i.automation;a.service.propose('mods.create_plan',{'selected':['unity-mod-manager'],'mode':'real-time'},request_id='focus-test');p=a.service.requests/'focus-test/request.json';raw=p.read_bytes();a.stop();self.assertEqual(raw,p.read_bytes())
 def test_selection_warning_visible(self):
  p=self.i.mods;p.tree.selection_set('kingmaker-tactics');p.show_details();self.assertIn('undiscovered',p.summary.get());self.assertFalse(p.technical.opened)

class SurfaceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.data=Path(self.tmp.name)/'view'
  self.root=tk.Tk();self.root.geometry('1280x760');self.errors=[];self.root.report_callback_exception=lambda *e:self.errors.append(str(e[1]));self.addCleanup(self.root.destroy)
  self.status=tk.StringVar(self.root);self.header=ttk.Frame(self.root);self.header.pack(fill='x');self.banner=tk.Label(self.root,text='Original scope');self.banner.pack(fill='x')
  self.root.game_tools_scope_banner=self.banner
  self.w=wa.Workspace(self.root,self.status,registry=navigation_registry(wa));self.w.frame.pack(fill='both',expand=True)
  self.book=ttk.Notebook(self.w.content);self.book.pack(fill='both',expand=True)
  self.i=Integration(self.book,self.data,self.status,focus=True);self.w.attach(self.book,self.i.routes)
  self.a=Appearance(self.root,self.header,self.w,self.status,self.data/'ui-preferences.json','fixture')
  self.surface=FocusSurface(self.root,self.header,self.banner,self.w,self.status,self.a,self.data,self.i)
  self.pump()
 def pump(self):
  for _ in range(3):self.root.update_idletasks();self.root.update()
 def tearDown(self):
  self.surface.close();self.i.close();self.a.preview_only=True;self.a.close();self.w.close();self.assertEqual(self.errors,[])
 def test_dense_header_hides_old_bands(self):self.assertFalse(self.header.winfo_ismapped());self.assertFalse(self.banner.winfo_ismapped());self.assertFalse(self.w.toolbar.winfo_ismapped())
 def test_essential_workspace_visible(self):self.assertTrue(self.i.mods.winfo_ismapped());self.assertTrue(self.surface.commands.winfo_ismapped())
 def test_typed_search_never_navigates(self):
  before=self.book.select();self.surface.query.set('AI');self.pump();self.assertEqual(self.book.select(),before)
 def test_search_enter_selects(self):self.surface.query.set('AI requests');self.surface.commit_search();self.pump();self.assertEqual(self.book.select(),str(self.i.automation))
 def test_search_esc_retains_page(self):
  before=self.book.select();self.surface.query.set('AI');self.surface.cancel_search();self.assertEqual(self.book.select(),before)
 def test_route_no_job_or_approval(self):
  for _ in range(5):self.surface.navigate('automation');self.surface.navigate('mods')
  self.assertFalse(self.i.service.mods_root.exists());self.assertIsNone(self.i.mods.job)
 def test_original_focus_switch_preserves_widgets_and_draft(self):
  self.i.mods.mode.set('turn-based');ids=self.book.tabs();self.surface.deactivate();self.pump();self.surface.activate();self.pump();self.assertEqual(self.book.tabs(),ids);self.assertEqual(self.i.mods.mode.get(),'turn-based')
 def test_zoom_saved_separately(self):
  self.surface.zoom.set(150);self.surface.apply_display();self.pump();self.assertTrue((self.data/'focus-view.json').exists());self.assertFalse((self.data/'ui-preferences.json').exists())
 def test_zoom_density_independent(self):
  self.surface.zoom.set(150);self.surface.density.set('Comfortable');self.surface.apply_display();self.assertEqual(self.surface.zoom.get(),150)
 def test_zoom_200_and_narrow_retains_routes(self):
  self.root.geometry('820x700');self.surface.zoom.set(200);self.surface.apply_display();self.pump();self.assertEqual(self.book.tabs(),tuple(self.w.route_tabs.values()));self.assertTrue(self.surface.selector.winfo_ismapped());self.surface.navigate('automation');self.pump();self.assertTrue(self.i.automation.winfo_ismapped())
 def test_reset_changes_only_view(self):
  self.i.mods.mode.set('turn-based');self.surface.reset();self.assertEqual(self.i.mods.mode.get(),'turn-based');self.assertIsNone(self.i.mods.job)
 def test_stop_uses_existing_channels(self):self.surface.stop_work();self.assertTrue(self.i.mods.cancel_event.is_set());self.assertTrue(self.i.service.cancel.is_set())
 def test_compact_header_space(self):self.assertLess(self.surface.commands.winfo_height(),130)
 def test_modal_keeps_focus(self):
  with patch.object(self.root,'grab_current',return_value=object()):self.assertIsNone(self.surface.focus_search())
 def test_no_repeated_resize_jobs(self):
  for _ in range(10):self.pump()
  self.assertIsNone(self.surface._layout_job)

if __name__=='__main__':unittest.main(verbosity=2)
