"""Offline owner/deadline/privacy contracts. No game, provider, recording or UI."""
from copy import deepcopy
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("coordinator_contracts", ROOT / "scripts/GameToolCoordinator.py")
CORE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CORE)
FIXTURES = ROOT / "examples/game-tool-hub/import-fixtures"
COMPARISON = ROOT / "examples/game-tool-hub/comparison-fixture.example.json"


class Clock:
    def __init__(self):
        self.value = 10.0

    def __call__(self):
        return self.value


class CoordinatorContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="GameCoordinatorContract-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.cp = self.folder / "saved-summary.json"
        self.cp.write_bytes((FIXTURES / "cyberpunk-summary.example.json").read_bytes())
        self.pm = self.folder / "saved-stats.csv"
        self.pm.write_bytes((FIXTURES / "presentmon-stats.example.csv").read_bytes())
        self.dataset = self.folder / "saved-dataset.json"
        self.dataset.write_bytes(COMPARISON.read_bytes())
        self.journal = self.folder / "session.jsonl"
        self.clock = Clock()
        self.c = CORE.Coordinator(clock=self.clock,
            utc_clock=lambda: datetime(2026, 10, 11, 8, tzinfo=timezone.utc))
        self.addCleanup(self.c.close)

    def start(self, **kwargs):
        return self.c.start(self.journal, **kwargs)

    def events(self):
        return [json.loads(line) for line in self.journal.read_text(encoding="utf-8").splitlines()]

    def assert_code(self, code, call, *args, **kwargs):
        with self.assertRaises(CORE.CoordinatorError) as failure:
            call(*args, **kwargs)
        self.assertEqual(failure.exception.code, code)
        self.assertNotIn(str(self.folder), str(failure.exception))
        return failure.exception

    def test_constructor_capabilities_and_idle_status_are_inert(self):
        before = {p.name: p.read_bytes() for p in self.folder.iterdir()}
        with patch.object(CORE, "_capture", side_effect=AssertionError("unexpected read")):
            coordinator = CORE.Coordinator()
            self.assertEqual(coordinator.status()["state"], "idle")
            self.assertEqual(coordinator.close()["state"], "idle")
            self.assertEqual(coordinator.cancel()["state"], "idle")
            self.assertEqual(set(CORE.capabilities()["capabilities"]), {"saved_report", "comparison", "crash_evidence", "workflow", "readiness"})
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.folder.iterdir()})

    def test_versioned_fixed_offline_capabilities_no_executor(self):
        contract = CORE.capabilities()
        self.assertEqual(CORE.VERSION, "0.4.0")
        self.assertEqual(contract["scope"], "offline_saved_data")
        self.assertEqual(contract["execution"], "offline_only")
        self.assertFalse(contract["runtime_verification"])
        self.assertTrue({"game_input", "launch", "benchmarks", "recording", "automatic_replay"} <= set(contract["unavailable"]))
        self.assertFalse(hasattr(self.c, "dispatch"))
        contract["capabilities"]["saved_report"]["adapters"].append("arbitrary")
        self.assertNotIn("arbitrary", CORE.capabilities()["capabilities"]["saved_report"]["adapters"])

    def test_source_has_no_live_control_or_hidden_listener_import(self):
        tree = ast.parse((ROOT / "scripts/GameToolCoordinator.py").read_text(encoding="utf-8"))
        imported = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}
        imported |= {node.module.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        self.assertFalse(imported & {"subprocess", "ctypes", "socket", "keyboard", "pynput", "win32api"})
        self.assertEqual(set(CORE._SIBLINGS), {"journal", "saved_report", "comparison", "crash_evidence", "workflow", "readiness"})

    def test_invalid_metadata_lifetime_and_clock_rejected_without_writes(self):
        for owner in ("", "path/secret", "C:\\secret", "line\nline", "x" * 81, "שלום", True):
            with self.subTest(owner=owner):
                self.assert_code("INVALID_METADATA", CORE.Coordinator, owner=owner)
        for lifetime in (0, -1, 3601, float("nan"), float("inf"), True, "900", 10 ** 400):
            with self.subTest(lifetime=str(lifetime)[:20]):
                self.assert_code("INVALID_LIFETIME", CORE.Coordinator, lifetime_seconds=lifetime)
        self.assert_code("INVALID_CLOCK", CORE.Coordinator, clock="not callable")
        self.assertFalse(self.journal.exists())

    def test_invalid_start_label_does_not_create_journal(self):
        self.assert_code("INVALID_METADATA", self.start, label="C:/private/path")
        self.assertEqual(self.c.status()["state"], "idle")
        self.assertFalse(self.journal.exists())

    def test_invalid_utc_clock_does_not_create_journal_or_expose_exception(self):
        c = CORE.Coordinator(utc_clock=lambda: (_ for _ in ()).throw(OSError("C:/private/secret")))
        self.assert_code("INVALID_CLOCK", c.start, self.journal)
        self.assertFalse(self.journal.exists())

    def test_naive_utc_clock_refused(self):
        c = CORE.Coordinator(utc_clock=lambda: datetime(2026, 10, 11))
        self.assert_code("INVALID_CLOCK", c.start, self.journal)
        self.assertFalse(self.journal.exists())

    def test_expiry_utc_overflow_validated_before_creating_writer(self):
        c = CORE.Coordinator(utc_clock=lambda: datetime.max.replace(tzinfo=timezone.utc))
        self.assert_code("INVALID_CLOCK", c.start, self.journal)
        self.assertEqual(c.status()["state"], "idle")
        self.assertIsNone(c._journal)
        self.assertFalse(self.journal.exists())

    def test_start_generates_unique_owner_and_session_and_complete_metadata(self):
        row = self.start(label="Offline validation")
        self.assertEqual(row["state"], "active")
        self.assertEqual(row["phase"], "Ready")
        self.assertEqual(row["remaining_seconds"], 900)
        self.assertEqual(row["journal_records"], 2)
        self.assertEqual(len(row["owner_id"]), 32)
        self.assertEqual(len(row["session_id"]), 32)
        self.assertNotEqual(row["owner_id"], row["session_id"])
        self.assertEqual(row["started_utc"], "2026-10-11T08:00:00.000000Z")
        self.assertEqual(row["expires_utc_hint"], "2026-10-11T08:15:00.000000Z")
        events = self.events()
        self.assertEqual([r["kind"] for r in events], ["journal_created", "session_started"])
        self.assertFalse(events[0]["data"]["replay_permitted"])
        self.assertEqual(events[1]["data"]["deadline_basis"], "process_monotonic")

    def test_start_requires_new_destination_and_never_reopens_old_evidence(self):
        self.journal.write_bytes(b"existing private evidence\n")
        self.assert_code("JOURNAL_CREATE_FAILED", self.start)
        self.assertEqual(self.journal.read_bytes(), b"existing private evidence\n")
        self.assertEqual(self.c.status()["state"], "failed")

    def test_second_start_same_owner_rejected_and_existing_unchanged(self):
        self.start()
        before = self.journal.read_bytes()
        self.assert_code("SESSION_ALREADY_USED", self.c.start, self.folder / "other.jsonl")
        self.assertEqual(self.journal.read_bytes(), before)
        self.assertFalse((self.folder / "other.jsonl").exists())

    def test_not_started_operations_do_not_read_source_or_dispatch(self):
        with patch.object(CORE, "_capture", side_effect=AssertionError("source read")):
            self.assert_code("SESSION_NOT_STARTED", self.c.inspect_saved_report, self.cp)
            self.assert_code("SESSION_NOT_STARTED", self.c.inspect_comparison, self.dataset)
            self.assert_code("SESSION_NOT_STARTED", self.c.checkpoint, "Inspection")
            self.assert_code("SESSION_NOT_STARTED", self.c.finish)
        self.assertFalse(self.journal.exists())

    def test_checkpoint_is_durable_phase_and_status_is_deep_copy(self):
        self.start()
        row = self.c.checkpoint("Review phase 1")
        self.assertEqual(row["phase"], "Review phase 1")
        self.assertEqual(self.events()[-1]["kind"], "checkpoint")
        row["limitations"].clear()
        self.assertTrue(self.c.status()["limitations"])

    def test_status_does_not_append_or_touch_file_times(self):
        self.start()
        before = self.journal.read_bytes(), self.journal.stat().st_mtime_ns
        for _ in range(5):
            self.c.status()
        self.assertEqual(before, (self.journal.read_bytes(), self.journal.stat().st_mtime_ns))

    def test_saved_report_uses_existing_adapter_preserves_values_and_source(self):
        self.start()
        before = self.cp.read_bytes(), self.cp.stat().st_mtime_ns
        result = self.c.inspect_saved_report(self.cp)
        self.assertEqual(result["adapter"], "cyberpunk_benchmark_summary")
        self.assertEqual(result["metrics"][0]["value"], 60)
        self.assertNotIn("private_source", result)
        self.assertFalse(result["runtime_verification"])
        self.assertEqual(result["source_sha256"], hashlib.sha256(before[0]).hexdigest())
        self.assertEqual(before, (self.cp.read_bytes(), self.cp.stat().st_mtime_ns))
        self.assertEqual(self.c.status()["latest_action"]["state"], "observed")

    def test_presentmon_auto_and_explicit_adapters_supported(self):
        self.start()
        for adapter in ("auto", "presentmon_gui_stats"):
            result = self.c.inspect_saved_report(self.pm, adapter=adapter)
            self.assertEqual(result["adapter"], "presentmon_gui_stats")
            self.assertEqual(result["metrics"][0]["frame_class"], "presented_intervals")

    def test_expected_hash_is_case_insensitive_and_no_receipt_authority(self):
        self.start()
        digest = hashlib.sha256(self.cp.read_bytes()).hexdigest()
        result = self.c.inspect_saved_report(self.cp, expected_sha256=digest.upper())
        self.assertEqual(result["source_sha256"], digest)
        self.assertFalse(result["runtime_verification"])

    def test_status_and_journal_exclude_paths_report_content_and_payloads(self):
        data = json.loads(self.cp.read_text(encoding="utf-8"))
        data["Data"]["benchmarkName"] = "private token should remain only in returned report"
        self.cp.write_text(json.dumps(data), encoding="utf-8")
        self.start()
        result = self.c.inspect_saved_report(self.cp)
        self.assertIn("private token", result["raw_metadata"]["benchmarkName"])
        evidence = self.journal.read_text(encoding="utf-8") + json.dumps(self.c.status())
        self.assertNotIn(str(self.folder), evidence)
        self.assertNotIn(self.cp.name, evidence)
        self.assertNotIn("private token", evidence)
        self.assertNotIn("requested_settings", evidence)
        self.assertNotIn("reported_fps", evidence)
        self.assertNotIn("raw_metadata", evidence)

    def test_comparison_reuses_fixture_definitions_without_recalculating_frames(self):
        self.start()
        result = self.c.inspect_comparison(self.dataset, metric="ram")
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertTrue(result["synthetic_fixture"])
        self.assertFalse(result["runtime_verification"])
        self.assertEqual(result["execution"], "none")
        self.assertEqual([r["id"] for r in result["metrics"]], ["ram"])
        self.assertEqual(result["case_summaries"][0]["mean"], 100)
        self.assertEqual(self.events()[-1]["data"]["status"], "COMPARABLE")
        self.assertNotIn("raw_runs", self.journal.read_text(encoding="utf-8"))

    def test_real_rendering_comparison_retains_fg_block(self):
        data = json.loads(self.dataset.read_text(encoding="utf-8"))
        data["origin"], data["measurement_scope"] = "imported_report", "injected_feature"
        for run in data["runs"]:
            run["fg"] = {"dynamic_mfg": "inactive", "effective_mode": "off", "multiplier": None, "evidence": "declared"}
        self.dataset.write_text(json.dumps(data), encoding="utf-8")
        self.start()
        result = self.c.inspect_comparison(self.dataset)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("RUNTIME_FG_UNVERIFIED", {r["code"] for r in result["gates"]})
        self.assertFalse(result["runtime_verification"])

    def test_invalid_hash_adapter_and_metric_rejected_before_dispatch(self):
        self.start()
        before = self.journal.read_bytes()
        for digest in (False, "wrong", "a" * 65, "g" * 64):
            self.assert_code("INVALID_HASH", self.c.inspect_saved_report, self.cp, expected_sha256=digest)
        for adapter in ("custom_module.py", "launch", {}, None):
            self.assert_code("INVALID_ADAPTER", self.c.inspect_saved_report, self.cp, adapter=adapter)
        for metric in (False, "x\nsecret", "../source", "x" * 81):
            self.assert_code("INVALID_METRIC", self.c.inspect_comparison, self.dataset, metric=metric)
        self.assertEqual(before, self.journal.read_bytes())

    def test_expected_hash_mismatch_records_failure_without_accepting(self):
        self.start()
        self.assert_code("SOURCE_CHANGED", self.c.inspect_saved_report, self.cp, expected_sha256="0" * 64)
        self.assertEqual(self.c.status()["latest_action"]["state"], "failed")
        self.assertEqual(self.events()[-1]["data"]["error_code"], "SOURCE_CHANGED")
        self.assertEqual(self.c.status()["state"], "active")

    def test_invalid_saved_source_failure_is_fixed_path_free_and_retry_explicit(self):
        self.start()
        self.cp.write_text("invalid summary", encoding="utf-8")
        self.assert_code("ADAPTER_REFUSED", self.c.inspect_saved_report, self.cp)
        self.assertEqual(self.events()[-1]["kind"], "action_failed")
        self.cp.write_bytes((FIXTURES / "cyberpunk-summary.example.json").read_bytes())
        self.assertEqual(self.c.inspect_saved_report(self.cp)["adapter"], "cyberpunk_benchmark_summary")

    def test_missing_empty_oversized_or_directory_source_refused(self):
        self.start()
        cases = [self.folder / "absent", self.folder]
        empty = self.folder / "empty"
        empty.write_bytes(b"")
        huge = self.folder / "huge"
        huge.write_bytes(b"x" * (CORE.MAX_SOURCE_BYTES + 1))
        for source in [*cases, empty, huge]:
            with self.subTest(source=source.name):
                self.assert_code("SOURCE_UNAVAILABLE", self.c.inspect_saved_report, source)
        self.assertFalse(any(r["kind"] == "action_observed" for r in self.events()))

    def test_source_content_change_during_adapter_refused(self):
        self.start()
        backend = self.c._module("saved_report")
        original = backend.inspect_report
        def change(source, **kwargs):
            result = original(source, **kwargs)
            source.write_bytes(source.read_bytes() + b" ")
            return result
        with patch.object(backend, "inspect_report", side_effect=change):
            self.assert_code("SOURCE_CHANGED", self.c.inspect_saved_report, self.cp)
        self.assertEqual(self.events()[-1]["kind"], "action_failed")

    def test_source_object_replacement_even_identical_bytes_refused(self):
        self.start()
        backend = self.c._module("saved_report")
        original = backend.inspect_report
        def replace(source, **kwargs):
            result = original(source, **kwargs)
            replacement = self.folder / "replacement"
            replacement.write_bytes(source.read_bytes())
            os.replace(replacement, source)
            return result
        with patch.object(backend, "inspect_report", side_effect=replace):
            self.assert_code("SOURCE_CHANGED", self.c.inspect_saved_report, self.cp)

    def test_reparse_source_refusal_is_deterministic(self):
        self.start()
        original = Path.lstat
        def linked(path):
            row = original(path)
            if path == self.cp:
                class Linked:
                    st_mode = row.st_mode
                    st_file_attributes = 0x400
                return Linked()
            return row
        with patch.object(Path, "lstat", linked):
            self.assert_code("SOURCE_UNAVAILABLE", self.c.inspect_saved_report, self.cp)

    def test_unchanged_ctime_difference_is_not_false_drift(self):
        self.start()
        original = CORE.os.fstat
        def changed_ctime(fd):
            row = original(fd)
            class Stat:
                st_mode = row.st_mode
                st_dev, st_ino, st_size, st_mtime_ns = row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns
                st_ctime_ns = row.st_ctime_ns + 12345
            return Stat()
        # The stable-source helper intentionally compares the established fields,
        # not Windows's inconsistent fstat/stat ctime meaning.
        with patch.object(CORE.os, "fstat", changed_ctime):
            _, row = CORE._capture(self.cp)
        self.assertEqual(row["sha256"], hashlib.sha256(self.cp.read_bytes()).hexdigest())

    def test_special_file_metadata_refused_before_open(self):
        original = Path.stat
        def special(path, **kwargs):
            row = original(path, **kwargs)
            if path == self.cp:
                class Special:
                    st_mode = stat.S_IFIFO
                    st_size = 20
                return Special()
            return row
        with patch.object(Path, "stat", special), patch.object(Path, "open", side_effect=AssertionError("special file opened")):
            self.assert_code("SOURCE_UNAVAILABLE", CORE._capture, self.cp)

    def test_module_loading_is_exact_captured_source_and_no_bytecode(self):
        self.start()
        self.c.inspect_saved_report(self.cp)
        self.assertEqual(set(self.c._modules), {"journal", "saved_report"})
        self.assertEqual(self.c._modules["saved_report"][0].__file__, str(ROOT / "scripts/GameToolReportImport.py"))
        self.assertFalse(any(p.name == "__pycache__" for p in self.folder.iterdir()))

    def test_changed_fixed_module_is_not_silently_reloaded(self):
        self.start()
        self.c._module("saved_report")
        original = CORE._capture
        def changed(path, maximum=CORE.MAX_SOURCE_BYTES):
            raw, snapshot = original(path, maximum)
            if Path(path).name == "GameToolReportImport.py":
                snapshot["sha256"] = "0" * 64
            return raw, snapshot
        with patch.object(CORE, "_capture", side_effect=changed):
            self.assert_code("MODULE_CHANGED", self.c.inspect_saved_report, self.cp)
        self.assertFalse(any(r["kind"] == "action_requested" for r in self.events()))

    def test_expiry_status_read_only_then_operation_durably_cancels(self):
        self.start()
        before = self.journal.read_bytes()
        self.clock.value += 900
        self.assertEqual(self.c.status()["state"], "expired")
        self.assertEqual(self.c.status()["remaining_seconds"], 0)
        self.assertEqual(before, self.journal.read_bytes())
        self.assert_code("SESSION_EXPIRED", self.c.checkpoint, "Later")
        self.assertEqual(self.events()[-1]["kind"], "session_cancelled")
        self.assertEqual(self.events()[-1]["data"]["reason_code"], "expired")
        self.assertIsNone(self.c._journal)

    def test_expiry_during_read_discards_result_no_observed_event(self):
        self.start()
        backend = self.c._module("saved_report")
        original = backend.inspect_report
        def expire(source, **kwargs):
            result = original(source, **kwargs)
            self.clock.value += 901
            return result
        with patch.object(backend, "inspect_report", side_effect=expire):
            self.assert_code("SESSION_EXPIRED", self.c.inspect_saved_report, self.cp)
        self.assertFalse(any(r["kind"] == "action_observed" for r in self.events()))
        self.assertEqual(self.c.status()["latest_action"]["state"], "cancelled")

    def test_cancel_during_read_discards_result_and_never_replays(self):
        self.start()
        backend = self.c._module("saved_report")
        original = backend.inspect_report
        def cancel(source, **kwargs):
            result = original(source, **kwargs)
            self.c.cancel()
            return result
        with patch.object(backend, "inspect_report", side_effect=cancel):
            self.assert_code("SESSION_CANCELLED", self.c.inspect_saved_report, self.cp)
        self.assertEqual(self.c.status()["state"], "cancelled")
        self.assertFalse(any(r["kind"] == "action_observed" for r in self.events()))
        self.assert_code("SESSION_ALREADY_USED", self.c.start, self.folder / "restart.jsonl")

    def test_cancel_can_interrupt_acceptance_from_another_thread(self):
        self.start()
        backend = self.c._module("saved_report")
        original = backend.inspect_report
        entered, release = threading.Event(), threading.Event()
        errors = []
        def waiting(source, **kwargs):
            entered.set()
            if not release.wait(5):
                raise AssertionError("fixture timed out")
            return original(source, **kwargs)
        def worker():
            try:
                self.c.inspect_saved_report(self.cp)
            except CORE.CoordinatorError as error:
                errors.append(error.code)
        with patch.object(backend, "inspect_report", side_effect=waiting):
            thread = threading.Thread(target=worker)
            thread.start()
            try:
                self.assertTrue(entered.wait(5))
                self.assertEqual(self.c.cancel()["state"], "cancelled")
            finally:
                release.set()
                thread.join(5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(errors, ["SESSION_CANCELLED"])

    def test_parallel_request_and_checkpoint_refused_while_owned_read(self):
        self.start()
        backend = self.c._module("saved_report")
        original = backend.inspect_report
        def busy(source, **kwargs):
            self.assert_code("ACTION_BUSY", self.c.inspect_saved_report, self.pm)
            self.assert_code("ACTION_BUSY", self.c.checkpoint, "Concurrent")
            self.assert_code("ACTION_BUSY", self.c.finish)
            return original(source, **kwargs)
        with patch.object(backend, "inspect_report", side_effect=busy):
            self.assertEqual(self.c.inspect_saved_report(self.cp)["adapter"], "cyberpunk_benchmark_summary")
        self.assertEqual(sum(r["kind"] == "action_requested" for r in self.events()), 1)

    def test_backward_or_nonfinite_monotonic_clock_fails_closed(self):
        self.start()
        self.clock.value = 9
        self.assert_code("INVALID_CLOCK", self.c.checkpoint, "Impossible")
        self.assertEqual(self.c.status()["state"], "failed")
        self.assertIsNone(self.c._journal)
        self.assertEqual(self.events()[-1]["data"]["reason_code"], "invalid_clock")

    def test_wall_clock_hint_never_grants_monotonic_extension(self):
        self.start()
        self.c._utc_clock = lambda: datetime(1900, 1, 1, tzinfo=timezone.utc)
        self.clock.value = 911
        self.assert_code("SESSION_EXPIRED", self.c.inspect_saved_report, self.cp)

    def test_cancel_finish_and_close_affect_only_owned_journal(self):
        self.start()
        other_path = self.folder / "other-owner.jsonl"
        other = CORE.Coordinator(owner="Other owner")
        self.addCleanup(other.close)
        other.start(other_path)
        before = other_path.read_bytes()
        self.assertEqual(self.c.cancel()["state"], "cancelled")
        self.assertEqual(other.status()["state"], "active")
        self.assertEqual(other_path.read_bytes(), before)
        self.assertEqual(other.finish()["state"], "finished")
        self.assertEqual(other.close()["state"], "finished")

    def test_terminal_finish_prevents_new_operations_without_touching_sources(self):
        self.start()
        self.c.inspect_saved_report(self.cp)
        self.assertEqual(self.c.finish()["state"], "finished")
        self.assertEqual(self.events()[-1]["kind"], "session_closed")
        before = self.journal.read_bytes()
        with patch.object(CORE, "_capture", side_effect=AssertionError("unexpected read")):
            self.assert_code("SESSION_ENDED", self.c.inspect_saved_report, self.cp)
            self.assertEqual(self.c.close()["state"], "finished")
            self.assertEqual(self.c.cancel()["state"], "finished")
        self.assertEqual(self.journal.read_bytes(), before)

    def test_close_cancel_is_idempotent_and_uses_fixed_reason(self):
        self.start()
        self.assertEqual(self.c.close()["state"], "cancelled")
        self.assertEqual(self.events()[-1]["data"]["reason_code"], "shutdown")
        before = self.journal.read_bytes()
        self.c.close()
        self.c.cancel()
        self.assertEqual(self.journal.read_bytes(), before)

    def test_free_cancel_reason_not_logged_as_payload(self):
        self.start()
        self.c.cancel("sensitive typed text")
        self.assertNotIn("sensitive typed text", self.journal.read_text(encoding="utf-8"))
        self.assertEqual(self.events()[-1]["data"]["reason_code"], "requested")

    def test_journal_ack_failure_does_not_claim_observed_success(self):
        self.start()
        writer = self.c._journal
        original = writer.append
        def refuse(kind, data):
            if kind == "action_observed":
                raise OSError("C:/private/path disk full")
            return original(kind, data)
        with patch.object(writer, "append", side_effect=refuse):
            self.assert_code("JOURNAL_FAILURE", self.c.inspect_saved_report, self.cp)
        status = self.c.status()
        self.assertEqual(status["state"], "failed")
        self.assertEqual(status["latest_action"]["state"], "failed")
        self.assertEqual(status["latest_action"]["error_code"], "JOURNAL_FAILURE")
        self.assertIsNone(self.c._journal)
        self.assertFalse(any(r["kind"] == "action_observed" for r in self.events()))

    def test_checkpoint_journal_failure_cannot_continue(self):
        self.start()
        writer = self.c._journal
        with patch.object(writer, "append", side_effect=OSError("fixture failure")):
            self.assert_code("JOURNAL_FAILURE", self.c.checkpoint, "New phase")
        self.assertEqual(self.c.status()["state"], "failed")
        self.assertEqual(self.c.status()["phase"], "Ready")
        self.assert_code("SESSION_ENDED", self.c.inspect_saved_report, self.cp)

    def test_creation_ack_failure_preserves_partial_evidence_no_active_claim(self):
        journal = self.c._module("journal")
        with patch.object(journal.os, "fsync", side_effect=OSError("fixture storage failure")):
            self.assert_code("JOURNAL_CREATE_FAILED", self.start)
        self.assertEqual(self.c.status()["state"], "failed")
        self.assertEqual(self.c.status()["journal_records"], 0)
        self.assertIsNone(self.c._journal)
        self.assertTrue(self.journal.exists())

    def test_writer_close_failure_retains_owned_handle_for_explicit_retry(self):
        self.start()
        writer = self.c._journal
        with patch.object(writer, "close", side_effect=OSError("fixture close failure")):
            row = self.c.finish()
            self.assertEqual(row["state"], "failed")
            self.assertEqual(row["failure_code"], "JOURNAL_FAILURE")
            self.assertTrue(row["writer_open"])
            self.assertIs(self.c._journal, writer)
        self.assertFalse(self.c.close()["writer_open"])
        self.assertEqual(self.c.status()["state"], "failed")

    def test_closed_original_is_inspection_only_with_new_owner(self):
        self.start()
        self.c.finish()
        before = self.journal.read_bytes()
        c2 = CORE.Coordinator()
        self.assertNotEqual(c2.status()["owner_id"], self.c.status()["owner_id"])
        self.assert_code("JOURNAL_CREATE_FAILED", c2.start, self.journal)
        self.assertEqual(self.journal.read_bytes(), before)
        self.assertFalse(hasattr(c2, "resume"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
