"""Bounded, data-only installation/diagnostic dry-runs. Never executes a plan.

All recipe facts are imported declarations. Even a complete declaration cannot
prove current ownership, stopped processes, backup coverage or runtime FG.
Portable results alias imported identifiers and omit paths/raw source content.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import types

VERSION = "0.1.0"
MAX_SOURCE_BYTES = 1024 * 1024
MAX_ITEMS = 64
_BASE = Path(__file__).absolute().parent
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.+-]{0,79}\Z")
_HASH = re.compile(r"[a-fA-F0-9]{64}\Z")
_COVERAGE = {"unknown", "inventory_only", "declared_copied", "declared_byte_verified", "declared_restore_tested"}
_ROLES = {"game", "launcher", "store", "helper", "compiler"}
_PHASES = {"creation", "evaluation", "delivery", "presentation", "visual", "stability"}
_REQUESTS = {"target_identity", "upstream_compatibility", "loaded_owners", "effective_bindings", "first_failure",
             "memory_scopes", "fixed_fg", "component_evaluation", "repeatability", "snapshot_coverage"}
_LIMITS = ["Recipe facts are declarations, not observations or execution authority.",
          "No install, rollback, process control, input, settings write, capture or recording capability.",
          "Current target/process/owner/hash/snapshot checks are still required immediately before any later authorized change.",
          "Inventory hashes do not prove copied, byte-verified or restore-tested recovery.",
          "Overlay visibility, faulting modules and memory warnings do not establish cause or feature correctness.",
          "Rendering comparisons still require the separate effective-FG/memory preflight; this plan cannot issue PASS."]


class WorkflowError(ValueError):
    def __init__(self, code="RECIPE_REFUSED"):
        self.code = code
        super().__init__("Offline workflow refused; no execution or original-file change occurred.")


def _refuse(code="RECIPE_REFUSED"):
    raise WorkflowError(code)


def _obj(value, keys):
    if type(value) is not dict or set(value) != set(keys.split()):
        _refuse()
    return value


def _enum(value, choices):
    if type(value) is not str or value not in choices:
        _refuse()
    return value


def _token(value, nullable=False, pattern=_ID):
    if nullable and value is None:
        return value
    if type(value) is not str or not pattern.fullmatch(value):
        _refuse()
    return value


def _hash(value):
    return _token(value, True, _HASH)


def _list(value):
    if type(value) is not list or len(value) > MAX_ITEMS:
        _refuse()
    return value


def _ids(value):
    value = _list(value)
    for item in value:
        _token(item)
    if len(set(value)) != len(value):
        _refuse()
    return value


def _relative(value):
    if type(value) is not str or len(value) > 240 or "\\" in value or ":" in value:
        _refuse()
    parts = value.split("/")
    reserved = {"con", "prn", "aux", "nul", *("com" + str(n) for n in range(1, 10)), *("lpt" + str(n) for n in range(1, 10))}
    if not parts or len(parts) > 12 or any(not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_. -]{0,79}", p) or
            p.endswith((".", " ")) or p.split(".")[0].lower() in reserved for p in parts):
        _refuse()
    return value


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            _refuse()
        result[key] = value
    return result


def _decode(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_SOURCE_BYTES:
        _refuse()
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: _refuse())
        # Bound the decoded tree independently of parser recursion limits.
        stack, count = [(value, 0)], 0
        while stack:
            item, depth = stack.pop()
            count += 1
            if depth > 12 or count > 8192:
                _refuse()
            if type(item) is dict:
                stack.extend((v, depth + 1) for v in item.values())
            elif type(item) is list:
                stack.extend((v, depth + 1) for v in item)
        return value
    except (UnicodeError, ValueError, RecursionError, OverflowError):
        _refuse()


def _validate(raw):
    recipe = _obj(_decode(raw), "schema_version kind target layer resources processes snapshot changes checks observations hypotheses")
    if type(recipe["schema_version"]) is not int or recipe["schema_version"] != 1:
        _refuse()
    kind = _enum(recipe["kind"], {"installation", "diagnostic"})
    target = _obj(recipe["target"], "game_id executable build renderer")
    _token(target["game_id"], True)
    if target["executable"] is not None:
        _relative(target["executable"])
    _token(target["build"], True, _TOKEN)
    if target["renderer"] is not None:
        _enum(target["renderer"], {"DX11", "DX12", "Vulkan", "OpenGL"})
    layer = _obj(recipe["layer"], "component version sha256 source_revision source_sha256 freshness")
    _token(layer["component"])
    for key in ("version", "source_revision"):
        _token(layer[key], True, _TOKEN)
    _hash(layer["sha256"])
    _hash(layer["source_sha256"])
    _enum(layer["freshness"], {"unknown", "declared_current", "stale"})
    resources = {}
    for resource in _list(recipe["resources"]):
        _obj(resource, "id kind owners expected_owner requires")
        _token(resource["id"])
        if resource["id"] in resources:
            _refuse()
        _enum(resource["kind"], {"proxy", "swapchain", "fg", "sr", "rr", "neural", "hdr", "host", "configuration"})
        if resource["owners"] is not None:
            _ids(resource["owners"])
        _token(resource["expected_owner"], True)
        _ids(resource["requires"])
        resources[resource["id"]] = resource
    for resource in resources.values():
        if not set(resource["requires"]) <= resources.keys():
            _refuse("DEPENDENCY_REFERENCE_INVALID")
    roles = set()
    for process in _list(recipe["processes"]):
        _obj(process, "role state")
        role = _enum(process["role"], _ROLES)
        if role in roles:
            _refuse()
        roles.add(role)
        _enum(process["state"], {"unknown", "declared_stopped", "declared_running"})
    snapshot = _obj(recipe["snapshot"], "current known_good distinct")
    _enum(snapshot["current"], _COVERAGE)
    _enum(snapshot["known_good"], _COVERAGE)
    if snapshot["distinct"] is not None and type(snapshot["distinct"]) is not bool:
        _refuse()
    ids, paths = set(), set()
    for change in _list(recipe["changes"]):
        _obj(change, "id action target owner resource before_sha256 after_sha256 current_state current_sha256 backup_state backup_sha256")
        _token(change["id"])
        _relative(change["target"])
        path = change["target"].lower()
        if change["id"] in ids or path in paths:
            _refuse()
        ids.add(change["id"])
        paths.add(path)
        _enum(change["action"], {"add", "replace", "configure"})
        _token(change["owner"])
        _token(change["resource"])
        if change["resource"] not in resources:
            _refuse("DEPENDENCY_REFERENCE_INVALID")
        for key in ("before_sha256", "after_sha256", "current_sha256", "backup_sha256"):
            _hash(change[key])
        _enum(change["current_state"], {"unknown", "declared_absent", "declared_hash"})
        _enum(change["backup_state"], _COVERAGE | {"not_applicable"})
        if change["action"] == "add" and (change["before_sha256"] is not None or
                change["backup_sha256"] is not None or change["backup_state"] != "not_applicable"):
            _refuse()
        if change["current_state"] == "declared_absent" and change["current_sha256"] is not None:
            _refuse()
    phases = set()
    for check in _list(recipe["checks"]):
        _obj(check, "phase result")
        phase = _enum(check["phase"], _PHASES)
        if phase in phases:
            _refuse()
        phases.add(phase)
        _enum(check["result"], {"unknown", "declared_pass", "declared_fail"})
    observations = set()
    for observation in _list(recipe["observations"]):
        _obj(observation, "id kind source_sha256")
        _token(observation["id"])
        if observation["id"] in observations:
            _refuse()
        observations.add(observation["id"])
        _enum(observation["kind"], {"memory_warning", "overlay_visible", "faulting_module", "process_exit", "source_drift", "visual_issue", "input_issue", "unknown"})
        _hash(observation["source_sha256"])
    hypotheses = set()
    for hypothesis in _list(recipe["hypotheses"]):
        _obj(hypothesis, "id category support contradicts requests")
        _token(hypothesis["id"])
        if hypothesis["id"] in hypotheses:
            _refuse()
        hypotheses.add(hypothesis["id"])
        _enum(hypothesis["category"], {"ownership_conflict", "version_mismatch", "memory_pressure", "input_focus", "configuration_drift", "unknown"})
        for key in ("support", "contradicts"):
            if not set(_ids(hypothesis[key])) <= observations:
                _refuse("EVIDENCE_REFERENCE_INVALID")
        if set(hypothesis["support"]) & set(hypothesis["contradicts"]):
            _refuse()
        if not set(_ids(hypothesis["requests"])) <= _REQUESTS:
            _refuse()
    if kind == "diagnostic" and recipe["changes"]:
        _refuse("DIAGNOSTIC_IS_NOT_A_FIX")
    return recipe


def plan_bytes(raw):
    """Portable derived plan from bounded bytes, no target-file inspection."""
    r = _validate(raw)
    blockers, rollback_blockers = [], []
    def block(code):
        if code not in blockers:
            blockers.append(code)
    installation = r["kind"] == "installation"
    if any(v is None for v in r["target"].values()):
        block("TARGET_IDENTITY_UNKNOWN")
    if any(r["layer"][k] is None for k in ("version", "sha256", "source_revision", "source_sha256")) or r["layer"]["freshness"] != "declared_current":
        block("UPSTREAM_SOURCE_UNKNOWN_OR_STALE")
    resources = {v["id"]: v for v in r["resources"]}
    changed = {c["resource"] for c in r["changes"]}
    for v in resources.values():
        if v["owners"] is None or v["expected_owner"] is None:
            block("OWNERSHIP_UNKNOWN")
        elif len(v["owners"]) > 1 or v["owners"] and v["owners"] != [v["expected_owner"]]:
            block("OWNERSHIP_CONFLICT")
        elif not v["owners"] and v["id"] not in changed:
            block("REQUIRED_HOST_MISSING")
    # Bounded DFS: at most 64 nodes, including disconnected cycles.
    visited, visiting = set(), set()
    def visit(key):
        if key in visiting:
            block("DEPENDENCY_CYCLE")
            return
        if key in visited:
            return
        visiting.add(key)
        for dependency in resources[key]["requires"]:
            visit(dependency)
        visiting.remove(key)
        visited.add(key)
    for key in resources:
        visit(key)
    if installation:
        if {p["role"] for p in r["processes"]} != _ROLES or any(p["state"] == "unknown" for p in r["processes"]):
            block("STOPPED_PROCESSES_UNVERIFIED")
        if any(p["state"] == "declared_running" for p in r["processes"]):
            block("PROCESS_DECLARED_RUNNING")
        if not r["changes"]:
            block("NO_SCOPED_CHANGE")
        if r["snapshot"]["current"] not in {"declared_byte_verified", "declared_restore_tested"}:
            block("CURRENT_SNAPSHOT_COVERAGE_INCOMPLETE")
        if r["snapshot"]["distinct"] is None or r["snapshot"]["distinct"] is True and r["snapshot"]["known_good"] not in {"declared_byte_verified", "declared_restore_tested"}:
            block("KNOWN_GOOD_PRESERVATION_UNKNOWN")
    changes = []
    for index, c in enumerate(r["changes"], 1):
        if c["owner"] != r["layer"]["component"] or resources[c["resource"]]["expected_owner"] != c["owner"]:
            block("CHANGE_OUTSIDE_SINGLE_LAYER")
        add = c["action"] == "add"
        if c["after_sha256"] is None:
            block("EXPECTED_AFTER_HASH_UNKNOWN")
        if add:
            if c["current_state"] != "declared_absent":
                block("ADD_TARGET_NOT_DECLARED_ABSENT")
            if resources[c["resource"]]["owners"]:
                block("ADD_RESOURCE_ALREADY_OWNED")
        else:
            if c["before_sha256"] is None or c["current_state"] != "declared_hash" or c["current_sha256"] is None:
                block("CURRENT_FILE_HASH_UNKNOWN")
            elif c["current_sha256"].lower() != c["before_sha256"].lower():
                block("CURRENT_FILE_HASH_DRIFT")
            if c["backup_state"] not in {"declared_byte_verified", "declared_restore_tested"} or c["before_sha256"] is None or c["backup_sha256"] is None or c["before_sha256"].lower() != c["backup_sha256"].lower():
                block("ORIGINAL_BACKUP_INCOMPLETE_OR_MISMATCHED")
        changes.append({"asset": f"asset_{index:03}", "action": c["action"], "resource_kind": resources[c["resource"]]["kind"],
            "before_sha256": c["before_sha256"], "expected_after_sha256": c["after_sha256"],
            "backup_coverage": c["backup_state"], "rollback_proposal": "remove_only_owned_new_file" if add else "restore_only_owned_original",
            "rollback_condition": "Recheck live ownership and exact expected-after hash; preserve failed state and refuse newer/unrelated files."})
    if any(o["kind"] == "memory_warning" for o in r["observations"]):
        block("MEMORY_WARNING_SUSPENDS_TESTING")
    if any(c["result"] == "declared_fail" for c in r["checks"]):
        block("VERIFICATION_DECLARED_FAILED")
    if installation and {c["phase"] for c in r["checks"]} != _PHASES:
        block("COMPONENT_VERIFICATION_PLAN_INCOMPLETE")
    rollback_blockers = list(blockers) if installation else ["DIAGNOSTIC_HAS_NO_MUTATION"]
    # Rank only by declared evidence support count. No confidence/cause claim.
    ranked = sorted(enumerate(r["hypotheses"], 1), key=lambda pair: (-len(pair[1]["support"]), len(pair[1]["contradicts"]), pair[0]))
    hypotheses = [{"hypothesis": f"hypothesis_{i:03}", "category": h["category"],
        "declared_support_count": len(h["support"]), "declared_contradiction_count": len(h["contradicts"]),
        "confidence": None, "cause_verified": False, "evidence_requests": h["requests"]} for i, h in ranked]
    return {"schema_version": 1, "workflow_version": VERSION, "kind": r["kind"],
        "source_sha256": hashlib.sha256(raw).hexdigest(), "source_bytes": len(raw),
        "status": "BLOCKED" if blockers else "PREPARED_NOT_AUTHORIZED" if installation else "EVIDENCE_REQUEST_ONLY",
        "declaration_blockers": blockers, "execution": "none", "execution_authorized": False,
        "runtime_verification": False, "fg_preflight": "NOT_PERFORMED", "root_cause_verified": False,
        "sequence": ["preflight", "snapshot_current_and_distinct_known_good", "one_scoped_layer", "component_verification", "evidence_checkpoint", "retain_or_conditional_rollback"],
        "change_list": changes, "rollback_status": "BLOCKED" if rollback_blockers else "CONDITIONAL_NOT_EXECUTABLE",
        "rollback_blockers": rollback_blockers,
        "rollback_steps": ["Stop on first failure; preserve evidence and resumable failed-state snapshot.",
            "Obtain separate scoped authority; verify all file-owning processes stopped immediately before changes.",
            "Reidentify target, ownership, dependencies and exact current/expected-after hashes.",
            "Restore/remove only the single owned layer; refuse source drift, incomplete backup and newer/unrelated state.",
            "Recheck restored bytes and component-specific behavior; retain evidence and rollback boundaries."],
        "required_live_evidence": ["real rendering executable/bitness/store and game build/API/GPU driver/display mode/native features/anti-cheat/mod loader/all hooks",
            "current process/loaded-file owners", "save risk and scoped authority", "current and known-good recovery coverage",
            "creation/evaluation/delivery/presentation/visual/stability", "effective FG and memory scopes before any later performance comparison"],
        "stop_conditions": ["Unknown/conflicting ownership or source/hash drift", "Loaded files or unverified stopped processes",
            "Incomplete recovery coverage", "Memory warning or first verification failure", "Cancellation, expiry or scope change"],
        "diagnostic_hypotheses": hypotheses, "observation_count": len(r["observations"]),
        "hypothesis_ranking": "Declared support count descending, contradictions ascending, source order; not likelihood or causality.",
        "limitations": list(_LIMITS)}


def _shared():
    """Reuse fixed coordinator capture, not an imported recipe-selected adapter."""
    path = _BASE / "GameToolCoordinator.py"
    try:
        for part in (path, *path.parents):
            info = part.lstat()
            if part.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                _refuse("SOURCE_UNAVAILABLE")
        before = path.stat()
        if not 0 < before.st_size <= 1024 * 1024:
            _refuse("SOURCE_UNAVAILABLE")
        with path.open("rb") as stream:
            raw = stream.read(1024 * 1024 + 1)
        if len(raw) != before.st_size or len(raw) > 1024 * 1024:
            _refuse("SOURCE_CHANGED")
        module = types.ModuleType("_workflow_shared_capture")
        module.__file__ = str(path)
        exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
        if module.VERSION not in {"0.3.0", "0.4.0"}:
            _refuse("MODULE_UNAVAILABLE")
        captured, snapshot = module._capture(path, 1024 * 1024)
        if captured != raw:
            _refuse("SOURCE_CHANGED")
        return module, path, snapshot
    except Exception:
        _refuse("MODULE_UNAVAILABLE")


def _capture(source, expected_sha256=None):
    if expected_sha256 is not None:
        _hash(expected_sha256)
    shared, module_path, code_snapshot = _shared()
    try:
        raw, snapshot = shared._capture(source, MAX_SOURCE_BYTES)
        if expected_sha256 is not None and snapshot["sha256"] != expected_sha256.lower():
            _refuse("SOURCE_CHANGED")
        return shared, module_path, code_snapshot, raw, snapshot
    except WorkflowError:
        raise
    except Exception:
        _refuse("SOURCE_UNAVAILABLE")


def _current(shared, module_path, code_snapshot, source, snapshot):
    try:
        if shared._capture(module_path, 1024 * 1024)[1] != code_snapshot or shared._capture(source, MAX_SOURCE_BYTES)[1] != snapshot:
            _refuse("SOURCE_CHANGED")
    except WorkflowError:
        raise
    except Exception:
        _refuse("SOURCE_CHANGED")


def preview_source(source, expected_sha256=None):
    """Private local targets are separate from the portable result."""
    shared, module_path, code, raw, snapshot = _capture(source, expected_sha256)
    result = plan_bytes(raw)
    r = _validate(raw)
    local = [{"target": c["target"], "owner": c["owner"], "action": c["action"]} for c in r["changes"]]
    _current(shared, module_path, code, source, snapshot)
    return {"portable": result, "local_changes": local}


def inspect_source(source, expected_sha256=None):
    return preview_source(source, expected_sha256)["portable"]


def export_plan(source, output, expected_sha256):
    """New portable JSON only; no original recipe/target/backup is copied."""
    def builder(raw):
        plan = plan_bytes(raw)
        return plan, plan["status"]
    return _export_data(source, output, expected_sha256, builder)


def _export_data(source, output, expected_sha256, builder):
    """Internal fixed-backend publisher shared by plan and scenario copies."""
    if expected_sha256 is None:
        _refuse("EXPECTED_HASH_REQUIRED")
    shared, module_path, code, raw, snapshot = _capture(source, expected_sha256)
    result, status = builder(raw)
    payload = (json.dumps(result, indent=2, ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
    destination, published_identity, parent_identity = None, None, None
    def parent_current():
        parent = shared._no_links(destination.parent)
        info = parent.stat()
        if (info.st_dev, info.st_ino) != parent_identity:
            _refuse("DESTINATION_REFUSED")
    try:
        destination = Path(output).absolute()
        _relative(destination.name)
        if destination.suffix.lower() != ".json":
            _refuse("DESTINATION_REFUSED")
        # Existing ordinary parent required; portable exports never enter Git.
        parent_info = shared._no_links(destination.parent).stat()
        parent_identity = (parent_info.st_dev, parent_info.st_ino)
        repo = _BASE.parent
        if destination == repo or repo in destination.parents or destination.exists() or destination.is_symlink():
            _refuse("DESTINATION_REFUSED")
        with tempfile.TemporaryDirectory(prefix="workflow-stage-", dir=destination.parent) as staging:
            staged = Path(staging) / "plan.json"
            with staged.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            staged_raw, staged_snapshot = shared._capture(staged, MAX_SOURCE_BYTES)
            if staged_raw != payload:
                _refuse("EXPORT_UNVERIFIED")
            _current(shared, module_path, code, source, snapshot)
            parent_current()
            os.link(staged, destination)  # exclusive publication; never overwrite
            published_identity = staged_snapshot["identity"]
            _current(shared, module_path, code, source, snapshot)
            parent_current()
            published, current = shared._capture(destination, MAX_SOURCE_BYTES)
            if published != payload or current["identity"] != published_identity:
                _refuse("EXPORT_UNVERIFIED")
        return {"workflow_version": VERSION, "source_sha256": snapshot["sha256"],
                "export_sha256": hashlib.sha256(payload).hexdigest(), "export_bytes": len(payload),
                "status": status, "execution": "none", "runtime_verification": False,
                "coverage": "portable_plan_only", "restore_tested": False}
    except Exception:
        # Delete only our still-identical published file, never another writer's
        # replacement. Parent/identity checks refuse link redirection.
        if destination is not None and published_identity is not None:
            try:
                parent_current()
                current_bytes, current_snapshot = shared._capture(destination, MAX_SOURCE_BYTES)
                if current_snapshot["identity"] == published_identity and current_bytes == payload:
                    destination.unlink()
            except Exception:
                pass
        _refuse("EXPORT_REFUSED")
