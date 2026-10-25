"""Optional native layer visibility, independent of the existing picture key.

Only the registered BASIC profile's momentary selectors are offered. No native
profile is edited and no keyboard input is inferred, registered or emitted.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
import tempfile
import uuid
import GameToolOverlay as api

VERSION = "0.1.0"


def validate(value):
    api.fields(value, "schema_version kind rules")
    api.require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["kind"] == "overlay_layer_show", "Unsupported layer-show settings")
    api.require(type(value["rules"]) is list and len(value["rules"]) <= 32, "Layer-show selection limit")
    identities = set()
    for rule in value["rules"]:
        api.fields(rule, "base_profile_id base_profile_sha256 profile_id profile_sha256 outputs_sha256 layer button_id")
        api.token(rule["layer"])
        for key in ("base_profile_id", "profile_id"):
            api.require(type(rule[key]) is str and str(uuid.UUID(rule[key])) == rule[key], "Invalid native profile ID")
        for key in ("base_profile_sha256", "profile_sha256", "outputs_sha256"): api.digest(rule[key])
        api.require(type(rule["button_id"]) is int and 1 <= rule["button_id"] <= 64, "Invalid layer button")
        api.require(rule["layer"] != "BASIC" and rule["profile_id"] != rule["base_profile_id"], "The base layer cannot open the overlay automatically")
        identity = (rule["profile_id"], rule["outputs_sha256"])
        api.require(identity not in identities, "Duplicate layer-show choice"); identities.add(identity)
    return value


def read(directory):
    path = api.no_links(Path(directory) / "overlay-layer-show.json")
    raw = api.read(path, 16384) if path.exists() else None
    return validate(api.decode(raw)) if raw is not None else {"schema_version": 1, "kind": "overlay_layer_show", "rules": []}, raw


def choices(store, profiles=None):
    """Resolve exact saved revisions and button numbers from native read-only data."""
    if profiles is None:
        profiles = Path(os.environ.get("APPDATA", "")) / "Azeron Software/Storage/DevicesStorage"
    profiles = api.no_links(profiles)
    value, _ = store.load(); indexed = api.validate_store(value)
    cache = {}; result = {}
    def native(layer):
        api.require(type(layer["profile_id"]) is str and str(uuid.UUID(layer["profile_id"])) == layer["profile_id"], "Unsupported native profile ID")
        identity = (layer["profile_id"], layer["profile_sha256"])
        if identity not in cache:
            matches = list(profiles.glob("*/ProfileStorage/profile_" + layer["profile_id"] + ".json"))
            api.require(len(matches) == 1, "Native profile missing or ambiguous")
            raw = api.read(api.no_links(matches[0]), 2 * 1024 * 1024)
            api.require(api.sha(raw) == layer["profile_sha256"], "Native profile revision changed")
            data = api.decode(raw)
            api.require(data.get("id") == layer["profile_id"], "Native profile identity changed")
            api.require(type(data.get("inputs")) is list and len(data["inputs"]) <= 128 and all(type(b) is dict for b in data["inputs"]), "Invalid native input list")
            cache[identity] = data
        return cache[identity]
    for keymap in indexed["keymaps"].values():
        base = next((l for l in keymap["layers"] if l["id"] == "BASIC"), None)
        if not base: continue
        try: data = native(base)
        except (OSError, ValueError): continue
        for layer in keymap["layers"]:
            if layer["id"] == "BASIC": continue
            selectors = [b for b in data.get("inputs", []) if b.get("types", [])[:1] == ["24"] and b.get("isToggleOnHold") is True and b.get("layeringProfileId") == layer["profile_id"]]
            if len(selectors) != 1: continue
            try: native(layer)
            except (OSError, ValueError): continue
            rule = dict(base_profile_id=base["profile_id"], base_profile_sha256=base["profile_sha256"], profile_id=layer["profile_id"], profile_sha256=layer["profile_sha256"], outputs_sha256=keymap["outputs_sha256"], layer=layer["id"], button_id=selectors[0]["id"])
            validate(dict(schema_version=1, kind="overlay_layer_show", rules=[rule]))
            identity = api.sha(api.encode(rule))
            result[identity] = rule
    return result


def save(store, selected, expected, profiles=None):
    value = validate(dict(schema_version=1, kind="overlay_layer_show", rules=selected))
    available = choices(store, profiles)
    api.require(all(rule in available.values() for rule in selected), "Layer/profile changed; reopen the layer choices")
    _, registry = store.load()
    directory = api.no_links(store.directory); directory.mkdir(parents=True, exist_ok=True)
    lock = api.no_links(directory / "overlay-layer-show.lock"); temp = None
    try: fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error: raise api.OverlayError("Layer-show settings busy; inspect the owner before retrying") from error
    try:
        os.close(fd); _, current = read(directory)
        api.require(current == expected, "Layer-show settings changed; reopen the controls")
        if current is not None:
            backup = api.no_links(directory / ("overlay-layer-show-before-" + api.sha(current) + ".json"))
            if backup.exists(): api.require(api.read(backup, 16384) == current, "Layer-show recovery copy differs")
            else:
                with backup.open("xb") as out: out.write(current); out.flush(); os.fsync(out.fileno())
        raw = api.encode(value)
        fd, name = tempfile.mkstemp(prefix="layer-show-", dir=directory); temp = Path(name)
        with os.fdopen(fd, "wb") as out: out.write(raw); out.flush(); os.fsync(out.fileno())
        api.require(read(directory)[1] == expected and store.load()[1] == registry, "Overlay settings changed while saving; reopen the controls")
        api.require(all(rule in choices(store, profiles).values() for rule in selected), "Native profile changed while saving")
        os.replace(temp, directory / "overlay-layer-show.json"); temp = None
        api.require(read(directory)[1] == raw, "Layer-show readback differs")
        return read(directory)
    finally:
        if temp is not None and temp.exists(): temp.unlink()
        lock.unlink()


def relay_fields(store, result, profiles=None):
    off = {"LayerShow": "0"}
    try:
        settings, _ = read(store.directory)
        if not settings["rules"] or not result.get("render") or result.get("display_target") != "studio" or result.get("layer_state") != "Event-tracked" or result.get("native_momentary_layer") is not True: return off
        stamp = result.get("native_event_utc")
        if type(stamp) not in (int, float) or not math.isfinite(stamp): return off
        value, _ = store.load(); keymap = api.validate_store(value)["keymaps"].get(result.get("keymap_id"))
        if not keymap: return off
        layer = next((l for l in keymap["layers"] if l["id"] == result.get("layer")), None)
        if layer is None: return off
        rule = next((r for r in settings["rules"] if r["profile_id"] == layer["profile_id"] and r["profile_sha256"] == layer["profile_sha256"] and r["outputs_sha256"] == keymap["outputs_sha256"] and r["layer"] == layer["id"]), None)
        if rule is None or rule not in choices(store, profiles).values(): return off
        return {"LayerShow": "1", "LayerHoldKey": api.sha(api.encode([rule["profile_id"], stamp]))}
    except (OSError, ValueError): return off  # Bad optional settings never disable the dedicated picture key.


class LayerShowEditor:
    def __init__(self, parent, store, on_save=lambda: None, profiles=None):
        import tkinter as tk
        from tkinter import ttk
        self.store, self.on_save, self.profiles = store, on_save, profiles
        value, self.expected = read(store.directory)
        self.available = choices(store, profiles)
        self.window = tk.Toplevel(parent); self.window.title("Show overlay with layer buttons")
        body = ttk.Frame(self.window, padding=16); body.pack(fill="both", expand=True); body.columnconfigure(0, weight=1)
        ttk.Label(body, text="Also show when a selected layer is active", wraplength=420).grid(row=0, column=0, sticky="w")
        self.selected = {}
        for row, (identity, rule) in enumerate(sorted(self.available.items(), key=lambda pair: (pair[1]["button_id"], pair[0])), 1):
            flag = tk.BooleanVar(self.window, value=rule in value["rules"]); self.selected[identity] = flag
            ttk.Checkbutton(body, text=f'#{rule["button_id"]} — {rule["layer"]}', variable=flag).grid(row=row, column=0, sticky="w", pady=3)
        row = len(self.available) + 1
        ttk.Label(body, text="#19 works independently. Select none for #19 only.\nNo profile changes. Applies to automatic layer maps;\nfixed picture guides keep their own keys.", wraplength=420).grid(row=row, column=0, sticky="w", pady=(10, 4))
        self.message = tk.StringVar(self.window, value="" if self.available else "No verified momentary layer buttons found. Keep your native profiles unchanged and check their registered revisions.")
        if any(rule not in self.available.values() for rule in value["rules"]): self.message.set("Some saved choices no longer match native profiles. Review the available choices before saving.")
        ttk.Label(body, textvariable=self.message, wraplength=420).grid(row=row+1, column=0, sticky="w", pady=6)
        bar = ttk.Frame(body); bar.grid(row=row+2, column=0, sticky="e")
        ttk.Button(bar, text="Select none", command=lambda: [v.set(False) for v in self.selected.values()]).pack(side="left", padx=6)
        ttk.Button(bar, text="Cancel", command=self.window.destroy).pack(side="left", padx=6)
        ttk.Button(bar, text="Save", command=self.commit).pack(side="left")
        self.window.bind("<Escape>", lambda _: self.window.destroy())
        self.window.update_idletasks()
        self.window.minsize(460, max(300, body.winfo_reqheight() + 16))

    def commit(self):
        try: save(self.store, [self.available[k] for k, flag in self.selected.items() if flag.get()], self.expected, self.profiles)
        except (OSError, ValueError) as error: self.message.set(str(error)); return
        self.on_save(); self.window.destroy()
