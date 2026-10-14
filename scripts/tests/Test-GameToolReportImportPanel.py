"""Withdrawn native-Tk saved-report import contracts; fixture files only.

No desktop focus, native input, processes, games, providers or recording. Dialogs
are mocked and all runtime fixture writes stay within one temporary directory.
"""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("report_import_panel_contracts", SCRIPTS / "GameToolComparisonPanel.py")
panel_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(panel_module)


class FixtureImporter:
    """Deterministic saved-summary preview and bundle; not a provider adapter."""

    def __init__(self):
        self.inspect_calls, self.import_calls = [], []
        self.error = None
        self.dataset = json.loads((SCRIPTS.parent / "examples/game-tool-hub/comparison-fixture.example.json").read_text(encoding="utf-8"))
        self.dataset["origin"] = "imported_report"
        self.dataset["measurement_scope"] = "rendering"
        for run in self.dataset["runs"]:
            run["fg"] = {"dynamic_mfg": "unverified", "effective_mode": "unknown", "multiplier": None, "evidence": "declared"}

    def inspect_report(self, path, adapter="auto"):
        path = Path(path)
        self.inspect_calls.append(path)
        raw = path.read_bytes()
        value = json.loads(raw)
        if not isinstance(value, dict) or value.get("summary") is not True:
            raise ValueError("Raw frames or unknown report schema refused")
        return {"schema_version": 1, "adapter": "fixture_summary", "adapter_revision": "fixture only",
                "provider": "Fixture provider", "provider_version": "unknown", "source_schema": "fixture summary",
                "coverage": {"duration_seconds": 10, "sample_count": 100, "started_utc": None, "ended_utc": None},
                "raw_metadata": {"cache_state": "unknown"}, "provider_outcome": "not_reported",
                "metrics": [{"id": "fps", "label": "Reported FPS", "value": value.get("value"), "unit": "FPS",
                             "definition": "Provider summary only", "frame_class": "unknown"}],
                "issues": ["Missing UTC boundaries", "Effective FG unverified"],
                "private_source": {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}}

    def import_bundle(self, assignments, output_directory, **kwargs):
        self.import_calls.append((copy.deepcopy(assignments), Path(output_directory), kwargs))
        if self.error:
            raise ValueError(self.error)
        for assignment in assignments:
            raw = Path(assignment["path"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != assignment.get("expected_sha256", hashlib.sha256(raw).hexdigest()):
                raise ValueError("Source drift")
        target = Path(output_directory)
        target.mkdir()
        dataset = copy.deepcopy(self.dataset)
        dataset["title"] = kwargs.get("title", "Saved reports")
        dataset["question"] = kwargs.get("question", "Compare saved provider summaries.")
        source = target / "comparison.json"
        encoded = json.dumps(dataset).encode("utf-8")
        source.write_bytes(encoded)
        for index, assignment in enumerate(assignments, 1):
            (target / f"source-{index:03d}.json").write_bytes(Path(assignment["path"]).read_bytes())
        return {"schema_version": 1, "status": "BLOCKED", "execution": "none", "bundle_path": str(target),
                "dataset_path": str(source), "dataset_sha256": hashlib.sha256(encoded).hexdigest(),
                "source_count": len(assignments), "manifest_path": str(target / "private-receipt.json")}


class ImportPanelContracts(unittest.TestCase):
    def setUp(self):
        import tkinter as tk
        from tkinter import ttk
        self.temp = tempfile.TemporaryDirectory(prefix="report-import-panel-fixtures-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.root = tk.Tk()
        self.root.withdraw()
        self.addCleanup(lambda: (self.root.update_idletasks(), self.root.destroy()))
        self.parent = ttk.Frame(self.root)
        self.status = tk.StringVar(master=self.root)
        self.importer = FixtureImporter()
        self.panel = panel_module.ComparisonPanel(self.parent, self.status, core=panel_module._load_core(), importer=self.importer)
        self.before = self.directory / "existing-normalized.json"
        self.before.write_bytes((SCRIPTS.parent / "examples/game-tool-hub/comparison-fixture.example.json").read_bytes())
        self.report = self.directory / "baseline-name-does-not-assign-case.json"
        self.report.write_text(json.dumps({"summary": True, "value": 31}), encoding="utf-8")
        self.safety = ExitStack()
        self.addCleanup(self.safety.close)
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_clear"))
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_append"))

    def wizard(self):
        return self.panel.open_import_wizard(show=False)

    def prepared(self):
        wizard = self.wizard()
        wizard.add_paths([self.report])
        wizard.case.set("baseline")
        wizard.assign_selected()
        return wizard

    def test_constructor_does_not_read_reports_or_load_optional_importer(self):
        with mock.patch.object(panel_module, "_load_importer") as loader:
            other = panel_module.ComparisonPanel(self.parent, self.status, core=self.panel.core)
        loader.assert_not_called()
        self.assertIsNone(other.import_wizard)
        self.assertEqual(self.importer.inspect_calls, [])
        self.assertEqual(self.importer.import_calls, [])
        self.assertEqual(self.root.state(), "withdrawn")
        self.assertIsNone(self.panel.result)

    def test_toolbar_keeps_existing_buttons_and_wraps_to_available_width(self):
        self.assertEqual(set(self.panel.buttons), {"Import saved reports", "Load summary JSON", "Reload source",
                                                 "Copy summary", "Export JSON", "Export HTML"})
        bar = self.panel.buttons["Import saved reports"].master
        buttons = dict(self.panel.buttons)
        commands = {key: button.cget("command") for key,button in buttons.items()}
        self.root.update_idletasks()
        bar.reflow(SimpleNamespace(widget=bar,width=350))
        self.assertGreater(max(button.grid_info()["row"] for button in buttons.values()),0)
        bar.reflow(SimpleNamespace(widget=bar,width=2400))
        self.assertEqual({button.grid_info()["row"] for button in buttons.values()}, {0})
        self.assertEqual(self.panel.buttons,buttons)
        self.assertEqual({key:button.cget("command") for key,button in buttons.items()},commands)
        self.assertEqual(self.importer.inspect_calls, [])
        self.assertEqual(self.importer.import_calls, [])

    def test_wizard_constructor_is_withdrawn_and_has_no_automatic_dialog(self):
        from tkinter import filedialog
        with mock.patch.object(filedialog, "askopenfilenames") as files, mock.patch.object(filedialog, "asksaveasfilename") as output:
            wizard = self.wizard()
        files.assert_not_called()
        output.assert_not_called()
        self.assertEqual(wizard.window.state(), "withdrawn")
        self.assertEqual(wizard.records, {})
        self.assertEqual(wizard.detail.cget("state"), "disabled")
        self.assertIsNone(wizard.window.grab_current())
        self.assertEqual(self.importer.inspect_calls, [])

    def test_add_dialog_cancel_is_noop(self):
        from tkinter import filedialog
        wizard = self.wizard()
        with mock.patch.object(filedialog, "askopenfilenames", return_value=()) as files:
            wizard.buttons["Add saved reports"].invoke()
        self.assertEqual(files.call_args.kwargs["parent"], wizard.window)
        self.assertEqual(wizard.records, {})
        self.assertEqual(self.importer.inspect_calls, [])

    def test_add_dialog_only_inspects_selected_files(self):
        from tkinter import filedialog
        wizard = self.wizard()
        with mock.patch.object(filedialog, "askopenfilenames", return_value=(str(self.report),)):
            wizard.buttons["Add saved reports"].invoke()
        self.assertEqual(self.importer.inspect_calls, [self.report])
        self.assertEqual(self.importer.import_calls, [])
        self.assertEqual(len(wizard.records), 1)
        self.assertEqual(wizard.records["report-0"]["case"], "unassigned")

    def test_preview_shows_raw_values_definition_coverage_and_unknowns(self):
        wizard = self.wizard()
        wizard.add_paths([self.report])
        detail = json.loads(wizard.detail.get("1.0", "end"))
        self.assertEqual(detail["preview"]["metrics"][0]["value"], 31)
        self.assertEqual(detail["preview"]["metrics"][0]["definition"], "Provider summary only")
        self.assertIsNone(detail["preview"]["coverage"]["started_utc"])
        self.assertEqual(detail["preview"]["raw_metadata"]["cache_state"], "unknown")
        self.assertEqual(detail["assignment_evidence"], "user declaration only")
        self.assertFalse(detail["runtime_verification"])
        self.assertIn("Effective FG unverified", wizard.detail.get("1.0", "end"))

    def test_cases_are_explicit_never_inferred_from_file_name(self):
        wizard = self.wizard()
        wizard.add_paths([self.report])
        self.assertEqual(wizard.tree.item("report-0", "values")[1], "unassigned")
        with self.assertRaisesRegex(ValueError, "Assign every"):
            wizard.assignments()
        wizard.case.set("a")
        self.assertTrue(wizard.assign_selected())
        assignment = wizard.assignments()[0]
        self.assertEqual(assignment["case"], "a")
        self.assertEqual(assignment["expected_sha256"], hashlib.sha256(self.report.read_bytes()).hexdigest())
        self.assertNotIn("fg", assignment)
        self.assertNotIn("origin", assignment)

    def test_invalid_case_cannot_change_assignment(self):
        wizard = self.prepared()
        wizard.case.set("fg_verified")
        self.assertFalse(wizard.assign_selected())
        self.assertEqual(wizard.records["report-0"]["case"], "baseline")

    def test_no_ui_control_can_promote_fg_origin_or_run_outcome(self):
        wizard = self.wizard()
        self.assertEqual(tuple(wizard.case_combo.cget("values")), ("unassigned", "baseline", "a"))
        self.assertEqual(set(wizard.entries), {"Report title", "Comparison question", "Tested factor ID (declaration)"})
        self.assertNotIn("FG verified", wizard.buttons)
        self.assertNotIn("synthetic_fixture", wizard.entries)

    def test_same_dialog_supports_distinct_repeat_files_without_case_guessing(self):
        paths = []
        for number in range(3):
            path = self.directory / f"repeat-{number}.json"
            path.write_text(json.dumps({"summary": True, "value": number}), encoding="utf-8")
            paths.append(path)
        wizard = self.wizard()
        wizard.add_paths(paths)
        self.assertEqual(len(wizard.records), 3)
        self.assertTrue(all(record["case"] == "unassigned" for record in wizard.records.values()))
        self.assertEqual(self.importer.inspect_calls, paths)

    def test_report_limit_refuses_whole_add_without_reading_files(self):
        wizard = self.wizard()
        self.assertFalse(wizard.add_paths([self.report] * 33))
        self.assertEqual(wizard.records, {})
        self.assertEqual(self.importer.inspect_calls, [])
        self.assertIn("32", wizard.notice.get())

    def test_remove_selected_changes_preview_only(self):
        original = self.report.read_bytes()
        wizard = self.prepared()
        self.assertTrue(wizard.remove_selected())
        self.assertEqual(wizard.records, {})
        self.assertEqual(wizard.tree.get_children(), ())
        self.assertEqual(self.report.read_bytes(), original)
        self.assertEqual(self.importer.import_calls, [])

    def test_remove_without_selection_is_noop(self):
        wizard = self.wizard()
        self.assertFalse(wizard.remove_selected())
        self.assertEqual(self.importer.inspect_calls, [])

    def test_explicit_multiselect_assigns_each_selected_repeat_and_no_other_row(self):
        wizard = self.wizard()
        wizard.add_paths([self.report] * 3)
        wizard.tree.selection_set(("report-0", "report-1"))
        wizard.case.set("baseline")
        self.assertTrue(wizard.assign_selected())
        self.assertEqual([record["case"] for record in wizard.records.values()], ["baseline", "baseline", "unassigned"])
        self.assertEqual(str(wizard.tree.cget("selectmode")), "extended")
        detail = json.loads(wizard.detail.get("1.0", "end"))
        self.assertEqual(detail["selected_report_count"], 2)

    def test_multiselect_remove_keeps_original_bytes_and_remaining_preview(self):
        wizard = self.wizard()
        original = self.report.read_bytes()
        wizard.add_paths([self.report] * 3)
        wizard.tree.selection_set(("report-0", "report-1"))
        self.assertTrue(wizard.remove_selected())
        self.assertEqual(list(wizard.records), ["report-2"])
        self.assertEqual(self.report.read_bytes(), original)
        self.assertEqual(self.importer.import_calls, [])

    def test_refused_source_reason_visible_without_discarding_existing_comparison(self):
        self.assertTrue(self.panel.load_from_path(self.before))
        retained = self.panel.result
        invalid = self.directory / "raw-frame.csv"
        invalid.write_text("raw frames", encoding="utf-8")
        wizard = self.wizard()
        wizard.add_paths([invalid])
        self.assertIsNone(wizard.records["report-0"]["preview"])
        self.assertIn("refusal_reason", wizard.detail.get("1.0", "end"))
        wizard.case.set("baseline")
        wizard.assign_selected()
        self.assertIsNone(wizard.create_import(self.directory / "not-created"))
        self.assertIs(self.panel.result, retained)
        self.assertFalse((self.directory / "not-created").exists())

    def test_unassigned_create_never_opens_destination_dialog(self):
        from tkinter import filedialog
        wizard = self.wizard()
        wizard.add_paths([self.report])
        with mock.patch.object(filedialog, "asksaveasfilename") as output:
            self.assertIsNone(wizard.create_import())
        output.assert_not_called()
        self.assertEqual(self.importer.import_calls, [])

    def test_destination_cancel_retains_preview_and_comparison(self):
        from tkinter import filedialog
        self.panel.load_from_path(self.before)
        retained = self.panel.result
        wizard = self.prepared()
        with mock.patch.object(filedialog, "asksaveasfilename", return_value="") as output:
            self.assertIsNone(wizard.create_import())
        self.assertEqual(output.call_args.kwargs["parent"], wizard.window)
        self.assertFalse(output.call_args.kwargs["confirmoverwrite"])
        self.assertEqual(self.importer.import_calls, [])
        self.assertIs(self.panel.result, retained)
        self.assertEqual(len(wizard.records), 1)

    def test_cancel_destroys_only_owned_window_and_writes_nothing(self):
        wizard = self.prepared()
        self.assertIs(wizard.window.master, self.root)
        wizard.cancel()
        self.assertIsNone(self.panel.import_wizard)
        self.assertEqual(self.importer.import_calls, [])
        self.assertTrue(self.root.winfo_exists())
        self.assertEqual(self.root.state(), "withdrawn")

    def test_import_button_uses_owned_wizard_without_test_visibility(self):
        with mock.patch.object(panel_module.SavedReportImportWizard, "show") as show:
            self.panel.buttons["Import saved reports"].invoke()
        show.assert_called_once()
        self.assertIsNotNone(self.panel.import_wizard)
        self.assertEqual(self.root.state(), "withdrawn")

    def test_optional_importer_failure_is_contained_manual_load_still_works(self):
        self.panel.importer = None
        with mock.patch.object(panel_module, "_load_importer", side_effect=ImportError("missing optional adapter")):
            self.assertIsNone(self.panel.open_import_wizard(show=False))
        self.assertIn("unavailable", self.status.get())
        self.assertTrue(self.panel.load_from_path(self.before))
        self.assertEqual(self.panel.result["status"], "COMPARABLE")

    def test_importer_failure_preserves_current_view_and_old_source(self):
        self.panel.load_from_path(self.before)
        retained, original = self.panel.result, self.before.read_bytes()
        self.importer.error = "fixture refused request"
        assignment = {"path": str(self.report), "case": "baseline"}
        self.assertIsNone(self.panel.import_saved_reports([assignment], self.directory / "not-created"))
        self.assertIs(self.panel.result, retained)
        self.assertEqual(self.before.read_bytes(), original)
        self.assertFalse((self.directory / "not-created").exists())

    def test_malformed_import_receipt_preserves_current_comparison(self):
        self.panel.load_from_path(self.before)
        retained = self.panel.result
        with mock.patch.object(self.importer, "import_bundle", return_value={"status": "BLOCKED"}):
            self.assertIsNone(self.panel.import_saved_reports([{"path": str(self.report), "case": "baseline"}], self.directory / "not-created"))
        self.assertIs(self.panel.result, retained)
        self.assertIn("no valid normalized dataset receipt", self.status.get())

    def test_preview_source_drift_refuses_create_and_retains_old_comparison(self):
        self.panel.load_from_path(self.before)
        retained = self.panel.result
        wizard = self.prepared()
        self.report.write_text(json.dumps({"summary": True, "value": 47}), encoding="utf-8")
        target = self.directory / "not-created"
        self.assertIsNone(wizard.create_import(target))
        self.assertFalse(target.exists())
        self.assertIs(self.panel.result, retained)
        self.assertIn("Source drift", self.status.get())
        self.assertIn("Source drift", wizard.notice.get())
        self.assertIn("Source drift", wizard.detail.get("1.0", "end"))

    def test_existing_destination_is_refused_without_modifying_user_content(self):
        self.panel.load_from_path(self.before)
        retained = self.panel.result
        target = self.directory / "existing-folder"
        target.mkdir()
        marker = target / "user-file.txt"
        marker.write_bytes(b"preserve")
        wizard = self.prepared()
        self.assertIsNone(wizard.create_import(target))
        self.assertEqual(marker.read_bytes(), b"preserve")
        self.assertEqual(list(target.iterdir()), [marker])
        self.assertIs(self.panel.result, retained)

    def test_explicit_create_archives_original_and_loads_raw_blocked_fg(self):
        original = self.report.read_bytes()
        wizard = self.prepared()
        wizard.title.set("My saved reports")
        wizard.question.set("What changes?")
        target = self.directory / "new-bundle"
        receipt = wizard.create_import(target)
        self.assertIsNotNone(receipt)
        self.assertIsNone(self.panel.import_wizard)
        self.assertEqual((target / "source-001.json").read_bytes(), original)
        self.assertEqual(self.report.read_bytes(), original)
        self.assertEqual(self.panel.source_path, target / "comparison.json")
        self.assertEqual(self.panel.result["status"], "BLOCKED")
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertTrue(self.panel.raw_tree.get_children())
        self.assertIn("RUNTIME_FG_UNVERIFIED", self.panel.run_text.get("1.0", "end"))
        self.assertEqual(self.importer.import_calls[0][2]["title"], "My saved reports")
        self.assertEqual(self.importer.import_calls[0][2]["question"], "What changes?")
        self.assertNotIn("SYNTHETIC", self.panel.verdict.get())

    def test_imported_dataset_drift_retains_existing_reload_export_guards(self):
        wizard = self.prepared()
        target = self.directory / "bundle"
        wizard.create_import(target)
        source = target / "comparison.json"
        source.write_bytes(source.read_bytes() + b" ")
        self.assertFalse(self.panel.copy_summary())
        self.assertTrue(self.panel.stale)
        self.assertIsNone(self.panel.export_to_path(self.directory / "not-created.json"))
        self.assertFalse((self.directory / "not-created.json").exists())
        self.assertTrue(self.panel.reload())
        self.assertEqual(self.panel.result["status"], "BLOCKED")

    def test_invalid_completed_bundle_is_not_accepted_as_current_comparison(self):
        self.panel.load_from_path(self.before)
        self.importer.dataset = {"broken": "invalid normalization"}
        receipt = self.panel.import_saved_reports([{"path": str(self.report), "case": "baseline"}], self.directory / "bundle")
        self.assertIsNotNone(receipt)
        self.assertIsNone(self.panel.result)
        self.assertTrue(Path(receipt["dataset_path"]).exists())
        self.assertIn("could not be validated", self.status.get())

    def test_dataset_receipt_drift_cannot_load_changed_synthetic_bytes_as_import(self):
        original = self.importer.import_bundle

        def race(*args, **kwargs):
            receipt = original(*args, **kwargs)
            path = Path(receipt["dataset_path"])
            altered = json.loads(path.read_text(encoding="utf-8"))
            altered["origin"] = "synthetic_fixture"
            path.write_text(json.dumps(altered), encoding="utf-8")
            return receipt

        with mock.patch.object(self.importer, "import_bundle", side_effect=race):
            receipt = self.panel.import_saved_reports([{"path": str(self.report), "case": "baseline"}], self.directory / "race-bundle")
        self.assertIsNotNone(receipt)
        self.assertIsNone(self.panel.result)
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertIn("receipt hash does not match", self.panel.run_text.get("1.0", "end"))

    def genuine_fixture(self, name):
        """Copy authored format fixtures, never a real private provider report."""
        path = self.directory / name
        path.write_bytes((SCRIPTS.parent / "examples/game-tool-hub/import-fixtures" / name).read_bytes())
        self.panel.importer = panel_module._load_importer()
        return path

    def test_genuine_cyberpunk_preview_retains_values_and_capacity_is_not_usage(self):
        source = self.genuine_fixture("cyberpunk-summary.example.json")
        original = source.read_bytes()
        wizard = self.wizard()
        self.assertTrue(wizard.add_paths([source]))
        preview = wizard.records["report-0"]["preview"]
        self.assertEqual(preview["adapter"], "cyberpunk_benchmark_summary")
        self.assertEqual(preview["metrics"][0]["id"], "cp_average_fps")
        self.assertEqual(preview["metrics"][0]["value"], 60)
        self.assertEqual(preview["metrics"][0]["frame_class"], "unknown")
        self.assertIn("capacity_metadata_not_usage", preview["raw_metadata"])
        self.assertIn("not effective FG", wizard.detail.get("1.0", "end"))
        self.assertEqual(wizard.records["report-0"]["case"], "unassigned")
        self.assertEqual(source.read_bytes(), original)

    def test_genuine_presentmon_preview_preserves_percentile_definition(self):
        source = self.genuine_fixture("presentmon-stats.example.csv")
        wizard = self.wizard()
        wizard.add_paths([source])
        preview = wizard.records["report-0"]["preview"]
        self.assertEqual(preview["adapter"], "presentmon_gui_stats")
        self.assertEqual(preview["provider_version"], "unknown")
        self.assertEqual(preview["metrics"][0]["value"], 60)
        percentile = next(metric for metric in preview["metrics"] if metric["id"] == "pm_percentile_1_fps")
        self.assertIn("not mean of slowest 1%", percentile["definition"])
        self.assertEqual(percentile["frame_class"], "presented_intervals")
        self.assertIsNone(preview["coverage"]["started_utc"])

    def test_genuine_json_and_csv_bundle_archives_bytes_and_loads_blocked_raw_rows(self):
        sources = [self.genuine_fixture("cyberpunk-summary.example.json"), self.genuine_fixture("presentmon-stats.example.csv")]
        originals = [source.read_bytes() for source in sources]
        wizard = self.wizard()
        wizard.add_paths(sources)
        for key, case in (("report-0", "baseline"), ("report-1", "a")):
            wizard.tree.selection_set(key)
            wizard.case.set(case)
            self.assertTrue(wizard.assign_selected())
        target = self.directory / "genuine-bundle"
        receipt = wizard.create_import(target)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["source_count"], 2)
        self.assertEqual((target / "source-001.json").read_bytes(), originals[0])
        self.assertEqual((target / "source-002.csv").read_bytes(), originals[1])
        self.assertEqual([source.read_bytes() for source in sources], originals)
        self.assertTrue(Path(receipt["manifest_path"]).exists())
        self.assertEqual(self.panel.result["status"], "BLOCKED")
        self.assertEqual(len(self.panel.raw_tree.get_children()), 2)
        self.assertEqual(self.panel.dataset["origin"], "imported_report")
        self.assertFalse(self.panel.result["synthetic_fixture"])
        self.assertFalse(self.panel.result["runtime_verification"])
        self.assertEqual(self.panel.contrast_tree.get_children(), ())
        self.assertEqual(self.panel.chart.find_withtag("bar"), ())
        self.assertIn("RUNTIME_FG_UNVERIFIED", self.panel.run_text.get("1.0", "end"))
        self.assertTrue(all(run["fg"]["dynamic_mfg"] == "unverified" for run in self.panel.dataset["runs"]))

    def test_genuine_raw_frame_csv_is_refused_without_changing_comparison(self):
        self.genuine_fixture("presentmon-stats.example.csv")
        self.panel.load_from_path(self.before)
        retained = self.panel.result
        source = self.directory / "raw-presentmon.csv"
        source.write_text("Application,ProcessID,CPUStartTime,MsBetweenPresents\nfixture.exe,1,1,16\n", encoding="utf-8")
        wizard = self.wizard()
        wizard.add_paths([source])
        self.assertIsNone(wizard.records["report-0"]["preview"])
        self.assertIn("Raw PresentMon frame CSV", wizard.detail.get("1.0", "end"))
        self.assertIs(self.panel.result, retained)

    def test_genuine_changed_preview_refuses_new_bundle_without_clearing_old_view(self):
        source = self.genuine_fixture("cyberpunk-summary.example.json")
        self.panel.load_from_path(self.before)
        retained = self.panel.result
        wizard = self.wizard()
        wizard.add_paths([source])
        wizard.case.set("baseline")
        wizard.assign_selected()
        source.write_bytes(source.read_bytes() + b" ")
        target = self.directory / "not-created"
        self.assertIsNone(wizard.create_import(target))
        self.assertFalse(target.exists())
        self.assertIs(self.panel.result, retained)
        self.assertIn("changed after preview", self.status.get())
        self.assertIn("changed after preview", wizard.notice.get())

    def test_genuine_existing_bundle_directory_is_not_overwritten(self):
        source = self.genuine_fixture("presentmon-stats.example.csv")
        wizard = self.wizard()
        wizard.add_paths([source])
        wizard.case.set("a")
        wizard.assign_selected()
        target = self.directory / "existing-bundle"
        target.mkdir()
        marker = target / "existing-user-content"
        marker.write_bytes(b"keep exactly")
        self.assertIsNone(wizard.create_import(target))
        self.assertEqual(list(target.iterdir()), [marker])
        self.assertEqual(marker.read_bytes(), b"keep exactly")

    def test_genuine_zero_frame_writer_report_preserves_outcome_not_zero_fps(self):
        source = self.genuine_fixture("presentmon-zero-stats.example.csv")
        wizard = self.wizard()
        wizard.add_paths([source])
        preview = wizard.records["report-0"]["preview"]
        self.assertEqual(preview["provider_outcome"], "zero_frames")
        self.assertTrue(all(metric["value"] is None for metric in preview["metrics"]))
        wizard.case.set("baseline")
        wizard.assign_selected()
        self.assertIsNotNone(wizard.create_import(self.directory / "zero-bundle"))
        self.assertEqual(self.panel.dataset["runs"][0]["status"], "incomplete")
        self.assertIsNotNone(self.panel.dataset["runs"][0]["failure_reason"])
        self.assertEqual(self.panel.dataset["runs"][0]["import_provenance"]["provider_outcome"], "zero_frames")
        self.assertEqual(self.panel.raw_tree.item("run-0", "values")[-1], "unavailable")

    def test_genuine_no_animation_writer_defect_remains_visible_not_repaired_metric(self):
        source = self.genuine_fixture("presentmon-no-animation-stats.example.csv")
        wizard = self.wizard()
        wizard.add_paths([source])
        preview = wizard.records["report-0"]["preview"]
        self.assertTrue(preview["raw_metadata"]["writer_defect"])
        self.assertIsNone(preview["raw_metadata"]["animation_fields"])
        self.assertEqual(preview["metrics"][0]["value"], 60)
        self.assertIn("missing-comma", wizard.detail.get("1.0", "end"))


class ImportLoaderContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="import-loader-fixtures-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / "GameToolReportImport.py"
        patch = mock.patch.object(panel_module, "__file__", str(self.directory / "GameToolComparisonPanel.py"))
        patch.start()
        self.addCleanup(patch.stop)

    def test_fixed_authored_importer_loaded_only_from_captured_utf8_bytes(self):
        self.source.write_bytes(b"FIXTURE = 'saved summaries only'\n")
        module = panel_module._load_importer()
        self.assertEqual(module.FIXTURE, "saved summaries only")
        self.assertFalse((self.directory / "__pycache__").exists())

    def test_arbitrary_module_name_cannot_be_supplied_by_report(self):
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            panel_module._load_authored("report_selected_code")

    def test_missing_importer_does_not_execute_another_filename(self):
        (self.directory / "other.py").write_bytes(b"raise AssertionError('must not execute')\n")
        with self.assertRaises(FileNotFoundError):
            panel_module._load_importer()

    def test_oversized_authored_importer_refused_before_execution(self):
        self.source.write_bytes(b"raise AssertionError('must not execute')\n" + b"#" * 1024 * 1024)
        with self.assertRaisesRegex(ValueError, "source limit"):
            panel_module._load_importer()


if __name__ == "__main__":
    unittest.main()
