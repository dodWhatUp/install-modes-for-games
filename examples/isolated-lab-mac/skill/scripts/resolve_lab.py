"""Read this host's installed binding without starting any VM."""
import json
import hashlib
from pathlib import Path
import sys

try:
    binding = json.loads((Path(__file__).resolve().parents[1] / "machine.json").read_bytes())
    root = Path(binding["lab_root"])
    source = Path(binding["source"])
    manifest = (source / "MAC-SOURCE-MANIFEST.json").read_bytes()
    if hashlib.sha256(manifest).hexdigest() != binding["source_sha256"]:
        raise ValueError("Installed source manifest changed; preserve it for review")
    for entry in json.loads(manifest)["files"]:
        data = (source / entry["path"]).read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Installed source bytes changed; preserve them for review")
    print(json.dumps({"schema": 1, "lab_root": str(root), "source": binding["source"],
                      "config_present": (root / "private/config.json").is_file(),
                      "acceptance": str(root / "private/acceptance.json"),
                      "source_sha256": binding["source_sha256"], "VM_started": False}, indent=2))
except Exception as error:
    print(json.dumps({"ok": False, "error": str(error), "VM_started": False}))
    sys.exit(2)
