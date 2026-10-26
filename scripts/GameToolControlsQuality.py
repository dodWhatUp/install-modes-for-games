"""Computed, read-only mapping review over the existing workbook and map owners.

Optional ``extensions.mapping_quality_review`` is review evidence, never Apply
authority. Recorded completion booleans, runtime claims and physical PASS values
are deliberately ignored. The checker cannot prove current game/device behavior.
"""
from __future__ import annotations
import copy
import GameToolControlsPlanner as planner
import GameToolKeymapDocument as maps
import GameToolOverlay as overlay

VERSION = "0.1.0"
MAX_AUDIT_BYTES = 8 * 1024 * 1024
METHODS = {"device_adaptation", "game_binding_adaptation"}
POLICIES = {"legacy-combat-r2", "azeron-little-finger-20261026-r1"}
DISPOSITIONS = {"retain", "protected", "new_shortcut_candidate", "move_candidate",
                "context_only", "intentionally_unassigned", "blocked_unknown"}
EMPTY_LABELS = {"", "no binding", "no reviewed binding", "unassigned", "spare",
                "spare / unbound", "unused", "action unknown", "unknown", "modifier only"}


def _evidence(value):
    return isinstance(value, list) and bool(value) and all(isinstance(x, str) and x.strip() for x in value)


def _nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def _actionful(cell):
    labels = [cell.get("action", "").strip().casefold(), cell.get("display_action", "").strip().casefold()]
    return any(label not in EMPTY_LABELS for label in labels)


def audit(w, document, preview_report=None, *, review_record=None):
    """Return deterministic findings; do not read devices/files or mutate inputs.

    Review fields: schema_version, pins(map_sha256/keymap_revision/source_revisions),
    method(selected/reason), ergonomic_policy(revision), requirements, button_decisions,
    primary_routes and combination_reviews. Unknown optional review fields survive
    the workbook owner but cannot increase computed completion here.
    """
    planner.validate(w); maps.validate(document)
    overlay.require(w["game_id"] == document["game_id"], "Quality audit needs the same game")
    record = review_record if review_record is not None else w["extensions"].get("mapping_quality_review", {})
    planner.bounded_data(record)
    overlay.require(isinstance(record, dict), "Mapping quality review must be an object")
    overlay.require(len(maps.encoded(record)) <= overlay.MAX_JSON, "Mapping review record exceeds 1 MiB")
    findings = []
    def finding(code, message, *, severity="review", routes=None, actions=None):
        findings.append({"code": code, "severity": severity, "message": message,
                         "routes": routes or [], "actions": actions or []})
    expected = {"map_sha256": maps.fingerprint(document), "keymap_revision": document["keymap_revision"],
                "source_revisions": [s["revision"] for s in w["sources"]]}
    if review_record is not None:
        expected["workbook_sha256"] = maps.fingerprint(w)
    baseline_current = (w["baseline"]["map_sha256"] == expected["map_sha256"] and
                        w["baseline"]["keymap_revision"] == expected["keymap_revision"])
    pins_current = record.get("schema_version") == 1 and record.get("pins") == expected
    if not baseline_current or not pins_current:
        finding("stale_or_missing_review_pins", "Review decisions need the current map, native contract and binding-source pins.", severity="blocker")
    method = record.get("method", {})
    method_selected = isinstance(method, dict) and isinstance(method.get("selected"), str) and method.get("selected") in METHODS and _nonblank(method.get("reason"))
    if not method_selected:
        finding("method_not_selected", "Select device adaptation or fixed-device/game-binding adaptation and record why.", severity="blocker")
    policy = record.get("ergonomic_policy", {})
    policy_revision = policy.get("revision") if isinstance(policy, dict) else None
    policy_known = isinstance(policy_revision, str) and policy_revision in POLICIES
    if not policy_known:
        finding("ergonomic_policy_unselected", "Choose the reconciled legacy or later little-finger policy explicitly.", severity="blocker")
    policy_matches = policy_known and w["baseline"]["rules_revision"] == (planner.RULES if policy_revision == "legacy-combat-r2" else planner.LITTLE_FINGER_RULES)
    if policy_known and not policy_matches:
        finding("ergonomic_policy_baseline_mismatch", "The review policy and workbook rules revision differ; reconcile the candidate explicitly.", severity="blocker")

    # Use the saved document's actual layer entry, never assume #2 is the holder.
    routes = planner.routes(document); indexed = {r["id"]: r for r in routes}
    cells = {f'{m["layer"]}/{m["context"]}/{c["button_id"]}': c for m in document["maps"] for c in m["cells"]}
    button_index = {b["id"]: b for b in document["buttons"]}
    for route in routes:
        route["available"] = not (route["holder"] is not None and route["holder_finger"] == route["finger"])
    # Hidden dedicated Overlay and movement controls need explicit disposition.
    for mapping in document["maps"]:
        for bid, role in ((19, "Dedicated Overlay hold"), (24, "Movement stick")):
            identity = f'{mapping["layer"]}/{mapping["context"]}/{bid}'
            indexed[identity] = {"id": identity, "layer": mapping["layer"], "context": mapping["context"],
                                 "button": bid, "hidden": True, "role": role, "available": False}
    decisions = record.get("button_decisions", [])
    if not isinstance(decisions, list): decisions = []
    decision_index = {}; malformed_decisions = []
    for row in decisions:
        if (not isinstance(row, dict) or not isinstance(row.get("route_id"), str) or row.get("route_id") not in indexed or row.get("route_id") in decision_index
                or not isinstance(row.get("disposition"), str) or row.get("disposition") not in DISPOSITIONS or not _nonblank(row.get("reason")) or not _evidence(row.get("evidence"))):
            malformed_decisions.append(row.get("route_id") if isinstance(row, dict) else None); continue
        decision_index[row["route_id"]] = row
    if malformed_decisions:
        finding("invalid_button_decisions", "Button decisions need a unique current route, disposition, reason and evidence.", severity="blocker")
    missing_decisions = sorted(set(indexed) - set(decision_index))
    if missing_decisions:
        finding("physical_controls_unreviewed", "Every visible position and hidden #19/#24 needs an explicit decision in each layer/context.", routes=missing_decisions)

    action_by_id = {a["id"]: a for a in w["actions"]}
    source_ids = {planner.action_source_id(source, field) for source in w["sources"] for field in source["snapshot"].get("action_fields", [])}
    missing_source_actions = sorted(source_ids - set(action_by_id))
    if missing_source_actions:
        finding("missing_saved_source_actions", "Saved-source action rows were omitted from the current workbook; existing labels cannot substitute for their inventory.", severity="blocker", actions=missing_source_actions)
    prior_review = w["extensions"].get("complete_accessibility_review", {})
    prior_coverage = prior_review.get("coverage", {}) if isinstance(prior_review, dict) else {}
    external_ui = prior_coverage.get("ui_only_actions_outside_parser") if isinstance(prior_coverage, dict) else None
    if not isinstance(external_ui, list): external_ui = None
    primary = record.get("primary_routes", {})
    if not isinstance(primary, dict): primary = {}
    valid_primary = {}; unresolved_primary = []
    for aid, rid in primary.items():
        if not isinstance(rid, str):
            unresolved_primary.append(aid); continue
        action = action_by_id.get(aid); route = indexed.get(rid)
        if (action is None or route is None or route.get("hidden") or route["context"] != action["overlay_context"]
                or not route["available"] or route["output"].startswith("LAYER:") or route["output"] == "UNASSIGNED"):
            unresolved_primary.append(aid); continue
        desired = indexed.get(action["proposed_route"], {}).get("output", action["output"])
        if planner.canonical_output(w, route["output"]) != planner.canonical_output(w, desired):
            unresolved_primary.append(aid); continue
        check = planner.route_review(action, route, lambda a, b: planner.canonical_output(w, a) == planner.canonical_output(w, b),
                                     protected_buttons=planner.protected_buttons(w, route))
        if check["blocked"] or planner.requirements_review(w, action, route):
            unresolved_primary.append(aid); continue
        valid_primary[aid] = rid
    if unresolved_primary:
        finding("invalid_primary_routes", "Primary routes must match the selected output/context and leave the holder finger available.", severity="blocker", actions=sorted(unresolved_primary))
    missing_primary = [a["id"] for a in w["actions"] if a["overlay_context"] is not None and a["id"] not in valid_primary]
    if missing_primary:
        finding("primary_routes_unreviewed", "Output aliases do not establish the intended ergonomic route; identify a primary route or explain the unsupported action.", actions=missing_primary)

    source_links = {}
    for action in w["actions"]:
        desired = indexed.get(action["proposed_route"], {}).get("output", action["output"])
        source_links.setdefault((action["overlay_context"], planner.canonical_output(w, desired)), []).append(action)
    inventory = []; unused = []; held_unavailable = []; display_reviews = []; unverified_labels = []
    for identity, route in indexed.items():
        if route.get("hidden"):
            inventory.append({"route_id": identity, "button": route["button"], "state": "protected_hidden", "reviewed": identity in decision_index}); continue
        cell = cells[identity]; decision = decision_index.get(identity)
        output = route["output"]
        if route["button"] == route["holder"]:
            state = "protected_layer_holder"
        elif not route["available"]:
            state = "holder_finger_unavailable"; held_unavailable.append(identity)
        elif output.startswith("LAYER:"): state = "layer_selector"
        elif output == "F24": state = "protected_overlay"
        elif output == "UNASSIGNED" or not _actionful(cell): state = "no_game_action"
        else: state = "action_label_present"
        reserved = policy_revision == "azeron-little-finger-20261026-r1" and route["button"] == 37
        if reserved:
            requested = bool(decision and decision.get("user_requested") is True and _nonblank(decision.get("origin")))
            if output != "UNASSIGNED" and not requested:
                finding("reserved_little_bottom_used", "Little-finger #37 stays empty unless the user explicitly requests an exception.", severity="blocker", routes=[identity])
            elif not requested: state = "user_reserved_empty"
        intentional = bool(decision and decision["disposition"] == "intentionally_unassigned")
        accessible = route["row"] in (2, 4) or button_index[route["button"]].get("ergonomics", {}).get("comfort", 0) >= 4
        if state == "no_game_action" and accessible and not reserved:
            unused.append({"route_id": identity, "row": route["row"], "intentional": intentional, "reason": decision.get("reason") if decision else None})
        linked = source_links.get((route["context"], planner.canonical_output(w, output)), [])
        bound = [a for a in linked if a["id"] in source_ids]
        semantic = [a for a in bound if a["meaning"] and a["activation"] != "unknown" and a["needs_movement"] is not None]
        if state == "action_label_present" and not semantic: unverified_labels.append(identity)
        inventory.append({"route_id": identity, "button": route["button"], "state": state,
                          "emits_input": output != "UNASSIGNED", "action_label_present": _actionful(cell),
                          "saved_action_ids": [a["id"] for a in bound], "semantics_reviewed_action_ids": [a["id"] for a in semantic],
                          "reviewed": identity in decision_index, "intentional_empty": intentional})
        if route["layer"] == "BASIC" and route["context"] == "gameplay" and "/" in cell["action"] and cell["display_action"]:
            visible = (cell["display_action"] + " " + cell.get("comment", {}).get("text", "")).casefold()
            missing = [branch.strip() for branch in cell["action"].split("/") if branch.strip() and branch.strip().casefold() not in visible]
            if missing:
                display_reviews.append({"route_id": identity, "branches_needing_visual_review": missing, "visible_text": cell["display_action"],
                                        "claim": "Heuristic abbreviation check; render all selected views to confirm meaning"})
    if display_reviews:
        finding("contextual_branch_display_review", "A shortened BASIC gameplay label may hide a contextual or held action branch; review visible text and comments in the actual views.", routes=[r["route_id"] for r in display_reviews])
    if unverified_labels:
        finding("action_labels_not_semantically_verified", "A visible action label is insufficient coverage without a linked saved action and reviewed meaning/activation/movement requirements.", routes=unverified_labels)
    # New little-finger preference is scoped by revision, not applied to old maps.
    if policy_revision == "azeron-little-finger-20261026-r1":
        for mapping in document["maps"]:
            if mapping["layer"] != "BASIC": continue
            for bid, target in ((1, "WEAPONS"), (3, "MENUS"), (36, "TOOLS")):
                rid = f'BASIC/{mapping["context"]}/{bid}'
                if cells[rid]["output"] != "LAYER:" + target:
                    finding("little_finger_layer_policy", f"Accepted layout policy places {target} on #{bid}; current output differs.", severity="blocker", routes=[rid])
            rid = f'BASIC/{mapping["context"]}/2'
            if cells[rid]["output"].startswith("LAYER:"):
                finding("little_finger_infrequent_role", "#2 is an infrequent action in the later policy, rather than the default held layer.", severity="blocker", routes=[rid])
            linked = source_links.get((mapping["context"], planner.canonical_output(w, cells[rid]["output"])), [])
            demanding = [a["id"] for a in linked if any(f >= 3 for f in a["frequency"]) or any(u >= 4 for u in a["urgency"])]
            if demanding:
                finding("little_finger_infrequent_role", "#2 is reserved for an infrequent, non-urgent action; current action demand conflicts with that role.", severity="blocker", routes=[rid], actions=demanding)
            rid = f'BASIC/{mapping["context"]}/4'
            if cells[rid]["output"] != "UNASSIGNED" and not cells[rid]["output"].startswith("LAYER:"):
                finding("little_finger_optional_layer_role", "#4 is an optional combat/overflow layer position; an empty position is allowed without requiring another layer.", severity="blocker", routes=[rid])

    demand_gaps = []; semantics_missing = []; frequency_unknown = []
    for action in w["actions"]:
        aid = action["id"]; score = planner.priority(action["urgency"], action["frequency"])
        if not action["frequency"]: frequency_unknown.append(aid)
        if not action["meaning"] or action["activation"] == "unknown" or action["needs_movement"] is None or action["overlay_context"] is None:
            semantics_missing.append(aid)
        route = indexed.get(valid_primary.get(aid, ""))
        demand_floor = action["user_priority_override"] if action["user_priority_override"] is not None else score["range"][0] if score["range"] else None
        if route and demand_floor is not None and demand_floor >= 13 and (route["holder"] is not None or route["row"] in (1, 5)):
            alternatives = [r["route_id"] for r in unused if indexed[r["route_id"]]["context"] == action["overlay_context"]]
            if alternatives:
                demand_gaps.append({"action_id": aid, "priority": score, "user_priority_override": action["user_priority_override"], "primary_route": route["id"], "accessible_unused": alternatives,
                                    "claim": "Review candidate only; displacement, native capabilities and comfort remain unverified"})
    if demand_gaps:
        finding("important_action_access_gap", "Important actions use an indirect or lower-preference primary route while accessible positions lack a game action.", actions=[r["action_id"] for r in demand_gaps])
    unused_open = []
    for row in unused:
        comparison = decision_index.get(row["route_id"], {}).get("comparison", {})
        ids = comparison.get("action_ids", []) if isinstance(comparison, dict) else []
        required = {g["action_id"] for g in demand_gaps if row["route_id"] in g["accessible_unused"]}
        compared = isinstance(ids, list) and all(isinstance(aid, str) and aid in action_by_id for aid in ids)
        complete = bool(compared and required <= set(ids) and comparison.get("result") in ("retain_empty", "new_shortcut_candidate")
                        and _nonblank(comparison.get("reason")) and _evidence(comparison.get("evidence")))
        row["comparison_recorded"] = complete
        if not complete: unused_open.append(row["route_id"])
    if unused_open:
        finding("accessible_unused_positions", "Accessible positions without a game action need an evidenced comparison with important indirect or awkward actions; declaring a spare alone does not close the review.", routes=unused_open)

    combinations = record.get("combination_reviews", [])
    if not isinstance(combinations, list): combinations = []
    combination_index = {}
    for row in combinations:
        if not isinstance(row, dict): continue
        ids = row.get("action_ids", [])
        if isinstance(ids, list) and len(ids) == 2 and all(isinstance(x, str) for x in ids) and len(set(ids)) == 2 and set(ids) <= set(action_by_id) and row.get("kind") in ("simultaneous", "sequence"):
            combination_index[(tuple(sorted(ids)), row.get("kind"))] = row
    pairs = {tuple(sorted((a["id"], other))) for a in w["actions"] for other in a["simultaneous"]}
    combination_results = []
    for pair in sorted(pairs):
        left, right = [indexed.get(valid_primary.get(aid, "")) for aid in pair]
        row = combination_index.get((pair, "simultaneous"), {})
        reviewed = row.get("status") == "reviewed" and _evidence(row.get("evidence"))
        same_finger = bool(left["finger"] == right["finger"] or left["holder_finger"] == right["finger"] or right["holder_finger"] == left["finger"]) if left and right else None
        combination_results.append({"action_ids": list(pair), "kind": "simultaneous", "same_finger_or_holder": same_finger,
                                    "geometry_status": "primary_routes_known" if left and right else "unknown_primary_routes",
                                    "review_recorded": reviewed, "physical_verified": False})
        if not reviewed or same_finger:
            finding("combination_needs_review", "Required overlap needs primary-route and hold/finger review; geometry alone cannot establish physical success or impossibility.", actions=list(pair))

    requirement_results = []; requirements = record.get("requirements", [])
    if not isinstance(requirements, list): requirements = []
    seen = set()
    for row in requirements:
        if not isinstance(row, dict): continue
        identity = row.get("id"); complete = bool(isinstance(identity, str) and identity and identity not in seen and
             _nonblank(row.get("origin")) and _nonblank(row.get("expectation")) and row.get("acceptance") == "accepted" and
             row.get("evidence_status") in ("configuration_verified", "user_reported", "source_reviewed") and
             row.get("status") == "implemented" and _evidence(row.get("evidence")))
        if isinstance(identity, str): seen.add(identity)
        requirement_results.append({"id": identity, "status": row.get("status", "pending"), "acceptance": row.get("acceptance", "pending"),
                                    "evidence_status": row.get("evidence_status", "unverified"), "evidence_recorded": _evidence(row.get("evidence")),
                                    "record_complete": complete, "external_claims_verified": False})
    requirements_complete = bool(requirement_results) and all(r["record_complete"] for r in requirement_results) and pins_current and baseline_current and method_selected and policy_matches and not missing_source_actions
    if not requirements_complete:
        finding("requirements_not_closed", "Each user requirement needs an origin, testable expectation, explicit disposition and evidence; deferred or omitted work remains open.", severity="blocker")

    # Reuse the existing compatibility owner. A supplied preview is accepted
    # only when it equals a fresh pure preview; external booleans never win.
    compatibility = "unverified"; compatibility_blocked = None
    if baseline_current:
        fresh = planner.preview(w, document)
        if preview_report is not None:
            overlay.require(preview_report == fresh, "Quality preview differs from the current workbook")
        compatibility_blocked = sum(bool(r["blocked"]) for r in fresh["rows"])
        compatibility = "blocked" if compatibility_blocked else "no_proposed_route_blocks"
        if compatibility_blocked:
            finding("existing_planner_blocks", "The existing planner reports blocked proposals. Later ergonomic preferences do not silently bypass its versioned native/apply constraints.", severity="blocker")
    result = {"kind": "game_controls_quality_audit", "schema_version": 1,
        "game_id": w["game_id"], "workbook_sha256": maps.fingerprint(w), "pins": expected,
        "review_record_source": "standalone_pinned_review" if review_record is not None else "workbook_extension",
        "review_record_sha256": maps.fingerprint(record),
        "selected_method": method.get("selected") if method_selected else None, "ergonomic_policy": policy_revision,
        "read_only": True, "ready_for_play": False, "runtime_acceptance": "external_verification_required",
        "dimensions": {"review_pins_current": baseline_current and pins_current, "method_selected": method_selected,
            "ergonomic_policy_matches_baseline": policy_matches,
            "ergonomic_roles_match": bool(policy_known and policy_matches and not any(f["code"] in {
                "reserved_little_bottom_used", "little_finger_layer_policy", "little_finger_infrequent_role", "little_finger_optional_layer_role"} for f in findings)),
            "physical_decisions_complete": not missing_decisions and not malformed_decisions,
            "semantics_complete": not semantics_missing, "unknown_frequency_count": len(frequency_unknown),
            "primary_routes_complete": not missing_primary and not unresolved_primary,
            "requirements_records_complete": requirements_complete, "compatibility": compatibility,
            "saved_source_action_coverage_complete": bool(w["sources"]) and not missing_source_actions,
            "compatibility_blocked_rows": compatibility_blocked, "physical_accepted": False},
        "coverage": {"visible_routes": len(routes), "hidden_protected_routes": len(indexed)-len(routes),
            "reviewed_routes": len(decision_index), "unreviewed_routes": len(missing_decisions),
            "accessible_unused": len(unused), "holder_finger_unavailable": len(held_unavailable),
            "unverified_action_labels": len(unverified_labels),
            "saved_action_linked_positions": sum(bool(r.get("saved_action_ids")) for r in inventory),
            "semantics_reviewed_positions": sum(bool(r.get("semantics_reviewed_action_ids")) for r in inventory),
            "expected_saved_source_actions": len(source_ids), "missing_saved_source_actions": len(missing_source_actions),
            "external_ui_actions_recorded": len(external_ui) if external_ui is not None else None},
        "button_inventory": inventory, "accessible_unused": unused, "demand_gaps": demand_gaps,
        "display_branch_review": display_reviews,
        "missing_saved_source_actions": missing_source_actions,
        "external_ui_inventory": {"status": "recorded_not_independently_verified" if external_ui is not None else "unknown_not_counted",
            "actions": copy.deepcopy(external_ui), "included_in_saved_source_action_count": False,
            "saved_source_proves_all_game_actions": False},
        "requirements": requirement_results, "combinations": combination_results, "findings": findings,
        "limitations": ["Action text is a display claim; effective source precedence and runtime behavior require separate evidence.",
            "Review evidence locators and historical acceptance are recorded, not independently authenticated by this pure checker.",
            "Azeron geometry applies only to this validated 29-cell document; controller/Vader drafts require their own inventory and geometry review."]}
    overlay.require(len(maps.encoded(result)) <= MAX_AUDIT_BYTES, "Quality audit exceeds the bounded 8 MiB report limit")
    return result


def compact(report):
    """Keep exported packet additions bounded; full inventory is available via audit."""
    result = copy.deepcopy({key: report[key] for key in ("kind", "schema_version", "game_id", "workbook_sha256", "pins", "review_record_source", "review_record_sha256",
        "selected_method", "ergonomic_policy", "read_only", "ready_for_play", "runtime_acceptance", "dimensions", "coverage", "findings", "limitations")})
    groups = {}
    for item in result["findings"]:
        identity = (item["code"], item["severity"], item["message"])
        group = groups.setdefault(identity, {"code": item["code"], "severity": item["severity"], "message": item["message"],
                                             "occurrences": 0, "routes": set(), "actions": set()})
        group["occurrences"] += 1
        for key in ("routes", "actions"): group[key].update(item[key])
    result["findings"] = []
    for group in groups.values():
        for key in ("routes", "actions"):
            values = sorted(group[key]); group[key + "_total"] = len(values); group[key] = values[:8]
        result["findings"].append(group)
    return result
