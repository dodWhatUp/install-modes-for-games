"""Read-only AI foundation contracts on synthetic/private temporary state only."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

import jsonschema

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

from GameToolAIFoundation import FoundationError, FoundationService
from GameToolAIContracts import decode_cursor, output_schema, result_envelope
from GameToolAutomation import AutomationService
from GameToolAITestPackage import build_ai_test_package


class FoundationContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.service = AutomationService(self.root / "private")
        self.package = build_ai_test_package(SCRIPTS.parent, self.root / "package")
        self.foundation = FoundationService(self.service, source_root=self.package)


    def test_repository_checkout_without_generated_manifest_fails_closed(self):
        if (SCRIPTS.parent / "MANIFEST.json").exists():
            self.skipTest("Package-mode run has the generated manifest by design.")
        with self.assertRaises(FoundationError) as raised:
            FoundationService(self.service, source_root=SCRIPTS.parent)
        self.assertEqual(raised.exception.code, "PACKAGE_UNAVAILABLE")

    def test_status_has_distinct_completion_and_no_private_path(self):
        result = self.foundation.status()
        self.assertEqual(result["status"], "CURRENT")
        self.assertEqual(result["completion"]["connection"], "verified")
        self.assertEqual(result["completion"]["runtime"], "not_started")
        self.assertFalse(result["privacy"]["paths_included"])
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_status_revision_delta(self):
        first = self.foundation.status()
        second = self.foundation.status(known_revision=first["revision"])
        self.assertEqual(second["status"], "UNCHANGED")
        self.assertTrue(second["data"]["unchanged"])

    def test_search_then_fetch_uses_stable_ids(self):
        result = self.foundation.search("local approval", "docs", 5)
        self.assertTrue(result["data"]["results"])
        row = result["data"]["results"][0]
        fetched = self.foundation.fetch(row["result_id"], row["revision"], limit=8)
        self.assertEqual(fetched["data"]["revision"], row["revision"])
        self.assertNotIn(str(self.root), json.dumps(fetched))
        self.assertTrue(row["resource_uri"].startswith("game-tools-knowledge://"))

    def test_fetch_refuses_unknown_and_changed_revision(self):
        with self.assertRaises(ValueError):
            self.foundation.fetch("knowledge:not-real")
        row = self.foundation.search("approval", limit=1)["data"]["results"][0]
        with self.assertRaises(ValueError):
            self.foundation.fetch(row["result_id"], "0" * 64)

    def test_resume_reports_pending_request_without_execution(self):
        before = self.service.mods_root.exists()
        self.service.propose(
            "mods.create_plan",
            {"mode": "real-time", "selected": ["unity-mod-manager"]},
            request_id="resume-fixture",
        )
        result = self.foundation.resume()
        self.assertEqual(result["status"], "RESUME_READY")
        self.assertEqual(result["data"]["open_work"]["requests"][0]["request_id"], "resume-fixture")
        self.assertEqual(before, self.service.mods_root.exists())
        self.assertFalse(result["retry"]["allowed"])

    def test_change_cursor_is_self_contained_and_tracks_requests(self):
        first = self.foundation.changes()
        cursor = first["data"]["new_cursor"]
        self.assertIn("revisions", decode_cursor(cursor))
        second = self.foundation.changes(cursor)
        self.assertEqual(second["status"], "UNCHANGED")
        self.service.propose(
            "mods.create_plan",
            {"mode": "real-time", "selected": ["unity-mod-manager"]},
            request_id="cursor-fixture",
        )
        third = self.foundation.changes(second["data"]["new_cursor"])
        self.assertEqual(third["status"], "CHANGED")
        self.assertIn("requests", third["data"]["changed_sections"])
        self.assertIn("cursor-fixture", {row["id"] for row in third["data"]["changed_ids"]})

    def test_changed_cursor_refused(self):
        cursor = self.foundation.changes()["data"]["new_cursor"]
        altered = cursor[:-1] + ("0" if cursor[-1] != "0" else "1")
        with self.assertRaises(ValueError):
            self.foundation.changes(altered)

    def test_blocker_preserves_unknown_effects_and_no_retry(self):
        result = self.foundation.blocker("UNKNOWN_EFFECTS_RECONCILE", "request-1")
        self.assertEqual(result["result_type"], "blocked")
        self.assertTrue(result["effects"]["unknown"])
        self.assertFalse(result["retry"]["allowed"])
        self.assertEqual(result["retry"]["inspect_handle"], "request-1")

    def test_batch_status_inspects_same_request(self):
        self.service.propose(
            "mods.create_plan",
            {"mode": "real-time", "selected": ["unity-mod-manager"]},
            request_id="batch-fixture",
        )
        result = self.foundation.status_batch([{"kind": "request", "id": "batch-fixture"}])
        row = result["data"]["results"][0]
        self.assertEqual(row["status"], "AWAITING_LOCAL_APPROVAL")
        self.assertEqual(row["value"]["request_id"], "batch-fixture")
        self.assertFalse(self.service.mods_root.exists())

    def test_batch_bad_handle_does_not_hide_valid_handle(self):
        self.service.propose(
            "mods.create_plan",
            {"mode": "real-time", "selected": ["unity-mod-manager"]},
            request_id="valid-fixture",
        )
        result = self.foundation.status_batch([
            {"kind": "request", "id": "missing"},
            {"kind": "request", "id": "valid-fixture"},
        ])
        self.assertEqual(len(result["data"]["results"]), 2)
        self.assertEqual(result["data"]["results"][1]["status"], "AWAITING_LOCAL_APPROVAL")

    def test_catalog_is_bundled_read_only(self):
        result = self.foundation.catalog("ReShade", limit=8)
        self.assertEqual(result["effects"]["write"], [])
        self.assertFalse(result["effects"]["network"])
        self.assertTrue(result["data"]["planning_only"])
        self.assertNotIn(str(self.root), json.dumps(result))

    def test_reports_reads_only_explicit_shared_summaries(self):
        empty = self.foundation.reports()
        self.assertEqual(empty["data"]["records"], [])
        self.assertFalse(empty["data"]["benchmark_executed"])


    def test_representative_outputs_validate_against_shipped_schema(self):
        schema = json.loads((SCRIPTS.parent / "schemas" / "ai-result-envelope.schema.json").read_text())
        outputs = [
            self.foundation.status(),
            self.foundation.search("approval", limit=1),
            self.foundation.resume(),
            self.foundation.changes(),
            self.foundation.blocker("SOURCE_CHANGED"),
            self.foundation.status_batch([{"kind": "request", "id": "missing"}]),
            self.foundation.catalog("ReShade", limit=2),
            self.foundation.reports(),
        ]
        for value in outputs:
            jsonschema.validate(value, schema)

    def test_prepare_handoff_is_stable_sanitized_preview_only(self):
        result = self.foundation.prepare_handoff(include=["status", "resume", "knowledge"])
        self.assertEqual(result["result_type"], "preview")
        self.assertEqual(result["status"], "HANDOFF_PREPARED")
        self.assertEqual(result["revision"], result["data"]["content_hash"])
        self.assertFalse(result["data"]["local_save_action"]["performed"])
        self.assertEqual(result["effects"]["write"], [])
        self.assertNotIn(str(self.root), json.dumps(result))
        jsonschema.validate(result, json.loads((SCRIPTS.parent / "schemas" / "ai-result-envelope.schema.json").read_text()))

    def test_result_envelope_rejects_untyped_evidence(self):
        with self.assertRaises(ValueError):
            result_envelope(
                result_type="read", status="OK",
                evidence=[{"id": "record", "level": "guess", "revision": "0" * 64}],
            )

    def test_output_schema_keeps_completion_fields_distinct(self):
        schema = output_schema()
        fields = schema["properties"]["completion"]["required"]
        self.assertEqual(len(fields), 9)
        self.assertIn("installation", fields)
        self.assertIn("runtime", fields)
        self.assertIn("publication", fields)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(FoundationContracts)
    )
    raise SystemExit(not result.wasSuccessful())
