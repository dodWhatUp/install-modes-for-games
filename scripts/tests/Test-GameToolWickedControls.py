"""Reviewed adapter tests use fictional executable/DLL bytes in temporary folders."""
import copy,json,shutil,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolModControls import ModControls
from GameToolWickedControls import WickedControls,SOURCE,TARGETS,module
from GameToolModControlCatalog import coordinate,validate_catalog
from game_mod_ops.definitions import default_definition
from game_mod_ops.safety import object_hash,ModError

class Workspaces:
    def __init__(self):
        definition=default_definition('no-rest-for-the-wicked','No Rest for the Wicked','directory','NoRestForTheWicked.exe')
        self.support={'no-rest-for-the-wicked':{'pack':{'definition':definition},'revision':object_hash(definition)}}
        self.catalog=SimpleNamespace(support=SimpleNamespace(rows=lambda:self.support),recipes=lambda:{})
    def game_rows(self):return [{'id':'no-rest-for-the-wicked','name':'No Rest for the Wicked','manager':'manual','recipe_available':False}]

class FixtureControls(ModControls):
    def _wicked(self,b,record):return WickedControls(b['workspace'],record['body']['game_dir'],process_check=lambda:[])
    def _closed(self,s):pass

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='wicked-shared-');self.base=Path(self.temp.name)
        self.game=self.base/'game';self.game.mkdir();(self.game/'NoRestForTheWicked.exe').write_bytes(b'fictional marker, never run')
        (self.game/'UserData').mkdir();self.config=self.game/'UserData/MelonPreferences.cfg'
        self.original=b'# personal configuration\r\n[WickedMenu]\r\nMenuHotkey = "F12"\r\n\r\n[UnknownMod]\r\nSecret = "private-value"\r\n'
        self.config.write_bytes(self.original);(self.game/'save.dat').write_bytes(b'progress retained')
        self.work=self.base/'controller';(self.work/'app').mkdir(parents=True);(self.work/'cache').mkdir()
        for name in ('switcher.py','mod_options.py'):shutil.copyfile(SOURCE/name,self.work/'app'/name)
        components=[]
        for ident,target in TARGETS.items():
            path=self.work/'cache'/(ident+'.dll');path.write_bytes(('fictional '+ident).encode())
            components.append({'id':ident,'name':ident,'url':'https://example.com/'+ident,'recommended':ident!='loader',
                'files':[{'target':target,'source':'cache/'+path.name,'sha256':module('switcher').sha(path)}]})
        (self.work/'deployment.json').write_text(json.dumps({'schema':1,'game_root':str(self.game),
            'game_exe_sha256':module('switcher').sha(self.game/'NoRestForTheWicked.exe'),'components':components}))
        self.data=self.base/'data';self.data.mkdir();self.controls=FixtureControls(self.data,Workspaces())
        self.controls.register_local('no-rest-for-the-wicked',self.game,instance_id='fixture-wicked')
        self.controls.connect_local('fixture-wicked',workspace=self.work,writes_enabled=True)
    def tearDown(self):self.temp.cleanup()
    def inspect(self):return self.controls.inspect('fixture-wicked')
    def apply(self,changes):return self.controls.apply_local('fixture-wicked',changes,self.inspect()['revision'])
    def on(self):return {key:True for key in TARGETS}
    def test_four_compact_modules_ten_typed_settings_and_public_context(self):
        state=self.inspect();self.assertEqual(len(state['modules']),4);self.assertEqual(len(state['schema']),10)
        self.assertEqual(state['values']['wm-hotkey'],'F12');text=json.dumps(state)
        for secret in (str(self.base),'private-value','UnknownMod'):self.assertNotIn(secret,text)
        self.assertFalse(state['coordination']['blocked']);self.assertFalse(state['runtime_verified'])
    def test_atomic_files_and_preferences_preserve_unknown_settings_and_save(self):
        result=self.apply(self.on()|{'wm-hotkey':'F10','bl-gems':False})
        self.assertTrue(result['game_files_written']);state=self.inspect()
        self.assertEqual(state['values']['wm-hotkey'],'F10');self.assertFalse(state['values']['bl-gems'])
        self.assertTrue(all((self.game/path).is_file() for path in TARGETS.values()))
        self.assertIn(b'Secret = "private-value"\r\n',self.config.read_bytes())
        self.assertEqual((self.game/'save.dat').read_bytes(),b'progress retained')
        self.assertTrue(any(len(json.loads(p.read_text())['files'])==5 for p in (self.work/'recovery').glob('*/transaction.json')))
    def test_late_proxy_failure_rolls_back_preferences_and_all_plugins(self):
        core=module('switcher');write=core.atomic_bytes;failed=False
        def fail_once(path,raw):
            nonlocal failed
            if Path(path)==self.game/'version.dll' and not failed:failed=True;raise OSError('simulated final proxy failure')
            return write(path,raw)
        with patch.object(core,'atomic_bytes',side_effect=fail_once):
            with self.assertRaisesRegex(OSError,'simulated'):self.apply(self.on()|{'wm-hotkey':'F10'})
        self.assertEqual(self.config.read_bytes(),self.original)
        self.assertTrue(all(not (self.game/path).exists() for path in TARGETS.values()))
    def test_external_writer_is_retained_during_failed_recovery(self):
        core=module('switcher');write=core.atomic_bytes
        def intervene(path,raw):
            if Path(path)==self.game/'version.dll':
                (self.game/TARGETS['build-liberator']).write_bytes(b'new external owner')
                raise OSError('simulated intervention')
            return write(path,raw)
        with patch.object(core,'atomic_bytes',side_effect=intervene):
            with self.assertRaisesRegex(RuntimeError,'Recovery requires local review'):self.apply(self.on())
        self.assertEqual((self.game/TARGETS['build-liberator']).read_bytes(),b'new external owner')
        receipt=next((self.work/'recovery').glob('*/transaction.json'))
        self.assertEqual(json.loads(receipt.read_text())['status'],'recovery-required')
    def test_dependency_preview_blocks_apply_without_writing(self):
        state=self.inspect();preview=self.controls.preview('fixture-wicked',{'build-liberator':True},state['revision'])
        self.assertTrue(preview['coordination']['blocked'])
        with self.assertRaisesRegex(ModError,'dependency or resource'):self.controls.apply_local('fixture-wicked',{'build-liberator':True},state['revision'])
        self.assertEqual(self.config.read_bytes(),self.original)
    def test_stale_preferences_and_wrong_controller_are_refused(self):
        state=self.inspect();self.config.write_bytes(self.original+b'# external edit\r\n')
        with self.assertRaises(ModError):self.controls.preview('fixture-wicked',{'wm-hotkey':'F10'},state['revision'])
        (self.work/'app/switcher.py').write_bytes(b'unreviewed source')
        with self.assertRaises(ModError):self.inspect()
    def test_profile_keeps_instance_and_schema_ownership(self):
        state=self.inspect();self.controls.save_profile_local('fixture-wicked','my-profile',{'wm-hotkey':'F10'},state['revision'])
        row=self.controls.profile_rows('fixture-wicked')[0]
        self.assertEqual(self.controls.profile('fixture-wicked',row['profile_id'])['values']['wm-hotkey'],'F10')
        self.assertEqual(self.config.read_bytes(),self.original)
    def test_read_only_connection_never_grants_apply(self):
        self.controls.connect_local('fixture-wicked',workspace=self.work,writes_enabled=False)
        self.assertFalse(self.inspect()['capabilities']['apply'])
        with self.assertRaisesRegex(ModError,'read-only'):self.apply({'wm-hotkey':'F10'})
    def test_generic_graphics_and_game_mods_share_resource_conflict_checks(self):
        fields=[{'id':'one','type':'bool'},{'id':'two','type':'bool'}]
        mods=[{'id':'one','name':'Loader','layer':'game-mods','mechanism':'loader','enabled_field':'one','settings':[], 'claims':['proxy:version.dll']},
              {'id':'two','name':'Graphics hook','layer':'graphics-tools','mechanism':'graphics-injector','enabled_field':'two','settings':[], 'claims':['proxy:VERSION.dll']}]
        validate_catalog(mods,fields)
        self.assertTrue(coordinate(mods,{'one':True,'two':True})['blocked'])
        self.assertFalse(coordinate(mods,{'one':True,'two':False})['blocked'])
        broken=copy.deepcopy(mods);broken[0]['claims']=['file:../escape.dll']
        with self.assertRaises(ModError):validate_catalog(broken,fields)
    def test_labeled_source_buttons_reject_unrelated_websites(self):
        fields=[{'id':'enabled','type':'bool'}]
        row={'id':'example','name':'Example','layer':'game-mods','mechanism':'configuration','settings':['enabled'],'github':'https://example.com/not-github'}
        with self.assertRaisesRegex(ModError,'must match'):validate_catalog([row],fields)

if __name__=='__main__':unittest.main(verbosity=2)
