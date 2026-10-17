"""Offline CLI contract; providers, registry, launches and UI are forbidden."""
from contextlib import redirect_stdout, ExitStack
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("workflow_cli", ROOT / "scripts/Game-Tool-Hub.py")
HUB = importlib.util.module_from_spec(spec); spec.loader.exec_module(HUB)


class CliContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="workflow-cli-"); self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "recipe.json"
        self.source.write_bytes((ROOT / "examples/game-tool-hub/workflow-installation.example.json").read_bytes())
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        for name in ("load_tools", "read_rtss", "read_afterburner", "process_names", "gui", "launch_allowed"):
            self.stack.enter_context(patch.object(HUB, name, side_effect=AssertionError("live action forbidden")))

    def invoke(self, args):
        out = io.StringIO()
        with redirect_stdout(out): status = HUB.main(args)
        return status, json.loads(out.getvalue())

    def test_inspect_returns_blocked_without_live_reads_or_new_files(self):
        status, result = self.invoke(["workflow", "inspect", "--source", str(self.source)])
        self.assertEqual(status, 3); self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(list(self.directory.iterdir()), [self.source]); self.assertFalse(result["runtime_verification"])

    def test_inspect_expected_hash_mismatch_refused(self):
        status, result = self.invoke(["workflow", "inspect", "--source", str(self.source), "--expected-sha256", "0" * 64])
        self.assertEqual(status, 2); self.assertEqual(result["error_code"], "WORKFLOW_REFUSED")

    def test_export_pinned_portable_new_file(self):
        output = self.directory / "plan.json"
        status, result = self.invoke(["workflow", "export", "--source", str(self.source), "--expected-sha256", self.sha, "--output", str(output)])
        self.assertEqual(status, 3); self.assertTrue(output.exists())
        self.assertNotIn("example-layer.ini", output.read_text()); self.assertEqual(result["coverage"], "portable_plan_only")

    def test_export_existing_no_overwrite(self):
        output = self.directory / "plan.json"; output.write_bytes(b"ORIGINAL")
        status, result = self.invoke(["workflow", "export", "--source", str(self.source), "--expected-sha256", self.sha, "--output", str(output)])
        self.assertEqual(status, 2); self.assertEqual(output.read_bytes(), b"ORIGINAL")

    def test_session_workflow_compact_journal_and_terminal_state(self):
        journal = self.directory / "session.jsonl"
        status, result = self.invoke(["session", "inspect-workflow", "--source", str(self.source), "--expected-sha256", self.sha, "--journal", str(journal)])
        self.assertEqual(status, 3); self.assertEqual(result["session"]["state"], "finished")
        self.assertFalse(result["session"]["writer_open"])
        self.assertNotIn("example-layer.ini", journal.read_text()); self.assertNotIn(str(self.source), journal.read_text())

    def test_session_existing_journal_refused(self):
        journal = self.directory / "session.jsonl"; journal.write_bytes(b"ORIGINAL")
        status, _ = self.invoke(["session", "inspect-workflow", "--source", str(self.source), "--expected-sha256", self.sha, "--journal", str(journal)])
        self.assertEqual(status, 2); self.assertEqual(journal.read_bytes(), b"ORIGINAL")

    def test_unavailable_module_errors_are_fixed_path_free(self):
        with patch.object(HUB, "load_catalog_module", side_effect=ImportError("PRIVATE_EXCEPTION " + str(self.directory))):
            status, result = self.invoke(["workflow", "inspect", "--source", str(self.source)])
        self.assertEqual(status, 2); self.assertNotIn("PRIVATE_EXCEPTION", json.dumps(result)); self.assertNotIn(str(self.directory), json.dumps(result))

    def test_recipe_selected_code_is_refused(self):
        self.source.write_bytes(b'{"module":"arbitrary","command":"arbitrary"}')
        status, result = self.invoke(["workflow", "inspect", "--source", str(self.source)])
        self.assertEqual(status, 2); self.assertEqual(result["execution"], "none")

    def test_capabilities_fixed_workflow_no_execution_route(self):
        status, result = self.invoke(["session", "capabilities"])
        self.assertEqual(status, 0); self.assertEqual(result["capabilities"]["workflow"]["operation"], "inspect_workflow")
        self.assertIn("arbitrary_commands", result["unavailable"])

    def test_inspect_output_paths_and_raw_identifiers_excluded(self):
        _, result = self.invoke(["workflow", "inspect", "--source", str(self.source)])
        for text in (str(self.directory), "ExampleLayer", "example-layer.ini"):
            self.assertNotIn(text, json.dumps(result))


if __name__ == "__main__":
    unittest.main()
