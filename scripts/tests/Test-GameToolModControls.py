"""Multiple disposable installations and the real shared controller/AI boundary."""
import copy,json,sys,tempfile,unittest,zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolModControls import ModControls,ini_template,validate_pack
from GameToolAI import Endpoint
from GameToolInstances import InstanceRegistry
from game_mod_ops.definitions import default_definition
from game_mod_ops.safety import ModError,object_hash

class Workspaces:
    def __init__(self):
        self.support={}
        for ident,adapter in [('fixture-one','directory'),('fixture-two','smapi')]:
            d=default_definition(ident,ident,adapter,'Fixture.exe')
            self.support[ident]={'pack':{'definition':d},'revision':object_hash(d)}
        self.catalog=SimpleNamespace(support=SimpleNamespace(rows=lambda:self.support),recipes=lambda:{})
    def game_rows(self):return [{'id':i,'name':i,'manager':'manual','recipe_available':False} for i in self.support]

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='mod-controls-');self.base=Path(self.tmp.name);self.data=self.base/'private';self.data.mkdir()
        self.workspaces=Workspaces();self.controls=ModControls(self.data,self.workspaces);self.roots={};self.initial={}
        for ident in ['fixture-one','fixture-two']:
            root=self.base/ident;root.mkdir();(root/'Fixture.exe').write_bytes(b'synthetic marker, never run')
            target=root/'Mods/Example/settings.ini';target.parent.mkdir(parents=True)
            raw=b'\xef\xbb\xbf; keep comment\r\n[General]\r\nEnabled=true\r\nAmount=2.0000\r\nUnknownSecret=do-not-share-this-text\r\n'
            target.write_bytes(raw);self.roots[ident]=root;self.initial[ident]=raw
            self.controls.register_local(ident,root,instance_id=ident)
            pack=ini_template(ident);pack['fields'].append({'id':'amount','label':'Amount','type':'number','file':'settings','section':'General','key':'Amount','min':0,'max':10})
            self.controls.connect_local(ident,pack=pack,writes_enabled=True)
    def tearDown(self):self.tmp.cleanup()
    def path(self,ident):return self.roots[ident]/'Mods/Example/settings.ini'
    def test_shared_registry_many_games_and_default_umm_guard_remains(self):
        result=self.controls.games();self.assertEqual(len(result['games']),2)
        default=InstanceRegistry(self.data,self.workspaces)
        self.assertEqual(len(default.list_public()['instances']),2)
        with self.assertRaises(ModError):default.inspect('fixture-two')
    def test_deep_inspection_is_typed_and_excludes_paths_comments_and_secrets(self):
        value=self.controls.inspect('fixture-one');text=json.dumps(value)
        self.assertEqual(value['values'],{'enabled':True,'amount':2.0});self.assertTrue(value['schema'])
        self.assertNotIn(str(self.base),text);self.assertNotIn('do-not-share',text);self.assertNotIn('UnknownSecret',text)
    def test_preview_does_not_apply(self):
        state=self.controls.inspect('fixture-one');preview=self.controls.preview('fixture-one',{'amount':4.5},state['revision'])
        self.assertEqual(preview['desired']['amount'],4.5);self.assertEqual(self.path('fixture-one').read_bytes(),self.initial['fixture-one'])
    def test_apply_changes_only_selected_values_and_one_installation(self):
        state=self.controls.inspect('fixture-one');self.controls.apply_local('fixture-one',{'enabled':False},state['revision'])
        self.assertEqual(self.path('fixture-one').read_bytes(),self.initial['fixture-one'].replace(b'Enabled=true',b'Enabled=false'))
        self.assertEqual(self.path('fixture-two').read_bytes(),self.initial['fixture-two'])
    def test_stale_and_cross_game_revisions_are_refused(self):
        state=self.controls.inspect('fixture-one')
        with self.assertRaises(ModError):self.controls.apply_local('fixture-two',{'enabled':False},state['revision'])
        self.path('fixture-one').write_bytes(self.initial['fixture-one']+b'; external change\r\n')
        with self.assertRaises(ModError):self.controls.apply_local('fixture-one',{'enabled':False},state['revision'])
    def test_invalid_fields_and_bounds_are_refused(self):
        for changes in [{'unknown':2},{'amount':11},{'amount':True},{'amount':float('nan')},{'enabled':'false'}]:
            with self.assertRaises((ModError,ValueError)):self.controls.preview('fixture-one',changes)
    def test_private_profile_roundtrip_and_wrong_owner_refusal(self):
        state=self.controls.inspect('fixture-one');self.controls.save_profile_local('fixture-one','my-profile',{'amount':6.5},state['revision'])
        profile=self.controls.profile_rows('fixture-one')[0];self.assertEqual(self.controls.profile('fixture-one',profile['profile_id'])['values']['amount'],6.5)
        doc=json.loads(profile['path'].read_text());doc['game_id']='fixture-two';profile['path'].write_text(json.dumps(doc))
        with self.assertRaises(ModError):self.controls.profile('fixture-one',self.controls.profile_rows('fixture-one')[0]['profile_id'])
        self.assertEqual(self.path('fixture-one').read_bytes(),self.initial['fixture-one'])
    def test_pack_rejects_escape_code_and_colliding_keys(self):
        pack=ini_template('fixture-one')
        for edit in [lambda p:p['files'].update(settings='../escape.ini'),lambda p:p.update(command='run me'),lambda p:p['fields'].append(copy.deepcopy(p['fields'][0]))]:
            value=copy.deepcopy(pack);edit(value)
            with self.assertRaises(ModError):validate_pack(value)
    def test_handoff_is_a_verified_private_zip_and_not_deployment(self):
        state=self.controls.inspect('fixture-one');result=self.controls.prepare_manager_local('fixture-one',state['revision'])
        folder=self.controls.export_path_local('fixture-one')
        with zipfile.ZipFile(folder/'Manager Files.zip') as z:
            self.assertIsNone(z.testzip());self.assertFalse(any(p.endswith(('.exe','.sav','.dll')) for p in z.namelist()))
        self.assertFalse(result['manager_deployed']);self.assertEqual(self.path('fixture-one').read_bytes(),self.initial['fixture-one'])
    def test_ai_reads_previews_proposals_and_local_approval_share_the_service(self):
        endpoint=Endpoint(SimpleNamespace(multi_game=True,controls=self.controls),allow_requests=True)
        state=endpoint.call('mod_controls_inspect',{'instance_id':'fixture-one'})
        result=endpoint.call('mod_controls_propose',{'instance_id':'fixture-one','operation':'controls.apply','arguments':{'revision':state['revision'],'changes':{'amount':3.5}},'request_id':'ai-action'})
        self.assertEqual(result['status'],'AWAITING_LOCAL_APPROVAL');self.assertEqual(self.path('fixture-one').read_bytes(),self.initial['fixture-one'])
        repeated=endpoint.call('mod_controls_propose',{'instance_id':'fixture-one','operation':'controls.apply','arguments':{'revision':state['revision'],'changes':{'amount':3.5}},'request_id':'ai-action'})
        self.assertEqual(repeated['request_sha256'],result['request_sha256'])
        with self.assertRaises(ModError):endpoint.call('mod_controls_approve',{})
        receipt=self.controls.requests('fixture-one').approve_local('ai-action',result['request_sha256'])
        self.assertEqual(receipt['status'],'COMPLETED');self.assertEqual(self.controls.inspect('fixture-one')['values']['amount'],3.5)
        self.assertEqual(self.controls.requests('fixture-one').request_status('ai-action')['status'],'COMPLETED')
    def test_changed_state_blocks_an_already_proposed_action(self):
        state=self.controls.inspect('fixture-one');service=self.controls.requests('fixture-one');proposal=service.propose('controls.apply',{'revision':state['revision'],'changes':{'amount':5}},request_id='stale')
        self.path('fixture-one').write_bytes(self.initial['fixture-one']+b'; new state\n')
        with self.assertRaises(ModError):service.approve_local('stale',proposal['request_sha256'])
    def test_failed_readback_restores_original_bytes(self):
        state=self.controls.inspect('fixture-one');real=self.controls._snapshot;count=[0]
        def fail(ident):
            count[0]+=1;result=real(ident)
            if count[0]>=4:result['values']['enabled']=True
            return result
        with patch.object(self.controls,'_snapshot',side_effect=fail):
            with self.assertRaises(ModError):self.controls.apply_local('fixture-one',{'enabled':False},state['revision'])
        self.assertEqual(self.path('fixture-one').read_bytes(),self.initial['fixture-one'])

if __name__=='__main__':unittest.main(verbosity=2)
