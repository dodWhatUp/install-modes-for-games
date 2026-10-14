"""Pure offline comparison contracts; no process/provider/game/recording calls."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("comparison_contracts", ROOT / "scripts/GameToolComparison.py")
CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORE)
FIXTURE = ROOT / "examples/game-tool-hub/comparison-fixture.example.json"


class ComparisonContracts(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.temp = tempfile.TemporaryDirectory(prefix="GameComparisonContract-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def write(self, data=None, name="dataset.json"):
        path = self.folder / name
        path.write_text(json.dumps(self.data if data is None else data, ensure_ascii=False), encoding="utf-8")
        return path

    def result(self, metric=None):
        return CORE.compare_dataset(self.data, metric)

    def codes(self, result=None):
        return {item["code"] for item in (self.result() if result is None else result)["gates"]}

    def reject(self):
        with self.assertRaises(CORE.ComparisonError):
            CORE.validate_dataset(self.data)

    def rendering(self, real=False):
        self.data["measurement_scope"] = "injected_feature"
        self.data["origin"] = "imported_report" if real else "synthetic_fixture"
        for run in self.data["runs"]:
            run["fg"] = {"dynamic_mfg": "inactive", "effective_mode": "off", "multiplier": None,
                         "evidence": "declared" if real else "synthetic"}

    def test_four_resource_fixture_visibly_synthetic(self):
        result = self.result()
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertTrue(result["synthetic_fixture"])
        self.assertEqual(result["execution"], "none")
        self.assertFalse(result["runtime_verification"])
        self.assertEqual({item["id"] for item in result["metrics"]}, {"cpu", "gpu", "ram", "vram"})
        self.assertIn("SYNTHETIC", result["warnings"][0])

    def test_incomplete_missing_import_metadata_nullable_without_fabrication(self):
        run = self.data["runs"][-1]
        run["started_utc"] = None
        run["configuration"]["fingerprint"] = None
        result = self.result()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue({"COVERAGE_UNKNOWN", "CONFIGURATION_UNKNOWN"} <= self.codes(result))
        self.assertIsNone(result["raw_runs"][-1]["started_utc"])
        self.assertIsNone(result["raw_runs"][-1]["configuration"]["fingerprint"])

    def test_complete_run_missing_metadata_still_refused(self):
        for field, value in (("started_utc", None), ("ended_utc", None),
                             ("duration_seconds", None), ("duration_seconds", 0),
                             ("sample_count", None), ("sample_count", 0),
                             ("configuration", {"fingerprint": None, "description": "unknown"})):
            with self.subTest(field=field, value=value):
                data = deepcopy(self.data)
                data["runs"][0][field] = value
                with self.assertRaises(CORE.ComparisonError):
                    CORE.validate_dataset(data)

    def test_failed_cancelled_missing_metadata_retained_blocked(self):
        for state in ("failed", "cancelled"):
            with self.subTest(state=state):
                data = deepcopy(self.data)
                run = data["runs"][-1]
                run.update(status=state, started_utc=None, ended_utc=None, duration_seconds=0, sample_count=0)
                run["configuration"]["fingerprint"] = None
                result = CORE.compare_dataset(data)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertEqual(result["raw_runs"][-1]["sample_count"], 0)

    def test_missing_start_cannot_imply_known_end(self):
        run = self.data["runs"][-1]
        run["started_utc"] = None
        run["ended_utc"] = "2026-10-11T08:01:00Z"
        self.reject()

    def test_oversized_integer_refused_without_overflow_exception(self):
        self.data["runs"][0]["metrics"]["cpu"]["value"] = 10 ** 400
        self.reject()

    def test_repeated_provider_summary_mean_and_spread(self):
        rows = self.result("ram")["case_summaries"]
        base = next(item for item in rows if item["case"] == "baseline")
        self.assertEqual(base, {"metric_id": "ram", "case": "baseline", "n": 3,
                               "mean": 100.0, "min": 99, "max": 101, "unit": "MiB"})

    def test_two_by_two_additive_contrasts(self):
        rows = {item["contrast"]: item for item in self.result("ram")["comparisons"]}
        self.assertEqual(rows["a minus baseline"]["delta"], 10)
        self.assertEqual(rows["b minus baseline"]["delta"], 20)
        self.assertEqual(rows["ab minus baseline"]["delta"], 35)
        self.assertEqual(rows["ab - a - b + baseline"]["delta"], 5)
        self.assertEqual(rows["a minus baseline"]["percent"], 10)
        self.assertIsNone(rows["ab - a - b + baseline"]["percent"])

    def test_nonadditive_no_interaction(self):
        result = self.result("gpu")
        self.assertEqual(len(result["comparisons"]), 3)
        self.assertTrue(any("not declared additive" in item for item in result["warnings"]))

    def test_one_factor_design(self):
        self.data["experiment"]["design"] = "one_factor"
        self.data["experiment"]["factors"] = ["tool-a"]
        self.data["experiment"]["dependencies"].pop("tool-b")
        self.data["runs"] = [run for run in self.data["runs"] if run["case"] in {"baseline", "a"}]
        self.assertEqual(self.result("cpu")["status"], "COMPARABLE")
        self.assertEqual(len(self.result("cpu")["comparisons"]), 1)

    def test_fps_cannot_claim_additive_interaction(self):
        self.data["metrics"][0]["unit"] = "FPS"
        self.data["metrics"][0]["additive"] = True
        result = self.result("cpu")
        self.assertEqual(len(result["comparisons"]), 3)
        self.assertTrue(any("FPS is nonlinear" in item for item in result["warnings"]))

    def test_incomplete_failure_and_null_preserved(self):
        row = self.result()["raw_runs"][-1]
        self.assertEqual(row["status"], "incomplete")
        self.assertIsNone(row["metrics"]["ram"])
        self.assertIsNone(row["ended_utc"])
        self.assertIn("producer stopped", row["failure_reason"])
        self.data["runs"][-1]["status"] = "failed"
        self.assertEqual(self.result()["raw_runs"][-1]["status"], "failed")

    def test_fewer_than_three_repeats_blocks(self):
        self.data["runs"].pop(0)
        result = self.result()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["comparisons"], [])
        self.assertIn("INSUFFICIENT_REPEATS", self.codes(result))

    def test_missing_metric_partial_not_zero(self):
        self.data["runs"][0]["metrics"].pop("ram")
        result = self.result()
        self.assertEqual(result["status"], "PARTIAL")
        self.assertIsNone(result["raw_runs"][0]["metrics"]["ram"])
        self.assertFalse(any(row["metric_id"] == "ram" for row in result["comparisons"]))

    def test_explicit_null_cannot_count_repeat(self):
        self.data["runs"][0]["metrics"]["cpu"]["value"] = None
        self.assertEqual(self.result("cpu")["status"], "BLOCKED")

    def test_actual_manager_idle_import_can_compare(self):
        self.data["origin"] = "imported_report"
        result = self.result()
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertFalse(result["synthetic_fixture"])
        self.assertFalse(result["runtime_verification"])
        self.assertEqual(result["provenance"]["report_hashes"], "declared_only")

    def test_actual_in_game_off_declarations_never_runtime_pass(self):
        self.rendering(real=True)
        result = self.result()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("RUNTIME_FG_UNVERIFIED", self.codes(result))
        self.assertEqual(result["case_summaries"], [])
        self.assertEqual(len(result["raw_runs"]), 13)

    def test_cannot_import_runtime_pass_field(self):
        self.rendering(real=True)
        self.data["runs"][0]["fg"]["trusted_runtime_pass"] = True
        self.reject()

    def test_synthetic_rendering_exercise_can_compare(self):
        self.rendering()
        self.assertEqual(self.result()["status"], "COMPARABLE")
        self.assertFalse(self.result()["runtime_verification"])

    def test_dynamic_mfg_active_and_unverified_block(self):
        self.rendering()
        for state in ("active", "unverified"):
            with self.subTest(state=state):
                self.data["runs"][0]["fg"]["dynamic_mfg"] = state
                self.assertIn("DYNAMIC_MFG_ACTIVE_OR_UNVERIFIED", self.codes())
                self.assertEqual(self.result()["comparisons"], [])

    def test_effective_unknown_blocks(self):
        self.rendering()
        self.data["runs"][0]["fg"]["effective_mode"] = "unknown"
        self.assertIn("EFFECTIVE_FG_UNKNOWN", self.codes())

    def test_fixed_fg_mismatch_blocks(self):
        self.rendering()
        for run in self.data["runs"]:
            run["fg"]["effective_mode"] = "fixed"
            run["fg"]["multiplier"] = 2
        self.data["runs"][0]["fg"]["multiplier"] = 4
        self.assertIn("FG_MODE_MISMATCH", self.codes())

    def test_memory_warning_any_run_suspends(self):
        for state in ("active", "unverified"):
            with self.subTest(state=state):
                self.data["runs"][-1]["memory_warning"] = state
                self.assertIn("MEMORY_WARNING", self.codes())
                self.assertEqual(self.result()["comparisons"], [])

    def test_workload_mismatch_blocks(self):
        for field in CORE._WORKLOAD_FIELDS:
            with self.subTest(field=field):
                data = deepcopy(self.data)
                data["runs"][0]["workload"][field] = "different"
                result = CORE.compare_dataset(data)
                self.assertIn("WORKLOAD_MISMATCH", self.codes(result))

    def test_identical_unknown_workload_does_not_match(self):
        for field in CORE._WORKLOAD_FIELDS:
            with self.subTest(field=field):
                data = deepcopy(self.data)
                for run in data["runs"]:
                    run["workload"][field] = "UnKnOwN"
                result = CORE.compare_dataset(data)
                self.assertIn("WORKLOAD_UNKNOWN", self.codes(result))
                self.assertEqual(result["comparisons"], [])

    def test_external_idle_cache_not_applicable_is_explicit(self):
        for run in self.data["runs"]:
            run["workload"]["cache_state"] = "not_applicable"
        self.assertEqual(self.result()["status"], "COMPARABLE")

    def test_duration_contradiction_and_unequal_windows_block(self):
        self.data["runs"][0]["duration_seconds"] = 10
        self.assertIn("COVERAGE_DURATION_CONTRADICTION", self.codes())
        self.assertIn("COVERAGE_WINDOW_MISMATCH", self.codes())
        self.data["runs"][0]["ended_utc"] = "2026-10-11T08:00:10Z"
        self.assertNotIn("COVERAGE_DURATION_CONTRADICTION", self.codes())
        self.assertIn("COVERAGE_WINDOW_MISMATCH", self.codes())

    def test_configuration_mismatch_blocks(self):
        self.data["runs"][0]["configuration"]["fingerprint"] = "b" * 64
        self.assertIn("CONFIGURATION_MISMATCH", self.codes())

    def test_unknown_external_process_scope_blocks(self):
        self.data["runs"][0]["workload"]["process_scope"] = "unknown"
        self.assertIn("EXTERNAL_SCOPE_UNSUPPORTED", self.codes())

    def test_nonidle_external_workload_blocks(self):
        self.data["runs"][0]["workload"]["phase"] = "installing"
        self.assertIn("EXTERNAL_SCOPE_UNSUPPORTED", self.codes())

    def test_external_rendering_declaration_blocks(self):
        self.data["runs"][0]["fg"]["effective_mode"] = "off"
        self.assertIn("EXTERNAL_FG_SCOPE", self.codes())

    def test_component_mismatch_blocks(self):
        self.data["runs"][0]["components"] = []
        self.assertIn("COMPONENT_STATE_MISMATCH", self.codes())

    def test_dependency_preserving_shared_host_required(self):
        self.data["experiment"]["dependencies"]["tool-b"] = ["tool-a"]
        self.reject()

    def test_descriptor_boundaries_never_mix(self):
        changed = {"provider": "another", "provider_version": "another", "definition": "another",
                   "unit": "GB", "scope": "game only", "frame_class": "displayed",
                   "latency_endpoints": ["input", "display"]}
        for field, value in changed.items():
            with self.subTest(field=field):
                data = deepcopy(self.data)
                descriptor = deepcopy(data["metrics"][0])
                descriptor[field] = value
                data["runs"][0]["metrics"]["cpu"]["descriptor"] = descriptor
                result = CORE.compare_dataset(data, "cpu")
                self.assertIn("METRIC_DEFINITION_MISMATCH", self.codes(result))
                self.assertEqual(result["comparisons"], [])
                self.assertEqual(result["raw_runs"][0]["metric_definitions"]["cpu"][field], value)

    def test_unknown_metric_semantics_block(self):
        self.data["metrics"][0]["provider_version"] = "unknown"
        self.assertIn("METRIC_COVERAGE_UNKNOWN", self.codes(self.result("cpu")))

    def test_duplicate_report_not_independent_repeat(self):
        self.data["runs"][0]["source_sha256"] = self.data["runs"][1]["source_sha256"]
        self.assertIn("DUPLICATED_REPORT", self.codes())

    def test_duplicate_run_and_repeat_reject(self):
        for field in ("id", "repeat"):
            with self.subTest(field=field):
                data = deepcopy(self.data)
                data["runs"][1][field] = data["runs"][0][field]
                with self.assertRaises(CORE.ComparisonError):
                    CORE.validate_dataset(data)

    def test_zero_baseline_percent_unavailable(self):
        for run in self.data["runs"]:
            if run["case"] == "baseline":
                run["metrics"]["cpu"]["value"] = 0
        result = self.result("cpu")
        self.assertTrue(all(row["percent"] is None for row in result["comparisons"]))

    def test_percentage_numeric_overflow_unavailable(self):
        for run in self.data["runs"]:
            if run["case"] == "baseline":
                run["metrics"]["cpu"]["value"] = 1e-320
        result = self.result("cpu")
        json.dumps(result, allow_nan=False)
        self.assertTrue(all(row["percent"] is None for row in result["comparisons"]))

    def test_nonfinite_bool_and_numeric_text_rejected(self):
        for value in (True, "0", float("inf"), float("nan"), 1e101):
            with self.subTest(value=value):
                self.data["runs"][0]["metrics"]["cpu"]["value"] = value
                self.reject()

    def test_bad_source_hash_rejected(self):
        self.data["runs"][0]["source_sha256"] = "not-a-hash"
        self.reject()

    def test_malformed_enum_types_have_safe_comparison_error(self):
        paths = (("origin",), ("measurement_scope",), ("experiment", "design"),
                 ("runs", 0, "case"), ("runs", 0, "status"), ("runs", 0, "memory_warning"),
                 ("runs", 0, "fg", "dynamic_mfg"), ("runs", 0, "fg", "effective_mode"),
                 ("runs", 0, "fg", "evidence"))
        for path in paths:
            for value in ([], {}, None, True, 1):
                with self.subTest(path=path, value=value):
                    data = deepcopy(self.data)
                    parent = data
                    for key in path[:-1]:
                        parent = parent[key]
                    parent[path[-1]] = value
                    with self.assertRaises(CORE.ComparisonError):
                        CORE.validate_dataset(data)
        source = self.write()
        for value in ([], {}, None, True, 1):
            with self.subTest(format=value):
                with self.assertRaises(CORE.ComparisonError):
                    CORE.export_report(source, self.folder / "never-created", format=value)
            if value is not None:
                with self.subTest(metric=value):
                    with self.assertRaises(CORE.ComparisonError):
                        CORE.compare_dataset(self.data, metric_id=value)
        self.assertFalse((self.folder / "never-created").exists())

    def test_timestamp_and_coverage_invalid(self):
        for field, value in (("started_utc", "2026-10-11T10:00:00+02:00"),
                             ("ended_utc", "2026-10-10T08:00:00Z"),
                             ("sample_count", 0), ("duration_seconds", None)):
            with self.subTest(field=field):
                data = deepcopy(self.data)
                data["runs"][0][field] = value
                with self.assertRaises(CORE.ComparisonError):
                    CORE.validate_dataset(data)

    def test_failed_requires_reason(self):
        self.data["runs"][-1]["failure_reason"] = None
        self.reject()

    def test_dataset_and_text_bounds(self):
        for field, value in (("runs", self.data["runs"] * 21), ("metrics", self.data["metrics"] * 17),
                             ("title", "x" * 4097)):
            with self.subTest(field=field):
                data = deepcopy(self.data)
                data[field] = value
                with self.assertRaises(CORE.ComparisonError):
                    CORE.validate_dataset(data)

    def test_depth_limit_before_schema(self):
        value = {}
        nested = value
        for _ in range(14):
            nested["nested"] = {}
            nested = nested["nested"]
        with self.assertRaises(CORE.ComparisonError):
            CORE.validate_dataset(value)

    def test_shared_definitions_cannot_amplify_into_unbounded_report(self):
        for metric in self.data["metrics"]:
            for field in ("label", "provider", "provider_version", "definition", "unit", "scope", "frame_class"):
                metric[field] = "x" * 4096
        original = self.data["runs"][:12]
        runs = []
        for index in range(100):
            run = deepcopy(original[index % 12])
            run["id"] = "expanded-" + str(index)
            run["repeat"] = index + 1
            run["source_sha256"] = format(index + 1, "064x")
            runs.append(run)
        self.data["runs"] = runs
        CORE.validate_dataset(self.data)  # Input itself is below two MiB.
        with self.assertRaises(CORE.ComparisonError):
            self.result()

    def test_selected_metric_only_and_unknown_rejected(self):
        self.assertEqual([item["id"] for item in self.result("ram")["metrics"]], ["ram"])
        with self.assertRaises(CORE.ComparisonError):
            self.result("unavailable")

    def test_input_object_unchanged(self):
        before = deepcopy(self.data)
        self.result()
        self.assertEqual(self.data, before)

    def test_loaded_dataset_bytes_verified_private_locator_not_exported(self):
        path = self.write()
        loaded = CORE.load_dataset(path)
        result = CORE.compare_dataset(loaded)
        self.assertTrue(result["provenance"]["normalized_bytes_verified"])
        self.assertEqual(result["provenance"]["dataset_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertNotIn(str(path), json.dumps(result))
        self.assertNotIn(str(path), CORE.render_html(result))

    def test_stale_file_refuses_compare_export(self):
        path = self.write()
        loaded = CORE.load_dataset(path)
        self.data["title"] = "changed"
        self.write()
        with self.assertRaises(CORE.ComparisonError):
            CORE.compare_dataset(loaded)
        with self.assertRaises(CORE.ComparisonError):
            CORE.export_report(path, self.folder / "out.json", expected_sha256=loaded["_source"]["sha256"])
        self.assertFalse((self.folder / "out.json").exists())

    def test_changed_loaded_object_cannot_claim_verified_bytes(self):
        loaded = CORE.load_dataset(self.write())
        loaded["title"] = "not original bytes"
        with self.assertRaises(CORE.ComparisonError):
            CORE.compare_dataset(loaded)

    def test_duplicate_json_fields_refused(self):
        path = self.folder / "bad.json"
        path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaises(CORE.ComparisonError):
            CORE.load_dataset(path)

    def test_large_file_invalid_utf8_and_nonfinite_json_refused(self):
        path = self.folder / "bad.json"
        for value in (b"x" * (CORE.MAX_DATASET_BYTES + 1), b"\xff", b'{"value":NaN}'):
            with self.subTest(size=len(value)):
                path.write_bytes(value)
                with self.assertRaises(CORE.ComparisonError):
                    CORE.load_dataset(path)

    def test_source_error_path_free(self):
        with self.assertRaises(CORE.ComparisonError) as caught:
            CORE.load_dataset(self.folder / "secret-missing.json")
        self.assertNotIn(str(self.folder), str(caught.exception))

    def test_html_escapes_malicious_text_no_scripts_links_media(self):
        self.data["title"] = '<script>alert("bad")</script>'
        self.data["metrics"][0]["definition"] = '<img src="https://invalid/" onerror="alert(1)">'
        rendered = CORE.render_html(self.result())
        self.assertNotIn("<script", rendered)
        self.assertNotIn("<img", rendered)
        self.assertNotIn("<a ", rendered)
        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("Content-Security-Policy", rendered)

    def test_html_preserves_per_run_definitions_and_preflight_metadata(self):
        descriptor = deepcopy(self.data["metrics"][0])
        descriptor["scope"] = "different exact per-run scope"
        self.data["runs"][0]["metrics"]["cpu"]["descriptor"] = descriptor
        self.data["runs"][0]["memory_warning"] = "active"
        rendered = CORE.render_html(self.result())
        self.assertIn("different exact per-run scope", rendered)
        for field in ("workload", "configuration", "fg", "memory_warning", "duration_seconds", "sample_count"):
            self.assertIn(field, rendered)
        self.assertIn("MEMORY_WARNING", rendered)
        self.assertIn("METRIC_DEFINITION_MISMATCH", rendered)

    def test_json_html_export_preserve_source_and_select_metric(self):
        source = self.write()
        before = source.read_bytes()
        for format in ("json", "html"):
            with self.subTest(format=format):
                target = self.folder / ("report." + format)
                receipt = CORE.export_report(source, target, format=format, metric_id="ram")
                self.assertEqual(receipt["sha256"], hashlib.sha256(target.read_bytes()).hexdigest())
                self.assertEqual(receipt["execution"], "none")
                self.assertEqual(source.read_bytes(), before)
                if format == "json":
                    self.assertEqual([item["id"] for item in json.loads(target.read_text())["metrics"]], ["ram"])
        self.assertFalse(list(self.folder.glob(".game-comparison-*.tmp")))

    def test_existing_destination_and_source_never_overwritten(self):
        source = self.write()
        target = self.folder / "keep.txt"
        target.write_text("existing", encoding="utf-8")
        for destination in (target, source):
            with self.subTest(destination=destination.name):
                before = destination.read_bytes()
                with self.assertRaises(CORE.ComparisonError):
                    CORE.export_report(source, destination)
                self.assertEqual(destination.read_bytes(), before)

    def test_export_format_and_missing_parent_refused(self):
        path = self.write()
        with self.assertRaises(CORE.ComparisonError):
            CORE.export_report(path, self.folder / "x", format="pdf")
        with self.assertRaises(CORE.ComparisonError):
            CORE.export_report(path, self.folder / "missing" / "x")

    def test_export_publish_failure_cleanup(self):
        path = self.write()
        target = self.folder / "x.json"
        with patch.object(CORE.os, "link", side_effect=OSError("synthetic disk/full publish failure")):
            with self.assertRaises(CORE.ComparisonError):
                CORE.export_report(path, target)
        self.assertFalse(target.exists())
        self.assertFalse(list(self.folder.glob(".game-comparison-*.tmp")))

    def test_export_source_changes_after_publication_rollback_owned_file(self):
        path = self.write()
        target = self.folder / "x.json"
        original = CORE.os.link
        def link_then_change(source, destination):
            original(source, destination)
            self.data["title"] = "concurrent new source"
            self.write()
        with patch.object(CORE.os, "link", side_effect=link_then_change):
            with self.assertRaises(CORE.ComparisonError):
                CORE.export_report(path, target)
        self.assertFalse(target.exists())
        self.assertEqual(json.loads(path.read_text())["title"], "concurrent new source")
        self.assertFalse(list(self.folder.glob(".game-comparison-*.tmp")))

    def test_export_blocked_raw_reports_keeps_gates(self):
        self.rendering(real=True)
        source = self.write()
        target = self.folder / "blocked.json"
        receipt = CORE.export_report(source, target)
        result = json.loads(target.read_text())
        self.assertEqual(receipt["status"], "BLOCKED")
        self.assertEqual(len(result["raw_runs"]), 13)
        self.assertEqual(result["comparisons"], [])
        self.assertIn("RUNTIME_FG_UNVERIFIED", self.codes(result))


if __name__ == "__main__":
    unittest.main(verbosity=2)
