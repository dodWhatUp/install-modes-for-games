"""Authored saved-file/packet contracts. No Windows log query or actual crash."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location("evidence_test_" + name, SCRIPTS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api = load("GameToolCrashEvidence")
coordinator = load("GameToolCoordinator")
journal = load("GameToolJournal")
NS = "http://schemas.microsoft.com/win/2004/08/events/event"


def event(provider="Application Error", event_id=1000, utc="2026-10-11T12:30:00.1234567Z", app="SkyrimSE.exe", extra=""):
    return f'''<Event xmlns="{NS}"><System><Provider Name="{provider}"/><EventID>{event_id}</EventID>
    <TimeCreated SystemTime="{utc}"/><EventRecordID>7</EventRecordID><Execution ProcessID="999" ThreadID="2"/>
    <Computer>PRIVATE_COMPUTER</Computer><Security UserID="PRIVATE_SID"/></System><EventData>
    <Data Name="AppName">{app}</Data><Data Name="ModuleName">PRIVATE_MODULE.dll</Data>
    <Data Name="AppPath">PRIVATE_PATH</Data><Data Name="ExceptionCode">c0000005</Data>
    <Data Name="ProcessId">123</Data><Data Name="Message">PRIVATE_MESSAGE</Data>{extra}</EventData></Event>'''


class EvidenceContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="saved-evidence-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.xml = self.directory / "not-a-game-name.xml"
        self.xml.write_text(event(), encoding="utf-8")

    def assignments(self, path=None):
        return [{"path": path or self.xml}]

    def refused(self, code, function, *args, **kwargs):
        with self.assertRaises(api.EvidenceError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)
        self.assertNotIn(str(self.directory), str(caught.exception))

    def test_module_import_and_public_contract_have_no_live_executor(self):
        source = (SCRIPTS / "GameToolCrashEvidence.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, ast.Import)}
        self.assertFalse(names & {"subprocess", "socket", "ctypes", "keyboard", "pynput"})
        self.assertFalse(hasattr(api, "watch"))
        self.assertFalse(hasattr(api, "launch"))

    def test_xml_fields_preserve_source_clock_precision_and_reporter_pid(self):
        row = api.inspect_source(self.xml)["events"][0]
        self.assertEqual(row["reported_utc"], "2026-10-11T12:30:00.1234567Z")
        self.assertEqual(row["reporter_process_id"], 999)
        self.assertNotEqual(row["reporter_process_id"], 123)
        self.assertEqual(row["event_record_id"], 7)
        self.assertEqual(row["game_id"], "skyrim-special-edition")
        self.assertIsNone(row["clock_uncertainty_ms"])

    def test_portable_preview_excludes_private_source_strings_and_paths(self):
        raw = json.dumps(api.build_packet(self.assignments()))
        for secret in ("PRIVATE_", "c0000005", "not-a-game-name", str(self.directory), "SkyrimSE.exe"):
            self.assertNotIn(secret, raw)
        self.assertIn("application_error_reported", raw)

    def test_read_only_inspection_preserves_source_bytes_mtime_and_directory(self):
        before, mtime = self.xml.read_bytes(), self.xml.stat().st_mtime_ns
        api.inspect_source(self.xml)
        api.build_packet(self.assignments())
        self.assertEqual(self.xml.read_bytes(), before)
        self.assertEqual(self.xml.stat().st_mtime_ns, mtime)
        self.assertEqual(list(self.directory.iterdir()), [self.xml])

    def test_wer_report_alone_is_not_classified_as_crash(self):
        self.xml.write_text(event("Windows Error Reporting", 1001), encoding="utf-8")
        report = api.build_packet(self.assignments())
        self.assertEqual(report["timeline"][0]["kind"], "wer_report_present")
        self.assertFalse(report["timeline"][0]["failure_reported"])
        self.assertIsNone(report["first_reported_failure"])
        self.assertIsNone(report["crash_cause"])

    def test_event_id_alone_does_not_classify_unknown_provider(self):
        self.xml.write_text(event("PRIVATE_PROVIDER", 1000), encoding="utf-8")
        row = api.inspect_source(self.xml)["events"][0]
        self.assertEqual(row["kind"], "unclassified_windows_event")
        self.assertIsNone(row["game_id"])

    def test_wrong_provider_id_pair_is_not_application_error(self):
        self.xml.write_text(event("Application Error", 1001), encoding="utf-8")
        self.assertFalse(api.inspect_source(self.xml)["events"][0]["failure_reported"])

    def test_app_path_or_filename_is_not_game_identity(self):
        self.xml.write_text(event(app="PRIVATE_PATH/SkyrimSE.exe"), encoding="utf-8")
        self.assertIsNone(api.inspect_source(self.xml)["events"][0]["game_id"])

    def test_duplicate_app_name_makes_game_association_unknown(self):
        self.xml.write_text(event(extra='<Data Name="AppName">Cyberpunk2077.exe</Data>'), encoding="utf-8")
        self.assertIsNone(api.inspect_source(self.xml)["events"][0]["game_id"])

    def test_cyberpunk_exact_name_is_declared_not_runtime_verified(self):
        self.xml.write_text(event(app="Cyberpunk2077.exe"), encoding="utf-8")
        row = api.inspect_source(self.xml)["events"][0]
        self.assertEqual(row["game_id"], "cyberpunk-2077")
        self.assertEqual(row["game_association"], "source_declared_not_runtime_verified")

    def test_missing_invalid_and_non_utc_times_remain_unknown(self):
        for stamp in ("", "2026-02-30T00:00:00Z", "2026-10-11T00:00:00+03:00", "PRIVATE_TIME"):
            self.xml.write_text(event(utc=stamp), encoding="utf-8")
            report = api.build_packet(self.assignments())
            self.assertIsNone(report["timeline"][0]["reported_utc"])
            self.assertIsNone(report["first_reported_failure"])
            self.assertEqual(report["untimed_failure_count"], 1)

    def test_optional_time_record_and_execution_are_null_not_zero(self):
        text = event().replace('<TimeCreated SystemTime="2026-10-11T12:30:00.1234567Z"/>', "")
        text = text.replace('<EventRecordID>7</EventRecordID>', "").replace('<Execution ProcessID="999" ThreadID="2"/>', "")
        self.xml.write_text(text, encoding="utf-8")
        row = api.inspect_source(self.xml)["events"][0]
        for key in ("reported_utc", "event_record_id", "reporter_process_id"):
            self.assertIsNone(row[key])

    def test_invalid_optional_numerics_do_not_become_false_zero(self):
        self.xml.write_text(event().replace('ProcessID="999"', 'ProcessID="-3"').replace('<EventRecordID>7', '<EventRecordID>PRIVATE'), encoding="utf-8")
        row = api.inspect_source(self.xml)["events"][0]
        self.assertIsNone(row["reporter_process_id"])
        self.assertIsNone(row["event_record_id"])

    def test_utf16_bom_export_and_utf8_xml_declaration(self):
        for encoding in ("utf-16", "utf-8-sig"):
            self.xml.write_bytes(('<?xml version="1.0"?>' + event()).encode(encoding))
            self.assertEqual(api.inspect_source(self.xml)["coverage"]["event_count"], 1)

    def test_multiple_events_sort_by_reported_utc_and_keep_source_order(self):
        self.xml.write_text('<Events>' + event(utc="2026-10-11T12:31:00Z") + event(utc="2026-10-11T12:30:00Z") + '</Events>', encoding="utf-8")
        report = api.build_packet(self.assignments())
        self.assertEqual([row["source_order"] for row in report["timeline"]], [2, 1])
        self.assertEqual(report["first_reported_failure"]["candidates"][0]["source_order"], 2)

    def test_equal_failure_timestamps_preserve_all_candidates(self):
        self.xml.write_text('<Events>' + event() * 2 + '</Events>', encoding="utf-8")
        first = api.build_packet(self.assignments())["first_reported_failure"]
        self.assertEqual(len(first["candidates"]), 2)
        self.assertIn("not_causal", first["ordering_certainty"])

    def test_dtd_entity_refused_before_parse_utf8_and_utf16(self):
        for encoding in ("utf-8", "utf-16"):
            self.xml.write_bytes(('<!DOCTYPE Event [<!ENTITY x "payload">]>' + event()).encode(encoding))
            self.refused("XML_DECLARATION_REFUSED", api.inspect_source, self.xml)

    def test_malformed_xml_is_fixed_path_free_failure(self):
        self.xml.write_text('<Event PRIVATE_MESSAGE', encoding="utf-8")
        self.refused("MALFORMED_XML", api.inspect_source, self.xml)

    def test_wrong_namespace_empty_events_and_non_event_child_refused(self):
        for text, code in ((event().replace(NS, "unknown"), "UNSUPPORTED_FORMAT"), ('<Events/>', "XML_LIMIT"),
                           ('<Events><Other/></Events>', "UNSUPPORTED_FORMAT")):
            self.xml.write_text(text, encoding="utf-8")
            self.refused(code, api.inspect_source, self.xml)

    def test_duplicate_or_missing_required_system_fields_refused(self):
        for text in (event().replace('<EventID>1000</EventID>', '<EventID>1000</EventID><EventID>1</EventID>'),
                     event().replace('<Provider Name="Application Error"/>', '')):
            self.xml.write_text(text, encoding="utf-8")
            self.refused("AMBIGUOUS_EVENT", api.inspect_source, self.xml)

    def test_bad_or_oversized_event_id_refused(self):
        for value in ("-1", "65536", "secret"):
            self.xml.write_text(event(event_id=value), encoding="utf-8")
            self.refused("MALFORMED_EVENT", api.inspect_source, self.xml)

    def test_xml_event_depth_and_byte_limits(self):
        values = ('<Events>' + event() * (api.MAX_EVENTS + 1) + '</Events>',
                  '<Events>' + '<x>' * 33 + '</x>' * 33 + '</Events>',
                  '<Events>' + ' ' * api.MAX_XML_BYTES + '</Events>')
        for text in values:
            self.xml.write_text(text, encoding="utf-8")
            self.refused("XML_LIMIT", api.inspect_source, self.xml)

    def test_missing_directory_empty_or_large_source_refused(self):
        missing, empty, large = (self.directory / name for name in ("missing.xml", "empty.txt", "large.txt"))
        empty.write_bytes(b"")
        with large.open("wb") as handle:
            handle.truncate(api.MAX_SOURCE_BYTES + 1)
        for path in (missing, empty, large, self.directory):
            self.refused("SOURCE_UNAVAILABLE", api.inspect_source, path)

    def test_unsupported_extensions_and_binary_text_are_refused(self):
        wrong = self.directory / "source.evtx"
        wrong.write_bytes(self.xml.read_bytes())
        self.refused("UNSUPPORTED_FORMAT", api.inspect_source, wrong)
        text = self.directory / "binary.log"
        text.write_bytes(b"a\x00b")
        self.refused("UNSUPPORTED_FORMAT", api.inspect_source, text)

    def test_opaque_text_does_not_invent_warning_or_failure_or_time(self):
        text = self.directory / "Cyberpunk2077.log"
        text.write_text("2026-10-11 OOM crash VRAM PRIVATE_MESSAGE", encoding="utf-8")
        report = api.build_packet(self.assignments(text))
        self.assertEqual(report["timeline"], [])
        self.assertFalse(report["memory_exhaustion_verified"])
        self.assertIsNone(report["first_reported_failure"])

    def test_explicit_adapter_can_read_xml_with_unusual_suffix(self):
        text = self.directory / "source.saved"
        text.write_bytes(self.xml.read_bytes())
        self.assertEqual(api.inspect_source(text, adapter="windows_event_xml")["coverage"]["event_count"], 1)

    def test_invalid_adapter_and_hash_are_refused(self):
        for adapter in ([], "custom", 1):
            self.refused("INVALID_ADAPTER", api.inspect_source, self.xml, adapter=adapter)
        self.refused("INVALID_HASH", api.inspect_source, self.xml, expected_sha256="wrong")
        self.refused("SOURCE_CHANGED", api.inspect_source, self.xml, expected_sha256="0" * 64)

    def test_correct_uppercase_hash_accepted(self):
        digest = hashlib.sha256(self.xml.read_bytes()).hexdigest()
        self.assertEqual(api.inspect_source(self.xml, expected_sha256=digest.upper())["source_sha256"], digest)

    def test_invalid_source_count_assignment_duplicate_and_total_bounds(self):
        for value in ([], [self.xml], [{"path": self.xml, "command": "launch"}], self.assignments() * 9):
            with self.assertRaises(api.EvidenceError):
                api.build_packet(value)
        self.refused("DUPLICATE_SOURCE", api.build_packet, self.assignments() * 2)
        with mock.patch.object(api, "MAX_TOTAL_BYTES", 1):
            self.refused("TOTAL_LIMIT", api.build_packet, self.assignments())
        with mock.patch.object(api, "MAX_TIMELINE", 0):
            self.refused("TIMELINE_LIMIT", api.build_packet, self.assignments())

    def test_journal_verified_prefix_retained_without_raw_data_or_replay(self):
        path = self.directory / "saved.jsonl"
        with journal.Journal.create(path, {"private": "PRIVATE_TYPED_PAYLOAD"}) as writer:
            writer.append("action_failed", {"private": "PRIVATE_TYPED_PAYLOAD"})
        with path.open("ab") as handle:
            handle.write(b'{"incomplete":')
        report = api.build_packet(self.assignments(path))
        coverage = report["sources"][0]["coverage"]
        self.assertEqual(coverage["event_count"], 2)
        self.assertFalse(coverage["valid"])
        self.assertGreater(coverage["unverified_tail_bytes"], 0)
        self.assertFalse(report["replay_allowed"])
        self.assertNotIn("PRIVATE_", json.dumps(report))
        self.assertIsNone(report["crash_cause"])

    def test_journal_open_end_is_not_failure(self):
        path = self.directory / "open.jsonl"
        with journal.Journal.create(path, {}) as writer:
            writer.append("checkpoint", {})
        report = api.build_packet(self.assignments(path))
        self.assertFalse(report["sources"][0]["coverage"]["clean_end"])
        self.assertIsNone(report["first_reported_failure"])

    def test_unknown_journal_kind_is_not_private_label_in_portable_data(self):
        path = self.directory / "other.jsonl"
        with journal.Journal.create(path, {}) as writer:
            writer.append("PRIVATE_EVENT", {})
        report = api.build_packet(self.assignments(path))
        self.assertEqual(report["timeline"][1]["kind"], "other_journal_event")
        self.assertNotIn("PRIVATE_EVENT", json.dumps(report))

    def test_journal_no_verified_prefix_refused(self):
        path = self.directory / "invalid.jsonl"
        path.write_bytes(b'{"x":1}\n')
        self.refused("NO_VERIFIED_PREFIX", api.inspect_source, path)

    def test_raw_windows_clock_stays_unknown_without_conversion(self):
        self.xml.write_text(event().replace('SystemTime="2026-10-11T12:30:00.1234567Z"', 'RawTime="1234567"'), encoding="utf-8")
        self.assertIsNone(api.inspect_source(self.xml)["events"][0]["reported_utc"])

    def test_utf16_encoding_declaration_is_supported(self):
        self.xml.write_bytes(('<?xml version="1.0" encoding="utf-16"?>' + event()).encode("utf-16"))
        self.assertEqual(api.inspect_source(self.xml)["coverage"]["event_count"], 1)

    def test_backend_source_drift_refuses_result(self):
        backend = api._journal()
        backend._authored_hash = "0" * 64  # Authored test seam; real source is not modified.
        with mock.patch.object(api, "_journal", return_value=backend):
            self.refused("MODULE_CHANGED", api.inspect_source, self.xml)

    def test_journal_utc_backsteps_visible_without_inventing_clock_alignment(self):
        path = self.directory / "backstep.jsonl"
        with journal.Journal.create(path, {}) as writer:
            writer.append("checkpoint", {})
        records = [json.loads(line) for line in path.read_bytes().splitlines()]
        records[0]["utc"] = "2026-10-11T12:31:00.000000Z"
        records[0]["sha256"] = journal._digest(records[0])
        records[1]["utc"] = "2026-10-11T12:30:00.000000Z"
        records[1]["prev_sha256"] = records[0]["sha256"]
        records[1]["sha256"] = journal._digest(records[1])
        path.write_bytes(b"".join(journal._canonical(row) + b"\n" for row in records))
        report = api.build_packet(self.assignments(path))
        self.assertEqual(report["sources"][0]["coverage"]["utc_backstep_count"], 1)
        self.assertEqual([row["source_order"] for row in report["timeline"]], [2, 1])

    def test_source_drift_during_interpretation_refuses_preview(self):
        original = api._preview
        def change(record, *args):
            result = original(record, *args)
            self.xml.write_bytes(self.xml.read_bytes() + b" ")
            return result
        with mock.patch.object(api, "_preview", side_effect=change):
            self.refused("SOURCE_CHANGED", api.inspect_source, self.xml)

    def test_reparse_source_is_refused_by_shared_reader(self):
        original = Path.lstat
        def fake(path):
            info = original(path)
            if path == self.xml:
                from types import SimpleNamespace
                return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
            return info
        with mock.patch.object(Path, "lstat", fake):
            self.refused("SOURCE_UNAVAILABLE", api.inspect_source, self.xml)

    def test_export_exact_originals_hashes_html_and_private_receipt(self):
        target = self.directory / "packet"
        before, mtime = self.xml.read_bytes(), self.xml.stat().st_mtime_ns
        result = api.export_packet(self.assignments(), target)
        self.assertEqual((target / "source-001.xml").read_bytes(), before)
        self.assertEqual(self.xml.read_bytes(), before)
        self.assertEqual(self.xml.stat().st_mtime_ns, mtime)
        manifest = json.loads((target / "manifest.json").read_bytes())
        for item in manifest["files"]:
            raw = (target / item["name"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), item["sha256"])
            self.assertEqual(len(raw), item["bytes"])
        receipt = json.loads((target / "private-receipt.json").read_bytes())
        self.assertEqual(receipt["sources"][0]["private_source_path"], str(self.xml))
        self.assertNotIn(str(self.directory), json.dumps(result))
        self.assertNotIn("PRIVATE_", (target / "evidence.html").read_text(encoding="utf-8"))
        self.assertFalse(result["runtime_verification"])

    def test_export_existing_directory_file_and_repository_refused(self):
        file = self.directory / "existing"
        file.write_bytes(b"KEEP")
        for target in (file, self.directory, SCRIPTS.parent / "never-create-evidence"):
            self.refused("DESTINATION_REFUSED", api.export_packet, self.assignments(), target)
        self.assertEqual(file.read_bytes(), b"KEEP")

    def test_disk_failure_before_publication_does_not_create_bundle(self):
        target = self.directory / "packet"
        with mock.patch.object(api.os, "fsync", side_effect=OSError("private disk error")):
            self.refused("EXPORT_FAILED", api.export_packet, self.assignments(), target)
        self.assertFalse(target.exists())

    def test_publication_failure_cleans_only_owned_packet(self):
        target = self.directory / "packet"
        original = api.os.link
        def fail(source, destination):
            if Path(destination).name == "source-001.xml":
                raise OSError("full disk")
            return original(source, destination)
        with mock.patch.object(api.os, "link", side_effect=fail):
            self.refused("EXPORT_FAILED", api.export_packet, self.assignments(), target)
        self.assertFalse(target.exists())

    def test_concurrent_replacement_not_removed_on_export_failure(self):
        target = self.directory / "packet"
        original = api.os.link
        def replace(source, destination):
            original(source, destination)
            if Path(destination).name == "evidence.json":
                Path(destination).unlink()
                Path(destination).write_bytes(b"FOREIGN_BYTES")
        with mock.patch.object(api.os, "link", side_effect=replace):
            self.refused("READBACK_FAILED", api.export_packet, self.assignments(), target)
        self.assertEqual((target / "evidence.json").read_bytes(), b"FOREIGN_BYTES")
        self.assertFalse((target / "manifest.json").exists())

    def test_source_drift_after_publication_removes_owned_output_not_original(self):
        target = self.directory / "packet"
        original = api._assert_current
        calls = 0
        def changed(records, backend):
            nonlocal calls
            calls += 1
            if calls == 3:
                self.xml.write_bytes(self.xml.read_bytes() + b" ")
            return original(records, backend)
        with mock.patch.object(api, "_assert_current", side_effect=changed):
            self.refused("SOURCE_CHANGED", api.export_packet, self.assignments(), target)
        self.assertFalse(target.exists())
        self.assertTrue(self.xml.read_bytes().endswith(b" "))

    def test_html_escaping_is_script_free(self):
        raw = api._html({"untrusted": '<script>alert("x")</script>'}).decode("utf-8")
        self.assertNotIn('<script>', raw)
        self.assertIn('&lt;script&gt;', raw)

    def test_coordinator_capability_records_compact_result_not_payload(self):
        path = self.directory / "task.jsonl"
        c = coordinator.Coordinator()
        self.addCleanup(c.close)
        c.start(path)
        result = c.inspect_crash_evidence(self.xml)
        self.assertEqual(result["adapter"], "windows_event_xml")
        c.finish()
        inspected = journal.inspect_journal(path)
        self.assertTrue(inspected["clean_end"])
        row = inspected["verified_records"][-2]["data"]
        self.assertEqual(row["status"], "EVIDENCE_ONLY")
        self.assertEqual(row["event_count"], 1)
        self.assertNotIn("PRIVATE_", path.read_text(encoding="utf-8"))
        self.assertNotIn("events", row)

    def test_coordinator_before_start_does_not_read(self):
        c = coordinator.Coordinator()
        with mock.patch.object(coordinator, "_capture", side_effect=AssertionError("source read")):
            with self.assertRaises(coordinator.CoordinatorError):
                c.inspect_crash_evidence(self.xml)

    def test_coordinator_changed_expected_hash_has_no_success(self):
        c = coordinator.Coordinator()
        self.addCleanup(c.close)
        c.start(self.directory / "task.jsonl")
        with self.assertRaises(coordinator.CoordinatorError):
            c.inspect_crash_evidence(self.xml, expected_sha256="0" * 64)
        self.assertEqual(c.status()["latest_action"]["state"], "failed")

    def test_coordinator_deadline_during_read_discards_result(self):
        now = [100.0]
        c = coordinator.Coordinator(clock=lambda: now[0])
        self.addCleanup(c.close)
        c.start(self.directory / "task.jsonl")
        backend = c._module("crash_evidence")
        original = backend.inspect_source
        def expire(*args, **kwargs):
            result = original(*args, **kwargs)
            now[0] += 901
            return result
        with mock.patch.object(backend, "inspect_source", side_effect=expire):
            with self.assertRaises(coordinator.CoordinatorError):
                c.inspect_crash_evidence(self.xml)
        self.assertEqual(c.status()["state"], "expired")
        self.assertFalse(c.status()["writer_open"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
