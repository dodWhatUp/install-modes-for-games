#!/usr/bin/env python3
"""Regression/negative tests with synthetic data and unchanged supplied R8 ZIPs.
Never accesses a live app/game. R8_ROOT must point to the exact recovery extraction.
"""
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid
import zipfile
import input_evidence as ev
import native_review as nr
import safe_io

R8 = Path(os.environ['R8_ROOT'])

class SafeIOTests(unittest.TestCase):
 def test_duplicate_json_rejected(self):
  with self.assertRaises(safe_io.ReviewError):safe_io.strict_json(b'{"x":1,"x":2}')
 def test_nonfinite_rejected(self):
  for x in [b'NaN',b'Infinity',b'-Infinity']:
   with self.assertRaises(safe_io.ReviewError):safe_io.strict_json(x)
 def test_numeric_overflow_rejected(self):
  with self.assertRaises(safe_io.ReviewError):safe_io.strict_json(b'{"x":1e309}')
 def test_utf8_bom(self):self.assertEqual(safe_io.strict_json(b'\xef\xbb\xbf{"x":1}'),{'x':1})
 def test_structural_limit(self):
  with self.assertRaises(safe_io.ReviewError):safe_io.strict_json(b'['*60+b'0'+b']'*60)
 def test_regular_read(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.txt';p.write_bytes(b'abc');b,m=safe_io.read_regular(p);self.assertEqual(b,b'abc');self.assertNotIn(td,json.dumps(m))
 def test_read_bound(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.txt';p.write_bytes(b'1234')
   with self.assertRaises(safe_io.ReviewError):safe_io.read_regular(p,3)
 def test_final_symlink(self):
  with tempfile.TemporaryDirectory() as td:
   a=Path(td)/'a';a.write_text('x');b=Path(td)/'b'
   try:b.symlink_to(a)
   except OSError:self.skipTest('Symlink creation not available on this platform.')
   with self.assertRaises(safe_io.ReviewError):safe_io.read_regular(b)
 def test_ancestor_symlink(self):
  with tempfile.TemporaryDirectory() as td:
   a=Path(td)/'a';a.mkdir();(a/'x').write_text('x');b=Path(td)/'b'
   try:b.symlink_to(a,target_is_directory=True)
   except OSError:self.skipTest('Symlink creation not available on this platform.')
   with self.assertRaises(safe_io.ReviewError):safe_io.read_regular(b/'x')
 def test_existing_output_refused(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(safe_io.ReviewError):safe_io.new_output(Path(td))

class CollectorTests(unittest.TestCase):
 def test_mode_duplicates(self):
  with self.assertRaises(ev.EvidenceError):ev.poe(b'[GENERAL]\nuser_input_mode=wasd\nuser_input_mode=mouse\n[ACTION_KEYS]\njump=32\n')
 def test_action_duplicate(self):
  with self.assertRaises(ev.EvidenceError):ev.poe(b'[ACTION_KEYS]\njump=32\njump=33\n')
 def test_banks_remain_distinct(self):
  x=ev.poe(b'[ACTION_KEYS]\na=81 2\n[WASD_ACTION_KEYS]\na=82 2\n')
  self.assertIsNone(x['selected_section']);self.assertEqual(x['sections']['ACTION_KEYS'][0]['modifier_tokens_unresolved'],[2]);self.assertEqual(len(x['sections']),2)
 def test_account_and_graphics_not_copied(self):
  x=ev.poe(b'[LOGIN]\nuser_email=private@example.invalid\n[DISPLAY]\nresolution_width=1234\n[ACTION_KEYS]\nuse_dodge_roll=32\n')
  self.assertNotIn('private',json.dumps(x));self.assertNotIn('1234',json.dumps(x))
 def test_bad_numeric_is_unknown(self):
  x=ev.poe(b'[ACTION_KEYS]\njump=32\nother=secret word\n');self.assertEqual(len(x['warnings']),1);self.assertNotIn('secret word',json.dumps(x))
 def test_cp_duplicate_refused(self):
  with self.assertRaises(ev.EvidenceError):ev.cp_json(b'{"name":"jump","value":"IK_E","value":"IK_F"}')
 def test_cp_pointer_redacted(self):
  x=ev.cp_json(b'{"private@example.invalid":{"name":"jump","value":"IK_Space"}}')
  self.assertTrue(x['key_code_records'][0]['pointer_redacted']);self.assertNotIn('private@example.invalid',json.dumps(x))
 def test_cp_code_list(self):
  x=ev.cp_json(b'{"name":"jump","value":["IK_Space","IK_Pad_A"]}');self.assertEqual(len(x['key_code_records'][0]['codes']),2)
 def test_cp_empty_not_effective(self):self.assertTrue(ev.cp_json(b'{"x":2}')['warnings'])
 def test_xml_entities_refused(self):
  with self.assertRaises(ev.EvidenceError):ev.cp_xml(b'<!DOCTYPE foo [<!ENTITY x "abc">]><a>&x;</a>')
 def test_xml_context_preserved(self):
  x=ev.cp_xml(b'<root><mapping name="onFoot"><button id="IK_E"/></mapping></root>');self.assertEqual(x['key_code_records'][0]['context_ids'],['onFoot'])
 def test_success_still_candidate(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.ini';p.write_text('[ACTION_KEYS]\njump=32');out=Path(td)/'out';r=ev.collect([('poe2',p)],out,'synthetic-fixture')
   self.assertEqual(r['status'],'CONFIG_CANDIDATE_NOT_EFFECTIVE');self.assertFalse(r['effective_binding_verified']);self.assertTrue((out/'INPUT_EVIDENCE.json').exists())
 def test_recheck_disappearance_only_failure_receipt(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.ini';p.write_text('[ACTION_KEYS]\njump=32');out=Path(td)/'out';original=ev.safe_read(p)
   with patch.object(ev,'safe_read',side_effect=[original,FileNotFoundError()]):
    with self.assertRaises(ev.EvidenceError):ev.collect([('poe2',p)],out,'synthetic-fixture')
   self.assertFalse((out/'INPUT_EVIDENCE.json').exists());r=json.loads((out/'COLLECTION_FAILED.json').read_text());self.assertFalse(r['records_usable'])
 def test_recheck_changed_only_failure_receipt(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.ini';p.write_text('[ACTION_KEYS]\njump=32');out=Path(td)/'out';original=ev.safe_read(p);changed=(b'x',dict(original[1],sha256='a'*64))
   with patch.object(ev,'safe_read',side_effect=[original,changed]):
    with self.assertRaises(ev.EvidenceError):ev.collect([('poe2',p)],out,'synthetic-fixture')
   self.assertFalse((out/'INPUT_EVIDENCE.json').exists())
 def test_duplicate_sources_refused(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.ini';p.write_text('[ACTION_KEYS]\njump=32')
   with self.assertRaises(ev.EvidenceError):ev.collect([('poe2',p),('poe2',p)],Path(td)/'out','synthetic-fixture')
 def test_second_run_no_overwrite(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.ini';p.write_text('[ACTION_KEYS]\njump=32');out=Path(td)/'out';ev.collect([('poe2',p)],out,'synthetic-fixture');original=(out/'INPUT_EVIDENCE.json').read_bytes()
   with self.assertRaises(FileExistsError):ev.collect([('poe2',p)],out,'synthetic-fixture')
   self.assertEqual((out/'INPUT_EVIDENCE.json').read_bytes(),original)

class NativeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.w=nr.expected(R8/'Azeron_R8_CORE5_Profiles.zip','CORE5')
 def profile(self):return copy.deepcopy(self.w['profiles'][0])
 def current(self,ps):return {'profiles':ps,'auxiliary_sha256':{}}
 def compare(self,ps):return nr.compare_family(self.w,self.current(ps),'CORE5')
 def test_exact_family(self):self.assertEqual(self.compare(copy.deepcopy(self.w['profiles']))['decision'],'FAMILY_MATCHES_SUPPLIED_SNAPSHOT_DO_NOT_REIMPORT')
 def test_both_pinned_zip_families(self):self.assertEqual(len(nr.expected(R8/'Azeron_R8_SPARSE6_Profiles.zip','SPARSE6')['profiles']),6)
 def test_wrong_family_digest_rejected(self):
  with self.assertRaises(nr.ReviewError):nr.expected(R8/'Azeron_R8_CORE5_Profiles.zip','SPARSE6')
 def test_empty_current_all_absent(self):self.assertEqual(self.compare([])['decision'],'ALL_ABSENT_IMPORT_REMAINS_A_SEPARATE_ACTION')
 def test_partial_current(self):self.assertIn('RECONCILE',self.compare(self.w['profiles'][:1])['decision'])
 def test_same_name_diff_output_stop(self):
  ps=copy.deepcopy(self.w['profiles']);ps[0]['inputs'][5]['keyValues'][0]='KeyZ';self.assertEqual(self.compare(ps)['decision'],'STOP_RECONCILE_EXISTING_STATE')
 def test_same_id_renamed_stop(self):
  ps=copy.deepcopy(self.w['profiles']);ps[0]['name']='Existing protected choice';self.assertEqual(self.compare(ps)['rows'][0]['status'],'ID_COLLISION_DIFFERENT_NAME_STOP')
 def test_duplicate_names_stop(self):
  ps=copy.deepcopy(self.w['profiles']);x=self.profile();x['id']=str(uuid.uuid4());ps.append(x);self.assertEqual(self.compare(ps)['rows'][0]['status'],'DUPLICATE_NAMES_STOP')
 def test_metadata_separated(self):
  ps=copy.deepcopy(self.w['profiles']);ps[0]['metaData']['createdAt']='different';ps[0]['isFavorite']=True;ps[0]['inputs'][5]['label']='Personal label';r=self.compare(ps)
  self.assertEqual(r['decision'],'FAMILY_MATCHES_SUPPLIED_SNAPSHOT_DO_NOT_REIMPORT');self.assertTrue(r['rows'][0]['metadata_or_label_differences'])
 def test_remapped_ids_links_match(self):
  ps=copy.deepcopy(self.w['profiles']);ids={p['id']:str(uuid.uuid4()) for p in ps}
  for p in ps:
   p['id']=ids[p['id']]
   for b in p['inputs']:
    for i,s in enumerate(nr.SLOTS):
     if b['types'][i]=='24':b['layeringProfileId'+s]=ids[b['layeringProfileId'+s]]
  r=self.compare(ps);self.assertEqual(r['decision'],'FAMILY_MATCHES_SUPPLIED_SNAPSHOT_DO_NOT_REIMPORT');self.assertTrue(all(x['status']=='MATCHES_WITH_REMAPPED_ID' for x in r['rows']))
 def test_remapped_ids_unfixed_links_stop(self):
  ps=copy.deepcopy(self.w['profiles'])
  for p in ps:p['id']=str(uuid.uuid4())
  self.assertEqual(self.compare(ps)['decision'],'STOP_RECONCILE_EXISTING_STATE')
 def test_same_button_duplicates_rejected(self):
  p=self.profile();p['inputs'].append(copy.deepcopy(p['inputs'][0]))
  with self.assertRaises(nr.ReviewError):nr.validate_profile(p)
 def test_timing_change_not_ignored(self):
  ps=copy.deepcopy(self.w['profiles']);ps[0]['inputs'][0]['featureDelay']+=1;self.assertEqual(self.compare(ps)['decision'],'STOP_RECONCILE_EXISTING_STATE')
 def test_pin_change_not_ignored(self):
  ps=copy.deepcopy(self.w['profiles']);ps[0]['inputs'][0]['pinOne']+=1;self.assertEqual(self.compare(ps)['decision'],'STOP_RECONCILE_EXISTING_STATE')
 def test_joystick_change_not_ignored(self):
  ps=copy.deepcopy(self.w['profiles']);next(b for b in ps[0]['inputs'] if b['id']==24)['analogSettings']['angle']+=1
  self.assertEqual(self.compare(ps)['decision'],'STOP_RECONCILE_EXISTING_STATE')
 def test_before_after_all_preserved(self):
  a=self.current(copy.deepcopy(self.w['profiles']));r=nr.preservation(a,a,'CORE5');self.assertTrue(r['all_prior_operational_fields_preserved'])
 def test_prior_deleted_stop(self):
  a=self.current(copy.deepcopy(self.w['profiles']));b=self.current(copy.deepcopy(self.w['profiles'][1:]));r=nr.preservation(a,b,'CORE5');self.assertFalse(r['all_prior_operational_fields_preserved']);self.assertEqual(r['prior_profiles'][0]['status'],'MISSING_AFTER_STOP')
 def test_unknown_operational_field_not_ignored(self):
  a=self.current(copy.deepcopy(self.w['profiles']));b=copy.deepcopy(a);b['profiles'][0]['newRuntimeOption']=True
  self.assertFalse(nr.preservation(a,b,'CORE5')['all_prior_operational_fields_preserved'])
 def test_zip_path_traversal_rejected(self):
  bio=io.BytesIO()
  with zipfile.ZipFile(bio,'w') as z:z.writestr('../x.json','{}')
  with self.assertRaises(nr.ReviewError):nr.bounded_zip(bio.getvalue())
 def test_unknown_zip_not_restored(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'unknown.zip'
   with zipfile.ZipFile(p,'w') as z:z.writestr('anything.json','{}')
   with self.assertRaises(nr.ReviewError):nr.snapshot(p)
 def test_snapshot_duplicate_profile_ids_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.json';x=self.profile();p.write_text(json.dumps([x,x]))
   with self.assertRaises(nr.ReviewError):nr.snapshot(p)
 def test_readonly_run_no_overwrite(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a.json';p.write_text(json.dumps(self.w['profiles']));initial=p.read_bytes();out=Path(td)/'out'
   r=nr.run(R8/'Azeron_R8_CORE5_Profiles.zip',p,'CORE5',out,snapshot_scope='synthetic-test');self.assertFalse(r['native_import_tested']);self.assertEqual(initial,p.read_bytes())
   with self.assertRaises(nr.ReviewError):nr.run(R8/'Azeron_R8_CORE5_Profiles.zip',p,'CORE5',out)

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 out={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
      'inputs':'synthetic fixtures plus pinned R8 profile deliveries','live_app_access':False,'game_tested':False,'import_executed':False}
 Path(os.environ.get('QA_OUTPUT','QA_PREFLIGHT.json')).write_text(json.dumps(out,indent=2)+'\n')
 raise SystemExit(not result.wasSuccessful())
