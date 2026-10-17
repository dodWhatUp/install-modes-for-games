"""Offline session routes: no registry, providers, executable or game activity."""
from contextlib import ExitStack
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("session_cli_hub", SCRIPTS / "Game-Tool-Hub.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


class SessionCLIContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="offline-session-cli-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.report = self.directory / "summary.json"
        self.report.write_bytes((SCRIPTS.parent / "examples/game-tool-hub/import-fixtures/cyberpunk-summary.example.json").read_bytes())
        self.comparison = self.directory / "comparison.json"
        self.comparison.write_bytes((SCRIPTS.parent / "examples/game-tool-hub/comparison-fixture.example.json").read_bytes())
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.spies = []
        for name in ("load_tools", "inspect", "gui", "process_names", "read_afterburner", "read_rtss",
                     "configuration", "version_of", "import_report", "register_tool", "new_catalog_service"):
            self.spies.append(self.stack.enter_context(mock.patch.object(hub, name,
                side_effect=AssertionError("Forbidden external action: " + name))))
        self.spies.append(self.stack.enter_context(mock.patch.object(hub.os, "startfile", create=True,
            side_effect=AssertionError("Forbidden launch"))))
        for name in ("run", "Popen"):
            self.spies.append(self.stack.enter_context(mock.patch.object(hub.subprocess, name,
                side_effect=AssertionError("Forbidden child process"))))
        self.addCleanup(self.assert_no_external_calls)

    def assert_no_external_calls(self):
        for spy in self.spies:
            spy.assert_not_called()

    def call(self, arguments, code=0):
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            actual = hub.main(["--data-dir", str(self.directory / "unused-private-registry"), "session", *arguments])
        self.assertEqual(actual, code, output.getvalue())
        self.assertFalse((self.directory / "unused-private-registry").exists())
        return json.loads(output.getvalue())

    def digest(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def inspect_report(self, journal=None, digest=None):
        journal = journal or self.directory / "session.jsonl"
        result = self.call(["inspect-report", "--source", str(self.report), "--journal", str(journal),
                            "--expected-sha256", digest or self.digest(self.report)])
        return journal, result

    def test_capabilities_is_inert(self):
        before = {p.name: p.read_bytes() for p in self.directory.iterdir()}
        value = self.call(["capabilities"])
        self.assertIn("offline", json.dumps(value).lower())
        self.assertEqual({p.name: p.read_bytes() for p in self.directory.iterdir()}, before)

    def test_report_action_finishes_new_journal_and_retains_source(self):
        original = self.report.read_bytes()
        journal, result = self.inspect_report()
        self.assertEqual(result["session"]["state"], "finished")
        self.assertEqual(self.report.read_bytes(), original)
        self.assertNotIn(str(self.directory), json.dumps(result))
        value = self.call(["inspect", "--source", str(journal)])
        self.assertTrue(value["valid"])
        self.assertTrue(value["clean_end"])
        self.assertFalse(value["replay_allowed"])
        self.assertNotIn("verified_records", value)

    def test_comparison_action_reuses_offline_core(self):
        journal = self.directory / "comparison-session.jsonl"
        value = self.call(["compare", "--source", str(self.comparison), "--metric", "cpu",
                           "--journal", str(journal), "--expected-sha256", self.digest(self.comparison)])
        self.assertEqual(value["session"]["state"], "finished")
        self.assertIn("synthetic", json.dumps(value["action_result"]).lower())
        self.assertNotIn(str(self.directory), json.dumps(value))

    def test_wrong_source_hash_fails_and_does_not_execute(self):
        journal = self.directory / "hash-failure.jsonl"
        value = self.call(["inspect-report", "--source", str(self.report), "--journal", str(journal),
                           "--expected-sha256", "0" * 64], 2)
        self.assertFalse(value["valid"])
        self.assertFalse(value["replay_allowed"])

    def test_existing_journal_is_not_overwritten(self):
        journal, _ = self.inspect_report()
        original = journal.read_bytes()
        value = self.call(["inspect-report", "--source", str(self.report), "--journal", str(journal),
                           "--expected-sha256", self.digest(self.report)], 2)
        self.assertFalse(value["valid"])
        self.assertEqual(journal.read_bytes(), original)

    def test_invalid_lifetime_is_refused_before_journal_creation(self):
        journal = self.directory / "invalid-lifetime.jsonl"
        self.call(["inspect-report", "--source", str(self.report), "--journal", str(journal),
                   "--expected-sha256", self.digest(self.report), "--lifetime-seconds", "0"], 2)
        self.assertFalse(journal.exists())

    def test_optional_module_failure_is_structured(self):
        with mock.patch.object(hub, "load_catalog_module", side_effect=ImportError("fixture optional module")):
            value = self.call(["capabilities"], 2)
        self.assertFalse(value["valid"])

    def test_unknown_loader_error_does_not_export_private_locator(self):
        locator = str(self.directory / "private-module.py")
        with mock.patch.object(hub, "load_catalog_module", side_effect=OSError("Missing: " + locator)):
            value = self.call(["capabilities"], 2)
        self.assertNotIn(locator, json.dumps(value))
        self.assertEqual(value["error_code"], "SESSION_REQUEST_FAILED")

    def test_truncated_journal_inspection_has_failure_verdict(self):
        journal, _ = self.inspect_report()
        journal.write_bytes(journal.read_bytes() + b'{"partial":')
        before = journal.read_bytes()
        value = self.call(["inspect", "--source", str(journal)], 3)
        self.assertFalse(value["valid"])
        self.assertEqual(journal.read_bytes(), before)

    def test_recover_creates_evidence_copy_without_changing_source(self):
        journal, _ = self.inspect_report()
        journal.write_bytes(journal.read_bytes() + b'{"partial":')
        original = journal.read_bytes()
        recovered = self.directory / "recovered.jsonl"
        value = self.call(["recover", "--source", str(journal), "--output", str(recovered),
                           "--expected-sha256", self.digest(journal)])
        self.assertFalse(value["replay_allowed"])
        self.assertEqual(journal.read_bytes(), original)
        self.assertTrue(self.call(["inspect", "--source", str(recovered)])["valid"])

    def test_recover_refuses_stale_hash_and_existing_destination(self):
        journal, _ = self.inspect_report()
        recovered = self.directory / "existing.jsonl"
        recovered.write_bytes(b"owned by another operation")
        for expected in ("0" * 64, self.digest(journal)):
            self.call(["recover", "--source", str(journal), "--output", str(recovered),
                       "--expected-sha256", expected], 2)
        self.assertEqual(recovered.read_bytes(), b"owned by another operation")

    def test_inspection_summary_never_exports_metadata_payloads(self):
        value = hub.journal_summary({"valid": True, "verified_records": [{"data": {"private": "payload"}}],
                                     "private_source": "locator", "source_sha256": "f" * 64})
        self.assertNotIn("payload", json.dumps(value))
        self.assertNotIn("locator", json.dumps(value))


if __name__ == "__main__":
    unittest.main()
