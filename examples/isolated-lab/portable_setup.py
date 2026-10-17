"""Install a verified source release and machine-local Codex skill binding.

Standard library only. No VM start, downloads, host input, or account sync.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import uuid
import zipfile

MAX_BUNDLE = 8 * 1024 * 1024
PREFIX = "examples/isolated-lab/"
ALLOWED_EXTENSIONS = {".py", ".ps1", ".md", ".json", ".sh", ".yaml"}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temporary.write_bytes(data)
    os.replace(temporary, path)


def save_json(path, data):
    atomic(path, (json.dumps(data, indent=2) + "\n").encode())


def safe_name(name):
    if not isinstance(name, str) or "\\" in name or ":" in name or re.search(r'[<>"|?*\x00-\x1f]', name):
        raise ValueError("Nonportable archive path")
    pieces = name.split("/")
    if any(p in ("", ".", "..") or p.endswith((".", " ")) for p in pieces):
        raise ValueError("Unsafe archive path")
    for piece in pieces:
        if re.match(r"(?i)^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", piece):
            raise ValueError("Reserved Windows archive name")
    if any(p.lower() in ("private", "artifacts", "vms", "downloads", "machine.json") for p in pieces):
        raise ValueError("Archive contains machine-private state")
    p = PurePosixPath(name)
    if name == "SOURCE-MANIFEST.json":
        return name
    if not (name.startswith(PREFIX) or name.startswith("docs/ISOLATED-")):
        raise ValueError("Archive outside the authored lab source")
    if p.suffix.lower() not in ALLOWED_EXTENSIONS or any(part.startswith(".") for part in pieces):
        raise ValueError("Archive contains non-source data")
    return name


def verify_bundle(bundle, expected_hash):
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_hash or ""):
        raise ValueError("Provide the independently received SHA256")
    bundle = Path(bundle)
    if bundle.stat().st_size > MAX_BUNDLE or digest(bundle) != expected_hash.lower():
        raise ValueError("Source bundle SHA256 or size mismatch")
    contents = {}
    folded = set()
    with zipfile.ZipFile(bundle) as z:
        if len(z.infolist()) > 150 or sum(i.file_size for i in z.infolist()) > MAX_BUNDLE:
            raise ValueError("Source bundle exceeds expansion budget")
        for i in z.infolist():
            name = safe_name(i.filename)
            if name.casefold() in folded or i.is_dir() or stat.S_ISLNK(i.external_attr >> 16):
                raise ValueError("Duplicate, directory or symlink source entry")
            folded.add(name.casefold())
            contents[name] = z.read(i)
    manifest = json.loads(contents.pop("SOURCE-MANIFEST.json"))
    entries = manifest["files"]
    declared = [safe_name(i["path"]) for i in entries]
    if len(set(declared)) != len(declared) or set(declared) != set(contents):
        raise ValueError("Source manifest and archive disagree")
    for entry in entries:
        data = contents[entry["path"]]
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Source manifest readback mismatch")
    release = json.loads(contents[PREFIX + "release.json"])
    if release["schema"] != 1 or release["version"] != manifest["version"]:
        raise ValueError("Unsupported or inconsistent source release")
    for required in ("lab.py", "Lab.ps1", "guest_mcp.py", "skill/SKILL.md", "skill/scripts/resolve_lab.py"):
        if PREFIX + required not in contents:
            raise ValueError("Incomplete source release")
    return manifest, contents


def dedicated_root(root):
    root = Path(root).expanduser().resolve()
    if root == Path(root.anchor) or root == Path.home().resolve():
        raise ValueError("Select a dedicated lab directory")
    if any(p.lower() in ("onedrive", ".git", ".codex", ".agents") or p.lower().startswith("onedrive -") for p in root.parts):
        raise ValueError("Lab runtime must be outside sync, Git and Codex configuration directories")
    for parent in (root, *root.parents):
        if (parent / ".git").exists():
            raise ValueError("Lab runtime must be outside a Git checkout")
    return root


def skill_directory():
    home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    existing = home / "skills/isolated-lab"
    modern = Path.home() / ".agents/skills/isolated-lab"
    if existing.exists() and modern.exists():
        raise ValueError("Two isolated-lab skills exist; reconcile their owner before installation")
    return existing if existing.exists() else modern


def check_owned_target(base, target):
    base = Path(base).resolve()
    target = Path(target)
    if base not in target.parents:
        raise ValueError("Installation target escaped its owned root")
    for path in (target, *target.parents):
        if path == base:
            break
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 1024:
                raise ValueError("Installation target contains a symlink or junction; preserve and reconcile it")


def host_preflight(root=None):
    supported = os.name == "nt" and platform.machine().lower() in ("amd64", "x86_64") and sys.version_info >= (3, 11)
    result = {"host": platform.system(), "architecture": platform.machine(),
              "python_version": platform.python_version(), "supported": supported,
              "codex_cli": bool(shutil.which("codex")), "ssh": bool(shutil.which("ssh.exe")),
              "ssh_keygen": bool(shutil.which("ssh-keygen.exe")),
              "automatic_vm_start": False, "other_host_ports": "not assumed"}
    if root:
        p = dedicated_root(root)
        probe = next(x for x in (p, *p.parents) if x.exists())
        result.update({"lab_root": str(p), "free_disk_gib": round(shutil.disk_usage(probe).free / 1024**3, 2),
                       "already_configured": (p / "private/config.json").exists()})
    return result


@contextmanager
def setup_lock(root):
    lock = root / "private/portable-setup.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("x", encoding="utf-8") as f:
        f.write(json.dumps({"pid": os.getpid(), "operation": "source installation"}))
    try:
        yield
    finally:
        lock.unlink()


def ensure_stopped(root):
    config = root / "private/config.json"
    if not config.exists():
        return
    code = root / "source/examples/isolated-lab/lab.py"
    result = subprocess.run([sys.executable, str(code), "--config", str(config), "status"],
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode or any(g.get("running") for g in json.loads(result.stdout).values()):
        raise RuntimeError("Source upgrade requires observed stopped guests; no guest was stopped automatically")


@contextmanager
def lifecycle_locks(root):
    """Hold the controller's operation locks through source replacement."""
    held = []
    try:
        if (root / "private/config.json").exists():
            for name in ("linux", "windows"):
                lock = root / "private" / (name + ".lock")
                with lock.open("x", encoding="utf-8") as f:
                    f.write(json.dumps({"pid": os.getpid(), "operation": "source upgrade; guests must remain stopped"}))
                held.append(lock)
        yield
    finally:
        for lock in reversed(held):
            lock.unlink()


def install(bundle, expected_hash, root, skill_root=None, upgrade=False, adopt_existing=False):
    # Verify all bytes before creating directories or touching installed files.
    manifest, contents = verify_bundle(bundle, expected_hash)
    root = dedicated_root(root)
    skill = Path(skill_root).resolve() if skill_root else skill_directory().resolve()
    if skill.name != "isolated-lab" or root == skill or root in skill.parents or skill in root.parents:
        raise ValueError("Skill and lab must be separate dedicated locations")
    if root.exists() and any(root.iterdir()) and not ((root / "source/examples/isolated-lab/lab.py").exists()):
        raise ValueError("Refusing a nonempty unrecognized lab directory")
    root.mkdir(parents=True, exist_ok=True)
    with setup_lock(root), lifecycle_locks(root):
        ensure_stopped(root)
        previous = root / "private/portable-install.json"
        if previous.exists():
            old = read_json(previous)
            for name, value in old["installed_hashes"].items():
                path = Path(name)
                if not path.is_file() or digest(path) != value:
                    raise RuntimeError("Installed source or skill was edited locally; preserve and reconcile it first")
            if old["version"] != manifest["version"] and not upgrade:
                raise RuntimeError("A version change needs explicit --upgrade")
        elif skill.exists():
            if not adopt_existing:
                raise RuntimeError("Existing skill has no installation receipt; inspect its source and use explicit --adopt-existing")
            # Adoption is allowed only for our previously authored skill with exact name.
            if "name: isolated-lab" not in (skill / "SKILL.md").read_text(encoding="utf-8-sig"):
                raise RuntimeError("Existing skill is owned by a different workflow")
        changes = {root / "source" / name: data for name, data in contents.items()}
        changes[root / "source/SOURCE-MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
        changes.update({root / target: contents[PREFIX + source] for source, target in
                        (("Lab.ps1", "Lab.ps1"), ("LAB-ROOT-README.md", "README.md"),
                         ("LAB-ROOT-AGENTS.template.md", "AGENTS.md"))})
        for name, data in contents.items():
            if name.startswith(PREFIX + "skill/"):
                changes[skill / name.removeprefix(PREFIX + "skill/")] = data
        binding = {"schema": 1, "lab_root": str(root), "source_version": manifest["version"],
                   "bundle_sha256": expected_hash.lower(), "guest_acceptance": "machine-local; inspect private/acceptance.json"}
        changes[skill / "machine.json"] = (json.dumps(binding, indent=2) + "\n").encode()
        changes[root / "private/runtime.json"] = (json.dumps({"python": sys.executable, "version": platform.python_version()}, indent=2) + "\n").encode()
        for target in changes:
            check_owned_target(skill if skill in target.parents else root, target)
        # Every replaced byte is backed up before the first write. New files are also tracked.
        transaction = root / "private/source-upgrades" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
        transaction.mkdir(parents=True)
        if previous.exists():
            (transaction / "previous-install.json").write_bytes(previous.read_bytes())
        entries = []
        for number, (target, data) in enumerate(changes.items()):
            backup = transaction / str(number)
            original = target.read_bytes() if target.exists() else None
            if original is not None:
                backup.write_bytes(original)
            entries.append({"target": str(target), "before": hashlib.sha256(original).hexdigest() if original is not None else None,
                            "after": hashlib.sha256(data).hexdigest(), "backup": str(backup) if original is not None else None})
        transaction_record = {"state": "PREPARED", "lab_root": str(root), "skill": str(skill), "entries": entries}
        save_json(transaction / "transaction.json", transaction_record)
        for (target, data), entry in zip(changes.items(), entries):
            check_owned_target(skill if skill in target.parents else root, target)
            current = digest(target) if target.exists() else None
            if current != entry["before"]:
                raise RuntimeError("Concurrent source edit; transaction preserved for reconciliation")
            atomic(target, data)
            if digest(target) != entry["after"]:
                raise RuntimeError("Installed source readback failed")
        if not (root / "private/acceptance.json").exists():
            save_json(root / "private/acceptance.json", {"schema": 1, "linux": "NOT_TESTED_ON_THIS_HOST", "windows": "NOT_TESTED_ON_THIS_HOST"})
        receipt = {"schema": 1, "version": manifest["version"], "bundle_sha256": expected_hash.lower(),
                   "installed_hashes": {str(p): digest(p) for p in changes}, "skill": str(skill),
                   "transaction": str(transaction), "mcp_registration": "separate supported configure_mcp.py step",
                   "VM_started": False, "credentials_copied": False}
        save_json(root / "private/portable-install.json", receipt)
        transaction_record["state"] = "COMMITTED"
        save_json(transaction / "transaction.json", transaction_record)
        return {"installed": True, "version": manifest["version"], "lab_root": str(root),
                "skill": str(skill), "files_byte_verified": len(changes), "VM_started": False,
                "transaction": str(transaction), "next": "prepare_portable_linux.py or inspect existing machine acceptance, then configure_mcp.py"}


def verify_install(root):
    root = dedicated_root(root)
    receipt = read_json(root / "private/portable-install.json")
    changed = [name for name, value in receipt["installed_hashes"].items() if not Path(name).is_file() or digest(name) != value]
    return {"ok": not changed, "version": receipt["version"], "changed_files": changed,
            "acceptance": read_json(root / "private/acceptance.json"), "current_chat_MCP": "inspect actual catalog; registration alone is insufficient"}


def bind_skill(bundle, expected_hash, root, skill_root=None, adopt_existing=False):
    """Update instructions/binding only; running guest/source is untouched."""
    manifest, contents = verify_bundle(bundle, expected_hash)
    root = dedicated_root(root)
    skill = Path(skill_root).resolve() if skill_root else skill_directory().resolve()
    if not (root / "source/examples/isolated-lab/lab.py").is_file() or not (root / "private/config.json").is_file():
        raise RuntimeError("Skill-only binding requires an existing configured lab")
    config = read_json(root / "private/config.json")
    if Path(config["root"]).resolve() != root or skill.name != "isolated-lab" or root in skill.parents or skill in root.parents:
        raise ValueError("Invalid lab/skill binding")
    with setup_lock(root):
        previous = root / "private/skill-install.json"
        source_receipt = root / "private/portable-install.json"
        source_record = read_json(source_receipt) if source_receipt.exists() else None
        if source_record:
            for name, value in source_record["installed_hashes"].items():
                if skill in Path(name).parents and (not Path(name).is_file() or digest(name) != value):
                    raise RuntimeError("Locally edited installed skill preserved")
        if previous.exists():
            for name, value in read_json(previous)["installed_hashes"].items():
                if not Path(name).is_file() or digest(name) != value:
                    raise RuntimeError("Locally edited skill preserved; reconcile before updating it")
        elif skill.exists() and not adopt_existing:
            raise RuntimeError("Inspect existing skill and use explicit --adopt-existing")
        if skill.exists() and "name: isolated-lab" not in (skill / "SKILL.md").read_text(encoding="utf-8-sig"):
            raise RuntimeError("Different skill owner preserved")
        files = {skill / n.removeprefix(PREFIX + "skill/"): d for n, d in contents.items() if n.startswith(PREFIX + "skill/")}
        files[skill / "machine.json"] = (json.dumps({"schema": 1, "lab_root": str(root),
            "workflow_version": manifest["version"], "bundle_path": str(Path(bundle).resolve()),
            "bundle_sha256": expected_hash.lower(), "runtime_source": "preserved; inspect this lab's actual capability"}, indent=2) + "\n").encode()
        transaction = root / "private/skill-upgrades" / uuid.uuid4().hex
        transaction.mkdir(parents=True)
        entries = []
        for number, (target, data) in enumerate(files.items()):
            check_owned_target(skill, target)
            backup = transaction / str(number)
            original = target.read_bytes() if target.exists() else None
            if original is not None:
                backup.write_bytes(original)
            entries.append({"target": str(target), "before": hashlib.sha256(original).hexdigest() if original is not None else None,
                            "after": hashlib.sha256(data).hexdigest(), "backup": str(backup) if original is not None else None})
        record = {"state": "PREPARED", "lab_root": str(root), "skill": str(skill), "entries": entries, "kind": "skill-only"}
        save_json(transaction / "transaction.json", record)
        for (target, data), entry in zip(files.items(), entries):
            check_owned_target(skill, target)
            if (digest(target) if target.exists() else None) != entry["before"]:
                raise RuntimeError("Concurrent skill edit preserved")
            atomic(target, data)
            if digest(target) != entry["after"]:
                raise RuntimeError("Skill readback failed")
        record["state"] = "COMMITTED"
        save_json(transaction / "transaction.json", record)
        save_json(previous, {"version": manifest["version"], "bundle_sha256": expected_hash.lower(),
                            "installed_hashes": {str(p): digest(p) for p in files}, "transaction": str(transaction)})
        if source_record:
            for target in files:
                source_record["installed_hashes"][str(target)] = digest(target)
            source_record["skill_only_update"] = str(transaction)
            save_json(source_receipt, source_record)
        return {"skill_bound": True, "files_byte_verified": len(files), "version": manifest["version"],
                "skill": str(skill), "lab_root": str(root), "running_source_changed": False, "VM_lifecycle_changed": False}


def rollback(root, transaction):
    root = dedicated_root(root)
    transaction = Path(transaction).resolve()
    if (root / "private/source-upgrades").resolve() not in transaction.parents:
        raise ValueError("Recovery transaction must belong to this lab")
    record = read_json(transaction / "transaction.json")
    if Path(record["lab_root"]).resolve() != root or record["state"] != "COMMITTED":
        raise ValueError("Only this lab's committed source transaction can be rolled back")
    skill = Path(record["skill"]).resolve()
    with setup_lock(root), lifecycle_locks(root):
        ensure_stopped(root)
        for entry in record["entries"]:
            target = Path(entry["target"]).resolve()
            if root not in target.parents and skill not in target.parents:
                raise ValueError("Recovery target outside owned source/skill")
            check_owned_target(skill if skill in Path(entry["target"]).parents else root, Path(entry["target"]))
            if not target.is_file() or digest(target) != entry["after"]:
                raise RuntimeError("Later edits detected; recovery refused without overwriting them")
            if entry["backup"]:
                backup = Path(entry["backup"]).resolve()
                if transaction not in backup.parents or digest(backup) != entry["before"]:
                    raise RuntimeError("Recovery baseline hash/path mismatch")
        for entry in record["entries"]:
            target = Path(entry["target"])
            if entry["backup"]:
                atomic(target, Path(entry["backup"]).read_bytes())
            else:
                target.unlink()
        previous = transaction / "previous-install.json"
        receipt = root / "private/portable-install.json"
        if previous.exists():
            atomic(receipt, previous.read_bytes())
        elif receipt.exists():
            receipt.unlink()
        record["state"] = "ROLLED_BACK"
        save_json(transaction / "transaction.json", record)
        return {"rolled_back": True, "files": len(record["entries"]), "guest_disk_changed": False,
                "MCP_registration_changed": False, "acceptance": "reinspect restored source; runtime acceptance remains separately recorded"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=("preflight", "install", "bind-skill", "verify", "rollback"))
    p.add_argument("--lab-root")
    p.add_argument("--bundle")
    p.add_argument("--sha256")
    p.add_argument("--skill-root", help="Override discovered user skill location")
    p.add_argument("--upgrade", action="store_true")
    p.add_argument("--adopt-existing", action="store_true", help="Adopt an inspected existing owned skill with a full source backup")
    p.add_argument("--transaction")
    args = p.parse_args()
    try:
        if args.action == "preflight":
            result = host_preflight(args.lab_root)
        elif not args.lab_root:
            raise ValueError("Select --lab-root")
        elif args.action == "install":
            if not host_preflight(args.lab_root)["supported"]:
                raise RuntimeError("Current host adapter supports Windows x64 with Python 3.11+ only")
            result = install(args.bundle, args.sha256, args.lab_root, args.skill_root, args.upgrade, args.adopt_existing)
        elif args.action == "bind-skill":
            result = bind_skill(args.bundle, args.sha256, args.lab_root, args.skill_root, args.adopt_existing)
        elif args.action == "rollback":
            result = rollback(args.lab_root, args.transaction)
        else:
            result = verify_install(args.lab_root)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok", True) else 2
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
