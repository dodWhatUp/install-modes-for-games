#!/usr/bin/env python3
"""Build the PoE2 grouped R2 record, native profiles and companion diagrams.

Default: preparation only. --add-to-library creates two new profiles after a
current-state backup; it never replaces or selects an existing profile.
"""
from __future__ import annotations

import argparse
import configparser
import copy
import hashlib
import html
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from generate_azeron_layer_overlays import icon_svg, icon_kind

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "grouped-r2"
REV = "2026-10-12-poe2-grouped-r2"
NAMES = {k: f"PATH OF EXILE 2 - GROUPED R2 {k}" for k in ("COMBAT", "MENU")}
IDS = {k: str(uuid.uuid5(uuid.NAMESPACE_URL, f"azeron-poe2/{REV}/{k}")) for k in NAMES}
SOURCE_IDS = {"COMBAT": "1e29fa38-5c56-4e8f-ae0a-23f32d1279ec", "MENU": "57d3d4da-d6ea-4ebe-9b81-b1dab68ee96b"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def save_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def decode(value: str) -> dict:
    numbers = [int(x) for x in value.split()]
    vk = numbers[0]
    mod = numbers[1] if len(numbers) > 1 else 0
    if vk in (1, 2, 4):
        return {"type": "mouse", "display": {1: "LMB", 4: "MMB", 2: "RMB"}[vk],
                "keys": [], "native_code": {1: "1", 4: "2", 2: "3"}[vk], "raw_encoding": value}
    codes = {9: ("Tab", "Tab"), 13: ("Enter", "Enter"), 16: ("Shift", None),
             17: ("Ctrl", None), 18: ("Alt", None), 32: ("Space", "Space"),
             90: ("Z", "KeyZ"), 222: ("'", "Quote"), 191: ("/", "Slash")}
    if 65 <= vk <= 90:
        label, code = chr(vk), "Key" + chr(vk)
    elif 48 <= vk <= 57:
        label, code = chr(vk), "Digit" + chr(vk)
    elif vk in codes:
        label, code = codes[vk]
    else:
        raise ValueError(f"Unsupported configured input {value!r}; reconcile before building")
    mods = {0: [], 2: ["ControlLeft"]}[mod]
    if code is None:
        mods = [{16: "ShiftLeft", 17: "ControlLeft", 18: "AltLeft"}[vk]]
    return {"type": "keyboard", "display": ("Ctrl+" if mod == 2 else "") + label,
            "keys": ([code] if code else []) + mods, "native_code": code or "0",
            "modifiers": mods, "raw_encoding": value}


def build_record(cfg: configparser.ConfigParser, cfg_hash: str, geometry: list) -> dict:
    record = json.loads((ROOT.parent.parent / "templates/GAME-KEYBINDS.example.json").read_text(encoding="utf-8-sig"))
    record.update(mapping_revision=REV, last_verified=datetime.now(timezone.utc).isoformat(),
                  shared_logical_base_version="PoE2 grouped R2; explicit game-specific ergonomics revision")
    record["game"] = {"name": "Path of Exile 2", "edition": "Steam", "build": "Current saved configuration",
                      "input_mode": "WASD selected; use_wasd_to_move=false remains a runtime uncertainty", "keyboard_layout": "unrecorded"}
    record["device"].update(alias="azeron-cyborg-ii-left", geometry_revision="SHARED R5 numbered Cyborg II geometry",
                           geometry_reference="../KEYBINDS.json", geometry_layout=geometry,
                           recognition_status="Connected HID interface signature matches saved Cyborg II; physical outputs pending",
                           baseline_version="Current user-edited PoE2 R1 pair; preserved separately")
    record["mapper"].update(name="Azeron Software", version="2.0.2", config_name="PoE2 GROUPED R2",
                           config_revision=REV, native_export_reference="native-profiles/", output_mode="software",
                           layers=list(NAMES), slot=None)
    record["azeron"].update(model="Cyborg II", software_version="2.0.2", orientation="left hand", profile_ids=list(IDS.values()))
    record["sources"] = [f"Current poe2_production_Config.ini SHA-256 {cfg_hash}; WASD_ACTION_KEYS read",
                         "Current native PoE2 profiles: #1 single hold MENU and #6 V retained as source observations",
                         "Installed Azeron 2.0.2 renderer enums: KeyboardKey=1, MouseButton=15, SwitchProfile=24; L/M/R=1/2/3",
                         "https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes",
                         "User correction: all builds use one grouped skill layout; class-specific customization unnecessary"]
    record["verification"] = {"configuration": "Generated from saved inputs; native files read back after preparation",
                              "gameplay": "unverified", "gameplay_prompts": "unverified"}
    record["bindings"] = []
    geom = {g["button_id"]: g for g in geometry}
    section = cfg["WASD_ACTION_KEYS"]

    def add(bid: int, layer: str, key: str, name: str, group: str, *, output: dict | None = None) -> None:
        out = output or decode(section[key])
        record["bindings"].append({"button_id": bid, "position_id": geom[bid]["position_id"],
            "device_control_id": bid, "layer": layer, "press_type": "single", "context": "gameplay" if layer == "COMBAT" else "menu",
            "output": out, "action": {"id": key, "name": name, "origin": "game_configured" if output is None else "native_profile"},
            "game_effective_binding": section.get(key), "group": group, "short_name": name,
            "gameplay_prompt": {"expected": out["display"], "observed": None, "status": "unverified"},
            "confidence": "configuration", "notes": "Ability names intentionally remain generic skill-slot labels for all builds." if key.startswith("use_bound") else ""})

    # Three mouse skills, five main keyboard skills, five direct Ctrl chords.
    skill_positions = {1: 8, 2: 7, 3: 5, 4: 12, 5: 11, 6: 10, 7: 9, 8: 13, 9: 17, 10: 16, 11: 15, 12: 38, 13: 18}
    for slot, bid in skill_positions.items():
        add(bid, "COMBAT", f"use_bound_skill{slot}", f"Skill {slot}", "mouse_skills" if slot < 4 else ("main_skills" if slot < 9 else "extra_skills"))
    for bid, key, name in [(4, "use_flask_in_slot1", "Flask 1"), (3, "use_flask_in_slot2", "Flask 2"),
                           (2, "use_temporary_skill1", "Temp skill 1"), (36, "use_temporary_skill2", "Temp skill 2")]:
        add(bid, "COMBAT", key, name, "flasks" if "flask" in key else "temporary")
    add(14, "COMBAT", "use_dodge_roll", "Dodge", "defense")
    add(37, "COMBAT", "weapon_swap", "Weapon swap", "utility")
    add(19, "COMBAT", "highlight", "Hold item labels", "utility")
    for bid, key, name, group in [
        (12, "open_skill_panel", "Skills", "character"), (11, "open_passive_skills_panel", "Passives", "character"),
        (10, "open_character_panel", "Character", "character"), (9, "open_inventory_panel", "Inventory", "character"),
        (13, "open_cosmetics_inventory", "Cosmetics", "character"), (17, "open_map", "Area map", "maps"),
        (16, "open_world_panel", "World / Atlas", "maps"), (15, "open_atlas_passives_screen", "Atlas passives", "maps"),
        (14, "close_panels", "Close panels", "navigation"), (18, "chat", "Chat", "navigation"),
        (2, "open_challenges_panel", "Challenges", "utility"), (36, "open_social_panel", "Social", "utility"),
        (37, "generic_league_panel_key", "League panel", "utility"), (38, "highlight_toggle", "Toggle item labels", "utility"),
        (4, "use_flask_in_slot1", "Flask 1", "flasks"), (3, "use_flask_in_slot2", "Flask 2", "flasks")]:
        add(bid, "MENU", key, name, group)
    for bid, slot in [(8, 1), (7, 2), (5, 3)]:
        add(bid, "MENU", f"use_bound_skill{slot}", {1: "Left click", 2: "Middle click", 3: "Right click"}[slot], "pointer")
    add(19, "MENU", "", "OptiScaler menu", "tools", output={"type": "keyboard", "display": "Home", "keys": ["Home"], "native_code": "Home", "modifiers": []})
    for layer in NAMES:
        for bid, key, name in [(28, "open_map", "Area map"), (29, "open_inventory_panel", "Inventory"),
                               (22, "open_character_panel", "Character"), (31, "open_skill_panel", "Skills"),
                               (30, "open_passive_skills_panel", "Passives"), (41, "chat", "Chat"), (23, "open_cosmetics_inventory", "Cosmetics")]:
            add(bid, layer, key, name, "thumb")
        add(20, layer, "", "Back / Esc", "thumb", output={"type": "keyboard", "display": "Esc", "keys": ["Escape"], "native_code": "Escape", "modifiers": []})
        add(24, layer, "", "Movement", "movement", output={"type": "preserved_analog", "display": "W / A / S / D", "keys": ["KeyW", "KeyA", "KeyS", "KeyD"]})
        target = "MENU" if layer == "COMBAT" else "COMBAT"
        for bid, press, label in [(1, "single_hold", "Hold MENU"), (6, "tap_long_hold", "V TAP" if layer == "COMBAT" else "Hold MENU")]:
            record["bindings"].append({"button_id": bid, "position_id": geom[bid]["position_id"], "layer": layer,
                "press_type": press, "context": "layer", "output": {"type": "layer_selector", "display": label},
                "action": {"id": "momentary_menu", "name": "Release returns to COMBAT", "origin": "user_preference"},
                "short_name": "MENU layer", "group": "layer", "layer_target": target,
                "layer_transition": {"activation": "single hold" if bid == 1 else "long press", "threshold_ms": 0 if bid == 1 else 150,
                                     "release_behavior": "return to COMBAT", "tap_behavior": None if bid == 1 else ("V on short release" if layer == "COMBAT" else None),
                                     "verification": "configured; physical behavior pending"}})
    record["exceptions_to_shared_base"] = ["User requested a grouped PoE2 combat layout for all builds; shared R8 and existing PoE2 profiles preserved.",
        "Skill 12 is at #38 because #14 remains Dodge; all 13 skills occupy the same three adjacent towers.",
        "Shift attack-in-place remains on the external keyboard; no unassigned flask 3/4 buttons occupy the skill block.",
        "#1 retains the user's newer immediate hold-layer shortcut; #6 restores V tap / 150 ms MENU hold using type 24."]
    record["pending_user_actions"] = ["Fully exit Azeron Software after the session, reopen it and select the GROUPED R2 COMBAT profile.",
                                      "Physical layer transitions and gameplay recognition remain unobserved."]
    record["diagrams"].update(geometry_reference="../KEYBINDS.json", source_mapping_revision=REV,
        keys=["combat-keys.svg", "menu-keys.svg"], actions=["combat-actions.svg", "menu-actions.svg"],
        keys_and_actions=["combat-combined.svg", "menu-combined.svg", "combat-icons.png", "menu-icons.png"])
    record["change_log"] = [{"date": "2026-10-12", "change": "Regrouped all 13 skills, paired main/extra keys, grouped flasks and temporary skills, grouped menu categories; native layer enum and mouse labels corrected."}]
    return record


def native_profile(source: dict, record: dict, layer: str) -> dict:
    result = copy.deepcopy(source)
    result.update(id=IDS[layer], name=NAMES[layer], isFavorite=False)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result["metaData"].update(createdAt=now, createdBy="2.0.2", changedLogs=[{"timestampt": now, "softwareVersion": "2.0.2", "type": "created"}])
    entries = {b["button_id"]: b for b in record["bindings"] if b["layer"] == layer}
    for item in result["inputs"]:
        if item["id"] == 24:
            continue
        item["types"] = ["11", "11", "11"]
        for suffix in ("", "Long", "Double"):
            for key, value in [("keyValues", ["0"] * 4), ("metaValues", ["0"] * 3), ("layeringProfileId", ""),
                               ("isBelkin", False), ("isToggleOnHold", False), ("isHold", False), ("holdTime", 0),
                               ("isTurbo", False), ("turboInterval", 0)]:
                item[key + suffix] = value
        for key in ("macro", "longMacro", "doubleMacro"):
            item[key] = {"repeat": False, "steps": [], "v": 1}
        item["sequenceTriggerSettings"] = {"sequenceSteps": [], "isPingPongLoop": False}
        item["label"] = ""
        binding = entries.get(item["id"])
        if not binding:
            continue
        out = binding["output"]
        item["label"] = binding["short_name"] + (f" [{out['display']}]" if out["type"] != "layer_selector" else "")
        if out["type"] == "layer_selector":
            target = IDS["MENU" if layer == "COMBAT" else "COMBAT"]
            if item["id"] == 1:
                item.update(types=["24", "11", "11"], layeringProfileId=target, isToggleOnHold=True, featureDelay=500)
            else:
                item.update(types=["1" if layer == "COMBAT" else "11", "24", "11"], featureDelay=150,
                            layeringProfileIdLong=target, isToggleOnHoldLong=True)
                if layer == "COMBAT":
                    item["keyValues"][0] = "KeyV"
        else:
            item["types"][0] = "15" if out["type"] == "mouse" else "1"
            item["keyValues"][0] = out["native_code"]
            for index, modifier in enumerate(out.get("modifiers", [])):
                item["metaValues"][index] = modifier
    return result


def svg(record: dict, layer: str, view: str) -> str:
    esc = html.escape
    bindings = {b["button_id"]: b for b in record["bindings"] if b["layer"] == layer}
    colors = {"mouse_skills": ("#eeeaff", "#6447aa"), "main_skills": ("#e5f5ef", "#137360"),
              "extra_skills": ("#e8efff", "#3e5fa3"), "flasks": ("#ffebe9", "#ac4545"),
              "temporary": ("#fff3e1", "#93631f"), "defense": ("#ffe9d2", "#ad570c"),
              "layer": ("#f5edff", "#7041a6"), "thumb": ("#edf4f6", "#47717b"),
              "character": ("#e5f5ef", "#137360"), "maps": ("#e8efff", "#3e5fa3")}
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1100" viewBox="0 0 1536 1100">',
             '<rect width="1536" height="1100" fill="#f8fafc"/>',
             '<style>text{font-family:"Segoe UI",Arial,sans-serif}</style>']

    def text(x, y, label, size=15, weight=500, color="#172033"):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}">{esc(str(label))}</text>')

    text(48, 54, f"Path of Exile 2 · GROUPED R2 · {layer}", 29, 750)
    text(48, 84, "Azeron Cyborg II · one layout for every build · " + {"keys": "Keys", "actions": "Actions", "combined": "Keys + actions"}[view], 17)
    text(48, 113, "#6 tap V / hold 150 ms MENU / release COMBAT    ·    #1 immediate hold MENU retained", 16, 650, "#7041a6")
    if layer == "COMBAT":
        parts.append('<rect x="350" y="240" width="443" height="710" rx="17" fill="#f0f2fc" stroke="#7886ae" stroke-width="2"/>')
        text(370, 224, "ALL 13 SKILLS TOGETHER", 20, 750, "#435782")
        text(54, 182, "Four same-row pairs: Q / Ctrl+Q · E / Ctrl+E · R / Ctrl+R · F / Ctrl+F", 16, 650)
        text(54, 208, "T is #9; Ctrl+T is #38. Dodge stays at #14. Both flask keys are adjacent.", 15)
        headers = ["FLASKS / TEMP", "MOUSE SKILLS", "MAIN SKILLS", "EXTRA / DODGE"]
    else:
        text(54, 184, "Character panels together · maps together · all main menus use fingers while #6 is held", 18, 650)
        headers = ["FLASKS / UTILITY", "POINTER", "CHARACTER", "MAPS / NAVIGATE"]
    for col, label in zip(range(2, 6), headers):
        text(66 + (col - 1) * 147 + 5, 279, label, 13, 750, "#435782")
    text(1097, 151, "THUMB SHORTCUTS", 15, 750, "#47717b")
    for g in record["device"]["geometry_layout"]:
        bid = g["button_id"]
        binding = bindings[bid]
        grid = g["grid"]
        x, y = 66 + (grid["column"] - 1) * 147, 162 + (grid["row"] - 2) * 132
        w, h = (282, 252) if bid == 24 else (128, 120)
        fill, stroke = colors.get(binding["group"], ("#f1f4f7", "#69788b"))
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        text(x + 8, y + 19, f"#{bid} · {g['position_id']}", 12, 700, stroke)
        if view != "keys" and bid not in (1, 6):
            kind = "skill" if binding["action"]["id"].startswith(("use_bound_skill", "use_temporary_skill")) else icon_kind(binding["short_name"], binding["output"]["display"], bid)
            parts.append(icon_svg(kind, x + w - 29, y + 29, stroke))
        lines = []
        if view != "actions":
            lines.append((binding["output"]["display"], 15 if bid in (1, 6) else 18, 750))
        if view != "keys":
            label = "Hold MENU" if bid == 6 else binding["short_name"]
            if len(label) > 16:
                import textwrap
                lines.extend((line, 14, 600) for line in textwrap.wrap(label, 16, break_long_words=False))
            else:
                lines.append((label, 15, 650))
        for index, (label, size, weight) in enumerate(lines):
            text(x + 8, y + 48 + index * 22, label, size, weight)
        if bid in (1, 6):
            if bid == 6:
                text(x + 8, y + 89, "150 ms", 11, 600, stroke)
            text(x + 8, y + 108, "Release → COMBAT", 10, 650, stroke)
        if bid == 24:
            text(x + 12, y + 150, "Stick settings preserved", 16, 600)
            text(x + 12, y + 180, "Active movement mode pending", 14, 500)
    parts.append('<rect x="40" y="970" width="1456" height="96" rx="12" fill="#eaf0f6"/>')
    text(58, 996, "R2 files prepared · active selection and physical/game behavior pending", 17, 650)
    text(58, 1021, "Direct chords are single simultaneous key combinations. Mouse outputs retain the game's configured LMB / MMB / RMB inputs.", 14)
    text(58, 1045, "Ctrl also toggles the skill bar in the saved game config. Ability names are generic slots; no class-specific assignments are needed.", 14)
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--add-to-library", action="store_true")
    args = parser.parse_args()
    store = Path(os.environ["APPDATA"]) / "Azeron Software/Storage/DevicesStorage/4855/ProfileStorage"
    source_bytes = {layer: (store / f"profile_{pid}.json").read_bytes() for layer, pid in SOURCE_IDS.items()}
    config_bytes = args.config.read_bytes()
    cfg = configparser.ConfigParser(strict=False)
    cfg.read_string(config_bytes.decode("utf-8-sig"))
    geometry = json.loads((ROOT / "KEYBINDS.json").read_text(encoding="utf-8-sig"))["device"]["geometry_layout"]
    record = build_record(cfg, sha(config_bytes), geometry)
    OUT.mkdir(parents=True, exist_ok=True)
    native = {layer: native_profile(json.loads(data), record, layer) for layer, data in source_bytes.items()}
    for layer in NAMES:
        save_json(OUT / "native-profiles" / (NAMES[layer] + ".json"), native[layer])
        for view in ("keys", "actions", "combined"):
            (OUT / f"{layer.lower()}-{view}.svg").write_text(svg(record, layer, view), encoding="utf-8")
    if args.add_to_library:
        for layer, pid in SOURCE_IDS.items():
            if (store / f"profile_{pid}.json").read_bytes() != source_bytes[layer]:
                raise RuntimeError("Source changed during preparation; refresh before adding profiles")
        for layer in NAMES:
            if (store / f"profile_{IDS[layer]}.json").exists():
                raise RuntimeError("R2 profile already exists; refuse to replace user edits")
        backup_dir = store.parents[3] / "Backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (datetime.now().strftime("Azeron-before-POE2-grouped-R2-%Y%m%d-%H%M%S.zip"))
        payload = {"profiles/" + p.name: p.read_bytes() for p in store.glob("*.json")}
        for p in (store.parent / "GlobalStore.json", store.parents[2] / "GlobalStore.json"):
            if p.is_file():
                payload["device-global.json" if p.parent == store.parent else "app-global.json"] = p.read_bytes()
        manifest = {"coverage": "All current native software profile JSONs and available global JSONs; IndexedDB/onboard hardware not exported",
                    "files": {k: {"size": len(v), "sha256": sha(v)} for k, v in payload.items()}}
        with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in payload.items():
                z.writestr(name, data)
            z.writestr("SNAPSHOT.json", json.dumps(manifest, indent=2))
        for layer in NAMES:
            save_json(store / f"profile_{IDS[layer]}.json", native[layer])
            observed = json.loads((store / f"profile_{IDS[layer]}.json").read_text(encoding="utf-8"))
            if observed != native[layer]:
                raise RuntimeError("Added profile readback differs")
        record["rollback"] = {"backup_reference": backup.name, "steps": ["Fully close Azeron Software, remove only the two GROUPED R2 profile IDs, then reopen.", "Original PoE2/R8 files remain preserved."]}
        record["mapper"]["library_status"] = "Two new profile JSONs added; UI recognition after full reload pending"
        save_json(OUT / "INSTALL-RECEIPT.json", {"revision": REV, "profile_ids": IDS, "profile_names": NAMES,
            "source_profile_sha256": {k: sha(v) for k, v in source_bytes.items()},
            "backup_name": backup.name, "backup_sha256": sha(backup.read_bytes()),
            "library_status": "Added alongside current profiles; active session unchanged", "gameplay": "unverified"})
        print("RECOVERY_BACKUP=" + str(backup))
    save_json(OUT / "KEYBINDS-GROUPED-R2.json", record)
    print(json.dumps({"revision": REV, "profile_names": NAMES, "profile_ids": IDS,
                      "skill_count": 13, "outputs": str(OUT), "added_to_library": args.add_to_library}))


if __name__ == "__main__":
    main()
