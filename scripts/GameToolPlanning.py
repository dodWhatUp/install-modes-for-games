"""Read-only goal plans and ownership/conflict graphs for Game Tools.

The compiler reuses registered support recipes, game-scoped workspaces, the
private instance registry, and existing UMM manifest inspection.  It creates no
job, proposal, download, stage, install, profile change, process, or game input.
"""
from __future__ import annotations

from copy import deepcopy

from game_mod_ops.safety import ModError, object_hash, require, slug
from game_mod_ops.recipes import validate_recipe
from game_mod_ops.managers import compare_installed
from game_mod_ops.definitions import validate_mode

VERSION = "0.1.0"
SCHEMA_VERSION = 1
GOALS = {
    "prepare-game",
    "review-mods",
    "inspect-installed",
    "compare-intended-installed",
    "review-keybinds",
}
_NODE_STATES = {"READY", "BLOCKED", "WAITING_LOCAL_SELECTION", "NOT_APPLICABLE"}


def _node(ident, kind, owner, status, summary, *, depends_on=(), reads=(), blockers=()):
    require(status in _NODE_STATES, "PLAN_SCHEMA", "Unknown plan-node state.")
    return {
        "id": ident,
        "kind": kind,
        "owner": owner,
        "status": status,
        "summary": summary,
        "depends_on": list(depends_on),
        "effects": {"read": list(reads), "write": []},
        "blockers": list(blockers),
    }


def _validate_dag(nodes):
    ids = [row["id"] for row in nodes]
    require(len(ids) == len(set(ids)), "PLAN_SCHEMA", "Plan node IDs must be unique.")
    known = set(ids)
    require(all(set(row["depends_on"]) <= known and row["id"] not in row["depends_on"] for row in nodes),
            "PLAN_SCHEMA", "Plan dependencies refer to unknown or self-owned nodes.")
    remaining = {row["id"]: set(row["depends_on"]) for row in nodes}
    visited = set()
    while remaining:
        ready = sorted(ident for ident, deps in remaining.items() if deps <= visited)
        require(bool(ready), "PLAN_CYCLE", "Goal plan contains a dependency cycle.")
        for ident in ready:
            visited.add(ident); remaining.pop(ident)


class PlanningService:
    def __init__(self, workspaces):
        self.workspaces = workspaces
        self.instances = workspaces.instances

    def _row(self, game_id):
        game_id = slug(game_id)
        row = next((item for item in self.workspaces.game_rows() if item["id"] == game_id), None)
        require(row is not None, "UNKNOWN_GAME", "Unknown game scope.")
        return row

    def _recipe(self, game_id):
        row = self.workspaces.catalog.recipes().get(slug(game_id))
        return None if row is None else row["recipe"]

    @staticmethod
    def _default_mode(recipe, mode):
        if mode is not None:
            return mode
        return "default" if "default" in recipe.get("presets", {}) else "real-time"

    def _selection(self, recipe, selected=None, mode=None):
        validate_recipe(recipe)
        mode = self._default_mode(recipe, mode)
        validate_mode(mode)
        by_id = {row["id"]: row for row in recipe["items"]}
        chosen_input = recipe.get("presets", {}).get(mode, []) if selected is None else selected
        require(type(chosen_input) is list and 0 < len(chosen_input) <= 100 and
                len(chosen_input) == len(set(chosen_input)) and all(type(item) is str for item in chosen_input),
                "INVALID_ARGUMENTS", "Choose a bounded distinct item list or a populated named preset.")
        chosen = set(); order = []

        def add(ident):
            require(ident in by_id, "UNKNOWN_ITEM", "Selected item is absent from the reviewed recipe.")
            if ident in chosen:
                return
            chosen.add(ident)
            for dependency in by_id[ident].get("requires", []):
                add(dependency)
            order.append(ident)

        for ident in chosen_input:
            add(ident)
        issues = []
        conflict_keys = set()
        for ident in order:
            item = by_id[ident]
            if mode in item.get("unsupported_modes", []):
                issues.append({
                    "code": "MODE_UNSUPPORTED", "severity": "blocker",
                    "owners": [ident], "message": "Selected item does not support this named mode.",
                })
            for other in item.get("conflicts", []):
                pair = tuple(sorted((ident, other)))
                if pair in conflict_keys:
                    continue
                conflict_keys.add(pair)
                active = other in chosen
                issues.append({
                    "code": "CHOICE_CONFLICT" if active else "DECLARED_ALTERNATIVE_CONFLICT",
                    "severity": "blocker" if active else "advisory",
                    "owners": list(pair),
                    "message": "Both declared alternatives are selected." if active else
                               "A selected item declares an unselected alternative conflict.",
                })
        return {
            "mode": mode,
            "selected": order,
            "items": [deepcopy(by_id[ident]) for ident in order],
            "issues": issues,
            "blocking": any(row["severity"] == "blocker" for row in issues),
        }

    def list_instances(self, game_id=None, limit=50):
        if game_id is not None:
            self._row(game_id)
        return self.instances.list_public(game_id, limit)

    def inspect_instance(self, instance_id, game_id=None):
        result = self.instances.inspect(instance_id)
        if game_id is not None:
            game_id = slug(game_id)
            require(result["instance"]["game_id"] == game_id,
                    "GAME_MISMATCH", "Registered instance belongs to another game scope.")
        return result

    def goal_plan(self, game_id, goal, *, instance_id=None, mode=None, selected=None):
        game_id = slug(game_id)
        require(goal in GOALS, "INVALID_ARGUMENTS", "Choose a supported read-only goal.")
        row = self._row(game_id)
        recipe = self._recipe(game_id)
        recipe_goal = goal in {"prepare-game", "review-mods", "compare-intended-installed"}
        if not recipe_goal:
            require(selected is None and mode is None, "INVALID_ARGUMENTS",
                    "This goal does not use a mod-recipe mode or item selection.")
        selection = self._selection(recipe, selected, mode) if recipe is not None and recipe_goal else None
        instance = self.instances.public(instance_id) if instance_id is not None else None
        if instance is not None:
            require(instance["game_id"] == game_id,
                    "GAME_MISMATCH", "Registered instance belongs to another game scope.")

        nodes = [_node(
            "scope", "scope", "GameToolGameWorkspaces", "READY",
            "Use one exact registered game scope and its current reviewed revisions.",
            reads=["game support and capability metadata"],
        )]
        blockers = []
        if recipe is None:
            recipe_state = "BLOCKED" if recipe_goal else "NOT_APPLICABLE"
            recipe_blockers = ["RECIPE_REQUIRED"] if recipe_goal else []
            blockers.extend(recipe_blockers)
            nodes.append(_node(
                "recipe", "recipe", "RecipeCatalog", recipe_state,
                "No reviewed mod recipe is registered; this goal does not require one."
                if not recipe_goal else "No reviewed mod recipe is registered for this goal.",
                depends_on=["scope"], blockers=recipe_blockers,
            ))
        else:
            nodes.append(_node(
                "recipe", "recipe", "RecipeCatalog", "READY" if recipe_goal else "NOT_APPLICABLE",
                "Read the immutable recipe and dependency/conflict declarations."
                if recipe_goal else "This goal reads installation metadata without a mod recipe.",
                depends_on=["scope"], reads=["reviewed recipe"] if recipe_goal else [],
            ))

        if selection is None:
            nodes.append(_node(
                "mod-plan", "preview", "GameToolAutomation", "NOT_APPLICABLE",
                "No mod-plan preview is available without a reviewed recipe.",
                depends_on=["recipe"],
            ))
        elif selection["blocking"]:
            codes = sorted({issue["code"] for issue in selection["issues"] if issue["severity"] == "blocker"})
            blockers.extend(codes)
            nodes.append(_node(
                "mod-plan", "preview", "GameToolAutomation", "BLOCKED",
                "Resolve declared mode or choice conflicts before creating an immutable plan.",
                depends_on=["recipe"], blockers=codes,
            ))
        else:
            nodes.append(_node(
                "mod-plan", "preview", "GameToolAutomation", "READY",
                "Preview the existing recipe through its current owner; no job is created.",
                depends_on=["recipe"], reads=["selected recipe subgraph"],
            ))

        needs_instance = goal in {"inspect-installed", "compare-intended-installed"}
        benefits_from_instance = goal == "prepare-game"
        if instance is None:
            state = "BLOCKED" if needs_instance else ("WAITING_LOCAL_SELECTION" if benefits_from_instance else "NOT_APPLICABLE")
            instance_blockers = ["INSTANCE_REQUIRED"] if needs_instance else []
            blockers.extend(instance_blockers)
            nodes.append(_node(
                "instance", "instance", "GameToolInstances", state,
                "A local operator must register one exact installation; AI cannot supply a path.",
                depends_on=["scope"], blockers=instance_blockers,
            ))
        else:
            nodes.append(_node(
                "instance", "instance", "GameToolInstances", "READY",
                "Use the existing opaque instance identity; its private path is not returned.",
                depends_on=["scope"], reads=["registered instance metadata"],
            ))

        inventory_state = "READY" if instance is not None else (
            "BLOCKED" if needs_instance else ("WAITING_LOCAL_SELECTION" if benefits_from_instance else "NOT_APPLICABLE")
        )
        nodes.append(_node(
            "inventory", "read", "UMMReadAdapter", inventory_state,
            "Read executable/loader markers and UMM Info.json manifests without loading DLLs.",
            depends_on=["instance"], reads=["registered game-folder metadata"] if instance else [],
            blockers=["INSTANCE_REQUIRED"] if needs_instance and instance is None else [],
        ))

        nodes.append(_node(
            "ownership", "graph", "GameToolPlanning",
            "READY" if recipe is not None and recipe_goal else "NOT_APPLICABLE",
            "Resolve declared manager, dependency, identity and alternative-conflict ownership."
            if recipe_goal else "This goal does not compile a recipe ownership graph.",
            depends_on=["recipe"],
            reads=["recipe ownership declarations"] if recipe is not None and recipe_goal else [],
        ))

        keybind_available = bool(row.get("keybind_pack_available"))
        keybind_needed = goal == "review-keybinds"
        keybind_state = "READY" if keybind_available else ("BLOCKED" if keybind_needed else "NOT_APPLICABLE")
        if keybind_needed and not keybind_available:
            blockers.append("KEYBIND_PACK_REQUIRED")
        nodes.append(_node(
            "keybinds", "read", "GameToolKeybindIntegration", keybind_state,
            "Inspect the separate keybind-pack owner without merging it into game-installation identity.",
            depends_on=["scope"], reads=["keybind pack and registered keybind instances"] if keybind_available else [],
            blockers=["KEYBIND_PACK_REQUIRED"] if keybind_needed and not keybind_available else [],
        ))

        comparison_needed = goal == "compare-intended-installed"
        comparison_ready = comparison_needed and instance is not None and recipe is not None and not selection["blocking"]
        nodes.append(_node(
            "comparison", "read", "game_mod_ops.managers.compare_installed",
            "READY" if comparison_ready else ("BLOCKED" if comparison_needed else "NOT_APPLICABLE"),
            "Compare intended mod identities with observed UMM manifests; runtime and enablement remain unknown.",
            depends_on=["inventory", "mod-plan"],
            reads=["observed UMM inventory", "selected plan"] if comparison_ready else [],
            blockers=[] if comparison_ready or not comparison_needed else
                     sorted(set(["INSTANCE_REQUIRED"] if instance is None else []) |
                            set(["RECIPE_REQUIRED"] if recipe is None else []) |
                            set(issue["code"] for issue in (selection or {}).get("issues", []) if issue["severity"] == "blocker")),
        ))
        _validate_dag(nodes)
        waiting = any(row["status"] == "WAITING_LOCAL_SELECTION" for row in nodes)
        plan_reads = ["reviewed support definitions"]
        if recipe is not None and recipe_goal:
            plan_reads.append("reviewed recipe")
        if instance is not None:
            plan_reads.append("registered instance metadata")
        body = {
            "schema_version": SCHEMA_VERSION,
            "kind": "game_tools_goal_plan",
            "goal": goal,
            "game_id": game_id,
            "instance_id": instance_id,
            "mode": selection["mode"] if selection else mode,
            "selected_items": selection["selected"] if selection else [],
            "status": "BLOCKED" if blockers else ("PARTIAL_READ_PLAN" if waiting else "READY_FOR_READS"),
            "nodes": nodes,
            "blockers": sorted(set(blockers)),
            "selection_issues": [] if selection is None else selection["issues"],
            "effects": {"read": plan_reads, "write": [], "network": False},
            "automatic_execution": False,
            "runtime_verified": False,
            "gameplay_verified": False,
        }
        plan_id = "gtplan:" + object_hash(body)[:32]
        plan = {**body, "plan_id": plan_id, "plan_revision": object_hash(body)}
        return plan

    def conflict_graph(self, game_id, *, instance_id=None, mode=None, selected=None):
        game_id = slug(game_id)
        row = self._row(game_id)
        recipe = self._recipe(game_id)
        require(recipe is not None, "RECIPE_REQUIRED",
                "A reviewed recipe is required for the ownership/conflict graph.")
        selection = self._selection(recipe, selected, mode)
        selected_ids = set(selection["selected"])
        by_id = {item["id"]: item for item in recipe["items"]}
        nodes = [
            {"id": "game:" + game_id, "kind": "game", "owner": "GameToolGameWorkspaces", "selected": True},
            {"id": "manager:" + recipe["manager_id"], "kind": "manager", "owner": recipe["manager_id"], "selected": True},
            {"id": "resource:mod-layout", "kind": "resource", "owner": recipe["manager_id"], "selected": True},
        ]
        edges = [
            {"from": "manager:" + recipe["manager_id"], "to": "resource:mod-layout", "kind": "owns", "active": True},
            {"from": "game:" + game_id, "to": "manager:" + recipe["manager_id"], "kind": "uses", "active": True},
        ]
        issues = deepcopy(selection["issues"])
        identities = {}
        for ident in selection["selected"]:
            item = by_id[ident]
            node_id = "item:" + ident
            nodes.append({"id": node_id, "kind": item["kind"], "owner": recipe["manager_id"], "selected": True})
            edges.append({"from": node_id, "to": "resource:mod-layout", "kind": "uses", "active": True})
            for dependency in item.get("requires", []):
                edges.append({"from": node_id, "to": "item:" + dependency, "kind": "requires", "active": True})
            identity = item.get("mod_id") or item.get("umm_id")
            if item["kind"] == "mod" and identity:
                identity_id = "identity:" + object_hash(identity.casefold())[:20]
                prior = identities.get(identity.casefold())
                if prior is not None and prior["item"] != ident:
                    issues.append({
                        "code": "OWNERSHIP_CONFLICT", "severity": "blocker",
                        "owners": [prior["item"], ident],
                        "message": "Two selected recipe items claim the same UMM manifest identity.",
                    })
                else:
                    identities[identity.casefold()] = {"node": identity_id, "item": ident, "identity": identity}
                    nodes.append({"id": identity_id, "kind": "manifest_identity", "owner": ident,
                                  "selected": True, "identity": identity})
                edges.append({"from": node_id, "to": identity_id, "kind": "owns", "active": True})
            elif item["kind"] == "mod":
                issues.append({
                    "code": "IDENTITY_NOT_CONFIGURED", "severity": "advisory",
                    "owners": [ident],
                    "message": "Recipe item has no exact UMM manifest identity, so installed matching is inconclusive.",
                })
        seen_conflicts = set()
        for item in recipe["items"]:
            if item["id"] not in selected_ids:
                continue
            for other in item.get("conflicts", []):
                pair = tuple(sorted((item["id"], other)))
                if pair in seen_conflicts:
                    continue
                seen_conflicts.add(pair)
                for alternative in pair:
                    node_id = "item:" + alternative
                    if not any(node["id"] == node_id for node in nodes):
                        nodes.append({
                            "id": node_id, "kind": by_id[alternative]["kind"],
                            "owner": recipe["manager_id"], "selected": False,
                        })
                edges.append({
                    "from": "item:" + pair[0], "to": "item:" + pair[1],
                    "kind": "conflicts", "active": pair[0] in selected_ids and pair[1] in selected_ids,
                })

        observed = None; comparison = None
        if instance_id is not None:
            inspected = self.instances.inspect(instance_id)
            require(inspected["instance"]["game_id"] == game_id,
                    "GAME_MISMATCH", "Registered instance belongs to another game scope.")
            observed = inspected["inventory"]
            groups = {}
            observed_rows = [mod for mod in observed.get("mods", []) if mod.get("id")]
            for mod in observed_rows:
                groups.setdefault(mod["id"].casefold(), []).append(mod)
            for mod in observed_rows:
                identity = mod["id"]
                observed_id = "observed:" + object_hash([identity.casefold(), mod.get("folder")])[:20]
                nodes.append({
                    "id": observed_id, "kind": "observed_manifest", "owner": "UMMReadAdapter",
                    "selected": False, "identity": identity, "version": mod.get("version"),
                })
                match = identities.get(identity.casefold())
                if match:
                    edges.append({"from": observed_id, "to": match["node"], "kind": "observes", "active": True})
                for dependency in mod.get("required_ids", []):
                    dependency_key = dependency.casefold()
                    if dependency_key not in groups and dependency_key not in identities:
                        issues.append({
                            "code": "OBSERVED_DEPENDENCY_UNRESOLVED", "severity": "advisory",
                            "owners": [identity, dependency],
                            "message": "Observed manifest declares a dependency not resolved by the selected plan graph.",
                        })
            for identity, members in groups.items():
                if len(members) > 1:
                    issues.append({
                        "code": "AMBIGUOUS_DUPLICATE", "severity": "blocker",
                        "owners": [member.get("id") for member in members],
                        "message": "Multiple observed manifests claim the same UMM identity.",
                    })
            for warning in observed.get("warnings", []):
                issues.append({
                    "code": "INVENTORY_WARNING", "severity": "advisory", "owners": ["UMMReadAdapter"],
                    "message": str(warning)[:512],
                })
            if not selection["blocking"]:
                service = self.workspaces.service(game_id)
                operation_plan = service.preview_plan(selection["selected"], selection["mode"])
                comparison = compare_installed(operation_plan, observed)

        if row.get("keybind_pack_available"):
            nodes.append({"id": "owner:keybind-service", "kind": "separate_owner",
                          "owner": "GameToolKeybindIntegration", "selected": False})
            nodes.append({"id": "resource:keybind-config", "kind": "resource",
                          "owner": "GameToolKeybindIntegration", "selected": False})
            edges.append({"from": "owner:keybind-service", "to": "resource:keybind-config",
                          "kind": "owns", "active": True})

        blocking = [item for item in issues if item["severity"] == "blocker"]
        graph = {
            "schema_version": SCHEMA_VERSION,
            "kind": "game_tools_ownership_conflict_graph",
            "game_id": game_id,
            "instance_id": instance_id,
            "mode": selection["mode"],
            "selected_items": selection["selected"],
            "status": "BLOCKING_CONFLICTS" if blocking else ("REVIEW_REQUIRED" if issues else "CLEAR"),
            "nodes": nodes,
            "edges": edges,
            "issues": issues,
            "comparison": comparison,
            "inventory_complete": None if observed is None else observed.get("complete") is True,
            "semantic_boundary": "declared recipe ownership and UMM manifest evidence; no runtime/load-order inference",
            "effects": {
                "read": ["reviewed recipe"] + (["registered UMM folder metadata"] if instance_id else []),
                "write": [], "network": False,
            },
            "paths_included": False,
            "runtime_verified": False,
            "automatic_resolution": False,
        }
        graph["graph_revision"] = object_hash(graph)
        return graph
