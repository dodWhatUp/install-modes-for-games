"""Optional display-only Hub overlay page. No hotkeys or arbitrary command runner."""
from __future__ import annotations
import copy
import ctypes
import io
import json
import os
from pathlib import Path
import time
import uuid
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import GameToolOverlay as api
from GameToolAzeronLayer import installed_follower
from GameToolCompactUI import Selector, VisibilityMenu

VERSION = "0.2.0"


def monitors(root):
    if os.name != "nt":
        return [(0, 0, root.winfo_screenwidth(), root.winfo_screenheight())]
    user = ctypes.WinDLL("user32")
    values = []
    class Rect(ctypes.Structure):
        _fields_ = [(n, ctypes.c_long) for n in ("left", "top", "right", "bottom")]
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(Rect), ctypes.c_ssize_t)
    def receive(handle, dc, rect, data):
        r = rect.contents
        values.append((r.left, r.top, r.right - r.left, r.bottom - r.top)); return 1
    callback = callback_type(receive)
    user.EnumDisplayMonitors(None, None, callback, 0)
    return values


class Renderer:
    """Only its own windows. Passive window has NOACTIVATE + click-through.

    Explore is explicit and pinned, never interpreted as foreground game state.
    Peek uses the UI's held button (or an existing AHK Hold slot via relay).
    No global keyboard shortcut is registered.
    """
    def __init__(self, parent, store):
        self.parent, self.store = parent, store
        self.passive = None; self.explore = None; self.key = None; self.photo = None

    def hide(self):
        if self.passive is not None:
            self.passive.destroy(); self.passive = None
        self.key = None; self.photo = None

    def show(self, result, pinned=False):
        from PIL import Image, ImageTk
        value, _ = self.store.load(); index = api.validate_store(value)
        asset = index["assets"].get(result.get("asset_id"))
        api.require(asset is not None, "No exact selected asset to display")
        raw, info = self.store.asset(asset)
        group = index["groups"][result["group_id"]]
        key = (asset["sha256"], json.dumps(group["rendering"], sort_keys=True))
        if not pinned and self.passive is not None and self.key == key:
            return
        if not pinned:
            self.hide()
        screen = monitors(self.parent)
        api.require(1 <= group["rendering"]["monitor"] <= len(screen), "Selected monitor unavailable")
        x, y, w, h = api.geometry(group["rendering"], info["width"], info["height"], screen[group["rendering"]["monitor"] - 1])
        window = tk.Toplevel(self.parent); window.withdraw()
        try:
            photo = ImageTk.PhotoImage(Image.open(io.BytesIO(raw)).resize((w, h)), master=window)
            if pinned:
                if self.explore:
                    self.explore.destroy()
                window.title("Explore — pinned selected snapshot (not live native observation)")
                ttk.Label(window, text="Pinned Explore • close to return • native/game bindings unchanged").pack(fill="x")
                ttk.Label(window, image=photo).pack(fill="both", expand=True)
                window.photo = photo
                window.geometry(f"+{x}+{y}")
                self.explore = window; window.deiconify()
            else:
                window.overrideredirect(True)
                tk.Label(window, image=photo, bd=0, highlightthickness=0).pack()
                window.geometry(f"{w}x{h}{x:+d}{y:+d}")
                window.attributes("-alpha", group["rendering"]["opacity"] / 100)
                window.update_idletasks()
                if os.name == "nt":
                    user = ctypes.WinDLL("user32", use_last_error=True)
                    user.GetParent.argtypes = [ctypes.c_void_p]; user.GetParent.restype = ctypes.c_void_p
                    hwnd = user.GetParent(window.winfo_id()) or window.winfo_id()
                    user.GetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int]
                    user.SetWindowLongW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
                    style = user.GetWindowLongW(hwnd, -20)
                    user.SetWindowLongW(hwnd, -20, style | 0x08000000 | 0x20 | 0x80)
                    user.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
                    user.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
                    window.deiconify()  # NOACTIVATE is already set before mapping.
                    user.ShowWindow(hwnd, 4)
                    user.SetWindowPos(hwnd, ctypes.c_void_p(-1), x, y, w, h, 0x10 | 0x40)
                else:
                    # No claim of a supported passive window outside Windows.
                    raise api.OverlayError("Passive rendering requires Windows; Explore remains available")
                self.passive, self.photo, self.key = window, photo, key
        except Exception:
            window.destroy(); raise

    def close(self):
        self.hide()
        if self.explore is not None:
            self.explore.destroy(); self.explore = None


class OverlayPanel:
    def __init__(self, parent, directory, status=None, foreground=api.foreground_windows, renderer_factory=Renderer,
                 layer_factory=installed_follower):
        self.parent, self.store = parent, api.Store(directory)
        self.status_callback = status.set if hasattr(status, "set") else status or (lambda _: None)
        self.foreground = foreground; self.closed = False; self.timer = None
        self.renderer = renderer_factory(parent, self.store)
        self.layer_follower = layer_factory()
        self.follow_layer = tk.BooleanVar(parent, value=True)
        self.result = None; self.peek_held = False; self.last_game_result = None
        self.note = tk.StringVar(parent, value="Stopped • no native layer telemetry • explicit layer selection available")
        self.path = tk.StringVar(parent)
        self.value, self.fingerprint = self.store.load()
        self.enabled = tk.BooleanVar(parent, value=self.value["preferences"]["enabled"])
        self.display = tk.BooleanVar(parent, value=self.value["preferences"]["display"])
        self.studio_target = tk.BooleanVar(parent, value=self.value["preferences"]["display_target"] == "studio")
        top = ttk.Frame(parent); top.pack(fill="x")
        ttk.Checkbutton(top, text="Enable automatic selection", variable=self.enabled, command=self.save_flags).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(top, text="Show selected overlay", variable=self.display, command=self.save_flags).grid(row=0, column=1, sticky="w", padx=8)
        ttk.Checkbutton(top, text="Studio trigger instead", variable=self.studio_target, command=self.save_flags).grid(row=1, column=0, sticky="w")
        self.visibility = VisibilityMenu(top, self.value["preferences"]["visibility"]["overlay"], self.save_visibility)
        self.visibility.grid(row=1, column=1, sticky="w", padx=8)
        ttk.Checkbutton(top, text="Follow Azeron layer (experimental, this session)", variable=self.follow_layer,
                        command=lambda: self.tick(reschedule=False)).grid(row=2, column=0, columnspan=2, sticky="w")
        self.top_controls = list(top.winfo_children())
        self.status_label = ttk.Label(parent, textvariable=self.note, wraplength=740)
        self.status_label.pack(fill="x", pady=6)
        rows = ttk.Frame(parent); rows.pack(fill="x")
        rows.columnconfigure(1, weight=1)
        self.selectors = {}
        for row, name in enumerate(("game", "group", "layer", "context", "view")):
            ttk.Label(rows, text=name.capitalize()).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
            selector = Selector(rows, on_select=lambda key, n=name: self.selected(n, key),
                                on_add=(lambda n=name: self.add_entity(n)) if name in {"game", "group", "context"} else None)
            selector.grid(row=row, column=1, sticky="ew", pady=3)
            self.selectors[name] = selector
        actions = ttk.Frame(parent); actions.pack(fill="x", pady=6)
        self.action_buttons = []
        for name, command in (("Return to Auto", self.auto), ("Cycle group", self.cycle), ("Explore (pinned)", self.explore)):
            button = ttk.Button(actions, text=name, command=command)
            self.action_buttons.append(button)
        self.peek = ttk.Button(actions, text="Hold Peek")
        self.action_buttons.append(self.peek)
        self.peek.bind("<ButtonPress-1>", self.peek_down); self.peek.bind("<ButtonRelease-1>", self.peek_up)
        self.peek.bind("<KeyPress-space>", self.peek_down); self.peek.bind("<KeyRelease-space>", self.peek_up)
        self.peek.bind("<FocusOut>", self.peek_up)
        self.associations = ttk.LabelFrame(parent, text="Associations / assets", padding=8)
        self.associations.columnconfigure(0, weight=1)
        self.import_entry = ttk.Entry(self.associations, textvariable=self.path)
        self.import_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(self.associations, text="Browse manifest…", command=self.browse).grid(row=0, column=1, padx=5)
        bar = ttk.Frame(self.associations); bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self.asset_buttons = []
        for name, command in (("Validate", self.validate), ("Import additive…", self.import_assets),
                              ("Export private…", self.export), ("Edit associations…", self.edit_association),
                              ("Inspect / edit manifest…", self.edit_manifest)):
            button = ttk.Button(bar, text=name, command=command)
            self.asset_buttons.append(button)
        def reflow(event=None):
            width = max(300, (event.width if event and event.width > 1 else parent.winfo_width()) - 24)
            self.status_label.configure(wraplength=width)
            top_columns = 2 if width >= 650 else 1
            for i, control in enumerate(self.top_controls):
                control.grid(row=i // top_columns, column=i % top_columns, sticky="w", padx=(0, 8), pady=2)
            action_columns = max(1, min(4, width // 200))
            for i, control in enumerate(self.action_buttons):
                control.grid(row=i // action_columns, column=i % action_columns, sticky="w", padx=(0, 6), pady=2)
            columns = max(1, min(5, width // 220))
            for i, button in enumerate(self.asset_buttons):
                button.grid(row=i // columns, column=i % columns, sticky="w", padx=(0, 6), pady=3)
        parent.bind("<Configure>", reflow, add="+")
        self.reflow = reflow
        reflow()
        self.details = tk.Text(parent, height=6, width=40, wrap="word")
        self.apply_visibility(); self.reload_choices()
        # Polling starts with page construction, but no display/provider activity
        # occurs unless explicitly enabled in this private sidecar.
        self.tick()

    def error(self, error):
        text = str(error) if isinstance(error, api.OverlayError) else "Overlay operation refused; inspect source/selection"
        self.note.set(text); self.status_callback(text)
        self.renderer.hide()

    def mutate(self, action, payload):
        try:
            receipt = self.store.update(action, copy.deepcopy(payload), self.fingerprint)
            self.value, self.fingerprint = self.store.load(); self.reload_choices(); return receipt
        except Exception as error:
            self.error(error); return None

    def save_flags(self):
        self.mutate("display", {"enabled": self.enabled.get(), "display": self.display.get(),
                                "display_target": "studio" if self.studio_target.get() else "hub"})
        self.tick(reschedule=False)

    def save_visibility(self, states):
        if self.mutate("visibility", states):
            self.apply_visibility()

    def apply_visibility(self):
        states = self.value["preferences"]["visibility"]["overlay"]
        for name in ("associations", "details"):
            widget = getattr(self, name)
            if states[name]:
                widget.pack(fill="both" if name == "details" else "x", expand=name == "details", pady=5)
            else:
                widget.pack_forget()

    def reload_choices(self):
        index = api.validate_store(self.value)
        game = self.selectors["game"].selected_id
        self.selectors["game"].set_choices([(r["id"], r["label"]) for r in index["games"].values()])
        if game not in index["games"]:
            game = next(iter(index["games"]), None)
        self.selectors["game"].select(game)
        groups = [g for g in index["groups"].values() if g["game_id"] == game]
        self.selectors["group"].set_choices([(g["id"], g["label"]) for g in groups])
        override = self.value["preferences"]["overrides"].get(game)
        assoc = next((a for a in index["associations"].values() if a["game_id"] == game), None)
        self.selectors["group"].select(override or (assoc["default_group"] if assoc else groups[0]["id"] if groups else None))
        keymap = index["keymaps"].get(groups[0]["keymap_id"]) if groups else None
        self.selectors["layer"].set_choices([("Unknown", "Unknown")] + [(l["id"], l["id"]) for l in keymap["layers"]] if keymap else [("Unknown", "Unknown")])
        contexts = sorted({a["context"] for a in index["assets"].values()} | {"gameplay"})
        self.selectors["context"].set_choices([(c, c) for c in contexts])
        self.selectors["view"].set_choices([(v, v) for v in api.VIEWS])
        selected = self.value["preferences"]["selections"].get(game, {"layer": "Unknown", "context": "gameplay", "view": "Combined"})
        for name in ("layer", "context", "view"):
            self.selectors[name].select(selected[name])

    def selected(self, name, key):
        if name == "game":
            self.reload_choices(); return
        game = self.selectors["game"].selected_id
        if not game:
            return
        if name == "group":
            self.mutate("select", {"game_id": game, "group_id": key})
        else:
            self.mutate("selection", {"game_id": game, **{n: self.selectors[n].selected_id or "Unknown" for n in ("layer", "context", "view")}})
        self.tick(reschedule=False)

    def auto(self):
        if self.selectors["game"].selected_id:
            self.mutate("auto", {"game_id": self.selectors["game"].selected_id, "group_id": ""})
            self.tick(reschedule=False)

    def cycle(self):
        if self.selectors["game"].selected_id:
            self.mutate("cycle", {"game_id": self.selectors["game"].selected_id, "group_id": ""})
            self.tick(reschedule=False)

    def preview_result(self):
        value = copy.deepcopy(self.value); value["preferences"].update(enabled=True, display=True)
        index = api.validate_store(value); game = self.selectors["game"].selected_id
        assoc = next((a for a in index["associations"].values() if a["game_id"] == game), None)
        api.require(assoc is not None, "Select an associated game first")
        result = api.choose(value, {"exe": assoc["executables"][0], "at": time.monotonic(), "own": False})
        result["reason"] = "Explicit selected preview; not observed game/layer"
        return result

    def explore(self):
        try:
            self.renderer.show(self.preview_result(), pinned=True)
        except Exception as error:
            self.error(error)

    def peek_down(self, *_):
        if not self.peek_held:
            try:
                self.peek_held = True
                self.renderer.show(self.preview_result())
            except Exception as error:
                self.peek_held = False; self.error(error)
        return "break"

    def peek_up(self, *_):
        self.peek_held = False; self.renderer.hide(); return "break"

    def browse(self):
        selected = filedialog.askopenfilename(parent=self.parent, title="Overlay manifest", filetypes=[("JSON manifest", "*.json")])
        if selected:
            self.path.set(selected)

    def validate(self):
        try:
            value, images, _ = self.store.validate_import(Path(self.path.get()))
            self.note.set(f"Valid manifest • {len(value['groups'])} groups • {len(images)} decoded/hash-verified images • no import")
        except Exception as error:
            self.error(error)

    def import_assets(self, conflict="stop"):
        try:
            if not messagebox.askokcancel("Import overlay assets", "Add validated groups/assets to the private overlay store? Native profiles and Studio settings are not changed.", parent=self.parent):
                return
            self.store.import_manifest(Path(self.path.get()), self.fingerprint, conflict)
            self.value, self.fingerprint = self.store.load(); self.reload_choices()
            self.note.set("Imported additively; manual layer remains Selected, not Observed")
        except api.OverlayError as error:
            if str(error).startswith("Import conflicts:"):
                window = tk.Toplevel(self.parent); window.title("Import conflicts — explicit policy")
                ttk.Label(window, text=str(error), wraplength=500).pack(padx=12, pady=8)
                for policy in ("keep", "replace"):
                    ttk.Button(window, text=policy.capitalize() + " conflicting records",
                               command=lambda p=policy: (window.destroy(), self.import_assets(p))).pack(padx=12, pady=5)
                ttk.Button(window, text="Cancel", command=window.destroy).pack(pady=5)
            else:
                self.error(error)
        except Exception as error:
            self.error(error)

    def export(self):
        destination = filedialog.asksaveasfilename(parent=self.parent, title="NEW private export directory (not a file)")
        if destination:
            try:
                result = api.export_manifest(self.store, destination, self.fingerprint)
                self.note.set("Private export verified: " + result["path"])
            except Exception as error:
                self.error(error)

    def editor(self, title, value, save, help_text=""):
        window = tk.Toplevel(self.parent); window.title(title); window.geometry("660x430")
        ttk.Label(window, text=help_text, wraplength=620).pack(fill="x", padx=10, pady=5)
        text = tk.Text(window, wrap="word", undo=True); text.pack(fill="both", expand=True, padx=10)
        text.insert("1.0", json.dumps(value, ensure_ascii=False, indent=2))
        error = tk.StringVar(window)
        ttk.Label(window, textvariable=error, wraplength=620).pack(fill="x", padx=10)
        def commit():
            try:
                draft = api.decode(text.get("1.0", "end-1c").encode())
                if save(draft):
                    window.destroy()
            except Exception as issue:
                error.set(str(issue))
        bar = ttk.Frame(window); bar.pack(fill="x", padx=10, pady=8)
        ttk.Button(bar, text="Validate and Save", command=commit).pack(side="left")
        ttk.Button(bar, text="Cancel", command=window.destroy).pack(side="right")

    def add_entity(self, name):
        from tkinter import simpledialog
        text = simpledialog.askstring("Add new " + name, "Readable name (creation is explicit):", parent=self.parent)
        if not text:
            return
        if name == "context":
            try:
                api.token(text)
                self.selectors[name].records[text] = f"{text} [{text}]"
                self.selectors[name].labels[f"{text} [{text}]"] = text
                self.selectors[name].select(text); self.selected(name, text)
            except Exception as error:
                self.error(error)
            return
        value = copy.deepcopy(self.value); new_id = name + "-" + uuid.uuid4().hex[:12]
        if name == "game":
            value["manifest"]["games"].append({"id": new_id, "label": text})
        else:
            game = self.selectors["game"].selected_id
            source = next((g for g in value["manifest"]["groups"] if g["game_id"] == game), None)
            if source is None:
                self.note.set("Import a keymap/asset template first, then add a group from that baseline"); return
            group = copy.deepcopy(source); group.update(id=new_id, label=text)
            value["manifest"]["groups"].append(group)
        try:
            self.store.write(value, self.fingerprint); self.value, self.fingerprint = self.store.load(); self.reload_choices()
        except Exception as error:
            self.error(error)

    def edit_association(self):
        game = self.selectors["game"].selected_id
        index = api.validate_store(self.value)
        groups = [g for g in index["groups"].values() if g["game_id"] == game]
        if not groups:
            self.note.set("Import a group/keymap first; no native profile will be created"); return
        previous = next((a for a in index["associations"].values() if a["game_id"] == game), None)
        draft = copy.deepcopy(previous) if previous else {"id": "association-" + uuid.uuid4().hex[:12], "game_id": game,
            "executables": ["Gameplay.exe"], "excluded_executables": ["Launcher.exe"], "keymap_id": groups[0]["keymap_id"],
            "default_group": groups[0]["id"], "cycle_groups": [g["id"] for g in groups], "cycle_enabled": False, "priority": 0}
        # Contextual details editor retains one editable executable selector.
        window = tk.Toplevel(self.parent); window.title("Gameplay association — explicit Save")
        window.columnconfigure(1, weight=1)
        ttk.Label(window, text="Game").grid(row=0, column=0, padx=8, pady=6)
        ttk.Label(window, text=index["games"][game]["label"]).grid(row=0, column=1, sticky="w")
        ttk.Label(window, text="Gameplay executable").grid(row=1, column=0, padx=8, pady=6)
        entry = ttk.Combobox(window, values=draft["executables"], state="normal", width=52)
        entry.set(draft["executables"][0]); entry.grid(row=1, column=1, sticky="ew")
        def browse_exe():
            file = filedialog.askopenfilename(parent=window, filetypes=[("Executable", "*.exe")])
            if file: entry.set(file)
        menu = tk.Menu(window, tearoff=False)
        menu.add_command(label="Browse executable…", command=browse_exe)
        def foreground_exe():
            # Select from running window processes; background process is an
            # association candidate only, never a selection observation.
            processes = api.running_windows()
            entry.configure(values=sorted({p["exe"] for p in processes}))
        menu.add_command(label="List running window processes", command=foreground_exe)
        utility = ttk.Menubutton(window, text="Choose…", menu=menu); utility.grid(row=1, column=2, padx=5)
        ttk.Label(window, text="Exact keymap revision").grid(row=2, column=0, padx=8, pady=6)
        keymap = Selector(window, [(k["id"], k["label"] + " / " + k["revision"]) for k in index["keymaps"].values()])
        keymap.select(draft["keymap_id"]); keymap.grid(row=2, column=1, sticky="ew")
        ttk.Label(window, text="Default group").grid(row=3, column=0, padx=8, pady=6)
        group = Selector(window, [(g["id"], g["label"]) for g in groups]); group.select(draft["default_group"])
        group.grid(row=3, column=1, sticky="ew")
        def change_keymap(k):
            available = [g for g in groups if g["keymap_id"] == k]
            group.set_choices([(g["id"], g["label"]) for g in available])
            group.select(available[0]["id"] if available else None)
        keymap.on_select = change_keymap
        cycle = tk.BooleanVar(window, value=draft["cycle_enabled"])
        ttk.Checkbutton(window, text="Enable ordered cycling", variable=cycle).grid(row=4, column=1, sticky="w")
        ttk.Label(window, text="Launcher exclusions, additional paths and cycle ordering: Advanced details.", wraplength=450).grid(row=5, column=1, sticky="w", pady=5)
        error = tk.StringVar(window); ttk.Label(window, textvariable=error, wraplength=450).grid(row=6, column=1, sticky="w")
        def save():
            try:
                api.executable(entry.get())
                draft["executables"] = [entry.get(), *draft["executables"][1:]]
                draft.update(default_group=group.selected_id, cycle_enabled=cycle.get(), keymap_id=keymap.selected_id)
                draft["cycle_groups"] = [g for g in draft["cycle_groups"] if index["groups"][g]["keymap_id"] == keymap.selected_id]
                if self.mutate("association", draft): window.destroy()
            except Exception as issue: error.set(str(issue))
        ttk.Button(window, text="Save association", command=save).grid(row=7, column=1, sticky="w", pady=8)
        ttk.Button(window, text="Advanced details…", command=lambda: self.editor("Association details", draft,
                   lambda obj: self.mutate("association", obj), "Explicit executable paths, exclusions, priority, group IDs and cycle order; never game bindings.")).grid(row=7, column=2)
        ttk.Button(window, text="Cancel", command=window.destroy).grid(row=7, column=0, padx=8)

    def edit_manifest(self):
        def save(draft):
            api.manifest(draft)
            value = copy.deepcopy(self.value); value["manifest"] = draft
            # Only managed asset references already validated/imported may be
            # edited here. New image activation goes through validated import.
            for asset in draft["assets"]: self.store.asset(asset)
            self.store.write(value, self.fingerprint)
            self.value, self.fingerprint = self.store.load(); self.reload_choices(); return True
        self.editor("Overlay groups / exact references", self.value["manifest"], save,
                    "Advanced data editor. Preserve IDs; images must already be imported and hash-verified. Native mappings are never edited.")

    def tick(self, reschedule=True):
        if self.closed:
            return
        try:
            previous = self.fingerprint
            self.value, self.fingerprint = self.store.load()
            if previous != self.fingerprint:
                self.enabled.set(self.value["preferences"]["enabled"])
                self.display.set(self.value["preferences"]["display"])
                self.studio_target.set(self.value["preferences"]["display_target"] == "studio")
                for name, flag in self.value["preferences"]["visibility"]["overlay"].items():
                    self.visibility.states[name].set(flag)
                self.reload_choices(); self.apply_visibility()
            following = self.value["preferences"]["enabled"] and self.follow_layer.get()
            if following:
                self.layer_follower.start(lambda: self.value["manifest"])
                native = self.layer_follower.snapshot()
            else:
                if self.layer_follower.thread is not None:
                    self.layer_follower.stop()
                native = None
            fg = self.foreground() if self.value["preferences"]["enabled"] else None
            result = api.checked_selection(self.store, self.value, fg, native=native)
            self.result = result
            if result.get("game_id") and not fg.get("own"):
                self.last_game_result = result
            self.note.set(f"{result['reason']} • game/group: {result.get('game_id') or 'None'} / {result.get('group_id') or 'None'} • layer: {result.get('layer', 'Unknown')} ({result['layer_state']}) • " +
                          ("Azeron event tracking; not snapshot-verified" if following else "manual selected layer") +
                          (" • MANUAL OVERRIDE — Return to Auto" if result["manual_override"] else ""))
            if result["render"] and result["display_target"] == "hub" and not self.peek_held:
                self.renderer.show(result)
            elif not self.peek_held:
                self.renderer.hide()
            self.details.delete("1.0", "end"); self.details.insert("1.0", json.dumps(result, indent=2))
            # Relay activation is display-only and fresh; automatic stop/fallback
            # publishes inactive. Installed AHK host is not modified or armed.
            if self.value["preferences"]["enabled"] or (self.store.directory / "overlay-selection.ini").exists():
                api.relay(self.store, result, self.store.directory)
        except Exception as error:
            self.result = None; self.error(error)
            # Any old relay expires within one second; no invalid replacement.
        finally:
            if reschedule and not self.closed:
                self.timer = self.parent.after(100 if self.follow_layer.get() else 250, self.tick)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.layer_follower.stop()
        if self.timer:
            self.parent.after_cancel(self.timer); self.timer = None
        self.renderer.close()
        if (self.store.directory / "overlay-selection.ini").exists():
            try: api.relay(self.store, {"render": False}, self.store.directory)
            except Exception: pass
