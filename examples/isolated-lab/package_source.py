"""Copy and archive an explicit authored-source allowlist, never private VM data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

from lab import Lab, sha256, stamp, write_json

FILES = ["lab.py", "Lab.ps1", "prepare_linux.py", "prepare_windows.py", "Install-VirtualBox.ps1",
         "config.example.json", "linux-smoke.sh", "linux-gui-smoke.sh", "linux-endurance.sh", "test_lab.py",
         "VALIDATION.json", "README.md", "LAB-ROOT-README.md", "LAB-ROOT-AGENTS.template.md",
         "guest_agent.py", "guest_tools.py", "guest_mcp.py", "install_guest_agent.sh", "install_guest_browser.sh",
         "accept_guest_agent.py", "accept_mcp.py", "test_guest_tools.py", "package_source.py",
         "prepare_guest_browser.py", "configure_mcp.py", "accept_cold_guest.py",
         "desktop_agent.py", "desktop_demo.py", "install_guest_desktop.sh", "accept_desktop.py",
         "accept_background.py", "accept_codex_client.py", "observe_host_resources.py",
         "skill/SKILL.md", "skill/agents/openai.yaml", "skill/scripts/resolve_lab.py", "skill/references/portability.md",
         "release.json", "dependencies.lock.json", "portable_setup.py", "prepare_portable_linux.py",
         "Start-Here.ps1", "test_portable_setup.py", "project-profile.example.json", "PORTABILITY-VALIDATION.json",
         "web_mcp.py", "prepare_web_connection.py", "Connect-WebLab.ps1", "web-connection.lock.json",
         "test_web_connection.py", "accept_web_connection.py", "WEB-CONNECTION-VALIDATION.json",
         "skill/references/web-connection.md"]
DOCS = ["ISOLATED-DEVELOPMENT-LAB.md", "ISOLATED-LAB-GUEST-TOOLS.md", "ISOLATED-LAB-WINDOWS-SETUP.md", "ISOLATED-LAB-PORTABILITY.md", "ISOLATED-LAB-WEB-CONNECTION.md"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--archive-only", action="store_true", help="Build verified bundle without replacing deployed source")
    args = parser.parse_args()
    lab = Lab(args.config)
    if not args.archive_only and any(g.get("running") for g in lab.status().values()):
        raise RuntimeError("Stop owned guests before replacing deployed source; archive-only does not replace it")
    repo = Path(__file__).resolve().parents[2]
    names = ["examples/isolated-lab/" + name for name in FILES] + ["docs/" + name for name in DOCS]
    version = json.loads(Path(__file__).with_name("release.json").read_text())["version"]
    manifest = {"version": version, "created": datetime.now(timezone.utc).isoformat(),
                "coverage": "authored source and sanitized knowledge; no disks, credentials, binaries or raw logs",
                "files": []}
    contents = {}
    for relative in names:
        data = (repo / relative).read_bytes()
        contents[relative] = data
        digest = hashlib.sha256(data).hexdigest()
        if not args.archive_only:
            target = lab.inside(lab.root / "source" / relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            if sha256(target) != digest:
                raise RuntimeError("Deployed source readback failed")
        manifest["files"].append({"path": relative, "bytes": len(data), "sha256": digest})
    if not args.archive_only:
        for source, target in (("LAB-ROOT-README.md", "README.md"),
                               ("LAB-ROOT-AGENTS.template.md", "AGENTS.md"), ("Lab.ps1", "Lab.ps1")):
            data = contents["examples/isolated-lab/" + source]
            lab.inside(lab.root / target).write_bytes(data)
    archive = lab.inside(lab.root / ("isolated-lab-source-" + version + "-" + stamp() + "-" + __import__('uuid').uuid4().hex[:8] + ".zip"))
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as z:
        for relative, data in contents.items():
            z.writestr(relative, data)
        z.writestr("SOURCE-MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(archive) as z:
        for entry in manifest["files"]:
            if hashlib.sha256(z.read(entry["path"])).hexdigest() != entry["sha256"]:
                raise RuntimeError("Archive readback failed")
    receipt = {"source_archive": str(archive), "archive_sha256": sha256(archive),
               "file_count": len(names), "copied": not args.archive_only, "byte_verified": True,
               "coverage": manifest["coverage"]}
    write_json(lab.private / ("source-receipt-" + version + "-" + stamp() + ".json"), receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
