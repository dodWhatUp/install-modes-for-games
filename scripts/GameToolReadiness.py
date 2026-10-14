"""Offline declared provider health and editable scenario contracts. No runner.

Only fixed authored sibling code is used. Imported facts never establish live
capture, optical latency, workload equality, FG readiness or execution authority.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import types

VERSION = "0.1.0"
MAX_SOURCE_BYTES = 1024 * 1024
_BASE = Path(__file__).absolute().parent
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,63}\Z")
_HASH = re.compile(r"[a-fA-F0-9]{64}\Z")
_VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,63}\Z")
_LIMITATIONS = [
    "Offline declarations/mock records only; health is not live capture verification.",
    "No provider launch, capture, input, game, benchmark, recording or settings capability.",
    "Scenario preparation is not execution authority or proof of route/save safety.",
    "Effective-FG/memory/workload runtime preflight remains separate and unperformed.",
    "Established providers retain complex metric calculation; missing data is not zero."]


class ReadinessError(ValueError):
    def __init__(self, code="CONTRACT_REFUSED"):
        self.code = code
        super().__init__("Offline contract refused or changed; no original or live tool was modified.")


def _bad(code="CONTRACT_REFUSED"):
    raise ReadinessError(code)


def _obj(value, fields):
    if type(value) is not dict or set(value) != set(fields.split()):
        _bad()
    return value


def _id(value, nullable=False, pattern=_ID):
    if nullable and value is None:
        return
    if type(value) is not str or not pattern.fullmatch(value):
        _bad()


def _enum(value, choices):
    if type(value) is not str or value not in choices:
        _bad()


def _number(value, minimum=0, maximum=3600000, nullable=False, integer=False):
    if nullable and value is None:
        return
    if type(value) not in ((int,) if integer else (int, float)) or not minimum <= value <= maximum or not math.isfinite(value):
        _bad()


def _bool(value):
    if type(value) is not bool:
        _bad()


def _list(value, maximum=64):
    if type(value) is not list or len(value) > maximum:
        _bad()
    return value


def _io():
    """Reuse the fixed workflow decoder/capture/publisher; never a recipe import."""
    try:
        path = _BASE / "GameToolWorkflow.py"
        for part in (path, *path.parents):
            info = part.lstat()
            if part.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                _bad("MODULE_REFUSED")
        with path.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
        if not 0 < len(raw) <= MAX_SOURCE_BYTES:
            _bad("MODULE_REFUSED")
        module = types.ModuleType("_readiness_fixed_workflow")
        module.__file__ = str(path)
        exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
        core, _, _ = module._shared()
        if module.VERSION != "0.1.0" or core._capture(path)[0] != raw:
            _bad("MODULE_REFUSED")
        return module
    except Exception:
        _bad("MODULE_REFUSED")


def _base(raw):
    try:
        data = _io()._decode(raw)
    except Exception:
        _bad()
    if type(data) is not dict or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        _bad("SCHEMA_UNSUPPORTED")
    _enum(data.get("kind"), {"provider_health", "scenario"})
    return data


def _provider(data):
    _obj(data, "schema_version kind provider context clock lifecycle stream")
    provider = _obj(data["provider"], "id version capabilities")
    _id(provider["id"]); _id(provider["version"], True, _VERSION)
    capabilities = _list(provider["capabilities"])
    for value in capabilities:
        _enum(value, {"connect", "capture", "report_import"})
    if len(set(capabilities)) != len(capabilities):
        _bad()
    context = _obj(data["context"], "target_id run_id phase_id")
    for value in context.values():
        _id(value, True)
    clock = _obj(data["clock"], "domain now_ms max_age_ms")
    _enum(clock["domain"], {"mock_monotonic_ms"})
    _number(clock["now_ms"], maximum=2**53)
    _number(clock["max_age_ms"], minimum=1, maximum=60000)
    life = _obj(data["lifecycle"], "discovered connected approval process armed cancelled")
    for key in ("discovered", "connected", "armed", "cancelled"):
        _bool(life[key])
    _enum(life["approval"], {"unknown", "pending", "approved", "denied", "not_required"})
    _enum(life["process"], {"unknown", "not_started", "running", "exited"})
    stream = _obj(data["stream"], "complete_write closed expected_interval_ms dropped_records missing_fields records")
    _bool(stream["complete_write"]); _bool(stream["closed"])
    _number(stream["expected_interval_ms"], minimum=1, maximum=60000, nullable=True)
    _number(stream["dropped_records"], maximum=1000000, integer=True)
    missing = _list(stream["missing_fields"])
    for item in missing:
        _id(item)
    if len(set(missing)) != len(missing):
        _bad()
    records = _list(stream["records"], 1024)
    for record in records:
        _obj(record, "sequence at_ms target_id run_id phase_id")
        _number(record["sequence"], minimum=1, maximum=2**53, integer=True)
        _number(record["at_ms"], maximum=2**53)
        for key in ("target_id", "run_id", "phase_id"):
            _id(record[key], True)
    blockers = []
    def check(condition, code):
        if condition:
            blockers.append(code)
    check(provider["version"] is None, "UNKNOWN_PROVIDER_VERSION")
    check("capture" not in capabilities, "CAPTURE_CAPABILITY_UNDECLARED")
    check(any(v is None for v in context.values()), "UNKNOWN_EXPECTED_CONTEXT")
    check(not life["discovered"], "NOT_DISCOVERED")
    check(not life["connected"], "DISCONNECTED")
    check(life["approval"] not in {"approved", "not_required"}, "APPROVAL_" + life["approval"].upper())
    check(life["process"] != "running", "PROCESS_" + life["process"].upper())
    check(not life["armed"], "NOT_ARMED")
    check(life["cancelled"], "CANCELLED")
    check(stream["closed"], "STREAM_STOPPED")
    check(not stream["complete_write"], "PARTIAL_WRITE")
    check(stream["dropped_records"] > 0, "DROPPED_RECORDS")
    check(bool(missing), "MISSING_FIELDS")
    check(len(records) < 2, "INSUFFICIENT_RECORDS")
    check(stream["expected_interval_ms"] is None, "UNKNOWN_CADENCE")
    check(any(any(r[k] != context[k] for k in context) for r in records), "CONTEXT_MISMATCH")
    check(any(r["at_ms"] > clock["now_ms"] for r in records), "FUTURE_RECORD")
    intervals = [b["at_ms"] - a["at_ms"] for a, b in zip(records, records[1:])]
    check(any(b["sequence"] != a["sequence"] + 1 for a, b in zip(records, records[1:])), "SEQUENCE_GAP_OR_REORDER")
    check(any(v <= 0 for v in intervals), "TIME_REORDER")
    check(stream["expected_interval_ms"] is not None and any(v > stream["expected_interval_ms"] * 1.5 for v in intervals), "CADENCE_GAP")
    age = clock["now_ms"] - records[-1]["at_ms"] if records else None
    check(age is not None and age > clock["max_age_ms"], "STALE_RECORDS")
    state = "writing_declared" if not blockers else "not_ready"
    # Lifecycle stage is descriptive; it is not derived capture permission.
    for condition, stage in ((stream["closed"], "stopped"), (life["cancelled"], "cancelled"),
            (life["process"] == "exited", "process_exited"), (life["approval"] == "pending", "approval_pending"),
            (life["process"] == "not_started", "not_started")):
        if condition:
            state = stage
            break
    return blockers, {"declared_state": state, "record_count": len(records),
        "last_record_age_ms": age, "interval_min_ms": min(intervals) if intervals else None,
        "interval_max_ms": max(intervals) if intervals else None,
        "dropped_records": stream["dropped_records"], "missing_field_count": len(missing)}


def _workload(value):
    _obj(value, "game_id build scene_id settings_sha256")
    for key in ("game_id", "build", "scene_id"):
        _id(value[key], True, _VERSION if key == "build" else _ID)
    _id(value["settings_sha256"], True, _HASH)


def _scenario(data):
    _obj(data, "schema_version kind scenario_id revision mode requested_workload declared_readback cache repeat_count measurement phases stop safety")
    _id(data["scenario_id"])
    _number(data["revision"], 1, 1000000, integer=True)
    _enum(data["mode"], {"builtin", "route_action"})
    _workload(data["requested_workload"])
    if data["declared_readback"] is not None:
        _workload(data["declared_readback"])
    cache = _obj(data["cache"], "process_start visit shader_cache source_revision")
    _enum(cache["process_start"], {"cold", "warm", "unknown"})
    _enum(cache["visit"], {"first", "warm_revisit", "unknown"})
    _enum(cache["shader_cache"], {"documented_cold", "documented_warm", "unknown"})
    _id(cache["source_revision"], True)
    _number(data["repeat_count"], 1, 100, integer=True)
    measurement = _obj(data["measurement"], "purpose provider_id frame_class endpoint calibration meaningful_input")
    _enum(measurement["purpose"], {"cost_comparison", "latency", "stability"})
    _id(measurement["provider_id"], True)
    _enum(measurement["frame_class"], {"rendered", "presented", "displayed", "unknown"})
    _enum(measurement["endpoint"], {"none", "software_response", "physical_input_to_pixel"})
    _enum(measurement["calibration"], {"not_applicable", "planned", "declared"})
    _bool(measurement["meaningful_input"])
    safety = _obj(data["safety"], "save_access quest_changes graphics_changes")
    for value in safety.values():
        _bool(value)
        if value:
            _bad("UNSAFE_ACTION_REFUSED")
    stop = _obj(data["stop"], "on_focus_loss on_provider_failure on_memory_warning on_cancel deadline_ms")
    for key in ("on_focus_loss", "on_provider_failure", "on_memory_warning", "on_cancel"):
        _bool(stop[key])
        if not stop[key]:
            _bad("STOP_POLICY_REFUSED")
    _number(stop["deadline_ms"], 1, 3600000, integer=True)
    phases = _list(data["phases"])
    if not phases:
        _bad()
    ids, actions, duration = set(), [], 0
    for phase in phases:
        _obj(phase, "id duration_ms actions")
        _id(phase["id"])
        if phase["id"] in ids:
            _bad("DUPLICATE_PHASE")
        ids.add(phase["id"])
        _number(phase["duration_ms"], 1, 600000, integer=True)
        duration += phase["duration_ms"]
        phase_actions = _list(phase["actions"])
        action_duration = 0
        for action in phase_actions:
            _obj(action, "kind duration_ms")
            _enum(action["kind"], {"marker", "wait", "builtin_scene", "camera_rotation", "camera_translation", "hud", "animation"})
            _number(action["duration_ms"], maximum=600000, integer=True)
            action_duration += action["duration_ms"]
            actions.append(action["kind"])
        if action_duration > phase["duration_ms"] or len(actions) > 256:
            _bad("ACTION_BUDGET_REFUSED")
    if duration > stop["deadline_ms"]:
        _bad("DEADLINE_REFUSED")
    if data["mode"] == "builtin" and any(a not in {"marker", "wait", "builtin_scene"} for a in actions) or \
            data["mode"] == "route_action" and "builtin_scene" in actions:
        _bad("MODE_ACTION_REFUSED")
    blockers = []
    if any(v is None for v in data["requested_workload"].values()):
        blockers.append("UNKNOWN_WORKLOAD")
    if data["declared_readback"] is None or data["declared_readback"] != data["requested_workload"]:
        blockers.append("READBACK_UNKNOWN_OR_MISMATCHED")
    if "unknown" in cache.values() or cache["source_revision"] is None:
        blockers.append("CACHE_EVIDENCE_UNKNOWN")
    if data["repeat_count"] < 3:
        blockers.append("INSUFFICIENT_REPEATS")
    if measurement["provider_id"] is None or measurement["frame_class"] == "unknown":
        blockers.append("PROVIDER_OR_FRAME_CLASS_UNKNOWN")
    motion = any(a in {"camera_rotation", "camera_translation", "hud", "animation"} for a in actions)
    if not any(a not in {"marker", "wait"} for a in actions):
        blockers.append("NO_MEASUREMENT_SCENE")
    if measurement["purpose"] == "latency":
        if not motion or not measurement["meaningful_input"]:
            blockers.append("NO_MEANINGFUL_INPUT")
        if measurement["endpoint"] == "none" or measurement["calibration"] != "declared":
            blockers.append("ENDPOINT_OR_CALIBRATION_UNPREPARED")
    elif measurement["endpoint"] != "none" or measurement["meaningful_input"]:
        blockers.append("LATENCY_SCOPE_MISMATCH")
    return blockers, {"revision": data["revision"], "mode": data["mode"], "repeat_count": data["repeat_count"],
        "duration_ms": duration, "purpose": measurement["purpose"], "endpoint": measurement["endpoint"],
        "phase_preview": [{"phase": "phase_" + str(i + 1).zfill(3), "duration_ms": p["duration_ms"],
            "actions": p["actions"]} for i, p in enumerate(phases)]}


def plan_bytes(raw):
    data = _base(raw)
    blockers, detail = _provider(data) if data["kind"] == "provider_health" else _scenario(data)
    return {"schema_version": 1, "readiness_version": VERSION, "kind": data["kind"],
        "source_sha256": hashlib.sha256(raw).hexdigest(), "source_bytes": len(raw),
        "status": "BLOCKED" if blockers else "MOCK_HEALTHY" if data["kind"] == "provider_health" else "PREPARED_NOT_AUTHORIZED",
        "blockers": blockers, "details": detail, "basis": "offline_declarations_only",
        "execution": "none", "execution_authorized": False, "runtime_verification": False,
        "fg_preflight": "not_performed", "limitations": list(_LIMITATIONS)}


def read_source(source, expected_sha256=None):
    try:
        io = _io()
        core, path, code, raw, snapshot = io._capture(source, expected_sha256)
        result = plan_bytes(raw)
        io._current(core, path, code, source, snapshot)
        return raw, result
    except ReadinessError:
        raise
    except Exception:
        _bad("SOURCE_REFUSED_OR_CHANGED")


def inspect_source(source, expected_sha256=None):
    return read_source(source, expected_sha256)[1]


def save_scenario(source, output, draft_raw, expected_sha256):
    """Validate draft and clone to a NEW private file; never edits source."""
    result = plan_bytes(draft_raw)
    if result["kind"] != "scenario":
        _bad("SCENARIO_REQUIRED")
    if expected_sha256 is None:
        _bad("EXPECTED_HASH_REQUIRED")
    data = _base(draft_raw)
    try:
        io = _io()
        def builder(original):
            if plan_bytes(original)["kind"] != "scenario":
                _bad("SCENARIO_REQUIRED")
            return data, result["status"]
        receipt = io._export_data(source, output, expected_sha256, builder)
        receipt.pop("workflow_version", None)
        receipt.update(readiness_version=VERSION, coverage="private_scenario_contract_only", draft_sha256=result["source_sha256"])
        return receipt
    except Exception:
        _bad("SAVE_REFUSED_OR_CHANGED")
