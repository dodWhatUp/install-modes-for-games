"""Run a retained synthetic seed/reconstruction proof, not native acceptance.

Creates new benign fixtures only. Local identity and volume observation are
explicitly mocked; no Windows prompt, production enrollment, service or network.
Retained output excludes binding/access/policy stores and is evidence, not an
installed workspace. Original MCI acceptance does not change from running this.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import sys

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from GameToolUserData import local_path, _write_new, _canonical
from game_system_control.workspace_state import private_root


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-parent", required=True, type=Path, help="Existing private parent outside Git, cloud folders, Codex and portable vaults")
    args = parser.parse_args(argv)
    parent = private_root(args.output_parent)
    if not parent.is_dir() or any((p / ".git").exists() or (p / "vault.json").exists() for p in (parent, *parent.parents)):
        parser.error("Choose an existing private parent outside repositories and vaults.")
    root = Path(tempfile.mkdtemp(prefix="synthetic-checkpoint-proof-", dir=parent))
    ns = runpy.run_path(str(SCRIPTS / "tests/Test-ManagedWorkspaceCheckpoints.py"))
    fixture = ns["Fixture"]()
    try:
        before = ns["snapshot"](fixture.root)
        preview = fixture.preview()
        assert before == ns["snapshot"](fixture.root), "Preview wrote persistent state"
        publication = fixture.service.publish_seed(preview, preview["plan_sha256"])
        inspected = ns["reopen"](fixture.root).inspect("checkpoint-seed")
        assert inspected["state"] == "PUBLISHED"
        restore = fixture.reconstruct_preview()
        reconstructed = fixture.service.reconstruct(restore, restore["plan_sha256"])
        status = fixture.service.inspect_reconstruction("reconstruction-restore")
        data_root = fixture.outputs / "reconstruction-restore/data/source"
        reference = (data_root / "lookup.txt").read_text().strip()
        numbers = json.loads((data_root / reference).read_text())
        assert sum(numbers["numbers"]) == numbers["sum"] == 5
        assert status["state"] == "RECONSTRUCTED_INACTIVE"
        fixture.access.stop_local()
        # Retain only immutable synthetic payloads and evidence, never grants.
        shutil.copytree(fixture.outputs / "checkpoint-seed", root / "checkpoint")
        shutil.copytree(fixture.outputs / "reconstruction-restore", root / "reconstructed")
        hashes = []
        repo = SCRIPTS.parent
        for relative in ("scripts/GameToolUserData.py", "scripts/GameToolManagedWorkspace.py", "scripts/game_system_control/checkpoints.py", "scripts/tests/Test-ManagedWorkspaceCheckpoints.py", "scripts/tests/Accept-ManagedWorkspaceCheckpoint.py", "schemas/workspace-checkpoint.schema.json"):
            hashes.append({"path": relative, "sha256": hashlib.sha256((repo / relative).read_bytes()).hexdigest()})
        result = {"kind": "ManagedCheckpointSyntheticProof", "schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
                  "source_base": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
                  "evidence_class": "synthetic", "os_identity": "explicit_fixture_only", "volume": "explicit_fixture_only",
                  "preview_no_persistent_effect": True, "publication": publication, "reopen": inspected,
                  "reconstruction": reconstructed, "relative_reference_and_sum_oracle": "passed", "fixture_access_left_stopped": True,
                  "binding_access_policy_stores_exported": False, "original_checks_closed": 0,
                  "not_tested": ["native Windows verification", "native macOS volume/account support", "physical moved drive", "other physical computer", "power loss durability", "full/delta transport", "native chat continuity", "active file adoption", "network/cloud", "model quality or token savings"],
                  "source_files": hashes}
        _write_new(root / "PROOF-RECEIPT.json", _canonical(result))
        assert json.loads((root / "PROOF-RECEIPT.json").read_text()) == result
        print(json.dumps({"state": "SYNTHETIC_PROOF_PASSED", "output": str(root), "receipt_sha256": hashlib.sha256((root / "PROOF-RECEIPT.json").read_bytes()).hexdigest(), "original_checks_closed": 0}, indent=2))
        return 0
    finally:
        # Only the newly created fixture is stopped/removed; no existing state.
        try:
            fixture.access.stop_local()
        finally:
            fixture.close()


if __name__ == "__main__":
    raise SystemExit(main())
