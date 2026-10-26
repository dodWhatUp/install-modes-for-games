"""Compact Controllers workspace; discovery and preference saving are inert."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import GameToolControllerRouting as api
from GameToolCompactUI import Selector, FlowToolbar, ScrollableFrame, TableLayout

VERSION = "0.1.0"

class NamedSelector(Selector):
    """Reuse the shared editable list without exposing private machine IDs."""
    def set_choices(self, choices):
        used = {}
        self.records = {}
        for key, label in choices:
            used[label] = used.get(label, 0) + 1
            display = label if used[label] == 1 else label + " (" + str(used[label]) + ")"
            self.records[key] = display
        self.labels = {label: key for key, label in self.records.items()}
        self.configure(values=list(self.records.values()) + (["Add new…"] if self.on_add else []))


class ControllersPanel:
    def __init__(self, parent, directory, status=None, profiles=None, open_native=None,
                 inventory=None, auto_refresh=True, foreground=None, game_lookup=None):
        self.parent = parent
        self.directory = Path(directory)
        self.store = api.Preferences(directory)
        self.profiles = profiles
        self.open_native = open_native
        self.foreground = foreground
        self.game_lookup = game_lookup
        self.last_observation = 0
        self.status = status.set if hasattr(status, "set") else status or (lambda text: None)
        if inventory is None:
            from GameToolControllerInventory import Inventory
            inventory = Inventory()
        self.inventory = inventory
        self.snapshot = {"devices": [], "xinput": [], "relationships": [], "warnings": []}
        self.results = queue.Queue()
        self.busy = False
        self.closed = False
        self.timer = None
        self.work_generation = 0
        self.row_identity = None
        self.saved_evidence = None
        self.loaded_row = None
        self.loading = False
        self.feedback = tk.StringVar(value="Refresh devices, or identify a held controller. Nothing is applied.")
        self.details_text = tk.StringVar()
        self.match_text = tk.StringVar(value="Automatic preference display: waiting for a recognized game. Native routing stays unchanged.")
        self.scroll = ScrollableFrame(parent, min_width=0)
        self.scroll.pack(fill="both", expand=True)
        body = self.scroll.body
        self.heading = ttk.Label(body, text="Controllers", font=("Segoe UI", 18, "bold"))
        self.heading.pack(anchor="w")
        self.intro = ttk.Label(body, text="Choose your preferred controller for a game or group. Inspect its route before using the existing reviewed native controls.", wraplength=720)
        self.intro.pack(anchor="w", pady=(4, 8))
        self.match_label = ttk.Label(body, textvariable=self.match_text, wraplength=720)
        self.match_label.pack(fill="x", pady=3)
        bar = FlowToolbar(body)
        bar.pack(fill="x", pady=4)
        self.refresh_button = bar.add("Refresh devices", self.refresh_inventory)
        self.identify_button = bar.add("Identify held input…", self.identify)
        bar.add("Keymaps & Overlay drafts…", self.keymaps)
        bar.add("DOOM binding files…", self.doom_files)
        form = ttk.Frame(body)
        form.pack(fill="x", pady=6)
        form.columnconfigure(1, weight=1)
        self.saved = NamedSelector(form, on_select=lambda _: self.load_selected(), width=28)
        self.controller = NamedSelector(form, on_select=lambda _: self.edited(), width=28)
        self.native = NamedSelector(form, on_select=lambda _: self.edited(), width=28)
        self.scope = tk.StringVar(value="global")
        self.scope_choice = NamedSelector(form, on_select=lambda _: self.edited(), on_add=self.add_scope, width=28)
        self.custom_scopes = {}
        self.name = tk.StringVar(value="Preferred controller")
        self.route = tk.StringVar(value=api.ROUTE_LABELS["rewasd"])
        self.automatic = tk.BooleanVar(value=False)
        self.accepted = tk.BooleanVar(value=False)
        self.note = tk.StringVar()
        fields = [
            ("Saved preference", self.saved),
            ("Controller", self.controller),
            ("Name", ttk.Entry(form, textvariable=self.name, width=28)),
            ("Scope", ttk.Combobox(form, textvariable=self.scope, values=api.SCOPES, state="readonly", width=26)),
            ("Game / genre / group", self.scope_choice),
            ("Input route", ttk.Combobox(form, textvariable=self.route, values=list(api.ROUTE_LABELS.values()), state="readonly", width=34)),
            ("Saved reWASD setup", self.native),
        ]
        self.scope_control = fields[3][1]
        self.scope_entry = fields[4][1]
        self.labels = []
        for n, (label, control) in enumerate(fields):
            text = ttk.Label(form, text=label)
            text.grid(row=n, column=0, sticky="w", padx=(0, 12), pady=4)
            control.grid(row=n, column=1, sticky="w", pady=4)
            self.labels.append(text)
        self.scope_control.bind("<<ComboboxSelected>>", lambda _: (self.scope_changed(), self.edited()))
        fields[5][1].bind("<<ComboboxSelected>>", lambda _: self.edited())
        ttk.Checkbutton(body, text="Show this preference automatically for matching games (does not change native routing)",
                        variable=self.automatic).pack(anchor="w", pady=5)
        actions = FlowToolbar(body)
        actions.pack(fill="x")
        actions.add("New preference", self.new)
        actions.add("Save preference", self.save)
        actions.add("Preview route", self.preview)
        actions.add("Review native controls…", self.native_controls)
        actions.add("Game groups…", self.game_groups)
        actions.add("Delete preference…", self.delete)
        self.notice = ttk.Label(body, textvariable=self.feedback, wraplength=720)
        self.notice.pack(fill="x", pady=8)
        self.table = ttk.Treeview(body, columns=("endpoint", "kind", "state"), show="headings", height=6)
        for name, width in (("endpoint", 270), ("kind", 110), ("state", 280)):
            self.table.heading(name, text=name.capitalize())
            self.table.column(name, width=width, minwidth=90, stretch=True)
        self.table.pack(fill="both", expand=True, pady=5)
        self.table_layout = TableLayout(self.table)
        self.detail_toggle = tk.BooleanVar(value=False)
        ttk.Checkbutton(body, text="Show route evidence and limitations", variable=self.detail_toggle,
                        command=self.toggle_details).pack(anchor="w", pady=5)
        self.detail_frame = ttk.Frame(body)
        ttk.Label(self.detail_frame, textvariable=self.details_text, wraplength=720).pack(fill="x")
        ttk.Checkbutton(self.detail_frame, text="I tested this route in the game", variable=self.accepted).pack(anchor="w", pady=5)
        ttk.Label(self.detail_frame, text="What worked / remaining limits").pack(anchor="w")
        ttk.Entry(self.detail_frame, textvariable=self.note, width=55).pack(anchor="w", pady=4)
        self.footer = ttk.Label(body, text="Identify reads controller state only. Save changes Game Tools preferences. Remap Off / Apply require their existing review; hardware disconnect and forced Windows priority are not available. Ordinary layer changes never recreate a controller here.", wraplength=720)
        self.footer.pack(fill="x", pady=8)
        for label in (self.intro, self.notice, self.footer, self.match_label):
            label.game_tools_wrap_managed = True
        body.bind("<Configure>", self.resize, add="+")
        self.refresh_saved()
        self.scope_changed()
        self.timer = parent.after(100, self.drain)
        if auto_refresh:
            self.refresh_inventory()

    def resize(self, event):
        for label in (self.intro, self.notice, self.footer, self.match_label):
            label.configure(wraplength=max(200, event.width - 32))

    def report(self, text):
        self.feedback.set(str(text))
        self.status(str(text))

    def scope_changed(self):
        scope = self.scope.get()
        previous = self.scope_choice.selected_id
        choices = self.profiles.games() if scope == "game" and self.profiles else {}
        if scope in ("genre", "group"):
            choices = {x["scope_value"]: x["scope_value"] for x in self.store.load()[0]["preferences"] if x["scope"] == scope}
        choices.update(self.custom_scopes.get(scope, {}))
        if scope == "global":
            choices = {"global": "All games"}
        self.scope_choice.set_choices(list(choices.items()))
        self.scope_choice.select("global" if scope == "global" else previous)

    def add_scope(self, *_):
        scope = self.scope.get()
        if scope == "global":
            return
        value = simpledialog.askstring("Add " + scope, "Name for this " + scope, parent=self.parent)
        if value is None:
            return
        try:
            value = value.strip()
            api.overlay.label(value)
            identity = value
            if scope == "game":
                import re
                identity = re.sub("[^a-z0-9]+", "-", value.lower()).strip("-")[:65]
                api.overlay.token(identity)
            self.custom_scopes.setdefault(scope, {})[identity] = value
            self.scope_changed()
            self.scope_choice.select(identity)
            self.edited()
        except Exception as error:
            self.report(error)

    def edited(self):
        if not self.loading:
            self.accepted.set(False)
            self.saved_evidence = None
        self.preview()

    def toggle_details(self):
        if self.detail_toggle.get():
            self.detail_frame.pack(fill="x", before=self.footer)
        else:
            self.detail_frame.pack_forget()

    def task(self, kind, function):
        if self.busy:
            self.report("A device read is still running. Wait for its result.")
            return
        self.busy = True
        generation = self.work_generation
        self.report("Reading devices…" if kind == "inventory" else "Keep controls released for one second, hold one button or stick for two seconds, then release. Reading for five seconds.")
        def run():
            try:
                self.results.put((generation, kind, function(), None))
            except Exception as error:
                self.results.put((generation, kind, None, str(error)))
        threading.Thread(target=run, daemon=True).start()

    def refresh_inventory(self):
        self.task("inventory", self.inventory.snapshot)

    def identify(self):
        self.task("identify", lambda: self.inventory.sample_hold(duration=5, min_hold=1.0, cancel=lambda: self.closed))

    def drain(self):
        self.timer = None
        if self.closed:
            return
        while not self.results.empty():
            generation, kind, value, error = self.results.get_nowait()
            if generation != self.work_generation:
                continue
            self.busy = False
            if error:
                self.report("Controller read needs attention: " + error)
            elif kind == "inventory":
                self.set_snapshot(value)
            else:
                self.details_text.set(json.dumps(value, ensure_ascii=False, indent=2))
                self.detail_toggle.set(True)
                self.toggle_details()
                self.report("Held-input result is shown below. A detected XInput slot does not identify its physical source; no preference or device state changed.")
        if time.monotonic() - self.last_observation >= 1 and self.parent.winfo_ismapped():
            self.last_observation = time.monotonic()
            if self.foreground and self.game_lookup:
                try:
                    fg = self.foreground()
                    if fg and not fg.get("own"):
                        self.observe_game(self.game_lookup(fg["exe"]) or "")
                except Exception as error:
                    self.match_text.set("Automatic preference display unavailable: " + str(error))
        self.timer = self.parent.after(100, self.drain)

    def observe_game(self, game, genres=None, groups=None):
        result = self.store.resolve(game, genres, groups, automatic_only=True)
        if result["state"] == "preferred":
            row = result["preference"]
            present = any(x["id"] == row["controller_id"] and x.get("present") is True and x.get("eligible_primary")
                          for x in self.snapshot.get("devices", []))
            self.match_text.set("Preferred for " + (game or "all games") + ": " + row["name"] + " · " +
                                api.ROUTE_LABELS[row["route"]] + (". Controller observed." if present else ". Saved controller absent or unverified.") +
                                " Effective game input remains unverified.")
        else:
            self.match_text.set("Automatic preference display: " + result["state"] + ". Native routing stays unchanged.")
        return result

    def set_snapshot(self, value):
        self.snapshot = value
        selected = self.controller.selected_id
        rows = [(x["id"], x.get("label", "Controller") + " · " + x.get("kind", "unknown"))
                for x in value.get("devices", []) if x.get("present") is True and x.get("eligible_primary")]
        self.controller.set_choices(rows)
        self.controller.select(selected if any(x[0] == selected for x in rows) else None)
        if selected != self.controller.selected_id:
            self.accepted.set(False)
            self.saved_evidence = None
        self.preview()
        self.status("Device snapshot refreshed. Windows slot order remains observational.")

    def refresh_saved(self):
        value, self.pin = self.store.load()
        old = self.saved.selected_id
        self.saved.set_choices([(x["id"], x["name"] + " · " + x["scope"] + (" / " + x["scope_value"] if x["scope_value"] else ""))
                                for x in value["preferences"]])
        self.saved.select(old)
        rows = self.profiles.load()[0]["profiles"] if self.profiles else []
        self.native.set_choices([("none", "No linked native setup")] +
                                [(x["id"], x["name"]) for x in rows if x.get("provider") == "rewasd"])
        if self.native.selected_id is None:
            self.native.select("none")

    def load_selected(self):
        value, self.pin = self.store.load()
        row = next((x for x in value["preferences"] if x["id"] == self.saved.selected_id), None)
        if row is None:
            return
        self.loading = True
        self.loaded_row = copy.deepcopy(row)
        self.row_identity = row["id"]
        self.name.set(row["name"])
        self.scope.set(row["scope"])
        self.route.set(api.ROUTE_LABELS[row["route"]])
        self.automatic.set(row["automatic"])
        self.controller.select(row["controller_id"])
        self.native.select(row["native_profile_id"] or "none")
        self.accepted.set(row["evidence"]["state"] == "user-reported")
        self.note.set(row["evidence"]["note"])
        self.saved_evidence = copy.deepcopy(row["evidence"])
        if row["scope"] != "global":
            self.custom_scopes.setdefault(row["scope"], {})[row["scope_value"]] = row["scope_value"]
        self.scope_changed()
        self.scope_choice.select("global" if row["scope"] == "global" else row["scope_value"])
        self.loading = False
        self.preview()

    def draft(self, require_present=False):
        api.overlay.require(bool(self.controller.selected_id), "Choose an observed controller first")
        if require_present:
            api.overlay.require(any(x["id"] == self.controller.selected_id and x.get("present") is True and x.get("eligible_primary")
                                    for x in self.snapshot.get("devices", [])), "Controller is no longer an eligible present endpoint; refresh devices")
        route = next(k for k, label in api.ROUTE_LABELS.items() if label == self.route.get())
        evidence = self.saved_evidence if self.saved_evidence and self.accepted.get() and self.note.get() == self.saved_evidence["note"] else {
                    "state": "user-reported" if self.accepted.get() else "unverified",
                    "note": self.note.get(), "at": int(time.time()) if self.accepted.get() else 0}
        native_id = "" if self.native.selected_id == "none" else self.native.selected_id or ""
        source_pin = ""
        if self.profiles and native_id:
            saved = next((x for x in self.profiles.load()[0]["profiles"] if x["id"] == native_id), None)
            source_pin = saved.get("native", {}).get("config_sha256", "") if saved else ""
        return api.preference(self.name.get(), self.scope.get(), "" if self.scope.get() == "global" else self.scope_choice.selected_id or "",
                              self.controller.selected_id, "" if self.native.selected_id == "none" else self.native.selected_id or "",
                              route, self.automatic.get(), self.row_identity, evidence, source_pin)

    def preview(self):
        try:
            row = self.draft() if self.controller.selected_id else self.loaded_row
            found = api.diagnose(self.snapshot, row)
            self.table.delete(*self.table.get_children())
            family = {x["id"] for x in found["family"]}
            for x in self.snapshot.get("devices", []):
                state = "Saved metadata · presence unverified" if x.get("present") is not True else (
                    "Selected / evidenced family" if x["id"] in family else "Other endpoint · relationship may be unknown")
                self.table.insert("", "end", values=(x.get("label", "Controller"), x.get("kind", "unknown"),
                    state))
            self.details_text.set("\n".join(found["warnings"]) + "\n\nPreferred controller does not establish effective game input.\n"
                                  "XInput slots present: " + ", ".join(map(str, found["xinput_indexes"])))
            self.feedback.set("Route preview · " + found["state"] + " · no native operation")
        except Exception as error:
            self.report(error)

    def save(self):
        try:
            row = self.draft(require_present=True)
            self.store.put(row, self.pin)
            self.row_identity = row["id"]
            self.refresh_saved()
            self.saved.select(row["id"])
            self.load_selected()
            self.report("Controller preference saved. Windows order, native remap and Steam settings are unchanged.")
        except Exception as error:
            self.report(error)

    def new(self):
        self.row_identity = None
        self.loaded_row = None
        self.saved.select(None)
        self.name.set("Preferred controller")
        self.scope.set("global")
        self.route.set(api.ROUTE_LABELS["rewasd"])
        self.native.select("none")
        self.accepted.set(False)
        self.saved_evidence = None
        self.note.set("")
        self.automatic.set(False)
        self.scope_changed()
        self.report("New unsaved preference. Choose a distinct scope, then Save.")

    def delete(self):
        try:
            api.overlay.require(bool(self.row_identity), "Choose a saved preference")
            if not messagebox.askokcancel("Delete controller preference", "Remove only this saved Game Tools preference? Native profiles and mappings are retained.", parent=self.parent):
                return
            self.store.remove(self.row_identity, self.pin)
            self.refresh_saved()
            self.new()
        except Exception as error:
            self.report(error)

    def native_controls(self):
        try:
            identity = self.native.selected_id
            api.overlay.require(identity and identity != "none", "Link a saved reWASD setup first")
            api.overlay.require(self.open_native is not None, "Open Game profiles to review native controls")
            self.open_native(identity)
        except Exception as error:
            self.report(error)

    def game_groups(self):
        win = tk.Toplevel(self.parent)
        win.title("Game genres and groups")
        body = ttk.Frame(win, padding=14)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Assign a game to genres or groups for automatic preference matching. This changes Game Tools metadata only.", wraplength=500).pack(fill="x")
        choice = NamedSelector(body, width=32)
        choice.pack(anchor="w", pady=8)
        choice.set_choices(list(self.profiles.games().items()) if self.profiles else [])
        genres, groups = tk.StringVar(), tk.StringVar()
        for label, variable in (("Genres (comma separated)", genres), ("Groups (comma separated)", groups)):
            ttk.Label(body, text=label).pack(anchor="w")
            ttk.Entry(body, textvariable=variable, width=42).pack(anchor="w", pady=5)
        def selected(*_):
            context = self.store.load()[0]["game_contexts"].get(choice.selected_id, {})
            genres.set(", ".join(context.get("genres", [])))
            groups.set(", ".join(context.get("groups", [])))
        choice.on_select = selected
        notice = tk.StringVar()
        ttk.Label(body, textvariable=notice, wraplength=500).pack(fill="x")
        value, pin = self.store.load()
        def save():
            try:
                api.overlay.require(bool(choice.selected_id), "Choose a game")
                parse = lambda v: list(dict.fromkeys(x.strip() for x in v.get().split(",") if x.strip()))
                self.store.set_game_context(choice.selected_id, parse(genres), parse(groups), pin)
                self.refresh_saved()
                win.destroy()
                self.report("Game groups saved. Matching preferences remain separate from native routing.")
            except Exception as error:
                notice.set(str(error))
        buttons = FlowToolbar(body)
        buttons.pack(fill="x", pady=8)
        buttons.add("Save groups", save)
        buttons.add("Cancel", win.destroy)

    def keymaps(self):
        window = None
        try:
            from GameToolControllerKeymapsUI import KeymapsPanel
            window = tk.Toplevel(self.parent)
            window.title("Controller keymaps & Overlay drafts")
            window.geometry("920x720")
            panel = KeymapsPanel(window, self.directory, status=self.status)
            window.protocol("WM_DELETE_WINDOW", lambda: (panel.close(), window.destroy()))
        except Exception as error:
            if window is not None:
                window.destroy()
            self.report("Controller drafts need attention: " + str(error))

    def doom_files(self):
        window = None
        try:
            from GameToolDoomBindingInspectUI import InspectPanel
            window = tk.Toplevel(self.parent)
            window.title("DOOM saved binding inspection")
            window.geometry("940x720")
            panel = InspectPanel(window, status=self.status)
            window.protocol("WM_DELETE_WINDOW", lambda: (panel.close(), window.destroy()))
        except Exception as error:
            if window is not None:
                window.destroy()
            self.report("DOOM file inspection needs attention: " + str(error))

    def close(self):
        self.closed = True
        self.work_generation += 1
        if self.timer:
            self.parent.after_cancel(self.timer)
            self.timer = None
        self.table_layout.close()
        self.scroll.close()
