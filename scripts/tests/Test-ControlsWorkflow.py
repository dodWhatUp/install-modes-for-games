"""Real existing adapters/rollback and SourceLibrary using private temp fixtures."""
import copy,hashlib,importlib.util,json,pathlib,sys,tempfile,unittest,uuid
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import GameToolControlsPlanner as p
import GameToolControlsWorkflow as flow
import GameToolKeymapBuilder as builder
import GameToolKeymapDocument as maps
import GameToolOverlay as overlay
from game_keybind_ops.core import Service
from game_keybind_ops.documents import Document
from game_keybind_ops.authoring import planner_bridge

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
fixture=load('planner_fixture',ROOT/'tests/Test-ControlsPlanner.py')
idtech=load('idtech_fixture',ROOT/'tests/keybinds/test_idtech_bindset.py')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=pathlib.Path(self.temp.name)
        self.config=self.root/'fixture.cfg';self.config.write_bytes(idtech.RAW)
        self.service=Service(self.root/'data',process_reader=lambda:set())
        self.service.register_local(idtech.spec(self.root,Document(idtech.RAW,'idtech-bindset')))
        self.doc=fixture.document();self.doc['game_id']='synthetic-doom'
        for m in self.doc['maps']:
            for c in m['cells']:c.update(output='UNASSIGNED',action='',display_action='')
        def cell(bid,key,label):next(c for c in self.doc['maps'][0]['cells'] if c['button_id']==bid).update(output=key,action=label)
        cell(6,'R','Shield / Spear');cell(11,'H','Hint');cell(7,'U','')
        manifest,_=fixture.f.fixtures.fixture(self.root)
        manifest['games'][0]['id']='synthetic-doom'
        for group in manifest['groups']:group['game_id']='synthetic-doom'
        for association in manifest['associations']:association['game_id']='synthetic-doom'
        self.keymap=manifest['keymaps'][0];self.keymap['revision']=self.doc['keymap_revision']
        self.keymap['layers'][1]['id']='WEAPONS';self.keymap['blank_masks']['WEAPONS']=self.keymap['blank_masks'].pop('MENUS')
        self.profiles=self.root/'native'
        for layer in self.keymap['layers']:
            identity=str(uuid.uuid4());layer['profile_id']=identity;raw=b'{"fixture": 1}'
            path=self.profiles/'device/ProfileStorage'/('profile_'+identity+'.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            layer['profile_sha256']=hashlib.sha256(raw).hexdigest()
        for asset in manifest['assets']:asset['profile_id']=self.keymap['layers'][0]['profile_id']
        self.library=builder.SourceLibrary(self.root/'data');path=self.root/'manifest.json';path.write_bytes(overlay.encode(manifest))
        self.library.store.import_manifest(path,'absent');self.saved=self.library.save_source(self.doc,self.keymap,'absent')
        self.w=p.attach_source(p.new_workbook(self.doc),p.source_snapshot(self.service,'target','fixture-idtech','synthetic-doom'))
        for a in self.w['actions']:
            if a['context']=='bindset:0':a['overlay_context']='gameplay'
            if a['label'] in ('_shield','_spear'):a['proposed_route']='BASIC/gameplay/7'
        self.workflow=flow.Workflow(self.library,self.service,self.profiles)

    def test_stable_id_bridge_never_falls_back_to_duplicate_label(self):
        row={'source_id':'one','source_action':'Translated','action':'native-use','context':'gameplay','slot':'primary','keys':{'K':'K'}}
        result=planner_bridge({'assignments':[{'source_id':'one','label':'Changed translation','target_key':'K'}]},[row])
        self.assertEqual(result['intents'][0]['action'],'native-use')
        bad=planner_bridge({'assignments':[{'source_id':'wrong','label':'Translated','target_key':'K'}]},[row])
        self.assertTrue(bad['unresolved'])

    def test_full_review_apply_candidate_save_publish_and_exact_rollback(self):
        before=self.config.read_bytes();_,registry=self.library.store.load()
        review=self.workflow.review(self.w,self.doc,self.keymap)
        self.assertEqual(len(review['game']['items'][0]['diff']),2)
        self.assertEqual(self.config.read_bytes(),before);self.assertEqual(self.library.store.load()[1],registry)
        staged=self.workflow.prepare(review,review['review_sha256'],authorize=lambda _:True)
        with self.assertRaisesRegex(ValueError,'must match'):self.workflow.publication_candidate(staged['plan_id'])
        applied=self.workflow.apply_game(staged['plan_id'],authorize=lambda _:True)
        self.assertEqual(applied['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED')
        self.assertIn(b'"U" "_shield"',self.config.read_bytes());self.assertIn(b'"U" "_spear"',self.config.read_bytes())
        candidate=self.workflow.publication_candidate(staged['plan_id'])
        self.assertEqual(maps.output_matrix(candidate),maps.output_matrix(self.doc))
        self.library.save_source(candidate,self.keymap,self.saved);self.workflow.check_publication(candidate)
        with mock.patch.object(flow,'default_profiles_root',return_value=self.profiles):self.library.publish(candidate,self.keymap,registry)
        with self.assertRaisesRegex(ValueError,'Suspend'):self.workflow.rollback_game(staged['plan_id'],authorize=lambda _:True)
        self.workflow.suspend_overlay(staged['plan_id'],authorize=lambda _:True)
        undone=self.workflow.rollback_game(staged['plan_id'],authorize=lambda _:True)
        self.assertEqual(undone['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED');self.assertEqual(self.config.read_bytes(),before)
        with self.assertRaises(ValueError):self.workflow.check_publication(candidate)
        self.assertEqual(self.workflow.original_overlay_candidate(staged['plan_id']),self.doc)

    def test_separate_authorization_and_source_drift(self):
        review=self.workflow.review(self.w,self.doc,self.keymap)
        with self.assertRaisesRegex(ValueError,'local review'):self.workflow.prepare(review,review['review_sha256'],authorize=lambda _:False)
        staged=self.workflow.prepare(review,review['review_sha256'],authorize=lambda _:True)
        with self.assertRaises(Exception):self.workflow.apply_game(staged['plan_id'],authorize=lambda _:False)
        self.assertEqual(self.config.read_bytes(),idtech.RAW)
        self.config.write_bytes(idtech.RAW+b'// new user change\r\n')
        with self.assertRaises(Exception):self.workflow.apply_game(staged['plan_id'],authorize=lambda _:True)

    def test_native_byte_drift_blocks_apply_without_reformatting(self):
        review=self.workflow.review(self.w,self.doc,self.keymap);staged=self.workflow.prepare(review,review['review_sha256'],authorize=lambda _:True)
        path=next(self.profiles.rglob('*.json'));path.write_bytes(b'{"fixture":1}\n')
        with self.assertRaisesRegex(ValueError,'Native profile'):self.workflow.apply_game(staged['plan_id'],authorize=lambda _:True)
        self.assertEqual(self.config.read_bytes(),idtech.RAW)

    def test_unknown_alias_requires_explicit_current_evidence(self):
        next(c for c in self.doc['maps'][0]['cells'] if c['button_id']==7)['output']='User Label'
        self.w['baseline']['map_sha256']=maps.fingerprint(self.doc)
        report=flow.binding_preview(self.w,self.doc,self.service);self.assertEqual(report['status'],'UNRESOLVED_ACTIONS')
        self.w['extensions']['key_aliases']=[{'display':'User Label','native':'U','evidence':'Explicit synthetic alias','source_revision':self.w['sources'][0]['revision']}]
        self.assertEqual(flow.binding_preview(self.w,self.doc,self.service)['status'],'PREVIEW_NOT_INSTALLED')

    def test_bundle_partial_move_refused(self):
        next(a for a in self.w['actions'] if a['label']=='_spear')['proposed_route']=None
        with self.assertRaisesRegex(ValueError,'blocked'):flow.binding_preview(self.w,self.doc,self.service)

    def test_prepared_record_cannot_remove_game_plan_to_bypass_publication(self):
        review=self.workflow.review(self.w,self.doc,self.keymap);record=self.workflow.prepare(review,review['review_sha256'],authorize=lambda _:True)
        path=self.workflow.root/(record['plan_id']+'.json');value=json.loads(path.read_text());value['game_plan']=None;path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError,'removed or added'):self.workflow.publication_candidate(record['plan_id'])

    def test_unapplied_exported_map_cannot_publish_through_existing_owner(self):
        candidate=p.overlay_candidate(self.w,self.doc);self.library.save_source(candidate,self.keymap,self.saved);_,sha=self.library.store.load()
        with self.assertRaisesRegex(ValueError,'preview-only'):self.library.publish(candidate,self.keymap,sha)

    def test_duplicate_translations_are_unambiguous_when_stable_ids_differ(self):
        rows=[{'source_id':ident,'source_action':'Same label','action':'native-'+ident,'context':'gameplay','slot':'primary','keys':{'K':'K'}} for ident in ('one','two')]
        result=planner_bridge({'assignments':[{'source_id':r['source_id'],'label':'Same label','target_key':'K'} for r in rows]},rows)
        self.assertEqual(len(result['intents']),2)

    def test_existing_multi_file_instance_bridge_keeps_whole_scope_dependency(self):
        sys.path.insert(0,str(ROOT/'tests/keybinds'))
        graph_module=load('graph_fixture',ROOT/'tests/keybinds/test_effective.py');graph=graph_module.GraphBase();graph.setUp()
        try:
            graph.create([('first',{'use':'E'},True,100),('second',{'reload':'F'},True,100)])
            doc=copy.deepcopy(self.doc);doc['game_id']='fictional'
            workbook=p.attach_source(p.new_workbook(doc),p.source_snapshot(graph.s,'instance','installation','fictional'))
            for action in workbook['actions']:
                action['overlay_context']='gameplay'
                if action['label']=='use':action['proposed_route']='BASIC/gameplay/6'
            result=flow.binding_preview(workbook,doc,graph.s)
            self.assertEqual(result['status'],'PREVIEW_NOT_INSTALLED')
            self.assertEqual(len(result['items'][0]['scope_guard']['dependencies']),2)
        finally:graph.tearDown();graph.doCleanups()


if __name__=='__main__':unittest.main()
