"""Bounded additive projection contracts, distinct from native runtime formats."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import math
import re

from GameToolAIContracts import stable_revision

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 256
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,191}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
STAGES = ("received", "verified", "staged", "adopted", "indexed", "context_exposed")
OBSERVATIONS = {"declared", "reported_loaded", "observed_execution", "unknown"}
NODE_KINDS = {"component", "instruction", "preference", "skill", "tool", "automation"}


class ContextError(ValueError):
    pass


def require(test, message):
    if not test:
        raise ContextError(message)


def _bounded(value, depth=0, budget=None):
    budget = [30000] if budget is None else budget
    budget[0] -= 1
    require(depth <= 12 and budget[0] >= 0, "Context structure exceeds its bound.")
    if isinstance(value, dict):
        for k, v in value.items():
            require(type(k) is str and len(k) <= 200, "Invalid context key.")
            _bounded(v, depth + 1, budget)
    elif isinstance(value, list):
        require(len(value) <= 4096, "Context collection exceeds its bound.")
        for v in value:
            _bounded(v, depth + 1, budget)
    elif isinstance(value, str):
        require(len(value) <= 131072 and "\x00" not in value, "Context text exceeds its bound.")
    else:
        require(value is None or type(value) in (bool, int, float), "Unsupported context value.")
        require(not isinstance(value, float) or math.isfinite(value), "Nonfinite context value.")


def _pairs(items):
    out = {}
    for k, v in items:
        require(k not in out, "Duplicate JSON key.")
        out[k] = v
    return out


def decode(raw):
    require(isinstance(raw, bytes) and len(raw) <= MAX_BYTES, "Context exceeds its byte bound.")
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: require(False, "Nonfinite JSON value."))
        return validate_context(value)
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise ContextError("Context is not bounded UTF-8 JSON.") from None


def identifier(value):
    require(type(value) is str and bool(ID.fullmatch(value)), "Invalid stable identifier.")
    return value


def timestamp(value):
    require(type(value) is str and len(value) <= 40, "Missing timestamp.")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(dt.tzinfo is not None, "Timestamp needs a timezone.")
        return dt.astimezone(timezone.utc)
    except ValueError:
        raise ContextError("Invalid timestamp.") from None


def _rows(doc, key):
    rows = doc.get(key, [])
    require(type(rows) is list and len(rows) <= MAX_ROWS, "Invalid " + key + " collection.")
    ids = set()
    for row in rows:
        require(type(row) is dict, "Invalid " + key + " record.")
        ident = identifier(row.get("id"))
        require(ident not in ids, "Duplicate " + key + " identity.")
        ids.add(ident)
    return rows


def validate_context(value):
    _bounded(value)
    require(type(value) is dict and value.get("schema_version") == 1 and
            type(value.get("schema_version")) is int and value.get("kind") == "GameToolsSystemContext",
            "Unsupported context format; preserve the original for a reviewed adapter.")
    require(len(json.dumps(value, ensure_ascii=True, allow_nan=False).encode()) <= MAX_BYTES,
            "Decoded context exceeds its byte bound.")
    identifier(value.get("scope"))
    sources = {r["id"]: r for r in _rows(value, "sources")}
    for row in sources.values():
        require(type(row.get("owner")) is str and bool(row["owner"]), "A source needs its original owner.")
        require(type(row.get("locator")) is str and bool(row["locator"]), "A source needs a locator.")
        require(row.get("availability") in {"available", "missing", "stale", "unreadable"}, "Invalid source availability.")
        require(row.get("sha256") is None or bool(SHA.fullmatch(str(row["sha256"]))), "Invalid source hash.")
        if row["availability"] == "available":
            require(bool(SHA.fullmatch(str(row.get("sha256")))), "Available sources need a revision.")
    nodes = {r["id"]: r for r in _rows(value, "nodes")}
    for row in nodes.values():
        require(row.get("kind") in NODE_KINDS and type(row.get("label")) is str, "Invalid node kind or label.")
        require(row.get("source_id") in sources, "Node source is missing.")
        require(row.get("observation") in OBSERVATIONS, "Invalid observation class.")
        require(type(row.get("scopes")) is list and all(x == "*" or ID.fullmatch(str(x)) for x in row["scopes"]), "Invalid applicability scope.")
        require(row.get("layer", "project") in {"global", "project", "directory", "historical"}, "Invalid instruction layer.")
        deps = row.get("depends_on", [])
        require(type(deps) is list and all(x in nodes for x in deps), "Unknown dependency.")
        if "default" in row:
            d = row["default"]
            require(type(d) is dict and type(d.get("key")) is str and "value" in d, "Invalid declared default.")
            require(type(d.get("redundant_lines", [])) is list and all(type(x) is str and 0 < len(x) <= 200 for x in d.get("redundant_lines", [])), "Invalid default phrases.")
        if "trigger_terms" in row:
            require(type(row["trigger_terms"]) is list and all(type(x) is str and 0 < len(x) <= 120 for x in row["trigger_terms"]), "Invalid declared trigger cues.")
    active, done = set(), set()
    def visit(k):
        require(k not in active, "Dependency cycle.")
        if k in done:
            return
        active.add(k)
        for d in nodes[k].get("depends_on", []):
            visit(d)
        active.remove(k)
        done.add(k)
    for key in nodes:
        visit(key)
    resources = {r["id"]: r for r in _rows(value, "resources")}
    for row in resources.values():
        require(row.get("source_id") in sources and type(row.get("relative")) is str, "Invalid resource reference.")
        require(row.get("access") in {"local_selected", "unavailable"}, "Unsupported resource route.")
    for row in _rows(value, "devices"):
        require(row.get("availability") in {"reported_online", "reported_offline", "unknown"}, "Invalid device availability.")
        require(type(row.get("label")) is str, "Device label is missing.")
        if row.get("last_seen") is not None:
            timestamp(row["last_seen"])
    for row in _rows(value, "events"):
        require(row.get("state") in set(STAGES) | {"conflict", "failed", "unknown"}, "Unknown event state.")
        identifier(row.get("operation_id")); identifier(row.get("device_id"))
        require(row.get("source_id") in sources, "Event source is missing.")
        timestamp(row.get("at"))
    for row in _rows(value, "activities"):
        require(row.get("source_id") in sources, "Activity source is missing.")
        require(row.get("detail_resource") is None or row["detail_resource"] in resources, "Activity detail resource is missing.")
        require(row.get("retention") in {"session_only", "no_store", "source_owned"}, "Invalid retention declaration.")
    # Unknown additive fields survive unchanged. They never select code or grant authority.
    return deepcopy(value)


def context_revision(context):
    return stable_revision(validate_context(context))


def validate_checkpoint(value):
    """Read-only future handoff contract; no publisher, adopter or native importer."""
    _bounded(value)
    require(type(value) is dict and value.get("schema_version") == 1, "Unsupported checkpoint.")
    for k in ("workspace_id", "replica_id", "checkpoint_id"):
        identifier(value.get(k))
    require(type(value.get("parents")) is list and len(value["parents"]) <= 16 and
            all(type(x) is str and SHA.fullmatch(x) for x in value["parents"]) and
            len(set(value["parents"])) == len(value["parents"]), "Invalid checkpoint ancestry.")
    require(value["checkpoint_id"] not in value["parents"], "Checkpoint cannot parent itself.")
    return deepcopy(value)


def lifecycle(previous, following):
    """Explain a transition; a true result never performs or authorizes it."""
    require(previous in (None, *STAGES) and following in STAGES, "Unknown lifecycle state.")
    pos = -1 if previous is None else STAGES.index(previous)
    return {"valid": STAGES.index(following) == pos + 1, "previous": previous,
            "following": following, "effect": "none", "authorized": False}


def replica_binding_status(records):
    """Check selected binding declarations; does not identify a physical drive."""
    require(type(records) is list and len(records) <= MAX_ROWS, "Invalid replica bindings.")
    seen, conflicts = {}, []
    for record in records:
        require(type(record) is dict, "Invalid replica binding record.")
        for key in ("workspace_id", "replica_id", "storage_instance_id"):
            identifier(record.get(key))
        key = record["workspace_id"], record["replica_id"]
        if key in seen and seen[key] != record["storage_instance_id"]:
            conflicts.append({"workspace_id": key[0], "replica_id": key[1], "state": "declared_clone_conflict"})
        seen[key] = record["storage_instance_id"]
    return {"state": "blocked" if conflicts else "declarations_consistent", "conflicts": conflicts,
            "physical_identity_observed": False, "effect": "none"}
