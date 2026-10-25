"""Optional other-application map preference; the existing Studio slot owns input."""
from __future__ import annotations
import os
from pathlib import Path
import tempfile
import GameToolOverlay as api

VERSION = "0.1.0"


def read(directory):
    path=api.no_links(Path(directory)/"overlay-fallback.json")
    raw=api.read(path,16384) if path.exists() else None
    if raw is None: return {"group_id":None},raw
    value=api.decode(raw);api.fields(value,"schema_version kind group_id")
    api.require(type(value["schema_version"]) is int and value["schema_version"]==1 and value["kind"]=="overlay_fallback","Unsupported other-application overlay settings")
    if value["group_id"] is not None:api.token(value["group_id"])
    return {"group_id":value["group_id"]},raw


def save(store,group_id,expected):
    if group_id is not None:api.token(group_id)
    value,registry=store.load();index=api.validate_store(value)
    api.require(group_id is None or group_id in index["groups"],"Fallback group missing; reopen the controls")
    directory=api.no_links(store.directory);directory.mkdir(parents=True,exist_ok=True)
    lock=api.no_links(directory/"overlay-fallback.lock");temp=None
    try:
        fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError as error:
        raise api.OverlayError("Other-application settings busy; inspect the owner before retrying") from error
    try:
        os.close(fd);_,current=read(directory)
        api.require(current==expected,"Other-application settings changed; reopen the controls")
        if current is not None:
            backup=api.no_links(directory/("overlay-fallback-before-"+api.sha(current)+".json"))
            if backup.exists():api.require(api.read(backup,16384)==current,"Fallback recovery copy differs")
            else:
                with backup.open("xb") as out:out.write(current);out.flush();os.fsync(out.fileno())
        raw=api.encode({"schema_version":1,"kind":"overlay_fallback","group_id":group_id})
        fd,name=tempfile.mkstemp(prefix="fallback-",dir=directory);temp=Path(name)
        with os.fdopen(fd,"wb") as out:out.write(raw);out.flush();os.fsync(out.fileno())
        api.require(read(directory)[1]==expected and store.load()[1]==registry,"Overlay settings changed while saving; reopen the controls")
        os.replace(temp,directory/"overlay-fallback.json");temp=None
        api.require(read(directory)[1]==raw,"Fallback settings readback differs")
        return read(directory)
    finally:
        if temp is not None and temp.exists():temp.unlink()
        lock.unlink()


class FallbackEditor:
    def __init__(self,parent,store,on_save=lambda:None):
        import tkinter as tk
        from tkinter import ttk
        from GameToolCompactUI import Selector
        self.store,self.on_save=store,on_save
        selected,self.expected=read(store.directory)
        value,_=store.load();index=api.validate_store(value)
        self.window=tk.Toplevel(parent);self.window.title("Overlay in other applications")
        body=ttk.Frame(self.window,padding=16);body.pack(fill="both",expand=True)
        body.columnconfigure(0,weight=1)
        ttk.Label(body,text="Map outside associated games").grid(row=0,column=0,sticky="w")
        self.group=Selector(body,on_select=lambda _:None)
        self.group.grid(row=1,column=0,sticky="ew",pady=(6,10))
        choices=[("__off__","Off — associated applications only")]
        choices += [(g["id"],index["games"][g["game_id"]]["label"]+" / "+g["label"]) for g in index["groups"].values()]
        self.group.set_choices(choices)
        self.group.select(selected["group_id"] or "__off__")
        ttk.Label(body,text="Games with a saved association keep their own maps.\nYour existing picture button still controls show/hide.\nUses Studio trigger instead; no key or profile changes.",wraplength=450).grid(row=2,column=0,sticky="w")
        self.message=tk.StringVar(self.window)
        ttk.Label(body,textvariable=self.message,wraplength=450).grid(row=3,column=0,sticky="w",pady=8)
        bar=ttk.Frame(body);bar.grid(row=4,column=0,sticky="e")
        ttk.Button(bar,text="Cancel",command=self.window.destroy).pack(side="left",padx=6)
        ttk.Button(bar,text="Save",command=self.commit).pack(side="left")
        self.window.bind("<Escape>",lambda _:self.window.destroy())
        self.window.minsize(460,250)

    def commit(self):
        try:
            self.group.commit()
            api.require(self.group.variable.get()==self.group.committed,"Select an existing map group or Off; search text is not a saved choice")
            group=self.group.selected_id
            api.require(group is not None,"Choose Off or an existing map group")
            save(self.store,None if group=="__off__" else group,self.expected)
        except (OSError,ValueError) as error:
            self.message.set(str(error));return
        self.on_save();self.window.destroy()
