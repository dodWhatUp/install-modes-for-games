"""Visual map authoring inside the existing Hub; all external data stays a draft."""
from __future__ import annotations
import copy
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from tkinter import font as tkfont
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as api
import GameToolOverlay as overlay
import GameToolKeymapComments as comments
import GameToolKeymapCustomization as customization
from GameToolCompactUI import Selector, ChoiceButtons
from GameToolKeyCapture import SPECIAL_KEYS, CaptureDialog

VERSION = "0.1.7"


class Builder:
    def __init__(self, panel):
        self.panel = panel
        self.library = api.SourceLibrary(panel.store.directory)
        self.documents = self.library.documents()
        self.keymaps = self.library.keymaps()
        self.expected = {game: maps.fingerprint(doc) for game, doc in self.documents.items()}
        self.current_game = None; self.map_index = 0; self.selected_button = None; self.drag = None
        self.window = tk.Toplevel(panel.parent); self.window.title("Keymap builder — keys and actions")
        sw, sh = self.window.winfo_screenwidth(), self.window.winfo_screenheight()
        self.window.geometry(f"{min(1180, sw-60)}x{min(820, sh-80)}")
        self.window.minsize(min(860, sw-60), min(620, sh-80))
        self.window.columnconfigure(0, weight=1); self.window.rowconfigure(3, weight=1)
        self.status = tk.StringVar(self.window, value="Select a map, then a physical button. Changes stay in the draft until Save.")
        self.title = tk.StringVar(self.window); self.width = tk.StringVar(self.window)
        self.view = tk.StringVar(self.window, value="Combined"); self.background = tk.StringVar(self.window)
        self.move = tk.BooleanVar(self.window, value=False)
        self.build_menus()
        top = ttk.Frame(self.window, padding=(10, 8)); top.grid(row=0, column=0, sticky="ew"); top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Game / draft").grid(row=0, column=0, padx=(0, 8))
        self.game = Selector(top, on_select=self.choose_game)
        self.game.grid(row=0, column=1, sticky="ew")
        ttk.Button(top, text="New game…", command=lambda: self.guard(self.new_game)).grid(row=0, column=2, padx=6)
        ttk.Button(top, text="Game Controls & Overlay…", command=lambda: self.guard(self.controls_planner)).grid(row=0, column=3, padx=6)
        context = ttk.Frame(self.window, padding=(10, 0)); context.grid(row=1, column=0, sticky="ew"); context.columnconfigure(1, weight=1)
        ttk.Label(context, text="Map / layer").grid(row=0, column=0, padx=(0, 8))
        self.map_choice = ttk.Combobox(context, state="readonly", width=32)
        self.map_choice.grid(row=0, column=1, sticky="ew")
        self.map_choice.bind("<<ComboboxSelected>>", self.choose_map)
        ttk.Button(context, text="Link / add map…", command=lambda: self.guard(self.map_link)).grid(row=0, column=2, padx=6)
        self.route_note = ttk.Label(context, text="Layer selects content; your existing Studio picture button controls visibility.")
        self.route_note.grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        appearance = ttk.Frame(self.window, padding=(10, 4)); appearance.grid(row=2, column=0, sticky="ew")
        ttk.Label(appearance, text="View").pack(side="left")
        self.view_choices = ChoiceButtons(appearance, overlay.VIEW_CHOICES, variable=self.view, on_select=lambda _: self.redraw())
        self.view_choices.pack(side="left", fill="x", expand=True, padx=(4, 12))
        ttk.Label(appearance, text="Background").pack(side="left")
        backgrounds = ttk.Combobox(appearance, state="readonly", textvariable=self.background, values=list(maps.BACKGROUNDS.values()), width=26)
        backgrounds.pack(side="left", padx=4); backgrounds.bind("<<ComboboxSelected>>", lambda _: self.sync_appearance())
        ttk.Label(appearance, text="Width %").pack(side="left", padx=(8, 4))
        ttk.Spinbox(appearance, from_=20, to=70, textvariable=self.width, width=5).pack(side="left")
        ttk.Checkbutton(appearance, text="Move buttons", variable=self.move).pack(side="left", padx=10)
        panes = ttk.Panedwindow(self.window, orient="horizontal"); panes.grid(row=3, column=0, sticky="nsew", padx=10)
        self.canvas = tk.Canvas(panes, background="#0D1522", highlightthickness=0, width=700, height=450)
        panes.add(self.canvas, weight=3)
        self.canvas.bind("<Configure>", lambda _: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.canvas_down); self.canvas.bind("<B1-Motion>", self.canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", lambda _: setattr(self, "drag", None))
        inspector = ttk.Frame(panes); inspector.columnconfigure(0, weight=1); inspector.rowconfigure(0, weight=1)
        inspector_canvas = tk.Canvas(inspector, highlightthickness=0, width=310)
        inspector_canvas.grid(row=0,column=0,sticky="nsew")
        inspector_scroll = ttk.Scrollbar(inspector,orient="vertical",command=inspector_canvas.yview)
        inspector_scroll.grid(row=0,column=1,sticky="ns");inspector_canvas.configure(yscrollcommand=inspector_scroll.set)
        form = ttk.Frame(inspector_canvas, padding=(12, 4)); form.columnconfigure(0, weight=1)
        form_id=inspector_canvas.create_window(0,0,anchor="nw",window=form)
        form.bind("<Configure>",lambda _:inspector_canvas.configure(scrollregion=inspector_canvas.bbox("all")))
        inspector_canvas.bind("<Configure>",lambda e:inspector_canvas.itemconfigure(form_id,width=e.width))
        panes.add(inspector, weight=1)
        ttk.Label(form, text="Physical button").grid(row=0, column=0, sticky="w")
        self.button_choice = ttk.Combobox(form, state="readonly", width=27)
        self.button_choice.grid(row=1, column=0, sticky="ew", pady=(3, 8))
        self.button_choice.bind("<<ComboboxSelected>>", lambda _: self.select_button(int(self.button_choice.get().split()[0][1:])))
        self.output = tk.StringVar(self.window)
        ttk.Label(form, text="Emitted key (Azeron source)").grid(row=2, column=0, sticky="w")
        ttk.Entry(form, state="readonly", textvariable=self.output).grid(row=3, column=0, sticky="ew", pady=3)
        self.fields = {}
        for row, (name, label) in enumerate((("display_key", "Key label"), ("display_action", "Action label"), ("action", "Full action"), ("source", "Action source / note"))):
            ttk.Label(form, text=label).grid(row=4+row*2, column=0, sticky="w", pady=(6, 0))
            variable = tk.StringVar(self.window); self.fields[name] = variable
            if name == "display_key":
                keys=ttk.Frame(form);keys.columnconfigure(0,weight=1)
                keys.grid(row=5+row*2,column=0,sticky="ew",pady=3)
                self.key_choice=ttk.Combobox(keys,textvariable=variable,values=SPECIAL_KEYS,width=18)
                self.key_choice.grid(row=0,column=0,sticky="ew")
                ttk.Button(keys,text="Capture…",command=self.capture_key).grid(row=0,column=1,padx=(5,0))
            else:
                ttk.Entry(form, textvariable=variable).grid(row=5+row*2, column=0, sticky="ew", pady=3)
        ttk.Button(form, text="Set fields in draft", command=lambda: self.guard(self.set_cell)).grid(row=12, column=0, sticky="ew", pady=10)
        ttk.Button(form, text="Position / finger guidance…", command=lambda: self.guard(self.geometry_editor)).grid(row=13, column=0, sticky="ew")
        ttk.Button(form, text="Key comment…", command=lambda: self.guard(lambda: self.comment_editor("key"))).grid(row=14, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(form, text="Preferences, icon / colors…", command=lambda: self.guard(self.customize)).grid(row=15, column=0, sticky="ew", pady=(6,0))
        self.evidence = ttk.Label(form, text="", wraplength=260); self.evidence.grid(row=16, column=0, sticky="w", pady=8)
        footer = ttk.Frame(self.window, padding=10); footer.grid(row=4, column=0, sticky="ew"); footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status, wraplength=720).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Button(footer, text="Save draft", command=lambda: self.guard(self.save)).grid(row=1, column=1, padx=6)
        ttk.Button(footer, text="Publish Overlay", command=lambda: self.guard(self.publish)).grid(row=1, column=2)
        ttk.Label(footer, text="Native keys unchanged · chat labels need review").grid(row=1, column=0, sticky="w")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.reload_games()
        selected = panel.selectors["game"].selected_id
        if selected not in self.documents: selected = next(iter(self.documents), None)
        if selected: self.choose_game(selected)
        else: self.status.set("No sources yet. Import a JSON map package to start.")

    @property
    def document(self):
        overlay.require(self.current_game in self.documents, "Select or import a map first")
        return self.documents[self.current_game]

    def controls_planner(self):
        from GameToolControlsPlannerUI import Planner
        return Planner(self)

    def guard(self, callback):
        try: return callback()
        except (OSError, ValueError, KeyError, StopIteration, UnicodeError) as error:
            self.status.set(str(error)); messagebox.showerror("Map operation stopped", str(error), parent=self.window)

    def build_menus(self):
        bar = tk.Menu(self.window)
        file = tk.Menu(bar, tearoff=False)
        for label, callback in (("Import JSON / text package…", self.import_file), ("Export JSON — all / game / map / global…", lambda: self.export("game")),
            ("Open previous saved map…", self.history)):
            file.add_command(label=label, command=lambda cb=callback: self.guard(cb))
        bar.add_cascade(label="File", menu=file)
        global_menu = tk.Menu(bar, tearoff=False)
        global_menu.add_command(label="Manage / import / export global templates…", command=lambda: self.guard(self.global_presets))
        bar.add_cascade(label="Global presets", menu=global_menu)
        notes = tk.Menu(bar, tearoff=False)
        for label, scope in (("Selected key comment…", "key"), ("This map comment…", "map"), ("All maps of this game…", "all")):
            notes.add_command(label=label, command=lambda s=scope: self.guard(lambda: self.comment_editor(s)))
        bar.add_cascade(label="Comments", menu=notes)
        custom = tk.Menu(bar, tearoff=False)
        custom.add_command(label="Preferences, icons, colors and position review…", command=lambda: self.guard(self.customize))
        bar.add_cascade(label="Customize", menu=custom)
        native = tk.Menu(bar, tearoff=False)
        native.add_command(label="Generate from installed Azeron profiles…", command=lambda: self.guard(lambda: self.from_native(True)))
        native.add_command(label="Generate from selected profile files…", command=lambda: self.guard(lambda: self.from_native(False)))
        bar.add_cascade(label="Azeron", menu=native)
        chat = tk.Menu(bar, tearoff=False)
        chat.add_command(label="Prepare selected maps for this chat…", command=lambda: self.guard(self.export_chat))
        chat.add_command(label="Review chat action-label proposal…", command=lambda: self.guard(self.import_proposal))
        chat.add_command(label="Layout / finger rules and source guidance…", command=lambda: self.guard(self.guidance))
        bar.add_cascade(label="Chat assistance", menu=chat)
        links = tk.Menu(bar, tearoff=False)
        links.add_command(label="Link game executable…", command=lambda: self.guard(self.associate))
        links.add_command(label="Link map to picture button…", command=lambda: self.guard(self.button_link))
        bar.add_cascade(label="Links", menu=links)
        self.window.configure(menu=bar)

    def reload_games(self):
        self.game.set_choices([(game, doc["title"]) for game, doc in self.documents.items()])

    def choose_game(self, game):
        if game not in self.documents: return
        self.current_game = game; self.game.select(game); self.map_index = 0
        self.title.set(self.document["title"])
        self.background.set(maps.BACKGROUNDS[self.document["presentation"]["background"]])
        self.width.set(str(self.document["presentation"]["width_percent"]))
        selected = self.panel.value["preferences"]["selections"].get(game, {})
        self.view_choices.select(selected.get("view", "Combined"))
        self.refresh_maps()

    def refresh_maps(self):
        self.map_index = min(self.map_index, len(self.document["maps"])-1)
        self.map_choice.configure(values=[f'{m["layer"]} / {m["context"]}' for m in self.document["maps"]])
        self.map_choice.current(self.map_index)
        self.button_choice.configure(values=[f'#{b["id"]} {b["position"]} · {b["finger"]}' for b in self.document["buttons"]])
        self.select_button(self.document["buttons"][0]["id"])

    def choose_map(self, *_):
        self.map_index = self.map_choice.current(); self.select_button(self.selected_button)

    def select_button(self, bid):
        self.selected_button = bid
        button = next(b for b in self.document["buttons"] if b["id"] == bid)
        cell = next(c for c in self.document["maps"][self.map_index]["cells"] if c["button_id"] == bid)
        self.button_choice.current(next(i for i,b in enumerate(self.document["buttons"]) if b["id"] == bid))
        self.output.set(cell["output"])
        for name, variable in self.fields.items(): variable.set(cell.get(name, ""))
        note = comments.get(cell)
        self.evidence.configure(text=f'{cell["evidence"]} · {button["finger"]}' + (f'\nComment: {note["text"]}' if note else ""))
        self.redraw()

    def sync_appearance(self):
        if self.current_game:
            candidate=copy.deepcopy(self.document)
            candidate["presentation"] = {"background": next(k for k,v in maps.BACKGROUNDS.items() if v == self.background.get()), "width_percent": int(self.width.get())}
            maps.validate(candidate); self.document["presentation"]=candidate["presentation"]; self.redraw()

    def set_cell(self):
        cell = next(c for c in self.document["maps"][self.map_index]["cells"] if c["button_id"] == self.selected_button)
        for name, limit in (("display_key",80),("display_action",80),("action",240),("source",500)):
            maps.text(self.fields[name].get(),limit)
        cell.update({k:v.get() for k,v in self.fields.items()}); cell["evidence"] = "user_label"
        maps.validate(self.document); self.redraw(); self.status.set("Fields changed in the draft. Save draft, then Publish Overlay separately.")

    def capture_key(self):
        # Keep the target fixed even if the non-modal editor changes selection.
        target=(self.current_game,self.map_index,self.selected_button)
        def use(value):
            if target!=(self.current_game,self.map_index,self.selected_button):
                self.status.set("Map or button changed. Capture again for the selected button.");return
            self.fields["display_key"].set(value)
            self.status.set("Captured key label. Set fields in draft, then Save when ready. Azeron output unchanged.")
        return CaptureDialog(self.window,use)

    def customize(self):
        from GameToolKeymapCustomizationUI import Editor
        return Editor(self)

    def styled_preview(self, mapping, scale):
        # Exact generated pixels, cached only for editor selection changes.
        # Runtime overlay rendering remains prebuilt and off the input path.
        import base64
        import io
        from PIL import Image
        key = (maps.fingerprint(self.document), self.map_index, self.view.get(), round(scale,5))
        if getattr(self, "_styled_preview_key", None) != key:
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/"preview.png"
                maps.render(self.document,mapping,path,self.view.get())
                with Image.open(path) as source:
                    pixels=source.resize((max(1,round(1252*scale)),max(1,round(858*scale))),Image.Resampling.LANCZOS)
                    raw=io.BytesIO(); pixels.save(raw,format="PNG")
            self._styled_image=tk.PhotoImage(master=self.window,data=base64.b64encode(raw.getvalue()))
            self._styled_preview_key=key
        self.canvas.create_image(0,0,anchor="nw",image=self._styled_image)
        for b in self.document["buttons"]:
            x,y,w,h=[b[k]*scale for k in ("x","y","width","height")]
            self.canvas.create_rectangle(x,y,x+w,y+h,fill="",outline="#EFC272" if b["id"]==self.selected_button else "",width=2,
                                         tags=("button",f'button-{b["id"]}'))

    def comment_editor(self, scope="key"):
        overlay.require(scope in {"key", "map", "all"}, "Choose a comment scope")
        target = (self.current_game, self.map_index, self.selected_button)
        mapping = self.document["maps"][self.map_index]
        cell = next(c for c in mapping["cells"] if c["button_id"] == self.selected_button)
        obj = cell if scope == "key" else mapping if scope == "map" else self.document
        existing = comments.get(obj) or dict(text="", color=comments.DEFAULT_COLOR)
        title = f'Key #{self.selected_button} comment' if scope == "key" else "This map comment" if scope == "map" else "All maps of this game — comment"
        dialog = tk.Toplevel(self.window); dialog.title(title)
        form = ttk.Frame(dialog, padding=12); form.pack(fill="both", expand=True); form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Comment").grid(row=0, column=0, sticky="w", padx=(0, 8))
        value = tk.StringVar(dialog, value=existing["text"])
        entry = ttk.Entry(form, textvariable=value, width=65); entry.grid(row=0, column=1, sticky="ew")
        ttk.Label(form, text="Text color").grid(row=1, column=0, sticky="w", pady=8)
        chosen_color = tk.StringVar(dialog, value=next((name for name, code in comments.COLORS.items() if code.upper() == existing["color"].upper()), existing["color"]))
        ttk.Combobox(form, textvariable=chosen_color, values=list(comments.COLORS), width=22).grid(row=1, column=1, sticky="w", pady=8)
        description = "Small colored text inside this key. Blank removes it; up to 160 characters." if scope == "key" else "Shown beneath the layer / content / context heading. Blank removes it; up to 240 characters."
        if scope == "all": description += " Shared by every map of the current game."
        ttk.Label(form, text=description + " Colors also accept #RRGGBB.", wraplength=590).grid(row=2, column=0, columnspan=2, sticky="w", pady=8)
        error = tk.StringVar(dialog)
        ttk.Label(form, textvariable=error, wraplength=590).grid(row=3, column=0, columnspan=2, sticky="w")
        def commit():
            try:
                overlay.require(target == (self.current_game, self.map_index, self.selected_button), "Selection changed; reopen the comment editor")
                if scope == "key": candidate = comments.set_key(self.document, self.map_index, self.selected_button, value.get(), chosen_color.get())
                else: candidate = comments.set_header(self.document, self.map_index, scope, value.get(), chosen_color.get())
                self.documents[self.current_game] = candidate; self.select_button(self.selected_button)
                self.status.set("Comment changed in draft. Save draft, then Publish Overlay; keys and actions are unchanged.")
                dialog.destroy()
            except (ValueError, OSError) as exc: error.set(str(exc))
        ttk.Button(form, text="Set comment in draft", command=commit).grid(row=4, column=1, sticky="e", pady=8)
        dialog.bind("<Escape>", lambda _: dialog.destroy()); entry.focus_set()
        return dialog

    def redraw(self):
        if not self.current_game: return
        self.canvas.delete("all")
        width, height = max(1,self.canvas.winfo_width()), max(1,self.canvas.winfo_height())
        if width < 20 or height < 20: return
        self.scale = min(width/1252, height/858)
        s = self.scale
        self.canvas.create_text(12,12,anchor="nw",text=self.document["title"],fill="#F2F6FF",font=("TkDefaultFont",12,"bold"))
        mapping = self.document["maps"][self.map_index]
        if customization.visual(self.document, mapping):
            self.canvas.delete("all"); self.styled_preview(mapping,s); return
        header_notes = comments.headers(self.document, mapping)
        if header_notes:
            self.canvas.delete("all")
            self.canvas.create_text(20*s,10*s,anchor="nw",text=self.document["title"],fill="#F2F6FF",font=("Segoe UI",-max(1,round(30*s)),"bold"))
            subtitle = "key + action" if self.view.get() == "Combined" else "action + key" if self.view.get() == "ActionFirst" else self.view.get()
            self.canvas.create_text(20*s,53*s,anchor="nw",text=f'{mapping["layer"]} · {subtitle} · {mapping["context"]}',fill="#BFD3EC",font=("Segoe UI",-max(1,round(22*s))))
            header_size, header_y, header_step = comments.header_style(len(header_notes))
            header_font = tkfont.Font(root=self.window, family="Segoe UI", size=-max(1,round(header_size*s)))
            for index, note in enumerate(header_notes):
                lines, _ = maps.fit_lines(note["text"], header_font.measure, 1212*s, 1)
                self.canvas.create_text(20*s,(header_y+header_step*index)*s,anchor="nw",text=lines[0] if lines else "",fill=note["color"],font=header_font,tags=("header-comment",))
        cells = {c["button_id"]:c for c in mapping["cells"]}
        for b in self.document["buttons"]:
            cell=cells[b["id"]]; x,y,w,h=[b[k]*s for k in ("x","y","width","height")]
            tags=("button",f'button-{b["id"]}')
            self.canvas.create_rectangle(x,y,x+w,y+h,fill="#202C40",outline="#EFC272" if b["id"]==self.selected_button else "#708EB7",width=2,tags=tags)
            key,action=maps.cell_labels(cell)
            if comments.get(cell):
                def measure(value, size, bold):
                    font = tkfont.Font(root=self.window, family="Segoe UI", size=-max(1,round(size*s)), weight="bold" if bold else "normal")
                    return font.measure(value) / s
                def text_height(size, bold):
                    font = tkfont.Font(root=self.window, family="Segoe UI", size=-max(1,round(size*s)), weight="bold" if bold else "normal")
                    return font.metrics("linespace") / s
                runs, _, show_id = comments.cell_layout(cell, b, self.view.get(), measure, line_height=text_height)
                if show_id:
                    self.canvas.create_text(x+8*s,y+5*s,anchor="nw",text=f'#{b["id"]}',fill="#AFC4DE",font=("Segoe UI",-max(1,round(15*s))),tags=tags)
                for run in runs:
                    self.canvas.create_text(x+run["x"]*s,y+run["y"]*s,anchor="nw",text=run["text"],fill=run["color"],font=("Segoe UI",-max(1,round(run["size"]*s)),"bold" if run["bold"] else "normal"),tags=tags+("key-comment",) if run["role"]=="comment" else tags)
                continue
            def fitted(value,size,lines,bold=False):
                # Negative font size is canvas pixels, independent of Windows/Tk point scaling.
                font=tkfont.Font(root=self.window,family="Segoe UI",size=-size,weight="bold" if bold else "normal")
                rows=[];current=""
                for word in value.split():
                    attempt=(current+" "+word).strip()
                    if font.measure(attempt)>w-8 and current:rows.append(current);current=word
                    else:current=attempt
                if current:rows.append(current)
                clipped=len(rows)>lines;rows=rows[:lines]
                for index,row in enumerate(rows):
                    shorten=font.measure(row)>w-8 or (clipped and index==len(rows)-1)
                    if shorten:
                        while row and font.measure(row+"…")>w-8:row=row[:-1]
                        rows[index]=row+"…"
                return "\n".join(rows)
            small=max(7,round(14*s));normal=max(8,round(20*s));action_size=max(7,round(18*s))
            if self.view.get()!="Actions":
                self.canvas.create_text(x+4,y+2,anchor="nw",text=f'#{b["id"]}',fill="#AFC4DE",font=("Segoe UI",-small),tags=tags)
            if self.view.get() in {"ActionFirst","Actions"}:
                for size in range(24,17,-1):
                    pixels=max(7,round(size*s))
                    font=tkfont.Font(root=self.window,family="Segoe UI",size=-pixels,weight="bold")
                    lines,clipped=maps.fit_lines(action,font.measure,max(1,w-8),2)
                    if not clipped:break
                line_height=max(9,round((size+4)*s))
                action_y=y+max(small+3,round(25*s)) if self.view.get()=="ActionFirst" else y+max(4,(h-len(lines)*line_height)/2)
                for index,line in enumerate(lines):
                    self.canvas.create_text(x+4,action_y+index*line_height,anchor="nw",text=line,fill="#F2F6FF",font=("Segoe UI",-pixels,"bold"),tags=tags)
                if self.view.get()=="ActionFirst":
                    for size in range(17,11,-1):
                        key_size=max(6,round(size*s))
                        font=tkfont.Font(root=self.window,family="Segoe UI",size=-key_size)
                        if font.measure(key)<=w-8:break
                    self.canvas.create_text(x+4,y+h-max(key_size+3,round(25*s)),anchor="nw",text=fitted(key,key_size,1),fill="#BFD3EC",font=("Segoe UI",-key_size),tags=tags)
                continue
            if self.view.get()!="Actions":
                self.canvas.create_text(x+4,y+max(small+3,round(25*s)),anchor="nw",text=fitted(key,normal,1,True),fill="#F2F6FF",font=("Segoe UI",-normal,"bold"),tags=tags)
            if self.view.get()!="Keys":
                action_y=y+max(small+3,round(25*s)) if self.view.get()=="Actions" else y+max(small+normal+6,round(57*s))
                available=max(0,int((y+h-action_y-3)/(action_size+3)))
                if available:
                    self.canvas.create_text(x+4,action_y,anchor="nw",text=fitted(action,action_size,min(2,available)),fill="#F2F6FF",font=("Segoe UI",-action_size),tags=tags)

    def canvas_down(self,event):
        hits=self.canvas.find_overlapping(event.x,event.y,event.x,event.y)
        for hit in reversed(hits):
            tag=next((t for t in self.canvas.gettags(hit) if t.startswith("button-")),None)
            if tag:
                self.select_button(int(tag[7:])); b=next(b for b in self.document["buttons"] if b["id"]==self.selected_button)
                self.drag=(event.x,event.y,b["x"],b["y"]); return
        # Transparent image interiors have no filled canvas item to hit.
        if getattr(self,"scale",0):
            for b in reversed(self.document["buttons"]):
                if b["x"] <= event.x/self.scale <= b["x"]+b["width"] and b["y"] <= event.y/self.scale <= b["y"]+b["height"]:
                    self.select_button(b["id"]); self.drag=(event.x,event.y,b["x"],b["y"]); return

    def canvas_drag(self,event):
        if not self.move.get() or not self.drag or not self.scale: return
        b=next(b for b in self.document["buttons"] if b["id"]==self.selected_button)
        x,y,bx,by=self.drag
        b["x"]=max(0,min(1252-b["width"],round(bx+(event.x-x)/self.scale)))
        b["y"]=max(0,min(800-b["height"],round(by+(event.y-y)/self.scale)))
        self.redraw(); self.status.set("Display geometry changed in draft; physical output and native profile unchanged.")

    def geometry_editor(self):
        b=next(b for b in self.document["buttons"] if b["id"]==self.selected_button)
        dialog=tk.Toplevel(self.window);dialog.title(f'Button #{b["id"]} — geometry and finger guidance')
        form=ttk.Frame(dialog,padding=12);form.pack(fill="both",expand=True);form.columnconfigure(1,weight=1);fields={}
        for row,key in enumerate(("x","y","width","height","position","finger","guidance")):
            ttk.Label(form,text=key.capitalize()).grid(row=row,column=0,sticky="w",padx=(0,8),pady=4)
            fields[key]=tk.StringVar(dialog,value=str(b[key]));ttk.Entry(form,textvariable=fields[key],width=55 if key=="guidance" else 16).grid(row=row,column=1,sticky="ew")
        def commit():
            candidate=copy.deepcopy(self.document);button=next(x for x in candidate["buttons"] if x["id"]==b["id"])
            for key,var in fields.items():button[key]=int(var.get()) if key in {"x","y","width","height"} else var.get()
            maps.validate(candidate);self.documents[self.current_game]=candidate;self.select_button(b["id"]);dialog.destroy()
        ttk.Button(form,text="Set geometry in draft",command=lambda:self.guard(commit)).grid(row=8,column=1,sticky="e",pady=10)

    def guidance(self):
        dialog=tk.Toplevel(self.window);dialog.title("Layout / finger rules and source guidance")
        box=tk.Text(dialog,wrap="word",width=95,height=28);box.pack(fill="both",expand=True,padx=10,pady=10)
        content="\n\n".join(f'{r["text"]}\nEvidence: {r["evidence"]}\nSource: {r["source"]}' for r in self.document["guidance"])
        box.insert("1.0",content);box.configure(state="disabled")
        ttk.Button(dialog,text="Close",command=dialog.destroy).pack(anchor="e",padx=10,pady=(0,10))

    def new_game(self):
        title=simpledialog.askstring("New game map","Game name — keys come from the selected native layout",parent=self.window)
        if not title:return
        doc=api.new_game(self.document,title);self.documents[doc["game_id"]]=doc;self.expected[doc["game_id"]]="absent"
        self.reload_games();self.choose_game(doc["game_id"]);self.status.set("New game draft. Add action labels, then Save. Link its executable explicitly for automatic game selection.")

    def map_link(self):
        dialog=tk.Toplevel(self.window);dialog.title("Link map to native layer / context")
        form=ttk.Frame(dialog,padding=12);form.pack(fill="both",expand=True)
        ttk.Label(form,text="Native layer").grid(row=0,column=0,sticky="w")
        layer=ttk.Combobox(form,state="readonly",values=list(api.map_outputs(self.document)),width=25);layer.grid(row=0,column=1,padx=8,pady=5);layer.set(self.document["maps"][self.map_index]["layer"])
        ttk.Label(form,text="New context").grid(row=1,column=0,sticky="w")
        context=ttk.Entry(form,width=28);context.insert(0,"menus");context.grid(row=1,column=1,padx=8,pady=5)
        ttk.Label(form,text="Creates a map for this layer/context. Native outputs are copied; action labels start empty.").grid(row=2,column=0,columnspan=2,pady=8)
        def commit():
            self.map_index=api.add_context(self.document,layer.get(),context.get().strip());self.refresh_maps();dialog.destroy()
            self.status.set("New layer/context map added to draft.")
        ttk.Button(form,text="Add linked map to draft",command=lambda:self.guard(commit)).grid(row=3,column=1,sticky="e")

    def import_file(self,path=None):
        path=path or filedialog.askopenfilename(parent=self.window,filetypes=[("JSON maps / package","*.json *.txt")])
        if not path:return
        header = overlay.decode(overlay.read(path)); overlay.require(type(header) is dict, "Expected a JSON map package")
        if header.get("kind") == "global_keymap_package":
            return self.global_presets().import_file(path)
        value=api.read_package(path,self.keymaps)
        for keymap in value["keymaps"]:
            overlay.require(keymap["id"] not in self.keymaps or self.keymaps[keymap["id"]]==keymap,"Native contract collision")
        if any(d["game_id"] in self.documents and maps.fingerprint(d)!=maps.fingerprint(self.documents[d["game_id"]]) for d in value["documents"]):
            if not messagebox.askokcancel("Replace in-memory drafts?","Imported drafts will replace these games' current drafts. Saved sources and active overlays stay unchanged.",parent=self.window):return
        self.keymaps.update({k["id"]:k for k in value["keymaps"]})
        for doc in value["documents"]:
            previous=self.documents.get(doc["game_id"])
            if previous and all(previous[k]==doc[k] for k in ("id","keymap_id","keymap_revision")):
                doc=api.merge_maps(previous,doc)
            self.documents[doc["game_id"]]=copy.deepcopy(doc)
            if doc["game_id"] not in self.expected:
                path=self.library.path(doc["game_id"]);self.expected[doc["game_id"]]=maps.fingerprint(maps.load(path)) if path.exists() else "absent"
        self.reload_games();self.choose_game(value["documents"][0]["game_id"])
        self.status.set(f'Loaded {len(value["documents"])} game drafts from one file. Select each game to review and save; no overlay activated.')

    def export(self,scope):
        from GameToolMapExchangeUI import KeymapExport
        return KeymapExport(self, "all" if scope == "library" else scope)

    def global_presets(self):
        from GameToolMapExchangeUI import GlobalTemplates
        return GlobalTemplates(self)

    def history(self):
        path=filedialog.askopenfilename(parent=self.window,initialdir=str(self.library.root/"history"/self.current_game),filetypes=[("Previous map","*.json")])
        if path:self.import_file(path)

    def from_native(self,installed):
        if installed:
            keymap=self.keymaps[self.document["keymap_id"]]
            base=Path(os.environ.get("APPDATA",""))/"Azeron Software/Storage/DevicesStorage"
            paths=[]
            for layer in keymap["layers"]:
                import uuid
                overlay.require(str(uuid.UUID(layer["profile_id"]))==layer["profile_id"].lower(),"Invalid installed profile identity")
                matches=list(base.glob("*/ProfileStorage/profile_"+layer["profile_id"]+".json"))
                overlay.require(len(matches)==1,"Installed native profile missing/ambiguous; select its exported JSON files instead")
                paths.extend(matches)
        else:
            paths=filedialog.askopenfilenames(parent=self.window,title="Select Azeron profile JSON files, including linked layers",filetypes=[("Azeron profiles","*.json")])
            if not paths:return
        title=simpledialog.askstring("Generate Azeron map","Game name for the new map draft",parent=self.window)
        if not title:return
        doc,keymap=api.native_profiles(paths,self.document,title,known_documents=list(self.documents.values()),known_keymaps=list(self.keymaps.values()))
        self.documents[doc["game_id"]]=doc;self.keymaps[keymap["id"]]=keymap;self.expected[doc["game_id"]]="absent"
        self.reload_games();self.choose_game(doc["game_id"]);self.status.set("Generated from native normal-press outputs. Game actions are unknown; profiles were read, not modified.")

    def save(self):
        self.sync_appearance()
        self.expected[self.current_game]=self.library.save_source(self.document,self.keymaps[self.document["keymap_id"]],self.expected[self.current_game])
        self.status.set("Source saved with previous version retained. Active overlays unchanged.")

    def publish(self):
        self.sync_appearance()
        overlay.require(self.library.path(self.current_game).exists() and
                        maps.fingerprint(self.library.current(self.current_game)) == maps.fingerprint(self.document),
                        "Save draft first, then review and Publish Overlay separately")
        receipt=self.library.publish(self.document,self.keymaps[self.document["keymap_id"]],self.panel.fingerprint,selected_map=self.map_index,selected_view=self.view.get())
        self.panel.value,self.panel.fingerprint=self.panel.store.load();self.panel.reload_choices();self.panel.tick(reschedule=False)
        self.status.set("Saved and linked to game/layer overlays. Native/game keys unchanged. New games need an executable association for Auto.")
        if any(receipt["truncated_positions"].values()):self.status.set("Saved and applied. Some display labels were shortened to fit; full actions remain in JSON.")

    def associate(self):
        value,sha=self.panel.store.load();indexed=overlay.validate_store(value)
        overlay.require(self.current_game in indexed["games"],"Publish Overlay first, then link the actual game executable")
        source=filedialog.askopenfilename(parent=self.window,title="Select the actual game .exe, not its launcher",filetypes=[("Game executable","*.exe")])
        if not source:return
        overlay.require(Path(source).is_file(),"Game executable is missing")
        group_id=api.stable("builder-",self.document["id"])
        association={"id":api.stable("builder-assoc-",self.current_game),"game_id":self.current_game,"executables":[source],"excluded_executables":[],
            "keymap_id":self.document["keymap_id"],"default_group":group_id,"cycle_groups":[],"cycle_enabled":False,"priority":20}
        self.panel.store.update("association",association,sha);self.panel.value,self.panel.fingerprint=self.panel.store.load();self.panel.tick(reschedule=False)
        self.status.set("Saved automatic game association. No game was launched.")

    def button_link(self):
        from GameToolKeymapButtons import open_link_editor
        open_link_editor(self)

    def export_chat(self):
        self.sync_appearance()
        all_maps=messagebox.askyesnocancel("Select chat scope","Include all maps of this game? Yes: all layers/contexts. No: only the selected map. Cancel: export nothing.",parent=self.window)
        if all_maps is None:return
        sources=[]
        if messagebox.askyesno("Optional binding evidence","Include selected text/JSON game-binding references? Only the files you choose are included.",parent=self.window):
            sources=filedialog.askopenfilenames(parent=self.window,filetypes=[("Binding references","*.json *.txt *.md *.csv")])
        value=api.ai_request(self.document,list(range(len(self.document["maps"]))) if all_maps else [self.map_index],sources)
        path=filedialog.asksaveasfilename(parent=self.window,defaultextension=".json",initialfile="chat-keymap-request.json")
        if path:api.write_new(path,value);self.status.set("Selected map context exported locally. Attach the JSON in this chat; no API, upload or automatic message was sent.")

    def import_proposal(self,path=None):
        path=path or filedialog.askopenfilename(parent=self.window,title="Review a chat action-label proposal",filetypes=[("Chat proposal JSON","*.json *.txt")])
        if not path:return
        proposal=overlay.decode(overlay.read(path));changes=api.proposal_changes(self.document,proposal)
        dialog=tk.Toplevel(self.window);dialog.title("Review chat labels — select rows to adopt into draft");dialog.geometry("940x480")
        tree=ttk.Treeview(dialog,columns=("map","button","key","old","new","source"),show="headings",selectmode="extended")
        for key in tree["columns"]:tree.heading(key,text=key.capitalize());tree.column(key,width=140)
        tree.pack(fill="both",expand=True,padx=10,pady=10)
        for i,(change,old) in enumerate(changes):tree.insert("","end",iid=str(i),values=(change["layer"]+"/"+change["context"],change["button_id"],change["output"],old["display_action"] or old["action"],change["display_action"] or change["action"],change["source"]))
        tree.selection_set(tree.get_children())
        def adopt():
            self.documents[self.current_game]=api.adopt_proposal(self.document,proposal,[int(i) for i in tree.selection()]);self.select_button(self.selected_button)
            dialog.destroy();self.status.set("Selected chat labels adopted into draft as AI suggestions. Save draft, then Publish Overlay separately.")
        ttk.Button(dialog,text="Adopt selected rows into draft",command=lambda:self.guard(adopt)).pack(side="right",padx=10,pady=10)
        ttk.Button(dialog,text="Cancel",command=dialog.destroy).pack(side="right",padx=6)

    def close(self):
        dirty=any(maps.fingerprint(doc)!=self.expected.get(game,"absent") for game,doc in self.documents.items())
        if dirty and not messagebox.askokcancel("Close unsaved drafts?","Unsaved map drafts will be discarded. Saved sources and active overlays remain.",parent=self.window):return
        self.window.destroy()
