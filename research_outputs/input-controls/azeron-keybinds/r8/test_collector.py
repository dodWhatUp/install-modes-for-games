import json,tempfile,unittest
from pathlib import Path
import collect_input_evidence as c
class CollectorTests(unittest.TestCase):
 def test_two_modes_are_not_merged(self):
  r=c.poe(b'[GENERAL]\nuser_input_mode=wasd\n[UI]\nuse_wasd_to_move=false\n[ACTION_KEYS]\nuse_bound_skill4=81\n[WASD_ACTION_KEYS]\nuse_bound_skill4=88\n')
  self.assertEqual(r['selected_section'],None);self.assertEqual(r['sections']['ACTION_KEYS'][0]['numeric_tokens'],[81]);self.assertEqual(r['sections']['WASD_ACTION_KEYS'][0]['numeric_tokens'],[88])
 def test_flags_remain_unknown(self):
  r=c.poe(b'[WASD_ACTION_KEYS]\nuse_bound_skill9=81 2\n');self.assertEqual(r['sections']['WASD_ACTION_KEYS'][0]['modifier_tokens_unresolved'],[2])
 def test_zero_not_a_button(self):
  r=c.poe(b'[ACTION_KEYS]\nuse_flask_in_slot3=0\n');self.assertEqual(r['sections']['ACTION_KEYS'][0]['binding_state'],'UNASSIGNED_CANDIDATE')
 def test_private_sections_omitted(self):
  r=c.poe(b'[ACCOUNT]\nname=PRIVATE\n[UI]\nlast_character=PRIVATE\n[ACTION_KEYS]\nchat=13\n');self.assertNotIn('PRIVATE',json.dumps(r))
 def test_duplicate_refused(self):
  with self.assertRaises(c.EvidenceError):c.poe(b'[ACTION_KEYS]\nchat=13\nchat=14\n')
 def test_text_not_copied(self):
  r=c.poe(b'[ACTION_KEYS]\nchat=secret@example.com\nuse_bound_skill1=1\n');self.assertNotIn('secret',json.dumps(r));self.assertEqual(len(r['warnings']),1)
 def test_missing_sections_refused(self):
  with self.assertRaises(c.EvidenceError):c.poe(b'[OTHER]\na=1\n')
 def test_json_key_codes_only(self):
  r=c.cp_json(json.dumps({'account':'SECRET','options':[{'name':'Jump','value':'IK_Space'},{'name':'Private','value':'SECRET'}]}).encode());self.assertEqual(len(r['key_code_records']),1);self.assertNotIn('SECRET',json.dumps(r))
 def test_json_unsupported_not_default(self):
  r=c.cp_json(b'{"options":[]}');self.assertEqual(r['key_code_records'],[]);self.assertTrue(r['warnings'])
 def test_entities_refused(self):
  with self.assertRaises(c.EvidenceError):c.cp_xml(b'<!DOCTYPE doc [<!ENTITY x SYSTEM "file:///secret">]><doc/>')
 def test_xml_preserves_context(self):
  r=c.cp_xml(b'<mappings><mapping name="Jump"><button id="IK_Space"/></mapping></mappings>');self.assertEqual(r['key_code_records'][0]['context_ids'],['Jump'])
 def test_output_and_source_integrity(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'poe2_production_Config.ini';p.write_bytes(b'[ACTION_KEYS]\nchat=13\n');b=p.read_bytes();out=Path(td)/'result'
   r=c.collect([('poe2',p)],out,'local-config-candidate');self.assertEqual(p.read_bytes(),b);self.assertFalse(r['effective_binding_verified']);self.assertFalse(r['full_source_bytes_copied']);self.assertNotIn(str(p),json.dumps(r))
   with self.assertRaises(FileExistsError):c.collect([('poe2',p)],out,'local-config-candidate')
 def test_symlink_refused(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'a';p.write_bytes(b'a');q=Path(td)/'b';q.symlink_to(p)
   with self.assertRaises(c.EvidenceError):c.safe_read(q)
 def test_oversized_refused(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'large';p.write_bytes(b'x'*(c.MAX_BYTES+1))
   with self.assertRaises(c.EvidenceError):c.safe_read(p)
 def test_empty_collection_refused(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(c.EvidenceError):c.collect([],Path(td)/'out','local-config-candidate')
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(CollectorTests);result=unittest.TextTestRunner(verbosity=1).run(suite)
 receipt={'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'synthetic_fixtures_only':True,'user_config_read':False,'no_game_launch':True,'no_network':True}
 (Path(__file__).parent/'QA_COLLECTOR_R8.json').write_text(json.dumps(receipt,indent=2)+'\n')
 if not result.wasSuccessful():raise SystemExit(1)
