"""Selected saved evidence only; no watcher, process query, collector or replay.

The fixed Journal 0.1.0 reader/verifier owns source identity and prefix checks.
Portable summaries use a strict allowlist, never raw names, messages or paths.
Originals and private locators belong only to explicitly created private packets.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
import html
import io
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import types
import xml.etree.ElementTree as ET

VERSION = "0.1.0"
MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_XML_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_SOURCES = 8
MAX_EVENTS = 256
MAX_TIMELINE = 8192
_BASE = Path(__file__).absolute().parent
_NS = "{http://schemas.microsoft.com/win/2004/08/events/event}"
_SHA = re.compile(r"[a-fA-F0-9]{64}\Z")
_UTC = re.compile(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d{1,7}))?(?:Z|\+00:00)\Z")
_ADAPTERS = {"auto", "windows_event_xml", "hub_journal", "opaque_text"}
_JOURNAL_KINDS = {"journal_created", "session_started", "checkpoint", "action_requested",
                  "action_observed", "action_failed", "session_closed", "session_cancelled"}
_LIMITATIONS = [
    "Selected saved files only; no live collection, game control, recording or automatic upload.",
    "Hashes verify byte identity, not authenticity, runtime settings or crash causality.",
    "First reported failure is limited to selected evidence, not the first actual failure.",
    "UTC ordering has unmeasured cross-provider clock error; no QPC/video/scene synchronization.",
    "Journal gaps or an open end do not prove a game crash; raw text is opaque, not diagnosed.",
    "Faulting modules, WER reports and memory warnings do not independently establish root cause.",
    "Originals/locators in a private packet need review before sharing; nothing is uploaded.",
]


class EvidenceError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__("Saved evidence request refused (" + code + "). Originals are retained; no live action was taken.")


def _fail(code):
    raise EvidenceError(code)


def _journal():
    # Fixed authored sibling, not a file/code name supplied by data or the user.
    path = _BASE / "GameToolJournal.py"
    try:
        for part in (path, *path.parents):
            info = part.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                _fail("MODULE_UNAVAILABLE")
        before = path.stat()
        if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= 1024 * 1024:
            _fail("MODULE_UNAVAILABLE")
        with path.open("rb") as stream:
            opened = os.fstat(stream.fileno())
            identity = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
            if identity(opened) != identity(before):
                _fail("MODULE_CHANGED")
            raw = stream.read(1024 * 1024 + 1)
            closed = os.fstat(stream.fileno())
        after = path.stat()
        if len(raw) != before.st_size or identity(before) != identity(closed) or identity(before) != identity(after):
            _fail("MODULE_CHANGED")
        module = types.ModuleType("_fixed_crash_evidence_journal")
        module.__file__ = str(path)
        exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
        if module.VERSION != "0.1.0":
            _fail("MODULE_UNAVAILABLE")
        module._authored_hash = hashlib.sha256(raw).hexdigest()
        module._authored_identity = identity(before)
        return module
    except EvidenceError:
        raise
    except Exception:
        _fail("MODULE_UNAVAILABLE")


def _capture(path, journal):
    try:
        path, raw, identity = journal._read_source(path)
        if not raw:
            _fail("SOURCE_UNAVAILABLE")
        return {"path": path, "raw": raw, "identity": identity,
                "sha256": hashlib.sha256(raw).hexdigest()}
    except EvidenceError:
        raise
    except Exception:
        _fail("SOURCE_UNAVAILABLE")


def _expected(value):
    if value is not None and (type(value) is not str or not _SHA.fullmatch(value)):
        _fail("INVALID_HASH")
    return value.lower() if value is not None else None


def _text(raw):
    try:
        value = raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else raw.decode("utf-8-sig")
        if any(ord(char) < 32 and char not in "\r\n\t" for char in value):
            _fail("UNSUPPORTED_FORMAT")
        return value
    except UnicodeError:
        _fail("UNSUPPORTED_FORMAT")


def _utc(value):
    if type(value) is not str:
        return None
    match = _UTC.fullmatch(value)
    if not match:
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        # Seven digits retain 100-ns source precision without claiming clock accuracy.
        return match[1] + "." + (match[2] or "").ljust(7, "0") + "Z"
    except ValueError:
        return None


def _integer(value, maximum=2**64 - 1):
    if type(value) is str and re.fullmatch(r"[0-9]{1,20}", value) and int(value) <= maximum:
        return int(value)
    return None


def _one(node, name, required=False):
    matches = node.findall(_NS + name)
    if len(matches) > 1 or required and len(matches) != 1:
        _fail("AMBIGUOUS_EVENT")
    return matches[0] if matches else None


def _xml(raw):
    if len(raw) > MAX_XML_BYTES:
        _fail("XML_LIMIT")
    value = _text(raw)
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", value, re.I):
        _fail("XML_DECLARATION_REFUSED")
    try:
        depth = nodes = 0
        parser = ET.iterparse(io.StringIO(value), events=("start", "end"))
        for kind, node in parser:
            if kind == "start":
                depth += 1
                nodes += 1
                if depth > 32 or nodes > 8192 or len(node.attrib) > 32 or any(len(value) > 4096 for value in node.attrib.values()):
                    _fail("XML_LIMIT")
            else:
                if len(node.text or "") > 65536 or len(node.tail or "") > 65536:
                    _fail("XML_LIMIT")
                depth -= 1
        root = parser.root
    except (ET.ParseError, ValueError) as error:
        if isinstance(error, EvidenceError):
            raise
        _fail("MALFORMED_XML")
    if root.tag == _NS + "Event":
        events = [root]
    elif root.tag in {"Events", _NS + "Events"} and all(child.tag == _NS + "Event" for child in root):
        events = list(root)
    else:
        _fail("UNSUPPORTED_FORMAT")
    if not 1 <= len(events) <= MAX_EVENTS:
        _fail("XML_LIMIT")
    rows = []
    for position, event in enumerate(events, 1):
        system = _one(event, "System", required=True)
        provider = _one(system, "Provider", required=True)
        event_id_node = _one(system, "EventID", required=True)
        event_id = _integer(event_id_node.text, 65535)
        if event_id is None:
            _fail("MALFORMED_EVENT")
        created, record, execution = (_one(system, key) for key in ("TimeCreated", "EventRecordID", "Execution"))
        name = provider.get("Name") or provider.get("EventSourceName")
        classification = "unclassified_windows_event"
        if name == "Application Error" and event_id == 1000:
            classification = "application_error_reported"
        elif name == "Windows Error Reporting" and event_id == 1001:
            classification = "wer_report_present"
        # Source strings (Computer/SID/messages/paths/AppName/ModuleName) remain private.
        # Only exact known executable names can produce a declared game association.
        data = _one(event, "EventData")
        game_id = None
        if classification == "application_error_reported" and data is not None:
            app_names = [child.text for child in data if child.tag == _NS + "Data" and child.get("Name") == "AppName"]
            if len(app_names) == 1 and type(app_names[0]) is str:
                game_id = {"skyrimse.exe": "skyrim-special-edition", "cyberpunk2077.exe": "cyberpunk-2077"}.get(app_names[0].lower())
        rows.append({"source_order": position, "kind": classification, "event_id": event_id,
            "event_record_id": None if record is None else _integer(record.text),
            "reported_utc": None if created is None else _utc(created.get("SystemTime")),
            "clock_basis": "provider_system_time", "clock_uncertainty_ms": None,
            "reporter_process_id": None if execution is None else _integer(execution.get("ProcessID"), 2**32 - 1),
            "game_id": game_id, "game_association": "source_declared_not_runtime_verified" if game_id else "unknown",
            "failure_reported": classification == "application_error_reported"})
    return rows, {"event_count": len(rows), "unverified_tail_bytes": None, "clean_end": None}


def _preview(record, adapter, journal):
    if type(adapter) is not str or adapter not in _ADAPTERS:
        _fail("INVALID_ADAPTER")
    if adapter == "auto":
        adapter = {".xml": "windows_event_xml", ".jsonl": "hub_journal", ".txt": "opaque_text", ".log": "opaque_text"}.get(record["path"].suffix.lower())
        if adapter is None:
            _fail("UNSUPPORTED_FORMAT")
    raw = record["raw"]
    if adapter == "windows_event_xml":
        rows, coverage = _xml(raw)
    elif adapter == "hub_journal":
        inspected = journal._inspect(raw)
        if not inspected["verified_count"]:
            _fail("NO_VERIFIED_PREFIX")
        rows = [{"source_order": item["seq"],
                 "kind": item["kind"] if item["kind"] in _JOURNAL_KINDS else "other_journal_event",
                 "reported_utc": _utc(item["utc"]), "monotonic_ns": item["monotonic_ns"],
                 "clock_basis": "journal_process_monotonic_and_utc", "clock_uncertainty_ms": None,
                 "failure_reported": item["kind"] == "action_failed"}
                for item in inspected["verified_records"]]
        coverage = {"event_count": len(rows), "verified_bytes": inspected["verified_bytes"],
                    "unverified_tail_bytes": len(raw) - inspected["verified_bytes"],
                    "valid": inspected["valid"], "clean_end": inspected["clean_end"],
                    "journal_clock_id": inspected["verified_records"][0]["clock_id"],
                    "utc_backstep_count": sum(rows[index]["reported_utc"] < rows[index - 1]["reported_utc"]
                                              for index in range(1, len(rows))),
                    "replay_allowed": False}
    else:
        _text(raw)  # Text only; no invented regex diagnosis or metadata from filenames.
        rows = []
        coverage = {"event_count": 0, "unverified_tail_bytes": None, "clean_end": None,
                    "interpretation": "opaque_private_attachment"}
    return {"schema_version": 1, "evidence_version": VERSION, "adapter": adapter,
            "backend": {"journal_version": journal.VERSION, "journal_source_sha256": journal._authored_hash},
            "source_sha256": record["sha256"], "source_bytes": len(raw), "coverage": coverage,
            "events": rows, "execution": "none", "runtime_verification": False,
            "limitations": list(_LIMITATIONS)}


def inspect_source(source, adapter="auto", expected_sha256=None):
    expected = _expected(expected_sha256)
    journal = _journal()
    record = _capture(source, journal)
    if expected is not None and record["sha256"] != expected:
        _fail("SOURCE_CHANGED")
    result = _preview(record, adapter, journal)
    _assert_current([record], journal)
    return result


def _assert_current(records, journal):
    try:
        path, raw, identity = journal._read_source(_BASE / "GameToolJournal.py")
        if len(raw) > 1024 * 1024 or identity != journal._authored_identity or \
                hashlib.sha256(raw).hexdigest() != journal._authored_hash:
            _fail("MODULE_CHANGED")
    except EvidenceError:
        raise
    except Exception:
        _fail("MODULE_CHANGED")
    for record in records:
        current = _capture(record["path"], journal)
        if current["identity"] != record["identity"] or current["sha256"] != record["sha256"]:
            _fail("SOURCE_CHANGED")


def _prepare(assignments):
    if type(assignments) is not list or not 1 <= len(assignments) <= MAX_SOURCES:
        _fail("SOURCE_COUNT")
    journal, records, sources, timeline, seen = _journal(), [], [], [], set()
    total = 0
    for index, item in enumerate(assignments, 1):
        if type(item) is not dict or not {"path"} <= set(item) <= {"path", "adapter", "expected_sha256"}:
            _fail("INVALID_ASSIGNMENT")
        expected = _expected(item.get("expected_sha256"))
        record = _capture(item["path"], journal)
        total += len(record["raw"])
        if total > MAX_TOTAL_BYTES:
            _fail("TOTAL_LIMIT")
        if record["sha256"] in seen:
            _fail("DUPLICATE_SOURCE")
        seen.add(record["sha256"])
        if expected is not None and record["sha256"] != expected:
            _fail("SOURCE_CHANGED")
        preview = _preview(record, item.get("adapter", "auto"), journal)
        source_id = "source-" + str(index).zfill(3)
        sources.append({key: preview[key] for key in ("adapter", "source_sha256", "source_bytes", "coverage")})
        sources[-1]["id"] = source_id
        timeline.extend({"source_id": source_id, **row} for row in preview["events"])
        if len(timeline) > MAX_TIMELINE:
            _fail("TIMELINE_LIMIT")
        record["preview"] = preview
        records.append(record)
    # Source order remains explicit. Sorting wall times does not prove causality/alignment.
    timeline.sort(key=lambda row: (row["reported_utc"] is None, row["reported_utc"] or "", row["source_id"], row["source_order"]))
    failures = [row for row in timeline if row["failure_reported"]]
    timed = [row for row in failures if row["reported_utc"] is not None]
    first = None
    if timed:
        first = {"reported_utc": timed[0]["reported_utc"], "candidates": [
            {"source_id": row["source_id"], "source_order": row["source_order"], "kind": row["kind"]}
            for row in timed if row["reported_utc"] == timed[0]["reported_utc"]],
            "ordering_certainty": "unmeasured_clock_error_not_causal_order"}
    report = {"schema_version": 1, "evidence_version": VERSION, "scope": "offline_selected_saved_evidence",
        "backend": {"journal_version": journal.VERSION, "journal_source_sha256": journal._authored_hash},
        "execution": "none", "runtime_verification": False, "replay_allowed": False,
        "sources": sources, "timeline": timeline, "first_reported_failure": first,
        "untimed_failure_count": len(failures) - len(timed),
        "status": "EVIDENCE_ONLY", "crash_cause": None, "memory_exhaustion_verified": False,
        "limitations": list(_LIMITATIONS)}
    _assert_current(records, journal)
    return report, records, journal


def build_packet(assignments):
    """Read-only portable preview; no private paths or raw event/log payloads."""
    return _prepare(assignments)[0]


def _json(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _html(report):
    payload = html.escape(_json(report).decode("utf-8"))
    return ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Saved evidence — not a diagnosis</title>'
            '<h1>Selected saved evidence</h1><p>Evidence only. No live verification or crash-cause claim. '
            'Private originals require review before sharing.</p><pre>' + payload + '</pre></html>').encode("utf-8")


def export_packet(assignments, output_directory):
    """Explicit new private bundle. Manifest is written last; existing paths refused.

    fsync/readback covers individual files, not every power/storage failure or
    an atomic whole-directory commit. A missing manifest means incomplete export.
    """
    report, records, journal = _prepare(assignments)
    try:
        target = journal._no_links(output_directory)
        if target.exists() or not target.parent.is_dir() or target == _BASE.parent or _BASE.parent in target.parents:
            _fail("DESTINATION_REFUSED")
        parent_id = journal._object_identity(target.parent.stat())
        payloads = {"evidence.json": _json(report), "evidence.html": _html(report)}
        receipt = {"schema_version": 1, "evidence_version": VERSION, "privacy": "private_originals_and_locators",
                   "coverage": "captured original bytes; hashes/readback verified; restore not tested", "sources": []}
        for index, record in enumerate(records, 1):
            preview = record["preview"]
            suffix = {"windows_event_xml": ".xml", "hub_journal": ".jsonl", "opaque_text": ".txt"}[preview["adapter"]]
            alias = "source-" + str(index).zfill(3) + suffix
            payloads[alias] = record["raw"]
            receipt["sources"].append({"archive_name": alias, "private_source_path": str(record["path"]),
                                        "sha256": record["sha256"], "adapter": preview["adapter"]})
        payloads["private-receipt.json"] = _json(receipt)
        manifest = {"schema_version": 1, "privacy": "private_packet_review_before_sharing", "complete": True,
                    "files": [{"name": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                              for name, raw in payloads.items()]}
        payloads["manifest.json"] = _json(manifest)
        with tempfile.TemporaryDirectory(prefix=".saved-evidence-", dir=target.parent) as stage_name:
            stage = Path(stage_name)
            for name, raw in payloads.items():
                with (stage / name).open("xb") as handle:
                    if handle.write(raw) != len(raw):
                        _fail("WRITE_FAILED")
                    handle.flush()
                    os.fsync(handle.fileno())
                if (stage / name).read_bytes() != raw:
                    _fail("READBACK_FAILED")
            _assert_current(records, journal)
            journal._no_links(target)
            if journal._object_identity(target.parent.stat()) != parent_id:
                _fail("DESTINATION_CHANGED")
            target.mkdir()
            owned_id = journal._object_identity(target.stat())
            published, success = [], False
            try:
                for name, raw in payloads.items():
                    journal._no_links(target)
                    if journal._object_identity(target.stat()) != owned_id:
                        _fail("DESTINATION_CHANGED")
                    os.link(stage / name, target / name)
                    published.append(name)
                    if (target / name).read_bytes() != raw:
                        _fail("READBACK_FAILED")
                _assert_current(records, journal)
                journal._no_links(target)
                if journal._object_identity(target.stat()) != owned_id:
                    _fail("DESTINATION_CHANGED")
                for name, raw in payloads.items():
                    if (target / name).read_bytes() != raw or not os.path.samefile(target / name, stage / name):
                        _fail("DESTINATION_CHANGED")
                success = True
                return {"status": "EVIDENCE_ONLY", "source_count": len(records), "execution": "none",
                        "runtime_verification": False, "replay_allowed": False,
                        "report_sha256": hashlib.sha256(payloads["evidence.json"]).hexdigest(),
                        "manifest_sha256": hashlib.sha256(payloads["manifest.json"]).hexdigest(),
                        "coverage": receipt["coverage"], "privacy": "private_packet_review_before_sharing"}
            finally:
                if not success:
                    # Never remove a replacement directory or another writer's bytes.
                    try:
                        journal._no_links(target)
                        if journal._object_identity(target.stat()) == owned_id:
                            for name in reversed(published):
                                try:
                                    if os.path.samefile(target / name, stage / name):
                                        (target / name).unlink()
                                except OSError:
                                    pass
                            target.rmdir()  # Non-recursive; foreign content prevents removal.
                    except (OSError, ValueError):
                        pass
    except EvidenceError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError):
        _fail("EXPORT_FAILED")
