"""Offline exchange on independent synthetic stores; no native/physical acceptance.

The authored byte carrier copies manifests/objects only. Grants stay local.
"""
from copy import deepcopy
import json
from pathlib import Path
import runpy
import shutil
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
ns = runpy.run_path(str(SCRIPTS / "tests/Test-ManagedWorkspaceCheckpoints.py"))
Fixture, ACTOR, REFUSED, snapshot = (ns[k] for k in ("Fixture", "ACTOR", "REFUSED", "snapshot"))
from game_system_control.checkpoints import validate_package, _package, MissingParents
from GameToolUserData import digest


def carrier(sender, relative, receiver, name):
    source, target = sender.outputs / relative, receiver.outputs / name
    target.mkdir()
    shutil.copyfile(source / "MANIFEST.json", target / "MANIFEST.json")
    shutil.copytree(source / "objects", target / "objects")
    return name


def produce(f, op, parent=None, ancestors=(), representation="full"):
    p = f.service.preview_checkpoint(f.selection, "checkpoint-" + op, op, parent=parent, parent_sources=ancestors, representation=representation)
    return p, f.service.publish_checkpoint(p, p["plan_sha256"])


def receive(f, source, op, package_id, parents=()):
    p = f.service.preview_receive(source, "checkpoint-" + op, op, package_id, parent_sources=parents)
    return f.service.receive(p, p["plan_sha256"])


def round_trip(a, b):
    p, sent = produce(a, "out")
    carrier(a, "checkpoint-out", b, "incoming-a")
    got = receive(b, "incoming-a", "from-a", sent["package_id"])
    restore = b.service.preview_reconstruction("checkpoint-from-a", "reconstruction-b", "b", sent["package_id"])
    b.service.reconstruct(restore, restore["plan_sha256"])
    data = b.outputs / "reconstruction-b/data/source"
    reference = (data / "lookup.txt").read_text().strip()
    numbers = json.loads((data / reference).read_text())
    assert sum(numbers["numbers"]) == numbers["sum"] == 5
    # Only authored synthetic work changes. No imported commands execute.
    (b.project / "source/numbers.json").write_bytes(b'{"numbers":[2,3,4],"sum":9}')
    back, sent_back = produce(b, "back", "checkpoint-from-a", representation="delta")
    carrier(b, "checkpoint-back", a, "incoming-b")
    active_before = (a.project / "source/numbers.json").read_bytes()
    got_back = receive(a, "incoming-b", "from-b", sent_back["package_id"], ["checkpoint-out"])
    r = a.service.preview_reconstruction("checkpoint-from-b", "reconstruction-a", "a", sent_back["package_id"], parent_sources=["checkpoint-out"])
    a.service.reconstruct(r, r["plan_sha256"])
    root = a.outputs / "reconstruction-a/data/source"
    restored = json.loads((root / (root / "lookup.txt").read_text().strip()).read_text())
    assert sum(restored["numbers"]) == restored["sum"] == 9
    assert (a.project / "source/numbers.json").read_bytes() == active_before
    assert all(digest((a.outputs / "reconstruction-a/data" / ns["CLASSES"][row["content_class"]] / row["relative"]).read_bytes()) == row["sha256"] for row in back["package"]["checkpoint"]["core"]["files"])
    return {"byte_verification": "passed", "functional_relative_reference_and_sum": "passed", "original_sum": 5, "returned_sum": 9,
            "A_to_B": got, "B_to_A": got_back, "source_replica_ids_distinct": p["package"]["checkpoint"]["core"]["replica_id"] != back["package"]["checkpoint"]["core"]["replica_id"],
            "active_source_preserved": True, "bindings_or_grants_transferred": False, "physical_computers_tested": False}


class ExchangeTests(unittest.TestCase):
    def setUp(self): self.f = Fixture()
    def tearDown(self): self.f.close()

    def test_full_delta_identity_and_inherited_restoration(self):
        self.f.publish()
        (self.f.project / "source/numbers.json").write_bytes(b'{"numbers":[3,4],"sum":7}')
        before = snapshot(self.f.root)
        full = self.f.service.preview_checkpoint(self.f.selection, "checkpoint-full", "full", parent="checkpoint-seed")
        delta = self.f.service.preview_checkpoint(self.f.selection, "checkpoint-delta", "delta", parent="checkpoint-seed", representation="delta")
        self.assertEqual(before, snapshot(self.f.root))
        self.assertEqual(full["package"]["checkpoint"], delta["package"]["checkpoint"])
        self.assertNotEqual(full["package"]["package_id"], delta["package"]["package_id"])
        self.assertEqual(len(delta["package"]["required_objects"]), 1)
        self.f.service.publish_checkpoint(delta, delta["plan_sha256"])
        self.assertEqual(self.f.service.inspect("checkpoint-delta")["state"], "MISSING_PARENTS")
        self.assertEqual(self.f.service.inspect("checkpoint-delta", parent_sources=["checkpoint-seed"])["state"], "PUBLISHED")
        restore = self.f.service.preview_reconstruction("checkpoint-delta", "reconstruction-d", "d", delta["package"]["package_id"], parent_sources=["checkpoint-seed"])
        self.f.service.reconstruct(restore, restore["plan_sha256"])
        self.assertEqual(self.f.service.inspect_reconstruction("reconstruction-d")["state"], "RECONSTRUCTED_INACTIVE")

    def test_parent_drift_refuses_before_writing(self):
        self.f.publish(); p = self.f.service.preview_checkpoint(self.f.selection, "checkpoint-d", "d", parent="checkpoint-seed", representation="delta")
        next((self.f.outputs / "checkpoint-seed/objects").iterdir()).write_bytes(b"corrupt")
        with self.assertRaises(REFUSED): self.f.service.publish_checkpoint(p, p["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-d").exists())

    def test_empty_delta_and_narrowed_selection_never_infer_deletions(self):
        self.f.publish()
        p = self.f.service.preview_checkpoint(self.f.selection[:1], "checkpoint-small", "small", parent="checkpoint-seed", representation="delta")
        self.assertEqual(p["package"]["required_objects"], [])
        self.assertEqual(p["package"]["checkpoint"]["core"]["tombstones"], [])
        self.f.service.publish_checkpoint(p, p["plan_sha256"])
        self.assertTrue((self.f.project / "source/numbers.json").exists())

    def test_parent_locators_are_bounded_exact_and_order_independent(self):
        self.f.publish(); produce(self.f, "one", "checkpoint-seed")
        produce(self.f, "two", "checkpoint-one", ["checkpoint-seed"], "delta")
        self.assertEqual(self.f.service.inspect("checkpoint-two", parent_sources=["checkpoint-seed", "checkpoint-one"])["state"], "PUBLISHED")
        for names in (["checkpoint-one"] * 8, ["checkpoint-one", "checkpoint-one"], ["../escape"]):
            with self.subTest(names=names), self.assertRaises(REFUSED): self.f.service.inspect("checkpoint-two", parent_sources=names)

    def test_out_of_order_receive_then_exact_parent_and_duplicate_refusal(self):
        _, parent = produce(self.f, "parent"); _, sent = produce(self.f, "child", "checkpoint-parent", representation="delta")
        other = Fixture({**ACTOR, "device_id": "fixture-b"})
        try:
            carrier(self.f, "checkpoint-child", other, "child-first")
            before = snapshot(other.root)
            with self.assertRaises(MissingParents): other.service.preview_receive("child-first", "checkpoint-child", "child", sent["package_id"])
            self.assertEqual(before, snapshot(other.root))
            carrier(self.f, "checkpoint-parent", other, "parent-second")
            receive(other, "parent-second", "parent", parent["package_id"])
            got = receive(other, "child-first", "child", sent["package_id"], ["checkpoint-parent"])
            self.assertTrue(got["received"]); self.assertTrue(got["verified"]); self.assertFalse(got["adopted"])
            before = snapshot(other.outputs / "checkpoint-child")
            with self.assertRaises(REFUSED): other.service.preview_receive("child-first", "checkpoint-child", "child", sent["package_id"], parent_sources=["checkpoint-parent"])
            self.assertEqual(before, snapshot(other.outputs / "checkpoint-child"))
        finally: other.close()

    def test_received_corruption_and_stop_cannot_write(self):
        _, sent = produce(self.f, "source")
        carrier(self.f, "checkpoint-source", self.f, "incoming")
        plan = self.f.service.preview_receive("incoming", "checkpoint-received", "received", sent["package_id"])
        next((self.f.outputs / "incoming/objects").iterdir()).write_bytes(b"corrupt")
        with self.assertRaises(REFUSED): self.f.service.receive(plan, plan["plan_sha256"])
        self.assertFalse((self.f.outputs / "checkpoint-received").exists())
        self.f.access.stop_local()
        with self.assertRaises(REFUSED): self.f.service.receive(plan, plan["plan_sha256"])

    def test_receive_receipt_loss_is_inspection_only(self):
        _, sent = produce(self.f, "source"); carrier(self.f, "checkpoint-source", self.f, "incoming")
        p = self.f.service.preview_receive("incoming", "checkpoint-received", "received", sent["package_id"])
        def fail(phase):
            if phase == "publication_written": raise OSError("fixture lost receive receipt")
        with self.assertRaises(OSError): self.f.service.receive(p, p["plan_sha256"], observer=fail)
        state = self.f.service.inspect("checkpoint-received")
        self.assertEqual(state["state"], "PUBLISHED_RECEIPT_PENDING"); self.assertFalse(state["automatic_retry"])

    def test_legacy_seed_cannot_be_misreported_as_a_v2_destination_receipt(self):
        _, sent = self.f.publish()
        with self.assertRaises(REFUSED): self.f.service.preview_receive("checkpoint-seed", "checkpoint-import", "import", sent["package_id"])
        self.assertFalse((self.f.outputs / "checkpoint-import").exists())

    def test_granular_recovery_preserves_interrupted_files_and_labels_subset(self):
        self.f.publish(); p = self.f.reconstruct_preview()
        def fail(phase):
            if phase == "file_reconstructed": raise OSError("fixture interruption")
        with self.assertRaises(OSError): self.f.service.reconstruct(p, p["plan_sha256"], observer=fail)
        old = self.f.outputs / "reconstruction-restore"; before = snapshot(old)
        selection = [{"content_class": "project_source", "relative": "numbers.json"}]
        recovery = self.f.service.preview_recovery("checkpoint-seed", "reconstruction-restore", selection, "reconstruction-recover", "recover", p["package"]["package_id"])
        result = self.f.service.reconstruct(recovery, recovery["plan_sha256"])
        self.assertFalse(result["whole_checkpoint"]); self.assertEqual(result["files"], 1)
        self.assertEqual(before, snapshot(old))
        self.assertEqual(self.f.service.inspect_reconstruction("reconstruction-recover")["state"], "RECONSTRUCTED_INACTIVE")

    def test_granular_recovery_refuses_later_external_edits(self):
        self.f.publish(); p = self.f.reconstruct_preview(); self.f.service.reconstruct(p, p["plan_sha256"])
        selection = [{"content_class": "project_source", "relative": "numbers.json"}]
        r = self.f.service.preview_recovery("checkpoint-seed", "reconstruction-restore", selection, "reconstruction-recover", "recover", p["package"]["package_id"])
        path = self.f.outputs / "reconstruction-restore/data/source/numbers.json"; path.write_bytes(b"later work")
        with self.assertRaises(REFUSED): self.f.service.reconstruct(r, r["plan_sha256"])
        self.assertFalse((self.f.outputs / "reconstruction-recover").exists()); self.assertEqual(path.read_bytes(), b"later work")

    def test_unlisted_restored_content_is_not_certified_complete(self):
        self.f.publish(); p = self.f.reconstruct_preview(); self.f.service.reconstruct(p, p["plan_sha256"])
        (self.f.outputs / "reconstruction-restore/data/source/later.txt").write_bytes(b"external")
        with self.assertRaises(REFUSED): self.f.service.inspect_reconstruction("reconstruction-restore")

    def test_v2_schema_unknown_features_and_inert_extensions(self):
        p = self.f.service.preview_checkpoint(self.f.selection, "checkpoint-ext", "ext", extensions={"future_note": {"inert": True}})
        value = validate_package(p["package"])
        self.assertEqual(value["extensions"], {"future_note": {"inert": True}})
        bad = deepcopy(value); bad["required_features"].append("execute-hooks")
        with self.assertRaises(REFUSED): validate_package(bad)
        bad = deepcopy(value); bad["checkpoint"]["core"]["parents"] = ["a" * 64, "b" * 64]
        with self.assertRaises(REFUSED): validate_package(_package(bad["checkpoint"]["core"]))
        try: import jsonschema
        except ImportError: self.skipTest("Optional jsonschema unavailable")
        schema = json.loads((SCRIPTS.parent / "schemas/workspace-checkpoint.schema.json").read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(value, schema); jsonschema.validate(self.f.preview()["package"], schema)

    def test_synthetic_A_to_B_to_A_separates_bytes_function_and_authority(self):
        other = Fixture({**ACTOR, "device_id": "fixture-b"})
        try:
            result = round_trip(self.f, other)
            self.assertEqual(result["byte_verification"], "passed")
            self.assertEqual(result["functional_relative_reference_and_sum"], "passed")
            self.assertTrue(result["source_replica_ids_distinct"])
            self.assertNotEqual(result["A_to_B"]["target_replica_id"], result["B_to_A"]["target_replica_id"])
        finally: other.close()

    def test_rollback_restores_exact_parent_subset_to_a_new_copy(self):
        parent, sent = produce(self.f, "parent")
        (self.f.project / "source/numbers.json").write_bytes(b'{"numbers":[8,9],"sum":17}')
        child, current = produce(self.f, "child", "checkpoint-parent", representation="delta")
        p = self.f.service.preview_reconstruction("checkpoint-child", "reconstruction-current", "current", current["package_id"], parent_sources=["checkpoint-parent"])
        self.f.service.reconstruct(p, p["plan_sha256"])
        before = snapshot(self.f.outputs / "reconstruction-current")
        selection = [{"content_class": "project_source", "relative": "numbers.json"}]
        r = self.f.service.preview_recovery("checkpoint-parent", "reconstruction-current", selection, "reconstruction-rollback", "rollback", sent["package_id"], rollback=True)
        result = self.f.service.reconstruct(r, r["plan_sha256"])
        self.assertEqual(result["recovery_kind"], "rollback_parent_subset"); self.assertFalse(result["whole_checkpoint"])
        restored = json.loads((self.f.outputs / "reconstruction-rollback/data/source/numbers.json").read_text())
        self.assertEqual(restored["sum"], 5); self.assertEqual(before, snapshot(self.f.outputs / "reconstruction-current"))
        self.assertEqual(self.f.service.inspect_reconstruction("reconstruction-rollback")["state"], "RECONSTRUCTED_INACTIVE")

    def test_torn_publication_marker_is_uncertain_and_never_reconstructed(self):
        _, sent = produce(self.f, "torn")
        (self.f.outputs / "checkpoint-torn/_PUBLISHED.json").write_bytes(b'{"operation_id":')
        state = self.f.service.inspect("checkpoint-torn")
        self.assertEqual(state["state"], "PUBLICATION_UNCERTAIN")
        with self.assertRaises(REFUSED): self.f.service.preview_reconstruction("checkpoint-torn", "reconstruction-no", "no", sent["package_id"])

    def test_policy_upgrade_requires_fresh_access_pin_and_ack_before_checkpoint(self):
        from game_system_control.policy import policy_revision
        p = self.f.policy.propose_revision_upgrade(); self.f.policy.accept(p, p["preview_sha256"])
        with self.assertRaises(REFUSED): self.f.preview()
        revision = policy_revision(self.f.policy.snapshot()["body"])
        self.f.change("pin_policy", {"policy_revision": revision})
        with self.assertRaises(REFUSED): self.f.preview()
        self.f.change("acknowledge", {"device_id": self.f.actor["device_id"], "policy_revision": revision})
        self.f.preview()
        queue = self.f.policy.stage_context("notice", "a" * 64, "notice"); self.f.policy.accept(queue, queue["preview_sha256"])
        self.f.preview()

    def test_new_cli_package_receive_and_recovery_modes_use_existing_service(self):
        import GameToolManagedWorkspace as cli
        from game_system_control.checkpoints import CheckpointService
        from game_system_control.vault import VaultRegistry
        from contextlib import redirect_stdout, redirect_stderr
        from io import StringIO
        from unittest.mock import patch
        self.f.selection = [{"content_class": "project_source", "relative": "numbers.json"}]
        count = [0]
        def call(mode, fields, *extra):
            count[0] += 1; path = self.f.root / ("cli-" + str(count[0]) + ".json")
            path.write_text(json.dumps({"actor": self.f.actor, **fields}))
            out, err = StringIO(), StringIO()
            args = [mode, "--state", str(self.f.root / "bindings"), "--policy-state", str(self.f.root / "policy"), "--access-state", str(self.f.root / "access"), "--vault-id", self.f.vault_id, "--input", str(path), *extra]
            def factory(registry, policy, access, actor, vault_id):
                return CheckpointService(registry, policy, access, actor, vault_id, clock=lambda: self.f.now)
            with patch.object(cli, "VaultRegistry", side_effect=lambda p: VaultRegistry(p, ns["observe"])), patch("game_system_control.checkpoints.CheckpointService", side_effect=factory), redirect_stdout(out), redirect_stderr(err): code = cli.main(args)
            self.assertEqual(code, 0, err.getvalue()); return json.loads(out.getvalue())
        p = call("checkpoint-package-preview", {"selection": self.f.selection, "destination": "checkpoint-cli-parent", "operation_id": "cli-parent", "representation": "full"})
        sent = call("checkpoint-package-publish", {"plan": p}, "--accept", p["plan_sha256"])
        carrier(self.f, "checkpoint-cli-parent", self.f, "cli-input")
        p = call("checkpoint-receive-preview", {"source": "cli-input", "destination": "checkpoint-cli-receive", "operation_id": "cli-receive", "package_id": sent["package_id"]})
        got = call("checkpoint-receive", {"plan": p}, "--accept", p["plan_sha256"])
        self.assertTrue(got["received"])
        p = call("checkpoint-restore-preview", {"source": "checkpoint-cli-parent", "destination": "reconstruction-cli-old", "operation_id": "cli-old", "package_id": sent["package_id"]})
        call("checkpoint-restore", {"plan": p}, "--accept", p["plan_sha256"])
        recover = call("checkpoint-recovery-preview", {"source": "checkpoint-cli-parent", "incomplete": "reconstruction-cli-old", "selection": self.f.selection, "destination": "reconstruction-cli-recover", "operation_id": "cli-recover", "package_id": sent["package_id"]})
        self.assertEqual(recover["recovery_kind"], "recover_subset")
        child, current = produce(self.f, "cli-child", "checkpoint-cli-parent", representation="delta")
        p = call("checkpoint-restore-preview", {"source": "checkpoint-cli-child", "destination": "reconstruction-cli-current", "operation_id": "cli-current", "package_id": current["package_id"], "parent_sources": ["checkpoint-cli-parent"]})
        call("checkpoint-restore", {"plan": p}, "--accept", p["plan_sha256"])
        rollback = call("checkpoint-rollback-preview", {"source": "checkpoint-cli-parent", "incomplete": "reconstruction-cli-current", "selection": self.f.selection, "destination": "reconstruction-cli-rollback", "operation_id": "cli-rollback", "package_id": sent["package_id"]})
        self.assertEqual(rollback["recovery_kind"], "rollback_parent_subset")


if __name__ == "__main__": unittest.main(verbosity=2)
