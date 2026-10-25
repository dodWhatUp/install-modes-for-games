"""Display-only overlay groups. No key injection, native remapping or game launch.

One versioned private store is shared by Hub UI, CLI and the optional AHK
picture relay. Imported declarations never become native layer observations.
"""
from __future__ import annotations

import copy
import ctypes
import hashlib
import io
import json
import math
import ntpath
import os
from pathlib import Path
import re
import tempfile
import time

VERSION = "0.2.13"
SCHEMA = 1
MAX_JSON = 1024 * 1024
# Retained map families and four views can exceed 512 images across games.
# Keep the JSON byte/depth and other manifest collection bounds unchanged.
MAX_ASSETS = 1024
# Each keymap supplies its exact 29 allowed positions from its source geometry.
VIEWS = ("Keys", "Actions", "Combined", "ActionFirst")
VIEW_CHOICES = (("Combined", "Key first"), ("ActionFirst", "Action first"),
                ("Actions", "Action only"), ("Keys", "Key only"))
R8_POSITIONS = {4,8,12,17,3,7,11,16,2,6,10,15,1,5,9,14,37,38,13,18,36,28,29,22,31,30,41,20,23}
ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,79}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")


class OverlayError(ValueError):
    pass


def require(ok, message):
    if not ok:
        raise OverlayError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=True, allow_nan=False, indent=2) + "\n").encode()


def pairs(items):
    value = {}
    for key, item in items:
        require(key not in value, "Duplicate JSON field")
        value[key] = item
    return value


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON, "JSON size limit")
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs,
                           parse_constant=lambda _: require(False, "Nonfinite JSON"))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise OverlayError("Invalid JSON") from error
    def check(v, depth=0):
        require(depth < 20, "JSON depth limit")
        if isinstance(v, dict):
            require(len(v) <= 512, "JSON field limit")
            for k, child in v.items():
                require(type(k) is str and len(k) <= 120, "Invalid field")
                check(child, depth + 1)
        elif isinstance(v, list):
            require(len(v) <= MAX_ASSETS, "JSON list limit")
            for child in v:
                check(child, depth + 1)
        elif isinstance(v, str):
            require(len(v) <= 4096 and not any(ord(c) < 32 for c in v), "Invalid text")
        elif type(v) is float:
            require(math.isfinite(v), "Nonfinite value")
    check(value)
    return value


def fields(obj, names):
    require(type(obj) is dict and set(obj) == set(names.split()), "Unexpected/missing fields")


def token(value):
    require(type(value) is str and ID.fullmatch(value), "Invalid stable ID")


def digest(value):
    require(type(value) is str and HASH.fullmatch(value), "Invalid SHA-256")


def label(value):
    require(type(value) is str and 0 < len(value) <= 240, "Invalid label")


def no_links(path):
    path = Path(path).absolute()
    for part in [path, *path.parents]:
        if part.exists():
            stat = part.lstat()
            require(not part.is_symlink() and not getattr(stat, "st_file_attributes", 0) & 0x400,
                    "Linked/reparse paths refused")
    return path


def read(path, limit=MAX_JSON):
    path = no_links(path)
    before = path.stat()
    require(path.is_file() and 0 < before.st_size <= limit, "Missing/oversized source")
    with path.open("rb") as incoming:
        raw = incoming.read(limit + 1)
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns) and len(raw) == before.st_size,
            "Source changed while reading")
    return raw


def image_bytes(raw, expected):
    from PIL import Image
    digest(expected)
    require(len(raw) <= 16 * 1024 * 1024 and sha(raw) == expected, "Image hash/size mismatch")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            require(im.format in {"PNG", "JPEG"}, "Only PNG/JPEG images supported")
            require(0 < im.width <= 8192 and 0 < im.height <= 8192 and im.width * im.height <= 16000000,
                    "Image dimensions exceed limits")
            size, fmt = im.size, im.format
            im.verify()
        with Image.open(io.BytesIO(raw)) as im:
            im.load()  # Verify compressed pixels, not just the header.
        return {"width": size[0], "height": size[1], "format": fmt}
    except OverlayError:
        raise
    except Exception as error:
        raise OverlayError("Corrupt/unsupported image") from error


def appearance(obj):
    fields(obj, "size_mode size_value opacity monitor anchor offset_x offset_y")
    require(obj["size_mode"] in {"Pixels", "Screen width %", "Screen height %", "Original %"}, "Size mode")
    require(obj["anchor"] in {"TopLeft", "TopRight", "Center", "BottomLeft", "BottomRight"}, "Anchor")
    for key in ("size_value", "opacity", "offset_x", "offset_y"):
        require(type(obj[key]) in (int, float) and math.isfinite(obj[key]), "Appearance number")
    require(1 <= obj["size_value"] <= 8000 and 5 <= obj["opacity"] <= 100 and
            abs(obj["offset_x"]) <= 8000 and abs(obj["offset_y"]) <= 8000 and
            type(obj["monitor"]) is int and 1 <= obj["monitor"] <= 16, "Appearance range")


def executable(value):
    require(type(value) is str and 0 < len(value) <= 1024 and value.lower().endswith(".exe") and
            not any(c in value for c in '*?\r\n\x00"') and not value.startswith(("\\\\", "//")), "Invalid executable")
    if "\\" in value or "/" in value or ":" in value:
        require(ntpath.isabs(value) and not any(p == ".." for p in value.replace("\\", "/").split("/")),
                "Executable path must be absolute")
    return ntpath.normcase(ntpath.normpath(value))


def manifest(value):
    fields(value, "schema_version kind games keymaps assets groups associations")
    require(value["schema_version"] == 1 and type(value["schema_version"]) is int and
            value["kind"] == "overlay_manifest", "Unsupported manifest schema")
    indexed = {}
    for name in ("games", "keymaps", "assets", "groups", "associations"):
        limit = MAX_ASSETS if name == "assets" else 512
        require(type(value[name]) is list and len(value[name]) <= limit, "Collection limit")
        indexed[name] = {}
        for item in value[name]:
            require(type(item) is dict, "Invalid record")
            token(item.get("id"))
            require(item["id"] not in indexed[name], "Duplicate ID")
            indexed[name][item["id"]] = item
    for game in value["games"]:
        fields(game, "id label")
        label(game["label"])
    for keymap in value["keymaps"]:
        fields(keymap, "id label revision outputs_sha256 geometry_sha256 atlas_revision family layers visible_positions hidden_positions blank_masks joystick_drawn")
        label(keymap["label"]); label(keymap["revision"]); label(keymap["atlas_revision"])
        digest(keymap["outputs_sha256"]); digest(keymap["geometry_sha256"])
        require(keymap["family"] in {"SPARSE6", "CORE5", "shared"}, "Layout family")
        positions = keymap["visible_positions"]
        require(type(positions) is list and len(positions) == 29 and all(type(p) is int for p in positions) and
                len(set(positions)) == 29 and 19 not in positions and {36, 37} <= set(positions) and
                all(1 <= p <= 64 for p in positions) and keymap["hidden_positions"] == [19] and
                keymap["joystick_drawn"] is False, "Geometry must retain exact 29 digital positions and hide #19/stick")
        if keymap["family"] in {"SPARSE6", "CORE5"}:
            require(set(positions) == R8_POSITIONS, "R8 exact geometry positions required, including #38/#41")
        require(type(keymap["layers"]) is list and 1 <= len(keymap["layers"]) <= 16, "Layers required")
        names = set()
        for layer in keymap["layers"]:
            fields(layer, "id profile_id profile_sha256")
            token(layer["id"]); label(layer["profile_id"]); digest(layer["profile_sha256"])
            require(layer["id"] not in names, "Duplicate layer")
            names.add(layer["id"])
        require(type(keymap["blank_masks"]) is dict and set(keymap["blank_masks"]) == names, "Exact layer blank masks required")
        for mask in keymap["blank_masks"].values():
            require(type(mask) is list and all(type(p) is int and p in positions for p in mask) and
                    len(mask) == len(set(mask)), "Invalid blank mask")
    for asset in value["assets"]:
        fields(asset, "id label path sha256 keymap_id layer context view profile_id evidence")
        label(asset["label"]); digest(asset["sha256"]); token(asset["context"])
        require(type(asset["path"]) is str and re.fullmatch(r"[A-Za-z0-9_. /-]{1,240}", asset["path"]) and
                all(p not in {"", ".", ".."} for p in asset["path"].split("/")) and
                asset["path"].lower().endswith((".png", ".jpg", ".jpeg")), "Relative image path required")
        require(asset["view"] in VIEWS and asset["evidence"] in {"effective_config", "published_default", "unknown"}, "View/evidence")
        keymap = indexed["keymaps"].get(asset["keymap_id"])
        require(keymap is not None, "Missing keymap")
        layer = next((l for l in keymap["layers"] if l["id"] == asset["layer"]), None)
        require(layer is not None and layer["profile_id"] == asset["profile_id"], "Exact installed profile/layer reference required")
    for group in value["groups"]:
        fields(group, "id label game_id keymap_id asset_ids rendering")
        label(group["label"]); appearance(group["rendering"])
        require(group["game_id"] in indexed["games"] and group["keymap_id"] in indexed["keymaps"], "Group references missing")
        require(type(group["asset_ids"]) is list and len(group["asset_ids"]) == len(set(group["asset_ids"])) and
                len(group["asset_ids"]) <= 128, "Asset references invalid")
        matches = set()
        for aid in group["asset_ids"]:
            asset = indexed["assets"].get(aid)
            require(asset is not None and asset["keymap_id"] == group["keymap_id"], "Group asset keymap mismatch")
            match = (asset["layer"], asset["context"], asset["view"])
            require(match not in matches, "Ambiguous asset in group")
            matches.add(match)
    for assoc in value["associations"]:
        association(assoc, indexed)
    return indexed


def association(obj, indexed):
    fields(obj, "id game_id executables excluded_executables keymap_id default_group cycle_groups cycle_enabled priority")
    require(obj["game_id"] in indexed["games"] and obj["keymap_id"] in indexed["keymaps"], "Association references")
    for name in ("executables", "excluded_executables"):
        require(type(obj[name]) is list and len(obj[name]) <= 32, "Executable list limit")
        for exe in obj[name]:
            executable(exe)
    require(bool(obj["executables"]), "Gameplay executable required; never select a launcher automatically")
    require(type(obj["priority"]) is int and -100 <= obj["priority"] <= 100 and type(obj["cycle_enabled"]) is bool,
            "Association options")
    require(type(obj["cycle_groups"]) is list and len(set(obj["cycle_groups"])) == len(obj["cycle_groups"]), "Cycle order")
    for gid in [obj["default_group"], *obj["cycle_groups"]]:
        group = indexed["groups"].get(gid)
        require(group is not None and group["game_id"] == obj["game_id"] and group["keymap_id"] == obj["keymap_id"],
                "Group must match game and exact keymap revision")


def empty_store():
    return {"schema_version": 1, "kind": "overlay_store", "revision": 0,
            "manifest": {"schema_version": 1, "kind": "overlay_manifest", **{n: [] for n in
                         ("games", "keymaps", "assets", "groups", "associations")}},
            "preferences": {"enabled": False, "display": False, "display_target": "hub", "selections": {}, "overrides": {},
                            "visibility": {"overlay": {"details": False, "associations": True}}}}


def validate_store(value):
    fields(value, "schema_version kind revision manifest preferences")
    require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["kind"] == "overlay_store" and
            type(value["revision"]) is int and value["revision"] >= 0, "Store schema")
    indexed = manifest(value["manifest"])
    p = value["preferences"]
    require(type(p) is dict, "Preferences object required")
    fields({k: v for k, v in p.items() if k != "appearance"}, "enabled display display_target selections overrides visibility")
    if "appearance" in p:
        from GameToolOverlayAppearance import validate_policy
        validate_policy(p["appearance"], indexed["games"])
    require(p["display_target"] in {"hub", "studio"}, "Display owner")
    require(type(p["enabled"]) is bool and type(p["display"]) is bool, "Display state")
    require(type(p["visibility"]) is dict and set(p["visibility"]) == {"overlay"}, "Page visibility")
    fields(p["visibility"]["overlay"], "details associations")
    require(all(type(v) is bool for v in p["visibility"]["overlay"].values()), "Visibility boolean")
    require(type(p["selections"]) is dict and type(p["overrides"]) is dict, "Selection state")
    for game, sel in p["selections"].items():
        require(game in indexed["games"], "Selection game")
        fields(sel, "layer context view")
        token(sel["layer"]); token(sel["context"]); require(sel["view"] in VIEWS, "Selection view")
    for game, gid in p["overrides"].items():
        require(game in indexed["games"] and gid in indexed["groups"] and indexed["groups"][gid]["game_id"] == game,
                "Override game mismatch")
    return indexed


class Store:
    def __init__(self, directory):
        self.directory = no_links(directory)
        self.path = self.directory / "overlay-groups.json"
        self.assets = self.directory / "overlay-assets"
        self._cached_raw = None
        self._cached_value = None
        self._image_info = {}

    def load(self):
        if not self.path.exists():
            return empty_store(), "absent"
        raw = read(self.path)
        if raw != self._cached_raw:
            value = decode(raw); validate_store(value)
            self._cached_raw, self._cached_value = raw, value
        # Callers own their draft: neither a UI mutation nor an import may
        # contaminate the next read. Every load still reads and compares bytes.
        return copy.deepcopy(self._cached_value), sha(raw)

    def write(self, value, expected):
        validate_store(value)
        no_links(self.directory); self.directory.mkdir(parents=True, exist_ok=True)
        lock = self.directory / "overlay-groups.lock"
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as error:
            raise OverlayError("Store busy; stale lock requires explicit inspection, never automatic removal") from error
        temp = None
        try:
            os.close(fd)
            current, current_hash = self.load()
            require(current_hash == expected, "Store changed; reload before write")
            value = copy.deepcopy(value); value["revision"] = current["revision"] + 1
            raw = encode(value)
            require(len(raw) <= MAX_JSON, "Store size limit")
            tempfd, temp = tempfile.mkstemp(prefix="overlay-", suffix=".tmp", dir=self.directory)
            with os.fdopen(tempfd, "wb") as out:
                out.write(raw); out.flush(); os.fsync(out.fileno())
            # Exact preceding state is retained separately, never overwritten.
            if self.path.exists():
                backup = self.directory / ("overlay-before-" + current_hash + ".json")
                if not backup.exists():
                    with backup.open("xb") as out:
                        out.write(read(self.path)); out.flush(); os.fsync(out.fileno())
            require(self.load()[1] == expected, "Concurrent store drift")
            no_links(self.path); os.replace(temp, self.path); temp = None
            require(read(self.path) == raw, "Saved store readback mismatch")
            return {"revision": value["revision"], "sha256": sha(raw), "native_changes": False}
        finally:
            if temp and Path(temp).exists():
                Path(temp).unlink()
            lock.unlink()

    def validate_import(self, source):
        source = no_links(source)
        raw = read(source); value = decode(raw); manifest(value)
        images = {}
        for asset in value["assets"]:
            path = source.parent / asset["path"]
            pixels = read(path, 16 * 1024 * 1024)
            info = image_bytes(pixels, asset["sha256"])
            images[asset["id"]] = (pixels, info)
        require(read(source) == raw, "Manifest changed while validating")
        return value, images, sha(raw)

    def import_manifest(self, source, expected, conflict="stop", preferences=None):
        require(conflict in {"stop", "keep", "replace"}, "Explicit import conflict policy")
        require(self.load()[1] == expected, "Store changed; reload before import")
        incoming, images, fingerprint = self.validate_import(source)
        value, _ = self.load(); conflicts = []
        for name in ("games", "keymaps", "assets", "groups", "associations"):
            old = {obj["id"]: obj for obj in value["manifest"][name]}
            for obj in incoming[name]:
                obj = copy.deepcopy(obj)
                if name == "assets":
                    obj["path"] = "overlay-assets/" + obj["sha256"] + (".png" if images[obj["id"]][1]["format"] == "PNG" else ".jpg")
                if obj["id"] in old and old[obj["id"]] != obj:
                    conflicts.append(name + ":" + obj["id"])
                    if conflict == "keep":
                        continue
                old[obj["id"]] = obj
            value["manifest"][name] = list(old.values())
        require(not conflicts or conflict != "stop", "Import conflicts: " + ", ".join(conflicts))
        if preferences is not None:
            value["preferences"] = copy.deepcopy(preferences)
        validate_store(value)  # No partial import if dependent records cannot coexist.
        require(read(source) and sha(read(source)) == fingerprint, "Manifest drift")
        self.assets.mkdir(parents=True, exist_ok=True); no_links(self.assets)
        for pixels, info in images.values():
            target = self.assets / (sha(pixels) + (".png" if info["format"] == "PNG" else ".jpg"))
            no_links(target)
            if target.exists():
                require(read(target, 16 * 1024 * 1024) == pixels, "Existing managed asset mismatch")
            else:
                with target.open("xb") as out:
                    out.write(pixels); out.flush(); os.fsync(out.fileno())
                require(read(target, 16 * 1024 * 1024) == pixels, "Managed asset readback mismatch")
        receipt = self.write(value, expected)
        receipt.update(conflicts=conflicts, policy=conflict, source_sha256=fingerprint)
        return receipt

    def update(self, action, payload, expected):
        payload = copy.deepcopy(payload)
        value, _ = self.load(); indexed = validate_store(value); p = value["preferences"]
        if action == "association":
            token(payload.get("id")); association(payload, indexed)
            rows = value["manifest"]["associations"]
            value["manifest"]["associations"] = [r for r in rows if r["id"] != payload["id"]] + [payload]
        elif action == "selection":
            fields(payload, "game_id layer context view")
            game = payload.pop("game_id")
            require(game in indexed["games"], "Unknown game")
            p["selections"][game] = payload
            if "appearance" in p:
                from GameToolOverlayAppearance import effective
                style = effective(p["appearance"], game)
                # A layer/context selection does not break global inheritance.
                if style["view"] != payload["view"]:
                    style["view"] = payload["view"]
                    p["appearance"]["games"][game] = style
        elif action in {"select", "auto", "cycle"}:
            fields(payload, "game_id group_id")
            game, gid = payload["game_id"], payload["group_id"]
            require(game in indexed["games"], "Unknown game")
            if action == "auto":
                p["overrides"].pop(game, None)
            elif action == "select":
                require(gid in indexed["groups"] and indexed["groups"][gid]["game_id"] == game, "Wrong game group")
                p["overrides"][game] = gid
            else:
                rows = sorted((a for a in indexed["associations"].values() if a["game_id"] == game), key=lambda a: (-a["priority"], a["id"]))
                require(bool(rows) and rows[0]["cycle_enabled"] and rows[0]["cycle_groups"], "Cycling disabled/empty")
                order = rows[0]["cycle_groups"]
                current = p["overrides"].get(game, rows[0]["default_group"])
                p["overrides"][game] = order[(order.index(current) + 1) % len(order)] if current in order else order[0]
        elif action == "display":
            fields(payload, "enabled display display_target")
            require(type(payload["enabled"]) is bool and type(payload["display"]) is bool, "Display booleans")
            require(payload["display_target"] in {"hub", "studio"}, "Display owner")
            p.update(payload)
        elif action == "visibility":
            fields(payload, "details associations"); p["visibility"]["overlay"] = payload
        else:
            raise OverlayError("Unsupported scoped write")
        return self.write(value, expected)

    def asset(self, asset):
        require(asset["path"].startswith("overlay-assets/"), "Managed asset required")
        raw = read(self.directory / asset["path"], 16 * 1024 * 1024)
        expected = asset["sha256"]
        info = self._image_info.get(expected)
        if info is None:
            info = image_bytes(raw, expected)
            if len(self._image_info) >= 16:
                self._image_info.pop(next(iter(self._image_info)))
            self._image_info[expected] = info
        else:
            # Reuse only decoded metadata for the exact verified bytes. File
            # existence/reparse/drift/size and content SHA remain checked on
            # every call, including the same path with altered bytes.
            require(sha(raw) == expected, "Image hash/size mismatch")
        return raw, dict(info)


def capabilities():
    return {"schema_version": 1, "version": VERSION, "read": ["schema", "capabilities", "status", "list", "inspect", "validate", "foreground"],
            "writes": ["import", "association", "selection", "select", "cycle", "auto", "display", "visibility", "export"],
            "foreground": "Windows GetForegroundWindow + QueryFullProcessImageNameW; polling 250ms; no injection",
            "native_observation": "experimental Azeron 2.0.2 native-log event tracking in Hub; fresh native snapshots/reWASD unsupported",
            "layer_fallback": "Selected/Unknown; keyboard keys never prove device/layer",
            "shortcut_changes": False, "input": False, "game_launch": False}


def choose(value, foreground, now=None, native=None, fallback_group=None):
    """Pure selection; native is trusted in-process adapter output, never CLI JSON."""
    now = time.monotonic() if now is None else now
    indexed = validate_store(value); p = value["preferences"]
    result = {"schema_version": 1, "state": "Fallback", "reason": "No foreground gameplay association",
              "game_id": None, "group_id": None, "asset_id": None, "manual_override": False,
              "profile_state": "Unknown", "layer_state": "Unknown", "native_mismatch": False,
              "native_capability": "unavailable", "foreground_age_ms": None,
              "display": p["display"], "enabled": p["enabled"], "render": False, "display_target": p["display_target"],
              "selection_scope": "none"}
    if not p["enabled"]:
        result["reason"] = "Automatic selection stopped"; return result
    if foreground is None:
        result["reason"] = "Foreground unavailable"; return result
    age = now - foreground.get("at", -1e30)
    result["foreground_age_ms"] = max(0, round(age * 1000))
    if not 0 <= age <= 1:
        result["reason"] = "Foreground Stale"; return result
    fallback_allowed = fallback_group is not None and p["display_target"] == "studio"
    if foreground.get("own") and not fallback_allowed:
        result["reason"] = "App-owned window; passive overlay hidden"; return result
    exe = executable(foreground["exe"])
    candidates = []
    for assoc in indexed["associations"].values():
        def match(rule):
            rule = executable(rule)
            return exe == rule if ntpath.isabs(rule) else ntpath.basename(exe) == rule
        if any(match(r) for r in assoc["excluded_executables"]):
            continue
        rules = [r for r in assoc["executables"] if match(r)]
        if rules:
            candidates.append((max(2 if ntpath.isabs(r) else 1 for r in rules), assoc["priority"], assoc))
    using_fallback = not candidates
    if using_fallback:
        if not fallback_allowed:return result
        group = indexed["groups"].get(fallback_group)
        if group is None:
            result["reason"] = "Other-application fallback group unavailable";return result
        assoc = {"game_id":group["game_id"],"keymap_id":group["keymap_id"],"default_group":group["id"]}
        result.update(selection_scope="fallback",reason="Other application; saved fallback map")
    else:
        candidates.sort(key=lambda r: (-r[0], -r[1], r[2]["id"]))
        best = candidates[0]
        ties = [r[2] for r in candidates if r[:2] == best[:2]]
        if len({(a["game_id"], a["keymap_id"], a["default_group"]) for a in ties}) > 1:
            result["reason"] = "Ambiguous equal-priority executable matches; nothing displayed"
            result["ambiguous_associations"] = [a["id"] for a in ties]; return result
        assoc = best[2]
        result.update(selection_scope="association",reason="Exact path" if best[0] == 2 else "Executable basename")
    game = assoc["game_id"]; keymap = indexed["keymaps"][assoc["keymap_id"]]
    selected = p["selections"].get(game, {"layer": "Unknown", "context": "gameplay", "view": "Combined"})
    layer = selected["layer"]
    result.update(game_id=game, profile_state="Selected", layer_state="Selected" if layer != "Unknown" else "Unknown",
                  context=selected["context"], view=selected["view"], keymap_id=keymap["id"], keymap_revision=keymap["revision"])
    if native is not None:
        result["native_capability"] = native.get("provider", "unknown")
        if native.get("available") is False:
            result.update(profile_state="Unknown", layer_state="Unknown", reason=native.get("reason", "Native layer unavailable"))
            return result
        fresh = 0 <= now - native.get("at", -1e30) <= 0.5
        if not fresh:
            result.update(profile_state="Stale", layer_state="Stale", reason="Native observation Stale; refusing action map")
            return result
        native_state = "Event-tracked" if native.get("state") == "Event-tracked" else "Observed"
        result.update(profile_state=native_state, layer_state=native_state)
        if native_state == "Event-tracked":
            result["native_event_utc"] = native.get("event_utc")
            result["native_momentary_layer"] = native.get("momentary_layer") is True
            result["native_snapshot_verified"] = False
        matching = next((l for l in keymap["layers"] if l["profile_id"] == native.get("profile_id")), None)
        if matching is None or native.get("outputs_sha256") != keymap["outputs_sha256"] or native.get("profile_sha256") != matching["profile_sha256"]:
            result.update(native_mismatch=True, reason="Observed native output/profile revision mismatch")
            return result
        layer = matching["id"]
    result["layer"] = layer
    gid = assoc["default_group"] if using_fallback else p["overrides"].get(game, assoc["default_group"])
    result["manual_override"] = not using_fallback and game in p["overrides"]
    result["group_id"] = gid
    group = indexed["groups"].get(gid)
    if not group or group["keymap_id"] != keymap["id"]:
        result["reason"] = "Group keymap revision mismatch"; return result
    assets = [indexed["assets"][aid] for aid in group["asset_ids"]]
    match = next((a for a in assets if (a["layer"], a["context"], a["view"]) ==
                  (layer, selected["context"], selected["view"])), None)
    if not match:
        result["reason"] = "No exact layer/context/view asset; no stale map fallback"; return result
    result.update(state="Selected", asset_id=match["id"], render=p["display"], evidence=match["evidence"],
                  reason=result["reason"] + ("; manual override" if result["manual_override"] else "; saved default"))
    return result


def foreground_windows():
    if os.name != "nt":
        return None
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user.GetForegroundWindow.restype = ctypes.c_void_p
    user.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    hwnd = user.GetForegroundWindow()
    if not hwnd:
        return None
    pid = ctypes.c_uint32(); user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    handle = kernel.OpenProcess(0x1000, False, pid.value)
    if not handle:
        return None
    try:
        text = ctypes.create_unicode_buffer(32768); size = ctypes.c_uint32(32768)
        if not kernel.QueryFullProcessImageNameW(handle, 0, text, ctypes.byref(size)):
            return None
        if user.GetForegroundWindow() != hwnd:
            return None
        return {"exe": text.value, "pid": pid.value, "hwnd": hwnd, "own": pid.value == os.getpid(), "at": time.monotonic()}
    finally:
        kernel.CloseHandle(handle)


def checked_selection(store, value, foreground, now=None, native=None):
    from GameToolOverlayFallback import read as read_fallback
    fallback_group = None; fallback_error = False
    try:
        fallback_group = read_fallback(store.directory)[0]["group_id"]
    except (OSError,ValueError):
        fallback_error = True
    result = choose(value, foreground, now=now, native=native, fallback_group=fallback_group)
    if fallback_error and result["game_id"] is None:
        result["reason"] += "; other-application settings invalid"
    if foreground:
        result["foreground_exe"] = foreground["exe"]
    if result.get("asset_id"):
        try:
            index = validate_store(value); store.asset(index["assets"][result["asset_id"]])
        except Exception:
            result.update(state="Fallback", reason="Selected image missing/corrupt/drifted; no stale map displayed", render=False, asset_id=None)
    return result


def running_windows():
    """Read window processes as association candidates, NOT selection evidence."""
    if os.name != "nt":
        return []
    user = ctypes.WinDLL("user32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    user.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
    user.IsWindowVisible.argtypes = [ctypes.c_void_p]
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    result = {}; callback_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_ssize_t)
    def collect(hwnd, extra):
        if not user.IsWindowVisible(hwnd): return 1
        pid = ctypes.c_uint32(); user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        handle = kernel.OpenProcess(0x1000, False, pid.value)
        if handle:
            try:
                text = ctypes.create_unicode_buffer(32768); size = ctypes.c_uint32(32768)
                if kernel.QueryFullProcessImageNameW(handle, 0, text, ctypes.byref(size)):
                    result[pid.value] = {"pid": pid.value, "exe": text.value, "basis": "running_candidate_only"}
            finally:
                kernel.CloseHandle(handle)
        return 1
    callback = callback_type(collect)
    user.EnumWindows.argtypes = [callback_type, ctypes.c_ssize_t]
    user.EnumWindows(callback, 0)
    return list(result.values())


def geometry(rendering, iw, ih, monitor):
    appearance(rendering)
    x, y, mw, mh = monitor
    require(iw > 0 and ih > 0 and mw > 32 and mh > 32, "Invalid monitor/image dimensions")
    mode, val = rendering["size_mode"], rendering["size_value"]
    w = val if mode == "Pixels" else (mw * val / 100 if mode == "Screen width %" else
                                     mh * val / 100 * iw / ih if mode == "Screen height %" else iw * val / 100)
    h = w * ih / iw; scale = min(1, (mw - 32) / w, (mh - 32) / h)
    w, h = max(1, round(w * scale)), max(1, round(h * scale))
    anchor = rendering["anchor"]
    px = (mw - w) / 2 if anchor == "Center" else mw - w - 16 if "Right" in anchor else 16
    py = (mh - h) / 2 if anchor == "Center" else mh - h - 16 if "Bottom" in anchor else 16
    px = min(mw - w, max(0, px + rendering["offset_x"])); py = min(mh - h, max(0, py + rendering["offset_y"]))
    return (round(x + px), round(y + py), w, h)


def export_manifest(store, output, expected):
    value, actual = store.load(); require(actual == expected, "Store changed")
    output = no_links(output); require(not output.exists(), "Export needs a new directory")
    output.mkdir(parents=True)
    exported = copy.deepcopy(value["manifest"])
    # Private export: executable paths/profile IDs remain private, never curated source.
    for asset in exported["assets"]:
        raw, info = store.asset(asset)
        target = output / asset["path"]; target.parent.mkdir(exist_ok=True, parents=True)
        if not target.exists():
            with target.open("xb") as out:
                out.write(raw); out.flush(); os.fsync(out.fileno())
    target = output / "manifest.json"
    require(store.load()[1] == expected, "Store changed during export")
    with target.open("xb") as out:
        out.write(encode(exported)); out.flush(); os.fsync(out.fileno())
    store.validate_import(target)
    return {"path": str(target), "privacy": "private_asset_export", "restore_tested": False}


def relay(store, result, directory, now=None):
    """Private display-only INI for existing AHK Hold/Toggle picture ownership.

    No commands, trigger assignments or input payload. Reader must check TTL,
    foreground identity and image hash. Written only while explicitly enabled.
    """
    import configparser
    now = time.time() if now is None else now
    value, _ = store.load(); indexed = validate_store(value)
    # Whole-second expiry alone can expire a fresh heartbeat at the next boundary.
    # Keep it for legacy readers; current Studio uses the exact millisecond value.
    data = {"Schema": "1", "ExpiresUnix": str(int(now + 1)),
            "ExpiresUnixMs": str(int((now + 1) * 1000)), "Active": "0",
            "StatusReason": str(result.get("reason", "No active selection")).replace("\r", " ").replace("\n", " ")[:200]}
    if result.get("render") and result.get("asset_id") and result.get("display_target") == "studio":
        asset = indexed["assets"][result["asset_id"]]; store.asset(asset)
        rendering = indexed["groups"][result["group_id"]]["rendering"]
        data.update(Active="1", File=str((store.directory / asset["path"]).absolute()), SHA256=asset["sha256"],
                    Game=result["game_id"], Asset=asset["id"], LayerState=result["layer_state"])
        data.pop("StatusReason", None)
        data.update({k: str(v) for k, v in rendering.items()})
        # No stale PID is persisted; current foreground is re-read by the host.
        data["Exe"] = result.get("foreground_exe", "")
        from GameToolOverlayTransition import read as read_transition
        transition, _ = read_transition(store.directory)
        duration = transition["duration_ms"] if transition["enabled"] else 0
        data.update(FadeInMs=str(duration), FadeOutMs=str(duration))
        # Preparation hints are display data, never active-layer observations.
        # Only this group's current context/view is eligible; the reader checks
        # each file's bytes before preparation and again on every cache use.
        group = indexed["groups"][result["group_id"]]
        warm = [indexed["assets"][aid] for aid in group["asset_ids"]
                if indexed["assets"][aid]["context"] == asset["context"]
                and indexed["assets"][aid]["view"] == asset["view"]][:8]
        data["WarmCount"] = str(len(warm))
        for number, hint in enumerate(warm, 1):
            data[f"WarmFile{number}"] = str((store.directory / hint["path"]).absolute())
            data[f"WarmSHA256{number}"] = hint["sha256"]
        from GameToolOverlayLayerShow import relay_fields
        data.update(relay_fields(store, result))
        from GameToolOverlayAlternate import relay_fields as alternate_fields
        data.update(alternate_fields(store, indexed, result, asset))
    write_relay(Path(directory) / "overlay-selection.ini", data)
    from GameToolKeymapButtons import relay_data
    linked = relay_data(store, indexed, result, {k: data[k] for k in ("Schema", "ExpiresUnix", "ExpiresUnixMs")})
    for slot, slot_data in linked.items():
        for field in ("FadeInMs", "FadeOutMs"):
            slot_data[field] = data.get(field, "0")
        write_relay(Path(directory) / f"overlay-selection-slot-{slot}.ini", slot_data)


def replace_relay(source, destination):
    """Keep atomic publication across a brief Windows reader/rename collision.

    Retry only the known sharing/access contention codes, for at most 50ms.
    Never truncate/unlink the last complete relay or extend its original TTL.
    Persistent permission errors still fail closed on this bounded attempt.
    """
    for attempt in range(5):
        try:
            os.replace(source, destination)
            return
        except OSError as error:
            if getattr(error, "winerror", None) not in {5, 32, 33} or attempt == 4:
                raise
            time.sleep(0.005 * (attempt + 1))


def write_relay(path, data):
    import configparser
    path = no_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    config = configparser.ConfigParser(interpolation=None); config.optionxform = str
    config["Overlay"] = data
    text = io.StringIO(); config.write(text)
    fd, temp = tempfile.mkstemp(prefix="relay-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(text.getvalue()); out.flush(); os.fsync(out.fileno())
        replace_relay(temp, path)
    finally:
        if Path(temp).exists():
            Path(temp).unlink()


def cli(argv):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("action", choices=("schema", "capabilities", "status", "list", "inspect", "foreground", "validate", "import", "export",
                                         "association", "selection", "select", "auto", "cycle", "display", "visibility"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--id", help="Inspect one stable association/group/keymap/asset ID")
    parser.add_argument("--conflict", choices=("stop", "keep", "replace"), default="stop")
    args = parser.parse_args(argv)
    try:
        store = Store(args.directory)
        if args.action == "schema":
            result = {"schema_version": 1, "kind": "overlay_manifest", "collections": ["games", "keymaps", "assets", "groups", "associations"],
                      "contract": "docs/OVERLAY-GROUPS.md", "template": "examples/game-tool-hub/overlay-manifest.example.json",
                      "validator_version": VERSION, "unknown_fields": "refused", "images": "PNG/JPEG, 16MiB/16MP, SHA-256 verified before activation"}
        elif args.action == "capabilities":
            result = capabilities()
        elif args.action == "foreground":
            result = foreground_windows()
        elif args.action in {"status", "list", "inspect"}:
            value, fingerprint = store.load()
            result = {"store_sha256": fingerprint, "revision": value["revision"], "capabilities": capabilities()}
            if args.action == "list":
                result.update(manifest=value["manifest"], preferences=value["preferences"])
            elif args.action == "inspect":
                rows = [row for name in ("games", "keymaps", "assets", "groups", "associations")
                        for row in value["manifest"][name] if row["id"] == args.id]
                require(len(rows) == 1, "Missing/ambiguous ID; use list to inspect collection")
                result["record"] = rows[0]
            else:
                result["selection"] = checked_selection(store, value, foreground_windows())
        elif args.action == "validate":
            value, images, fingerprint = store.validate_import(args.source)
            result = {"valid": True, "sha256": fingerprint, "images": len(images), "groups": len(value["groups"])}
        else:
            require(args.expected_sha256 is not None, "Scoped writes require expected store hash ('absent' for new)")
            if args.action == "import":
                result = store.import_manifest(args.source, args.expected_sha256, args.conflict)
            elif args.action == "export":
                result = export_manifest(store, args.output, args.expected_sha256)
            else:
                result = store.update(args.action, decode(read(args.source)), args.expected_sha256)
        print(json.dumps(result, ensure_ascii=True, indent=2)); return 0
    except Exception as error:
        print(json.dumps({"valid": False, "error": str(error) if isinstance(error, OverlayError) else "Overlay operation refused",
                          "input": False, "native_changes": False})); return 2


if __name__ == "__main__":
    import sys
    raise SystemExit(cli(sys.argv[1:]))
