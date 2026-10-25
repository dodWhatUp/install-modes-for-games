"""Local JSON exchange dialogs. Import review is distinct from activation."""
from __future__ import annotations
import copy
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
import GameToolOverlay as api
import GameToolKeymapBuilder as builder
import GameToolOverlayAppearanceExchange as appearances
import GameToolKeymapExchange as keymaps
from GameToolCompactUI import Selector

VERSION = "0.1.1"
CONFLICTS = (("keep", "Keep existing; add new"), ("copy", "Keep both; rename copies"), ("replace", "Replace matching names"))
GLOBAL = "appearance-global-defaults"


def shell(parent, title):
    window = tk.Toplevel(parent); window.title(title); window.transient(parent)
    window.geometry("760x480"); window.minsize(560, 360)
    frame = ttk.Frame(window, padding=12); frame.pack(fill="both", expand=True)
    frame.columnconfigure(1, weight=1)
    return window, frame


def status(frame, row):
    variable = tk.StringVar(frame)
    ttk.Label(frame, textvariable=variable, wraplength=680).grid(row=row, column=0, columnspan=3, sticky="w", pady=8)
    return variable


def attempt(note, callback):
    try: return callback()
    except (OSError, ValueError, TypeError, KeyError) as error: note.set(str(error)); return None


def save_json(parent, value, filename, note):
    path = filedialog.asksaveasfilename(parent=parent, title="Export portable JSON — choose a new filename",
                                      defaultextension=".json", initialfile=filename, filetypes=[("JSON", "*.json")])
    if path:
        builder.write_new(path, value)
        note.set("JSON exported locally. Existing files are preserved; no upload or activation.")
    return path


class AppearanceExport:
    def __init__(self, editor):
        self.editor = editor; self.window, form = shell(editor.window, "Export appearance JSON")
        ttk.Label(form, text="Export scope").grid(row=0, column=0, sticky="w", padx=(0, 8))
        records = [("all", "All scopes — global + every game"), ("global", "Global defaults & global presets"), ("game", "One game")]
        if editor.preset.selected_id in editor.policy["presets"]: records.append(("preset", "Selected named preset only"))
        self.scope = Selector(form, records, on_select=lambda _: self.refresh()); self.scope.grid(row=0, column=1, sticky="ew")
        ttk.Label(form, text="Game").grid(row=1, column=0, sticky="w", pady=8)
        self.game = Selector(form, [(g["id"], g["label"]) for g in editor.value["manifest"]["games"]]); self.game.grid(row=1, column=1, sticky="ew", pady=8)
        self.current = tk.BooleanVar(self.window, value=True)
        self.include = ttk.Checkbutton(form, text="Include saved active appearances as named snapshots", variable=self.current); self.include.grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Label(form, text="Exports saved settings. Apply draft edits first if you want them included.\nThe JSON contains sizes, layout, background and position; no images, executable paths or native profiles.", wraplength=680).grid(row=3, column=0, columnspan=2, sticky="w", pady=12)
        self.note = status(form, 4)
        self.export_button = ttk.Button(form, text="Export JSON…", command=lambda: attempt(self.note, self.export)); self.export_button.grid(row=5, column=1, sticky="e")
        game = editor.scope_id(); self.game.select(game or next(iter(self.game.records), None))
        self.scope.select("global" if game is None else "game"); self.refresh()

    def refresh(self):
        self.game.state(["!disabled"] if self.scope.selected_id == "game" else ["disabled"])
        self.include.state(["disabled"] if self.scope.selected_id == "preset" else ["!disabled"])

    def payload(self):
        # Reload saved values rather than silently exporting stale editor drafts.
        value, _, policy = self.editor.service.load()
        return appearances.export_package(policy, value["manifest"]["games"], self.scope.selected_id,
            game=self.game.selected_id, preset=self.editor.preset.selected_id, include_current=self.current.get())

    def export(self):
        value = self.payload(); api.require(bool(value["presets"]), "No saved presets in this scope; include current appearances")
        return save_json(self.window, value, "overlay-appearances-" + self.scope.selected_id + ".json", self.note)


class AppearanceImport:
    def __init__(self, editor, path=None):
        self.editor = editor
        path = path or filedialog.askopenfilename(parent=editor.window, title="Import appearance preset JSON", filetypes=[("JSON", "*.json")])
        if not path: return
        self.path = Path(path); raw = api.read(self.path); self.source_hash = api.sha(raw)
        self.package = appearances.validate(api.decode(raw))
        self.value, self.expected, self.base = editor.service.load()
        self.window, form = shell(editor.window, "Review appearance JSON import")
        ttk.Label(form, text="Destination").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.target = Selector(form, [(appearances.ORIGINAL, "Keep scopes from file"), (GLOBAL, "Global preset library")] +
            [(g["id"], g["label"]) for g in self.value["manifest"]["games"]], on_select=lambda _: self.review())
        self.target.grid(row=0, column=1, sticky="ew"); self.target.select(appearances.ORIGINAL)
        ttk.Label(form, text="Matching names").grid(row=1, column=0, sticky="w", pady=8)
        self.conflict = Selector(form, CONFLICTS, on_select=lambda _: self.review()); self.conflict.grid(row=1, column=1, sticky="ew", pady=8); self.conflict.select("keep")
        self.table = ttk.Treeview(form, columns=("name", "scope", "text", "action"), show="headings", height=9)
        for key, label, width in (("name", "Preset", 205), ("scope", "Destination", 150), ("text", "Action / key size", 135), ("action", "Result", 145)):
            self.table.heading(key, text=label); self.table.column(key, width=width, minwidth=60)
        self.table.grid(row=2, column=0, columnspan=2, sticky="nsew"); form.rowconfigure(2, weight=1)
        ttk.Label(form, text="Import adds saved presets. Current global/game appearances stay active until you select a preset and Apply.", wraplength=680).grid(row=3, column=0, columnspan=2, sticky="w", pady=8)
        self.note = status(form, 4)
        self.import_button = ttk.Button(form, text="Import reviewed presets", command=lambda: attempt(self.note, self.commit)); self.import_button.grid(row=5, column=1, sticky="e")
        self.review()

    def review(self):
        self.table.delete(*self.table.get_children()); self.candidate = None
        def plan():
            target = None if self.target.selected_id == GLOBAL else self.target.selected_id
            games = {g["id"]: g["label"] for g in self.value["manifest"]["games"]}
            self.candidate, rows = appearances.import_plan(self.package, self.base, games, target, self.conflict.selected_id)
            for row in rows:
                style = self.candidate["presets"][row["id"]]["style"]
                self.table.insert("", "end", values=(row["name"], "Global" if row["scope"] is None else games[row["scope"]],
                    f'{style["action_text_percent"]}% / {style["key_text_percent"]}%', row["action"]))
            self.note.set(f'{len(rows)} records reviewed. No styles have been activated.')
        attempt(self.note, plan)
        self.import_button.state(["!disabled"] if self.candidate is not None else ["disabled"])

    def commit(self):
        api.require(self.candidate is not None, "Resolve import scope/conflicts first")
        api.require(api.sha(api.read(self.path)) == self.source_hash, "Import file changed; reopen it before saving")
        self.editor.service.save_library(self.candidate, self.expected)
        self.editor.value, self.editor.fingerprint, self.editor.policy = self.editor.service.load()
        self.editor.presets(); self.editor.panel.value, self.editor.panel.fingerprint = self.editor.panel.store.load()
        self.editor.note.set("Appearance presets imported. Select a preset, then Apply to use it.")
        self.window.destroy()


class KeymapExport:
    def __init__(self, editor, initial="all"):
        self.editor = editor; self.window, form = shell(editor.window, "Export keymap JSON")
        ttk.Label(form, text="Export scope").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.scope = Selector(form, [("all", "All loaded games — one package"), ("game", "One game — all layers / contexts"),
                                    ("map", "One layer / context map"), ("global", "Global keymap templates")], on_select=lambda _: self.refresh())
        self.scope.grid(row=0, column=1, sticky="ew"); self.scope.select(initial)
        ttk.Label(form, text="Game").grid(row=1, column=0, sticky="w", pady=8)
        self.game = Selector(form, [(gid, d["title"]) for gid, d in editor.documents.items()], on_select=lambda _: self.maps())
        self.game.grid(row=1, column=1, sticky="ew", pady=8); self.game.select(editor.current_game)
        ttk.Label(form, text="Map").grid(row=2, column=0, sticky="w")
        self.map = ttk.Combobox(form, state="readonly"); self.map.grid(row=2, column=1, sticky="ew")
        ttk.Label(form, text="Global template").grid(row=3, column=0, sticky="w", pady=8)
        self.templates, _ = keymaps.Templates(editor.panel.store.directory).load()
        self.template = Selector(form, [("all-global-templates", "All global templates")] + [(p["id"], p["name"]) for p in self.templates["presets"]])
        self.template.grid(row=3, column=1, sticky="ew", pady=8); self.template.select("all-global-templates")
        ttk.Label(form, text="Exports editable keys, action labels, geometry, layer/context and source references. Images are rebuilt after import.\nGame exports include current loaded drafts. Native identity references stay in the package; use a private Git repository. Native profile files, executable associations and credentials are excluded.", wraplength=680).grid(row=4, column=0, columnspan=2, sticky="w", pady=12)
        self.note = status(form, 5)
        ttk.Button(form, text="Export JSON…", command=lambda: attempt(self.note, self.export)).grid(row=6, column=1, sticky="e")
        self.maps(); self.refresh()
        if initial == "map" and 0 <= editor.map_index < len(self.map.cget("values")): self.map.current(editor.map_index)

    def maps(self):
        doc = self.editor.documents.get(self.game.selected_id)
        self.map.configure(values=[m["layer"] + " / " + m["context"] for m in doc["maps"]] if doc else [])
        if doc: self.map.current(0)

    def refresh(self):
        self.game.state(["!disabled"] if self.scope.selected_id in {"game", "map"} else ["disabled"])
        self.map.configure(state="readonly" if self.scope.selected_id == "map" else "disabled")
        self.template.state(["!disabled"] if self.scope.selected_id == "global" else ["disabled"])

    def payload(self):
        scope = self.scope.selected_id
        if scope == "global":
            value, _ = keymaps.Templates(self.editor.panel.store.directory).load()
            if self.template.selected_id != "all-global-templates": value["presets"] = [p for p in value["presets"] if p["id"] == self.template.selected_id]
            api.require(bool(value["presets"]), "Save a global keymap template first")
            return keymaps.validate_templates(value)
        self.editor.sync_appearance()
        return keymaps.export_keymaps(self.editor.documents, self.editor.keymaps, scope, self.game.selected_id, self.map.current())

    def export(self):
        return save_json(self.window, self.payload(), "keymaps-" + self.scope.selected_id + ".json", self.note)


class GlobalTemplates:
    def __init__(self, editor):
        self.editor = editor; self.store = keymaps.Templates(editor.panel.store.directory)
        self.value, self.expected = self.store.load()
        self.window, form = shell(editor.window, "Global keymap presets")
        ttk.Label(form, text="Global template").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.preset = Selector(form, on_select=self.selected); self.preset.grid(row=0, column=1, sticky="ew")
        save_button = ttk.Button(form, text="Save current draft as global…", command=self.save_current)
        save_button.grid(row=1, column=0, columnspan=2, sticky="w", pady=10)
        if editor.current_game not in editor.documents: save_button.state(["disabled"])
        self.detail = tk.StringVar(self.window)
        ttk.Label(form, textvariable=self.detail, wraplength=680).grid(row=2, column=0, columnspan=2, sticky="w", pady=10)
        ttk.Label(form, text="Templates can seed a new game draft. They do not remap Azeron, edit a game or activate an overlay. Native source identities are checked again when you Save & use.", wraplength=680).grid(row=3, column=0, columnspan=2, sticky="w")
        bar = ttk.Frame(form); bar.grid(row=4, column=0, columnspan=2, sticky="ew", pady=12)
        for label, callback in (("New game from preset…", self.instantiate), ("Import JSON…", self.import_file), ("Export JSON…", self.export)):
            ttk.Button(bar, text=label, command=lambda cb=callback: attempt(self.note, cb)).pack(side="left", padx=(0, 8))
        self.note = status(form, 5); self.reload()

    def reload(self, selected=None):
        self.value, self.expected = self.store.load(); self.preset.set_choices([(p["id"], p["name"]) for p in self.value["presets"]])
        selected = selected or next(iter(self.preset.records), None); self.preset.select(selected); self.selected(selected)

    def selected(self, pid):
        preset = next((p for p in self.value["presets"] if p["id"] == pid), None)
        self.detail.set(f'{len(preset["document"]["maps"])} maps • {preset["keymap"]["label"]} • keys and actions remain separate' if preset else "No global templates yet. Save the current shared layout or import a global template package.")

    def save_current(self):
        dialog = tk.Toplevel(self.window); dialog.title("Save global keymap preset"); form = ttk.Frame(dialog, padding=12); form.pack(fill="both", expand=True)
        ttk.Label(form, text="Preset name").grid(row=0, column=0, sticky="w", padx=(0, 8))
        name = tk.StringVar(dialog, value=self.editor.document["title"][:85] + " template")
        ttk.Entry(form, textvariable=name, width=44).grid(row=0, column=1, sticky="ew")
        keep = tk.BooleanVar(dialog, value=False)
        ttk.Checkbutton(form, text="Keep action labels and comments from this game", variable=keep).grid(row=1, column=0, columnspan=2, sticky="w", pady=8)
        note = status(form, 2)
        def commit():
            preset = keymaps.make_template(self.editor.document, self.editor.keymaps[self.editor.document["keymap_id"]], name.get(), keep.get())
            self.store.add(preset, self.expected); self.reload(preset["id"]); dialog.destroy()
            self.note.set("Global template saved. Existing game sources and active overlays are unchanged.")
        ttk.Button(form, text="Save global template", command=lambda: attempt(note, commit)).grid(row=3, column=1, sticky="e")
        return dialog

    def instantiate(self):
        from tkinter import simpledialog
        preset = next((p for p in self.value["presets"] if p["id"] == self.preset.selected_id), None)
        api.require(preset is not None, "Select a global template first")
        title = simpledialog.askstring("New game from global preset", "Game name", parent=self.window)
        if not title: return
        doc, keymap = keymaps.new_game(preset, title)
        api.require(keymap["id"] not in self.editor.keymaps or self.editor.keymaps[keymap["id"]] == keymap, "Native contract collision; reconcile the source first")
        self.editor.keymaps[keymap["id"]] = keymap; self.editor.documents[doc["game_id"]] = doc; self.editor.expected[doc["game_id"]] = "absent"
        self.editor.reload_games(); self.editor.choose_game(doc["game_id"])
        self.editor.status.set("New game draft created from global preset. Review labels; Save and Save & use are separate actions."); self.window.destroy()

    def export(self):
        value, _ = self.store.load(); api.require(bool(value["presets"]), "No global templates to export")
        return save_json(self.window, value, "global-keymap-presets.json", self.note)

    def import_file(self, path=None):
        path = path or filedialog.askopenfilename(parent=self.window, title="Import global keymap presets", filetypes=[("JSON", "*.json")])
        if not path: return
        raw = api.read(path); incoming = keymaps.validate_templates(api.decode(raw)); source_hash = api.sha(raw)
        dialog, form = shell(self.window, "Review global keymap import")
        ttk.Label(form, text="Matching names").grid(row=0, column=0, sticky="w", padx=(0, 8))
        conflict = Selector(form, CONFLICTS); conflict.grid(row=0, column=1, sticky="ew"); conflict.select("keep")
        table = ttk.Treeview(form, columns=("name", "result"), show="headings", height=10)
        table.heading("name", text="Global template"); table.heading("result", text="Import result")
        table.grid(row=1, column=0, columnspan=2, sticky="nsew"); form.rowconfigure(1, weight=1)
        note = status(form, 2); state = {}
        def review():
            state.clear(); table.delete(*table.get_children())
            def plan():
                candidate, expected, rows = self.store.import_plan(incoming, conflict.selected_id)
                state.update(candidate=candidate, expected=expected)
                for name, result in rows: table.insert("", "end", values=(name, result))
                note.set("Import stores templates only. Current games and overlays stay active.")
            attempt(note, plan)
        conflict.on_select = lambda _: review()
        def commit():
            api.require(bool(state), "Resolve conflicts before importing")
            api.require(api.sha(api.read(path)) == source_hash, "Import file changed; reopen it")
            self.store.write(state["candidate"], state["expected"]); self.reload(); dialog.destroy()
        ttk.Button(form, text="Import reviewed templates", command=lambda: attempt(note, commit)).grid(row=3, column=1, sticky="e")
        review(); return dialog
