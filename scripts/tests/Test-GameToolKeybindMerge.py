"""Conflict/integration contracts for the 0.25 A+B source merge.

Uses only temporary fictional keybind files and the shipped data recipes. No
network, installed game, native Windows, device, or gameplay operation occurs.
"""
from __future__ import annotations
import json,shutil,sys,tempfile,threading,time,unittest
from pathlib import Path
import tkinter as tk

SCRIPTS=Path(__file__).resolve().parents[1]
ROOT=SCRIPTS.parent
sys.path.insert(0,str(SCRIPTS));sys.dont_write_bytecode=True

from GameToolGameWorkspaces import (GameWorkspaces,WorkspaceAI,ScopedAutomation,
    KeybindScopedAutomation,KeybindOnlyAutomation)
from GameToolKeybindAI import Endpoint
from GameToolWorkbench import Workbench
from game_mod_ops.safety import ModError
from game_keybind_ops.core import sha
from game_keybind_ops.packs import (inspect_pack,import_pack_local,load_pin,
    bind_instance_local)
from game_keybind_ops.effective import inspect_instance,intent_preview


class MergeContracts(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.data=self.root/'private';self.w=GameWorkspaces(self.data)

    def pack(self,game_id,pack_id=None):
        dest=self.root/('pack-'+game_id);shutil.copytree(ROOT/'game-packs/format-examples/sample-json',dest)
        body=json.loads((dest/'pack.json').read_text())
        body['id']=pack_id or game_id+'-keybind-fixture';body['game_id']=game_id
        body['title']='Synthetic merge fixture for '+game_id
        (dest/'pack.json').write_text(json.dumps(body,indent=2,ensure_ascii=False)+'\n')
        report=inspect_pack(dest)
        pin=import_pack_local(self.w.keybinds,dest,report['pack_sha256'],authorize=lambda _:True)['pin']
        return dest,pin,body

    def bind(self,folder,pin,instance='merge-installation'):
        pack=load_pin(self.w.keybinds,pin);native=self.root/(instance+'-native');native.mkdir()
        bindings={};hashes={};paths={}
        for file in pack['files']:
            fixture=next(x for x in pack['fixtures'] if x['file_id']==file['id'])
            raw=(folder/fixture['before']).read_bytes();path=native/file['locations'][0]['pattern']
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            bindings[file['id']]={'root':str(native),'relative':path.relative_to(native).as_posix()}
            hashes[file['id']]=sha(raw);paths[file['id']]=path
        state=bind_instance_local(self.w.keybinds,pin,instance,pack['variants'][0]['id'],bindings,hashes,
            authorize=lambda _:True,evidence='Synthetic merge test; no real game installed.')
        return state,paths

    @staticmethod
    def ready(service,requests=True):
        endpoint=Endpoint(service,requests)
        endpoint.handle({'jsonrpc':'2.0','id':1,'method':'initialize','params':{}})
        endpoint.handle({'jsonrpc':'2.0','method':'notifications/initialized'})
        return endpoint

    def test_same_game_keeps_two_pack_identities_and_one_service(self):
        before=next(r for r in self.w.game_rows() if r['id']=='pathfinder-kingmaker')
        _,pin,_=self.pack('pathfinder-kingmaker')
        row=next(r for r in self.w.game_rows() if r['id']=='pathfinder-kingmaker')
        self.assertTrue(row['recipe_available']);self.assertTrue(row['keybind_pack_available'])
        self.assertEqual(row['support_revision'],before['support_revision'])
        self.assertEqual(row['keybind_pack_revision'],pin['sha256'])
        service=self.w.service('pathfinder-kingmaker')
        self.assertIsInstance(service,KeybindScopedAutomation)
        self.assertIs(service.keybinds,self.w.keybinds)
        self.assertEqual(service.requests,self.data/'automation'/'requests')
        self.assertTrue(service.preview_plan())

    def test_support_only_and_keybind_only_are_not_falsely_promoted(self):
        support=next(r for r in self.w.game_rows() if r['id']=='stardew-valley')
        self.assertTrue(support['recipe_available']);self.assertFalse(support['keybind_pack_available'])
        service=self.w.service('stardew-valley')
        self.assertIsInstance(service,ScopedAutomation);self.assertFalse(hasattr(service,'keybinds'))
        mode='default' if 'default' in service.recipe.get('presets',{}) else 'real-time'
        self.assertTrue(service.preview_plan(mode=mode))
        _,_,body=self.pack('sample-json','sample-json-merge')
        row=next(r for r in self.w.game_rows() if r['id']=='sample-json')
        self.assertFalse(row['recipe_available']);self.assertTrue(row['keybind_pack_available'])
        keybind=self.w.service('sample-json')
        self.assertIsInstance(keybind,KeybindOnlyAutomation);self.assertIs(keybind.keybinds,self.w.keybinds)
        with self.assertRaises(ModError) as error:keybind.preview_plan()
        self.assertEqual(error.exception.code,'MOD_RECIPE_REQUIRED')
        with self.assertRaises(ModError) as error:keybind.propose('mods.create_plan',{},request_id='forbidden-mod')
        self.assertEqual(error.exception.code,'CAPABILITY_UNAVAILABLE')
        self.assertEqual(body['game_id'],'sample-json')

    def test_one_tools_list_contains_host_support_and_keybind_families_without_duplicates(self):
        self.pack('pathfinder-kingmaker')
        ai=WorkspaceAI(self.data);endpoint=self.ready(ai)
        response=endpoint.handle({'jsonrpc':'2.0','id':2,'method':'tools/list','params':{}})
        names=[x['name'] for x in response['result']['tools']]
        self.assertEqual(len(names),len(set(names)))
        self.assertIn('hub_context',names);self.assertIn('games_support_schema',names)
        self.assertIn('keybinds_context',names);self.assertIn('keybinds_propose',names)
        self.assertFalse(any('approve' in n or 'activate' in n or 'register' in n for n in names))

    def test_capability_change_requires_reopen_instead_of_mutating_cached_service(self):
        cached=self.w.service('pathfinder-kingmaker');self.assertIsInstance(cached,ScopedAutomation)
        self.pack('pathfinder-kingmaker')
        with self.assertRaises(ModError) as error:self.w.service('pathfinder-kingmaker')
        self.assertEqual(error.exception.code,'SOURCE_CHANGED')
        reopened=GameWorkspaces(self.data).service('pathfinder-kingmaker')
        self.assertIsInstance(reopened,KeybindScopedAutomation)

    def test_same_mailbox_stages_applies_and_rolls_back_keybind_bytes(self):
        folder,pin,_=self.pack('pathfinder-kingmaker');state,paths=self.bind(folder,pin)
        service=self.w.service('pathfinder-kingmaker');before=paths['input'].read_bytes()
        view=intent_preview(self.w.keybinds,'merge-installation',[{'action':'use','context':'gameplay','key':'F'}],state['revision'])
        request=service.propose('keybinds.prepare',{'items':view['items_request'],'preview_sha256':view['preview_sha256']},request_id='merge-stage')
        staged=service.approve_local('merge-stage',request['request_sha256'])['result']
        request=service.propose('keybinds.apply',{'plan_id':staged['plan_id'],'plan_sha256':staged['plan_sha256']},request_id='merge-apply')
        applied=service.approve_local('merge-apply',request['request_sha256'])['result']
        self.assertEqual(applied['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED');self.assertNotEqual(paths['input'].read_bytes(),before)
        preview=self.w.keybinds.exact_rollback_preview(staged['plan_id'])
        request=service.propose('keybinds.prepare_rollback',{'plan_id':staged['plan_id'],'preview_sha256':preview['preview_sha256'],'selective':False},request_id='merge-undo-stage')
        undo=service.approve_local('merge-undo-stage',request['request_sha256'])['result']
        request=service.propose('keybinds.apply',{'plan_id':undo['plan_id'],'plan_sha256':undo['plan_sha256']},request_id='merge-undo-apply')
        result=service.approve_local('merge-undo-apply',request['request_sha256'])['result']
        self.assertEqual(result['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED');self.assertEqual(paths['input'].read_bytes(),before)
        self.assertTrue(str(service.requests).startswith(str(self.data/'automation')))

    def test_context_keeps_revisions_privacy_and_distinct_sections(self):
        self.pack('pathfinder-kingmaker');out=self.w.context('pathfinder-kingmaker')
        self.assertEqual(set(out['sections']),{'games','jobs','keybinds','capabilities'})
        text=json.dumps(out);self.assertNotIn(str(self.root),text);self.assertIn('support_revision',text);self.assertIn('keybind_pack_revision',text)
        again=self.w.context('pathfinder-kingmaker',out['revisions'])
        self.assertEqual(set(again['unchanged']),set(out['revisions']));self.assertEqual(again['sections'],{})


class WorkbenchMergeLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.data=Path(self.tmp.name)/'private'
        self.root=tk.Tk();self.errors=[];self.root.report_callback_exception=lambda *e:self.errors.append(str(e[1]))
        self.app=Workbench(self.root,self.data);self.root.update()
    def tearDown(self):
        self.app.keybind_panel.worker=None
        self.app.model.runner.stop();deadline=time.time()+3
        while self.app.model.runner.active() and time.time()<deadline:time.sleep(.01)
        self.app.close();self.tmp.cleanup();self.assertEqual(self.errors,[])
    def test_one_keybind_pane_reuses_workbench_model_stop_and_selection(self):
        labels=[self.app.tabs.tab(tab,'text') for tab in self.app.tabs.tabs()]
        self.assertEqual(labels.count('Keybinds'),1);self.assertIs(self.app.keybind_panel.service,self.app.model.keybinds)
        self.app.load_game('pathfinder-kingmaker');self.root.update();self.assertEqual(self.app.keybind_panel.game.get(),'pathfinder-kingmaker')
        self.app.keybind_panel.worker=object();self.app.refresh_activity();self.root.update()
        self.assertIn('keybind-pane-active',self.app.activity.get_children());self.assertEqual(str(self.app.stop_all['state']),'normal')
        self.app.stop();self.assertTrue(self.app.keybind_panel.cancel.is_set());self.app.keybind_panel.worker=None


if __name__=='__main__':unittest.main(verbosity=2)
