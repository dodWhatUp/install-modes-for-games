"""Install a hash-verified local source/skill and append the scoped Codex default.

No VM provisioning, account access, keys, host input or MCP configuration changes.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

from contracts import canonical, digest, publish, relative


def upgrade(source, root, skill_dir):
    """Rebind this owned installation while preserving prior source and guidance."""
    binding_file = skill_dir / "machine.json"
    old_bytes = binding_file.read_bytes()
    binding = json.loads(old_bytes)
    previous = Path(binding["source"])
    old_manifest = (previous / "MAC-SOURCE-MANIFEST.json").read_bytes()
    if digest(old_manifest) != binding["source_sha256"]:
        raise ValueError("Prior installed source changed; preserve and inspect")
    for entry in json.loads(old_manifest)["files"]:
        p = previous / entry["path"]
        if p.is_symlink() or digest(p.read_bytes()) != entry["sha256"]:
            raise ValueError("Prior source changed")
        if entry["path"].startswith("skill/"):
            installed = skill_dir / entry["path"][len("skill/"):]
            if installed.is_symlink() or digest(installed.read_bytes()) != entry["sha256"]:
                raise ValueError("Installed skill has later edits; reconcile rather than overwrite")
    expected_skill = {p.relative_to(previous / "skill").as_posix() for p in (previous / "skill").rglob("*") if p.is_file()}
    actual_skill = {p.relative_to(skill_dir).as_posix() for p in skill_dir.rglob("*") if p.is_file()}
    if actual_skill != expected_skill | {"machine.json"}:
        raise ValueError("Unexpected installed skill files; preserve later work")
    raw = (source / "MAC-SOURCE-MANIFEST.json").read_bytes()
    manifest_hash = digest(raw)
    manifest = json.loads(raw)
    target = root / "source" / ("mac-" + manifest.get("version", "candidate") + "-" + manifest_hash[:12])
    target.mkdir(parents=True, mode=0o700, exist_ok=False)
    for entry in manifest["files"]:
        relative(entry["path"])
        p = source / entry["path"]
        if p.is_symlink() or not p.is_file() or len(p.read_bytes()) != entry["bytes"] or digest(p.read_bytes()) != entry["sha256"]:
            raise ValueError("New source integrity failure")
        publish(target, entry["path"], p.read_bytes(), entry["sha256"])
    publish(target, "MAC-SOURCE-MANIFEST.json", raw, manifest_hash)
    staging = skill_dir.parent / (".isolated-lab-upgrade-" + uuid.uuid4().hex)
    shutil.copytree(target / "skill", staging)
    binding.update(source=str(target), source_sha256=manifest_hash)
    (staging / "machine.json").write_bytes(canonical(binding))
    backup = skill_dir.parent / (".isolated-lab-before-" + uuid.uuid4().hex)
    if binding_file.read_bytes() != old_bytes:
        raise ValueError("Concurrent binding change; preserve it")
    skill_dir.rename(backup)
    staging.rename(skill_dir)
    return {"source": str(target), "source_sha256": manifest_hash, "previous_skill": str(backup),
            "global_instructions_changed": False, "VM_started": False}


def install(source, root, skill_dir, agents_file):
    if skill_dir.exists() or skill_dir.is_symlink():
        raise FileExistsError("Existing isolated-lab skill preserved; review its binding before merging")
    if agents_file.name != "AGENTS.md" or (agents_file.parent / "AGENTS.override.md").exists():
        raise ValueError("Resolve effective global override before installing defaults")
    if agents_file.is_symlink():
        raise ValueError("Global instruction symlink needs owner review")
    existing = agents_file.read_bytes() if agents_file.exists() else b""
    if b"<!-- BEGIN ISOLATEDLAB_DEVELOPMENT_DEFAULT -->" in existing:
        raise ValueError("Existing managed default preserved; reconcile rather than duplicate")
    manifest_path = source / "MAC-SOURCE-MANIFEST.json"
    raw = manifest_path.read_bytes()
    manifest = json.loads(raw)
    manifest_hash = digest(raw)
    for entry in manifest["files"]:
        relative(entry["path"])
        p = source / entry["path"]
        if p.is_symlink() or not p.is_file():
            raise ValueError("Source is not a regular file")
        data = p.read_bytes()
        if len(data) != entry["bytes"] or digest(data) != entry["sha256"]:
            raise ValueError("Source manifest mismatch")
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    private = root / "private"
    private.mkdir(mode=0o700, exist_ok=True)
    if private.stat().st_mode & 0o077:
        raise ValueError("Private state directory must have mode 700")
    target = root / "source" / ("mac-" + manifest.get("version", "candidate") + "-" + manifest_hash[:12])
    target.mkdir(parents=True, mode=0o700, exist_ok=False)
    for entry in manifest["files"]:
        data = (source / entry["path"]).read_bytes()
        publish(target, entry["path"], data, entry["sha256"])
    publish(target, manifest_path.name, raw, manifest_hash)
    skill_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = skill_dir.parent / (".isolated-lab-stage-" + uuid.uuid4().hex)
    shutil.copytree(target / "skill", staging)
    binding = {"schema": 1, "lab_root": str(root.resolve()), "source": str(target.resolve()),
               "source_sha256": manifest_hash, "runtime_accepted": False}
    (staging / "machine.json").write_bytes(canonical(binding))
    staging.rename(skill_dir)
    begin, end = "<!-- BEGIN ISOLATEDLAB_DEVELOPMENT_DEFAULT -->", "<!-- END ISOLATEDLAB_DEVELOPMENT_DEFAULT -->"
    block = "\n\n" + begin + "\n" + (
        "For compatible software-development tasks requiring browser or native-app interaction, "
        "use the locally enrolled isolated guest by default through the isolated-lab skill. "
        "Resolve its binding and readiness before GUI work; preserve project source masters, "
        "transfer selected files, test with DOM/accessibility readback, retrieve selected outputs, "
        "and clean up the owned workflow. Missing guest readiness requires scoped setup; "
        "never automatically use host mouse, keyboard, focus or display control as a fallback. "
        "Ordinary file edits and headless CLI work do not require a VM. Explicit host configuration "
        "or hardware requests retain their requested host scope. Preserve more specific user/project overrides. "
        "Installation or historical Windows acceptance does not prove this Mac's guest acceptance.\n"
    ) + end + "\n"
    agents_file.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(agents_file, os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.lseek(fd, 0, os.SEEK_SET)
        old = os.read(fd, 100000)
        if begin.encode() in old or end.encode() in old:
            raise ValueError("Existing managed default preserved; reconcile rather than duplicate")
        backup = "AGENTS-before-" + uuid.uuid4().hex + ".md"
        publish(private, backup, old, digest(old))
        written = os.write(fd, block.encode())
        if written != len(block.encode()):
            raise RuntimeError("Partial default append; inspect the same file before repair")
        os.fsync(fd)
    finally:
        os.close(fd)
    now = agents_file.read_bytes()
    if not now.startswith(old) or now.count(begin.encode()) != 1:
        raise ValueError("Global default readback failed; preserve effects for recovery")
    for entry in manifest["files"]:
        if digest((target / entry["path"]).read_bytes()) != entry["sha256"]:
            raise ValueError("Installed source readback mismatch")
    receipt = {"schema": 1, "source": str(target), "source_sha256": manifest_hash,
               "skill": str(skill_dir), "agents_file": str(agents_file),
               "previous_agents_sha256": digest(old), "installed_agents_sha256": digest(now),
               "backup": str(private / backup), "VM_started": False, "runtime_accepted": False}
    publish(private, "install-receipt-" + uuid.uuid4().hex + ".json", canonical(receipt), digest(canonical(receipt)))
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.home() / ".local/share/isolatedlab")
    p.add_argument("--skill-dir", type=Path, default=Path.home() / ".agents/skills/isolated-lab")
    p.add_argument("--agents-file", type=Path, default=Path.home() / ".codex/AGENTS.md")
    p.add_argument("--upgrade", action="store_true")
    args = p.parse_args()
    operation = upgrade(Path(__file__).resolve().parent, args.root, args.skill_dir) if args.upgrade else install(
        Path(__file__).resolve().parent, args.root, args.skill_dir, args.agents_file)
    print(json.dumps(operation, indent=2))
