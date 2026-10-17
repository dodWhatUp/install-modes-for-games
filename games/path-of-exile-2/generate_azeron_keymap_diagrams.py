#!/usr/bin/env python3
"""Render three SVG reference views for each layer in KEYBINDS.json."""

from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "KEYBINDS.json"
DEST = ROOT / "azeron-keymap"
WIDTH, HEIGHT = 1120, 900
CELL_X, CELL_Y = 105, 94
START_X, START_Y = 62, 112

LAYERS = {
    "SHARED R5 - BASIC": "basic",
    "SHARED R5 - NUMBERS": "numbers",
    "SHARED R5 - LETTERS": "letters",
    "SHARED R5 - TOOLS": "tools",
}

COLORS = {
    "configured": ("#d9f3e5", "#177245"),
    "layer": ("#eee4ff", "#7041a6"),
    "modifier": ("#e6e7ff", "#4e54a3"),
    "unbound": ("#fff1cc", "#9a6800"),
    "unknown": ("#f0f1f4", "#687080"),
    "unavailable": ("#ffe6e1", "#a94432"),
    "empty": ("#f7f8fa", "#9aa1ad"),
}


def short_action(binding: dict) -> tuple[str, str, str]:
    """Return a compact label, state tag, and color category."""
    output = binding.get("output") or {}
    action = binding.get("action") or {}
    origin = action.get("origin", "unknown")
    output_type = output.get("type", "none")
    output_label = (output.get("display") or "").strip()

    if output_type == "layer_selector":
        name = action.get("name") or "Change layer"
        m = re.search(r"Hold (BASIC|NUMBERS|LETTERS|TOOLS)", name, re.I)
        target = m.group(1).title() if m else "Layer"
        return f"Hold {target}", "LAYER", "layer"
    if output_type == "none" or output_label in {"", "—", "-"}:
        return "Unassigned", "—", "empty"
    if output_label.casefold() in {"ctrl", "shift", "alt"}:
        name = action.get("name") or ""
        if origin == "game_configured" and output_label.casefold() == "ctrl":
            return "Skill bar/chord", "MOD", "modifier"
        if origin == "game_configured" and output_label.casefold() == "alt":
            return "Hold highlight", "MOD", "modifier"
        return "Modifier", "MOD", "modifier"
    if origin == "game_configured_unbound":
        name = action.get("name") or "Unbound in game"
        m = re.search(r"Key (\d+)", name)
        label = f"Key {m.group(1)}; unbound" if m else "Unbound in game"
        return label, "UNBOUND", "unbound"
    if origin == "not_available":
        name = action.get("name") or "Unavailable"
        if "NR" in name:
            return "NR unavailable", "N/A", "unavailable"
        if "ReShade" in name:
            return "ReShade absent", "N/A", "unavailable"
        if "preference" in name.casefold():
            return "Unbound by pref", "N/A", "unavailable"
        if "DLSS" in name:
            return "Shortcut absent", "N/A", "unavailable"
        return "Unavailable", "N/A", "unavailable"
    if origin == "user_preference_unbound":
        return "Unbound by pref", "UNBOUND", "unbound"
    if origin == "unknown":
        return "No game bind", "?", "unknown"

    name = action.get("name") or "Configured action"
    if name.startswith("Move with WASD"):
        return "Move (mode?)", "CFG?", "unbound"
    if name.startswith("Use bound skill slot "):
        main_slot = re.search(r"Use bound skill slot (\d+)", name)
        modifier_slot = re.search(r"Ctrl\+\w reaches slot (\d+)", name)
        main = main_slot.group(1) if main_slot else "?"
        label = f"Skill {main}/{modifier_slot.group(1)}" if modifier_slot else f"Skill {main}"
        return label, "CFG", "configured"
    if name.startswith("Use flask slot "):
        return "Flask " + name.rsplit(" ", 1)[-1], "CFG", "configured"
    if name.startswith("Use temporary skill "):
        return "Temp skill " + name.rsplit(" ", 1)[-1], "CFG", "configured"
    short_names = {
        "Open map overlay": "Map",
        "Open skill panel": "Skills",
        "Open character panel": "Character",
        "Open inventory": "Inventory",
        "Open cosmetics inventory": "Cosmetics",
        "Open passive skills panel": "Passives",
        "Open chat": "Chat",
        "Dodge roll": "Dodge",
        "Toggle item highlight": "Toggle highlight",
        "Hold to highlight items": "Hold highlight",
        "Weapon swap": "Weapon swap",
        "Generic league action": "League action",
        "Open generic league panel": "League panel",
    }
    if name.startswith("With Ctrl"):
        return "Ctrl+U: Atlas", "CFG", "configured"
    if name in short_names:
        return short_names[name], "CFG", "configured"
    return name[:24], "CFG", "configured"


def wrapped(text: str, limit: int = 17) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:3] or [""]


def draw_text(x: float, y: float, lines: list[str], size: int, weight: int = 500) -> str:
    parts = [f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" font-weight="{weight}">']
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else size + 2
        parts.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
    parts.append("</text>")
    return "".join(parts)


def svg_for(layer_name: str, view: str, record: dict) -> str:
    bindings = [b for b in record["bindings"] if b.get("layer") == layer_name]
    by_id = {int(b["button_id"]): b for b in bindings if b.get("button_id") is not None}
    layer_slug = LAYERS[layer_name]
    title = layer_name.replace("SHARED R5 - ", "")
    view_title = {"keys": "Keys", "actions": "Actions", "combined": "Keys + actions"}[view]
    elems = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#172033}.small{fill:#546071}.card{stroke-width:2}</style>',
        f'<text x="44" y="43" font-size="27" font-weight="700">Path of Exile 2 · Azeron Cyborg II · {escape(title)} · {escape(view_title)}</text>',
        '<text x="44" y="75" class="small" font-size="15">SHARED R5 · based on saved Azeron output and local game config · gameplay prompts not verified</text>',
    ]
    geometry = record["device"]["geometry_layout"]
    for item in geometry:
        bid = int(item["button_id"])
        binding = by_id.get(bid, {})
        out = binding.get("output") or {}
        action = binding.get("action") or {}
        key = out.get("display") or "—"
        label, tag, category = short_action(binding) if binding else ("Unassigned", "—", "empty")
        if view == "keys":
            category = "layer" if tag == "LAYER" else ("modifier" if tag == "MOD" else ("empty" if key == "—" else "configured"))
        elif view == "actions" and tag in {"CFG?", "UNBOUND"}:
            category = "unbound"
        fill, stroke = COLORS[category]
        grid = item["grid"]
        col, row = int(grid["column"]), int(grid["row"])
        x = START_X + (col - 1) * CELL_X
        y = START_Y + (row - 1) * CELL_Y
        if item.get("kind") == "analog_stick":
            w = CELL_X * int(grid.get("column_span", 2)) - 12
            h = CELL_Y * int(grid.get("row_span", 2)) - 12
        else:
            w, h = 88, 84
        elems.append(f'<g><rect class="card" x="{x}" y="{y}" width="{w}" height="{h}" rx="11" fill="{fill}" stroke="{stroke}"/>')
        elems.append(f'<text x="{x+8}" y="{y+17}" font-size="11" font-weight="650">#{bid} · {escape(item["position_id"])}</text>')
        cx = x + w / 2
        if view == "keys":
            label_lines = wrapped(key, 14)
            elems.append(draw_text(cx, y + (h / 2) + (len(label_lines)-1)*-8, label_lines, 17, 700))
            if bid == 24:
                tag = "MODE?"
            key_tag = "MODE?" if bid == 24 else (tag if tag in {"LAYER", "MOD"} else ("—" if key == "—" else "KEY"))
            elems.append(f'<text x="{x+w-7}" y="{y+h-6}" text-anchor="end" font-size="10" font-weight="700">{escape(key_tag)}</text>')
        elif view == "actions":
            lines = wrapped(label, 13)
            elems.append(draw_text(cx, y + h / 2 - (len(lines)-1)*7, lines, 13, 650))
            elems.append(f'<text x="{x+w-7}" y="{y+h-6}" text-anchor="end" font-size="10" font-weight="700">{escape(tag)}</text>')
        else:
            key_lines = wrapped(key, 14)
            elems.append(draw_text(cx, y + 34, key_lines[:2], 15, 700))
            action_lines = wrapped(label, 15)
            elems.append(f'<line x1="{x+8}" y1="{y+43}" x2="{x+w-8}" y2="{y+43}" stroke="{stroke}" stroke-opacity=".35"/>')
            elems.append(draw_text(cx, y + 58, action_lines[:2], 11, 600))
            elems.append(f'<text x="{x+w-7}" y="{y+h-4}" text-anchor="end" font-size="9" font-weight="700">{escape(tag)}</text>')
        elems.append("</g>")
    legend_rows = [
        [
            ("KEY", "saved R5 output", "configured"),
            ("CFG", "config-derived, not tested", "configured"),
            ("LAYER", "hold / release BASIC", "layer"),
        ],
        [
            ("MOD", "modifier/chord", "modifier"),
            ("?", "no game bind found", "unknown"),
            ("—", "no output", "empty"),
        ],
    ]
    for row_index, legend in enumerate(legend_rows):
        x = 44
        legend_y = 780 + row_index * 34
        for tag, label, cat in legend:
            fill, stroke = COLORS[cat]
            elems.append(f'<rect x="{x}" y="{legend_y}" width="54" height="27" rx="7" fill="{fill}" stroke="{stroke}"/>')
            elems.append(f'<text x="{x+27}" y="{legend_y+18}" text-anchor="middle" font-size="11" font-weight="700">{escape(tag)}</text>')
            elems.append(f'<text x="{x+61}" y="{legend_y+18}" class="small" font-size="12">{escape(label)}</text>')
            x += 54 + 10 + (len(label) * 5.5) + 24
    elems.append('<text x="44" y="862" class="small" font-size="13">Stick #24 is labeled W/A/S/D in the saved profile. The config has conflicting WASD mode fields; confirm movement in a normal game session.</text>')
    elems.append("</svg>")
    return "\n".join(elems)


def skill_overview_svg(record: dict) -> str:
    """Render every configured active skill slot and both temporary skill keys."""
    slots: dict[int, tuple[str, str]] = {}
    basic = [b for b in record["bindings"] if b.get("layer") == "SHARED R5 - BASIC"]
    key_to_button = {
        (b.get("output") or {}).get("display", ""): b.get("button_id")
        for b in basic
    }
    for external in record.get("external_mouse_bindings", []):
        match = re.search(r"skill\.slot(\d+)", (external.get("action") or {}).get("id", ""))
        if match:
            slot = int(match.group(1))
            slots[slot] = (external.get("device_control_id", "Mouse"), "External mouse binding")
    for binding in basic:
        name = (binding.get("action") or {}).get("name", "")
        output = (binding.get("output") or {}).get("display", "")
        button = binding.get("button_id")
        main_slot = re.search(r"Use bound skill slot (\d+)", name)
        if main_slot:
            n = int(main_slot.group(1))
            slots[n] = (output, f"BASIC · key {output} · Azeron #{button}")
        modifier_slot = re.search(r"Ctrl\+(\w+) reaches slot (\d+)", name)
        if modifier_slot:
            key, target = modifier_slot.group(1), int(modifier_slot.group(2))
            base_button = key_to_button.get(key, "?")
            slots[target] = (f"Ctrl+{key}", f"BASIC + Ctrl · #5 + #{base_button}")

    width, height = 1200, 690
    card_w, card_h = 340, 66
    xs = [50, 430, 810]
    top = 120
    elems = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#172033}.muted{fill:#586579}</style>',
        '<text x="50" y="48" font-size="28" font-weight="700">Path of Exile 2 · All configured skill slots</text>',
        '<text x="50" y="78" class="muted" font-size="15">Slot bindings from the local config · actual socketed skill names are not stored there · gameplay prompts not verified</text>',
    ]
    for slot in range(1, 14):
        col, row = (slot - 1) % 3, (slot - 1) // 3
        x, y = xs[col], top + row * 76
        key, detail = slots.get(slot, ("Unmapped", "No binding recorded"))
        fill = "#e5f3eb" if slot <= 8 else "#eee8ff"
        stroke = "#26734d" if slot <= 8 else "#7041a6"
        elems.append(f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elems.append(f'<text x="{x+16}" y="{y+25}" font-size="17" font-weight="700">Slot {slot}</text>')
        elems.append(f'<text x="{x+120}" y="{y+25}" font-size="17" font-weight="700">{escape(key)}</text>')
        elems.append(f'<text x="{x+16}" y="{y+49}" class="muted" font-size="13">{escape(detail)}</text>')
    elems.append('<text x="50" y="528" font-size="19" font-weight="700">Temporary skill keys on NUMBERS layer</text>')
    temporary = []
    for binding in record["bindings"]:
        if binding.get("layer") != "SHARED R5 - NUMBERS":
            continue
        name = (binding.get("action") or {}).get("name", "")
        match = re.search(r"Use temporary skill (\d+)", name)
        if match:
            temporary.append((int(match.group(1)), binding))
    for index, (number, binding) in enumerate(sorted(temporary)):
        x = 50 + index * 380
        key = (binding.get("output") or {}).get("display", "")
        button = binding.get("button_id")
        y = 548
        elems.append(f'<rect x="{x}" y="{y}" width="340" height="60" rx="11" fill="#fff2d6" stroke="#9a6800" stroke-width="2"/>')
        elems.append(f'<text x="{x+16}" y="{y+24}" font-size="16" font-weight="700">Temporary skill {number} · key {key}</text>')
        elems.append(f'<text x="{x+16}" y="{y+46}" class="muted" font-size="13">Hold #2 for NUMBERS · Azeron #{button}</text>')
    elems.append('<text x="50" y="648" class="muted" font-size="14">NUMBERS is a hold layer; it does not contain the main skill slots 1–13. Ctrl is also configured as a skill-bar toggle, so confirm Ctrl behavior in game.</text>')
    elems.append("</svg>")
    return "\n".join(elems)


def main() -> None:
    record = json.loads(SOURCE.read_text(encoding="utf-8"))
    DEST.mkdir(parents=True, exist_ok=True)
    for layer_name, slug in LAYERS.items():
        for view in ("keys", "actions", "combined"):
            output = DEST / f"{slug}-{view}.svg"
            output.write_text(svg_for(layer_name, view, record), encoding="utf-8")
    (DEST / "skill-slots.svg").write_text(skill_overview_svg(record), encoding="utf-8")
    print(f"Rendered 13 SVG diagrams in {DEST}")


if __name__ == "__main__":
    main()
