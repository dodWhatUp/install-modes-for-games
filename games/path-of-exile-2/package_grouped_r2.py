"""Add the grouped R2 artifacts to the existing single delivery ZIP."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime

ROOT = Path(__file__).resolve().parent
R2 = ROOT / "grouped-r2"
ARCHIVE = ROOT / "POE2-Azeron-Keymap-and-Overlays-2026-10-12.zip"
sha = lambda data: hashlib.sha256(data).hexdigest().upper()
record = json.loads((R2 / "KEYBINDS-GROUPED-R2.json").read_text(encoding="utf-8"))
receipt = json.loads((R2 / "INSTALL-RECEIPT.json").read_text(encoding="utf-8"))
store = Path(os.environ["APPDATA"]) / "Azeron Software/Storage/DevicesStorage/4855/ProfileStorage"
backup = store.parents[3] / "Backups" / receipt["backup_name"]
with zipfile.ZipFile(backup) as z:
    snapshot = json.loads(z.read("SNAPSHOT.json"))
    for name, metadata in snapshot["files"].items():
        data = z.read(name)
        if sha(data) != metadata["sha256"]:
            raise RuntimeError("Recovery archive identity mismatch")
        if name.startswith("profiles/") and (store / Path(name).name).read_bytes() != data:
            raise RuntimeError("Earlier native profile changed since snapshot; reconcile before declaring preservation")

views = []
for layer in ("COMBAT", "MENU"):
    pid = receipt["profile_ids"][layer]
    native_file = R2 / "native-profiles" / (receipt["profile_names"][layer] + ".json")
    if native_file.read_bytes() != (store / f"profile_{pid}.json").read_bytes():
        raise RuntimeError("Export differs from added native file")
    image = R2 / (layer.lower() + "-icons.png")
    views.append({"layer": layer, "profile_id": pid, "profile_name": receipt["profile_names"][layer],
                  "profile_file": "native-profiles/" + native_file.name,
                  "profile_sha256": sha(native_file.read_bytes()), "png": image.name,
                  "png_sha256": sha(image.read_bytes()), "svg": layer.lower() + "-combined.svg"})
handoff = {"schema_version": 1, "kind": "poe2_overlay_handoff", "mapping_revision": record["mapping_revision"],
           "status": "Native library files added; UI recognition/active layer/gameplay/host integration pending",
           "game_executable": "PathOfExileSteam.exe", "source_record": "KEYBINDS-GROUPED-R2.json",
           "source_record_sha256": sha((R2 / "KEYBINDS-GROUPED-R2.json").read_bytes()), "views": views,
           "layer_controls": {"primary": {"button_id": 6, "tap": "V", "hold_ms": 150, "hold": "MENU", "release": "COMBAT"},
                              "alternative": {"button_id": 1, "hold": "MENU", "release": "COMBAT"}},
           "integration_boundary": "Descriptive handoff only. Not a validated/imported Hub overlay_manifest; joystick is drawn and all current native positions are shown."}
(R2 / "overlay-handoff.json").write_text(json.dumps(handoff, indent=2) + "\n", encoding="utf-8")
proposal_path = ROOT / "KEYMAP-PROPOSAL.json"
proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
proposal["status"] = "historical_r1_pair_user_reported_visible_after_full_task_manager_exit"
proposal["latest_revision_reference"] = "grouped-r2/KEYBINDS-GROUPED-R2.json"
proposal["implementation_boundary"] = "User confirmed R1 pair visible after ending Azeron Software through Task Manager. Current R1 edits are preserved in the R2 recovery snapshot. See grouped R2 for the requested ergonomic revision."
proposal["implementation"]["status"] = "R1 UI visibility user-confirmed; current user edits preserved; physical/game behavior unverified."
proposal["implementation"]["not_verified"] = ["on-device layer transition", "gameplay prompts and action behavior"]
proposal_path.write_text(json.dumps(proposal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

archive_backup = store.parents[3] / "Backups" / datetime.now().strftime("POE2-bundle-before-grouped-R2-%Y%m%d-%H%M%S.zip")
shutil.copy2(ARCHIVE, archive_backup)
with zipfile.ZipFile(ARCHIVE) as z:
    payload = {name: z.read(name) for name in z.namelist() if not name.endswith("/")}
prefix = "POE2-Azeron-Keymap-and-Overlays-2026-10-12/"
payload.pop(prefix + "MANIFEST-SHA256.txt", None)
for folder in ("07-Grouped-R2/",):
    for name in list(payload):
        if name.startswith(prefix + folder):
            del payload[name]
for filename in ("KEYMAP.md", "KEYMAP-PROPOSAL.json", "HISTORY.md", "OVERLAY-NAVIGATION.md"):
    data = (ROOT / filename).read_bytes()
    if filename.endswith(".md"):
        data = data.decode("utf-8").replace("grouped-r2/", "../07-Grouped-R2/").encode("utf-8")
    payload[prefix + "01-Mapping/" + filename] = data
payload[prefix + "01-Mapping/azeron-profile-pair/README.md"] = (ROOT / "azeron-profile-pair/README.md").read_bytes()
for path in R2.rglob("*"):
    if path.is_file():
        payload[prefix + "07-Grouped-R2/" + path.relative_to(R2).as_posix()] = path.read_bytes()
payload[prefix + "04-Source-Generators/build_grouped_r2.py"] = (ROOT / "build_grouped_r2.py").read_bytes()
payload[prefix + "04-Source-Generators/package_grouped_r2.py"] = Path(__file__).read_bytes()
payload[prefix + "00-START-HERE.md"] = b"""# Path of Exile 2 - Azeron keymap and overlays

## Latest: GROUPED R2

Open **07-Grouped-R2/README.md**. This revision groups all 13 skills together,
puts both flasks next to each other, and groups the finger-only MENU panels.
The native profiles are in **07-Grouped-R2/native-profiles/**; pictures and the
authoritative mapping record are beside the guide.

Two GROUPED R2 profiles were added alongside the existing native profiles.
After the current session, fully exit/reopen Azeron Software and select
**PATH OF EXILE 2 - GROUPED R2 COMBAT**. The user previously confirmed a full
Task Manager exit resolved visibility. Active R2 selection and physical/game
acceptance remain pending. The current game session was not changed.

Earlier sections 01-06 retain historical mapping/reference files and R1 exports.
Use the R2 files together; earlier pictures describe different mappings.
Overlay-host activation remains a separate integration step.
"""
payload[prefix + "05-Status/STATUS.md"] = b"""# Current status - GROUPED R2

- All 13 skill inputs grouped across three adjacent towers; flasks adjacent.
- Character menus and map/navigation menus grouped on separate finger towers.
- Two new native profile JSONs added to the local Azeron library; old files
  preserved against the current 31-profile recovery snapshot.
- #1 immediate hold MENU retained; #6 V tap / 150 ms MENU hold encoded using
  native type 24 with reciprocal targets.
- Native file readback and rendered diagrams inspected. Active selection,
  physical outputs, game prompts and Ctrl interactions remain unobserved.
- Earlier R1 pair visibility was user-confirmed after a full Task Manager exit.
- Overlay PNGs and descriptive handoff prepared; host integration pending.
- Recovery snapshot is separate from this delivery/source ZIP.
"""
manifest = "\n".join(f"{sha(data)}  {name[len(prefix):]}" for name, data in sorted(payload.items())) + "\n"
payload[prefix + "MANIFEST-SHA256.txt"] = manifest.encode("utf-8")
temp = ARCHIVE.with_name(ARCHIVE.name + ".grouped-r2.tmp")
with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in sorted(payload.items()):
        z.writestr(name, data)
with zipfile.ZipFile(temp) as z:
    for name, data in payload.items():
        if z.read(name) != data:
            raise RuntimeError("Delivery archive readback differs")
temp.replace(ARCHIVE)
print(json.dumps({"archive": str(ARCHIVE), "size": ARCHIVE.stat().st_size,
                  "sha256": sha(ARCHIVE.read_bytes()), "members": len(payload),
                  "original_profiles_preserved": 31, "new_profiles": 2, "recovery_backup": str(backup)}))
