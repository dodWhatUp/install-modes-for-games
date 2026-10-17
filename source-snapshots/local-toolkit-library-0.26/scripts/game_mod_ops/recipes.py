"""Portable data-only game recipes. Installing GPU/device drivers is out of scope."""
from __future__ import annotations
import copy
import re
from pathlib import Path
from .safety import require, read_json, slug, object_hash, safe_relative
from .definitions import validate_definition, validate_mode, archive_contract

SUPPORTED_MANAGERS = {"unity-mod-manager", "vortex", "mod-organizer-2", "rhi", "manual", "smapi", "bepinex"}


def validate_recipe(recipe: dict) -> dict:
    require(isinstance(recipe, dict) and recipe.get("schema_version") == 1, "SCHEMA", "Expected mod-workflow recipe schema 1.")
    require(recipe.get("kind") == "game_mod_recipe", "SCHEMA", "This is not a mod-workflow recipe.")
    slug(recipe.get("game_id", ""))
    definition=recipe.get("game_definition")
    if definition is not None:
        validate_definition(definition)
        require(definition['game_id']==recipe['game_id'] and definition['manager_id']==recipe.get('manager_id'),
                'GAME_MISMATCH','Recipe and game definition do not match.')
    else:
        require(recipe.get("manager_id") in SUPPORTED_MANAGERS, "MANAGER_UNSUPPORTED", "An unfamiliar manager needs a game definition with a supported adapter.")
    slug(recipe.get('manager_id',''))
    items = recipe.get("items")
    require(isinstance(items, list) and 0 < len(items) <= 100, "SCHEMA", "A recipe requires 1–100 items.")
    def check_data(value):
        if isinstance(value, dict):
            require(not ({str(k).lower() for k in value} & {"command", "script", "shell", "password", "api_key", "apikey", "cookie", "token"}),
                    "EXECUTABLE_RECIPE", "Recipe data must not carry commands or secrets.")
            for child in value.values(): check_data(child)
        elif isinstance(value, list):
            for child in value: check_data(child)
    check_data(recipe)
    if recipe.get("game_exe"):
        safe_relative(recipe["game_exe"])
    ids = set()
    for item in items:
        require(isinstance(item, dict), "SCHEMA", "Each item must be an object.")
        ident = slug(item.get("id", ""))
        require(ident not in ids, "DUPLICATE_ID", "Duplicate item ID.")
        ids.add(ident)
        require(item.get("kind") in {"mod", "manager"}, "SCHEMA", "Only mod and manager items are supported.")
        require(isinstance(item.get("name"), str) and len(item["name"]) <= 200, "SCHEMA", "Item needs a short name.")
        require(type(item.get("max_download_bytes")) is int and 0 < item["max_download_bytes"] <= 256 * 1024 * 1024,
                "SCHEMA", "Item needs a bounded download size.")
        require(item.get("sha256") is None or bool(re.fullmatch(r"[0-9a-f]{64}", item["sha256"])), "SCHEMA", "Invalid SHA-256.")
        src = item.get("source", {})
        require(src.get("kind") in {"github_release", "author_https", "nexus", "manual"}, "PROVIDER_UNSUPPORTED", "No source adapter is implemented for this recipe.")
        require(isinstance(item.get("download_page"), str) and item["download_page"].startswith("https://"),
                "SCHEMA", "An official download page is required.")
        if src["kind"] == "github_release":
            require(all(isinstance(src.get(k), str) and src[k] for k in ("repository", "tag", "asset")), "SCHEMA", "GitHub requires repository, exact tag and asset name.")
            slug(src["asset"])
        if src["kind"] == "nexus":
            slug(src.get("game", ""))
            require(type(src.get("mod_id")) is int and src["mod_id"] > 0, "SCHEMA", "Nexus needs a positive mod ID.")
        archive_contract(item,recipe['manager_id'],definition)
        if item.get('expected_version') is not None:
            require(type(item['expected_version']) is str and 0<len(item['expected_version'])<=80,
                    'SCHEMA','Invalid expected manifest version.')
        for key in ('requires','conflicts','unsupported_modes'):
            require(type(item.get(key,[])) is list and all(type(v) is str for v in item.get(key,[])),
                    'SCHEMA','Dependency, conflict and mode lists must contain strings.')
        require(not any(k in item for k in ("command", "script", "shell", "password", "api_key", "cookie")),
                "EXECUTABLE_RECIPE", "Recipes may not contain commands or credentials.")
    for item in items:
        for dep in item.get("requires", []):
            require(dep in ids and dep != item["id"], "DEPENDENCY", "Invalid dependency.")
        for conflict in item.get("conflicts", []):
            require(conflict in ids, "SCHEMA", "Unknown conflict ID.")
    presets=recipe.get('presets',{})
    require(type(presets) is dict and len(presets)<=24,'SCHEMA','Use a bounded named preset map.')
    for mode,selected in presets.items():
        validate_mode(mode)
        require(type(selected) is list and len(selected)<=100 and all(type(i) is str and i in ids for i in selected),
                'SCHEMA','A preset names an unknown item.')
    # Verify the entire dependency graph, including unselected items.
    visited, visiting = set(), set()
    by_id = {i["id"]: i for i in items}
    def walk(ident):
        require(ident not in visiting, "DEPENDENCY_CYCLE", "The recipe contains a dependency cycle.")
        if ident in visited:
            return
        visiting.add(ident)
        for dep in by_id[ident].get("requires", []):
            walk(dep)
        visiting.remove(ident)
        visited.add(ident)
    for ident in ids:
        walk(ident)
    return recipe


def load_recipe(path: Path) -> dict:
    return validate_recipe(read_json(path))


def plan(recipe: dict, selected: list[str] | None = None, mode: str = "real-time", file_pins: dict | None = None) -> dict:
    validate_recipe(recipe)
    validate_mode(mode)
    by_id = {i["id"]: i for i in recipe["items"]}
    selected = selected if selected is not None else recipe.get("presets", {}).get(mode, [])
    require(isinstance(selected, list) and bool(selected), "EMPTY_PLAN", "Choose a named preset or at least one item.")
    chosen, order = set(), []
    def add(ident):
        require(ident in by_id, "UNKNOWN_ITEM", "Selected item is absent from the recipe.")
        if ident in chosen:
            return
        chosen.add(ident)
        for dep in by_id[ident].get("requires", []):
            add(dep)
        order.append(ident)
    for ident in selected:
        add(ident)
    warnings = list(recipe.get("warnings", []))
    for ident in chosen:
        item = by_id[ident]
        require(not (set(item.get("conflicts", [])) & chosen), "CHOICE_CONFLICT", "Choose only one of the conflicting workflow items.")
        require(mode not in item.get("unsupported_modes", []), "MODE_UNSUPPORTED", "A selected item does not support this play mode.")
        warnings.extend(item.get("warnings", []))
    items = [copy.deepcopy(by_id[i]) for i in order]
    require(not (set(file_pins or {}) - set(order)), "UNKNOWN_ITEM", "A file pin names an unselected item.")
    for item in items:
        pin = (file_pins or {}).get(item["id"])
        if pin is not None:
            require(item["source"]["kind"] == "nexus" and type(pin) is int and pin > 0,
                    "FILE_PIN_REQUIRED", "File pins must refer to a Nexus item and an exact positive file ID.")
            item["source"]["file_id"] = pin
            item["source"]["pin_evidence"] = "caller_selected; preserve originating file metadata separately"
    p = {"schema_version": 1, "kind": "mod_operation_plan", "game_id": recipe["game_id"],
         "manager_id": recipe["manager_id"], "recipe_sha256": object_hash(recipe), "mode": mode,
         "game_exe": recipe.get("game_exe"), "items": items, "warnings": warnings,
         "network_authorized": False, "installation_authorized": False,
         "download_bytes_upper_bound": sum(i["max_download_bytes"] for i in items),
         "policy": "explicit actions; no install, activation, game launch, benchmark, capture, or driver update from planning"}
    if recipe.get('game_definition') is not None:
        p['game_definition']=copy.deepcopy(recipe['game_definition'])
    if recipe.get('support_revision') is not None:
        p['support_revision']=recipe['support_revision']
    p["plan_sha256"] = object_hash(p)
    return p


def validate_plan(p: dict) -> dict:
    require(isinstance(p, dict) and p.get("kind") == "mod_operation_plan", "SCHEMA", "Not a workflow plan.")
    body = {k: v for k, v in p.items() if k != "plan_sha256"}
    require(p.get("plan_sha256") == object_hash(body), "PLAN_CHANGED", "Plan digest does not match. Create a new reviewed plan.")
    require(p.get("schema_version") == 1, "SCHEMA", "Invalid plan schema.")
    validate_mode(p.get('mode'))
    items = copy.deepcopy(p["items"])
    ids = {item["id"] for item in items}
    for item in items:
        require(not (set(item.get("conflicts", [])) & ids), "CHOICE_CONFLICT", "Plan selects conflicting items.")
        require(p["mode"] not in item.get("unsupported_modes", []), "MODE_UNSUPPORTED", "Plan mode is not supported by this item.")
        # Conflicts with an unselected catalog item remain in the immutable plan;
        # they do not become phantom dependencies in its selected subgraph.
        item["conflicts"] = []
    recipe = {"schema_version": 1, "kind": "game_mod_recipe", "game_id": p["game_id"],
              "manager_id": p["manager_id"], "game_exe": p.get("game_exe"), "items": items}
    if p.get('game_definition') is not None:recipe['game_definition']=p['game_definition']
    validate_recipe(recipe)
    visited = set()
    for item in items:
        require(set(item.get("requires", [])) <= visited, "DEPENDENCY_ORDER", "Plan dependencies are not in installation order.")
        visited.add(item["id"])
    return p
