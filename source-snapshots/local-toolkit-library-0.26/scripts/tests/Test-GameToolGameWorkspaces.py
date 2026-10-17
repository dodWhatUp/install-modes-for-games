"""Isolated multi-game contracts; no network, real games, UI approvals or desktop effects."""
import copy,importlib.util,json,queue,sys,tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
from GameToolGameWorkspaces import *
from GameToolAI import Endpoint,tools

class WorkspaceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.data=Path(self.tmp.name)/'private';self.w=GameWorkspaces(self.data)
 def samples(self):return self.w.create_samples_local(confirmed=True)
 def sample(self,g='beta'):
  self.samples();gid='workflow-sample-'+g;r=self.w.jobs(gid)[0];return gid,r,self.w.job(gid,r['job_id'])
 def test_initialization_has_no_files_or_threads(self):
  self.assertFalse(self.data.exists());self.assertEqual(self.w.runner.active(),[])
 def test_catalog_does_not_claim_installed_or_missing_recipe_support(self):
  rows=self.w.catalog.game_rows();self.assertTrue(all(r['installation']=='unknown' for r in rows));self.assertEqual({r['id'] for r in rows if r['recipe_available']},{'pathfinder-kingmaker','stardew-valley'})
 def test_context_for_known_unsupported_game(self):
  out=self.w.context('cyberpunk-2077');self.assertFalse(out['sections']['games'][0]['recipe_available']);self.assertFalse(self.data.exists())
 def test_action_for_unsupported_game_blocked(self):
  with self.assertRaises(ModError):self.w.new_plan('cyberpunk-2077')
 def test_sample_requires_local_confirmation(self):
  with self.assertRaises(ModError):self.w.create_samples_local()
  self.assertFalse(self.data.exists())
 def test_sample_text_only_no_network_and_two_states(self):
  with patch('game_mod_ops.network.urllib.request.build_opener',side_effect=AssertionError('network forbidden')):
   r=self.samples()
  self.assertFalse(r['network_used']);self.assertEqual(len(r['jobs']),2)
  a=self.w.jobs('workflow-sample-alpha')[0];b=self.w.jobs('workflow-sample-beta')[0]
  self.assertEqual(self.w.item_rows('workflow-sample-alpha',a['job_id'])[0]['state'],'STAGED_NOT_INSTALLED')
  self.assertEqual(self.w.item_rows('workflow-sample-beta',b['job_id'])[0]['state'],'ACQUIRED')
 def test_samples_reuse_existing_jobs(self):
  r=self.samples();r2=self.samples();self.assertEqual([x['job_id'] for x in r['jobs']],[x['job_id'] for x in r2['jobs']]);self.assertTrue(all(x['reused'] for x in r2['jobs']))
 def test_job_game_mismatch_refused(self):
  g,r,j=self.sample()
  with self.assertRaises(ModError):self.w.job('pathfinder-kingmaker',r['job_id'])
 def test_lists_only_selected_game(self):
  self.samples();self.assertEqual(len(self.w.jobs()),2);self.assertEqual(len(self.w.jobs('workflow-sample-alpha')),1)
 def test_prepare_uses_existing_engine(self):
  g,r,j=self.sample();out=self.w.prepare(g,r['job_id'],r['revision'],['sample-content']);self.assertEqual(out['items'][0]['status'],'STAGED_NOT_INSTALLED')
 def test_stale_prepare_refused(self):
  g,r,j=self.sample();self.w.prepare(g,r['job_id'],r['revision'],['sample-content'])
  with self.assertRaises(ModError):self.w.prepare(g,r['job_id'],r['revision'],['sample-content'])
 def test_manager_is_not_staged_as_mod(self):
  j=self.w.new_plan('pathfinder-kingmaker',mode='turn-based')
  with self.assertRaises(ModError):self.w.prepare('pathfinder-kingmaker',j.path.name,self.w.revision(j),['unity-mod-manager'])
 def test_cancel_before_prepare(self):
  g,r,j=self.sample();e=threading.Event();e.set()
  with self.assertRaises(ModError):self.w.prepare(g,r['job_id'],r['revision'],['sample-content'],e)
  self.assertEqual(j.latest('sample-content')['status'],'ACQUIRED')
 def test_operator_check_does_not_promote_status(self):
  g,r,j=self.sample();before=j.events();self.w.record_check(g,r['job_id'],r['revision'],'sample-content','feature_works','passed')
  self.assertEqual(before,j.events());self.assertEqual(j.latest('sample-content')['status'],'ACQUIRED');self.assertFalse(self.w.checks(g,r['job_id'])[0]['stale'])
 def test_manual_note_not_exported(self):
  g,r,j=self.sample();secret='C:\\Users\\PrivatePerson\\secrets.txt'
  self.w.record_check(g,r['job_id'],r['revision'],'sample-content','feature_works','failed',secret)
  self.assertNotIn('PrivatePerson',json.dumps(self.w.context(g)));self.assertIn(secret,self.w.checks(g,r['job_id'])[0]['note'])
 def test_manual_check_becomes_stale_after_job_change(self):
  g,r,j=self.sample();self.w.record_check(g,r['job_id'],r['revision'],'sample-content','feature_works','passed')
  self.w.prepare(g,r['job_id'],r['revision'],['sample-content']);self.assertTrue(self.w.checks(g,r['job_id'])[0]['stale'])
 def test_tampered_manual_evidence_refused(self):
  g,r,j=self.sample();self.w.record_check(g,r['job_id'],r['revision'],'sample-content','feature_works','failed')
  p=next((j.path/'manual-checks').glob('*.json'));raw=read_json(p);raw['outcome']='passed';p.write_text(json.dumps(raw))
  with self.assertRaises(ModError):self.w.checks(g,r['job_id'])
 def test_manual_limit_no_silent_overflow(self):
  g,r,j=self.sample();folder=j.path/'manual-checks';folder.mkdir()
  for i in range(128):(folder/f'{i}.json').write_text('{}')
  with self.assertRaises(ModError):self.w.record_check(g,r['job_id'],r['revision'],'sample-content','feature_works','passed')
  self.assertEqual(len(list(folder.iterdir())),128)
 def test_installed_inspection_other_game_blocked(self):
  g,r,j=self.sample()
  with self.assertRaises(ModError):self.w.inspect_installed(g,r['job_id'],r['revision'],self.data)
 def test_recipe_import_requires_confirmation(self):
  with self.assertRaises(ModError):self.w.catalog.import_local(RECIPE)
 def test_recipe_conflict_not_overwritten(self):
  g,r,j=self.sample();p=self.data/'changed.json';old=self.w.catalog.get(g);v=copy.deepcopy(old['recipe']);v['name']='Altered';p.write_text(json.dumps(v))
  with self.assertRaises(ModError):self.w.catalog.import_local(p,confirmed=True)
  self.assertEqual(self.w.catalog.get(g)['revision'],old['revision'])
 def test_recipe_paths_and_executable_fields_refused(self):
  p=self.data/'bad.json';self.data.mkdir();v=copy.deepcopy(load_recipe(RECIPE));v['command']='run.exe';p.write_text(json.dumps(v))
  with self.assertRaises(ModError):self.w.catalog.import_local(p,confirmed=True)
 def test_request_namespaces_do_not_collide(self):
  self.samples();a=self.w.service('workflow-sample-alpha');b=self.w.service('workflow-sample-beta')
  for s in (a,b):s.propose('mods.create_plan',{'selected':['sample-content'],'mode':'real-time'},request_id='same-id')
  self.assertNotEqual(a.requests,b.requests);self.assertEqual(len(a.list_requests()),1);self.assertEqual(len(b.list_requests()),1)
 def test_propose_does_not_execute(self):
  g,r,j=self.sample();s=self.w.service(g);before=self.w.jobs(g)
  v=s.propose('mods.create_plan',{'selected':['sample-content'],'mode':'real-time'},request_id='proposal');self.assertEqual(v['status'],'AWAITING_LOCAL_APPROVAL');self.assertEqual(before,self.w.jobs(g))
 def test_local_approve_and_no_replay(self):
  g,r,j=self.sample();s=self.w.service(g);v=s.propose('mods.create_plan',{'selected':['sample-content'],'mode':'real-time'},request_id='approved')
  out=self.w.approve_request(g,'approved',v['request_sha256'],threading.Event());self.assertEqual(out['status'],'COMPLETED');self.assertEqual(len(self.w.jobs(g)),2)
  with self.assertRaises(ModError):self.w.approve_request(g,'approved',v['request_sha256'],threading.Event())
 def test_wrong_hash_approval_refused(self):
  g,r,j=self.sample();s=self.w.service(g);s.propose('mods.create_plan',{'selected':['sample-content'],'mode':'real-time'},request_id='hash-test')
  with self.assertRaises(ModError):self.w.approve_request(g,'hash-test','0'*64,threading.Event())
  self.assertEqual(len(self.w.jobs(g)),1)
 def test_expired_approval_refused(self):
  g,r,j=self.sample();s=self.w.service(g);v=s.propose('mods.create_plan',{'selected':['sample-content'],'mode':'real-time'},request_id='expired')
  with patch('GameToolAutomation.time.time',return_value=time.time()+1800):
   with self.assertRaises(ModError):self.w.approve_request(g,'expired',v['request_sha256'],threading.Event())
 def test_foreign_job_proposal_refused(self):
  g,r,j=self.sample();s=self.w.service('pathfinder-kingmaker')
  with self.assertRaises(ModError):s.propose('mods.download',{'job_id':r['job_id'],'job_revision':r['revision']},request_id='foreign')
 def test_plan_diff_not_installed_diff(self):
  g,r,j=self.sample();other=self.w.new_plan(g);v=self.w.compare_plans(g,r['job_id'],other.path.name)
  self.assertEqual(v['added'],[]);self.assertFalse(v['writes_game_files']);self.assertEqual(v['compares'],'intended_plans_not_installed_state')
 def test_context_delta_and_privacy(self):
  self.samples();c=self.w.context();d=self.w.context(known_revisions=c['revisions']);self.assertEqual(d['sections'],{});self.assertNotIn(str(self.data),json.dumps(c));self.assertNotIn('https:',json.dumps(c))
 def test_ai_schema_scoped_no_approve(self):
  defs=tools(True,True);self.assertEqual(len(defs),10)
  self.assertNotIn('approve',','.join(d['name'] for d in defs))
  for d in defs:
   if d['name'] in {'hub_propose','mods_preview_plan','hub_request_status'}:self.assertIn('game_id',d['inputSchema']['required'])
 def test_ai_read_and_propose_without_execute(self):
  self.samples();e=Endpoint(WorkspaceAI(self.data),True);g='workflow-sample-beta'
  p=e.call('mods_preview_plan',{'game_id':g});self.assertNotIn('items',p['items'][0]);self.assertFalse(p['installation_authorized'])
  r=e.call('hub_propose',{'game_id':g,'operation':'mods.create_plan','arguments':{'selected':['sample-content'],'mode':'real-time'},'request_id':'ai-test'})
  self.assertEqual(r['status'],'AWAITING_LOCAL_APPROVAL');self.assertEqual(len(self.w.jobs(g)),1)
  self.assertEqual(e.call('hub_request_status',{'game_id':g,'request_id':'ai-test'})['game_id'],g)
 def test_ai_cannot_supply_approval(self):
  self.samples();e=Endpoint(WorkspaceAI(self.data),True)
  with self.assertRaises(ModError):e.call('hub_propose',{'game_id':'workflow-sample-beta','operation':'mods.create_plan','arguments':{},'request_id':'bad','approved':True})
 def test_ai_read_only_mode_cannot_propose(self):
  e=Endpoint(WorkspaceAI(self.data))
  with self.assertRaises(ModError):e.call('hub_propose',{})
 def test_view_drafts_roundtrip_and_cas(self):
  p=self.data/'workbench-view.json';a=ViewState(p);b=ViewState(p)
  a.value['games']={'pathfinder-kingmaker':{'selected':['buff-bot'],'mode':'turn-based'},'workflow-sample-alpha':{'selected':['sample-content']}};a.save()
  self.assertEqual(ViewState(p).value,a.value);b.value['zoom']=120
  with self.assertRaises(ModError):b.save()
 def test_view_state_cannot_carry_operations(self):
  v=copy.deepcopy(ViewState.DEFAULT);v['approve']=True
  with self.assertRaises(ModError):ViewState.validate(v)

class ConcurrencyTests(unittest.TestCase):
 def setUp(self):self.r=ActivityRunner();self.release=threading.Event();self.addCleanup(self.cleanup)
 def cleanup(self):
  self.release.set();self.r.stop()
  deadline=time.time()+3
  while self.r.active() and time.time()<deadline:time.sleep(.01)
  self.assertFalse(self.r.active())
 def wait(self,cancel):self.release.wait(2);return {'status':'PLANNED'}
 def test_two_games_and_same_game_exclusion(self):
  self.r.start('game-a','Test A',self.wait);self.r.start('game-b','Test B',self.wait)
  self.assertEqual(len(self.r.active()),2)
  with self.assertRaises(ModError):self.r.start('game-a','Duplicate',self.wait)
 def test_single_transfer_does_not_block_other_local_work(self):
  self.r.start('game-a','Download placeholder',self.wait,network=True)
  self.assertFalse(self.r.can_start('game-b',True)[0]);self.assertTrue(self.r.can_start('game-b',False)[0])
  self.r.start('game-b','Local preparation placeholder',self.wait)
 def test_cancel_scope_does_not_cancel_other_game(self):
  seen={}
  def work(g):
   def run(c):self.release.wait(2);seen[g]=c.is_set();return {'status':'PLANNED'}
   return run
  self.r.start('game-a','A',work('a'));self.r.start('game-b','B',work('b'));self.r.stop('game-a');self.release.set()
  self.r.events.get(timeout=3);self.r.events.get(timeout=3);self.assertEqual(seen,{'a':True,'b':False})
 def test_failure_no_automatic_retry(self):
  calls=[]
  def fail(c):calls.append(1);raise RuntimeError('private path not disclosed')
  self.r.start('game-a','Failure',fail);out=self.r.events.get(timeout=2)
  self.assertEqual(len(calls),1);self.assertEqual(out['status'],'STOPPED_REVIEW');self.assertNotIn('private path',json.dumps(out))
 def test_scope_captured_in_completion(self):
  self.r.start('game-a','Local',self.wait,job_id='job-a');self.release.set();r=self.r.events.get(timeout=2)
  self.assertEqual((r['game_id'],r['job_id']),('game-a','job-a'))

if __name__=='__main__':unittest.main(verbosity=2)
