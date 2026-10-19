"""Source-bound local instruction/component projection, not a rule executor."""
from __future__ import annotations

from copy import deepcopy

from GameToolAIContracts import stable_revision
from .contracts import ContextError, validate_context, require
from .inventory import selected_text, MAX_SELECTED_SOURCES, MAX_TOTAL_SOURCE_BYTES


def build_view(context, root=None, scope=None, query=""):
    doc = validate_context(context)
    scope = doc["scope"] if scope is None else scope
    sources, texts, total = {}, {}, 0
    require(sum(s.get("binding") == "selected_project" for s in doc.get("sources", [])) <= MAX_SELECTED_SOURCES,
            "Too many selected sources for one view.")
    for source in doc.get("sources", []):
        row = deepcopy(source)
        row["verification"] = "not_observed"
        if root is not None and source.get("binding") == "selected_project":
            try:
                snap = selected_text(root, source["locator"], source.get("sha256"))
                total += snap["bytes"]
                row.update(availability="available", verification="hash_checked", sha256=snap["sha256"])
                texts[source["id"]] = snap["content"]
            except ContextError as exc:
                row.update(availability="stale" if "changed" in str(exc) else "unreadable", problem=str(exc))
        require(total <= MAX_TOTAL_SOURCE_BYTES, "Selected-source total exceeds its bound.")
        sources[source["id"]] = row
    nodes = []
    for raw in doc.get("nodes", []):
        node = deepcopy(raw)
        source = sources[node["source_id"]]
        node["applicable"] = node.get("layer") != "historical" and (scope in node["scopes"] or "*" in node["scopes"])
        node["source"] = {k: source.get(k) for k in ("id", "owner", "locator", "sha256", "availability", "verification")}
        node["fresh"] = source["availability"] == "available" and source["verification"] == "hash_checked"
        quote = node.get("quote")
        if quote and source["id"] in texts and quote not in texts[source["id"]]:
            node["fresh"] = False
            node["source"]["availability"] = "stale"
            node["source"]["problem"] = "Declared rule quote is absent from the selected revision."
        node["runtime_load"] = "not_observed" if node["observation"] == "declared" else "reported_by_selected_context"
        nodes.append(node)
    defaults = {}
    for node in nodes:
        if node["applicable"] and node.get("default"):
            defaults.setdefault(node["default"]["key"], []).append(node)
    conflicts, repeated = [], []
    for key, group in defaults.items():
        variants = {stable_revision(n["default"]["value"]) for n in group}
        if len(variants) > 1:
            conflicts.append({"key": key, "nodes": [n["id"] for n in group],
                              "meaning": "Conflicting declarations; no default is treated as settled."})
        elif len(group) > 1:
            repeated.append({"key": key, "nodes": [n["id"] for n in group]})
    terms = query.casefold().split()
    filtered = [n for n in nodes if all(t in str(n).casefold() for t in terms)]
    return {"kind": "read_only_system_view", "scope": scope, "label": doc.get("label", "Selected context"),
            "nodes": filtered, "all_nodes": nodes, "sources": list(sources.values()),
            "edges": [{"from": n["id"], "to": d, "relationship": "depends_on"} for n in nodes for d in n.get("depends_on", [])],
            "conflicts": conflicts, "repeated_defaults": repeated,
            "revision": stable_revision({"document": doc, "sources": list(sources.values()), "scope": scope}),
            "precedence": "Documented Codex discovery is global then project root to working directory, with override selection within each directory. Session/platform authority and actual load are not established by this view.",
            "unknowns": ["Hidden platform instructions", "Inaccessible memory", "Unreported tools/automations", "Exact future model behavior"],
            "effect": "none"}


def graph_text(view):
    labels = {n["id"]: n["label"] for n in view["all_nodes"]}
    lines = [f"{n['id']}: {n['label']}" for n in view["nodes"]]
    lines += [f"{e['from']} -> {e['to']} ({labels[e['to']]})" for e in view["edges"]]
    return "\n".join(lines) or "No matching nodes."
