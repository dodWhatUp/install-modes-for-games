"""Local controller preferences and diagnosis over existing native owners.

Preference resolution never changes Windows, Steam, reWASD or game settings.
XInput indexes are observations, never persistent controller identifiers.
"""
from __future__ import annotations

import copy
import os
from pathlib import Path
import time
import uuid

import GameToolOverlay as overlay

VERSION = "0.1.0"
ROUTES = ("native", "rewasd", "rewasd-steam")
SCOPES = ("global", "genre", "group", "game")
ROUTE_LABELS = {
    "native": "Native controller",
    "rewasd": "reWASD virtual output",
    "rewasd-steam": "reWASD virtual output through Steam Input",
}


def empty():
    return {"schema_version": 1, "revision": 0, "preferences": [], "game_contexts": {}}


def fingerprint(value):
    return overlay.sha(overlay.encode(value))


def validate(value):
    overlay.fields(value, "schema_version revision preferences game_contexts")
    overlay.require(value["schema_version"] == 1, "Unsupported controller preference schema")
    overlay.require(type(value["revision"]) is int and value["revision"] >= 0, "Invalid revision")
    rows = value["preferences"]
    overlay.require(type(rows) is list and len(rows) <= 256, "Controller preference limit")
    ids = set()
    scopes = set()
    for row in rows:
        overlay.fields(row, "id name scope scope_value controller_id native_profile_id native_config_sha256 route automatic evidence saved_at")
        overlay.token(row["id"])
        overlay.label(row["name"])
        overlay.require(row["id"] not in ids, "Duplicate controller preference")
        ids.add(row["id"])
        overlay.require(row["scope"] in SCOPES, "Unknown preference scope")
        if row["scope"] == "global":
            overlay.require(row["scope_value"] == "", "Global scope needs no value")
        else:
            overlay.label(row["scope_value"])
        scope = (row["scope"], row["scope_value"])
        overlay.require(scope not in scopes, "A preference already exists for this scope; update it")
        scopes.add(scope)
        overlay.require(type(row["controller_id"]) is str and 0 < len(row["controller_id"]) <= 180,
                        "Choose an observed controller; a slot number is not a controller ID")
        overlay.require(not row["controller_id"].lower().startswith(("xinput", "slot")),
                        "XInput indexes cannot be saved as controller identities")
        overlay.require(type(row["native_profile_id"]) is str, "Invalid saved setup reference")
        if row["native_profile_id"]:
            overlay.token(row["native_profile_id"])
        overlay.require(type(row["native_config_sha256"]) is str, "Invalid native source pin")
        if row["native_config_sha256"]:
            overlay.digest(row["native_config_sha256"])
        overlay.require(row["route"] in ROUTES and type(row["automatic"]) is bool, "Invalid route or selection mode")
        overlay.require(type(row["saved_at"]) is int, "Invalid save time")
        evidence = row["evidence"]
        overlay.fields(evidence, "state note at")
        overlay.require(evidence["state"] in ("unverified", "user-reported"), "Unknown acceptance state")
        overlay.require(type(evidence["note"]) is str and len(evidence["note"]) <= 1000, "Acceptance note limit")
        overlay.require(type(evidence["at"]) is int, "Invalid acceptance time")
    contexts = value["game_contexts"]
    overlay.require(type(contexts) is dict and len(contexts) <= 256, "Game context limit")
    for game, context in contexts.items():
        overlay.token(game)
        overlay.fields(context, "genres groups")
        for tags in context.values():
            overlay.require(type(tags) is list and len(tags) <= 32 and len(tags) == len(set(tags)), "Context tag limit")
            for tag in tags:
                overlay.label(tag)
    return value


def preference(name, scope, scope_value, controller_id, native_profile_id="", route="rewasd",
               automatic=False, identity=None, evidence=None, native_config_sha256=""):
    row = dict(id=identity or "controller-pref-" + uuid.uuid4().hex, name=name.strip(),
               scope=scope, scope_value=scope_value.strip(), controller_id=controller_id,
               native_profile_id=native_profile_id, route=route, automatic=automatic,
               native_config_sha256=native_config_sha256,
               evidence=evidence or {"state": "unverified", "note": "", "at": 0},
               saved_at=int(time.time()))
    validate(dict(schema_version=1, revision=0, preferences=[row], game_contexts={}))
    return row


class Preferences:
    def __init__(self, directory):
        self.root = overlay.no_links(Path(directory) / "controller-routing")
        self.path = self.root / "preferences.json"

    def load(self):
        value = validate(overlay.decode(overlay.read(self.path, 1024 * 1024))) if self.path.exists() else empty()
        return value, fingerprint(value)

    def save(self, value, expected):
        validate(value)
        self.root.mkdir(parents=True, exist_ok=True)
        lock = overlay.no_links(self.root / "edit.lock")
        pending = None
        with lock.open("xb"):
            pass
        try:
            before, pin = self.load()
            overlay.require(pin == expected, "Controller preferences changed; refresh before saving")
            value = copy.deepcopy(value)
            value["revision"] = before["revision"] + 1
            if self.path.exists():
                history = overlay.no_links(self.root / "history")
                history.mkdir(exist_ok=True)
                backup = overlay.no_links(history / (pin + ".json"))
                if not backup.exists():
                    with backup.open("xb") as out:
                        out.write(overlay.read(self.path, 1024 * 1024))
            pending = overlay.no_links(self.root / ("pending-" + uuid.uuid4().hex + ".json"))
            with pending.open("xb") as out:
                out.write(overlay.encode(value))
                out.flush()
                os.fsync(out.fileno())
            overlay.require(self.load()[1] == expected, "Concurrent controller preference change")
            os.replace(pending, self.path)
            pending = None
            overlay.require(self.load()[0] == value, "Controller preference readback differs")
            return value
        finally:
            if pending is not None and pending.exists():
                pending.unlink()
            lock.unlink()

    def put(self, row, expected):
        value, pin = self.load()
        overlay.require(pin == expected, "Controller preferences changed; refresh first")
        row = copy.deepcopy(row)
        before = next((x for x in value["preferences"] if x["id"] == row["id"]), None)
        signature = ("controller_id", "native_profile_id", "native_config_sha256", "route", "scope", "scope_value")
        if before and any(before[k] != row[k] for k in signature):
            row["evidence"] = {"state": "unverified", "note": "Controller, source or route changed; previous acceptance is historical.", "at": 0}
        value["preferences"] = [x for x in value["preferences"] if x["id"] != row["id"]] + [row]
        return self.save(value, expected)

    def remove(self, identity, expected):
        value, pin = self.load()
        overlay.require(pin == expected, "Controller preferences changed; refresh first")
        overlay.require(any(x["id"] == identity for x in value["preferences"]), "Preference no longer exists")
        value["preferences"] = [x for x in value["preferences"] if x["id"] != identity]
        return self.save(value, expected)

    def set_game_context(self, game, genres, groups, expected):
        value, pin = self.load()
        overlay.require(pin == expected, "Controller preferences changed; refresh first")
        value["game_contexts"][game] = {"genres": list(genres), "groups": list(groups)}
        return self.save(value, expected)

    def resolve(self, game="", genres=None, groups=None, automatic_only=False):
        value = self.load()[0]
        rows = value["preferences"]
        context = value["game_contexts"].get(game, {})
        genres = context.get("genres", ()) if genres is None else genres
        groups = context.get("groups", ()) if groups is None else groups
        ranked = []
        for row in rows:
            if automatic_only and not row["automatic"]:
                continue
            s, v = row["scope"], row["scope_value"]
            applies = s == "global" or (s == "game" and v == game) or (s == "genre" and v in genres) or (s == "group" and v in groups)
            if applies:
                ranked.append((SCOPES.index(s), row))
        if not ranked:
            return {"state": "none", "preference": None}
        rank = max(x[0] for x in ranked)
        winners = [x[1] for x in ranked if x[0] == rank]
        if len(winners) != 1:
            return {"state": "ambiguous", "preference": None, "candidates": winners}
        return {"state": "preferred", "preference": copy.deepcopy(winners[0]),
                "effective_windows_priority": "unverified", "native_changes": False}


def diagnose(snapshot, row=None):
    """Explain observed endpoints without assuming every interface is a competitor."""
    devices = {x["id"]: x for x in snapshot.get("devices", []) if x.get("present") is True}
    result = {"state": "unselected", "selected": None, "family": [], "other_endpoints": [],
              "xinput_indexes": [x["index"] for x in snapshot.get("xinput", []) if x.get("present")],
              "warnings": list(snapshot.get("warnings", [])), "native_changes": False,
              "effective_priority": "unverified"}
    if row is None:
        return result
    selected = devices.get(row["controller_id"])
    result["selected"] = selected
    if selected is None:
        result["state"] = "missing"
        result["warnings"].append("Saved controller is absent or its local identity changed. Identify it again.")
        return result
    family = {selected["id"]}
    # Only adapter-evidenced edges are traversed. Similar names or shared VID/PID
    # do not establish a relationship between multiple physical controllers.
    edges = snapshot.get("relationships", [])
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if edge.get("status") not in ("observed", "verified"):
                continue
            a, b = edge.get("source_id"), edge.get("target_id")
            if a in family or b in family:
                for identity in (a, b):
                    if identity in devices and identity not in family:
                        family.add(identity)
                        changed = True
    result["state"] = "observed"
    result["family"] = [devices[x] for x in sorted(family)]
    result["other_endpoints"] = [x for key, x in devices.items() if key not in family]
    if len(result["xinput_indexes"]) > 1:
        result["warnings"].append("Multiple XInput slots are present. Their numbers do not prove which controller the game reads.")
    if row["route"] == "rewasd-steam":
        result["warnings"].append("This route expects Steam Input only for the chosen game, downstream of reWASD's virtual output. Saved preference does not enable it.")
    result["warnings"].append("Keep the physical/HID feeder connected. Remap Off is not a hardware disconnect.")
    return result


def capabilities():
    return {"preferences": True, "read_only_inventory": True, "held_input_identification": True,
            "windows_device_disconnect": False, "windows_priority_write": False,
            "automatic_native_remap": False, "steam_input_write": False,
            "reviewed_native_operations_owner": "GameToolRewasd.Native",
            "issues_reconnect_on_layer_switch": False, "native_layer_continuity_observed": False}
