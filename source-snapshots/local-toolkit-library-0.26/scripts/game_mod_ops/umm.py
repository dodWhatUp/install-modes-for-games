"""Kingmaker UMM adapter: inspect, new-folder deployment and conservative rollback.

No loader injection, overwrites, automatic upgrades, mod enabling or game launches.
The process guard is a best-effort observation, not an OS-wide exclusive lease.
"""
from __future__ import annotations
import ctypes
import os
import re
import time
import uuid
import zipfile
from pathlib import Path
from .archive import tree_audit
from .safety import (ModError, require, no_links, contained, regular, digest, read_json,
                     json_new, local_lock, copy_new, object_hash, slug)
from .workflow import Job

BLOCKED_PROCESSES = {"kingmaker.exe", "unitymodmanager.exe", "unitymodmanagerconsole.exe",
                     "steam.exe", "galaxyclient.exe", "epicgameslauncher.exe", "vortex.exe",
                     "modorganizer.exe"}
LOADER_RELATIVE = "Kingmaker_Data/Managed/UnityModManager/UnityModManager.dll"


def windows_process_names() -> set[str]:
    require(os.name == "nt", "WINDOWS_REQUIRED", "Live installation is implemented only on Windows; planning and staging work elsewhere.")
    from ctypes import wintypes
    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    k.Process32FirstW.restype = wintypes.BOOL
    k.Process32NextW.argtypes = k.Process32FirstW.argtypes
    k.Process32NextW.restype = wintypes.BOOL
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k.CreateToolhelp32Snapshot(2, 0)
    require(h not in (None, ctypes.c_void_p(-1).value), "PROCESS_STATE_UNKNOWN", "Cannot inspect running processes; installation is blocked.")
    entry = PROCESSENTRY32W(); entry.dwSize = ctypes.sizeof(entry)
    names = set()
    try:
        require(bool(k.Process32FirstW(h, ctypes.byref(entry))), "PROCESS_STATE_UNKNOWN", "Process inventory was unavailable.")
        while True:
            names.add(entry.szExeFile.casefold())
            if not k.Process32NextW(h, ctypes.byref(entry)):
                require(ctypes.get_last_error() == 18, "PROCESS_STATE_UNKNOWN", "Process enumeration ended unexpectedly.")
                break
    finally:
        k.CloseHandle(h)
    return names


def require_closed():
    running = windows_process_names() & BLOCKED_PROCESSES
    require(not running, "RUNNING_OWNER", "Close the game, mod managers and game-store clients before deployment: " + ", ".join(sorted(running)))


def version(value: str) -> tuple:
    require(isinstance(value, str) and bool(re.fullmatch(r"\d+(?:\.\d+){1,3}[a-z]?", value)),
            "VERSION_UNKNOWN", "Use the observed numeric release version, such as 2.1.7 or 0.33.2.")
    parts = tuple(int(x) for x in re.sub(r"[a-z]$", "", value).split("."))
    return parts + (0,) * (4 - len(parts))


def inventory(game_dir: Path) -> dict:
    root = no_links(game_dir)
    regular(contained(root, "Kingmaker.exe"))
    loader = contained(root, LOADER_RELATIVE)
    mods = contained(root, "Mods")
    records, unknown = [], []
    if mods.exists():
        require(mods.is_dir(), "BAD_GAME_LAYOUT", "Mods is not a directory.")
        children = list(mods.iterdir())
        require(len(children) <= 1000, "INVENTORY_LIMIT", "Mod inventory is too large for this preview.")
        for child in sorted(children):
            no_links(child)
            if not child.is_dir():
                unknown.append(child.name); continue
            choices = [p for p in child.iterdir() if p.name.casefold() == "info.json"]
            if len(choices) != 1:
                unknown.append(child.name); continue
            info = read_json(choices[0], 256 * 1024)
            records.append({"folder": child.name, "id": info.get("Id"), "version": info.get("Version"),
                            "info_sha256": digest(choices[0])})
    return {"game_id": "pathfinder-kingmaker", "game_exe_sha256": digest(root / "Kingmaker.exe"),
            "loader_present": loader.is_file(), "loader_sha256": digest(loader) if loader.is_file() else None,
            "mods": records, "unknown_entries": unknown,
            "runtime_verification": "not_performed", "versions": "mod metadata only; game patch not inferred from Unity executable"}


def _backup_state(source: Path, job: Job, item_id: str) -> dict:
    source = no_links(source)
    require(source.is_dir(), "RECOVERY_REQUIRED", "Select the existing Kingmaker user-data folder (containing Saves), not the game install folder.")
    files, total = [], 0
    for p in source.rglob("*"):
        no_links(p)
        if p.is_file():
            total += p.stat().st_size
            require(total <= 1024 * 1024 * 1024 and len(files) < 10000,
                    "RECOVERY_LIMIT", "Recovery exceeds 1 GiB or 10,000 files. Prepare a separately reviewed recovery snapshot.")
            rel = p.relative_to(source).as_posix()
            contained(source, rel)
            files.append((p, rel, digest(p)))
    require(files, "RECOVERY_REQUIRED", "The selected user-data folder is empty.")
    require(any(rel.casefold().startswith("saves/") and rel.casefold().endswith(".zks") for _, rel, _ in files),
            "RECOVERY_REQUIRED", "No Kingmaker .zks save was found under Saves. Review the recovery source before deployment.")
    recovery = contained(job.path, "recovery/" + item_id + "-" + uuid.uuid4().hex[:12] + ".zip")
    recovery.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(recovery, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for p, rel, sha in files:
            require(digest(p) == sha, "SOURCE_CHANGED", "User-data changed while preparing recovery.")
            z.write(p, rel)
    import hashlib
    with zipfile.ZipFile(recovery) as z:
        for p, rel, sha in files:
            h = hashlib.sha256()
            with z.open(rel) as f:
                for b in iter(lambda: f.read(1024 * 1024), b""): h.update(b)
            require(h.hexdigest() == sha and digest(p) == sha, "SOURCE_CHANGED", "Recovery bytes or their source changed.")
    manifest = {rel: {"sha256": sha, "bytes": p.stat().st_size} for p, rel, sha in files}
    require(tree_audit(source, manifest)["status"] == "MATCH", "SOURCE_CHANGED", "The recovery source file set changed during backup.")
    return {"source_private": str(source), "source_manifest": manifest,
            "relative_path": recovery.relative_to(job.path).as_posix(), "sha256": digest(recovery),
            "source_file_count": len(files), "source_bytes": total, "verification": "copied_and_readback_hashed", "restore_tested": False}


def _dependency_gate(info: dict, observed: dict, umm_version: str):
    require(version(umm_version) >= version(info.get("ManagerVersion") or "0.0"), "MANAGER_TOO_OLD", "This mod requires a newer UMM version.")
    installed = {r["id"]: r["version"] for r in observed["mods"]}
    requirements = info.get("Requirements") or []
    require(isinstance(requirements, list), "DEPENDENCY_UNKNOWN", "UMM requirements have an unsupported shape.")
    for req in requirements:
        require(isinstance(req, str), "DEPENDENCY_UNKNOWN", "Invalid UMM dependency.")
        m = re.fullmatch(r"(.+)-(\d+(?:\.\d+){1,3})", req)
        ident, minimum = (m[1], m[2]) if m else (req, None)
        require(ident in installed, "DEPENDENCY_MISSING", "A required mod is absent: " + slug(ident))
        if minimum:
            require(version(installed[ident]) >= version(minimum), "DEPENDENCY_TOO_OLD", "A required mod version is too old.")


def install_new(job: Job, item_id: str, game_dir: Path, recovery_source: Path, *,
                approved_plan_sha256: str, game_version: str, umm_version: str,
                reviewed_umm_id: str | None = None) -> dict:
    """Explicit operation. On a valued installation, first complete Windows acceptance.
    No flag disables process or preservation checks.
    """
    item = job.item(item_id)
    require(job.plan["game_id"] == "pathfinder-kingmaker" and job.plan["manager_id"] == "unity-mod-manager",
            "MANAGER_HANDOFF", "Only Kingmaker's reviewed UMM folder layout has a deployment adapter.")
    require(item["kind"] == "mod", "MANAGER_HANDOFF", "Install the UMM loader through its official installer. This function never injects the loader.")
    require(approved_plan_sha256 == job.plan["plan_sha256"], "APPROVAL_MISMATCH", "Explicit approval must match this immutable plan.")
    require(version(game_version) >= version("2.1.7") and version(umm_version) >= version("0.23.0"),
            "VERSION_TOO_OLD", "The Kingmaker profile requires game 2.1.7+ and UMM 0.23.0+.")
    require_closed()
    root = no_links(game_dir)
    with local_lock(job.path), local_lock(root, ".game-mod-workflow.lock"):
        job.reconcile_gate(item_id)
        _, receipt = job.acquired(item_id)
        ins = receipt["inspected"]
        require(ins["kind"] == "umm_mod", "ARCHIVE_LAYOUT", "Only reviewed UMM mod archives can be deployed by this adapter.")
        ident = ins["info"]["Id"]
        require(item.get("umm_id") == ident or reviewed_umm_id == ident, "MOD_ID_REVIEW_REQUIRED", "This recipe lacks a verified UMM ID; review the staged Info.json and explicitly supply its exact ID.")
        staged = contained(job.path, "staged/" + item_id)
        require(job.checkpoint(item_id, "STAGED_NOT_INSTALLED") is not None, "NOT_STAGED", "Stage and review this archive first.")
        require(tree_audit(staged, ins["files"])["status"] == "MATCH", "SOURCE_CHANGED", "Staged files changed; no deployment.")
        target = contained(root, "Mods/" + slug(ident))
        old_receipt = job.checkpoint(item_id, "FILES_INSTALLED_RUNTIME_UNVERIFIED")
        if old_receipt:
            require(old_receipt["target_private"] == str(target), "TARGET_CHANGED", "Job already has another installation target.")
            require(tree_audit(target, ins["files"])["status"] == "MATCH", "CONCURRENT_CHANGE", "Installed content changed; it was not replaced.")
            return {"status": "FILES_INSTALLED_RUNTIME_UNVERIFIED", "reused": True}
        observed = inventory(root)
        require(observed["loader_present"], "LOADER_MISSING", "Run the official Unity Mod Manager installer for Kingmaker first.")
        require(not observed["unknown_entries"], "UNRECOGNIZED_EXISTING_MODS", "Existing unrecognized Mods entries need inspection before automated deployment.")
        require(not target.exists() and not any(r["id"] == ident or r["folder"].casefold() == ident.casefold() for r in observed["mods"]),
                "EXISTING_MOD", "This mod already exists. Upgrades belong to its current manager; nothing was overwritten.")
        _dependency_gate(ins["info"], observed, umm_version)
        recovery = no_links(recovery_source)
        require(recovery != root and root not in recovery.parents and recovery not in job.path.parents and job.path not in recovery.parents,
                "RECOVERY_SOURCE_INVALID", "Recovery must be a separate Kingmaker user-data directory, not the install or job directory.")
        job.event(item_id, "PREPARING_RECOVERY")
        backup = _backup_state(recovery, job, item_id)
        require_closed()
        require(object_hash(inventory(root)) == object_hash(observed), "CONCURRENT_CHANGE", "Game or manager state changed during preparation.")
        job.event(item_id, "INSTALLING", target_private=str(target), prior_state="absent",
                  before_inventory=observed, recovery=backup,
                  versions={"game": game_version, "umm": umm_version, "evidence": "caller_confirmed_not_independently_detected"})
        target.parent.mkdir(exist_ok=True)
        target.mkdir(exist_ok=False)
        for rel, meta in ins["files"].items():
            require_closed()
            copy_new(contained(staged, rel), contained(target, rel), meta["sha256"])
        require(tree_audit(target, ins["files"])["status"] == "MATCH", "CONCURRENT_CHANGE", "Installed-file verification failed; preserve partial state.")
        after = inventory(root)
        require(after["game_exe_sha256"] == observed["game_exe_sha256"] and after["loader_sha256"] == observed["loader_sha256"],
                "CONCURRENT_CHANGE", "Game or loader changed; runtime remains unverified.")
        job.event(item_id, "FILES_INSTALLED_RUNTIME_UNVERIFIED", target_private=str(target),
                  prior_state="absent", recovery=backup, files=ins["files"], umm_id=ident)
        return {"status": "FILES_INSTALLED_RUNTIME_UNVERIFIED", "mod_id": ident,
                "warning": "No game was started and no activation setting was changed. UMM may enable new mods by default at next launch. Review UMM before continuing a valued save."}


def audit_installed(job: Job, item_id: str) -> dict:
    rec = job.checkpoint(item_id, "FILES_INSTALLED_RUNTIME_UNVERIFIED")
    require(rec is not None, "NOT_INSTALLED_BY_JOB", "This job has no verified installed-file receipt.")
    return {"item_id": item_id, **tree_audit(Path(rec["target_private"]), rec["files"]), "runtime_verification": "not_performed"}


def rollback_new(job: Job, item_id: str, approved_plan_sha256: str) -> dict:
    require(approved_plan_sha256 == job.plan["plan_sha256"], "APPROVAL_MISMATCH", "Rollback approval must match this plan.")
    require_closed()
    with local_lock(job.path):
        job.reconcile_gate(item_id)
        rec = job.checkpoint(item_id, "FILES_INSTALLED_RUNTIME_UNVERIFIED")
        require(rec is not None and rec["prior_state"] == "absent", "ROLLBACK_UNSUPPORTED", "Only a complete new-folder installation owned by this job can be rolled back.")
        target = no_links(Path(rec["target_private"]))
        game = target.parent.parent
        require(target.parent.name == "Mods" and target.name == rec["umm_id"], "TARGET_CHANGED", "Receipt target does not match the recorded UMM layout.")
        with local_lock(game, ".game-mod-workflow.lock"):
            require(tree_audit(Path(rec["recovery"]["source_private"]), rec["recovery"]["source_manifest"])["status"] == "MATCH",
                    "SAVE_STATE_CHANGED", "Kingmaker user data changed after installation. A save-aware rollback needs review; nothing was removed.")
            original = job.checkpoint(item_id, "INSTALLING")["before_inventory"]
            now = inventory(game)
            require(now["game_exe_sha256"] == original["game_exe_sha256"] and now["loader_sha256"] == original["loader_sha256"],
                    "TARGET_CHANGED", "Game or loader no longer matches this installation receipt.")
            require(tree_audit(target, rec["files"])["status"] == "MATCH", "CONCURRENT_CHANGE", "Files or settings changed after installation. Keep them and use a reviewed manager rollback; do not erase later work.")
            require_closed()
            # Retain bytes on the same volume OUTSIDE Mods, so UMM does not load them.
            quarantine = contained(game, ".mod-workflow-recovery/" + item_id + "-" + uuid.uuid4().hex[:12])
            quarantine.parent.mkdir(parents=True, exist_ok=True)
            require(not quarantine.exists(), "EXISTS", "Recovery target already exists.")
            job.event(item_id, "ROLLING_BACK", target_private=str(target), quarantine_private=str(quarantine))
            target.rename(quarantine)
            require(tree_audit(quarantine, rec["files"])["status"] == "MATCH", "CONCURRENT_CHANGE", "Retained rollback copy differs from its manifest.")
            job.event(item_id, "ROLLED_BACK_RETAINED", quarantine_private=str(quarantine))
    return {"status": "ROLLED_BACK_RETAINED", "warning": "New mod folder retained outside Mods. No saves or unrelated settings were restored or removed."}
