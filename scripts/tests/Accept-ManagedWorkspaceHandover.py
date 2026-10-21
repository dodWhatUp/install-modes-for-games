"""Prepare or run one benign native Windows fixture; never ejects a drive.

Default: read-only preflight. --run-local-fixture creates unique private stores
and a non-system-volume vault, verifies full/delta/inactive restore and stops
local managed access. No protected presence, second host or physical acceptance
is inferred. Existing projects and Windows/Codex settings are never selected.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

SCRIPTS = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SCRIPTS))
from GameToolUserData import _canonical, _write_new, digest
from game_system_control.access import AccessStore
from game_system_control.checkpoints import CheckpointService
from game_system_control.contracts import require
from game_system_control.policy import PolicyStore, policy_revision
from game_system_control.vault import VaultRegistry, volume_identity, CLASSES
from game_system_control.workspace_state import private_root


def source_record():
    files = ("scripts/GameToolUserData.py", "scripts/GameToolJournal.py", "scripts/game_system_control/checkpoints.py",
             "scripts/game_system_control/access.py", "scripts/game_system_control/policy.py", "scripts/game_system_control/vault.py",
             "scripts/game_system_control/workspace_state.py", "scripts/tests/Accept-ManagedWorkspaceHandover.py")
    repo = SCRIPTS.parent
    return {"source_head": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
            "source_files": [{"path": p, "sha256": hashlib.sha256((repo / p).read_bytes()).hexdigest()} for p in files]}


def selected_parent(path):
    # Drive roots are valid data parents; private_root forbids filesystem roots.
    path = Path(path).absolute()
    probe = path / "new-fixture" if path == Path(path.anchor) else path
    private_root(probe)
    require(path.is_dir(), "Select an existing fixture parent.")
    require(not any((p / ".git").exists() or (p / "vault.json").exists() for p in (path, *path.parents)), "Choose parents outside repositories and existing vaults.")
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-parent", type=Path, required=True)
    parser.add_argument("--data-parent", type=Path, required=True)
    parser.add_argument("--run-local-fixture", action="store_true")
    args = parser.parse_args(argv)
    local_parent, data_parent = selected_parent(args.local_parent), selected_parent(args.data_parent)
    local_volume, data_volume = volume_identity(local_parent), volume_identity(data_parent)
    require(data_volume["system_volume"] is False and local_volume["volume_id"] != data_volume["volume_id"], "Use a non-system data volume with local authority/evidence on another volume.")
    result = {"kind": "ManagedCheckpointNativeHandoverPreparation", "schema_version": 1,
              "recorded_at": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(), "python": platform.python_version(),
              "evidence_class": "one_host_native_windows_local_os_session_fixture", "protected_windows_presence": "not_tested",
              "physical_release": "not_attempted", "second_computer": "not_tested", "original_checks_closed": 0, **source_record()}
    if not args.run_local_fixture:
        print(json.dumps({**result, "effect": "none", "volume_adapters": [local_volume["adapter"], data_volume["adapter"]]}, indent=2))
        return 0
    local = Path(tempfile.mkdtemp(prefix="native-handover-local-", dir=local_parent))
    data = Path(tempfile.mkdtemp(prefix="GameTools-Handover-Fixture-", dir=data_parent))
    access = None
    try:
        actor = {"workspace_id": "handover-fixture", "project_id": "fixture-project", "account_id": "fixture-account", "device_id": "fixture-host-a", "generation": 1}
        registry = VaultRegistry.create(local / "bindings")
        registry.enroll(data / "vault", actor["workspace_id"], registry.state.snapshot()["revision"])
        vault_id = registry.state.snapshot()["body"]["vaults"][0]["marker"]["vault_id"]
        policy = PolicyStore.create(local / "policy")
        rule = {"id": "fixture-rule", "scope": {**{k: actor[k] for k in ("account_id", "workspace_id", "project_id")},
                "source_device": actor["device_id"], "destination_device": actor["device_id"], "capability": "*", "content_class": "*"},
                "origin": "destination", "enabled": True, "controls": {"transfer": True, "adoption": True, "index": False, "context": False}, "context_depth": "none", "trigger": {"kind": "manual"}}
        p = policy.propose_rule(rule); policy.accept(p, p["preview_sha256"])
        access = AccessStore.create(local / "access", actor["account_id"], actor["device_id"], actor["project_id"], workspace_id=actor["workspace_id"], now=time.time())
        admin = {**actor, "capability": "enrollment.manage"}
        def change(action, values):
            p = access.propose_change(admin, action, values, now=time.time()); access.accept(admin, p, p["preview_sha256"], now=time.time())
        change("membership", {"account_id": actor["account_id"], "project_id": actor["project_id"], "roles": ["policy_administrator", "contributor"]})
        change("storage", {"account_id": actor["account_id"], "project_id": actor["project_id"], "storage_id": vault_id, "read": sorted(CLASSES), "write": sorted(CLASSES)})
        revision = policy_revision(policy.snapshot()["body"])
        change("pin_policy", {"policy_revision": revision}); change("acknowledge", {"device_id": actor["device_id"], "policy_revision": revision})
        service = CheckpointService(registry, policy, access, actor, vault_id)
        project = data / "vault/projects" / actor["project_id"]
        for name in CLASSES.values(): (project / name).mkdir(parents=True)
        payloads = {("project_source", "lookup.txt"): b"numbers.json\n", ("project_source", "numbers.json"): b'{"numbers":[2,3],"sum":5}',
                    ("selected_assets", "fixture.bin"): bytes(range(32)), ("selected_results", "report.txt"): b"benign result only\n", ("continuation_packet", "next.txt"): b"inactive fixture context only\n"}
        selection = []
        for (cls, relative), raw in payloads.items():
            (project / CLASSES[cls] / relative).write_bytes(raw); selection.append({"content_class": cls, "relative": relative})
        p = service.preview_checkpoint(selection, "checkpoint-full", "full"); full = service.publish_checkpoint(p, p["plan_sha256"])
        (project / "source/numbers.json").write_bytes(b'{"numbers":[2,3,4],"sum":9}')
        p = service.preview_checkpoint(selection, "checkpoint-delta", "delta", parent="checkpoint-full", representation="delta")
        delta = service.publish_checkpoint(p, p["plan_sha256"])
        restore = service.preview_reconstruction("checkpoint-delta", "reconstruction-readback", "readback", delta["package_id"], parent_sources=["checkpoint-full"])
        service.reconstruct(restore, restore["plan_sha256"])
        target = project / "outputs/reconstruction-readback/data"
        require(all(digest((target / CLASSES[r["content_class"]] / r["relative"]).read_bytes()) == r["sha256"] for r in p["package"]["checkpoint"]["core"]["files"]), "Byte oracle failed.")
        numbers = json.loads((target / "source" / (target / "source/lookup.txt").read_text().strip()).read_text())
        require(sum(numbers["numbers"]) == numbers["sum"] == 9, "Functional relative-reference oracle failed.")
        handover = service.preview_handover("checkpoint-delta", "physical-preparation", delta["package_id"], parent_sources=["checkpoint-full"])
        result.update(full_package_id=full["package_id"], delta_package_id=delta["package_id"], byte_verification="passed", functional_restoration="passed",
                      preparation=service.prepare_handover(handover, handover["plan_sha256"]), inspection=service.inspect_handover("physical-preparation"),
                      data_fixture=str(data), local_fixture=str(local), actor=actor, vault_id=vault_id, selection=selection, status="LOCAL_PREPARATION_PASSED")
    except Exception as error:
        result.update(status="NOT_COMPLETED", error_type=type(error).__name__)
        raise
    finally:
        if access is not None: access.stop_local()
        result["fixture_access_left_stopped"] = access is not None and (local / "access/LOCAL-STOP.json").exists()
        _write_new(local / "ACCEPTANCE.private.json", _canonical(result))
        print(json.dumps({"private_receipt": str(local / "ACCEPTANCE.private.json"), "receipt_sha256": digest((local / "ACCEPTANCE.private.json").read_bytes()), "status": result.get("status"), "original_checks_closed": 0}, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
