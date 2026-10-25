"""Portable JSON snapshots of appearances; imports never activate a style."""
from __future__ import annotations
import copy
import GameToolOverlay as api
import GameToolOverlayAppearance as looks

VERSION = "0.1.0"
ORIGINAL = "keep-source-scopes"


def validate(value):
    api.fields(value, "schema_version kind games presets")
    api.require(type(value["schema_version"]) is int and value["schema_version"] == 1 and
                value["kind"] == "overlay_appearance_package", "Unsupported appearance JSON package")
    api.require(type(value["games"]) is list and len(value["games"]) <= 512, "Appearance game limit")
    games = set()
    for game in value["games"]:
        api.fields(game, "id label"); api.token(game["id"]); api.label(game["label"])
        api.require(game["id"] not in games, "Duplicate appearance game"); games.add(game["id"])
    api.require(type(value["presets"]) is list and len(value["presets"]) <= 128, "Appearance preset count limit")
    ids, names = set(), set()
    for row in value["presets"]:
        api.fields(row, "id name scope style")
        api.token(row["id"]); api.label(row["name"])
        api.require(row["id"] not in ids, "Duplicate appearance preset ID"); ids.add(row["id"])
        api.require(row["scope"] is None or (type(row["scope"]) is str and row["scope"] in games), "Appearance scope missing from package")
        api.require(row["name"] == row["name"].strip() and not any(ord(c) < 32 for c in row["name"]), "Invalid preset name")
        pair = (row["scope"], row["name"].casefold())
        api.require(pair not in names, "Duplicate preset name in scope"); names.add(pair)
        try: looks.validate_style(row["style"])
        except (TypeError, KeyError) as error: raise api.OverlayError("Invalid appearance values") from error
    return value


def read(path):
    return validate(api.decode(api.read(path)))


def export_package(policy, games, scope="all", game=None, preset=None, include_current=True):
    """Only saved values are exported, with active values as optional snapshots."""
    labels = {g["id"]: g["label"] for g in games}
    looks.validate_policy(policy, labels)
    api.require(scope in {"all", "global", "game", "preset"}, "Choose an appearance export scope")
    if scope == "game": api.require(game in labels, "Choose a game to export")
    if scope == "preset": api.require(preset in policy["presets"], "Choose a saved preset")
    def selected(row):
        return scope == "all" or (scope == "global" and row["scope"] is None) or (scope == "game" and row["scope"] == game)
    rows = [{"id": pid, **copy.deepcopy(row)} for pid, row in sorted(policy["presets"].items())
            if (pid == preset if scope == "preset" else selected(row))]
    if include_current and scope != "preset":
        scopes = [None, *sorted(labels)] if scope == "all" else [None] if scope == "global" else [game]
        for current in scopes:
            name = "Current global defaults" if current is None else "Current appearance"
            names = {r["name"].casefold() for r in rows if r["scope"] == current}
            root = name; n = 2
            while name.casefold() in names: name = root + f" ({n})"; n += 1
            style = policy["global"] if current is None else looks.effective(policy, current)
            pid = "snapshot-" + api.sha(api.encode({"scope": current, "style": style}))[:32]
            if any(r["id"] == pid and r["scope"] == current and r["style"] == style for r in rows):
                continue  # Re-exporting an imported snapshot stays idempotent.
            while any(r["id"] == pid for r in rows):
                pid = "snapshot-" + api.sha(api.encode({"id": pid, "scope": current, "style": style}))[:32]
            rows.append(dict(id=pid, name=name, scope=current, style=copy.deepcopy(style)))
    referenced = {r["scope"] for r in rows if r["scope"] is not None}
    return validate(dict(schema_version=1, kind="overlay_appearance_package",
                         games=[dict(id=gid, label=labels[gid]) for gid in sorted(referenced)], presets=rows))


def import_plan(package, policy, game_ids, target=ORIGINAL, conflict="keep", selected=None):
    validate(package); looks.validate_policy(policy, game_ids)
    api.require(conflict in {"keep", "copy", "replace"}, "Choose an import conflict policy")
    api.require(target == ORIGINAL or target is None or (type(target) is str and target in game_ids), "Choose a destination scope")
    if selected is not None:
        api.require(type(selected) is list and len(selected) == len(set(selected)) and
                    set(selected) <= {r["id"] for r in package["presets"]}, "Select known appearance records")
    candidate = copy.deepcopy(policy); rows = []
    for row in package["presets"]:
        if selected is not None and row["id"] not in selected: continue
        scope = row["scope"] if target == ORIGINAL else target
        api.require(scope is None or scope in game_ids, "Destination lacks a game in this file; choose Global or an existing game scope")
        match = next((pid for pid, p in candidate["presets"].items()
                      if p["scope"] == scope and p["name"].casefold() == row["name"].casefold()), None)
        name = row["name"]; action = "Add"
        if match and conflict == "keep":
            rows.append(dict(id=match, name=name, scope=scope, action="Keep existing")); continue
        if match and conflict == "replace":
            pid = match; action = "Replace"
        else:
            pid = row["id"]
            if pid in candidate["presets"]:
                import uuid
                pid = "look-" + uuid.uuid4().hex
            if match:
                names = {p["name"].casefold() for p in candidate["presets"].values() if p["scope"] == scope}
                root = name[:215]; n = 2
                while name.casefold() in names: name = root + f" (imported {n})"; n += 1
                action = "Add renamed copy"
        candidate["presets"][pid] = dict(name=name, scope=scope, style=copy.deepcopy(row["style"]))
        rows.append(dict(id=pid, name=name, scope=scope, action=action))
    looks.validate_policy(candidate, game_ids)
    return candidate, rows
