"""Windows-account contract tests; no credential prompt is automated."""
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import ctypes as c

SCRIPTS = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SCRIPTS))
from game_system_control import windows_account as windows
from game_system_control.access import AccessStore, validate_access
from game_system_control.contracts import ContextError
from game_system_control.workspace_state import principal


class WindowsAccountTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="windows-account-contract-")
        self.root = Path(self.tmp.name)
        self.access = AccessStore.create(self.root/"access", "admin", "device", "project", now=100)
        self.actor = {"workspace_id": "workspace", "project_id": "project", "account_id": "admin", "device_id": "device", "generation": 1, "capability": "enrollment.manage"}

    def tearDown(self): self.tmp.cleanup()

    def upgrade(self):
        proposal = self.access.propose_change(self.actor, "require_windows_sign_in", {}, now=100)
        with patch.object(windows, "_native_verify", return_value="verified"):
            return self.access.accept(self.actor, proposal, proposal["preview_sha256"], now=100)

    def prepared(self):
        return self.access.propose_change(self.actor, "enroll", {"device_id": "new-device"}, now=100)

    def test_new_windows_registry_verifies_before_creating_any_output(self):
        with patch.object(windows, "_native_verify", return_value="canceled"):
            with self.assertRaises(ContextError):
                AccessStore.create(self.root/"new", "admin", "device", "project", now=100, windows_sign_in=True)
        self.assertFalse((self.root/"new").exists())

    def test_new_windows_registry_remains_machine_bound_without_storage_or_policy_grants(self):
        with patch.object(windows, "_native_verify", return_value="verified") as native:
            access = AccessStore.create(self.root/"new", "admin", "device", "project", now=100, windows_sign_in=True)
        body = access.snapshot()["body"]
        self.assertEqual(body["authentication"], "windows_hello"); self.assertEqual(native.call_count, 1)
        self.assertEqual(body["accounts"][0]["subject_hash"], principal())
        self.assertEqual(body["storage_permissions"], []); self.assertIsNone(body["active_policy_revision"])

    def test_upgrade_preview_is_inert_and_every_nonverified_result_leaves_state_unchanged(self):
        before = self.access.snapshot()
        with patch.object(windows, "_native_verify") as native:
            proposal = self.access.propose_change(self.actor, "require_windows_sign_in", {}, now=100)
            native.assert_not_called()
        for result in (*windows.RESULTS[1:], "unavailable", None, True, {"verified": True}):
            with self.subTest(result=result), patch.object(windows, "_native_verify", return_value=result):
                with self.assertRaises(ContextError): self.access.accept(self.actor, proposal, proposal["preview_sha256"], now=100)
            self.assertEqual(self.access.snapshot(), before)

    def test_each_privileged_commit_needs_a_new_native_verification(self):
        self.upgrade()
        with patch.object(windows, "_native_verify", return_value="verified") as native:
            p = self.prepared(); self.access.accept(self.actor, p, p["preview_sha256"], now=100)
            p = self.access.propose_change(self.actor, "revoke", {"device_id": "new-device"}, now=100)
            self.access.accept(self.actor, p, p["preview_sha256"], now=100)
        self.assertEqual(native.call_count, 2)

    def test_native_error_does_not_modify_state_or_leave_an_action_lock(self):
        self.upgrade(); before = self.access.snapshot(); p = self.prepared()
        with patch.object(windows, "_native_verify", side_effect=ContextError("unavailable")):
            with self.assertRaises(ContextError): self.access.accept(self.actor, p, p["preview_sha256"], now=100)
        self.assertEqual(self.access.snapshot(), before)
        self.assertFalse((self.access.state.root/".workspace-state.lock").exists())

    def test_imported_json_receipt_cannot_satisfy_the_process_local_proof(self):
        self.upgrade(); p = self.prepared()
        p["windows_verified"] = {"provider": "windows_hello", "result": "verified"}
        with patch.object(windows, "_native_verify") as native:
            with self.assertRaises(ContextError): self.access.accept(self.actor, p, p["preview_sha256"], now=100)
            native.assert_not_called()

    def test_stale_or_tampered_preview_is_rejected_before_any_prompt(self):
        self.upgrade(); stale = self.prepared()
        with patch.object(windows, "_native_verify", return_value="verified"):
            self.access.accept(self.actor, stale, stale["preview_sha256"], now=100)
        p = self.access.propose_change(self.actor, "heartbeat", {"device_id": "device", "online": True}, now=100)
        tampered = deepcopy(p); tampered["body"]["devices"][0]["online"] = False
        for candidate, accepted in ((stale, stale["preview_sha256"]), (tampered, p["preview_sha256"]), (p, "a"*64)):
            with patch.object(windows, "_native_verify") as native:
                with self.assertRaises(ContextError): self.access.accept(self.actor, candidate, accepted, now=100)
                native.assert_not_called()

    def test_secure_registry_cannot_be_downgraded_by_an_accepted_proposal(self):
        self.upgrade(); body = self.access.snapshot()["body"]; body.pop("authentication")
        p = self.access.state.propose(body)
        with patch.object(windows, "_native_verify") as native:
            with self.assertRaises(ContextError): self.access.accept(self.actor, p, p["preview_sha256"], now=100)
            native.assert_not_called()

    def test_local_stop_during_verification_prevents_commit_and_needs_no_prompt(self):
        self.upgrade(); before = self.access.snapshot(); p = self.prepared()
        def interrupted(scope): self.access.stop_local(); return "verified"
        with patch.object(windows, "_native_verify", side_effect=interrupted):
            with self.assertRaises(ContextError): self.access.accept(self.actor, p, p["preview_sha256"], now=100)
        self.assertEqual(self.access.snapshot(), before)
        with patch.object(windows, "_native_verify") as native:
            self.access.stop_local(); native.assert_not_called()

    def test_revision_drift_during_verification_does_not_rebase_the_selected_action(self):
        self.upgrade(); p = self.prepared()
        def drift(scope):
            body = self.access.snapshot()["body"]; body["devices"][0]["online"] = False
            changed = self.access.state.propose(body)
            self.access.state.commit(changed, changed["preview_sha256"])
            return "verified"
        with patch.object(windows, "_native_verify", side_effect=drift):
            with self.assertRaises(ContextError): self.access.accept(self.actor, p, p["preview_sha256"], now=100)
        self.assertEqual(len(self.access.snapshot()["body"]["devices"]), 1)

    def test_expiry_is_rechecked_after_interactive_wait(self):
        self.upgrade(); p = self.prepared()
        # Before proof, proof issue, proof consume, after proof: simulate a wait
        # crossing the enrollment's expiry without sleeping or opening a UI.
        with patch.object(windows, "_native_verify", return_value="verified"), patch("time.monotonic", side_effect=[0, 4000, 4000, 4000]):
            with self.assertRaises(ContextError): self.access.accept(self.actor, p, p["preview_sha256"], now=100)
        self.assertEqual(len(self.access.snapshot()["body"]["devices"]), 1)

    def test_resume_requires_fresh_verification_and_preserves_stop_on_cancel(self):
        self.upgrade(); stop = self.access.stop_local()
        with patch.object(windows, "_native_verify", return_value="canceled"):
            with self.assertRaises(ContextError): self.access.resume_local(self.actor, stop["stop_sha256"], now=100)
        self.assertTrue((self.access.state.root/"LOCAL-STOP.json").exists())
        with patch.object(windows, "_native_verify", return_value="verified"):
            self.access.resume_local(self.actor, stop["stop_sha256"], now=100)
        self.assertFalse((self.access.state.root/"LOCAL-STOP.json").exists())

    def test_proof_is_single_use_and_bound_to_scope_account_and_time(self):
        with patch.object(windows, "_native_verify", return_value="verified"):
            proof = windows.verify("a"*64)
        with self.assertRaises(ContextError): proof.consume("b"*64)
        proof.consume("a"*64)
        with self.assertRaises(ContextError): proof.consume("a"*64)
        for subject, issued in (("b"*64, windows.time.monotonic()), (principal(), windows.time.monotonic()-61), (principal(), windows.time.monotonic()+60)):
            with self.assertRaises(ContextError): windows._Verified("a"*64, subject, issued).consume("a"*64)

    def test_local_root_actor_and_exact_content_change_operation_binding(self):
        scope = windows.operation_scope(self.root/"access", "commit", {"actor": "one", "revision": "a"*64})
        for root, purpose, content in ((self.root/"other", "commit", {"actor": "one", "revision": "a"*64}),
                                       (self.root/"access", "resume", {"actor": "one", "revision": "a"*64}),
                                       (self.root/"access", "commit", {"actor": "two", "revision": "a"*64}),
                                       (self.root/"access", "commit", {"actor": "one", "revision": "b"*64})):
            self.assertNotEqual(scope, windows.operation_scope(root, purpose, content))

    def test_unknown_authentication_mode_is_refused(self):
        body = self.access.snapshot()["body"]; body["authentication"] = "imported_token"
        with self.assertRaises(ContextError): validate_access(body)

    def test_unknown_credential_or_authentication_receipt_fields_cannot_be_persisted(self):
        before = self.access.snapshot()
        for location in ("body", "accounts", "devices", "memberships"):
            body = deepcopy(before["body"])
            target = body if location == "body" else body[location][0]
            target["imported_sign_in"] = "synthetic-secret-sentinel"
            p = self.access.state.propose(body)
            with self.assertRaises(ContextError): self.access.accept(self.actor, p, p["preview_sha256"], now=100)
        self.assertEqual(self.access.snapshot(), before)

    def test_cli_exposes_headless_probe_and_explicit_windows_creation(self):
        result = subprocess.run([sys.executable, "-B", str(SCRIPTS/"GameToolManagedWorkspace.py"), "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0); self.assertIn("access-windows-create", result.stdout); self.assertIn("windows-account-status", result.stdout)

    def test_async_bridge_reads_result_and_releases_both_owned_interfaces(self):
        runtime, events = self.fake_runtime(status=1, value=6)
        self.assertEqual(runtime.wait(c.c_void_p(1), timeout=1), 6)
        self.assertIn("close", events); self.assertEqual(events.count("release"), 2)

    def test_async_bridge_cancel_timeout_and_failed_operation_never_produce_success(self):
        for status, timeout, pump in ((0, 1, lambda: False), (0, 0, lambda: True), (2, 1, lambda: True), (3, 1, lambda: True)):
            runtime, events = self.fake_runtime(status=status, value=0)
            with self.subTest(status=status, timeout=timeout), self.assertRaises(ContextError):
                runtime.wait(c.c_void_p(1), timeout=timeout, pump=pump)
            self.assertNotIn("result", events); self.assertEqual(events.count("release"), 2)
            if status == 0: self.assertIn("cancel", events)

    def test_wait_checks_closed_window_before_accepting_a_completed_result(self):
        runtime, events = self.fake_runtime(status=1, value=0)
        with self.assertRaises(ContextError): runtime.wait(c.c_void_p(1), timeout=1, pump=lambda: False)
        self.assertNotIn("result", events)

    @staticmethod
    def fake_runtime(*, status, value):
        runtime, events = object.__new__(windows._Runtime), []
        def call(pointer, slot, *types):
            def invoke(pointer, *args):
                if slot == 0: args[1]._obj.value = 2
                elif slot == 7: args[0]._obj.value = status
                elif slot == 8: events.append("result"); args[0]._obj.value = value
                elif slot == 9: events.append("cancel")
                elif slot == 10: events.append("close")
                return 0
            return invoke
        runtime.call = call; runtime.release = lambda pointer: events.append("release")
        return runtime, events


if __name__ == "__main__": unittest.main(verbosity=2)
