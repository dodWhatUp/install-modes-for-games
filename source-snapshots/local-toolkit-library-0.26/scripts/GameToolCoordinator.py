"""Opt-in offline session coordination for fixed saved-data readers only.

Construction is inert. Explicit start creates one fresh append-only journal;
existing journals are evidence, never replay authority. This coordinator has no
game, input, launch, settings, collector or recording capability and does not
reserve the desktop. Cancellation/deadlines gate acceptance of bounded reads,
not hard preemption of a Python function or control of another application.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import math
import os
from pathlib import Path
import re
import stat
import threading
import time
import types
import uuid


VERSION = "0.4.0"
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_MODULE_BYTES = 1024 * 1024
MAX_SESSION_SECONDS = 3600
_SCOPE = "offline_saved_data"
_BASE = Path(__file__).absolute().parent
_LABEL = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}\Z")
_METRIC = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
_SHA = re.compile(r"[a-fA-F0-9]{64}\Z")
_SIBLINGS = {
    "journal": ("GameToolJournal.py", "0.1.0"),
    "saved_report": ("GameToolReportImport.py", "0.1.0"),
    "comparison": ("GameToolComparison.py", "0.1.1"),
    "crash_evidence": ("GameToolCrashEvidence.py", "0.1.0"),
    "workflow": ("GameToolWorkflow.py", "0.1.0"),
    "readiness": ("GameToolReadiness.py", "0.1.0"),
}
_ADAPTERS = {"auto", "cyberpunk_benchmark_summary", "presentmon_gui_stats"}
_PROVIDERS = {"cyberpunk_benchmark_summary": "Cyberpunk 2077 built-in benchmark",
              "presentmon_gui_stats": "PresentMon GUI"}
_REASONS = {"user": "user", "shutdown": "shutdown", "window closed": "window_closed",
            "window_closed": "window_closed", "expired": "expired"}
_ERRORS = {
    "INVALID_METADATA": "Use a short simple label, not a path, command or typed payload.",
    "INVALID_LIFETIME": "Offline session lifetime must be between one and 3600 seconds.",
    "INVALID_CLOCK": "The session clock is invalid or moved backwards; no result was accepted.",
    "SESSION_NOT_STARTED": "Explicitly start a fresh offline session before using its readers.",
    "SESSION_ALREADY_USED": "This owner has already been used; create a new coordinator for a fresh session.",
    "SESSION_ENDED": "This session has ended; no action was dispatched or resumed.",
    "SESSION_EXPIRED": "This offline session expired; no result was accepted or automatically resumed.",
    "SESSION_CANCELLED": "This offline session was cancelled; no result was accepted.",
    "ACTION_BUSY": "This coordinator already has an in-flight saved-data read.",
    "INVALID_ADAPTER": "Only the fixed supported saved-report adapters are available.",
    "INVALID_METRIC": "Choose a valid metric identifier from the selected saved dataset.",
    "INVALID_HASH": "An expected source hash must be a SHA-256 hexadecimal string.",
    "SOURCE_UNAVAILABLE": "The selected source could not be read safely within its bounded file limit.",
    "SOURCE_CHANGED": "The selected source changed; explicitly inspect the new source before retrying.",
    "MODULE_UNAVAILABLE": "A fixed sibling module is unavailable or unsupported; no alternate executor was used.",
    "MODULE_CHANGED": "A fixed sibling source changed; start a new coordinator instead of using stale code.",
    "ADAPTER_REFUSED": "The fixed saved-data reader refused this source; no game or provider was started.",
    "RESULT_INVALID": "The saved-data reader returned an unsupported result; it was not accepted.",
    "JOURNAL_FAILURE": "The journal did not acknowledge durable evidence; ownership was closed and no result accepted.",
    "JOURNAL_CREATE_FAILED": "A fresh journal could not be created exclusively; existing evidence was not reopened.",
}
_LIMITATIONS = [
    "Only explicitly selected saved evidence/reports/datasets are read; no live tools are controlled.",
    "Ownership is cooperative and journal-local, not an OS-wide desktop or input lock.",
    "Deadlines/cancellation prevent result acceptance; bounded Python reads are not hard-preempted.",
    "Journal recovery is evidence-only, not automatic resumption, crash-cause proof or runtime FG verification.",
    "Session labels are explicit metadata; review imported source content before sharing a result.",
]


class CoordinatorError(ValueError):
    """Fixed path-free failure, with an inspectable stable reason code."""

    def __init__(self, code):
        self.code = code if code in _ERRORS else "ADAPTER_REFUSED"
        super().__init__(_ERRORS[self.code])


def _fail(code):
    raise CoordinatorError(code)


def _label(value):
    if type(value) is not str or not _LABEL.fullmatch(value) or not value.strip():
        _fail("INVALID_METADATA")
    return value.strip()


def _expected_hash(value):
    if value is not None and (type(value) is not str or not _SHA.fullmatch(value)):
        _fail("INVALID_HASH")
    return None if value is None else value.lower()


def capabilities():
    """Code-owned capabilities; declarations are not permission to execute."""
    return {"schema_version": 1, "coordinator_version": VERSION, "scope": _SCOPE,
            "execution": "offline_only", "runtime_verification": False,
            "capabilities": {
                "saved_report": {"operation": "inspect_saved_report", "read_only_source": True,
                    "adapters": sorted(_ADAPTERS), "adapter_version": "0.1.0",
                    "side_effects": "append compact evidence to this explicitly started journal only"},
                "comparison": {"operation": "inspect_comparison", "read_only_source": True,
                    "adapter_version": "0.1.1",
                    "side_effects": "append compact evidence to this explicitly started journal only"},
                "crash_evidence": {"operation": "inspect_crash_evidence", "read_only_source": True,
                    "adapter_version": "0.1.0", "source_bytes": 16 * 1024 * 1024,
                    "adapters": ["auto", "hub_journal", "opaque_text", "windows_event_xml"],
                    "side_effects": "append compact evidence to this explicitly started journal only"},
                "workflow": {"operation": "inspect_workflow", "read_only_source": True,
                    "adapter_version": "0.1.0", "source_bytes": 1024 * 1024,
                    "side_effects": "append compact plan verdict/counts to this explicitly started journal only"},
                "readiness": {"operation": "inspect_readiness", "read_only_source": True,
                    "adapter_version": "0.1.0", "source_bytes": 1024 * 1024,
                    "side_effects": "append compact declared/mock status and counts only; no capture or scenario runner"}},
            "unavailable": ["arbitrary_commands", "custom_executors", "game_input", "launch",
                "settings_write", "collectors", "benchmarks", "recording", "automatic_replay"],
            "limits": {"source_bytes": MAX_SOURCE_BYTES, "module_bytes": MAX_MODULE_BYTES,
                       "maximum_session_seconds": MAX_SESSION_SECONDS},
            "limitations": list(_LIMITATIONS)}


def _no_links(locator):
    try:
        locator = os.fspath(locator)
        if type(locator) is not str or not locator or len(locator) > 4096 or any(ord(c) < 32 for c in locator):
            _fail("SOURCE_UNAVAILABLE")
        path = Path(locator).absolute()
        for part in (path, *path.parents):
            metadata = part.lstat()
            if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & \
                    getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
                _fail("SOURCE_UNAVAILABLE")
        return path
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        if isinstance(error, CoordinatorError):
            raise
        _fail("SOURCE_UNAVAILABLE")


def _identity(metadata):
    # Windows Python/filesystem providers disagree on fstat/stat ctime meaning.
    # Use the established file-object identity plus size/mtime and byte hash.
    return metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns


def _capture(path, maximum=MAX_SOURCE_BYTES):
    """Bound the read and require stable opened-file and pathname identity."""
    try:
        path = _no_links(path)
        path_before = path.stat()
        if not stat.S_ISREG(path_before.st_mode) or not 0 < path_before.st_size <= maximum:
            _fail("SOURCE_UNAVAILABLE")
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= maximum or \
                    _identity(path_before) != _identity(before):
                _fail("SOURCE_UNAVAILABLE")
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        current = _no_links(path).stat()
        if len(raw) != before.st_size or len(raw) > maximum or \
                _identity(before) != _identity(after) or _identity(after) != _identity(current):
            _fail("SOURCE_CHANGED")
        return raw, {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                     "identity": _identity(current)}
    except (OSError, RuntimeError, TypeError) as error:
        _fail("SOURCE_UNAVAILABLE")


class Coordinator:
    """One explicit offline owner. No existing-journal reopen/resume operation."""

    def __init__(self, owner="Hub", lifetime_seconds=900, *, clock=None, utc_clock=None):
        self._owner = _label(owner)
        if type(lifetime_seconds) not in (int, float) or abs(lifetime_seconds) > MAX_SESSION_SECONDS or \
                not math.isfinite(lifetime_seconds) or not 1 <= lifetime_seconds <= MAX_SESSION_SECONDS:
            _fail("INVALID_LIFETIME")
        if clock is not None and not callable(clock) or utc_clock is not None and not callable(utc_clock):
            _fail("INVALID_CLOCK")
        self._clock = time.monotonic if clock is None else clock
        self._utc_clock = (lambda: datetime.now(timezone.utc)) if utc_clock is None else utc_clock
        self._lifetime = float(lifetime_seconds)
        self._guard = threading.RLock()
        self._owner_id = uuid.uuid4().hex
        self._session_id = None
        self._state = "idle"
        self._label = None
        self._phase = None
        self._started = self._deadline = self._last_clock = None
        self._started_utc = self._expires_utc = None
        self._journal = None
        self._records = 0
        self._modules = {}
        self._latest_action = None
        self._in_flight = False
        self._failure_code = None

    def _now(self):
        try:
            value = self._clock()
        except Exception:
            _fail("INVALID_CLOCK")
        if type(value) not in (int, float) or abs(value) > 1e15 or not math.isfinite(value) or value < 0 or \
                self._last_clock is not None and value < self._last_clock:
            _fail("INVALID_CLOCK")
        self._last_clock = value
        return float(value)

    def _utc(self):
        try:
            value = self._utc_clock()
            if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
                _fail("INVALID_CLOCK")
            return value.astimezone(timezone.utc)
        except Exception:
            _fail("INVALID_CLOCK")

    def _module(self, key):
        filename, supported = _SIBLINGS[key]  # Only code-owned literal keys call this method.
        path = _BASE / filename
        if key in self._modules:
            self._assert_module_current(key)
            return self._modules[key][0]
        try:
            raw, snapshot = _capture(path, MAX_MODULE_BYTES)
            module = types.ModuleType("_offline_game_tool_" + key)
            module.__file__ = str(path)
            exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
            if getattr(module, "VERSION", None) != supported:
                _fail("MODULE_UNAVAILABLE")
            _, current = _capture(path, MAX_MODULE_BYTES)
            if current != snapshot:
                _fail("MODULE_CHANGED")
            self._modules[key] = (module, snapshot)
            return module
        except CoordinatorError as error:
            if error.code in {"MODULE_CHANGED", "MODULE_UNAVAILABLE"}:
                raise
            _fail("MODULE_UNAVAILABLE")
        except Exception:
            _fail("MODULE_UNAVAILABLE")

    def _assert_module_current(self, key):
        filename = _SIBLINGS[key][0]
        try:
            _, current = _capture(_BASE / filename, MAX_MODULE_BYTES)
            if current != self._modules[key][1]:
                _fail("MODULE_CHANGED")
        except CoordinatorError:
            _fail("MODULE_CHANGED")

    def _assert_modules_current(self):
        for key in tuple(self._modules):
            self._assert_module_current(key)

    def _close_writer(self):
        journal = self._journal
        if journal is not None:
            try:
                journal.close()
                self._journal = None
            except Exception:
                # Preserve the owned handle for a later explicit cleanup retry.
                # Do not assert that ownership released merely because close was requested.
                self._failure_code = "JOURNAL_FAILURE"
                self._state = "failed"

    def _append(self, kind, data):
        try:
            self._assert_module_current("journal")
            record = self._journal.append(kind, data)
            if type(record) is not dict or record.get("seq") != self._records + 1:
                _fail("JOURNAL_FAILURE")
            self._records = record["seq"]
        except Exception:
            self._failure_code = "JOURNAL_FAILURE"
            self._state = "failed"
            if self._in_flight and self._latest_action is not None:
                self._latest_action.update(state="failed", error_code="JOURNAL_FAILURE")
            self._in_flight = False
            self._close_writer()
            _fail("JOURNAL_FAILURE")

    def start(self, journal_path, label="Offline task"):
        """Create exclusively; never append to or replay an earlier journal."""
        with self._guard:
            if self._state != "idle":
                _fail("SESSION_ALREADY_USED")
            label = _label(label)
            now, utc = self._now(), self._utc()
            try:
                expiry_utc = utc + timedelta(seconds=self._lifetime)
            except (ValueError, OverflowError):
                _fail("INVALID_CLOCK")
            journal = self._module("journal")
            session_id = uuid.uuid4().hex
            metadata = {"schema_version": 1, "coordinator_version": VERSION, "scope": _SCOPE,
                "session_id": session_id, "owner_id": self._owner_id, "owner": self._owner,
                "label": label, "lifetime_seconds": self._lifetime,
                "capabilities": sorted(capabilities()["capabilities"]), "execution": "offline_only",
                "runtime_verification": False, "replay_permitted": False}
            try:
                self._journal = journal.Journal.create(journal_path, metadata)
            except Exception:
                self._state = "failed"
                self._failure_code = "JOURNAL_CREATE_FAILED"
                self._close_writer()
                _fail("JOURNAL_CREATE_FAILED")
            self._session_id, self._label, self._phase = session_id, label, "Ready"
            self._started, self._deadline = now, now + self._lifetime
            self._started_utc = utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
            self._expires_utc = expiry_utc.isoformat(timespec="microseconds").replace("+00:00", "Z")
            self._records, self._state = 1, "active"
            self._append("session_started", {"session_id": session_id, "owner_id": self._owner_id,
                "phase": self._phase, "started_utc": self._started_utc,
                "expires_utc_hint": self._expires_utc, "deadline_basis": "process_monotonic"})
            return self.status()

    def status(self):
        """Read-only view. Expiry is enforced on the next explicit operation."""
        with self._guard:
            state, remaining = self._state, None
            if state == "active":
                remaining = max(0.0, self._deadline - self._now())
                if remaining == 0:
                    state = "expired"
            return {"schema_version": 1, "coordinator_version": VERSION, "scope": _SCOPE,
                "state": state, "session_id": self._session_id, "owner_id": self._owner_id,
                "owner": self._owner, "label": self._label, "phase": self._phase,
                "lifetime_seconds": self._lifetime, "remaining_seconds": remaining,
                "started_utc": self._started_utc, "expires_utc_hint": self._expires_utc,
                "latest_action": deepcopy(self._latest_action), "journal_records": self._records,
                "writer_open": self._journal is not None,
                "failure_code": self._failure_code, "execution": "offline_only",
                "runtime_verification": False, "limitations": list(_LIMITATIONS)}

    def _end(self, state, reason_code):
        self._state = state
        if self._in_flight and self._latest_action is not None:
            self._latest_action.update(state="cancelled", error_code="SESSION_EXPIRED" if state == "expired" else "SESSION_CANCELLED")
        self._in_flight = False
        kind = "session_closed" if state == "finished" else "session_cancelled"
        try:
            self._append(kind, {"session_id": self._session_id, "state": state,
                "reason_code": reason_code, "latest_action": deepcopy(self._latest_action)})
        finally:
            self._close_writer()

    def _require_active(self):
        if self._state == "idle":
            _fail("SESSION_NOT_STARTED")
        if self._state != "active":
            _fail("SESSION_EXPIRED" if self._state == "expired" else
                  "SESSION_CANCELLED" if self._state == "cancelled" else "SESSION_ENDED")
        try:
            expired = self._now() >= self._deadline
        except CoordinatorError:
            self._failure_code = "INVALID_CLOCK"
            self._end("failed", "invalid_clock")
            _fail("INVALID_CLOCK")
        if expired:
            self._end("expired", "expired")
            _fail("SESSION_EXPIRED")

    def checkpoint(self, phase):
        with self._guard:
            phase = _label(phase)
            self._require_active()
            if self._in_flight:
                _fail("ACTION_BUSY")
            self._append("checkpoint", {"session_id": self._session_id, "phase": phase})
            self._phase = phase
            return self.status()

    def _begin_action(self, capability):
        with self._guard:
            self._require_active()
            if self._in_flight:
                _fail("ACTION_BUSY")
            self._assert_modules_current()
            action = {"id": uuid.uuid4().hex, "capability": capability, "state": "requested",
                      "source_sha256": None, "verdict": None, "error_code": None}
            self._append("action_requested", {"session_id": self._session_id,
                "action_id": action["id"], "capability": capability, "phase": self._phase})
            self._latest_action, self._in_flight = action, True
            return action["id"]

    def _gate_action(self, action_id):
        with self._guard:
            self._require_active()
            if not self._in_flight or self._latest_action["id"] != action_id:
                _fail("SESSION_CANCELLED")

    def _failed_action(self, action_id, code):
        with self._guard:
            if self._state != "active" or not self._in_flight or self._latest_action["id"] != action_id:
                return
            self._latest_action.update(state="failed", error_code=code)
            self._in_flight = False
            self._append("action_failed", {"session_id": self._session_id,
                "action_id": action_id, "capability": self._latest_action["capability"], "error_code": code})

    def _perform(self, capability, source, expected, operation, maximum=MAX_SOURCE_BYTES):
        action_id = self._begin_action(capability)
        try:
            _, snapshot = _capture(source, maximum)
            if expected is not None and snapshot["sha256"] != expected:
                _fail("SOURCE_CHANGED")
            self._gate_action(action_id)
            backend = self._module(capability)
            result, compact = operation(backend, snapshot)
            self._gate_action(action_id)
            _, current = _capture(source, maximum)
            if current != snapshot:
                _fail("SOURCE_CHANGED")
            self._assert_modules_current()
            with self._guard:
                self._gate_action(action_id)
                self._latest_action.update(state="observed", source_sha256=snapshot["sha256"],
                                           verdict=compact["status"], error_code=None)
                self._append("action_observed", {"session_id": self._session_id,
                    "action_id": action_id, "capability": capability,
                    "source_sha256": snapshot["sha256"], "source_bytes": snapshot["bytes"],
                    "runtime_verification": False, **compact})
                self._in_flight = False
            return deepcopy(result)
        except Exception as error:
            code = error.code if isinstance(error, CoordinatorError) else "ADAPTER_REFUSED"
            self._failed_action(action_id, code)
            if isinstance(error, CoordinatorError):
                raise
            raise CoordinatorError(code) from None

    def inspect_saved_report(self, source, adapter="auto", expected_sha256=None):
        if type(adapter) is not str or adapter not in _ADAPTERS:
            _fail("INVALID_ADAPTER")
        expected = _expected_hash(expected_sha256)
        def operation(backend, snapshot):
            row = backend.inspect_report(source, adapter=adapter)
            if type(row) is not dict or row.get("private_source", {}).get("sha256") != snapshot["sha256"]:
                _fail("SOURCE_CHANGED")
            actual = row.get("adapter")
            if actual not in _PROVIDERS or row.get("provider") != _PROVIDERS[actual] or \
                    type(row.get("metrics")) is not list or len(row["metrics"]) > 512:
                _fail("RESULT_INVALID")
            row = deepcopy(row)
            row.pop("private_source", None)
            row.update(source_sha256=snapshot["sha256"], source_bytes=snapshot["bytes"],
                       execution="offline_only", runtime_verification=False)
            return row, {"adapter": actual, "provider": _PROVIDERS[actual],
                         "metric_count": len(row["metrics"]), "status": "INSPECTED"}
        return self._perform("saved_report", source, expected, operation)

    def inspect_comparison(self, source, metric=None, expected_sha256=None):
        if metric is not None and (type(metric) is not str or not _METRIC.fullmatch(metric)):
            _fail("INVALID_METRIC")
        expected = _expected_hash(expected_sha256)
        def operation(backend, snapshot):
            dataset = backend.load_dataset(source)
            if dataset.get("_source", {}).get("sha256") != snapshot["sha256"]:
                _fail("SOURCE_CHANGED")
            result = backend.compare_dataset(dataset, metric_id=metric)
            if type(result) is not dict or result.get("status") not in {"COMPARABLE", "PARTIAL", "BLOCKED"} or \
                    result.get("runtime_verification") is not False or result.get("execution") != "none":
                _fail("RESULT_INVALID")
            return result, {"adapter": "comparison_summary", "run_count": len(result["raw_runs"]),
                "metric_count": len(result["metrics"]), "gate_count": len(result["gates"]),
                "status": result["status"]}
        return self._perform("comparison", source, expected, operation)

    def inspect_crash_evidence(self, source, adapter="auto", expected_sha256=None):
        if type(adapter) is not str or adapter not in {"auto", "hub_journal", "opaque_text", "windows_event_xml"}:
            _fail("INVALID_ADAPTER")
        expected = _expected_hash(expected_sha256)
        def operation(backend, snapshot):
            result = backend.inspect_source(source, adapter=adapter, expected_sha256=snapshot["sha256"])
            if type(result) is not dict or result.get("source_sha256") != snapshot["sha256"] or \
                    result.get("runtime_verification") is not False or result.get("adapter") not in \
                    {"hub_journal", "opaque_text", "windows_event_xml"}:
                _fail("RESULT_INVALID")
            return result, {"adapter": result["adapter"], "event_count": len(result["events"]),
                            "status": "EVIDENCE_ONLY"}
        return self._perform("crash_evidence", source, expected, operation, maximum=16 * 1024 * 1024)

    def inspect_workflow(self, source, expected_sha256=None):
        """Fixed data-only planning; no recipe-selected code or live preflight."""
        expected = _expected_hash(expected_sha256)
        def operation(module, snapshot):
            raw, current = _capture(source, 1024 * 1024)
            if current != snapshot:
                _fail("SOURCE_CHANGED")
            result = module.plan_bytes(raw)
            if not isinstance(result, dict) or result.get("source_sha256") != snapshot["sha256"] or \
                    result.get("status") not in {"BLOCKED", "PREPARED_NOT_AUTHORIZED", "EVIDENCE_REQUEST_ONLY"} or \
                    result.get("execution") != "none" or result.get("runtime_verification") is not False:
                _fail("RESULT_INVALID")
            compact = {"status": result["status"], "kind": result["kind"],
                "change_count": len(result["change_list"]), "blocker_count": len(result["declaration_blockers"]),
                "runtime_verification": False}
            return result, compact
        return self._perform("workflow", source, expected, operation, maximum=1024 * 1024)

    def inspect_readiness(self, source, expected_sha256=None):
        """Fixed offline provider/scenario data only, not live verification."""
        expected = _expected_hash(expected_sha256)
        def operation(module, snapshot):
            raw, current = _capture(source, 1024 * 1024)
            if current != snapshot:
                _fail("SOURCE_CHANGED")
            result = module.plan_bytes(raw)
            if type(result) is not dict or result.get("source_sha256") != snapshot["sha256"] or \
                    result.get("status") not in {"BLOCKED", "MOCK_HEALTHY", "PREPARED_NOT_AUTHORIZED"} or \
                    result.get("execution") != "none" or result.get("runtime_verification") is not False or \
                    result.get("execution_authorized") is not False:
                _fail("RESULT_INVALID")
            return result, {"status": result["status"], "kind": result["kind"],
                "blocker_count": len(result["blockers"]), "runtime_verification": False}
        return self._perform("readiness", source, expected, operation, maximum=1024 * 1024)

    def cancel(self, reason="user"):
        reason = _label(reason)
        with self._guard:
            if self._state == "active":
                try:
                    expired = self._now() >= self._deadline
                except CoordinatorError:
                    self._failure_code = "INVALID_CLOCK"
                    self._end("failed", "invalid_clock")
                    return self.status()
                self._end("expired" if expired else "cancelled",
                          "expired" if expired else _REASONS.get(reason.lower(), "requested"))
            return self.status()

    def finish(self):
        with self._guard:
            self._require_active()
            if self._in_flight:
                _fail("ACTION_BUSY")
            self._end("finished", "finished")
            return self.status()

    def close(self):
        """Close only this owner; does not stop any application, input or provider."""
        with self._guard:
            if self._state == "active":
                return self.cancel("shutdown")
            self._close_writer()
            return self.status()
