#!/usr/bin/env python3
"""Build paired Path of Exile 2 Azeron Overlay Studio reference images."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
import re
import textwrap


ROOT = Path(__file__).resolve().parent
PROPOSAL = ROOT / "KEYMAP-PROPOSAL.json"
KEYBINDS = ROOT / "KEYBINDS.json"
OUT = ROOT / "azeron-keymap" / "overlay"

WIDTH, HEIGHT = 1536, 1160
CELL_X, CELL_Y = 147, 132
START_X, START_Y = 66, 150
CARD_W, CARD_H = 128, 120

ICONS = {
    "temp skill": "🧪",
    "flask": "🧴",
    "skill slot": "✨",
    "map": "🗺️",
    "inventory": "🎒",
    "character": "👤",
    "skill panel": "📚",
    "passive": "🌳",
    "cosmetic": "🎭",
    "league panel": "🏟️",
    "league": "🏆",
    "chat": "💬",
    "dodge": "⚡",
    "atlas": "🧭",
    "optiscaler": "🎛️",
    "highlight": "🔦",
    "weapon": "⚔️",
    "movement": "🕹️",
    "modifier": "⌨️",
    "run": "🏃",
    "back": "↩️",
    "layer": "🔀",
    "default": "🎮",
}


def icon_for(action: str) -> str:
    value = action.casefold()
    for needle, icon in ICONS.items():
        if needle in value:
            return icon
    if "hold" in value or "release" in value:
        return ICONS["layer"]
    return ICONS["default"]


def compact_action(action: str) -> str:
    """Shorten known long action names while retaining their meaning."""
    value = action.strip()
    replacements = (
        ("Temporary skill ", "Temp skill "),
        ("Use temporary skill ", "Temp skill "),
        ("Use bound skill slot ", "Skill slot "),
        ("Use flask slot ", "Flask "),
        ("Open map overlay", "Map"),
        ("Open inventory", "Inventory"),
        ("Open character panel", "Character"),
        ("Open skill panel", "Skill panel"),
        ("Open passive skills panel", "Passives"),
        ("Open cosmetics inventory", "Cosmetics"),
        ("Open generic league panel", "League panel"),
        ("Generic league action", "League action"),
        ("Open chat", "Chat"),
        ("Dodge roll", "Dodge"),
        ("Hold to highlight items", "Hold highlight"),
        ("Toggle item highlight", "Toggle highlight"),
        ("Weapon swap", "Weapon swap"),
        ("With Ctrl #5: open Atlas passives screen", "Ctrl+U Atlas"),
        ("OptiScaler menu; static setting exists, runtime input pending", "OptiScaler menu"),
        ("Back/close behavior not found in the inspected game config", "Back/close?"),
        ("Tap: generic league action; hold: enter MENU; release: return COMBAT", "V tap / hold MENU"),
        ("Hold MENU", "Hold MENU"),
        ("Move; input mode fields conflict", "Move W/A/S/D?"),
        ("Modifier; also configured as skill-bar toggle", "Ctrl modifier"),
        ("No matching game action identified", "Modifier"),
    )
    flask_unbound = re.search(r"Flask slot (\d+) is unbound", value, re.I)
    if flask_unbound:
        return f"Flask {flask_unbound.group(1)} unbound"
    skill_chord = re.search(r"Skill slot (\d+); Ctrl\+(\w+) reaches slot (\d+)", value, re.I)
    if skill_chord:
        return f"Skill {skill_chord.group(1)} / Ctrl+{skill_chord.group(2)}→{skill_chord.group(3)}"
    for old, new in replacements:
        if value.startswith(old):
            value = new + value[len(old) :]
            break
    value = value.replace("; Ctrl+", " / Ctrl+").replace(" reaches slot ", "→")
    value = value.replace("With Ctrl #5: ", "Ctrl+U ")
    return value


def wrap(value: str, limit: int = 17, lines: int = 2) -> list[str]:
    value = value.strip()
    if not value or value == "—":
        return ["—"]
    parts = textwrap.wrap(value, width=limit, break_long_words=True, break_on_hyphens=False)
    if len(parts) > lines:
        parts = parts[:lines]
        parts[-1] = parts[-1].rstrip(".,;:/-") + "…"
    return parts or [""]


def action_entry(button: dict, layer: str) -> tuple[str, str, str] | None:
    if button is None:
        return None
    key = str(button.get("output", "—"))
    action = compact_action(str(button.get("action", "—")))
    if key == "—" and action == "—":
        return None
    return key, action, str(button.get("state", ""))


def collect_controls(proposal: dict) -> dict[int, dict[str, tuple[str, str, str]]]:
    controls: dict[int, dict[str, tuple[str, str, str]]] = {}
    for layer in ("COMBAT", "MENU"):
        for item in proposal["layers"][layer]:
            bid = int(item["button_id"])
            entry = action_entry(item, layer)
            if entry:
                controls.setdefault(bid, {})[layer] = entry

    for item in proposal.get("shared_thumb_controls", []):
        bid = int(item["button_id"])
        entry = action_entry(item, "shared")
        if entry:
            controls.setdefault(bid, {})["COMBAT"] = entry
            controls.setdefault(bid, {})["MENU"] = entry

    for item in proposal.get("shared_non_thumb_controls", []):
        bid = int(item["button_id"])
        entry = action_entry(item, "shared")
        if entry:
            controls.setdefault(bid, {}).setdefault("COMBAT", entry)
            controls.setdefault(bid, {}).setdefault("MENU", entry)

    # Keep the tap/hold action readable without repeating V three times.
    controls.setdefault(6, {})["COMBAT"] = ("", "Tap V · hold MENU", "layer")
    controls[6]["MENU"] = ("", "Hold MENU · release to COMBAT", "layer")

    movement = (
        "W/A/S/D",
        "Move W/A/S/D?",
        "saved profile labels stick directions; game movement mode is unresolved",
    )
    controls.setdefault(24, {})["COMBAT"] = movement
    controls[24]["MENU"] = movement
    return controls


def text_element(x: float, y: float, value: str, size: float, weight: int = 500, color: str = "#172033", anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}">{escape(value)}</text>'
    )


def render_svg(proposal: dict, keybinds: dict, with_icons: bool) -> str:
    controls = collect_controls(proposal)
    geometry = keybinds["device"]["geometry_layout"]
    flavor = "Icons + emoji" if with_icons else "Plain"
    title = f"Path of Exile 2 · Azeron Cyborg II · {flavor} keymap"
    subtitle = "COMBAT + MENU · #6: tap V / hold MENU for 150 ms · release returns to COMBAT"
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect x="22" y="18" width="1492" height="1120" rx="24" fill="#ffffff" fill-opacity="0.96" stroke="#667085" stroke-width="3"/>',
        '<style>text{font-family:"Segoe UI Emoji","Segoe UI",Arial,sans-serif}.small{fill:#536071}.card{stroke-width:2}</style>',
        text_element(54, 56, title, 28, 750),
        text_element(54, 84, subtitle, 16, 500, "#536071"),
    ]

    for item in geometry:
        bid = int(item["button_id"])
        position = str(item.get("position_id", ""))
        grid = item["grid"]
        col, row = int(grid["column"]), int(grid["row"])
        x = START_X + (col - 1) * CELL_X
        y = START_Y + (row - 1) * CELL_Y
        span_x = int(grid.get("column_span", 2 if bid == 24 else 1))
        span_y = int(grid.get("row_span", 2 if bid == 24 else 1))
        if bid == 24:
            w = CELL_X * span_x - 12
            h = CELL_Y * span_y - 12
        else:
            w, h = CARD_W, CARD_H

        current = controls.get(bid, {})
        combat = current.get("COMBAT")
        menu = current.get("MENU")
        is_layer = bid == int(proposal["layer_control"]["button_id"])
        is_thumb = any(int(v["button_id"]) == bid for v in proposal.get("shared_thumb_controls", []))
        if is_layer:
            fill, stroke = "#eee4ff", "#7041a6"
        elif is_thumb:
            fill, stroke = "#e2f3ef", "#18746c"
        elif combat and menu:
            fill, stroke = "#fff1d6", "#9a6800"
        elif combat or menu:
            fill, stroke = "#e7f1ff", "#2e6596"
        else:
            fill, stroke = "#f2f3f5", "#9aa1ad"

        elements.append(f'<g><rect class="card" x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}"/>')
        elements.append(text_element(x + 8, y + 18, f"#{bid} · {position}", 11, 700))
        if bid == 24:
            elements.append(text_element(x + w / 2, y + 60, "W / A / S / D", 18, 700, "#172033", "middle"))
            elements.append(text_element(x + w / 2, y + 84, "Move · mode needs confirmation", 12, 600, "#536071", "middle"))
            elements.append(text_element(x + w / 2, y + 104, "Joystick", 11, 650, "#536071", "middle"))
            elements.append("</g>")
            continue

        def draw_layer_line(label: str, entry: tuple[str, str, str] | None, baseline: float, color: str) -> None:
            if entry:
                key, action, _state = entry
                display = f"{key} · {action}" if key and key not in action else action
                emoji = icon_for(action) if with_icons else ""
            else:
                display = "—"
                emoji = ""
            offset = 8
            elements.append(text_element(x + offset, baseline, label, 10, 800, color))
            if emoji:
                elements.append(text_element(x + w - 7, baseline + 2, emoji, 15, 600, "#172033", "end"))
            lines = wrap(display, 12 if emoji else 15)
            tx = x + 27
            for n, line in enumerate(lines):
                elements.append(text_element(tx, baseline + n * 13, line, 10.5, 600, "#172033"))

        draw_layer_line("C", combat, y + 43, "#225e95")
        draw_layer_line("M", menu, y + 78, "#287547")
        if is_layer:
            elements.append(text_element(x + w - 7, y + h - 7, "LAYER", 9, 800, stroke, "end"))
        elif is_thumb:
            elements.append(text_element(x + w - 7, y + h - 7, "THUMB", 9, 800, stroke, "end"))
        elements.append("</g>")

    legend_y = 1080
    elements.append('<rect x="52" y="1057" width="1428" height="62" rx="12" fill="#f5f7fa" stroke="#cbd2dc"/>')
    if with_icons:
        legend = "🧪 Skills/flasks   🗺️ Menus   🕹️ Movement   🔦 Highlight   ⚔️ Weapons   💬 Chat   🎛️ OptiScaler"
    else:
        legend = "C = COMBAT    M = MENU    Mouse buttons 1–3 stay on the mouse    Profile/game prompts not yet verified"
    elements.append(text_element(70, legend_y, legend, 15, 650, "#344054"))
    elements.append("</svg>")
    return "\n".join(elements)


def main() -> None:
    proposal = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    keybinds = json.loads(KEYBINDS.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for name, with_icons in (("poe2-overlay-plain", False), ("poe2-overlay-icons", True)):
        (OUT / f"{name}.svg").write_text(render_svg(proposal, keybinds, with_icons), encoding="utf-8")
    print(f"Wrote paired SVG references to {OUT}")


if __name__ == "__main__":
    main()
