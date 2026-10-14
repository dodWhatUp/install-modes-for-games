"""Build a private display contract from exact R8 design and fresh native files.
No native modification or inferred active layer. Assets are created by their owner.
"""
from pathlib import Path
import argparse
import hashlib
import json
import GameToolOverlay as api


def build(design_path, profiles_dir, family="SPARSE6", revision="f7511d43956c20ab4280bbcf5e2d0744dd04adf1"):
    design_raw = api.read(design_path)
    design = api.decode(design_raw)
    maps = design["variants"][family]["maps"]
    positions = design["position_map"]
    rows = []
    profiles = sorted(Path(profiles_dir).rglob("profile_*.json"))
    api.require(1 <= len(profiles) <= 128, "Unsupported native inventory")
    for layer in maps:
        matches = []
        for path in profiles:
            raw = api.read(path); profile = api.decode(raw)
            if profile.get("name") == "SHARED R8 " + family + " - " + layer:
                matches.append((profile, raw))
        api.require(len(matches) == 1, "Missing/ambiguous installed layer " + layer)
        profile, raw = matches[0]
        rows.append({"id": layer, "profile_id": profile["id"], "profile_sha256": api.sha(raw)})
    blanks = {layer: sorted(positions[p] for p, key in mapping.items() if key == "UNASSIGNED" and positions[p] != 19)
              for layer, mapping in maps.items()}
    keymap = {"id": "r8-" + family.lower() + "-installed", "label": "Installed R8 " + family,
              "revision": api.sha(api.encode(rows)), "outputs_sha256": api.sha(api.encode(maps)),
              "geometry_sha256": api.sha(api.encode(positions)), "atlas_revision": revision, "family": family,
              "layers": rows, "visible_positions": sorted(p for p in positions.values() if p != 19),
              "hidden_positions": [19], "blank_masks": blanks, "joystick_drawn": False}
    value = api.empty_store()["manifest"]; value["keymaps"] = [keymap]
    api.manifest(value)
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--design", type=Path, required=True)
    p.add_argument("--profiles-directory", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--family", choices=("SPARSE6", "CORE5"), default="SPARSE6")
    args = p.parse_args()
    value = build(args.design, args.profiles_directory, args.family)
    output = api.no_links(args.output)
    with output.open("xb") as out:
        out.write(api.encode(value))
    api.require(api.decode(api.read(output)) == value, "Contract readback mismatch")
    print(json.dumps({"path": str(output), "sha256": api.sha(api.read(output)), "privacy": "private_installed_profile_references",
                      "native_changes": False, "native_active_layer_observed": False}))


if __name__ == "__main__":
    main()
