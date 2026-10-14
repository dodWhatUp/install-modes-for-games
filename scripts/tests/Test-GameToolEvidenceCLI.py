"""Offline CLI contracts with all providers, launches and registry routes forbidden."""
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
spec = importlib.util.spec_from_file_location("saved_evidence_cli_hub", SCRIPTS / "Game-Tool-Hub.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


class EvidenceCLIContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="saved-evidence-cli-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "opaque.log"
        self.source.write_text("PRIVATE_MESSAGE", encoding="utf-8")
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.spies = []
        for name in ("load_tools", "inspect", "gui", "process_names", "read_afterburner", "read_rtss",
                     "configuration", "version_of", "import_report", "register_tool", "new_catalog_service", "read_form_file"):
            self.spies.append(self.stack.enter_context(mock.patch.object(hub, name, side_effect=AssertionError(name))))
        self.spies.append(self.stack.enter_context(mock.patch.object(hub.os, "startfile", create=True,
                         side_effect=AssertionError("launch"))))
        for name in ("run", "Popen"):
            self.spies.append(self.stack.enter_context(mock.patch.object(hub.subprocess, name, side_effect=AssertionError(name))))
        self.addCleanup(self.assert_inert)

    def assert_inert(self):
        for spy in self.spies:
            spy.assert_not_called()
        self.assertFalse((self.directory / "unused-registry").exists())

    def call(self, args, code=0):
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            actual = hub.main(["--data-dir", str(self.directory / "unused-registry"), *args])
        self.assertEqual(actual, code, output.getvalue())
        value = json.loads(output.getvalue())
        self.assertNotIn("PRIVATE_MESSAGE", output.getvalue())
        self.assertNotIn(str(self.directory), output.getvalue())
        return value

    def test_inspect_is_read_only_and_portable(self):
        before = self.source.read_bytes(), self.source.stat().st_mtime_ns
        value = self.call(["saved-evidence", "inspect", "--source", str(self.source)])
        self.assertEqual(value["status"], "EVIDENCE_ONLY")
        self.assertEqual(value["timeline"], [])
        self.assertEqual((self.source.read_bytes(), self.source.stat().st_mtime_ns), before)
        self.assertEqual(list(self.directory.iterdir()), [self.source])

    def test_packet_creates_only_requested_new_private_directory(self):
        target = self.directory / "packet"
        value = self.call(["saved-evidence", "packet", "--source", str(self.source), "--output-directory", str(target)])
        self.assertEqual(value["source_count"], 1)
        self.assertEqual((target / "source-001.txt").read_bytes(), self.source.read_bytes())
        self.assertTrue((target / "manifest.json").exists())

    def test_existing_destination_refused(self):
        self.call(["saved-evidence", "packet", "--source", str(self.source), "--output-directory", str(self.directory)], 2)

    def test_wrong_expected_hash_refused_before_output(self):
        target = self.directory / "packet"
        self.call(["saved-evidence", "packet", "--source", str(self.source), "--expected-sha256", "0" * 64,
                   "--output-directory", str(target)], 2)
        self.assertFalse(target.exists())

    def test_one_expected_hash_per_source_required(self):
        self.call(["saved-evidence", "inspect", "--source", str(self.source), "--source", str(self.source),
                   "--expected-sha256", "0" * 64], 2)

    def test_duplicate_sources_refused(self):
        self.call(["saved-evidence", "inspect", "--source", str(self.source), "--source", str(self.source)], 2)

    def test_missing_source_fixed_error(self):
        value = self.call(["saved-evidence", "inspect", "--source", str(self.directory / "missing.xml")], 2)
        self.assertEqual(value["error_code"], "SAVED_EVIDENCE_REFUSED")

    def test_optional_module_error_does_not_expose_exception(self):
        with mock.patch.object(hub, "load_catalog_module", side_effect=ImportError("PRIVATE_MESSAGE")):
            self.call(["saved-evidence", "inspect", "--source", str(self.source)], 2)

    def test_session_inspection_finishes_journal_without_raw_evidence(self):
        target = self.directory / "task.jsonl"
        digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        value = self.call(["session", "inspect-evidence", "--source", str(self.source),
                           "--expected-sha256", digest, "--journal", str(target)])
        self.assertEqual(value["session"]["state"], "finished")
        self.assertFalse(value["session"]["writer_open"])
        self.assertEqual(value["session"]["latest_action"]["capability"], "crash_evidence")
        self.assertNotIn("PRIVATE_MESSAGE", target.read_text(encoding="utf-8"))

    def test_session_wrong_hash_records_failure_not_success(self):
        self.call(["session", "inspect-evidence", "--source", str(self.source),
                   "--expected-sha256", "0" * 64, "--journal", str(self.directory / "task.jsonl")], 2)

    def test_session_existing_journal_not_overwritten(self):
        path = self.directory / "old.jsonl"
        path.write_bytes(b"KEEP")
        self.call(["session", "inspect-evidence", "--source", str(self.source),
                   "--expected-sha256", "0" * 64, "--journal", str(path)], 2)
        self.assertEqual(path.read_bytes(), b"KEEP")

    def test_invalid_arguments_do_not_fall_through_to_gui(self):
        with mock.patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
            hub.main(["saved-evidence", "inspect"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
