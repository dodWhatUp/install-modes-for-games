"""Bounded read-only Mod Organizer 2 profile declarations.

The caller supplies one already-registered private instance record.  This module
reads only the exact profile declaration files and fixed manager markers owned by
that record.  It performs no discovery, process/API/VFS access, archive loading,
manager/game mutation, or runtime inference.
"""
from __future__ import annotations

import hashlib
import hmac
from pathlib import Path
import re
from typing import Any

from game_mod_ops.safety import canonical, ModError, no_links, regular, require

VERSION = "0.2.0"
SCHEMA_VERSION = 1
MAX_TEXT_BYTES = 2 * 1024 * 1024
MAX_LINES = 5000
MAX_PUBLIC_ROWS = 1000

# Keep this fail-closed screen aligned with the public instance boundary.  Safe
# relative identifiers and ordinary HTTPS URLs remain allowed; absolute paths,
# file URIs, environment/home expansions, credentials and secret-like values do
# not enter public output.
_PRIVATE_TEXT = (
    re.compile(r"(?i)(?<!\w)[a-z]:[\\/]+"),
    re.compile(r"(?<![\w/])/(?!/)[^\s/]+(?:/[^\s/]+)*"),
    re.compile(r"(?<![\w:])//[^/\s]+(?:/[^/\s]+)*"),
    re.compile(r"(?<![\w\\])\\\\[^\\\s]+(?:\\[^\\\s]+)*"),
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


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_stable(path: Path, *, required: bool) -> tuple[bytes | None, dict[str, Any] | None]:
    path = no_links(path)
    if not path.exists():
        require(not required, "MANAGER_STATE_INCOMPLETE", "A required MO2 profile file is missing.")
        return None, None
    path = regular(path, MAX_TEXT_BYTES)
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require(
        (before.st_ino, before.st_size, before.st_mtime_ns) ==
        (after.st_ino, after.st_size, after.st_mtime_ns) and len(raw) == before.st_size,
        "SOURCE_CHANGED", "MO2 profile data changed while reading.",
    )
    return raw, {
        "bytes": len(raw), "sha256": _sha(raw),
        "mtime_ns": before.st_mtime_ns, "ino": before.st_ino,
    }


def _presence_snapshot(path: Path) -> dict[str, Any]:
    path = no_links(path)
    if not path.exists():
        return {"present": False}
    path = regular(path)
    stat = path.stat()
    return {
        "present": True, "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns, "ino": stat.st_ino,
    }


def _decode(raw: bytes) -> str:
    require(b"\x00" not in raw[:4] or raw.startswith((b"\xff\xfe", b"\xfe\xff")),
            "INVALID_MANAGER_STATE", "Unsupported NUL-bearing manager text.")
    try:
        if raw.startswith(b"\xff\xfe"):
            text = raw.decode("utf-16-le")
        elif raw.startswith(b"\xfe\xff"):
            text = raw.decode("utf-16-be")
        else:
            text = raw.decode("utf-8-sig")
    except UnicodeError as error:
        raise ModError("INVALID_MANAGER_STATE", "MO2 profile text is not supported UTF text.") from error
    require(not any(ord(char) < 32 and char not in "\r\n\t\ufeff" for char in text),
            "INVALID_MANAGER_STATE", "MO2 profile text contains control characters.")
    return text.lstrip("\ufeff")


def _bounded_name(value: str) -> str:
    value = value.strip()
    require(0 < len(value) <= 240 and not any(ord(char) < 32 for char in value),
            "INVALID_MANAGER_STATE", "MO2 entry name is empty or outside its bound.")
    return value


def _private(value: str) -> bool:
    return any(pattern.search(value) for pattern in _PRIVATE_TEXT)


def _public_identity(kind: str, name: str, file_index: int) -> tuple[str, str, bool]:
    if _private(name):
        # Never expose a stable fingerprint derived from private text.
        return f"{kind}:redacted-{file_index:04d}", "[redacted-local-entry]", True
    token = hashlib.sha256(name.casefold().encode("utf-8")).hexdigest()[:24]
    return f"{kind}:{token}", name, False


def parse_modlist(raw: bytes) -> dict[str, Any]:
    lines = _decode(raw).splitlines()
    require(len(lines) <= MAX_LINES, "INVENTORY_LIMIT", "MO2 modlist exceeds its reviewed line limit.")
    rows: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    comments = 0
    unclassified = 0
    redacted = 0
    for file_index, source in enumerate(lines):
        line = source.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments += 1
            continue
        marker = line[0] if line[0] in "+-*" else "?"
        name = _bounded_name(line[1:] if marker != "?" else line)
        seen[name.casefold()] = seen.get(name.casefold(), 0) + 1
        state = {
            "+": "DECLARED_ENABLED",
            "-": "DECLARED_DISABLED",
            "*": "DECLARED_FOREIGN_ENABLED",
            "?": "UNCLASSIFIED",
        }[marker]
        if marker == "?":
            unclassified += 1
        token, public_name, name_redacted = _public_identity("mo2mod", name, file_index)
        redacted += int(name_redacted)
        rows.append({
            "mod_token": token,
            "name": public_name,
            "name_redacted": name_redacted,
            "source_marker": marker,
            "declared_state": state,
            "file_index": file_index,
            "runtime_loaded": "UNKNOWN",
        })
    duplicate_count = sum(1 for count in seen.values() if count > 1)
    warnings = []
    if unclassified:
        warnings.append("One or more entries had no reviewed MO2 state marker; they remain unclassified.")
    if duplicate_count:
        warnings.append("Duplicate case-insensitive mod names were observed; identity is ambiguous.")
    if redacted:
        warnings.append("One or more private-looking mod names were redacted; exact identity is unavailable publicly.")
    truncated = len(rows) > MAX_PUBLIC_ROWS
    if truncated:
        warnings.append("The public mod declaration list reached its reviewed row limit.")
    return {
        "rows": rows[:MAX_PUBLIC_ROWS],
        "total_rows": len(rows),
        "truncated": truncated,
        "comments_omitted": comments,
        "duplicate_name_count": duplicate_count,
        "redacted_name_count": redacted,
        "complete": not duplicate_count and not unclassified and not redacted and not truncated,
        "warnings": warnings,
        "order_semantics": "raw_modlist_file_order_only",
    }


def parse_plugins(raw: bytes) -> dict[str, Any]:
    lines = _decode(raw).splitlines()
    require(len(lines) <= MAX_LINES, "INVENTORY_LIMIT", "MO2 plugins list exceeds its reviewed line limit.")
    rows: list[dict[str, Any]] = []
    seen: dict[str, int] = {}
    comments = 0
    redacted = 0
    for file_index, source in enumerate(lines):
        line = source.strip()
        if not line:
            continue
        if line.startswith("#"):
            comments += 1
            continue
        enabled = line.startswith("*")
        name = _bounded_name(line[1:] if enabled else line)
        seen[name.casefold()] = seen.get(name.casefold(), 0) + 1
        token, public_name, name_redacted = _public_identity("mo2plugin", name, file_index)
        redacted += int(name_redacted)
        rows.append({
            "plugin_token": token,
            "name": public_name,
            "name_redacted": name_redacted,
            "source_marker": "*" if enabled else "",
            "declared_state": "DECLARED_ENABLED" if enabled else "DECLARED_DISABLED",
            "file_index": file_index,
            "runtime_loaded": "UNKNOWN",
        })
    duplicate_count = sum(1 for count in seen.values() if count > 1)
    truncated = len(rows) > MAX_PUBLIC_ROWS
    return {
        "present": True,
        "rows": rows[:MAX_PUBLIC_ROWS],
        "total_rows": len(rows),
        "truncated": truncated,
        "comments_omitted": comments,
        "duplicate_name_count": duplicate_count,
        "redacted_name_count": redacted,
        "complete": duplicate_count == 0 and redacted == 0 and not truncated,
        "order_semantics": "raw_plugins_file_order_only",
    }


def inspect_instance(body: dict[str, Any], instance_revision: str,
                     game_markers: list[dict[str, Any]]) -> dict[str, Any]:
    """Read one already-validated MO2 binding and return path-free declarations."""
    require(type(body) is dict and body.get("adapter") == "mo2" and
            body.get("manager_id") == "mod-organizer-2",
            "MANAGER_UNSUPPORTED", "The selected instance does not use the reviewed MO2 read adapter.")
    require(type(game_markers) is list and 1 <= len(game_markers) <= 32 and
            all(type(row) is dict and set(row) == {"relative", "bytes"} and
                type(row["relative"]) is str and type(row["bytes"]) is int and row["bytes"] >= 0
                for row in game_markers),
            "INSTANCE_CORRUPT", "Reviewed game-marker evidence is invalid.")
    binding = body.get("manager_binding")
    require(type(binding) is dict and set(binding) == {"kind", "manager_root", "profile_root"} and
            binding.get("kind") == "mo2-profile",
            "INSTANCE_CORRUPT", "The private MO2 manager binding is invalid.")
    game_root = no_links(Path(body["game_dir"]))
    manager_root = no_links(Path(binding["manager_root"]))
    profile_root = no_links(Path(binding["profile_root"]))
    require(game_root.is_dir() and manager_root.is_dir() and profile_root.is_dir(),
            "MANAGER_STATE_INCOMPLETE", "One registered MO2 root is missing or not a directory.")

    manager_markers = [manager_root / "ModOrganizer.exe", manager_root / "ModOrganizer.ini"]
    manager_marker_before = [_presence_snapshot(path) for path in manager_markers]
    require(any(item["present"] for item in manager_marker_before),
            "MANAGER_STATE_INCOMPLETE", "The registered MO2 root has no reviewed manager marker.")

    selected = {
        "modlist": (profile_root / "modlist.txt", True),
        "plugins": (profile_root / "plugins.txt", False),
    }
    presence_paths = {
        "loadorder": profile_root / "loadorder.txt",
        "manager_ini": manager_root / "ModOrganizer.ini",
    }
    raw_files: dict[str, bytes | None] = {}
    snapshots: dict[str, dict[str, Any] | None] = {}
    for role, (path, required) in selected.items():
        raw, snapshot = _read_stable(path, required=required)
        raw_files[role] = raw
        snapshots[role] = snapshot
    presence_before = {role: _presence_snapshot(path) for role, path in presence_paths.items()}

    modlist = parse_modlist(raw_files["modlist"] or b"")
    plugins = parse_plugins(raw_files["plugins"]) if raw_files["plugins"] is not None else {
        "present": False, "rows": [], "total_rows": 0, "truncated": False,
        "comments_omitted": 0, "duplicate_name_count": 0, "redacted_name_count": 0, "complete": True,
        "order_semantics": "not_observed",
    }

    # Re-read exactly the selected declaration files and recheck presence-only
    # markers.  No watcher, manager API, VFS or runtime state is implied.
    for role, (path, required) in selected.items():
        raw, snapshot = _read_stable(path, required=required)
        require(raw == raw_files[role] and snapshot == snapshots[role],
                "SOURCE_CHANGED", "MO2 profile data changed during inspection.")
    presence_after = {role: _presence_snapshot(path) for role, path in presence_paths.items()}
    manager_marker_after = [_presence_snapshot(path) for path in manager_markers]
    require(presence_after == presence_before and manager_marker_after == manager_marker_before,
            "SOURCE_CHANGED", "MO2 profile or manager marker state changed during inspection.")

    source_files = []
    relative_names = {"modlist": "profile/modlist.txt", "plugins": "profile/plugins.txt"}
    redacted_by_role = {
        "modlist": modlist["redacted_name_count"] > 0,
        "plugins": plugins["redacted_name_count"] > 0,
    }
    for role, snapshot in snapshots.items():
        if snapshot is not None:
            expose_raw_hash = not redacted_by_role[role]
            source_files.append({
                "role": role,
                "relative_name": relative_names[role],
                "bytes": snapshot["bytes"],
                "sha256": snapshot["sha256"] if expose_raw_hash else None,
                "raw_hash_exposed": expose_raw_hash,
            })

    warnings = list(modlist["warnings"])
    if not plugins["complete"]:
        warnings.append("Plugin declarations are partial, redacted or ambiguous.")
    public = {
        "schema_version": SCHEMA_VERSION,
        "kind": "mo2_registered_profile_state",
        "instance_id": body["instance_id"],
        "game_id": body["game_id"],
        "manager_id": "mod-organizer-2",
        "profile": body["profile"],
        "instance_revision": instance_revision,
        "game_markers": game_markers,
        "source_files": source_files,
        "mods": modlist,
        "plugins": plugins,
        "loadorder_file_present": presence_before["loadorder"]["present"],
        "manager_ini_present": presence_before["manager_ini"]["present"],
        "complete": modlist["complete"] and plugins["complete"],
        "warnings": warnings,
        "evidence": "registered_exact_files_read_only",
        "virtual_deployment": "NOT_READ",
        "manager_process": "NOT_READ",
        "runtime": "NOT_VERIFIED",
        "gameplay": "NOT_VERIFIED",
        "paths_included": False,
        "automatic_discovery": False,
        "writes_manager_or_game": False,
    }
    private_revision_material = {
        "public": public,
        "raw_source_sha256": {
            role: snapshot["sha256"] if snapshot is not None else None
            for role, snapshot in snapshots.items()
        },
        "manager_marker_snapshot": manager_marker_before,
        "presence_snapshot": presence_before,
    }
    public["state_revision"] = hmac.new(
        bytes.fromhex(body["nonce"]), canonical(private_revision_material), hashlib.sha256,
    ).hexdigest()
    return public
