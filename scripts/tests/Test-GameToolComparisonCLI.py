"""Offline Hub CLI contracts; no providers, processes, clipboard or GUI."""
from contextlib import ExitStack
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
EXAMPLE = SCRIPTS.parent / "examples/game-tool-hub/comparison-fixture.example.json"
spec = importlib.util.spec_from_file_location("comparison_cli_hub", SCRIPTS / "Game-Tool-Hub.py")
hub = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hub)


class CLIContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="comparison-cli-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "source.json"
        self.data = json.loads(EXAMPLE.read_bytes())
        self.save_source()
        self.registry = self.directory / "tools.json"
        self.registry.write_bytes(b'{"fixture":"must remain unchanged"}')
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
                hub.subprocess, name, side_effect=AssertionError("Forbidden child process"))))
        self.forbidden.append(self.stack.enter_context(mock.patch.object(
            hub.os, "startfile", create=True, side_effect=AssertionError("Forbidden launch"))))
        self.addCleanup(self.assert_no_external_calls)

    def assert_no_external_calls(self):
        for spy in self.forbidden:
            spy.assert_not_called()
        self.assertEqual(self.registry.read_bytes(), b'{"fixture":"must remain unchanged"}')

    def save_source(self):
        self.source.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")

    def call(self, extra=(), code=0):
        before = self.source.read_bytes()
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            actual = hub.main(["--data-dir", str(self.directory), "compare-report",
                               "--source", str(self.source), *extra])
        self.assertEqual(actual, code, output.getvalue())
        self.assertEqual(self.source.read_bytes(), before)
        result = json.loads(output.getvalue())
        self.assertEqual(result["execution"], "none")
        return result

    def test_comparable_fixture_never_reads_registry_or_providers(self):
        result = self.call()
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertTrue(result["synthetic_fixture"])
        self.assertFalse(result["runtime_verification"])
        self.assertNotIn(str(self.directory), json.dumps(result))

    def test_real_rendering_declarations_return_blocked_exit_three(self):
        self.data["origin"] = "imported_report"
        self.data["measurement_scope"] = "rendering"
        self.save_source()
        result = self.call(code=3)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["comparisons"], [])
        self.assertIn("RUNTIME_FG_UNVERIFIED", {gate["code"] for gate in result["gates"]})

    def test_metric_selection_applies_to_stdout_and_json_export(self):
        selected = self.data["metrics"][0]["id"]
        target = self.directory / "new-report.json"
        result = self.call(["--metric", selected, "--output", str(target)])
        exported = json.loads(target.read_bytes())
        self.assertEqual([metric["id"] for metric in result["metrics"]], [selected])
        self.assertEqual(exported, {key: value for key, value in result.items() if key != "export_receipt"})
        self.assertEqual(result["export_receipt"]["bytes"], target.stat().st_size)

    def test_invalid_metric_is_refused_without_output(self):
        target = self.directory / "refused.json"
        result = self.call(["--metric", "undefined-fixture-metric", "--output", str(target)], code=2)
        self.assertFalse(result["valid"])
        self.assertFalse(target.exists())

    def test_existing_destination_is_not_overwritten(self):
        target = self.directory / "existing.json"
        target.write_bytes(b"preserve existing bytes")
        self.call(["--output", str(target)], code=2)
        self.assertEqual(target.read_bytes(), b"preserve existing bytes")

    def test_source_cannot_be_export_destination(self):
        self.call(["--output", str(self.source)], code=2)

    def test_blocked_html_export_retains_raw_evidence(self):
        self.data["origin"] = "imported_report"
        self.data["measurement_scope"] = "rendering"
        self.save_source()
        target = self.directory / "blocked.html"
        result = self.call(["--output", str(target), "--format", "html"], code=3)
        text = target.read_text(encoding="utf-8")
        self.assertIn("RUNTIME_FG_UNVERIFIED", text)
        self.assertIn("All retained runs", text)
        self.assertEqual(result["export_receipt"]["status"], "BLOCKED")
        self.assertNotIn("<script", text.lower())

    def test_invalid_json_is_contained(self):
        self.source.write_bytes(b'{"invalid":')
        result = self.call(code=2)
        self.assertFalse(result["valid"])

    def test_optional_backend_failure_is_contained(self):
        with mock.patch.object(hub, "load_catalog_module", side_effect=ImportError("Fixture unavailable")):
            result = self.call(code=2)
        self.assertFalse(result["valid"])


if __name__ == "__main__":
    unittest.main()
