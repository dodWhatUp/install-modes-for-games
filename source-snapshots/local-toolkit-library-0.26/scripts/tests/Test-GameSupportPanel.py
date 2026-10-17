"""Headless interaction tests for new extension controls, with temporary fixtures.
No screenshots, network, native manager, cloud AI or real game use.
"""
from __future__ import annotations
import importlib.util,json,sys,tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
from GameToolWorkbench import Workbench
from game_mod_ops.support import scaffold,object_hash,read_pack
from game_mod_ops.safety import digest
from GameToolAI import Endpoint
from GameToolGameWorkspaces import WorkspaceAI
spec=importlib.util.spec_from_file_location('support_test_fixtures',Path(__file__).with_name('Test-GameSupport.py'))
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)

class Panels(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.base=Path(self.tmp.name);self.data=self.base/'private';self.root=tk.Tk();self.errors=[]
  self.root.report_callback_exception=lambda *e:self.errors.append(str(e[1]));self.a=Workbench(self.root,self.data);self.root.update()
 def tearDown(self):
  self.a.model.runner.stop();deadline=time.time()+3
  while self.a.model.runner.active() and time.time()<deadline:self.root.update();time.sleep(.01)
  self.a.close();self.tmp.cleanup();self.assertEqual(self.errors,[])
 def save(self,p):
  out=self.base/'game-support.json';out.write_text(json.dumps(p));return out
 def import_(self,p,accept=True):
  out=self.save(p)
  with patch('GameToolWorkbench.filedialog.askopenfilename',return_value=str(out)),patch('GameToolWorkbench.messagebox.askyesno',return_value=accept):
   self.a.import_recipe();self.root.update()
  return out
 def drain(self):
  end=time.time()+3
  while self.a.model.runner.active() and time.time()<end:self.root.update();time.sleep(.01)
  self.root.after(220,self.root.quit);self.root.mainloop();self.root.update()
 def widgets(self,root):
  out=[]
  for w in root.winfo_children():out.append(w);out.extend(self.widgets(w))
  return out
 def test_stardew_noncombat_preset_and_dependency_plan(self):
  self.a.load_game('stardew-valley');self.root.update();self.assertEqual(self.a.mode.get(),'default')
  self.a.use_preset();self.a.primary.invoke();self.drain()
  self.assertIsNotNone(self.a.job_id);j=self.a.model.job('stardew-valley',self.a.job_id);self.assertEqual(list(j.items),['smapi','content-patcher'])
 def test_unknown_game_import_populates_normal_ui(self):
  p=fixtures.make_pack('added-game');self.import_(p)
  self.assertEqual(self.a.game_id,'added-game');self.assertEqual(self.a.mode.get(),'default');self.assertIn('test-mod',self.a.mods.get_children())
 def test_cancel_import_keeps_previous_selection_and_registry(self):
  before=self.a.game_id;self.import_(fixtures.make_pack('not-added'),False)
  self.assertEqual(self.a.game_id,before);self.assertNotIn('not-added',self.a.model.catalog.support.rows())
 def test_metadata_only_pack_has_inspection_without_fake_recipe(self):
  p=scaffold('meta-game','Meta game','directory');self.import_(p)
  self.assertIsNone(self.a.recipe);self.assertEqual(self.a.primary['text'],'Import recipe')
  self.assertIn('meta-game',self.a.model.catalog.support.rows())
 def test_copy_extension_brief_uses_same_contract_no_machine_path(self):
  self.a.load_game('stardew-valley');self.a.copy_extension_brief();raw=self.root.clipboard_get();obj=json.loads(raw)
  self.assertEqual(obj['current_pack']['definition']['game_id'],'stardew-valley');self.assertIn('contract',obj);self.assertNotIn(str(self.data),raw)
 def test_copy_context_metadata_game_is_available(self):
  self.a.load_game('valheim');self.a.copy_context();out=json.loads(self.root.clipboard_get())
  self.assertEqual(out['sections']['games'][0]['game_id'],'valheim');self.assertFalse(out['sections']['games'][0]['recipe_available'])
 def test_export_registered_support_file(self):
  self.a.load_game('stardew-valley');out=self.base/'export.json'
  with patch('GameToolWorkbench.filedialog.asksaveasfilename',return_value=str(out)):self.a.export_support()
  self.assertEqual(read_pack(out)[0]['definition']['game_id'],'stardew-valley')
 def test_import_updates_pack_not_existing_job(self):
  p=fixtures.make_pack('added-game');self.import_(p);j=self.a.model.new_plan('added-game');old=digest(j.path/'plan.json')
  p['notes']=['version change'];p['pack_version']='0.2.0';self.import_(p)
  self.assertEqual(old,digest(j.path/'plan.json'));self.assertEqual(self.a.model.catalog.support.get('added-game')['pack']['pack_version'],'0.2.0')
 def test_inspect_metadata_only_game_uses_registered_layout(self):
  p=scaffold('inspect-game','Inspect game','directory','bin/Target.exe');self.import_(p)
  g=self.base/'fake-game';(g/'bin').mkdir(parents=True);(g/'bin/Target.exe').write_text('not executable')
  (g/'Mods').mkdir();(g/'Mods/hello.txt').write_text('content')
  with patch('GameToolWorkbench.filedialog.askdirectory',return_value=str(g)):self.a.inspect_installed()
  self.drain();records=list((self.data/'mod-workflows/support-inspections/inspect-game').glob('*.json'))
  self.assertEqual(len(records),1);r=json.loads(records[0].read_text());self.assertEqual(r['result']['mods'][0]['relative_file'],'hello.txt')
 def test_import_while_worker_active_is_refused(self):
  release=threading.Event();self.a.start('hold',lambda e:(release.wait(2),{'status':'PLANNED'})[1])
  with patch('GameToolWorkbench.filedialog.askopenfilename',side_effect=AssertionError('picker must not open')):self.a.import_recipe()
  self.assertIn('Finish',self.a.status.get());release.set();self.drain()
 def test_manual_handoff_cancel_is_nonmutating(self):
  self.a.model.create_samples_local(confirmed=True);self.a.load_game('workflow-sample-beta');self.root.update()
  out=self.base/'exports';out.mkdir()
  with patch('GameToolWorkbench.filedialog.askdirectory',return_value=str(out)),patch('GameToolWorkbench.messagebox.askyesno',return_value=False):self.a.manager_handoff()
  self.assertEqual(list(out.iterdir()),[])
 def test_manual_handoff_writes_private_originals_once(self):
  r=self.a.model.create_samples_local(confirmed=True);g='workflow-sample-beta';j=self.a.model.jobs(g)[0];self.a.view.value['games'][g]={'job_id':j['job_id']};self.a.load_game(g)
  out=self.base/'exports';out.mkdir()
  with patch('GameToolWorkbench.filedialog.askdirectory',return_value=str(out)),patch('GameToolWorkbench.messagebox.askyesno',return_value=True):self.a.manager_handoff()
  self.drain();folder=next(out.iterdir());self.assertTrue((folder/'VERIFIED.json').is_file());self.assertEqual(json.loads((folder/'MANAGER-HANDOFF.json').read_text())['installed'],False)
 def test_template_dialog_save_without_commands(self):
  self.a.create_support_template();self.root.update();win=next(w for w in self.root.winfo_children() if isinstance(w,tk.Toplevel))
  entries=[w for w in self.widgets(win) if isinstance(w,ttk.Entry) and not isinstance(w,ttk.Combobox)]
  self.assertEqual(len(entries),3)
  for w,v in zip(entries,['Custom Game','custom-game','bin/Custom.exe']):w.delete(0,'end');w.insert(0,v)
  target=self.base/'custom.json';button=next(w for w in self.widgets(win) if isinstance(w,ttk.Button) and w['text']=='Save template')
  with patch('GameToolWorkbench.filedialog.asksaveasfilename',return_value=str(target)):button.invoke()
  self.root.update();self.assertEqual(read_pack(target)[0]['definition']['game_id'],'custom-game');self.assertNotIn('custom-game',self.a.model.catalog.support.rows())
 def test_ai_definition_does_not_send_free_text_notes(self):
  p=fixtures.make_pack('note-game');p['definition']['review_note']='PRIVATE-LOCAL-OBSERVATION';self.import_(p)
  result=Endpoint(WorkspaceAI(self.data)).call('games_support_details',{'game_id':'note-game'})
  self.assertNotIn('PRIVATE-LOCAL-OBSERVATION',json.dumps(result));self.assertNotIn('review_note',result['definition'])

if __name__=='__main__':unittest.main(verbosity=2)
