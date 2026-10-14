"""Tests actual inherited Workbench controllers and opt-in keybind endpoint; no live client."""
from __future__ import annotations
import copy,json,os,sys,threading,unittest
from pathlib import Path
HOST=os.environ.get('GAME_TOOLS_HOST_SOURCE')
if not HOST:raise SystemExit('Set GAME_TOOLS_HOST_SOURCE to the verified current Workbench source.')
SCRIPTS=Path(__file__).absolute().parents[2];sys.path.insert(0,str(Path(HOST)/'scripts'));sys.path.insert(0,str(SCRIPTS))
from test_extensibility import Base
from GameToolKeybindWorkspaces import KeybindGameWorkspaces,KeybindOnlyAutomation
from GameToolKeybindIntegration import KeybindAutomationService,OPERATIONS
from GameToolKeybindAI import Endpoint
from game_keybind_ops.effective import inspect_instance,intent_preview
from game_keybind_ops.authoring import scaffold
from game_keybind_ops.core import Service
from game_keybind_ops.deps import Error

class Integration(Base):
    def setUp(self):
        super().setUp();self.folder=self.sample();self.state,self.paths,self.pin=self.binding(self.folder)
        self.w=KeybindGameWorkspaces(self.root/'state');self.game_id=json.loads((self.folder/'pack.json').read_text())['game_id'];self.host=self.w.service(self.game_id)
        self.host.keybinds=self.s
    def ready(self):
        e=Endpoint(self.host,True);e.handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{}});e.handle({'jsonrpc':'2.0','method':'notifications/initialized'});return e
    def rpc(self,e,name,args=None):return e.handle({'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':name,'arguments':args or {}}})
    def propose_stage(self):
        v=self.view();return self.host.propose('keybinds.prepare',{'items':v['items_request'],'preview_sha256':v['preview_sha256']},request_id='semantic-change')
    def test_keybind_only_without_mod_recipe(self):
        self.assertIsInstance(self.host,KeybindOnlyAutomation);self.assertNotIn(self.game_id,self.w.catalog.recipes());self.assertTrue(next(r['keybind_pack_available'] for r in self.w.game_rows() if r['id']==self.game_id))
    def test_no_fake_mod_recipe_or_executor(self):
        self.failcode('MOD_RECIPE_REQUIRED',lambda:self.host.preview_plan());self.failcode('CAPABILITY_UNAVAILABLE',lambda:self.host.propose('mods.create_plan',{},request_id='no'))
    def test_shared_workbench_approval_controller(self):
        r=self.propose_stage();self.assertEqual(r['status'],'AWAITING_LOCAL_APPROVAL');self.assertEqual(self.host.requests,self.root/'state/automation/game-scopes'/self.game_id/'requests')
        self.assertEqual(self.w.approve_request(self.game_id,r['request_id'],r['request_sha256'],threading.Event())['status'],'COMPLETED')
    def test_workbench_review_has_correct_effect_and_game(self):
        p=self.propose_stage();r=self.w.request_review(self.game_id,p['request_id']);self.assertEqual(r['game_id'],self.game_id);self.assertIn('no game',r['effect']);self.assertTrue(r['manual_approval_required'])
    def test_approved_draft_not_imported_or_activated(self):
        draft=self.root/'draft';scaffold(draft,self.game_id,'My game');p=json.loads((draft/'pack.json').read_text());p['evidence']['stage']='source-reviewed'
        req=self.host.propose('keybinds.draft_pack',{'pack':p},request_id='draft');self.assertFalse((self.s.root/'authoring').exists())
        r=self.host.approve_local('draft',req['request_sha256']);self.assertEqual(r['status'],'COMPLETED');d=r['result'];self.assertFalse(d['activated']);saved=json.loads((self.s.root/'authoring'/d['draft_id']/'pack.json').read_text());self.assertEqual(saved['evidence']['stage'],'draft')
    def test_draft_wrong_game_refused(self):
        p=json.loads((self.folder/'pack.json').read_text());p['game_id']='other';self.failcode('GAME_MISMATCH',lambda:self.host.propose('keybinds.draft_pack',{'pack':p}))
    def test_draft_self_approval_refused(self):
        p=json.loads((self.folder/'pack.json').read_text());self.failcode('INVALID_ARGUMENTS',lambda:self.host.propose('keybinds.draft_pack',{'pack':p,'approved':True}))
    def test_ai_has_no_import_activate_approve_tool(self):
        e=self.ready();r=e.handle({'jsonrpc':'2.0','id':3,'method':'tools/list'});names=[t['name'] for t in r['result']['tools']]
        self.assertTrue(all(n.startswith('keybinds_') for n in names));self.assertIn('keybinds_intent_preview',names);self.assertFalse(any('approve' in n or 'activate' in n or 'import' in n for n in names))
    def test_ai_context_path_free(self):
        r=self.rpc(self.ready(),'keybinds_instance_context',{'instance_id':'installation'})['result']['structuredContent'];self.assertNotIn(str(self.root),json.dumps(r));self.assertEqual(r['game_id'],self.game_id)
    def test_ai_delta_and_pagination(self):
        e=self.ready();r=self.rpc(e,'keybinds_instance_context',{'instance_id':'installation','limit':1})['result']['structuredContent'];self.assertEqual(len(r['effective_bindings']),1)
        d=self.rpc(e,'keybinds_instance_context',{'instance_id':'installation','known_revision':r['revision']})['result']['structuredContent'];self.assertTrue(d['unchanged'])
    def test_ai_semantic_preview_no_native_write(self):
        before=self.paths['input'].read_bytes();r=self.rpc(self.ready(),'keybinds_intent_preview',{'instance_id':'installation','revision':self.state['revision'],'changes':[{'action':'use','context':'gameplay','key':'F'}]})['result'];self.assertFalse(r['isError']);self.assertEqual(self.paths['input'].read_bytes(),before)
    def test_original_tool_not_routed_from_keybind_only(self):
        r=self.rpc(self.ready(),'mods_create_plan');self.assertIn('error',r)
    def test_other_game_legacy_context_rejected(self):
        self.host.game_id='another';r=self.rpc(self.ready(),'keybinds_context',{'target_id':'installation-input'})['result'];self.assertTrue(r['isError']);self.assertEqual(r['structuredContent']['status'],'GAME_MISMATCH')
    def test_other_game_instance_rejected(self):
        self.host.game_id='another';r=self.rpc(self.ready(),'keybinds_instance_context',{'instance_id':'installation'})['result'];self.assertTrue(r['isError']);self.assertEqual(r['structuredContent']['status'],'GAME_MISMATCH')
    def test_other_game_proposal_rejected(self):
        self.host.game_id='another';self.failcode('GAME_MISMATCH',self.propose_stage)
    def test_global_legacy_context_requires_scope_target(self):
        r=self.rpc(self.ready(),'keybinds_context')['result'];self.assertEqual(r['structuredContent']['status'],'TARGET_REQUIRED')
    def test_keybind_only_capabilities_do_not_offer_mods(self):
        r=self.rpc(self.ready(),'keybinds_capabilities')['result']['structuredContent'];self.assertEqual(set(r['requestable']),set(OPERATIONS))
    def test_existing_mod_workspace_preserved(self):
        original=self.w.service('pathfinder-kingmaker');self.assertFalse(getattr(original,'keybind_only',False));self.assertTrue(original.preview_plan())
    def test_unregistered_game_has_no_executor(self):self.failcode('PACK_REQUIRED',lambda:self.w.service('not-registered'))
    def test_workbench_context_delta(self):
        r=self.w.keybind_context();self.assertTrue(self.w.keybind_context(known_revision=r['revision'])['unchanged'])


class DraftDeltas(Integration):
    # Explicit test loader below keeps parent tests from being counted a second time.
    def seed(self):
        path=self.root/'draft-seed';scaffold(path,self.game_id,'Draft');p=json.loads((path/'pack.json').read_text())
        req=self.host.propose('keybinds.draft_pack',{'pack':p},request_id='base-draft');return self.host.approve_local('base-draft',req['request_sha256'])['result']
    def args(self,base):return {'draft_id':base['draft_id'],'draft_sha256':base['pack_sha256'],'edits':[{'op':'replace','path':'/title','value':'Reviewed draft title'}]}
    def test_delta_preserves_parent(self):
        base=self.seed();before=(self.s.root/'authoring'/base['draft_id']/'pack.json').read_bytes();req=self.host.propose('keybinds.edit_draft',self.args(base),request_id='child')
        r=self.host.approve_local('child',req['request_sha256'])['result'];self.assertNotEqual(r['draft_id'],base['draft_id']);self.assertEqual((self.s.root/'authoring'/base['draft_id']/'pack.json').read_bytes(),before);self.assertTrue((self.s.root/'authoring'/r['draft_id']/'PARENT.json').exists())
    def test_delta_stale_base_refused(self):
        base=self.seed();a=self.args(base);a['draft_sha256']='0'*64;self.failcode('DRAFT_STALE',lambda:self.host.propose('keybinds.edit_draft',a))
    def test_delta_identity_fixed(self):
        a=self.args(self.seed());a['edits'][0]['path']='/game_id';self.failcode('DRAFT_IDENTITY',lambda:self.host.propose('keybinds.edit_draft',a))
    def test_delta_unknown_command_refused(self):
        a=self.args(self.seed());a['edits']=[{'op':'execute','path':'/title','value':'no'}];self.failcode('DRAFT_EDIT',lambda:self.host.propose('keybinds.edit_draft',a))
    def test_delta_add_fields_incrementally(self):
        base=self.seed();a=self.args(base);a['edits']=[{'op':'add','path':'/files/0/fields/-','value':{'id':'use','action':'use','contexts':['gameplay'],'keymap':'keyboard','selector':{'pointer':'/use'}}}]
        req=self.host.propose('keybinds.edit_draft',a,request_id='add-field');result=self.host.approve_local('add-field',req['request_sha256'])['result'];e=self.ready()
        r=self.rpc(e,'keybinds_draft_context',{'draft_id':result['draft_id'],'section':'fields','file_id':'input','limit':1})['result']['structuredContent'];self.assertEqual(r['items'][0]['id'],'use');self.assertFalse(r['activated'])
    def test_delta_does_not_self_promote(self):
        a=self.args(self.seed());a['edits']=[{'op':'replace','path':'/evidence/stage','value':'source-reviewed'},{'op':'replace','path':'/title','value':'Still a draft'}]
        req=self.host.propose('keybinds.edit_draft',a,request_id='promotion');r=self.host.approve_local('promotion',req['request_sha256'])['result'];p=json.loads((self.s.root/'authoring'/r['draft_id']/'pack.json').read_text());self.assertEqual(p['evidence']['stage'],'draft')
    def test_delta_can_be_read_without_native_paths(self):
        base=self.seed();r=self.rpc(self.ready(),'keybinds_draft_context',{'draft_id':base['draft_id']})['result']['structuredContent'];self.assertNotIn(str(self.root),json.dumps(r));self.assertEqual(r['stage'],'draft')

def load_tests(loader,tests,pattern):
    suite=unittest.TestSuite(loader.loadTestsFromTestCase(Integration))
    suite.addTests(DraftDeltas(name) for name in DraftDeltas.__dict__ if name.startswith('test_'))
    return suite

if __name__=='__main__':unittest.main(verbosity=2)
