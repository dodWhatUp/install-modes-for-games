"""Offline journal fixtures; child interruption affects only an authored helper.

No game, benchmark, recorder, input tool, resident service or settings changes.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import queue
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts/GameToolJournal.py"
SPEC = importlib.util.spec_from_file_location("journal_contracts", MODULE)
JOURNAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOURNAL)


class JournalContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="GameJournalContract-")
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.path = self.folder / "events.jsonl"

    def create(self, metadata=None, path=None):
        writer = JOURNAL.Journal.create(self.path if path is None else path,
                                        {"scope": "offline_fixture"} if metadata is None else metadata)
        self.addCleanup(writer.close)
        return writer

    def source(self, terminal=False):
        writer = self.create()
        writer.append("phase_changed", {"phase": "inspect"})
        if terminal:
            writer.append("session_closed", {"outcome": "finished"})
        writer.close()
        return self.path.read_bytes()

    def inspect(self):
        return JOURNAL.inspect_journal(self.path)

    def edit_record(self, index, mutation, resign=False):
        lines = self.path.read_bytes().splitlines(keepends=True)
        record = json.loads(lines[index])
        mutation(record)
        if resign:
            record["sha256"] = JOURNAL._digest(record)
        lines[index] = JOURNAL._canonical(record) + b"\n"
        self.path.write_bytes(b"".join(lines))

    def test_creation_durable_record_and_fixed_version(self):
        writer = self.create()
        result = self.inspect()
        self.assertEqual(JOURNAL.VERSION, "0.1.0")
        self.assertTrue(result["valid"])
        self.assertFalse(result["clean_end"])
        self.assertEqual(result["verified_count"], 1)
        first = result["verified_records"][0]
        self.assertEqual(first["kind"], "journal_created")
        self.assertEqual(first["seq"], 1)
        self.assertEqual(first["prev_sha256"], "0" * 64)
        self.assertFalse(result["replay_allowed"])
        self.assertIn("not identify a game crash", result["safety_caveat"])
        writer.close()

    def test_hash_sequence_clock_and_copy_isolation(self):
        metadata = {"scope": "offline", "extra": {"number": 1}}
        writer = self.create(metadata)
        metadata["extra"]["number"] = 9
        data = {"rows": [{"count": 3}]}
        second = writer.append("inspection_observed", data)
        data["rows"][0]["count"] = 99
        second["data"]["rows"][0]["count"] = 55
        result = self.inspect()
        records = result["verified_records"]
        self.assertEqual(records[0]["data"]["extra"]["number"], 1)
        self.assertEqual(records[1]["data"]["rows"][0]["count"], 3)
        self.assertEqual(records[1]["prev_sha256"], records[0]["sha256"])
        self.assertEqual(records[1]["clock_id"], records[0]["clock_id"])
        self.assertGreaterEqual(records[1]["monotonic_ns"], records[0]["monotonic_ns"])

    def test_context_manager_close_is_not_terminal_claim(self):
        with JOURNAL.Journal.create(self.path, {}) as writer:
            writer.append("checkpoint")
        self.assertFalse(self.inspect()["clean_end"])
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("after_close")

    def test_closed_terminal_blocks_future_append(self):
        writer = self.create()
        writer.append("session_closed")
        self.assertTrue(self.inspect()["clean_end"])
        before = self.path.read_bytes()
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("checkpoint")
        self.assertEqual(self.path.read_bytes(), before)

    def test_cancelled_is_clean_terminal(self):
        writer = self.create()
        writer.append("session_cancelled", {"reason": "user"})
        self.assertTrue(self.inspect()["clean_end"])

    def test_duplicate_creation_append_refused_without_poisoning(self):
        writer = self.create()
        before = self.path.read_bytes()
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("journal_created", {})
        self.assertEqual(self.path.read_bytes(), before)
        writer.append("checkpoint")
        self.assertTrue(self.inspect()["valid"])

    def test_create_never_overwrites_existing_file(self):
        self.path.write_bytes(b"private existing evidence")
        before = self.path.read_bytes(), self.path.stat().st_mtime_ns
        with self.assertRaises(JOURNAL.JournalError):
            self.create()
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_missing_parent_not_created(self):
        missing = self.folder / "missing" / "events.jsonl"
        with self.assertRaises(JOURNAL.JournalError):
            self.create(path=missing)
        self.assertFalse(missing.parent.exists())

    def test_invalid_path_types_and_control_characters_refused(self):
        for path in (None, 3, b"bytes-not-locator", "bad\x00path", ""):
            with self.subTest(path=repr(path)):
                with self.assertRaises(JOURNAL.JournalError):
                    JOURNAL.Journal.create(path, {})
                with self.assertRaises(JOURNAL.JournalError):
                    JOURNAL.inspect_journal(path)

    def test_invalid_metadata_no_file_created(self):
        for data in (None, [], {"value": float("nan")}, {"value": float("inf")},
                     {"value": 10 ** 101}, {"": 1}, {"bad\x00": 1}, {"value": object()}):
            with self.subTest(data=type(data).__name__):
                with self.assertRaises(JOURNAL.JournalError):
                    JOURNAL.Journal.create(self.path, data)
                self.assertFalse(self.path.exists())

    def test_depth_bounds_no_file_created(self):
        value = {}
        for _ in range(10):
            value = {"nested": value}
        with self.assertRaises(JOURNAL.JournalError):
            self.create(value)
        self.assertFalse(self.path.exists())

    def test_text_field_and_list_bounds(self):
        for data in ({"value": "x" * 4097}, {"value": [0] * 513},
                     {str(i): 0 for i in range(257)}, {"bad" * 44: 1}):
            with self.subTest(data_type=type(data).__name__):
                with self.assertRaises(JOURNAL.JournalError):
                    JOURNAL.Journal.create(self.path, data)
                self.assertFalse(self.path.exists())

    def test_total_work_budget(self):
        metadata = {str(i): [0] * 512 for i in range(10)}
        with self.assertRaises(JOURNAL.JournalError):
            self.create(metadata)
        self.assertFalse(self.path.exists())

    def test_invalid_append_keeps_writer_usable(self):
        writer = self.create()
        for kind, data in (("bad kind", {}), ("ok", []), ("ok", {"value": float("nan")}),
                           ("", None), ("x" * 65, {})):
            with self.subTest(kind=kind):
                with self.assertRaises(JOURNAL.JournalError):
                    writer.append(kind, data)
        writer.append("still_valid", {"value": True})
        self.assertEqual(self.inspect()["verified_count"], 2)

    def test_line_size_append_limit(self):
        writer = self.create()
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("oversized", {str(i): "x" * 4096 for i in range(17)})
        self.assertEqual(self.inspect()["verified_count"], 1)

    def test_record_count_limit(self):
        writer = self.create()
        with patch.object(JOURNAL, "MAX_RECORDS", 2):
            writer.append("checkpoint")
            with self.assertRaises(JOURNAL.JournalError):
                writer.append("checkpoint")
        self.assertEqual(self.inspect()["verified_count"], 2)

    def test_total_byte_limit(self):
        writer = self.create()
        with patch.object(JOURNAL, "MAX_JOURNAL_BYTES", writer._bytes):
            with self.assertRaises(JOURNAL.JournalError):
                writer.append("checkpoint")
        self.assertEqual(self.inspect()["verified_count"], 1)

    def test_read_only_inspection_preserves_bytes_and_time(self):
        self.source()
        before = self.path.read_bytes(), self.path.stat().st_mtime_ns
        self.inspect()
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_old_writer_evidence_remains_readable_after_code_release_change(self):
        self.source(terminal=True)
        before = self.path.read_bytes(), self.path.stat().st_mtime_ns
        with patch.object(JOURNAL, "VERSION", "0.2.0"):
            result = self.inspect()
        self.assertTrue(result["valid"])
        self.assertTrue(result["clean_end"])
        self.assertEqual({r["journal_version"] for r in result["verified_records"]}, {"0.1.0"})
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_compatible_schema_accepts_bounded_writer_release_provenance(self):
        for index, version in enumerate(("0.0.9", "0.1.7", "1.2.3", "2.0.0-preview.1", "3.0.0+build.2")):
            with self.subTest(writer=version):
                path = self.folder / ("release-" + str(index) + ".jsonl")
                with patch.object(JOURNAL, "VERSION", version):
                    with JOURNAL.Journal.create(path, {"scope": "offline_fixture"}) as writer:
                        writer.append("session_closed", {"outcome": "finished"})
                before = path.read_bytes(), path.stat().st_mtime_ns
                result = JOURNAL.inspect_journal(path)
                self.assertTrue(result["valid"])
                self.assertTrue(result["clean_end"])
                self.assertEqual({r["journal_version"] for r in result["verified_records"]}, {version})
                self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime_ns))

    def test_writer_version_remains_hash_protected(self):
        self.source()
        self.edit_record(1, lambda record: record.update(journal_version="0.1.7"))
        before = self.path.read_bytes(), self.path.stat().st_mtime_ns
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertEqual(result["verified_count"], 1)
        self.assertIn("hash chain", result["error"])
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_invalid_writer_version_provenance_is_refused_even_resigned(self):
        raw = self.source()
        invalid = (None, True, 1, [], {}, "", "0.1", "v0.1.0", "..", "0.1.0\n",
                   "0.1.0;run", "0.1.0..preview", "0.1.0-", "0.1.0+", "1" * 65 + ".0.0")
        for version in invalid:
            with self.subTest(writer=repr(version)):
                self.path.write_bytes(raw)
                self.edit_record(1, lambda record: record.update(journal_version=version), resign=True)
                before = self.path.read_bytes(), self.path.stat().st_mtime_ns
                result = self.inspect()
                self.assertFalse(result["valid"])
                self.assertEqual(result["verified_count"], 1)
                self.assertIn("writer-version provenance", result["error"])
                self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_unknown_schema_still_refused_across_code_release_versions(self):
        raw = self.source()
        for schema in (0, 2, True, "1", None):
            with self.subTest(schema=repr(schema)):
                self.path.write_bytes(raw)
                self.edit_record(1, lambda record: record.update(schema_version=schema), resign=True)
                before = self.path.read_bytes(), self.path.stat().st_mtime_ns
                with patch.object(JOURNAL, "VERSION", "0.2.0"):
                    result = self.inspect()
                self.assertFalse(result["valid"])
                self.assertEqual(result["verified_count"], 1)
                self.assertIn("schema", result["error"])
                self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_compatible_old_prefix_recovery_does_not_migrate_or_replay(self):
        raw = self.source()
        self.path.write_bytes(raw + b'{"schema_version":2,"incomplete":')
        before = self.path.read_bytes(), self.path.stat().st_mtime_ns
        destination = self.folder / "old-release-prefix.jsonl"
        with patch.object(JOURNAL, "VERSION", "0.2.0"):
            result = self.inspect()
            receipt = JOURNAL.recover_journal(self.path, destination, result["source_sha256"])
            copied = JOURNAL.inspect_journal(destination)
        self.assertFalse(result["valid"])
        self.assertTrue(copied["valid"])
        self.assertEqual(destination.read_bytes(), raw)
        self.assertEqual({r["journal_version"] for r in copied["verified_records"]}, {"0.1.0"})
        self.assertFalse(receipt["replay_allowed"])
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_empty_file_has_no_recoverable_evidence(self):
        self.path.write_bytes(b"")
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertEqual(result["verified_count"], 0)
        with self.assertRaises(JOURNAL.JournalError):
            JOURNAL.recover_journal(self.path, self.folder / "copy.jsonl")

    def test_truncated_tail_recovers_complete_prefix(self):
        raw = self.source()
        self.path.write_bytes(raw + b'{"seq":3,"data":')
        before = self.path.read_bytes(), self.path.stat().st_mtime_ns
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertTrue(result["recovery_required"])
        self.assertEqual(result["verified_bytes"], len(raw))
        destination = self.folder / "recovered.jsonl"
        receipt = JOURNAL.recover_journal(self.path, destination, result["source_sha256"])
        self.assertEqual(destination.read_bytes(), raw)
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))
        self.assertEqual(receipt["discarded_tail_bytes"], len(before[0]) - len(raw))
        self.assertFalse(receipt["replay_allowed"])
        self.assertTrue(JOURNAL.inspect_journal(destination)["valid"])

    def test_truncated_valid_json_without_newline_not_acknowledged_prefix(self):
        raw = self.source()
        self.path.write_bytes(raw[:-1])
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertEqual(result["verified_count"], 1)

    def test_middle_corruption_does_not_skip_to_later_records(self):
        self.source(terminal=True)
        self.edit_record(1, lambda record: record["data"].update(phase="changed"))
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertFalse(result["clean_end"])
        self.assertEqual(result["verified_count"], 1)
        self.assertIn("hash chain", result["error"])

    def test_invalid_utf8_stops_at_prefix(self):
        raw = self.source()
        self.path.write_bytes(raw + b"\xff\n")
        self.assertEqual(self.inspect()["verified_count"], 2)
        self.assertFalse(self.inspect()["valid"])

    def test_duplicate_json_keys_refused(self):
        raw = self.source()
        self.path.write_bytes(raw + b'{"seq":3,"seq":3}\n')
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertIn("Duplicate", result["error"])

    def test_nonfinite_json_refused(self):
        raw = self.source()
        self.path.write_bytes(raw + b'{"value":NaN}\n')
        self.assertFalse(self.inspect()["valid"])
        self.assertIn("Nonfinite", self.inspect()["error"])

    def test_sequence_gap_refused_even_resigned(self):
        self.source()
        self.edit_record(1, lambda record: record.update(seq=5), resign=True)
        self.assertFalse(self.inspect()["valid"])
        self.assertIn("sequence", self.inspect()["error"])

    def test_clock_change_refused_even_resigned(self):
        self.source()
        self.edit_record(1, lambda record: record.update(clock_id="1" * 32), resign=True)
        self.assertFalse(self.inspect()["valid"])
        self.assertIn("another process", self.inspect()["error"])

    def test_clock_backwards_refused_even_resigned(self):
        self.source()
        self.edit_record(1, lambda record: record.update(monotonic_ns=0), resign=True)
        self.assertFalse(self.inspect()["valid"])

    def test_bad_utc_and_extra_field_refused_even_resigned(self):
        self.source()
        original = self.path.read_bytes()
        for mutation in (lambda record: record.update(utc="2026-99-99T00:00:00.000000Z"),
                         lambda record: record.update(unrecognized=True)):
            self.path.write_bytes(original)
            self.edit_record(1, mutation, resign=True)
            self.assertFalse(self.inspect()["valid"])

    def test_records_after_terminal_refused(self):
        raw = self.source(terminal=True)
        self.path.write_bytes(raw + raw.splitlines(keepends=True)[-1])
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertEqual(result["verified_count"], 3)
        self.assertIn("terminal", result["error"])

    def test_read_byte_limit_refused(self):
        self.path.write_bytes(b"x" * 100)
        with patch.object(JOURNAL, "MAX_JOURNAL_BYTES", 99):
            with self.assertRaises(JOURNAL.JournalError):
                self.inspect()

    def test_special_source_refused_before_open_without_fifo_wait(self):
        self.source()
        original = JOURNAL.Path.stat

        def special(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path == self.path:
                class SpecialInfo:
                    st_mode = stat.S_IFIFO | 0o600
                    st_size = 0
                return SpecialInfo()
            return info

        with patch.object(JOURNAL.Path, "stat", special), \
                patch.object(JOURNAL.Path, "open", side_effect=AssertionError("Special source must not be opened")) as opening:
            with self.assertRaises(JOURNAL.JournalError):
                self.inspect()
            opening.assert_not_called()

    def test_preopen_to_handle_identity_replacement_refused(self):
        self.source()
        original = JOURNAL.Path.stat

        def replaced(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path == self.path:
                class ReplacedInfo:
                    st_mode = info.st_mode
                    st_size = info.st_size
                    st_dev = info.st_dev
                    st_ino = info.st_ino + 1
                    st_mtime_ns = info.st_mtime_ns
                return ReplacedInfo()
            return info

        with patch.object(JOURNAL.Path, "stat", replaced):
            with self.assertRaises(JOURNAL.JournalError):
                self.inspect()

    def test_inspect_line_limit_stops_at_prefix(self):
        raw = self.source()
        self.path.write_bytes(raw + b"x" * (JOURNAL.MAX_LINE_BYTES + 1) + b"\n")
        result = self.inspect()
        self.assertEqual(result["verified_count"], 2)
        self.assertIn("line exceeds", result["error"])

    def test_inspect_record_limit_stops_at_prefix(self):
        self.source()
        with patch.object(JOURNAL, "MAX_RECORDS", 1):
            result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertEqual(result["verified_count"], 1)

    def test_fsync_failure_poisoned_no_further_acknowledgment(self):
        writer = self.create()
        with patch.object(JOURNAL.os, "fsync", side_effect=OSError("fixture disk failure")):
            with self.assertRaises(JOURNAL.JournalError):
                writer.append("unknown_durability")
        self.assertTrue(writer._poisoned)
        before = self.path.read_bytes()
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("must_not_continue")
        self.assertEqual(self.path.read_bytes(), before)
        # Bytes may have reached storage despite missing acknowledgement. A
        # verified stream is not proof that the failed fsync was durable.
        self.assertTrue(self.inspect()["valid"])

    def test_creation_fsync_failure_preserves_unacknowledged_evidence(self):
        with patch.object(JOURNAL.os, "fsync", side_effect=OSError("fixture")):
            with self.assertRaises(JOURNAL.JournalError):
                self.create()
        self.assertTrue(self.path.exists())
        self.assertFalse(self.inspect()["clean_end"])

    def test_short_write_poisoned_and_recoverable_prefix(self):
        writer = self.create()
        original = writer._handle

        class ShortWriter:
            def __getattr__(self, name):
                return getattr(original, name)

            def write(self, data):
                return original.write(data[:17])

        writer._handle = ShortWriter()
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("short_write")
        self.assertTrue(writer._poisoned)
        result = self.inspect()
        self.assertFalse(result["valid"])
        self.assertEqual(result["verified_count"], 1)

    def test_external_size_drift_poisoned(self):
        writer = self.create()
        with self.path.open("ab") as external:
            external.write(b"external\n")
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("must_not_append")
        self.assertTrue(writer._poisoned)

    def test_external_same_size_mtime_drift_poisoned(self):
        writer = self.create()
        before = self.path.stat()
        with self.path.open("r+b", buffering=0) as external:
            external.write(b"!")
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000_000))
        with self.assertRaises(JOURNAL.JournalError):
            writer.append("must_not_append")
        self.assertTrue(writer._poisoned)

    def test_read_identity_drift_refused(self):
        self.source()
        original = JOURNAL._identity
        calls = [0]

        def drift(info):
            calls[0] += 1
            identity = original(info)
            return identity if calls[0] != 4 else (*identity[:-1], identity[-1] + 1)

        with patch.object(JOURNAL, "_identity", side_effect=drift):
            with self.assertRaises(JOURNAL.JournalError):
                self.inspect()

    def test_os_writer_lock_conflict_and_release(self):
        writer = self.create()
        with self.path.open("r+b", buffering=0) as other:
            with self.assertRaises(JOURNAL.JournalBusy):
                JOURNAL._lock(other)
            writer.close()
            JOURNAL._lock(other)
            JOURNAL._unlock(other)

    def test_recovery_expected_hash_gate_and_no_overwrite(self):
        self.source()
        destination = self.folder / "copy.jsonl"
        with self.assertRaises(JOURNAL.JournalError):
            JOURNAL.recover_journal(self.path, destination, "0" * 64)
        self.assertFalse(destination.exists())
        destination.write_bytes(b"retain existing")
        before = destination.read_bytes(), destination.stat().st_mtime_ns
        with self.assertRaises(JOURNAL.JournalError):
            JOURNAL.recover_journal(self.path, destination)
        self.assertEqual(before, (destination.read_bytes(), destination.stat().st_mtime_ns))

    def test_recovery_same_file_refused_and_source_retained(self):
        self.source()
        before = self.path.read_bytes(), self.path.stat().st_mtime_ns
        with self.assertRaises(JOURNAL.JournalError):
            JOURNAL.recover_journal(self.path, self.path)
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_mtime_ns))

    def test_recovery_fsync_failure_leaves_no_copy_or_stage(self):
        raw = self.source()
        destination = self.folder / "copy.jsonl"
        with patch.object(JOURNAL.os, "fsync", side_effect=OSError("fixture")):
            with self.assertRaises(JOURNAL.JournalError):
                JOURNAL.recover_journal(self.path, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(list(self.folder.glob("*.staged")), [])

    def test_recovery_source_drift_before_publish_refused(self):
        self.source()
        destination = self.folder / "copy.jsonl"
        original = JOURNAL._read_source
        calls = [0]

        def drift(path):
            if Path(path) == self.path:
                calls[0] += 1
                if calls[0] == 2:
                    with self.path.open("ab") as handle:
                        handle.write(b"changed\n")
            return original(path)

        with patch.object(JOURNAL, "_read_source", side_effect=drift):
            with self.assertRaises(JOURNAL.JournalError):
                JOURNAL.recover_journal(self.path, destination)
        self.assertFalse(destination.exists())
        self.assertTrue(self.path.read_bytes().endswith(b"changed\n"))

    def test_recovery_source_drift_after_publish_removes_only_owned_copy(self):
        self.source()
        destination = self.folder / "copy.jsonl"
        original = JOURNAL._read_source
        calls = [0]

        def drift(path):
            if Path(path) == self.path:
                calls[0] += 1
                if calls[0] == 3:
                    with self.path.open("ab") as handle:
                        handle.write(b"changed\n")
            return original(path)

        with patch.object(JOURNAL, "_read_source", side_effect=drift):
            with self.assertRaises(JOURNAL.JournalError):
                JOURNAL.recover_journal(self.path, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.folder.glob("*.staged")), [])

    def test_recovery_concurrent_existing_destination_preserved(self):
        self.source()
        destination = self.folder / "copy.jsonl"

        def conflict(_stage, final):
            Path(final).write_bytes(b"concurrent owner's evidence")
            raise FileExistsError("fixture")

        with patch.object(JOURNAL.os, "link", side_effect=conflict):
            with self.assertRaises(JOURNAL.JournalError):
                JOURNAL.recover_journal(self.path, destination)
        self.assertEqual(destination.read_bytes(), b"concurrent owner's evidence")
        self.assertEqual(list(self.folder.glob("*.staged")), [])

    def test_recovery_identical_byte_replacement_not_acknowledged_or_deleted(self):
        raw = self.source()
        destination = self.folder / "copy.jsonl"
        replacement = self.folder / "replacement.jsonl"
        original = JOURNAL._read_source
        calls = [0]

        def replace(path):
            if Path(path) == self.path:
                calls[0] += 1
                if calls[0] == 3:
                    replacement.write_bytes(raw)
                    os.replace(replacement, destination)
            return original(path)

        with patch.object(JOURNAL, "_read_source", side_effect=replace):
            with self.assertRaises(JOURNAL.JournalError):
                JOURNAL.recover_journal(self.path, destination)
        self.assertEqual(destination.read_bytes(), raw)
        self.assertEqual(list(self.folder.glob("*.staged")), [])

    def test_recovery_missing_parent_refused(self):
        self.source()
        destination = self.folder / "missing" / "copy.jsonl"
        with self.assertRaises(JOURNAL.JournalError):
            JOURNAL.recover_journal(self.path, destination)
        self.assertFalse(destination.parent.exists())

    def test_linked_source_and_destination_refused_when_supported(self):
        self.source()
        link = self.folder / "linked.jsonl"
        try:
            link.symlink_to(self.path)
        except OSError:
            self.skipTest("Physical symlink creation is unavailable; deterministic reparse fixture covers the rule.")
        with self.assertRaises(JOURNAL.JournalError):
            JOURNAL.inspect_journal(link)
        with self.assertRaises(JOURNAL.JournalError):
            JOURNAL.recover_journal(self.path, link)

    def test_reparse_attribute_refused(self):
        self.source()
        original = JOURNAL.Path.lstat

        def flagged(path):
            info = original(path)
            if path == self.path:
                class Info:
                    st_mode = info.st_mode
                    st_file_attributes = 0x400
                return Info()
            return info

        with patch.object(JOURNAL.Path, "lstat", flagged):
            with self.assertRaises(JOURNAL.JournalError):
                self.inspect()

    def test_child_interruption_acknowledged_prefix_and_os_lock_release(self):
        code = ("import sys,time; sys.path.insert(0,sys.argv[1]); "
                "from GameToolJournal import Journal; "
                "w=Journal.create(sys.argv[2],{'scope':'authored_child_fixture'}); "
                "w.append('checkpoint',{'count':1}); print('ACKNOWLEDGED',flush=True); "
                "time.sleep(15)")
        process = subprocess.Popen([sys.executable, "-B", "-c", code, str(MODULE.parent), str(self.path)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        messages = queue.Queue()
        reader = threading.Thread(target=lambda: messages.put(process.stdout.readline()), daemon=True)
        reader.start()
        try:
            self.assertEqual(messages.get(timeout=6).strip(), "ACKNOWLEDGED")
            live = self.inspect()  # Windows lock byte must not block this read.
            self.assertTrue(live["valid"])
            self.assertEqual(live["verified_count"], 2)
            with self.path.open("r+b", buffering=0) as other:
                with self.assertRaises(JOURNAL.JournalBusy):
                    JOURNAL._lock(other)
            before = self.path.read_bytes()
            process.kill()  # Only this known authored fixture process is terminated.
            process.wait(timeout=5)
            with self.path.open("r+b", buffering=0) as other:
                JOURNAL._lock(other)
                JOURNAL._unlock(other)
            result = self.inspect()
            self.assertTrue(result["valid"])
            self.assertFalse(result["clean_end"])
            destination = self.folder / "recovered.jsonl"
            receipt = JOURNAL.recover_journal(self.path, destination, result["source_sha256"])
            self.assertEqual(destination.read_bytes(), before)
            self.assertEqual(self.path.read_bytes(), before)
            self.assertEqual(receipt["verified_count"], 2)
            self.assertEqual(receipt["discarded_tail_bytes"], 0)
            self.assertFalse(receipt["replay_allowed"])
        finally:
            if process.poll() is None:
                process.kill()
            process.communicate(timeout=5)
            reader.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
