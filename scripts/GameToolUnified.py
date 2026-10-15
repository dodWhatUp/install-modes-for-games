"""Explicit local source updates. No uninstall, downloads, game or input runner.

Keep private user data outside immutable versions. Snapshot before fixed Studio
file replacement; commit the version pointer last. SHA-256 is integrity, not a
publisher signature: select archives from a trusted source.
"""
from __future__ import annotations
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import uuid
import zipfile

VERSION = "0.2.1"
BOOTSTRAP = "scripts/Start-UnifiedTools.pyw"
SOURCE_LOCK = ".game-tools-owner.lock"
STUDIO = {
    "AzeronOverlayStudio.ahk": "examples/game-input/AzeronOverlayStudio.integrated.ahk",
    **{n: "examples/game-input/" + n for n in
       ("GameInputModule.ahk", "OverlayStudioGameInput.ahk", "StudioPictureModule.ahk",
        "StudioOverlayGroups.ahk", "StudioHubBridge.ahk")},
}
REQUIRED = {*STUDIO.values(), "scripts/Game-Tool-Hub.py", "scripts/GameToolUnified.py",
            "scripts/GameToolUnifiedPanel.py", "scripts/Start-UnifiedTools.pyw",
            "scripts/GameToolKeybindIntegration.py", "scripts/game_keybind_ops/core.py",
            "schemas/game-pack.schema.json", "scripts/GameToolInstances.py",
            "scripts/GameToolPlanning.py", "scripts/GameToolMO2Read.py",
            "scripts/Game-Instances.py", "schemas/game-tools-goal-plan.schema.json",
            "schemas/mo2-profile-state.schema.json"}
MAX_BYTES = 32 * 1024 * 1024
BLOCKED = {"skyrimse.exe", "skyrimvr.exe", "cyberpunk2077.exe", "obs64.exe", "obs32.exe",
           "presentmon.exe", "presentmonconsole.exe", "frameview.exe", "capframex.exe"}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def version_tag(value):
    if not isinstance(value, str) or not re.fullmatch(r"hub-[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)?-[a-f0-9]{12}", value):
        raise ValueError("Invalid immutable version pointer.")
    return value

def acquire_source_lease(directory, purpose):
    """Cooperative ownership shared by all installs using these Studio sources.

    A process crash leaves a fail-closed marker for explicit recovery inspection.
    It is not an OS-wide lock and cannot prevent an unrelated standalone launch.
    """
    p = local_path(Path(directory) / SOURCE_LOCK)
    token = {"schema_version": 1, "token": uuid.uuid4().hex, "pid": os.getpid(), "purpose": purpose}
    raw = (json.dumps(token, sort_keys=True) + "\n").encode()
    with p.open("xb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    return {"path": p, "raw": raw}

def release_source_lease(lease):
    if lease is not None and read_bytes(lease["path"]) == lease["raw"]:
        lease["path"].unlink()  # Remove only this owner's exact marker.
    elif lease is not None:
        raise ValueError("Source ownership marker changed; preserve it for inspection.")

def local_path(value):
    p = Path(value)
    if not p.is_absolute() or p == Path(p.anchor) or str(p).startswith("\\\\"):
        raise ValueError("Use a named absolute local path.")
    for node in (p, *p.parents):
        if node.is_symlink() or (node.exists() and getattr(node.stat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("Linked/reparse paths are refused.")
    return p

def read_bytes(path, limit=MAX_BYTES):
    p = local_path(path)
    before = p.stat()
    if before.st_size > limit:
        raise ValueError("File exceeds the bounded limit.")
    with p.open("rb") as f:
        raw = f.read(limit + 1)
    after = p.stat()
    if len(raw) != before.st_size or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != \
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("Source changed while being inspected.")
    return raw

def load_json(path):
    return json.loads(read_bytes(path, 2 * 1024 * 1024).decode("utf-8-sig"))

def atomic_json(path, value):
    p = local_path(path)
    tmp = p.with_name(p.name + ".pending-" + uuid.uuid4().hex)
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
    with tmp.open("xb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)

def member_name(name):
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_./+\-]+", name):
        raise ValueError("Unsafe archive member name.")
    p = PurePosixPath(name)
    if p.is_absolute() or ".." in p.parts or str(p) != name or not p.parts or \
            p.parts[0] not in {"scripts", "examples", "docs", "templates", "preferences", "schemas", "game-packs"} and name != "AGENTS.md":
        raise ValueError("Archive member is outside the curated source layout.")
    for segment in p.parts:
        if segment.endswith(".") or segment.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *("COM"+str(i) for i in range(1,10)), *("LPT"+str(i) for i in range(1,10))}:
            raise ValueError("Reserved Windows archive member.")
    return name

def check_manifest(manifest, payloads):
    if manifest.get("schema_version") != 1 or manifest.get("bundle") != "GameTools":
        raise ValueError("Expected a GameTools authored-source manifest.")
    rows = manifest.get("files")
    versions = manifest.get("component_versions", {})
    if not isinstance(rows, list) or not 1 <= len(rows) <= 512:
        raise ValueError("Invalid bounded source inventory.")
    for key in ("tool_hub", "overlay_studio", "instances", "planning", "mo2_read"):
        if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)?", str(versions.get(key, ""))):
            raise ValueError("Invalid component version.")
    seen = set()
    for row in rows:
        name = member_name(row["path"])
        if name.casefold() in seen:
            raise ValueError("Duplicate source inventory member.")
        seen.add(name.casefold())
        raw = payloads.get(name)
        if type(row.get("bytes")) is not int or raw is None or len(raw) != row["bytes"] or \
                digest(raw) != str(row.get("sha256", "")).lower():
            raise ValueError("Manifest size/hash mismatch: " + name)
    if set(payloads) != {r["path"] for r in rows} or not REQUIRED <= set(payloads):
        raise ValueError("Missing required or unlisted source members.")
    if sum(len(v) for v in payloads.values()) > MAX_BYTES:
        raise ValueError("Uncompressed package exceeds the bounded limit.")
    # Source version labels must agree with the inventory, without executing it.
    for name, key, expression in (
        ("scripts/Game-Tool-Hub.py", "tool_hub", r'^VERSION = "([^"]+)"'),
        (STUDIO["AzeronOverlayStudio.ahk"], "overlay_studio", r'\s*this.Version := "([^"]+)"'),
        ("scripts/GameToolInstances.py", "instances", r'^VERSION = "([^"]+)"'),
        ("scripts/GameToolPlanning.py", "planning", r'^VERSION = "([^"]+)"'),
        ("scripts/GameToolMO2Read.py", "mo2_read", r'^VERSION = "([^"]+)"')):
        labels = re.findall(expression, payloads[name].decode("utf-8-sig"), re.M)
        if labels != [versions[key]]:
            raise ValueError("Source version does not agree with manifest.")
    return manifest

def inspect_archive(archive, expected_sha256):
    if not re.fullmatch(r"[a-fA-F0-9]{64}", expected_sha256):
        raise ValueError("Enter the trusted package's exact SHA-256 first.")
    raw = read_bytes(archive)
    if digest(raw) != expected_sha256.lower():
        raise ValueError("Package SHA-256 differs from the expected checkpoint.")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        entries = z.infolist()
        if len(entries) > 513 or sum(e.file_size for e in entries) > MAX_BYTES + 2 * 1024 * 1024:
            raise ValueError("Archive bounds exceeded.")
        names = set(); payloads = {}; manifest = None
        for e in entries:
            if e.filename != e.orig_filename:
                raise ValueError("Archive member normalization is refused.")
            if e.is_dir() or e.flag_bits & 1 or stat.S_ISLNK(e.external_attr >> 16):
                raise ValueError("Directories, encrypted or linked members are refused.")
            if e.filename.casefold() in names:
                raise ValueError("Duplicate/case-colliding archive member.")
            names.add(e.filename.casefold())
            data = z.read(e)
            if e.filename == "MANIFEST.json":
                if len(data) > 2 * 1024 * 1024:
                    raise ValueError("Manifest is too large.")
                manifest = json.loads(data.decode("utf-8-sig"))
            else:
                payloads[member_name(e.filename)] = data
    if not isinstance(manifest, dict):
        raise ValueError("Package has no root manifest.")
    check_manifest(manifest, payloads)
    return {"manifest": manifest, "payloads": payloads, "sha256": digest(raw)}

def inspect_directory(path):
    p = local_path(path)
    manifest = load_json(p / "MANIFEST.json")
    payloads = {member_name(r["path"]): read_bytes(p / r["path"]) for r in manifest["files"]}
    check_manifest(manifest, payloads)
    return {"manifest": manifest, "payloads": payloads,
            "sha256": digest(read_bytes(p / "MANIFEST.json"))}

def process_names():
    if os.name != "nt":
        raise ValueError("Live update safety checks require Windows.")
    r = subprocess.run(["tasklist.exe", "/FO", "CSV", "/NH"], capture_output=True,
                       text=True, errors="replace", timeout=8, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    return {row[0].lower() for row in csv.reader(io.StringIO(r.stdout)) if len(row) >= 2}

def assert_idle(names=None):
    names = process_names() if names is None else {n.lower() for n in names}
    blocked = sorted(n for n in names if n in BLOCKED or n.startswith("autohotkey"))
    if blocked:
        raise ValueError("Close relevant games/capture/benchmark/AHK owners normally before updating: " + ", ".join(blocked))

def studio_hashes(directory):
    p = local_path(directory)
    return {name: digest(read_bytes(p / name)) if (p / name).exists() else "absent" for name in STUDIO}

def read_install(root):
    root = local_path(root)
    value = load_json(root / "install.json")
    if value.get("schema_version") != 1:
        raise ValueError("Unknown unified installation schema.")
    for k in ("studio_dir", "studio_settings", "data_dir", "pythonw", "ahk"):
        local_path(value[k])
    version_tag(value["current"])
    if value.get("previous") is not None:
        version_tag(value["previous"])
    return value

def verify_current(root, value):
    release = inspect_directory(local_path(root) / "versions" / value["current"])
    if studio_hashes(value["studio_dir"]) != value["studio_hashes"]:
        raise ValueError("Installed Studio source drift. Reconcile newer changes before replacing them.")
    return release

def _copy_version(root, release):
    versions = release["manifest"]["component_versions"]
    tag = version_tag("hub-" + versions["tool_hub"] + "-" + release["sha256"][:12])
    target = local_path(root) / "versions" / tag
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        old = inspect_directory(target)
        if old["payloads"] != release["payloads"] or old["manifest"] != release["manifest"]:
            raise ValueError("Existing immutable version differs; never overwrite it.")
        return tag
    target.mkdir()  # Never merge or overwrite immutable version directories.
    for name, raw in release["payloads"].items():
        dest = local_path(target / name)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as f:
            f.write(raw); f.flush(); os.fsync(f.fileno())
        if read_bytes(dest) != raw:
            raise ValueError("Staged byte readback differs; preserve incomplete stage.")
    atomic_json(target / "MANIFEST.json", release["manifest"])
    inspect_directory(target)
    return tag

def _snapshot(root, value):
    recovery = local_path(root) / "recovery" / uuid.uuid4().hex
    recovery.mkdir(parents=True)
    originals = {}
    for name in STUDIO:
        p = local_path(Path(value["studio_dir"]) / name)
        originals[name] = read_bytes(p) if p.exists() else None
        if originals[name] is not None:
            _recovery_file(recovery / name, originals[name])
            if read_bytes(recovery / name) != originals[name]:
                raise ValueError("Recovery readback differs.")
    # Profiles/assets stay in place, not copied into public source versions.
    settings = local_path(value["studio_settings"])
    if settings.exists():
        raw = read_bytes(settings)
        _recovery_file(recovery / "settings.ini.backup", raw)
        if read_bytes(recovery / "settings.ini.backup") != raw:
            raise ValueError("Settings recovery readback differs.")
    atomic_json(recovery / "before.json", value)
    bootstrap = Path(root) / "Start-UnifiedTools.pyw"
    if bootstrap.exists():
        _recovery_file(recovery / "Start-UnifiedTools.pyw.backup", read_bytes(bootstrap))
    return recovery, originals

def _recovery_file(path, raw):
    with local_path(path).open("xb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    if read_bytes(path) != raw:
        raise ValueError("Durable recovery readback differs.")

def _replace_file(path, raw):
    p = local_path(path)
    tmp = p.with_name(p.name + ".update-" + uuid.uuid4().hex)
    with tmp.open("xb") as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)
    if read_bytes(p) != raw:
        raise ValueError("Installed source readback differs.")

def apply_release(root, release, *, expected_state_sha256, expected_studio, initial=None, names=None):
    """Explicit mutation of six owned source files and version pointer only."""
    root = local_path(root)
    assert_idle(names)
    current_path = root / "install.json"
    if initial is None:
        old_raw = read_bytes(current_path)
        if digest(old_raw) != expected_state_sha256:
            raise ValueError("Installation changed since preview.")
        value = read_install(root)
        current_release = verify_current(root, value)
        old_bootstrap = read_bytes(root / "Start-UnifiedTools.pyw")
        if old_bootstrap != current_release["payloads"][BOOTSTRAP]:
            raise ValueError("Stable launcher source drift; reconcile it before updating.")
    else:
        if root.exists():
            raise ValueError("Initial installation needs a new named folder.")
        value = dict(initial)
        for k in ("studio_dir", "studio_settings", "data_dir", "pythonw", "ahk"):
            local_path(value[k])
        old_raw = None
        old_bootstrap = None
    check_manifest(release["manifest"], release["payloads"])
    before = studio_hashes(value["studio_dir"])
    if before != expected_studio:
        raise ValueError("Installed Studio changed since the authorized preview.")
    lease = acquire_source_lease(value["studio_dir"], "source-update")
    # Cooperative update lock. A crashed transaction stays blocked for inspection.
    lock = root / "update.lock"
    try:
        root.mkdir(parents=True, exist_ok=initial is None)
        with lock.open("xb") as f:
            f.write(b"Explicit update in progress; do not remove until recovery inspected.\n"); f.flush(); os.fsync(f.fileno())
    except Exception:
        release_source_lease(lease)
        raise
    safe_to_unlock = False
    bootstrap_changed = False
    try:
        recovery, originals = _snapshot(root, value)
        tag = _copy_version(root, release)
        new_hashes = {name: digest(release["payloads"][source]) for name, source in STUDIO.items()}
        transaction = {"schema_version": 1, "phase": "prepared", "before": value,
                       "new_version": tag, "before_hashes": before, "after_hashes": new_hashes,
                       "coverage": "six source files, stable launcher, pointer and copied INI; no data/profile/overlay rewrite"}
        atomic_json(recovery / "transaction.json", transaction)
        changed = []
        try:
            assert_idle(names)
            if studio_hashes(value["studio_dir"]) != before or \
                    (read_bytes(current_path) != old_raw if old_raw is not None else current_path.exists()):
                raise ValueError("Target drift before source replacement.")
            for name, source in STUDIO.items():
                changed.append(name)
                _replace_file(Path(value["studio_dir"]) / name, release["payloads"][source])
            if old_bootstrap is not None and read_bytes(root / "Start-UnifiedTools.pyw") != old_bootstrap:
                raise ValueError("Stable launcher changed during update.")
            if old_bootstrap is None:
                _recovery_file(root / "Start-UnifiedTools.pyw", release["payloads"][BOOTSTRAP])
            else:
                bootstrap_changed = True  # A readback failure may follow a completed swap.
                _replace_file(root / "Start-UnifiedTools.pyw", release["payloads"][BOOTSTRAP])
            bootstrap_changed = True
            # Recheck the whole inventory, not just each earlier write individually.
            assert_idle(names)
            if studio_hashes(value["studio_dir"]) != new_hashes or \
                    read_bytes(root / "Start-UnifiedTools.pyw") != release["payloads"][BOOTSTRAP] or \
                    (read_bytes(current_path) != old_raw if old_raw is not None else current_path.exists()):
                raise ValueError("Concurrent source/pointer change before commit.")
            transaction["phase"] = "sources_verified"
            atomic_json(recovery / "transaction.json", transaction)
            new_value = {**value, "schema_version": 1, "current": tag,
                         "previous": value.get("current"), "studio_hashes": new_hashes,
                         "bootstrap_sha256": digest(release["payloads"][BOOTSTRAP]),
                         "recovery": str(recovery), "component_versions": release["manifest"]["component_versions"]}
            atomic_json(current_path, new_value)  # Commit last.
        except Exception:
            # Roll back only owned bytes which still equal our attempted version.
            for name in reversed(changed):
                p = Path(value["studio_dir"]) / name
                if p.exists() and digest(read_bytes(p)) == new_hashes[name]:
                    if originals[name] is None:
                        p.unlink()
                    else:
                        _replace_file(p, originals[name])
            bootstrap = root / "Start-UnifiedTools.pyw"
            if bootstrap_changed and bootstrap.exists() and read_bytes(bootstrap) == release["payloads"][BOOTSTRAP]:
                if old_bootstrap is None:
                    bootstrap.unlink()
                else:
                    _replace_file(bootstrap, old_bootstrap)
            transaction["phase"] = "failed_conditional_recovery"
            atomic_json(recovery / "transaction.json", transaction)
            safe_to_unlock = studio_hashes(value["studio_dir"]) == before and \
                (read_bytes(bootstrap) == old_bootstrap if old_bootstrap is not None else not bootstrap.exists()) and \
                (read_bytes(current_path) == old_raw if old_raw is not None else not current_path.exists())
            raise
        transaction["phase"] = "committed"
        atomic_json(recovery / "transaction.json", transaction)
        safe_to_unlock = True
        return new_value
    finally:
        # Leave a failed partial source swap locked for explicit recovery inspection.
        if safe_to_unlock:
            lock.unlink()
            release_source_lease(lease)

def rollback_previous(root, *, expected_state_sha256, names=None):
    root = local_path(root)
    value = read_install(root)
    previous = value.get("previous")
    if not previous:
        raise ValueError("No previous unified version is available. The initial private backup remains separate.")
    version_tag(previous)
    release = inspect_directory(root / "versions" / previous)
    # Re-stage as a unique immutable checkpoint; keep both prior source versions.
    release["sha256"] = digest((release["sha256"] + uuid.uuid4().hex).encode())
    return apply_release(root, release, expected_state_sha256=expected_state_sha256,
                         expected_studio=value["studio_hashes"], names=names)

def launch_command(root):
    root = local_path(root)
    value = read_install(root)
    verify_current(root, value)
    if (root / "update.lock").exists():
        raise ValueError("An update transaction requires inspection before launch.")
    if (Path(value["studio_dir"]) / SOURCE_LOCK).exists():
        raise ValueError("Studio sources are owned or require recovery inspection before launch.")
    return [value["pythonw"], "-B", str(root / "versions" / value["current"] / "scripts/Game-Tool-Hub.py"),
            "--data-dir", value["data_dir"], "--unified-install", str(root)]
