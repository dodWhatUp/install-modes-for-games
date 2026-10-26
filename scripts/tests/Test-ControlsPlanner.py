"""Planning and adapter contracts. Synthetic files; no live writes or input."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolControlsPlanner as p
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder

spec = importlib.util.spec_from_file_location("map_fixture", Path(__file__).with_name("Test-KeymapDocument.py"))
f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)


def document():
    doc = f.document(); doc["maps"][1]["layer"] = "WEAPONS"
    for button in doc["buttons"]:
        button["finger"] = ("little" if button["id"] in {1, 2, 3, 4, 37} else
                            "ring" if button["id"] in {5, 6, 7, 8, 38} else
                            "middle" if button["id"] in {9, 10, 11, 12, 13} else
                            "index" if button["id"] in {14, 15, 16, 17, 18} else "thumb")
    for m in doc["maps"]:
        for c in m["cells"]:
            c.update(output="UNASSIGNED", action="", display_action="")
    def cell(layer, bid, key, label):
        next(c for c in doc["maps"][layer]["cells"] if c["button_id"] == bid).update(output=key, action=label)
    cell(0, 2, "LAYER:WEAPONS", "Hold WEAPONS")
    cell(0, 5, "Ctrl", "Crouch"); cell(0, 9, "Shift", "Sprint"); cell(0, 14, "Space", "Jump")
    cell(0, 6, "J", "Use / Spear"); cell(0, 10, "K", "Utility"); cell(0, 11, "H", "Block")
    cell(0, 7, "G", "Weapon wheel")
    cell(1, 23, "K", "Utility"); cell(1, 7, "1", "Weapon 1"); cell(1, 3, "X", "Invalid held finger")
    return maps.validate(doc)


class PriorityTests(unittest.TestCase):
    def test_critical_rare(self): self.assertEqual(p.priority([5], [1])["score"], 17)
    def test_paused_frequent(self): self.assertEqual(p.priority([2], [4])["score"], 8)
    def test_unknown_is_null(self): self.assertEqual(p.priority([], []), {"policy": p.POLICY, "candidates": [], "score": None, "range": None})
    def test_partial_and_discrete_candidates(self):
        self.assertEqual(p.priority([4], [2, 4])["candidates"], [14, 16])
        self.assertEqual(p.priority([5], [])["range"], [17, 20])
    def test_bad_scores(self):
        for u, freq in (([0], [1]), ([6], [1]), ([True], [1]), ([1], [5]), ([1, 1], [1])):
            with self.assertRaises(ValueError): p.priority(u, freq)
    def test_bundle_preserves_highest_urgency_unknown_unique_rate(self):
        actions = [{"context": "combat", "urgency": [5], "frequency": [1]}, {"context": "combat", "urgency": [2], "frequency": [4]}]
        self.assertEqual(p.bundle_priority(actions)["range"], [17, 20])
        actions[1]["context"] = "menu"
        with self.assertRaises(ValueError): p.bundle_priority(actions)


class PlanningTests(unittest.TestCase):
    def setUp(self): self.doc = document(); self.w = p.new_workbook(self.doc, rules_revision=p.RULES)
    def action(self, key): return next(a for a in self.w["actions"] if a["output"] == key)
    def row(self, key): return next(r for r in p.preview(self.w, self.doc)["rows"] if r["from_key"] == key)
    def test_seed_does_not_invent_research_or_mutate(self):
        before = copy.deepcopy(self.doc); report = p.preview(self.w, self.doc)
        self.assertEqual(self.doc, before); self.assertTrue(all(a["urgency"] == [] for a in self.w["actions"]))
        self.assertTrue(all(not r["changed"] for r in report["rows"])); self.assertTrue(report["read_only"])
        self.assertIn("Effective game source unknown", self.row("J")["warnings"][0])
    def test_duplicate_K_across_layers_is_visible(self):
        self.assertEqual(set(self.row("K")["aliases"]), {"BASIC/gameplay/10", "WEAPONS/gameplay/23"})
    def test_conflicting_alias_labels_are_retained_for_research(self):
        next(c for c in self.doc["maps"][1]["cells"] if c["button_id"] == 23)["action"] = "Different label"
        self.w = p.new_workbook(self.doc, rules_revision=p.RULES)
        self.assertTrue(any("Different label" in e for e in self.action("K")["evidence"]))
        self.assertIn("Overlay labels disagree across exact input aliases", self.row("K")["warnings"])
    def test_thumb_movement_route_blocked(self):
        a = self.action("K"); a.update(needs_movement=True, proposed_route="WEAPONS/gameplay/23")
        self.assertTrue(any("thumb" in s for s in self.row("K")["blocked"]))
    def test_held_layer_holder_finger_blocked(self):
        self.action("J")["proposed_route"] = "WEAPONS/gameplay/3"
        self.assertIn("Held layer occupies the target finger", self.row("J")["blocked"])
    def test_layer_button_and_movement_anchors_protected(self):
        for route in ("BASIC/gameplay/2", "BASIC/gameplay/5"):
            self.action("J")["proposed_route"] = route
            self.assertTrue(self.row("J")["blocked"])
        self.assertNotIn(19, [r["button"] for r in p.routes(self.doc)])
    def test_move_exposes_displaced_action(self):
        self.action("J")["proposed_route"] = "BASIC/gameplay/10"
        self.assertTrue(any("Utility" in s for s in self.row("J")["blocked"]))
    def test_bundle_cannot_split(self):
        for key in ("J", "H"): self.action(key)["bundle_id"] = "same-native-bind"
        self.action("J")["proposed_route"] = "BASIC/gameplay/7"
        self.assertIn("Keep shared binding bundle together", self.row("J")["blocked"])
    def test_contexts_need_explicit_exclusivity(self):
        other = copy.deepcopy(self.action("K")); other.update(id="another", context="menu")
        self.w["actions"].append(other)
        self.assertTrue(any("overlap" in s for s in self.row("K")["warnings"]))
        self.w["exclusive_contexts"] = [{"contexts": ["gameplay", "menu"], "evidence": "Reviewed fixture engine routing"}]
        self.assertFalse(any("overlap" in s for s in self.row("K")["warnings"]))
    def test_unknown_overlay_context_cannot_place(self):
        self.action("J").update(overlay_context=None, proposed_route="BASIC/gameplay/6")
        self.assertTrue(any("context" in s for s in self.row("J")["blocked"]))
    def test_simultaneous_fingers_are_review_not_proof(self):
        self.action("J")["simultaneous"] = [self.action("Ctrl")["id"]]
        self.assertTrue(any("Simultaneous" in s for s in self.row("J")["warnings"]))
    def test_stale_map_and_native_identity_rejected(self):
        for change in ("label", "native"):
            doc = copy.deepcopy(self.doc)
            if change == "label": doc["title"] = "Changed"
            else: doc["keymap_revision"] = "a" * 64
            with self.assertRaisesRegex(ValueError, "Stale"): p.preview(self.w, doc)
    def test_new_schema_and_rules_rejected(self):
        for key, value in (("schema_version", 2), ("kind", "azeron_game_workbook")):
            bad = copy.deepcopy(self.w); bad[key] = value
            with self.assertRaises(ValueError): p.validate(bad)
        bad = copy.deepcopy(self.w); bad["baseline"]["rules_revision"] = "future"
        with self.assertRaises(ValueError): p.validate(bad)
    def test_override_separate_from_computed_score(self):
        a = self.action("J"); a.update(urgency=[5], frequency=[1], user_priority_override=20, override_reason="Game scope request")
        r = self.row("J"); self.assertEqual(r["priority"]["score"], 17); self.assertEqual(r["user_priority_override"], 20)
    def test_review_cannot_change_raw_binding_or_bundle(self):
        incoming = copy.deepcopy(self.w); incoming["actions"][0]["output"] = "F24"
        with self.assertRaisesRegex(ValueError, "native binding"): p.import_review(self.w, incoming, self.doc)
        incoming = copy.deepcopy(self.w); incoming["actions"][0]["meaning"] = "Reviewed fixture"
        self.assertEqual(p.import_review(self.w, incoming, self.doc), incoming)
    def test_candidate_keeps_native_keys_comments_styles_all_views(self):
        self.doc["maps"][0]["cells"][0]["comment"] = {"text": "Keep", "color": "#FF0000"}
        self.w = p.new_workbook(self.doc, rules_revision=p.RULES)
        candidate = p.overlay_candidate(self.w, self.doc)
        self.assertEqual(maps.output_matrix(candidate), maps.output_matrix(self.doc))
        self.assertEqual(candidate["maps"][0]["cells"][0]["comment"], self.doc["maps"][0]["cells"][0]["comment"])
        with tempfile.TemporaryDirectory() as tmp:
            for view in ("Keys", "Actions", "Combined", "ActionFirst"):
                maps.render(candidate, candidate["maps"][0], Path(tmp) / (view + ".png"), view)
    def test_candidate_refuses_blocked_proposals(self):
        self.action("J")["proposed_route"] = "BASIC/gameplay/2"
        with self.assertRaisesRegex(ValueError, "blocked"): p.overlay_candidate(self.w, self.doc)

    def test_compact_multi_layer_packet_shares_routes_and_respects_existing_limit(self):
        doc=copy.deepcopy(self.doc);template=doc['maps'][0];doc['maps']=[]
        layers=('BASIC','WEAPONS','MENUS','TOOLS','NAV','SYMBOLS')
        for layer in layers:
            for context in ('gameplay','menus'):
                mapping=copy.deepcopy(template);mapping.update(layer=layer,context=context)
                for cell in mapping['cells']:cell.update(output='K'+str(cell['button_id']),action='Action '+str(cell['button_id']))
                if layer=='BASIC':
                    for bid,target in zip((2,1,36,28,30),layers[1:]):next(c for c in mapping['cells'] if c['button_id']==bid)['output']='LAYER:'+target
                doc['maps'].append(mapping)
        value=p.new_workbook(doc, rules_revision=p.RULES);packet=p.export_packet(value,doc)
        self.assertEqual(len(packet['route_catalog']),348)
        self.assertLess(len(maps.encoded(packet)),f.overlay.MAX_JSON)
        self.assertTrue(all(len(row['candidates'])<=8 for row in packet['preview']['rows']))
        self.assertTrue(any(row['candidate_total']>8 for row in packet['preview']['rows']))

    def test_unchanged_seed_preserves_alias_labels_and_evidence_exactly(self):
        self.assertEqual(p.overlay_candidate(self.w,self.doc),self.doc)


class StorageTests(unittest.TestCase):
    def test_candidate_export_is_exclusive_offline_and_four_views_per_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); manifest, _ = f.fixtures.fixture(root)
            doc = document(); keymap = manifest["keymaps"][0]; keymap["revision"] = doc["keymap_revision"]
            keymap["layers"][1]["id"] = "WEAPONS"
            keymap["blank_masks"]["WEAPONS"] = keymap["blank_masks"].pop("MENUS")
            w = p.new_workbook(doc, rules_revision=p.RULES); destination = root / "candidate"
            receipt = p.export_candidate(w, doc, keymap, destination)
            self.assertEqual(len(receipt["images"]), len(doc["maps"]) * 4)
            self.assertFalse(receipt["published"])
            package = builder.read_package(destination / "candidate.keymaps.json", {})
            self.assertEqual(maps.output_matrix(package["documents"][0]), maps.output_matrix(doc))
            with self.assertRaises(FileExistsError): p.export_candidate(w, doc, keymap, destination)

    def test_exact_native_byte_guard_detects_formatting_drift(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); identity = "12345678-1234-1234-1234-123456789abc"
            path = root / "device/ProfileStorage" / ("profile_" + identity + ".json")
            path.parent.mkdir(parents=True); original = b'{"keys": []}'
            path.write_bytes(original)
            keymap = {"layers": [{"id": "BASIC", "profile_id": identity,
                                  "profile_sha256": hashlib.sha256(original).hexdigest()}]}
            self.assertEqual(p.native_status(keymap, root)[0]["state"], "match")
            path.write_bytes(b'{"keys":[]}\n')
            self.assertEqual(p.native_status(keymap, root)[0]["state"], "drift")

    def test_save_history_stale_and_source_library_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib = builder.SourceLibrary(Path(tmp)); library = p.WorkbookLibrary(lib)
            doc = document(); w = p.new_workbook(doc, rules_revision=p.RULES)
            revision = library.save(w); changed = copy.deepcopy(w); changed["extensions"] = {"future_note": "kept"}
            library.save(changed, revision)
            self.assertEqual(library.load(w["game_id"]), changed)
            self.assertEqual(lib.documents(), {})
            self.assertTrue((library.root / "history" / w["game_id"] / (revision + ".json")).exists())
            with self.assertRaisesRegex(ValueError, "changed"): library.save(w, revision)
            self.assertFalse(lib.store.path.exists())


class SourceTests(unittest.TestCase):
    def test_real_idtech_target_snapshot_and_drift(self):
        from game_keybind_ops.core import Service
        from game_keybind_ops.documents import Document
        spec = importlib.util.spec_from_file_location("idtech_fixture", Path(__file__).parent / "keybinds/test_idtech_bindset.py")
        fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); config = root / "fixture.cfg"; config.write_bytes(fixture.RAW)
            service = Service(root / "data"); service.register_local(fixture.spec(root, Document(fixture.RAW, "idtech-bindset")))
            source = p.source_snapshot(service, "target", "fixture-idtech", "synthetic-doom")
            self.assertIn("_shield", [a["label"] for a in source["snapshot"]["action_fields"]])
            self.assertEqual(config.read_bytes(), fixture.RAW)
            config.write_bytes(fixture.RAW + b"// later user edit\r\n")
            doc = document(); doc["game_id"] = "synthetic-doom"
            w = p.attach_source(p.new_workbook(doc, rules_revision=p.RULES), source)
            with self.assertRaisesRegex(ValueError, "changed"): p.check_sources(w, service)

    def service(self):
        service = mock.Mock()
        service.inspect_target.return_value = {"game_id": "game", "current_sha256": "a"*64,
            "bindings": [{"id": "field", "key": "J", "context": "bindset-0"}]}
        service.target.return_value = {"spec": {"game_id": "game", "fields": [
            {"id": "field", "selector": {"command": "_use"}, "linked_group": "native-bundle"}]}}
        return service
    def test_registered_target_read_only_context_not_guessed(self):
        service = self.service(); source = p.source_snapshot(service, "target", "target", "game")
        w = p.attach_source(p.new_workbook(document(), rules_revision=p.RULES), source)
        self.assertEqual(w["actions"][0]["label"], "_use"); self.assertIsNone(w["actions"][0]["overlay_context"])
        self.assertEqual(w["actions"][0]["bundle_id"], "native-bundle")
        self.assertEqual(set(call[0] for call in service.mock_calls), {"inspect_target", "target"})
    def test_file_drift_and_wrong_game_rejected(self):
        service = self.service(); source = p.source_snapshot(service, "target", "target", "game")
        w = p.attach_source(p.new_workbook(document(), rules_revision=p.RULES), source)
        p.check_sources(w, service)
        service.inspect_target.return_value["current_sha256"] = "b"*64
        with self.assertRaisesRegex(ValueError, "changed"): p.check_sources(w, service)
        with self.assertRaisesRegex(ValueError, "another game"): p.source_snapshot(service, "target", "target", "other-game")


if __name__ == "__main__": unittest.main()
