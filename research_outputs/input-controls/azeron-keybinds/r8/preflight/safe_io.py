"""Bounded local reads and new-directory reports. Python 3.9+, stdlib only.
No network, recursive disk search, native profile writes, or input capture.
All returned metadata omits absolute paths. Files must not traverse symlinks or
Windows reparse points. Local races are checked; no claim of adversarial FS isolation.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
import os
import stat
from pathlib import Path
from typing import Any, Tuple

MAX_FILE = 8_000_000
class ReviewError(ValueError):
    """Input needs inspection; errors are intentionally free of source path values."""

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def timestamp() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ReviewError('Duplicate JSON property; no last-value resolution is applied.')
        out[key] = value
    return out

def strict_json(raw: bytes, max_bytes: int = MAX_FILE) -> Any:
    if len(raw) > max_bytes:
        raise ReviewError('JSON exceeds the size bound.')
    try:
        obj = json.loads(raw.decode('utf-8-sig'), object_pairs_hook=no_duplicates,
                         parse_constant=lambda _: (_ for _ in ()).throw(ReviewError('Non-finite JSON number.')))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as e:
        raise ReviewError('Unsupported encoding, invalid JSON or excessive nesting.') from e
    stack = [(obj, 0)]; nodes = 0
    while stack:
        value, depth = stack.pop(); nodes += 1
        if nodes > 100_000 or depth > 48:
            raise ReviewError('JSON exceeds structure bound.')
        if isinstance(value, float) and not math.isfinite(value):
            raise ReviewError('Non-finite JSON number after numeric conversion.')
        if isinstance(value, dict): stack.extend((v, depth + 1) for v in value.values())
        elif isinstance(value, list): stack.extend((v, depth + 1) for v in value)
    return obj

def plain_path(path: Path) -> Path:
    path = Path(os.path.abspath(os.fspath(path)))
    for item in reversed((path,) + tuple(path.parents)):
        try: st = item.lstat()
        except OSError as e: raise ReviewError('An input or parent cannot be read; stop this read.') from e
        if stat.S_ISLNK(st.st_mode) or getattr(st, 'st_file_attributes', 0) & 0x400:
            raise ReviewError('Symlink/reparse path is not an approved regular-file source.')
    return path

def signature(st) -> tuple:
    return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)

def read_regular(path: Path, limit: int = MAX_FILE) -> Tuple[bytes, dict]:
    path = plain_path(Path(path))
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise ReviewError('Expected a bounded regular file.')
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NONBLOCK', 0)
        fd = os.open(str(path), flags)
        with os.fdopen(fd, 'rb') as f:
            opened = os.fstat(f.fileno())
            if signature(before) != signature(opened): raise ReviewError('Input identity changed before read.')
            raw = f.read(limit + 1)
            closed = os.fstat(f.fileno())
        after = path.lstat()
        if len(raw) > limit or signature(before) != signature(closed) or signature(before) != signature(after):
            raise ReviewError('Input changed during read; inspect before any recollection.')
        # Recheck parents after the bounded read. This is not a hostile-filesystem guarantee.
        plain_path(path)
    except OSError as e:
        raise ReviewError('Input became inaccessible; no automatic retry.') from e
    return raw, {'basename': path.name, 'bytes': len(raw), 'sha256': sha(raw),
                 'mtime_utc': dt.datetime.fromtimestamp(before.st_mtime, dt.timezone.utc).isoformat()}

def new_output(path: Path) -> Path:
    path = Path(os.path.abspath(os.fspath(path)))
    plain_path(path.parent)
    if path.exists() or path.is_symlink(): raise ReviewError('Output must be a new directory.')
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    return path

def write_report(folder: Path, name: str, payload: Any) -> Path:
    if Path(name).name != name: raise ReviewError('Report name must be a basename.')
    target = folder / name
    with target.open('x', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    return target
