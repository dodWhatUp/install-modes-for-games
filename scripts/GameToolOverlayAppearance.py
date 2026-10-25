"""Scoped display styles and snapshot presets; never writes native/game input.

Pixels are prepared off the polling thread, then registry preferences and image
references are committed together through the existing optimistic Store owner.
"""
from __future__ import annotations
import copy
from pathlib import Path
import tempfile
import uuid
import GameToolOverlay as api

VERSION = "0.1.0"
RENDER_FIELDS = "size_mode size_value opacity monitor anchor offset_x offset_y".split()
STYLE_FIELDS = "view action_text_percent key_text_percent background".split() + RENDER_FIELDS


def default_style():
    return dict(view="Combined", action_text_percent=100, key_text_percent=100,
                background="opaque", size_mode="Screen width %", size_value=35,
                opacity=100, monitor=1, anchor="Center", offset_x=0, offset_y=0)


def validate_style(value):
    api.fields(value, " ".join(STYLE_FIELDS))
    api.require(value["view"] in api.VIEWS, "Choose a display layout")
    api.require(value["background"] in {"opaque", "buttons"}, "Choose a background")
    for name in ("action_text_percent", "key_text_percent"):
        api.require(type(value[name]) is int and 50 <= value[name] <= 200,
                    "Action and key text sizes must each be 50–200%")
    api.appearance(rendering(value))
    return value


def rendering(style):
    return {k: style[k] for k in RENDER_FIELDS}


def validate_policy(value, game_ids):
    api.fields(value, "schema_version global games presets")
    api.require(type(value["schema_version"]) is int and value["schema_version"] == 1, "Appearance schema")
    validate_style(value["global"])
    api.require(type(value["games"]) is dict and set(value["games"]) <= set(game_ids), "Appearance game scope")
    for style in value["games"].values(): validate_style(style)
    api.require(type(value["presets"]) is dict and len(value["presets"]) <= 64, "Up to 64 appearance presets")
    names = set()
    for pid, preset in value["presets"].items():
        api.token(pid); api.fields(preset, "name scope style")
        api.label(preset["name"])
        api.require(not any(ord(c) < 32 for c in preset["name"]), "Preset names must be one line")
        api.require(preset["name"] == preset["name"].strip(), "Trim the preset name")
        api.require(preset["scope"] is None or (type(preset["scope"]) is str and preset["scope"] in game_ids), "Preset game scope")
        key = (preset["scope"], preset["name"].casefold())
        api.require(key not in names, "Preset name already exists in this scope")
        names.add(key); validate_style(preset["style"])
    return value


def policy(value, documents=None):
    """Legacy stores acquire explicit overrides so existing looks are retained."""
    if "appearance" in value["preferences"]:
        return copy.deepcopy(value["preferences"]["appearance"])
    documents = documents or {}
    result = {"schema_version": 1, "global": default_style(), "games": {}, "presets": {}}
    for game in value["manifest"]["games"]:
        gid = game["id"]; style = default_style()
        groups = [g for g in value["manifest"]["groups"] if g["game_id"] == gid]
        associations = sorted((a for a in value["manifest"]["associations"] if a["game_id"] == gid), key=lambda a: (-a["priority"], a["id"]))
        preferred = value["preferences"]["overrides"].get(gid) or (associations[0]["default_group"] if associations else None)
        group = next((g for g in groups if g["id"] == preferred), groups[0] if groups else None)
        if group: style.update(group["rendering"])
        style["view"] = value["preferences"]["selections"].get(gid, {}).get("view", "Combined")
        if gid in documents: style["background"] = documents[gid]["presentation"]["background"]
        result["games"][gid] = style
    return result


def effective(policy_value, game):
    return copy.deepcopy(policy_value["games"].get(game, policy_value["global"]))


def set_scope(policy_value, scope, style, inherit=False, all_games=False):
    result = copy.deepcopy(policy_value); validate_style(style)
    if scope is None:
        api.require(not inherit, "Global settings cannot inherit")
        result["global"] = copy.deepcopy(style)
        if all_games: result["games"].clear()
    elif inherit:
        result["games"].pop(scope, None)
    else:
        result["games"][scope] = copy.deepcopy(style)
    return result


def save_preset(policy_value, scope, name, style, preset_id=None):
    result = copy.deepcopy(policy_value)
    if preset_id is not None:
        api.require(preset_id in result["presets"] and result["presets"][preset_id]["scope"] == scope,
                    "Select a preset in this scope before replacing it")
    pid = preset_id or "look-" + uuid.uuid4().hex
    result["presets"][pid] = {"name": name.strip(), "scope": scope, "style": copy.deepcopy(style)}
    return result, pid


def transfer_preset(policy_value, preset_id, scope, name, move=False):
    api.require(preset_id in policy_value["presets"], "Select a saved preset")
    result = copy.deepcopy(policy_value)
    pid = preset_id if move else "look-" + uuid.uuid4().hex
    result["presets"][pid] = dict(name=name.strip(), scope=scope,
                                 style=copy.deepcopy(result["presets"][preset_id]["style"]))
    return result, pid


class Service:
    def __init__(self, directory):
        self.store = api.Store(directory)

    def documents(self):
        from GameToolKeymapBuilder import SourceLibrary
        return SourceLibrary(self.store.directory).documents()

    def load(self):
        value, fingerprint = self.store.load()
        return value, fingerprint, policy(value, self.documents())

    def save_library(self, candidate, expected):
        value, current = self.store.load()
        api.require(current == expected, "Overlay settings changed; reopen Appearance before saving")
        old = policy(value, self.documents())
        api.require(candidate["global"] == old["global"] and candidate["games"] == old["games"],
                    "Preset library changes cannot apply a draft appearance")
        validate_policy(candidate, {g["id"] for g in value["manifest"]["games"]})
        value["preferences"]["appearance"] = copy.deepcopy(candidate)
        return self.store.write(value, expected)

    def apply(self, candidate, expected, progress=lambda _: None, cancelled=lambda: False):
        """Render supported current source families; preserve archived revisions.

        All four views are prepared. Switching a layer or view still selects a
        prebuilt image, with no font/layout work on the input/display path.
        """
        import GameToolKeymapDocument as maps
        from GameToolKeymapBuilder import package
        value, current = self.store.load()
        api.require(current == expected, "Overlay settings changed; reopen Appearance before applying")
        documents = self.documents(); old = policy(value, documents)
        indexed = api.validate_store(value)
        validate_policy(candidate, indexed["games"])
        changed = {g for g in indexed["games"] if effective(old, g) != effective(candidate, g)}
        selected_groups = {}
        for game in changed:
            groups = [g for g in indexed["groups"].values() if g["game_id"] == game]
            doc = documents.get(game)
            api.require(doc is not None, "Import an editable map before styling " + indexed["games"][game]["label"])
            # An archived native family is retained byte-for-byte, never rebuilt
            # from a different family's current source.
            groups = [g for g in groups if g["keymap_id"] == doc["keymap_id"]]
            api.require(bool(groups), "No registered group matches this editable map's native layout")
            active = value["preferences"]["overrides"].get(game)
            if active: api.require(any(g["id"] == active for g in groups), "Select the current editable layout before changing its appearance")
            package([doc], [indexed["keymaps"][doc["keymap_id"]]])
            owned_assets = {aid for group in groups for aid in group["asset_ids"]}
            api.require(not any(g["game_id"] != game and owned_assets.intersection(g["asset_ids"]) for g in indexed["groups"].values()),
                        "An image is shared between games; publish an independent editable map before styling it")
            selected_groups[game] = groups
        sources = {game: maps.fingerprint(documents[game]) for game in changed}
        preferences = copy.deepcopy(value["preferences"])
        preferences["appearance"] = copy.deepcopy(candidate)
        manifest = api.empty_store()["manifest"]
        manifest["games"] = copy.deepcopy(value["manifest"]["games"])
        manifest["keymaps"] = copy.deepcopy(value["manifest"]["keymaps"])
        truncated = {}; rendered = {}; skipped = []; count = 0
        total = sum(len({aid for g in selected_groups[game] for aid in g["asset_ids"]}) for game in changed)
        with tempfile.TemporaryDirectory(prefix="appearance-", dir=self.store.directory) as folder:
            stage = Path(folder)
            for game in sorted(changed):
                style = effective(candidate, game); doc = copy.deepcopy(documents[game])
                doc["presentation"]["background"] = style["background"]
                mapping_index = {(m["layer"], m["context"]): m for m in doc["maps"]}
                for group in selected_groups[game]:
                    new_group = copy.deepcopy(group); new_group["rendering"] = rendering(style)
                    manifest["groups"].append(new_group)
                    for aid in group["asset_ids"]:
                        if aid in rendered: continue
                        api.require(not cancelled(), "Appearance apply cancelled; previous appearance kept")
                        asset = copy.deepcopy(indexed["assets"][aid])
                        mapping = mapping_index.get((asset["layer"], asset["context"]))
                        api.require(mapping is not None, "Editable source lacks an exact layer/context; keep the previous appearance")
                        target = stage / (aid + ".png")
                        truncated[aid] = maps.render(doc, mapping, target, asset["view"], style)
                        asset.update(path=target.name, sha256=api.sha(target.read_bytes()))
                        manifest["assets"].append(asset); rendered[aid] = True
                        count += 1; progress(f"Preparing appearance {count}/{total}…")
                sel = preferences["selections"].get(game)
                if sel: sel["view"] = style["view"]
                else:
                    first = doc["maps"][0]
                    preferences["selections"][game] = dict(layer=first["layer"], context=first["context"], view=style["view"])
                skipped.extend(g["id"] for g in indexed["groups"].values() if g["game_id"] == game and g["keymap_id"] != doc["keymap_id"])
            api.require(not cancelled(), "Appearance apply cancelled; previous appearance kept")
            fresh = self.documents()
            api.require(all(game in fresh and maps.fingerprint(fresh[game]) == fingerprint for game, fingerprint in sources.items()),
                        "Map source changed while preparing appearance; reopen before applying")
            source = stage / "manifest.json"; source.write_bytes(api.encode(manifest))
            receipt = self.store.import_manifest(source, expected, conflict="replace", preferences=preferences)
        receipt.update(rendered_images=count, changed_games=sorted(changed),
                       truncated_positions={k: v for k, v in truncated.items() if v}, archived_groups_preserved=skipped)
        return receipt


def open_editor(panel):
    from GameToolOverlayAppearanceUI import Editor
    return Editor(panel)
