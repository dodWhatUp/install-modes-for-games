"""Hash-owned, nonresident file switching; never launches or controls a game."""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def checked(root, relative):
    root = Path(root).resolve(strict=True)
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ValueError('Expected a relative, forward-slash file path')
    bits = PurePosixPath(relative).parts
    if not bits or relative.startswith('/') or any(x in ('', '.', '..') for x in bits):
        raise ValueError('Unsafe file path')
    path = root.joinpath(*bits)
    cursor = path
    while cursor != root:
        if cursor.is_symlink() or (hasattr(cursor, 'is_junction') and cursor.is_junction()):
            raise ValueError('Linked paths are not managed')
        cursor = cursor.parent
    if not path.resolve().is_relative_to(root):
        raise ValueError('File leaves its managed root')
    return path


def atomic_bytes(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.wicked-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_json(path, value):
    atomic_bytes(path, (json.dumps(value, indent=2) + '\n').encode('utf-8'))


def game_processes():
    if os.name != 'nt':
        return []
    # Read-only process inventory, no input or game termination.
    command = "Get-CimInstance Win32_Process | Where-Object {$_.Name -ieq 'NoRestForTheWicked.exe'} | Select-Object ProcessId,ExecutablePath | ConvertTo-Json -Compress"
    completed = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
        capture_output=True, text=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    if completed.returncode:
        raise RuntimeError('Cannot verify that the game is closed')
    text = completed.stdout.strip()
    if not text:
        return []
    result = json.loads(text)
    return result if isinstance(result, list) else [result]


class Switcher:
    def __init__(self, workspace, process_check=game_processes):
        self.workspace = Path(workspace).resolve(strict=True)
        self.manifest_path = self.workspace / 'deployment.json'
        self.manifest = json.loads(self.manifest_path.read_text(encoding='utf-8-sig'))
        if self.manifest.get('schema') != 1:
            raise ValueError('Unsupported deployment manifest')
        self.game = Path(self.manifest['game_root']).resolve(strict=True)
        self.process_check = process_check
        self.components = self.manifest['components']
        ids = [x['id'] for x in self.components]
        if len(ids) != len(set(ids)) or 'loader' not in ids:
            raise ValueError('Invalid component identities')
        seen = set()
        for component in self.components:
            for item in component['files']:
                checked(self.game, item['target'])
                checked(self.workspace, item['source'])
                if item['target'].casefold() in seen:
                    raise ValueError('Two components own the same file')
                seen.add(item['target'].casefold())

    def _closed(self):
        if self.process_check():
            raise RuntimeError('Save and exit No Rest for the Wicked before applying changes.')

    def inspect(self):
        rows = []
        fingerprint = []
        for c in self.components:
            source_ok = bool(c['files'])
            present = 0
            conflicts = []
            for f in c['files']:
                target = checked(self.game, f['target'])
                source = checked(self.workspace, f['source'])
                source_ok &= source.is_file() and sha(source) == f['sha256']
                found = sha(target) if target.is_file() else ('DIRECTORY' if target.exists() else None)
                fingerprint.append([f['target'], found])
                if found is not None:
                    present += 1
                    if found != f['sha256']:
                        conflicts.append(f['target'])
            state = 'conflict' if conflicts else ('on' if c['files'] and present == len(c['files']) else ('partial' if present else 'off'))
            rows.append({'id': c['id'], 'name': c['name'], 'state': state,
                'available': bool(source_ok), 'conflicts': conflicts,
                'recommended': c.get('recommended', False), 'note': c.get('note', ''), 'url': c['url']})
        fingerprint.append(['manifest', sha(self.manifest_path)])
        exe = checked(self.game, 'NoRestForTheWicked.exe')
        marker_matches = sha(exe) == self.manifest['game_exe_sha256']
        fingerprint.append(['game_exe', sha(exe)])
        for relative, expected in self.manifest.get('game_markers', {}).items():
            path = checked(self.game, relative)
            actual = sha(path) if path.is_file() else None
            marker_matches &= actual == expected
            fingerprint.append([relative, actual])
        return {'components': rows, 'revision': hashlib.sha256(json.dumps(fingerprint, sort_keys=True).encode()).hexdigest(),
            'game_build_matches': bool(marker_matches)}

    @contextlib.contextmanager
    def lease(self):
        lock = self.workspace / 'switch.lock'
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            yield
        finally:
            lock.unlink(missing_ok=True)

    def apply(self, desired, revision):
        with self.lease():
            return self._apply_locked(desired, revision)

    def apply_with_options(self, desired, revision, changes, options_revision):
        try:
            from .mod_options import ModOptions
        except ImportError:
            from mod_options import ModOptions
        with self.lease():
            self._closed()
            preferences = ModOptions(self).preview_many(changes, options_revision)
            return self._apply_locked(desired, revision, preferences)

    def _apply_locked(self, desired, revision, preferences=None):
        self._closed()
        state = self.inspect()
        if state['revision'] != revision:
            raise RuntimeError('Files changed since Refresh. Refresh and review again.')
        if not state['game_build_matches'] and any(desired.values()):
            raise RuntimeError('The game executable changed. Review compatibility before applying mods.')
        ids = {c['id'] for c in self.components}
        if set(desired) != ids or any(type(v) is not bool for v in desired.values()):
            raise ValueError('Expected one on/off selection for every managed component')
        if any(r['state'] in ('partial', 'conflict') for r in state['components']):
            raise RuntimeError('A managed file is modified or incomplete. Inspect recovery before continuing.')
        if any(desired[r['id']] and not r['available'] for r in state['components']):
            raise RuntimeError('A selected component has not been downloaded and prepared.')
        if any(v for k, v in desired.items() if k != 'loader') and not desired['loader']:
            raise ValueError('Selected gameplay mods require the MelonLoader switch to be on.')
        if desired['loader']:
            for item in self.manifest.get('loader_support', []):
                path = checked(self.game, item['target'])
                if not path.is_file() or sha(path) != item['sha256']:
                    raise RuntimeError('Loader setup is missing or changed: ' + item['target'])
        plan = []
        for c in self.components:
            for item in c['files']:
                target = checked(self.game, item['target'])
                before = target.read_bytes() if target.is_file() else None
                after = checked(self.workspace, item['source']).read_bytes() if desired[c['id']] else None
                if before != after:
                    plan.append((item, target, before, after))
        if preferences and preferences['before'] != preferences['after']:
            if not state['game_build_matches']:
                raise RuntimeError('The game changed. Review compatibility before changing options.')
            target = checked(self.game, 'UserData/MelonPreferences.cfg')
            current = target.read_bytes() if target.is_file() else None
            if current != preferences['before']:
                raise RuntimeError('The settings changed since preview; refresh and review again.')
            plan.append(({'target': 'UserData/MelonPreferences.cfg'}, target,
                         preferences['before'], preferences['after']))
        if not plan:
            return {'changed': 0, 'state': state, 'recovery': None}
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        recovery = self.workspace / 'recovery' / stamp
        recovery.mkdir(parents=True)
        originals = []
        for item, target, before, after in plan:
            relative = item['target']
            if before is not None:
                original = checked(recovery, relative)
                atomic_bytes(original, before)
            originals.append({'target': relative, 'before_sha256': hashlib.sha256(before).hexdigest() if before is not None else None,
                'after_sha256': hashlib.sha256(after).hexdigest() if after is not None else None})
        atomic_json(recovery / 'transaction.json', {'schema': 1, 'status': 'prepared', 'files': originals, 'desired': desired})
        written = []
        try:
            self._closed()
            if self.inspect()['revision'] != revision:
                raise RuntimeError('Files changed during preparation; no changes applied.')
            # The proxy goes on last, off first. Every change is reversible.
            plan.sort(key=lambda row: (0 if row[0]['target'] == 'version.dll' and row[3] is None else
                2 if row[0]['target'] == 'version.dll' else 1))
            for item, target, before, after in plan:
                self._closed()
                current = target.read_bytes() if target.is_file() else None
                if current != before:
                    raise RuntimeError('A file changed during Apply: ' + item['target'])
                if after is None:
                    target.unlink()
                else:
                    atomic_bytes(target, after)
                written.append((target, before, after))
                actual = target.read_bytes() if target.is_file() else None
                if actual != after:
                    raise RuntimeError('Readback failed: ' + item['target'])
            final = self.inspect()
            for row in final['components']:
                if (row['state'] == 'on') != desired[row['id']]:
                    raise RuntimeError('Final state differs from selection: ' + row['name'])
            receipt = {'schema': 1, 'status': 'applied', 'files': originals, 'desired': desired,
                'revision': final['revision'], 'runtime_verified': False}
            atomic_json(recovery / 'transaction.json', receipt)
            atomic_json(self.workspace / 'last-applied.json', receipt)
            return {'changed': len(plan), 'state': final, 'recovery': str(recovery)}
        except BaseException:
            pending = []
            for target, before, after in reversed(written):
                try:
                    self._closed()
                    actual = target.read_bytes() if target.is_file() else None
                    if actual != after:
                        raise RuntimeError('An external writer changed the recovery target.')
                    if before is None:
                        target.unlink(missing_ok=True)
                    else:
                        atomic_bytes(target, before)
                except Exception:
                    pending.append(target.relative_to(self.game).as_posix())
            atomic_json(recovery / 'transaction.json', {'schema': 1,
                'status': 'recovery-required' if pending else 'rolled-back',
                'files': originals, 'pending': pending})
            if pending:
                raise RuntimeError('Recovery requires local review. A changed file or running game was preserved.')
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', required=True)
    parser.add_argument('--mode', choices=['status', 'recommended', 'off'], default='status')
    args = parser.parse_args()
    service = Switcher(args.workspace)
    state = service.inspect()
    if args.mode != 'status':
        desired = {r['id']: bool(args.mode == 'recommended' and (r['recommended'] or r['id'] == 'loader')) for r in state['components']}
        state = service.apply(desired, state['revision'])
    print(json.dumps(state, indent=2))


if __name__ == '__main__':
    main()
