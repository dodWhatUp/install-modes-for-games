"""Human-run, destination-local Windows acceptance; never run unattended.

Recommended: --phase success, then --phase cancel --fixture EXACT_LOCAL_FIXTURE.
Each phase opens one dialog with one intended action. The legacy combined mode
opens success followed by Cancel. No credential values are read by Python.
Creates/selects only a private acceptance fixture and leaves it locally stopped.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

SCRIPTS = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SCRIPTS))
from game_system_control.access import AccessStore
from game_system_control.contracts import ContextError, require
from game_system_control.windows_account import availability, WindowsAccountDenied, WindowsAccountWaitFailed
from game_system_control.workspace_state import private_root
from GameToolUserData import _canonical, _write_new, _read, _decode, digest


def source_record():
    repo = SCRIPTS.parent
    paths = ("scripts/game_system_control/windows_account.py", "scripts/game_system_control/access.py", "scripts/game_system_control/workspace_state.py", "scripts/GameToolUserData.py", "scripts/tests/Accept-ManagedWorkspaceWindowsAccount.py")
    return {"source_head": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
            "source_files": [{"path": p, "sha256": hashlib.sha256((repo / p).read_bytes()).hexdigest()} for p in paths]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-parent", required=True, type=Path)
    parser.add_argument("--host-label", choices=("A", "B"), default="A", help="Evidence label only; never an account identity or pairing claim")
    parser.add_argument("--phase", choices=("combined", "success", "cancel"), default="combined", help="Use separate success and cancel runs to avoid adjacent indistinguishable dialogs")
    parser.add_argument("--fixture", type=Path, help="Cancel phase only: exact fresh stopped local fixture from a successful creation receipt")
    parser.add_argument("--run-interactive", action="store_true", help="Human present: open the selected phase; combined opens success then Cancel. Default is read-only preflight.")
    args = parser.parse_args(argv)
    parent = private_root(args.local_parent)
    require(parent.is_dir(), "Select an existing private parent outside Codex/OneDrive.")
    require(not any((p / ".git").exists() or (p / "vault.json").exists() for p in (parent, *parent.parents)), "Acceptance evidence must stay outside Git and portable vaults.")
    result = {"provider": "windows_hello", "interactive_acceptance": "not_completed", "codex_changed": False,
              "scope": "one physical computer; no remote authentication", "availability": availability(),
              "host_label": args.host_label, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": platform.python_version(), "original_checks_closed": 0,
              "requested_phase": args.phase, "phase_acceptance": "not_completed", **source_record()}
    require((args.phase == "cancel") == (args.fixture is not None), "Select --fixture only for the separate cancel phase.")
    if not args.run_interactive:
        print(json.dumps({**result, "effect": "none", "next": "human_run_with_--run-interactive"}, indent=2))
        return 0
    require(result["availability"]["status"] == "available", "Windows verification is not available; preserve current settings and inspect locally.")
    root = parent/("windows-account-acceptance-"+uuid.uuid4().hex)
    root.mkdir(mode=0o700)
    access = None
    access_fixture = root
    stage = "select_cancel_fixture" if args.phase == "cancel" else "create_windows_registry"
    try:
        if args.phase == "cancel":
            selected = private_root(args.fixture)
            require(selected.parent == parent and selected.name.startswith("windows-account-acceptance-"), "Select the exact fixture under this private local parent.")
            prior_raw, _ = _read(selected / "ACCEPTANCE.private.json", 128 * 1024)
            prior = _decode(prior_raw)
            require(prior.get("fresh_creation") == "passed" and prior.get("fixture_access_left_stopped") is True and prior.get("host_label") == args.host_label,
                    "The selected local fixture needs a successful creation receipt and retained stop.")
            old_sources = {r["path"]: r["sha256"] for r in prior["source_files"]}
            for row in result["source_files"]:
                if row["path"] != "scripts/tests/Accept-ManagedWorkspaceWindowsAccount.py":
                    require(old_sources.get(row["path"]) == row["sha256"], "A native/access/IO owner changed; create a fresh success fixture before Cancel acceptance.")
            candidate = AccessStore(selected / "access")
            body = candidate.snapshot()["body"]
            require(body.get("authentication") == "windows_hello" and body["project_id"] == "acceptance-project" and body["workspace_id"] == "workspace",
                    "Select the protected local acceptance fixture, not an existing project registry.")
            raw_stop, _ = _read(selected / "access/LOCAL-STOP.json")
            stop = {"stop_sha256": digest(raw_stop)}
            access, access_fixture = candidate, selected
            result["paired_success_receipt_sha256"] = digest(prior_raw)
        else:
            print("Success prompt: confirm using the Windows UI. Do not enter credentials in this console.", flush=True)
            access = AccessStore.create(root/"access", "local-account", "local-device", "acceptance-project", now=time.time(), windows_sign_in=True)
            result["fresh_creation"] = "passed"
            stop = access.stop_local()
            if args.phase == "success":
                result["phase_acceptance"] = "passed"
                return 0
        actor = {"workspace_id": "workspace", "project_id": "acceptance-project", "account_id": "local-account",
                 "device_id": "local-device", "generation": 1, "capability": "enrollment.manage"}
        print("Cancel prompt: choose Cancel in Windows. Do not verify this prompt. The fixture must remain stopped.", flush=True)
        stage = "cancel_resume"
        try:
            access.resume_local(actor, stop["stop_sha256"], now=time.time())
        except WindowsAccountDenied as error:
            if error.outcome != "canceled": raise
            require(digest(_read(access_fixture/"access/LOCAL-STOP.json")[0]) == stop["stop_sha256"], "Cancellation must retain the exact local stop.")
            result["canceled_resume_kept_stop"] = "passed"
            result["cancel_outcome"] = "native_canceled"
        else:
            result["cancel_outcome"] = "unexpectedly_verified"
            require(False, "The Cancel prompt was verified; cancellation acceptance remains pending. Fixture will be stopped.")
        result["phase_acceptance"] = "passed"
        if args.phase == "combined": result["interactive_acceptance"] = "passed"
    except Exception as error:
        result["error_type"] = type(error).__name__
        result["failure_stage"] = stage
        # Store only bounded classifications, never arbitrary exception text,
        # account identifiers, credentials or native reusable proof.
        result["failure_reason"] = (error.reason if isinstance(error, WindowsAccountWaitFailed) else
                                    "native_" + error.outcome if isinstance(error, WindowsAccountDenied) else "operation_refused_or_failed")
        raise
    finally:
        primary_error = sys.exc_info()[1]
        cleanup_error = None
        if access is not None:
            try: access.stop_local()
            except Exception as error:
                cleanup_error = error
                result.update(interactive_acceptance="not_completed", phase_acceptance="not_completed", cleanup_error_type=type(error).__name__, cleanup_failure="fixture_stop_failed")
        result["access_fixture"] = str(access_fixture)
        result["fixture_access_left_stopped"] = access is not None and cleanup_error is None and (access_fixture/"access/LOCAL-STOP.json").exists()
        _write_new(root/"ACCEPTANCE.private.json", _canonical(result))
        print("Private receipt: " + str(root/"ACCEPTANCE.private.json"), flush=True)
        if cleanup_error is not None and primary_error is None: raise cleanup_error
    return 0


if __name__ == "__main__": raise SystemExit(main())
