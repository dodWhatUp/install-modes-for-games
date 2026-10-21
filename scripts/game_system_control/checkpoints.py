"""MCI-08 bounded checkpoints, offline packages and inactive reconstruction.

This format adapter reuses UserData IO, Journal, VaultRegistry, PolicyStore,
AccessStore and their cooperative locks. No network, native-state import,
active project adoption, index/context delivery, task replay or garbage collection.
V1 seeds remain supported. V2 adds single-parent full/delta representations;
neither profile infers tombstones or performs active adoption.
Application consistency and physical power-loss durability are not asserted.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import os
import time

from GameToolUserData import (
    MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_MANIFEST_BYTES,
    _canonical, _decode, _read, _write_new, _relative, digest, local_path,
    stream_fingerprint, copy_stream_new,
)
from GameToolJournal import Journal, JournalError, inspect_journal
from game_mod_ops.safety import local_lock
from .contracts import require, identifier, SHA, ContextError
from .vault import CLASSES, EXCLUDED, _relative_managed
from .policy import evaluate, policy_revision

VERSION = "0.3.0-preview.1"
_ACTIVATION_NAMES = {"agents.md", "agents.override.md", "claude.md", "skill.md"}
_COVERAGE = {
    "mode": "explicit_selected_files", "unselected_files": "not_captured",
    "unsaved_work": "not_observed", "consistency": "saved_file_observation_only",
    "excluded_classes": sorted(EXCLUDED),
}


def _hash(value):
    require(type(value) is str and SHA.fullmatch(value), "An exact lowercase SHA-256 is required.")
    return value


def _named(value):
    identifier(value)
    _relative(value)
    require("/" not in value, "Operation identities cannot contain paths.")
    return value


def _portable(value):
    value = _relative_managed(value)
    require(not any(p.casefold() in _ACTIVATION_NAMES for p in value.split("/")),
            "Instruction discovery files are outside this first inactive-copy proof.")
    return value


def _seal(domain, value):
    return digest(domain.encode("ascii") + b"\x00" + _canonical(value))


def _package(core, representation="full", required_objects=None, extensions=None):
    if core.get("schema_version") == 2:
        checkpoint = {"checkpoint_id": _seal("gametools-checkpoint-v2", core), "core": deepcopy(core)}
        objects = sorted({r["sha256"] for r in core["files"]}) if required_objects is None else required_objects
        body = {"schema_version": 2, "kind": "GameToolsCheckpointPackage", "format": "directory-objects-v2",
                "checkpoint": checkpoint, "representation": representation, "required_parents": deepcopy(core["parents"]),
                "required_objects": objects, "required_features": ["complete-selection", "parent-bound"],
                "extensions": deepcopy(extensions or {})}
        return {**body, "package_id": _seal("gametools-package-v2", body)}
    checkpoint = {"checkpoint_id": _seal("gametools-checkpoint-v1", core), "core": deepcopy(core)}
    body = {"schema_version": 1, "kind": "GameToolsSeedPackage", "format": "directory-objects-v1", "checkpoint": checkpoint}
    return {**body, "package_id": _seal("gametools-package-v1", body)}


def validate_package(value):
    """Strict operational validation; projection-only schemas are not authority."""
    _decode(_canonical(value))
    if type(value) is dict and type(value.get("schema_version")) is int and value["schema_version"] == 2:
        return _validate_v2(value)
    require(type(value) is dict and set(value) == {"schema_version", "kind", "format", "checkpoint", "package_id"}, "Unsupported seed package fields.")
    require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["kind"] == "GameToolsSeedPackage" and value["format"] == "directory-objects-v1", "Unsupported seed package format.")
    cp = value["checkpoint"]
    require(type(cp) is dict and set(cp) == {"checkpoint_id", "core"}, "Invalid checkpoint envelope.")
    core = cp["core"]
    require(type(core) is dict and set(core) == {"schema_version", "kind", "workspace_id", "project_id", "replica_id", "parents", "tombstones", "coverage", "files"}, "Invalid checkpoint core.")
    require(type(core["schema_version"]) is int and core["schema_version"] == 1 and core["kind"] == "GameToolsSeedCheckpoint", "Unsupported checkpoint version.")
    for key in ("workspace_id", "project_id", "replica_id"):
        identifier(core[key])
    require(type(core["parents"]) is list and core["parents"] == [] and type(core["tombstones"]) is list and core["tombstones"] == [], "Parents, deltas and deletion are not implemented by the seed slice.")
    require(core["coverage"] == _COVERAGE, "Unsupported coverage or application-consistency claim.")
    rows = core["files"]
    require(type(rows) is list and 1 <= len(rows) <= MAX_FILES, "Selected file count exceeds the seed bound.")
    names, sizes, total = set(), {}, 0
    for row in rows:
        require(type(row) is dict and set(row) == {"content_class", "relative", "bytes", "sha256"}, "Invalid selected file entry.")
        require(type(row["content_class"]) is str and row["content_class"] in CLASSES, "Unsupported content class.")
        relative = _portable(row["relative"])
        logical = _relative("data/" + CLASSES[row["content_class"]] + "/" + relative)
        folded = logical.casefold()
        require(folded not in names and not any(folded.startswith(n + "/") or n.startswith(folded + "/") for n in names), "Duplicate, case-alias or file/directory collision.")
        names.add(folded)
        require(type(row["bytes"]) is int and 0 <= row["bytes"] <= MAX_FILE_BYTES, "File size is outside the seed bound.")
        sha = _hash(row["sha256"])
        require(sha not in sizes or sizes[sha] == row["bytes"], "One object has conflicting declared sizes.")
        sizes[sha] = row["bytes"]
        total += row["bytes"]
    require(total <= MAX_TOTAL_BYTES, "Selected payload exceeds the seed bound.")
    require(rows == sorted(rows, key=lambda r: (r["content_class"], r["relative"])), "File ordering is not canonical.")
    require(value == _package(core), "Checkpoint or package identity does not match its contents.")
    return deepcopy(value)


def _validate_v2(value):
    require(set(value) == {"schema_version", "kind", "format", "checkpoint", "package_id", "representation", "required_parents", "required_objects", "required_features", "extensions"}, "Unsupported v2 package fields.")
    require(value["kind"] == "GameToolsCheckpointPackage" and value["format"] == "directory-objects-v2", "Unsupported package format.")
    cp = value["checkpoint"]
    require(type(cp) is dict and set(cp) == {"checkpoint_id", "core"} and type(cp["core"]) is dict, "Invalid checkpoint envelope.")
    core = cp["core"]
    require(type(core.get("schema_version")) is int and core["schema_version"] == 2 and core.get("kind") == "GameToolsCheckpoint", "Unsupported logical checkpoint.")
    parents = core.get("parents")
    require(type(parents) is list and len(parents) <= 1, "This offline profile supports at most one parent; merges retain MCI-09 ownership.")
    for parent in parents: _hash(parent)
    # Reuse the proven seed entry/coverage/path validator without changing v1.
    seed = {**core, "schema_version": 1, "kind": "GameToolsSeedCheckpoint", "parents": []}
    validate_package(_package(seed))
    require(type(value["required_parents"]) is list and value["required_parents"] == parents, "Expected ancestry differs from the checkpoint.")
    require(value["representation"] in {"full", "delta"} and (value["representation"] != "delta" or len(parents) == 1), "A delta requires its exact parent.")
    objects = value["required_objects"]
    all_objects = {r["sha256"] for r in core["files"]}
    require(type(objects) is list and all(type(s) is str and SHA.fullmatch(s) for s in objects) and objects == sorted(set(objects)) and set(objects) <= all_objects, "Invalid required object set.")
    require(value["representation"] != "full" or set(objects) == all_objects, "Full packages must carry every current object.")
    require(value["required_features"] == ["complete-selection", "parent-bound"], "Unsupported required package semantics.")
    require(type(value["extensions"]) is dict, "Optional inert metadata must be an object.")
    require(value == _package(core, value["representation"], objects, value["extensions"]), "Checkpoint or representation identity mismatch.")
    return deepcopy(value)


def _object_ids(package):
    return set(package["required_objects"]) if package["schema_version"] == 2 else {r["sha256"] for r in package["checkpoint"]["core"]["files"]}


class MissingParents(ContextError):
    def __init__(self, ids):
        self.ids = sorted(ids)
        super().__init__("Exact parent checkpoints are unavailable; receive/verify parents first.")


def _entries(path, maximum):
    """Bound directory enumeration without recursive discovery."""
    path = local_path(path)
    require(path.is_dir(), "Selected directory is unavailable.")
    names = []
    with os.scandir(path) as iterator:
        for entry in iterator:
            require(len(names) < maximum, "Directory entry bound exceeded.")
            local_path(path / entry.name)
            names.append(entry.name)
    return set(names)


def _load(path):
    return _decode(_read(path, MAX_MANIFEST_BYTES)[0])


def _verify_payload(root, package, check=None, inherited=None):
    root = local_path(root)
    package = validate_package(package)
    allowed = {"_ATTEMPT.json", "AUDIT.jsonl", "objects", "MANIFEST.json", "_PUBLISHED.json"}
    require(_entries(root, 5) <= allowed, "Unknown files in the selected package.")
    objects = {r["sha256"]: r for r in package["checkpoint"]["core"]["files"]}
    supplied = _object_ids(package)
    require(_entries(root / "objects", MAX_FILES) == supplied, "Payload objects are missing or unlisted.")
    inherited = inherited or {}
    if package["schema_version"] == 2 and package["representation"] == "delta":
        require(supplied == set(objects) - set(inherited), "Delta object set does not match its exact parent.")
    for sha, row in objects.items():
        require(sha in supplied or sha in inherited, "Parent does not close the current payload.")
        observed = stream_fingerprint(root / "objects" / sha if sha in supplied else inherited[sha], row["bytes"], before_chunk=check)
        require(observed == {"bytes": row["bytes"], "sha256": sha}, "Payload integrity failed; do not adopt or retry.")
    return package


def _publication_audit(root, package):
    marker = _publication(root, package)
    attempt = _load(root / "_ATTEMPT.json")
    require(type(attempt) is dict and set(attempt) == {"schema_version", "operation_id", "plan_sha256", "checkpoint_id", "package_id"} and type(attempt["schema_version"]) is int and attempt["schema_version"] == 1, "Invalid operation intent marker.")
    require(all(attempt.get(k) == marker[k] for k in ("operation_id", "checkpoint_id", "package_id")), "Attempt and publication identities differ.")
    _hash(attempt["plan_sha256"])
    try:
        audit = inspect_journal(root / "AUDIT.jsonl")
        records = audit["verified_records"]
        return bool(audit["valid"] and audit["clean_end"] and records[-1]["kind"] == "session_closed" and
                    records[0]["data"] == {"owner": "managed-checkpoint", **attempt} and
                    [r["data"] for r in records if r["kind"] == "operation_intent"] == [{"plan_sha256": attempt["plan_sha256"], "operation_id": attempt["operation_id"]}] and
                    [r["data"] for r in records if r["kind"] == "operation_result"] == [marker])
    except (JournalError, OSError):
        return False


def _selected_rows(package, selection=None):
    rows = package["checkpoint"]["core"]["files"]
    if selection is None: return rows
    require(type(selection) is list and 0 < len(selection) <= len(rows), "Select a nonempty bounded recovery subset.")
    names = []
    for row in selection:
        require(type(row) is dict and set(row) == {"content_class", "relative"}, "Recovery selects class and relative path only.")
        names.append((row["content_class"], _portable(row["relative"])))
    require(len(set(names)) == len(names), "Duplicate recovery selection.")
    selected = [r for r in rows if (r["content_class"], r["relative"]) in names]
    require(len(selected) == len(names), "Recovery selection is outside the checkpoint.")
    return selected


def _restored_closure(root, rows):
    """Do not certify a copy containing unlisted files, links or directories."""
    require(_entries(root, 5) <= {"_RECONSTRUCTION.json", "MANIFEST.json", "AUDIT.jsonl", "data", "_COMPLETE.json"}, "Unlisted reconstruction metadata; preserve external work.")
    expected = {"data/" + CLASSES[r["content_class"]] + "/" + r["relative"] for r in rows}
    dirs = {str(Path(p).parent).replace("\\", "/") for p in expected}
    dirs |= {str(p).replace("\\", "/") for d in tuple(dirs) for p in Path(d).parents if str(p) != "."}
    count, seen = 0, set()
    for directory, subdirs, files in os.walk(local_path(root / "data"), followlinks=False):
        for name in subdirs + files:
            count += 1
            require(count <= MAX_FILES * 13, "Reconstruction tree exceeds its bound.")
            path = local_path(Path(directory) / name)
            relative = path.relative_to(root).as_posix()
            require(relative in (dirs if name in subdirs else expected), "Unlisted reconstruction content; preserve external work.")
            if name in files: seen.add(relative)
    require(seen == expected, "Reconstruction payload closure is incomplete.")


def _publication(root, package):
    value = _load(root / "_PUBLISHED.json")
    fields = {"operation_id", "checkpoint_id", "package_id"}
    if package["schema_version"] == 2: fields |= {"target_replica_id", "received", "verified", "adopted"}
    require(type(value) is dict and set(value) == fields, "Invalid publication marker.")
    _named(value["operation_id"])
    require(value["checkpoint_id"] == package["checkpoint"]["checkpoint_id"] and value["package_id"] == package["package_id"], "Publication marker identity mismatch.")
    if package["schema_version"] == 2:
        identifier(value["target_replica_id"])
        require(type(value["received"]) is bool and value["verified"] is True and value["adopted"] is False, "Receipt cannot imply adoption or unverified delivery.")
    return value


class CheckpointService:
    """Destination-local, exact-plan operation adapter; no implicit enrollment.

    A test may supply an explicit synthetic registry observer and clock. Ordinary
    callers retain the existing native observer/identity; this adds no OS adapter.
    """
    def __init__(self, registry, policy, access, actor, vault_id, *, clock=time.time):
        require(type(actor) is dict and set(actor) == {"account_id", "workspace_id", "project_id", "device_id", "generation"}, "Select an exact local actor and scope.")
        for key in ("account_id", "workspace_id", "project_id", "device_id"):
            identifier(actor[key])
        require(type(actor["generation"]) is int and actor["generation"] >= 1, "Select an integer writer generation.")
        self.registry, self.policy, self.access = registry, policy, access
        self.actor, self.vault_id, self.clock = deepcopy(actor), identifier(vault_id), clock
        roots = [s.state.root for s in (access, policy, registry)]
        require(all(p.is_dir() for p in roots) and not any(a.samefile(b) for i, a in enumerate(roots) for b in roots[i + 1:]), "Access, policy and binding stores must be distinct existing local stores.")

    def _vector(self):
        return {name: store.state.snapshot()["revision"] for name, store in
                (("access", self.access), ("policy", self.policy), ("bindings", self.registry))}

    def _check(self, specs, expected=None):
        vector = self._vector()
        require(expected is None or vector == expected, "Local access, policy or bindings changed; prepare a fresh preview.")
        binding = self.registry._binding(self.vault_id)
        self.registry._verify(binding, binding["root"])
        require(binding["marker"]["workspace_id"] == self.actor["workspace_id"], "Vault and actor workspace differ.")
        body = self.policy.snapshot()["body"]
        effective_revision = policy_revision(body)
        for capability, cls, effect in sorted(set(specs)):
            request = {**self.actor, "capability": capability, "storage_id": self.vault_id,
                       "content_class": cls, "policy_revision": effective_revision}
            require(self.access.authorize(request, now=self.clock())["allowed"], "Local stop, expiry, enrollment, role or storage grant refuses this operation.")
            scope = {k: self.actor[k] for k in ("account_id", "workspace_id", "project_id")}
            scope.update(source_device=self.actor["device_id"], destination_device=self.actor["device_id"], capability=capability, content_class=cls)
            decision = evaluate(body, scope, active_turn=True, now=self.clock())
            require(decision["controls"][effect], "The selected destination policy refuses this effect.")
        require(vector == self._vector(), "Local state changed during inspection.")
        return vector

    def _target(self, relative):
        _portable(relative)
        return self.registry.route(self.vault_id, self.actor["project_id"], "selected_results", relative + "/MANIFEST.json").parent

    @contextmanager
    def _locked(self):
        # Same order as the existing managed-placement front door.
        with local_lock(self.access.state.root, ".workspace-state.lock"), \
                local_lock(self.policy.state.root, ".workspace-state.lock"), \
                local_lock(self.registry.state.root, ".workspace-state.lock"):
            yield

    def _plan(self, body):
        body = {**body, "schema_version": 1, "actor": deepcopy(self.actor), "vault_id": self.vault_id}
        _decode(_canonical(body))
        return {**body, "plan_sha256": _seal("gametools-local-checkpoint-plan-v1", body)}

    def _accept(self, plan, accepted, action):
        require(type(plan) is dict and plan.get("action") == action, "Select the exact operation preview.")
        body = {k: v for k, v in plan.items() if k != "plan_sha256"}
        require(plan.get("plan_sha256") == _hash(accepted) == _seal("gametools-local-checkpoint-plan-v1", body), "Accept the exact current private plan digest.")
        require(type(plan.get("schema_version")) is int and plan["schema_version"] == 1 and plan.get("actor") == self.actor and plan.get("vault_id") == self.vault_id, "Plan actor, vault or version mismatch.")
        _named(plan["operation_id"])
        vector = plan.get("expected_state")
        require(type(vector) is dict and set(vector) == {"access", "policy", "bindings"}, "An exact local revision vector is required.")
        for revision in vector.values(): _hash(revision)

    def _sources(self, selections, check):
        require(type(selections) is list and 1 <= len(selections) <= MAX_FILES, "Explicit bounded source selection is required.")
        rows, total = [], 0
        for row in selections:
            require(type(row) is dict and set(row) == {"content_class", "relative"}, "Select content class and relative name only.")
            cls, relative = row["content_class"], _portable(row["relative"])
            require(type(cls) is str and cls in CLASSES, "Unsupported selected content class.")
            path = self.registry.route(self.vault_id, self.actor["project_id"], cls, relative)
            fingerprint = stream_fingerprint(path, min(MAX_FILE_BYTES, MAX_TOTAL_BYTES - total), before_chunk=check)
            total += fingerprint["bytes"]
            rows.append({"content_class": cls, "relative": relative, **fingerprint})
        return sorted(rows, key=lambda r: (r["content_class"], r["relative"]))

    def preview_seed(self, selections, destination, operation_id):
        """Read only. The returned private plan is not transferable authority."""
        _named(operation_id)
        require(destination == "checkpoint-" + operation_id, "Use the operation-bound checkpoint destination.")
        require(type(selections) is list and all(type(r) is dict and type(r.get("content_class")) is str and r["content_class"] in CLASSES for r in selections), "Invalid selected classes.")
        specs = [("managed.read", r["content_class"], "transfer") for r in selections] + [("managed.write", "selected_results", "transfer")]
        vector = self._check(specs)
        check = lambda: self._check(specs, vector)
        target = self._target(destination)
        require(target.parent.is_dir() and not target.exists(), "Checkpoint destination must be new beneath an existing managed parent; inspect earlier attempts instead of retrying.")
        rows = self._sources(selections, check)
        marker = self.registry._binding(self.vault_id)["marker"]
        core = {"schema_version": 1, "kind": "GameToolsSeedCheckpoint", "workspace_id": self.actor["workspace_id"],
                "project_id": self.actor["project_id"], "replica_id": marker["replica_id"], "parents": [], "tombstones": [],
                "coverage": deepcopy(_COVERAGE), "files": rows}
        package = validate_package(_package(core))
        check()
        return self._plan({"action": "publish_seed", "operation_id": operation_id, "destination": destination,
                           "expected_state": vector, "package": package, "effects": ["write_new_checkpoint_only"], "source_revision_basis": "selected_file_hashes"})

    def publish_seed(self, plan, accepted_sha256, *, observer=None):
        """Publish a seed after exact revalidation; partial attempts remain intact.

        observer is an in-process test hook, never deserialized or exposed by CLI.
        """
        self._accept(plan, accepted_sha256, "publish_seed")
        require(plan["destination"] == "checkpoint-" + plan["operation_id"], "Checkpoint destination does not match this operation identity.")
        require(set(plan) == {"schema_version", "actor", "vault_id", "plan_sha256", "action", "operation_id", "destination", "expected_state", "package", "effects", "source_revision_basis"} and plan["effects"] == ["write_new_checkpoint_only"] and plan["source_revision_basis"] == "selected_file_hashes", "Unsupported publication plan.")
        package = validate_package(plan["package"])
        rows = package["checkpoint"]["core"]["files"]
        selections = [{k: r[k] for k in ("content_class", "relative")} for r in rows]
        specs = [("managed.read", r["content_class"], "transfer") for r in rows] + [("managed.write", "selected_results", "transfer")]
        check = lambda: self._check(specs, plan["expected_state"])
        require(package["schema_version"] == 1, "Use the explicit full/delta publisher for v2.")
        def verify():
            require(self._sources(selections, check) == rows, "Source changed; retain any incomplete attempt without publication.")
            core = package["checkpoint"]["core"]
            marker = self.registry._binding(self.vault_id)["marker"]
            require((core["workspace_id"], core["project_id"], core["replica_id"]) == (self.actor["workspace_id"], self.actor["project_id"], marker["replica_id"]), "Checkpoint belongs to another local scope.")
        sources = {r["sha256"]: self.registry.route(self.vault_id, self.actor["project_id"], r["content_class"], r["relative"]) for r in rows}
        return self._publish(plan, check, sources, {}, verify, observer)

    def _publish(self, plan, check, sources, inherited, verify, observer):
        package = plan["package"]
        rows = package["checkpoint"]["core"]["files"]
        with self._locked():
            check()
            target = self._target(plan["destination"])
            require(target.parent.is_dir() and not target.exists(), "Existing attempt is inspection-only; do not replay.")
            verify()
            check(); target.mkdir(mode=0o700)
            attempt = {"schema_version": 1, "operation_id": plan["operation_id"], "plan_sha256": plan["plan_sha256"],
                       "checkpoint_id": package["checkpoint"]["checkpoint_id"], "package_id": package["package_id"]}
            check(); _write_new(target / "_ATTEMPT.json", _canonical(attempt))
            check(); (target / "objects").mkdir(mode=0o700)
            with Journal.create(target / "AUDIT.jsonl", {"owner": "managed-checkpoint", **attempt}) as journal:
                journal.append("operation_intent", {"plan_sha256": plan["plan_sha256"], "operation_id": plan["operation_id"]})
                if observer: observer("staging_created")
                copied = set()
                for row in rows:
                    if row["sha256"] in copied or row["sha256"] not in _object_ids(package): continue
                    source = sources[row["sha256"]]
                    copy_stream_new(source, target / "objects" / row["sha256"], row["sha256"], row["bytes"], before_chunk=check)
                    copied.add(row["sha256"])
                    if observer: observer("object_written")
                check(); _write_new(target / "MANIFEST.json", _canonical(package))
                _verify_payload(target, package, check, inherited)
                journal.append("payload_verified", {"package_id": package["package_id"]})
                if observer: observer("payload_verified")
                verify()
                check()
                publication = {k: attempt[k] for k in ("operation_id", "checkpoint_id", "package_id")}
                if package["schema_version"] == 2:
                    publication.update(target_replica_id=self.registry._binding(self.vault_id)["marker"]["replica_id"], received=plan["action"] == "receive_checkpoint", verified=True, adopted=False)
                _write_new(target / "_PUBLISHED.json", _canonical(publication))
                if observer: observer("publication_written")
                journal.append("operation_result", publication)
                journal.append("session_closed", {"reason": "checkpoint_published"})
            return {"state": "PUBLISHED", **publication, "files": len(rows), "bytes": sum(r["bytes"] for r in rows),
                    "durability": "file_fsync_and_inspected_process_interruption_only", "adopted": False, "indexed": False, "context_exposed": False}

    def inspect(self, relative, *, parent_sources=()):
        """Read-only inspection of the same attempt; never repairs or replays."""
        specs = [("managed.read", "selected_results", "transfer")]
        vector = self._check(specs)
        check = lambda: self._check(specs, vector)
        root = self._target(relative)
        require(root.is_dir(), "The selected checkpoint attempt is unavailable.")
        base = {"automatic_retry": False, "effect": "none", "adopted": False, "indexed": False, "context_exposed": False}
        if not (root / "MANIFEST.json").exists():
            require(not (root / "_PUBLISHED.json").exists(), "Publication marker without a manifest is invalid.")
            _entries(root, 5)
            return {**base, "state": "STAGING_INCOMPLETE" if (root / "_ATTEMPT.json").exists() else "UNIDENTIFIED_PARTIAL_DIRECTORY", "next_boundary": "inspect_selected_partial_attempt"}
        package = validate_package(_load(root / "MANIFEST.json"))
        self._scope(package)
        specs += [("managed.read", r["content_class"], "transfer") for r in package["checkpoint"]["core"]["files"]]
        check()
        try:
            self._graph(relative, parent_sources, specs, vector, receipt=False)
        except MissingParents as exc:
            return {**base, "state": "MISSING_PARENTS", "missing_parents": exc.ids, "next_boundary": "receive_exact_parents_then_inspect"}
        details = {"package_id": package["package_id"], "checkpoint_id": package["checkpoint"]["checkpoint_id"]}
        if not (root / "_PUBLISHED.json").exists():
            return {**base, **details, "state": "VERIFIED_NOT_PUBLISHED", "next_boundary": "review_candidate_without_replay"}
        try:
            marker = _publication(root, package)
            if package["schema_version"] == 2:
                require(marker["target_replica_id"] == self.registry._binding(self.vault_id)["marker"]["replica_id"], "A peer receipt is not local destination acceptance.")
            clean = _publication_audit(root, package)
        except (ContextError, ValueError, OSError):
            check()
            return {**base, **details, "state": "PUBLICATION_UNCERTAIN", "next_boundary": "inspect_marker_and_intent_without_replay"}
        audit_state = "complete" if clean else "incomplete_or_invalid"
        check()
        return {**base, **marker, "state": "PUBLISHED" if clean else "PUBLISHED_RECEIPT_PENDING", "audit": audit_state,
                "next_boundary": "separate_reconstruction_preview" if clean else "inspect_evidence_no_automatic_repair"}

    def _scope(self, package):
        core = package["checkpoint"]["core"]
        require((core["workspace_id"], core["project_id"]) == (self.actor["workspace_id"], self.actor["project_id"]), "Package scope mismatch.")

    def _handover_path(self, operation_id):
        _named(operation_id)
        return local_path(self.access.state.root / "audit" / ("handover-" + operation_id))

    def _handover_local(self):
        binding = self.registry._binding(self.vault_id)
        for store in (self.access, self.policy, self.registry):
            require(self.registry.observer(store.state.root)["volume_id"] != binding["volume"]["volume_id"],
                    "Handover evidence and all local authority stores must stay off the selected data volume.")
        return binding["volume"]["volume_id"]

    def _handover_verify(self, source, parents, package, vector):
        specs = [("managed.read", "selected_results", "transfer")]
        specs += [("managed.read", r["content_class"], "transfer") for r in package["checkpoint"]["core"]["files"]]
        def check():
            self._check(specs, vector)
            require(self.access.authorize({**self.actor, "capability": "enrollment.manage"}, now=self.clock())["allowed"],
                    "Current local administrator authorization is required for handover preparation.")
        check()
        observed, _ = self._graph(source, parents, specs, vector)
        require(observed == package and package["schema_version"] == 2 and
                package["checkpoint"]["core"]["replica_id"] == self.registry._binding(self.vault_id)["marker"]["replica_id"],
                "Select an exact locally produced v2 checkpoint with complete publication evidence.")
        rows = package["checkpoint"]["core"]["files"]
        require(self._sources([{k: r[k] for k in ("content_class", "relative")} for r in rows], check) == rows,
                "Saved selected files differ from the checkpoint; publish a fresh checkpoint before handover.")
        check()

    def preview_handover(self, source, operation_id, expected_package_id, *, parent_sources=()):
        """Plan local quiescence only; external writers and native unmount remain pending."""
        _hash(expected_package_id); self._handover_path(operation_id)
        vector = self._check([("managed.read", "selected_results", "transfer")])
        package = validate_package(_load(self._target(source) / "MANIFEST.json")); self._scope(package)
        require(package["package_id"] == expected_package_id, "Select the exact handover package.")
        self._handover_verify(source, parent_sources, package, vector)
        volume = self._handover_local()
        require(not self._handover_path(operation_id).exists(), "Existing handover attempt is inspection-only; do not replay.")
        return self._plan({"action": "prepare_handover", "operation_id": operation_id, "source": source,
                           "parent_sources": list(parent_sources), "package": package, "expected_state": vector,
                           "data_volume_id": volume, "effects": ["stop_local_access_and_write_local_evidence"],
                           "pending": ["external_writer_shutdown", "native_safe_unmount", "physical_handover", "destination_local_acceptance"]})

    def _stop_observation(self):
        path = self.access.state.root / "LOCAL-STOP.json"
        if not path.exists() and not path.is_symlink(): return None
        raw, stat = _read(path)
        return {"sha256": digest(raw), "file_identity_sha256": digest(_canonical(
            [stat.st_dev, stat.st_ino, stat.st_mtime_ns, stat.st_ctime_ns]))}

    def prepare_handover(self, plan, accepted_sha256, *, observer=None):
        self._accept(plan, accepted_sha256, "prepare_handover")
        fields = {"schema_version", "actor", "vault_id", "plan_sha256", "action", "operation_id", "source", "parent_sources", "package",
                  "expected_state", "data_volume_id", "effects", "pending"}
        require(set(plan) == fields and plan["effects"] == ["stop_local_access_and_write_local_evidence"] and
                plan["pending"] == ["external_writer_shutdown", "native_safe_unmount", "physical_handover", "destination_local_acceptance"],
                "Unsupported handover effects; this operation cannot release or unmount a drive.")
        package = validate_package(plan["package"]); self._scope(package)
        with self._locked():
            self._handover_verify(plan["source"], plan["parent_sources"], package, plan["expected_state"])
            require(self._handover_local() == plan["data_volume_id"], "Data-volume identity changed.")
            target = self._handover_path(plan["operation_id"])
            require(not target.exists(), "Existing handover attempt is inspection-only; preserve it.")
            target.mkdir(mode=0o700)
            intent = {k: deepcopy(plan[k]) for k in ("operation_id", "plan_sha256", "actor", "vault_id", "expected_state", "data_volume_id")}
            intent.update(checkpoint_id=package["checkpoint"]["checkpoint_id"], package_id=package["package_id"])
            _write_new(target / "INTENT.json", _canonical(intent))
            with Journal.create(target / "AUDIT.jsonl", {"owner": "managed-checkpoint-handover", **intent}) as journal:
                journal.append("operation_intent", intent)
                if observer: observer("handover_verified")
                # Recheck saved bytes, receipts, stop, expiry and every revision
                # under the existing locks immediately before stopping access.
                self._handover_verify(plan["source"], plan["parent_sources"], package, plan["expected_state"])
                require(self._handover_local() == plan["data_volume_id"], "Local evidence volume changed.")
                self.access.stop_local()
                stop = self._stop_observation()
                if observer: observer("local_access_stopped")
                require(self._vector() == plan["expected_state"] and stop == self._stop_observation(), "State or stop changed after quiescence; inspect without replay.")
                result = {"state": "LOCAL_ACCESS_STOPPED", "operation_id": plan["operation_id"], "plan_sha256": accepted_sha256,
                          "checkpoint_id": intent["checkpoint_id"], "package_id": intent["package_id"], "stop": stop,
                          "drive_release": "pending_native_unmount", "all_writers_released": False, "physical_transfer_ready": False}
                _write_new(target / "RESULT.json", _canonical(result))
                if observer: observer("handover_receipt_written")
                journal.append("operation_result", result)
                journal.append("session_closed", {"reason": "local_handover_preparation_only"})
            return result

    def inspect_handover(self, operation_id):
        """Inspect local evidence even while stopped or the data volume is absent.

        Never reads that volume, resumes access, repairs a journal or removes a
        lock. The current OS owner can inspect private evidence after expiry.
        """
        target = self._handover_path(operation_id)
        self.access.snapshot()  # Existing local OS ownership and schema checks.
        require(target.is_dir(), "Selected local handover attempt is absent.")
        base = {"operation_id": operation_id, "effect": "none", "automatic_retry": False,
                "drive_release": "pending_native_unmount", "all_writers_released": False, "physical_transfer_ready": False}
        try:
            intent = _load(target / "INTENT.json")
            require(type(intent) is dict and set(intent) == {"operation_id", "plan_sha256", "actor", "vault_id", "expected_state", "data_volume_id", "checkpoint_id", "package_id"} and
                    intent["operation_id"] == operation_id and intent["actor"] == self.actor and intent["vault_id"] == self.vault_id, "Handover intent scope mismatch.")
            for key in ("plan_sha256", "checkpoint_id", "package_id"): _hash(intent[key])
            require(type(intent["expected_state"]) is dict and set(intent["expected_state"]) == {"access", "policy", "bindings"}, "Missing handover revision vector.")
            for revision in intent["expected_state"].values(): _hash(revision)
            stop = self._stop_observation()
            if stop is None: return {**base, "state": "LOCAL_STOP_NOT_PRESENT"}
            if not (target / "RESULT.json").exists(): return {**base, "state": "LOCAL_ACCESS_STOPPED_RECEIPT_PENDING"}
            result = _load(target / "RESULT.json")
            require(type(result) is dict and set(result) == {"state", "operation_id", "plan_sha256", "checkpoint_id", "package_id", "stop", "drive_release", "all_writers_released", "physical_transfer_ready"} and
                    all(result[k] == intent[k] for k in ("operation_id", "plan_sha256", "checkpoint_id", "package_id")) and result["state"] == "LOCAL_ACCESS_STOPPED" and
                    result["drive_release"] == base["drive_release"] and result["all_writers_released"] is False and result["physical_transfer_ready"] is False,
                    "Invalid local preparation evidence; physical release is not certified.")
            require(type(result["stop"]) is dict and set(result["stop"]) == {"sha256", "file_identity_sha256"}, "Missing exact stop observation.")
            for sha in result["stop"].values(): _hash(sha)
            if result["stop"] != stop: return {**base, "state": "LOCAL_STOP_REPLACED"}
            if self._vector() != intent["expected_state"]: return {**base, "state": "LOCAL_STATE_CHANGED"}
            audit = inspect_journal(target / "AUDIT.jsonl"); records = audit["verified_records"]
            clean = (audit["valid"] and audit["clean_end"] and records[-1]["kind"] == "session_closed" and
                     records[0]["data"] == {"owner": "managed-checkpoint-handover", **intent} and
                     [r["data"] for r in records if r["kind"] == "operation_intent"] == [intent] and
                     [r["data"] for r in records if r["kind"] == "operation_result"] == [result])
            return {**base, "state": "LOCAL_ACCESS_STOPPED" if clean else "LOCAL_ACCESS_STOPPED_RECEIPT_PENDING",
                    "checkpoint_id": intent["checkpoint_id"], "package_id": intent["package_id"]}
        except (ContextError, ValueError, OSError, JournalError):
            return {**base, "state": "HANDOVER_UNCERTAIN"}

    def _graph(self, relative, parent_sources, specs, vector, *, receipt=True):
        """Resolve only explicitly selected local parents, at most eight nodes.

        Parent locator order is immaterial. No directory search, remote fetch,
        alternate-parent fallback, trust from sender paths or persistent cache.
        """
        require(type(parent_sources) in {tuple, list} and len(parent_sources) <= 7 and len(set(parent_sources)) == len(parent_sources), "Select at most seven distinct local ancestor sources.")
        check = lambda: self._check(specs, vector)
        check()
        indexed, packages = {}, {}
        for name in (relative, *parent_sources):
            root = self._target(name)
            p = validate_package(_load(root / "MANIFEST.json")); self._scope(p)
            ident = p["checkpoint"]["checkpoint_id"]
            require(ident not in indexed, "Ambiguous duplicate checkpoint sources; select one exact representation.")
            indexed[ident], packages[name] = name, p
            specs.extend(("managed.read", r["content_class"], "transfer") for r in p["checkpoint"]["core"]["files"])
            check()
        active, resolved = set(), {}
        def visit(name):
            p = packages[name]; ident = p["checkpoint"]["checkpoint_id"]
            require(ident not in active, "Checkpoint ancestry cycle.")
            if ident in resolved: return resolved[ident]
            active.add(ident)
            inherited = {}
            missing = set(p["checkpoint"]["core"]["parents"]) - set(indexed)
            if missing: raise MissingParents(missing)
            for parent in p["checkpoint"]["core"]["parents"]:
                inherited.update(visit(indexed[parent]))
            root = self._target(name)
            _verify_payload(root, p, check, inherited)
            if name != relative or receipt:
                require(_publication_audit(root, p), "Parent/source publication receipt is incomplete; inspect without replay.")
                if p["schema_version"] == 2:
                    require(_publication(root, p)["target_replica_id"] == self.registry._binding(self.vault_id)["marker"]["replica_id"], "A peer receipt is not destination-local verification; receive it separately.")
            current = {r["sha256"]: root / "objects" / r["sha256"] if r["sha256"] in _object_ids(p) else inherited[r["sha256"]] for r in p["checkpoint"]["core"]["files"]}
            active.remove(ident); resolved[ident] = current
            return current
        sources = visit(relative)
        require(set(resolved) == set(indexed), "Unused parent locators are outside this exact ancestry.")
        check()
        return packages[relative], sources

    def preview_checkpoint(self, selections, destination, operation_id, *, parent=None, parent_sources=(), representation="full", extensions=None):
        """Additive v2 full/delta preview. V1 seed identities and APIs stay valid."""
        _named(operation_id)
        require(extensions is None or type(extensions) is dict, "Optional inert metadata must be an object.")
        require(destination == "checkpoint-" + operation_id and representation in {"full", "delta"}, "Select the operation-bound full/delta destination.")
        require(type(selections) is list and selections and all(type(r) is dict and r.get("content_class") in CLASSES for r in selections), "Explicit selected classes are required.")
        require(parent is not None or not parent_sources and representation == "full", "A delta requires an explicit exact parent.")
        require(type(parent_sources) in {tuple, list} and len(parent_sources) <= 6, "A new checkpoint plus its ancestors must fit the eight-node profile.")
        specs = [("managed.read", r["content_class"], "transfer") for r in selections] + [("managed.read", "selected_results", "transfer"), ("managed.write", "selected_results", "transfer")]
        vector = self._check(specs); check = lambda: self._check(specs, vector)
        inherited, parents = {}, []
        if parent is not None:
            p, inherited = self._graph(parent, parent_sources, specs, vector)
            parents = [p["checkpoint"]["checkpoint_id"]]
        target = self._target(destination)
        require(target.parent.is_dir() and not target.exists(), "Select a new checkpoint attempt; inspect earlier attempts.")
        rows = self._sources(selections, check)
        core = {"schema_version": 2, "kind": "GameToolsCheckpoint", "workspace_id": self.actor["workspace_id"], "project_id": self.actor["project_id"],
                "replica_id": self.registry._binding(self.vault_id)["marker"]["replica_id"], "parents": parents, "tombstones": [], "coverage": deepcopy(_COVERAGE), "files": rows}
        objects = sorted({r["sha256"] for r in rows} - (set(inherited) if representation == "delta" else set()))
        package = validate_package(_package(core, representation, objects, extensions)); check()
        return self._plan({"action": "publish_checkpoint", "operation_id": operation_id, "destination": destination, "expected_state": vector,
                           "package": package, "parent_sources": [parent, *parent_sources] if parent is not None else [], "effects": ["write_new_checkpoint_only"]})

    def preview_receive(self, source, destination, operation_id, expected_package_id, *, parent_sources=()):
        """Verify an already locally staged byte carrier; never copies its grants.

        The carrier has no active effect or sender-authenticity guarantee. Local
        per-class storage grants are required before payload inspection/writing.
        """
        _named(operation_id); _hash(expected_package_id)
        require(destination == "checkpoint-" + operation_id, "Use the operation-bound receive destination.")
        specs = [("managed.read", "selected_results", "transfer"), ("managed.write", "selected_results", "transfer")]
        vector = self._check(specs)
        package, _ = self._graph(source, parent_sources, specs, vector, receipt=False)
        require(package["schema_version"] == 2, "Destination-local receive receipts require v2; v1 seeds remain readable local sources/parents.")
        require(package["package_id"] == expected_package_id, "Received package differs from the selected representation.")
        for row in package["checkpoint"]["core"]["files"]: specs.append(("managed.write", row["content_class"], "transfer"))
        self._check(specs, vector)
        target = self._target(destination)
        require(target.parent.is_dir() and not target.exists(), "Receive destination already exists; inspect the same operation.")
        return self._plan({"action": "receive_checkpoint", "operation_id": operation_id, "source": source, "destination": destination, "expected_state": vector,
                           "package": package, "parent_sources": list(parent_sources), "effects": ["write_new_checkpoint_only"]})

    def publish_checkpoint(self, plan, accepted_sha256, *, observer=None):
        return self._publish_extended(plan, accepted_sha256, "publish_checkpoint", observer)

    def receive(self, plan, accepted_sha256, *, observer=None):
        return self._publish_extended(plan, accepted_sha256, "receive_checkpoint", observer)

    def _publish_extended(self, plan, accepted, action, observer):
        self._accept(plan, accepted, action)
        fields = {"schema_version", "actor", "vault_id", "plan_sha256", "action", "operation_id", "destination", "expected_state", "package", "parent_sources", "effects"}
        require(set(plan) == fields | ({"source"} if action == "receive_checkpoint" else set()) and plan["effects"] == ["write_new_checkpoint_only"], "Unsupported full/delta effect plan.")
        require(plan["destination"] == "checkpoint-" + plan["operation_id"], "Operation destination mismatch.")
        package = validate_package(plan["package"]); self._scope(package)
        require(package["schema_version"] == 2, "The explicit full/delta and receive interfaces require v2 packages.")
        specs = [("managed.read", "selected_results", "transfer"), ("managed.write", "selected_results", "transfer")]
        rows = package["checkpoint"]["core"]["files"]
        specs.extend(("managed.read", r["content_class"], "transfer") for r in rows)
        if action == "receive_checkpoint": specs.extend(("managed.write", r["content_class"], "transfer") for r in rows)
        check = lambda: self._check(specs, plan["expected_state"])
        check(); parents = plan["parent_sources"]
        require(type(parents) is list and len(parents) <= 7, "Checkpoint ancestry exceeds the eight-node profile.")
        inherited = {}
        if action == "receive_checkpoint":
            observed, sources = self._graph(plan["source"], parents, specs, plan["expected_state"], receipt=False)
            require(observed == package, "Received source changed after preview.")
            inherited = {sha: path for sha, path in sources.items() if sha not in _object_ids(package)}
            def verify():
                p, _ = self._graph(plan["source"], parents, specs, plan["expected_state"], receipt=False)
                require(p == package, "Received source changed; preserve staging without publication.")
        else:
            require(package["schema_version"] == 2 and package["checkpoint"]["core"]["replica_id"] == self.registry._binding(self.vault_id)["marker"]["replica_id"], "Use the current local v2 checkpoint producer.")
            if package["checkpoint"]["core"]["parents"]:
                require(parents, "Select the exact parent source.")
                p, inherited = self._graph(parents[0], parents[1:], specs, plan["expected_state"])
                require([p["checkpoint"]["checkpoint_id"]] == package["checkpoint"]["core"]["parents"], "Wrong expected parent.")
            else: require(parents == [], "Unexpected parent sources.")
            sources = {r["sha256"]: self.registry.route(self.vault_id, self.actor["project_id"], r["content_class"], r["relative"]) for r in rows}
            def verify():
                require(self._sources([{k: r[k] for k in ("content_class", "relative")} for r in rows], check) == rows, "Selected source drift; preserve staging.")
                if parents:
                    p, _ = self._graph(parents[0], parents[1:], specs, plan["expected_state"])
                    require([p["checkpoint"]["checkpoint_id"]] == package["checkpoint"]["core"]["parents"], "Parent drift.")
        return self._publish(plan, check, sources, inherited, verify, observer)

    def preview_reconstruction(self, source_relative, destination, operation_id, expected_package_id, *, parent_sources=(), selection=None):
        _named(operation_id); _hash(expected_package_id)
        require(destination == "reconstruction-" + operation_id, "Use the operation-bound inactive destination.")
        source = self._target(source_relative)
        self._check([("managed.read", "selected_results", "transfer")])
        package = validate_package(_load(source / "MANIFEST.json"))
        require(package["package_id"] == expected_package_id, "Selected package revision changed.")
        core = package["checkpoint"]["core"]
        require((core["workspace_id"], core["project_id"]) == (self.actor["workspace_id"], self.actor["project_id"]), "Package scope mismatch.")
        specs = [("managed.read", "selected_results", "transfer"), ("managed.write", "selected_results", "adoption")] + [(capability, r["content_class"], effect) for r in core["files"] for capability, effect in (("managed.read", "transfer"), ("managed.write", "adoption"))]
        vector = self._check(specs)
        check = lambda: self._check(specs, vector)
        self._graph(source_relative, parent_sources, specs, vector)
        _selected_rows(package, selection)
        target = self._target(destination)
        require(target.parent.is_dir() and not target.exists(), "Select a new inactive reconstruction directory, not an active or existing copy.")
        check()
        extra = {"parent_sources": list(parent_sources), "selection": deepcopy(selection)} if package["schema_version"] == 2 or selection is not None else {}
        return self._plan({"action": "reconstruct_inactive", "operation_id": operation_id, "source": source_relative, "destination": destination,
                           "expected_state": vector, "package": package, "effects": ["write_new_inactive_copy_only"], **extra})

    def preview_recovery(self, source_relative, incomplete_relative, selection, destination, operation_id, expected_package_id, *, parent_sources=(), rollback=False):
        """Recover selected files to a new copy, preserving all interrupted work."""
        plan = self.preview_reconstruction(source_relative, destination, operation_id, expected_package_id, parent_sources=parent_sources, selection=selection)
        old = self._target(incomplete_relative)
        require(type(rollback) is bool and old.is_dir(), "Select an existing inactive copy and an explicit recovery kind.")
        old_package = validate_package(_load(old / "MANIFEST.json")); self._scope(old_package)
        if rollback:
            require(old_package["checkpoint"]["core"]["parents"] == [plan["package"]["checkpoint"]["checkpoint_id"]], "Rollback requires the exact direct parent, not an unrelated historical package.")
        else: require(old_package == plan["package"], "Select an interrupted/restored copy of this exact package.")
        specs = [("managed.read", r["content_class"], "transfer") for r in old_package["checkpoint"]["core"]["files"]] + [("managed.read", "selected_results", "transfer")]
        check = lambda: self._check(specs, plan["expected_state"])
        # Bind a read-only observation of the selected old paths. No overwrite,
        # deletion, automatic repair or re-use of old operation authority.
        observation = self._recovery_observation(old, _selected_rows(plan["package"], selection), check); check()
        return self._plan({**{k: v for k, v in plan.items() if k != "plan_sha256"}, "recovery_of": incomplete_relative, "recovery_observation": observation,
                           "recovery_package": old_package, "recovery_kind": "rollback_parent_subset" if rollback else "recover_subset"})

    def _recovery_observation(self, root, rows, check=None):
        observed = []
        for row in rows:
            path = local_path(root / "data" / CLASSES[row["content_class"]] / row["relative"])
            fp = stream_fingerprint(path, MAX_FILE_BYTES, before_chunk=check) if path.exists() else None
            observed.append({"content_class": row["content_class"], "relative": row["relative"], "observed": fp})
        return observed

    def reconstruct(self, plan, accepted_sha256, *, observer=None):
        self._accept(plan, accepted_sha256, "reconstruct_inactive")
        require(plan["destination"] == "reconstruction-" + plan["operation_id"], "Reconstruction destination does not match this operation identity.")
        base_fields = {"schema_version", "actor", "vault_id", "plan_sha256", "action", "operation_id", "source", "destination", "expected_state", "package", "effects"}
        extras = ({"parent_sources", "selection"} if "selection" in plan else set()) | ({"recovery_of", "recovery_observation", "recovery_package", "recovery_kind"} if "recovery_of" in plan else set())
        require(set(plan) == base_fields | extras and plan["effects"] == ["write_new_inactive_copy_only"], "Unsupported reconstruction plan.")
        package = validate_package(plan["package"])
        core = package["checkpoint"]["core"]
        require((core["workspace_id"], core["project_id"]) == (self.actor["workspace_id"], self.actor["project_id"]), "Reconstruction package scope mismatch.")
        rows = _selected_rows(package, plan.get("selection"))
        specs = [("managed.read", "selected_results", "transfer"), ("managed.write", "selected_results", "adoption")] + [(capability, r["content_class"], effect) for r in core["files"] for capability, effect in (("managed.read", "transfer"), ("managed.write", "adoption"))]
        if "recovery_of" in plan:
            prior = validate_package(plan["recovery_package"]); self._scope(prior)
            require(plan["recovery_kind"] in {"recover_subset", "rollback_parent_subset"} and plan.get("selection") is not None, "Unsupported granular recovery effect.")
            require(prior == package if plan["recovery_kind"] == "recover_subset" else prior["checkpoint"]["core"]["parents"] == [package["checkpoint"]["checkpoint_id"]], "Recovery ancestry mismatch.")
            specs.extend(("managed.read", r["content_class"], "transfer") for r in prior["checkpoint"]["core"]["files"])
        check = lambda: self._check(specs, plan["expected_state"])
        with self._locked():
            check()
            source, target = self._target(plan["source"]), self._target(plan["destination"])
            observed, sources = self._graph(plan["source"], plan.get("parent_sources", ()), specs, plan["expected_state"])
            require(observed == package, "Package or publication evidence changed after preview.")
            if "recovery_of" in plan:
                require(_load(self._target(plan["recovery_of"]) / "MANIFEST.json") == plan["recovery_package"] and self._recovery_observation(self._target(plan["recovery_of"]), rows, check) == plan["recovery_observation"], "Selected interrupted files changed; review recovery again.")
            require(target.parent.is_dir() and not target.exists(), "Existing reconstruction is inspection-only; preserve it.")
            check(); target.mkdir(mode=0o700)
            start = {"operation_id": plan["operation_id"], "plan_sha256": accepted_sha256, "package_id": package["package_id"], "mode": "inactive_new_copy"}
            if plan.get("selection") is not None:
                start["selection"] = [{k: r[k] for k in ("content_class", "relative")} for r in rows]
            if "recovery_of" in plan: start["recovery_kind"] = plan["recovery_kind"]
            check(); _write_new(target / "_RECONSTRUCTION.json", _canonical(start))
            check(); _write_new(target / "MANIFEST.json", _canonical(package))
            with Journal.create(target / "AUDIT.jsonl", {"owner": "managed-checkpoint-reconstruction", **start}) as journal:
                journal.append("operation_intent", start)
                for row in rows:
                    dest = local_path(target / "data" / CLASSES[row["content_class"]] / row["relative"])
                    require(target in dest.parents, "Reconstruction escaped its inactive root.")
                    check(); dest.parent.mkdir(parents=True, exist_ok=True)
                    copy_stream_new(sources[row["sha256"]], dest, row["sha256"], row["bytes"], before_chunk=check)
                    if observer: observer("file_reconstructed")
                observed, _ = self._graph(plan["source"], plan.get("parent_sources", ()), specs, plan["expected_state"])
                require(observed == package, "Source changed during reconstruction.")
                for row in rows:
                    path = target / "data" / CLASSES[row["content_class"]] / row["relative"]
                    require(stream_fingerprint(path, row["bytes"], before_chunk=check) == {"bytes": row["bytes"], "sha256": row["sha256"]}, "Reconstruction changed before completion; preserve the incomplete copy.")
                _restored_closure(target, rows); check()
                receipt = {"state": "RECONSTRUCTED_INACTIVE", "operation_id": plan["operation_id"], "package_id": package["package_id"],
                           "files": len(rows), "bytes": sum(r["bytes"] for r in rows), "active_adoption": False, "indexed": False, "context_exposed": False}
                if "selection" in start: receipt["whole_checkpoint"] = False
                if "recovery_kind" in start: receipt["recovery_kind"] = start["recovery_kind"]
                _write_new(target / "_COMPLETE.json", _canonical(receipt))
                if observer: observer("reconstruction_complete_written")
                journal.append("operation_result", receipt)
                journal.append("session_closed", {"reason": "inactive_reconstruction_complete"})
            return receipt

    def inspect_reconstruction(self, relative):
        specs = [("managed.read", "selected_results", "transfer")]
        vector = self._check(specs)
        check = lambda: self._check(specs, vector)
        root = self._target(relative)
        require(root.is_dir(), "Selected reconstruction is absent.")
        if not (root / "MANIFEST.json").exists():
            return {"state": "RECONSTRUCTION_INCOMPLETE", "effect": "none", "automatic_retry": False}
        package = validate_package(_load(root / "MANIFEST.json"))
        self._scope(package)
        specs += [("managed.read", r["content_class"], "transfer") for r in package["checkpoint"]["core"]["files"]]
        check()
        missing, partial = [], []
        start = _load(root / "_RECONSTRUCTION.json")
        require(type(start) is dict and set(start) == {"operation_id", "plan_sha256", "package_id", "mode"} | ({"selection"} if "selection" in start else set()) | ({"recovery_kind"} if "recovery_kind" in start else set()) and start["package_id"] == package["package_id"] and start["mode"] == "inactive_new_copy", "Reconstruction intent mismatch.")
        require("recovery_kind" not in start or "selection" in start and start["recovery_kind"] in {"recover_subset", "rollback_parent_subset"}, "Unsupported recovery receipt kind.")
        _named(start["operation_id"]); _hash(start["plan_sha256"])
        rows = _selected_rows(package, start.get("selection"))
        for row in rows:
            path = local_path(root / "data" / CLASSES[row["content_class"]] / row["relative"])
            if not path.exists(): missing.append({"content_class": row["content_class"], "relative": row["relative"]}); continue
            if stream_fingerprint(path, MAX_FILE_BYTES, before_chunk=check) != {"bytes": row["bytes"], "sha256": row["sha256"]}:
                partial.append({"content_class": row["content_class"], "relative": row["relative"], "state": "partial_or_changed_not_verified"})
        complete = (root / "_COMPLETE.json").exists()
        require(not complete or not missing and not partial, "Completion receipt contradicts missing or changed files; integrity failure.")
        state = "RECONSTRUCTION_INCOMPLETE"
        if complete:
            receipt = _load(root / "_COMPLETE.json")
            expected = {"state": "RECONSTRUCTED_INACTIVE", "operation_id": start["operation_id"], "package_id": package["package_id"], "files": len(rows), "bytes": sum(r["bytes"] for r in rows), "active_adoption": False, "indexed": False, "context_exposed": False}
            if "selection" in start: expected["whole_checkpoint"] = False
            if "recovery_kind" in start: expected["recovery_kind"] = start["recovery_kind"]
            require(receipt == expected and all(type(receipt[k]) is bool for k in ("active_adoption", "indexed", "context_exposed")) and type(receipt["files"]) is int and type(receipt["bytes"]) is int, "Reconstruction receipt identity/effects mismatch.")
            require("selection" not in start or receipt["whole_checkpoint"] is False, "A subset cannot claim whole checkpoint restoration.")
            _restored_closure(root, rows)
            try:
                audit = inspect_journal(root / "AUDIT.jsonl")
                results = [r["data"] for r in audit["verified_records"] if r["kind"] == "operation_result"]
                records = audit["verified_records"]
                clean = (audit["valid"] and audit["clean_end"] and records[-1]["kind"] == "session_closed" and
                         records[0]["data"] == {"owner": "managed-checkpoint-reconstruction", **start} and
                         [r["data"] for r in records if r["kind"] == "operation_intent"] == [start] and results == [receipt])
                state = "RECONSTRUCTED_INACTIVE" if clean else "RECONSTRUCTED_RECEIPT_PENDING"
            except (JournalError, OSError):
                state = "RECONSTRUCTED_RECEIPT_PENDING"
        check()
        subset = {"whole_checkpoint": False, "selected_files": len(rows), "recovery_kind": start.get("recovery_kind", "selected_subset")} if "selection" in start else {}
        return {"state": state, "package_id": package["package_id"], "missing": missing, "partial": partial, "effect": "none", "automatic_retry": False, "active_adoption": False, "indexed": False, "context_exposed": False, **subset}
