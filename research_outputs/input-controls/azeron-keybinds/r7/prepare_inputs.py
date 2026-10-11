#!/usr/bin/env python3
"""Extract exact, bounded R7 analysis inputs. No executable is run or installed."""
import argparse, hashlib, stat, zipfile
from pathlib import Path, PurePosixPath

EXPECTED = '8d1977ee2aa0e4dccf8e9ed0636bfb91e36dd52dc1fcb4f8a813801b3bdc9205'
WANTED = {
    'inputs/r4/CORPUS_AUDIT_R4.json': 'CORPUS_AUDIT_R4.json',
    'research/DESIGN_R6.json': 'DESIGN_R6.json',
    'research/audit_r6_access.py': 'audit_r6_access.py',
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raw = a.archive.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('R6 archive hash mismatch; stop and reconcile the source revision.')
    if a.output.exists():
        raise FileExistsError('Use a new input directory; existing work is not overwritten.')
    with zipfile.ZipFile(a.archive) as z:
        names = z.namelist()
        if len(set(names)) != len(names):
            raise ValueError('Duplicate archive paths.')
        payloads = {}
        for source, target in WANTED.items():
            info = z.getinfo(source)
            path = PurePosixPath(source)
            if path.is_absolute() or '..' in path.parts or stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError('Unsafe archive entry.')
            if info.file_size > 20_000_000:
                raise ValueError('Unexpectedly large input.')
            payloads[target] = z.read(info)
    a.output.mkdir(parents=True, exist_ok=False)
    for name, data in payloads.items():
        (a.output / name).write_bytes(data)
        print(name, len(data), hashlib.sha256(data).hexdigest())

if __name__ == '__main__':
    main()
