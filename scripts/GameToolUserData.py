"""Bounded shared user-data compatibility and private recovery exports.

Application releases and data versions are independent. Existing INI/native
profiles are opaque byte-preserved files, not guessed migrations. JSON envelope
migrations are previewed and saved only to a new copy. ZIP imports never replace
the active profile store. No networking, process control, input or auto-replay.

Hashes detect drift/corruption; they are not signatures or trust in a publisher.
Exports contain private source locators and must not enter public source bundles.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import uuid
import zipfile

VERSION = "0.1.0"
ENVELOPE_SCHEMA = 1
DATA_VERSION = 2
ARCHIVE_SCHEMA = 1
MAX_FILES = 512
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_JSON_BYTES = 2 * 1024 * 1024
_HASH = re.compile(r"[a-fA-F0-9]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:+-]{0,127}\Z")
_RESERVED = {"con", "prn", "aux", "nul", *("com" + str(n) for n in range(1, 10)),
             *("lpt" + str(n) for n in range(1, 10)),
             *("com" + n for n in "¹²³"), *("lpt" + n for n in "¹²³")}


class UserDataError(ValueError):
    """A refused operation; inspect its stable code without exposing paths."""

    def __init__(self, code="USER_DATA_REFUSED"):
        self.code = code
        super().__init__(code.replace("_", " ").capitalize() + ". Originals were not replaced.")


def _fail(code):
    raise UserDataError(code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _canonical(value):
    try:
        raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, RecursionError, OverflowError):
        _fail("INVALID_JSON_DATA")
    if len(raw) > MAX_JSON_BYTES:
        _fail("JSON_LIMIT_EXCEEDED")
    return raw


def _tree(value):
    stack, count = [(value, 0)], 0
    while stack:
        node, depth = stack.pop()
        count += 1
        if count > 32768 or depth > 20:
            _fail("JSON_TREE_LIMIT_EXCEEDED")
        if type(node) is dict:
            if any(type(k) is not str for k in node):
                _fail("INVALID_JSON_DATA")
            stack.extend((v, depth + 1) for v in node.values())
        elif type(node) is list:
            stack.extend((v, depth + 1) for v in node)
        elif node is not None and type(node) not in {str, int, float, bool}:
            _fail("INVALID_JSON_DATA")
    _canonical(value)
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("DUPLICATE_JSON_FIELD")
        result[key] = value
    return result


def _decode(raw, limit=MAX_JSON_BYTES):
    if type(raw) is not bytes or not 0 < len(raw) <= limit:
        _fail("JSON_LIMIT_EXCEEDED")
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: _fail("NONFINITE_JSON_VALUE"))
        return _tree(value)
    except (UnicodeError, ValueError, RecursionError, OverflowError) as exc:
        if isinstance(exc, UserDataError):
            raise
        _fail("INVALID_JSON_DATA")


def _id(value):
    if type(value) is not str or not _ID.fullmatch(value):
        _fail("INVALID_STABLE_ID")
    return value


def _version(value):
    if type(value) is not int or not 1 <= value <= 1000000:
        _fail("INVALID_DATA_VERSION")
    return value


def _hash(value):
    if type(value) is not str or not _HASH.fullmatch(value):
        _fail("EXPECTED_HASH_REQUIRED")
    return value.lower()


def _text(value, nullable=False):
    if nullable and value is None:
        return value
    if type(value) is not str or not 1 <= len(value) <= 512 or any(ord(c) < 32 for c in value):
        _fail("INVALID_PROVENANCE_TEXT")
    return value


def local_path(value):
    """Absolute named local path, refusing symlinks/reparse points in ancestors."""
    try:
        path = Path(value)
    except (ValueError, TypeError):
        _fail("UNSAFE_LOCAL_PATH")
    if not path.is_absolute() or path == Path(path.anchor) or str(path).startswith("\\\\") or \
            any(part in {".", ".."} for part in path.parts):
        _fail("UNSAFE_LOCAL_PATH")
    # Reject lexical parent traversal before pathlib silently normalizes dots.
    if re.search(r"(?:^|[\\/])\.{1,2}(?:[\\/]|$)", str(value)):
        _fail("UNSAFE_LOCAL_PATH")
    for part in path.parts:
        if part == path.anchor:
            continue
        if part.endswith((".", " ")) or part.split(".")[0].casefold() in _RESERVED or \
                any(ord(c) < 32 or c in '<>:"|?*' for c in part):
            _fail("UNSAFE_LOCAL_PATH")
    for node in (path, *path.parents):
        try:
            info = node.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            _fail("LINKED_PATH_REFUSED")
    return path


def _read(path, limit=MAX_FILE_BYTES):
    path = local_path(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        _fail("FILE_LIMIT_OR_TYPE_REFUSED")
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    after = path.stat()
    if len(raw) > limit or len(raw) != before.st_size or \
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_ino) != \
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino):
        _fail("SOURCE_CHANGED")
    return raw, after


def _write_new(path, raw):
    path = local_path(path)
    if not path.parent.is_dir():
        _fail("EXISTING_PARENT_REQUIRED")
    try:
        with path.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        _fail("NEW_COPY_REQUIRED")
    if _read(path, max(MAX_FILE_BYTES, len(raw)))[0] != raw:
        _fail("NEW_COPY_READBACK_FAILED")


def _relative(value):
    if type(value) is not str or not 1 <= len(value) <= 240 or "\\" in value or ":" in value:
        _fail("UNSAFE_ARCHIVE_PATH")
    path = PurePosixPath(value)
    parts = value.split("/")
    if path.is_absolute() or str(path) != value or len(parts) > 12 or any(
            part in {"", ".", ".."} or part.endswith((".", " ")) or
            part.split(".")[0].casefold() in _RESERVED or
            any(ord(c) < 32 or c in '<>"|?*' for c in part) for part in parts):
        _fail("UNSAFE_ARCHIVE_PATH")
    return value


def _utc():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_envelope(kind, payload, record_id=None, source=None, app_version=None):
    """Create a current shared envelope; callers may supply a preserved stable ID.

    ``source`` is a private provenance object. Unknown payload/provenance fields
    are retained verbatim; neither an envelope nor its metadata is an action.
    """
    envelope = {"schema_version": ENVELOPE_SCHEMA, "data_version": DATA_VERSION,
                "record_id": _id(record_id or str(uuid.uuid4())), "kind": _id(kind),
                "payload": copy.deepcopy(payload), "source": copy.deepcopy({} if source is None else source),
                "links": [], "extensions": {}, "producer": {"app_version": app_version}}
    _validate_envelope(envelope)
    return envelope


def _validate_envelope(envelope):
    _tree(envelope)
    if type(envelope) is not dict:
        _fail("ENVELOPE_OBJECT_REQUIRED")
    for field in ("schema_version", "data_version", "record_id", "kind", "payload", "source"):
        if field not in envelope:
            _fail("ENVELOPE_FIELD_MISSING")
    _version(envelope["schema_version"])
    _version(envelope["data_version"])
    _id(envelope["record_id"])
    _id(envelope["kind"])
    if type(envelope["source"]) is not dict:
        _fail("PROVENANCE_OBJECT_REQUIRED")
    if envelope["schema_version"] != ENVELOPE_SCHEMA or envelope["data_version"] > DATA_VERSION:
        return False
    if envelope["data_version"] == 2 and (type(envelope.get("links")) is not list or
                                           type(envelope.get("extensions")) is not dict):
        _fail("CURRENT_ENVELOPE_FIELD_INVALID")
    return True


def preview_migration(envelope, target_version=DATA_VERSION):
    """Pure additive migration preview; no original mutation or file write.

    Future versions return ``BLOCKED_FUTURE_VERSION`` and an unchanged envelope.
    IDs, payload and unknown fields survive the v1→v2 migration.
    """
    supported = _validate_envelope(envelope)
    current = envelope["data_version"]
    target_version = _version(target_version)
    original = copy.deepcopy(envelope)
    if not supported or target_version > DATA_VERSION:
        return {"state": "BLOCKED_FUTURE_VERSION", "read_only": True, "changes": [],
                "envelope": original, "source_sha256": digest(_canonical(original)),
                "preview_sha256": digest(_canonical(original))}
    if target_version < current:
        _fail("DOWNGRADE_REFUSED")
    migrated, changes = copy.deepcopy(envelope), []
    if current == 1 and target_version >= 2:
        for field, default in (("links", []), ("extensions", {})):
            if field not in migrated:
                migrated[field] = default
                changes.append({"field": field, "operation": "add"})
        migrated["data_version"] = 2
        changes.append({"field": "data_version", "from": 1, "to": 2})
    _validate_envelope(migrated)
    return {"state": "PREVIEW_READY", "read_only": False, "changes": changes,
            "envelope": migrated, "source_sha256": digest(_canonical(original)),
            "preview_sha256": digest(_canonical(migrated))}


def inspect_envelope(path):
    raw, _ = _read(path, MAX_JSON_BYTES)
    result = preview_migration(_decode(raw))
    result["file_sha256"] = digest(raw)
    return result


def save_migrated_copy(source, destination, expected_sha256, preview_sha256):
    """Commit an already reviewed migration to a new file, never in-place."""
    raw, _ = _read(source, MAX_JSON_BYTES)
    if digest(raw) != _hash(expected_sha256):
        _fail("SOURCE_CHANGED")
    result = preview_migration(_decode(raw))
    if result["read_only"]:
        _fail("FUTURE_VERSION_READ_ONLY")
    if result["preview_sha256"] != _hash(preview_sha256):
        _fail("PREVIEW_CHANGED")
    # Check again at commit boundary; an original-byte hash is not schema proof.
    if digest(_read(source, MAX_JSON_BYTES)[0]) != digest(raw):
        _fail("SOURCE_CHANGED")
    output = _canonical(result["envelope"]) + b"\n"
    _write_new(destination, output)
    if digest(_read(source, MAX_JSON_BYTES)[0]) != digest(raw):
        _fail("SOURCE_CHANGED_PRESERVE_NEW_COPY")
    return {"state": "MIGRATED_NEW_COPY", "sha256": digest(output),
            "record_id": result["envelope"]["record_id"], "source_sha256": digest(raw),
            "originals_replaced": False}


def _selection(row):
    if type(row) is not dict or not {"path", "logical_path"} <= row.keys() or \
            not set(row) <= {"path", "logical_path", "record_id", "owner", "revision", "format"}:
        _fail("EXPLICIT_FILE_SELECTION_REQUIRED")
    path = local_path(row["path"])
    logical = _relative(row["logical_path"])
    owner = _text(row.get("owner", "user-selected-local-file"))
    revision = _text(row.get("revision"), True)
    record_id = _id(row.get("record_id") or str(uuid.uuid5(uuid.NAMESPACE_URL,
                     "gametools:user-data:" + owner + ":" + logical)))
    format_name = row.get("format", "opaque")
    if format_name not in {"opaque", "envelope"}:
        _fail("UNSUPPORTED_FILE_FORMAT")
    raw, info = _read(path)
    data_version = None
    if format_name == "envelope":
        envelope = _decode(raw)
        _validate_envelope(envelope)
        data_version = envelope["data_version"]
        if row.get("record_id") is not None and row["record_id"] != envelope["record_id"]:
            _fail("ENVELOPE_STABLE_ID_MISMATCH")
        record_id = envelope["record_id"]
    return {"record_id": record_id, "logical_path": logical, "member": "data/" + logical,
            "bytes": len(raw), "sha256": digest(raw), "format": format_name,
            "data_version": data_version, "provenance": {"owner": owner, "revision": revision,
            "source_path": str(path), "sha256": digest(raw), "mtime_ns": info.st_mtime_ns}}


def _inventory(rows):
    if type(rows) is not list or not 1 <= len(rows) <= MAX_FILES:
        _fail("FILE_COUNT_LIMIT_EXCEEDED")
    names, ids, total = set(), set(), 0
    for row in rows:
        if type(row) is not dict:
            _fail("INVALID_FILE_INVENTORY")
        logical = _relative(row.get("logical_path"))
        if row.get("member") != "data/" + logical:
            _fail("UNSAFE_ARCHIVE_PATH")
        _id(row.get("record_id"))
        folded = logical.casefold()
        if folded in names or row["record_id"] in ids or any(
                folded.startswith(n + "/") or n.startswith(folded + "/") for n in names):
            _fail("DUPLICATE_FILE_OR_ID")
        names.add(logical.casefold()); ids.add(row["record_id"])
        if type(row.get("bytes")) is not int or not 0 <= row["bytes"] <= MAX_FILE_BYTES:
            _fail("FILE_LIMIT_OR_TYPE_REFUSED")
        total += row["bytes"]
        _hash(row.get("sha256"))
        provenance = row.get("provenance")
        if type(provenance) is not dict:
            _fail("PROVENANCE_OBJECT_REQUIRED")
        _text(provenance.get("owner"))
        _text(provenance.get("revision"), True)
        _text(provenance.get("source_path"))
        if provenance.get("sha256") != row["sha256"] or type(provenance.get("mtime_ns")) is not int:
            _fail("INVALID_PROVENANCE")
        if row.get("format") not in {"opaque", "envelope"}:
            _fail("UNSUPPORTED_FILE_FORMAT")
        if row["format"] == "envelope":
            _version(row.get("data_version"))
        elif row.get("data_version") is not None:
            _fail("OPAQUE_VERSION_MUST_BE_UNKNOWN")
    if total > MAX_TOTAL_BYTES:
        _fail("TOTAL_SIZE_LIMIT_EXCEEDED")
    return total


def preview_export(selections, app_version=None):
    """Inspect explicitly selected files only; no recursive discovery or write.

    Selection: ``path``, portable ``logical_path`` and optional stable
    ``record_id``, ``owner``, exact ``revision`` and ``format`` (opaque/envelope).
    A missing revision stays null; content SHA identifies the exact source bytes.
    """
    if type(selections) is not list or not 1 <= len(selections) <= MAX_FILES:
        _fail("FILE_COUNT_LIMIT_EXCEEDED")
    rows = [_selection(row) for row in selections]
    total = _inventory(rows)
    manifest = {"schema_version": ARCHIVE_SCHEMA, "data_version": DATA_VERSION,
                "kind": "GameToolsUserData", "bundle_id": str(uuid.uuid4()), "created_utc": _utc(),
                "producer": {"component": VERSION, "app_version": app_version},
                "privacy": "private_recovery", "cloud_transfer": "manual_export_only", "files": rows}
    raw = _canonical(manifest)
    return {"state": "EXPORT_PREVIEW", "manifest": manifest, "files": len(rows), "bytes": total,
            "preview_sha256": digest(raw), "originals_replaced": False,
            "network_sync": False, "warning": "Private export includes selected source locators; not a public source ZIP."}


def _source_payloads(manifest):
    payloads = {}
    for row in manifest["files"]:
        raw, info = _read(row["provenance"]["source_path"])
        if len(raw) != row["bytes"] or digest(raw) != row["sha256"] or \
                info.st_mtime_ns != row["provenance"]["mtime_ns"]:
            _fail("SOURCE_CHANGED")
        payloads[row["member"]] = raw
    return payloads


def export_archive(destination, preview):
    """Commit exactly an export preview to a NEW ZIP; recheck source drift."""
    if type(preview) is not dict or preview.get("state") != "EXPORT_PREVIEW":
        _fail("EXPORT_PREVIEW_REQUIRED")
    manifest = copy.deepcopy(preview.get("manifest"))
    _check_manifest(manifest)
    if digest(_canonical(manifest)) != _hash(preview.get("preview_sha256")):
        _fail("PREVIEW_CHANGED")
    payloads = _source_payloads(manifest)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("MANIFEST.json", _canonical(manifest))
        for member, raw in payloads.items():
            archive.writestr(member, raw)
    _source_payloads(manifest)
    raw = output.getvalue()
    _write_new(destination, raw)
    result = inspect_archive(destination, digest(raw))
    _source_payloads(manifest)
    return {"state": "EXPORTED_NEW_ARCHIVE", "sha256": result["archive_sha256"],
            "files": len(manifest["files"]), "bytes": result["bytes"],
            "cloud_transfer": "manual_export_only", "originals_replaced": False}


def _check_manifest(manifest):
    if type(manifest) is not dict or manifest.get("kind") != "GameToolsUserData":
        _fail("USER_DATA_MANIFEST_REQUIRED")
    _version(manifest.get("schema_version")); _version(manifest.get("data_version"))
    _id(manifest.get("bundle_id"))
    _text(manifest.get("created_utc"))
    if type(manifest.get("producer")) is not dict or manifest.get("privacy") != "private_recovery" or \
            manifest.get("cloud_transfer") != "manual_export_only":
        _fail("INVALID_PRIVATE_MANIFEST")
    _inventory(manifest.get("files"))
    return manifest["schema_version"] == ARCHIVE_SCHEMA and manifest["data_version"] <= DATA_VERSION


def inspect_archive(archive, expected_sha256=None):
    """Read-only import preview; verify all member hashes and portable names.

    Any recognized future data/schema version remains viewable read-only and
    blocks restore. Opaque native files are not parsed or automatically applied.
    ``expected_sha256`` pins an already selected checkpoint, not authenticity.
    """
    raw, _ = _read(archive, MAX_TOTAL_BYTES + MAX_MANIFEST_BYTES)
    archive_hash = digest(raw)
    if expected_sha256 is not None and archive_hash != _hash(expected_sha256):
        _fail("ARCHIVE_CHANGED")
    payloads, manifest = {}, None
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
            entries = bundle.infolist()
            if not 2 <= len(entries) <= MAX_FILES + 1 or \
                    sum(e.file_size for e in entries) > MAX_TOTAL_BYTES + MAX_MANIFEST_BYTES:
                _fail("ARCHIVE_LIMIT_EXCEEDED")
            seen = set()
            for entry in entries:
                # On Windows ZipInfo normalizes backslashes. Validate the
                # unnormalized header name, not only the convenient filename.
                name = _relative(entry.orig_filename)
                if entry.filename != name:
                    _fail("UNSAFE_ARCHIVE_PATH")
                mode = entry.external_attr >> 16
                if entry.is_dir() or entry.flag_bits & 1 or \
                        (stat.S_IFMT(mode) and not stat.S_ISREG(mode)) or entry.external_attr & 0x400:
                    _fail("ARCHIVE_LINK_OR_TYPE_REFUSED")
                if name.casefold() in seen:
                    _fail("ARCHIVE_DUPLICATE_MEMBER")
                seen.add(name.casefold())
                limit = MAX_MANIFEST_BYTES if name == "MANIFEST.json" else MAX_FILE_BYTES
                if entry.file_size > limit or entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    _fail("ARCHIVE_MEMBER_LIMIT_EXCEEDED")
                with bundle.open(entry) as handle:
                    content = handle.read(limit + 1)
                if len(content) != entry.file_size or len(content) > limit:
                    _fail("ARCHIVE_MEMBER_SIZE_MISMATCH")
                if name == "MANIFEST.json":
                    manifest = _decode(content, MAX_MANIFEST_BYTES)
                else:
                    if not name.startswith("data/"):
                        _fail("UNLISTED_ARCHIVE_MEMBER")
                    payloads[name] = content
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError, OSError):
        _fail("INVALID_ARCHIVE")
    supported = _check_manifest(manifest)
    if set(payloads) != {row["member"] for row in manifest["files"]}:
        _fail("ARCHIVE_INVENTORY_MISMATCH")
    migration_rows = []
    for row in manifest["files"]:
        content = payloads[row["member"]]
        if len(content) != row["bytes"] or digest(content) != row["sha256"]:
            _fail("ARCHIVE_HASH_MISMATCH")
        if row["format"] == "envelope":
            result = preview_migration(_decode(content))
            envelope = result["envelope"]
            if envelope["record_id"] != row["record_id"] or \
                    _decode(content)["data_version"] != row["data_version"]:
                _fail("ARCHIVE_ENVELOPE_IDENTITY_MISMATCH")
            supported = supported and not result["read_only"]
            migration_rows.append({"record_id": row["record_id"], "state": result["state"],
                                   "changes": result["changes"]})
    preview_body = {"archive_sha256": archive_hash, "manifest": manifest,
                    "migrations": migration_rows, "restore_mode": "unchanged_new_copy_only"}
    return {**preview_body, "state": "IMPORT_PREVIEW" if supported else "BLOCKED_FUTURE_VERSION",
            "read_only": not supported, "preview_sha256": digest(_canonical(preview_body)),
            "files": len(manifest["files"]), "bytes": sum(len(v) for v in payloads.values()),
            "originals_replaced": False, "network_sync": False}


def restore_new_copy(archive, destination, expected_sha256, preview_sha256):
    """Restore original bytes to a NEW directory after an exact import preview.

    Does not activate profiles or execute/import any settings. An incomplete copy
    is retained with an explicit marker on failure; originals remain untouched.
    Envelope migration, if desired, is a separate reviewed new-file operation.
    """
    result = inspect_archive(archive, _hash(expected_sha256))
    if result["read_only"]:
        _fail("FUTURE_VERSION_READ_ONLY")
    if result["preview_sha256"] != _hash(preview_sha256):
        _fail("PREVIEW_CHANGED")
    target = local_path(destination)
    if not target.parent.is_dir():
        _fail("EXISTING_PARENT_REQUIRED")
    # No source path is used as a destination, and no existing directory merges.
    try:
        target.mkdir()
    except FileExistsError:
        _fail("NEW_COPY_REQUIRED")
    marker = target / "_RESTORE-INCOMPLETE.json"
    _write_new(marker, _canonical({"archive_sha256": result["archive_sha256"],
                                  "state": "INCOMPLETE_EVIDENCE_ONLY_COPY"}))
    raw, _ = _read(archive, MAX_TOTAL_BYTES + MAX_MANIFEST_BYTES)
    if digest(raw) != result["archive_sha256"]:
        _fail("ARCHIVE_CHANGED_PRESERVE_NEW_COPY")
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        for row in result["manifest"]["files"]:
            path = local_path(target / "data" / row["logical_path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            content = bundle.read(row["member"])
            _write_new(path, content)
            if digest(_read(path)[0]) != row["sha256"]:
                _fail("RESTORE_READBACK_FAILED")
    if digest(_read(archive, MAX_TOTAL_BYTES + MAX_MANIFEST_BYTES)[0]) != result["archive_sha256"]:
        _fail("ARCHIVE_CHANGED_PRESERVE_NEW_COPY")
    _write_new(target / "MANIFEST.json", _canonical(result["manifest"]) + b"\n")
    receipt = {"state": "RESTORED_NEW_COPY", "archive_sha256": result["archive_sha256"],
               "files": result["files"], "restored_utc": _utc(), "originals_replaced": False,
               "profiles_activated": False, "envelopes_migrated": False, "network_sync": False}
    _write_new(target / "RESTORE-RECEIPT.json", _canonical(receipt) + b"\n")
    marker.unlink()  # Only this operation's own transient completion marker.
    return receipt


# MCI-08 additive streaming primitives. Legacy archives above are unchanged.
STREAM_BUFFER_BYTES = 1024 * 1024


def _stream_visit(path, limit, before_chunk=None, sink=None):
    """Bounded stable-file read; the caller owns authorization and destinations."""
    if type(limit) is not int or not 0 <= limit <= MAX_FILE_BYTES:
        _fail("FILE_LIMIT_OR_TYPE_REFUSED")
    path = local_path(path)
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
        _fail("FILE_LIMIT_OR_TYPE_REFUSED")
    # Windows 3.12 may report creation time from stat and change time from
    # fstat as st_ctime_ns. Compare each observation channel with itself;
    # cross-channel identity uses the shared object/size/write-time fields.
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    stable = lambda s: (*identity(s), s.st_ctime_ns)
    count, hashed = 0, hashlib.sha256()
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if identity(opened) != identity(before):
            _fail("SOURCE_CHANGED")
        while True:
            if before_chunk is not None:
                before_chunk()
            block = stream.read(min(STREAM_BUFFER_BYTES, limit - count + 1))
            if not block:
                break
            count += len(block)
            if count > limit:
                _fail("FILE_LIMIT_OR_TYPE_REFUSED")
            hashed.update(block)
            if sink is not None:
                if sink.write(block) != len(block):
                    _fail("SHORT_WRITE_PRESERVE_PARTIAL")
        after_handle = os.fstat(stream.fileno())
    after = local_path(path).stat()
    if count != before.st_size or stable(opened) != stable(after_handle) or stable(before) != stable(after):
        _fail("SOURCE_CHANGED")
    return {"bytes": count, "sha256": hashed.hexdigest()}


def stream_fingerprint(path, limit=MAX_FILE_BYTES, *, before_chunk=None):
    """Read and hash one regular selected file without retaining its full body."""
    return _stream_visit(path, limit, before_chunk)


def copy_stream_new(source, destination, expected_sha256, expected_bytes, *, before_chunk=None):
    """Exact bounded copy to a new file. Errors preserve inspectable partial data.

    No implicit mkdir, overwrite, retry, permissions transfer or action replay.
    Files are flushed/fsynced; physical power-loss durability is not asserted.
    """
    expected = {"bytes": expected_bytes, "sha256": _hash(expected_sha256)}
    if type(expected_bytes) is not int or not 0 <= expected_bytes <= MAX_FILE_BYTES:
        _fail("FILE_LIMIT_OR_TYPE_REFUSED")
    if stream_fingerprint(source, expected_bytes, before_chunk=before_chunk) != expected:
        _fail("SOURCE_CHANGED")
    target = local_path(destination)
    if not target.parent.is_dir():
        _fail("EXISTING_PARENT_REQUIRED")
    if before_chunk is not None:
        before_chunk()
    try:
        with target.open("xb") as output:
            observed = _stream_visit(source, expected_bytes, before_chunk, output)
            if observed != expected:
                _fail("SOURCE_CHANGED_PRESERVE_NEW_COPY")
            if before_chunk is not None:
                before_chunk()
            output.flush()
            os.fsync(output.fileno())
    except FileExistsError:
        _fail("NEW_COPY_REQUIRED")
    if stream_fingerprint(target, expected_bytes, before_chunk=before_chunk) != expected:
        _fail("NEW_COPY_READBACK_FAILED")
    return expected
