"""Withdrawn Tk comparison contracts; no desktop focus or live providers.

Fixture-only core supplies defined summaries for widget callbacks. Genuine core
schema/arithmetic/source contracts are tested separately; these tests establish
native Tk behavior, not game performance or benchmark acceptance.
"""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("comparison_panel_contracts", SCRIPTS / "GameToolComparisonPanel.py")
panel_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel_module)


def fixture_result(status="COMPARABLE", synthetic=True):
    descriptor = {"id": "private_bytes", "label": "Process private commit", "unit": "MiB",
                  "scope": "process-private-commit", "provider": "fixture only", "definition": "Not measured"}
    runs = [{"id": f"{case}-{repeat}", "case": case, "repeat": repeat, "status": "complete",
             "source_sha256": hashlib.sha256(f"{case}-{repeat}".encode()).hexdigest(),
             "metrics": {"private_bytes": value + repeat}, "metric_definitions": {"private_bytes": descriptor},
             "failure_reason": None, "workload": {"phase": "idle"}}
            for case, value in (("baseline", 10), ("a", 15)) for repeat in range(1, 4)]
    return {"schema_version": 1, "status": status, "execution": "none", "synthetic_fixture": synthetic,
            "raw_runs": runs, "metrics": [descriptor],
            "case_summaries": [] if status == "BLOCKED" else [
                {"metric_id": "private_bytes", "case": "baseline", "n": 3, "mean": 12, "min": 11, "max": 13},
                {"metric_id": "private_bytes", "case": "a", "n": 3, "mean": 17, "min": 16, "max": 18}],
            "comparisons": [] if status == "BLOCKED" else [
                {"metric_id": "private_bytes", "contrast": "a - baseline", "delta": 5,
                 "percent": 100 * 5 / 12, "unit": "MiB"}],
            "gates": [{"code": "fixture", "message": "Synthetic only", "run_id": None, "metric_id": None}],
            "warnings": ["Not measured resource costs"],
            "provenance": {"normalized_bytes_verified": True, "report_hashes": "declared_only",
                           "runtime_verification": False}}


class FixtureCore:
    """Only the fixture source is read; no registry, telemetry or game route."""

    def __init__(self, result=None):
        self.result = result or fixture_result()
        self.load_calls = []
        self.comparison_calls = []
        self.export_calls = []

    def load_dataset(self, path):
        path = Path(path)
        raw = path.read_bytes()
        parsed = json.loads(raw)
        if parsed != {"fixture": "explicit normalized dataset"}:
            raise ValueError("Invalid fixture source")
        self.load_calls.append(path)
        parsed["_source"] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
        return parsed

    def compare_dataset(self, dataset, metric_id=None):
        self.comparison_calls.append(dataset)
        return copy.deepcopy(self.result)

    def assert_source_current(self, path, expected_sha256):
        raw = Path(path).read_bytes()
        current = hashlib.sha256(raw).hexdigest()
        if current != expected_sha256:
            raise ValueError("Source drift")
        return current

    def export_report(self, source_path, output_path, format="json", expected_sha256=None, metric_id=None):
        self.assert_source_current(source_path, expected_sha256)
        self.export_calls.append((source_path, Path(output_path), format, expected_sha256, metric_id))
        payload = json.dumps(self.result).encode() if format == "json" else b"<!doctype html><title>Fixture only</title>"
        with Path(output_path).open("xb") as stream:
            stream.write(payload)
        return {"path": str(output_path), "sha256": hashlib.sha256(payload).hexdigest(), "status": self.result["status"]}


class SourceLoaderContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="comparison-loader-fixtures-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "GameToolComparison.py"
        self.relocation = mock.patch.object(panel_module, "__file__", str(self.directory / "GameToolComparisonPanel.py"))
        self.relocation.start()
        self.addCleanup(self.relocation.stop)

    def test_fixed_sibling_captured_source_loads_without_bytecode_cache(self):
        self.source.write_bytes(b"FIXTURE = 'captured bytes'\n")
        module = panel_module._load_core()
        self.assertEqual(module.FIXTURE, "captured bytes")
        self.assertFalse((self.directory / "__pycache__").exists())

    def test_missing_sibling_refuses_without_loading_other_filename(self):
        (self.directory / "arbitrary.py").write_bytes(b"raise AssertionError('must not run')\n")
        with self.assertRaises(FileNotFoundError):
            panel_module._load_core()

    def test_oversized_source_is_refused_before_any_execution(self):
        self.source.write_bytes(b"raise AssertionError('must not execute')\n" + b"#" * (1024 * 1024))
        with self.assertRaisesRegex(ValueError, "source limit"):
            panel_module._load_core()

    def test_source_must_be_utf8_and_syntax_failure_is_not_fallback_execution(self):
        self.source.write_bytes(b"#\xff\n")
        with self.assertRaises(UnicodeDecodeError):
            panel_module._load_core()
        self.source.write_bytes(b"this is invalid syntax :\n")
        with self.assertRaises(SyntaxError):
            panel_module._load_core()

    def test_source_metadata_drift_refuses_before_execution(self):
        self.source.write_bytes(b"raise AssertionError('must not execute changed source')\n")
        original = Path.stat
        observations = []

        def changed_stat(path, *args, **kwargs):
            actual = original(path, *args, **kwargs)
            observations.append(path)
            return SimpleNamespace(st_size=actual.st_size, st_mtime_ns=actual.st_mtime_ns,
                                   st_ctime_ns=actual.st_ctime_ns + (1 if len(observations) > 1 else 0))

        with mock.patch.object(Path, "stat", autospec=True, side_effect=changed_stat):
            with self.assertRaisesRegex(ValueError, "changed while loading"):
                panel_module._load_core()


class NativeTkContracts(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk = tk, ttk
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Native Tk unavailable; widget acceptance not established: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.temp = tempfile.TemporaryDirectory(prefix="comparison-panel-fixtures-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "fixture.json"
        self.raw = b'{"fixture":"explicit normalized dataset"}'
        self.source.write_bytes(self.raw)
        self.parent = ttk.Frame(self.root)
        self.parent.pack(fill="both", expand=True)
        self.status = tk.StringVar(master=self.root)
        self.core = FixtureCore()
        self.safety = ExitStack()
        self.addCleanup(self.safety.close)
        self.clipboard = []
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_clear", side_effect=self.clipboard.clear))
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_append", side_effect=self.clipboard.append))
        self.panel = panel_module.ComparisonPanel(self.parent, self.status, core=self.core)

    def load(self):
        self.assertTrue(self.panel.load_from_path(self.source))

    def choose_metric(self, identifier):
        self.panel.metric.set(next(label for label, value in self.panel.metric_ids.items() if value == identifier))
        self.panel.metric_combo.event_generate("<<ComboboxSelected>>", when="now")

    def test_constructor_reads_nothing_and_keeps_test_root_withdrawn(self):
        self.assertEqual(self.root.state(), "withdrawn")
        self.assertEqual(self.core.load_calls, [])
        self.assertEqual(self.core.export_calls, [])
        self.assertEqual(self.clipboard, [])
        self.assertIsNone(self.panel.result)
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())

    def test_tabs_and_all_scrolled_read_only_views_exist(self):
        self.assertEqual([self.panel.tabs.tab(tab, "text") for tab in self.panel.tabs.tabs()],
                         ["Case summaries and contrasts", "Raw runs and blockers", "Definitions and provenance"])
        for text in (self.panel.run_text, self.panel.provenance_text):
            self.assertEqual(text.cget("state"), "disabled")
            self.assertEqual(text.cget("wrap"), "none")
            self.assertTrue(text.cget("yscrollcommand"))
            self.assertTrue(text.cget("xscrollcommand"))
        for tree in (self.panel.case_tree, self.panel.contrast_tree, self.panel.raw_tree):
            self.assertTrue(tree.cget("yscrollcommand"))
            self.assertTrue(tree.cget("xscrollcommand"))

    def test_load_is_explicit_and_synthetic_banner_never_calls_it_measured(self):
        self.load()
        self.assertEqual(self.core.load_calls, [self.source])
        self.assertIn("SYNTHETIC FIXTURE", self.panel.verdict.get())
        self.assertIn("NOT MEASURED", self.panel.verdict.get())
        self.assertEqual(len(self.panel.raw_tree.get_children()), 6)
        self.assertEqual(len(self.panel.case_tree.get_children()), 2)
        self.assertEqual(len(self.panel.contrast_tree.get_children()), 1)
        self.assertEqual(len(self.panel.chart.find_withtag("bar")), 2)
        self.assertIn(hashlib.sha256(self.raw).hexdigest(), self.panel.source.get())

    def test_large_warning_list_does_not_expand_header_and_hide_all_views(self):
        self.core.result["warnings"] = ["Fixture warning " + "x" * 1000 for _ in range(256)]
        self.load()
        self.assertLess(len(self.panel.verdict.get()), 300)
        self.assertIn("Fixture warning", self.panel.run_text.get("1.0", "end"))

    def test_metric_combobox_preserves_provider_label_unit_and_scope_in_details(self):
        self.load()
        self.assertIn("[MiB]", self.panel.metric.get())
        self.assertIn("private-commit", self.panel.provenance_text.get("1.0", "end"))
        self.assertIn("report_hashes", self.panel.provenance_text.get("1.0", "end"))

    def test_selected_run_detail_preserves_raw_and_definition_without_altering_source(self):
        self.load()
        self.panel.raw_tree.selection_set("run-0")
        self.panel.raw_tree.event_generate("<<TreeviewSelect>>", when="now")
        detail = json.loads(self.panel.run_text.get("1.0", "end"))
        self.assertEqual(detail["run"]["id"], "baseline-1")
        self.assertFalse(detail["historical_only"])
        self.assertEqual(detail["run"]["metrics"]["private_bytes"], 11)
        self.assertIn("metric_definitions", detail["run"])
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_blocked_runs_keep_raw_values_and_reasons_without_numeric_deltas(self):
        self.core.result = fixture_result("BLOCKED", synthetic=False)
        self.core.result["gates"] = [{"code": "unverified_effective_fg", "message": "Dynamic MFG unknown",
                                      "run_id": None, "metric_id": None}]
        self.load()
        self.assertIn("BLOCKED", self.panel.verdict.get())
        self.assertEqual(len(self.panel.raw_tree.get_children()), 6)
        self.assertEqual(self.panel.raw_tree.item("run-0", "values")[-1], "11")
        self.assertEqual(self.panel.case_tree.get_children(), ())
        self.assertEqual(self.panel.contrast_tree.get_children(), ())
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertIn("Dynamic MFG unknown", self.panel.run_text.get("1.0", "end"))

    def test_partial_result_charts_only_core_valid_metric(self):
        self.core.result["status"] = "PARTIAL"
        self.core.result["metrics"].append({"id": "missing_vram", "label": "VRAM unknown", "unit": "MiB"})
        self.load()
        self.assertEqual(len(self.panel.chart.find_withtag("bar")), 2)
        self.choose_metric("missing_vram")
        self.assertEqual(self.panel.case_tree.get_children(), ())
        self.assertEqual(self.panel.contrast_tree.get_children(), ())
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertEqual(self.panel.raw_tree.item("run-0", "values")[-1], "unavailable")

    def test_zero_stays_zero_and_null_stays_unavailable(self):
        self.core.result["raw_runs"][0]["metrics"]["private_bytes"] = None
        self.core.result["raw_runs"][1]["metrics"]["private_bytes"] = 0
        self.core.result["comparisons"][0]["percent"] = None
        self.load()
        self.assertEqual(self.panel.raw_tree.item("run-0", "values")[-1], "unavailable")
        self.assertEqual(self.panel.raw_tree.item("run-1", "values")[-1], "0")
        contrast = self.panel.contrast_tree.get_children()[0]
        self.assertEqual(self.panel.contrast_tree.item(contrast, "values")[-1], "unavailable")

    def test_chart_signed_values_do_not_use_absolute_costs(self):
        self.core.result["case_summaries"][0].update(mean=-12, min=-13, max=-11)
        self.load()
        bars = [self.panel.chart.coords(item) for item in self.panel.chart.find_withtag("bar")]
        self.assertEqual(len(bars), 2)
        self.assertAlmostEqual(bars[0][2], bars[1][0])
        texts = [self.panel.chart.itemcget(item, "text") for item in self.panel.chart.find_withtag("value")]
        self.assertTrue(any("-12" in text for text in texts))

    def test_copy_button_uses_mocked_clipboard_current_recomputed_result(self):
        self.load()
        self.panel.buttons["Copy summary"].invoke()
        self.assertEqual(len(self.clipboard), 1)
        copied = json.loads(self.clipboard[0])
        self.assertEqual(copied["status"], "COMPARABLE")
        self.assertEqual(copied["execution"], "none")
        self.assertTrue(copied["synthetic_fixture"])
        self.assertNotIn(str(self.directory), self.clipboard[0])

    def test_copy_recomputes_the_selected_metric_instead_of_a_stored_verdict(self):
        self.load()
        with mock.patch.object(self.core, "compare_dataset", wraps=self.core.compare_dataset) as compare:
            self.assertTrue(self.panel.copy_summary())
        compare.assert_called_once_with(self.panel.dataset, metric_id="private_bytes")

    def test_blocked_summary_can_be_copied_as_blocked_report(self):
        self.core.result = fixture_result("BLOCKED")
        self.load()
        self.assertTrue(self.panel.copy_summary())
        self.assertEqual(json.loads(self.clipboard[0])["comparisons"], [])

    def test_source_drift_blocks_copy_and_chart_but_preserves_historical_raw(self):
        self.load()
        self.source.write_bytes(self.raw + b" ")
        self.assertFalse(self.panel.copy_summary())
        self.assertEqual(self.clipboard, [])
        self.assertTrue(self.panel.stale)
        self.assertIn("STALE", self.panel.verdict.get())
        self.assertEqual(self.panel.case_tree.get_children(), ())
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertEqual(len(self.panel.raw_tree.get_children()), 6)
        self.panel.raw_tree.selection_set("run-0")
        self.panel.show_run()
        self.assertTrue(json.loads(self.panel.run_text.get("1.0", "end"))["historical_only"])

    def test_source_drift_on_metric_change_requires_explicit_reload(self):
        self.load()
        self.source.write_bytes(self.raw + b" ")
        self.panel.metric_combo.event_generate("<<ComboboxSelected>>", when="now")
        self.assertTrue(self.panel.stale)
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.panel.buttons["Reload source"].invoke()
        self.assertFalse(self.panel.stale)
        self.assertEqual(len(self.panel.chart.find_withtag("bar")), 2)

    def test_chart_redraw_after_source_drift_never_reuses_numeric_cached_verdict(self):
        self.load()
        self.source.write_bytes(self.raw + b" ")
        # Withdrawn windows have no OS resize event. Exercise the exact bound
        # callback explicitly while retaining native Canvas/readback coverage.
        self.assertIn("_draw_chart", self.panel.chart.bind("<Configure>"))
        self.panel._draw_chart(SimpleNamespace(widget=self.panel.chart))
        self.assertTrue(self.panel.stale)
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertEqual(self.panel.case_tree.get_children(), ())
        self.assertEqual(self.panel.contrast_tree.get_children(), ())
        self.assertEqual(len(self.panel.raw_tree.get_children()), 6)

    def test_missing_source_blocks_export_without_writing_target(self):
        self.load()
        self.source.unlink()
        target = self.directory / "not-created.json"
        self.assertIsNone(self.panel.export_to_path(target))
        self.assertFalse(target.exists())
        self.assertEqual(self.core.export_calls, [])

    def test_json_and_html_export_buttons_use_dialog_selected_new_paths(self):
        self.load()
        from tkinter import filedialog
        for format in ("json", "html"):
            target = self.directory / f"report.{format}"
            with mock.patch.object(filedialog, "asksaveasfilename", return_value=str(target)) as dialog:
                self.panel.buttons[f"Export {format.upper()}"].invoke()
            self.assertTrue(target.exists())
            self.assertEqual(dialog.call_args.kwargs["parent"], self.root)
            self.assertFalse(dialog.call_args.kwargs["confirmoverwrite"])
            self.assertEqual(self.core.export_calls[-1][-1], "private_bytes")
            self.assertEqual(self.core.export_calls[-1][2], format)
        self.assertEqual(self.source.read_bytes(), self.raw)

    def test_export_existing_file_refused_without_overwrite_or_discarding_view(self):
        self.load()
        target = self.directory / "already.json"
        target.write_bytes(b"existing user-owned report")
        self.assertIsNone(self.panel.export_to_path(target))
        self.assertEqual(target.read_bytes(), b"existing user-owned report")
        self.assertFalse(self.panel.stale)
        self.assertIsNotNone(self.panel.result)
        self.assertIn("refused", self.status.get())

    def test_export_source_race_refuses_and_invalidates_view(self):
        self.load()
        original_export = self.core.export_report

        def race(*args, **kwargs):
            self.source.write_bytes(self.raw + b" ")
            return original_export(*args, **kwargs)

        with mock.patch.object(self.core, "export_report", side_effect=race):
            self.assertIsNone(self.panel.export_to_path(self.directory / "race.json"))
        self.assertTrue(self.panel.stale)
        self.assertFalse((self.directory / "race.json").exists())

    def test_file_dialog_cancel_is_noop_keeps_current_view(self):
        self.load()
        from tkinter import filedialog
        original = self.panel.result
        with mock.patch.object(filedialog, "askopenfilename", return_value="") as dialog:
            self.panel.buttons["Load summary JSON"].invoke()
        self.assertEqual(dialog.call_args.kwargs["parent"], self.root)
        self.assertIs(self.panel.result, original)
        self.assertEqual(len(self.core.load_calls), 1)

    def test_export_dialog_cancel_does_not_write_or_copy(self):
        self.load()
        from tkinter import filedialog
        with mock.patch.object(filedialog, "asksaveasfilename", return_value=""):
            self.panel.buttons["Export JSON"].invoke()
        self.assertEqual(self.core.export_calls, [])
        self.assertEqual(self.clipboard, [])

    def test_load_button_accepts_explicit_dialog_path_no_automatic_export(self):
        from tkinter import filedialog
        with mock.patch.object(filedialog, "askopenfilename", return_value=str(self.source)):
            self.panel.buttons["Load summary JSON"].invoke()
        self.assertEqual(self.core.load_calls, [self.source])
        self.assertEqual(self.core.export_calls, [])

    def test_bad_load_clears_previous_deltas_and_avoids_leaking_old_copy(self):
        self.load()
        invalid = self.directory / "invalid.json"
        invalid.write_bytes(b"{broken")
        self.assertFalse(self.panel.load_from_path(invalid))
        self.assertIsNone(self.panel.result)
        self.assertEqual(self.panel.raw_tree.get_children(), ())
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertFalse(self.panel.copy_summary())
        self.assertEqual(self.clipboard, [])

    def test_bad_selected_source_can_recover_only_with_explicit_reload(self):
        self.source.write_bytes(b"{broken")
        self.assertFalse(self.panel.load_from_path(self.source))
        self.source.write_bytes(self.raw)
        self.assertIsNone(self.panel.result)
        self.panel.buttons["Reload source"].invoke()
        self.assertIsNotNone(self.panel.result)

    def test_reload_without_source_does_not_open_dialog_or_read_files(self):
        from tkinter import filedialog
        with mock.patch.object(filedialog, "askopenfilename") as dialog:
            self.panel.buttons["Reload source"].invoke()
        dialog.assert_not_called()
        self.assertEqual(self.core.load_calls, [])

    def test_core_failure_is_contained_leaving_widget_construction_usable(self):
        parent = self.ttk.Frame(self.root)
        with mock.patch.object(panel_module, "_load_core", side_effect=ImportError("fixture missing core")):
            panel = panel_module.ComparisonPanel(parent, self.status)
        self.assertIsNone(panel.core)
        self.assertFalse(panel.load_from_path(self.source))
        self.assertEqual(len(panel.tabs.tabs()), 3)
        self.assertIn("unavailable", self.status.get())

    def test_status_callback_as_well_as_stringvar_supported(self):
        captured = []
        parent = self.ttk.Frame(self.root)
        panel = panel_module.ComparisonPanel(parent, captured.append, core=self.core)
        self.assertFalse(panel.reload())
        self.assertTrue(captured)

    def test_no_auto_refresh_watchers_focus_or_input_bindings(self):
        bindings = self.root.bind()
        self.assertEqual(bindings, ())
        self.assertEqual(self.root.tk.call("after", "info"), "")
        self.assertEqual(self.core.load_calls, [])
        self.assertEqual(self.core.export_calls, [])

    def genuine_source(self):
        example = SCRIPTS.parent / "examples/game-tool-hub/comparison-fixture.example.json"
        source = self.directory / "genuine-normalized-fixture.json"
        source.write_bytes(example.read_bytes())
        self.panel.core = panel_module._load_core()
        return source

    def test_genuine_core_fixture_load_keeps_interrupted_run_and_valid_2x2_rows(self):
        source = self.genuine_source()
        original = source.read_bytes()
        self.assertTrue(self.panel.load_from_path(source))
        self.assertEqual(self.panel.result["status"], "COMPARABLE")
        self.assertEqual(len(self.panel.raw_tree.get_children()), 13)
        self.assertEqual(len(self.panel.case_tree.get_children()), 4)
        self.assertEqual(len(self.panel.contrast_tree.get_children()), 4)
        self.assertEqual(len(self.panel.chart.find_withtag("bar")), 4)
        self.assertIn("SYNTHETIC", self.panel.verdict.get())
        self.assertEqual(source.read_bytes(), original)
        self.assertFalse(self.panel.result["runtime_verification"])

    def test_genuine_core_selected_metric_copy_and_exports_have_matching_definitions(self):
        source = self.genuine_source()
        self.assertTrue(self.panel.load_from_path(source))
        self.choose_metric("ram")
        self.assertTrue(self.panel.copy_summary())
        copied = json.loads(self.clipboard[-1])
        self.assertEqual([metric["id"] for metric in copied["metrics"]], ["ram"])
        output = self.directory / "genuine-report.json"
        receipt = self.panel.export_to_path(output)
        self.assertIsNotNone(receipt)
        exported = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(copied, exported)
        html_target = self.directory / "genuine-report.html"
        self.assertIsNotNone(self.panel.export_to_path(html_target, "html"))
        html = html_target.read_text(encoding="utf-8")
        self.assertNotIn("<script", html)
        self.assertNotIn(str(self.directory), html)
        self.assertIn("SYNTHETIC FIXTURE", html)
        self.assertIn("Process private commit", html)

    def test_genuine_core_imported_rendering_declarations_cannot_establish_fg_pass(self):
        source = self.genuine_source()
        fixture = json.loads(source.read_text(encoding="utf-8"))
        fixture["origin"] = "imported_report"
        fixture["measurement_scope"] = "rendering"
        for run in fixture["runs"]:
            run["fg"] = {"dynamic_mfg": "inactive", "effective_mode": "fixed", "multiplier": 2, "evidence": "declared"}
        source.write_text(json.dumps(fixture), encoding="utf-8")
        self.assertTrue(self.panel.load_from_path(source))
        self.assertEqual(self.panel.result["status"], "BLOCKED")
        self.assertIn("RUNTIME_FG_UNVERIFIED", self.panel.run_text.get("1.0", "end"))
        self.assertEqual(len(self.panel.raw_tree.get_children()), 13)
        self.assertEqual(self.panel.contrast_tree.get_children(), ())
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())

    def test_genuine_core_missing_metric_partial_does_not_make_null_zero(self):
        source = self.genuine_source()
        fixture = json.loads(source.read_text(encoding="utf-8"))
        for run in fixture["runs"]:
            run["metrics"]["vram"]["value"] = None
        source.write_text(json.dumps(fixture), encoding="utf-8")
        self.assertTrue(self.panel.load_from_path(source))
        self.assertEqual(self.panel.result["status"], "PARTIAL")
        self.choose_metric("vram")
        self.assertEqual(self.panel.raw_tree.item("run-0", "values")[-1], "unavailable")
        self.assertEqual(self.panel.case_tree.get_children(), ())
        self.assertEqual(self.panel.contrast_tree.get_children(), ())
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())

    def test_genuine_core_source_drift_refuses_without_clobbering_existing_report(self):
        source = self.genuine_source()
        self.assertTrue(self.panel.load_from_path(source))
        output = self.directory / "existing-report.json"
        output.write_bytes(b"retained original report")
        source.write_bytes(source.read_bytes() + b" ")
        self.assertIsNone(self.panel.export_to_path(output))
        self.assertEqual(output.read_bytes(), b"retained original report")
        self.assertTrue(self.panel.stale)
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())


if __name__ == "__main__":
    unittest.main()
