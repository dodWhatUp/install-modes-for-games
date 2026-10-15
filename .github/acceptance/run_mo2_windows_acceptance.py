from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
import zipfile

PRODUCT_COMMIT = "3ff5dd922e3f43edb5d5db3856164f4fe0c6df7d"
HARNESS_REVISION = "R2"
CANONICAL_BASE = "290bea7983ccca50073c5f45ce44337cacafc32a"
MODERN = "2026-07-28"
LEGACY = "2025-11-25"
GAME_ID = "skyrim-special-edition"
TIMEOUT = 240
EXPECTED_SUITES = {
    "scripts/tests/Test-GameToolMO2Read.py": (19, 0),
    "scripts/tests/Test-GameToolPlanning.py": (31, 0),
    "scripts/tests/Test-GameToolAIFoundation.py": (17, 0),
    "scripts/tests/Test-GameToolAIModern.py": (20, 0),
    "scripts/tests/Test-GameToolAutomation.py": (52, 1),
    "scripts/tests/Test-GameToolGameWorkspaces.py": (41, 0),
    "scripts/tests/Test-GameSupport.py": (56, 2),
    "scripts/tests/Test-GameToolUnified.py": (35, 0),
    "scripts/tests/Test-GameToolWorkbenchLauncher.py": (12, 0),
    "scripts/tests/Test-GameToolKeybindMerge.py": (7, 0),
    "scripts/tests/keybinds/test_host_integration.py": (35, 0),
    "scripts/tests/keybinds/test_schema_contract.py": (10, 0),
    "scripts/tests/Test-GameSupportPackaging.py": (7, 4),
}


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sanitized_tail(text: str, *roots: Path, limit: int = 8000) -> str:
    value = text
    for root in sorted({str(Path(item)) for item in roots if item is not None}, key=len, reverse=True):
        value = value.replace(root, "[PRIVATE_PATH]")
        value = value.replace(root.replace("\\", "/"), "[PRIVATE_PATH]")
    value = re.sub(r"(?i)[A-Z]:[\\/](?:[^\r\n<>:\"|?*]+[\\/])*[^\r\n<>:\"|?*]*", "[WINDOWS_PATH]", value)
    value = re.sub(r"(?i)\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b", "[REDACTED_TOKEN]", value)
    value = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._-]{25,}", "[REDACTED_TOKEN]", value)
    value = re.sub(r"\bsk-[A-Za-z0-9_-]{20,}", "[REDACTED_TOKEN]", value)
    value = re.sub(r"\bAKIA[A-Z0-9]{16}\b", "[REDACTED_TOKEN]", value)
    return value[-limit:]


def run(command: list[str], *, cwd: Path, env: dict | None = None, timeout: int = TIMEOUT) -> dict:
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            cwd=str(cwd),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", **(env or {})},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "return_code": proc.returncode,
            "timed_out": False,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "duration_seconds": round(time.time() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", "replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        return {
            "return_code": None,
            "timed_out": True,
            "stdout": stdout,
            "stderr": stderr,
            "duration_seconds": round(time.time() - started, 3),
        }


def git(candidate: Path, *args: str) -> str:
    result = run(["git", *args], cwd=candidate, timeout=120)
    if result["return_code"] != 0:
        raise RuntimeError("Git readback failed.")
    return result["stdout"].strip()


def candidate_receipt(candidate: Path, output: Path) -> dict:
    head = git(candidate, "rev-parse", "HEAD")
    parent = git(candidate, "rev-parse", "HEAD^")
    status = git(candidate, "status", "--porcelain=v1")
    files = git(candidate, "ls-files").splitlines()
    rows = []
    for relative in files:
        path = candidate / relative
        if not path.is_file():
            raise RuntimeError("Candidate tracked file is missing.")
        rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    aggregate = sha256_bytes(
        "\n".join(f"{row['path']}|{row['bytes']}|{row['sha256']}" for row in rows).encode("utf-8")
    )
    receipt = {
        "schema_version": 1,
        "kind": "game-tools-mo2-windows-candidate",
        "harness_revision": HARNESS_REVISION,
        "status": "PASS" if head == PRODUCT_COMMIT and parent == CANONICAL_BASE and not status else "FAIL",
        "product_commit": head,
        "parent_commit": parent,
        "tracked_files": len(rows),
        "payload_bytes": sum(row["bytes"] for row in rows),
        "aggregate_sha256": aggregate,
        "checks": {
            "head_exact": head == PRODUCT_COMMIT,
            "parent_exact": parent == CANONICAL_BASE,
            "worktree_clean": not status,
        },
        "effects": {"repository_write": False, "production": False, "game": False, "manager": False},
    }
    write_json(output / "WINDOWS-CANDIDATE.json", receipt)
    return receipt


def parse_unittest(text: str) -> tuple[int | None, int]:
    matches = re.findall(r"Ran\s+(\d+)\s+tests?", text)
    tests = int(matches[-1]) if matches else None
    skips = sum(int(value) for value in re.findall(r"skipped=(\d+)", text[-4000:]))
    return tests, skips


def selected_gate(candidate: Path, output: Path) -> dict:
    rows = []
    for relative, (expected_tests, max_skips) in EXPECTED_SUITES.items():
        result = run(
            [sys.executable, "-B", str(candidate / relative)],
            cwd=candidate,
            env={"GAME_TOOLS_HOST_SOURCE": str(candidate)},
        )
        text = result["stdout"] + "\n" + result["stderr"]
        tests, skips = parse_unittest(text)
        status = (
            "PASS"
            if result["return_code"] == 0 and not result["timed_out"] and tests == expected_tests and skips <= max_skips
            else "FAIL_OR_INCOMPLETE"
        )
        row = {
            "suite": relative,
            "status": status,
            "return_code": result["return_code"],
            "timed_out": result["timed_out"],
            "tests": tests,
            "expected_tests": expected_tests,
            "skipped": skips,
            "maximum_environment_skips": max_skips,
            "duration_seconds": result["duration_seconds"],
        }
        if status != "PASS":
            row["stdout_tail"] = sanitized_tail(result["stdout"], candidate)
            row["stderr_tail"] = sanitized_tail(result["stderr"], candidate)
        rows.append(row)
        print(json.dumps(row), flush=True)
    passed = all(row["status"] == "PASS" for row in rows)
    receipt = {
        "schema_version": 1,
        "kind": "game-tools-mo2-windows-selected-gate",
        "harness_revision": HARNESS_REVISION,
        "status": "PASS" if passed else "FAIL_OR_INCOMPLETE",
        "product_commit": PRODUCT_COMMIT,
        "python": sys.version,
        "automatic_retry": False,
        "suite_count": len(rows),
        "tests_run": sum(row["tests"] or 0 for row in rows),
        "passed": sum((row["tests"] or 0) - row["skipped"] for row in rows if row["status"] == "PASS"),
        "skipped": sum(row["skipped"] for row in rows if row["status"] == "PASS"),
        "timeouts": sum(int(row["timed_out"]) for row in rows),
        "results": rows,
        "effects": {
            "isolated_candidate_only": True,
            "production": False,
            "real_game": False,
            "manager_profile": False,
            "input": False,
            "capture": False,
            "network_by_product": False,
        },
    }
    write_json(output / "WINDOWS-SELECTED-GATE.json", receipt)
    return receipt


def powershell_contracts(candidate: Path) -> dict:
    result = run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(candidate / "scripts/tests/Test-GameSourceExport.ps1"),
        ],
        cwd=candidate,
    )
    text = result["stdout"] + "\n" + result["stderr"]
    match = re.search(r"PASS:\s+(\d+)\s+source-export contracts", text)
    value = {
        "status": "PASS" if result["return_code"] == 0 and not result["timed_out"] and match else "FAIL_OR_INCOMPLETE",
        "return_code": result["return_code"],
        "timed_out": result["timed_out"],
        "contracts": int(match.group(1)) if match else None,
        "duration_seconds": result["duration_seconds"],
    }
    if value["status"] != "PASS":
        value["stdout_tail"] = sanitized_tail(result["stdout"], candidate)
        value["stderr_tail"] = sanitized_tail(result["stderr"], candidate)
    return value


def source_export(candidate: Path, output: Path) -> tuple[dict, Path]:
    export_root = output / "source-export"
    command = [
        "powershell.exe",
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(candidate / "scripts/Export-GameTools.ps1"),
        "-OutputDirectory",
        str(export_root),
        "-Bundle",
        "GameTools",
        "-ClientDate",
        "2026-10-15",
    ]
    result = run(command, cwd=candidate, timeout=300)
    try:
        value = json.loads(result["stdout"].strip()) if result["return_code"] == 0 else None
    except json.JSONDecodeError:
        value = None
    if not isinstance(value, dict):
        receipt = {
            "schema_version": 1,
            "kind": "game-tools-mo2-windows-source-export",
        "harness_revision": HARNESS_REVISION,
            "status": "FAIL_OR_INCOMPLETE",
            "return_code": result["return_code"],
            "timed_out": result["timed_out"],
            "duration_seconds": result["duration_seconds"],
            "stdout_tail": sanitized_tail(result["stdout"], candidate, export_root),
            "stderr_tail": sanitized_tail(result["stderr"], candidate, export_root),
        }
        write_json(output / "WINDOWS-SOURCE-EXPORT.json", receipt)
        return receipt, export_root
    archive = Path(value["archive"])
    source = export_root / "source"
    manifest_path = source / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    missing = []
    mismatched = []
    for row in manifest["files"]:
        path = source / Path(row["path"])
        if not path.is_file():
            missing.append(row["path"])
        elif path.stat().st_size != row["bytes"] or sha256_file(path).lower() != row["sha256"].lower():
            mismatched.append(row["path"])
    expected_names = {row["path"] for row in manifest["files"]} | {"MANIFEST.json"}
    zip_errors = []
    with zipfile.ZipFile(archive) as package:
        infos = package.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(name.casefold() for name in names)):
            zip_errors.append("duplicate_entries")
        if set(names) != expected_names:
            zip_errors.append("inventory_mismatch")
        for info in infos:
            raw = package.read(info)
            if info.filename == "MANIFEST.json":
                expected_sha = value["manifest_sha256"].lower()
                expected_bytes = manifest_path.stat().st_size
            else:
                row = next(item for item in manifest["files"] if item["path"] == info.filename)
                expected_sha = row["sha256"].lower()
                expected_bytes = row["bytes"]
            if len(raw) != expected_bytes or sha256_bytes(raw) != expected_sha:
                zip_errors.append(info.filename)
    component_versions = manifest.get("component_versions", {})
    checks = {
        "powershell_exit": result["return_code"] == 0 and not result["timed_out"],
        "integrity_reported": value.get("integrity") == "all_source_and_manifest_zip_entries_verified",
        "source_current": value.get("source_current_at_final_hash_check") is True,
        "archive_hash": sha256_file(archive).lower() == value.get("sha256", "").lower(),
        "manifest_hash": sha256_file(manifest_path).lower() == value.get("manifest_sha256", "").lower(),
        "source_files_match": not missing and not mismatched,
        "zip_entries_match": not zip_errors,
        "preacceptance_refs_absent": manifest.get("mo2_windows_acceptance_reference") is None
        and manifest.get("mo2_windows_acceptance_json_reference") is None,
        "preacceptance_status_truthful": "remain pending" in manifest.get("runtime_status", ""),
        "versions_exact": component_versions.get("tool_hub") == "0.28.0-preview.1"
        and component_versions.get("game_workspaces") == "0.2.2"
        and component_versions.get("instances") == "0.2.0"
        and component_versions.get("planning") == "0.2.0"
        and component_versions.get("mo2_read") == "0.2.0",
    }
    receipt = {
        "schema_version": 1,
        "kind": "game-tools-mo2-windows-source-export",
        "status": "PASS" if all(checks.values()) else "FAIL_OR_INCOMPLETE",
        "product_commit": PRODUCT_COMMIT,
        "files": value["files"],
        "archive_name": archive.name,
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "manifest_sha256": sha256_file(manifest_path),
        "manifest_files": len(manifest["files"]),
        "missing": missing,
        "mismatched": mismatched,
        "zip_errors": zip_errors,
        "checks": checks,
        "powershell_contracts": powershell_contracts(candidate),
        "duration_seconds": result["duration_seconds"],
        "effects": {"production": False, "real_game": False, "manager": False, "input": False, "capture": False},
    }
    if receipt["powershell_contracts"]["status"] != "PASS":
        receipt["status"] = "FAIL_OR_INCOMPLETE"
    write_json(output / "WINDOWS-SOURCE-EXPORT.json", receipt)
    return receipt, export_root


def exported_package_checks(export_root: Path, output: Path) -> dict:
    source = export_root / "source"
    profile = Path(os.environ["LOCALAPPDATA"]) / "GameToolHub-Workbench-Preview-0.28.0-preview.1-MO2-Planning-Keybinds"
    before = profile.exists()
    checks_to_run = [
        ("packaging", [sys.executable, "-B", str(source / "scripts/tests/Test-GameSupportPackaging.py")]),
        ("workbench_verify", [sys.executable, "-B", str(source / "scripts/GameToolWorkbenchLaunch.pyw"), "--verify-only"]),
        ("original_verify", [sys.executable, "-B", str(source / "scripts/GameToolWorkbenchLaunch.pyw"), "--layout", "Original", "--verify-only"]),
        ("host_pins", [sys.executable, "-B", str(source / "scripts/check_host.py"), "--host", str(source)]),
    ]
    rows = []
    for name, command in checks_to_run:
        result = run(command, cwd=source)
        text = result["stdout"] + "\n" + result["stderr"]
        tests, skips = parse_unittest(text)
        host_ok = False
        if name == "host_pins" and result["return_code"] == 0:
            try:
                payload = json.loads(result["stdout"])
                host_ok = payload.get("status") == "EXACT_DEPENDENCIES_MATCH" and len(payload.get("files", [])) == 13
            except json.JSONDecodeError:
                host_ok = False
        row_ok = result["return_code"] == 0 and not result["timed_out"]
        if name == "packaging":
            row_ok = row_ok and tests == 7 and skips == 0
        if name == "host_pins":
            row_ok = row_ok and host_ok
        rows.append(
            {
                "name": name,
                "status": "PASS" if row_ok else "FAIL_OR_INCOMPLETE",
                "return_code": result["return_code"],
                "timed_out": result["timed_out"],
                "tests": tests,
                "skipped": skips,
                "duration_seconds": result["duration_seconds"],
            }
        )
    after = profile.exists()
    checks = {
        "all_commands_pass": all(row["status"] == "PASS" for row in rows),
        "packaging_zero_skips": rows[0]["tests"] == 7 and rows[0]["skipped"] == 0,
        "verify_only_created_no_profile": before == after,
    }
    receipt = {
        "schema_version": 1,
        "kind": "game-tools-mo2-windows-exported-package",
        "harness_revision": HARNESS_REVISION,
        "status": "PASS" if all(checks.values()) else "FAIL_OR_INCOMPLETE",
        "checks": checks,
        "results": rows,
        "effects": {"profile_created": after and not before, "production": False, "real_game": False, "manager": False},
    }
    write_json(output / "WINDOWS-EXPORTED-PACKAGE.json", receipt)
    return receipt


class JsonLineClient:
    def __init__(self, command: list[str], cwd: Path):
        self.process = subprocess.Popen(
            command,
            cwd=str(cwd),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self.responses: queue.Queue[str | None] = queue.Queue()
        self.stderr_lines: list[str] = []
        self.stdout_thread = threading.Thread(target=self._stdout, daemon=True)
        self.stderr_thread = threading.Thread(target=self._stderr, daemon=True)
        self.stdout_thread.start()
        self.stderr_thread.start()

    def _stdout(self):
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self.responses.put(line)
        self.responses.put(None)

    def _stderr(self):
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self.stderr_lines.append(line.rstrip("\r\n"))

    def call(self, payload: dict, timeout: float = 30) -> dict:
        if self.process.poll() is not None:
            raise RuntimeError("MCP process exited before request.")
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.process.stdin.flush()
        try:
            line = self.responses.get(timeout=timeout)
        except queue.Empty as exc:
            raise RuntimeError("MCP response timeout; no retry was made.") from exc
        if line is None:
            raise RuntimeError("MCP stdout closed before response.")
        return json.loads(line)

    def notify(self, payload: dict) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def close(self) -> dict:
        assert self.process.stdin is not None
        self.process.stdin.close()
        forced = False
        try:
            self.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
            forced = True
        self.stdout_thread.join(timeout=2)
        self.stderr_thread.join(timeout=2)
        return {"exit_code": self.process.returncode, "forced": forced, "stderr_count": len(self.stderr_lines)}


def tree_digest(root: Path) -> dict:
    rows = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if path.is_file():
            raw = path.read_bytes()
            rows.append({"path": path.relative_to(root).as_posix(), "bytes": len(raw), "sha256": sha256_bytes(raw)})
    return {"files": len(rows), "aggregate_sha256": sha256_bytes("\n".join(
        f"{row['path']}|{row['bytes']}|{row['sha256']}" for row in rows
    ).encode("utf-8"))}


def modern_payload(ident: int, method: str, meta: dict, **params) -> dict:
    return {"jsonrpc": "2.0", "id": ident, "method": method, "params": {"_meta": meta, **params}}


def structured(response: dict, *, allow_error: bool = False) -> dict:
    if "error" in response:
        raise RuntimeError("MCP framing error.")
    result = response["result"]
    if result.get("isError") and not allow_error:
        raise RuntimeError("Unexpected MCP domain refusal.")
    return result["structuredContent"]


def external_mcp(source: Path, output: Path) -> dict:
    root = output / "mcp-fixture"
    data = root / "data"
    game = root / "game"
    manager = root / "manager"
    profiles = {name: root / "profiles" / name for name in ("normal", "credential", "path", "malformed")}
    if root.exists():
        raise RuntimeError("MCP fixture root already exists; no retry permitted.")
    game.mkdir(parents=True)
    manager.mkdir(parents=True)
    for profile in profiles.values():
        profile.mkdir(parents=True)
    (game / "SkyrimSE.exe").write_bytes(b"synthetic executable marker\n")
    (manager / "ModOrganizer.exe").write_bytes(b"synthetic manager marker\n")
    (manager / "ModOrganizer.ini").write_text("[General]\nselected_profile=normal\n", encoding="utf-8")
    normal_mods = "# generated fixture\n+Unofficial Patch\n-Disabled Example\n*Foreign Example\n"
    normal_plugins = "# generated fixture\n*Skyrim.esm\nUpdate.esm\n"
    secret = "gh" + "p_" + "a" * 24
    private_path = "C:" + "\\" + "Users" + "\\" + "fixture" + "\\" + "private-mod"
    authored = {
        "normal": normal_mods,
        "credential": "+" + secret + "\n",
        "path": "+" + private_path + "\n",
        "malformed": "+Temporary Valid Entry\n",
    }
    for name, profile in profiles.items():
        (profile / "modlist.txt").write_text(authored[name], encoding="utf-8")
        (profile / "plugins.txt").write_text(normal_plugins, encoding="utf-8")
        (profile / "loadorder.txt").write_text("Skyrim.esm\nUpdate.esm\n", encoding="utf-8")
    before_registration = {"game": tree_digest(game), "manager": tree_digest(manager), **{
        "profile_" + name: tree_digest(path) for name, path in profiles.items()
    }}
    public_registration = []
    for name, profile in profiles.items():
        command = [
            sys.executable,
            "-B",
            str(source / "scripts/Game-Instances.py"),
            "--data-dir",
            str(data),
            "register-mo2",
            "--instance-id",
            "skyrim-" + name,
            "--game-id",
            GAME_ID,
            "--game-dir",
            str(game),
            "--manager-root",
            str(manager),
            "--profile-root",
            str(profile),
            "--profile",
            name,
            "--store",
            "steam",
            "--build",
            "synthetic",
            "--confirm",
        ]
        result = run(command, cwd=source)
        if result["return_code"] != 0 or result["timed_out"]:
            raise RuntimeError("Local MO2 registration failed.")
        value = json.loads(result["stdout"])
        public_registration.append(value)
    after_registration = {"game": tree_digest(game), "manager": tree_digest(manager), **{
        "profile_" + name: tree_digest(path) for name, path in profiles.items()
    }}
    # Author the malformed state after successful registration; subsequent MCP reads must not mutate it.
    (profiles["malformed"] / "modlist.txt").write_bytes(b"\x00unsupported\n")
    before_mcp = {"game": tree_digest(game), "manager": tree_digest(manager), **{
        "profile_" + name: tree_digest(path) for name, path in profiles.items()
    }}

    base_command = [sys.executable, "-B", str(source / "scripts/GameToolAI.py"), "--data-dir", str(data), "--workspaces", "stdio"]
    meta = {
        "io.modelcontextprotocol/protocolVersion": MODERN,
        "io.modelcontextprotocol/clientCapabilities": {},
        "io.modelcontextprotocol/clientInfo": {"name": "mo2-windows-acceptance", "version": "1.0.0"},
    }
    modern = JsonLineClient(base_command, source)
    transcript = {}
    try:
        discover = modern.call(modern_payload(1, "server/discover", meta))
        listed = modern.call(modern_payload(2, "tools/list", meta))
        tools = listed["result"]["tools"]
        names = [row["name"] for row in tools]
        definitions = {row["name"]: row for row in tools}

        def tool(ident: int, name: str, arguments: dict | None = None) -> dict:
            return modern.call(modern_payload(ident, "tools/call", meta, name=name, arguments=arguments or {}))

        instances = structured(tool(3, "game_tools_instances", {"game_id": GAME_ID}))
        normal = structured(tool(4, "game_tools_instance_inspect", {"instance_id": "skyrim-normal", "game_id": GAME_ID}))
        credential = structured(tool(5, "game_tools_instance_inspect", {"instance_id": "skyrim-credential", "game_id": GAME_ID}))
        path_value = structured(tool(6, "game_tools_instance_inspect", {"instance_id": "skyrim-path", "game_id": GAME_ID}))
        malformed_response = tool(7, "game_tools_instance_inspect", {"instance_id": "skyrim-malformed", "game_id": GAME_ID})
        malformed = structured(malformed_response, allow_error=True)
        plan = structured(tool(8, "game_tools_plan_goal", {"game_id": GAME_ID, "goal": "inspect-installed", "instance_id": "skyrim-normal"}))
        compare = structured(tool(9, "game_tools_plan_goal", {"game_id": GAME_ID, "goal": "compare-intended-installed", "instance_id": "skyrim-normal"}))
        blocker = structured(tool(10, "game_tools_explain_blocker", {"code": "ADAPTER_COMPARISON_PENDING"}))
        batch = structured(tool(11, "game_tools_status_batch", {"handles": [{"kind": "instance", "id": "skyrim-normal", "game_id": GAME_ID}]}))
        raw_public = json.dumps(
            [discover, listed, instances, normal, credential, path_value, malformed_response, plan, compare, blocker, batch, public_registration],
            ensure_ascii=False,
        )
        path_fields = {"path", "game_dir", "root", "directory", "manager_root", "profile_root"}
        inventory_nodes = {node["id"]: node for node in plan["data"]["nodes"]}
        checks = {
            "modern_discover": discover["result"]["supportedVersions"] == [MODERN, LEGACY],
            "modern_tool_count": len(names) == 38,
            "tools_sorted_unique": names == sorted(set(names)),
            "no_registration_tool": not any("register" in name.casefold() for name in names),
            "no_arbitrary_path_arguments": all(not (path_fields & set(row["inputSchema"]["properties"])) for row in definitions.values()),
            "read_only_connection_has_no_proposal": "hub_propose" not in names,
            "four_instances": instances["status"] == "INSTANCES_LISTED" and instances["data"]["count"] == 4,
            "normal_adapter": normal["data"]["adapter_contract"]["adapter"] == "mo2",
            "normal_rows": normal["data"]["inventory"]["mods"]["total_rows"] == 3,
            "normal_hash_exposed": normal["data"]["inventory"]["source_files"][0]["raw_hash_exposed"] is True,
            "credential_redacted": credential["data"]["inventory"]["mods"]["redacted_name_count"] == 1
            and credential["data"]["inventory"]["source_files"][0]["sha256"] is None,
            "path_redacted": path_value["data"]["inventory"]["mods"]["redacted_name_count"] == 1
            and path_value["data"]["inventory"]["source_files"][0]["sha256"] is None,
            "malformed_typed": malformed_response["result"]["isError"] is True and malformed["status"] == "INVALID_MANAGER_STATE",
            "private_values_absent": secret not in raw_public and private_path not in raw_public
            and str(root) not in raw_public and str(game) not in raw_public and str(manager) not in raw_public,
            "inspect_plan_ready": plan["data"]["status"] == "READY_FOR_READS" and inventory_nodes["inventory"]["owner"] == "MO2ReadAdapter",
            "compare_blocked": compare["data"]["status"] == "BLOCKED" and "ADAPTER_COMPARISON_PENDING" in compare["data"]["blockers"],
            "typed_comparison_blocker": blocker["status"] == "ADAPTER_COMPARISON_PENDING" and blocker["retry"]["allowed"] is False,
            "batch_metadata_only": batch["status"] == "BATCH_INSPECTED",
        }
        transcript["modern"] = {"tools": len(names), "checks": checks}
    finally:
        transcript["modern_process"] = modern.close()

    legacy = JsonLineClient(base_command, source)
    try:
        initialize = legacy.call({"jsonrpc": "2.0", "id": 20, "method": "initialize", "params": {}})
        legacy.notify({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        listed = legacy.call({"jsonrpc": "2.0", "id": 21, "method": "tools/list", "params": {}})
        legacy_names = [row["name"] for row in listed["result"]["tools"]]
        legacy_checks = {
            "initialize": initialize["result"]["protocolVersion"] == LEGACY,
            "tool_count": len(legacy_names) == 24,
            "new_tools_absent": not ({"game_tools_instances", "game_tools_instance_inspect", "game_tools_plan_goal", "game_tools_conflicts"} & set(legacy_names)),
            "registration_absent": not any("register" in name.casefold() for name in legacy_names),
        }
        transcript["legacy"] = {"tools": len(legacy_names), "checks": legacy_checks}
    finally:
        transcript["legacy_process"] = legacy.close()

    after_mcp = {"game": tree_digest(game), "manager": tree_digest(manager), **{
        "profile_" + name: tree_digest(path) for name, path in profiles.items()
    }}
    data_files = sorted(path.relative_to(data).as_posix() for path in data.rglob("*") if path.is_file())
    checks = {
        **transcript["modern"]["checks"],
        **{"legacy_" + key: value for key, value in transcript["legacy"]["checks"].items()},
        "registration_did_not_change_fixture": before_registration == after_registration,
        "mcp_did_not_change_fixture": before_mcp == after_mcp,
        "only_registry_metadata_written": len(data_files) == 4 and all(item.startswith("game-instances/") and item.endswith(".json") for item in data_files),
        "no_job_or_request_store": not (data / "mod-workflows" / "jobs").exists() and not (data / "automation" / "requests").exists(),
        "processes_clean": all(
            transcript[name]["exit_code"] == 0 and transcript[name]["forced"] is False and transcript[name]["stderr_count"] == 0
            for name in ("modern_process", "legacy_process")
        ),
    }
    receipt = {
        "schema_version": 1,
        "kind": "game-tools-mo2-windows-external-mcp",
        "harness_revision": HARNESS_REVISION,
        "status": "PASS" if all(checks.values()) else "FAIL_OR_INCOMPLETE",
        "product_commit": PRODUCT_COMMIT,
        "protocols": [MODERN, LEGACY],
        "checks": checks,
        "check_count": len(checks),
        "fixture": {"valid_instances": 3, "malformed_instances": 1, "game_files": before_registration["game"]["files"]},
        "private_data_files": len(data_files),
        "processes": {name: transcript[name] for name in ("modern_process", "legacy_process")},
        "effects": {
            "private_registry_metadata": True,
            "game_files": False,
            "manager_profile_mutation": False,
            "production": False,
            "proposal": False,
            "execution": False,
            "input": False,
            "capture": False,
            "network_by_product": False,
        },
        "limitations": [
            "Synthetic folders only; no real MO2 installation or live profile.",
            "Declaration presence is not VFS deployment, overwrite order, runtime loading or gameplay.",
            "Independent stdio acceptance is not a specific ChatGPT or Codex product UI connection.",
        ],
    }
    write_json(output / "WINDOWS-EXTERNAL-MCP.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError("Acceptance output exists; no automatic overwrite or retry.")
    output.mkdir(parents=True)

    candidate_result = candidate_receipt(candidate, output)
    selected = selected_gate(candidate, output)
    export, export_root = source_export(candidate, output)
    package = exported_package_checks(export_root, output) if export["status"] == "PASS" else {"status": "NOT_RUN"}
    mcp = external_mcp(export_root / "source", output) if package["status"] == "PASS" else {"status": "NOT_RUN"}
    checks = {
        "candidate": candidate_result["status"] == "PASS",
        "selected_gate": selected["status"] == "PASS",
        "source_export": export["status"] == "PASS",
        "exported_package": package["status"] == "PASS",
        "external_mcp": mcp["status"] == "PASS",
    }
    final = {
        "schema_version": 1,
        "kind": "game-tools-mo2-windows-final-acceptance",
        "harness_revision": HARNESS_REVISION,
        "status": "PASS" if all(checks.values()) else "FAIL_OR_INCOMPLETE",
        "product_commit": PRODUCT_COMMIT,
        "canonical_base": CANONICAL_BASE,
        "checks": checks,
        "candidate": {
            "files": candidate_result.get("tracked_files"),
            "aggregate_sha256": candidate_result.get("aggregate_sha256"),
        },
        "selected_gate": {
            "suites": selected.get("suite_count"),
            "tests": selected.get("tests_run"),
            "passed": selected.get("passed"),
            "skipped": selected.get("skipped"),
            "timeouts": selected.get("timeouts"),
        },
        "source_export": {
            "files": export.get("files"),
            "archive_sha256": export.get("archive_sha256"),
            "manifest_sha256": export.get("manifest_sha256"),
            "contracts": export.get("powershell_contracts", {}).get("contracts"),
        },
        "external_mcp_checks": mcp.get("check_count"),
        "automatic_retry": False,
        "effects": {
            "production": False,
            "real_game": False,
            "real_manager_profile": False,
            "manager_or_game_write": False,
            "proposal": False,
            "execution": False,
            "input": False,
            "capture": False,
            "main": False,
        },
    }
    write_json(output / "WINDOWS-FINAL-ACCEPTANCE.json", final)
    # Remove private synthetic fixture bytes before artifact upload. Receipts retain only sanitized counts/hashes.
    fixture = output / "mcp-fixture"
    if fixture.exists():
        import shutil
        shutil.rmtree(fixture)
    # Keep source archive/package out of the public acceptance artifact; its exact hashes are in receipts.
    export_dir = output / "source-export"
    if export_dir.exists():
        import shutil
        shutil.rmtree(export_dir)
    print("FINAL " + json.dumps(final), flush=True)
    return 0 if final["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
