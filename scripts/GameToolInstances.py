"""Private game-installation identities and bounded read-only adapters.

Registration is an explicit local operator action.  Modern AI tools may list or
inspect only an already registered opaque instance ID; they never receive or
supply a filesystem path.  This module writes registry metadata only and never
writes a game, manager profile, loader, mod, save, input profile, or setting.
Legacy UMM records remain readable; MO2 uses an additive version-2 private
binding inside the same registry owner rather than a competing registry.
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

VERSION = "0.2.0"
SCHEMA_VERSION = 2
LEGACY_SCHEMA_VERSION = 1
MAX_INSTANCES = 64
MAX_RECORD_BYTES = 64 * 1024
MAX_PUBLIC_VALUES = 4096
_ACCEPTED_ADAPTERS = {"umm", "mo2"}
_STORES = {"steam", "gog", "epic", "microsoft", "other", "unknown"}
_BASE_BODY_FIELDS = {
    "instance_id", "game_id", "manager_id", "adapter", "platform",
    "store", "build", "profile", "definition_revision",
    "support_revision", "game_dir", "nonce",
}
_MANAGER_BINDING_FIELDS = {"kind", "manager_root", "profile_root"}
_SHORT = re.compile(r"[^\x00-\x1f\x7f]{1,120}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_PRIVATE_METADATA = (
    # Absolute paths may be embedded after punctuation, not just whitespace.
    # The negative boundaries avoid treating ordinary URL path segments or
    # relative identifiers such as ``Mods/Foo`` as local filesystem paths.
    re.compile(r"(?i)(?<!\w)[a-z]:[\\/]+"),
    re.compile(r"(?<![\w/])/(?!/)[^\s/]+(?:/[^\s/]+)*"),
    re.compile(r"(?<![\w:])//[^/\s]+(?:/[^/\s]+)*"),
    re.compile(r"(?<!\w)\\\\[^\\\s]+(?:\\[^\\\s]+)*"),
    re.compile(r"(?<![\w\\])\\(?!\\)[^\\\s]+(?:\\[^\\\s]+)*"),
    re.compile(r"(?i)(?<!\w)file:(?:/{2,3}|\\\\)"),
    re.compile(r"(?<!\w)~[A-Za-z0-9._-]*[\\/]"),
    re.compile(r"(?i)(?<!\w)(?:%[A-Z_][A-Z0-9_]*%|\$[A-Z_][A-Z0-9_]*|\$\{[A-Z_][A-Z0-9_]*\})[\\/]"),
    re.compile(r"(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@"),
    re.compile(r"(?i)\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{25,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
)


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


def _assert_public_metadata(value, depth=0):
    """Fail closed before arbitrary manifest text reaches a public AI result."""
    require(depth <= 16, "INSTANCE_PRIVATE_METADATA",
            "Installed metadata exceeded the public result depth limit.")
    if value is None or type(value) in (bool, int, float):
        return
    if type(value) is str:
        require(len(value) <= 4096 and not any(ord(char) < 32 for char in value),
                "INSTANCE_PRIVATE_METADATA",
                "Installed metadata contains unsupported private text.")
        require(not any(pattern.search(value) for pattern in _PRIVATE_METADATA),
                "INSTANCE_PRIVATE_METADATA",
                "Installed metadata contains a path or credential candidate; review it locally.")
        return
    if type(value) is list:
        require(len(value) <= MAX_PUBLIC_VALUES,
                "INSTANCE_PRIVATE_METADATA", "Installed metadata exceeds its public list bound.")
        for item in value:
            _assert_public_metadata(item, depth + 1)
        return
    if type(value) is dict:
        require(len(value) <= 512 and all(type(key) is str and len(key) <= 120 for key in value),
                "INSTANCE_PRIVATE_METADATA", "Installed metadata has unsupported public fields.")
        for key, item in value.items():
            _assert_public_metadata(key, depth + 1)
            _assert_public_metadata(item, depth + 1)
        return
    raise ModError("INSTANCE_PRIVATE_METADATA",
                   "Installed metadata contains an unsupported public value type.")


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
        self._read_adapter(definition)
        return definition, support_revision

    def adapter_for_game(self, game_id):
        definition, _ = self._definition(game_id)
        return self._read_adapter(definition)

    @staticmethod
    def _read_adapter(definition):
        if definition.get("adapter") == "umm":
            return "umm"
        if definition.get("adapter") == "external" and definition.get("manager_id") == "mod-organizer-2":
            return "mo2"
        raise ModError("ADAPTER_ACCEPTANCE_PENDING",
                       "This game has no separately accepted installed-state read adapter.")

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
        schema_version = value["schema_version"]
        require(schema_version in {LEGACY_SCHEMA_VERSION, SCHEMA_VERSION} and value["kind"] == "game-instance",
                "INSTANCE_CORRUPT", "Unsupported game-instance record.")
        body = value["body"]
        expected_fields = (
            _BASE_BODY_FIELDS if schema_version == LEGACY_SCHEMA_VERSION else
            _BASE_BODY_FIELDS | {"manager_binding"}
        )
        require(type(body) is dict and set(body) == expected_fields,
                "INSTANCE_CORRUPT", "Unexpected game-instance body fields.")
        slug(body["instance_id"]); slug(body["game_id"]); slug(body["manager_id"])
        require(body["adapter"] in _ACCEPTED_ADAPTERS and body["platform"] in {"windows", "linux", "macos"},
                "INSTANCE_CORRUPT", "Instance adapter or platform is unsupported.")
        if schema_version == LEGACY_SCHEMA_VERSION:
            require(body["adapter"] == "umm",
                    "INSTANCE_CORRUPT", "Legacy instance records are accepted only for the UMM adapter.")
        else:
            require(body["adapter"] == "mo2" and body["manager_id"] == "mod-organizer-2",
                    "INSTANCE_CORRUPT", "Version-2 instance records require the reviewed MO2 binding.")
            binding = body["manager_binding"]
            require(type(binding) is dict and set(binding) == _MANAGER_BINDING_FIELDS and
                    binding.get("kind") == "mo2-profile",
                    "INSTANCE_CORRUPT", "The private MO2 manager binding is invalid.")
            require(all(type(binding[key]) is str and os.path.isabs(binding[key])
                        for key in ("manager_root", "profile_root")),
                    "INSTANCE_CORRUPT", "Private MO2 roots must be absolute paths.")
        require(body["store"] in _STORES, "INSTANCE_CORRUPT", "Instance store is unsupported.")
        _text(body["build"], "build")
        _text(body["profile"], "profile", optional=body["adapter"] != "mo2")
        require(type(body["definition_revision"]) is str and bool(_SHA.fullmatch(body["definition_revision"])),
                "INSTANCE_CORRUPT", "Definition revision is invalid.")
        require(body["support_revision"] is None or
                (type(body["support_revision"]) is str and bool(_SHA.fullmatch(body["support_revision"]))),
                "INSTANCE_CORRUPT", "Support revision is invalid.")
        require(type(body["game_dir"]) is str and os.path.isabs(body["game_dir"]),
                "INSTANCE_CORRUPT", "Private game directory is invalid.")
        require(type(body["nonce"]) is str and bool(re.fullmatch(r"[a-f0-9]{32}", body["nonce"])),
                "INSTANCE_CORRUPT", "Instance nonce is invalid.")
        require(value["revision"] == object_hash(body),
                "INSTANCE_CORRUPT", "Game-instance record changed after registration.")
        return value

    def _read_path(self, path: Path):
        record = self._validate_record(read_json(path, MAX_RECORD_BYTES))
        try:
            expected = slug(path.stem)
        except ModError:
            raise ModError("INSTANCE_CORRUPT", "Instance filename is not a valid opaque identity.") from None
        require(record["body"]["instance_id"] == expected,
                "INSTANCE_CORRUPT", "Instance filename and identity differ.")
        return record

    def _read(self, instance_id):
        instance_id = slug(instance_id)
        path = contained(self.root, instance_id + ".json")
        require(path.is_file(), "INSTANCE_NOT_FOUND", "Registered game instance was not found.")
        return self._read_path(path)

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
            "manager_profile_registered": body["adapter"] == "mo2",
            "record_schema_version": record["schema_version"],
        }

    def list_public(self, game_id=None, limit=50):
        require(type(limit) is int and 1 <= limit <= MAX_INSTANCES,
                "INVALID_ARGUMENTS", "Instance result limit must be 1–64.")
        if game_id is not None:
            game_id = slug(game_id)
        rows = []
        matched = 0
        paths = self._paths()
        for position, path in enumerate(paths, start=1):
            public = None
            try:
                record = self._read_path(path)
                if game_id is None or record["body"]["game_id"] == game_id:
                    public = self._public(record)
            except (ModError, OSError, ValueError, KeyError):
                if game_id is None:
                    public = {
                        "instance_id": f"corrupt-record-{position:03d}",
                        "status": "INCOMPLETE_OR_CORRUPT",
                        "path_included": False,
                        "writes_game_files": False,
                        "runtime_verified": False,
                    }
            if public is not None:
                matched += 1
                if len(rows) < limit:
                    rows.append(public)
        return {
            "instances": rows,
            "count": len(rows),
            "truncated": matched > len(rows),
            "registration": "LOCAL_OPERATOR_ONLY",
            "accepted_adapter": "umm",
            "accepted_adapters": ["umm", "mo2"],
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
        require(self._read_adapter(definition) == "umm",
                "MANAGER_BINDING_REQUIRED",
                "This game requires the separate local register-mo2 route with exact manager and profile roots.")
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
                "schema_version": LEGACY_SCHEMA_VERSION,
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

    def register_mo2_local(self, *, instance_id, game_id, game_dir, manager_root,
                           profile_root, profile, store="unknown", build="unknown",
                           confirmed=False):
        """Register one exact MO2 profile binding after explicit local confirmation."""
        require(confirmed, "LOCAL_APPROVAL_REQUIRED",
                "Registering an MO2 profile identity requires explicit local confirmation.")
        instance_id = slug(instance_id); game_id = slug(game_id)
        require(store in _STORES, "INSTANCE_SCHEMA", "Choose a supported store label.")
        build = _text(build, "build"); profile = _text(profile, "profile")
        definition, support_revision = self._definition(game_id)
        require(self._read_adapter(definition) == "mo2",
                "MANAGER_UNSUPPORTED", "The selected game is not owned by the reviewed MO2 read adapter.")
        game = no_links(Path(game_dir).expanduser().absolute())
        manager = no_links(Path(manager_root).expanduser().absolute())
        profile_path = no_links(Path(profile_root).expanduser().absolute())
        require(game.is_dir(), "GAME_MISSING", "Choose the exact existing game directory.")
        require(manager.is_dir() and profile_path.is_dir(),
                "MANAGER_STATE_INCOMPLETE", "Choose exact existing MO2 manager and profile directories.")
        # Validate the reviewed game marker before binding a manager profile.
        game_before = inspect_game(game, definition)["game_markers"]
        body_common = {
            "instance_id": instance_id,
            "game_id": game_id,
            "manager_id": definition["manager_id"],
            "adapter": "mo2",
            "platform": definition["platform"],
            "store": store,
            "build": build,
            "profile": profile,
            "definition_revision": object_hash(definition),
            "support_revision": support_revision,
            "game_dir": str(game),
            "manager_binding": {
                "kind": "mo2-profile",
                "manager_root": str(manager),
                "profile_root": str(profile_path),
            },
        }
        from GameToolMO2Read import inspect_instance as inspect_mo2
        with local_lock(self.root, ".game-instance-registry.lock"):
            target = contained(self.root, instance_id + ".json")
            if target.exists():
                current = self._read_path(target)
                current_body = current["body"]
                require(current["schema_version"] == SCHEMA_VERSION and
                        current_body.get("adapter") == "mo2" and
                        type(current_body.get("manager_binding")) is dict,
                        "INSTANCE_CONFLICT",
                        "This instance ID already belongs to another reviewed adapter or record version.")
                scalar_keys = set(body_common) - {"game_dir", "manager_binding"}
                comparable = {key: current_body.get(key) for key in scalar_keys}
                expected = {key: body_common[key] for key in scalar_keys}
                current_binding = current_body["manager_binding"]
                same_roots = (
                    _same_path(Path(current_body["game_dir"]), game) and
                    _same_path(Path(current_binding["manager_root"]), manager) and
                    _same_path(Path(current_binding["profile_root"]), profile_path)
                )
                require(comparable == expected and same_roots,
                        "INSTANCE_CONFLICT",
                        "This instance ID already describes another reviewed installation or profile.")
                observation = inspect_mo2(current_body, current["revision"], game_before)
                require(inspect_game(game, definition)["game_markers"] == game_before,
                        "SOURCE_CHANGED", "Game marker changed during MO2 inspection.")
                return {
                    "instance": self._public(current, status="ALREADY_REGISTERED_READ_ONLY"),
                    "inventory_summary": {
                        "declared_mods": observation["mods"]["total_rows"],
                        "declared_plugins": observation["plugins"]["total_rows"],
                        "complete": observation["complete"],
                        "runtime": "NOT_VERIFIED",
                    },
                    "metadata_written": False,
                    "manager_files_written": False,
                    "game_files_written": False,
                }
            require(len(self._paths()) < MAX_INSTANCES, "RECORD_LIMIT",
                    "At most 64 local game instances are retained.")
            for path in self._paths():
                current = self._read_path(path)
                current_body = current["body"]
                if current_body["adapter"] == "mo2":
                    binding = current_body["manager_binding"]
                    require(not _same_path(Path(binding["profile_root"]), profile_path),
                            "INSTANCE_PATH_OWNED",
                            "This MO2 profile directory already belongs to another registered instance.")
                else:
                    require(not _same_path(Path(current_body["game_dir"]), game),
                            "INSTANCE_PATH_OWNED",
                            "This game directory already belongs to another non-MO2 registered instance.")
            body = {**body_common, "nonce": uuid.uuid4().hex}
            record = {
                "schema_version": SCHEMA_VERSION,
                "kind": "game-instance",
                "body": body,
                "revision": object_hash(body),
            }
            # Inspect before committing metadata; a failed or private read leaves no record.
            observation = inspect_mo2(body, record["revision"], game_before)
            require(inspect_game(game, definition)["game_markers"] == game_before,
                    "SOURCE_CHANGED", "Game marker changed during MO2 inspection.")
            _assert_public_metadata(observation)
            json_new(target, record)
            verified = self._read_path(target)
        return {
            "instance": self._public(verified),
            "inventory_summary": {
                "declared_mods": observation["mods"]["total_rows"],
                "declared_plugins": observation["plugins"]["total_rows"],
                "complete": observation["complete"],
                "runtime": "NOT_VERIFIED",
            },
            "metadata_written": True,
            "manager_files_written": False,
            "game_files_written": False,
        }

    def inspect(self, instance_id):
        record = self._read(instance_id)
        body = record["body"]
        definition, support_revision = self._definition(body["game_id"])
        read_adapter = self._read_adapter(definition)
        require(read_adapter == body["adapter"] and
                object_hash(definition) == body["definition_revision"] and
                support_revision == body["support_revision"],
                "INSTANCE_STALE",
                "The support definition or accepted read adapter changed after registration; review it locally.")
        if read_adapter == "umm":
            observation = inspect_game(Path(body["game_dir"]), definition)
            contract = {
                "adapter": "umm",
                "version": 1,
                "reads": ["executable_markers", "loader_markers", "Mods/Info.json", "declared_assemblies"],
                "writes": [],
                "manager_profile_read": False,
                "runtime_verified": False,
            }
        else:
            from GameToolMO2Read import inspect_instance as inspect_mo2
            game_before = inspect_game(Path(body["game_dir"]), definition)["game_markers"]
            observation = inspect_mo2(body, record["revision"], game_before)
            require(inspect_game(Path(body["game_dir"]), definition)["game_markers"] == game_before,
                    "SOURCE_CHANGED", "Game marker changed during MO2 inspection.")
            contract = {
                "adapter": "mo2",
                "version": 1,
                "reads": [
                    "registered_game_marker", "profile/modlist.txt", "profile/plugins.txt",
                    "loadorder_presence", "manager_marker_presence",
                ],
                "writes": [],
                "manager_profile_read": True,
                "runtime_verified": False,
            }
        _assert_public_metadata(observation)
        observation_revision = observation.get("state_revision") or object_hash(observation)
        return {
            "instance": self._public(record),
            "inventory": observation,
            "observation_revision": observation_revision,
            "adapter_contract": contract,
            "paths_included": False,
            "manager_files_written": False,
            "game_files_written": False,
        }

    def compare(self, instance_id, operation_plan):
        record = self._read(instance_id)
        require(record["body"]["adapter"] == "umm",
                "ADAPTER_COMPARISON_PENDING",
                "Planned-versus-observed comparison is not accepted for this read adapter.")
        inspected = self.inspect(instance_id)
        comparison = compare_installed(operation_plan, inspected["inventory"])
        return {
            **inspected,
            "comparison": comparison,
            "comparison_revision": object_hash(comparison),
            "comparison_boundary": "planned items versus observed UMM manifests; not enabled state or runtime",
        }
