"""Real headless Tk widget/action tests on owned temporary data; no screenshots."""
import json,sys,tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
from GameToolWorkbench import Workbench
from GameToolGameWorkspaces import ViewState

class UITests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.data=Path(self.tmp.name)/'private';self.root=tk.Tk();self.errors=[]
  self.root.report_callback_exception=lambda *e:self.errors.append(str(e[1]));self.a=Workbench(self.root,self.data);self.root.update()
 def tearDown(self):
  self.a.model.runner.stop();deadline=time.time()+3
  while self.a.model.runner.active() and time.time()<deadline:time.sleep(.01)
  self.a.close();self.tmp.cleanup();self.assertEqual(self.errors,[])
 def sample(self,suffix='beta'):
  r=self.a.model.create_samples_local(confirmed=True)
  for x in r['jobs']:self.a.view.value['games'].setdefault(x['game_id'],{})['job_id']=x['job_id']
  self.a.load_game('workflow-sample-'+suffix);self.root.update()
 def drain(self):
  end=time.time()+3
  while self.a.model.runner.active() and time.time()<end:self.root.update();time.sleep(.01)
  # Consume on the normal event-loop polling path, not by executing operations again.
  self.root.after(210,self.root.quit);self.root.mainloop();self.root.update()
 def test_initial_geometry_and_default_real_recipe(self):
  self.assertGreater(self.a.main.winfo_width(),500);self.assertGreater(self.a.mods.winfo_height(),200)
  self.assertEqual(self.a.game_id,'pathfinder-kingmaker');self.assertTrue(self.a.mods.selection())
 def test_default_essential_columns_and_version_reveal(self):
  self.assertNotIn('version',self.a.mods['displaycolumns']);ids=self.a.mods.get_children();self.a.toggle_versions()
  self.assertIn('version',self.a.mods['displaycolumns']);self.assertEqual(ids,self.a.mods.get_children());self.a.toggle_versions()
 def test_known_unsupported_game_no_fake_actions(self):
  self.a.load_game('cyberpunk-2077');self.root.update()
  self.assertIsNone(self.a.recipe);self.assertEqual(self.a.primary['text'],'Import recipe');self.assertIn('catalog',self.a.subtitle.get())
 def test_per_game_draft_filter_and_mode_preserved(self):
  self.a.mode.set('turn-based');self.a.use_preset();self.a.query.set('Buff Bot');self.a.load_game('cyberpunk-2077');self.a.load_game('pathfinder-kingmaker')
  self.assertEqual(self.a.mode.get(),'turn-based');self.assertEqual(self.a.query.get(),'Buff Bot');self.assertEqual(self.a.mods.get_children(),('buff-bot',))
 def test_view_sort_does_not_change_plan(self):
  self.sample();j=self.a.model.job(self.a.game_id,self.a.job_id);before=j.plan.copy();self.a.sort_rows('name');self.assertEqual(j.plan,before)
 def test_sample_menu_requires_consent(self):
  with patch('GameToolWorkbench.messagebox.askyesno',return_value=False):self.a.samples()
  self.assertEqual(self.a.model.jobs(),[])
 def test_sample_menu_prepares_and_switches_to_alpha(self):
  with patch('GameToolWorkbench.messagebox.askyesno',return_value=True):self.a.samples()
  self.root.update();self.assertEqual(self.a.game_id,'workflow-sample-alpha');self.assertEqual(self.a.mod_rows['sample-content']['label'],'Prepared')
 def test_prepare_button_performs_real_owned_file_preparation(self):
  self.sample();self.a.mods.selection_set('sample-content');self.a.mod_selected();self.a.primary.invoke();self.drain()
  self.assertEqual(self.a.mod_rows['sample-content']['label'],'Prepared');self.assertFalse(self.a.model.context()['sections']['capabilities']['installed_game_control'])
 def test_switch_during_task_does_not_redirect_result(self):
  self.sample();g=self.a.game_id;release=threading.Event()
  self.a.start('Scope test',lambda cancel:(release.wait(2) or True) and {'new_job':self.a.model.new_plan(g).path.name,'status':'PLANNED'})
  self.a.load_game('pathfinder-kingmaker');release.set();self.drain()
  self.assertEqual(self.a.game_id,'pathfinder-kingmaker');self.assertIsNone(self.a.job_id);self.assertEqual(len(self.a.model.jobs(g)),2)
 def test_busy_game_does_not_disable_other_game_actions(self):
  self.sample();release=threading.Event();self.a.start('Wait',lambda c:release.wait(2) and {'status':'PLANNED'})
  self.a.load_game('pathfinder-kingmaker');self.root.update();self.assertFalse(self.a.primary.instate(['disabled']));release.set();self.drain()
 def test_local_test_proposal_needs_exact_approval(self):
  self.sample();before=self.a.model.jobs(self.a.game_id);self.a.test_request();self.root.update()
  self.assertIsNotNone(self.a.last_review);self.assertEqual(self.a.last_review['status'],'AWAITING_LOCAL_APPROVAL');self.assertEqual(self.a.model.jobs(self.a.game_id),before)
  with patch('GameToolWorkbench.messagebox.askyesno',return_value=False):self.a.approve_request()
  self.assertEqual(self.a.model.jobs(self.a.game_id),before)
 def test_local_approval_runs_without_simulating_client_connection(self):
  self.sample();self.a.test_request();self.root.update();review=self.a.last_review.copy()
  with patch('GameToolWorkbench.messagebox.askyesno',return_value=True):self.a.approve_request()
  self.drain();self.assertEqual(len(self.a.model.jobs(self.a.game_id)),2)
  self.assertEqual(self.a.model.service(self.a.game_id).request_status(review['request_id'])['status'],'COMPLETED')
  self.assertEqual(self.a.job_id,self.a.model.service(self.a.game_id).request_status(review['request_id'])['result']['result']['job_id'])
 def test_reject_does_not_create_plan(self):
  self.sample();self.a.test_request();self.root.update();self.a.reject_request();self.assertEqual(len(self.a.model.jobs(self.a.game_id)),1)
 def test_manual_results_shown_as_reported(self):
  self.sample();gid,jid,rev=self.a.capture_job();self.a.model.record_check(gid,jid,rev,'sample-content','feature_works','passed','Local note')
  self.a.refresh_checks();self.assertEqual(self.a.checks_tree.item('0','values')[2],'Reported pass');self.assertEqual(self.a.mod_rows['sample-content']['label'],'Downloaded')
 def test_copy_context_excludes_local_notes_and_paths(self):
  self.sample();g,j,r=self.a.capture_job();self.a.model.record_check(g,j,r,'sample-content','feature_works','failed','SECRET-LOCAL-PATH')
  self.a.copy_context();txt=self.root.clipboard_get();self.assertNotIn('SECRET-LOCAL-PATH',txt);self.assertNotIn(str(self.data),txt);self.assertIn(self.a.game_id,txt)
 def test_game_choice_does_not_enable_watch(self):
  self.a.load_game('cyberpunk-2077');self.a.load_game('pathfinder-kingmaker');self.assertFalse(self.a.watch.get())
 def test_dark_light_and_density_leave_draft_unchanged(self):
  before=self.a.view.value['games'][self.a.game_id]['selected'].copy();self.a.theme.set('Light');self.a.density.set('Comfortable');self.a.change_view();self.root.update()
  self.assertEqual(before,self.a.view.value['games'][self.a.game_id]['selected']);self.assertEqual(self.a.theme.get(),'Light')
 def test_zoom_and_narrow_actions_remain_visible(self):
  for width,zoom in [(1240,80),(1240,100),(980,120),(740,150),(840,200)]:
   with self.subTest(width=width,zoom=zoom):
    self.a.zoom.set(zoom);self.a.change_view();self.root.geometry(f'{width}x1000');self.root.update()
    self.assertGreater(self.a.main.winfo_width(),500);self.assertTrue(self.a.primary.winfo_ismapped());self.assertGreater(self.a.mods.winfo_height(),70)
    self.assertLessEqual(self.a.primary.winfo_rootx()+self.a.primary.winfo_width(),self.root.winfo_rootx()+self.root.winfo_width()+1)
    if str(self.a.details_frame) not in self.a.shell.panes():self.assertTrue(self.a.inspect_button.winfo_ismapped())
 def test_all_header_controls_accessible_at_narrow_200_percent(self):
  for width,zoom in [(1240,80),(1240,100),(980,120),(740,150),(840,200)]:
   with self.subTest(width=width,zoom=zoom):
    self.a.zoom.set(zoom);self.a.change_view();self.root.geometry(f'{width}x1000');self.root.update()
    buttons=[self.a.samples_button,self.a.copy_button,self.a.view_button,self.a.more_button]
    if str(self.a.rail) not in self.a.shell.panes():buttons.append(self.a.games_button)
    bounds=[]
    for button in buttons:
     self.assertTrue(button.winfo_ismapped(),button['text'])
     left=button.winfo_rootx();top=button.winfo_rooty();right=left+button.winfo_width();bottom=top+button.winfo_height()
     self.assertGreaterEqual(left,self.root.winfo_rootx())
     self.assertLessEqual(right,self.root.winfo_rootx()+self.root.winfo_width())
     self.assertLessEqual(bottom,self.a.header.winfo_rooty()+self.a.header.winfo_height())
     for x,y,r,b in bounds:self.assertFalse(left<r and right>x and top<b and bottom>y)
     bounds.append((left,top,right,bottom))
  # Conditional visibility must not destroy More or leave sample-only dead space.
  self.sample();self.root.update();self.assertFalse(self.a.samples_button.winfo_ismapped())
  self.assertTrue(self.a.more_button.winfo_ismapped())
 def test_modal_shortcuts_do_not_steal_focus(self):
  win=tk.Toplevel(self.root);entry=tk.Entry(win);entry.pack();self.root.update();win.grab_set();old=self.a.zoom.get()
  self.a.zoom_key(None,10);self.assertEqual(self.a.zoom.get(),old);win.grab_release();win.destroy()
 def test_zero_value_not_rendered_unknown(self):
  self.a.detail_text('Count',[('Files',0)]);self.assertIn('0',self.a.detail.get('1.0','end'));self.assertNotIn('Unknown',self.a.detail.get('1.0','end'))

if __name__=='__main__':unittest.main(verbosity=2)
