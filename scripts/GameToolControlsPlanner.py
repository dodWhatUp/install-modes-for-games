"""Read-only controls planning beside SourceLibrary. No runtime/input owner.

The small versioned application workbook deliberately does not accept the
larger handoff's azeron_game_workbook v2 as a native map or apply operation.
"""
from __future__ import annotations
import copy
import hashlib
from pathlib import Path
import os
import uuid
import GameToolOverlay as overlay
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder
from game_keybind_ops.deps import strict_json

VERSION = "0.2.1"
POLICY = "A20-UF-1"
RULES = "combat-r2-readonly-1"
LITTLE_FINGER_RULES = "azeron-little-finger-20261026-r1"
ROWS = {bid: row for row, ids in ((5, (4, 8, 12, 17)), (4, (3, 7, 11, 16)),
        (3, (2, 6, 10, 15)), (2, (1, 5, 9, 14)), (1, (37, 38, 13, 18))) for bid in ids}
ROW_ORDER = (2, 4, 3, 5, 1)
ANCHORS = {5, 9, 14, 24, 19, 2}
ACTIVATIONS = ("unknown", "press", "hold", "toggle", "repeat", "release", "select", "activate")


def protected_buttons(w, route=None):
    """Versioned planning reservations; movement outputs remain separate anchors.

    The new little-finger #3/#4 layer roles and #37 blank cannot be consumed by
    action optimization merely because the old native map still emits a key.
    A #37 exception is a recorded, scoped user proposal, never Apply authority.
    """
    if w["baseline"]["rules_revision"] != LITTLE_FINGER_RULES: return {19, 24, 2}
    reserved = {19, 24, 3, 4, 37}
    if route is not None and route.get("button") == 37:
        review = w["extensions"].get("mapping_quality_review", {})
        decisions = review.get("button_decisions", []) if isinstance(review, dict) else []
        if isinstance(decisions, list) and any(isinstance(row, dict) and row.get("route_id") == route["id"] and
                row.get("user_requested") is True and isinstance(row.get("origin"), str) and row["origin"].strip() for row in decisions):
            reserved.remove(37)
    return reserved


def route_access_rank(w, route):
    """Ordinal preference only; little-finger roles supersede generic row order."""
    if w["baseline"]["rules_revision"] == LITTLE_FINGER_RULES and str(route.get("finger", "")).casefold() == "little":
        return {1: 0, 3: 1, 2: 3, 4: 4, 37: 5}.get(route["button"], 5)
    return ROW_ORDER.index(route["row"]) if route.get("row") in ROW_ORDER else 5


def bounded_data(value, depth=0, count=None):
    """Planning text may contain paragraphs; runtime registry rules stay separate."""
    count = count if count is not None else [0]; count[0] += 1
    overlay.require(depth <= 24 and count[0] <= 150000, "Workbook nesting/item budget exceeded")
    if type(value) is dict:
        overlay.require(len(value) <= 2048 and all(type(k) is str and len(k) <= 240 for k in value), "Workbook field budget")
        for child in value.values(): bounded_data(child, depth+1, count)
    elif type(value) is list:
        overlay.require(len(value) <= 4096, "Workbook list budget")
        for child in value: bounded_data(child, depth+1, count)
    elif type(value) is str:
        overlay.require(len(value) <= 16000 and not any(ord(c) < 32 and c not in '\n\r\t' for c in value), "Workbook text budget")
    elif type(value) is float:
        import math
        overlay.require(math.isfinite(value), "Nonfinite workbook value")
    else: overlay.require(value is None or type(value) in (bool, int), "Unknown workbook value")


def decode(raw):
    overlay.require(type(raw) is bytes and 0 < len(raw) <= overlay.MAX_JSON, "Planning JSON exceeds 1 MiB")
    value = strict_json(raw); bounded_data(value); return value


def priority(urgency, frequency):
    """Ordinal demand; missing evidence is never a zero or midpoint."""
    for values, maximum in ((urgency, 5), (frequency, 4)):
        overlay.require(type(values) is list and len(values) <= maximum and len(set(values)) == len(values)
                        and all(type(v) is int and 1 <= v <= maximum for v in values), "Invalid U/F candidates")
    candidates = sorted({4 * (u - 1) + f for u in (urgency or range(1, 6))
                         for f in (frequency or range(1, 5))}) if urgency or frequency else []
    return {"policy": POLICY, "candidates": candidates, "score": candidates[0] if len(candidates) == 1 else None,
            "range": [min(candidates), max(candidates)] if candidates else None}


def bundle_priority(actions):
    """Preserve highest urgency; shared physical activation frequency is unknown.

    Do not sum member rates, average priorities, or combine different contexts.
    """
    overlay.require(bool(actions) and len({a["context"] for a in actions}) == 1, "Bundle needs one source context")
    if not any(a["urgency"] for a in actions):
        return {**priority([], []), "frequency_basis": "unique shared activations unknown"}
    possible = {1}
    for a in actions:
        possible = {max(x, y) for x in possible for y in (a["urgency"] or range(1, 6))}
    return {**priority(sorted(possible), []), "frequency_basis": "unique shared activations unknown"}


def _action(identity, label, context, output, **extra):
    return {"id": builder.stable("action-", identity), "label": label[:240], "context": context,
            "output": output, "overlay_context": context, "meaning": "", "activation": "unknown",
            "categories": [], "urgency": [], "frequency": [], "needs_movement": None,
            "simultaneous": [], "bundle_id": None, "evidence": [], "user_priority_override": None,
            "override_reason": "", "proposed_route": None, **extra}


def new_workbook(document, *, rules_revision=LITTLE_FINGER_RULES):
    maps.validate(document); builder.map_outputs(document)
    actions = []
    seen = {}
    for m in document["maps"]:
        for c in m["cells"]:
            if c["output"] == "UNASSIGNED" or c["output"].startswith("LAYER:"): continue
            identity = (m["context"], c["output"])
            label = c["action"] or c["display_action"] or c["output"]
            if identity in seen:
                prior = seen[identity]
                if label != prior["label"]:
                    prior["evidence"].append(f'Conflicting overlay label: {m["layer"]}/#{c["button_id"]}: {label}')
                continue
            action = _action("|".join(identity), label, m["context"], c["output"],
                             evidence=["saved-overlay-label; game meaning unverified"])
            seen[identity] = action; actions.append(action)
    return validate({"kind": "game_controls_workbook", "schema_version": 1, "game_id": document["game_id"],
        "id": builder.stable("controls-", document["game_id"]), "revision": 1, "policy": POLICY,
        "baseline": {"map_sha256": maps.fingerprint(document), "keymap_revision": document["keymap_revision"],
                     "rules_revision": rules_revision}, "sources": [], "actions": actions,
        "exclusive_contexts": [], "pending_shared_changes": [], "change_log": [], "extensions": {}})


def validate(w):
    bounded_data(w)
    overlay.fields(w, "kind schema_version game_id id revision policy baseline sources actions exclusive_contexts pending_shared_changes change_log extensions")
    overlay.require(w["kind"] == "game_controls_workbook" and type(w["schema_version"]) is int and
                    w["schema_version"] == 1 and w["policy"] == POLICY, "Unsupported controls workbook; handoff v2 is a planning contract")
    for key in ("id", "game_id"): overlay.token(w[key])
    overlay.require(type(w["revision"]) is int and w["revision"] >= 1, "Invalid workbook revision")
    overlay.fields(w["baseline"], "map_sha256 keymap_revision rules_revision")
    for key in ("map_sha256", "keymap_revision"): overlay.digest(w["baseline"][key])
    overlay.require(w["baseline"]["rules_revision"] in {RULES, LITTLE_FINGER_RULES}, "Unknown required physical rules revision")
    overlay.require(type(w["sources"]) is list and len(w["sources"]) <= 16, "At most 16 binding sources")
    for s in w["sources"]:
        overlay.fields(s, "kind id revision snapshot")
        overlay.require(s["kind"] in {"target", "instance"}, "Unknown source type")
        overlay.token(s["id"]); overlay.digest(s["revision"])
        overlay.require(type(s["snapshot"]) is dict and maps.fingerprint(s["snapshot"]) == s["revision"], "Source snapshot differs")
        overlay.require(s["snapshot"].get("game_id") == w["game_id"], "Source belongs to another game")
    overlay.require(type(w["actions"]) is list and len(w["actions"]) <= 2048, "Action count limit")
    ids = set()
    for a in w["actions"]:
        overlay.fields(a, "id label context output overlay_context meaning activation categories urgency frequency needs_movement simultaneous bundle_id evidence user_priority_override override_reason proposed_route")
        overlay.token(a["id"]); overlay.require(a["id"] not in ids, "Duplicate action ID"); ids.add(a["id"])
        for key in ("label", "context", "output", "meaning", "override_reason"): maps.text(a[key], 1000 if key == "meaning" else 240)
        overlay.require(a["overlay_context"] is None or type(a["overlay_context"]) is str, "Choose an overlay context or Unknown")
        overlay.require(a["activation"] in ACTIVATIONS, "Unknown activation")
        overlay.require(a["needs_movement"] is None or type(a["needs_movement"]) is bool, "Movement requirement is unknown/yes/no")
        priority(a["urgency"], a["frequency"])
        for key in ("categories", "simultaneous", "evidence"):
            overlay.require(type(a[key]) is list and len(a[key]) <= 32, "Action annotation limit")
            for item in a[key]: maps.text(item, 1000)
        overlay.require(a["bundle_id"] is None or type(a["bundle_id"]) is str, "Invalid bundle identity")
        override = a["user_priority_override"]
        overlay.require(override is None or type(override) is int and 1 <= override <= 20 and bool(a["override_reason"].strip()), "Priority override needs a score and reason")
        overlay.require(a["proposed_route"] is None or type(a["proposed_route"]) is str, "Invalid proposed route")
    for a in w["actions"]:
        overlay.require(set(a["simultaneous"]) <= ids and a["id"] not in a["simultaneous"], "Unknown simultaneous action")
    overlay.require(type(w["exclusive_contexts"]) is list and len(w["exclusive_contexts"]) <= 64, "Context-pair limit")
    for pair in w["exclusive_contexts"]:
        overlay.fields(pair, "contexts evidence")
        overlay.require(type(pair["contexts"]) is list and len(pair["contexts"]) == 2 and len(set(pair["contexts"])) == 2
                        and all(type(c) is str for c in pair["contexts"]) and bool(pair["evidence"]), "Context exclusivity needs evidence")
    for key in ("pending_shared_changes", "change_log"):
        overlay.require(type(w[key]) is list and len(w[key]) <= 256, "History/rule limit")
    overlay.require(type(w["extensions"]) is dict and len(maps.encoded(w)) <= overlay.MAX_JSON, "Workbook exceeds 1 MiB")
    return w


def routes(document):
    """Only routes in the saved map. LAYER: is the native reader's hold contract."""
    buttons = {b["id"]: b for b in document["buttons"]}
    holds = {}
    for m in document["maps"]:
        if m["layer"] == "BASIC":
            for c in m["cells"]:
                if c["output"].startswith("LAYER:"):
                    holds.setdefault(c["output"].split(":", 1)[1], set()).add(c["button_id"])
    out = []
    for m in document["maps"]:
        holder = next(iter(holds[m["layer"]])) if len(holds.get(m["layer"], ())) == 1 else None
        for c in m["cells"]:
            b = buttons[c["button_id"]]
            out.append({"id": f'{m["layer"]}/{m["context"]}/{b["id"]}', "layer": m["layer"], "context": m["context"],
                "button": b["id"], "finger": b["finger"], "row": ROWS.get(b["id"]), "output": c["output"],
                "holder": holder, "holder_finger": buttons[holder]["finger"] if holder else None,
                "entry_known": m["layer"] == "BASIC" or holder is not None})
    return out


def route_review(action, route, equivalent=lambda a, b: a == b, *, protected_buttons=None):
    blocked, warnings = [], []
    protected_buttons = {19, 24, 2} if protected_buttons is None else protected_buttons
    if route["output"] == "UNASSIGNED" or route["output"].startswith("LAYER:") or route["button"] in protected_buttons:
        blocked.append("Protected input or layer selector")
    if equivalent(route["output"], "F24"): blocked.append("Dedicated overlay output")
    if route["button"] in {5, 9, 14} and not equivalent(route["output"], action["output"]):
        blocked.append("Preserve movement anchor")
    if route["context"] != action["overlay_context"]: blocked.append("Source context has no matching reviewed overlay context")
    if not route["entry_known"]: blocked.append("Layer entry unknown")
    if action["needs_movement"] and route["button"] not in ROWS: blocked.append("Movement requires keeping thumb on stick")
    if route["holder"] and route["holder_finger"] == route["finger"]:
        blocked.append("Held layer occupies the target finger")
    if action["needs_movement"] is None: warnings.append("Movement requirement unknown")
    if not action["meaning"] or action["activation"] == "unknown": warnings.append("Action meaning or activation unverified")
    if not priority(action["urgency"], action["frequency"])["candidates"]: warnings.append("Priority unknown")
    return {"blocked": blocked, "warnings": warnings}


def requirements_review(w, action, route, rules=None):
    requirements = w["extensions"].get("requirements_by_action", {}).get(action["id"], {})
    blocked = []
    if w["baseline"]["rules_revision"] == LITTLE_FINGER_RULES and route["button"] == 2 and any(f >= 3 for f in action["frequency"]):
        blocked.append("Little-finger #2 is reserved for an infrequent action")
    if w["baseline"]["rules_revision"] == LITTLE_FINGER_RULES and route["button"] == 2 and any(u >= 4 for u in action["urgency"]):
        blocked.append("Little-finger #2 is reserved for a non-urgent action")
    if requirements.get("direct_access") is True and route["holder"] is not None: blocked.append("Action requires direct access")
    from GameToolControlsRules import route_constraints
    blocked.extend(route_constraints(w, action, route, rules))
    return blocked


def preview(w, document):
    validate(w); maps.validate(document); builder.map_outputs(document)
    overlay.require(w["game_id"] == document["game_id"] and w["baseline"]["map_sha256"] == maps.fingerprint(document)
                    and w["baseline"]["keymap_revision"] == document["keymap_revision"], "Stale map/native baseline; reload and reconcile")
    all_routes = routes(document); indexed = {r["id"]: r for r in all_routes}
    canonical = {key: canonical_output(w, key) for key in {a["output"] for a in w["actions"]} | {r["output"] for r in all_routes} | {"F24"}}
    equivalent = lambda a, b: canonical.get(a, a) == canonical.get(b, b)
    from GameToolControlsRules import active_rules
    rule_set = active_rules(w)
    locked = set()
    for source in w["sources"]:
        if source["kind"] == "target":
            protected = {r["id"] for r in source["snapshot"].get("bindings", []) if r.get("locked")}
            locked.update(action_source_id(source, f) for f in source["snapshot"]["action_fields"] if f["id"] in protected)
    rows = []; bundles = {}
    for a in w["actions"]:
        if a["bundle_id"]: bundles.setdefault((a["context"], a["bundle_id"]), []).append(a)
    exclusive = {frozenset(p["contexts"]) for p in w["exclusive_contexts"]}
    for a in w["actions"]:
        current = [r for r in all_routes if r["context"] == a["overlay_context"] and equivalent(r["output"], a["output"])]
        choices = []
        for r in all_routes:
            review = route_review(a, r, equivalent, protected_buttons=protected_buttons(w, r)); review["blocked"].extend(requirements_review(w, a, r, rule_set))
            if a["id"] in locked and not equivalent(a["output"], r["output"]): review["blocked"].append("Native binding field is locked")
            if a["output"] in {"MouseLeft", "MouseRight", "MouseMiddle", "WheelUp", "WheelDown", "WheelLeft", "WheelRight"} and not equivalent(a["output"], r["output"]): review["blocked"].append("Preserve existing mouse binding")
            if not review["blocked"]: choices.append({**r, "warnings": review["warnings"]})
        # No uncalibrated comfort arithmetic. Keep accepted routes first and
        # rank alternatives qualitatively; this is not an optimizing solver.
        choices.sort(key=lambda r: (not equivalent(r["output"], a["output"]), r["holder"] is not None,
                     route_access_rank(w, r), r["id"]))
        chosen = indexed.get(a["proposed_route"])
        blocked = []; warnings = []
        if a["proposed_route"]:
            overlay.require(chosen is not None, "Proposed route no longer exists")
            check = route_review(a, chosen, equivalent, protected_buttons=protected_buttons(w, chosen)); blocked.extend(check["blocked"]); warnings.extend(check["warnings"])
            blocked.extend(requirements_review(w, a, chosen, rule_set))
            if a["id"] in locked and not equivalent(a["output"], chosen["output"]): blocked.append("Native binding field is locked")
            if a["output"] in {"MouseLeft", "MouseRight", "MouseMiddle", "WheelUp", "WheelDown", "WheelLeft", "WheelRight"} and not equivalent(a["output"], chosen["output"]): blocked.append("Preserve existing mouse binding")
        if not w["sources"]: warnings.append("Effective game source unknown; overlay labels only")
        elif any(s["kind"] == "target" for s in w["sources"]): warnings.append("Saved binding rows; override precedence unverified")
        if any(e.startswith("Conflicting overlay label:") for e in a["evidence"]):
            warnings.append("Overlay labels disagree across exact input aliases")
        if a["bundle_id"]:
            members = bundles[(a["context"], a["bundle_id"])]
            if len({(x["proposed_route"], x["overlay_context"]) for x in members}) > 1:
                blocked.append("Keep shared binding bundle together")
        desired = chosen["output"] if chosen else a["output"]
        for other in w["actions"]:
            if other["id"] == a["id"] or (a["bundle_id"] and (a["context"], a["bundle_id"]) == (other["context"], other["bundle_id"])): continue
            other_route = indexed.get(other["proposed_route"])
            other_key = other_route["output"] if other_route else other["output"]
            if equivalent(desired, other_key) and frozenset((a["context"], other["context"])) not in exclusive:
                if chosen and not equivalent(desired, a["output"]): blocked.append("Would displace or collide with " + other["label"])
                else: warnings.append("Shared output/context overlap: " + other["label"])
            if other["id"] in a["simultaneous"] or a["id"] in other["simultaneous"]:
                ours = [chosen] if chosen else current
                theirs = [other_route] if other_route else [r for r in all_routes if r["context"] == other["overlay_context"] and r["output"] == other["output"]]
                if any(x["finger"] == y["finger"] or x["holder_finger"] == y["finger"] or y["holder_finger"] == x["finger"] for x in ours for y in theirs):
                    warnings.append("Simultaneous finger/hold compatibility needs review: " + other["label"])
        aliases = [r["id"] for r in all_routes if equivalent(r["output"], desired)]
        rows.append({"id": a["id"], "label": a["label"], "context": a["context"],
            "priority": priority(a["urgency"], a["frequency"]), "user_priority_override": a["user_priority_override"],
            "bundle_priority": bundle_priority(bundles[(a["context"], a["bundle_id"])]) if a["bundle_id"] else None,
            "current": [r["id"] for r in current], "proposed": chosen["id"] if chosen else None,
            "from_key": a["output"], "to_key": desired, "aliases": aliases,
            "candidates": choices, "blocked": sorted(set(blocked)), "warnings": sorted(set(warnings)),
            "changed": chosen is not None and not equivalent(chosen["output"], a["output"])})
    return {"kind": "game_controls_preview", "schema_version": 1, "plan_sha256": maps.fingerprint(w),
            "game_id": w["game_id"], "rows": rows, "read_only": True,
            "operations": {"save_draft": "available", "publish_overlay": "separate existing builder review",
                           "apply_game_bindings": "separate reviewed workflow", "apply_native_profile": "native software / manual review"},
            "limitations": ["Candidates preserve current placement; no global optimality claim", "Native equality is a saved contract, not a fresh device observation",
                            "Exact output spelling only; sided/modifier/Steam Input aliases need source review", "Game behavior and physical comfort untested"]}


def source_snapshot(service, kind, identity, game_id):
    """Reuse actual adapter owners; never register a target or create a plan."""
    if kind == "target":
        body = service.inspect_target(identity); spec = service.target(identity)["spec"]
        fields = {f["id"]: f for f in spec["fields"]}
        body["game_id"] = spec["game_id"]
        body["action_fields"] = [{"id": b["id"], "label": fields[b["id"]]["selector"].get("command", b["id"]),
             "context": b["context"], "key": b["key"], "bundle": fields[b["id"]].get("linked_group")}
             for b in body["bindings"]]
    else:
        overlay.require(kind == "instance", "Unknown binding source")
        from game_keybind_ops import effective
        rec = effective.instance(service, identity); values, hashes = effective.read_values(service, rec)
        active, shadowed = effective.resolved(values)
        body = {"game_id": rec["body"]["game_id"], "instance_revision": rec["revision"], "file_hashes": hashes,
                "action_fields": [{"id": r["target_id"] + ":" + r["field_id"], "label": r["action"], "context": r["context"],
                    "key": r["key"], "bundle": r.get("linked_group") or None} for r in active], "shadowed": shadowed}
    overlay.require(body["game_id"] == game_id, "Binding source belongs to another game")
    return {"kind": kind, "id": identity, "revision": maps.fingerprint(body), "snapshot": body}


def attach_source(w, source):
    result = copy.deepcopy(w)
    result["sources"] = [copy.deepcopy(source)]
    result["actions"] = [_action(source["id"] + "|" + r["id"] + "|" + r["context"], r["label"], r["context"], r["key"],
        overlay_context=None, bundle_id=r["bundle"], evidence=[source["kind"] + ":" + source["id"] + "@" + source["revision"]])
        for r in source["snapshot"]["action_fields"]]
    return validate(result)


def action_source_id(source, field):
    """Exact identity used by attach_source, independent of translated labels."""
    return builder.stable("action-", source["id"] + "|" + field["id"] + "|" + field["context"])


def canonical_output(w, value):
    """Only explicitly evidenced aliases, never case or sided-modifier guesses."""
    aliases = w["extensions"].get("key_aliases", [])
    overlay.require(type(aliases) is list and len(aliases) <= 128, "Key alias budget")
    seen = set(); result = value
    for alias in aliases:
        overlay.fields(alias, "display native evidence source_revision")
        overlay.require(alias["display"] not in seen and bool(alias["evidence"]) and
                        alias["source_revision"] in {s["revision"] for s in w["sources"]}, "Key alias needs an exact current source and evidence")
        for key in ("display", "native", "evidence"): maps.text(alias[key], 500)
        if len(alias["display"]) == len(alias["native"]) == 1 and alias["display"].isalnum() and alias["native"].isalnum():
            overlay.require(alias["display"].casefold() == alias["native"].casefold(), "A key-name alias cannot remap one letter/digit to another")
        seen.add(alias["display"])
        if alias["display"] == value: result = alias["native"]
    return result


def check_sources(w, service):
    for s in w["sources"]:
        fresh = source_snapshot(service, s["kind"], s["id"], w["game_id"])
        overlay.require(fresh["revision"] == s["revision"], "Binding source changed; reconcile before exporting or saving")


def reconcile_source(w, fresh, document):
    """Keep annotations, re-read native keys, clear proposals on changed rows."""
    validate(w); overlay.require(len(w["sources"]) == 1, "Choose one source to reconcile")
    previous = w["sources"][0]
    overlay.require((previous["kind"], previous["id"]) == (fresh["kind"], fresh["id"]), "Reconciliation cannot replace the source owner")
    seed = attach_source(w, fresh); old = {a["id"]: a for a in w["actions"]}; differences = []
    for action in seed["actions"]:
        prior = old.get(action["id"])
        if prior is None:
            differences.append({"action_id": action["id"], "change": "added", "current_key": action["output"]}); continue
        changed = any(prior[k] != action[k] for k in ("output", "context", "bundle_id"))
        for key in ("label", "meaning", "activation", "categories", "urgency", "frequency", "needs_movement", "user_priority_override", "override_reason", "overlay_context"):
            action[key] = copy.deepcopy(prior[key])
        action["simultaneous"] = [ident for ident in prior["simultaneous"] if ident in {a["id"] for a in seed["actions"]}]
        action["evidence"] = list(dict.fromkeys(action["evidence"] + prior["evidence"]))[:32]
        if not changed: action["proposed_route"] = prior["proposed_route"]
        else: differences.append({"action_id": action["id"], "change": "binding_or_bundle", "previous_key": prior["output"], "current_key": action["output"]})
    for ident in set(old) - {a["id"] for a in seed["actions"]}: differences.append({"action_id": ident, "change": "removed"})
    changed_bundles = {(a["context"], a["bundle_id"]) for a in seed["actions"] if a["id"] in {d["action_id"] for d in differences} and a["bundle_id"]}
    for a in seed["actions"]:
        if (a["context"], a["bundle_id"]) in changed_bundles: a["proposed_route"] = None
    seed["extensions"].setdefault("source_reconciliation_history", []).append({"from": previous["revision"], "to": fresh["revision"], "differences": differences})
    seed["extensions"].pop("key_aliases", None)  # prior aliases need current-source evidence again
    validate(seed); preview(seed, document)
    return seed, differences


def native_status(keymap, profiles_root):
    """Exact on-disk profile guard; formatting drift is still drift."""
    root = overlay.no_links(Path(profiles_root))
    rows = []
    for layer in keymap["layers"]:
        identity = layer.get("profile_id")
        try: valid = str(uuid.UUID(identity)) == identity.lower()
        except (ValueError, TypeError, AttributeError): valid = False
        if not valid:
            rows.append({"layer": layer["id"], "state": "unverified"}); continue
        paths = list(root.glob("*/ProfileStorage/profile_" + identity + ".json")) if root.exists() else []
        if len(paths) != 1:
            rows.append({"layer": layer["id"], "state": "missing_or_ambiguous"}); continue
        raw = overlay.read(overlay.no_links(paths[0]))
        digest = hashlib.sha256(raw).hexdigest()
        rows.append({"layer": layer["id"], "state": "match" if digest == layer.get("profile_sha256") else "drift",
                     "current_sha256": digest})
    return rows


class WorkbookLibrary:
    """Separate planning namespace inside SourceLibrary, with exact edit guards."""
    def __init__(self, source_library):
        self.root = overlay.no_links(source_library.root / "controls-planning")

    def path(self, game):
        overlay.token(game); return overlay.no_links(self.root / (game + ".json"))

    def load(self, game):
        return validate(decode(overlay.read(self.path(game))))

    def save(self, w, expected="absent"):
        validate(w); self.root.mkdir(parents=True, exist_ok=True)
        target = self.path(w["game_id"]); lock = overlay.no_links(self.root / "edit.lock")
        with lock.open("xb"): pass
        try:
            old = self.load(w["game_id"]) if target.exists() else None
            overlay.require((maps.fingerprint(old) if old else "absent") == expected, "Workbook changed; reload before saving")
            if old:
                history = overlay.no_links(self.root / "history" / w["game_id"]); history.mkdir(parents=True, exist_ok=True)
                backup = overlay.no_links(history / (maps.fingerprint(old) + ".json"))
                if not backup.exists(): builder.write_new(backup, old)
            temp = overlay.no_links(target.with_name(target.name + ".pending-" + uuid.uuid4().hex))
            try:
                builder.write_new(temp, w); os.replace(temp, target)
            finally:
                if temp.exists(): temp.unlink()
            overlay.require(self.load(w["game_id"]) == w, "Workbook readback mismatch")
            return maps.fingerprint(w)
        finally: lock.unlink()


def export_packet(w, document):
    report = preview(w, document)
    from GameToolControlsQuality import audit, compact
    quality = compact(audit(w, document, report))
    # Share each physical route once. Repeating its geometry/constraints in
    # every action made real multi-layer games exceed the existing JSON bound.
    for row in report["rows"]:
        row["candidate_total"] = len(row["candidates"])
        row["candidates"] = [r["id"] for r in row["candidates"][:8]]
    packet = {"kind": "game_controls_review_packet", "schema_version": 2, "workbook": copy.deepcopy(w),
            "route_catalog": routes(document), "preview": report, "quality_audit": quality,
            "instructions": "Data only. Candidate IDs reference route_catalog; eight ranked examples per action, with total count. Return a game_controls_workbook v1 with unchanged baseline and source pins. Do not apply or publish. Preserve bundles, unknowns and fixed native outputs."}
    if len(maps.encoded(packet)) > overlay.MAX_JSON:
        # Larger real workbooks retain every action/source row. Only repeated
        # derived diagnostics/route geometry change representation; the v1
        # workbook and its importer remain identical. v3 is explicit, not a
        # silently truncated v2 packet or an increased input budget.
        catalog = packet["route_catalog"]
        messages = sorted({text for row in report["rows"] for key in ("blocked", "warnings") for text in row[key]})
        codes = {text: "m"+str(index+1) for index, text in enumerate(messages)}
        entries = {}
        for route in catalog:
            entries.setdefault(route["layer"], {"holder": route["holder"], "holder_finger": route["holder_finger"], "entry_known": route["entry_known"]})
        packet = {"kind": "game_controls_review_packet", "schema_version": 3, "workbook": copy.deepcopy(w),
            "route_catalog_encoding": "route_id_to_output", "route_catalog": {r["id"]: r["output"] for r in catalog},
            "physical_controls": [{"button": b["id"], "finger": b["finger"], "row": ROWS.get(b["id"]),
                **{key: b[key] for key in ("x", "y", "width", "height")}} for b in document["buttons"]],
            "hidden_protected_controls": [{"button": 19, "role": "Overlay hold"}, {"button": 24, "role": "Movement stick"}],
            "layer_entries": entries,
            "preview": {"kind": report["kind"], "plan_sha256": report["plan_sha256"], "game_id": report["game_id"], "read_only": True,
                "row_fields": ["action_id", "changed", "blocked_codes", "warning_codes", "candidate_total", "candidate_ids"],
                "rows": [[row["id"], row["changed"], [codes[x] for x in row["blocked"]], [codes[x] for x in row["warnings"]],
                          row["candidate_total"], row["candidates"][:2]] for row in report["rows"]],
                "message_catalog": {code: text for text, code in codes.items()}},
            "quality_audit": quality,
            "instructions": "Data only. v3 retains the entire game_controls_workbook v1, including every action and source pin. route_catalog maps layer/context/button IDs to outputs; physical_controls supplies each button's finger, row and geometry; layer_entries supplies holders. preview.row_fields names each compact row's columns. Resolve blocked/warning codes through preview.message_catalog. Candidate IDs give at most two examples, with the full candidate_total. Current routes follow matching workbook output/context and route_catalog; proposed routes remain in each workbook action. Return only the supported v1 workbook with unchanged baseline/source pins. No Apply or Publish authority."}
    overlay.require(len(maps.encoded(packet)) <= overlay.MAX_JSON, "Review packet exceeds 1 MiB; export the focused research request or a smaller reviewed scope")
    return packet


def overlay_candidate(w, document):
    """Prepare all affected layer/context labels through the existing renderer.

    This is a display-only candidate, never a claim that proposed inputs work.
    """
    report = preview(w, document)
    overlay.require(not any(r["blocked"] for r in report["rows"]), "Resolve blocked routes before preparing overlay candidates")
    result = copy.deepcopy(document)
    by_id = {a["id"]: a for a in w["actions"]}
    original_labels = {a["id"]: a["label"] for a in new_workbook(document, rules_revision=w["baseline"]["rules_revision"])["actions"]} if not w["sources"] else {}
    labels = {}; old_keys = set()
    for r in report["rows"]:
        a = by_id[r["id"]]
        if a["overlay_context"] is None: continue
        if not w["sources"] and not r["changed"] and a["label"] == original_labels.get(a["id"]): continue
        labels.setdefault((a["overlay_context"], canonical_output(w, r["to_key"])), []).append(a["label"])
        if r["changed"]: old_keys.add((a["overlay_context"], canonical_output(w, a["output"])))
    for m in result["maps"]:
        for c in m["cells"]:
            pair = (m["context"], canonical_output(w, c["output"]))
            if pair in labels:
                label = " / ".join(dict.fromkeys(labels[pair]))
                c.update(action=label[:240], display_action=label[:80], evidence="ai_suggestion",
                         source="Planning preview only; proposed game bindings have not been applied")
            elif pair in old_keys:
                c.update(action="Pending binding move", display_action="Pending move", evidence="ai_suggestion",
                         source="Planning preview only; inspect the exact game diff before publication")
    overlay.require(maps.output_matrix(result) == maps.output_matrix(document), "Candidate changed native output")
    if any(row["changed"] for row in report["rows"]):
        result["guidance"] = [g for g in result["guidance"] if g["id"] != "controls-unapplied-proposal"]
        result["guidance"].append({"id": "controls-unapplied-proposal", "text": "Candidate game bindings have not been verified; preview only",
                                  "evidence": "proposal", "source": maps.fingerprint(w)})
    return maps.validate(result)


def export_candidate(w, document, keymap, destination, appearance=None):
    """Create a new offline review folder; never writes the active registry."""
    candidate = overlay_candidate(w, document)
    package = builder.package([candidate], [keymap])
    packet = export_packet(w, document)
    target = overlay.no_links(Path(destination)); target.mkdir()  # exclusive: no partial overwrite
    builder.write_new(target / "candidate.keymaps.json", package)
    builder.write_new(target / "controls-review.json", packet)
    images = []
    for index, mapping in enumerate(candidate["maps"]):
        for view in ("Keys", "Actions", "Combined", "ActionFirst"):
            name = f"map-{index:02d}-{view}.png"; path = target / name
            rendered = maps.render(candidate, mapping, path, view, appearance)
            images.append({"layer": mapping["layer"], "context": mapping["context"], "view": view, "path": name,
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "render_result": rendered})
    receipt = {"kind": "game_controls_candidate_preview", "schema_version": 1, "plan_sha256": maps.fingerprint(w),
               "game_id": w["game_id"], "images": images, "published": False, "game_bindings_applied": False,
               "appearance_snapshot": copy.deepcopy(appearance),
               "next_step": "Review game binding compatibility before importing the candidate through the existing builder. Save draft and Publish Overlay are separate."}
    builder.write_new(target / "PREVIEW.json", receipt)
    return receipt


def import_review(current, incoming, document):
    validate(incoming); validate(current)
    overlay.require((incoming["id"], incoming["game_id"], incoming["baseline"], incoming["sources"]) ==
                    (current["id"], current["game_id"], current["baseline"], current["sources"]), "Response changed source identity or baseline")
    overlay.require({a["id"] for a in incoming["actions"]} == {a["id"] for a in current["actions"]}, "Response added or removed actions")
    originals = {a["id"]: a for a in current["actions"]}
    for a in incoming["actions"]:
        overlay.require(all(a[k] == originals[a["id"]][k] for k in ("output", "context", "bundle_id")), "Response changed a native binding or bundle")
    preview(incoming, document)
    return copy.deepcopy(incoming)
