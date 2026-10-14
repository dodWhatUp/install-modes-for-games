"""Shared limits, safe paths, immutable writes and cooperative local locks."""
from __future__ import annotations
import hashlib
import json
import os
import re
import stat
import time
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

class ModError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message
    def record(self) -> dict:
        return {"status": self.code, "message": self.message}

def require(ok: bool, code: str, message: str) -> None:
    if not ok:
        raise ModError(code, message)

def slug(value: str) -> str:
    require(isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}", value)),
            "INVALID_ID", "Identifiers must be short ASCII names without path separators.")
    require(value not in (".", "..") and not value.endswith("."), "INVALID_ID", "Invalid identifier.")
    safe_relative(value)
    return value

def safe_relative(value: str) -> PurePosixPath:
    require(isinstance(value, str) and value and "\\" not in value,
            "UNSAFE_PATH", "Backslashes or empty archive paths are not accepted.")
    require(not value.startswith("/") and not any(ord(c) < 32 for c in value),
            "UNSAFE_PATH", "Absolute or control-character paths are not accepted.")
    raw = value.rstrip("/").split("/")
    for part in raw:
        require(part not in ("", ".", "..") and part == part.rstrip(" ."),
                "UNSAFE_PATH", "Dot, empty, or Windows-aliased paths are not accepted.")
        require(not any(c in part for c in ':<>"|?*'), "UNSAFE_PATH", "Invalid Windows filename.")
        base = part.split(".")[0].upper()
        require(base not in {"CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$"}
                and not re.fullmatch(r"(?:COM|LPT)[0-9¹²³]", base),
                "UNSAFE_PATH", "Windows device names are not accepted.")
    require(len(value) <= 220, "UNSAFE_PATH", "Archive path is too long for this preview.")
    return PurePosixPath(*raw)

def no_links(path: Path) -> Path:
    path = Path(os.path.abspath(os.path.expanduser(str(path))))
    for p in (path, *path.parents):
        if p.exists() or p.is_symlink():
            st = p.lstat()
            require(not stat.S_ISLNK(st.st_mode) and not getattr(st, "st_file_attributes", 0) & 0x400,
                    "LINK_BLOCKED", "Symlinks and Windows reparse points are not supported here.")
    return path

def contained(root: Path, relative: str) -> Path:
    rel = safe_relative(relative)
    root = no_links(root)
    path = no_links(root.joinpath(*rel.parts))
    require(root in path.parents, "UNSAFE_PATH", "Path is not inside the selected folder.")
    return path

def regular(path: Path, max_bytes: int | None = None) -> Path:
    path = no_links(path)
    require(path.is_file(), "FILE_MISSING", "The selected regular file is missing.")
    if max_bytes is not None:
        require(path.stat().st_size <= max_bytes, "SIZE_LIMIT", "The selected file exceeds its size limit.")
    return path

def digest(path: Path) -> str:
    path = regular(path)
    before = path.stat()
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    after = path.stat()
    require((before.st_size, before.st_mtime_ns, before.st_ino) ==
            (after.st_size, after.st_mtime_ns, after.st_ino),
            "SOURCE_CHANGED", "Source changed while hashing; no acceptance is recorded.")
    return h.hexdigest()

def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")

def object_hash(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()

def strict_json(raw: bytes | str) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "INVALID_JSON", "Duplicate JSON keys are not accepted.")
            result[key] = value
        return result
    def bad_constant(_):
        raise ModError("INVALID_JSON", "Non-finite JSON values are not accepted.")
    try:
        text = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
        return json.loads(text, object_pairs_hook=pairs, parse_constant=bad_constant)
    except (ValueError, UnicodeError) as e:
        raise ModError("INVALID_JSON", "Invalid or non-UTF-8 JSON.") from e

def read_json(path: Path, limit: int = 4 * 1024 * 1024) -> Any:
    raw = regular(path, limit).read_bytes()
    try:
        return strict_json(raw)
    except (ValueError, UnicodeError) as e:
        raise ModError("INVALID_JSON", "Invalid or non-UTF-8 JSON.") from e

def write_new(path: Path, data: bytes) -> None:
    path = no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())

def json_new(path: Path, obj: Any) -> None:
    write_new(path, json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n")

@contextmanager
def local_lock(root: Path, name: str = ".mod-ops.lock") -> Iterator[None]:
    root = no_links(root)
    root.mkdir(parents=True, exist_ok=True)
    lock = contained(root, name)
    try:
        json_new(lock, {"pid": os.getpid(), "created_unix": time.time(), "kind": "cooperative-only"})
    except FileExistsError as e:
        raise ModError("OWNER_UNKNOWN", "A lock already exists. Reconcile the existing operation; do not retry or delete it automatically.") from e
    try:
        yield
    finally:
        lock.unlink()

def copy_new(source: Path, dest: Path, expected: str) -> None:
    source = regular(source)
    dest = no_links(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    with source.open("rb") as src, dest.open("xb") as out:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            out.write(chunk)
            h.update(chunk)
        out.flush()
        os.fsync(out.fileno())
    require(h.hexdigest() == expected, "SOURCE_CHANGED", "Copied bytes differ from the reviewed source; preserve the partial operation.")
