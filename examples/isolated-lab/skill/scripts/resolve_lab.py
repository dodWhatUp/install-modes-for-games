"""Resolve this host's generated binding, never a copied machine credential."""
import argparse
import json
from pathlib import Path
import sys


def resolve(root=None):
    binding = Path(__file__).resolve().parents[1] / "machine.json"
    if not root:
        if not binding.is_file():
            raise RuntimeError("No machine binding. Install the verified isolatedLab source bundle on this host first.")
        value = json.loads(binding.read_text(encoding="utf-8-sig"))
        if value.get("schema") != 1:
            raise ValueError("Unsupported machine binding")
        root = value["lab_root"]
    root = Path(root).resolve()
    config = root / "private/config.json"
    runtime = root / "private/runtime.json"
    result = {"lab_root": str(root), "source": str(root / "source/examples/isolated-lab"),
            "config": str(config), "configured": config.is_file(),
            "python": json.loads(runtime.read_text(encoding="utf-8-sig"))["python"] if runtime.is_file() else None,
            "acceptance": str(root / "private/acceptance.json"), "VM_started": False}
    if binding.is_file():
        machine = json.loads(binding.read_text(encoding="utf-8-sig"))
        result["source_bundle"] = machine.get("bundle_path")
        result["bundle_sha256"] = machine.get("bundle_sha256")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", help="Explicitly selected private lab; binding remains unchanged")
    try:
        print(json.dumps(resolve(p.parse_args().root), indent=2))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        sys.exit(2)
