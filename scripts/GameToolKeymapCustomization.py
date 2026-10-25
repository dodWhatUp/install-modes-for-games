"""Portable physical preferences and display styling; never changes emitted inputs."""
from __future__ import annotations
import copy
import re
import unicodedata
from pathlib import Path
import os
import GameToolOverlay as api

VERSION = "0.1.0"
ICONS = ("", "★", "◆", "↑", "↓", "←", "→", "⚔", "🛡", "🎯", "🔫", "💥", "🏃", "🦘", "🔄", "⚙", "📦", "🗺", "💬", "⚠")
KINDS = ("", "Movement", "Combat", "Weapon selection", "Defense", "Interaction", "Menu", "Map", "Utility")
FREQUENCIES = ("", "Frequent", "Sometimes", "Rare")
STYLE_COLORS = ("key_color", "action_color", "background_color", "border_color", "icon_color")


def short(value, limit=80):
    api.require(type(value) is str and len(value) <= limit and
                not any(unicodedata.category(c) == "Cc" for c in value), "Use short single-line text")


def subset(obj, names):
    api.require(type(obj) is dict and set(obj) <= set(names.split()), "Unknown customization field")


def validate_style(style):
    subset(style, " ".join(STYLE_COLORS) + " background_opacity")
    for name in STYLE_COLORS:
        if name in style:
            api.require(type(style[name]) is str and re.fullmatch(r"#[0-9A-Fa-f]{6}", style[name]), "Colors must be #RRGGBB")
    if "background_opacity" in style:
        api.require(type(style["background_opacity"]) is int and 0 <= style["background_opacity"] <= 100,
                    "Background opacity must be 0–100%")


def validate(obj, kind):
    if "key_style" in obj: validate_style(obj["key_style"])
    if kind == "map" and "label" in obj: short(obj["label"], 80)
    if kind == "button" and "ergonomics" in obj:
        e = obj["ergonomics"]
        subset(e, "comfort group action_kind tags notes")
        if "comfort" in e:
            api.require(type(e["comfort"]) is int and 1 <= e["comfort"] <= 5, "Comfort must be 1–5; 5 is easiest")
        for k in ("group", "action_kind", "notes"):
            if k in e: short(e[k], 240 if k == "notes" else 80)
        if "tags" in e:
            api.require(type(e["tags"]) is list and len(e["tags"]) <= 12, "Up to 12 tags")
            for tag in e["tags"]: short(tag, 40)
    if kind == "cell":
        if "icon" in obj: short(obj["icon"], 24)
        if "organization" in obj:
            o = obj["organization"]; subset(o, "category frequency together")
            if "category" in o: short(o["category"], 80)
            if "frequency" in o: api.require(o["frequency"] in FREQUENCIES, "Choose a frequency")
            if "together" in o:
                v = o["together"]
                api.require(type(v) is list and len(v) <= 29 and all(type(b) is int and b in api.R8_POSITIONS for b in v)
                            and len(v) == len(set(v)) and obj["button_id"] not in v, "Select distinct other physical buttons")


def style(document, mapping, cell):
    result = {}
    for obj in (document, mapping, cell): result.update(obj.get("key_style", {}))
    return result


def visual(document, mapping):
    return bool(document.get("key_style") or mapping.get("key_style") or mapping.get("label") or
                any(c.get("key_style") or c.get("icon") for c in mapping["cells"]))


def set_style(document, index, button_id, scope, value):
    """Empty removes only the chosen override, revealing inherited values."""
    import GameToolKeymapDocument as maps
    validate_style(value)
    api.require(scope in {"key", "map", "layer", "all"}, "Choose a style scope")
    candidate = copy.deepcopy(document); mapping = candidate["maps"][index]
    targets = [candidate] if scope == "all" else [m for m in candidate["maps"] if m["layer"] == mapping["layer"]] if scope == "layer" else [mapping] if scope == "map" else [next(c for c in mapping["cells"] if c["button_id"] == button_id)]
    for obj in targets:
        if value: obj["key_style"] = copy.deepcopy(value)
        else: obj.pop("key_style", None)
    return maps.validate(candidate)


def issues(document, mapping):
    """Advisory constraints, not physical reachability or game-action proof."""
    buttons = {b["id"]: b for b in document["buttons"]}
    result = {bid: [] for bid in buttons}
    for cell in mapping["cells"]:
        bid = cell["button_id"]; finger = buttons[bid]["finger"]
        if cell["output"] == "UNASSIGNED": result[bid].append("No emitted input")
        for other in cell.get("organization", {}).get("together", []):
            if finger == buttons[other]["finger"]:
                result[bid].append(f"May conflict with #{other}: same assigned finger")
        if cell.get("organization", {}).get("frequency") == "Frequent" and buttons[bid].get("ergonomics", {}).get("comfort", 5) <= 2:
            result[bid].append("Frequent action on a low-comfort position")
    return result


def ordered_buttons(document):
    def key(b):
        e = b.get("ergonomics", {})
        return (-e.get("comfort", 0), e.get("group", "").casefold(), e.get("action_kind", "").casefold(), b["id"])
    return sorted(document["buttons"], key=key)


def draw_cell(image, document, mapping, cell, button, view, font, key_scale, action_scale):
    from PIL import Image, ImageDraw, ImageFont, ImageColor
    import GameToolKeymapComments as comments
    s = style(document, mapping, cell)
    x, y, width, height = (button[k] for k in ("x", "y", "width", "height"))
    blank = cell["output"] == "UNASSIGNED"
    edge = "#B599F5" if cell["output"].startswith("LAYER:") else "#3D506D" if blank else "#708EB7"
    tile = Image.new("RGBA", image.size); d = ImageDraw.Draw(tile)
    bg = ImageColor.getrgb(s.get("background_color", "#162131" if blank else "#202C40"))
    d.rounded_rectangle((x, y, x+width, y+height), radius=10, fill=(*bg, round(255*s.get("background_opacity", 100)/100)),
                        outline=s.get("border_color", edge), width=2)
    image.alpha_composite(tile); d = ImageDraw.Draw(image)
    icon = cell.get("icon", "")
    show_id = view != "Actions" and height >= 86
    if show_id: d.text((x+8, y+5), f'#{button["id"]}', font=font(15), fill="#AFC4DE")
    if icon:
        candidates = [Path(os.environ.get("WINDIR", "C:/Windows"))/"Fonts/seguiemj.ttf",
                      Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
        compact = height < 86
        iconfont = ImageFont.truetype(str(next(p for p in candidates if p.is_file())), 16 if compact else 21)
        # A bounded icon tile also clips long custom emoji sequences safely.
        glyph = Image.new("RGBA", (20, 24) if compact else (40, 27)); gd = ImageDraw.Draw(glyph)
        gd.text((0, -2), icon, font=iconfont, fill=s.get("icon_color", "#F6C667"))
        image.alpha_composite(glyph, (x+6 if compact else x+width-45, y+4))
    runs, cut, _ = comments.cell_layout(cell, button, view, lambda t, size, bold: d.textlength(t, font=font(size, bold)),
                                       key_scale, action_scale, line_height=lambda size, bold: font(size,bold).getbbox("Agjy")[3]+2,
                                       reserved_top=32 if icon and height >= 86 else None, content_left=30 if icon and height < 86 else 8)
    for run in runs:
        color = s.get(run["role"]+"_color", run["color"])
        d.text((x+run["x"],y+run["y"]), run["text"], font=font(run["size"], run["bold"]), fill=color,
               stroke_width=1, stroke_fill="#0D1522")
    return cut
