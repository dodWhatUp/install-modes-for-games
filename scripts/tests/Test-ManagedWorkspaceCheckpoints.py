"""MCI-08 synthetic tests. Identity/volume are explicitly mocked, not enrolled.

All data belongs to new temporary fixtures. No native OS/Codex/client acceptance
is implied. Child-process crash tests exit only the child created by this suite.
"""
from contextlib import ExitStack
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import GameToolUserData as io
from game_system_control import workspace_state, access as access_module
from game_system_control.access import AccessStore
from game_system_control.policy import PolicyStore
from game_system_control.vault import VaultRegistry, CLASSES
from game_system_control.checkpoints import CheckpointService, validate_package, _package
from game_system_control.contracts import ContextError
from GameToolAIContracts import stable_revision

ACTOR = {"account_id": "fixture-account", "workspace_id": "fixture-workspace", "project_id": "fixture-project", "device_id": "fixture-device", "generation": 1}
REFUSED = (ContextError, io.UserDataError, OSError, ValueError)


def observe(_):
    return {"volume_id": "explicit-fixture-volume", "system_volume": False, "adapter": "synthetic-only"}


def identity_fixture():
    stack = ExitStack()
    stack.enter_context(patch.object(workspace_state, "principal", return_value="a" * 64))
    stack.enter_context(patch.object(access_module, "principal", return_value="a" * 64))
    return stack


def reopen(root, clock=lambda: 100.0):
    registry = VaultRegistry(root / "bindings", observe)
    vault_id = registry.state.snapshot()["body"]["vaults"][0]["marker"]["vault_id"]
    return CheckpointService(registry, PolicyStore(root / "policy"), AccessStore(root / "access"), ACTOR, vault_id, clock=clock)


class Fixture:
    def __init__(self, actor=None):
        self.actor = deepcopy(ACTOR if actor is None else actor)
        self.temp = tempfile.TemporaryDirectory(prefix="checkpoint-fixture-")
        self.root = Path(self.temp.name).resolve()
        self.identities = identity_fixture()
        self.now = 100.0
        registry = VaultRegistry.create(self.root / "bindings", observe)
        registry.enroll(self.root / "vault", self.actor["workspace_id"], registry.state.snapshot()["revision"])
        self.vault_id = registry.state.snapshot()["body"]["vaults"][0]["marker"]["vault_id"]
        self.policy = PolicyStore.create(self.root / "policy")
        self.rule = {"id": "fixture-local", "scope": {"account_id": self.actor["account_id"], "workspace_id": self.actor["workspace_id"], "project_id": self.actor["project_id"], "source_device": self.actor["device_id"], "destination_device": self.actor["device_id"], "capability": "*", "content_class": "*"}, "origin": "destination", "enabled": True, "controls": {"transfer": True, "adoption": True, "index": False, "context": False}, "context_depth": "none", "trigger": {"kind": "manual"}}
        p = self.policy.propose_rule(self.rule); self.policy.accept(p, p["preview_sha256"])
        self.access = AccessStore.create(self.root / "access", self.actor["account_id"], self.actor["device_id"], self.actor["project_id"], workspace_id=self.actor["workspace_id"], now=self.now)
        self.admin = {**self.actor, "capability": "enrollment.manage"}
        self.change("membership", {"account_id": self.actor["account_id"], "project_id": self.actor["project_id"], "roles": ["policy_administrator", "contributor"]})
        self.change("storage", {"account_id": self.actor["account_id"], "project_id": self.actor["project_id"], "storage_id": self.vault_id, "read": sorted(CLASSES), "write": sorted(CLASSES)})
        rev = stable_revision(self.policy.snapshot()["body"])
        self.change("pin_policy", {"policy_revision": rev})
        self.change("acknowledge", {"device_id": self.actor["device_id"], "policy_revision": rev})
        self.service = CheckpointService(registry, self.policy, self.access, self.actor, self.vault_id, clock=lambda: self.now)
        self.project = self.root / "vault" / "projects" / self.actor["project_id"]
        for name in CLASSES.values(): (self.project / name).mkdir(parents=True)
        content = {("project_source", "lookup.txt"): b"numbers.json\n", ("project_source", "numbers.json"): b'{"numbers":[2,3],"sum":5}', ("selected_assets", "asset.bin"): bytes(range(256)), ("selected_results", "report.txt"): b"Synthetic result only\n", ("continuation_packet", "next.txt"): "Selected synthetic context שלום\n".encode()}
        self.selection = []
        for (cls, relative), body in content.items():
            (self.project / CLASSES[cls] / relative).write_bytes(body)
            self.selection.append({"content_class": cls, "relative": relative})
        self.outputs = self.project / "outputs"

    def change(self, action, values):
        p = self.access.propose_change(self.admin, action, values, now=self.now)
        return self.access.accept(self.admin, p, p["preview_sha256"], now=self.now)

    def preview(self, op="seed", selections=None):
        return self.service.preview_seed(self.selection if selections is None else selections, "checkpoint-" + op, op)

    def publish(self, op="seed"):
        p = self.preview(op)
        return p, self.service.publish_seed(p, p["plan_sha256"])

    def reconstruct_preview(self, op="restore"):
        return self.service.preview_reconstruction("checkpoint-seed", "reconstruction-" + op, op, self.service.inspect("checkpoint-seed")["package_id"])

    def close(self):
        self.identities.close()
        self.temp.cleanup()


def snapshot(root):
    return {str(p.relative_to(root)): io.digest(p.read_bytes()) if p.is_file() else "directory" for p in root.rglob("*")}


class CheckpointTests(unittest.TestCase):
    def setUp(self): self.f = Fixture()
    def tearDown(self): self.f.close()

    def test_preview_is_read_only_including_stores_locks_and_journal(self):
        before = snapshot(self.f.root); plan = self.f.preview()
        self.assertEqual(before, snapshot(self.f.root))
        self.assertEqual(plan["effects"], ["write_new_checkpoint_only"])
        self.assertEqual(plan["package"]["checkpoint"]["core"]["coverage"]["unsaved_work"], "not_observed")

    def test_all_four_content_classes_publish_verify_and_reopen(self):
        plan, result = self.f.publish()
        self.assertEqual(result["state"], "PUBLISHED")
        self.assertEqual(reopen(self.f.root).inspect("checkpoint-seed")["state"], "PUBLISHED")
        self.assertEqual(len(plan["package"]["checkpoint"]["core"]["files"]), 5)
        self.assertFalse(result["adopted"])

    def test_source_drift_after_preview_refused_before_destination_creation(self):
        p = self.f.preview(); (self.f.project / "source/numbers.json").write_bytes(b"changed")
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-seed").exists())

    def test_selected_coverage_does_not_turn_unselected_files_into_deletions(self):
        p = self.f.preview(); (self.f.project / "source/unselected.txt").write_bytes(b"not selected")
        result = self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertEqual(result["files"], 5)
        self.assertEqual(p["package"]["checkpoint"]["core"]["tombstones"], [])
        self.assertEqual(p["package"]["checkpoint"]["core"]["coverage"]["unselected_files"], "not_captured")

    def test_changed_plan_and_wrong_acceptance_digest_are_refused(self):
        p = self.f.preview()
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, "0" * 64)
        p["package"]["checkpoint"]["core"]["files"][0]["bytes"] += 1
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-seed").exists())

    def test_existing_attempt_is_never_overwritten_or_replayed(self):
        p, _ = self.f.publish(); before = snapshot(self.f.outputs / "checkpoint-seed")
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertEqual(before, snapshot(self.f.outputs / "checkpoint-seed"))
        self.assertEqual(self.f.service.inspect("checkpoint-seed")["state"], "PUBLISHED")

    def test_operation_target_is_canonical_without_a_second_operation_registry(self):
        with self.assertRaises(REFUSED): self.f.service.preview_seed(self.f.selection, "another-target", "seed")
        self.assertFalse((self.f.outputs / "another-target").exists())

    def test_exact_local_revisions_cannot_be_disabled_in_an_accepted_plan(self):
        for vector in (None, {}, {"access": "0" * 64}):
            p = self.f.preview(); p["expected_state"] = vector
            p = self.f.service._plan({k: v for k, v in p.items() if k != "plan_sha256"})
            with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-seed").exists())

    def test_stream_accepts_distinct_path_and_handle_ctime_but_detects_handle_drift(self):
        from types import SimpleNamespace
        original = io.os.fstat
        changed = [False]
        def observed(fd):
            s = original(fd)
            return SimpleNamespace(**{k: getattr(s, k) for k in ("st_dev", "st_ino", "st_size", "st_mtime_ns")},
                                   st_ctime_ns=s.st_ctime_ns + 100 + int(changed[0]))
        file = self.f.project / "source/lookup.txt"
        with patch.object(io.os, "fstat", side_effect=observed):
            self.assertEqual(io.stream_fingerprint(file)["sha256"], io.digest(file.read_bytes()))
            with self.assertRaises(REFUSED):
                io.stream_fingerprint(file, before_chunk=lambda: changed.__setitem__(0, True))

    def test_checkpoint_identity_is_independent_of_attempt_identity(self):
        a = self.f.preview("one"); b = self.f.preview("two")
        self.assertEqual(a["package"], b["package"])
        self.assertNotEqual(a["plan_sha256"], b["plan_sha256"])

    def test_exact_byte_identical_files_share_one_object(self):
        (self.f.project / "source/twin.txt").write_bytes((self.f.project / "source/lookup.txt").read_bytes())
        self.f.selection.append({"content_class": "project_source", "relative": "twin.txt"})
        p, _ = self.f.publish()
        self.assertEqual(len(list((self.f.outputs / "checkpoint-seed/objects").iterdir())), len(p["package"]["checkpoint"]["core"]["files"]) - 1)

    def test_privacy_projection_has_no_local_roots_principal_or_grants(self):
        p, _ = self.f.publish()
        raw = (self.f.outputs / "checkpoint-seed/MANIFEST.json").read_text()
        for forbidden in (str(self.f.root), "owner_principal", "subject_hash", "storage_permissions", "source_path", "a" * 64): self.assertNotIn(forbidden, raw)
        self.assertNotIn("actor", p["package"])

    def test_access_revision_drift_refuses_prepared_publication(self):
        p = self.f.preview(); self.f.change("heartbeat", {"device_id": ACTOR["device_id"], "online": True})
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-seed").exists())

    def test_policy_revision_drift_refuses_prepared_publication(self):
        p = self.f.preview(); rule = deepcopy(self.f.rule); rule["trigger"] = {"kind": "checkpoint"}
        edit = self.f.policy.propose_rule(rule); self.f.policy.accept(edit, edit["preview_sha256"])
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-seed").exists())

    def test_binding_revision_drift_refuses_prepared_publication(self):
        p = self.f.preview(); state = self.f.service.registry.state
        edit = state.propose({**state.snapshot()["body"], "fixture_note": True}); state.commit(edit, edit["preview_sha256"])
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])

    def test_stop_before_publication_creates_no_attempt(self):
        p = self.f.preview(); self.f.access.stop_local()
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-seed").exists())

    def test_stop_during_payload_copy_preserves_partial_and_prevents_commit(self):
        p = self.f.preview()
        def stop(phase):
            if phase == "object_written": self.f.access.stop_local()
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"], observer=stop)
        root = self.f.outputs / "checkpoint-seed"
        self.assertTrue((root / "_ATTEMPT.json").exists()); self.assertFalse((root / "_PUBLISHED.json").exists())
        marker = self.f.access.stop_local(); self.f.access.resume_local(self.f.admin, marker["stop_sha256"], now=100)
        self.assertEqual(self.f.service.inspect("checkpoint-seed")["state"], "STAGING_INCOMPLETE")

    def test_expiry_during_staging_is_not_automatically_renewed(self):
        p = self.f.preview()
        def expire(phase):
            if phase == "object_written": self.f.now = 3700.0
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"], observer=expire)
        self.assertFalse((self.f.outputs / "checkpoint-seed/_PUBLISHED.json").exists())
        self.assertEqual(self.f.access.state.snapshot()["body"]["devices"][0]["expires_at"], 3700)

    def test_source_drift_during_staging_leaves_verified_candidate_unpublished(self):
        p = self.f.preview()
        def drift(phase):
            if phase == "payload_verified": (self.f.project / "source/numbers.json").write_bytes(b"newer work")
        with self.assertRaises(REFUSED): self.f.service.publish_seed(p, p["plan_sha256"], observer=drift)
        self.assertEqual(self.f.service.inspect("checkpoint-seed")["state"], "VERIFIED_NOT_PUBLISHED")

    def test_error_after_commit_marker_is_visible_as_pending_receipt(self):
        p = self.f.preview()
        def fail(phase):
            if phase == "publication_written": raise OSError("injected lost terminal receipt")
        with self.assertRaises(OSError): self.f.service.publish_seed(p, p["plan_sha256"], observer=fail)
        result = self.f.service.inspect("checkpoint-seed")
        self.assertEqual(result["state"], "PUBLISHED_RECEIPT_PENDING"); self.assertFalse(result["automatic_retry"])
        with self.assertRaises(REFUSED): self.f.service.preview_reconstruction("checkpoint-seed", "reconstruction-r", "r", result["package_id"])

    def test_injected_disk_full_retains_attempt_without_false_publication(self):
        p = self.f.preview()
        with patch("game_system_control.checkpoints.copy_stream_new", side_effect=OSError(28, "synthetic disk full")):
            with self.assertRaises(OSError): self.f.service.publish_seed(p, p["plan_sha256"])
        self.assertEqual(self.f.service.inspect("checkpoint-seed")["state"], "STAGING_INCOMPLETE")

    def test_corrupt_payload_is_refused_without_repair(self):
        _, _ = self.f.publish(); path = next((self.f.outputs / "checkpoint-seed/objects").iterdir()); path.write_bytes(b"corrupt")
        before = snapshot(self.f.outputs / "checkpoint-seed")
        with self.assertRaises(REFUSED): self.f.service.inspect("checkpoint-seed")
        self.assertEqual(before, snapshot(self.f.outputs / "checkpoint-seed"))

    def test_unknown_extra_payload_is_not_silently_ignored(self):
        self.f.publish(); (self.f.outputs / "checkpoint-seed/objects/unlisted").write_bytes(b"extra")
        with self.assertRaises(REFUSED): self.f.service.inspect("checkpoint-seed")

    def test_new_copy_reconstruction_is_functionally_readable_without_execution(self):
        self.f.publish(); p = self.f.reconstruct_preview(); before = snapshot(self.f.root / "access")
        result = self.f.service.reconstruct(p, p["plan_sha256"])
        source = self.f.outputs / "reconstruction-restore/data/source"
        referred = (source / "lookup.txt").read_text().strip()
        data = json.loads((source / referred).read_text())
        self.assertEqual(sum(data["numbers"]), data["sum"])
        self.assertEqual(result["state"], "RECONSTRUCTED_INACTIVE")
        self.assertEqual(self.f.service.inspect_reconstruction("reconstruction-restore")["state"], "RECONSTRUCTED_INACTIVE")
        self.assertEqual(before, snapshot(self.f.root / "access"))
        self.assertFalse(result["active_adoption"]); self.assertFalse(result["indexed"]); self.assertFalse(result["context_exposed"])

    def test_reconstruction_never_overwrites_an_existing_destination(self):
        self.f.publish(); p = self.f.reconstruct_preview(); root = self.f.outputs / "reconstruction-restore"; root.mkdir(); (root / "keep.txt").write_bytes(b"later work")
        with self.assertRaises(REFUSED): self.f.service.reconstruct(p, p["plan_sha256"])
        self.assertEqual((root / "keep.txt").read_bytes(), b"later work")

    def test_reconstruction_requires_logical_content_class_write_grant(self):
        self.f.publish()
        self.f.change("storage", {"account_id": ACTOR["account_id"], "project_id": ACTOR["project_id"], "storage_id": self.f.vault_id, "read": sorted(CLASSES), "write": ["selected_results"]})
        with self.assertRaises(REFUSED): self.f.reconstruct_preview()
        self.assertFalse((self.f.outputs / "reconstruction-restore").exists())

    def test_reconstruction_stop_is_checked_between_files(self):
        self.f.publish(); p = self.f.reconstruct_preview()
        def stop(phase):
            if phase == "file_reconstructed": self.f.access.stop_local()
        with self.assertRaises(REFUSED): self.f.service.reconstruct(p, p["plan_sha256"], observer=stop)
        root = self.f.outputs / "reconstruction-restore"
        self.assertFalse((root / "_COMPLETE.json").exists())
        marker = self.f.access.stop_local(); self.f.access.resume_local(self.f.admin, marker["stop_sha256"], now=100)
        result = self.f.service.inspect_reconstruction("reconstruction-restore")
        self.assertEqual(result["state"], "RECONSTRUCTION_INCOMPLETE"); self.assertTrue(result["missing"])

    def test_reconstructed_external_change_is_checked_before_completion(self):
        self.f.publish(); p = self.f.reconstruct_preview()
        root = self.f.outputs / "reconstruction-restore"
        def mutate(phase):
            if phase == "file_reconstructed":
                path = root / "data/continuation/next.txt"
                if path.exists(): path.write_bytes(b"newer external edit")
        with self.assertRaises(REFUSED): self.f.service.reconstruct(p, p["plan_sha256"], observer=mutate)
        self.assertFalse((root / "_COMPLETE.json").exists())
        self.assertEqual((root / "data/continuation/next.txt").read_bytes(), b"newer external edit")

    def test_receipt_loss_after_reconstruction_keeps_bytes_and_pending_evidence(self):
        self.f.publish(); p = self.f.reconstruct_preview()
        def fail(phase):
            if phase == "reconstruction_complete_written": raise OSError("injected receipt loss")
        with self.assertRaises(OSError): self.f.service.reconstruct(p, p["plan_sha256"], observer=fail)
        self.assertEqual(self.f.service.inspect_reconstruction("reconstruction-restore")["state"], "RECONSTRUCTED_RECEIPT_PENDING")

    def test_oversized_source_is_refused_before_reading_or_writing_payload(self):
        path = self.f.project / "source/large.bin"
        with path.open("wb") as f: f.truncate(io.MAX_FILE_BYTES + 1)
        with self.assertRaises(REFUSED): self.f.preview(selections=[{"content_class": "project_source", "relative": "large.bin"}])
        self.assertFalse((self.f.outputs / "checkpoint-seed").exists())

    def test_symlink_source_is_refused(self):
        link = self.f.project / "source/link.txt"
        try: link.symlink_to(self.f.project / "source/lookup.txt")
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314: self.skipTest("Windows account cannot create a symlink fixture (WinError 1314).")
            raise
        with self.assertRaises(REFUSED): self.f.preview(selections=[{"content_class": "project_source", "relative": "link.txt"}])

    def test_streaming_reads_do_not_request_whole_file_buffers(self):
        path = self.f.project / "source/large.bin"; path.write_bytes(b"z" * (3 * io.STREAM_BUFFER_BYTES + 7))
        real_open, sizes = Path.open, []
        class Capped:
            def __init__(self, f): self.f = f
            def __getattr__(self, key): return getattr(self.f, key)
            def __enter__(self): self.f.__enter__(); return self
            def __exit__(self, *args): return self.f.__exit__(*args)
            def read(self, n=-1):
                if n < 0 or n > io.STREAM_BUFFER_BYTES: raise AssertionError("unbounded read")
                sizes.append(n); return self.f.read(n)
        def wrapped(p, *args, **kwargs):
            f = real_open(p, *args, **kwargs)
            return Capped(f) if args and args[0] == "rb" else f
        with patch.object(Path, "open", new=wrapped):
            fp = io.stream_fingerprint(path)
            io.copy_stream_new(path, self.f.root / "copied.bin", fp["sha256"], fp["bytes"])
        self.assertTrue(sizes); self.assertLessEqual(max(sizes), io.STREAM_BUFFER_BYTES)
        self.assertEqual((self.f.root / "copied.bin").read_bytes(), path.read_bytes())

    def test_killed_child_after_payload_verification_leaves_unpublished_checkpoint(self):
        self._child_crash("payload_verified", "VERIFIED_NOT_PUBLISHED")

    def test_killed_child_after_publication_does_not_replay_or_claim_terminal_receipt(self):
        self._child_crash("publication_written", "PUBLISHED_RECEIPT_PENDING")

    def _child_crash(self, phase, expected_state):
        p = self.f.preview(); path = self.f.root / "private-plan.json"; path.write_text(json.dumps(p))
        code = "import sys,os,runpy,json;from pathlib import Path;ns=runpy.run_path(sys.argv[1]);scope=ns['identity_fixture']();s=ns['reopen'](Path(sys.argv[2]));p=json.loads(Path(sys.argv[3]).read_text());s.publish_seed(p,p['plan_sha256'],observer=lambda phase: os._exit(17) if phase==sys.argv[4] else None)"
        result = subprocess.run([sys.executable, "-B", "-c", code, str(Path(__file__).resolve()), str(self.f.root), str(path), phase], capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(self.f.service.inspect("checkpoint-seed")["state"], expected_state)
        self.assertTrue((self.f.root / "access/.workspace-state.lock").exists())
        self.assertFalse(self.f.service.inspect("checkpoint-seed")["automatic_retry"])



    def test_per_class_read_revocation_blocks_payload_inspection(self):
        self.f.publish()
        self.f.change("storage", {"account_id": ACTOR["account_id"], "project_id": ACTOR["project_id"], "storage_id": self.f.vault_id, "read": ["selected_results"], "write": sorted(CLASSES)})
        with patch("game_system_control.checkpoints.stream_fingerprint", wraps=io.stream_fingerprint) as read:
            with self.assertRaises(REFUSED): self.f.service.inspect("checkpoint-seed")
            self.assertEqual(read.call_count, 0)

    def test_foreign_workspace_manifest_is_refused_before_payload_reads(self):
        package = deepcopy(self.f.preview()["package"])
        package["checkpoint"]["core"]["workspace_id"] = "other-workspace"
        package = _package(package["checkpoint"]["core"])
        root = self.f.outputs / "checkpoint-foreign"; root.mkdir()
        (root / "MANIFEST.json").write_bytes(io._canonical(package))
        with patch("game_system_control.checkpoints.stream_fingerprint", wraps=io.stream_fingerprint) as read:
            with self.assertRaises(REFUSED): self.f.service.inspect("checkpoint-foreign")
            self.assertEqual(read.call_count, 0)

    def test_stop_inside_a_multichunk_reconstruction_leaves_inspectable_partial_file(self):
        file = self.f.project / "assets/large.bin"; file.write_bytes(b"q" * (3 * io.STREAM_BUFFER_BYTES + 7))
        self.f.selection = [{"content_class": "selected_assets", "relative": "large.bin"}]
        self.f.publish(); p = self.f.reconstruct_preview()
        target = self.f.outputs / "reconstruction-restore/data/assets/large.bin"
        original = self.f.service._check
        def check(specs, expected=None):
            if target.exists() and target.stat().st_size >= io.STREAM_BUFFER_BYTES: self.f.access.stop_local()
            return original(specs, expected)
        with patch.object(self.f.service, "_check", side_effect=check):
            with self.assertRaises(REFUSED): self.f.service.reconstruct(p, p["plan_sha256"])
        self.assertGreater(target.stat().st_size, 0); self.assertLess(target.stat().st_size, file.stat().st_size)
        marker = self.f.access.stop_local(); self.f.access.resume_local(self.f.admin, marker["stop_sha256"], now=100)
        result = self.f.service.inspect_reconstruction("reconstruction-restore")
        self.assertEqual(result["state"], "RECONSTRUCTION_INCOMPLETE"); self.assertTrue(result["partial"])

    def test_reconstruction_receipt_cannot_claim_different_effects(self):
        self.f.publish(); p = self.f.reconstruct_preview(); self.f.service.reconstruct(p, p["plan_sha256"])
        file = self.f.outputs / "reconstruction-restore/_COMPLETE.json"
        receipt = json.loads(file.read_text()); receipt["active_adoption"] = True; file.write_text(json.dumps(receipt))
        with self.assertRaises(REFUSED): self.f.service.inspect_reconstruction("reconstruction-restore")

    def test_reconstruction_audit_requires_its_own_intent_and_success_terminal(self):
        from GameToolJournal import Journal
        self.f.publish(); p = self.f.reconstruct_preview(); receipt = self.f.service.reconstruct(p, p["plan_sha256"])
        root = self.f.outputs / "reconstruction-restore"
        # Replace only this fixture's journal with a valid unrelated audit.
        (root / "AUDIT.jsonl").unlink()
        with Journal.create(root / "AUDIT.jsonl", {"owner": "unrelated"}) as journal:
            journal.append("operation_result", receipt)
            journal.append("session_cancelled", {"reason": "fixture"})
        self.assertEqual(self.f.service.inspect_reconstruction("reconstruction-restore")["state"], "RECONSTRUCTED_RECEIPT_PENDING")

    def test_all_six_existing_cli_checkpoint_modes_use_guarded_synthetic_service(self):
        import GameToolManagedWorkspace as cli
        from contextlib import redirect_stdout, redirect_stderr
        from io import StringIO
        count = [0]
        real = CheckpointService
        def factory(registry, policy, access, actor, vault_id):
            return real(registry, policy, access, actor, vault_id, clock=lambda: self.f.now)
        def call(mode, fields, *extra):
            count[0] += 1; path = self.f.root / ("cli-request-" + str(count[0]) + ".json")
            path.write_text(json.dumps({"actor": ACTOR, **fields}))
            out, err = StringIO(), StringIO()
            args = [mode, "--state", str(self.f.root / "bindings"), "--policy-state", str(self.f.root / "policy"), "--access-state", str(self.f.root / "access"), "--vault-id", self.f.vault_id, "--input", str(path), *extra]
            with patch.object(cli, "VaultRegistry", side_effect=lambda p: VaultRegistry(p, observe)), patch("game_system_control.checkpoints.CheckpointService", side_effect=factory), redirect_stdout(out), redirect_stderr(err):
                code = cli.main(args)
            self.assertEqual(code, 0, err.getvalue())
            return json.loads(out.getvalue())
        plan = call("checkpoint-preview", {"selection": self.f.selection, "destination": "checkpoint-cli", "operation_id": "cli"})
        receipt = call("checkpoint-publish", {"plan": plan}, "--accept", plan["plan_sha256"])
        self.assertEqual(call("checkpoint-inspect", {}, "--relative", "checkpoint-cli")["state"], "PUBLISHED")
        restore = call("checkpoint-restore-preview", {"source": "checkpoint-cli", "destination": "reconstruction-cli", "operation_id": "cli", "package_id": receipt["package_id"]})
        call("checkpoint-restore", {"plan": restore}, "--accept", restore["plan_sha256"])
        self.assertEqual(call("checkpoint-inspect-restore", {}, "--relative", "reconstruction-cli")["state"], "RECONSTRUCTED_INACTIVE")


class PackageValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        f = Fixture()
        try: cls.package = f.preview()["package"]
        finally: f.close()

    def test_schema_and_byte_count_boolean_float_string_aliases_are_refused(self):
        for bad in (True, False, 1.0, "1", None):
            with self.subTest(value=bad):
                v = deepcopy(self.package); v["checkpoint"]["core"]["files"][0]["bytes"] = bad
                with self.assertRaises(REFUSED): validate_package(_package(v["checkpoint"]["core"]))
                v = deepcopy(self.package); v["schema_version"] = bad
                with self.assertRaises(REFUSED): validate_package(v)

    def test_v1_golden_identity_from_original_candidate_is_unchanged(self):
        from game_system_control.checkpoints import _COVERAGE
        core = {"schema_version": 1, "kind": "GameToolsSeedCheckpoint", "workspace_id": "golden-workspace", "project_id": "golden-project", "replica_id": "golden-replica",
                "parents": [], "tombstones": [], "coverage": deepcopy(_COVERAGE), "files": [{"content_class": "project_source", "relative": "hello.txt", "bytes": 5, "sha256": io.digest(b"hello")}]}
        package = validate_package(_package(core))
        self.assertEqual(package["checkpoint"]["checkpoint_id"], "93b343aa5b652af01eabfe420575c9eb27756098d33640f15db226a3baaa89fa")
        self.assertEqual(package["package_id"], "e0031bd55e299ae174a68c819b7c2ddbd536037f989a61f7c6f85c86cfbdf011")

    def test_duplicate_paths_prefix_collisions_and_case_aliases_are_refused(self):
        for relative in ("next.txt", "NEXT.txt", "next.txt/sub.txt"):
            v = deepcopy(self.package); row = deepcopy(v["checkpoint"]["core"]["files"][0]); row["relative"] = relative
            v["checkpoint"]["core"]["files"].append(row)
            with self.assertRaises(REFUSED): validate_package(_package(v["checkpoint"]["core"]))

    def test_unsafe_native_and_instruction_paths_are_refused(self):
        for relative in ("../out", "/absolute", "C:/x", "a\\b", "CON.txt", "trailing. ", "e\u0301.txt", ".env", ".codex/x", "sessions/x", "x.db", "AGENTS.md", "x/SKILL.md"):
            with self.subTest(path=relative):
                v = deepcopy(self.package); v["checkpoint"]["core"]["files"][0]["relative"] = relative
                with self.assertRaises(REFUSED): validate_package(_package(v["checkpoint"]["core"]))

    def test_parents_tombstones_unknown_fields_and_false_consistency_are_refused(self):
        for key, value in (("parents", ["a" * 64]), ("tombstones", [{"relative": "removed"}]), ("extra", True), ("coverage", {"consistency": "application_snapshot"})):
            v = deepcopy(self.package); v["checkpoint"]["core"][key] = value
            with self.assertRaises(REFUSED): validate_package(_package(v["checkpoint"]["core"]))

    def test_manifest_identity_corruption_is_refused(self):
        v = deepcopy(self.package); v["package_id"] = "0" * 64
        with self.assertRaises(REFUSED): validate_package(v)

    def test_total_size_and_file_count_bounds_are_enforced(self):
        v = deepcopy(self.package)
        for i, row in enumerate(v["checkpoint"]["core"]["files"]): row.update(bytes=io.MAX_FILE_BYTES, sha256=io.digest(str(i).encode()))
        with self.assertRaises(REFUSED): validate_package(_package(v["checkpoint"]["core"]))
        v = deepcopy(self.package); v["checkpoint"]["core"]["files"] *= 103
        with self.assertRaises(REFUSED): validate_package(_package(v["checkpoint"]["core"]))

    def test_duplicate_json_keys_and_nonfinite_values_are_refused(self):
        for raw in (b'{"schema_version":1,"schema_version":1}', b'{"x":NaN}'):
            with self.assertRaises(io.UserDataError): io._decode(raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
