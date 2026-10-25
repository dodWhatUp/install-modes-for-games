"""Documented per-mod TOML preferences, edited only after an explicit Save."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tomllib
import uuid
try:
    from .switcher import atomic_bytes, atomic_json, checked
except ImportError:
    from switcher import atomic_bytes, atomic_json, checked

KEYS = tuple(f'F{i}' for i in range(1, 16)) + (
    'Home', 'End', 'Insert', 'Delete', 'PageUp', 'PageDown', 'Pause',
    'BackQuote', 'Tab', 'Escape', 'None',
) + tuple(chr(i) for i in range(65, 91)) + tuple(f'Alpha{i}' for i in range(10)) + tuple(f'Keypad{i}' for i in range(10))

SCHEMAS = {
    'build-liberator': {'section': 'BuildLiberator', 'fields': (
        {'key': 'FreelySwitchRunes', 'label': 'Free rune changes; keep equipment', 'type': 'bool', 'default': True},
        {'key': 'FreelySwitchGems', 'label': 'Free gem changes; keep equipment', 'type': 'bool', 'default': True},
    )},
    'rune-details': {'section': 'RuneDetails', 'fields': (
        {'key': 'Enabled', 'label': 'Show additional rune information', 'type': 'bool', 'default': True},
        {'key': 'Mode', 'label': 'Detail level', 'type': 'enum', 'choices': ('Off', 'Brief', 'Detailed'), 'default': 'Brief'},
        {'key': 'AddSettingsRows', 'label': 'Show detail selector in the game menu', 'type': 'bool', 'default': True},
    )},
    'wicked-menu': {'section': 'WickedMenu', 'fields': (
        {'key': 'MenuHotkey', 'label': 'Open menu key', 'type': 'enum', 'choices': KEYS, 'default': 'F1'},
    )},
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest() if raw is not None else None


def validate(field, value, *, existing=False):
    if field['type'] == 'bool' and type(value) is not bool:
        raise ValueError(field['label'] + ' must be true or false.')
    if field['type'] == 'enum':
        if type(value) is not str or (value not in field['choices'] and not (existing and re.fullmatch(r'[A-Za-z0-9_]{1,60}', value))):
            raise ValueError('Choose a supported value for ' + field['label'] + '.')
    return value


def rewrite(raw, section, changes):
    """Keep unrelated lines and comments byte-for-byte in standard loader TOML."""
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    if '\"\"\"' in text or "'''" in text:
        raise ValueError('This file uses multiline TOML. Edit it through the mod or its configuration file instead.')
    newline = '\r\n' if '\r\n' in text else '\n'
    lines = text.splitlines(keepends=True)
    header = re.compile(r'^\s*\[([^\[\]]+)\]\s*(?:#.*)?$')
    active = None
    found_section = False
    remaining = dict(changes)
    out = []

    def add_missing():
        if remaining and out and not out[-1].endswith(('\n', '\r')):
            out[-1] += newline
        for key, value in remaining.items():
            out.append(key + ' = ' + json.dumps(value, ensure_ascii=True) + newline)
        remaining.clear()

    for line in lines:
        plain = line.rstrip('\r\n')
        match = header.fullmatch(plain)
        if match:
            if active == section:
                add_missing()
            active = match.group(1).strip()
            found_section |= active == section
        elif active == section:
            key = re.match(r'^(\s*)([A-Za-z0-9_]+)(\s*=\s*)(.*)$', plain)
            if key and key.group(2) in remaining:
                name = key.group(2)
                # Known fields are booleans or simple enum names; no # inside them.
                comment = re.search(r'(\s+#.*)$', key.group(4))
                suffix = comment.group(1) if comment else ''
                ending = line[len(plain):]
                line = key.group(1) + name + key.group(3) + json.dumps(remaining.pop(name), ensure_ascii=True) + suffix + ending
        out.append(line)
    if active == section:
        add_missing()
    if not found_section:
        if out and not out[-1].endswith(('\n', '\r')):
            out[-1] += newline
        if out and out[-1].strip():
            out.append(newline)
        out.append('[' + section + ']' + newline)
        add_missing()
    if remaining:
        raise ValueError('The target configuration section could not be updated safely.')
    result = ('\ufeff' if bom else '') + ''.join(out)
    encoded = result.encode('utf-8')
    parsed = tomllib.loads(result.lstrip('\ufeff'))
    if any(parsed[section].get(key) != value for key, value in changes.items()):
        raise ValueError('Configuration preview did not match the requested options.')
    return encoded


class ModOptions:
    def __init__(self, service):
        self.service = service
        self.path = checked(service.game, 'UserData/MelonPreferences.cfg')

    def read(self, ident):
        schema = SCHEMAS.get(ident, {'section': '', 'fields': ()})
        if self.path.exists() and not self.path.is_file():
            raise ValueError('The mod settings path is not a file.')
        if self.path.is_file() and self.path.stat().st_size > 1048576:
            raise ValueError('The mod settings file exceeds the supported size.')
        raw = self.path.read_bytes() if self.path.is_file() else None
        doc = tomllib.loads(raw.decode('utf-8-sig')) if raw is not None else {}
        section = doc.get(schema['section'], {})
        if not isinstance(section, dict):
            raise ValueError('The mod settings section is not a table.')
        values = {field['key']: validate(field, section.get(field['key'], field['default']), existing=True) for field in schema['fields']}
        return {'id': ident, 'values': values, 'revision': digest(raw), 'exists': raw is not None}

    def preview_many(self, changes, revision):
        if type(changes) is not dict or set(changes) - SCHEMAS.keys():
            raise ValueError('Only documented mod preferences may be previewed.')
        current = self.read('wicked-menu')
        if current['revision'] != revision:
            raise RuntimeError('The settings changed since preview. Refresh and review again.')
        before = self.path.read_bytes() if self.path.is_file() else None
        after = before
        for ident, wanted in changes.items():
            schema = SCHEMAS[ident]
            fields = {f['key']: f for f in schema['fields']}
            if type(wanted) is not dict or set(wanted) - fields.keys():
                raise ValueError('Only documented options for this mod may be previewed.')
            saved = self.read(ident)['values']
            for key, value in wanted.items():
                validate(fields[key], value)
            delta = {k: v for k, v in wanted.items() if v != saved[k]}
            if delta:
                after = rewrite(after or b'', schema['section'], delta)
        return {'before': before, 'after': after}

    def save(self, ident, changes, revision):
        if ident not in SCHEMAS:
            raise ValueError('This component has no reviewed editable options.')
        schema = SCHEMAS[ident]
        fields = {f['key']: f for f in schema['fields']}
        if type(changes) is not dict or set(changes) - fields.keys():
            raise ValueError('Only documented options for this mod may be saved.')
        for key, value in changes.items():
            validate(fields[key], value)
        with self.service.lease():
            self.service._closed()
            current = self.read(ident)
            if current['revision'] != revision:
                raise RuntimeError('The settings changed since this window was opened. Reload before saving.')
            changes = {key: value for key, value in changes.items() if value != current['values'][key]}
            if not changes:
                return {'changed': 0, 'snapshot': current, 'recovery': None}
            if not self.service.inspect()['game_build_matches']:
                raise RuntimeError('The game changed. Review mod compatibility before changing options.')
            before = self.path.read_bytes() if self.path.is_file() else None
            after = rewrite(before or b'', schema['section'], changes)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
            recovery = self.service.workspace / 'recovery' / ('options-' + stamp)
            recovery.mkdir(parents=True)
            if before is not None:
                atomic_bytes(recovery / 'MelonPreferences.cfg', before)
            transaction = {'schema': 1, 'kind': 'mod-options', 'mod': ident, 'keys': list(changes),
                'before_sha256': digest(before), 'after_sha256': digest(after), 'status': 'prepared'}
            atomic_json(recovery / 'transaction.json', transaction)
            self.service._closed()
            if digest(self.path.read_bytes() if self.path.is_file() else None) != revision:
                raise RuntimeError('The settings changed during preparation; nothing was saved.')
            try:
                atomic_bytes(self.path, after)
                if self.path.read_bytes() != after:
                    raise RuntimeError('Saved options did not pass readback.')
                saved = self.read(ident)
                transaction['status'] = 'applied'
                atomic_json(recovery / 'transaction.json', transaction)
                return {'changed': len(changes), 'snapshot': saved, 'recovery': str(recovery)}
            except BaseException:
                if before is None:
                    self.path.unlink(missing_ok=True)
                else:
                    atomic_bytes(self.path, before)
                transaction['status'] = 'rolled-back'
                atomic_json(recovery / 'transaction.json', transaction)
                raise
