"""Read and stage ZIPs without executing their contents. Reject Windows path aliases."""
from __future__ import annotations
import hashlib
import os
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from .safety import ModError, require, safe_relative, contained, no_links, regular, digest, slug, strict_json

MAX_FILES = 10000
MAX_EXPANDED = 512 * 1024 * 1024
MAX_SINGLE = 256 * 1024 * 1024


def inspect_zip(path: Path, expected_id: str | None = None, manager: bool = False, layout: str = "umm") -> dict:
    path = regular(path, 256 * 1024 * 1024)
    initial_sha = digest(path)
    try:
        with zipfile.ZipFile(path) as z:
            entries = z.infolist()
            require(0 < len(entries) <= MAX_FILES, "ZIP_LIMIT", "Archive has too many or no entries.")
            seen, sizes, files = set(), 0, {}
            for i in entries:
                rel = str(safe_relative(i.filename))
                folded = rel.casefold()
                require(folded not in seen, "ZIP_COLLISION", "Archive contains duplicate or case-colliding paths.")
                seen.add(folded)
                mode = i.external_attr >> 16
                require(stat.S_IFMT(mode) in (0, stat.S_IFREG, stat.S_IFDIR), "ZIP_SPECIAL_FILE", "Links and special files are not accepted.")
                require(not (i.flag_bits & 1), "ZIP_ENCRYPTED", "Encrypted archives are not supported.")
                require(i.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), "ZIP_FORMAT", "Unsupported ZIP compression; use the author's supported archive workflow.")
                sizes += i.file_size
                require(sizes <= MAX_EXPANDED and i.file_size <= MAX_SINGLE, "ZIP_LIMIT", "Expanded archive exceeds the safety limit.")
                require(i.file_size < 1024 * 1024 or i.file_size / max(1, i.compress_size) <= 500,
                        "ZIP_RATIO", "Archive compression ratio exceeds the safety limit.")
                if not i.is_dir():
                    files[rel] = i
            all_paths = {p.casefold(): p for p in files}
            for p in all_paths:
                require(not any(str(parent).casefold() in all_paths for parent in PurePosixPath(p).parents if str(parent) != "."),
                        "ZIP_COLLISION", "An archive file is also used as a directory.")
            require(layout in {"umm", "generic"}, "ARCHIVE_LAYOUT", "Unknown archive layout.")
            if layout == "generic":
                prefix, info = "", {"Id": "unidentified", "Version": "not-verified"}
            elif manager:
                exe = [p for p in files if PurePosixPath(p).name.casefold() == "unitymodmanager.exe"]
                require(len(exe) == 1, "MANAGER_IDENTITY", "Expected one UnityModManager.exe in this manager archive.")
                prefix = str(PurePosixPath(exe[0]).parent)
                prefix = "" if prefix == "." else prefix + "/"
                require((prefix + "UnityModManagerConfig.xml").casefold() in all_paths,
                        "MANAGER_IDENTITY", "UMM configuration is missing from this archive.")
                info = {"Id": "UnityModManager", "Version": "not-verified-from-binary"}
            else:
                infos = [p for p in files if PurePosixPath(p).name.casefold() == "info.json"]
                require(len(infos) == 1, "ARCHIVE_LAYOUT", "Expected one UMM Info.json; multi-mod packs need separate review.")
                require(files[infos[0]].file_size <= 256 * 1024, "ZIP_LIMIT", "Mod metadata is too large.")
                try:
                    info = strict_json(z.read(infos[0]))
                except (ValueError, UnicodeError):
                    raise ModError("INVALID_MOD_INFO", "Mod metadata is not valid UTF-8 JSON.") from None
                require(isinstance(info, dict), "INVALID_MOD_INFO", "UMM metadata must be an object.")
                mod_id = slug(info.get("Id", ""))
                require(not expected_id or mod_id == expected_id, "MOD_ID_MISMATCH", "The archive UMM ID differs from the recipe.")
                require(isinstance(info.get("Version"), str) and 0 < len(info["Version"]) < 80,
                        "INVALID_MOD_INFO", "UMM version is missing or invalid.")
                prefix = str(PurePosixPath(infos[0]).parent)
                prefix = "" if prefix == "." else prefix + "/"
                assembly = info.get("AssemblyName", mod_id + ".dll")
                safe_relative(assembly)
                require((prefix + assembly).casefold() in all_paths, "ASSEMBLY_MISSING", "The declared mod assembly is missing.")
            manifest, omitted = {}, []
            for p, i in files.items():
                h = hashlib.sha256()
                with z.open(i) as f:
                    for chunk in iter(lambda: f.read(1024 * 1024), b""):
                        h.update(chunk)
                if p.startswith(prefix):
                    relative = p[len(prefix):]
                    manifest[relative] = {"sha256": h.hexdigest(), "bytes": i.file_size}
                else:
                    omitted.append(p)
            require(not omitted or all(PurePosixPath(p).suffix.lower() in (".md", ".txt", ".png", ".jpg")
                                        or PurePosixPath(p).name.upper() in ("LICENSE", "COPYING") for p in omitted),
                    "ARCHIVE_LAYOUT", "Unexpected payload outside the mod folder; staging stopped for review.")
            require(digest(path) == initial_sha, "SOURCE_CHANGED", "Archive changed during inspection.")
            return {"archive_sha256": initial_sha, "kind": "generic_zip" if layout == "generic" else ("umm_manager" if manager else "umm_mod"),
                    "mod_id": info["Id"], "version": info["Version"], "prefix": prefix,
                    "info": {k: info[k] for k in ("Id", "Version", "ManagerVersion", "Requirements", "AssemblyName") if k in info},
                    "manager_version": info.get("ManagerVersion"), "requirements": info.get("Requirements", []),
                    "files": manifest, "omitted_documentation": omitted, "uncompressed_bytes": sizes}
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as e:
        raise ModError("INVALID_ZIP", "Archive could not be verified; no contents were executed.") from e


def stage_zip(path: Path, dest: Path, inspected: dict) -> dict:
    dest = no_links(dest)
    require(not dest.exists(), "EXISTS", "Staging folder already exists; inspect it instead of replacing it.")
    require(digest(path) == inspected["archive_sha256"], "SOURCE_CHANGED", "Archive changed after inspection.")
    dest.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(path) as z:
        for rel, expected in inspected["files"].items():
            target = contained(dest, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            size = 0
            with z.open(inspected["prefix"] + rel) as src, target.open("xb") as out:
                for data in iter(lambda: src.read(1024 * 1024), b""):
                    size += len(data)
                    require(size <= expected["bytes"], "SOURCE_CHANGED", "Expanded bytes exceed the reviewed entry size.")
                    out.write(data)
                    h.update(data)
                out.flush(); os.fsync(out.fileno())
            require(size == expected["bytes"] and h.hexdigest() == expected["sha256"],
                    "SOURCE_CHANGED", "Staged file does not match inspected bytes.")
    require(digest(path) == inspected["archive_sha256"], "SOURCE_CHANGED", "Archive changed during staging.")
    return {"status": "STAGED_NOT_INSTALLED", "files": len(inspected["files"]), "mod_id": inspected["mod_id"]}


def tree_audit(root: Path, expected: dict) -> dict:
    root = no_links(root)
    actual, changed, missing, extra_dirs = set(), [], [], []
    expected_dirs = {str(p) for rel in expected for p in PurePosixPath(rel).parents if str(p) != "."}
    if root.exists():
        for p in root.rglob("*"):
            no_links(p)
            if p.is_dir() and p.relative_to(root).as_posix() not in expected_dirs:
                extra_dirs.append(p.relative_to(root).as_posix())
            if p.is_file():
                rel = p.relative_to(root).as_posix()
                actual.add(rel)
                if rel in expected and digest(p) != expected[rel]["sha256"]:
                    changed.append(rel)
    missing = sorted(set(expected) - actual)
    extra = sorted(actual - set(expected))
    return {"status": "MATCH" if not (changed or missing or extra or extra_dirs) else "DRIFT",
            "changed": sorted(changed), "missing": missing, "extra": extra, "extra_directories": sorted(extra_dirs),
            "note": "Drift may be legitimate generated settings, not necessarily damage. No automatic repair."}
