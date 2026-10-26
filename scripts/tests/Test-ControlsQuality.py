"""Meaningful review omissions, source pins and versioned ergonomic policies."""
import copy, importlib.util, pathlib, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
import GameToolControlsPlanner as p
import GameToolControlsQuality as quality
import GameToolKeymapDocument as maps
spec = importlib.util.spec_from_file_location("planner_fixture", ROOT/"tests/Test-ControlsPlanner.py")
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.doc = fixture.document(); self.w = p.new_workbook(self.doc, rules_revision=p.RULES)

    def review(self, policy="legacy-combat-r2"):
        record = {"schema_version": 1, "pins": {"map_sha256": maps.fingerprint(self.doc),
            "keymap_revision": self.doc["keymap_revision"], "source_revisions": []},
            "method": {"selected": "device_adaptation", "reason": "Retain current game inputs"},
            "ergonomic_policy": {"revision": policy}, "requirements": [], "button_decisions": [],
            "primary_routes": {}, "combination_reviews": []}
        self.w["extensions"]["mapping_quality_review"] = record
        return record

    def codes(self, report): return {f["code"] for f in report["findings"]}

    def cell(self, layer, bid): return next(c for c in self.doc["maps"][layer]["cells"] if c["button_id"] == bid)

    def reseed(self, revision=p.RULES): self.w = p.new_workbook(self.doc, rules_revision=revision)

    def test_completion_booleans_cannot_establish_quality_or_play_readiness(self):
        self.w["extensions"]["complete_accessibility_review"] = {"completion_axes": {"physical_accepted": True, "runtime_effective": True}, "status": "complete"}
        result = quality.audit(self.w, self.doc)
        self.assertFalse(result["ready_for_play"]); self.assertFalse(result["dimensions"]["physical_accepted"])
        self.assertIn("physical_controls_unreviewed", self.codes(result)); self.assertIn("requirements_not_closed", self.codes(result))

    def test_ignored_and_deferred_requirements_remain_open(self):
        record = self.review(); record["requirements"] = [{"id": "do-what-user-requested", "origin": "user request",
            "expectation": "Every accessible position reviewed", "status": "deferred", "acceptance": "accepted",
            "evidence_status": "source_reviewed", "evidence": ["test receipt"]}]
        result = quality.audit(self.w, self.doc)
        self.assertFalse(result["dimensions"]["requirements_records_complete"])
        record["requirements"][0]["status"] = "implemented"
        self.assertTrue(quality.audit(self.w, self.doc)["dimensions"]["requirements_records_complete"])
        self.assertFalse(quality.audit(self.w, self.doc)["requirements"][0]["external_claims_verified"])

    def test_stale_review_pin_is_reported_not_trusted(self):
        self.review()["pins"]["map_sha256"] = "f"*64
        self.assertIn("stale_or_missing_review_pins", self.codes(quality.audit(self.w, self.doc)))

    def test_spare_output_and_modifier_do_not_count_as_game_actions(self):
        self.cell(0, 11).update(action="No binding", display_action="Spare / unbound")
        self.cell(0, 3).update(output="Alt", action="Modifier only", display_action="Modifier only")
        self.reseed(); result = quality.audit(self.w, self.doc)
        rows = {r["route_id"]: r for r in result["button_inventory"]}
        self.assertTrue(rows["BASIC/gameplay/11"]["emits_input"])
        self.assertEqual(rows["BASIC/gameplay/11"]["state"], "no_game_action")
        self.assertEqual(rows["BASIC/gameplay/3"]["state"], "no_game_action")
        self.assertEqual(rows["BASIC/gameplay/2"]["state"], "layer_selector")

    def test_held_finger_positions_are_unavailable_not_accessible_gaps(self):
        result = quality.audit(self.w, self.doc)
        rows = {r["route_id"]: r for r in result["button_inventory"]}
        self.assertEqual(rows["WEAPONS/gameplay/3"]["state"], "holder_finger_unavailable")
        self.assertNotIn("WEAPONS/gameplay/3", [r["route_id"] for r in result["accessible_unused"]])

    def test_high_urgency_unknown_frequency_still_has_access_need_range(self):
        self.cell(0, 11).update(action="No binding", display_action="No binding")
        self.reseed(); record = self.review()
        action = next(a for a in self.w["actions"] if a["output"] == "1")
        action.update(meaning="Rare emergency selection", activation="select", needs_movement=True, urgency=[5], frequency=[])
        record["primary_routes"][action["id"]] = "WEAPONS/gameplay/7"
        result = quality.audit(self.w, self.doc)
        self.assertEqual(result["demand_gaps"][0]["priority"]["range"], [17, 20])
        self.assertIn("important_action_access_gap", self.codes(result))

    def test_aliases_do_not_silently_choose_primary_route(self):
        record = self.review(); action = next(a for a in self.w["actions"] if a["output"] == "K")
        result = quality.audit(self.w, self.doc)
        self.assertFalse(result["dimensions"]["primary_routes_complete"])
        record["primary_routes"][action["id"]] = "WEAPONS/gameplay/23"
        self.assertNotIn(action["id"], next(f["actions"] for f in quality.audit(self.w, self.doc)["findings"] if f["code"] == "primary_routes_unreviewed"))

    def test_same_finger_review_is_not_physical_pass_or_impossible(self):
        record = self.review(); a = next(x for x in self.w["actions"] if x["output"] == "J"); b = next(x for x in self.w["actions"] if x["output"] == "Ctrl")
        a["simultaneous"] = [b["id"]]
        record["primary_routes"].update({a["id"]: "BASIC/gameplay/6", b["id"]: "BASIC/gameplay/5"})
        record["combination_reviews"] = [{"action_ids": [a["id"], b["id"]], "kind": "simultaneous", "status": "reviewed", "evidence": ["User historical statement"], "physical_verified": True}]
        row = quality.audit(self.w, self.doc)["combinations"][0]
        self.assertTrue(row["same_finger_or_holder"]); self.assertFalse(row["physical_verified"])

    def test_hidden_overlay_and_stick_are_in_review_inventory(self):
        result = quality.audit(self.w, self.doc)
        self.assertEqual(result["coverage"]["visible_routes"], 58)
        self.assertEqual(result["coverage"]["hidden_protected_routes"], 4)

    def test_new_little_finger_policy_is_opt_in_and_bottom_reserved(self):
        record = self.review("azeron-little-finger-20261026-r1")
        self.assertIn("little_finger_layer_policy", self.codes(quality.audit(self.w, self.doc)))
        self.cell(0, 37).update(output="M", action="Combat shortcut")
        self.reseed(p.LITTLE_FINGER_RULES); record = self.review("azeron-little-finger-20261026-r1")
        self.assertIn("reserved_little_bottom_used", self.codes(quality.audit(self.w, self.doc)))
        record["button_decisions"].append({"route_id": "BASIC/gameplay/37", "disposition": "retain", "reason": "Explicit exception",
            "evidence": ["Direct user request"], "user_requested": True, "origin": "User specifically requested this position"})
        self.assertNotIn("reserved_little_bottom_used", self.codes(quality.audit(self.w, self.doc)))

    def test_vader_draft_cannot_be_claimed_as_azeron_geometry(self):
        with self.assertRaises(ValueError): quality.audit(self.w, {"kind": "controller_game_keymap_draft"})

    def test_export_adds_compact_quality_without_mutation(self):
        before = copy.deepcopy(self.w); packet = p.export_packet(self.w, self.doc)
        self.assertIn("quality_audit", packet); self.assertNotIn("button_inventory", packet["quality_audit"])
        self.assertEqual(self.w, before); self.assertFalse(packet["quality_audit"]["ready_for_play"])

    def test_stale_or_fabricated_preview_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "preview differs"):
            quality.audit(self.w, self.doc, {"ready": True})

    def test_reserved_bottom_cannot_emit_spare_key(self):
        self.cell(0, 37).update(output="M", action="Spare", display_action="Spare / unbound")
        self.reseed(p.LITTLE_FINGER_RULES); self.review("azeron-little-finger-20261026-r1")
        self.assertIn("reserved_little_bottom_used", self.codes(quality.audit(self.w, self.doc)))

    def test_unknown_combination_geometry_is_null_not_false(self):
        a, b = self.w["actions"][:2]; a["simultaneous"] = [b["id"]]
        row = quality.audit(self.w, self.doc)["combinations"][0]
        self.assertIsNone(row["same_finger_or_holder"]); self.assertEqual(row["geometry_status"], "unknown_primary_routes")

    def test_held_layer_release_owner_is_protected_separately(self):
        rows = {r["route_id"]: r for r in quality.audit(self.w, self.doc)["button_inventory"]}
        self.assertEqual(rows["WEAPONS/gameplay/2"]["state"], "protected_layer_holder")

    def test_shortened_bundle_branch_requires_visible_review(self):
        self.cell(0, 6).update(action="Use / Spear", display_action="Use")
        self.reseed(); report = quality.audit(self.w, self.doc)
        self.assertIn("contextual_branch_display_review", self.codes(report))
        self.cell(0, 6)["comment"] = {"text": "Spear", "color": "#FFFFFF"}
        self.reseed(); self.assertNotIn("contextual_branch_display_review", self.codes(quality.audit(self.w, self.doc)))

    def test_declared_spare_needs_evidenced_comparison(self):
        self.cell(0, 11).update(action="No binding", display_action="Spare")
        self.reseed(); record = self.review(); decision = {"route_id": "BASIC/gameplay/11", "disposition": "intentionally_unassigned",
            "reason": "No supported useful action", "evidence": ["Action review"]}
        record["button_decisions"] = [decision]
        self.assertFalse(next(r for r in quality.audit(self.w, self.doc)["accessible_unused"] if r["route_id"] == decision["route_id"])["comparison_recorded"])
        decision["comparison"] = {"action_ids": [], "result": "retain_empty", "reason": "No classified indirect demand in this fixture", "evidence": ["Bounded fixture comparison"]}
        self.assertTrue(next(r for r in quality.audit(self.w, self.doc)["accessible_unused"] if r["route_id"] == decision["route_id"])["comparison_recorded"])

    def test_thumb_movement_route_cannot_be_accepted_as_primary(self):
        record = self.review(); action = next(a for a in self.w["actions"] if a["output"] == "K")
        action["needs_movement"] = True; record["primary_routes"][action["id"]] = "WEAPONS/gameplay/23"
        report = quality.audit(self.w, self.doc)
        self.assertIn(action["id"], next(f["actions"] for f in report["findings"] if f["code"] == "invalid_primary_routes"))

    def test_unknown_layer_entry_cannot_be_primary(self):
        self.doc["maps"][1]["layer"] = "UNKNOWNLAYER"; self.reseed()
        record = self.review(); action = next(a for a in self.w["actions"] if a["output"] == "1")
        record["primary_routes"][action["id"]] = "UNKNOWNLAYER/gameplay/7"
        self.assertIn("invalid_primary_routes", self.codes(quality.audit(self.w, self.doc)))

    def test_dropped_source_action_is_found_and_ui_inventory_is_separate(self):
        fields = [{"id": a["id"], "label": a["label"], "context": a["context"], "key": a["output"], "bundle": a["bundle_id"]} for a in self.w["actions"]]
        snapshot = {"game_id": self.w["game_id"], "action_fields": fields}
        source = {"kind": "instance", "id": "fixture-effective", "snapshot": snapshot, "revision": maps.fingerprint(snapshot)}
        for action, field in zip(self.w["actions"], fields): action["id"] = p.action_source_id(source, field)
        self.w["sources"] = [source]
        self.w["extensions"]["complete_accessibility_review"] = {"coverage": {"ui_only_actions_outside_parser": ["UI-only selection"]}}
        report = quality.audit(self.w, self.doc)
        self.assertTrue(report["dimensions"]["saved_source_action_coverage_complete"])
        removed = self.w["actions"].pop()
        report = quality.audit(self.w, self.doc)
        self.assertEqual(report["missing_saved_source_actions"], [removed["id"]])
        self.assertFalse(report["dimensions"]["saved_source_action_coverage_complete"])
        self.assertEqual(report["coverage"]["external_ui_actions_recorded"], 1)
        self.assertFalse(report["external_ui_inventory"]["included_in_saved_source_action_count"])

    def test_compact_findings_preserve_totals_without_large_route_arrays(self):
        report = quality.audit(self.w, self.doc); compact = quality.compact(report)
        finding = next(f for f in compact["findings"] if f["code"] == "physical_controls_unreviewed")
        self.assertEqual(finding["routes_total"], 62); self.assertEqual(len(finding["routes"]), 8)

    def test_external_review_is_pinned_to_master_and_does_not_mutate_it(self):
        record = copy.deepcopy(self.review()); self.w["extensions"].pop("mapping_quality_review")
        record["pins"]["workbook_sha256"] = maps.fingerprint(self.w)
        before = copy.deepcopy(self.w); report = quality.audit(self.w, self.doc, review_record=record)
        self.assertEqual(report["review_record_source"], "standalone_pinned_review")
        self.assertTrue(report["dimensions"]["review_pins_current"]); self.assertEqual(self.w, before)
        self.w["actions"][0]["meaning"] = "Later researched action meaning"
        stale = quality.audit(self.w, self.doc, review_record=record)
        self.assertFalse(stale["dimensions"]["review_pins_current"]); self.assertFalse(stale["ready_for_play"])

    def test_computed_roles_dimension_catches_urgent_little_finger_action(self):
        for bid, output in ((1, "LAYER:WEAPONS"), (2, "B"), (3, "LAYER:MENUS"), (4, "UNASSIGNED"), (36, "LAYER:TOOLS"), (37, "UNASSIGNED")):
            self.cell(0, bid).update(output=output, action="Reviewed role")
        self.reseed(p.LITTLE_FINGER_RULES); self.review("azeron-little-finger-20261026-r1")
        self.assertTrue(quality.audit(self.w, self.doc)["dimensions"]["ergonomic_roles_match"])
        action = next(a for a in self.w["actions"] if a["output"] == "B")
        action.update(urgency=[5], frequency=[1])
        self.assertFalse(quality.audit(self.w, self.doc)["dimensions"]["ergonomic_roles_match"])

    def test_large_workbook_fallback_preserves_every_action_and_source(self):
        # Repeated private review text represents a retained larger research
        # workbook; no proprietary live game fixture is embedded in this test.
        for index in range(10):
            mapping = copy.deepcopy(self.doc["maps"][0]); mapping["context"] = "context-"+str(index)
            self.doc["maps"].append(mapping)
        self.reseed(); self.w["extensions"]["retained_research"] = ["Evidence text "+("x"*1000) for _ in range(800)]
        before = copy.deepcopy(self.w); packet = p.export_packet(self.w, self.doc)
        self.assertEqual(packet["schema_version"], 3); self.assertEqual(packet["workbook"], before)
        self.assertEqual({row[0] for row in packet["preview"]["rows"]}, {a["id"] for a in self.w["actions"]})
        self.assertLessEqual(len(maps.encoded(packet)), 1024*1024)
        self.assertTrue(all(len(row[-1]) <= 2 for row in packet["preview"]["rows"]))


class VersionedPolicyTests(unittest.TestCase):
    def setUp(self):
        self.doc = fixture.document()
        for mapping in self.doc["maps"]:
            if mapping["layer"] == "BASIC":
                next(c for c in mapping["cells"] if c["button_id"] == 1).update(output="LAYER:WEAPONS", action="Hold WEAPONS")
                next(c for c in mapping["cells"] if c["button_id"] == 2).update(output="B", action="Rare magnify")

    def choices(self, workbook):
        return next(row for row in p.preview(workbook, self.doc)["rows"] if row["from_key"] == "J")["candidates"]

    def test_legacy_still_protects_number_two_without_migration(self):
        workbook = p.new_workbook(self.doc, rules_revision=p.RULES); before = copy.deepcopy(workbook)
        self.assertNotIn("BASIC/gameplay/2", [r["id"] for r in self.choices(workbook)])
        self.assertEqual(workbook, before); self.assertEqual(workbook["baseline"]["rules_revision"], p.RULES)

    def test_new_policy_allows_number_two_action_position(self):
        workbook = p.new_workbook(self.doc, rules_revision=p.LITTLE_FINGER_RULES)
        self.assertIn("BASIC/gameplay/2", [r["id"] for r in self.choices(workbook)])

    def test_new_actual_number_one_layer_holder_remains_protected(self):
        workbook = p.new_workbook(self.doc, rules_revision=p.LITTLE_FINGER_RULES)
        choices = [r["id"] for r in self.choices(workbook)]
        self.assertNotIn("BASIC/gameplay/1", choices)
        self.assertNotIn("WEAPONS/gameplay/3", choices)

    def test_new_layer_and_blank_roles_are_reserved_even_before_native_change(self):
        self.doc["maps"][0]["cells"] = [dict(c, output="Alt", action="Modifier only") if c["button_id"] in {3, 4, 37} else c for c in self.doc["maps"][0]["cells"]]
        workbook = p.new_workbook(self.doc, rules_revision=p.LITTLE_FINGER_RULES)
        choices = [r["id"] for r in self.choices(workbook)]
        for bid in (3, 4, 37): self.assertNotIn(f"BASIC/gameplay/{bid}", choices)
        self.assertEqual(p.protected_buttons(workbook), {19, 24, 3, 4, 37})

    def test_known_frequent_action_does_not_consume_infrequent_number_two(self):
        workbook = p.new_workbook(self.doc, rules_revision=p.LITTLE_FINGER_RULES)
        next(a for a in workbook["actions"] if a["output"] == "J")["frequency"] = [4]
        self.assertNotIn("BASIC/gameplay/2", [r["id"] for r in self.choices(workbook)])

    def test_other_fingers_keep_row_order_and_little_finger_overrides_it(self):
        workbook = p.new_workbook(self.doc, rules_revision=p.LITTLE_FINGER_RULES)
        indexed = {r["id"]: r for r in p.routes(self.doc)}
        self.assertEqual(p.route_access_rank(workbook, indexed["BASIC/gameplay/7"]), 1)
        self.assertEqual(p.route_access_rank(workbook, indexed["BASIC/gameplay/2"]), 3)

    def test_actual_document_capitalized_little_label_uses_override(self):
        for button in self.doc["buttons"]: button["finger"] = button["finger"].title()
        workbook = p.new_workbook(self.doc, rules_revision=p.LITTLE_FINGER_RULES)
        route = next(r for r in p.routes(self.doc) if r["id"] == "BASIC/gameplay/2")
        self.assertEqual(route["finger"], "Little"); self.assertEqual(p.route_access_rank(workbook, route), 3)

    def test_new_drafts_default_to_current_policy(self):
        self.assertEqual(p.new_workbook(self.doc)["baseline"]["rules_revision"], p.LITTLE_FINGER_RULES)

    def test_existing_legacy_workbook_round_trip_remains_unchanged(self):
        legacy = p.new_workbook(self.doc, rules_revision=p.RULES); before = copy.deepcopy(legacy)
        decoded = p.decode(maps.encoded(legacy)); p.validate(decoded)
        self.assertEqual(decoded, before); self.assertEqual(decoded["baseline"]["rules_revision"], p.RULES)

    def test_rare_critical_action_does_not_consume_non_urgent_number_two(self):
        workbook = p.new_workbook(self.doc, rules_revision=p.LITTLE_FINGER_RULES)
        action = next(a for a in workbook["actions"] if a["output"] == "J")
        action.update(urgency=[5], frequency=[1])
        self.assertEqual(p.priority(action["urgency"], action["frequency"])["score"], 17)
        self.assertNotIn("BASIC/gameplay/2", [r["id"] for r in self.choices(workbook)])


if __name__ == "__main__": unittest.main()
