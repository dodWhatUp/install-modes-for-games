"""Prepare double-click access to an existing verified Windows installation.

No app/game launch, downloads, installation, profile migration or input.
Windows packaged-app path redirection is resolved by real opened file handles.
Only a proven alternate spelling of the same existing data directory may change
in installation metadata; user files and immutable source versions stay intact.
"""
from __future__ import annotations
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import GameToolUnified as api


def final_file(path):
    """Return the real local file reached by this process, without moving it."""
    path = api.local_path(path)
    if os.name != "nt":
        raise ValueError("Real file identity requires Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
    kernel.GetFinalPathNameByHandleW.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(path), 0x80000000, 7, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        text = ctypes.create_unicode_buffer(32768)
        count = kernel.GetFinalPathNameByHandleW(handle, text, len(text), 0)
        if not count or count >= len(text):
            raise ValueError("Real file path could not be read completely")
        result = text.value
        if result.startswith("\\\\?\\"):
            result = result[4:]
        return api.local_path(result)
    finally:
        kernel.CloseHandle(handle)


def inspect_access(root, *, identity=final_file):
    canonical = identity(Path(root) / "install.json").parent
    raw = api.read_bytes(canonical / "install.json")
    value = api.read_install(canonical)
    release = api.verify_current(canonical, value)
    launcher = canonical / "Start-UnifiedTools.pyw"
    if api.digest(api.read_bytes(launcher)) != value["bootstrap_sha256"]:
        raise ValueError("Stable launcher differs from its recorded source")
    # Fixed existing registry proves which directory contains this user's data.
    # Do not guess a package name or choose whichever of two folders looks newer.
    logical_registry = Path(value["data_dir"]) / "tools.json"
    observed_registry = identity(logical_registry)
    if observed_registry.name != "tools.json":
        raise ValueError("Unexpected registry identity")
    if api.read_bytes(logical_registry) != api.read_bytes(observed_registry):
        raise ValueError("Registry changed while resolving its real path")
    desired = dict(value, data_dir=str(observed_registry.parent))
    if api.read_bytes(canonical / "install.json") != raw:
        raise ValueError("Installation changed during access inspection")
    runtime = identity(value["pythonw"])
    if runtime.name.lower() != "pythonw.exe":
        raise ValueError("Expected the installation's existing Python window runtime")
    return dict(root=canonical, raw=raw, before=value, after=desired,
                runtime=runtime, launcher=launcher,
                files_verified=len(release["manifest"]["files"]))


def cmd_quote(path):
    text = str(api.local_path(path))
    # Quoting does not disable cmd environment expansion; refuse ambiguous paths.
    if any(char in text for char in ('"', '%', '!', '\r', '\n')):
        raise ValueError("This path cannot be represented safely in a CMD launcher")
    return '"' + text + '"'


def launcher_text(plan):
    runtime, launcher = cmd_quote(plan["runtime"]), cmd_quote(plan["launcher"])
    return ("@echo off\r\nsetlocal DisableDelayedExpansion\r\nchcp 65001 >nul\r\n"
            f"if not exist {runtime} goto missing_runtime\r\n"
            f"if not exist {launcher} goto missing_install\r\n"
            f"start \"\" {runtime} -B {launcher}\r\nexit /b 0\r\n"
            ":missing_runtime\r\necho The existing Python runtime was not found.\r\n"
            "echo Ask for launcher repair; do not reinstall or reset profiles.\r\npause\r\nexit /b 2\r\n"
            ":missing_install\r\necho The Unified Game Tools installation was not found.\r\n"
            "echo Ask for launcher repair; your settings have not been changed.\r\npause\r\nexit /b 2\r\n")


def prepare_access(root, output, recovery, *, identity=final_file, names=None):
    output, recovery = api.local_path(output), api.local_path(recovery)
    if output.exists() or recovery.exists():
        raise ValueError("Use new access and recovery folders; existing files are retained")
    plan = inspect_access(root, identity=identity)
    command = launcher_text(plan).encode("utf-8")
    api.assert_idle(names)
    lease = api.acquire_source_lease(plan["before"]["studio_dir"], "prepare-user-launchers")
    try:
        api.assert_idle(names)
        fresh = inspect_access(root, identity=identity)
        if fresh["raw"] != plan["raw"] or fresh["after"] != plan["after"]:
            raise ValueError("Installation changed; inspect again before preparing access")
        recovery.mkdir(parents=True)
        backup = recovery / "install.json.before"
        with backup.open("xb") as handle:
            handle.write(plan["raw"]); handle.flush(); os.fsync(handle.fileno())
        if api.read_bytes(backup) != plan["raw"]:
            raise ValueError("Access checkpoint readback failed")
        # Only this field can change; it denotes the same opened existing data.
        if plan["after"] != plan["before"]:
            api.atomic_json(plan["root"] / "install.json", plan["after"])
        if api.read_install(plan["root"]) != plan["after"]:
            raise ValueError("Access metadata readback differs; preserve recovery")
        api.verify_current(plan["root"], plan["after"])
        output.mkdir(parents=True)
        launch_file = output / "Open Unified Game Tools.cmd"
        with launch_file.open("xb") as handle:
            handle.write(command); handle.flush(); os.fsync(handle.fileno())
        if api.read_bytes(launch_file) != command:
            raise ValueError("Double-click launcher readback differs")
        guide = ("UNIFIED GAME TOOLS — START HERE\n\n"
                 "Already installed on this computer. No reinstall is needed.\n\n"
                 "OPEN: Double-click Unified Game Tools on your Desktop.\n"
                 "Alternative: double-click Open Unified Game Tools.cmd in this folder.\n"
                 "No terminal commands, Python file association or administrator rights are needed.\n\n"
                 "CLOSE: Use the app's normal Close/Exit action.\n\n"
                 "UPDATE LATER: In the app, open Updates, choose a trusted local release ZIP\n"
                 "and its supplied SHA-256, then Inspect package and Update. No uninstall.\n"
                 "The same launcher opens the updated version. Do not unzip over the installation.\n\n"
                 "Game Input starts Off. Opening this app does not start games, benchmarks\n"
                 "or recording. Existing enabled display overlays may appear as usual.\n\n"
                 "These launchers are for this computer, not an installer for another PC.\n")
        with (output / "START HERE.txt").open("x", encoding="utf-8") as handle:
            handle.write(guide)
        receipt = dict(schema_version=1, installation=str(plan["root"]),
                       version=plan["before"]["current"],
                       metadata_changed=plan["before"] != plan["after"],
                       changed_fields=["data_dir"] if plan["before"] != plan["after"] else [],
                       previous_pointer_sha256=api.digest(plan["raw"]),
                       current_pointer_sha256=api.digest(api.read_bytes(plan["root"] / "install.json")),
                       launch_file=str(launch_file), launch_file_sha256=api.digest(command),
                       runtime=str(plan["runtime"]), launcher=str(plan["launcher"]),
                       working_directory=str(plan["root"]), source_files_verified=plan["files_verified"],
                       profile_or_data_migration=False, app_launched=False)
        api.atomic_json(recovery / "ACCESS.json", receipt)
        return receipt
    finally:
        api.release_source_lease(lease)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    if args.check_only:
        plan = inspect_access(args.install_root)
        print(json.dumps(dict(valid=True, current=plan["before"]["current"],
                              files_verified=plan["files_verified"], app_launched=False)))
    else:
        if not args.output or not args.recovery:
            parser.error("--output and --recovery are required for explicit preparation")
        print(json.dumps(prepare_access(args.install_root, args.output, args.recovery), indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as error:
        print(json.dumps(dict(valid=False, error=str(error))))
        raise SystemExit(2)
