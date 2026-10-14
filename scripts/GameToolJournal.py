"""Bounded, append-only evidence journal; no input, launch or replay service.

Acknowledged records have been flushed and fsynced. This supports recovery of
the verified complete prefix after an interrupted helper process, not a promise
against every filesystem, hardware, power-loss or storage-controller failure.
Hashes detect accidental changes; they do not authenticate the author. Metadata
is private local evidence: callers must exclude typed input, credentials and
secrets. Recovered copies never grant action permission or resume a session.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import tempfile
import threading
import time
import uuid


VERSION = "0.1.0"
SCHEMA_VERSION = 1
MAX_LINE_BYTES = 64 * 1024
MAX_JOURNAL_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 4096
MAX_DEPTH = 8
MAX_NODES = 4096
_ZERO = "0" * 64
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_KIND = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
_CLOCK = re.compile(r"[0-9a-f]{32}\Z")
_WRITER_VERSION = re.compile(
    r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*)?"
    r"(?:\+[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*)?\Z")
_TERMINAL = {"session_closed", "session_cancelled"}
_FIELDS = {"schema_version", "journal_version", "seq", "utc", "monotonic_ns",
           "clock_id", "kind", "data", "prev_sha256", "sha256"}
CAVEAT = ("Verified prefix recovery only; unflushed tails or storage failures may "
          "lose evidence. An open or interrupted journal does not identify a game "
          "crash. Monotonic timestamps apply only to their clock_id. No replay or "
          "automatic resumption is permitted; hashes are not authentication.")


class JournalError(ValueError):
    """Path-free validation or durability failure."""


class JournalBusy(JournalError):
    """Another cooperating writer owns the OS lock."""


def _fail(message):
    raise JournalError(message)


def _bounded(value, depth=0, budget=None):
    budget = [0] if budget is None else budget
    budget[0] += 1
    if depth > MAX_DEPTH or budget[0] > MAX_NODES:
        _fail("Journal data exceeds its nesting or work limit.")
    if type(value) is dict:
        if len(value) > 256:
            _fail("Journal data has too many fields.")
        for key, item in value.items():
            if type(key) is not str or not key or len(key) > 128 or any(ord(c) < 32 for c in key):
                _fail("Invalid journal field name.")
            _bounded(item, depth + 1, budget)
    elif type(value) is list:
        if len(value) > 512:
            _fail("Journal data list is too large.")
        for item in value:
            _bounded(item, depth + 1, budget)
    elif type(value) is str:
        if len(value) > 4096 or any(ord(c) < 32 and c not in "\r\n\t" for c in value):
            _fail("Invalid or overlong journal text.")
    elif value is None or type(value) is bool:
        pass
    elif type(value) in (int, float):
        if abs(value) > 1e100 or not math.isfinite(value):
            _fail("Journal data contains a nonfinite or oversized number.")
    else:
        _fail("Unsupported journal data value.")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail("Duplicate journal field; ambiguous evidence refused.")
        result[key] = value
    return result


def _no_links(path):
    try:
        locator = os.fspath(path)
    except (TypeError, ValueError):
        _fail("Invalid local journal path.")
    if not isinstance(locator, str) or not locator or len(locator) > 4096 or any(ord(c) < 32 for c in locator):
        _fail("Invalid local journal path.")
    path = Path(locator).absolute()
    for component in (path, *path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            _fail("Journal path could not be checked safely.")
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            _fail("Linked or reparse journal paths are not supported.")
    return path


def _identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _object_identity(info):
    return info.st_dev, info.st_ino


def _read_source(path):
    try:
        path = _no_links(path)
        pathname_before = path.stat()
        if not stat.S_ISREG(pathname_before.st_mode) or pathname_before.st_size > MAX_JOURNAL_BYTES:
            _fail("Journal must be a regular file within the sixteen-MiB limit.")
        with path.open("rb") as source:
            before = os.fstat(source.fileno())
            if (not stat.S_ISREG(before.st_mode) or before.st_size > MAX_JOURNAL_BYTES or
                    _identity(before) != _identity(pathname_before)):
                _fail("Journal must be a regular file within the sixteen-MiB limit.")
            raw = source.read(MAX_JOURNAL_BYTES + 1)
            after = os.fstat(source.fileno())
        current = _no_links(path).stat()
        if len(raw) > MAX_JOURNAL_BYTES or _identity(before) != _identity(after) or _identity(after) != _identity(current):
            _fail("Journal changed during its bounded read; inspect again.")
        return path, raw, _identity(current)
    except JournalError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError):
        _fail("Journal could not be read safely.")


def _canonical(value):
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, OverflowError):
        _fail("Journal data could not be encoded safely.")


def _digest(record):
    return hashlib.sha256(_canonical({key: value for key, value in record.items()
                                      if key != "sha256"})).hexdigest()


def _lock(handle):
    try:
        # The reserved lock byte lies beyond the maximum journal extent: Windows
        # byte-range locks would otherwise block harmless reads of live evidence.
        handle.seek(MAX_JOURNAL_BYTES + 1)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        raise JournalBusy("Journal is owned by another cooperating writer.") from None


def _unlock(handle):
    try:
        handle.seek(MAX_JOURNAL_BYTES + 1)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except OSError:
        pass  # Closing the handle also releases the OS-owned lock.


def _remove_owned(path, identity):
    try:
        if _object_identity(_no_links(path).stat()) == identity:
            path.unlink()
    except (OSError, JournalError):
        pass


class Journal:
    """One fresh journal writer. Existing journals are inspection-only evidence."""

    def __init__(self):
        self._handle = None
        self._guard = threading.RLock()
        self._closed = False
        self._poisoned = False
        self._terminal = False
        self._seq = 0
        self._bytes = 0
        self._prev = _ZERO
        self._last_monotonic = -1
        self._clock_id = uuid.uuid4().hex

    @classmethod
    def create(cls, path, metadata):
        if type(metadata) is not dict:
            _fail("Journal metadata must be a bounded object.")
        _bounded(metadata)
        # Validate an entire first record before creating any filesystem object.
        if len(_canonical(metadata)) > MAX_LINE_BYTES - 1024:
            _fail("Journal metadata exceeds its record limit.")
        writer = cls()
        path = _no_links(path)
        if not path.parent.is_dir():
            _fail("The explicit journal output directory must already exist.")
        try:
            fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
            writer._handle = os.fdopen(fd, "r+b", buffering=0)
            info = os.fstat(writer._handle.fileno())
            writer._identity = _object_identity(info)
            writer._observed_identity = _identity(info)
            writer.path = path
            _lock(writer._handle)
            writer.append("journal_created", metadata)
            return writer
        except JournalError:
            writer.close()
            raise
        except FileExistsError:
            _fail("Journal destination already exists; choose a new file.")
        except (OSError, RuntimeError, ValueError):
            writer.close()
            _fail("Fresh journal could not be created durably.")

    def append(self, kind, data=None):
        with self._guard:
            if self._closed or self._handle is None:
                _fail("Journal writer is closed.")
            if self._poisoned:
                _fail("Journal writer failed durability; inspect evidence instead of continuing.")
            if self._terminal:
                _fail("A terminal session record cannot be followed by more events.")
            if type(kind) is not str or not _KIND.fullmatch(kind):
                _fail("Invalid journal event kind.")
            if kind == "journal_created" and self._seq:
                _fail("Journal creation metadata cannot be appended twice.")
            if data is not None and type(data) is not dict:
                _fail("Journal event data must be a bounded object or null.")
            _bounded(data)
            if self._seq >= MAX_RECORDS:
                _fail("Journal record limit reached; close this session.")
            monotonic = time.monotonic_ns()
            if monotonic < self._last_monotonic:
                _fail("Monotonic clock moved backwards; stop the session.")
            record = {"schema_version": SCHEMA_VERSION, "journal_version": VERSION,
                      "seq": self._seq + 1,
                      "utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                      "monotonic_ns": monotonic, "clock_id": self._clock_id,
                      "kind": kind, "data": deepcopy(data), "prev_sha256": self._prev}
            record["sha256"] = _digest(record)
            line = _canonical(record) + b"\n"
            if len(line) > MAX_LINE_BYTES or self._bytes + len(line) > MAX_JOURNAL_BYTES:
                _fail("Journal record or total byte limit reached.")
            try:
                current = _no_links(self.path).stat()
                handle_info = os.fstat(self._handle.fileno())
                if (_object_identity(current) != self._identity or
                        _identity(current) != _identity(handle_info) or
                        _identity(current) != self._observed_identity or
                        current.st_size != self._bytes):
                    _fail("Journal identity or size changed; no further append is safe.")
                self._handle.seek(0, os.SEEK_END)
                if self._handle.write(line) != len(line):
                    _fail("Journal short write; the event was not acknowledged.")
                self._handle.flush()
                os.fsync(self._handle.fileno())
                self._seq += 1
                self._bytes += len(line)
                self._prev = record["sha256"]
                self._last_monotonic = monotonic
                self._terminal = kind in _TERMINAL
                self._observed_identity = _identity(os.fstat(self._handle.fileno()))
                return deepcopy(record)
            except (OSError, RuntimeError, JournalError):
                self._poisoned = True
                _fail("Journal write or durability check failed; event not acknowledged. Stop and inspect evidence.")

    def close(self):
        with self._guard:
            if self._handle is not None:
                _unlock(self._handle)
                self._handle.close()
                self._handle = None
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


def _inspect(raw):
    records = []
    verified_bytes = 0
    previous = _ZERO
    clock_id = None
    last_monotonic = -1
    error = None
    # splitlines is safe after the sixteen-MiB bounded read; parsing stops at
    # the first bad record, never jumping over missing or corrupted evidence.
    for line in raw.splitlines(keepends=True):
        try:
            if len(records) >= MAX_RECORDS:
                _fail("Journal exceeds its record limit.")
            if len(line) > MAX_LINE_BYTES:
                _fail("Journal line exceeds its byte limit.")
            if not line.endswith(b"\n"):
                _fail("Incomplete final journal line; recover the complete prefix only.")
            if records and records[-1]["kind"] in _TERMINAL:
                _fail("Evidence appears after a terminal session event.")
            record = json.loads(line.decode("utf-8"), object_pairs_hook=_pairs,
                                parse_constant=lambda _value: _fail("Nonfinite JSON value refused."))
            if type(record) is not dict or set(record) != _FIELDS:
                _fail("Unsupported or incomplete journal record shape.")
            if (type(record["schema_version"]) is not int or
                    record["schema_version"] != SCHEMA_VERSION):
                _fail("Unsupported journal schema.")
            # The writer's code release is provenance, not the data format.
            # Keep its original value/hash untouched while applying this schema's
            # full field, sequence, clock and hash checks. Compatible old evidence
            # must not become unreadable solely after a module-version update.
            if (type(record["journal_version"]) is not str or
                    not 1 <= len(record["journal_version"]) <= 64 or
                    not _WRITER_VERSION.fullmatch(record["journal_version"])):
                _fail("Invalid journal writer-version provenance.")
            if type(record["seq"]) is not int or record["seq"] != len(records) + 1:
                _fail("Journal sequence gap or duplicate detected.")
            if type(record["kind"]) is not str or not _KIND.fullmatch(record["kind"]):
                _fail("Invalid journal event kind.")
            if not records and record["kind"] != "journal_created":
                _fail("Journal creation record is missing.")
            if records and record["kind"] == "journal_created":
                _fail("Duplicate journal creation record.")
            if record["data"] is not None and type(record["data"]) is not dict:
                _fail("Journal event data is not a bounded object.")
            if not records and type(record["data"]) is not dict:
                _fail("Journal creation metadata is missing.")
            _bounded(record["data"])
            if type(record["clock_id"]) is not str or not _CLOCK.fullmatch(record["clock_id"]):
                _fail("Invalid journal clock identity.")
            if clock_id is not None and record["clock_id"] != clock_id:
                _fail("A journal cannot resume under another process clock.")
            if (type(record["monotonic_ns"]) is not int or record["monotonic_ns"] < 0 or
                    record["monotonic_ns"] > 2 ** 63 - 1 or
                    record["monotonic_ns"] < last_monotonic):
                _fail("Invalid or backwards monotonic journal clock.")
            if type(record["utc"]) is not str or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z", record["utc"]):
                _fail("Invalid journal UTC timestamp.")
            datetime.fromisoformat(record["utc"].replace("Z", "+00:00"))
            if record["prev_sha256"] != previous or type(record["sha256"]) is not str or not _SHA.fullmatch(record["sha256"]) or _digest(record) != record["sha256"]:
                _fail("Journal hash chain mismatch; do not skip the damaged record.")
            records.append(record)
            verified_bytes += len(line)
            previous = record["sha256"]
            clock_id = record["clock_id"]
            last_monotonic = record["monotonic_ns"]
        except JournalError as exc:
            error = str(exc)
            break
        except (UnicodeError, json.JSONDecodeError, ValueError, TypeError, RecursionError, OverflowError):
            error = "Malformed journal record; recover only its verified complete prefix."
            break
    if not records and error is None:
        error = "Journal is empty; no verified creation evidence exists."
    valid = error is None
    return {"valid": valid, "clean_end": bool(valid and records and records[-1]["kind"] in _TERMINAL),
            "verified_records": records, "verified_count": len(records),
            "verified_bytes": verified_bytes,
            "source_sha256": hashlib.sha256(raw).hexdigest(), "source_bytes": len(raw),
            "error": error, "recovery_required": not valid, "replay_allowed": False,
            "safety_caveat": CAVEAT}


def inspect_journal(path):
    """Read stable bounded evidence. No writes, repair, locks or replay."""
    _path, raw, _identity_value = _read_source(path)
    return _inspect(raw)


def recover_journal(source, destination, expected_sha256=None):
    """Publish a new verified-prefix evidence copy; never repair the original."""
    source, raw, before = _read_source(source)
    result = _inspect(raw)
    if expected_sha256 is not None and (type(expected_sha256) is not str or not _SHA.fullmatch(expected_sha256) or expected_sha256 != result["source_sha256"]):
        _fail("Journal changed since inspection; reload before recovery.")
    if not result["verified_count"]:
        _fail("No verified complete records are available for recovery.")
    destination = _no_links(destination)
    if os.path.normcase(str(source)) == os.path.normcase(str(destination)):
        _fail("Recovery must use a different new destination.")
    if destination.exists():
        _fail("Recovery destination already exists; original and existing evidence are preserved.")
    if not destination.parent.is_dir():
        _fail("The explicit recovery directory must already exist.")
    prefix = raw[:result["verified_bytes"]]
    stage = None
    owned = None
    published = False
    success = False
    try:
        fd, filename = tempfile.mkstemp(prefix=".journal-", suffix=".staged", dir=destination.parent)
        stage = Path(filename)
        with os.fdopen(fd, "wb") as target:
            owned = _object_identity(os.fstat(target.fileno()))
            if target.write(prefix) != len(prefix):
                _fail("Recovery short write; no complete copy was published.")
            target.flush()
            os.fsync(target.fileno())
        copied = inspect_journal(stage)
        if (not copied["valid"] or copied["verified_count"] != result["verified_count"] or
                copied["source_sha256"] != hashlib.sha256(prefix).hexdigest() or
                _object_identity(_no_links(stage).stat()) != owned):
            _fail("Recovery copy verification failed.")
        _current_path, current_raw, current_identity = _read_source(source)
        if current_identity != before or hashlib.sha256(current_raw).hexdigest() != result["source_sha256"]:
            _fail("Journal changed during recovery; inspect again.")
        _no_links(destination)
        os.link(stage, destination)  # atomic, no-overwrite publication on supported filesystems
        published = True
        _current_path, current_raw, current_identity = _read_source(source)
        if current_identity != before or hashlib.sha256(current_raw).hexdigest() != result["source_sha256"]:
            _fail("Journal changed at recovery publication; no recovery was acknowledged.")
        final = inspect_journal(destination)
        if (not final["valid"] or final["source_sha256"] != copied["source_sha256"] or
                _object_identity(_no_links(destination).stat()) != owned):
            _fail("Published recovery changed; no recovery was acknowledged.")
        receipt = {"schema_version": 1, "journal_version": VERSION,
                   "source_sha256": result["source_sha256"],
                   "destination_sha256": final["source_sha256"],
                   "verified_count": result["verified_count"],
                   "verified_bytes": result["verified_bytes"],
                   "discarded_tail_bytes": len(raw) - result["verified_bytes"],
                   "source_was_valid": result["valid"], "clean_end": final["clean_end"],
                   "replay_allowed": False, "safety_caveat": CAVEAT}
        success = True
        return receipt
    except JournalError:
        raise
    except (OSError, RuntimeError, TypeError, ValueError):
        _fail("Recovery could not be published safely; choose a supported new destination.")
    finally:
        if owned is not None:
            if published and not success:
                _remove_owned(destination, owned)
            if stage is not None:
                _remove_owned(stage, owned)
