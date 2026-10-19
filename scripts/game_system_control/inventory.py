"""Explicit selected-source snapshots; no profile/database/drive discovery."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path, PurePosixPath

from GameToolAIKnowledge import KnowledgeError, read_selected_source, read_selected_bytes
from .contracts import ContextError, decode, json_value, require, validate_context

MAX_SELECTED_SOURCES = 32
MAX_TOTAL_SOURCE_BYTES = 2 * 1024 * 1024
SENSITIVE_PARTS = {"auth.json", "credentials", "sessions", "archived_sessions", "browser", "cookies", "tokens"}


def _safe_relative(relative):
    require(type(relative) is str, "A selected source needs a relative locator.")
    parts = PurePosixPath(relative).parts
    require(not any(x.casefold() in SENSITIVE_PARTS or x.casefold().startswith(".env") for x in parts) and
            not relative.casefold().endswith((".sqlite", ".sqlite3", ".db", ".env")),
            "Native state and credential sources are outside this reader.")


def selected_text(root, relative, expected=None):
    _safe_relative(relative)
    try:
        return read_selected_source(Path(root), relative, expected)
    except (KnowledgeError, OSError) as exc:
        raise ContextError(str(exc)) from None


def selected_bytes(root, relative, expected, maximum):
    _safe_relative(relative)
    require(expected is not None, "Full content needs an expected revision.")
    try:
        return read_selected_bytes(Path(root), relative, expected, maximum=maximum)
    except (KnowledgeError, OSError) as exc:
        raise ContextError(str(exc)) from None


def bound_root(roots, binding):
    # Only a caller-selected binding supplies filesystem authority. Context JSON
    # cannot introduce a root by embedding an absolute path.
    if isinstance(roots, dict):
        return roots.get(binding)
    return roots if binding == "selected_project" else None


def deferred_sources(context):
    return {r["source_id"] for r in context.get("resources", [])} | {
        s["id"] for s in context["sources"] if s.get("read_policy") == "on_demand"}


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
    deferred = deferred_sources(out)
    selected = [s for s in out["sources"] if s["id"] not in deferred and bound_root(root, s.get("binding")) is not None]
    require(len(selected) <= MAX_SELECTED_SOURCES, "Too many selected sources.")
    refreshed, total = [], 0
    for s in selected:
        row = capture_sources(bound_root(root, s.get("binding")), [{**s, "expected_sha256": s.get("sha256")}])[0]
        total += row.get("bytes", 0)
        require(total <= MAX_TOTAL_SOURCE_BYTES, "Selected-source total exceeds its bound.")
        refreshed.append(row)
    by_id = {s["id"]: s for s in refreshed}
    out["sources"] = [by_id.get(s["id"], s) for s in out["sources"]]
    return validate_context(out)


def environment_context(project_root, cwd="", *, global_root=None, skill_roots=(), catalog=None):
    """Inventory only caller-selected guidance, skill folders and a tool catalog.

    Descriptions and routing cues are declarations, never observed runtime load.
    No configuration, profile database, scheduler or credential store is read.
    Root bindings are returned separately and must not be published with evidence.
    """
    require(len(skill_roots) <= 8, "Too many selected skill folders.")
    doc = project_context(project_root)
    roots = {"selected_project": Path(project_root)}
    chain = discover_instructions(project_root, cwd, global_root=global_root)
    doc["sources"] = [s for s in doc["sources"] if s["id"] != "instructions"]
    doc["nodes"] = [n for n in doc["nodes"] if n["id"] != "instructions"]
    omissions = []
    def add(binding, relative, kind, label, layer="global", **extra):
        if len(doc["sources"]) >= MAX_SELECTED_SOURCES or len(doc["nodes"]) >= 256:
            omissions.append({"kind": kind, "reason": "inventory bound reached"})
            return None
        ident = "selected-" + str(len(doc["sources"]))
        source = capture_sources(roots[binding], [{"id": ident, "owner": "caller-selected source", "locator": relative, "binding": binding}])[0]
        doc["sources"].append(source)
        node = {"id": ident, "kind": kind, "label": label, "source_id": ident, "scopes": [doc["scope"]],
                "layer": layer, "observation": "declared", "depends_on": [], **extra}
        doc["nodes"].append(node)
        return node
    if global_root is not None:
        roots["selected_global"] = Path(global_root)
    for s in chain["sources"]:
        add("selected_global" if s["layer"] == "global" else "selected_project", s["locator"], "instruction",
            s["layer"] + " / " + s["locator"], s["layer"], precedence_order=s["precedence_order"],
            included_bytes=s["included_bytes"], truncated=s["truncated"])
    for i, root in enumerate(skill_roots):
        root = Path(root)
        binding = "selected_skills_" + str(i); roots[binding] = root
        # No recursion; .system or plugin folders need their own explicit selection.
        try:
            if root.is_symlink() or getattr(root.lstat(), "st_file_attributes", 0) & 0x400:
                raise OSError("Linked skill folder")
            names = sorted(p.name for p in root.iterdir())
            require(len(names) <= 512, "Selected skill folder exceeds its entry bound.")
        except OSError:
            omissions.append({"kind": "skill", "reason": "selected folder unavailable"}); continue
        candidates = ["SKILL.md"] if "SKILL.md" in names else [name + "/SKILL.md" for name in names if not name.startswith(".")]
        for relative in candidates:
            if not (root/relative).is_file():
                continue
            node = add(binding, relative, "skill", relative)
            if node is None:
                break
            source = next(s for s in doc["sources"] if s["id"] == node["source_id"])
            if source["availability"] != "available":
                continue
            text = selected_text(root, relative, source["sha256"])["content"]
            header = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
            # Exact scalar frontmatter only. Multiline/YAML constructs stay visible
            # in the source; they are not guessed or executed by a YAML loader.
            fields = dict(line.split(":", 1) for line in header.splitlines() if ":" in line and not line.startswith((" ", "\t")))
            name = fields.get("name", "").strip().strip("\"'")
            description = fields.get("description", "").strip().strip("\"'")
            if name and len(name) <= 100:
                node.update(label=name, trigger_terms=["$" + name], trigger="Explicit skill name; semantic matching remains conditional.")
            if description and description not in {"|", ">", "|-", ">-"}:
                node["declared_description"] = description
    if catalog is not None:
        path = Path(catalog).absolute(); roots["selected_catalog"] = path.parent
        node = add("selected_catalog", path.name, "component", "Selected capability declarations")
        if node is not None:
            source = next(s for s in doc["sources"] if s["id"] == node["source_id"])
            value = json_value(selected_text(path.parent, path.name, source["sha256"])["content"].encode("utf-8"))
            require(type(value) is dict and value.get("kind") == "GameToolsCapabilityCatalog" and value.get("schema_version") == 1,
                    "Unsupported capability catalog.")
            for group, kind in (("tools", "tool"), ("automations", "automation")):
                rows = value.get(group, [])
                require(type(rows) is list and len(rows) <= 256, "Capability catalog exceeds its bound.")
                for row in rows:
                    require(type(row) is dict and type(row.get("name")) is str and bool(row["name"]), "A capability needs a name.")
                    if len(doc["nodes"]) >= 256:
                        omissions.append({"kind": kind, "reason": "node bound reached"}); break
                    doc["nodes"].append({"id": "capability-" + str(len(doc["nodes"])), "kind": kind, "label": row["name"],
                        "source_id": source["id"], "scopes": [doc["scope"]], "layer": "global", "observation": "declared",
                        "depends_on": [], "declared_description": row.get("description", ""), "trigger_terms": row.get("trigger_terms", [])})
    require(sum(s.get("bytes", 0) for s in doc["sources"]) <= MAX_TOTAL_SOURCE_BYTES, "Selected-source total exceeds its bound.")
    doc["instruction_discovery"] = {k: v for k, v in chain.items() if k != "sources"}
    doc["inventory_omissions"] = omissions
    doc["unknown_coverage"] = ["Unselected guidance, skills, tools and automations", "Account and platform memory", "Actual runtime load and tool permission", "Other computer"]
    doc["label"] = "Selected environment guidance and capability declarations"
    return validate_context(doc), roots


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
