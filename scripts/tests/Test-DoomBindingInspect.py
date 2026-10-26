"""Synthetic-only read-only inspection and denied-writer contract checks."""
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolDoomBindingInspect as mod

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    AESGCM = None

IDENTITY = str(mod.STEAM_ID64_BASE + 42)  # Generated test identity, not user data.


def plaintext(contexts):
    data = bytearray(mod.MAGIC_VERSION + b'\0' * 4 + b'\x14\x08keyInput')
    data.append(0x40 + len(contexts))
    names, strings = {}, {}
    def name(value):
        position = len(data)
        if value in names:
            data.extend(struct.pack('>h', names[value] - position))
        else:
            raw = value.encode('ascii')
            names[value] = position
            data.extend(bytes([len(raw)]) + raw)
    def string(value):
        position = len(data)
        if value in strings:
            data.extend(b'\x0d' + (strings[value] - position - 3 + 65536).to_bytes(2, 'little'))
        else:
            raw = value.encode('ascii')
            strings[value] = position
            data.extend(bytes([0x20 + len(raw)]) + raw)
    for rows in contexts:
        if len(rows) <= 31:
            data.append(0x40 + len(rows))
        else:
            data.extend(b'\x11' + bytes([len(rows)]))
        for key, command, secondary in rows:
            data.append(0x14)
            name('key'); string(key)
            name('binding'); string(command)
            name('isSecondary'); data.extend(bytes([secondary, 0]))
    data.append(0)
    return bytes(data)


def wrap(plain, identity=IDENTITY):
    nonce = os.urandom(12)
    aad = (identity + 'MANCUBUSprofile.bin').encode('ascii')
    return nonce + AESGCM(hashlib.sha256(aad).digest()[:16]).encrypt(nonce, plain, aad)


def inspect(plain=None, identity=IDENTITY, game_build='test-build'):
    plain = plain or plaintext([[('K', '_throw', 1), ('K', '_ready', 1)], []])
    raw = wrap(plain, identity)
    return mod.inspect_snapshot(raw, identity, expected_sha256=hashlib.sha256(raw).hexdigest(), game_build=game_build)


class CapabilityTests(unittest.TestCase):
    def test_writer_and_whole_profile_switch_always_unavailable(self):
        info = mod.capabilities()
        self.assertFalse(info['binary_game_write'])
        self.assertFalse(info['whole_profile_switch'])
        self.assertFalse(info['internal_checksum_verified'])
        for arguments in ({}, {'approved': True, 'force': True}):
            with self.assertRaises(mod.InspectError) as caught:
                mod.prepare_binary_changes(**arguments)
            self.assertEqual(caught.exception.code, 'BINARY_WRITE_UNVERIFIED')


@unittest.skipIf(AESGCM is None, 'Reviewed cryptography runtime unavailable')
class ReaderTests(unittest.TestCase):
    def assert_code(self, code, call):
        with self.assertRaises(mod.InspectError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_read_reference_backed_bundles_and_contexts(self):
        value = inspect()
        self.assertEqual(value['context_counts'], [2, 0])
        self.assertEqual(value['binding_count'], 2)
        self.assertEqual([r['output'] for r in value['bindings']], ['K', 'K'])
        self.assertGreater(value['validated_reference_count'], 0)
        self.assertTrue(value['source']['envelope_authenticated'])
        self.assertFalse(value['source']['internal_checksum_verified'])
        self.assertNotIn(IDENTITY, json.dumps(value))

    def test_keyboard_mouse_controller_labels_are_retained(self):
        value = inspect(plaintext([[('A', '_a', 1), ('MOUSE3', '_b', 1), ('JOY1', '_c', 1)]]))
        self.assertEqual([r['input_family'] for r in value['bindings']], ['keyboard', 'mouse', 'controller'])
        self.assertEqual(value['bindings'][2]['output'], 'JOY1')

    def test_source_pin_is_mandatory_and_exact(self):
        raw = wrap(plaintext([[('K', '_a', 1)]]))
        self.assert_code('SOURCE_PIN_REQUIRED', lambda: mod.inspect_snapshot(raw, IDENTITY, expected_sha256=''))
        self.assert_code('SOURCE_CHANGED', lambda: mod.inspect_snapshot(raw, IDENTITY, expected_sha256='0' * 64))

    def test_authenticated_tampering_is_rejected_even_with_new_source_hash(self):
        raw = bytearray(wrap(plaintext([[('K', '_a', 1)]]))); raw[-1] ^= 1; raw = bytes(raw)
        self.assert_code('AUTHENTICATION_FAILED', lambda: mod.inspect_snapshot(raw, IDENTITY, expected_sha256=hashlib.sha256(raw).hexdigest()))

    def test_wrong_identity_is_rejected(self):
        raw = wrap(plaintext([[('K', '_a', 1)]]))
        self.assert_code('AUTHENTICATION_FAILED', lambda: mod.inspect_snapshot(raw, str(int(IDENTITY) + 1), expected_sha256=hashlib.sha256(raw).hexdigest()))

    def test_wrong_role_is_rejected(self):
        raw = wrap(plaintext([[('K', '_a', 1)]]))
        self.assert_code('FILE_ROLE_UNSUPPORTED', lambda: mod.inspect_snapshot(raw, IDENTITY, expected_sha256=hashlib.sha256(raw).hexdigest(), filename='settings.bin'))

    def test_unreviewed_header_is_rejected(self):
        p = bytearray(plaintext([[('K', '_a', 1)]])); p[7] = 4
        self.assert_code('FORMAT_UNSUPPORTED', lambda: inspect(bytes(p)))

    def test_duplicate_marker_is_rejected(self):
        p = plaintext([[('K', '_a', 1)]]) + b'\x08keyInput'
        self.assert_code('FORMAT_INVALID', lambda: inspect(p))

    def test_truncated_binding_array_is_rejected(self):
        p = plaintext([[('K', '_a', 1)]])[:-3]
        self.assert_code('FORMAT_INVALID', lambda: inspect(p))

    def test_unknown_array_encoding_is_rejected(self):
        p = bytearray(plaintext([[('K', '_a', 1)]])); at = p.index(b'keyInput') + 8; p[at] = 0x19
        self.assert_code('FORMAT_UNSUPPORTED', lambda: inspect(bytes(p)))

    def test_unknown_secondary_token_is_rejected(self):
        p = bytearray(plaintext([[('K', '_a', 1)]])); at = p.index(b'isSecondary') + 11; p[at] = 3
        self.assert_code('FORMAT_UNSUPPORTED', lambda: inspect(bytes(p)))

    def test_empty_output_is_rejected(self):
        self.assert_code('FORMAT_INVALID', lambda: inspect(plaintext([[('', '_a', 1)]])))

    def test_unknown_string_reference_is_rejected(self):
        p = bytearray(plaintext([[('K', '_a', 1), ('K', '_b', 1)]]))
        at = p.index(b'\x0d', p.index(b'keyInput') + 8); p[at + 1:at + 3] = b'\xff\x7f'
        self.assert_code('FORMAT_INVALID', lambda: inspect(bytes(p)))

    def test_unknown_name_reference_is_rejected(self):
        p = bytearray(plaintext([[('K', '_a', 1), ('P', '_b', 1)]]))
        at = p.index(b'\0\x14', p.index(b'isSecondary')) + 2
        p[at:at + 2] = b'\x80\0'
        self.assert_code('FORMAT_INVALID', lambda: inspect(bytes(p)))

    def test_long_array_count_and_secondary_raw_token(self):
        rows = [('K', '_same', 1)] * 33 + [('P', '_secondary', 2)]
        value = inspect(plaintext([rows]))
        self.assertEqual(value['context_counts'], [34])
        self.assertEqual(value['bindings'][-1]['secondary_raw_token'], 2)

    def test_semantic_diff_ignores_row_reorder_and_other_profile_bytes(self):
        before = inspect(plaintext([[('K', '_a', 1), ('P', '_b', 1)]]))
        after = inspect(plaintext([[('P', '_b', 1), ('K', '_a', 1)]]))
        diff = mod.diff_evidence(before, after)
        self.assertTrue(diff['binding_rows_identical'])
        self.assertFalse(diff['source_bytes_identical'])
        self.assertEqual(diff['added'], [])

    def test_diff_keeps_context_and_duplicate_counts(self):
        before = inspect(plaintext([[('K', '_a', 1), ('K', '_a', 1)], []]))
        after = inspect(plaintext([[('K', '_a', 1)], [('K', '_a', 1)]]))
        diff = mod.diff_evidence(before, after)
        self.assertFalse(diff['binding_rows_identical'])
        self.assertEqual(diff['removed'][0]['context_index'], 0)
        self.assertEqual(diff['added'][0]['context_index'], 1)

    def test_different_accounts_and_builds_require_reconciliation(self):
        value = inspect()
        other = inspect(identity=str(int(IDENTITY) + 1))
        self.assert_code('IDENTITY_MISMATCH', lambda: mod.diff_evidence(value, other))
        other = inspect(game_build='another-build')
        self.assert_code('BUILD_MISMATCH', lambda: mod.diff_evidence(value, other))

    def test_unknown_build_stays_unknown(self):
        value = inspect(game_build=None)
        self.assertEqual(mod.diff_evidence(value, value)['build_comparison'], 'unknown')

    def test_edited_evidence_is_not_reexported_as_observed(self):
        value = inspect(); value['bindings'][0]['output'] = 'Q'
        self.assert_code('EVIDENCE_CHANGED', lambda: mod.export_json(value))
        self.assert_code('EVIDENCE_CHANGED', lambda: mod.export_csv(value))

    def test_invalid_row_indexes_do_not_reach_csv(self):
        value = inspect(); value['bindings'][0]['row_index'] = '=1+1'
        self.assert_code('EVIDENCE_INVALID', lambda: mod.export_csv(value))
        value = inspect(); value['bindings'][1]['row_index'] = 0
        self.assert_code('EVIDENCE_INVALID', lambda: mod.export_csv(value))

    def test_non_ascii_identity_is_rejected_before_authentication(self):
        raw = wrap(plaintext([[('K', '_a', 1)]]))
        identity = ''.join(chr(0x660 + int(c)) for c in IDENTITY)
        self.assert_code('IDENTITY_REQUIRED', lambda: mod.inspect_snapshot(raw, identity, expected_sha256=hashlib.sha256(raw).hexdigest()))

    def test_exports_are_data_only_and_csv_formula_safe(self):
        value = inspect(plaintext([[('=', '+synthetic', 1)]]))
        text = mod.export_json(value)
        self.assertEqual(json.loads(text), value)
        rows = list(csv.reader(io.StringIO(mod.export_csv(value))))
        self.assertEqual(rows[1][2], "'+synthetic")
        self.assertEqual(rows[1][3], "'=")
        self.assertFalse(value['capabilities']['binary_game_write'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
