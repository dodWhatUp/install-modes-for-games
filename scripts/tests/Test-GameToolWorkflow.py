"""Authored offline recipes; no targets, games, input or providers are accessed."""
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location("workflow_test_" + name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


API, CORE = load("GameToolWorkflow"), load("GameToolCoordinator")
EXAMPLE = ROOT / "examples/game-tool-hub/workflow-installation.example.json"
DIAGNOSTIC = ROOT / "examples/game-tool-hub/workflow-diagnostic.example.json"


def complete():
    r = json.loads(EXAMPLE.read_bytes())
    r["target"] = dict(game_id="FixtureGame", executable="fixture.exe", build="1.0", renderer="DX12")
    r["layer"].update(version="1.0", sha256="a" * 64, source_revision="revision-1", source_sha256="b" * 64, freshness="declared_current")
    r["resources"][0]["owners"] = ["ExampleLayer"]
    for p in r["processes"]:
        p["state"] = "declared_stopped"
    r["snapshot"].update(current="declared_byte_verified", known_good="declared_byte_verified", distinct=True)
    r["changes"][0].update(before_sha256="c" * 64, after_sha256="d" * 64, current_state="declared_hash", current_sha256="c" * 64,
                            backup_state="declared_byte_verified", backup_sha256="c" * 64)
    return r


def raw(recipe):
    return json.dumps(recipe).encode()


class WorkflowContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-contract-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder / "recipe.json"
        self.source.write_bytes(raw(complete()))
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def plan(self, r=None):
        return API.plan_bytes(raw(complete() if r is None else r))

    def blocker(self, r, code):
        result = self.plan(r)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(code, result["declaration_blockers"])
        self.assertEqual(result["execution"], "none")
        return result

    def test_complete_is_only_prepared_never_authority(self):
        result = self.plan()
        self.assertEqual(result["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(result["rollback_status"], "CONDITIONAL_NOT_EXECUTABLE")
        self.assertFalse(result["execution_authorized"])
        self.assertFalse(result["runtime_verification"])
        self.assertEqual(result["fg_preflight"], "NOT_PERFORMED")

    def test_all_declared_pass_checks_do_not_issue_runtime_pass(self):
        r = complete()
        for c in r["checks"]:
            c["result"] = "declared_pass"
        self.assertFalse(self.plan(r)["runtime_verification"])

    def test_unknown_example_blocked_not_recommendation(self):
        result = API.inspect_source(EXAMPLE)
        self.assertIn("OWNERSHIP_UNKNOWN", result["declaration_blockers"])
        self.assertEqual(result["status"], "BLOCKED")

    def test_unknown_target(self):
        r = complete(); r["target"]["build"] = None
        self.blocker(r, "TARGET_IDENTITY_UNKNOWN")

    def test_stale_or_missing_upstream(self):
        for value in ("stale", "unknown"):
            r = complete(); r["layer"]["freshness"] = value
            self.blocker(r, "UPSTREAM_SOURCE_UNKNOWN_OR_STALE")

    def test_unknown_owner(self):
        r = complete(); r["resources"][0]["owners"] = None
        self.blocker(r, "OWNERSHIP_UNKNOWN")

    def test_conflicting_multi_or_wrong_owner(self):
        for owners in (["Other"], ["ExampleLayer", "Other"]):
            r = complete(); r["resources"][0]["owners"] = owners
            self.blocker(r, "OWNERSHIP_CONFLICT")

    def test_dependency_host_preserved_and_missing_host_blocks(self):
        r = complete()
        r["resources"].append(dict(id="Host", kind="host", owners=["HostOwner"], expected_owner="HostOwner", requires=[]))
        r["resources"][0]["requires"] = ["Host"]
        self.assertEqual(self.plan(r)["status"], "PREPARED_NOT_AUTHORIZED")
        r["resources"][1]["owners"] = []
        self.blocker(r, "REQUIRED_HOST_MISSING")

    def test_missing_dependency_reference_refused(self):
        r = complete(); r["resources"][0]["requires"] = ["Missing"]
        with self.assertRaises(API.WorkflowError): self.plan(r)

    def test_dependency_cycle_blocks(self):
        r = complete(); r["resources"][0]["requires"] = ["ExampleResource"]
        self.blocker(r, "DEPENDENCY_CYCLE")

    def test_missing_or_unknown_processes_block(self):
        for processes in ([], [dict(role="game", state="unknown")]):
            r = complete(); r["processes"] = processes
            self.blocker(r, "STOPPED_PROCESSES_UNVERIFIED")

    def test_running_process_blocks(self):
        r = complete(); r["processes"][0]["state"] = "declared_running"
        self.blocker(r, "PROCESS_DECLARED_RUNNING")

    def test_snapshot_inventory_or_copied_not_byte_verified(self):
        for coverage in ("inventory_only", "declared_copied", "unknown"):
            r = complete(); r["snapshot"]["current"] = coverage
            self.blocker(r, "CURRENT_SNAPSHOT_COVERAGE_INCOMPLETE")

    def test_distinct_known_good_not_lost(self):
        r = complete(); r["snapshot"]["known_good"] = "unknown"
        self.blocker(r, "KNOWN_GOOD_PRESERVATION_UNKNOWN")

    def test_current_hash_drift_blocks_install_and_rollback(self):
        r = complete(); r["changes"][0]["current_sha256"] = "e" * 64
        result = self.blocker(r, "CURRENT_FILE_HASH_DRIFT")
        self.assertEqual(result["rollback_status"], "BLOCKED")

    def test_original_backup_hash_and_coverage_required(self):
        for key, value in (("backup_sha256", "f" * 64), ("backup_state", "inventory_only"), ("before_sha256", None)):
            r = complete(); r["changes"][0][key] = value
            self.blocker(r, "ORIGINAL_BACKUP_INCOMPLETE_OR_MISMATCHED")

    def test_after_hash_unknown_blocks(self):
        r = complete(); r["changes"][0]["after_sha256"] = None
        self.blocker(r, "EXPECTED_AFTER_HASH_UNKNOWN")

    def test_change_other_layer_blocks(self):
        r = complete(); r["changes"][0]["owner"] = "Other"
        self.blocker(r, "CHANGE_OUTSIDE_SINGLE_LAYER")

    def test_add_rollback_only_own_new_file(self):
        r = complete()
        r["resources"][0]["owners"] = []
        r["changes"][0].update(action="add", before_sha256=None, current_state="declared_absent", current_sha256=None, backup_state="not_applicable", backup_sha256=None)
        result = self.plan(r)
        self.assertEqual(result["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(result["change_list"][0]["rollback_proposal"], "remove_only_owned_new_file")
        self.assertIn("newer/unrelated", result["change_list"][0]["rollback_condition"])

    def test_add_existing_file_blocks(self):
        r = complete()
        r["changes"][0].update(action="add", before_sha256=None, backup_state="not_applicable", backup_sha256=None)
        self.blocker(r, "ADD_TARGET_NOT_DECLARED_ABSENT")

    def test_no_change_or_missing_verification_plan_blocks(self):
        r = complete(); r["changes"] = []
        self.blocker(r, "NO_SCOPED_CHANGE")
        r = complete(); r["checks"] = []
        self.blocker(r, "COMPONENT_VERIFICATION_PLAN_INCOMPLETE")

    def test_failure_and_memory_warning_suspend(self):
        r = complete(); r["checks"][0]["result"] = "declared_fail"
        self.blocker(r, "VERIFICATION_DECLARED_FAILED")
        r = complete(); r["observations"] = [dict(id="Warning", kind="memory_warning", source_sha256=None)]
        self.blocker(r, "MEMORY_WARNING_SUSPENDS_TESTING")

    def test_diagnosis_is_evidence_request_not_verified_cause(self):
        r = complete(); r.update(kind="diagnostic", changes=[], observations=[dict(id="Visible", kind="overlay_visible", source_sha256=None)],
            hypotheses=[dict(id="Maybe", category="unknown", support=["Visible"], contradicts=[], requests=["component_evaluation"])])
        result = self.plan(r)
        self.assertEqual(result["status"], "EVIDENCE_REQUEST_ONLY")
        self.assertFalse(result["root_cause_verified"])
        self.assertIsNone(result["diagnostic_hypotheses"][0]["confidence"])
        self.assertFalse(result["diagnostic_hypotheses"][0]["cause_verified"])

    def test_diagnostic_mutation_refused(self):
        r = complete(); r["kind"] = "diagnostic"
        with self.assertRaises(API.WorkflowError): self.plan(r)

    def test_hypothesis_references_ranking_and_contradictions(self):
        r = complete(); r.update(kind="diagnostic", changes=[])
        r["observations"] = [dict(id="First", kind="faulting_module", source_sha256=None), dict(id="Second", kind="process_exit", source_sha256=None)]
        r["hypotheses"] = [dict(id="One", category="unknown", support=["First"], contradicts=["Second"], requests=["first_failure"]),
                           dict(id="Two", category="version_mismatch", support=["First", "Second"], contradicts=[], requests=["upstream_compatibility"])]
        self.assertEqual(self.plan(r)["diagnostic_hypotheses"][0]["hypothesis"], "hypothesis_002")
        r["hypotheses"][0]["support"] = ["Missing"]
        with self.assertRaises(API.WorkflowError): self.plan(r)

    def test_portable_omits_names_paths_ids_and_private_source(self):
        r = complete(); r["changes"][0]["target"] = "PRIVATE_FIXTURE.ini"
        self.source.write_bytes(raw(r))
        preview = API.preview_source(self.source)
        self.assertEqual(preview["local_changes"][0]["target"], "PRIVATE_FIXTURE.ini")
        serialized = json.dumps(preview["portable"])
        for text in ("PRIVATE_FIXTURE", "ExampleLayer", "FixtureGame", str(self.folder)):
            self.assertNotIn(text, serialized)

    def test_arbitrary_commands_unknown_fields_or_true_schema_refused(self):
        for key, value in (("execute", "shell"), ("command", "do something"), ("schema_version", True)):
            r = complete(); r[key] = value
            with self.assertRaises(API.WorkflowError): self.plan(r)

    def test_duplicate_nonfinite_invalid_utf8_empty_large_deep_refused(self):
        for data in (b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'', b' ' * (API.MAX_SOURCE_BYTES + 1), b'[' * 100 + b'0' + b']' * 100):
            with self.assertRaises(API.WorkflowError): API.plan_bytes(data)

    def test_target_paths_absolute_traversal_devices_ads_control_refused(self):
        for target in ("../file.ini", "C:/private.ini", "x\\file.ini", "CON.txt", "NUL", "x:ads", "/file.ini", "x/../file.ini", "x\n.ini", "x."):
            r = complete(); r["changes"][0]["target"] = target
            with self.assertRaises(API.WorkflowError): self.plan(r)

    def test_duplicate_targets_case_insensitive_refused(self):
        r = complete(); c = deepcopy(r["changes"][0]); c.update(id="Another", target=c["target"].upper()); r["changes"].append(c)
        with self.assertRaises(API.WorkflowError): self.plan(r)

    def test_count_bounds_refused(self):
        r = complete(); r["resources"] *= API.MAX_ITEMS + 1
        with self.assertRaises(API.WorkflowError): self.plan(r)

    def test_inspection_read_only_and_pin_drift_refused(self):
        before = self.source.read_bytes()
        self.assertEqual(API.inspect_source(self.source, self.sha)["source_sha256"], self.sha)
        self.assertEqual(self.source.read_bytes(), before)
        self.source.write_bytes(before + b' ')
        with self.assertRaises(API.WorkflowError): API.inspect_source(self.source, self.sha)

    def test_export_new_portable_file_byte_verified_no_source_mutation(self):
        output = self.folder / "plan.json"
        before = self.source.read_bytes()
        result = API.export_plan(self.source, output, self.sha)
        self.assertEqual(result["export_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(json.loads(output.read_bytes())["execution"], "none")
        self.assertFalse(result["restore_tested"])

    def test_export_existing_no_overwrite_or_missing_pin(self):
        output = self.folder / "plan.json"; output.write_bytes(b"ORIGINAL")
        for digest in (self.sha, None, "e" * 64):
            with self.assertRaises(API.WorkflowError): API.export_plan(self.source, output, digest)
        self.assertEqual(output.read_bytes(), b"ORIGINAL")

    def test_export_in_repository_refused(self):
        output = ROOT / "not-created-workflow.json"
        with self.assertRaises(API.WorkflowError): API.export_plan(self.source, output, self.sha)
        self.assertFalse(output.exists())

    def test_export_unsafe_leaf_or_nonjson_refused(self):
        for leaf in ("CON.json", "file:stream.json", "not-a-plan.ahk", "newline\n.json"):
            with self.assertRaises(API.WorkflowError): API.export_plan(self.source, self.folder / leaf, self.sha)
        self.assertEqual(list(self.folder.iterdir()), [self.source])

    def test_post_publication_source_drift_removes_only_owned_output(self):
        output = self.folder / "plan.json"
        original = API._current
        calls = []
        def changed(*args):
            calls.append(1)
            if len(calls) == 2:
                self.source.write_bytes(self.source.read_bytes() + b' ')
            return original(*args)
        with patch.object(API, "_current", side_effect=changed):
            with self.assertRaises(API.WorkflowError): API.export_plan(self.source, output, self.sha)
        self.assertFalse(output.exists())

    def test_foreign_output_replacement_retained_after_failure(self):
        output = self.folder / "plan.json"
        original = API._current
        calls = []
        def changed(*args):
            calls.append(1)
            if len(calls) == 2:
                output.unlink(); output.write_bytes(b"FOREIGN_STATE")
                raise API.WorkflowError()
            return original(*args)
        with patch.object(API, "_current", side_effect=changed):
            with self.assertRaises(API.WorkflowError): API.export_plan(self.source, output, self.sha)
        self.assertEqual(output.read_bytes(), b"FOREIGN_STATE")

    def test_source_has_no_game_control_or_hidden_executor(self):
        tree = ast.parse((ROOT / "scripts/GameToolWorkflow.py").read_text())
        imports = {n.names[0].name for n in ast.walk(tree) if isinstance(n, ast.Import)}
        self.assertFalse(imports & {"subprocess", "socket", "ctypes", "keyboard", "pynput"})
        self.assertFalse(hasattr(API, "execute"))

    def test_coordinator_plan_compact_journal_owns_no_target(self):
        c = CORE.Coordinator(); self.addCleanup(c.close)
        journal = self.folder / "session.jsonl"
        c.start(journal)
        result = c.inspect_workflow(self.source, self.sha)
        self.assertEqual(result["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(c.status()["latest_action"]["capability"], "workflow")
        c.finish()
        events = journal.read_text()
        self.assertNotIn("example-layer.ini", events)
        self.assertNotIn(str(self.source), events)
        self.assertIn('"change_count":1', events)

    def test_coordinator_cancellation_blocks_result_acceptance(self):
        c = CORE.Coordinator(); self.addCleanup(c.close); c.start(self.folder / "cancel.jsonl")
        backend = c._module("workflow")
        original = backend.plan_bytes
        def cancelled(data):
            result = original(data); c.cancel(); return result
        with patch.object(backend, "plan_bytes", side_effect=cancelled):
            with self.assertRaises(CORE.CoordinatorError): c.inspect_workflow(self.source, self.sha)
        self.assertEqual(c.status()["state"], "cancelled")

    def test_coordinator_expiry_and_malformed_recipe_not_accepted(self):
        clock = [0.0]
        c = CORE.Coordinator(clock=lambda: clock[0], lifetime_seconds=1); self.addCleanup(c.close)
        c.start(self.folder / "expired.jsonl"); clock[0] = 2
        with self.assertRaises(CORE.CoordinatorError): c.inspect_workflow(self.source)
        other = CORE.Coordinator(); self.addCleanup(other.close); other.start(self.folder / "invalid.jsonl")
        self.source.write_bytes(b'{"command":"none"}')
        with self.assertRaises(CORE.CoordinatorError): other.inspect_workflow(self.source)
        self.assertEqual(other.status()["latest_action"]["state"], "failed")

    def test_source_drift_during_planning_refused(self):
        original = API.plan_bytes
        def changed(data):
            result = original(data); self.source.write_bytes(data + b' '); return result
        with patch.object(API, "plan_bytes", side_effect=changed):
            with self.assertRaises(API.WorkflowError): API.inspect_source(self.source)

    def test_same_bytes_new_source_object_refused(self):
        original = API.plan_bytes
        def changed(data):
            result = original(data)
            replacement = self.folder / "replacement.json"; replacement.write_bytes(data); replacement.replace(self.source)
            return result
        with patch.object(API, "plan_bytes", side_effect=changed):
            with self.assertRaises(API.WorkflowError): API.inspect_source(self.source)

    def test_shared_source_drift_refused(self):
        original = API._current
        with patch.object(API, "_current", side_effect=API.WorkflowError("SOURCE_CHANGED")):
            with self.assertRaises(API.WorkflowError): API.inspect_source(self.source)
        self.assertTrue(callable(original))

    def test_coordinator_invalid_backend_result_is_not_acknowledged(self):
        c = CORE.Coordinator(); self.addCleanup(c.close); c.start(self.folder / "invalid-result.jsonl")
        backend = c._module("workflow")
        with patch.object(backend, "plan_bytes", return_value={"status": "PASS", "runtime_verification": True}):
            with self.assertRaises(CORE.CoordinatorError): c.inspect_workflow(self.source)
        self.assertEqual(c.status()["latest_action"]["state"], "failed")

    def test_coordinator_drift_after_plan_is_not_accepted(self):
        c = CORE.Coordinator(); self.addCleanup(c.close); c.start(self.folder / "drift.jsonl")
        backend = c._module("workflow"); original = backend.plan_bytes
        def changed(data):
            result = original(data); self.source.write_bytes(data + b' '); return result
        with patch.object(backend, "plan_bytes", side_effect=changed):
            with self.assertRaises(CORE.CoordinatorError): c.inspect_workflow(self.source)
        self.assertEqual(c.status()["latest_action"]["state"], "failed")

    def test_coordinator_journal_ack_failure_poisoned_no_result(self):
        c = CORE.Coordinator(); self.addCleanup(c.close); c.start(self.folder / "ack.jsonl")
        original = c._journal.append
        def fail_observed(kind, data=None):
            if kind == "action_observed": raise OSError("PRIVATE_DISK_ERROR")
            return original(kind, data)
        with patch.object(c._journal, "append", side_effect=fail_observed):
            with self.assertRaises(CORE.CoordinatorError): c.inspect_workflow(self.source)
        self.assertEqual(c.status()["state"], "failed")


if __name__ == "__main__":
    unittest.main()
