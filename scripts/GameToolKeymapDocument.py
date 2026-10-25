"""Editable, portable display documents. Rendering never remaps a device or game.

JSON is the master; PNGs are disposable derivatives consumed by the existing
hash/foreground/layer guarded overlay route. No second trigger or input owner.
"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid
import GameToolOverlay as overlay
import GameToolKeymapComments as comments
import GameToolKeymapCustomization as customization

VERSION = "0.2.5"
BACKGROUNDS = {"opaque": "Whole map opaque", "buttons": "Opaque buttons, clear gaps"}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def fingerprint(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def text(value, limit=240):
    overlay.require(type(value) is str and len(value) <= limit and
                    not any(ord(c) < 32 and c != "\n" for c in value), "Invalid map text")


def validate(value):
    overlay.require(type(value) is dict, "Map document object required")
    overlay.fields({k: v for k, v in value.items() if k not in {"comment", "key_style"}}, "schema_version kind id game_id keymap_id keymap_revision title canvas buttons maps guidance presentation")
    customization.validate(value, "document")
    if "comment" in value: comments.validate(value["comment"])
    overlay.require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["kind"] == "keymap_document", "Unknown map document schema")
    for key in ("id", "game_id", "keymap_id"):
        overlay.token(value[key])
    overlay.digest(value["keymap_revision"]); text(value["title"], 100)
    overlay.require(value["canvas"] == {"width": 1252, "height": 858}, "Use the versioned R8 canvas")
    buttons = value["buttons"]
    overlay.require(type(buttons) is list and len(buttons) == 29, "Exactly 29 visible digital positions required")
    ids = set()
    for b in buttons:
        overlay.fields({k:v for k,v in b.items() if k != "ergonomics"}, "id position finger x y width height guidance")
        customization.validate(b, "button")
        overlay.require(type(b["id"]) is int and b["id"] in overlay.R8_POSITIONS and b["id"] not in ids, "Invalid or duplicate position")
        ids.add(b["id"])
        for k in ("position", "finger", "guidance"):
            text(b[k], 1200)
        for k in ("x", "y", "width", "height"):
            overlay.require(type(b[k]) is int and 0 <= b[k] <= 1252, "Invalid button geometry")
        overlay.require(b["width"] >= 60 and b["height"] >= 60 and b["x"] + b["width"] <= 1252 and
                        b["y"] + b["height"] <= 800, "Button outside map canvas")
    overlay.require(ids == overlay.R8_POSITIONS, "Incomplete physical layout")
    maps = value["maps"]
    overlay.require(type(maps) is list and 1 <= len(maps) <= 32, "Map count limit")
    seen = set()
    for m in maps:
        overlay.fields({k: v for k, v in m.items() if k not in {"comment", "key_style", "label"}}, "layer context cells")
        customization.validate(m, "map")
        if "comment" in m: comments.validate(m["comment"])
        overlay.token(m["layer"]); overlay.token(m["context"])
        pair = (m["layer"], m["context"])
        overlay.require(pair not in seen, "Duplicate layer/context")
        seen.add(pair)
        overlay.require(type(m["cells"]) is list and len(m["cells"]) == 29, "Each map needs 29 cells")
        cell_ids = set()
        for c in m["cells"]:
            overlay.fields({k: v for k, v in c.items() if k not in {"display_key", "comment", "key_style", "icon", "organization"}}, "button_id output action display_action evidence source")
            if "comment" in c: comments.validate(c["comment"], 160)
            if "display_key" in c:
                text(c["display_key"], 80)
            overlay.require(type(c["button_id"]) is int and c["button_id"] in ids and c["button_id"] not in cell_ids, "Invalid map cell")
            cell_ids.add(c["button_id"])
            customization.validate(c, "cell")
            for key, limit in (("output", 80), ("action", 240), ("display_action", 80), ("source", 500)):
                text(c[key], limit)
            overlay.require(c["evidence"] in {"saved_config", "archived_reference", "published_default", "user_label", "native_layer", "unknown", "ai_suggestion"}, "Unknown evidence kind")
    overlay.require(type(value["guidance"]) is list and len(value["guidance"]) <= 64, "Guidance limit")
    for rule in value["guidance"]:
        overlay.fields(rule, "id text evidence source")
        overlay.token(rule["id"])
        for key in ("text", "evidence", "source"):
            text(rule[key], 2400)
    p = value["presentation"]
    overlay.fields(p, "background width_percent")
    overlay.require(type(p["background"]) is str and p["background"] in BACKGROUNDS and type(p["width_percent"]) is int and
                    20 <= p["width_percent"] <= 70, "Map width must be 20–70%")
    overlay.require(len(encoded(value)) <= 512 * 1024, "Map document exceeds the 512 KiB source limit")
    return value


def output_matrix(document):
    return sorted((m["layer"], m["context"], c["button_id"], c["output"]) for m in document["maps"] for c in m["cells"])


def load(path):
    return validate(overlay.decode(overlay.read(path, 512 * 1024)))


def cell_labels(cell):
    output = cell["output"]
    key = cell.get("display_key") or output
    if output.startswith("LAYER:") and not cell.get("display_key"):
        key = "Hold " + output.split(":", 1)[1]
    key = {"UNASSIGNED": "—", "Backspace": "Bksp", "Page Down": "PgDn", "Page Up": "PgUp",
           "Left Arrow": "←", "Right Arrow": "→", "Up Arrow": "↑", "Down Arrow": "↓"}.get(key, key)
    action = cell["display_action"] or cell["action"] or ("Unassigned" if output == "UNASSIGNED" else "Action unknown")
    return key, action


def fit_lines(value, measure, width, limit):
    lines = []
    for word in value.split():
        if not lines or measure(lines[-1] + " " + word) > width:
            lines.append(word)
        else:
            lines[-1] += " " + word
    clipped = len(lines) > limit or any(measure(line) > width for line in lines)
    lines = lines[:limit]
    for index, line in enumerate(lines):
        if measure(line) > width or (clipped and index == len(lines) - 1):
            while line and measure(line + "…") > width:
                line = line[:-1]
            lines[index] = line + "…"
    return lines, clipped


def render(document, mapping, path, view="Combined", appearance=None):
    """Generate a diagram from structured cells; never edit a supplied bitmap."""
    from PIL import Image, ImageDraw, ImageFont
    validate(document)
    overlay.require(view in overlay.VIEWS, "Unknown map view")
    if appearance is not None:
        from GameToolOverlayAppearance import validate_style
        validate_style(appearance)
    action_scale = (appearance or {}).get("action_text_percent", 100) / 100
    key_scale = (appearance or {}).get("key_text_percent", 100) / 100
    if view == "Actions": key_scale = 1
    if view == "Keys": action_scale = 1
    p = document["presentation"]
    image = Image.new("RGBA", (1252, 858), (13, 21, 34, 255) if p["background"] == "opaque" else (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    fontdir = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    def font(size, bold=False):
        candidates = [fontdir / ("segoeuib.ttf" if bold else "segoeui.ttf"),
                      Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
        return ImageFont.truetype(str(next(f for f in candidates if f.is_file())), size)
    def label(x, y, value, size=22, fill="#F2F6FF", bold=False):
        draw.text((x, y), value, font=font(size, bold), fill=fill, stroke_width=1, stroke_fill="#0D1522")
    def role(value, x, y, width, height, requested, bold, limit, color):
        # Constrain each role to its own region. A large action never overwrites
        # a key or a neighbouring button; the source label remains complete.
        size = max(8, min(round(requested), int(height) - 5))
        limit = max(1, min(limit, int(height // (size + 4))))
        lines, clipped = fit_lines(value, lambda text: draw.textlength(text, font=font(size, bold)), width, limit)
        for i, line in enumerate(lines):
            label(x, y + i * (size + 4), line, size, color, bold)
        return clipped
    label(20, 10, document["title"], 30, bold=True)
    subtitle = "key + action" if view == "Combined" else "action + key" if view == "ActionFirst" else view
    label(20, 53, f'{mapping.get("label") or mapping["layer"]}  ·  {subtitle}  ·  {mapping["context"]}', 22, "#BFD3EC")
    header_notes = comments.headers(document, mapping)
    header_size, header_y, header_step = comments.header_style(len(header_notes))
    for i, note in enumerate(header_notes):
        lines, _ = fit_lines(note["text"], lambda t: draw.textlength(t, font=font(header_size)), 1212, 1)
        label(20, header_y + i * header_step, lines[0] if lines else "", header_size, note["color"])
    for x, title in ((174, "LITTLE"), (332, "RING"), (490, "MIDDLE"), (648, "INDEX"), (945, "THUMB / SIDE")):
        label(x, 114, title, 18, "#BFD3EC", True)
    geometry = {b["id"]: b for b in document["buttons"]}
    truncated = []
    for c in mapping["cells"]:
        b = geometry[c["button_id"]]; x, y, width = b["x"], b["y"], b["width"]
        if document.get("key_style") or mapping.get("key_style") or c.get("key_style") or c.get("icon"):
            if customization.draw_cell(image, document, mapping, c, b, view, font, key_scale, action_scale): truncated.append(b["id"])
            continue
        output = c["output"]
        key, action = cell_labels(c)
        layer = output.startswith("LAYER:")
        blank = output == "UNASSIGNED"
        edge = "#B599F5" if layer else "#708EB7" if not blank else "#3D506D"
        draw.rounded_rectangle((x, y, x + width, y + b["height"]), radius=10,
                               fill="#202C40" if not blank else "#162131", outline=edge, width=2)
        if comments.get(c):
            runs, cut, show_id = comments.cell_layout(c, b, view, lambda t, size, bold: draw.textlength(t, font=font(size, bold)), key_scale, action_scale,
                                                    line_height=lambda size, bold: font(size, bold).getbbox("Agjy")[3] + 2)
            if show_id: label(x + 8, y + 5, f'#{b["id"]}', 15, "#AFC4DE")
            for run in runs:
                label(x + run["x"], y + run["y"], run["text"], run["size"], run["color"], run["bold"])
            if cut: truncated.append(b["id"])
            continue
        if view != "Actions":
            label(x + 8, y + 5, f'#{b["id"]}', 15, "#AFC4DE")
        if action_scale != 1 or key_scale != 1:
            top = y + (8 if view == "Actions" else 25)
            available = b["height"] - (top - y) - 8
            clipped = False
            if view in {"Actions", "Keys"}:
                is_action = view == "Actions"
                clipped = role(action if is_action else key, x + 8, top, width - 16, available,
                               24 * (action_scale if is_action else key_scale), True, 2 if is_action else 1, "#F2F6FF")
            else:
                action_first = view == "ActionFirst"
                primary_weight = 48 * action_scale if action_first else 24 * key_scale
                secondary_weight = 17 * key_scale if action_first else 40 * action_scale
                primary_height = (available - 6) * primary_weight / (primary_weight + secondary_weight)
                roles = [(action, 24 * action_scale, True, 2, "#F2F6FF"), (key, 17 * key_scale, False, 1, "#BFD3EC")] if action_first else [(key, 24 * key_scale, True, 1, "#F2F6FF"), (action, 20 * action_scale, False, 2, "#F2F6FF")]
                for (value, size, bold, limit, color), start, height in zip(roles, (top, top + primary_height + 6), (primary_height, available - primary_height - 6)):
                    clipped = role(value, x + 8, start, width - 16, height, size, bold, limit, color) or clipped
            if clipped: truncated.append(b["id"])
            continue
        if view in {"ActionFirst", "Actions"}:
            for size in range(24, 17, -1):
                lines, clipped = fit_lines(action, lambda text: draw.textlength(text, font=font(size, True)), width - 16, 2)
                if not clipped:
                    break
            if clipped:
                truncated.append(b["id"])
            line_height = size + 4
            start = 25 if view == "ActionFirst" else max(8, (b["height"] - len(lines) * line_height) // 2)
            for i, line in enumerate(lines):
                label(x + 8, y + start + i * line_height, line, size, bold=True)
            if view == "ActionFirst":
                for key_size in range(17, 11, -1):
                    key_lines, key_clipped = fit_lines(key, lambda text: draw.textlength(text, font=font(key_size)), width - 16, 1)
                    if not key_clipped:
                        break
                if key_clipped and b["id"] not in truncated:
                    truncated.append(b["id"])
                label(x + 8, y + b["height"] - 25, key_lines[0] if key_lines else "", key_size, "#BFD3EC")
            continue
        keysize = 24 if draw.textlength(key, font=font(24, True)) <= width - 16 else 17
        if view != "Actions":
            label(x + 8, y + (40 if view == "Keys" else 25), key, keysize, bold=True)
        if view == "Keys":
            continue
        lines = []
        for word in action.split():
            if not lines or draw.textlength(lines[-1] + " " + word, font=font(20)) > width - 16:
                lines.append(word)
            else:
                lines[-1] += " " + word
        if len(lines) > 2 or any(draw.textlength(line, font=font(20)) > width - 16 for line in lines):
            truncated.append(b["id"])
            lines = lines[:2]
            while lines and draw.textlength(lines[-1] + "…", font=font(20)) > width - 16:
                lines[-1] = lines[-1][:-1]
            if lines:
                lines[-1] += "…"
        for i, line in enumerate(lines):
            label(x + 8, y + (38 if view == "Actions" else 58) + i * 24, line, 20)
        marker = {"saved_config": "CFG", "archived_reference": "REF", "published_default": "PUB", "user_label": "EDIT", "ai_suggestion": "AI"}.get(c["evidence"])
        if marker:
            label(x + width - 42, y + 5, marker, 12, "#EFC272")
    label(20, 807, "Show: hold #19 or an enabled layer button  ·  hide: release all active show controls", 19, "#BCD0E7")
    label(20, 834, "CFG: saved · REF: archived · PUB: default · EDIT: label · AI: suggestion · Gameplay unverified", 17, "#DEC58E")
    image.save(path, format="PNG", optimize=True)
    return truncated


class Library:
    def __init__(self, directory):
        self.root = overlay.no_links(Path(directory) / "keymap-documents")
        self.store = overlay.Store(directory)

    def path(self, game):
        overlay.token(game)
        return self.root / (game + ".json")

    def current(self, game):
        return load(self.path(game))

    def save(self, document, expected="absent"):
        validate(document)
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.path(document["game_id"]); overlay.no_links(target)
        lock = self.root / "edit.lock"
        with lock.open("xb") as out:
            out.write(b"Keymap document edit\n")
        try:
            old = load(target) if target.exists() else None
            overlay.require((fingerprint(old) if old else "absent") == expected, "Map changed; reload before saving")
            if old:
                history = self.root / "history" / document["game_id"]
                history.mkdir(parents=True, exist_ok=True); overlay.no_links(history)
                backup = history / (fingerprint(old) + ".json")
                if not backup.exists():
                    backup.write_bytes(encoded(old))
            temp = target.with_name(target.name + ".pending-" + uuid.uuid4().hex)
            try:
                with temp.open("xb") as out:
                    out.write(encoded(document)); out.flush(); os.fsync(out.fileno())
                os.replace(temp, target)
            finally:
                if temp.exists():
                    temp.unlink()
            overlay.require(load(target) == document, "Map saved readback mismatch")
            return fingerprint(document)
        finally:
            lock.unlink()

    def apply(self, document, expected_store):
        validate(document)
        baseline = self.current(document["game_id"])
        overlay.require(output_matrix(document) == output_matrix(baseline),
                        "Display editor cannot change emitted keys. Review a native/game binding plan separately.")
        value, current_hash = self.store.load()
        overlay.require(current_hash == expected_store, "Overlay registry changed; reload before applying")
        manifest = copy.deepcopy(value["manifest"])
        keymap = next((k for k in manifest["keymaps"] if k["id"] == document["keymap_id"]), None)
        overlay.require(keymap is not None and keymap["revision"] == document["keymap_revision"], "Native keymap revision changed; reconcile the document")
        groups = [g for g in manifest["groups"] if g["game_id"] == document["game_id"]]
        overlay.require(bool(groups), "Register the game's overlay group first")
        asset_ids = {aid for g in groups for aid in g["asset_ids"]}
        maps = {(m["layer"], m["context"]): m for m in document["maps"]}
        self.root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="render-", dir=self.root) as folder:
            stage = Path(folder); (stage / "images").mkdir()
            truncations = {}
            for asset in manifest["assets"]:
                destination = stage / "images" / (asset["id"] + ".png")
                if asset["id"] in asset_ids:
                    pair = (asset["layer"], asset["context"])
                    overlay.require(pair in maps, "Document is missing a registered layer/context")
                    truncations[asset["id"]] = render(document, maps[pair], destination, asset["view"])
                    asset["sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
                    if asset["view"] != "Keys":
                        asset["evidence"] = "unknown" # Cell-level sources stay in JSON, never promoted to runtime acceptance.
                else:
                    raw, _ = self.store.asset(asset)
                    destination.write_bytes(raw)
                asset["path"] = "images/" + destination.name
            for group in groups:
                group["rendering"].update(size_mode="Screen width %", size_value=document["presentation"]["width_percent"],
                    opacity=100, anchor="Center", offset_x=0, offset_y=0)
            source = stage / "manifest.json"; source.write_bytes(encoded(manifest))
            receipt = self.store.import_manifest(source, expected_store, conflict="replace")
        receipt["truncated_positions"] = truncations
        receipt["native_changes"] = False
        return receipt


def open_editor(panel):
    from GameToolKeymapBuilderUI import Builder
    return Builder(panel)


def open_legacy_editor(panel):
    """Contextual display editor; applying is a separate, explicit user action."""
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    game = panel.selectors["game"].selected_id
    library = Library(panel.store.directory)
    try:
        document = library.current(game)
    except (OSError, ValueError) as error:
        messagebox.showinfo("Editable map", f"No editable source for this game yet. Import a reviewed keymap_document JSON after matching its native outputs.\n{error}", parent=panel.parent)
        return
    saved_hash = fingerprint(document)
    window = tk.Toplevel(panel.parent); window.title("Edit game map — display only"); window.geometry("920x710"); window.minsize(820, 600)
    window.columnconfigure(0, weight=1); window.rowconfigure(3, weight=1)
    ttk.Label(window, text=document["title"], font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=8)
    ttk.Label(window, text="Keys remain owned by Azeron. Save keeps previous maps. Applying changes display only.").grid(row=1, column=0, sticky="w", padx=12)
    controls = ttk.Frame(window); controls.grid(row=2, column=0, sticky="ew", padx=12, pady=8)
    choices = [f'{m["layer"]} / {m["context"]}' for m in document["maps"]]
    selected_map = ttk.Combobox(controls, state="readonly", values=choices, width=25); selected_map.current(0); selected_map.pack(side="left")
    background = ttk.Combobox(controls, state="readonly", values=list(BACKGROUNDS.values()), width=28)
    background.set(BACKGROUNDS[document["presentation"]["background"]]); background.pack(side="left", padx=8)
    ttk.Label(controls, text="Screen width %").pack(side="left")
    width = tk.StringVar(window, value=str(document["presentation"]["width_percent"]))
    ttk.Spinbox(controls, from_=20, to=70, textvariable=width, width=5).pack(side="left", padx=4)
    table = ttk.Treeview(window, columns=("position", "key", "action", "evidence"), show="headings", selectmode="browse")
    for name, size in (("position", 90), ("key", 140), ("action", 400), ("evidence", 130)):
        table.heading(name, text=name.capitalize()); table.column(name, width=size, minwidth=60)
    table.grid(row=3, column=0, sticky="nsew", padx=12)
    scrollbar = ttk.Scrollbar(window, orient="vertical", command=table.yview)
    scrollbar.grid(row=3, column=1, sticky="ns", padx=(0, 6)); table.configure(yscrollcommand=scrollbar.set)
    editor = ttk.Frame(window); editor.grid(row=4, column=0, sticky="ew", padx=12, pady=6); editor.columnconfigure(1, weight=1)
    ttk.Label(editor, text="Action label").grid(row=0, column=0, padx=(0, 8))
    action = tk.StringVar(window); ttk.Entry(editor, textvariable=action).grid(row=0, column=1, sticky="ew")
    note = tk.StringVar(window, value="Select a button to see its position and finger guidance.")
    detail_label = ttk.Label(window, textvariable=note, wraplength=850)
    detail_label.grid(row=5, column=0, sticky="w", padx=12)
    window.bind("<Configure>", lambda e: detail_label.configure(wraplength=max(500, window.winfo_width() - 36)) if e.widget == window else None, add="+")
    def refresh(*_):
        table.delete(*table.get_children())
        for c in document["maps"][selected_map.current()]["cells"]:
            b = next(b for b in document["buttons"] if b["id"] == c["button_id"])
            table.insert("", "end", iid=str(c["button_id"]), values=(f'#{b["id"]} {b["position"]}', c["output"], c["display_action"] or c["action"], c["evidence"]))
        action.set("")
    def select(*_):
        if not table.selection(): return
        bid = int(table.selection()[0]); b = next(b for b in document["buttons"] if b["id"] == bid)
        c = next(c for c in document["maps"][selected_map.current()]["cells"] if c["button_id"] == bid)
        action.set(c["display_action"] or c["action"]); note.set(f'{b["finger"]}: {b["guidance"]}  Actions: {c["action"]}  Source: {c["source"]}')
    def edit():
        if not table.selection(): return
        c = next(c for c in document["maps"][selected_map.current()]["cells"] if c["button_id"] == int(table.selection()[0]))
        text(action.get(), 80); c.update(display_action=action.get(), evidence="user_label", source="User display label; effective game binding unverified")
        refresh()
    ttk.Button(editor, text="Set draft label", command=edit).grid(row=0, column=2, padx=6)
    selected_map.bind("<<ComboboxSelected>>", refresh); table.bind("<<TreeviewSelect>>", select)
    def draft():
        value = copy.deepcopy(document)
        value["presentation"] = {"background": next(k for k,v in BACKGROUNDS.items() if v == background.get()), "width_percent": int(width.get())}
        return validate(value)
    def guarded(callback):
        try: callback()
        except (OSError, ValueError, StopIteration) as error:
            messagebox.showerror("Map operation stopped — review needed", str(error), parent=window)
    def apply():
        nonlocal saved_hash
        value = draft()
        overlay.require(fingerprint(library.current(game)) == saved_hash, "Map source changed; reopen before applying")
        receipt = library.apply(value, panel.fingerprint)
        saved_hash = library.save(value, expected=saved_hash)
        panel.value, panel.fingerprint = panel.store.load()
        panel.fingerprint = panel.store.update("selection", {"game_id": game, "layer": panel.value["preferences"]["selections"][game]["layer"],
            "context": panel.value["preferences"]["selections"][game]["context"], "view": "Combined"}, panel.fingerprint)["sha256"]
        panel.value, panel.fingerprint = panel.store.load(); panel.reload_choices(); panel.tick(reschedule=False)
        note.set("Saved and applied to display. Previous JSON and overlay registry retained. Native/game keys unchanged.")
    def export():
        target = filedialog.asksaveasfilename(parent=window, defaultextension=".json", initialfile=document["id"] + ".json", filetypes=[("Editable map", "*.json")])
        if target: Path(target).write_bytes(encoded(draft()))
    def import_draft(previous=False):
        nonlocal document
        source = filedialog.askopenfilename(parent=window, title="Open previous map as a draft" if previous else "Open JSON as a draft; Save & use is separate",
                    initialdir=str(library.root / "history" / game) if previous else str(library.root), filetypes=[("Editable map", "*.json")])
        if not source: return
        candidate = load(source)
        overlay.require(candidate["game_id"] == game and candidate["keymap_id"] == document["keymap_id"] and
                        output_matrix(candidate) == output_matrix(library.current(game)), "Import must match this game's native output matrix")
        document = candidate
        selected_map.configure(values=[f'{m["layer"]} / {m["context"]}' for m in document["maps"]]); selected_map.current(0)
        background.set(BACKGROUNDS[document["presentation"]["background"]]); width.set(str(document["presentation"]["width_percent"]))
        refresh(); note.set("Imported draft. Review labels, sources and geometry before Save & use.")
    buttons = ttk.Frame(window); buttons.grid(row=6, column=0, sticky="ew", padx=12, pady=10)
    for title, callback in (("Save & use overlay", apply), ("Open JSON draft…", import_draft), ("Previous maps…", lambda: import_draft(True)), ("Export JSON…", export)):
        ttk.Button(buttons, text=title, command=lambda cb=callback: guarded(cb)).pack(side="left", padx=(0, 6))
    guidance = "\n\n".join(f'{r["text"]}\n[{r["evidence"]}; {r["source"]}]' for r in document["guidance"])
    def rules():
        view = tk.Toplevel(window); view.title("Map construction guidance — evidence and limits")
        box = tk.Text(view, wrap="word", width=90, height=24); box.pack(fill="both", expand=True)
        box.insert("1.0", guidance); box.configure(state="disabled")
    ttk.Button(buttons, text="Layout / AI guidance…", command=rules).pack(side="left")
    refresh()

