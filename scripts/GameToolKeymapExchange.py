"""Scoped keymap packages and versioned global templates. Data only."""
from __future__ import annotations
import copy
import os
from pathlib import Path
import tempfile
import uuid
import GameToolOverlay as api
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder

VERSION = "0.1.0"


def export_keymaps(documents, keymaps, scope="all", game=None, map_index=0):
    api.require(scope in {"all", "game", "map"}, "Choose all games, one game or one map")
    api.require(bool(documents), "No editable keymaps to export")
    if scope != "all": api.require(game in documents, "Choose a game to export")
    chosen = copy.deepcopy(list(documents.values()) if scope == "all" else [documents[game]])
    if scope == "map":
        api.require(type(map_index) is int and 0 <= map_index < len(chosen[0]["maps"]), "Choose a layer/context map")
        chosen[0]["maps"] = [chosen[0]["maps"][map_index]]
    needed = sorted({d["keymap_id"] for d in chosen})
    api.require(all(k in keymaps for k in needed), "Missing native source contract; export refused")
    return builder.package(chosen, [keymaps[k] for k in needed])


def validate_templates(value):
    api.fields(value, "schema_version kind presets")
    api.require(type(value["schema_version"]) is int and value["schema_version"] == 1 and
                value["kind"] == "global_keymap_package", "Unsupported global keymap package")
    api.require(type(value["presets"]) is list and len(value["presets"]) <= 16, "Up to 16 global keymap presets")
    ids, names, contracts = set(), set(), {}
    for preset in value["presets"]:
        api.fields(preset, "id name document keymap")
        api.token(preset["id"]); api.label(preset["name"])
        maps.text(preset["name"], 100)
        api.require(preset["name"] == preset["name"].strip() and not any(ord(c) < 32 for c in preset["name"]), "Invalid global preset name")
        api.require(preset["id"] not in ids and preset["name"].casefold() not in names, "Duplicate global keymap preset")
        ids.add(preset["id"]); names.add(preset["name"].casefold())
        builder.package([preset["document"]], [preset["keymap"]])
        kid = preset["keymap"]["id"]
        api.require(kid not in contracts or contracts[kid] == preset["keymap"], "Global presets contain a native contract collision")
        contracts[kid] = preset["keymap"]
        api.require(preset["document"]["game_id"] == preset["id"], "Global preset identity mismatch")
    api.require(len(api.encode(value)) <= api.MAX_JSON, "Global presets exceed 1 MiB; export fewer presets")
    return value


def make_template(document, keymap, name, keep_actions=False):
    builder.package([document], [keymap])
    pid = "global-map-" + uuid.uuid4().hex
    doc = copy.deepcopy(document) if keep_actions else builder.new_game(document, name, pid)
    doc.update(id="map-" + pid, game_id=pid, title=name.strip())
    preset = dict(id=pid, name=name.strip(), document=doc, keymap=copy.deepcopy(keymap))
    validate_templates(dict(schema_version=1, kind="global_keymap_package", presets=[preset]))
    return preset


def new_game(preset, title, game_id=None):
    validate_templates(dict(schema_version=1, kind="global_keymap_package", presets=[preset]))
    # Keep the labels the user chose to save in this template. Creating a game
    # remains an in-memory draft; native validation/publication owners stay intact.
    doc = copy.deepcopy(preset["document"])
    gid = game_id or "game-" + uuid.uuid4().hex
    api.token(gid); maps.text(title, 100); api.require(bool(title.strip()), "Enter a game name")
    doc.update(game_id=gid, id=builder.stable("map-", gid), title=title.strip())
    return maps.validate(doc), copy.deepcopy(preset["keymap"])


class Templates:
    def __init__(self, directory):
        self.directory = api.no_links(directory)
        self.path = self.directory / "keymap-global-presets.json"

    def load(self):
        if not self.path.exists(): return dict(schema_version=1, kind="global_keymap_package", presets=[]), "absent"
        raw = api.read(self.path); return validate_templates(api.decode(raw)), api.sha(raw)

    def write(self, value, expected):
        validate_templates(value); self.directory.mkdir(parents=True, exist_ok=True)
        lock = api.no_links(self.directory / "keymap-global-presets.lock")
        try: fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error: raise api.OverlayError("Global presets busy; inspect the lock owner before retrying") from error
        temp = None
        try:
            os.close(fd); _, current = self.load()
            api.require(current == expected, "Global keymap presets changed; reload before saving")
            raw = api.encode(value)
            if self.path.exists():
                backup = api.no_links(self.directory / ("keymap-global-presets-before-" + current + ".json"))
                if not backup.exists():
                    with backup.open("xb") as out: out.write(api.read(self.path)); out.flush(); os.fsync(out.fileno())
            fd, temp = tempfile.mkstemp(prefix="keymap-presets-", suffix=".tmp", dir=self.directory)
            with os.fdopen(fd, "wb") as out: out.write(raw); out.flush(); os.fsync(out.fileno())
            api.require(self.load()[1] == expected, "Concurrent global preset drift")
            api.no_links(self.path); os.replace(temp, self.path); temp = None
            api.require(api.read(self.path) == raw, "Global preset readback mismatch")
            return api.sha(raw)
        finally:
            if temp and Path(temp).exists(): Path(temp).unlink()
            lock.unlink()

    def add(self, preset, expected):
        value, current = self.load(); api.require(current == expected, "Global presets changed; reload")
        value["presets"].append(copy.deepcopy(preset)); return self.write(value, expected)

    def import_plan(self, incoming, conflict="keep"):
        validate_templates(incoming); api.require(conflict in {"keep", "copy", "replace"}, "Choose a conflict policy")
        value, expected = self.load(); rows = []
        for preset in incoming["presets"]:
            match = next((p for p in value["presets"] if p["name"].casefold() == preset["name"].casefold()), None)
            row = copy.deepcopy(preset); action = "Add"
            if match and conflict == "keep": rows.append((preset["name"], "Keep existing")); continue
            if match and conflict == "replace":
                row["id"] = match["id"]; row["document"]["game_id"] = row["id"]; row["document"]["id"] = "map-" + row["id"]
                value["presets"] = [p for p in value["presets"] if p["id"] != match["id"]]; action = "Replace"
            else:
                if match:
                    names = {p["name"].casefold() for p in value["presets"]}; root = row["name"][:75]; n = 2
                    while row["name"].casefold() in names: row["name"] = root + f" (imported {n})"; n += 1
                    action = "Add renamed copy"
                if any(p["id"] == row["id"] for p in value["presets"]):
                    row["id"] = "global-map-" + uuid.uuid4().hex
                    row["document"].update(id="map-" + row["id"], game_id=row["id"])
            row["document"]["title"] = row["name"]
            value["presets"].append(row); rows.append((row["name"], action))
        return validate_templates(value), expected, rows
