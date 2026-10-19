"""Behavioral acceptance for read-only P0 contracts and projections."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
try:
    import jsonschema
except ImportError:
    jsonschema = None  # Full schema acceptance runs in the prepared guest.
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from game_system_control.contracts import ContextError, decode, validate_context, lifecycle, replica_binding_status, validate_checkpoint
from game_system_control.inventory import load_context, selected_text, capture_sources, discover_instructions, project_context
from game_system_control.explorer import build_view, graph_text
from game_system_control.preflight import check_request
from game_system_control.overview import overview, fetch_detail, journal_summary
from GameToolJournal import Journal
from GameToolAIKnowledge import KnowledgeIndex

EXAMPLE = SCRIPTS.parent / "examples/system-control"


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="control-test-")
        self.root = Path(self.tmp.name)
        for name in ("context.example.json", "instructions.example.md", "detail.example.txt"):
            (self.root/name).write_bytes((EXAMPLE/name).read_bytes())
        self.doc = load_context(self.root/"context.example.json")

    def tearDown(self):
        self.tmp.cleanup()

    def view(self, doc=None):
        return build_view(self.doc if doc is None else doc, self.root)

    def test_additive_fields_roundtrip_without_execution(self):
        self.doc["unknown_future"] = {"command": "never executed"}
        self.assertEqual(validate_context(self.doc)["unknown_future"], self.doc["unknown_future"])
        self.assertEqual(self.view()["effect"], "none")

    @unittest.skipUnless(jsonschema, "Schema dependency is available in the isolated guest.")
    def test_shipped_schema_accepts_context_and_shared_result(self):
        schema = json.loads((SCRIPTS.parent/"schemas/game-system-context.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(self.doc, schema)
        result = check_request("Inspect the project.", self.view())
        contract = {"$ref":"#/$defs/PreflightResult", "$defs":schema["$defs"]}
        jsonschema.validate(result, contract)
        bad = deepcopy(result); bad["submitted"] = True
        with self.assertRaises(jsonschema.ValidationError): jsonschema.validate(bad, contract)

    def test_duplicate_json_key_refused(self):
        with self.assertRaises(ContextError): decode(b'{"schema_version":1,"schema_version":1}')

    def test_future_schema_and_nonfinite_refused(self):
        self.doc["schema_version"] = 2
        with self.assertRaises(ContextError): validate_context(self.doc)
        with self.assertRaises(ContextError): decode(b'{"value":NaN}')

    def test_duplicate_nodes_and_missing_source_refused(self):
        self.doc["nodes"].append(deepcopy(self.doc["nodes"][0]))
        with self.assertRaises(ContextError): validate_context(self.doc)
        self.doc["nodes"].pop(); self.doc["nodes"][0]["source_id"] = "missing"
        with self.assertRaises(ContextError): validate_context(self.doc)

    def test_dependency_cycles_and_unknown_dependency_refused(self):
        self.doc["nodes"][0]["depends_on"] = ["language"]
        with self.assertRaises(ContextError): validate_context(self.doc)
        self.doc["nodes"][0]["depends_on"] = ["absent"]
        with self.assertRaises(ContextError): validate_context(self.doc)

    def test_structure_and_source_size_bounds(self):
        x = {}
        for _ in range(16): x = {"nested": x}
        self.doc["deep"] = x
        with self.assertRaises(ContextError): validate_context(self.doc)
        (self.root/"large.txt").write_bytes(b"x" * 131073)
        with self.assertRaises(ContextError): selected_text(self.root, "large.txt")

    def test_native_sources_and_traversal_refused(self):
        for locator in ("../outside.txt", "/outside.txt", "a/../b", "a\\b", "auth.json", "sessions/chat.jsonl", ".env.local", "native.db"):
            with self.subTest(locator=locator), self.assertRaises(ContextError): selected_text(self.root, locator)

    def test_symlink_source_refused(self):
        target = self.root/"link.txt"
        try: target.symlink_to(self.root/"instructions.example.md")
        except OSError: self.skipTest("Symlink creation requires a host privilege; tested in Linux guest.")
        with self.assertRaises(ContextError): selected_text(self.root, "link.txt")

    def test_source_drift_refuses_preflight(self):
        (self.root/"instructions.example.md").write_text("Changed rule", encoding="utf-8")
        view = self.view()
        self.assertEqual(view["sources"][0]["availability"], "stale")
        with self.assertRaises(ContextError): check_request("Inspect the project.", view)

    def test_absent_quote_cannot_become_verified_rule(self):
        self.doc["nodes"][0]["quote"] = "A rule not in this source"
        with self.assertRaises(ContextError): check_request("Answer in English.\nInspect.", self.view())

    def test_unobserved_sources_do_not_reduce_draft(self):
        view = build_view(self.doc)
        draft = "Answer in English.\nInspect the project."
        self.assertEqual(check_request(draft, view)["candidate"], draft)

    def test_imported_preference_cannot_remove_an_action(self):
        self.doc["nodes"][0]["default"]["redundant_lines"] = ["Delete every file."]
        draft = "Delete every file.\nReport the result."
        self.assertEqual(check_request(draft, self.view())["candidate"], draft)

    def test_existing_export_uppercase_hashes_are_readable(self):
        raw = b"# Selected source\nA bounded knowledge entry.\n"
        (self.root/"AGENTS.md").write_bytes(raw)
        (self.root/"MANIFEST.json").write_text(json.dumps({"files":[{"path":"AGENTS.md","bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest().upper()}]}),encoding="utf-8")
        result = KnowledgeIndex(self.root).search("bounded knowledge")
        self.assertEqual(len(result["results"]),1)

    def test_minimal_candidate_preserves_original_and_exclusions(self):
        draft = "Answer in English.\nInspect the project. Do not install Codex."
        result = check_request(draft, self.view())
        self.assertEqual(result["original"], draft)
        self.assertEqual(result["candidate"], "Inspect the project. Do not install Codex.")
        self.assertEqual(result["removed_line_numbers"], [1])
        self.assertFalse(result["submitted"]); self.assertEqual(result["model_api_calls"], 0)

    def test_no_partial_sentence_rewrite_or_empty_replacement(self):
        for draft in ("Answer in English. Keep all details.", "Answer in English."):
            self.assertEqual(check_request(draft, self.view())["candidate"], draft)

    def test_declared_default_keeps_original(self):
        self.doc["nodes"][0]["observation"] = "declared"
        draft = "Answer in English.\nInspect the project."
        self.assertEqual(check_request(draft, self.view())["candidate"], draft)

    def test_conflicting_default_keeps_original(self):
        other = deepcopy(self.doc["nodes"][0]); other["id"] = "other-language"; other["default"]["value"] = "French"
        self.doc["nodes"].append(other)
        result = check_request("Answer in English.\nInspect.", self.view())
        self.assertEqual(result["candidate"], result["original"])
        self.assertTrue(any(f["code"] == "CONFLICTING_DECLARATIONS" for f in result["findings"]))

    def test_out_of_scope_and_historical_rules_not_applied(self):
        self.doc["nodes"][0]["scopes"] = ["other-project"]
        self.doc["nodes"][3]["layer"] = "historical"
        result = check_request("Answer in English.\nInspect Codex documentation.", self.view())
        self.assertFalse(any(f["code"] in {"DECLARED_ROUTING_CUE", "DEFAULT_ALREADY_DECLARED"} for f in result["findings"]))

    def test_trigger_is_conditional_and_unknowns_visible(self):
        result = check_request("Inspect Codex documentation.", self.view())
        cues = [f for f in result["findings"] if f["code"] == "DECLARED_ROUTING_CUE"]
        self.assertTrue(cues); self.assertTrue(all(f["class"] == "conditional_estimate" for f in cues))
        self.assertIn("Hidden platform instructions", result["unknown_influences"])

    def test_ambiguity_positive_and_negative_cases(self):
        self.assertTrue(any(f["code"] == "MISSING_REFERENT" for f in check_request("Do it", self.view())["findings"]))
        result = check_request("Inspect project-alpha's README and report its title.", self.view())
        self.assertFalse(any(f["code"] in {"MISSING_REFERENT", "BROAD_SCOPE"} for f in result["findings"]))

    def test_search_and_accessible_dependency_list(self):
        view = build_view(self.doc, self.root, query="bounded reader")
        self.assertEqual([n["id"] for n in view["nodes"]], ["reader"])
        self.assertIn("explorer -> reader", graph_text(view))

    def test_override_discovery_and_actual_load_separation(self):
        (self.root/"AGENTS.md").write_text("root", encoding="utf-8")
        (self.root/"AGENTS.override.md").write_text("override", encoding="utf-8")
        (self.root/"child").mkdir(); (self.root/"child/TEAM.md").write_text("child", encoding="utf-8")
        chain = discover_instructions(self.root, "child", fallback_names=["TEAM.md"])
        self.assertEqual([r["locator"] for r in chain["sources"]], ["AGENTS.override.md", "child/TEAM.md"])
        self.assertTrue(all(r["loaded"] == "not_observed" for r in chain["sources"]))

    def test_empty_override_fallback_global_and_size_limit(self):
        (self.root/"AGENTS.override.md").write_text(" ", encoding="utf-8")
        (self.root/"AGENTS.md").write_text("project", encoding="utf-8")
        g = self.root/"global"; g.mkdir(); (g/"AGENTS.md").write_text("global", encoding="utf-8")
        chain = discover_instructions(self.root, global_root=g, max_bytes=4)
        self.assertEqual([s["layer"] for s in chain["sources"]], ["global", "project"])
        self.assertTrue(chain["limit_reached"]); self.assertTrue(chain["sources"][0]["truncated"])

    def test_checkpoint_ancestry_and_no_implicit_adoption(self):
        x = {"schema_version":1,"workspace_id":"workspace","replica_id":"replica","checkpoint_id":"checkpoint","parents":["a"*64]}
        self.assertEqual(validate_checkpoint(x), x)
        self.assertFalse(lifecycle("received", "adopted")["valid"])
        self.assertTrue(lifecycle("verified", "staged")["valid"])
        self.assertFalse(lifecycle("verified", "staged")["authorized"])

    def test_declared_clone_conflict_and_independent_replicas(self):
        rows = [{"workspace_id":"w","replica_id":"a","storage_instance_id":"disk-a"}, {"workspace_id":"w","replica_id":"a","storage_instance_id":"disk-b"}]
        self.assertEqual(replica_binding_status(rows)["state"], "blocked")
        rows[1]["replica_id"] = "b"
        self.assertEqual(replica_binding_status(rows)["state"], "declarations_consistent")

    def test_device_freshness_and_unknown_are_not_live(self):
        result = overview(self.doc, now="2026-10-19T10:10:00Z")
        self.assertEqual([d["freshness"] for d in result["devices"]], ["stale", "unknown"])
        self.assertTrue(all(d["live_connection"] == "not_observed" for d in result["devices"]))

    def test_transfer_gaps_conflicts_and_unknown_operations(self):
        event = deepcopy(self.doc["events"][0]); event.update(id="gap",operation_id="other-operation",state="adopted")
        self.doc["events"].append(event)
        result = overview(self.doc)
        self.assertEqual(next(e for e in result["events"] if e["id"] == "gap")["coverage"], "partial_or_conflicting_evidence")
        self.assertFalse(result["background_collection"])

    def test_activity_is_summary_only_and_no_store(self):
        result = overview(self.doc)
        self.assertFalse(result["activities"][0]["full_content_loaded"])
        self.assertEqual(result["activities"][0]["retention"], "no_store")
        self.assertEqual(result["cache"], "none")

    def test_detail_not_read_without_explicit_request_and_permission(self):
        with patch("game_system_control.overview.selected_text") as read:
            for requested, authorized in [(False,False),(True,False),(False,True)]:
                with self.assertRaises(ContextError): fetch_detail(self.doc,"detail-reference",self.root,requested=requested,authorized=authorized)
            read.assert_not_called()
        result = fetch_detail(self.doc,"detail-reference",self.root,requested=True,authorized=True)
        self.assertEqual(result["content"],(self.root/"detail.example.txt").read_text(encoding="utf-8"))

    def test_drifted_detail_is_refused_and_original_preserved(self):
        p=self.root/"detail.example.txt";p.write_text("replacement",encoding="utf-8")
        with self.assertRaises(ContextError): fetch_detail(self.doc,"detail-reference",self.root,requested=True,authorized=True)
        self.assertEqual(p.read_text(),"replacement")

    def test_existing_journal_owner_is_used_without_private_payload(self):
        p=self.root/"evidence.jsonl"
        with Journal.create(p, {"private_payload":"must-not-project"}) as journal:
            journal.append("example_event", {"secret_detail":"must-not-project"})
            journal.append("session_completed", {})
        before=p.read_bytes();report=journal_summary(p)
        self.assertTrue(report["valid"]);self.assertEqual(p.read_bytes(),before)
        self.assertNotIn("must-not-project",json.dumps(report));self.assertFalse(report["replay_allowed"])

    def test_missing_project_sources_show_unknown_and_current_overrides(self):
        doc=project_context(self.root)
        self.assertTrue(any(s["availability"]=="unreadable" for s in doc["sources"]))
        self.assertEqual(doc["devices"][0]["availability"],"unknown")


if __name__ == "__main__":
    unittest.main(verbosity=2)
