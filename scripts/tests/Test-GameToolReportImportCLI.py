"""Offline saved-report CLI integration; temporary authored fixtures only."""
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
FIXTURES = SCRIPTS.parent / "examples/game-tool-hub/import-fixtures"
spec = importlib.util.spec_from_file_location("report_import_cli_hub", SCRIPTS / "Game-Tool-Hub.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


class SavedReportCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="saved-report-cli-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registry = self.directory / "tools.json"
        self.registry.write_bytes(b'{"fixture":"preserve registry"}')
        self.source = self.directory / "misleading-a-date-20000101.json"
        self.data = json.loads((FIXTURES / "cyberpunk-summary.example.json").read_bytes())
        self.source.write_text(json.dumps(self.data), encoding="utf-8")
        changed = json.loads(json.dumps(self.data))
        changed["Data"]["averageFps"] += 1
        self.other = self.directory / "misleading-baseline-date-20990101.json"
        self.other.write_text(json.dumps(changed), encoding="utf-8")
        self.csv = self.directory / "unknown-provider-date.csv"
        self.csv.write_bytes((FIXTURES / "presentmon-stats.example.csv").read_bytes())
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.forbidden = []
        for name in ("load_tools", "inspect", "gui", "process_names", "read_afterburner",
                     "read_rtss", "configuration", "import_report", "register_tool", "exclusive_json",
                     "new_catalog_service", "read_form_file"):
            self.forbidden.append(self.stack.enter_context(mock.patch.object(
                hub, name, side_effect=AssertionError("Forbidden external action: " + name))))
        for name in ("run", "Popen"):
            self.forbidden.append(self.stack.enter_context(mock.patch.object(
                hub.subprocess, name, side_effect=AssertionError("Forbidden process"))))
        self.forbidden.append(self.stack.enter_context(mock.patch.object(
            hub.os, "startfile", create=True, side_effect=AssertionError("Forbidden launch"))))
        self.addCleanup(self.assert_preserved)

    def assert_preserved(self):
        for spy in self.forbidden:
            spy.assert_not_called()
        self.assertEqual(self.registry.read_bytes(), b'{"fixture":"preserve registry"}')

    def call(self, args, expected=0):
        before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in (self.source, self.other, self.csv, self.registry)}
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            actual = hub.main(["--data-dir", str(self.directory), *args])
        self.assertEqual(actual, expected, output.getvalue())
        for name, (data, mtime) in before.items():
            path = self.directory / name
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), (data, mtime))
        result = json.loads(output.getvalue())
        self.assertEqual(result["execution"], "none")
        return result

    def inspect(self, path=None, extra=(), expected=0):
        return self.call(["inspect-saved-report", "--source", str(path or self.source), *extra], expected)

    def import_args(self, output=None):
        return ["import-saved-reports", "--baseline", str(self.source), "--a", str(self.other),
                "--output-directory", str(output or self.directory / "fresh-import")]

    def test_cyberpunk_preview_read_only_no_private_locator(self):
        names = set(self.directory.iterdir())
        result = self.inspect()
        self.assertEqual(result["adapter"], "cyberpunk_benchmark_summary")
        self.assertEqual(result["metrics"][0]["value"], self.data["Data"]["averageFps"])
        self.assertIsNone(result["coverage"]["started_utc"])
        self.assertNotIn("private_source", result)
        self.assertNotIn(str(self.directory), json.dumps(result))
        self.assertEqual(set(self.directory.iterdir()), names)

    def test_presentmon_keeps_provider_percentiles_not_lows(self):
        result = self.inspect(self.csv)
        self.assertEqual(result["adapter"], "presentmon_gui_stats")
        self.assertEqual(result["provider_version"], "unknown")
        metric = next(item for item in result["metrics"] if item["id"] == "pm_percentile_1_fps")
        self.assertEqual(metric["frame_class"], "presented_intervals")
        self.assertIn("not mean of slowest", metric["definition"])

    def test_import_creates_blocked_bundle_with_exact_originals(self):
        result = self.call(self.import_args(), 3)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["runtime_verification"])
        target = Path(result["bundle_path"])
        self.assertEqual((target / "source-001.json").read_bytes(), self.source.read_bytes())
        self.assertEqual((target / "source-002.json").read_bytes(), self.other.read_bytes())
        normalized = Path(result["dataset_path"]).read_bytes()
        self.assertEqual(hashlib.sha256(normalized).hexdigest(), result["dataset_sha256"])
        dataset = json.loads(normalized)
        self.assertEqual(dataset["origin"], "imported_report")
        self.assertEqual(dataset["measurement_scope"], "rendering")
        self.assertEqual([run["case"] for run in dataset["runs"]], ["baseline", "a"])
        self.assertNotIn(str(self.directory), json.dumps(dataset))
        for run in dataset["runs"]:
            self.assertEqual(run["fg"]["dynamic_mfg"], "unverified")
            self.assertEqual(run["fg"]["effective_mode"], "unknown")
            self.assertEqual(run["memory_warning"], "unverified")
            self.assertEqual(run["status"], "incomplete")
            self.assertIsNone(run["started_utc"])
            self.assertIsNone(run["configuration"]["fingerprint"])
            self.assertIn("not evidence of a provider-run crash", run["failure_reason"])
        comparison = self.call(["compare-report", "--source", result["dataset_path"]], 3)
        self.assertEqual(comparison["comparisons"], [])
        self.assertIn("RUNTIME_FG_UNVERIFIED", {gate["code"] for gate in comparison["gates"]})

    def test_repeated_arguments_and_explicit_factor(self):
        result = self.call(["import-saved-reports", "--baseline", str(self.source),
                           "--baseline", str(self.other), "--a", str(self.csv),
                           "--output-directory", str(self.directory / "repeats"),
                           "--title", "Declared conditions", "--factor", "my_factor"], 3)
        dataset = json.loads(Path(result["dataset_path"]).read_bytes())
        self.assertEqual([run["repeat"] for run in dataset["runs"]], [1, 2, 1])
        self.assertEqual(dataset["experiment"]["factors"], ["my_factor"])
        self.assertEqual(dataset["title"], "Declared conditions")

    def test_existing_directory_preserved(self):
        target = self.directory / "existing"
        target.mkdir()
        marker = target / "preserve.txt"
        marker.write_bytes(b"preserve bytes")
        result = self.call(self.import_args(target), 2)
        self.assertFalse(result["valid"])
        self.assertEqual(list(target.iterdir()), [marker])
        self.assertEqual(marker.read_bytes(), b"preserve bytes")

    def test_existing_file_destination_preserved(self):
        result = self.call(self.import_args(self.source), 2)
        self.assertFalse(result["valid"])

    def test_duplicate_report_assignments_refused_before_output(self):
        args = self.import_args()
        args[4] = str(self.source)
        self.assertFalse(self.call(args, 2)["valid"])
        self.assertFalse((self.directory / "fresh-import").exists())

    def test_no_assignments_refused(self):
        result = self.call(["import-saved-reports", "--output-directory", str(self.directory / "empty")], 2)
        self.assertFalse(result["valid"])
        self.assertFalse((self.directory / "empty").exists())

    def test_invalid_factor_refused_before_output(self):
        result = self.call([*self.import_args(), "--factor", "not a stable factor"], 2)
        self.assertFalse(result["valid"])
        self.assertFalse((self.directory / "fresh-import").exists())

    def test_unknown_json_summary_refused(self):
        self.source.write_bytes(b'{"arbitrary":"not a provider summary"}')
        self.assertFalse(self.inspect(expected=2)["valid"])

    def test_raw_frame_csv_refused(self):
        self.csv.write_bytes(b"Application,ProcessID,CPUStartTime,FrameTime\nfixture,1,0,16.6\n")
        result = self.inspect(self.csv, expected=2)
        self.assertFalse(result["valid"])
        self.assertIn("not a summary", result["error"])

    def test_wrong_explicit_adapter_refused(self):
        result = self.inspect(extra=["--adapter", "presentmon_gui_stats"], expected=2)
        self.assertFalse(result["valid"])

    def test_oversized_json_integer_is_structured_refusal(self):
        self.data["Data"]["averageFps"] = 10 ** 400
        self.source.write_text(json.dumps(self.data), encoding="utf-8")
        result = self.inspect(expected=2)
        self.assertFalse(result["valid"])
        self.assertNotIn(str(self.directory), result["error"])

    def test_missing_source_refused_without_locator(self):
        result = self.inspect(self.directory / "missing-private-file.json", expected=2)
        self.assertFalse(result["valid"])
        self.assertNotIn(str(self.directory), result["error"])

    def test_utf8_bom_supported_without_rewrite(self):
        self.source.write_bytes(b"\xef\xbb\xbf" + self.source.read_bytes())
        result = self.inspect()
        self.assertEqual(result["adapter"], "cyberpunk_benchmark_summary")

    def test_optional_importer_unavailable_is_contained(self):
        with mock.patch.object(hub, "load_catalog_module", side_effect=ImportError("Fixture unavailable")):
            result = self.inspect(expected=2)
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
