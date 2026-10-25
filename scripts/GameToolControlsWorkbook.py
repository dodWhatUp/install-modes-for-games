"""Lossless intake of the supplied planning v2 contract, never a native import.

The bounded validator implements only the pinned schema's keyword subset, with
no remote refs or execution. The full original graph is retained. Projection to
the smaller app model requires exact/reviewed identities and cannot alter a
native output, recipe, source hash, authorization or runtime owner.
"""
from __future__ import annotations
import copy,hashlib,json,math,re
from pathlib import Path
import GameToolControlsPlanner as p
import GameToolKeymapDocument as maps
import GameToolOverlay as overlay
from game_keybind_ops.deps import strict_json

VERSION = "0.1.0"
SCHEMA = Path(__file__).resolve().parents[1] / "schemas/azeron-game-workbook-v2.schema.json"
SCHEMA_SHA = "0de8477defac24b6861fdb241cebca3fdcf7f2259a1a3b67d0780a0f98a25aaa"
FEATURES = {"action_priority_A20_UF_1", "scoped_rules", "unknown_not_zero", "contextual_routes", "evidence_by_field"}
COLLECTIONS = ("source_inventory", "evidence", "contexts", "actions", "bundles", "combinations", "groups", "layers", "routes", "rules", "assignments", "research_queue", "change_log")


def _check(value, schema, root, path="$", depth=0):
    overlay.require(depth < 48, "Schema reference depth exceeded")
    if "$ref" in schema:
        ref = schema["$ref"]
        overlay.require(ref.startswith("#/definitions/") and ref.count("/") == 2, "Only pinned local schema references are supported")
        return _check(value, root["definitions"][ref.split("/")[-1]], root, path, depth+1)
    if "const" in schema: overlay.require(type(value) is type(schema["const"]) and value == schema["const"], path + ": wrong constant")
    if "enum" in schema: overlay.require(any(type(value) is type(x) and value == x for x in schema["enum"]), path + ": unknown enum")
    types = schema.get("type", []); types = [types] if type(types) is str else types
    match = {"null": value is None, "boolean": type(value) is bool, "integer": type(value) is int,
             "number": type(value) in (int, float), "string": type(value) is str,
             "object": type(value) is dict, "array": type(value) is list}
    if types: overlay.require(any(match[t] for t in types), path + ": wrong type")
    if type(value) is dict:
        overlay.require(set(schema.get("required", ())) <= set(value), path + ": missing fields")
        props = schema.get("properties", {}); additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            if key in props: _check(child, props[key], root, path + "." + key, depth+1)
            elif additional is False: raise ValueError(path + ": unknown field " + key)
            elif type(additional) is dict: _check(child, additional, root, path + "." + key, depth+1)
    elif type(value) is list:
        if "minItems" in schema: overlay.require(len(value) >= schema["minItems"], path + ": too few items")
        if schema.get("uniqueItems"): overlay.require(len({maps.fingerprint(v) for v in value}) == len(value), path + ": duplicate items")
        if "items" in schema:
            for i, child in enumerate(value): _check(child, schema["items"], root, f"{path}[{i}]", depth+1)
    elif type(value) is str:
        overlay.require(len(value) >= schema.get("minLength", 0), path + ": text too short")
        if "pattern" in schema: overlay.require(re.search(schema["pattern"], value) is not None, path + ": invalid pattern")
    elif type(value) in (int, float):
        overlay.require(value >= schema.get("minimum", -math.inf) and value <= schema.get("maximum", math.inf), path + ": value outside range")


def validate(value):
    p.bounded_data(value); overlay.require(len(maps.encoded(value)) <= overlay.MAX_JSON, "Workbook exceeds 1 MiB")
    raw = SCHEMA.read_bytes(); overlay.require(hashlib.sha256(raw).hexdigest() == SCHEMA_SHA, "Workbook schema changed; review the new contract")
    schema = strict_json(raw); _check(value, schema, schema)
    overlay.require(value["owner"] == "dodWhatUp/install-modes-for-games", "Unexpected workbook owner")
    overlay.require(set(value["required_features"]) <= FEATURES, "Unknown required workbook feature; keep original read-only")
    ids = {}
    for name in COLLECTIONS:
        items = value[name]; ids[name] = {r["id"]: r for r in items}
        overlay.require(len(ids[name]) == len(items), "Duplicate " + name + " identity")
    def refs(items, collection):
        overlay.require(set(items) <= set(ids[collection]), "Unknown " + collection + " reference")
    def priority(score):
        calculated = p.priority(score["urgency_candidates"], score["frequency_candidates"])
        overlay.require(score["score_candidates"] == calculated["candidates"] and score["computed_priority"] == calculated["score"], "Stored A20 arithmetic differs from evidence candidates")
        refs(score["evidence_refs"], "evidence")
        if score["override_rule_id"] is not None: refs([score["override_rule_id"]], "rules")
    for name in COLLECTIONS:
        for row in value[name]: refs(row["evidence_refs"], "evidence")
    for row in value["source_inventory"]: refs(row["overrides_source_ids"], "source_inventory")
    for row in value["evidence"]: refs(row["context_ids"], "contexts")
    for row in value["contexts"]:
        if row["parent_context_id"] is not None: refs([row["parent_context_id"]], "contexts")
        refs(row["entry_action_ids"] + row["exit_action_ids"], "actions")
        refs(row["exclusive_with_context_ids"], "contexts")
    for a in value["actions"]:
        refs([a["context_id"]], "contexts")
        if a["bundle_id"] is not None: refs([a["bundle_id"]], "bundles")
        refs(a["group_ids"], "groups"); refs(a["requirements"]["required_combination_ids"], "combinations")
        for links in a["evidence_by_field"].values(): refs(links, "evidence")
        priority(a["priority"]); refs(a["usage"]["evidence_refs"], "evidence")
    for bundle in value["bundles"]:
        refs(bundle["member_action_ids"], "actions"); refs(bundle["context_ids"], "contexts")
        if bundle["split_rule_id"] is not None: refs([bundle["split_rule_id"]], "rules")
        for profile in bundle["context_profiles"]:
            refs([profile["context_id"]], "contexts"); refs(profile["applicable_member_action_ids"], "actions")
            overlay.require(set(profile["applicable_member_action_ids"]) <= set(bundle["member_action_ids"]), "Bundle context names a nonmember action")
            refs(profile["evidence_refs"] + profile["unique_binding_usage"]["evidence_refs"], "evidence"); priority(profile["priority"])
    for row in value["combinations"]:
        refs(row["action_ids"], "actions"); refs(row["context_ids"], "contexts"); refs(row["route_ids"], "routes")
    for row in value["groups"]:
        refs(row["member_action_ids"], "actions"); refs(row["reserved_route_ids"], "routes"); refs(row["exception_rule_ids"], "rules")
    for row in value["layers"]: refs(row["rank_context_ids"], "contexts")
    for route in value["routes"]:
        refs([route["layer_id"]], "layers"); refs(route["context_ids"], "contexts")
        if route["start_layer_id"] is not None: refs([route["start_layer_id"]], "layers")
        refs(route["held_route_ids"], "routes"); refs(route["candidate_alias_route_ids"], "routes"); refs(route["verified_alias_route_ids"], "routes")
    for row in value["assignments"]:
        refs(row["action_ids"], "actions"); refs(row["context_ids"], "contexts"); refs([row["route_id"]], "routes")
        refs(row["displaced_assignment_ids"], "assignments"); refs(row["affected_alias_route_ids"], "routes"); refs(row["unresolved_question_ids"], "research_queue")
    return value


def read(path, retain_to=None):
    raw = overlay.read(overlay.no_links(path)); value = validate(p.decode(raw))
    if retain_to is not None:
        directory = overlay.no_links(Path(retain_to)); directory.mkdir(parents=True, exist_ok=True)
        target = overlay.no_links(directory / (hashlib.sha256(raw).hexdigest() + ".json"))
        if target.exists(): overlay.require(target.read_bytes() == raw, "Original intake bytes differ")
        else:
            with target.open("xb") as out: out.write(raw)
    return value


def suggested_links(value, w):
    """Exact ID, or exact native command AND native context. No label similarity."""
    available = {a["id"]: a for a in w["actions"]}; result = {}
    source_fields = {}
    for source in w["sources"]:
        for field in source["snapshot"]["action_fields"]: source_fields[p.action_source_id(source, field)] = field
    for action in value["actions"]:
        if action["id"] in available: result[action["id"]] = action["id"]; continue
        matches = [ident for ident, f in source_fields.items() if action["native_command"] and
                   f["label"] == action["native_command"] and f["context"] == action["context_id"]]
        if len(matches) == 1: result[action["id"]] = matches[0]
    return result


def import_workbook(value, w, document, links=None, *, confirmed_game_id=None):
    validate(value); p.preview(w, document)
    overlay.require(value["game_identity"]["game_id"] in {None, w["game_id"]}, "Workbook belongs to another game")
    known_game = value["game_identity"]["game_id"] == w["game_id"] or confirmed_game_id == w["game_id"]
    links = (suggested_links(value, w) if known_game else {}) if links is None else links
    overlay.require(not links or known_game, "Explicitly confirm the target game before linking an unidentified workbook")
    overlay.require(type(links) is dict and len(set(links.values())) == len(links), "Ambiguous action identity links")
    originals = {a["id"]: a for a in value["actions"]}; result = copy.deepcopy(w); app = {a["id"]: a for a in result["actions"]}
    overlay.require(set(links) <= set(originals) and set(links.values()) <= set(app), "Unknown action link")
    projected = []
    for source_id, target_id in links.items():
        source = originals[source_id]; target = app[target_id]; score = source["priority"]
        target.update(label=source["label"][:240], meaning=source["meaning"] or "", categories=source["tags"][:32],
                      urgency=score["urgency_candidates"], frequency=score["frequency_candidates"],
                      needs_movement=source["requirements"]["movement_simultaneous"], user_priority_override=score["user_priority_override"],
                      override_reason=score["explanation"] or "Imported explicit planning override" if score["user_priority_override"] is not None else "")
        target["activation"] = {"repeat_press": "repeat"}.get(source["gesture"], source["gesture"])
        if target["activation"] not in p.ACTIVATIONS: target["activation"] = "unknown"
        target["evidence"] = list(dict.fromkeys(target["evidence"] + ["v2 evidence: " + x for x in source["evidence_refs"]]))[:32]
        result["extensions"].setdefault("requirements_by_action", {})[target_id] = copy.deepcopy(source["requirements"])
        projected.append(source_id)
    # Full rules, assignments, routes, citations and unknown extension data stay
    # in the original graph. Projection is additive; no route is adopted merely
    # because the external record called it accepted/applied/play-verified.
    result["extensions"]["workbook_v2"] = {"original": copy.deepcopy(value), "source_sha256": maps.fingerprint(value),
                                            "action_links": copy.deepcopy(links), "projection": "classifications_only",
                                            "confirmed_game_id": confirmed_game_id}
    p.validate(result)
    return result, {"projected_actions": projected, "unlinked_actions": sorted(set(originals)-set(links)),
                    "retained_collections": list(COLLECTIONS), "assignments_adopted": False,
                    "native_or_game_changes": False, "shared_rules_promoted": False}


def export_workbook(w):
    p.validate(w); record = w["extensions"].get("workbook_v2")
    overlay.require(type(record) is dict, "Import a planning v2 workbook first")
    value = copy.deepcopy(record["original"]); validate(value)
    overlay.require(maps.fingerprint(value) == record["source_sha256"], "Original v2 workbook changed")
    app = {a["id"]: a for a in w["actions"]}; original = {a["id"]: a for a in value["actions"]}
    for source, target in record["action_links"].items():
        a = app[target]; row = original[source]; computed = p.priority(a["urgency"], a["frequency"])
        row.update(label=a["label"], meaning=a["meaning"] or None, tags=copy.deepcopy(a["categories"]))
        row["priority"].update(urgency_candidates=a["urgency"], frequency_candidates=a["frequency"],
                              score_candidates=computed["candidates"], computed_priority=computed["score"],
                              user_priority_override=a["user_priority_override"], explanation=a["override_reason"] or row["priority"]["explanation"])
    value["extensions"]["game_tools_projection"] = {"workbook_sha256": maps.fingerprint(w),
        "planning_only": True, "proposed_routes": {a["id"]: a["proposed_route"] for a in w["actions"] if a["proposed_route"]}}
    return validate(value)


def assignment_preview(w, document):
    """Turn retained external assignments into reviewable app proposals only."""
    p.preview(w,document);record=w["extensions"].get("workbook_v2")
    overlay.require(type(record) is dict,"Import a planning v2 workbook first")
    value=record["original"];validate(value)
    overlay.require(maps.fingerprint(value)==record["source_sha256"],"Original v2 graph changed")
    routes={r["id"]:r for r in value["routes"]};links=record["action_links"]
    existing={r["id"]:r for r in p.routes(document)};candidate=copy.deepcopy(w);actions={a["id"]:a for a in candidate["actions"]}
    proposed={};unresolved=[]
    layer_links=w["extensions"].get("v2_layer_links",{});context_links=w["extensions"].get("v2_context_links",{})
    for assignment in value["assignments"]:
        if assignment["state"]=="superseded" or assignment["role"]!="primary":continue
        route=routes[assignment["route_id"]];layer=layer_links.get(route["layer_id"],route["layer_id"])
        if not all(a in links for a in assignment["action_ids"]):
            unresolved.append({"assignment_id":assignment["id"],"reason":"Exact action links required"});continue
        for original in assignment["action_ids"]:
            action=actions[links[original]];contexts=[context_links.get(c,c) for c in assignment["context_ids"]]
            context=action["overlay_context"] if action["overlay_context"] in contexts else contexts[0] if len(contexts)==1 else None
            identity=f'{layer}/{context}/{route["button_id"]}'
            if identity not in existing or route["output_display"]!=existing[identity]["output"]:
                unresolved.append({"assignment_id":assignment["id"],"reason":"Layer/context/output does not match an existing native route"});continue
            overlay.require(action["id"] not in proposed or proposed[action["id"]]==identity,"Divergent v2 assignments need reconciliation; timestamps do not choose a winner")
            proposed[action["id"]]=identity;action["proposed_route"]=identity;action["overlay_context"]=context
    checked=p.preview(candidate,document)
    return {"candidate":candidate,"proposed":proposed,"unresolved":unresolved,
            "blocked":[{"action_id":r["id"],"reasons":r["blocked"]} for r in checked["rows"] if r["blocked"]],
            "adopted_verification_claims":False,"native_or_game_changes":False}
