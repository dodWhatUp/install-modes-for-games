"""Optional display comments and shared bounded text layout. No input owner."""
from __future__ import annotations
import copy
import math
import re
import GameToolOverlay as api

VERSION = "0.1.1"
DEFAULT_COLOR = "#F6C667"
COLORS = {"Amber": DEFAULT_COLOR, "Cyan": "#79DDF2", "Green": "#9FE3B1", "Pink": "#F5A6CF", "Lavender": "#C9B2FF"}


def color(value):
    api.require(type(value) is str, "Choose a comment color or enter #RRGGBB")
    value = COLORS.get(value, value)
    api.require(re.fullmatch(r"#[0-9a-fA-F]{6}", value), "Choose a comment color or enter #RRGGBB")
    return value.upper()


def validate(value, limit=240):
    api.fields(value, "text color")
    api.require(type(value["text"]) is str and len(value["text"]) <= limit and
                not any(ord(c) < 32 for c in value["text"]), "Comment must be one line, up to " + str(limit) + " characters")
    api.require(type(value["color"]) is str and re.fullmatch(r"#[0-9a-fA-F]{6}", value["color"]), "JSON comment color must be #RRGGBB")
    return value


def get(obj):
    value = obj.get("comment")
    return value if value and value["text"].strip() else None


def set_value(obj, text, chosen_color=DEFAULT_COLOR, limit=240):
    """Mutates only the caller's draft. Blank removes an optional comment."""
    api.require(type(text) is str, "Enter comment text")
    if text.strip(): obj["comment"] = validate(dict(text=text.strip(), color=color(chosen_color)), limit)
    else: obj.pop("comment", None)


def set_header(document, map_index, scope, text, chosen_color=DEFAULT_COLOR):
    import GameToolKeymapDocument as maps
    api.require(scope in {"map", "all"}, "Choose this map or all maps of this game")
    api.require(type(map_index) is int and 0 <= map_index < len(document["maps"]), "Select a layer/context map")
    candidate = copy.deepcopy(document)
    set_value(candidate if scope == "all" else candidate["maps"][map_index], text, chosen_color)
    return maps.validate(candidate)


def set_key(document, map_index, button_id, text, chosen_color=DEFAULT_COLOR):
    import GameToolKeymapDocument as maps
    api.require(type(map_index) is int and 0 <= map_index < len(document["maps"]), "Select a layer/context map")
    candidate = copy.deepcopy(document)
    cell = next((c for c in candidate["maps"][map_index]["cells"] if c["button_id"] == button_id), None)
    api.require(cell is not None, "Select a physical key")
    set_value(cell, text, chosen_color, 160)
    return maps.validate(candidate)


def headers(document, mapping):
    return [c for obj in (document, mapping) if (c := get(obj))]


def header_style(count):
    return (12 if count > 1 else 15), 82, 17


def cell_layout(cell, button, view, measure, key_scale=1, action_scale=1, line_height=None, reserved_top=None, content_left=8):
    """Source-pixel runs shared by PIL output and the editable Tk preview."""
    import GameToolKeymapDocument as maps
    note = get(cell)
    key, action = maps.cell_labels(cell)
    width, height = button["width"], button["height"]
    primary = 24 * (action_scale if view in {"Actions", "ActionFirst"} else key_scale)
    line_height = line_height or (lambda size, bold: math.ceil(size * 1.5) + 2)
    note_size = min(12, max(7, round(primary * .5)), max(7, math.floor(height * .12)))
    note_lines, clipped = maps.fit_lines(note["text"], lambda t: measure(t, note_size, False), width - 16, 2 if height >= 140 else 1) if note else ([], False)
    note_height = line_height(note_size, False)
    note_y = height - 8 - len(note_lines) * note_height
    show_id = view != "Actions" and height >= 86
    top = max(25 if show_id else 8, reserved_top or 0)
    available = note_y - 4 - top
    runs = []
    def role(text, y, region, requested, bold, lines, fill, name):
        nonlocal clipped
        size = max(6, round(requested))
        while size > 6 and line_height(size, bold) > region: size -= 1
        step = line_height(size, bold)
        count = max(1, min(lines, math.floor(region / step)))
        fitted, cut = maps.fit_lines(text, lambda t: measure(t, size, bold), width - content_left - 8, count)
        clipped = clipped or cut
        for i, line in enumerate(fitted):
            runs.append(dict(text=line, x=content_left, y=y + i * step, size=size, bold=bold, color=fill, role=name))
    if view in {"Actions", "Keys"}:
        role(action if view == "Actions" else key, top, available, primary, True, 2 if view == "Actions" else 1, "#F2F6FF", "action" if view == "Actions" else "key")
    else:
        action_first = view == "ActionFirst"
        secondary = (17 * key_scale) if action_first else (20 * action_scale)
        gap = 3
        first_height = max(line_height(6, True), min(line_height(max(6,round(primary)), True), available - gap - max(line_height(6,False),min(line_height(max(6,round(secondary)),False),available*.45))))
        second_height = available - first_height - gap
        role(action if action_first else key, top, first_height, primary, True, 1, "#F2F6FF", "action" if action_first else "key")
        role(key if action_first else action, top + first_height + gap, second_height, secondary, False, 1 if action_first else 2,
             "#BFD3EC" if action_first else "#F2F6FF", "key" if action_first else "action")
    for i, line in enumerate(note_lines):
        runs.append(dict(text=line, x=8, y=note_y + i * note_height, size=note_size, bold=False, color=note["color"], role="comment"))
    return runs, clipped, show_id
