"""Disposable passive-inventory fixtures; no native input or configuration writes."""
import copy,ctypes,json,math,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolControllerInventory as inv

CID="11111111-2222-3333-4444-555555555555"
OTHER_CID="22222222-2222-3333-4444-555555555555"
SID="S-1-5-21-111-222-333-1001"

def pnp(instance="USB\\VID_37D7&PID_2401\\PRIVATE-SERIAL",cid=CID,**more):
    return {"InstanceId":instance,"Label":"Test game controller","Class":"HIDClass","Enumerator":"USB","ContainerId":cid,**more}

def state(index=0,buttons=0,present=True,**values):
    return {"index":index,"present":present,"state":{"buttons":buttons,**values}}

class Clock:
    def __init__(self):self.value=0
    def now(self):return self.value
    def sleep(self,t):self.value+=t

class Inventory(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.native=self.root/'native';self.native.mkdir()
    def service(self,rows=None,xinput=None,**args):
        return inv.Inventory(pnp_provider=lambda:{"devices":rows or [],"user_sid":SID},
            xinput_provider=xinput or (lambda include_state=False:[]),rewasd_root=self.native,**args)
    def native_files(self,cid=CID):
        member={"DataType":"Controller","Guid":"source-guid","ContainerId":cid,"ControllerType":"Xbox360",
                "ManufacturerInfo":{"ContainerDescription":"Flydigi Vader 5 Pro","VendorId":14295,"ProductId":9217},
                "ConnectionType":"Wireless","IsExclusiveAccessSupported":False,"IsExclusiveAccessFailed":False}
        (self.native/'GamepadCollection.json').write_text(json.dumps([member]))
        assigned={"source-guid":{"IsRemapToggled":True,"SlotProfiles":{"Slot1":{"ConfigPath":r'C:\Private\Test Game.rewasd'}}}}
        name='GamepadProfileUserRelations_'+SID.replace('-','')+'.json'
        (self.native/name).write_text(json.dumps(assigned))
    def test_native_structures_match_documented_abi(self):
        self.assertEqual(ctypes.sizeof(inv._Gamepad),12)
        self.assertEqual(ctypes.sizeof(inv._State),16)
        self.assertEqual(ctypes.sizeof(inv._Capabilities),20)
    def test_ids_repeat_across_snapshots_and_new_adapter_objects(self):
        a=self.service([pnp()]).snapshot();b=self.service([pnp()]).snapshot()
        self.assertEqual(a['devices'][0]['id'],b['devices'][0]['id'])
        self.assertEqual(a['identity_scope'],'private_machine_data_only')
        self.assertNotIn('PRIVATE-SERIAL',json.dumps(a))
    def test_actual_container_and_parent_edges_are_observed(self):
        a=pnp();b=pnp('HID\\VID_37D7&PID_2401\\SECOND',Parent=a['InstanceId'])
        s=self.service([a,b]).snapshot()
        self.assertEqual({x['kind'] for x in s['relationships']},{'same-container','pnp-parent'})
        self.assertTrue(all(x['status']=='observed' for x in s['relationships']))
    def test_equal_vid_pid_is_not_an_identity_relationship(self):
        s=self.service([pnp(),pnp('USB\\VID_37D7&PID_2401\\ANOTHER',OTHER_CID)]).snapshot()
        self.assertEqual(s['relationships'],[])
    def test_xbox_label_is_not_proof_of_virtual_hardware(self):
        s=self.service([pnp(Label='Xbox 360 Controller')]).snapshot()
        self.assertEqual(s['devices'][0]['kind'],'physical')
        self.assertEqual(s['devices'][0]['identity_status'],'inferred')
        self.assertIn('virtual USB',s['devices'][0]['classification_reason'])
    def test_virtual_metadata_is_only_inferred(self):
        s=self.service([pnp('ROOT\\VIGEMBUS\\PRIVATE',Enumerator='ROOT',Label='Virtual controller')]).snapshot()
        self.assertEqual(s['devices'][0]['kind'],'virtual')
        self.assertEqual(s['devices'][0]['identity_status'],'inferred')
    def test_xna_controller_class_is_eligible_but_keyboard_feeder_is_not(self):
        s=self.service([pnp(Class='XnaComposite',Label='Xbox 360 Controller'),
                        pnp('HID\\KEYBOARD',OTHER_CID,Class='Keyboard',Label='HID Keyboard Device')]).snapshot()
        self.assertTrue(s['devices'][0]['eligible_primary']);self.assertFalse(s['devices'][1]['eligible_primary'])
        self.assertIn('XnaComposite',inv.PNP_QUERY)
    def test_no_state_read_on_snapshot_default_and_export_strips_private_ids(self):
        calls=[]
        def reader(include_state=False):calls.append(include_state);return [state(0,4096)]
        s=self.service([pnp()],reader).snapshot()
        self.assertEqual(calls,[False])
        exported=inv.export_summary(s);text=json.dumps(exported)
        self.assertNotIn(s['devices'][0]['id'],text)
        self.assertNotIn('buttons',text);self.assertNotIn('group_id',text)
        self.assertNotIn('state',exported['xinput'][0])
    def test_label_scrubs_raw_guid_and_device_paths(self):
        self.assertNotIn(CID,inv._label('Controller '+CID))
        self.assertEqual(inv._label(r'HID\VID_37D7\serial'),'Controller')
    def test_over_budget_pnp_does_not_silently_truncate(self):
        s=self.service([pnp(str(i)) for i in range(257)]).snapshot()
        self.assertFalse(s['devices']);self.assertTrue(s['warnings'])
    def test_exact_native_collection_join_preserves_uncertainty(self):
        self.native_files();s=self.service([pnp()]).snapshot()
        self.assertTrue(s['rewasd']['available'])
        native=next(d for d in s['devices'] if d['source']=='rewasd_saved_collection')
        self.assertIsNone(native['present']);self.assertEqual(native['kind'],'unknown')
        self.assertTrue(native['eligible_primary'])
        self.assertFalse(native['exclusive_access_supported']);self.assertFalse(native['exclusive_access_failed'])
        self.assertEqual(s['relationships'][0]['kind'],'same-container')
        assignment=s['rewasd']['relations'][0]
        self.assertEqual(assignment['config_label'],'Test Game');self.assertTrue(assignment['saved_remap_on'])
        self.assertIn('no live',assignment['basis']);self.assertNotIn('C:\\Private',json.dumps(s))
    def test_native_relation_does_not_read_other_users_file(self):
        self.native_files()
        current=self.native/('GamepadProfileUserRelations_'+SID.replace('-','')+'.json');current.unlink()
        (self.native/'GamepadProfileUserRelations_S1999.json').write_text('{invalid')
        s=self.service().snapshot()
        self.assertEqual(s['rewasd']['relations'],[])
        self.assertTrue(s['rewasd']['warnings'])
    def test_unknown_user_never_reads_per_user_relations(self):
        self.native_files()
        service=self.service();service.pnp_provider=lambda:{'devices':[]}
        self.assertEqual(service.snapshot()['rewasd']['relations'],[])
    def test_unsupported_native_schema_does_not_guess(self):
        (self.native/'GamepadCollection.json').write_text('{"unexpected":true}')
        s=self.service().snapshot();self.assertFalse(s['rewasd']['available']);self.assertTrue(s['rewasd']['warnings'])
    def test_composite_native_members_are_read_without_changing_collection(self):
        self.native_files();path=self.native/'GamepadCollection.json'
        member=json.loads(path.read_text())[0]
        path.write_text(json.dumps([{'DataType':'PeripheralController','Guid':'group-guid','Controllers':[member]}]));before=path.read_bytes()
        self.assertEqual(len(self.service().snapshot()['rewasd']['devices']),1)
        self.assertEqual(path.read_bytes(),before)
    def sampler(self,sequence):
        clock=Clock();calls=[]
        def reader(include_state=False):
            self.assertTrue(include_state);i=min(len(calls),len(sequence)-1);calls.append(i);return copy.deepcopy(sequence[i])
        return self.service(xinput=reader,monotonic=clock.now,sleep=clock.sleep),calls
    def test_neutral_hold_release_is_only_a_slot_candidate(self):
        s,_=self.sampler([[state()]]+[[state(buttons=4096)]]*5+[[state()]]*5)
        r=s.sample_hold(.5,min_hold=.15)
        self.assertEqual(r['status'],'candidate');self.assertTrue(r['candidates'][0]['release_observed'])
        self.assertEqual(r['candidates'][0]['controls'],['A'])
        self.assertIsNone(r['selected_device_id']);self.assertFalse(r['physical_identity_verified'])
    def test_initially_held_input_is_not_deliberate_identification(self):
        s,_=self.sampler([[state(buttons=4096)]]*12)
        self.assertEqual(s.sample_hold(.5,min_hold=.15)['status'],'no_candidate')
    def test_multiple_mirrored_slots_are_ambiguous_not_selected(self):
        s,_=self.sampler([[state(0),state(1)]]+[[state(0,4096),state(1,4096)]]*5+[[state(0),state(1)]]*5)
        r=s.sample_hold(.5,min_hold=.15)
        self.assertEqual(r['status'],'ambiguous');self.assertEqual(len(r['candidates']),2)
        self.assertIsNone(r['selected_device_id'])
    def test_disconnect_invalidates_held_candidate(self):
        s,_=self.sampler([[state()]]+[[state(buttons=4096)]]*5+[[state(present=False)]]*5)
        r=s.sample_hold(.5,min_hold=.15);self.assertEqual(r['status'],'interrupted');self.assertEqual(r['candidates'],[])
    def test_short_taps_and_stick_drift_do_not_pass_hold_gate(self):
        s,_=self.sampler([[state(left_x=4000)],[state(buttons=4096)],[state()]]+[[state()]]*8)
        self.assertEqual(s.sample_hold(.5,min_hold=.15)['status'],'no_candidate')
    def test_cancellation_and_stalled_clock_are_bounded(self):
        s,calls=self.sampler([[state()]])
        self.assertEqual(s.sample_hold(.5,cancel=lambda:True)['status'],'cancelled');self.assertFalse(calls)
        s,calls=self.sampler([[state()]])
        s.monotonic=lambda:0;s.sleep=lambda _:None
        self.assertLessEqual(s.sample_hold(.5)['frames'],12)
    def test_sampling_limits_refuse_unbounded_or_invalid_requests(self):
        s=self.service()
        for duration in (True,0,6,float('nan'),'3'):
            with self.assertRaises(ValueError):s.sample_hold(duration)
        with self.assertRaises(ValueError):s.sample_hold(3,interval=.001)
    def test_no_mutating_capability_or_untrusted_shell_command_exists(self):
        self.assertFalse(self.service().snapshot()['capabilities']['disconnect'])
        self.assertFalse(self.service().snapshot()['capabilities']['reconnect'])
        self.assertNotIn('XInputSetState',inv.XInput.__doc__ or '')
        self.assertNotRegex(inv.PNP_QUERY,r'Disable-PnpDevice|Enable-PnpDevice|Restart-PnpDevice|Invoke-Expression')
        self.assertFalse(hasattr(self.service(),'disconnect'))

if __name__=='__main__':unittest.main()
