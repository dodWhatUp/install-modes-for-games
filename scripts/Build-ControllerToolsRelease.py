"""Add controller tools over a verified incumbent; keep unrelated payload bytes."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

OWNED = [
    "scripts/Game-Tool-Hub.py", "scripts/GameToolWorkspace.py",
    "scripts/GameToolGameProfiles.py", "scripts/GameToolGameProfilesUI.py",
    "scripts/GameToolControllerRouting.py", "scripts/GameToolControllerRoutingUI.py",
    "scripts/GameToolControllerInventory.py",
    "scripts/GameToolControllerKeymaps.py", "scripts/GameToolControllerKeymapsUI.py",
    "scripts/GameToolDoomBindingInspect.py", "scripts/GameToolDoomBindingInspectUI.py",
    "scripts/Build-ControllerToolsRelease.py",
    "scripts/tests/Test-ControllerRouting.py", "scripts/tests/Test-ControllerRoutingGUI.py",
    "scripts/tests/Test-ControllerInventory.py", "scripts/tests/Test-ControllerKeymaps.py",
    "scripts/tests/Test-ControllerKeymapsGUI.py",
    "scripts/tests/Test-DoomBindingInspect.py", "scripts/tests/Test-DoomBindingInspectUI.py",
    "docs/CONTROLLER-ROUTING.md", "docs/CONTROLLER-INVENTORY.md",
    "docs/CONTROLLER-KEYMAP-DRAFTS.md", "docs/DOOM-BINARY-BINDING-INSPECTION.md",
    "schemas/controller-game-keymap-draft-v1.schema.json",
    "examples/controller-keymaps/vader-5-pro-reference.json",
    "scripts/tests/Test-DoomBindingInspectGUI.py",
    "scripts/tests/Test-GameToolModernUI.py",
]


def build(base, source, output):
    spec = importlib.util.spec_from_file_location("_controller_tools_incumbent", base / "scripts/GameToolUnified.py")
    api = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = api
    spec.loader.exec_module(api)
    before = api.inspect_directory(base)
    if subprocess.check_output(["git", "status", "--porcelain", "--", *OWNED], cwd=source, text=True).strip():
        raise ValueError("Commit the scoped controller tools source before packaging")
    payloads = dict(before["payloads"])
    for name in OWNED:
        payloads[api.member_name(name)] = (source / name).read_bytes()
    manifest = copy.deepcopy(before["manifest"])
    manifest["component_versions"].update(
        tool_hub="0.27.35-preview.1", game_profiles="0.2.2", game_profiles_ui="0.2.2",
        controller_routing="0.1.0", controller_routing_ui="0.1.0",
        controller_inventory="0.1.0", controller_keymaps="0.1.0",
        doom_binding_inspect="0.1.0")
    manifest["component_update"] = {
        "component": "controller_tools",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip(),
        "base_manifest_sha256": api.digest((base / "MANIFEST.json").read_bytes()),
        "incumbent_sources_preserved_except": OWNED, "game_state_included": False}
    manifest["files"] = [{"path": n, "bytes": len(b), "sha256": api.digest(b)} for n, b in sorted(payloads.items())]
    api.check_manifest(manifest, payloads)
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        for name, raw in sorted(payloads.items()):
            archive.writestr(name, raw)
    digest = api.digest(output.read_bytes())
    api.inspect_archive(output, digest)
    return {"archive": str(output), "sha256": digest, "payloads": len(payloads),
            "incumbent_preserved": sum(payloads[n] == raw for n, raw in before["payloads"].items())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.base, args.source, args.output), indent=2))
