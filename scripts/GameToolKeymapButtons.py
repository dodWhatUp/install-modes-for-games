"""Associate maps with existing Studio picture slots; never creates a hotkey."""
from __future__ import annotations
import configparser
import copy
import os
from pathlib import Path
import uuid
import GameToolOverlay as overlay
import GameToolKeymapDocument as maps

VERSION = "0.1.0"


def validate(value):
    overlay.fields(value, "schema_version kind links")
    overlay.require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["kind"] == "keymap_button_links", "Unknown button-link schema")
    overlay.require(type(value["links"]) is list and len(value["links"]) <= 128, "Button link limit")
    seen=set()
    for link in value["links"]:
        overlay.fields(link,"slot game_id group_id layer context view")
        overlay.require(type(link["slot"]) is int and 1<=link["slot"]<=12,"Existing picture slot must be 1–12")
        for key in ("game_id","group_id","layer","context"):overlay.token(link[key])
        overlay.require(link["view"] in overlay.VIEWS,"Unknown map view")
        key=(link["slot"],link["game_id"]);overlay.require(key not in seen,"Duplicate game/button link");seen.add(key)
    return value


def read(directory):
    path=Path(directory)/"keymap-button-links.json"
    if not path.exists():return {"schema_version":1,"kind":"keymap_button_links","links":[]},"absent"
    raw=overlay.read(path);return validate(overlay.decode(raw)),overlay.sha(raw)


def save(directory,link,expected,remove=False):
    directory=overlay.no_links(directory);value,current=read(directory)
    overlay.require(current==expected,"Button links changed; reopen the controls")
    value["links"]=[l for l in value["links"] if (l["slot"],l["game_id"])!=(link["slot"],link["game_id"])]
    if not remove:value["links"].append(copy.deepcopy(link))
    validate(value);directory.mkdir(parents=True,exist_ok=True)
    path=overlay.no_links(directory/"keymap-button-links.json")
    if path.exists():
        backup=directory/("keymap-button-links-before-"+current+".json")
        if not backup.exists():maps_raw=overlay.read(path);backup.write_bytes(maps_raw)
    pending=path.with_name(path.name+".pending-"+uuid.uuid4().hex)
    try:
        with pending.open("xb") as out:out.write(maps.encoded(value));out.flush();os.fsync(out.fileno())
        overlay.require(read(directory)[1]==expected,"Button links changed during save")
        os.replace(pending,path)
    finally:
        if pending.exists():pending.unlink()
    return read(directory)


def existing_slots(path=None):
    path=Path(path) if path else Path(os.environ.get("APPDATA",""))/"AzeronOverlayStudio/settings.ini"
    if not path.exists():return []
    raw=overlay.read(path,65536);text=raw.decode("utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig")
    config=configparser.ConfigParser(interpolation=None);config.read_string(text)
    count=min(12,max(1,config.getint("General","SlotCount",fallback=4)))
    return [{"slot":i,"name":config.get(f"Slot{i}","Name",fallback=f"Picture {i}"),"key":config.get(f"Slot{i}","Key",fallback="unconfigured"),
        "enabled":config.get(f"Slot{i}","Enabled",fallback="0")=="1","source":config.get(f"Slot{i}","Source",fallback="Local")} for i in range(1,count+1)]


def relay_data(store,indexed,result,expiry):
    """Only an already-validated game/native selection may publish a fixed guide."""
    settings,_=read(store.directory);active_slots={l["slot"] for l in settings["links"]}
    outputs={slot:{**expiry,"Linked":"0","Active":"0"} for slot in range(1,13)
        if (store.directory/f"overlay-selection-slot-{slot}.ini").exists() or slot in active_slots}
    for link in settings["links"]:
        if link["game_id"]==result.get("game_id"):outputs[link["slot"]].update(Linked="1")
    if not (result.get("render") and result.get("display_target")=="studio" and result.get("foreground_exe")):
        return outputs
    current=indexed["groups"].get(result.get("group_id"))
    for link in settings["links"]:
        if link["game_id"]!=result.get("game_id"):continue
        group=indexed["groups"].get(link["group_id"])
        if not group or not current or group["game_id"]!=link["game_id"] or group["keymap_id"]!=current["keymap_id"]:continue
        asset=next((indexed["assets"][aid] for aid in group["asset_ids"] if all(indexed["assets"][aid][key]==link[key] for key in ("layer","context","view"))),None)
        if not asset:continue
        store.asset(asset)
        data=outputs[link["slot"]]
        data.update(Active="1",File=str((store.directory/asset["path"]).absolute()),SHA256=asset["sha256"],Exe=result["foreground_exe"],
                    FixedGuide="1",Game=link["game_id"],LayerState="Fixed guide selected by picture button")
        data.update({k:str(v) for k,v in group["rendering"].items()})
    return outputs


def open_link_editor(builder):
    import tkinter as tk
    from tkinter import ttk
    from GameToolKeymapBuilder import stable
    slots=existing_slots();overlay.require(bool(slots),"Configure an existing local picture slot in Studio first")
    value,expected=read(builder.panel.store.directory)
    doc=builder.document;mapping=doc["maps"][builder.map_index];group_id=stable("builder-",doc["id"])
    registry,_=builder.panel.store.load();overlay.require(any(g["id"]==group_id for g in registry["manifest"]["groups"]),"Save & use overlays before linking a picture button")
    dialog=tk.Toplevel(builder.window);dialog.title("Link map to an existing picture button")
    body=ttk.Frame(dialog,padding=12);body.pack(fill="both",expand=True)
    ttk.Label(body,text=f'{doc["title"]} · {mapping["layer"]} / {mapping["context"]} · {builder.view.get()}').pack(anchor="w")
    ttk.Label(body,text="A fixed guide for this game. The existing slot's key controls visibility; layer-following remains available when this link is removed.",wraplength=520).pack(anchor="w",pady=8)
    choice=ttk.Combobox(body,state="readonly",width=62,values=[f'Slot {s["slot"]} · {s["key"]} · {s["name"]} · {"enabled" if s["enabled"] else "disabled"}' for s in slots]);choice.current(0);choice.pack(fill="x")
    ttk.Label(body,text="No key or device assignment is created. For another button, configure an unused key and Local picture slot in Azeron/Studio first.",wraplength=520).pack(anchor="w",pady=8)
    def commit(remove=False):
        slot=slots[choice.current()];overlay.require(slot["source"]=="Local","Choose a Local picture slot")
        link={"slot":slot["slot"],"game_id":doc["game_id"],"group_id":group_id,"layer":mapping["layer"],"context":mapping["context"],"view":builder.view.get()}
        save(builder.panel.store.directory,link,expected,remove);builder.panel.tick(reschedule=False);dialog.destroy()
        builder.status.set("Button link removed; automatic layer map restored." if remove else "Fixed guide linked to existing slot. Disabled slots must be enabled in Studio before use.")
    actions=ttk.Frame(body);actions.pack(fill="x")
    ttk.Button(actions,text="Remove this slot/game link",command=lambda:builder.guard(lambda:commit(True))).pack(side="left")
    ttk.Button(actions,text="Save button link",command=lambda:builder.guard(commit)).pack(side="right")
