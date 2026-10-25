"""Native-controller references and reviewed argv, using disposable fixtures."""
import copy, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolRewasd as native
import GameToolGameProfiles as profiles

class Rewasd(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.config_root=self.root/'Profiles';self.config=self.config_root/'GENERAL/Controller/Config 1.rewasd';self.config.parent.mkdir(parents=True)
        self.raw=native.overlay.encode({'schemaVersion':3.0,'appVersion':'9.5.0','config':{'appName':'GENERAL'},
          'devices':{'hardware':[{'id':1,'convertToVirtual':True,'unknown':{'keep':'exact'}}],
                     'virtual':{'gamepads':[{'id':1,'type':'360'}]}}})
        self.config.write_bytes(self.raw);self.program=self.root/'program';self.program.mkdir()
        (self.program/'reWASDCommandLine.exe').write_bytes(b'fixture-not-executable')
        self.service=native.Native(self.root/'data',self.config_root,self.program)
        self.binding=self.service.capture(self.config,'Test controller','123456789;123456788',2)
    def test_catalog_summary_preserves_unknown_native_fields_and_original_bytes(self):
        rows=self.service.configs();self.assertEqual(len(rows),1);self.assertEqual(rows[0]['outputs'],['360'])
        self.assertEqual(self.config.read_bytes(),self.raw);self.assertNotIn('raw',rows[0])
        self.assertEqual(self.service.check(self.binding)['raw'],self.raw)
    def test_backup_is_byte_exact_and_new_native_edit_fails_closed(self):
        backup=self.service.private/(self.binding['config_sha256']+'.rewasd')
        self.assertEqual(backup.read_bytes(),self.raw)
        self.config.write_bytes(self.raw+b' ')
        with self.assertRaisesRegex(ValueError,'changed'):self.service.preview(self.binding,'apply')
        self.assertEqual(backup.read_bytes(),self.raw)
    def test_bad_recovery_bytes_refused(self):
        (self.service.private/(self.binding['config_sha256']+'.rewasd')).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'recovery'):self.service.check(self.binding)
    def test_no_device_id_can_save_but_cannot_apply(self):
        value=self.service.capture(self.config,'Another controller')
        with self.assertRaisesRegex(ValueError,'Device ID'):self.service.preview(value,'apply')
    def test_unregistered_path_symlink_and_unsupported_schema_refused(self):
        outside=self.root/'other.rewasd';outside.write_bytes(self.raw)
        with self.assertRaises(ValueError):native.inspect(outside,self.config_root)
        value=json.loads(self.raw);value['schemaVersion']=4;self.config.write_text(json.dumps(value))
        self.assertIn('error',self.service.configs()[0])
        with self.assertRaisesRegex(ValueError,'schema'):native.inspect(self.config,self.config_root)
        try:
            link=self.config.parent/'link.rewasd';link.symlink_to(outside)
        except (OSError,NotImplementedError):return
        with self.assertRaisesRegex(ValueError,'Linked'):native.inspect(link,self.config_root)
    def test_shell_text_invalid_ids_slots_and_unknown_actions_refused(self):
        for key,value in [('device_id','123; & calc.exe'),('device_id','0x37d7/0x2401'),('slot',True),('slot',5)]:
            bad=copy.deepcopy(self.binding);bad[key]=value
            with self.assertRaises(ValueError):native.validate(bad)
        with self.assertRaises(ValueError):self.service.preview(self.binding,'clear_slot')
    def test_separate_exact_review_required_and_stale_proposal_cannot_execute(self):
        proposal=self.service.preview(self.binding,'apply')
        with mock.patch.object(native.subprocess,'run')as run:
            with self.assertRaisesRegex(ValueError,'Review'):self.service.execute_reviewed(self.binding,'apply',proposal)
            bad=copy.deepcopy(proposal);bad['slot']=1
            with self.assertRaisesRegex(ValueError,'changed'):self.service.execute_reviewed(self.binding,'apply',bad,confirmed=True)
            run.assert_not_called()
    def test_reviewed_apply_is_structured_argv_and_records_only_unverified_output(self):
        proposal=self.service.preview(self.binding,'apply')
        with mock.patch.object(native.subprocess,'run',return_value=SimpleNamespace(returncode=0))as run:
            receipt=self.service.execute_reviewed(self.binding,'apply',proposal,confirmed=True)
            self.assertEqual(run.call_args.args[0],[str(self.program/'reWASDCommandLine.exe'),'apply','--id','123456789;123456788','--path',str(self.config),'--slot','slot2'])
            self.assertNotIn('shell',run.call_args.kwargs);self.assertEqual(receipt['physical_acceptance'],'unverified')
        self.assertEqual(self.config.read_bytes(),self.raw)
    def test_remap_off_survives_missing_config_and_failed_command_is_not_success(self):
        self.config.unlink();proposal=self.service.preview(self.binding,'off')
        self.assertEqual(proposal['argv'][-4:],['--id','123456789;123456788','--state','off'])
        with mock.patch.object(native.subprocess,'run',return_value=SimpleNamespace(returncode=3)):
            with self.assertRaisesRegex(ValueError,'failed'):self.service.execute_reviewed(self.binding,'off',proposal,confirmed=True)
        self.assertEqual(json.loads(next(self.service.private.glob('operation-*.json')).read_text())['returncode'],3)
    def test_native_profile_needs_no_azeron_map_and_preserves_other_game_defaults(self):
        service=profiles.Profiles(self.root/'data');service.rewasd=self.service
        p=service.capture_rewasd('new-game','New Game','Controller setup',self.config,'Controller','123',1)
        value=service.put(p,service.load()[1]);self.assertEqual(service.check(p),[])
        self.assertFalse(p['automatic']);self.assertEqual(service.games()['new-game'],'New Game')
        with mock.patch.object(native.subprocess,'run')as run:
            service.activate(p['id'],profiles.fingerprint(value))
            value,pin=service.load();value['options']['restore_on_open']=True;service.save(value,pin)
            self.assertIsNone(service.match('new-game.exe'));service.deactivate(service.load()[1]);run.assert_not_called()
        self.assertEqual(self.config.read_bytes(),self.raw)
        self.assertFalse(service.store.load()[0]['preferences']['display'])
    def test_native_timeout_records_unknown_and_does_not_retry(self):
        proposal=self.service.preview(self.binding,'apply')
        with mock.patch.object(native.subprocess,'run',side_effect=native.subprocess.TimeoutExpired('fixture',15))as run:
            with self.assertRaisesRegex(ValueError,'outcome unknown'):
                self.service.execute_reviewed(self.binding,'apply',proposal,confirmed=True)
            self.assertEqual(run.call_count,1)
        self.assertEqual(json.loads(next(self.service.private.glob('operation-*.json')).read_text())['outcome'],'unknown')

if __name__=='__main__':unittest.main()
