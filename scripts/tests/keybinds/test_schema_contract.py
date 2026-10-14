#!/usr/bin/env python3
"""Parity checks for the public keybind JSON schemas and runtime validators."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
from game_keybind_ops.deps import Error
from game_keybind_ops.packs import validate_intent,validate_pack
try:
    from jsonschema import Draft202012Validator,ValidationError
except ImportError as exc:  # Test-only tool; never a runtime dependency.
    raise SystemExit('jsonschema is required only for schema contract validation: '+str(exc))

GAME_SCHEMA=json.loads((ROOT/'schemas/game-pack.schema.json').read_text())
INTENT_SCHEMA=json.loads((ROOT/'schemas/semantic-intent.schema.json').read_text())
GAME_VALIDATOR=Draft202012Validator(GAME_SCHEMA)
INTENT_VALIDATOR=Draft202012Validator(INTENT_SCHEMA)


def packs():
    for path in sorted((ROOT/'game-packs').rglob('pack.json')):
        yield path,json.loads(path.read_text())


def first_pack():
    return copy.deepcopy(next(packs())[1])


class SchemaContractTests(unittest.TestCase):
    def assert_both_reject_pack(self,value):
        with self.assertRaises(ValidationError):GAME_VALIDATOR.validate(value)
        with self.assertRaises(Error):validate_pack(value)

    def assert_both_reject_intent(self,value):
        with self.assertRaises(ValidationError):INTENT_VALIDATOR.validate({'changes':[value]})
        with self.assertRaises(Error):validate_intent(value)

    def test_schemas_are_valid_draft_2020_12(self):
        Draft202012Validator.check_schema(GAME_SCHEMA)
        Draft202012Validator.check_schema(INTENT_SCHEMA)

    def test_every_shipped_pack_passes_schema_and_runtime(self):
        seen=[]
        for path,value in packs():
            GAME_VALIDATOR.validate(value);validate_pack(value);seen.append(path)
        self.assertEqual(len(seen),27)

    def test_semantic_version_is_consistent(self):
        value=first_pack();value['version']='1.0';self.assert_both_reject_pack(value)

    def test_slug_trailing_dot_is_consistent(self):
        value=first_pack();value['keymaps']['invalid.']=value['keymaps'].pop(next(iter(value['keymaps'])))
        self.assert_both_reject_pack(value)

    def test_runtime_valid_300_character_location_is_not_rejected_by_schema(self):
        value=first_pack();value['files'][0]['locations'][0]['pattern']='a'*300
        GAME_VALIDATOR.validate(value);validate_pack(value)

    def test_stopped_process_policy_is_consistent(self):
        value=first_pack();value['files'][0]['stopped_processes']=['bad/name.exe']
        self.assert_both_reject_pack(value)

    def test_nonempty_evidence_note_is_consistent(self):
        value=first_pack();value['evidence']['notes']='';self.assert_both_reject_pack(value)

    def test_variant_files_are_distinct(self):
        value=first_pack();file_id=value['variants'][0]['files'][0];value['variants'][0]['files']=[file_id,file_id]
        self.assert_both_reject_pack(value)

    def test_exclusive_context_pair_is_distinct(self):
        value=first_pack();value['exclusive_contexts']=[['gameplay','gameplay']]
        self.assert_both_reject_pack(value)

    def test_intent_key_limit_is_consistent(self):
        self.assert_both_reject_intent({'action':'use','context':'gameplay','key':'K'*65})


if __name__=='__main__':unittest.main(verbosity=2)
