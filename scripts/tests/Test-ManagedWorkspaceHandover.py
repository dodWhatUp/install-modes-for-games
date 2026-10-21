"""Local quiescence contracts; no physical eject or Windows prompt is simulated as acceptance."""
from copy import deepcopy
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
import json
from pathlib import Path
import runpy
import subprocess
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SCRIPTS))
ns = runpy.run_path(str(SCRIPTS / "tests/Test-ManagedWorkspaceExchange.py"))
Fixture, produce, carrier, receive, snapshot, REFUSED = (ns[k] for k in ("Fixture", "produce", "carrier", "receive", "snapshot", "REFUSED"))
from game_system_control.checkpoints import CheckpointService
from game_system_control.vault import VaultRegistry
from game_mod_ops.safety import ModError


class HandoverTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.f.service.registry.observer = self.observe
        self.p, self.sent = produce(self.f, "full")

    def tearDown(self): self.f.close()

    def observe(self, path):
        volume = "explicit-fixture-volume" if Path(path) == self.f.root / "vault" else "explicit-local-authority-volume"
        return {"volume_id": volume, "system_volume": False, "adapter": "synthetic-only"}

    def preview(self, op="out"):
        return self.f.service.preview_handover("checkpoint-full", op, self.sent["package_id"])

    def prepare(self, op="out", observer=None):
        p = self.preview(op)
        return self.f.service.prepare_handover(p, p["plan_sha256"], observer=observer)

    def test_pure_preview_then_stop_with_no_physical_release_claim(self):
        before = snapshot(self.f.root); plan = self.preview()
        self.assertEqual(before, snapshot(self.f.root))
        data_before = snapshot(self.f.root / "vault")
        result = self.f.service.prepare_handover(plan, plan["plan_sha256"])
        self.assertEqual(result["state"], "LOCAL_ACCESS_STOPPED")
        self.assertFalse(result["physical_transfer_ready"]); self.assertFalse(result["all_writers_released"])
        self.assertEqual(data_before, snapshot(self.f.root / "vault"))
        self.assertTrue((self.f.root / "access/LOCAL-STOP.json").exists())
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_ACCESS_STOPPED")
        with self.assertRaises(REFUSED): self.f.preview("later")

    def test_saved_file_drift_before_preview_and_after_preview(self):
        plan = self.preview(); (self.f.project / "source/numbers.json").write_bytes(b"new saved work")
        with self.assertRaises(REFUSED): self.preview()
        with self.assertRaises(REFUSED): self.f.service.prepare_handover(plan, plan["plan_sha256"])
        self.assertFalse((self.f.root / "access/LOCAL-STOP.json").exists())
        self.assertFalse((self.f.root / "access/audit/handover-out").exists())

    def test_revision_drift_expiry_stop_and_exact_digest_refuse(self):
        for mode in ("digest", "expiry", "stop", "revision"):
            with self.subTest(mode=mode):
                p = self.preview(mode)
                if mode == "expiry": self.f.now += 301
                if mode == "stop": self.f.access.stop_local()
                if mode == "revision": self.f.change("heartbeat", {"device_id": self.f.actor["device_id"], "online": True})
                with self.assertRaises(REFUSED): self.f.service.prepare_handover(p, "0" * 64 if mode == "digest" else p["plan_sha256"])
                self.assertFalse((self.f.root / ("access/audit/handover-" + mode)).exists())
                if mode == "expiry": self.f.now -= 301
                if mode == "stop": self.f.access.resume_local(self.f.admin, self.f.access.stop_local()["stop_sha256"], now=self.f.now)

    def test_requires_off_volume_stores_and_local_admin(self):
        with patch.object(self.f.service.registry, "observer", return_value=self.observe(self.f.root / "vault")):
            with self.assertRaises(REFUSED): self.preview()
        self.f.change("membership", {"account_id": self.f.actor["account_id"], "project_id": self.f.actor["project_id"], "roles": ["contributor"]})
        with self.assertRaises(REFUSED): self.preview()

    def test_delta_uses_exact_parents_and_v1_is_not_a_handover_receipt(self):
        _, child = produce(self.f, "delta", "checkpoint-full", representation="delta")
        with self.assertRaises(REFUSED): self.f.service.preview_handover("checkpoint-delta", "d", child["package_id"])
        p = self.f.service.preview_handover("checkpoint-delta", "d", child["package_id"], parent_sources=["checkpoint-full"])
        self.assertEqual(self.f.service.prepare_handover(p, p["plan_sha256"])["state"], "LOCAL_ACCESS_STOPPED")
        self.f.access.resume_local(self.f.admin, self.f.access.stop_local()["stop_sha256"], now=self.f.now)
        _, seed = self.f.publish()
        with self.assertRaises(REFUSED): self.f.service.preview_handover("checkpoint-seed", "seed", seed["package_id"])

    def test_interruption_after_stop_preserves_stop_and_attempt_and_never_replays(self):
        p = self.preview()
        def fail(phase):
            if phase == "local_access_stopped": raise OSError("fixture receipt loss")
        with self.assertRaises(OSError): self.f.service.prepare_handover(p, p["plan_sha256"], observer=fail)
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_ACCESS_STOPPED_RECEIPT_PENDING")
        before = snapshot(self.f.root)
        with self.assertRaises(REFUSED): self.f.service.prepare_handover(p, p["plan_sha256"])
        self.assertEqual(before, snapshot(self.f.root))

    def test_before_stop_interruption_preserves_source_and_reports_no_stop(self):
        before = snapshot(self.f.root / "vault")
        def fail(phase):
            if phase == "handover_verified": raise OSError("fixture before stop")
        with self.assertRaises(OSError): self.prepare(observer=fail)
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_STOP_NOT_PRESENT")
        self.assertEqual(before, snapshot(self.f.root / "vault"))
        with self.assertRaises(REFUSED): self.preview()

    def test_late_source_change_is_rechecked_before_stop(self):
        def change(phase):
            if phase == "handover_verified": (self.f.project / "source/lookup.txt").write_bytes(b"later.txt")
        with self.assertRaises(REFUSED): self.prepare(observer=change)
        self.assertFalse((self.f.root / "access/LOCAL-STOP.json").exists())

    def test_cancelled_or_torn_audit_cannot_be_reported_complete(self):
        def fail(phase):
            if phase == "handover_receipt_written": raise OSError("fixture lost terminal event")
        with self.assertRaises(OSError): self.prepare(observer=fail)
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_ACCESS_STOPPED_RECEIPT_PENDING")
        (self.f.root / "access/audit/handover-out/INTENT.json").write_bytes(b"{")
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "HANDOVER_UNCERTAIN")

    def test_inspection_reads_only_local_evidence_after_volume_removal(self):
        self.prepare()
        with patch.object(self.f.service.registry, "observer", side_effect=OSError("volume absent")), patch.object(self.f.service, "_target", side_effect=AssertionError("must not access volume")):
            self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_ACCESS_STOPPED")

    def test_resume_and_new_stop_do_not_reuse_old_quiescence_evidence(self):
        self.prepare()
        self.f.access.resume_local(self.f.admin, self.f.access.stop_local()["stop_sha256"], now=self.f.now)
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_STOP_NOT_PRESENT")
        self.f.access.stop_local()
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_STOP_REPLACED")

    def test_unknown_lock_is_preserved_and_no_stop_is_inferred(self):
        p = self.preview(); lock = self.f.root / "access/.workspace-state.lock"; lock.write_bytes(b"unknown owner")
        with self.assertRaises(ModError): self.f.service.prepare_handover(p, p["plan_sha256"])
        self.assertEqual(lock.read_bytes(), b"unknown owner")
        self.assertFalse((self.f.root / "access/LOCAL-STOP.json").exists())

    def test_forced_child_exit_after_stop_keeps_unknown_locks_for_read_only_inspection(self):
        p = self.preview(); request = self.f.root / "child-plan.json"; request.write_text(json.dumps(p))
        code = """import sys,os,json,runpy
from pathlib import Path
ns=runpy.run_path(sys.argv[1]); scope=ns['identity_fixture'](); root=Path(sys.argv[2]); s=ns['reopen'](root)
s.registry.observer=lambda path: {'volume_id':'explicit-fixture-volume' if Path(path)==root/'vault' else 'explicit-local-authority-volume','system_volume':False,'adapter':'synthetic-only'}
p=json.loads(Path(sys.argv[3]).read_text())
s.prepare_handover(p,p['plan_sha256'],observer=lambda phase: os._exit(17) if phase=='local_access_stopped' else None)
"""
        result = subprocess.run([sys.executable, "-B", "-c", code, str(SCRIPTS / "tests/Test-ManagedWorkspaceCheckpoints.py"), str(self.f.root), str(request)], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 17, result.stderr)
        locks = [self.f.root / store / ".workspace-state.lock" for store in ("access", "policy", "bindings")]
        before = [p.read_bytes() for p in locks]
        self.assertEqual(self.f.service.inspect_handover("out")["state"], "LOCAL_ACCESS_STOPPED_RECEIPT_PENDING")
        self.assertEqual(before, [p.read_bytes() for p in locks])
        self.assertTrue((self.f.root / "access/LOCAL-STOP.json").exists())

    def test_receipt_pending_payload_can_be_reverified_in_fresh_receive_without_repair(self):
        carrier(self.f, "checkpoint-full", self.f, "incoming")
        p = self.f.service.preview_receive("incoming", "checkpoint-lost", "lost", self.sent["package_id"])
        def fail(phase):
            if phase == "publication_written": raise OSError("fixture lost terminal receipt")
        with self.assertRaises(OSError): self.f.service.receive(p, p["plan_sha256"], observer=fail)
        before = snapshot(self.f.outputs / "checkpoint-lost")
        self.assertEqual(self.f.service.inspect("checkpoint-lost")["state"], "PUBLISHED_RECEIPT_PENDING")
        fresh = receive(self.f, "checkpoint-lost", "fresh", self.sent["package_id"])
        self.assertTrue(fresh["received"]); self.assertFalse(fresh["adopted"])
        self.assertEqual(self.f.service.inspect("checkpoint-fresh")["state"], "PUBLISHED")
        self.assertEqual(before, snapshot(self.f.outputs / "checkpoint-lost"))

    def test_cli_handover_modes_use_same_service_and_private_plan(self):
        import GameToolManagedWorkspace as cli
        def call(mode, payload, *extra):
            path = self.f.root / "request.json"; path.write_text(json.dumps({"actor": self.f.actor, **payload}))
            args = [mode, "--state", str(self.f.root / "bindings"), "--policy-state", str(self.f.root / "policy"), "--access-state", str(self.f.root / "access"), "--vault-id", self.f.vault_id, "--input", str(path), *extra]
            out, err = StringIO(), StringIO()
            def factory(registry, policy, access, actor, vault_id): return CheckpointService(registry, policy, access, actor, vault_id, clock=lambda: self.f.now)
            with patch.object(cli, "VaultRegistry", side_effect=lambda p: VaultRegistry(p, self.observe)), patch("game_system_control.checkpoints.CheckpointService", side_effect=factory), redirect_stdout(out), redirect_stderr(err): code = cli.main(args)
            self.assertEqual(code, 0, err.getvalue()); return json.loads(out.getvalue())
        p = call("checkpoint-handover-preview", {"source": "checkpoint-full", "operation_id": "cli", "package_id": self.sent["package_id"]})
        self.assertEqual(call("checkpoint-handover-prepare", {"plan": p}, "--accept", p["plan_sha256"])["state"], "LOCAL_ACCESS_STOPPED")
        self.assertEqual(call("checkpoint-handover-inspect", {"operation_id": "cli"})["state"], "LOCAL_ACCESS_STOPPED")


if __name__ == "__main__": unittest.main(verbosity=2)
