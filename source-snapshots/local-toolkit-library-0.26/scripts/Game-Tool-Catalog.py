"""Read-only catalog and overhead plans. No actions, collectors or metric calculations."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

VERSION = "0.1.1"
RELATIONS = {"hosts", "manages", "enables", "depends_on", "alternative_to", "conflict_candidate"}
STATUSES = {"local-tested", "upstream-supported", "inference", "unknown", "historical"}
INSTALLATION = {"unknown", "recorded-present", "recorded-absent"}
METRICS = {"cpu_utilization_pct": None, "cpu_time_s": None, "gpu_utilization_pct": None,
           "process_resident_ram_mib": None, "process_private_commit_mib": None,
           "adapter_vram_used_mib": None, "process_vram_resident_mib": None,
           "process_vram_budget_mib": None}
SCOPES = {
    "CPU": "Provider process CPU/time versus system/core use; interval and scope retained.",
    "GPU": "Provider adapter or process workload; utilization is not a bottleneck proof.",
    "RAM": "Resident working set, private commit and system commit are different quantities.",
    "VRAM": "Adapter allocation includes other processes; process residency/budget require a validated source.",
}
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "examples/game-tool-hub/catalog.example.json"


class CatalogError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise CatalogError(message)


def string(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} must be nonempty text")
    return value


def keys(value, allowed, required, label):
    require(isinstance(value, dict), f"{label} must be an object")
    require(not (set(value) - allowed), f"{label} has unsupported fields")
    require(required <= set(value), f"{label} is missing required fields")


def evidence(value, label):
    require(isinstance(value, list) and bool(value), f"{label} requires provenance")
    for item in value:
        keys(item, {"kind", "reference", "reviewed", "scope"}, {"kind", "reference", "reviewed"}, label)
        require(item["kind"] in {"repository", "primary", "chat"}, f"{label} has an unknown source kind")
        string(item["reference"], label)
        require(isinstance(item["reviewed"], str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", item["reviewed"])),
                f"{label} requires an ISO review date")
        if "scope" in item:
            string(item["scope"], label)


def relation_applies(relation, game):
    return relation.get("game") in (None, game)


def dependencies(catalog, node, game):
    found = set()
    for relation in catalog["relationships"]:
        if not relation_applies(relation, game):
            continue
        if relation["type"] == "depends_on" and relation["from"] == node:
            found.add(relation["to"])
        elif relation["type"] == "hosts" and relation["to"] == node:
            found.add(relation["from"])
    return found


def closure(catalog, initial, game):
    complete, visiting = set(), set()

    def visit(node):
        if node in complete:
            return
        require(node not in visiting, "Mandatory dependency cycle prevents a safe plan")
        visiting.add(node)
        for dependency in sorted(dependencies(catalog, node, game)):
            visit(dependency)
        visiting.remove(node)
        complete.add(node)
    for node in sorted(initial):
        visit(node)
    return complete


def validate(catalog):
    keys(catalog, {"schema_version", "status", "components", "games", "features", "relationships", "actions"},
         {"schema_version", "status", "components", "games", "features", "relationships", "actions"}, "catalog")
    require(catalog["schema_version"] == 1, "Unsupported catalog schema")
    require(catalog["status"] == "planning-foundation", "Catalog is not a planning-only foundation")
    for field in ("components", "games", "features", "relationships", "actions"):
        require(isinstance(catalog[field], list) and len(catalog[field]) <= 1000, f"Invalid bounded {field} list")
    index = {}
    common = {"id", "name", "kind", "categories", "status", "provenance", "installation", "notes", "idle_process"}
    for collection in ("components", "games", "features"):
        for node in catalog[collection]:
            allowed = common if collection == "components" else ({"id", "name", "required_components", "provenance"}
                      if collection == "games" else common | {"component", "game", "planning", "settings_label"})
            required = {"id", "name", "provenance"} if collection == "games" else {"id", "name", "kind", "categories", "status", "provenance", "installation"}
            if collection == "features":
                required |= {"component", "game", "planning"}
            keys(node, allowed, required, collection)
            identifier = string(node["id"], collection)
            require(bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", identifier)), "Invalid portable identifier")
            require(identifier not in index, f"Duplicate identifier: {identifier}")
            string(node["name"], identifier)
            evidence(node["provenance"], identifier)
            index[identifier] = (collection, node)
            if collection == "games":
                require(isinstance(node.get("required_components", []), list), "Required components must be a list")
                continue
            require(node["status"] in STATUSES, f"Unknown evidence status: {identifier}")
            string(node["kind"], identifier)
            require(isinstance(node["categories"], list) and all(isinstance(x, str) for x in node["categories"]), "Invalid categories")
            keys(node["installation"], {"status", "evidence"}, {"status", "evidence"}, "installation")
            require(node["installation"]["status"] in INSTALLATION, "Invalid installation status")
            require(isinstance(node["installation"]["evidence"], list), "Installation evidence must be a list")
            if node["installation"]["status"] != "unknown":
                evidence(node["installation"]["evidence"], "Recorded installation")
            if "idle_process" in node:
                require(isinstance(node["idle_process"], bool), "idle_process must be boolean")
            if collection == "features":
                require(node["planning"] in {"prepared", "needs-review", "blocked"}, "Unknown feature planning gate")
    for identifier, (collection, node) in index.items():
        if collection == "features":
            require(index.get(node["component"], (None,))[0] == "components", f"Unknown component: {identifier}")
            require(index.get(node["game"], (None,))[0] == "games", f"Unknown game: {identifier}")
        elif collection == "games":
            require(all(index.get(x, (None,))[0] == "components" for x in node.get("required_components", [])), "Invalid required component")
    relationship_ids = set()
    for relation in catalog["relationships"]:
        keys(relation, {"id", "type", "from", "to", "game", "status", "provenance", "notes"},
             {"id", "type", "from", "to", "status", "provenance"}, "relationship")
        require(relation["id"] not in relationship_ids, "Duplicate relationship identifier")
        relationship_ids.add(string(relation["id"], "relationship"))
        require(relation["type"] in RELATIONS, "Unsupported relationship type")
        require(relation["status"] in STATUSES, "Unknown relationship evidence status")
        require(relation["from"] in index and relation["to"] in index, "Relationship references an unknown node")
        require(relation["from"] != relation["to"], "Self relationship is invalid")
        require("game" not in relation or index.get(relation["game"], (None,))[0] == "games", "Unknown relationship game")
        evidence(relation["provenance"], "relationship")
    for game in catalog["games"]:
        closure(catalog, index, game["id"])
    action_ids = set()
    for action in catalog["actions"]:
        keys(action, {"id", "name", "target", "capability", "execution", "preconditions", "provenance"},
             {"id", "name", "target", "capability", "execution", "preconditions", "provenance"}, "action")
        require(action["id"] not in action_ids, "Duplicate action identifier")
        action_ids.add(string(action["id"], "action"))
        string(action["name"], "action")
        require(action["target"] in index, "Unknown action target")
        require(action["capability"] in {"inspect", "import-report", "prepare-input-check", "prepare-install", "prepare-capture", "prepare-diagnostic-capture", "prepare-overhead"}, "Unknown capability")
        require(action["execution"] == "declaration-only", "Executable actions are prohibited")
        require(isinstance(action["preconditions"], list) and bool(action["preconditions"]) and all(isinstance(x, str) for x in action["preconditions"]), "Actions require declared preconditions")
        evidence(action["provenance"], "action")
    return index


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key")
        result[key] = value
    return result


def load_catalog(path):
    require(path.stat().st_size <= 1024 * 1024, "Catalog exceeds the 1 MiB limit")
    def reject_constant(value):
        raise CatalogError("Nonfinite JSON constants are prohibited")
    catalog = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=no_duplicate_keys, parse_constant=reject_constant)
    validate(catalog)
    return catalog


def filtered_nodes(catalog, kind=None, category=None, game=None, status=None, relationship=None, search=None,
                   installation=None, sort="id"):
    index = validate(catalog)
    require(game is None or index.get(game, (None,))[0] == "games", "Unknown game filter")
    require(relationship is None or relationship in RELATIONS, "Unknown relationship filter")
    require(installation is None or installation in INSTALLATION, "Unknown installation evidence filter")
    require(sort in {"id", "name", "kind", "status"}, "Unknown catalog sort")
    selected = set(index)
    if game:
        selected = {game}
        for feature in catalog["features"]:
            if feature["game"] == game:
                selected |= {feature["id"], feature["component"]}
        for relation in catalog["relationships"]:
            if relation.get("game") == game:
                selected |= {relation["from"], relation["to"]}
        selected = closure(catalog, selected, game)
    if relationship:
        selected &= {end for r in catalog["relationships"] if r["type"] == relationship and (not game or relation_applies(r, game))
                     for end in (r["from"], r["to"])}
    result = []
    for identifier in sorted(selected):
        collection, node = index[identifier]
        if kind and kind not in (collection.rstrip("s"), node.get("kind")):
            continue
        if category and category not in node.get("categories", []):
            continue
        if status and status != node.get("status"):
            continue
        if installation and installation != node.get("installation", {}).get("status"):
            continue
        if search and search.casefold() not in " ".join((node["name"], identifier, *node.get("categories", []))).casefold():
            continue
        result.append({"entity": collection.rstrip("s"), **node})
    return sorted(result, key=lambda node: (str(node.get(sort, node["entity"] if sort == "kind" else "unknown")).casefold(), node["id"]))


def show_node(catalog, identifier):
    index = validate(catalog)
    require(identifier in index, "Unknown catalog identifier")
    collection, node = index[identifier]
    return {"entity": collection.rstrip("s"), **node,
            "relationships": [r for r in catalog["relationships"] if identifier in (r["from"], r["to"])],
            "declared_actions": [a for a in catalog["actions"] if a["target"] == identifier],
            "measured_metrics": METRICS.copy()}


def plan_overhead(catalog, scope, game=None, factors=None):
    index = validate(catalog)
    factors = factors or []
    require(len(factors) in (1, 2) and len(set(factors)) == len(factors), "Select one distinct factor or two for a 2x2 plan")
    require(all(x in index for x in factors), "Unknown factor")
    require(scope in {"process-idle", "in-game"}, "Unknown overhead scope")
    plan = {"schema_version": 1, "status": "prepared-not-authorized", "scope": scope, "game": game,
            "factors": factors, "execution": "none", "metrics_calculated": False,
            "measured_metrics": METRICS.copy(), "metric_scopes": SCOPES.copy(), "cases": [], "blockers": [],
            "preconditions": ["Explicit user authorization before any execution",
                "Just-in-time snapshot and one input/capture owner", "Existing provider exports and their definitions validated",
                "No saves or graphics changes outside separately authorized scope", "Matched workload/settings/cache and repeated runs",
                "Measure coordinator/recording overhead separately; missing values remain unavailable"],
            "interpretation": "Process-idle manager cost is separate from deployed/injected in-game feature cost; no assigned estimates."}
    def block(message):
        plan["status"] = "blocked"
        plan["blockers"].append(message)
    if scope == "process-idle":
        if game is not None or any(index[x][0] != "components" or not index[x][1].get("idle_process", False) for x in factors):
            block("Idle process plans require identified standalone components, not game features or unresolved aliases")
        plan["interpretation"] += " Keep deployed game files identical; no game run or capture is implied. Closing a manager does not disable its payload."
        protected = set()
    else:
        if index.get(game, (None,))[0] != "games":
            block("An exact catalog game is required")
        for factor in factors:
            collection, feature = index[factor]
            if collection != "features" or feature.get("game") != game:
                block(f"{factor}: choose a feature belonging to this game")
            elif feature["planning"] != "prepared":
                block(f"{factor}: feature needs compatibility review or is unsupported")
        if plan["blockers"]:
            return plan
        roots = set(index[game][1].get("required_components", []))
        # Keep every selected feature's component and dependency union on in all cases.
        # This measures incremental features, never host/loader removal as an off state.
        roots |= {index[x][1]["component"] for x in factors}
        for factor in factors:
            roots |= dependencies(catalog, factor, game)
        protected = closure(catalog, roots, game)
        if protected & set(factors):
            block("A factor is a mandatory dependency of another factor; independent Off states are invalid")
        all_nodes = protected | set(factors)
        for relation in catalog["relationships"]:
            if relation["type"] in {"hosts", "depends_on"} and relation_applies(relation, game) and {relation["from"], relation["to"]} <= all_nodes and relation["status"] in {"unknown", "inference"}:
                block(f"Mandatory dependency requires support review: {relation['id']}")
            if relation["type"] == "conflict_candidate" and relation_applies(relation, game) and {relation["from"], relation["to"]} <= all_nodes:
                block(f"Unresolved compatibility gate: {relation['id']}")
        unknown = [x for x in protected if index[x][0] == "components" and index[x][1]["kind"] == "unresolved-alias"]
        if unknown:
            block("Unresolved dependency identity prevents a plan")
        plan["interpretation"] += " Required native baseline and all shared hosts/loaders remain On, including Off/Off. Feature disable paths require separate live acceptance."
    plan["always_on"] = sorted(protected)
    if plan["blockers"]:
        return plan
    bits = [(0,), (1,)] if len(factors) == 1 else [(0, 0), (1, 0), (0, 1), (1, 1)]
    for values in bits:
        plan["cases"].append({"id": "-".join(map(str, values)), "factor_state": dict(zip(factors, (bool(x) for x in values))),
            "always_on": sorted(protected), "measured_metrics": METRICS.copy(), "runs": [],
            "acceptance": "Configuration equality, component ownership, compatible feature toggle and provider scope must be observed before a run is comparable."})
    plan["repeat_policy"] = "At least three matched runs per case; A/B/A or balanced order; warm/first-visit/loading phases separate."
    plan["interaction_status"] = "Not measured; compare reported case results without assuming costs add linearly."
    return plan


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        raise CatalogError(message)


def main(argv=None):
    parser = JsonParser(add_help=False, description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    sub = parser.add_subparsers(dest="command", required=True, parser_class=JsonParser)
    sub.add_parser("validate", add_help=False)
    listing = sub.add_parser("list", add_help=False)
    for option in ("kind", "category", "game", "status", "relationship", "search"):
        listing.add_argument("--" + option)
    listing.add_argument("--installation", choices=sorted(INSTALLATION))
    listing.add_argument("--sort", choices=("id", "name", "kind", "status"), default="id")
    show = sub.add_parser("show", add_help=False)
    show.add_argument("id")
    plan = sub.add_parser("plan-overhead", add_help=False)
    plan.add_argument("--scope", required=True, choices=("process-idle", "in-game"))
    plan.add_argument("--game")
    plan.add_argument("--factor", action="append", required=True)
    try:
        args = parser.parse_args(argv)
        catalog = load_catalog(args.catalog)
        if args.command == "validate":
            result = {"valid": True, "schema_version": 1, "version": VERSION,
                      "counts": {x: len(catalog[x]) for x in ("components", "games", "features", "relationships", "actions")}}
        elif args.command == "list":
            result = {"nodes": filtered_nodes(catalog, **{x: getattr(args, x) for x in ("kind", "category", "game", "status", "relationship", "search", "installation", "sort")})}
        elif args.command == "show":
            result = show_node(catalog, args.id)
        else:
            result = plan_overhead(catalog, args.scope, args.game, args.factor)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except (CatalogError, OSError, ValueError, TypeError, RecursionError) as error:
        # No traceback, terminal commands, writes, or automatic recovery actions.
        print(json.dumps({"valid": False, "error": str(error), "execution": "none"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
