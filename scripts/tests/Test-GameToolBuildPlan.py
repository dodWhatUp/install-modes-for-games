"""Build context is a bounded read-only view, not another task master."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SCRIPTS))
from game_system_control.build_plan import BUILD_MAP, build_packet, build_context
from game_system_control.contracts import ContextError
from game_system_control.inventory import check_sources
from game_system_control.report import accessible_report


class BuildPlanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="build-plan-test-")
        self.root = Path(self.tmp.name)
        self.plan = json.loads((SCRIPTS.parent/BUILD_MAP).read_text(encoding="utf-8-sig"))
        self.manifest = json.loads((SCRIPTS.parent/self.plan["task_manifest"]).read_text(encoding="utf-8-sig"))
        self.write(BUILD_MAP, self.plan); self.write(self.plan["task_manifest"], self.manifest)
        self.write(self.plan["master_plan"], "# Selected master plan\n")
        for component in self.plan["core"] + self.plan["systems"]:
            for path in component.get("owners", []):
                if not (self.root/path).exists(): self.write(path, "owner-body-must-not-be-in-packet\n")

    def tearDown(self): self.tmp.cleanup()

    def write(self, path, value):
        target = self.root/path; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value if type(value) is str else json.dumps(value), encoding="utf-8")

    def test_full_view_derives_all_existing_checks_without_claiming_runtime_effects(self):
        packet = build_packet(self.root)
        self.assertEqual(packet["counts"], {"tasks": 18, "items": 108, "accepted": 47, "complete_packages": 7})
        self.assertEqual(packet["effect"], "none")
        self.assertEqual({t["id"] for t in packet["frontier"]}, {"MCI-08", "MCI-13", "MCI-16"})
        self.assertIn("not runtime permission", packet["frontier"][0]["readiness_scope"])

    def test_scoped_packet_keeps_required_context_and_omits_unrelated_bodies_and_tasks(self):
        full = build_packet(self.root); packet = build_packet(self.root, "MCI-08")
        self.assertEqual(len(packet["task"]["steps"]), 6)
        self.assertTrue(packet["task"]["requirements"])
        self.assertEqual(packet["task"]["unaccepted_prerequisites"], [])
        self.assertNotIn("S3", {c["id"] for c in packet["components"]})
        self.assertNotIn("tasks", packet); self.assertNotIn("frontier", packet)
        self.assertLess(len(json.dumps(packet)), len(json.dumps(full)))
        self.assertNotIn("owner-body-must-not-be-in-packet", json.dumps(packet))
        self.assertNotIn(str(self.root), json.dumps(packet))

    def test_pending_signin_or_merge_dependencies_are_not_presented_as_ready(self):
        packet = build_packet(self.root, "MCI-10")
        self.assertEqual(set(packet["task"]["unaccepted_prerequisites"]), {"MCI-09", "MCI-13"})

    def test_scoped_source_work_exposes_shared_windows_gate_without_new_dependency(self):
        packet = build_packet(self.root, "MCI-08")
        gate = next(g for g in packet["relevant_capability_gates"] if g["id"] == "MCI-13")
        self.assertEqual(gate["accepted"], 5); self.assertEqual(len(gate["remaining_criteria"]), 1)
        self.assertEqual(packet["task"]["depends_on"], ["MCI-02", "MCI-07"])

    def test_source_vector_changed_during_owner_collection_is_refused(self):
        import game_system_control.build_plan as module
        original = module.selected_text
        changed = [False]
        def read(root, path, expected=None):
            result = original(root, path, expected)
            if path.startswith("scripts/") and not changed[0]:
                changed[0] = True
                self.write(self.plan["task_manifest"], {**self.manifest, "date": "concurrent-edit"})
            return result
        with patch.object(module, "selected_text", side_effect=read), self.assertRaises(ContextError): build_packet(self.root, "MCI-08")

    def test_manifest_change_updates_progress_without_editing_the_build_map(self):
        task = next(t for t in self.manifest["tasks"] if t["id"] == "MCI-13")
        task["checklist_complete"] = [True]*6; task["status"] = "completed"
        self.write(self.plan["task_manifest"], self.manifest)
        self.assertEqual(build_packet(self.root)["counts"]["accepted"], 48)
        self.assertEqual(build_packet(self.root)["counts"]["complete_packages"], 8)

    def test_completed_label_without_accepted_checks_is_rejected(self):
        self.manifest["tasks"][0]["checklist_complete"][0] = False
        self.write(self.plan["task_manifest"], self.manifest)
        with self.assertRaises(ContextError): build_packet(self.root)

    def test_task_and_component_cycles_are_rejected(self):
        for graph in ("task", "component"):
            with self.subTest(graph=graph):
                if graph == "task":
                    self.manifest["tasks"][0]["depends_on"] = [self.manifest["tasks"][0]["id"]]
                    self.write(self.plan["task_manifest"], self.manifest)
                else:
                    self.plan["core"][0]["depends_on"] = ["C1"]; self.write(BUILD_MAP, self.plan)
                with self.assertRaises(ContextError): build_packet(self.root)
                self.manifest["tasks"][0]["depends_on"] = []; self.write(self.plan["task_manifest"], self.manifest)

    def test_uncovered_task_unknown_reference_and_duplicate_component_fail_closed(self):
        original = deepcopy(self.plan)
        for failure in ("missing", "unknown", "duplicate"):
            self.plan = deepcopy(original)
            if failure == "missing": self.plan["release"]["tasks"] = []
            elif failure == "unknown": self.plan["core"][0]["tasks"] = ["MCI-99"]
            else: self.plan["core"].append(deepcopy(self.plan["core"][0]))
            self.write(BUILD_MAP, self.plan)
            with self.subTest(failure=failure), self.assertRaises(ContextError): build_packet(self.root)

    def test_owner_path_escape_and_native_auth_source_are_not_read(self):
        for path in ("../outside.txt", ".codex/auth.json"):
            self.plan["core"][0]["owners"] = [path]; self.write(BUILD_MAP, self.plan)
            with self.subTest(path=path), self.assertRaises(ContextError): build_packet(self.root, "MCI-08")

    def test_integrated_release_packet_contains_all_components_and_release_evidence(self):
        packet = build_packet(self.root, "MCI-18")
        self.assertEqual(len(packet["components"]), 17); self.assertIn("release", packet)
        self.assertTrue(packet["task"]["unaccepted_prerequisites"])

    def test_existing_report_escapes_content_and_tracks_all_three_source_owners(self):
        self.plan["core"][0]["label"] = "<script>untrusted-label</script>"; self.write(BUILD_MAP, self.plan)
        context = build_context(self.root); report = accessible_report(context, self.root)
        self.assertEqual(len(context["sources"]), 3); self.assertEqual(len(context["nodes"]), 19)
        self.assertNotIn("<script>untrusted-label</script>", report)
        self.assertIn("&lt;script&gt;untrusted-label", report)
        self.assertIn("Filter report records", report)
        self.assertIn("7 shared components", report); self.assertIn("47/108", report)
        self.assertIn("Receives", report); self.assertIn("Source and machine-readable record", report)
        self.write(self.plan["task_manifest"], {**self.manifest, "date": "changed"})
        refreshed = check_sources(context, self.root)
        self.assertNotEqual(next(s for s in refreshed["sources"] if s["id"] == "plan-source-0")["availability"], "available")

    def test_cli_needs_explicit_root_and_does_not_create_files(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*"))
        cli = str(SCRIPTS/"GameToolSystemControl.py")
        missing = subprocess.run([sys.executable, "-B", cli, "build-plan"], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 2)
        result = subprocess.run([sys.executable, "-B", cli, "build-plan", "--root", str(self.root), "--task", "MCI-08"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["effect"], "none")
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob("*")))

    def test_duplicate_json_keys_and_unknown_task_are_rejected(self):
        with self.assertRaises(ContextError): build_packet(self.root, "MCI-99")
        self.write(BUILD_MAP, '{"schema_version":1,"schema_version":1}')
        with self.assertRaises(ContextError): build_packet(self.root)


if __name__ == "__main__": unittest.main(verbosity=2)
