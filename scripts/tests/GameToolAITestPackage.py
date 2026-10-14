"""Build a bounded real-file package fixture for source-checkout AI tests.

Production remains fail-closed on a missing generated MANIFEST.json. Tests copy
only the same allowlisted text domains consumed by KnowledgeIndex into a private
temporary directory, hash those ordinary files, and generate package metadata
there. No symlinks, repository writes, network calls, or runtime shortcuts are
used.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import stat

_ALLOWED_ROOTS = ("docs", "schemas", "templates", "preferences")
_ALLOWED_SUFFIXES = {".md", ".json", ".txt"}
_MAX_FILE_BYTES = 128 * 1024
_MAX_FILES = 512
_MAX_TOTAL_BYTES = 4 * 1024 * 1024


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_ai_test_package(source_root: Path, destination: Path) -> Path:
    """Create one immutable package-shaped fixture and return its root."""
    source_root = Path(source_root).resolve()
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError("AI test package destination already exists.")
    destination.mkdir(parents=True)

    candidates = []
    agents = source_root / "AGENTS.md"
    if agents.is_file():
        candidates.append(agents)
    for name in _ALLOWED_ROOTS:
        root = source_root / name
        if root.is_dir():
            candidates.extend(path for path in root.rglob("*") if path.is_file())

    rows = []
    total = 0
    for source in sorted(set(candidates), key=lambda path: path.relative_to(source_root).as_posix().casefold()):
        relative = source.relative_to(source_root).as_posix()
        info = source.lstat()
        if not stat.S_ISREG(info.st_mode) or source.is_symlink():
            raise ValueError("AI test package source must be an ordinary file.")
        if source.suffix.lower() not in _ALLOWED_SUFFIXES or info.st_size > _MAX_FILE_BYTES:
            continue
        target = destination.joinpath(*Path(relative).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied = target.stat()
        if copied.st_size != info.st_size:
            raise ValueError("AI test package copy size changed.")
        digest = _sha256(target)
        rows.append({"path": relative, "bytes": copied.st_size, "sha256": digest})
        total += copied.st_size

    if not rows or len(rows) > _MAX_FILES or total > _MAX_TOTAL_BYTES:
        raise ValueError("AI test package inventory is outside the production knowledge bounds.")

    manifest = {
        "schema_version": 1,
        "bundle": "game-tools-ai-source-test-fixture",
        "component_versions": {"tool_hub": "0.26.0-preview.1", "ai_transport": "0.26.0-preview.1"},
        "canonical_reference_revision": "043f3c4733788f082da98dfcb43c0972d2794c6a",
        "files": rows,
        "test_fixture": True,
    }
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    (destination / "MANIFEST.json").write_bytes(raw)
    return destination
