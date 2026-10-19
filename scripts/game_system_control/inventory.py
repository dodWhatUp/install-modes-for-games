"""Explicit selected-source snapshots; no profile/database/drive discovery."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath

from GameToolAIKnowledge import KnowledgeError, read_selected_source
from .contracts import ContextError, decode, require, validate_context

MAX_SELECTED_SOURCES = 32
MAX_TOTAL_SOURCE_BYTES = 2 * 1024 * 1024
SENSITIVE_PARTS = {"auth.json", "credentials", "sessions", "archived_sessions", "browser", "cookies", "tokens"}


def selected_text(root, relative, expected=None):
    require(type(relative) is str, "A selected source needs a relative locator.")
    parts = PurePosixPath(relative).parts
    require(not any(x.casefold() in SENSITIVE_PARTS or x.casefold().startswith(".env") for x in parts) and
            not relative.casefold().endswith((".sqlite", ".sqlite3", ".db", ".env")),
            "Native state and credential sources are outside this reader.")
    try:
        return read_selected_source(Path(root), relative, expected)
    except (KnowledgeError, OSError) as exc:
        raise ContextError(str(exc)) from None


def load_context(path):
    path = Path(path).absolute()
    # The existing bounded reader owns filesystem identity and link checks.
    value = selected_text(path.parent, path.name)
    return decode(value["content"].encode("utf-8"))


def capture_sources(root, selections):
    require(type(selections) is list and len(selections) <= MAX_SELECTED_SOURCES, "Too many selected sources.")
    rows, total, seen = [], 0, set()
    for source in selections:
        require(source["id"] not in seen, "Duplicate selected source identity.")
        seen.add(source["id"])
        row = deepcopy(source)
        try:
            snap = selected_text(root, source["locator"], source.get("expected_sha256"))
            total += snap["bytes"]
            row.update(sha256=snap["sha256"], bytes=snap["bytes"], availability="available")
        except ContextError as exc:
            row.update(sha256=source.get("expected_sha256"), availability="stale" if "changed" in str(exc) else "unreadable", problem=str(exc))
        require(total <= MAX_TOTAL_SOURCE_BYTES, "Selected-source total exceeds its bound.")
        rows.append(row)
    return rows


def project_context(root):
    """Explicit current-project view over a small fixed source selection."""
    chain = discover_instructions(root)
    instruction_path = chain["sources"][0]["locator"] if chain["sources"] else "AGENTS.md"
    paths = [("instructions", instruction_path, "instruction", "Project instructions"),
             ("preferences", "preferences/GENERAL.md", "preference", "Project preferences"),
             ("data", "scripts/GameToolUserData.py", "component", "Existing user-data archive owner"),
             ("journal", "scripts/GameToolJournal.py", "component", "Existing journal owner"),
             ("approval", "scripts/GameToolAutomation.py", "component", "Existing approval owner"),
             ("knowledge", "scripts/GameToolAIKnowledge.py", "component", "Existing bounded source reader"),
             ("tools", "scripts/GameToolAITools.py", "tool", "Declared toolkit AI capabilities"),
             ("plan", "docs/INTEGRATED-SYSTEM-WORK-PACKAGES.json", "component", "Development task dependencies")]
    sources = capture_sources(root, [{"id": ident, "owner": "dodWhatUp/install-modes-for-games", "locator": locator,
                                      "binding": "selected_project"} for ident, locator, _, _ in paths])
    nodes = [{"id": ident, "kind": kind, "label": label, "source_id": ident,
              "scopes": ["project.game-tools"], "layer": "project", "observation": "declared", "depends_on": []}
             for ident, _, kind, label in paths]
    try:
        preference = selected_text(root, "preferences/GENERAL.md")
        sentence = next((line for line in preference["content"].splitlines() if line.startswith("Response language,") and "always answer in English" in line), None)
        if sentence:
            nodes[1]["quote"] = sentence
            nodes[1]["default"] = {"key": "response.language", "value": "English", "category": "presentation_preference", "redundant_lines": ["Answer in English."]}
    except ContextError:
        pass
    return validate_context({"schema_version": 1, "kind": "GameToolsSystemContext", "scope": "project.game-tools",
                             "label": "Current project · selected source inventory", "sources": sources, "nodes": nodes,
                             "instruction_discovery": {k: v for k, v in chain.items() if k != "sources"},
                             "devices": [{"id": "other-device", "label": "Other computer · not observed", "availability": "unknown", "last_seen": None}],
                             "events": [], "activities": [], "resources": [],
                             "unknown_coverage": ["Global/child-directory instructions outside this selected root", "Unselected skills, automations and account memory", "Actual runtime-loaded instructions", "Other computer"]})


def check_sources(context, root):
    out = validate_context(context)
    # This local adapter refreshes only locators explicitly marked for this root.
    selected = [s for s in out["sources"] if s.get("binding") == "selected_project"]
    refreshed = capture_sources(root, [{**s, "expected_sha256": s.get("sha256")} for s in selected])
    by_id = {s["id"]: s for s in refreshed}
    out["sources"] = [by_id.get(s["id"], s) for s in out["sources"]]
    return validate_context(out)


def discover_instructions(project_root, cwd="", *, global_root=None, fallback_names=(), max_bytes=32768):
    """Explain documented Codex discovery for selected roots, not runtime load.

    https://learn.chatgpt.com/docs/agent-configuration/agents-md
    A global override is independent of the root-to-leaf project chain. No
    configuration is edited and no hidden platform instructions are inferred.
    """
    require(type(cwd) is str and (cwd == "" or (PurePosixPath(cwd).as_posix() == cwd and
            not cwd.startswith("/") and ":" not in cwd and "\\" not in cwd and
            all(p not in {".", "..", ""} for p in cwd.split("/")))), "Invalid selected working directory.")
    require(type(max_bytes) is int and 1 <= max_bytes <= MAX_TOTAL_SOURCE_BYTES, "Invalid instruction byte limit.")
    require(len(fallback_names) <= 8 and all(type(n) is str and PurePosixPath(n).name == n and
            "/" not in n and "\\" not in n and n not in {"", ".", ".."} for n in fallback_names), "Invalid fallback name.")
    roots = []
    if global_root is not None:
        roots.append((Path(global_root), "", "global", ("AGENTS.override.md", "AGENTS.md")))
    project_root = Path(project_root)
    chain = [""] + ["/".join(cwd.split("/")[:i]) for i in range(1, len(cwd.split("/")) + 1) if cwd]
    require(len(chain) <= 16, "Instruction chain exceeds its bound.")
    roots += [(project_root, prefix, "project" if not prefix else "directory", ("AGENTS.override.md", "AGENTS.md", *fallback_names)) for prefix in chain]
    result, consumed = [], 0
    for root, prefix, layer, names in roots:
        for name in names:
            relative = prefix + "/" + name if prefix else name
            try:
                snap = selected_text(root, relative)
            except ContextError:
                # Missing files are normal. Present but unsafe sources are not silently skipped.
                if (root / relative).exists() or (root / relative).is_symlink():
                    raise
                continue
            if not snap["content"].strip():
                continue
            remaining = max_bytes - consumed
            result.append({**snap, "layer": layer, "precedence_order": len(result),
                           "loaded": "not_observed", "included_bytes": min(snap["bytes"], max(0, remaining)),
                           "truncated": snap["bytes"] > remaining})
            consumed += snap["bytes"]
            break
    return {"sources": result, "max_bytes": max_bytes, "coverage": "declared_discovery_only",
            "limit_reached": consumed > max_bytes, "runtime_loaded": "not_observed"}
