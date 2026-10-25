"""Versioned action/game/context/genre/shared planning rules; never remaps input."""
from __future__ import annotations
import copy,os,uuid
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder
import GameToolOverlay as overlay
from game_keybind_ops.deps import local_lock

VERSION = "0.1.0"
FIELDS = ("route_lock", "forbidden_buttons", "preferred_buttons", "preferred_layer", "direct_access")
SCOPES = ("action", "game", "context", "genre", "global")


def validate(rule):
    overlay.fields(rule, "id revision scope field value acceptance reason")
    overlay.token(rule["id"]); overlay.require(type(rule["revision"]) is int and rule["revision"] >= 1, "Invalid rule revision")
    overlay.fields(rule["scope"], "level target_ids")
    overlay.require(rule["scope"]["level"] in SCOPES and type(rule["scope"]["target_ids"]) is list and
                    len(rule["scope"]["target_ids"]) <= 128 and all(type(x) is str and x for x in rule["scope"]["target_ids"]), "Invalid rule scope")
    overlay.require((rule["scope"]["level"] == "global") == (not rule["scope"]["target_ids"]), "Global scope has no targets; other scopes need targets")
    overlay.require(rule["field"] in FIELDS and rule["acceptance"] in {"proposed", "accepted", "reported_existing", "superseded"}, "Unknown rule field or acceptance")
    maps.text(rule["reason"], 1000); overlay.require(bool(rule["reason"].strip()), "A rule needs its reason")
    value = rule["value"]
    if rule["field"] in {"forbidden_buttons", "preferred_buttons"}:
        overlay.require(type(value) is list and len(value) <= 29 and len(set(value)) == len(value) and
                        all(type(x) is int and x in overlay.R8_POSITIONS for x in value), "Choose distinct visible physical buttons")
    elif rule["field"] == "direct_access": overlay.require(type(value) is bool, "Direct access is yes/no")
    else: maps.text(value, 240); overlay.require(bool(value), "Choose an explicit route/layer")
    return rule


def applies(rule, w, action):
    scope = rule["scope"]; targets = set(scope["target_ids"])
    return {"global": True, "game": w["game_id"] in targets, "action": action["id"] in targets,
        "context": action["context"] in targets or action["overlay_context"] in targets,
        "genre": bool(targets & set(w["extensions"].get("genre_tags", [])))}[scope["level"]]


def active_rules(w):
    rules = list(w["extensions"].get("rules", []))
    snapshot = w["extensions"].get("shared_rules_snapshot")
    if snapshot:
        validate_snapshot(snapshot); rules += snapshot["rules"]
    overlay.require(len(rules) <= 256, "Planning rule count budget")
    identities = set()
    for rule in rules:
        validate(rule)
        overlay.require(rule["id"] not in identities, "Same rule appears in both local and shared scope; reconcile revisions")
        identities.add(rule["id"])
    return [r for r in rules if r["acceptance"] in {"accepted", "reported_existing"}]


def route_constraints(w, action, route, rules=None):
    blocked = []
    for rule in active_rules(w) if rules is None else rules:
        if not applies(rule, w, action): continue
        field, value = rule["field"], rule["value"]
        if field == "route_lock" and route["id"] != value: blocked.append("Accepted route anchor: " + rule["id"])
        if field == "forbidden_buttons" and route["button"] in value: blocked.append("Excluded position: " + rule["id"])
        if field == "direct_access" and value and route["holder"] is not None: blocked.append("Direct-access rule: " + rule["id"])
    return blocked


def preference(w, action, route, rules=None):
    penalty = 0
    for rule in active_rules(w) if rules is None else rules:
        if not applies(rule, w, action): continue
        if rule["field"] == "preferred_buttons" and route["button"] not in rule["value"]: penalty += 1
        if rule["field"] == "preferred_layer" and route["layer"] != rule["value"]: penalty += 1
    return penalty


def empty_snapshot():
    body = {"kind": "controls_shared_rules", "schema_version": 1, "revision": 1, "rules": []}
    return {**body, "sha256": maps.fingerprint(body)}


def validate_snapshot(snapshot):
    overlay.fields(snapshot, "kind schema_version revision rules sha256")
    overlay.require(snapshot["kind"] == "controls_shared_rules" and snapshot["schema_version"] == 1 and type(snapshot["revision"]) is int,
                    "Unknown shared rules schema")
    overlay.require(maps.fingerprint({k: v for k, v in snapshot.items() if k != "sha256"}) == snapshot["sha256"], "Shared rules hash differs")
    overlay.require(type(snapshot["rules"]) is list and len(snapshot["rules"]) <= 128, "Shared rule budget")
    for rule in snapshot["rules"]:
        validate(rule); overlay.require(rule["scope"]["level"] in {"global", "genre"}, "Shared store accepts explicit global or genre rules only")
    overlay.require(len({r["id"] for r in snapshot["rules"]}) == len(snapshot["rules"]), "Duplicate shared rule")
    return snapshot


class Library:
    def __init__(self, source_library):
        self.source_library = source_library
        self.root = overlay.no_links(source_library.root / "controls-planning")
        self.path = overlay.no_links(self.root / "shared-rules.json")

    def read(self):
        from GameToolControlsPlanner import decode
        return validate_snapshot(decode(overlay.read(self.path))) if self.path.exists() else empty_snapshot()

    def save(self, rules, expected, *, authorize):
        for rule in rules: validate(rule)
        old = self.read(); overlay.require(old["sha256"] == expected, "Shared rules changed; review before saving")
        body = {"kind": "controls_shared_rules", "schema_version": 1, "revision": old["revision"] + 1, "rules": copy.deepcopy(rules)}
        candidate = validate_snapshot({**body, "sha256": maps.fingerprint(body)})
        overlay.require(callable(authorize) and authorize(copy.deepcopy(candidate)) is True, "Saving shared scope needs explicit local review")
        self.root.mkdir(parents=True, exist_ok=True)
        with local_lock(self.root, "rules-edit.lock"):
            overlay.require(self.read()["sha256"] == expected, "Shared rules changed during review")
            history = overlay.no_links(self.root / "shared-rules-history"); history.mkdir(exist_ok=True)
            backup = overlay.no_links(history / (old["sha256"] + ".json"))
            if not backup.exists(): builder.write_new(backup, old)
            temp = overlay.no_links(self.path.with_name("rules.pending-" + uuid.uuid4().hex))
            try: builder.write_new(temp, candidate); os.replace(temp, self.path)
            finally:
                if temp.exists(): temp.unlink()
        overlay.require(self.read() == candidate, "Shared rules readback differs")
        return candidate

    def impact(self, candidate):
        validate_snapshot(candidate)
        from GameToolControlsPlanner import WorkbookLibrary
        workbooks = WorkbookLibrary(self.source_library)
        affected = []
        if self.root.exists():
            for path in sorted(self.root.glob("*.json")):
                if path.name == "shared-rules.json": continue
                workbook = workbooks.load(path.stem)
                hits = {a["id"] for a in workbook["actions"] for rule in candidate["rules"] if applies(rule, workbook, a)}
                if hits: affected.append({"game_id": workbook["game_id"], "action_ids": sorted(hits), "automatic_adoption": False})
        return affected
