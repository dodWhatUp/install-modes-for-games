#!/usr/bin/env python3
"""Read-only exact dependency check. This does not install, repin or adopt a host."""
import argparse
import hashlib
import json
from pathlib import Path

HASH_POLICY = "utf8_lf"

PINS = {
    "scripts/GameToolAutomation.py": "34bffd633608713905f87f3ecdac50653169fbb815415e6a737a6766bad3fccf",
    "scripts/GameToolAI.py": "aa7f29eb7063beb298c4e46399d5a0b78e6752cc0216f787362b590f5efcd87a",
    "scripts/GameToolAIContracts.py": "1d1fe821cf0e4a91a00abe1ed48d842f9745a4df136b659661c3516e310c700d",
    "scripts/GameToolAIFoundation.py": "2fe10b7a1bb9d8969e42ff63b2d8b65edd101fc7628174fbbc680d82533aadac",
    "scripts/GameToolAITools.py": "b6107df58a18bec2d338e951dc2ac9dbc9817c5ae2d3cdcac6f7024c04c8ce34",
    "scripts/GameToolAIModern.py": "d0fd6e30b2995c765dc3d84c4e5e8ebda038142de87ff6d88a10b78124e0840b",
    "scripts/GameToolJournal.py": "01e76b93c69adefa742dfcb139756903c2259812c437ec72c508739b2a81657a",
    "scripts/GameToolGameWorkspaces.py": "bf1c270d7c4c3bab779ffda9ed40335f333b0a3e534ccf38a3f1b4cca753f0a2",
    "scripts/GameToolInstances.py": "af768f4b199ed5ec8da0e19de48a8c733decb8a5a8e99b62cf3e505fa9e08c7e",
    "scripts/GameToolPlanning.py": "461ae02e04448150bc18f5cee73699787f1617b19f714ed56e3a00ff5309b8e6",
    "scripts/GameToolMO2Read.py": "319b6275b2f0a5d827e3efa50970abacb30e12bfcb6629660db2e9c6fa0ce217",
    "scripts/game_mod_ops/managers.py": "8f0f3c41861211ac2fd7665028b123ae532e0fd427826f5017c064656acd53a7",
    "scripts/game_mod_ops/safety.py": "a40f7a172716a02d19c4aef688ee67d45b4e86dcede00702eed766528175598b",
}


def source_hash(path):
    """Hash UTF-8 source with line endings normalized to LF.

    Git may materialize authored text as LF or CRLF on different supported
    platforms.  The policy ignores only that checkout representation; any other
    byte/content change still produces a different digest.
    """
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return hashlib.sha256(raw).hexdigest()
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(normalized).hexdigest()


def check(root):
    rows = []
    for relative, expected in PINS.items():
        path = root / relative
        actual = source_hash(path) if path.is_file() else None
        rows.append({
            "path": relative,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "matches": actual == expected,
        })
    return {
        "status": "EXACT_DEPENDENCIES_MATCH" if all(row["matches"] for row in rows)
        else "REVIEW_HOST_DIFFERENCES",
        "host_reference_version": "0.28.0-preview.1",
        "hash_policy": HASH_POLICY,
        "files": rows,
        "installed": False,
        "repinned": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", type=Path, required=True)
    args = parser.parse_args()
    result = check(args.host)
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] != "EXACT_DEPENDENCIES_MATCH")
