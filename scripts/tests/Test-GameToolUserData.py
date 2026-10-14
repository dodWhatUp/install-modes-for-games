"""Offline fixtures only: no installed profiles, process control or network."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

MODULE = Path(__file__).resolve().parents[1] / "GameToolUserData.py"
spec = importlib.util.spec_from_file_location("user_data_under_test", MODULE)
data = importlib.util.module_from_spec(spec)
spec.loader.exec_module(data)


class UserDataFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="GameTools-UserDataFixture-")
        self.root = Path(self.temp.name)
        self.source = self.root / "settings.ini"
        self.source.write_bytes(b"[Profile]\nF7=LocalHold\nPicture=fixture.png\n")
        self.other = self.root / "overlay.json"
        self.other.write_bytes('{"unknown": [1, "עברית"], "active": true}'.encode())
        self.selections = [{"path": str(self.source), "logical_path": "studio/settings.ini",
                            "record_id": "studio-settings", "owner": "fixture-studio", "revision": "r-original"},
                           {"path": str(self.other), "logical_path": "hub/overlay.json", "owner": "fixture-hub"}]
        self.before = {p: p.read_bytes() for p in (self.source, self.other)}

    def tearDown(self):
        for path, original in self.before.items():
            # Tests with deliberate drift opt out only for the selected fixture.
            self.assertEqual(path.read_bytes(), original)
        self.temp.cleanup()

    def refused(self, code, fn, *args, **kwargs):
        with self.assertRaises(data.UserDataError) as raised:
            fn(*args, **kwargs)
        self.assertEqual(raised.exception.code, code)

    def old_envelope(self):
        return {"schema_version": 1, "data_version": 1, "record_id": "stable-profile-1",
                "kind": "overlay.profile", "source": {"owner": "original", "revision": "r9",
                "future_source_fact": {"value": 3}}, "payload": {"hotkey": "F7", "future": ["x"]},
                "future_top_level": {"a": True}, "producer": {"app_version": "0.2.0"}}

    def package(self):
        preview = data.preview_export(self.selections, app_version="9.0.0")
        archive = self.root / "private.zip"
        exported = data.export_archive(archive, preview)
        inspected = data.inspect_archive(archive, exported["sha256"])
        return archive, preview, inspected

    def rewrite_zip(self, archive, mutate):
        with zipfile.ZipFile(archive) as z:
            contents = {row.filename: z.read(row) for row in z.infolist()}
        mutate(contents)
        edited = self.root / ("edited-" + str(len(list(self.root.glob("edited-*")))) + ".zip")
        with zipfile.ZipFile(edited, "w") as z:
            for name, raw in contents.items():
                z.writestr(name, raw)
        return edited

    def test_current_envelope_data_not_app_version(self):
        envelope = data.make_envelope("scenario", {"nested": [1]}, record_id="retained", app_version="0.001")
        self.assertEqual(envelope["data_version"], 2)
        self.assertEqual(envelope["producer"]["app_version"], "0.001")
        self.assertEqual(data.preview_migration(envelope)["changes"], [])

    def test_make_envelope_copies_mutable_source(self):
        payload, source = {"settings": {"x": 1}}, {"a": []}
        envelope = data.make_envelope("profile", payload, source=source)
        payload["settings"]["x"] = 9; source["a"].append(1)
        self.assertEqual(envelope["payload"]["settings"]["x"], 1)
        self.assertEqual(envelope["source"]["a"], [])

    def test_additive_migration_preserves_unknown_fields(self):
        original = self.old_envelope(); before = copy.deepcopy(original)
        result = data.preview_migration(original)
        self.assertEqual(original, before)
        migrated = result["envelope"]
        for field in original:
            if field != "data_version":
                self.assertEqual(migrated[field], original[field])
        self.assertEqual(migrated["links"], [])
        self.assertEqual(migrated["extensions"], {})
        self.assertEqual(migrated["record_id"], "stable-profile-1")
        self.assertEqual(result["state"], "PREVIEW_READY")

    def test_migration_preserves_existing_extension_fields(self):
        envelope = self.old_envelope()
        envelope.update(links=[{"unknown_link": True}], extensions={"unrecognized": {"a": 2}})
        migrated = data.preview_migration(envelope)["envelope"]
        self.assertEqual(migrated["links"], envelope["links"])
        self.assertEqual(migrated["extensions"], envelope["extensions"])

    def test_migration_collision_is_not_silently_rewritten(self):
        envelope = self.old_envelope(); envelope["links"] = "unknown legacy meaning"
        self.refused("CURRENT_ENVELOPE_FIELD_INVALID", data.preview_migration, envelope)
        self.assertEqual(envelope["links"], "unknown legacy meaning")

    def test_future_envelope_is_unchanged_read_only(self):
        envelope = self.old_envelope(); envelope.update(data_version=700, schema_version=9)
        result = data.preview_migration(envelope)
        self.assertTrue(result["read_only"])
        self.assertEqual(result["state"], "BLOCKED_FUTURE_VERSION")
        self.assertEqual(result["envelope"], envelope)

    def test_requested_future_migration_blocks(self):
        result = data.preview_migration(self.old_envelope(), 3)
        self.assertTrue(result["read_only"])

    def test_downgrade_refused(self):
        self.refused("DOWNGRADE_REFUSED", data.preview_migration, data.make_envelope("p", {}), 1)

    def test_migration_new_copy_original_unchanged(self):
        original = self.root / "old-envelope.json"
        original.write_text(json.dumps(self.old_envelope()), encoding="utf-8")
        raw = original.read_bytes(); result = data.inspect_envelope(original)
        destination = self.root / "new-envelope.json"
        receipt = data.save_migrated_copy(original, destination, result["file_sha256"], result["preview_sha256"])
        self.assertEqual(original.read_bytes(), raw)
        self.assertEqual(json.loads(destination.read_text())["data_version"], 2)
        self.assertFalse(receipt["originals_replaced"])

    def test_migration_in_place_refused(self):
        original = self.root / "old.json"; original.write_text(json.dumps(self.old_envelope()))
        p = data.inspect_envelope(original)
        self.refused("NEW_COPY_REQUIRED", data.save_migrated_copy, original, original,
                     p["file_sha256"], p["preview_sha256"])

    def test_migration_source_drift_refused(self):
        original = self.root / "old.json"; original.write_text(json.dumps(self.old_envelope()))
        p = data.inspect_envelope(original); original.write_text(json.dumps(self.old_envelope()) + " ")
        self.refused("SOURCE_CHANGED", data.save_migrated_copy, original, self.root / "copy.json",
                     p["file_sha256"], p["preview_sha256"])
        self.assertFalse((self.root / "copy.json").exists())

    def test_migration_preview_mismatch_refused(self):
        original = self.root / "old.json"; original.write_text(json.dumps(self.old_envelope()))
        p = data.inspect_envelope(original)
        self.refused("PREVIEW_CHANGED", data.save_migrated_copy, original, self.root / "copy.json",
                     p["file_sha256"], "0" * 64)

    def test_future_migration_commit_refused(self):
        original = self.root / "future.json"; env = self.old_envelope(); env["data_version"] = 8
        original.write_text(json.dumps(env)); p = data.inspect_envelope(original)
        self.refused("FUTURE_VERSION_READ_ONLY", data.save_migrated_copy, original, self.root / "copy.json",
                     p["file_sha256"], p["preview_sha256"])

    def test_nonfinite_and_duplicate_json_refused(self):
        self.refused("NONFINITE_JSON_VALUE", data._decode, b'{"v":NaN}')
        self.refused("DUPLICATE_JSON_FIELD", data._decode, b'{"v":1,"v":2}')

    def test_json_bounds_and_unsupported_objects(self):
        self.refused("INVALID_JSON_DATA", data.make_envelope, "p", {"x": object()})
        with patch.object(data, "MAX_JSON_BYTES", 20):
            self.refused("JSON_LIMIT_EXCEEDED", data.make_envelope, "p", {})
        deep = []; node = deep
        for _ in range(22):
            node.append([]); node = node[0]
        self.refused("JSON_TREE_LIMIT_EXCEEDED", data.make_envelope, "p", deep)

    def test_preview_export_is_read_only_exact_provenance(self):
        before_names = sorted(p.name for p in self.root.iterdir())
        preview = data.preview_export(self.selections, app_version="0.13.0")
        self.assertEqual(before_names, sorted(p.name for p in self.root.iterdir()))
        self.assertFalse(preview["network_sync"])
        row = preview["manifest"]["files"][0]
        self.assertEqual(row["provenance"]["source_path"], str(self.source))
        self.assertEqual(row["provenance"]["revision"], "r-original")
        self.assertEqual(row["sha256"], hashlib.sha256(self.before[self.source]).hexdigest())
        self.assertIsNone(row["data_version"])

    def test_default_ids_stable_across_changed_contents(self):
        selection = [{"path": str(self.source), "logical_path": "same.ini", "owner": "same-owner"}]
        a = data.preview_export(selection)["manifest"]["files"][0]["record_id"]
        self.source.write_bytes(b"changed"); self.before[self.source] = b"changed"
        b = data.preview_export(selection)["manifest"]["files"][0]["record_id"]
        self.assertEqual(a, b)

    def test_restore_bytes_to_new_directory_not_active_data(self):
        archive, _, inspected = self.package()
        target = self.root / "recovered"
        receipt = data.restore_new_copy(archive, target, inspected["archive_sha256"], inspected["preview_sha256"])
        self.assertEqual((target / "data/studio/settings.ini").read_bytes(), self.before[self.source])
        self.assertEqual((target / "data/hub/overlay.json").read_bytes(), self.before[self.other])
        self.assertFalse((target / "_RESTORE-INCOMPLETE.json").exists())
        self.assertFalse(receipt["profiles_activated"])
        self.assertFalse(receipt["envelopes_migrated"])
        self.assertTrue((target / "RESTORE-RECEIPT.json").is_file())

    def test_restore_existing_directory_never_merges(self):
        archive, _, p = self.package(); target = self.root / "recovered"; target.mkdir()
        marker = target / "existing.txt"; marker.write_text("keep")
        self.refused("NEW_COPY_REQUIRED", data.restore_new_copy, archive, target,
                     p["archive_sha256"], p["preview_sha256"])
        self.assertEqual(marker.read_text(), "keep")
        self.assertEqual(list(target.iterdir()), [marker])

    def test_restore_hash_and_preview_guard(self):
        archive, _, p = self.package()
        self.refused("ARCHIVE_CHANGED", data.restore_new_copy, archive, self.root / "new", "0" * 64,
                     p["preview_sha256"])
        self.refused("PREVIEW_CHANGED", data.restore_new_copy, archive, self.root / "new",
                     p["archive_sha256"], "0" * 64)
        self.assertFalse((self.root / "new").exists())

    def test_export_source_drift_refuses_before_archive_write(self):
        preview = data.preview_export(self.selections)
        self.source.write_bytes(b"intentional drift"); self.before[self.source] = b"intentional drift"
        self.refused("SOURCE_CHANGED", data.export_archive, self.root / "private.zip", preview)
        self.assertFalse((self.root / "private.zip").exists())

    def test_export_preview_tamper_refused(self):
        preview = data.preview_export(self.selections); preview["manifest"]["producer"]["app_version"] = "changed"
        self.refused("PREVIEW_CHANGED", data.export_archive, self.root / "private.zip", preview)

    def test_archive_tampered_payload_refused(self):
        archive, _, _ = self.package()
        edited = self.rewrite_zip(archive, lambda contents: contents.update({"data/studio/settings.ini": b"tamper"}))
        self.refused("ARCHIVE_HASH_MISMATCH", data.inspect_archive, edited)

    def test_archive_missing_or_unlisted_member_refused(self):
        archive, _, _ = self.package()
        edited = self.rewrite_zip(archive, lambda contents: contents.pop("data/studio/settings.ini"))
        self.refused("ARCHIVE_INVENTORY_MISMATCH", data.inspect_archive, edited)
        extra = self.rewrite_zip(archive, lambda contents: contents.update({"data/extra.ini": b"x"}))
        self.refused("ARCHIVE_INVENTORY_MISMATCH", data.inspect_archive, extra)

    def test_archive_traversal_and_windows_aliases_refused(self):
        archive, _, _ = self.package()
        for name in ("../escape", "data/../escape", "data\\escape", "/data/file", "data/C:evil",
                     "data/NUL.ini", "data/COM¹.txt", "data/trailing.", "data/trailing ",
                     "data//empty", "data/./dot"):
            with self.subTest(name=name):
                edited = self.rewrite_zip(archive, lambda c: c.update({name: b"x"}))
                if "\\" in name:
                    # ZipInfo normalizes Windows os.sep on creation; simulate an
                    # external archive's actual backslash local/central headers.
                    edited.write_bytes(edited.read_bytes().replace(name.replace("\\", "/").encode(), name.encode()))
                self.refused("UNSAFE_ARCHIVE_PATH", data.inspect_archive, edited)
        self.assertFalse((self.root.parent / "escape").exists())

    def test_archive_symlink_and_directory_refused(self):
        archive, _, _ = self.package()
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o600, stat.S_IFDIR | 0o755):
            edited = self.rewrite_zip(archive, lambda c: None)
            info = zipfile.ZipInfo("data/link"); info.create_system = 3; info.external_attr = mode << 16
            with zipfile.ZipFile(edited, "a") as z:
                z.writestr(info, b"destination")
            self.refused("ARCHIVE_LINK_OR_TYPE_REFUSED", data.inspect_archive, edited)

    def test_archive_case_collision_refused(self):
        archive, _, _ = self.package()
        edited = self.rewrite_zip(archive, lambda c: c.update({"data/STUDIO/settings.ini": b"x"}))
        self.refused("ARCHIVE_DUPLICATE_MEMBER", data.inspect_archive, edited)

    def test_explicit_selections_no_directory_or_broad_discovery(self):
        self.refused("EXPLICIT_FILE_SELECTION_REQUIRED", data.preview_export, [{"directory": str(self.root)}])
        self.refused("FILE_LIMIT_OR_TYPE_REFUSED", data.preview_export,
                     [{"path": str(self.root), "logical_path": "directory"}])
        self.refused("FILE_COUNT_LIMIT_EXCEEDED", data.preview_export, [])

    def test_selection_duplicate_names_and_ids_refused(self):
        rows = copy.deepcopy(self.selections); rows[1]["logical_path"] = "STUDIO/settings.ini"
        self.refused("DUPLICATE_FILE_OR_ID", data.preview_export, rows)

    def test_file_parent_prefix_collision_refused_before_restore(self):
        rows = copy.deepcopy(self.selections); rows[0]["logical_path"] = "profile"
        rows[1]["logical_path"] = "Profile/settings.json"
        self.refused("DUPLICATE_FILE_OR_ID", data.preview_export, rows)

    def test_invalid_falsy_source_not_silently_dropped(self):
        self.refused("PROVENANCE_OBJECT_REQUIRED", data.make_envelope, "profile", {}, source=False)
        rows = copy.deepcopy(self.selections); rows[1]["record_id"] = "studio-settings"
        self.refused("DUPLICATE_FILE_OR_ID", data.preview_export, rows)

    def test_source_file_link_refused_where_supported(self):
        linked = self.root / "link.ini"
        try:
            linked.symlink_to(self.source)
        except OSError:
            self.skipTest("Symlink creation unavailable; archive links separately tested.")
        self.refused("LINKED_PATH_REFUSED", data.preview_export,
                     [{"path": str(linked), "logical_path": "linked.ini"}])

    def test_local_root_relative_traversal_refused(self):
        for value in ("relative.ini", self.root.anchor, str(self.root / ".." / "x"),
                      str(self.root / "file.ini:alternate-stream"), str(self.root / "NUL.txt"),
                      str(self.root / "trailing ")):
            self.refused("UNSAFE_LOCAL_PATH", data.local_path, value)

    def test_file_count_and_total_limits(self):
        with patch.object(data, "MAX_FILES", 1):
            self.refused("FILE_COUNT_LIMIT_EXCEEDED", data.preview_export, self.selections)
        with patch.object(data, "MAX_TOTAL_BYTES", 2):
            self.refused("TOTAL_SIZE_LIMIT_EXCEEDED", data.preview_export, self.selections)
        with patch.object(data, "MAX_FILE_BYTES", 2):
            self.refused("FILE_LIMIT_OR_TYPE_REFUSED", data.preview_export, self.selections)

    def test_archive_entry_limits(self):
        archive, _, _ = self.package()
        with patch.object(data, "MAX_FILES", 1):
            self.refused("ARCHIVE_LIMIT_EXCEEDED", data.inspect_archive, archive)
        with patch.object(data, "MAX_FILE_BYTES", 1):
            self.refused("ARCHIVE_MEMBER_LIMIT_EXCEEDED", data.inspect_archive, archive)

    def test_future_archive_version_read_only_no_restore(self):
        archive, _, _ = self.package()
        def future(contents):
            manifest = json.loads(contents["MANIFEST.json"]); manifest["data_version"] = 90
            manifest["future_field"] = {"preserve": True}
            contents["MANIFEST.json"] = json.dumps(manifest).encode()
        edited = self.rewrite_zip(archive, future); p = data.inspect_archive(edited)
        self.assertTrue(p["read_only"])
        self.assertEqual(p["manifest"]["future_field"], {"preserve": True})
        self.refused("FUTURE_VERSION_READ_ONLY", data.restore_new_copy, edited, self.root / "new",
                     p["archive_sha256"], p["preview_sha256"])
        self.assertFalse((self.root / "new").exists())

    def test_old_envelope_archive_restores_unchanged_not_implicit_migration(self):
        old = self.root / "old.json"; old.write_text(json.dumps(self.old_envelope()))
        selection = [{"path": str(old), "logical_path": "profiles/old.json", "format": "envelope"}]
        preview = data.preview_export(selection); archive = self.root / "old.zip"
        data.export_archive(archive, preview); inspected = data.inspect_archive(archive)
        self.assertEqual(inspected["migrations"][0]["changes"][-1]["to"], 2)
        target = self.root / "recovered"
        data.restore_new_copy(archive, target, inspected["archive_sha256"], inspected["preview_sha256"])
        self.assertEqual((target / "data/profiles/old.json").read_bytes(), old.read_bytes())
        self.assertEqual(json.loads(old.read_text())["data_version"], 1)

    def test_declared_envelope_id_cannot_change_stable_source_id(self):
        old = self.root / "old.json"; old.write_text(json.dumps(self.old_envelope()))
        selection = [{"path": str(old), "logical_path": "old.json", "format": "envelope",
                      "record_id": "different-id"}]
        self.refused("ENVELOPE_STABLE_ID_MISMATCH", data.preview_export, selection)

    def test_future_envelope_blocks_archive_restore(self):
        old = self.root / "future.json"; env = self.old_envelope(); env["data_version"] = 99
        old.write_text(json.dumps(env)); selection = [{"path": str(old), "logical_path": "future.json", "format": "envelope"}]
        preview = data.preview_export(selection); archive = self.root / "future.zip"
        data.export_archive(archive, preview); inspected = data.inspect_archive(archive)
        self.assertTrue(inspected["read_only"])
        self.refused("FUTURE_VERSION_READ_ONLY", data.restore_new_copy, archive, self.root / "new",
                     inspected["archive_sha256"], inspected["preview_sha256"])

    def test_export_destination_not_overwritten(self):
        preview = data.preview_export(self.selections); destination = self.root / "existing.zip"
        destination.write_bytes(b"keep-original")
        self.refused("NEW_COPY_REQUIRED", data.export_archive, destination, preview)
        self.assertEqual(destination.read_bytes(), b"keep-original")

    def test_interrupted_restore_retains_incomplete_marker(self):
        archive, _, p = self.package(); target = self.root / "incomplete"
        original_write = data._write_new
        def fail_payload(path, raw):
            if str(path).endswith("settings.ini"):
                raise OSError("offline disk failure fixture")
            original_write(path, raw)
        with patch.object(data, "_write_new", fail_payload):
            with self.assertRaises(OSError):
                data.restore_new_copy(archive, target, p["archive_sha256"], p["preview_sha256"])
        self.assertTrue((target / "_RESTORE-INCOMPLETE.json").is_file())
        self.assertFalse((target / "RESTORE-RECEIPT.json").exists())

    def test_invalid_archive_refused(self):
        invalid = self.root / "invalid.zip"; invalid.write_bytes(b"not a zip")
        self.refused("INVALID_ARCHIVE", data.inspect_archive, invalid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
