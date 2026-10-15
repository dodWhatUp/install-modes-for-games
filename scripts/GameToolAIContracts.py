"""Versioned, path-free contracts for the Game Tools AI foundation.

This module contains no transport, filesystem mutation, game control, network
access, or approval path.  It normalizes results for modern clients while the
legacy MCP adapter keeps its historical payloads byte-for-byte compatible.
"""
from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
import re
from typing import Any

VERSION = "0.28.0-preview.1"
SCHEMA_VERSION = 1
CURSOR_VERSION = 1
MAX_CURSOR_BYTES = 16 * 1024

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,191}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_RESULT_TYPES = {"read", "preview", "proposal", "receipt", "blocked"}
_EVIDENCE_LEVELS = {"tested", "observed", "reported", "documented", "unknown"}
_COMPLETION_STATES = {
    "not_started", "prepared", "partially_verified", "verified", "blocked",
    "not_applicable", "unknown",
}
_COMPLETION_FIELDS = (
    "source", "tests", "package", "installation", "connection", "execution",
    "runtime", "gameplay", "publication",
)


def canonical_bytes(value: Any) -> bytes:
    """Return deterministic strict JSON bytes for a bounded public value."""
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def stable_revision(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def completion_matrix(**overrides: str) -> dict[str, str]:
    unknown = set(overrides) - set(_COMPLETION_FIELDS)
    if unknown:
        raise ValueError("Unknown completion field.")
    result = {field: "unknown" for field in _COMPLETION_FIELDS}
    for field, state in overrides.items():
        if state not in _COMPLETION_STATES:
            raise ValueError("Unknown completion state.")
        result[field] = state
    return result


def _safe_id(value: Any, *, optional: bool = True) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError("Invalid public identifier.")
    return value


def normalize_scope(scope: dict[str, Any] | None = None) -> dict[str, str]:
    scope = {} if scope is None else scope
    if not isinstance(scope, dict) or set(scope) - {"game_id", "instance_id", "plan_id", "request_id"}:
        raise ValueError("Invalid result scope.")
    result: dict[str, str] = {}
    for key, value in scope.items():
        parsed = _safe_id(value)
        if parsed is not None:
            result[key] = parsed
    return result


def result_envelope(
    *,
    result_type: str,
    status: str,
    data: Any = None,
    scope: dict[str, Any] | None = None,
    revision: str | None = None,
    freshness: dict[str, Any] | None = None,
    completion: dict[str, str] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    effects: dict[str, Any] | None = None,
    next_safe_actions: list[str] | None = None,
    retry: dict[str, Any] | None = None,
    privacy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the additive result envelope used by modern tools.

    ``data`` may contain the existing domain payload.  Historical records are
    adapted on read and are never rewritten by this function.
    """
    if result_type not in _RESULT_TYPES:
        raise ValueError("Invalid result type.")
    status = _safe_id(status, optional=False)
    if revision is None:
        revision = stable_revision(data)
    if not isinstance(revision, str) or not _SHA.fullmatch(revision):
        raise ValueError("Invalid result revision.")
    complete = completion_matrix() if completion is None else deepcopy(completion)
    if set(complete) != set(_COMPLETION_FIELDS) or any(
        state not in _COMPLETION_STATES for state in complete.values()
    ):
        raise ValueError("Invalid completion matrix.")
    facts = [] if evidence is None else deepcopy(evidence)
    if not isinstance(facts, list) or len(facts) > 128:
        raise ValueError("Evidence list is outside its bound.")
    for fact in facts:
        if not isinstance(fact, dict) or set(fact) != {"id", "level", "revision"}:
            raise ValueError("Invalid evidence record.")
        _safe_id(fact["id"], optional=False)
        if fact["level"] not in _EVIDENCE_LEVELS or not isinstance(fact["revision"], str) or not _SHA.fullmatch(fact["revision"]):
            raise ValueError("Invalid evidence fields.")
    actions = [] if next_safe_actions is None else list(next_safe_actions)
    if len(actions) > 32 or any(not isinstance(item, str) or not item or len(item) > 512 for item in actions):
        raise ValueError("Invalid next action list.")
    effect_value = {
        "read": [], "write": [], "network": False, "unknown": False,
    } if effects is None else deepcopy(effects)
    if not isinstance(effect_value, dict) or set(effect_value) != {"read", "write", "network", "unknown"}:
        raise ValueError("Invalid effects object.")
    if not isinstance(effect_value["read"], list) or not isinstance(effect_value["write"], list) or \
            len(effect_value["read"]) > 64 or len(effect_value["write"]) > 64 or \
            any(not isinstance(item, str) or not item or len(item) > 256 for item in effect_value["read"] + effect_value["write"]) or \
            type(effect_value["network"]) is not bool or type(effect_value["unknown"]) is not bool:
        raise ValueError("Invalid effects fields.")
    retry_value = {"allowed": False, "inspect_handle": None} if retry is None else deepcopy(retry)
    if not isinstance(retry_value, dict) or set(retry_value) != {"allowed", "inspect_handle"} or \
            type(retry_value["allowed"]) is not bool:
        raise ValueError("Invalid retry contract.")
    if retry_value["inspect_handle"] is not None:
        _safe_id(retry_value["inspect_handle"], optional=False)
    privacy_value = {
        "paths_included": False,
        "credentials_included": False,
        "raw_logs_included": False,
        "source_relative_references_only": True,
    } if privacy is None else deepcopy(privacy)
    required_privacy = {
        "paths_included", "credentials_included", "raw_logs_included",
        "source_relative_references_only",
    }
    if not isinstance(privacy_value, dict) or set(privacy_value) != required_privacy or \
            any(type(value) is not bool for value in privacy_value.values()):
        raise ValueError("Invalid privacy contract.")
    fresh = {} if freshness is None else deepcopy(freshness)
    if not isinstance(fresh, dict) or len(fresh) > 16:
        raise ValueError("Invalid freshness object.")
    return {
        "schema_version": SCHEMA_VERSION,
        "result_type": result_type,
        "status": status,
        "scope": normalize_scope(scope),
        "revision": revision,
        "freshness": fresh,
        "completion": complete,
        "evidence": facts,
        "effects": effect_value,
        "data": deepcopy(data),
        "next_safe_actions": actions,
        "retry": retry_value,
        "privacy": privacy_value,
    }


_BLOCKERS = {
    "INVALID_ARGUMENTS": {
        "meaning": "The request does not match the reviewed bounded schema.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_explain_blocker",
        "user_action": "Correct only the named missing or invalid field.",
    },
    "CAPABILITY_UNAVAILABLE": {
        "meaning": "The selected endpoint does not expose that capability.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Choose a listed capability or the correct game scope.",
    },
    "SOURCE_CHANGED": {
        "meaning": "A source revision changed after the reviewed operation was prepared.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_changes",
        "user_action": "Review the current revision and prepare a fresh preview.",
    },
    "CONCURRENT_CHANGE": {
        "meaning": "Another writer changed the selected record or profile.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Refresh the exact record and reconcile the competing change.",
    },
    "RECONCILIATION_REQUIRED": {
        "meaning": "The prior operation may no longer match current state.",
        "effects_known": False, "retry": False,
        "inspection_tool": "game_tools_status_batch",
        "user_action": "Inspect the same handle; do not submit a duplicate operation.",
    },
    "UNKNOWN_EFFECTS_RECONCILE": {
        "meaning": "The operation ended without proof of whether its effects occurred.",
        "effects_known": False, "retry": False,
        "inspection_tool": "game_tools_status_batch",
        "user_action": "Inspect the same transaction and read back current state before any retry.",
    },
    "REQUESTS_DISABLED": {
        "meaning": "This client connection exposes read-only tools.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Use a locally configured proposal-enabled connection; approval remains local.",
    },
    "AWAITING_LOCAL_APPROVAL": {
        "meaning": "A proposal exists but has not been approved or executed.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status_batch",
        "user_action": "Review the exact request in the local Game Tools interface.",
    },
    "EXPIRED": {
        "meaning": "The proposal expired before local approval.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status_batch",
        "user_action": "Prepare a new preview against the current source revision.",
    },
    "UNKNOWN_GAME": {
        "meaning": "The requested game scope is not registered in this workspace.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Select one registered game or validate a data-only support draft.",
    },
    "RECIPE_REQUIRED": {
        "meaning": "No reviewed mod recipe owns this game scope.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_search",
        "user_action": "Create and locally review a data-only recipe before planning mod operations.",
    },
    "MOD_RECIPE_REQUIRED": {
        "meaning": "Keybind data exists, but no reviewed mod recipe is registered.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Continue with keybind tools or add a separately reviewed mod recipe.",
    },
    "INSTANCE_REQUIRED": {
        "meaning": "This read requires one exact locally registered game installation.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instances",
        "user_action": "Select an existing opaque instance or register one locally; AI cannot supply a path.",
    },
    "INSTANCE_NOT_FOUND": {
        "meaning": "The requested opaque installation identity is not registered.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instances",
        "user_action": "Refresh the instance list and select one exact current identity.",
    },
    "INSTANCE_STALE": {
        "meaning": "The reviewed game-support definition changed after local instance registration.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instances",
        "user_action": "Review and register the current definition locally; do not reuse the stale binding.",
    },
    "INSTANCE_CORRUPT": {
        "meaning": "A private instance record failed identity, revision, or filename integrity checks.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instances",
        "user_action": "Review the local registry record; do not expose or reconstruct its private filename.",
    },
    "INSTANCE_PRIVATE_METADATA": {
        "meaning": "Installed metadata contains a path or credential candidate that is not safe for an AI result.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instances",
        "user_action": "Review the exact manifest locally and remove or separately sanitize the private value.",
    },
    "MANAGER_BINDING_REQUIRED": {
        "meaning": "This game needs an exact locally registered manager/profile binding rather than a game folder alone.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instances",
        "user_action": "Use the local register-mo2 route with the exact reviewed game, manager and profile directories.",
    },
    "MANAGER_STATE_INCOMPLETE": {
        "meaning": "One required registered manager/profile directory, marker or declaration file is missing.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instances",
        "user_action": "Review the same registered instance locally; do not discover or substitute another profile automatically.",
    },
    "INVALID_MANAGER_STATE": {
        "meaning": "The selected manager declaration file is malformed or outside the reviewed text contract.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instance_inspect",
        "user_action": "Review the exact manager-owned declaration locally and preserve its original bytes.",
    },
    "MANAGER_UNSUPPORTED": {
        "meaning": "The selected instance is not owned by a read adapter accepted for this slice.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Use an accepted UMM or MO2 instance, or complete a separate adapter acceptance.",
    },
    "ADAPTER_COMPARISON_PENDING": {
        "meaning": "Read-only inspection is accepted, but planned-versus-observed comparison is not yet accepted for this adapter.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_instance_inspect",
        "user_action": "Review the declaration state only; design and accept a separate comparison contract before calculating differences.",
    },
    "ADAPTER_ACCEPTANCE_PENDING": {
        "meaning": "The requested manager adapter has not passed this read-only slice's acceptance gate.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Use an accepted UMM or MO2 read adapter, or complete separate adapter conformance work.",
    },
    "KEYBIND_PACK_REQUIRED": {
        "meaning": "No reviewed keybind data pack owns this game scope.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Import a separately reviewed keybind pack before planning keybind work.",
    },
    "OWNERSHIP_CONFLICT": {
        "meaning": "Two declared or observed owners claim an overlapping identity or resource.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_conflicts",
        "user_action": "Resolve the listed owners explicitly; no automatic winner is selected.",
    },
    "TARGET_REQUIRED": {
        "meaning": "The operation needs one exact registered target.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Select one listed target; no target is chosen automatically.",
    },
    "GAME_MISMATCH": {
        "meaning": "The selected target belongs to another game scope.",
        "effects_known": True, "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Use the target's owning game workspace.",
    },
}


def explain_blocker(code: str, handle: str | None = None) -> dict[str, Any]:
    code = _safe_id(code, optional=False)
    item = deepcopy(_BLOCKERS.get(code, {
        "meaning": "The subsystem refused the operation without authorizing an alternate route.",
        "effects_known": False,
        "retry": False,
        "inspection_tool": "game_tools_status",
        "user_action": "Inspect the same scope and preserve the original failure evidence.",
    }))
    item["code"] = code
    item["handle"] = _safe_id(handle) if handle is not None else None
    return item


def encode_cursor(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict):
        raise ValueError("Cursor payload must be an object.")
    body = {"v": CURSOR_VERSION, **deepcopy(payload)}
    raw = canonical_bytes(body)
    if len(raw) > MAX_CURSOR_BYTES:
        raise ValueError("Cursor payload exceeds its bound.")
    token = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    seal = hashlib.sha256(raw).hexdigest()[:24]
    return f"gtc{CURSOR_VERSION}.{token}.{seal}"


def decode_cursor(cursor: str) -> dict[str, Any]:
    if not isinstance(cursor, str) or len(cursor) > MAX_CURSOR_BYTES * 2:
        raise ValueError("Invalid change cursor.")
    try:
        prefix, token, seal = cursor.split(".")
        if prefix != f"gtc{CURSOR_VERSION}" or not re.fullmatch(r"[A-Za-z0-9_-]+", token) or not re.fullmatch(r"[a-f0-9]{24}", seal):
            raise ValueError
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        if len(raw) > MAX_CURSOR_BYTES or hashlib.sha256(raw).hexdigest()[:24] != seal:
            raise ValueError
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict) or value.pop("v", None) != CURSOR_VERSION:
            raise ValueError
        return value
    except (ValueError, UnicodeError, json.JSONDecodeError, base64.binascii.Error):
        raise ValueError("Invalid or changed change cursor.") from None


def output_schema() -> dict[str, Any]:
    """JSON Schema 2020-12 shape for all modern foundation tool outputs."""
    states = sorted(_COMPLETION_STATES)
    fields = {field: {"type": "string", "enum": states} for field in _COMPLETION_FIELDS}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "schema_version", "result_type", "status", "scope", "revision",
            "freshness", "completion", "evidence", "effects", "data",
            "next_safe_actions", "retry", "privacy",
        ],
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "result_type": {"type": "string", "enum": sorted(_RESULT_TYPES)},
            "status": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"},
            "scope": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    key: {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"}
                    for key in ("game_id", "instance_id", "plan_id", "request_id")
                },
            },
            "revision": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
            "freshness": {"type": "object", "maxProperties": 16},
            "completion": {
                "type": "object", "required": list(_COMPLETION_FIELDS),
                "additionalProperties": False, "properties": fields,
            },
            "evidence": {
                "type": "array", "maxItems": 128,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["id", "level", "revision"],
                    "properties": {
                        "id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"},
                        "level": {"type": "string", "enum": sorted(_EVIDENCE_LEVELS)},
                        "revision": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                    },
                },
            },
            "effects": {
                "type": "object", "required": ["read", "write", "network", "unknown"],
                "additionalProperties": False,
                "properties": {
                    "read": {"type": "array", "maxItems": 64, "items": {"type": "string", "minLength": 1, "maxLength": 256}},
                    "write": {"type": "array", "maxItems": 64, "items": {"type": "string", "minLength": 1, "maxLength": 256}},
                    "network": {"type": "boolean"},
                    "unknown": {"type": "boolean"},
                },
            },
            "data": {},
            "next_safe_actions": {
                "type": "array", "maxItems": 32,
                "items": {"type": "string", "minLength": 1, "maxLength": 512},
            },
            "retry": {
                "type": "object", "additionalProperties": False,
                "required": ["allowed", "inspect_handle"],
                "properties": {
                    "allowed": {"type": "boolean"},
                    "inspect_handle": {
                        "oneOf": [
                            {"type": "null"},
                            {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{0,191}$"},
                        ]
                    },
                },
            },
            "privacy": {
                "type": "object", "additionalProperties": False,
                "required": [
                    "paths_included", "credentials_included", "raw_logs_included",
                    "source_relative_references_only",
                ],
                "properties": {
                    "paths_included": {"type": "boolean"},
                    "credentials_included": {"type": "boolean"},
                    "raw_logs_included": {"type": "boolean"},
                    "source_relative_references_only": {"type": "boolean"},
                },
            },
        },
    }
