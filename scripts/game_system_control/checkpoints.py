"""MCI-08 bounded seed checkpoints and inactive reconstruction.

This format adapter reuses UserData IO, Journal, VaultRegistry, PolicyStore,
AccessStore and their cooperative locks. No network, native-state import,
active project adoption, index/context delivery, task replay or garbage collection.
The first format supports explicit selected regular files, no parents/tombstones.
Application consistency and physical power-loss durability are not asserted.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import os
import time

from GameToolAIContracts import stable_revision
from GameToolUserData import (
    MAX_FILES, MAX_FILE_BYTES, MAX_TOTAL_BYTES, MAX_MANIFEST_BYTES,
    _canonical, _decode, _read, _write_new, _relative, digest, local_path,
    stream_fingerprint, copy_stream_new,
)
from GameToolJournal import Journal, JournalError, inspect_journal
from game_mod_ops.safety import local_lock
from .contracts import require, identifier, SHA
from .vault import CLASSES, EXCLUDED, _relative_managed
from .policy import evaluate

VERSION = "0.1.0-preview.1"
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


def _package(core):
    checkpoint = {"checkpoint_id": _seal("gametools-checkpoint-v1", core), "core": deepcopy(core)}
    body = {"schema_version": 1, "kind": "GameToolsSeedPackage", "format": "directory-objects-v1", "checkpoint": checkpoint}
    return {**body, "package_id": _seal("gametools-package-v1", body)}


def validate_package(value):
    """Strict operational validation; projection-only schemas are not authority."""
    _decode(_canonical(value))
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


def _verify_payload(root, package, check=None):
    root = local_path(root)
    package = validate_package(package)
    allowed = {"_ATTEMPT.json", "AUDIT.jsonl", "objects", "MANIFEST.json", "_PUBLISHED.json"}
    require(_entries(root, 5) <= allowed, "Unknown files in the selected package.")
    objects = {r["sha256"]: r for r in package["checkpoint"]["core"]["files"]}
    require(_entries(root / "objects", MAX_FILES) == set(objects), "Payload objects are missing or unlisted.")
    for sha, row in objects.items():
        observed = stream_fingerprint(root / "objects" / sha, row["bytes"], before_chunk=check)
        require(observed == {"bytes": row["bytes"], "sha256": sha}, "Payload integrity failed; do not adopt or retry.")
    return package


def _publication(root, package):
    value = _load(root / "_PUBLISHED.json")
    require(type(value) is dict and set(value) == {"operation_id", "checkpoint_id", "package_id"}, "Invalid publication marker.")
    _named(value["operation_id"])
    require(value["checkpoint_id"] == package["checkpoint"]["checkpoint_id"] and value["package_id"] == package["package_id"], "Publication marker identity mismatch.")
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
        policy_revision = stable_revision(body)
        for capability, cls, effect in sorted(set(specs)):
            request = {**self.actor, "capability": capability, "storage_id": self.vault_id,
                       "content_class": cls, "policy_revision": policy_revision}
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
        with self._locked():
            check()
            target = self._target(plan["destination"])
            require(target.parent.is_dir() and not target.exists(), "Existing attempt is inspection-only; do not replay.")
            require(self._sources(selections, check) == rows, "Source changed after preview; nothing was published.")
            expected_core = package["checkpoint"]["core"]
            marker = self.registry._binding(self.vault_id)["marker"]
            require((expected_core["workspace_id"], expected_core["project_id"], expected_core["replica_id"]) == (self.actor["workspace_id"], self.actor["project_id"], marker["replica_id"]), "Checkpoint belongs to another local scope.")
            check(); target.mkdir(mode=0o700)
            attempt = {"schema_version": 1, "operation_id": plan["operation_id"], "plan_sha256": accepted_sha256,
                       "checkpoint_id": package["checkpoint"]["checkpoint_id"], "package_id": package["package_id"]}
            check(); _write_new(target / "_ATTEMPT.json", _canonical(attempt))
            check(); (target / "objects").mkdir(mode=0o700)
            with Journal.create(target / "AUDIT.jsonl", {"owner": "managed-checkpoint", **attempt}) as journal:
                journal.append("operation_intent", {"plan_sha256": accepted_sha256, "operation_id": plan["operation_id"]})
                if observer: observer("staging_created")
                copied = set()
                for row in rows:
                    if row["sha256"] in copied: continue
                    source = self.registry.route(self.vault_id, self.actor["project_id"], row["content_class"], row["relative"])
                    copy_stream_new(source, target / "objects" / row["sha256"], row["sha256"], row["bytes"], before_chunk=check)
                    copied.add(row["sha256"])
                    if observer: observer("object_written")
                check(); _write_new(target / "MANIFEST.json", _canonical(package))
                _verify_payload(target, package, check)
                journal.append("payload_verified", {"package_id": package["package_id"]})
                if observer: observer("payload_verified")
                require(self._sources(selections, check) == rows, "Source changed during staging; retain candidate without publication.")
                check()
                publication = {k: attempt[k] for k in ("operation_id", "checkpoint_id", "package_id")}
                _write_new(target / "_PUBLISHED.json", _canonical(publication))
                if observer: observer("publication_written")
                journal.append("operation_result", publication)
                journal.append("session_closed", {"reason": "checkpoint_published"})
            return {"state": "PUBLISHED", **publication, "files": len(rows), "bytes": sum(r["bytes"] for r in rows),
                    "durability": "file_fsync_and_inspected_process_interruption_only", "adopted": False, "indexed": False, "context_exposed": False}

    def inspect(self, relative):
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
        specs += [("managed.read", r["content_class"], "transfer") for r in package["checkpoint"]["core"]["files"]]
        check()
        _verify_payload(root, package, check)
        details = {"package_id": package["package_id"], "checkpoint_id": package["checkpoint"]["checkpoint_id"]}
        if not (root / "_PUBLISHED.json").exists():
            return {**base, **details, "state": "VERIFIED_NOT_PUBLISHED", "next_boundary": "review_candidate_without_replay"}
        marker = _publication(root, package)
        attempt = _load(root / "_ATTEMPT.json")
        require(type(attempt) is dict and set(attempt) == {"schema_version", "operation_id", "plan_sha256", "checkpoint_id", "package_id"} and type(attempt["schema_version"]) is int and attempt["schema_version"] == 1, "Invalid operation intent marker.")
        require(all(attempt.get(k) == v for k, v in marker.items()), "Attempt and publication identities differ.")
        _hash(attempt["plan_sha256"])
        try:
            audit = inspect_journal(root / "AUDIT.jsonl")
            records = audit["verified_records"]
            results = [r["data"] for r in records if r["kind"] == "operation_result"]
            created = records[0]["data"] if records else {}
            clean = audit["valid"] and audit["clean_end"] and records[-1]["kind"] == "session_closed" and results == [marker] and all(created.get(k) == v for k, v in attempt.items())
            audit_state = "complete" if clean else "incomplete_or_invalid"
        except (JournalError, OSError):
            clean, audit_state = False, "unreadable"
        check()
        return {**base, **marker, "state": "PUBLISHED" if clean else "PUBLISHED_RECEIPT_PENDING", "audit": audit_state,
                "next_boundary": "separate_reconstruction_preview" if clean else "inspect_evidence_no_automatic_repair"}

    def preview_reconstruction(self, source_relative, destination, operation_id, expected_package_id):
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
        _verify_payload(source, package, check); _publication(source, package)
        require(self.inspect(source_relative)["state"] == "PUBLISHED", "Publication evidence needs reconciliation before reconstruction.")
        target = self._target(destination)
        require(target.parent.is_dir() and not target.exists(), "Select a new inactive reconstruction directory, not an active or existing copy.")
        check()
        return self._plan({"action": "reconstruct_inactive", "operation_id": operation_id, "source": source_relative, "destination": destination,
                           "expected_state": vector, "package": package, "effects": ["write_new_inactive_copy_only"]})

    def reconstruct(self, plan, accepted_sha256, *, observer=None):
        self._accept(plan, accepted_sha256, "reconstruct_inactive")
        require(plan["destination"] == "reconstruction-" + plan["operation_id"], "Reconstruction destination does not match this operation identity.")
        require(set(plan) == {"schema_version", "actor", "vault_id", "plan_sha256", "action", "operation_id", "source", "destination", "expected_state", "package", "effects"} and plan["effects"] == ["write_new_inactive_copy_only"], "Unsupported reconstruction plan.")
        package = validate_package(plan["package"])
        core = package["checkpoint"]["core"]
        require((core["workspace_id"], core["project_id"]) == (self.actor["workspace_id"], self.actor["project_id"]), "Reconstruction package scope mismatch.")
        rows = core["files"]
        specs = [("managed.read", "selected_results", "transfer"), ("managed.write", "selected_results", "adoption")] + [(capability, r["content_class"], effect) for r in rows for capability, effect in (("managed.read", "transfer"), ("managed.write", "adoption"))]
        check = lambda: self._check(specs, plan["expected_state"])
        with self._locked():
            check()
            source, target = self._target(plan["source"]), self._target(plan["destination"])
            require(_load(source / "MANIFEST.json") == package and self.inspect(plan["source"])["state"] == "PUBLISHED", "Package or publication evidence changed after preview.")
            require(target.parent.is_dir() and not target.exists(), "Existing reconstruction is inspection-only; preserve it.")
            check(); target.mkdir(mode=0o700)
            start = {"operation_id": plan["operation_id"], "plan_sha256": accepted_sha256, "package_id": package["package_id"], "mode": "inactive_new_copy"}
            check(); _write_new(target / "_RECONSTRUCTION.json", _canonical(start))
            check(); _write_new(target / "MANIFEST.json", _canonical(package))
            with Journal.create(target / "AUDIT.jsonl", {"owner": "managed-checkpoint-reconstruction", **start}) as journal:
                journal.append("operation_intent", start)
                for row in rows:
                    dest = local_path(target / "data" / CLASSES[row["content_class"]] / row["relative"])
                    require(target in dest.parents, "Reconstruction escaped its inactive root.")
                    check(); dest.parent.mkdir(parents=True, exist_ok=True)
                    copy_stream_new(source / "objects" / row["sha256"], dest, row["sha256"], row["bytes"], before_chunk=check)
                    if observer: observer("file_reconstructed")
                _verify_payload(source, package, check)
                for row in rows:
                    path = target / "data" / CLASSES[row["content_class"]] / row["relative"]
                    require(stream_fingerprint(path, row["bytes"], before_chunk=check) == {"bytes": row["bytes"], "sha256": row["sha256"]}, "Reconstruction changed before completion; preserve the incomplete copy.")
                check()
                receipt = {"state": "RECONSTRUCTED_INACTIVE", "operation_id": plan["operation_id"], "package_id": package["package_id"],
                           "files": len(rows), "bytes": sum(r["bytes"] for r in rows), "active_adoption": False, "indexed": False, "context_exposed": False}
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
        specs += [("managed.read", r["content_class"], "transfer") for r in package["checkpoint"]["core"]["files"]]
        check()
        missing, partial = [], []
        for row in package["checkpoint"]["core"]["files"]:
            path = local_path(root / "data" / CLASSES[row["content_class"]] / row["relative"])
            if not path.exists(): missing.append({"content_class": row["content_class"], "relative": row["relative"]}); continue
            if stream_fingerprint(path, MAX_FILE_BYTES, before_chunk=check) != {"bytes": row["bytes"], "sha256": row["sha256"]}:
                partial.append({"content_class": row["content_class"], "relative": row["relative"], "state": "partial_or_changed_not_verified"})
        complete = (root / "_COMPLETE.json").exists()
        require(not complete or not missing and not partial, "Completion receipt contradicts missing or changed files; integrity failure.")
        state = "RECONSTRUCTION_INCOMPLETE"
        if complete:
            receipt = _load(root / "_COMPLETE.json")
            start = _load(root / "_RECONSTRUCTION.json")
            require(type(start) is dict and set(start) == {"operation_id", "plan_sha256", "package_id", "mode"} and start["package_id"] == package["package_id"] and start["mode"] == "inactive_new_copy", "Reconstruction intent mismatch.")
            _named(start["operation_id"]); _hash(start["plan_sha256"])
            rows = package["checkpoint"]["core"]["files"]
            expected = {"state": "RECONSTRUCTED_INACTIVE", "operation_id": start["operation_id"], "package_id": package["package_id"], "files": len(rows), "bytes": sum(r["bytes"] for r in rows), "active_adoption": False, "indexed": False, "context_exposed": False}
            require(receipt == expected and all(type(receipt[k]) is bool for k in ("active_adoption", "indexed", "context_exposed")) and type(receipt["files"]) is int and type(receipt["bytes"]) is int, "Reconstruction receipt identity/effects mismatch.")
            try:
                audit = inspect_journal(root / "AUDIT.jsonl")
                results = [r["data"] for r in audit["verified_records"] if r["kind"] == "operation_result"]
                state = "RECONSTRUCTED_INACTIVE" if audit["valid"] and audit["clean_end"] and results == [receipt] else "RECONSTRUCTED_RECEIPT_PENDING"
            except (JournalError, OSError):
                state = "RECONSTRUCTED_RECEIPT_PENDING"
        check()
        return {"state": state, "package_id": package["package_id"], "missing": missing, "partial": partial, "effect": "none", "automatic_retry": False, "active_adoption": False, "indexed": False, "context_exposed": False}
