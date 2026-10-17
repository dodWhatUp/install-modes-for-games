"""Merger behavior against fictional files; never production settings or game input."""
import copy, importlib.util, json, os, sys, threading, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'scripts/tests')]
os.environ['GAME_TOOLS_HOST_SOURCE']=str(ROOT)
from test_extensibility import Base
from GameToolGameWorkspaces import GameWorkspaces, WorkspaceAI
from GameToolMerged import MergedEndpoint, ScopedKeybindService
from GameToolKeybindWorkspaces import KeybindOnlyAutomation
from game_keybind_ops.deps import object_hash, Error
spec=importlib.util.spec_from_file_location('support_fixtures',ROOT/'scripts/tests/Test-GameSupport.py')
support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)

class Merger(Base):
    def setUp(self):
        super().setUp()
        self.folder=self.sample()
        self.state,self.paths,self.pin=self.binding(self.folder)
        self.game_id=json.loads((self.folder/'pack.json').read_text())['game_id']
        self.w=GameWorkspaces(self.root/'state');self.w.keybinds=self.s
    def add_support(self, ident=None):
        pack=support.make_pack(ident or self.game_id)
        path=self.root/'support.json';path.write_text(json.dumps(pack))
        return self.w.catalog.import_support(path,reviewed_sha256=object_hash(pack),confirmed=True)
    def endpoint(self):
        facade=WorkspaceAI(self.root/'state');facade.workspaces=self.w
        endpoint=MergedEndpoint(facade,True)
        endpoint.handle({'jsonrpc':'2.0','id':1,'method':'initialize'})
        endpoint.handle({'jsonrpc':'2.0','method':'notifications/initialized'})
        return endpoint
    def rpc(self,name,args=None):
        return self.endpoint().handle({'jsonrpc':'2.0','id':2,'method':'tools/call',
                       'params':{'name':name,'arguments':args or {}}})['result']
    def proposal(self,ident='stage'):
        preview=self.view()
        return self.w.service(self.game_id).propose('keybinds.prepare',
            {'items':preview['items_request'],'preview_sha256':preview['preview_sha256']},request_id=ident)
    def test_shared_game_retains_both_schemas_and_support_revision(self):
        self.add_support()
        row=next(r for r in self.w.catalog.game_rows() if r['id']==self.game_id)
        self.assertTrue(row['recipe_available'] and row['keybind_pack_available'])
        self.assertTrue(row['support_revision']);self.assertTrue(row['adapter_capabilities'])
        self.assertTrue(self.w.service(self.game_id).preview_plan(mode='default'))
        self.assertTrue(self.w.keybind_context(self.game_id)['instances'])
    def test_keybind_only_has_no_fabricated_mod_recipe(self):
        service=self.w.service(self.game_id)
        self.assertIsInstance(service,KeybindOnlyAutomation)
        self.failcode('MOD_RECIPE_REQUIRED',service.preview_plan)
    def test_support_only_keeps_original_plan(self):
        self.add_support('support-only')
        row=next(r for r in self.w.catalog.game_rows() if r['id']=='support-only')
        self.assertFalse(row['keybind_pack_available'])
        self.assertTrue(self.w.service('support-only').preview_plan(mode='default'))
    def test_endpoint_contains_both_families_once(self):
        tools=self.endpoint().handle({'jsonrpc':'2.0','id':2,'method':'tools/list'})['result']['tools']
        names=[t['name'] for t in tools]
        self.assertEqual(len(names),len(set(names)))
        self.assertIn('games_support_validate',names);self.assertIn('keybinds_propose',names)
        self.assertFalse(any('approve' in n or 'execute' in n for n in names))
    def test_proposal_stages_only_after_existing_local_approval(self):
        before=self.paths['input'].read_bytes();req=self.proposal()
        self.assertEqual(self.paths['input'].read_bytes(),before)
        self.assertFalse(self.s.plans.exists())
        self.assertIn('no game',self.w.request_review(self.game_id,req['request_id'])['effect'])
        result=self.w.approve_request(self.game_id,req['request_id'],req['request_sha256'],threading.Event())
        self.assertEqual(result['status'],'COMPLETED');self.assertEqual(self.paths['input'].read_bytes(),before)
    def test_exact_apply_and_rollback_share_mailbox(self):
        before=self.paths['input'].read_bytes();req=self.proposal()
        prepared=self.w.approve_request(self.game_id,req['request_id'],req['request_sha256'],threading.Event())['result']
        host=self.w.service(self.game_id)
        req=host.propose('keybinds.apply',{'plan_id':prepared['plan_id'],'plan_sha256':prepared['plan_sha256']},request_id='apply')
        self.w.approve_request(self.game_id,req['request_id'],req['request_sha256'],threading.Event())
        self.assertNotEqual(self.paths['input'].read_bytes(),before)
        preview=self.s.exact_rollback_preview(prepared['plan_id'])
        undo=self.s.prepare_rollback(prepared['plan_id'],preview['preview_sha256'])
        req=host.propose('keybinds.apply',{'plan_id':undo['plan_id'],'plan_sha256':undo['plan_sha256']},request_id='undo')
        self.w.approve_request(self.game_id,req['request_id'],req['request_sha256'],threading.Event())
        self.assertEqual(self.paths['input'].read_bytes(),before)
    def test_cancelled_request_cannot_write_game(self):
        before=self.paths['input'].read_bytes();req=self.proposal()
        cancel=threading.Event();cancel.set()
        result=self.w.approve_request(self.game_id,req['request_id'],req['request_sha256'],cancel)
        self.assertEqual(result['status'],'STOPPED_RECONCILE');self.assertEqual(self.paths['input'].read_bytes(),before)
    def test_self_approval_and_missing_game_are_refused(self):
        r=self.rpc('keybinds_propose',{'operation':'keybinds.prepare','arguments':{'approved':True},'request_id':'no'})
        self.assertTrue(r['isError'])
    def test_wrong_game_cannot_read_native_target(self):
        target=self.view()['items_request'][0]['target_id']
        r=self.rpc('keybinds_context',{'game_id':'pathfinder-kingmaker','target_id':target})
        self.assertTrue(r['isError'])
    def test_scoped_panel_context_and_history(self):
        scoped=ScopedKeybindService(self.s,lambda:self.game_id)
        value=scoped.context();self.assertEqual(value['game_id'],self.game_id)
        self.assertNotIn(str(self.root),json.dumps(value))
        self.assertTrue(scoped.context(value['revision'])['unchanged'])
    def test_source_change_rejects_pending_request(self):
        self.add_support();req=self.proposal()
        pack=support.make_pack(self.game_id);pack['definition']['name']='Updated metadata'
        old=self.w.catalog.support.get(self.game_id)['revision']
        recipe=self.w.catalog.recipes()[self.game_id]['revision']
        path=self.root/'new-support.json';path.write_text(json.dumps(pack))
        self.w.catalog.import_support(path,reviewed_sha256=object_hash(pack),expected_revision=old,
                                      expected_recipe_revision=recipe,confirmed=True)
        # The derived recipe includes reviewed game metadata; stale requests stay blocked.
        self.assertFalse(self.w.request_review(self.game_id,req['request_id'])['current'])
        self.assertTrue(self.w.request_review(self.game_id,req['request_id'])['blocking_reason'])
    def test_ui_has_one_game_owner_and_stops_keybind_worker(self):
        import tkinter as tk
        from GameToolWorkbench import Workbench
        root=tk.Tk();root.withdraw()
        try:
            app=Workbench(root,self.root/'state')
            self.assertIn('Keybinds',[app.tabs.tab(t,'text') for t in app.tabs.tabs()])
            app.load_game(self.game_id);self.assertEqual(app.keybind_panel.game.get(),self.game_id)
            self.assertEqual(str(app.keybind_panel.game_box.cget('state')),'disabled')
            app.keybind_panel.worker=object()
            app.keybind_panel.operation_game=self.game_id
            current=app.game_id;app.load_game('pathfinder-kingmaker');self.assertEqual(app.game_id,current)
            app.stop();self.assertTrue(app.keybind_panel.cancel.is_set())
            app.keybind_panel.worker=None
            self.assertTrue(app.close())
        finally:
            try:root.destroy()
            except tk.TclError:pass

if __name__=='__main__':unittest.main(verbosity=2)
