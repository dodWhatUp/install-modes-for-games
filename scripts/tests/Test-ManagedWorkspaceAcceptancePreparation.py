"""Acceptance launcher boundaries; native prompts are mocked, never product acceptance."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SCRIPTS))
from game_system_control import windows_account
from game_system_control.contracts import ContextError
from game_system_control.access import AccessStore


class AcceptancePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="acceptance-launcher-contract-")
        self.root = Path(self.temp.name)
        self.main = runpy.run_path(str(SCRIPTS / "tests/Accept-ManagedWorkspaceWindowsAccount.py"))["main"]

    def tearDown(self): self.temp.cleanup()

    def run_harness(self, *args, availability="available", outcomes=()):
        out = StringIO()
        with patch.dict(self.main.__globals__, {"availability": lambda: {"status": availability}, "source_record": lambda: {"source_head": "fixture-only", "source_files": []}}), patch.object(windows_account, "_native_verify", side_effect=outcomes) as verify, redirect_stdout(out):
            result = self.main(["--local-parent", str(self.root), *args])
        return result, out.getvalue(), verify.call_count

    def receipt(self):
        return json.loads(next(self.root.glob("*/ACCEPTANCE.private.json")).read_text())

    def test_default_preflight_does_not_prompt_or_create_anything(self):
        code, output, calls = self.run_harness("--host-label", "B")
        self.assertEqual((code, calls), (0, 0)); self.assertEqual(list(self.root.iterdir()), [])
        result = json.loads(output)
        self.assertEqual(result["host_label"], "B"); self.assertEqual(result["effect"], "none")
        self.assertEqual(result["interactive_acceptance"], "not_completed")

    def test_unavailable_preflight_is_evidence_not_acceptance(self):
        _, output, calls = self.run_harness(availability="not_configured_for_user")
        self.assertEqual(calls, 0); self.assertEqual(json.loads(output)["interactive_acceptance"], "not_completed")
        with self.assertRaises(ContextError): self.run_harness("--run-interactive", availability="unavailable")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_interactive_requires_success_then_explicit_cancel_and_stays_stopped(self):
        code, _, calls = self.run_harness("--run-interactive", "--host-label", "B", outcomes=["verified", "canceled"])
        self.assertEqual((code, calls), (0, 2))
        result = self.receipt()
        self.assertEqual(result["interactive_acceptance"], "passed"); self.assertTrue(result["fixture_access_left_stopped"])
        self.assertEqual(result["original_checks_closed"], 0)

    def test_failed_second_prompt_is_not_a_cancellation_pass(self):
        with self.assertRaises(ContextError): self.run_harness("--run-interactive", outcomes=["verified", "device_busy"])
        result = self.receipt()
        self.assertEqual(result["interactive_acceptance"], "not_completed"); self.assertTrue(result["fixture_access_left_stopped"])

    def test_accidental_second_success_is_stopped_and_not_accepted(self):
        with self.assertRaises(ContextError): self.run_harness("--run-interactive", outcomes=["verified", "verified"])
        self.assertTrue(self.receipt()["fixture_access_left_stopped"])
        self.assertEqual(self.receipt()["interactive_acceptance"], "not_completed")

    def test_first_prompt_cancel_creates_no_access_registry(self):
        with self.assertRaises(ContextError): self.run_harness("--run-interactive", outcomes=["canceled"])
        self.assertFalse(self.receipt()["fixture_access_left_stopped"])
        self.assertEqual(list(self.root.glob("*/access")), [])

    def test_repository_or_portable_parent_is_rejected_before_prompt(self):
        for marker in (".git", "vault.json"):
            with self.subTest(marker=marker):
                p = self.root / marker; p.touch()
                with self.assertRaises(ContextError): self.run_harness("--run-interactive", outcomes=["verified", "canceled"])
                p.unlink()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_real_source_record_covers_the_native_owner_and_launcher(self):
        ns = runpy.run_path(str(SCRIPTS / "tests/Accept-ManagedWorkspaceWindowsAccount.py"))
        record = ns["source_record"]()
        self.assertEqual(len(record["source_head"]), 40)
        self.assertEqual(len(record["source_files"]), 4)
        self.assertTrue(all(len(p["sha256"]) == 64 and not Path(p["path"]).is_absolute() for p in record["source_files"]))

    def test_stale_stopped_registry_does_not_silently_refresh_or_resume(self):
        with patch.object(windows_account, "_native_verify", return_value="verified"):
            access = AccessStore.create(self.root / "stale", "account", "device", "project", now=100, windows_sign_in=True)
        actor = {"workspace_id": "workspace", "project_id": "project", "account_id": "account", "device_id": "device", "generation": 1, "capability": "enrollment.manage"}
        stop = access.stop_local()
        with patch.object(windows_account, "_native_verify", side_effect=AssertionError("no implicit reauthorization")):
            with self.assertRaises(ContextError): access.resume_local(actor, stop["stop_sha256"], now=401)
            with self.assertRaises(ContextError): access.propose_change(actor, "heartbeat", {"device_id": "device", "online": True}, now=401)
        self.assertTrue((access.state.root / "LOCAL-STOP.json").exists())
        self.assertEqual(access.snapshot()["body"]["devices"][0]["last_seen"], 100)

    def test_native_handover_preflight_never_creates_or_enrolls(self):
        main = runpy.run_path(str(SCRIPTS / "tests/Accept-ManagedWorkspaceHandover.py"))["main"]
        local, data = self.root / "local", self.root / "data"; local.mkdir(); data.mkdir()
        def observe(path): return {"volume_id": Path(path).name, "system_volume": Path(path) == local, "adapter": "fixture-only"}
        out = StringIO()
        with patch.dict(main.__globals__, {"volume_identity": observe, "source_record": lambda: {}, "VaultRegistry": lambda *a: self.fail("Preflight must not enroll")}), redirect_stdout(out):
            self.assertEqual(main(["--local-parent", str(local), "--data-parent", str(data)]), 0)
        self.assertEqual(list(local.iterdir()), []); self.assertEqual(list(data.iterdir()), [])
        self.assertEqual(json.loads(out.getvalue())["effect"], "none")

    def test_native_handover_parent_safety_refuses_system_data_and_repositories(self):
        main = runpy.run_path(str(SCRIPTS / "tests/Accept-ManagedWorkspaceHandover.py"))["main"]
        args = ["--local-parent", str(self.root), "--data-parent", str(self.root)]
        with patch.dict(main.__globals__, {"volume_identity": lambda _: {"volume_id": "same", "system_volume": True}}):
            with self.assertRaises(ContextError): main(args)
        (self.root / ".git").touch()
        with self.assertRaises(ContextError): main(args)


if __name__ == "__main__": unittest.main(verbosity=2)
