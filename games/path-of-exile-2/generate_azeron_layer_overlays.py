#!/usr/bin/env python3
"""Render layer-specific, icon-led Azeron overlays from the POE2 proposal."""

from __future__ import annotations

import html
import json
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROPOSAL_PATH = ROOT / "KEYMAP-PROPOSAL.json"
KEYBINDS_PATH = ROOT / "KEYBINDS.json"
OUT = ROOT / "azeron-keymap" / "overlay"

WIDTH, HEIGHT = 1536, 1100
X0, Y0 = 66, 162
STEP_X, STEP_Y = 147, 132
CARD_W, CARD_H = 128, 120


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: float, y: float, value: str, size: float, weight: int = 500,
         fill: str = "#172033", anchor: str = "start") -> str:
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(value)}</text>')


def wrapped(value: str, limit: int = 16, max_lines: int = 3) -> list[str]:
    parts = textwrap.wrap(value.strip(), width=limit, break_long_words=False,
                          break_on_hyphens=False) or [""]
    if len(parts) > max_lines:
        parts = parts[:max_lines]
        parts[-1] = parts[-1].rstrip(".,;:/-") + "…"
    return parts


def icon_kind(action: str, output: str, button_id: int) -> str:
    value = f"{action} {output}".casefold()
    if button_id == 6 or "layer" in value or "hold menu" in value:
        return "layer"
    if "movement" in value or "move" in value or "w/a/s/d" in value:
        return "movement"
    if "flask" in value:
        return "flask"
    if "temporary skill" in value or "skill slot" in value or "skill panel" in value:
        return "skill"
    if "map" in value:
        return "map"
    if "inventory" in value:
        return "inventory"
    if "character" in value:
        return "character"
    if "passive" in value:
        return "passive"
    if "cosmetic" in value:
        return "cosmetic"
    if "league" in value:
        return "league"
    if "chat" in value:
        return "chat"
    if "dodge" in value:
        return "dodge"
    if "atlas" in value:
        return "atlas"
    if "optiscaler" in value:
        return "settings"
    if "highlight" in value:
        return "highlight"
    if "weapon" in value:
        return "weapon"
    if "modifier" in value or "ctrl" in value or "shift" in value:
        return "modifier"
    if "back" in value or "close" in value or "escape" in value or "esc" in output.casefold():
        return "back"
    return "default"


def icon_svg(kind: str, x: float, y: float, color: str) -> str:
    """Draw small consistent vector glyphs; no external font or emoji required."""
    shapes = {
        "skill": '<path d="M12 2.5 14.5 9l7 .4-5.4 4.4 1.8 6.8L12 16.8l-5.9 3.8 1.8-6.8-5.4-4.4 7-.4z"/>',
        "flask": '<path d="M9 2h6M10 2v6l-5 9.3A3.1 3.1 0 0 0 7.7 22h8.6a3.1 3.1 0 0 0 2.7-4.7L14 8V2M7.4 16h9.2"/>',
        "map": '<path d="m3 5 6-2 6 2 6-2v16l-6 2-6-2-6 2zM9 3v16m6-14v16"/>',
        "inventory": '<path d="M5 8h14l1 13H4L5 8ZM8 8V6a4 4 0 0 1 8 0v2M9 12h6"/>',
        "character": '<circle cx="12" cy="7" r="3.5"/><path d="M4 21a8 8 0 0 1 16 0"/>',
        "passive": '<path d="M12 3v17M5 7l7 4 7-4M5 16l7-5 7 5"/><circle cx="12" cy="3" r="2"/><circle cx="5" cy="7" r="2"/><circle cx="19" cy="7" r="2"/><circle cx="5" cy="16" r="2"/><circle cx="19" cy="16" r="2"/>',
        "cosmetic": '<path d="M3 12c2-5 6-7 9-7s7 2 9 7c-2 5-6 7-9 7s-7-2-9-7Z"/><path d="M8 11h2m4 0h2M9 16h6"/>',
        "league": '<path d="M7 3h10v5a5 5 0 0 1-10 0V3ZM7 5H3v2a5 5 0 0 0 5 5m9-7h4v2a5 5 0 0 1-5 5m-4 1v4m-4 2h8m-10 3h12"/>',
        "chat": '<path d="M4 4h16v13H9l-5 4z"/><circle cx="8" cy="10.5" r=".8"/><circle cx="12" cy="10.5" r=".8"/><circle cx="16" cy="10.5" r=".8"/>',
        "dodge": '<path d="m13 2-9 12h7l-1 8 10-13h-7z"/>',
        "atlas": '<circle cx="12" cy="12" r="9"/><path d="m15.8 8.2-2.5 5.1-5.1 2.5 2.5-5.1z"/>',
        "settings": '<path d="M4 6h16M4 12h16M4 18h16"/><circle cx="9" cy="6" r="2" fill="#fff"/><circle cx="15" cy="12" r="2" fill="#fff"/><circle cx="7" cy="18" r="2" fill="#fff"/>',
        "highlight": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
        "weapon": '<path d="m4 3 13 13m-10 5 4-4M20 4 7 17m10-13 4-1-1 4M3 20l4 1-1-4"/>',
        "movement": '<path d="M5 16a7 4 0 1 0 14 0 7 4 0 1 0-14 0ZM12 15V6m0 0 4 3m-4-3L9 4"/><circle cx="12" cy="5" r="2"/>',
        "modifier": '<rect x="2.5" y="5" width="19" height="14" rx="2"/><path d="M6 9h2m2 0h2m2 0h2m2 0h1M6 12h2m2 0h2m2 0h2M7 15h10"/>',
        "back": '<path d="M20 12H5m0 0 6-6m-6 6 6 6"/>',
        "layer": '<path d="m12 3 9 5-9 5-9-5zM3 12l9 5 9-5M3 16l9 5 9-5"/>',
        "default": '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
    }
    return (f'<g transform="translate({x:.1f},{y:.1f}) scale(.78)" fill="none" '
            f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round">{shapes.get(kind, shapes["default"])}</g>')


def status_label(state: str) -> str:
    labels = {
        "configured": "CFG",
        "saved_and_game_configured": "CFG",
        "saved_and_game_configured_overlap": "OVERLAP",
        "proposed_game_binding": "PROPOSED",
        "saved_output_action_unverified": "KEY ONLY",
        "action_unverified": "ACTION ?",
        "mod_configured_runtime_pending": "MOD PENDING",
        "configured_modifier": "MOD",
        "saved_configured_mode_unverified": "MODE ?",
        "unbound": "UNBOUND",
        "layer": "LAYER",
    }
    return labels.get(state, "UNKNOWN")


def compact_action(action: str) -> str:
    replacements = {
        "Use bound skill slot ": "Use skill slot ",
        "Use flask slot ": "Use flask ",
        "Flask slot 3 is unbound in the current game config": "Flask 3 is unbound in game config",
        "Flask slot 4 is unbound in the current game config": "Flask 4 is unbound in game config",
        "Skill slot 4; Ctrl+Q reaches slot 9": "Skill 4 · Ctrl+Q → Skill 9",
        "Skill slot 5; Ctrl+E reaches slot 10": "Skill 5 · Ctrl+E → Skill 10",
        "Skill slot 6; Ctrl+R reaches slot 11": "Skill 6 · Ctrl+R → Skill 11",
        "Skill slot 8; Ctrl+F reaches slot 13": "Skill 8 · Ctrl+F → Skill 13",
        "Toggle item highlight; Ctrl+Z enables key pickup": "Toggle highlight · Ctrl+Z pickup",
        "Back/close behavior not found in the inspected game config": "Esc output · action not identified",
        "Modifier; also configured as skill-bar toggle": "Ctrl modifier · also toggles skill bar",
        "No matching game action identified": "No matching game action",
    }
    for old, new in replacements.items():
        if action.startswith(old):
            return new + action[len(old):]
    return action


def layer_entries(proposal: dict, layer: str) -> dict[int, dict]:
    entries: dict[int, dict] = {}
    for item in proposal["layers"][layer]:
        entries[int(item["button_id"])] = dict(item)
    for collection in ("shared_thumb_controls", "shared_non_thumb_controls"):
        for item in proposal.get(collection, []):
            entries[int(item["button_id"])] = dict(item)
    return entries


def render_layer(proposal: dict, keybinds: dict, layer: str) -> str:
    entries = layer_entries(proposal, layer)
    geometry = keybinds["device"]["geometry_layout"]
    layer_id = int(proposal["layer_control"]["button_id"])
    thumb_ids = {int(item["button_id"]) for item in proposal.get("shared_thumb_controls", [])}
    subtitle = ("PROPOSAL PREVIEW · NOT INSTALLED · SHARED R5 baseline remains unchanged"
                if proposal.get("status") == "design_only_not_installed" else "PROPOSAL PREVIEW")
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<rect width="100%" height="100%" fill="#f4f7fb"/>',
        '<rect x="22" y="18" width="1492" height="1064" rx="22" fill="#ffffff" stroke="#667085" stroke-width="2"/>',
        '<style>text{font-family:"Segoe UI",Arial,sans-serif}.muted{fill:#536071}</style>',
        text(54, 54, f"Path of Exile 2 · {layer}", 28, 760),
        text(54, 82, "Azeron Cyborg II · COMBAT / MENU profile-pair proposal · revision 2026-10-11-poe2-combat-menu-r1", 15, 550, "#536071"),
        text(54, 108, subtitle, 14, 750, "#8a4b08"),
        '<rect x="52" y="120" width="1428" height="36" rx="10" fill="#f1edff" stroke="#7041a6"/>',
        text(68, 144, "QUICK SWITCH", 12, 800, "#7041a6"),
        text(188, 144, "#6 tap = V · hold 150 ms = MENU · release = COMBAT", 14, 650, "#283044"),
        text(1070, 144, f"VIEW: {layer}", 14, 800, "#7041a6", "end"),
    ]

    for item in geometry:
        bid = int(item["button_id"])
        entry = entries.get(bid)
        grid = item["grid"]
        col, row = int(grid["column"]), int(grid["row"])
        x = X0 + (col - 1) * STEP_X
        y = Y0 + (row - 2) * STEP_Y  # compact the same device geometry without changing positions
        if item.get("kind") == "analog_stick":
            w = STEP_X * int(grid.get("column_span", 2)) - 12
            h = STEP_Y * int(grid.get("row_span", 2)) - 12
        else:
            w, h = CARD_W, CARD_H
        is_thumb = bid in thumb_ids
        is_layer = bid == layer_id
        role = "LAYER" if is_layer else ("THUMB" if is_thumb else ("STICK" if bid == 24 else "FINGER"))
        state = str(entry.get("state", "")) if entry else ""
        action = compact_action(str(entry.get("action", "No action assigned in this proposal"))) if entry else "No action assigned in this proposal"
        output = str(entry.get("output", "—")) if entry else "—"
        if bid == layer_id:
            output = "V TAP · HOLD"
            action = "Hold → MENU · release → COMBAT"
            state = "layer"
        if bid == 24 and entry:
            output = "W / A / S / D"
            action = "Move · confirm active WASD mode"

        if is_layer:
            fill, stroke = "#f0e9ff", "#7041a6"
        elif is_thumb:
            fill, stroke = "#e5f4f0", "#14756c"
        elif state == "proposed_game_binding":
            fill, stroke = "#fff4dd", "#9b6500"
        elif entry:
            fill, stroke = "#eaf2ff", "#336899"
        else:
            fill, stroke = "#f2f4f7", "#9aa4b2"

        elements.append(f'<g><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        elements.append(text(x + 8, y + 17, f"#{bid} · {item.get('position_id', '')}", 10.5, 700))
        elements.append(text(x + w - 8, y + 17, role, 8.5, 800, stroke, "end"))
        if bid == 24:
            elements.append(icon_svg("movement", x + w/2 - 10, y + 27, stroke))
            elements.append(text(x + w/2, y + 64, output, 18, 750, "#172033", "middle"))
            for n, line in enumerate(wrapped(action, 29, 2)):
                elements.append(text(x + w/2, y + 88 + n*15, line, 12, 600, "#536071", "middle"))
            elements.append(text(x + 9, y + h - 9, status_label(state) if entry else "EMPTY", 9, 800, stroke))
            elements.append("</g>")
            continue

        kind = icon_kind(action, output, bid)
        elements.append(icon_svg(kind, x + w - 31, y + 24, stroke))
        output_lines = wrapped(output, 14, 2)
        for n, line in enumerate(output_lines):
            elements.append(text(x + 9, y + 42 + n*15, line, 15, 760, "#172033"))
        action_lines = wrapped(action, 17, 3)
        action_y = y + 65 + (len(output_lines)-1)*12
        for n, line in enumerate(action_lines):
            elements.append(text(x + 9, action_y + n*13, line, 10.5, 560, "#344054"))
        elements.append(text(x + 9, y + h - 8, status_label(state) if entry else "EMPTY", 8.5, 800, stroke))
        elements.append("</g>")

    footer_y = 976
    elements.extend([
        '<rect x="52" y="958" width="1428" height="103" rx="12" fill="#f5f7fa" stroke="#cbd2dc"/>',
        text(70, footer_y, "THUMB MENU KEYS STAY AVAILABLE IN BOTH VIEWS", 12, 800, "#14756c"),
        text(70, footer_y + 23, "Map · Inventory · Character · Skills · Passives · Chat · Cosmetics", 15, 650, "#283044"),
        text(70, footer_y + 47, "PROPOSED = new profile mapping · CFG = present in inspected game config · KEY ONLY / ? = action or runtime still unverified", 12, 600, "#536071"),
        text(70, footer_y + 68, "Configuration preview only: layer behavior, prompts, movement mode, and proposed bindings still need verification before installation.", 11.5, 550, "#536071"),
        "</svg>",
    ])
    return "\n".join(elements)


def main() -> None:
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
    keybinds = json.loads(KEYBINDS_PATH.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    for layer in ("COMBAT", "MENU"):
        path = OUT / f"poe2-proposal-{layer.casefold()}-icons.svg"
        path.write_text(render_layer(proposal, keybinds, layer), encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()
