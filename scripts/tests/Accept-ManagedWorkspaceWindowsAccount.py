"""Human-run, destination-local Windows acceptance; never run unattended.

First Windows prompt: confirm with your PIN/biometric in the Windows UI.
Second Windows prompt: choose Cancel. No credential values are read by Python.
Creates only a unique private fixture and leaves it locally stopped.
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
from game_system_control.windows_account import availability, WindowsAccountDenied
from game_system_control.workspace_state import private_root


def source_record():
    repo = SCRIPTS.parent
    paths = ("scripts/game_system_control/windows_account.py", "scripts/game_system_control/access.py", "scripts/game_system_control/workspace_state.py", "scripts/tests/Accept-ManagedWorkspaceWindowsAccount.py")
    return {"source_head": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
            "source_files": [{"path": p, "sha256": hashlib.sha256((repo / p).read_bytes()).hexdigest()} for p in paths]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-parent", required=True, type=Path)
    parser.add_argument("--host-label", choices=("A", "B"), default="A", help="Evidence label only; never an account identity or pairing claim")
    parser.add_argument("--run-interactive", action="store_true", help="Human present: open the success then explicit Cancel prompts. Default is read-only preflight.")
    args = parser.parse_args(argv)
    parent = private_root(args.local_parent)
    require(parent.is_dir(), "Select an existing private parent outside Codex/OneDrive.")
    require(not any((p / ".git").exists() or (p / "vault.json").exists() for p in (parent, *parent.parents)), "Acceptance evidence must stay outside Git and portable vaults.")
    result = {"provider": "windows_hello", "interactive_acceptance": "not_completed", "codex_changed": False,
              "scope": "one physical computer; no remote authentication", "availability": availability(),
              "host_label": args.host_label, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": platform.python_version(), "original_checks_closed": 0, **source_record()}
    if not args.run_interactive:
        print(json.dumps({**result, "effect": "none", "next": "human_run_with_--run-interactive"}, indent=2))
        return 0
    require(result["availability"]["status"] == "available", "Windows verification is not available; preserve current settings and inspect locally.")
    root = parent/("windows-account-acceptance-"+uuid.uuid4().hex)
    root.mkdir(mode=0o700)
    access = None
    try:
        print("First Windows prompt: confirm using the Windows UI. Do not enter credentials in this console.", flush=True)
        access = AccessStore.create(root/"access", "local-account", "local-device", "acceptance-project", now=time.time(), windows_sign_in=True)
        result["fresh_creation"] = "passed"
        stop = access.stop_local()
        actor = {"workspace_id": "workspace", "project_id": "acceptance-project", "account_id": "local-account",
                 "device_id": "local-device", "generation": 1, "capability": "enrollment.manage"}
        print("Second Windows prompt: choose Cancel. The fixture must remain stopped.", flush=True)
        try:
            access.resume_local(actor, stop["stop_sha256"], now=time.time())
        except WindowsAccountDenied as error:
            require(error.outcome == "canceled", "Only Windows' explicit canceled result accepts the cancellation test.")
            require((root/"access"/"LOCAL-STOP.json").exists(), "Cancellation must retain local stop.")
            result["canceled_resume_kept_stop"] = "passed"
        else:
            require(False, "The second prompt was accepted; cancellation acceptance remains pending. Fixture will be stopped.")
        result["interactive_acceptance"] = "passed"
    except Exception as error:
        result["error_type"] = type(error).__name__
        raise
    finally:
        if access is not None: access.stop_local()
        result["fixture_access_left_stopped"] = access is not None and (root/"access/LOCAL-STOP.json").exists()
        (root/"ACCEPTANCE.private.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        print("Private receipt: " + str(root/"ACCEPTANCE.private.json"), flush=True)
    return 0


if __name__ == "__main__": raise SystemExit(main())
