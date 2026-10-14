"""Private game-installation identities and one bounded UMM read adapter.

Registration is an explicit local operator action.  Modern AI tools may list or
inspect only an already registered opaque instance ID; they never receive or
supply a filesystem path.  This module writes registry metadata only and never
writes a game, manager profile, loader, mod, save, input profile, or setting.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import re
import uuid

from game_mod_ops.managers import inspect_game, compare_installed
from game_mod_ops.safety import (
    ModError, contained, json_new, local_lock, no_links, object_hash,
    read_json, require, slug,
)

VERSION = "0.1.0"
SCHEMA_VERSION = 1
MAX_INSTANCES = 64
MAX_RECORD_BYTES = 64 * 1024
_ACCEPTED_ADAPTERS = {"umm"}
_STORES = {"steam", "gog", "epic", "microsoft", "other", "unknown"}
_SHORT = re.compile(r"[^\x00-\x1f\x7f]{1,120}\Z")


def _text(value, field, *, optional=False):
    if value is None and optional:
        return None
    require(type(value) is str and bool(_SHORT.fullmatch(value)),
            "INSTANCE_SCHEMA", f"{field} must be short printable text.")
    lower = value.casefold()
    require(not any(mark in value for mark in ("/", "\\", ":", "@")) and ".." not in value and
            not any(token in lower for token in ("ghp_", "github_pat_", "bearer ", "sk-")) and
            not re.search(r"\bAKIA[A-Z0-9]{16}\b", value),
            "INSTANCE_PRIVATE_LABEL",
            f"{field} must be a path-free, credential-free public label.")
    return value


def _path_key(path: Path) -> str:
    return os.path.normcase(os.path.realpath(os.path.abspath(str(path))))


def _same_path(left: Path, right: Path) -> bool:
    try:
        return os.path.samefile(left, right)
    except (FileNotFoundError, OSError):
        return _path_key(left) == _path_key(right)


class InstanceRegistry:
    """Opaque identities over explicitly selected local game directories."""

    def __init__(self, data_dir: Path, workspaces):
        self.data_dir = no_links(Path(data_dir))
        self.root = self.data_dir / "game-instances"
        self.workspaces = workspaces

    def _definition(self, game_id):
        game_id = slug(game_id)
        support = self.workspaces.catalog.support.rows().get(game_id)
        recipe_row = self.workspaces.catalog.recipes().get(game_id)
        if support is not None:
            definition = deepcopy(support["pack"]["definition"])
            support_revision = support["revision"]
        elif recipe_row and recipe_row["recipe"].get("game_definition"):
            definition = deepcopy(recipe_row["recipe"]["game_definition"])
            support_revision = recipe_row["recipe"].get("support_revision")
        else:
            raise ModError("ADAPTER_UNAVAILABLE",
                           "This game has no reviewed folder-identification definition.")
        require(definition["adapter"] in _ACCEPTED_ADAPTERS,
                "ADAPTER_ACCEPTANCE_PENDING",
                "This slice accepts only the reviewed UMM read adapter.")
        return definition, support_revision

    def _paths(self):
        if not self.root.exists():
            return []
        no_links(self.root)
        rows = []
        for path in sorted(self.root.glob("*.json"), key=lambda item: item.name.casefold()):
            require(len(rows) < MAX_INSTANCES, "RECORD_LIMIT",
                    "Instance registry limit reached; no records were silently omitted.")
            rows.append(no_links(path))
        return rows

    @staticmethod
    def _validate_record(value):
        require(type(value) is dict and set(value) == {"schema_version", "kind", "body", "revision"},
                "INSTANCE_CORRUPT", "Unexpected game-instance record fields.")
        require(value["schema_version"] == SCHEMA_VERSION and value["kind"] == "game-instance",
                "INSTANCE_CORRUPT", "Unsupported game-instance record.")
        body = value["body"]
        fields = {
            "instance_id", "game_id", "manager_id", "adapter", "platform",
            "store", "build", "profile", "definition_revision",
            "support_revision", "game_dir", "nonce",
        }
        require(type(body) is dict and set(body) == fields,
                "INSTANCE_CORRUPT", "Unexpected game-instance body fields.")
        slug(body["instance_id"]); slug(body["game_id"]); slug(body["manager_id"])
        require(body["adapter"] in _ACCEPTED_ADAPTERS and body["platform"] in {"windows", "linux", "macos"},
                "INSTANCE_CORRUPT", "Instance adapter or platform is unsupported.")
        require(body["store"] in _STORES, "INSTANCE_CORRUPT", "Instance store is unsupported.")
        _text(body["build"], "build")
        _text(body["profile"], "profile", optional=True)
        require(type(body["definition_revision"]) is str and len(body["definition_revision"]) == 64,
                "INSTANCE_CORRUPT", "Definition revision is invalid.")
        require(body["support_revision"] is None or
                (type(body["support_revision"]) is str and len(body["support_revision"]) == 64),
                "INSTANCE_CORRUPT", "Support revision is invalid.")
        require(type(body["game_dir"]) is str and os.path.isabs(body["game_dir"]),
                "INSTANCE_CORRUPT", "Private game directory is invalid.")
        require(type(body["nonce"]) is str and bool(re.fullmatch(r"[a-f0-9]{32}", body["nonce"])),
                "INSTANCE_CORRUPT", "Instance nonce is invalid.")
        require(value["revision"] == object_hash(body),
                "INSTANCE_CORRUPT", "Game-instance record changed after registration.")
        return value

    def _read_path(self, path: Path):
        return self._validate_record(read_json(path, MAX_RECORD_BYTES))

    def _read(self, instance_id):
        instance_id = slug(instance_id)
        path = contained(self.root, instance_id + ".json")
        require(path.is_file(), "INSTANCE_NOT_FOUND", "Registered game instance was not found.")
        record = self._read_path(path)
        require(record["body"]["instance_id"] == instance_id,
                "INSTANCE_CORRUPT", "Instance filename and identity differ.")
        return record

    @staticmethod
    def _public(record, *, status="REGISTERED_READ_ONLY"):
        body = record["body"]
        return {
            "instance_id": body["instance_id"],
            "game_id": body["game_id"],
            "manager_id": body["manager_id"],
            "adapter": body["adapter"],
            "platform": body["platform"],
            "store": body["store"],
            "build": body["build"],
            "profile": body["profile"],
            "definition_revision": body["definition_revision"],
            "support_revision": body["support_revision"],
            "instance_revision": record["revision"],
            "status": status,
            "selected_by_local_operator": True,
            "path_included": False,
            "writes_game_files": False,
            "runtime_verified": False,
        }

    def list_public(self, game_id=None, limit=50):
        require(type(limit) is int and 1 <= limit <= MAX_INSTANCES,
                "INVALID_ARGUMENTS", "Instance result limit must be 1–64.")
        if game_id is not None:
            game_id = slug(game_id)
        rows = []
        for path in self._paths():
            try:
                record = self._read_path(path)
                if game_id is None or record["body"]["game_id"] == game_id:
                    rows.append(self._public(record))
            except (ModError, OSError, ValueError, KeyError):
                if game_id is None:
                    rows.append({
                        "instance_id": path.stem,
                        "status": "INCOMPLETE_OR_CORRUPT",
                        "path_included": False,
                        "writes_game_files": False,
                        "runtime_verified": False,
                    })
            if len(rows) >= limit:
                break
        return {
            "instances": rows,
            "count": len(rows),
            "truncated": len(rows) == limit and len(self._paths()) > limit,
            "registration": "LOCAL_OPERATOR_ONLY",
            "accepted_adapter": "umm",
            "paths_included": False,
            "writes_game_files": False,
        }

    def public(self, instance_id):
        return self._public(self._read(instance_id))

    def register_local(self, *, instance_id, game_id, game_dir, store="unknown",
                       build="unknown", profile=None, confirmed=False):
        """Register metadata after an explicit local selection and read-only probe."""
        require(confirmed, "LOCAL_APPROVAL_REQUIRED",
                "Registering an installation identity requires explicit local confirmation.")
        instance_id = slug(instance_id); game_id = slug(game_id)
        require(store in _STORES, "INSTANCE_SCHEMA", "Choose a supported store label.")
        build = _text(build, "build"); profile = _text(profile, "profile", optional=True)
        definition, support_revision = self._definition(game_id)
        root = no_links(Path(game_dir).expanduser().absolute())
        require(root.is_dir(), "GAME_MISSING", "Choose the exact existing game directory.")
        observation = inspect_game(root, definition)
        body_common = {
            "instance_id": instance_id,
            "game_id": game_id,
            "manager_id": definition["manager_id"],
            "adapter": definition["adapter"],
            "platform": definition["platform"],
            "store": store,
            "build": build,
            "profile": profile,
            "definition_revision": object_hash(definition),
            "support_revision": support_revision,
            "game_dir": str(root),
        }
        with local_lock(self.root, ".game-instance-registry.lock"):
            target = contained(self.root, instance_id + ".json")
            if target.exists():
                current = self._read_path(target)
                comparable_keys = set(body_common) - {"game_dir"}
                comparable = {key: current["body"][key] for key in comparable_keys}
                expected = {key: body_common[key] for key in comparable_keys}
                existing_root = no_links(Path(current["body"]["game_dir"]))
                require(comparable == expected and _same_path(existing_root, root),
                        "INSTANCE_CONFLICT",
                        "This instance ID already describes another reviewed installation.")
                return {
                    "instance": self._public(current, status="ALREADY_REGISTERED_READ_ONLY"),
                    "inventory_summary": {
                        "inventory_status": observation.get("inventory_status"),
                        "mods_observed": len(observation.get("mods", [])),
                        "complete": observation.get("complete") is True,
                        "runtime": "NOT_VERIFIED",
                    },
                    "metadata_written": False,
                    "game_files_written": False,
                }
            require(len(self._paths()) < MAX_INSTANCES, "RECORD_LIMIT",
                    "At most 64 local game instances are retained.")
            for path in self._paths():
                current = self._read_path(path)
                existing_root = no_links(Path(current["body"]["game_dir"]))
                require(not _same_path(existing_root, root),
                        "INSTANCE_PATH_OWNED",
                        "This game directory already belongs to another registered instance.")
            body = {**body_common, "nonce": uuid.uuid4().hex}
            record = {
                "schema_version": SCHEMA_VERSION,
                "kind": "game-instance",
                "body": body,
                "revision": object_hash(body),
            }
            json_new(target, record)
            verified = self._read_path(target)
        return {
            "instance": self._public(verified),
            "inventory_summary": {
                "inventory_status": observation.get("inventory_status"),
                "mods_observed": len(observation.get("mods", [])),
                "complete": observation.get("complete") is True,
                "runtime": "NOT_VERIFIED",
            },
            "metadata_written": True,
            "game_files_written": False,
        }

    def inspect(self, instance_id):
        record = self._read(instance_id)
        body = record["body"]
        definition, support_revision = self._definition(body["game_id"])
        require(object_hash(definition) == body["definition_revision"] and
                support_revision == body["support_revision"],
                "INSTANCE_STALE",
                "The support definition changed after instance registration; review it locally.")
        observation = inspect_game(Path(body["game_dir"]), definition)
        return {
            "instance": self._public(record),
            "inventory": observation,
            "observation_revision": object_hash(observation),
            "adapter_contract": {
                "adapter": "umm",
                "version": 1,
                "reads": ["executable_markers", "loader_markers", "Mods/Info.json", "declared_assemblies"],
                "writes": [],
                "manager_profile_read": False,
                "runtime_verified": False,
            },
            "paths_included": False,
            "game_files_written": False,
        }

    def compare(self, instance_id, operation_plan):
        inspected = self.inspect(instance_id)
        comparison = compare_installed(operation_plan, inspected["inventory"])
        return {
            **inspected,
            "comparison": comparison,
            "comparison_revision": object_hash(comparison),
            "comparison_boundary": "planned items versus observed UMM manifests; not enabled state or runtime",
        }
