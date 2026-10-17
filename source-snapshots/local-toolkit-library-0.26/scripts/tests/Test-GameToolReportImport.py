"""Saved-report adapter/bundle fixtures only. No provider, game, process or UI."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("report_import_contracts", ROOT / "scripts/GameToolReportImport.py")
IMPORT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORT)
FIXTURES = ROOT / "examples/game-tool-hub/import-fixtures"


class ReportImportContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="GameReportImportContract-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.cp_data = json.loads((FIXTURES / "cyberpunk-summary.example.json").read_text(encoding="utf-8"))
        self.cp = self.folder / "source.json"
        self.cp.write_bytes((FIXTURES / "cyberpunk-summary.example.json").read_bytes())
        self.pm = self.folder / "provider-stats.csv"
        self.pm.write_bytes((FIXTURES / "presentmon-stats.example.csv").read_bytes())

    def cp_write(self):
        self.cp.write_text(json.dumps(self.cp_data), encoding="utf-8")
        return self.cp

    def assignment(self, path=None, case="baseline", **kwargs):
        return {"path": self.cp if path is None else path, "case": case, **kwargs}

    def preview(self, path=None, **kwargs):
        return IMPORT.inspect_report(self.cp if path is None else path, **kwargs)

    def reject(self, path=None, **kwargs):
        with self.assertRaises(IMPORT.ReportImportError):
            self.preview(path, **kwargs)

    def dataset(self, assignments=None, **kwargs):
        return IMPORT.build_dataset([self.assignment()] if assignments is None else assignments, **kwargs)

    def test_cyberpunk_signature_values_and_no_mutation(self):
        before = self.cp.read_bytes(), self.cp.stat().st_mtime_ns
        row = self.preview()
        self.assertEqual(row["adapter"], "cyberpunk_benchmark_summary")
        self.assertEqual(row["provider_version"], "2.31")
        self.assertEqual({item["id"]: item["value"] for item in row["metrics"]},
                         {"cp_average_fps": 60, "cp_minimum_fps": 40, "cp_maximum_fps": 90})
        self.assertEqual(row["coverage"], {"started_utc": None, "ended_utc": None,
                                           "duration_seconds": 60, "sample_count": 3600})
        self.assertEqual(before, (self.cp.read_bytes(), self.cp.stat().st_mtime_ns))

    def test_capacity_not_usage_no_false_memory_metric(self):
        row = self.preview()
        self.assertEqual(row["raw_metadata"]["capacity_metadata_not_usage"], {"gpuMemory": 16384, "systemMemory": 32768})
        self.assertTrue(all(item["unit"] == "FPS" for item in row["metrics"]))
        self.assertNotIn("vram", str(row["metrics"]).lower())

    def test_native_fg_requested_only(self):
        row = self.preview()
        self.assertTrue(row["raw_metadata"]["requested_settings"]["DLSSMultiFrameGenEnabled"])
        run = self.dataset()["runs"][0]
        self.assertEqual(run["fg"], {"dynamic_mfg": "unverified", "effective_mode": "unknown", "multiplier": None, "evidence": "declared"})
        self.assertEqual(run["memory_warning"], "unverified")

    def test_missing_cyberpunk_metric_and_version_unknown(self):
        del self.cp_data["Data"]["averageFps"]
        del self.cp_data["Data"]["gameVersion"]
        self.cp_write()
        row = self.preview()
        self.assertIsNone(row["metrics"][0]["value"])
        self.assertEqual(row["provider_version"], "unknown")

    def test_zero_cyberpunk_coverage_retained_not_measured(self):
        self.cp_data["Data"]["frameNumber"] = 0
        self.cp_data["Data"]["time"] = 0
        self.cp_write()
        row = self.preview()
        self.assertEqual(row["provider_outcome"], "zero_frames")
        self.assertTrue(all(item["value"] is None for item in row["metrics"]))
        self.assertEqual(self.dataset()["runs"][0]["sample_count"], 0)

    def test_json_duplicate_fields_refused(self):
        self.cp.write_text('{"RootType":"worldBenchmarkSummary","RootType":"worldBenchmarkSummary","Data":{}}', encoding="utf-8")
        self.reject()

    def test_unknown_root_extra_fields_or_no_fps_refused(self):
        for data in ({"RootType": "other", "Data": {"averageFps": 60}},
                     {"RootType": "worldBenchmarkSummary", "Data": {}},
                     {**self.cp_data, "origin": "synthetic_fixture"}):
            with self.subTest(data=data):
                self.cp.write_text(json.dumps(data), encoding="utf-8")
                self.reject()

    def test_json_boolean_numeric_and_negative_count_refused(self):
        for key, value in (("averageFps", True), ("time", False), ("frameNumber", -1), ("frameNumber", 1.0)):
            with self.subTest(key=key, value=value):
                data = deepcopy(self.cp_data)
                data["Data"][key] = value
                self.cp.write_text(json.dumps(data), encoding="utf-8")
                self.reject()

    def test_oversized_integer_safe_error_not_overflow(self):
        self.cp_data["Data"]["averageFps"] = 10 ** 400
        self.cp_write()
        self.reject()
        self.assertEqual(sorted(path.name for path in self.folder.iterdir()), ["provider-stats.csv", "source.json"])

    def test_json_nonfinite_and_deeply_nested_refused(self):
        for text in ('{"RootType":"worldBenchmarkSummary","Data":{"averageFps":NaN}}',
                     '[' * 1500 + '0' + ']' * 1500):
            self.cp.write_text(text, encoding="utf-8")
            self.reject()

    def test_text_limit_and_invalid_unicode_refused(self):
        self.cp_data["Data"]["benchmarkName"] = "x" * 4097
        self.cp_write()
        self.reject()
        self.cp.write_bytes(b'\xff\xfeinvalid')
        self.reject()

    def test_oversized_empty_or_directory_source_refused(self):
        for data in (b"", b" " * (IMPORT.MAX_REPORT_BYTES + 1)):
            self.cp.write_bytes(data)
            self.reject()
        self.reject(self.folder)

    def test_path_controls_refused(self):
        self.reject("bad\x00path")

    def test_bom_accepted_without_filename_inference(self):
        weird = self.folder / "2099-01-01-GPU-untrusted-stats.json"
        weird.write_bytes(b'\xef\xbb\xbf' + self.cp.read_bytes())
        row = self.preview(weird)
        self.assertIsNone(row["coverage"]["started_utc"])
        self.assertEqual(row["provider_version"], "2.31")

    def test_presentmon_summary_values_exactly_provider_supplied(self):
        row = self.preview(self.pm)
        self.assertEqual(row["adapter"], "presentmon_gui_stats")
        self.assertEqual(row["provider_version"], "unknown")
        self.assertEqual([item["value"] for item in row["metrics"]], [60, 40, 42, 48, 90])
        self.assertEqual(row["coverage"]["sample_count"], 3600)
        self.assertTrue(all(item["frame_class"] == "presented_intervals" for item in row["metrics"]))
        self.assertIn("not mean of slowest 1%", row["metrics"][2]["definition"])
        self.assertTrue(all(item["latency_endpoints"] is None for item in row["metrics"]))

    def test_presentmon_animation_not_imported_as_metric(self):
        row = self.preview(self.pm)
        self.assertEqual(row["raw_metadata"]["animation_fields"], [0, 0])
        self.assertEqual(len(row["metrics"]), 5)

    def test_presentmon_known_missing_comma_defect(self):
        row = self.preview(FIXTURES / "presentmon-no-animation-stats.example.csv")
        self.assertEqual([item["value"] for item in row["metrics"]], [60, 40, 42, 48, 90])
        self.assertIsNone(row["raw_metadata"]["animation_fields"])
        self.assertTrue(row["raw_metadata"]["writer_defect"])

    def test_presentmon_zero_writer_defect_unavailable_not_zero(self):
        path = FIXTURES / "presentmon-zero-stats.example.csv"
        row = self.preview(path)
        self.assertEqual(row["provider_outcome"], "zero_frames")
        self.assertTrue(all(item["value"] is None for item in row["metrics"]))
        run = self.dataset([self.assignment(path)])["runs"][0]
        self.assertEqual(run["duration_seconds"], 0)
        self.assertEqual(run["sample_count"], 0)
        self.assertEqual(run["status"], "incomplete")

    def test_presentmon_raw_frames_explicitly_refused(self):
        self.pm.write_text("Application,ProcessID,CPUStartTime,FrameTime\nGame.exe,123,0,16\nGame.exe,123,16,16\n", encoding="utf-8")
        with self.assertRaisesRegex(IMPORT.ReportImportError, "Raw PresentMon frame CSV"):
            self.preview(self.pm)

    def test_presentmon_delimiter_header_width_and_extra_rows_refused(self):
        original = self.pm.read_text(encoding="utf-8")
        for text in (original.replace(",", ";"), original.replace("Average FPS", "Unknown FPS"),
                     original.rsplit(",", 1)[0] + "\n", original + "1,2,3\n"):
            with self.subTest(text=text):
                self.pm.write_text(text, encoding="utf-8")
                self.reject(self.pm)

    def test_presentmon_boolean_nonfinite_and_fractional_count_refused(self):
        original = self.pm.read_text(encoding="utf-8")
        for value in ("true", "NaN", "1e999", "-1"):
            self.pm.write_text(original.replace("60.000,3600,60.000", "60.000,3600," + value), encoding="utf-8")
            self.reject(self.pm)
        self.pm.write_text(original.replace(",3600,", ",3600.0,"), encoding="utf-8")
        self.reject(self.pm)

    def test_presentmon_source_bom_and_crlf_supported(self):
        self.pm.write_bytes(b'\xef\xbb\xbf' + self.pm.read_bytes().replace(b'\n', b'\r\n'))
        self.assertEqual(self.preview(self.pm)["metrics"][0]["value"], 60)

    def test_explicit_adapter_mismatch_and_unknown_refused(self):
        self.reject(adapter="presentmon_gui_stats")
        self.reject(self.pm, adapter="cyberpunk_benchmark_summary")
        self.reject(adapter="arbitrary_module")

    def test_build_is_detached_incomplete_and_side_effect_free(self):
        before = {path.name: path.read_bytes() for path in self.folder.iterdir()}
        dataset = self.dataset()
        self.assertEqual(dataset["origin"], "imported_report")
        self.assertEqual(dataset["measurement_scope"], "rendering")
        run = dataset["runs"][0]
        self.assertIsNone(run["started_utc"])
        self.assertIsNone(run["configuration"]["fingerprint"])
        self.assertEqual(run["status"], "incomplete")
        self.assertIn("not evidence of a provider-run crash", run["failure_reason"])
        self.assertNotIn(str(self.folder), json.dumps(dataset))
        dataset["runs"][0]["metrics"]["cp_average_fps"]["value"] = 999
        self.assertEqual(self.dataset()["runs"][0]["metrics"]["cp_average_fps"]["value"], 60)
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.folder.iterdir()})

    def test_rendering_gate_cannot_be_bypassed_with_requested_fg(self):
        result = IMPORT._core().compare_dataset(self.dataset())
        codes = {gate["code"] for gate in result["gates"]}
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["runtime_verification"])
        self.assertEqual(result["comparisons"], [])
        self.assertTrue({"COVERAGE_UNKNOWN", "CONFIGURATION_UNKNOWN", "IMPORTED_COMPONENTS_UNVERIFIED",
                         "RUNTIME_FG_UNVERIFIED", "DYNAMIC_MFG_ACTIVE_OR_UNVERIFIED", "EFFECTIVE_FG_UNKNOWN", "MEMORY_WARNING"} <= codes)

    def test_provenance_cannot_be_relabelled_to_synthetic_or_idle(self):
        for field, value in (("origin", "synthetic_fixture"), ("measurement_scope", "external_process")):
            data = self.dataset()
            data[field] = value
            with self.assertRaises(ValueError):
                IMPORT._core().validate_dataset(data)

    def test_provenance_runtime_pass_and_coverage_edit_refused(self):
        for mutation in (lambda p: p.update(runtime_verification=True),
                         lambda p: p.update(case_assignment="observed"),
                         lambda p: p["coverage"].update(sample_count=100)):
            data = self.dataset()
            mutation(data["runs"][0]["import_provenance"])
            with self.assertRaises(ValueError):
                IMPORT._core().validate_dataset(data)

    def test_user_case_roles_no_filename_guessing_or_unknown_fields(self):
        for assignment in ({"path": self.cp}, self.assignment(case="B"), self.assignment(origin="synthetic_fixture"),
                           self.assignment(context={"fg": "off"}), self.assignment(context={"status": "complete"})):
            with self.subTest(assignment=assignment):
                with self.assertRaises(IMPORT.ReportImportError):
                    self.dataset([assignment])

    def test_two_by_two_explicit_roles_and_provider_definitions_preserved(self):
        other = self.folder / "other.json"
        data = deepcopy(self.cp_data)
        data["Data"]["averageFps"] = 55
        other.write_text(json.dumps(data), encoding="utf-8")
        dataset = self.dataset([self.assignment(), self.assignment(self.pm, "a"), self.assignment(other, "ab")], design="two_by_two")
        self.assertEqual(dataset["runs"][2]["components"], ["changed_configuration", "changed_configuration_b"])
        self.assertEqual(len(dataset["metrics"]), 8)
        self.assertEqual(dataset["runs"][1]["metrics"]["pm_average_fps"]["descriptor"]["provider_version"], "unknown")

    def test_duplicate_report_content_not_repeat(self):
        copy = self.folder / "renamed.json"
        copy.write_bytes(self.cp.read_bytes())
        with self.assertRaisesRegex(IMPORT.ReportImportError, "Duplicate report bytes"):
            self.dataset([self.assignment(), self.assignment(copy, "a")])

    def test_report_count_limits_and_invalid_designs(self):
        for assignments in ([], [self.assignment()] * 33):
            with self.assertRaises(IMPORT.ReportImportError):
                self.dataset(assignments)
        for kwargs in ({"design": "arbitrary"}, {"factor": "../bad"}, {"design": "two_by_two", "factor_b": "changed_configuration"}):
            with self.assertRaises(IMPORT.ReportImportError):
                self.dataset(**kwargs)

    def test_source_changed_after_preview_refused_without_writes(self):
        digest = self.preview()["private_source"]["sha256"]
        self.cp_data["Data"]["averageFps"] = 99
        self.cp_write()
        output = self.folder / "bundle"
        with self.assertRaisesRegex(IMPORT.ReportImportError, "changed after preview"):
            IMPORT.import_bundle([self.assignment(expected_sha256=digest)], output)
        self.assertFalse(output.exists())

    def test_exclusive_bundle_preserves_bytes_and_manifest_hashes(self):
        original = self.cp.read_bytes(), self.pm.read_bytes()
        output = self.folder / "bundle"
        receipt = IMPORT.import_bundle([self.assignment(), self.assignment(self.pm, "a")], output)
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertEqual(receipt["execution"], "none")
        self.assertEqual(receipt["source_count"], 2)
        self.assertEqual((output / "source-001.json").read_bytes(), original[0])
        self.assertEqual((output / "source-002.csv").read_bytes(), original[1])
        self.assertEqual((self.cp.read_bytes(), self.pm.read_bytes()), original)
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        for item in manifest["files"]:
            content = (output / item["name"]).read_bytes()
            self.assertEqual(len(content), item["bytes"])
            self.assertEqual(hashlib.sha256(content).hexdigest(), item["sha256"])
        normalized = IMPORT._core().load_dataset(receipt["dataset_path"])
        self.assertEqual(IMPORT._core().compare_dataset(normalized)["status"], "BLOCKED")
        self.assertNotIn(str(self.folder), (output / "comparison.json").read_text(encoding="utf-8"))
        private = json.loads((output / "private-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(private["sources"][0]["private_source"]["path"], str(self.cp.resolve()))

    def test_existing_target_never_overwritten(self):
        output = self.folder / "bundle"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_bytes(b"user existing")
        with self.assertRaises(IMPORT.ReportImportError):
            IMPORT.import_bundle([self.assignment()], output)
        self.assertEqual(sentinel.read_bytes(), b"user existing")
        self.assertEqual([p.name for p in output.iterdir()], ["keep.txt"])

    def test_all_sources_validated_before_output(self):
        self.pm.write_text("bad data", encoding="utf-8")
        output = self.folder / "bundle"
        with self.assertRaises(IMPORT.ReportImportError):
            IMPORT.import_bundle([self.assignment(), self.assignment(self.pm, "a")], output)
        self.assertFalse(output.exists())
        self.assertFalse(any(p.name.startswith(".game-report-import-") for p in self.folder.iterdir()))

    def test_final_source_drift_rolls_back_complete_looking_bundle(self):
        output = self.folder / "bundle"
        original_check = IMPORT._assert_records_current
        count = [0]
        def check(records):
            count[0] += 1
            if count[0] == 3:
                raise IMPORT.ReportImportError("Source drift test")
            return original_check(records)
        with patch.object(IMPORT, "_assert_records_current", side_effect=check):
            with self.assertRaises(IMPORT.ReportImportError):
                IMPORT.import_bundle([self.assignment()], output)
        self.assertFalse(output.exists())

    def test_last_file_verification_failure_rolls_back_all_own_files(self):
        output = self.folder / "bundle"
        original_read = Path.read_bytes
        def read(path):
            if path == output / "manifest.json":
                return b"verification mismatch"
            return original_read(path)
        with patch.object(Path, "read_bytes", read):
            with self.assertRaises(IMPORT.ReportImportError):
                IMPORT.import_bundle([self.assignment()], output)
        self.assertFalse(output.exists())

    def test_failure_cleanup_preserves_concurrent_replacement(self):
        output = self.folder / "bundle"
        original_check = IMPORT._assert_records_current
        count = [0]
        def check(records):
            count[0] += 1
            if count[0] == 3:
                (output / "comparison.json").unlink()
                (output / "comparison.json").write_bytes(b"concurrent user replacement")
                raise IMPORT.ReportImportError("Source drift test")
            return original_check(records)
        with patch.object(IMPORT, "_assert_records_current", side_effect=check):
            with self.assertRaises(IMPORT.ReportImportError):
                IMPORT.import_bundle([self.assignment()], output)
        self.assertEqual((output / "comparison.json").read_bytes(), b"concurrent user replacement")
        self.assertEqual([p.name for p in output.iterdir()], ["comparison.json"])

    def test_linked_source_or_target_parent_refused(self):
        linked = self.folder / "linked.json"
        try:
            linked.symlink_to(self.cp)
        except OSError:
            self.skipTest("Symlink creation is unavailable; no privileges changed.")
        self.reject(linked)
        directory = self.folder / "linkdir"
        directory.symlink_to(self.folder, target_is_directory=True)
        with self.assertRaises(IMPORT.ReportImportError):
            IMPORT.import_bundle([self.assignment()], directory / "bundle")

    def test_reparse_flag_rejected_without_requiring_symlink_privileges(self):
        original_lstat = Path.lstat
        def lstat(path):
            if path == self.cp.absolute():
                return SimpleNamespace(st_mode=0o100600, st_file_attributes=0x400)
            return original_lstat(path)
        with patch.object(Path, "lstat", lstat):
            self.reject()

    def test_source_identity_drift_during_read_refused(self):
        original_stat = Path.stat
        def metadata(path, *args, **kwargs):
            item = original_stat(path, *args, **kwargs)
            if path == self.cp.absolute() and not kwargs.get("follow_symlinks") is False:
                return SimpleNamespace(st_dev=item.st_dev, st_ino=item.st_ino,
                    st_size=item.st_size, st_mtime_ns=item.st_mtime_ns + 1)
            return item
        with patch.object(Path, "stat", metadata):
            self.reject()

    def test_authored_core_read_bounded_before_allocation(self):
        sibling = self.folder / "GameToolComparison.py"
        sibling.write_bytes(b" " * (1024 * 1024 + 1))
        with patch.object(IMPORT, "__file__", str(self.folder / "GameToolReportImport.py")), patch.object(IMPORT, "_CORE", None):
            with self.assertRaisesRegex(IMPORT.ReportImportError, "bounded source limit"):
                IMPORT._core()


if __name__ == "__main__":
    unittest.main(verbosity=2)
