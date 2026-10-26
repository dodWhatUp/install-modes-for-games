"""Read-only DOOM The Dark Ages Steam binding evidence from a pinned snapshot.

This module accepts bytes, never opens a path, writes a game file, registers a
mutation adapter, launches an app or changes a mapper. It deliberately does not
extend game_keybind_ops' text-only adapter seam to binary saves.

Envelope references (read, not executed):
https://github.com/mi5hmash/idSaveDataResigner/blob/6d06b734ff81196d1d2acecea753148eeb782764/idSaveDataResignerCore/Helpers/IdDeencryption.cs
https://github.com/GoobyCorp/DOOM-TDA-Utilities/blob/d1dcd9c4b9046fc6ee30b102bd88853daf95fb41/DOOM_TDA_Save.py

The bounded keyInput grammar was independently checked against copied native UI
before/after snapshots. It is not the upstream incomplete whole-profile decoder.
AES-GCM authentication does not establish the internal profile checksum or game
acceptance. No binary writer is available until both have been validated.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import importlib.util
import io
import json
import re
import struct

VERSION = '0.1.0'
MAX_BYTES = 2 * 1024 * 1024
MAX_CONTEXTS = 32
MAX_ROWS = 4096
MAX_REFERENCES = MAX_ROWS * 5
MAGIC_VERSION = bytes.fromhex('a90d8daa00000003')
EVIDENCE_KIND = 'doom_binary_binding_evidence'
SCHEMA_VERSION = 1
STEAM_ID64_BASE = 76561197960265728


class InspectError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _require(condition, code, message):
    if not condition:
        raise InspectError(code, message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _fingerprint(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
    return _sha(raw)


def capabilities() -> dict:
    """Suitable for an existing workspace's explicit capability/status view."""
    try:
        envelope_available = importlib.util.find_spec('cryptography') is not None
    except (ImportError, ValueError):
        envelope_available = False
    return {
        'kind': 'doom_binary_binding_capabilities', 'schema_version': 1,
        'component_version': VERSION,
        'inspect_pinned_snapshot': envelope_available,
        'diff_evidence': True, 'export_json': True, 'export_csv': True,
        'binary_game_write': False, 'whole_profile_switch': False,
        'gameplay_verified': False, 'internal_checksum_verified': False,
        'write_block_code': 'BINARY_WRITE_UNVERIFIED',
        'reason': 'Internal profile checksum and native changed-file acceptance are unverified.',
        'input_role': 'Steam profile.bin only; no game-save discovery or automatic file access.',
    }


class _KeyInputReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.names = {}
        self.strings = {}
        self.references = 0

    def take(self, count):
        _require(0 <= count <= len(self.data) - self.pos,
                 'FORMAT_INVALID', 'Truncated binding field.')
        start = self.pos
        self.pos += count
        return self.data[start:self.pos]

    def array_count(self):
        tag = self.take(1)[0]
        if 0x40 <= tag <= 0x5f:
            return tag - 0x40
        _require(tag == 0x11, 'FORMAT_UNSUPPORTED', 'Unreviewed binding-array encoding.')
        return self.take(1)[0]

    def _reference(self):
        self.references += 1
        _require(self.references <= MAX_REFERENCES, 'SIZE_LIMIT', 'Too many binding references.')

    def name(self):
        start = self.pos
        tag = self.take(1)[0]
        if 0 < tag < 0x80:
            _require(tag <= 31, 'FORMAT_UNSUPPORTED', 'Unreviewed binding property name.')
            value = self.take(tag).decode('ascii')
            self.names[start] = value
            return value
        self.pos = start
        delta = struct.unpack('>h', self.take(2))[0]
        target = start + delta
        _require(delta < 0 and target in self.names,
                 'FORMAT_INVALID', 'Unknown binding property reference.')
        self._reference()
        return self.names[target]

    def string(self):
        start = self.pos
        tag = self.take(1)[0]
        if 0x20 <= tag <= 0x3f:
            value = self.take(tag - 0x20).decode('ascii')
            _require(value and all(32 <= ord(c) < 127 for c in value),
                     'FORMAT_INVALID', 'Invalid binding token.')
            self.strings[start] = value
            return value
        _require(tag == 0x0d, 'FORMAT_UNSUPPORTED', 'Unreviewed binding-string encoding.')
        # Value references use a wrapped unsigned 16-bit backward distance from
        # the end of the reference. They must resolve inside the reviewed array.
        delta = int.from_bytes(self.take(2), 'little') - 65536
        target = self.pos + delta
        _require(target in self.strings, 'FORMAT_INVALID', 'Unknown binding string reference.')
        self._reference()
        return self.strings[target]

    def read(self):
        marker = b'\x08keyInput'
        _require(self.data.count(marker) == 1, 'FORMAT_INVALID', 'Expected one unique keyInput array.')
        self.pos = self.data.index(marker) + len(marker)
        count = self.array_count()
        _require(0 < count <= MAX_CONTEXTS, 'SIZE_LIMIT', 'Unreviewed binding-context count.')
        rows = []
        context_counts = []
        for context in range(count):
            row_count = self.array_count()
            _require(len(rows) + row_count <= MAX_ROWS, 'SIZE_LIMIT', 'Too many bindings.')
            context_counts.append(row_count)
            for row_index in range(row_count):
                _require(self.take(1) == b'\x14', 'FORMAT_INVALID', 'Expected binding object.')
                _require(self.name() == 'key', 'FORMAT_INVALID', 'Expected key property.')
                output = self.string()
                _require(self.name() == 'binding', 'FORMAT_INVALID', 'Expected command property.')
                command = self.string()
                _require(self.name() == 'isSecondary', 'FORMAT_INVALID', 'Expected secondary property.')
                secondary = self.take(1)[0]
                _require(secondary in (1, 2), 'FORMAT_UNSUPPORTED', 'Unreviewed secondary token.')
                _require(self.take(1) == b'\0', 'FORMAT_INVALID', 'Expected binding-object terminator.')
                family = 'controller' if output.startswith('JOY') else (
                    'mouse' if output.startswith(('MOUSE', 'MWHEEL')) else 'keyboard')
                rows.append({'context_index': context, 'row_index': row_index,
                             'output': output, 'command': command,
                             'secondary_raw_token': secondary, 'input_family': family})
        return rows, context_counts, self.references


def inspect_snapshot(raw: bytes, identity: str, *, expected_sha256: str,
                     filename: str = 'profile.bin', game_build: str | None = None) -> dict:
    """Inspect explicit, locally selected snapshot bytes and return binding data.

    identity is the owning SteamID64 from the existing local source owner; it is
    used only for authentication and is never returned. game_build is caller
    supplied provenance, not a build detected from the profile. Unknown remains
    unknown. The expected hash must come from the selected source owner.
    """
    _require(type(raw) is bytes and 40 <= len(raw) <= MAX_BYTES,
             'SIZE_LIMIT', 'Expected a bounded encrypted profile snapshot.')
    _require(filename == 'profile.bin', 'FILE_ROLE_UNSUPPORTED', 'Only the selected Steam profile binding role is reviewed.')
    _require(type(expected_sha256) is str and re.fullmatch(r'[0-9a-f]{64}', expected_sha256),
             'SOURCE_PIN_REQUIRED', 'A complete lowercase source SHA-256 is required.')
    _require(_sha(raw) == expected_sha256, 'SOURCE_CHANGED', 'Selected profile bytes changed; refresh the source.')
    _require(type(identity) is str and re.fullmatch(r'[0-9]{17}', identity)
             and STEAM_ID64_BASE <= int(identity) <= STEAM_ID64_BASE + 0xffffffff,
             'IDENTITY_REQUIRED', 'Use the owning local SteamID64; no identity guessing.')
    _require(game_build is None or (type(game_build) is str and re.fullmatch(r'[A-Za-z0-9._-]{1,80}', game_build)),
             'PROVENANCE_INVALID', 'Invalid declared game-build provenance.')
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.exceptions import InvalidTag
    except ImportError as exc:
        raise InspectError('ENVELOPE_READER_UNAVAILABLE', 'The existing runtime needs its reviewed cryptography dependency.') from exc
    aad = (identity + 'MANCUBUS' + filename).encode('ascii')
    try:
        plain = AESGCM(hashlib.sha256(aad).digest()[:16]).decrypt(raw[:12], raw[12:], aad)
    except InvalidTag as exc:
        raise InspectError('AUTHENTICATION_FAILED', 'Snapshot identity, filename or authenticated bytes do not match.') from exc
    _require(plain[:8] == MAGIC_VERSION, 'FORMAT_UNSUPPORTED', 'Unreviewed profile magic/version.')
    try:
        rows, counts, references = _KeyInputReader(plain).read()
    except (UnicodeError, struct.error, IndexError) as exc:
        raise InspectError('FORMAT_INVALID', 'Profile binding data is malformed.') from exc
    matrix = sorted((r['context_index'], r['command'], r['output'], r['secondary_raw_token']) for r in rows)
    return {
        'kind': EVIDENCE_KIND, 'schema_version': SCHEMA_VERSION,
        'component_version': VERSION,
        'game_id': 'doom-the-dark-ages',
        'source': {'sha256': expected_sha256, 'bytes': len(raw),
                   'plaintext_sha256': _sha(plain), 'role': filename,
                   'account_scope': _sha(('steam:' + identity).encode('ascii')),
                   'declared_game_build': game_build,
                   'envelope_authenticated': True, 'profile_format': 3,
                   'internal_checksum_verified': False},
        'binding_revision': _fingerprint(matrix),
        'context_counts': counts, 'binding_count': len(rows),
        'validated_reference_count': references, 'bindings': rows,
        'verification': {'saved_binding_evidence': True, 'gameplay': False,
                         'native_prompt_readback': False,
                         'secondary_token_meaning': 'raw token retained; no enum interpretation'},
        'capabilities': capabilities(),
    }


def _validate_evidence(value):
    _require(type(value) is dict and value.get('kind') == EVIDENCE_KIND
             and value.get('schema_version') == SCHEMA_VERSION
             and value.get('game_id') == 'doom-the-dark-ages',
             'EVIDENCE_INVALID', 'Expected reviewed binding evidence schema 1.')
    rows = value.get('bindings')
    _require(type(rows) is list and len(rows) <= MAX_ROWS,
             'EVIDENCE_INVALID', 'Invalid binding evidence rows.')
    counts = value.get('context_counts')
    _require(type(counts) is list and 0 < len(counts) <= MAX_CONTEXTS
             and all(type(n) is int and 0 <= n <= 255 for n in counts)
             and sum(counts) == len(rows) and value.get('binding_count') == len(rows),
             'EVIDENCE_INVALID', 'Invalid binding-context inventory.')
    for row in rows:
        _require(type(row) is dict and type(row.get('context_index')) is int
                 and 0 <= row['context_index'] < MAX_CONTEXTS
                 and type(row.get('row_index')) is int and 0 <= row['row_index'] < 255
                 and type(row.get('command')) is str and 0 < len(row['command']) <= 31
                 and type(row.get('output')) is str and 0 < len(row['output']) <= 31
                 and type(row.get('secondary_raw_token')) is int
                 and row['secondary_raw_token'] in (1, 2)
                 and all(32 <= ord(c) < 127 for c in row['command'] + row['output']),
                 'EVIDENCE_INVALID', 'Invalid binding evidence token.')
    _require([sum(r['context_index'] == i for r in rows) for i in range(len(counts))] == counts,
             'EVIDENCE_INVALID', 'Binding rows do not match their context inventory.')
    _require(all(sorted(r['row_index'] for r in rows if r['context_index'] == i)
                 == list(range(count)) for i, count in enumerate(counts)),
             'EVIDENCE_INVALID', 'Binding row indexes are incomplete or ambiguous.')
    source = value.get('source')
    _require(type(source) is dict and source.get('envelope_authenticated') is True
             and type(source.get('sha256')) is str and re.fullmatch(r'[0-9a-f]{64}', source['sha256'])
             and type(source.get('account_scope')) is str and re.fullmatch(r'[0-9a-f]{64}', source['account_scope'])
             and source.get('role') == 'profile.bin',
             'EVIDENCE_INVALID', 'Invalid source provenance.')
    matrix = sorted((r['context_index'], r['command'], r['output'], r['secondary_raw_token']) for r in rows)
    _require(value.get('binding_revision') == _fingerprint(matrix),
             'EVIDENCE_CHANGED', 'Binding evidence was edited; inspect the pinned snapshot again.')
    return rows


def diff_evidence(before: dict, after: dict) -> dict:
    """Compare semantic rows, preserving intentional duplicates and context."""
    a = _validate_evidence(before)
    b = _validate_evidence(after)
    _require(before['source']['account_scope'] == after['source']['account_scope'],
             'IDENTITY_MISMATCH', 'Do not combine different owning-account evidence.')
    ba = before['source'].get('declared_game_build')
    bb = after['source'].get('declared_game_build')
    _require(not (ba and bb and ba != bb), 'BUILD_MISMATCH', 'Different declared game builds require reconciliation.')
    def counter(rows):
        return Counter((r['context_index'], r['command'], r['output'], r['secondary_raw_token']) for r in rows)
    ac, bc = counter(a), counter(b)
    def records(counter):
        return [{'context_index': c, 'command': command, 'output': output,
                 'secondary_raw_token': secondary}
                for c, command, output, secondary in sorted(counter.elements())]
    return {'kind': 'doom_binary_binding_diff', 'schema_version': 1,
            'before_source_sha256': before['source']['sha256'],
            'after_source_sha256': after['source']['sha256'],
            'source_bytes_identical': before['source']['sha256'] == after['source']['sha256'],
            'binding_rows_identical': ac == bc,
            'build_comparison': 'same_declared_build' if ba and bb else 'unknown',
            'removed': records(ac - bc), 'added': records(bc - ac),
            'gameplay_verified': False, 'binary_write_available': False}


def export_json(evidence: dict) -> str:
    """Data-only interchange; never an importable save or authority token."""
    _validate_evidence(evidence)
    return json.dumps(evidence, indent=2, ensure_ascii=False, sort_keys=True) + '\n'


def export_csv(evidence: dict) -> str:
    rows = _validate_evidence(evidence)
    output = io.StringIO(newline='')
    writer = csv.writer(output)
    writer.writerow(['Context index', 'Row index', 'Action command', 'Output', 'Secondary raw token'])
    def safe_text(text):
        return "'" + text if text.startswith(('=', '+', '-', '@')) else text
    for row in rows:
        writer.writerow([row['context_index'], row.get('row_index', ''),
                         safe_text(row['command']), safe_text(row['output']), row['secondary_raw_token']])
    return output.getvalue()


def prepare_binary_changes(*args, **kwargs):
    """No approval flag or external JSON can enable an unvalidated writer."""
    raise InspectError('BINARY_WRITE_UNVERIFIED',
                       'Binary binding changes are unavailable: internal checksum and native changed-file acceptance remain unverified.')
