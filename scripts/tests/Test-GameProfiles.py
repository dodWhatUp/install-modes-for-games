"""Disposable runtime-profile cases; never uses installed data or game input."""
import copy,importlib.util,sys,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolGameProfiles as api
import GameToolKeymapDocument as maps
spec=importlib.util.spec_from_file_location('profile_fixtures',Path(__file__).with_name('Test-KeymapBuilder.py'))
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)

class Profiles(unittest.TestCase):
    def setUp(self):
        fixtures.Sources.setUp(self)
        self.service=api.Profiles(self.library.root.parent)
        self.native=mock.patch('GameToolControlsPlanner.native_status',return_value=[{'state':'match'}]);self.native.start();self.addCleanup(self.native.stop)
        self.profile=self.service.capture('game','My setup')
        self.before,self.overlay_pin=self.library.store.load()
    def save(self):return self.service.put(self.profile,self.service.load()[1])
    def test_capture_and_save_are_inert_and_restore_off_by_default(self):
        v=self.save()
        self.assertEqual(self.library.store.load()[1],self.overlay_pin)
        self.assertFalse(v['options']['enabled']);self.assertFalse(v['options']['restore_on_open'])
        self.assertEqual(self.profile['source_sha256'],maps.fingerprint(self.doc))
    def test_activate_existing_assets_only_preserves_manifest_and_appearance(self):
        v=self.save();self.service.activate(self.profile['id'],api.fingerprint(v))
        after,_=self.library.store.load()
        self.assertEqual(after['manifest'],self.before['manifest'])
        self.assertEqual(after['preferences']['visibility'],self.before['preferences']['visibility'])
        self.assertEqual(after['preferences']['display_target'],'studio');self.assertTrue(after['preferences']['enabled'])
        self.assertTrue(self.service.load()[0]['options']['enabled'])
    def test_deactivate_is_persistent_and_keeps_profiles(self):
        v=self.save();v=self.service.activate(self.profile['id'],api.fingerprint(v))
        pin=api.fingerprint(v);v['options']['automatic_game_switch']=True;v=self.service.save(v,pin)
        self.service.deactivate(api.fingerprint(v));v,_=self.service.load()
        self.assertFalse(v['options']['enabled']);self.assertIsNone(v['active_profile_id'])
        self.assertEqual(len(v['profiles']),1);self.assertFalse(self.library.store.load()[0]['preferences']['display'])
    def test_stale_profile_write_rejected_and_history_preserved(self):
        old,pin=self.service.load();v=self.save()
        with self.assertRaisesRegex(ValueError,'changed'):self.service.save(old,pin)
        pin=api.fingerprint(v);v['options']['restore_on_open']=True;self.service.save(v,pin)
        self.assertTrue(list((self.service.root/'history').glob('*.json')))
    def test_changed_source_blocks_activation_without_touching_overlay(self):
        v=self.save();changed=copy.deepcopy(self.doc);changed['title']='Edited elsewhere'
        self.library.save_source(changed,self.keymap,self.saved)
        with self.assertRaisesRegex(ValueError,'source changed'):self.service.activate(self.profile['id'],api.fingerprint(v))
        self.assertEqual(self.library.store.load()[1],self.overlay_pin)
    def test_corrupt_asset_rejected_before_activation(self):
        v=self.save();asset=self.before['manifest']['assets'][0]
        (self.service.directory/asset['path']).write_bytes(b'broken')
        with self.assertRaises(ValueError):self.service.activate(self.profile['id'],api.fingerprint(v))
        self.assertEqual(self.library.store.load()[1],self.overlay_pin)
    def test_one_automatic_profile_per_game_and_exact_focus_match(self):
        self.save();p=self.service.capture('game','Second');v=self.service.put(p,self.service.load()[1])
        self.assertEqual(sum(x['automatic']for x in v['profiles']),1)
        assoc=self.before['manifest']['associations'][0]
        self.assertEqual(self.service.match(assoc['executables'][0])['id'],p['id'])
        self.assertIsNone(self.service.match('unrelated.exe'))
    def test_unknown_profile_commands_and_schema_refused(self):
        p=copy.deepcopy(self.profile);p['command']='launch';v=api.empty();v['profiles']=[p]
        with self.assertRaises(ValueError):api.validate(v)
    def test_startup_entry_refuses_foreign_file_and_only_removes_owned_entry(self):
        root=self.root/'startup';root.mkdir();path=root/api.LAUNCHER
        with mock.patch.object(api,'launcher_bytes',return_value=b'fixed app launcher'):
            self.assertTrue(api.startup_entry(self.root,True,root))
            self.assertFalse(api.startup_entry(self.root,False,root))
            path.write_bytes(b'other owner')
            with self.assertRaisesRegex(ValueError,'another owner'):api.startup_entry(self.root,False,root)
            self.assertEqual(path.read_bytes(),b'other owner')
    def test_settings_reader_and_fresh_exact_pid_receipt(self):
        settings=self.root/'settings.ini';settings.write_text('[General]\nEnabled=1\nSlotCount=1\n[Slot1]\nEnabled=1\nKey=F24\nMode=Hold\nSource=Local\nFile=test.png\n')
        self.assertEqual(api.studio_settings(settings)['slots'][0]['key'],'F24')
        status=self.root/'runtime-status.ini'
        status.write_text('[Runtime]\nSchema=1\nPID=123\nAtUnix=100\nEnabled=1\nBoundTriggers=1\nOverlayTrigger=1\nRouteEnabled=1\nSettingsFile='+str(settings)+'\nSettingsSHA256='+api.overlay.sha(settings.read_bytes())+'\nRoutePath=relay.ini\n')
        self.assertTrue(api.runtime_status(settings,123,now=101)['fresh'])
        self.assertFalse(api.runtime_status(settings,124,now=101)['fresh'])
        self.assertFalse(api.runtime_status(settings,123,now=110)['fresh'])
        settings.write_text('[General]\nEnabled=0\n')
        self.assertFalse(api.runtime_status(settings,123,now=101)['fresh'])

if __name__=='__main__':unittest.main()
