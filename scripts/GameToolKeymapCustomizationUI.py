"""Contextual customization of a builder draft. Save/publish remains with its owner."""
from __future__ import annotations
import copy
import tkinter as tk
from tkinter import ttk, colorchooser
from tkinter import font as tkfont
import GameToolKeymapCustomization as api
import GameToolKeymapDocument as maps
import GameToolOverlay as overlay

VERSION = "0.1.1"
SCOPES = {"Selected key": "key", "This map": "map", "This layer / all contexts": "layer", "All maps of this game": "all"}


def scroll_page(parent):
    outer=ttk.Frame(parent);outer.columnconfigure(0,weight=1);outer.rowconfigure(0,weight=1)
    canvas=tk.Canvas(outer,highlightthickness=0);canvas.grid(row=0,column=0,sticky="nsew")
    scroll=ttk.Scrollbar(outer,orient="vertical",command=canvas.yview);scroll.grid(row=0,column=1,sticky="ns")
    canvas.configure(yscrollcommand=scroll.set)
    form=ttk.Frame(canvas,padding=12);item=canvas.create_window(0,0,anchor="nw",window=form)
    form.bind("<Configure>",lambda _:canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>",lambda e:canvas.itemconfigure(item,width=e.width))
    return outer,form


class Editor:
    def __init__(self, builder):
        self.builder = builder
        self.target = (builder.current_game, builder.map_index, builder.selected_button)
        self.window = tk.Toplevel(builder.window); self.window.title("Key preferences, icons and colors")
        self.window.geometry("760x620"); self.window.minsize(660, 560)
        self.window.transient(builder.window)
        self.window.columnconfigure(0, weight=1); self.window.rowconfigure(1, weight=1)
        self.note = tk.StringVar(self.window, value="Changes affect this draft. Save draft, then Publish Overlay; native/game inputs are separate.")
        doc, mapping, button, cell = self.objects()
        ttk.Label(self.window, text=f'{doc["title"]} · {mapping["layer"]} / {mapping["context"]} · #{button["id"]} {button["finger"]}',
                  wraplength=620, padding=10).grid(row=0, column=0, sticky="w")
        tabs = ttk.Notebook(self.window); tabs.grid(row=1, column=0, sticky="nsew", padx=10)
        detail_page,details=scroll_page(tabs);color_page,colors=scroll_page(tabs); review = ttk.Frame(tabs, padding=8)
        tabs.add(detail_page, text="Preferences / icon"); tabs.add(color_page, text="Colors / opacity"); tabs.add(review, text="Review positions")
        self.values = {}; self.style_values = {}
        e = button.get("ergonomics", {}); o = cell.get("organization", {})
        fields = [("comfort", "Comfort (5 easiest)", str(e.get("comfort", "")), ("", "5", "4", "3", "2", "1")),
                  ("group", "My group", e.get("group", ""), ("", "Primary", "Secondary", "Utility")),
                  ("action_kind", "Preferred action kind", e.get("action_kind", ""), api.KINDS),
                  ("tags", "Position tags (comma-separated)", ", ".join(e.get("tags", [])), None),
                  ("notes", "Comfort / movement notes", e.get("notes", ""), None),
                  ("category", "This action's category", o.get("category", ""), api.KINDS),
                  ("frequency", "This action's frequency", o.get("frequency", ""), api.FREQUENCIES),
                  ("together", "Needed together with buttons #", ", ".join(map(str, o.get("together", []))), None),
                  ("icon", "Icon / emoji", cell.get("icon", ""), api.ICONS),
                  ("label", "Layer display name (all contexts)", mapping.get("label", ""), None)]
        details.columnconfigure(1, weight=1)
        for row, (name, label, value, choices) in enumerate(fields):
            self.values[name] = tk.StringVar(self.window, value=value)
            ttk.Label(details, text=label).grid(row=row, column=0, sticky="w", padx=(0,12), pady=5)
            widget = ttk.Combobox(details, textvariable=self.values[name], values=choices, width=30) if choices is not None else ttk.Entry(details, textvariable=self.values[name], width=30)
            if name in {"comfort", "frequency"}: widget.configure(state="readonly")
            widget.grid(row=row, column=1, sticky="ew")
        ttk.Label(details, text="Position preferences apply across this game's maps. Category, frequency, icon and simultaneous buttons belong to this map.\nSame-finger warnings are advisory; verify actual reach and game behavior.",
                  wraplength=560).grid(row=10, column=0, columnspan=2, sticky="w", pady=8)
        ttk.Button(details, text="Set preferences / icon in draft", command=lambda: builder.guard(self.apply_details)).grid(row=11, column=1, sticky="e")
        colors.columnconfigure(1, weight=1)
        ttk.Label(colors, text="Apply colors to").grid(row=0,column=0,sticky="w",pady=5)
        self.scope = tk.StringVar(self.window, value="Selected key")
        selector = ttk.Combobox(colors, textvariable=self.scope, state="readonly", values=list(SCOPES), width=32)
        selector.grid(row=0,column=1,sticky="ew"); selector.bind("<<ComboboxSelected>>", lambda _: builder.guard(self.load_style))
        for row, name in enumerate(api.STYLE_COLORS, 1):
            ttk.Label(colors, text=name.replace("_", " ").capitalize()).grid(row=row,column=0,sticky="w",padx=(0,12),pady=6)
            self.style_values[name] = tk.StringVar(self.window)
            ttk.Entry(colors,textvariable=self.style_values[name],width=24).grid(row=row,column=1,sticky="ew")
            ttk.Button(colors,text="Choose…",command=lambda n=name: builder.guard(lambda: self.pick_color(n))).grid(row=row,column=2,padx=(6,0))
        self.style_values["background_opacity"] = tk.StringVar(self.window)
        ttk.Label(colors,text="Key background opacity %").grid(row=6,column=0,sticky="w",pady=6)
        ttk.Spinbox(colors,from_=0,to=100,textvariable=self.style_values["background_opacity"],width=12).grid(row=6,column=1,sticky="w")
        self.inherited = tk.StringVar(self.window)
        ttk.Label(colors,textvariable=self.inherited,wraplength=560).grid(row=7,column=0,columnspan=3,sticky="w",pady=12)
        ttk.Label(colors,text="Blank inherits: game → layer/map → key. More specific overrides win.\nFor visible content behind translucent keys, choose clear gaps in the builder's Background selector. Text stays opaque. Emoji appearance depends on installed fonts.",
                  wraplength=560).grid(row=8,column=0,columnspan=3,sticky="w",pady=8)
        buttons = ttk.Frame(colors); buttons.grid(row=9,column=0,columnspan=3,sticky="e",pady=10)
        ttk.Button(buttons,text="Clear this override",command=lambda: builder.guard(self.clear_style)).pack(side="left",padx=5)
        ttk.Button(buttons,text="Set colors in draft",command=lambda: builder.guard(self.apply_style)).pack(side="left")
        self.build_review(review)
        self.load_style()
        self.refresh_review()
        ttk.Label(self.window,textvariable=self.note,wraplength=620,padding=10).grid(row=2,column=0,sticky="ew")
        ttk.Button(self.window,text="Close",command=self.window.destroy).grid(row=3,column=0,sticky="e",padx=10,pady=(0,10))

    def objects(self):
        overlay.require(self.target == (self.builder.current_game,self.builder.map_index,self.builder.selected_button),
                        "Builder selection changed. Reopen customization for the selected map/key.")
        doc = self.builder.document; mapping = doc["maps"][self.target[1]]
        return doc, mapping, next(b for b in doc["buttons"] if b["id"] == self.target[2]), next(c for c in mapping["cells"] if c["button_id"] == self.target[2])

    def replace(self, candidate, message):
        self.builder.documents[self.target[0]] = maps.validate(candidate)
        self.builder.select_button(self.target[2]); self.builder.status.set(message); self.note.set(message)
        self.refresh_review()

    def apply_details(self):
        self.objects(); candidate = copy.deepcopy(self.builder.document)
        mapping = candidate["maps"][self.target[1]]; b = next(b for b in candidate["buttons"] if b["id"] == self.target[2])
        c = next(c for c in mapping["cells"] if c["button_id"] == self.target[2]); v = {k:x.get().strip() for k,x in self.values.items()}
        e = {k:v[k] for k in ("group","action_kind","notes") if v[k]}
        if v["comfort"]: e["comfort"] = int(v["comfort"])
        if v["tags"]: e["tags"] = list(dict.fromkeys(t.strip() for t in v["tags"].split(",") if t.strip()))
        if e: b["ergonomics"] = e
        else: b.pop("ergonomics",None)
        o = {k:v[k] for k in ("category","frequency") if v[k]}
        if v["together"]: o["together"] = list(dict.fromkeys(int(t.strip().lstrip("#")) for t in v["together"].split(",") if t.strip()))
        if o: c["organization"] = o
        else: c.pop("organization",None)
        if v["icon"]: c["icon"] = v["icon"]
        else: c.pop("icon",None)
        for m in candidate["maps"]:
            if m["layer"] == mapping["layer"]:
                if v["label"]: m["label"] = v["label"]
                else: m.pop("label",None)
        self.replace(candidate,"Preferences and icon set in draft. Save draft and Publish Overlay are separate.")

    def load_style(self):
        doc,mapping,_,cell = self.objects(); scope = SCOPES[self.scope.get()]
        obj = doc if scope == "all" else cell if scope == "key" else mapping
        for k,v in self.style_values.items(): v.set(str(obj.get("key_style",{}).get(k,"")))
        resolved = api.style(doc,mapping,cell)
        self.inherited.set("Effective selected-key overrides: " + (", ".join(k.replace("_"," ")+"="+str(v) for k,v in resolved.items()) or "Built-in colors; 100% key background opacity"))

    def pick_color(self,name):
        initial=self.style_values[name].get() or "#202C40";api.validate_style({name:initial})
        chosen = colorchooser.askcolor(initial,parent=self.window,title=name.replace("_"," "))[1]
        if chosen: self.style_values[name].set(chosen.upper())

    def apply_style(self):
        self.objects(); v = {k:x.get().strip() for k,x in self.style_values.items() if x.get().strip()}
        if "background_opacity" in v: v["background_opacity"] = int(v["background_opacity"])
        candidate = api.set_style(self.builder.document,self.target[1],self.target[2],SCOPES[self.scope.get()],v)
        self.replace(candidate,"Colors set in draft. Save draft, then Publish Overlay applies prepared images."); self.load_style()

    def clear_style(self):
        self.objects()
        candidate = api.set_style(self.builder.document,self.target[1],self.target[2],SCOPES[self.scope.get()],{})
        self.replace(candidate,"Chosen style override cleared in draft; inherited styles remain."); self.load_style()

    def build_review(self,parent):
        parent.columnconfigure(0,weight=1); parent.rowconfigure(1,weight=1)
        self.search = tk.StringVar(self.window)
        ttk.Label(parent,text="Comfort first → my group → preferred action kind. Type to filter.",wraplength=560).grid(row=0,column=0,sticky="w")
        columns = ("button","comfort","group","kind","input","action","issues")
        theme=ttk.Style(self.window)
        theme.configure("KeymapReview.Treeview.Heading",font="TkDefaultFont")
        theme.configure("KeymapReview.Treeview",rowheight=max(22,tkfont.nametofont("TkDefaultFont").metrics("linespace")+6))
        self.table = ttk.Treeview(parent,columns=columns,show="headings",height=12,style="KeymapReview.Treeview")
        for name,width in zip(columns,(70,85,120,140,100,160,250)):
            self.table.heading(name,text=name.capitalize()); self.table.column(name,width=width,minwidth=width,stretch=True)
        self.table.grid(row=1,column=0,sticky="nsew")
        scroll = ttk.Scrollbar(parent,orient="vertical",command=self.table.yview); scroll.grid(row=1,column=1,sticky="ns")
        self.table.configure(yscrollcommand=scroll.set)
        hscroll=ttk.Scrollbar(parent,orient="horizontal",command=self.table.xview);hscroll.grid(row=2,column=0,sticky="ew");self.table.configure(xscrollcommand=hscroll.set)
        ttk.Entry(parent,textvariable=self.search).grid(row=3,column=0,sticky="ew",pady=7)
        self.search.trace_add("write",lambda *_: self.refresh_review())
        ttk.Label(parent,text="Unrated positions stay unknown. Empty input positions require an Azeron profile change; labels/icons never add an input.",wraplength=560).grid(row=4,column=0,sticky="w")

    def refresh_review(self):
        doc,mapping,_,_ = self.objects(); issues = api.issues(doc,mapping); cells = {c["button_id"]:c for c in mapping["cells"]}
        self.table.delete(*self.table.get_children()); query=self.search.get().casefold()
        for b in api.ordered_buttons(doc):
            e=b.get("ergonomics",{}); c=cells[b["id"]]
            row=(f'#{b["id"]}',e.get("comfort","Unrated"),e.get("group",""),e.get("action_kind",""),c["output"],c["display_action"] or c["action"],"; ".join(issues[b["id"]]))
            search_text=" ".join(map(str,row))+" "+b["finger"]+" "+str(e)+" "+str(c.get("organization",{}))
            if not query or query in search_text.casefold(): self.table.insert("","end",iid=str(b["id"]),values=row)
