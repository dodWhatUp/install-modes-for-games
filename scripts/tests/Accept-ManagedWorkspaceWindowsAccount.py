"""Human-run, destination-local Windows acceptance; never run unattended.

First Windows prompt: confirm with your PIN/biometric in the Windows UI.
Second Windows prompt: choose Cancel. No credential values are read by Python.
Creates only a unique private fixture and leaves it locally stopped.
"""
import argparse
import json
from pathlib import Path
import sys
import time
import uuid

SCRIPTS = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(SCRIPTS))
from game_system_control.access import AccessStore
from game_system_control.contracts import ContextError, require
from game_system_control.windows_account import availability, WindowsAccountDenied
from game_system_control.workspace_state import private_root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-parent", required=True, type=Path)
    args = parser.parse_args()
    parent = private_root(args.local_parent)
    require(parent.is_dir(), "Select an existing private parent outside Codex/OneDrive.")
    result = {"provider": "windows_hello", "interactive_acceptance": "not_completed", "codex_changed": False,
              "scope": "one physical computer; no remote authentication", "availability": availability()}
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
        (root/"ACCEPTANCE.private.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
        print("Private receipt: " + str(root/"ACCEPTANCE.private.json"), flush=True)
    return 0


if __name__ == "__main__": raise SystemExit(main())
