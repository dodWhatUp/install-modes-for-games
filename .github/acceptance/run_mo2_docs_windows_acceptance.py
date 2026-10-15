from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile

DOCS_COMMIT = "d5c332ab789d31265f484a49c40cf2b7d8ad3dda"
PRODUCT_COMMIT = "c0809f7ac99a776390e131859991105c2f4c88f4"
DOCS_PARENT_COMMIT = "c9db66871d1464b444657d47d201d377a8de14ca"
CANONICAL_BASE = "290bea7983ccca50073c5f45ce44337cacafc32a"
HARNESS_REVISION = "DOCS-R3"
CLIENT_DATE = "2026-10-16"
TIMEOUT = 300
EXPECTED_DOCS = {
    "docs/AI-EFFICIENCY-FOUNDATION-CONTINUATION.md",
    "docs/GAME-TOOL-CONNECTIONS.md",
    "docs/GAME-TOOLS-ARCHITECTURE.md",
    "docs/GAME-TOOLS-KNOWLEDGE-INDEX.md",
    "docs/MO2-READ-ADAPTER-SOURCE-DELTA.json",
    "docs/MO2-READ-ADAPTER-VALIDATION.json",
    "docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json",
    "docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md",
    "docs/MO2-READ-ADAPTER.md",
    "docs/UNIFIED-GAME-TOOLS.md",
    "examples/game-tool-hub/README.md",
    "scripts/tests/Test-GameSourceExport.ps1",
}
ACCEPTANCE_DOCS = {
    "docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json",
    "docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md",
}


class GateError(RuntimeError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def require(condition: bool, code: str) -> None:
    if not condition:
        raise GateError(code)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def decode(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeError:
            pass
    return raw.decode("utf-8", "replace")


def run(name: str, argv: list[str], cwd: Path, timeout: int = TIMEOUT) -> dict:
    started = time.time()
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "name": name,
            "status": "PASS" if proc.returncode == 0 else "FAIL",
            "return_code": proc.returncode,
            "timed_out": False,
            "stdout": decode(proc.stdout),
            "stderr": decode(proc.stderr),
            "duration_seconds": round(time.time() - started, 3),
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "status": "TIMEOUT_NO_RETRY",
            "return_code": None,
            "timed_out": True,
            "stdout": "",
            "stderr": "",
            "duration_seconds": round(time.time() - started, 3),
        }


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=str(root), text=True, encoding="utf-8").strip()


def parse_json_output(text: str) -> dict:
    stripped = text.strip().lstrip("\ufeff")
    candidates = [stripped] + [line.strip().lstrip("\ufeff") for line in reversed(stripped.splitlines())]
    for candidate in candidates:
        if not candidate.startswith("{"):
            continue
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise GateError("JSON_OUTPUT_MISSING")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def privacy_clean(value: object) -> bool:
    text = json.dumps(value, ensure_ascii=False)
    patterns = (
        re.compile(r"/Users/[^/\s]+/"),
        re.compile(r"(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]"),
        re.compile(r"(?i)\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b"),
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._-]{25,}"),
        re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    )
    return not any(pattern.search(text) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.product_root.resolve()
    out = args.output.resolve()
    if out.exists():
        raise RuntimeError("Acceptance output already exists; refusing overwrite.")
    out.mkdir(parents=True)
    stage = "INITIALIZE"
    try:
        stage = "CANDIDATE_IDENTITY"
        head = git(root, "rev-parse", "HEAD")
        parent = git(root, "rev-parse", "HEAD^")
        product_ancestor = git(root, "merge-base", "HEAD", PRODUCT_COMMIT)
        merge_base = git(root, "merge-base", "HEAD", CANONICAL_BASE)
        status = git(root, "status", "--porcelain")
        changed = set(git(root, "diff", "--name-only", PRODUCT_COMMIT, DOCS_COMMIT).splitlines())
        require(head == DOCS_COMMIT, "DOCS_HEAD_MISMATCH")
        require(parent == DOCS_PARENT_COMMIT, "DOCS_PARENT_MISMATCH")
        require(product_ancestor == PRODUCT_COMMIT, "PRODUCT_ANCESTOR_MISMATCH")
        require(merge_base == CANONICAL_BASE, "CANONICAL_BASE_MISMATCH")
        require(not status, "DOCS_WORKTREE_DIRTY")
        require(changed == EXPECTED_DOCS, "DOCS_CHANGED_SET_MISMATCH")
        tracked = git(root, "ls-files").splitlines()
        require(len(tracked) == 725, "DOCS_TRACKED_FILE_COUNT")
        rows = []
        for relative in tracked:
            path = root / relative
            require(path.is_file(), "TRACKED_FILE_MISSING")
            rows.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
        aggregate = hashlib.sha256(
            "\n".join(f"{row['path']}|{row['bytes']}|{row['sha256']}" for row in rows).encode("utf-8")
        ).hexdigest()
        candidate_receipt = {
            "schema_version": 1,
            "kind": "game-tools-mo2-docs-windows-candidate",
            "harness_revision": HARNESS_REVISION,
            "status": "PASS",
            "docs_commit": DOCS_COMMIT,
            "product_commit": PRODUCT_COMMIT,
            "docs_parent_commit": DOCS_PARENT_COMMIT,
            "canonical_base": CANONICAL_BASE,
            "tracked_files": len(rows),
            "payload_bytes": sum(row["bytes"] for row in rows),
            "aggregate_sha256": aggregate,
            "changed_paths": sorted(changed),
            "checks": {
                "head_exact": True,
                "parent_exact": True,
                "product_ancestor_exact": True,
                "base_exact": True,
                "worktree_clean": True,
                "docs_and_acceptance_contract_only": True,
            },
            "effects": {"production": False, "real_game": False, "manager": False, "main": False},
        }
        require(privacy_clean(candidate_receipt), "CANDIDATE_RECEIPT_PRIVACY")
        write_json(out / "WINDOWS-DOCS-CANDIDATE.json", candidate_receipt)

        stage = "SOURCE_EXPORT_CONTRACTS"
        contracts = run(
            "source_export_contracts",
            [
                "powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(root / "scripts/tests/Test-GameSourceExport.ps1"),
            ],
            root,
        )
        contract_match = re.search(r"PASS:\s+(\d+)\s+source-export contracts", contracts["stdout"] + contracts["stderr"])
        require(contracts["status"] == "PASS" and contract_match is not None, "SOURCE_EXPORT_CONTRACTS_FAILED")
        contract_count = int(contract_match.group(1))
        require(contract_count == 73, "SOURCE_EXPORT_CONTRACT_COUNT")

        stage = "REAL_SOURCE_EXPORT"
        export_root = out / "source-export"
        export_run = run(
            "source_export",
            [
                "powershell.exe", "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(root / "scripts/Export-GameTools.ps1"),
                "-OutputDirectory", str(export_root),
                "-Bundle", "GameTools",
                "-ClientDate", CLIENT_DATE,
            ],
            root,
        )
        require(export_run["status"] == "PASS", "SOURCE_EXPORT_FAILED")
        export_value = parse_json_output(export_run["stdout"])
        source_root = export_root / "source"
        manifest_path = source_root / "MANIFEST.json"
        require(source_root.is_dir() and manifest_path.is_file(), "EXPORTED_SOURCE_MISSING")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        manifest_rows = manifest.get("files")
        require(isinstance(manifest_rows, list) and len(manifest_rows) == 402, "EXPORTED_MANIFEST_COUNT")
        row_paths = {row["path"] for row in manifest_rows}
        require(ACCEPTANCE_DOCS <= row_paths, "ACCEPTANCE_DOCS_NOT_EXPORTED")
        missing = []
        mismatched = []
        for row in manifest_rows:
            path = source_root / Path(row["path"])
            if not path.is_file():
                missing.append(row["path"])
                continue
            actual_size = path.stat().st_size
            actual_sha = sha256(path)
            if actual_size != row["bytes"] or actual_sha.lower() != row["sha256"].lower():
                mismatched.append(row["path"])
        require(not missing and not mismatched, "EXPORTED_SOURCE_HASH_MISMATCH")
        archive = Path(export_value["archive"])
        require(archive.is_file(), "SOURCE_ARCHIVE_MISSING")
        archive_errors = []
        with zipfile.ZipFile(archive) as zf:
            bad = zf.testzip()
            if bad:
                archive_errors.append(bad)
            names = set(zf.namelist())
        require(not archive_errors, "SOURCE_ARCHIVE_CRC")
        require(names == row_paths | {"MANIFEST.json"}, "SOURCE_ARCHIVE_INVENTORY")
        require(export_value.get("integrity") == "all_source_and_manifest_zip_entries_verified", "SOURCE_EXPORT_INTEGRITY")
        require(export_value.get("source_current_at_final_hash_check") is True, "SOURCE_EXPORT_STALE")
        require(export_value.get("files") == 402, "SOURCE_EXPORT_FILE_COUNT")
        require(sha256(archive) == export_value.get("sha256"), "SOURCE_ARCHIVE_SHA")
        require(sha256(manifest_path) == export_value.get("manifest_sha256"), "SOURCE_MANIFEST_SHA")
        acceptance_json = json.loads((source_root / "docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json").read_text(encoding="utf-8"))
        validation_json = json.loads((source_root / "docs/MO2-READ-ADAPTER-VALIDATION.json").read_text(encoding="utf-8"))
        require(acceptance_json.get("tested_product_commit") == PRODUCT_COMMIT, "EXPORTED_ACCEPTANCE_PRODUCT")
        require(validation_json.get("current_tested_product_commit") == PRODUCT_COMMIT, "EXPORTED_VALIDATION_PRODUCT")
        require(validation_json.get("status") == "PRODUCT_R5_WINDOWS_ACCEPTED_SYNTHETIC_READ_ONLY", "EXPORTED_VALIDATION_STATUS")
        require(validation_json.get("publication_state", {}).get("main_adopted") is False, "EXPORTED_FALSE_ADOPTION")
        source_receipt = {
            "schema_version": 1,
            "kind": "game-tools-mo2-docs-windows-source-export",
            "harness_revision": HARNESS_REVISION,
            "status": "PASS",
            "docs_commit": DOCS_COMMIT,
            "product_commit": PRODUCT_COMMIT,
            "docs_parent_commit": DOCS_PARENT_COMMIT,
            "files": len(manifest_rows),
            "archive_name": archive.name,
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": sha256(archive),
            "manifest_sha256": sha256(manifest_path),
            "acceptance_docs_exported": sorted(ACCEPTANCE_DOCS),
            "powershell_contracts": {
                "status": "PASS",
                "contracts": contract_count,
                "automatic_retry": False,
            },
            "checks": {
                "manifest_files_match": True,
                "archive_entries_match": True,
                "source_current_at_final_hash_check": True,
                "acceptance_product_boundary_exact": True,
                "main_not_adopted": True,
            },
            "effects": {"production": False, "real_game": False, "manager": False, "network_by_product": False},
        }
        require(privacy_clean(source_receipt), "SOURCE_RECEIPT_PRIVACY")
        write_json(out / "WINDOWS-DOCS-SOURCE-EXPORT.json", source_receipt)

        stage = "EXTRACTED_PACKAGE"
        profile_parent = Path(os.environ["LOCALAPPDATA"])
        before_profiles = {path.name for path in profile_parent.glob("GameToolHub-Workbench-Preview-0.28.0-preview.1*")}
        commands = [
            run("packaging", [sys.executable, "-B", str(source_root / "scripts/tests/Test-GameSupportPackaging.py")], source_root),
            run("workbench_verify", [sys.executable, "-B", str(source_root / "scripts/GameToolWorkbenchLaunch.pyw"), "--verify-only"], source_root),
            run("original_verify", [sys.executable, "-B", str(source_root / "scripts/GameToolWorkbenchLaunch.pyw"), "--layout", "Original", "--verify-only"], source_root),
            run("host_pins", [sys.executable, "-B", str(source_root / "scripts/check_host.py"), "--host", str(source_root)], source_root),
        ]
        after_profiles = {path.name for path in profile_parent.glob("GameToolHub-Workbench-Preview-0.28.0-preview.1*")}
        package_text = commands[0]["stdout"] + commands[0]["stderr"]
        test_match = re.search(r"Ran\s+(\d+)\s+tests?", package_text)
        skips = sum(int(value) for value in re.findall(r"skipped=(\d+)", package_text))
        require(all(row["status"] == "PASS" for row in commands), "EXTRACTED_PACKAGE_COMMAND")
        require(test_match is not None and int(test_match.group(1)) == 7 and skips == 0, "EXTRACTED_PACKAGE_TESTS")
        require(before_profiles == after_profiles, "VERIFY_ONLY_PROFILE_CREATED")
        host_value = parse_json_output(commands[3]["stdout"])
        require(host_value.get("status") == "EXACT_DEPENDENCIES_MATCH", "HOST_PINS_STATUS")
        require(len(host_value.get("files", [])) == 13 and all(row.get("matches") for row in host_value["files"]), "HOST_PINS_COUNT")
        package_receipt = {
            "schema_version": 1,
            "kind": "game-tools-mo2-docs-windows-exported-package",
            "harness_revision": HARNESS_REVISION,
            "status": "PASS",
            "docs_commit": DOCS_COMMIT,
            "product_commit": PRODUCT_COMMIT,
            "docs_parent_commit": DOCS_PARENT_COMMIT,
            "packaging_tests": 7,
            "packaging_skips": 0,
            "workbench_verify_only": True,
            "original_verify_only": True,
            "verify_only_created_no_profile": True,
            "host_pins": {"matched": 13, "total": 13},
            "automatic_retry": False,
            "effects": {"production": False, "real_game": False, "manager": False, "profile_created": False},
        }
        require(privacy_clean(package_receipt), "PACKAGE_RECEIPT_PRIVACY")
        write_json(out / "WINDOWS-DOCS-EXPORTED-PACKAGE.json", package_receipt)

        stage = "FINAL"
        final_receipt = {
            "schema_version": 1,
            "kind": "game-tools-mo2-docs-windows-final-acceptance",
            "harness_revision": HARNESS_REVISION,
            "status": "PASS",
            "docs_commit": DOCS_COMMIT,
            "product_commit": PRODUCT_COMMIT,
            "docs_parent_commit": DOCS_PARENT_COMMIT,
            "canonical_base": CANONICAL_BASE,
            "checks": {
                "candidate": True,
                "source_export_contracts": True,
                "source_export": True,
                "exported_package": True,
                "privacy": True,
            },
            "candidate": {"files": candidate_receipt["tracked_files"], "aggregate_sha256": candidate_receipt["aggregate_sha256"]},
            "source_export": {"files": source_receipt["files"], "archive_sha256": source_receipt["archive_sha256"], "manifest_sha256": source_receipt["manifest_sha256"], "contracts": contract_count},
            "package": {"tests": 7, "skipped": 0, "host_pins": 13},
            "automatic_retry": False,
            "effects": {"production": False, "real_game": False, "real_manager_profile": False, "manager_or_game_write": False, "proposal": False, "execution": False, "input": False, "capture": False, "main": False},
        }
        require(privacy_clean(final_receipt), "FINAL_RECEIPT_PRIVACY")
        write_json(out / "WINDOWS-DOCS-FINAL-ACCEPTANCE.json", final_receipt)
        print(json.dumps({"status": "PASS", "docs_commit": DOCS_COMMIT, "files": source_receipt["files"], "contracts": contract_count, "packaging_tests": 7}))
        return 0
    except (GateError, OSError, ValueError, KeyError, json.JSONDecodeError, zipfile.BadZipFile):
        failure = {
            "schema_version": 1,
            "kind": "game-tools-mo2-docs-windows-final-acceptance",
            "harness_revision": HARNESS_REVISION,
            "status": "FAIL_OR_INCOMPLETE",
            "failure_stage": stage,
            "failure_code": sys.exc_info()[1].code if isinstance(sys.exc_info()[1], GateError) else "BOUNDED_GATE_FAILURE",
            "automatic_retry": False,
            "effects": {"production": False, "real_game": False, "real_manager_profile": False, "manager_or_game_write": False, "proposal": False, "execution": False, "input": False, "capture": False, "main": False},
        }
        write_json(out / "WINDOWS-DOCS-FINAL-ACCEPTANCE.json", failure)
        print(json.dumps({"status": failure["status"], "failure_stage": stage, "failure_code": failure["failure_code"]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
