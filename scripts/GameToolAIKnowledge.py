"""Deterministic allowlisted knowledge search for packaged Game Tools sources.

The index reads only text files named by the package manifest.  It never accepts
an arbitrary local path, scans a drive, follows links, downloads content, or
indexes private runtime data.  Search results use stable opaque IDs and source-
relative provenance; callers fetch exact content in a separate bounded step.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlparse

from GameToolAIContracts import stable_revision

MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_FILE_BYTES = 128 * 1024
MAX_FILES = 512
MAX_TOTAL_BYTES = 4 * 1024 * 1024
MAX_RESULTS = 20
MAX_FETCH_LINES = 200
_TEXT_SUFFIXES = {".md", ".json", ".txt"}
_SCOPES = {
    "all": ("AGENTS.md", "docs/", "schemas/", "templates/", "preferences/"),
    "docs": ("docs/",),
    "schemas": ("schemas/",),
    "templates": ("templates/",),
    "preferences": ("preferences/", "AGENTS.md"),
}
_TOKEN = re.compile(r"[A-Za-z0-9_.+-]{2,}")
_RESOURCE = re.compile(r"game-tools-knowledge://([a-f0-9]{24})\Z")


class KnowledgeError(ValueError):
    pass


def _identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _regular_no_links(root: Path, relative: str, maximum: int) -> tuple[Path, bytes]:
    if not isinstance(relative, str) or not relative or "\\" in relative or relative.startswith("/"):
        raise KnowledgeError("Invalid packaged source identity.")
    parts = Path(relative).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise KnowledgeError("Invalid packaged source identity.")
    path = root.joinpath(*parts)
    root_abs = root.absolute()
    for item in (path, *path.parents):
        if item == root_abs.parent:
            break
        try:
            info = item.lstat()
        except FileNotFoundError:
            raise KnowledgeError("Packaged knowledge source is missing.") from None
        except OSError:
            raise KnowledgeError("Packaged knowledge source could not be inspected.") from None
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            raise KnowledgeError("Linked packaged knowledge sources are not supported.")
        if item == root_abs:
            break
    try:
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
                raise KnowledgeError("Packaged knowledge source is outside its size bound.")
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        current = path.stat()
    except KnowledgeError:
        raise
    except OSError:
        raise KnowledgeError("Packaged knowledge source could not be read.") from None
    if len(raw) > maximum or _identity(before) != _identity(after) or _identity(after) != _identity(current):
        raise KnowledgeError("Packaged knowledge source changed during read.")
    return path, raw


def read_selected_source(root: Path, relative: str, expected_sha256: str | None = None) -> dict:
    """Local read-only adapter for an explicitly selected source, never a scan.

    This shares the package reader's bounds/link/identity checks. It does not
    enroll the source in KnowledgeIndex or make its contents an instruction.
    """
    from pathlib import PurePosixPath
    if (not isinstance(relative, str) or not relative or
            PurePosixPath(relative).as_posix() != relative or
            any(c in relative for c in "\\\\:\x00") or
            any(p in {".", "..", ""} for p in relative.split("/"))):
        raise KnowledgeError("Invalid selected source identity.")
    if expected_sha256 is not None and not re.fullmatch(r"[a-f0-9]{64}", expected_sha256):
        raise KnowledgeError("Invalid expected source revision.")
    _, raw = _regular_no_links(Path(root).absolute(), relative, MAX_FILE_BYTES)
    revision = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and revision != expected_sha256:
        raise KnowledgeError("Selected source changed; reload before using it.")
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeError:
        raise KnowledgeError("Selected source is not UTF-8 text.") from None
    return {"locator": relative, "sha256": revision, "bytes": len(raw), "content": content}


def _heading(relative: str, text: str) -> str:
    if relative.endswith(".md"):
        for line in text.splitlines()[:40]:
            match = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
            if match:
                return match.group(1)[:160]
    return Path(relative).name[:160]


def _resource_id(relative: str, revision: str) -> str:
    return hashlib.sha256((relative + "\0" + revision).encode("utf-8")).hexdigest()[:24]


def _scope_matches(relative: str, scope: str) -> bool:
    prefixes = _SCOPES[scope]
    return any(relative == prefix or relative.startswith(prefix) for prefix in prefixes)


class KnowledgeIndex:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or Path(__file__).resolve().parents[1]).absolute()
        _, raw_manifest = _regular_no_links(self.root, "MANIFEST.json", MAX_MANIFEST_BYTES)
        try:
            manifest = json.loads(raw_manifest.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError, RecursionError):
            raise KnowledgeError("Package manifest is not valid UTF-8 JSON.") from None
        rows = manifest.get("files")
        if not isinstance(rows, list) or len(rows) > MAX_FILES:
            raise KnowledgeError("Package manifest file list is outside its bound.")
        entries = []
        total = 0
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
                raise KnowledgeError("Package manifest file record is invalid.")
            relative = row["path"]
            if not isinstance(relative, str) or Path(relative).suffix.lower() not in _TEXT_SUFFIXES or not _scope_matches(relative, "all"):
                continue
            if not isinstance(row["bytes"], int) or row["bytes"] < 0 or row["bytes"] > MAX_FILE_BYTES or \
                    not isinstance(row["sha256"], str) or not re.fullmatch(r"[a-fA-F0-9]{64}", row["sha256"]):
                continue
            _, raw = _regular_no_links(self.root, relative, MAX_FILE_BYTES)
            digest = hashlib.sha256(raw).hexdigest()
            if digest != row["sha256"].lower() or len(raw) != row["bytes"]:
                raise KnowledgeError("Packaged source no longer matches its manifest.")
            total += len(raw)
            if total > MAX_TOTAL_BYTES:
                raise KnowledgeError("Packaged knowledge index exceeds its total byte bound.")
            try:
                text = raw.decode("utf-8")
            except UnicodeError:
                continue
            ident = _resource_id(relative, digest)
            entries.append({
                "id": ident,
                "result_id": "knowledge:" + ident,
                "uri": "game-tools-knowledge://" + ident,
                "relative": relative,
                "title": _heading(relative, text),
                "revision": digest,
                "bytes": len(raw),
                "text": text,
                "lower": text.casefold(),
            })
        entries.sort(key=lambda item: item["relative"].casefold())
        self._entries = entries
        self._by_result = {item["result_id"]: item for item in entries}
        self._by_uri = {item["uri"]: item for item in entries}
        self.revision = stable_revision([
            {key: item[key] for key in ("result_id", "relative", "revision", "bytes")}
            for item in entries
        ])
        self.canonical_reference_revision = manifest.get("canonical_reference_revision")

    @staticmethod
    def _terms(query: str) -> list[str]:
        if not isinstance(query, str) or not query.strip() or len(query) > 256 or any(ord(char) < 32 for char in query):
            raise KnowledgeError("Search query must be nonempty bounded text.")
        terms = [token.casefold() for token in _TOKEN.findall(query)]
        if not terms:
            raise KnowledgeError("Search query has no searchable terms.")
        return list(dict.fromkeys(terms))[:16]

    def search(self, query: str, scope: str = "all", limit: int = 8) -> dict:
        if scope not in _SCOPES or type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
            raise KnowledgeError("Invalid search scope or result limit.")
        terms = self._terms(query)
        phrase = query.strip().casefold()
        scored = []
        for item in self._entries:
            if not _scope_matches(item["relative"], scope):
                continue
            title = item["title"].casefold()
            relative = item["relative"].casefold()
            lower = item["lower"]
            matched = [term for term in terms if term in lower or term in relative or term in title]
            if not matched:
                continue
            score = sum(lower.count(term) for term in matched)
            score += sum(20 for term in matched if term in title)
            score += sum(10 for term in matched if term in relative)
            if phrase in lower:
                score += 30
            position = min((lower.find(term) for term in matched if term in lower), default=0)
            start = max(0, position - 180)
            end = min(len(item["text"]), position + 420)
            snippet = " ".join(item["text"][start:end].split())[:600]
            scored.append((score, item["relative"].casefold(), item, snippet, matched))
        scored.sort(key=lambda row: (-row[0], row[1]))
        results = []
        for score, _, item, snippet, matched in scored[:limit]:
            results.append({
                "result_id": item["result_id"],
                "resource_uri": item["uri"],
                "title": item["title"],
                "source": item["relative"],
                "snippet": snippet,
                "revision": item["revision"],
                "matched_terms": matched,
                "score": score,
                "evidence_level": "packaged_source",
            })
        return {
            "query": query.strip(), "scope": scope, "results": results,
            "total_matches": len(scored), "index_revision": self.revision,
            "canonical_reference_revision": self.canonical_reference_revision,
        }

    def fetch(self, result_id: str, revision: str | None = None, offset: int = 0, limit: int = 120) -> dict:
        if result_id not in self._by_result or type(offset) is not int or type(limit) is not int or \
                offset < 0 or not 1 <= limit <= MAX_FETCH_LINES:
            raise KnowledgeError("Unknown result ID or invalid fetch range.")
        item = self._by_result[result_id]
        if revision is not None and revision != item["revision"]:
            raise KnowledgeError("Knowledge source revision changed; search again.")
        lines = item["text"].splitlines()
        page = lines[offset:offset + limit]
        next_offset = offset + len(page) if offset + len(page) < len(lines) else None
        return {
            "result_id": item["result_id"], "resource_uri": item["uri"],
            "title": item["title"], "source": item["relative"],
            "revision": item["revision"], "offset": offset,
            "line_count": len(lines), "content": "\n".join(page),
            "next_offset": next_offset,
            "provenance": {
                "kind": "packaged_source", "manifest_verified": True,
                "canonical_reference_revision": self.canonical_reference_revision,
            },
        }

    def list_resources(self, cursor: str | None = None, limit: int = 100) -> dict:
        if cursor is None:
            offset = 0
        elif isinstance(cursor, str) and cursor.isdigit():
            offset = int(cursor)
        else:
            raise KnowledgeError("Invalid resource cursor.")
        if type(limit) is not int or not 1 <= limit <= 100 or offset < 0 or offset > len(self._entries):
            raise KnowledgeError("Invalid resource page.")
        page = self._entries[offset:offset + limit]
        resources = [{
            "uri": item["uri"], "name": Path(item["relative"]).name,
            "title": item["title"],
            "description": "Manifest-verified packaged source: " + item["relative"],
            "mimeType": "text/markdown" if item["relative"].endswith(".md") else "application/json",
            "size": item["bytes"],
            "annotations": {"audience": ["assistant", "user"], "priority": 0.5},
        } for item in page]
        next_cursor = str(offset + len(page)) if offset + len(page) < len(self._entries) else None
        return {"resources": resources, "nextCursor": next_cursor}

    def read_resource(self, uri: str) -> dict:
        if not isinstance(uri, str) or not _RESOURCE.fullmatch(uri) or uri not in self._by_uri:
            raise KnowledgeError("Resource not found.")
        item = self._by_uri[uri]
        return {
            "contents": [{
                "uri": item["uri"],
                "mimeType": "text/markdown" if item["relative"].endswith(".md") else "application/json",
                "text": item["text"],
            }],
            "revision": item["revision"],
        }

    def metadata(self) -> dict:
        return {
            "revision": self.revision, "resource_count": len(self._entries),
            "canonical_reference_revision": self.canonical_reference_revision,
            "arbitrary_paths": False, "network": False,
        }
