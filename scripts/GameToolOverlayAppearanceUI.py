"""Compact appearance editor. Rendering workers never access Tk widgets."""
from __future__ import annotations
import copy
import base64
import io
from pathlib import Path
import queue
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import GameToolOverlay as api
import GameToolOverlayAppearance as looks
from GameToolCompactUI import Selector, ChoiceButtons

VERSION = "0.1.1"
GLOBAL = "appearance-global-defaults"


class Editor:
    def __init__(self, panel):
        self.panel = panel; self.service = looks.Service(panel.store.directory)
        self.value, self.fingerprint, self.policy = self.service.load()
        self.documents = self.service.documents()
        self.messages = queue.Queue(); self.busy = False; self.closed = False
        self.cancelled = threading.Event(); self.preview_serial = 0; self.preview_job = None
        self.window = tk.Toplevel(panel.parent); self.window.title("Overlay appearance & presets")
        self.window.geometry(f'{min(1020, self.window.winfo_screenwidth()-60)}x{min(740, self.window.winfo_screenheight()-90)}')
        self.window.minsize(610, 440); self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.window.columnconfigure(0, weight=1); self.window.rowconfigure(1, weight=1)
        self.scope_records = [(GLOBAL, "Global defaults")] + [(g["id"], g["label"]) for g in self.value["manifest"]["games"]]
        header = ttk.Frame(self.window, padding=10); header.grid(row=0, column=0, sticky="ew"); header.columnconfigure(1, weight=1)
        ttk.Label(header, text="Save settings for").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.scope = Selector(header, self.scope_records, on_select=self.change_scope)
        self.scope.grid(row=0, column=1, sticky="ew")
        self.inherit = tk.BooleanVar(self.window)
        self.inherit_button = ttk.Checkbutton(header, text="Use global defaults for this game", variable=self.inherit, command=self.inheritance)
        self.inherit_button.grid(row=1, column=1, sticky="w", pady=4)
        ttk.Label(header, text="Saved appearance").grid(row=2, column=0, sticky="w", padx=(0, 8))
        self.preset = Selector(header, on_select=self.load_preset, on_add=self.save_new)
        self.preset.grid(row=2, column=1, sticky="ew")
        menu = tk.Menu(header, tearoff=False)
        for label, command in (("Save current draft as new…", self.save_new), ("Replace selected preset", self.replace_preset),
                               ("Duplicate to game / global…", lambda: self.transfer(False)), ("Move to game / global…", lambda: self.transfer(True)),
                               ("Delete selected preset", self.delete_preset)):
            menu.add_command(label=label, command=command)
        preset_menu = ttk.Menubutton(header, text="Preset actions", menu=menu)
        preset_menu.grid(row=2, column=2, sticky="e", padx=(8, 0)); self.preset_menu = menu
        menu.add_separator()
        menu.add_command(label="Import appearance JSON…", command=lambda: self.guard(self.import_json))
        menu.add_command(label="Export appearance JSON…", command=lambda: self.guard(self.export_json))
        self.body_canvas = tk.Canvas(self.window, highlightthickness=0)
        self.body_canvas.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(self.window, orient="vertical", command=self.body_canvas.yview); scroll.grid(row=1, column=1, sticky="ns")
        self.body_canvas.configure(yscrollcommand=scroll.set)
        self.body = ttk.Frame(self.body_canvas, padding=10); body_id = self.body_canvas.create_window(0, 0, anchor="nw", window=self.body)
        self.body.bind("<Configure>", lambda _: self.body_canvas.configure(scrollregion=self.body_canvas.bbox("all")))
        self.body_canvas.bind("<Configure>", lambda e: self.body_canvas.itemconfigure(body_id, width=e.width))
        self.form = ttk.Frame(self.body); self.form.grid(row=0, column=0, sticky="new"); self.form.columnconfigure(1, weight=1)
        self.body.columnconfigure(0, weight=1); self.body.columnconfigure(1, weight=1)
        self.variables = {key: tk.StringVar(self.window) for key in looks.STYLE_FIELDS}
        ttk.Label(self.form, text="Text layout").grid(row=0, column=0, sticky="w")
        self.views = ChoiceButtons(self.form, api.VIEW_CHOICES, on_select=self.choose_view)
        self.views.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.edit_controls = list(self.views.buttons.values())
        for row, (key, label, low, high) in enumerate((("action_text_percent", "Action text (%)", 50, 200),
                                                      ("key_text_percent", "Key text (%)", 50, 200)), 2):
            ttk.Label(self.form, text=label).grid(row=row, column=0, sticky="w", pady=4)
            spin = ttk.Spinbox(self.form, from_=low, to=high, increment=5, width=8, textvariable=self.variables[key])
            spin.grid(row=row, column=1, sticky="w", padx=8); self.edit_controls.append(spin)
        ttk.Label(self.form, text="100% = original size. Long labels shorten to fit.", wraplength=365).grid(row=4, column=0, columnspan=2, sticky="w", pady=(0, 8))
        self.choice(5, "background", "Background", ("opaque", "buttons"))
        ttk.Label(self.form, text="opaque: full panel • buttons: clear gaps, opaque keys", wraplength=365).grid(row=6, column=0, columnspan=2, sticky="w")
        self.choice(7, "size_mode", "Overlay size", ("Screen width %", "Screen height %", "Pixels", "Original %"))
        self.number(8, "size_value", "Size value", 1, 8000)
        self.number(9, "opacity", "Opacity (%)", 5, 100)
        self.advanced_visible = tk.BooleanVar(self.window)
        ttk.Checkbutton(self.form, text="Show position & monitor", variable=self.advanced_visible, command=self.reveal).grid(row=10, column=0, columnspan=2, sticky="w", pady=8)
        self.advanced = ttk.Frame(self.form); self.advanced.columnconfigure(1, weight=1)
        for row, (key, label, choices) in enumerate((("anchor", "Position", ("Center", "TopLeft", "TopRight", "BottomLeft", "BottomRight")),)):
            self.choice(row, key, label, choices, parent=self.advanced)
        for row, (key, label, low, high) in enumerate((("monitor", "Monitor", 1, 16), ("offset_x", "Horizontal offset", -8000, 8000), ("offset_y", "Vertical offset", -8000, 8000)), 1):
            self.number(row, key, label, low, high, parent=self.advanced)
        self.preview_frame = ttk.LabelFrame(self.body, text="Map preview • draft", padding=8)
        self.preview_frame.grid(row=0, column=1, sticky="new", padx=(12, 0))
        self.preview_label = ttk.Label(self.preview_frame, text="Preparing preview…", anchor="center")
        self.preview_label.pack(fill="both", expand=True)
        ttk.Label(self.preview_frame, text="Preview shows text/background. Apply updates the overlay's size and position.\nNative and game bindings stay unchanged; fade timing is separate.", wraplength=430).pack(fill="x", pady=8)
        self.all_games = tk.BooleanVar(self.window)
        self.all_button = ttk.Checkbutton(self.form, text="Use these global defaults for all games now", variable=self.all_games)
        footer = ttk.Frame(self.window, padding=10); footer.grid(row=2, column=0, sticky="ew"); footer.columnconfigure(0, weight=1)
        self.note = tk.StringVar(self.window, value="Changes are drafts until Apply. Saving a preset does not apply it.")
        ttk.Label(footer, textvariable=self.note, wraplength=660).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        self.apply_button = ttk.Button(footer, text="Apply appearance", command=self.apply); self.apply_button.grid(row=1, column=1, padx=6)
        self.close_button = ttk.Button(footer, text="Close", command=self.close); self.close_button.grid(row=1, column=2)
        self.body_canvas.bind("<Configure>", self.reflow, add="+")
        game = panel.selectors["game"].selected_id
        self.scope.select(game if game in dict(self.scope_records) else GLOBAL)
        self.change_scope(self.scope.selected_id)
        for key, variable in self.variables.items():
            variable.trace_add("write", lambda *_, k=key: self.schedule_preview())
        self.timer = self.window.after(80, self.poll)

    def choice(self, row, key, label, values, parent=None):
        parent = parent or self.form
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        box = ttk.Combobox(parent, state="readonly", values=values, textvariable=self.variables[key], width=21)
        box.grid(row=row, column=1, sticky="ew", padx=8); self.edit_controls.append(box)

    def export_json(self):
        from GameToolMapExchangeUI import AppearanceExport
        return AppearanceExport(self)

    def import_json(self):
        from GameToolMapExchangeUI import AppearanceImport
        return AppearanceImport(self)

    def number(self, row, key, label, low, high, parent=None):
        parent = parent or self.form
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=4)
        box = ttk.Spinbox(parent, from_=low, to=high, textvariable=self.variables[key], width=8)
        box.grid(row=row, column=1, sticky="w", padx=8); self.edit_controls.append(box)

    def reflow(self, event=None):
        narrow = self.body_canvas.winfo_width() < 860
        self.preview_frame.grid(row=12 if narrow else 0, column=0 if narrow else 1, sticky="new", padx=(0, 0) if narrow else (12, 0), pady=(10, 0) if narrow else 0)
        self.body.columnconfigure(1, weight=0 if narrow else 1)

    def reveal(self):
        if self.advanced_visible.get(): self.advanced.grid(row=11, column=0, columnspan=2, sticky="ew")
        else: self.advanced.grid_remove()

    def scope_id(self):
        api.require(self.scope.selected_id in dict(self.scope_records), "Choose a saved game or Global defaults")
        return None if self.scope.selected_id == GLOBAL else self.scope.selected_id

    def draft(self):
        result = {}
        for key, variable in self.variables.items():
            raw = variable.get()
            if key in {"view", "background", "anchor", "size_mode"}: result[key] = raw
            elif key in {"monitor", "action_text_percent", "key_text_percent"}: result[key] = int(raw)
            else: result[key] = float(raw)
        return looks.validate_style(result)

    def set_style(self, style):
        for key, value in style.items(): self.variables[key].set(str(value))
        self.views.select(style["view"]); self.schedule_preview()

    def change_scope(self, key):
        if self.busy: return
        scope = self.scope_id(); self.all_games.set(False)
        self.inherit.set(scope is not None and scope not in self.policy["games"])
        self.inherit_button.state(["disabled"] if scope is None else ["!disabled"])
        if scope is None: self.all_button.grid(row=13, column=0, columnspan=2, sticky="w", pady=8)
        else: self.all_button.grid_remove()
        self.set_style(self.policy["global"] if scope is None else looks.effective(self.policy, scope))
        self.presets(); self.update_disabled()

    def presets(self, selected=None):
        scope = self.scope_id()
        self.preset.set_choices([(pid, p["name"]) for pid, p in self.policy["presets"].items() if p["scope"] == scope])
        self.preset.select(selected)

    def inheritance(self):
        if self.inherit.get(): self.set_style(self.policy["global"])
        self.update_disabled()

    def update_disabled(self):
        disabled = self.busy or self.inherit.get()
        for widget in self.edit_controls:
            if isinstance(widget, ttk.Combobox): widget.configure(state="disabled" if disabled else "readonly")
            else: widget.state(["disabled"] if disabled else ["!disabled"])

    def choose_view(self, view):
        self.variables["view"].set(view)

    def guard(self, callback):
        try:
            api.require(not self.busy, "Wait for Apply to finish")
            return callback()
        except (OSError, ValueError) as error:
            self.note.set(str(error)); return None

    def load_preset(self, pid):
        def load():
            p = self.policy["presets"][pid]
            api.require(p["scope"] == self.scope_id(), "Select a preset in the current scope")
            self.inherit.set(False); self.set_style(p["style"]); self.update_disabled()
            self.note.set("Preset loaded as a draft. Apply to use it in this scope.")
        self.guard(load)

    def library_commit(self, candidate, selected=None):
        self.service.save_library(candidate, self.fingerprint)
        self.value, self.fingerprint, self.policy = self.service.load()
        self.presets(selected); self.panel.value, self.panel.fingerprint = self.panel.store.load()
        self.note.set("Preset library saved. Active appearances are unchanged.")

    def name_dialog(self, title, callback, transfer=False, initial=""):
        if self.busy: return
        dialog = tk.Toplevel(self.window); dialog.title(title); dialog.transient(self.window)
        frame = ttk.Frame(dialog, padding=12); frame.pack(fill="both", expand=True); frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Name").grid(row=0, column=0, sticky="w", padx=(0, 8))
        name = tk.StringVar(dialog, value=initial); entry = ttk.Entry(frame, textvariable=name, width=38); entry.grid(row=0, column=1, sticky="ew")
        destination = Selector(frame, self.scope_records)
        if transfer:
            ttk.Label(frame, text="Destination").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=8)
            destination.grid(row=1, column=1, sticky="ew", pady=8); destination.select(self.scope.selected_id)
        error = tk.StringVar(dialog); ttk.Label(frame, textvariable=error, wraplength=400).grid(row=2, column=0, columnspan=2, sticky="w")
        def commit():
            try:
                key = destination.selected_id
                if transfer: api.require(key in dict(self.scope_records), "Choose a destination scope")
                callback(name.get(), None if key == GLOBAL else key)
                dialog.destroy()
            except (OSError, ValueError) as exc: error.set(str(exc))
        ttk.Button(frame, text="Save", command=commit).grid(row=3, column=1, sticky="e", pady=(8, 0))
        entry.focus_set(); dialog.bind("<Return>", lambda _: commit()); dialog.bind("<Escape>", lambda _: dialog.destroy())
        return dialog

    def save_new(self):
        def begin():
            style = self.draft(); scope = self.scope_id()
            def save(name, _):
                candidate, pid = looks.save_preset(self.policy, scope, name, style)
                self.library_commit(candidate, pid)
            self.name_dialog("Save appearance preset", save)
        self.guard(begin)

    def replace_preset(self):
        def replace():
            pid = self.preset.selected_id; api.require(pid in self.policy["presets"], "Select a preset to replace")
            p = self.policy["presets"][pid]
            candidate, _ = looks.save_preset(self.policy, self.scope_id(), p["name"], self.draft(), pid)
            self.library_commit(candidate, pid)
        self.guard(replace)

    def transfer(self, move):
        def begin():
            pid = self.preset.selected_id; api.require(pid in self.policy["presets"], "Select a saved preset first")
            def save(name, scope):
                candidate, new_id = looks.transfer_preset(self.policy, pid, scope, name, move)
                self.library_commit(candidate)
                self.scope.select(GLOBAL if scope is None else scope); self.change_scope(self.scope.selected_id); self.preset.select(new_id)
            self.name_dialog("Move preset" if move else "Duplicate preset", save, transfer=True, initial=self.policy["presets"][pid]["name"])
        self.guard(begin)

    def delete_preset(self):
        def delete():
            pid = self.preset.selected_id; api.require(pid in self.policy["presets"], "Select a saved preset first")
            candidate = copy.deepcopy(self.policy); del candidate["presets"][pid]; self.library_commit(candidate)
        self.guard(delete)

    def schedule_preview(self):
        if self.closed: return
        if self.preview_job: self.window.after_cancel(self.preview_job)
        self.preview_job = self.window.after(250, self.preview)

    def preview(self):
        self.preview_job = None
        if self.busy: return
        try:
            style = self.draft(); scope = self.scope_id()
            game = scope or self.panel.selectors["game"].selected_id
            doc = self.documents.get(game) or next(iter(self.documents.values()), None)
            api.require(doc is not None, "Import an editable map for a preview")
            doc = copy.deepcopy(doc); doc["presentation"]["background"] = style["background"]
        except (OSError, ValueError) as error:
            self.note.set(str(error)); return
        self.preview_serial += 1; serial = self.preview_serial
        def worker():
            try:
                from GameToolKeymapDocument import render
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / "preview.png"; clipped = render(doc, doc["maps"][0], path, style["view"], style)
                    self.messages.put(("preview", serial, path.read_bytes(), len(clipped)))
            except Exception as error: self.messages.put(("preview_error", serial, str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def apply(self):
        def begin():
            scope = self.scope_id()
            candidate = looks.set_scope(self.policy, scope, self.draft(), self.inherit.get(), self.all_games.get())
            self.busy = True; self.cancelled.clear(); self.update_disabled()
            self.apply_button.state(["disabled"]); self.close_button.configure(text="Cancel preparation")
            self.inherit_button.state(["disabled"]); self.all_button.state(["disabled"])
            self.scope.state(["disabled"]); self.preset.state(["disabled"])
            self.note.set("Preparing images; the previous appearance stays active until Apply completes…")
            expected = self.fingerprint
            def worker():
                try:
                    receipt = self.service.apply(candidate, expected, progress=lambda text: self.messages.put(("progress", text)), cancelled=self.cancelled.is_set)
                    self.messages.put(("applied", receipt))
                except Exception as error: self.messages.put(("error", str(error)))
            threading.Thread(target=worker, daemon=True).start()
        self.guard(begin)

    def poll(self):
        if self.closed: return
        try:
            while True:
                row = self.messages.get_nowait(); kind = row[0]
                if kind == "preview" and row[1] == self.preview_serial and not self.busy:
                    from PIL import Image
                    im = Image.open(io.BytesIO(row[2])); im.thumbnail((440, 304))
                    buffer = io.BytesIO(); im.save(buffer, format="PNG")
                    self.photo = tk.PhotoImage(data=base64.b64encode(buffer.getvalue()), master=self.window)
                    self.preview_label.configure(image=self.photo, text="")
                elif kind == "preview_error" and row[1] == self.preview_serial: self.note.set(row[2])
                elif kind == "progress": self.note.set(row[1])
                elif kind in {"applied", "error"}:
                    self.busy = False; self.apply_button.state(["!disabled"]); self.close_button.configure(text="Close")
                    self.scope.state(["!disabled"]); self.preset.state(["!disabled"])
                    self.all_button.state(["!disabled"])
                    if self.scope_id() is not None: self.inherit_button.state(["!disabled"])
                    self.update_disabled()
                    if kind == "applied":
                        self.last_receipt = row[1]
                        self.value, self.fingerprint, self.policy = self.service.load()
                        self.panel.value, self.panel.fingerprint = self.panel.store.load(); self.panel.reload_choices()
                        self.panel.tick(reschedule=False)
                        self.note.set("Appearance applied and saved. Previous settings retained for recovery.")
                    else: self.note.set(row[1])
        except queue.Empty: pass
        self.timer = self.window.after(80, self.poll)

    def close(self):
        if self.busy:
            self.cancelled.set(); self.note.set("Cancelling preparation. If commit already started, its verified result will be shown."); return
        self.closed = True; self.preview_serial += 1
        if self.preview_job: self.window.after_cancel(self.preview_job)
        self.window.after_cancel(self.timer); self.window.destroy()
