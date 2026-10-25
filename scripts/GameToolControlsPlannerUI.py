"""Guided controls planning and separately reviewed existing-owner operations."""
from __future__ import annotations
import copy
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import GameToolControlsPlanner as api
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder_api
import GameToolOverlay as overlay
from GameToolCompactUI import Selector
from game_keybind_ops.core import Service

VERSION = "0.2.0"


class Planner:
    def __init__(self, builder):
        self.builder = builder
        self.document = copy.deepcopy(builder.document)
        self.library = api.WorkbookLibrary(builder.library)
        self.service = Service(builder.library.root.parent)
        from GameToolControlsWorkflow import Workflow, default_profiles_root
        self.workflow = Workflow(builder.library, self.service, default_profiles_root())
        self.prepared = None
        source_path = builder.library.path(self.document["game_id"])
        self.saved_map_revision = maps.fingerprint(builder.library.current(self.document["game_id"])) if source_path.exists() else "absent"
        self.native = api.native_status(builder.keymaps[self.document["keymap_id"]], Path(os.environ.get("APPDATA", "")) / "Azeron Software/Storage/DevicesStorage") if os.name == "nt" else []
        self.expected = "absent"
        path = self.library.path(self.document["game_id"])
        self.workbook = self.library.load(self.document["game_id"]) if path.exists() else api.new_workbook(self.document)
        if path.exists(): self.expected = maps.fingerprint(self.workbook)
        self.window = tk.Toplevel(builder.window); self.window.title("Game Controls & Overlay — planning")
        self.window.geometry("1100x740"); self.window.minsize(790, 550)
        self.window.columnconfigure(0, weight=1); self.window.rowconfigure(2, weight=1)
        ttk.Label(self.window, text=self.document["title"] + " · Draft planning · live configuration unchanged",
                  padding=10).grid(row=0, column=0, sticky="w")
        self.note = tk.StringVar(self.window, value="Sources → Actions & priority → Preview. Save, publish and apply remain independent.")
        ttk.Label(self.window, textvariable=self.note, wraplength=1000, padding=(10, 3)).grid(row=1, column=0, sticky="ew")
        self.tabs = ttk.Notebook(self.window); self.tabs.grid(row=2, column=0, sticky="nsew", padx=10)
        self.sources = ttk.Frame(self.tabs, padding=10); self.actions_tab = ttk.Frame(self.tabs, padding=10)
        self.review_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.sources, text="1 Sources"); self.tabs.add(self.actions_tab, text="2 Actions & priority")
        self.tabs.add(self.review_tab, text="3 Preview & export")
        self.build_sources(); self.build_actions(); self.build_review()
        footer = ttk.Frame(self.window, padding=10); footer.grid(row=3, column=0, sticky="ew")
        ttk.Button(footer, text="Save planning draft", command=lambda: self.guard(self.save)).pack(side="right")
        ttk.Label(footer, text="Planning draft · publish and apply require separate review").pack(side="left")
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh()

    def guard(self, callback):
        try: return callback()
        except Exception as e:
            self.note.set(str(e)); messagebox.showerror("Controls planning", str(e), parent=self.window)

    def current(self):
        # Detect edits made in the still-open builder after this planner opened.
        overlay.require(maps.fingerprint(self.builder.document) == maps.fingerprint(self.document),
                        "Builder draft changed; close and reopen planning to reconcile")
        source_path = self.builder.library.path(self.document["game_id"])
        fresh = maps.fingerprint(self.builder.library.current(self.document["game_id"])) if source_path.exists() else "absent"
        overlay.require(fresh == self.saved_map_revision, "Saved map changed; reopen the builder and reconcile")
        if os.name == "nt":
            self.native = api.native_status(self.builder.keymaps[self.document["keymap_id"]], Path(os.environ.get("APPDATA", "")) / "Azeron Software/Storage/DevicesStorage")
            # Planning against a preserved source remains useful while drift is
            # unresolved. Carry the exact observation, never relax runtime guards.
            self.workbook["extensions"]["native_profile_files"] = copy.deepcopy(self.native)
            if any(r["state"] == "drift" for r in self.native):
                self.note.set("Native profile bytes differ: planning snapshot only; reconcile before any future publication or apply.")
        api.preview(self.workbook, self.document)
        api.check_sources(self.workbook, self.service)

    def build_sources(self):
        self.sources.columnconfigure(0, weight=1); self.sources.rowconfigure(2, weight=1)
        ttk.Label(self.sources, wraplength=900, text="Start from the saved native map. Registered targets show actual saved rows; only a reviewed instance resolves declared override precedence. Source selection never launches a game.").grid(row=0, column=0, sticky="ew", pady=(0, 8))
        choices = []; self.source_ids = {}
        for p in self.service._list(self.service.targets, 128):
            try:
                spec = self.service.target(p.stem)["spec"]
                if spec["game_id"] == self.document["game_id"]:
                    identity = "target:" + p.stem; self.source_ids[identity] = ("target", p.stem)
                    choices.append((identity, "Saved rows · " + p.stem))
            except (ValueError, OSError): continue
        from game_keybind_ops.effective import list_instances
        for row in list_instances(self.service, game_id=self.document["game_id"])["instances"]:
            identity = "instance:" + row["instance_id"]; self.source_ids[identity] = ("instance", row["instance_id"])
            choices.append((identity, "Effective instance · " + row["instance_id"]))
        line = ttk.Frame(self.sources); line.grid(row=1, column=0, sticky="ew"); line.columnconfigure(0, weight=1)
        self.source_choice = Selector(line, choices); self.source_choice.grid(row=0, column=0, sticky="ew")
        ttk.Button(line, text="Read selected source…", command=lambda: self.guard(self.attach)).grid(row=0, column=1, padx=6)
        self.source_text = tk.Text(self.sources, wrap="word", height=12); self.source_text.grid(row=2, column=0, sticky="nsew", pady=10)
        ttk.Button(self.sources, text="Recheck source revisions", command=lambda: self.guard(self.recheck)).grid(row=3, column=0, sticky="w")
        ttk.Button(self.sources, text="Compare / reconcile current source…", command=lambda: self.guard(self.reconcile_source)).grid(row=4, column=0, sticky="w", pady=6)
        ttk.Button(self.sources, text="Discover binding-file candidates…", command=lambda: self.guard(self.discover)).grid(row=5,column=0,sticky="w")

    def discover(self):
        from game_keybind_ops.discovery import windows_roots
        from GameToolControlsWorkflow import discover
        roots,warnings=windows_roots() if os.name=="nt" else ({},[])
        result=discover(self.service,self.workbook["game_id"],roots)
        text="Binding file candidates — effective ownership still needs review:\n"
        text+="\n".join(str({k:v for k,v in row.items() if k!="private_path"}) for row in result["candidates"])
        text+="\n"+str(warnings+result["warnings"])
        self.text(self.source_text,text)

    def reconcile_source(self):
        overlay.require(len(self.workbook["sources"]) == 1, "Select a binding source first")
        old = self.workbook["sources"][0]; fresh = api.source_snapshot(self.service, old["kind"], old["id"], self.workbook["game_id"])
        candidate, changes = api.reconcile_source(self.workbook, fresh, self.document)
        self.text(self.review_text, "Current source comparison:\n" + "\n".join(str(c) for c in changes))
        self.tabs.select(self.review_tab)
        if messagebox.askyesno("Reconcile planning source", f'{len(changes)} changed/added/removed rows. Adopt current saved keys, retain annotations and clear affected proposals? No game/native file changes.', parent=self.window):
            self.workbook = candidate; self.prepared = None; self.refresh()

    @staticmethod
    def text(widget, value):
        widget.configure(state="normal"); widget.delete("1.0", "end"); widget.insert("1.0", value); widget.configure(state="disabled")

    def recheck(self):
        self.current(); self.note.set("Pinned map and selected binding files still match. Live native/device state and game behavior remain unverified.")

    def attach(self):
        identity = self.source_choice.selected_id
        overlay.require(identity in self.source_ids, "Select an existing registered target or instance")
        source = api.source_snapshot(self.service, *self.source_ids[identity], self.document["game_id"])
        if not messagebox.askyesno("Read binding source", "Replace this planning action list with the selected source's actual binding rows? Existing annotations stay in the last saved revision. Nothing is applied.", parent=self.window): return
        self.workbook = api.attach_source(self.workbook, source); self.refresh()
        self.note.set("Read actual binding rows. Match source contexts to overlay contexts explicitly; commands are not researched meanings.")

    def build_actions(self):
        self.actions_tab.columnconfigure(0, weight=1); self.actions_tab.rowconfigure(1, weight=1)
        self.search = tk.StringVar(self.window); self.filter = tk.StringVar(self.window, value="All")
        top = ttk.Frame(self.actions_tab); top.grid(row=0, column=0, sticky="ew"); top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Find action / key").grid(row=0, column=0)
        ttk.Entry(top, textvariable=self.search).grid(row=0, column=1, sticky="ew", padx=6)
        choice = ttk.Combobox(top, textvariable=self.filter, state="readonly", width=16, values=("All", "Unknown", "Conflicts", "Changed")); choice.grid(row=0, column=2)
        self.search.trace_add("write", lambda *_: self.refresh_rows()); choice.bind("<<ComboboxSelected>>", lambda _: self.refresh_rows())
        columns = ("action", "context", "priority", "key", "proposed", "review")
        self.table = ttk.Treeview(self.actions_tab, columns=columns, show="headings", selectmode="browse")
        for name, label, width in zip(columns, ("Action / native command", "Context", "Priority", "Key", "Proposed route", "Review"), (230, 100, 90, 80, 150, 210)):
            self.table.heading(name, text=label); self.table.column(name, width=width, minwidth=60)
        self.table.grid(row=1, column=0, sticky="nsew", pady=8)
        scroll = ttk.Scrollbar(self.actions_tab, orient="vertical", command=self.table.yview); scroll.grid(row=1, column=1, sticky="ns"); self.table.configure(yscrollcommand=scroll.set)
        xscroll = ttk.Scrollbar(self.actions_tab, orient="horizontal", command=self.table.xview); xscroll.grid(row=2, column=0, sticky="ew"); self.table.configure(xscrollcommand=xscroll.set)
        self.table.bind("<Double-1>", lambda _: self.guard(self.edit)); self.table.bind("<Return>", lambda _: self.guard(self.edit))
        ttk.Button(self.actions_tab, text="Edit selected action…", command=lambda: self.guard(self.edit)).grid(row=3, column=0, sticky="w", pady=4)
        tools = ttk.Menubutton(self.actions_tab, text="Planning tools…"); menu = tk.Menu(tools, tearoff=False); tools.configure(menu=menu)
        for label, callback in (("Suggest positions…", self.recommend), ("Scoped rule…", self.rule_editor),
                                ("Review shared rule updates…", self.shared_rules), ("Review retained v2 assignments…", self.v2_assignments),
                                ("Prepare focused research request…", self.research), ("Show selected route in builder", self.show_route)):
            menu.add_command(label=label, command=lambda cb=callback: self.guard(cb))
        tools.grid(row=4, column=0, sticky="w")

    def refresh(self):
        sources = self.workbook["sources"]
        text = "Map revision: " + self.workbook["baseline"]["map_sha256"] + "\nNative contract: " + self.document["keymap_revision"]
        text += "\nRules: " + api.RULES + " · game scope; shared changes are proposals only.\n"
        snapshot=self.workbook["extensions"].get("shared_rules_snapshot")
        if snapshot:
            from GameToolControlsRules import Library
            text+=f'\nPinned shared rules: revision {snapshot["revision"]} · {snapshot["sha256"]}\n'
            if Library(self.builder.library).read()["sha256"]!=snapshot["sha256"]:
                text+="New shared rules are available; this game retains its pinned snapshot until review.\n"
        text += "\nNative profile files: " + (", ".join(r["layer"] + " " + r["state"] for r in self.native) or "unverified in this environment") + "\n"
        for source in sources:
            text += "\n" + source["kind"] + " · " + source["id"] + "\nRevision: " + source["revision"]
            if source["kind"] == "target": text += "\nSaved rows only. Effective override precedence remains unknown."
        if not sources: text += "\nNo game binding source selected. Overlay labels are reference data; actual game actions are unknown."
        text += "\n\n#19 Hold, #2 WEAPONS, mouse, stick and native movement outputs stay protected.\nPreview/preparation do not apply changes. Reviewed Game Bindings operations are separate; native software retains profile ownership."
        self.text(self.source_text, text)
        self.refresh_rows()

    def refresh_rows(self):
        if not hasattr(self, "table"): return
        try:
            revision=maps.fingerprint(self.workbook)
            if getattr(self,"_preview_revision",None)!=revision:
                self._preview_value=api.preview(self.workbook,self.document);self._preview_revision=revision
            report=self._preview_value
        except ValueError as e: self.note.set(str(e)); return
        self.report = report
        selected = self.table.selection(); self.table.delete(*self.table.get_children())
        needle = self.search.get().casefold()
        for row in report["rows"]:
            p = row["priority"]; score = str(p["score"]) if p["score"] is not None else (f'{p["range"][0]}–{p["range"][1]}' if p["range"] else "Unknown")
            if row["user_priority_override"] is not None: score += " / user " + str(row["user_priority_override"])
            if needle not in (row["label"] + " " + row["from_key"] + " " + row["context"]).casefold(): continue
            mode = self.filter.get()
            if mode == "Unknown" and not row["warnings"]: continue
            if mode == "Conflicts" and not row["blocked"]: continue
            if mode == "Changed" and not row["changed"]: continue
            values = (row["label"], row["context"], score, row["from_key"], row["proposed"] or "Keep current", "; ".join(row["blocked"] or row["warnings"]) or "Draft")
            self.table.insert("", "end", iid=row["id"], values=values)
        if selected and self.table.exists(selected[0]): self.table.selection_set(selected[0])

    def edit(self):
        selected = self.table.selection(); overlay.require(bool(selected), "Select an action")
        action = next(a for a in self.workbook["actions"] if a["id"] == selected[0])
        row = next(r for r in self.report["rows"] if r["id"] == action["id"])
        win = tk.Toplevel(self.window); win.title("Action evidence and route"); win.columnconfigure(1, weight=1)
        variables = {}
        fields = [("label", "Label", None), ("meaning", "Meaning / evidence", None),
            ("activation", "Activation", api.ACTIVATIONS), ("urgency", "Urgency U · candidates 1–5", None),
            ("frequency", "In-context frequency F · 1–4", None), ("needs_movement", "Needs movement", ("Unknown", "Yes", "No")),
            ("overlay_context", "Reviewed overlay context", ("Unknown", *sorted({m["context"] for m in self.document["maps"]}))),
            ("proposed_route", "Proposed position", ("Keep current", *(r["id"] for r in api.routes(self.document)))),
            ("categories", "Categories · comma separated", None), ("evidence", "Evidence / source", None)]
        for i, (name, label, choices) in enumerate(fields):
            value = action[name]
            if name in ("urgency", "frequency", "categories", "evidence"): value = ", ".join(map(str, value))
            if name == "needs_movement": value = "Unknown" if value is None else "Yes" if value else "No"
            if name == "overlay_context": value = value or "Unknown"
            if name == "proposed_route": value = value or "Keep current"
            variables[name] = tk.StringVar(win, value=value)
            ttk.Label(win, text=label).grid(row=i, column=0, sticky="w", padx=8, pady=4)
            widget = ttk.Combobox(win, textvariable=variables[name], values=choices, state="readonly") if choices else ttk.Entry(win, textvariable=variables[name], width=58)
            widget.grid(row=i, column=1, sticky="ew", padx=8, pady=4)
        ttk.Label(win, wraplength=650, text="20 = greatest access need. Blank U/F stays unknown. Bundle members move together; same-finger combinations still need physical review.\n" + "; ".join(row["blocked"] + row["warnings"])).grid(row=10, column=0, columnspan=2, padx=8, pady=8)
        def commit():
            candidate = copy.deepcopy(self.workbook)
            target = next(a for a in candidate["actions"] if a["id"] == action["id"])
            for name, variable in variables.items():
                v = variable.get().strip()
                if name in ("urgency", "frequency"): v = [int(x.strip()) for x in v.split(",") if x.strip()]
                elif name in ("categories", "evidence"): v = [x.strip() for x in v.split(",") if x.strip()]
                elif name == "needs_movement": v = {"Unknown": None, "Yes": True, "No": False}[v]
                elif name in ("overlay_context", "proposed_route"): v = None if v in ("Unknown", "Keep current") else v
                target[name] = v
            if target["bundle_id"]:
                for a in candidate["actions"]:
                    if (a["context"], a["bundle_id"]) == (target["context"], target["bundle_id"]):
                        a["proposed_route"] = target["proposed_route"]; a["overlay_context"] = target["overlay_context"]
            api.validate(candidate); self.workbook = candidate; self.refresh_rows(); win.destroy()
        ttk.Button(win, text="Keep in planning draft", command=lambda: self.guard(commit)).grid(row=11, column=1, sticky="e", padx=8, pady=8)

    def build_review(self):
        self.review_tab.columnconfigure(0, weight=1); self.review_tab.rowconfigure(1, weight=1)
        bar = ttk.Frame(self.review_tab); bar.grid(row=0, column=0, sticky="ew")
        for label, callback in (("Review changes", self.review), ("Map preview…", self.map_preview),
                                ("Import reviewed response…", self.import_response)):
            ttk.Button(bar, text=label, command=lambda cb=callback: self.guard(cb)).pack(side="left", padx=(0, 6))
        export = ttk.Menubutton(bar, text="Export…"); menu = tk.Menu(export, tearoff=False); export.configure(menu=menu)
        menu.add_command(label="Review packet for offline assistance…", command=lambda: self.guard(self.export))
        menu.add_command(label="Candidate map sources and all four views…", command=lambda: self.guard(self.export_candidate))
        menu.add_command(label="Planning v2 workbook, preserving original graph…", command=lambda: self.guard(self.export_v2))
        menu.add_command(label="Manual checklist for unsupported/UI-only bindings…", command=lambda: self.guard(self.export_manual))
        export.pack(side="left")
        operations = ttk.Menubutton(bar, text="Reviewed operations…"); ops = tk.Menu(operations, tearoff=False); operations.configure(menu=ops)
        for label, callback in (("Preview exact game-binding diff", self.game_diff), ("Prepare reviewed plan…", self.prepare_plan),
                                ("Apply Game Bindings…", self.apply_game), ("Review game rollback…", self.rollback_game),
                                ("Load verified candidate in builder…", self.load_candidate),
                                ("Suspend game overlay before rollback…", self.suspend_overlay), ("Load original map after exact rollback…", self.load_original)):
            ops.add_command(label=label, command=lambda cb=callback: self.guard(cb))
        ops.add_separator(); ops.add_command(label="Apply Native Profile — native software/manual review only", state="disabled")
        operations.pack(side="left", padx=6)
        self.review_text = tk.Text(self.review_tab, wrap="word"); self.review_text.grid(row=1, column=0, sticky="nsew", pady=8)
        self.text(self.review_text, "Review changes to see current → proposed routes, aliases and unresolved constraints. Export carries one pinned workbook for offline assistance; importing it cannot apply changes.")

    def review(self):
        self.current(); report = api.preview(self.workbook, self.document)
        lines = ["Read-only plan " + report["plan_sha256"], "Native profile: unchanged · Game files: unchanged · Overlay: unchanged", ""]
        for r in report["rows"]:
            if r["proposed"] or r["blocked"]:
                lines.extend([r["label"] + " · " + r["context"],
                    ", ".join(r["current"]) + " → " + (r["proposed"] or "Keep current"),
                    r["from_key"] + " → " + r["to_key"], "All output occurrences: " + ", ".join(r["aliases"]),
                    "Review: " + "; ".join(r["blocked"] + r["warnings"]), ""])
        if not any(r["proposed"] for r in report["rows"]): lines.append("No placement changes proposed. Unknown action classifications need evidence before recommendations.")
        lines.extend(report["limitations"]); self.text(self.review_text, "\n".join(lines))

    def map_preview(self):
        self.current(); proposed = api.overlay_candidate(self.workbook, self.document)
        appearance=self.appearance()
        win = tk.Toplevel(self.window); win.title("Current / proposed overlay — preview only")
        from PIL import Image
        win.images = []
        layer = ttk.Combobox(win, state="readonly", values=[m["layer"] + " / " + m["context"] for m in self.document["maps"]], width=45)
        layer.grid(row=0, column=0, columnspan=2, sticky="ew"); layer.current(self.builder.map_index)
        labels = [ttk.Label(win), ttk.Label(win)]
        for i, label in enumerate(labels):
            ttk.Label(win, text=("Current" if i == 0 else "Proposed · game changes not applied")).grid(row=1, column=i)
            label.grid(row=2, column=i)
        def draw(*_):
            win.images.clear()
            with tempfile.TemporaryDirectory() as tmp:
                for i, doc in enumerate((self.document, proposed)):
                    path = Path(tmp) / (str(i) + ".png")
                    maps.render(doc, doc["maps"][layer.current()], path, self.builder.view.get(), appearance)
                    with Image.open(path) as image:
                        image.thumbnail((min(520, win.winfo_screenwidth() // 2 - 40), 520))
                        thumb = Path(tmp) / ("thumb-" + str(i) + ".png"); image.save(thumb)
                    photo = tk.PhotoImage(file=str(thumb), master=win)
                    win.images.append(photo); labels[i].configure(image=photo)
        layer.bind("<<ComboboxSelected>>", lambda _: self.guard(draw)); draw()

    def save(self):
        self.current(); candidate = copy.deepcopy(self.workbook); candidate["revision"] += 1
        candidate["change_log"].append({"revision": candidate["revision"], "scope": "game", "operation": "save planning draft"})
        self.expected = self.library.save(candidate, self.expected); self.workbook = candidate
        self.note.set("Planning draft saved with history. Native profiles, game files and published overlays unchanged.")

    def export(self):
        self.current()
        path = filedialog.asksaveasfilename(parent=self.window, title="Export new review packet", defaultextension=".json", initialfile=self.document["game_id"] + "-controls-review.json")
        if path: builder_api.write_new(path, api.export_packet(self.workbook, self.document)); self.note.set("Pinned review packet exported. No API key or upload used.")

    def import_response(self):
        self.current()
        path = filedialog.askopenfilename(parent=self.window, filetypes=[("Controls workbook", "*.json")])
        if not path: return
        value = api.decode(overlay.read(path))
        if value.get("kind") == "azeron_game_workbook":
            import GameToolControlsWorkbook as workbook
            value = workbook.read(path, self.library.root / "intake")
            unidentified=value["game_identity"]["game_id"] is None and bool(value["actions"])
            candidate, report = workbook.import_workbook(value, self.workbook, self.document,confirmed_game_id=self.workbook["game_id"] if unidentified else None)
            prefix=f'Explicitly link this unidentified workbook to {self.document["title"]}? ' if unidentified else ''
            if not messagebox.askyesno("Review planning v2 intake", prefix+f'{len(report["projected_actions"])} exact action links; {len(report["unlinked_actions"])} retained without links. Import classifications and preserve the full original graph? No route/apply authority is imported.', parent=self.window): return
        elif value.get("kind") == "controls_action_research_reply":
            from GameToolControlsResearch import adopt_reply
            candidate, report = adopt_reply(self.workbook,value,self.document)
            if report["conflicts"]:
                if not messagebox.askyesno("Review research conflicts",f'{len(report["conflicts"])} existing annotations differ. Replace those fields with the cited response?',parent=self.window):return
                candidate, report = adopt_reply(self.workbook,value,self.document,replace_conflicts=True)
        else: candidate = api.import_review(self.workbook, value, self.document)
        # Every imported change remains reviewable and unsaved.
        self.workbook = candidate; self.refresh(); self.tabs.select(self.review_tab); self.review()

    def export_v2(self):
        self.current(); import GameToolControlsWorkbook as workbook
        value = workbook.export_workbook(self.workbook)
        path = filedialog.asksaveasfilename(parent=self.window, title="Export preserved planning v2 workbook", defaultextension=".json")
        if path: builder_api.write_new(path, value)

    def v2_assignments(self):
        self.current();from GameToolControlsWorkbook import assignment_preview
        result=assignment_preview(self.workbook,self.document)
        self.text(self.review_text,__import__("json").dumps({k:v for k,v in result.items() if k!="candidate"},indent=2));self.tabs.select(self.review_tab)
        if not result["blocked"] and result["proposed"] and messagebox.askyesno("Review imported route assignments",f'Keep {len(result["proposed"])} exact existing native routes as proposals? Imported applied/verified states do not become local acceptance.',parent=self.window):
            self.workbook=result["candidate"];self.prepared=None;self.refresh_rows()

    def research(self):
        self.current()
        from GameToolControlsResearch import request_packet
        path = filedialog.asksaveasfilename(parent=self.window, title="Export focused research request", defaultextension=".json")
        if path: builder_api.write_new(path, request_packet(self.workbook))

    def show_route(self):
        selected=self.table.selection();overlay.require(bool(selected),"Select an action")
        row=next(r for r in self.report["rows"] if r["id"]==selected[0]);identity=row["proposed"] or next(iter(row["current"]),None)
        overlay.require(identity is not None,"No verified native route for this source key/context")
        layer,context,button=identity.split("/");overlay.require(self.builder.document["game_id"]==self.document["game_id"],"Builder game changed")
        self.builder.map_index=next(i for i,m in enumerate(self.builder.document["maps"]) if (m["layer"],m["context"])==(layer,context))
        self.builder.map_choice.current(self.builder.map_index);self.builder.select_button(int(button))
        self.note.set("Highlighted "+identity+" in the existing builder; display selection only.")

    def export_manual(self):
        self.current(); from GameToolControlsResearch import manual_checklist
        path=filedialog.asksaveasfilename(parent=self.window,title="Export manual binding review checklist",defaultextension=".json")
        if path:builder_api.write_new(path,manual_checklist(self.workbook,self.document))

    def recommend(self):
        self.current(); from GameToolControlsOptimizer import recommend
        result = recommend(self.workbook, self.document)
        self.text(self.review_text, result["claim"] + f'\n{result["states"]} states; limited={result["search_limited"]}\n' +
                  "\n".join(str(x) for x in result["proposals"] + result["withheld"]))
        self.tabs.select(self.review_tab)
        if result["proposals"] and messagebox.askyesno("Review position recommendations", f'Adopt {len(result["proposals"])} suggested action routes in the planning draft? This does not apply them.', parent=self.window):
            self.workbook = result["candidate"]; self.prepared = None; self.refresh_rows()

    def rule_editor(self):
        from GameToolControlsRules import FIELDS, SCOPES, Library, validate
        win = tk.Toplevel(self.window); win.title("Scoped planning rule")
        selected = self.table.selection(); action = next((a for a in self.workbook["actions"] if selected and a["id"] == selected[0]), None)
        scope = tk.StringVar(win, value="game"); field = tk.StringVar(win, value="preferred_buttons")
        targets = tk.StringVar(win, value=self.workbook["game_id"]); value = tk.StringVar(win); reason = tk.StringVar(win)
        accepted = tk.BooleanVar(win, value=False)
        for row,(label,variable,choices) in enumerate((("Scope",scope,SCOPES),("Rule",field,FIELDS),("Scope targets",targets,None),("Value",value,None),("Reason",reason,None))):
            ttk.Label(win,text=label).grid(row=row,column=0,sticky="w",padx=8,pady=5)
            control=ttk.Combobox(win,textvariable=variable,values=choices,state="readonly") if choices else ttk.Entry(win,textvariable=variable,width=52)
            control.grid(row=row,column=1,sticky="ew",padx=8,pady=5)
        def scope_changed(*_):
            targets.set({"game":self.workbook["game_id"],"action":action["id"] if action else "", "context":action["context"] if action else "", "global":"", "genre":""}[scope.get()])
        scope.trace_add("write",scope_changed)
        ttk.Checkbutton(win,text="Accept this planning rule",variable=accepted).grid(row=5,column=1,sticky="w",padx=8)
        def save():
            v=value.get().strip()
            if field.get() in {"preferred_buttons","forbidden_buttons"}: v=[int(x.strip()) for x in v.split(",") if x.strip()]
            elif field.get()=="direct_access":
                overlay.require(v.lower() in {"yes","no","true","false"},"Enter yes or no");v=v.lower() in {"yes","true"}
            rule={"id":builder_api.stable("rule-",scope.get()+"|"+targets.get()+"|"+field.get()),"revision":1,
                  "scope":{"level":scope.get(),"target_ids":[x.strip() for x in targets.get().split(",") if x.strip()]},
                  "field":field.get(),"value":v,"acceptance":"accepted" if accepted.get() else "proposed","reason":reason.get()}
            validate(rule)
            if scope.get() in {"global","genre"}:
                lib=Library(self.builder.library);old=lib.read();rules=[r for r in old["rules"] if r["id"]!=rule["id"]]
                previous=next((r for r in old["rules"] if r["id"]==rule["id"]),None);rule["revision"]=previous["revision"]+1 if previous else 1
                changed=lib.save(rules+[rule],old["sha256"],authorize=lambda _:messagebox.askyesno("Save shared planning rule", "Save this explicit shared/genre rule? Other game workbooks will require review before adopting it.",parent=win))
                self.note.set(f'Shared rule saved. {len(lib.impact(changed))} saved games may need review; none adopted automatically.')
            else:
                records=self.workbook["extensions"].setdefault("rules",[]);previous=next((r for r in records if r["id"]==rule["id"]),None)
                rule["revision"]=previous["revision"]+1 if previous else 1
                self.workbook["extensions"]["rules"]=[r for r in records if r["id"]!=rule["id"]]+[rule]
                self.refresh_rows()
            win.destroy()
        ttk.Button(win,text="Review and keep rule",command=lambda:self.guard(save)).grid(row=6,column=1,sticky="e",padx=8,pady=8)

    def shared_rules(self):
        from GameToolControlsRules import Library
        snapshot = Library(self.builder.library).read()
        if messagebox.askyesno("Review shared rules", f'Adopt shared rules revision {snapshot["revision"]} ({len(snapshot["rules"])} rules) in this game draft only? Existing source and native profiles remain unchanged.', parent=self.window):
            self.workbook["extensions"]["shared_rules_snapshot"] = snapshot; self.refresh_rows()

    def game_diff(self):
        self.current(); from GameToolControlsWorkflow import binding_preview
        value=binding_preview(self.workbook,self.document,self.service)
        self.text(self.review_text,__import__("json").dumps(value,ensure_ascii=False,indent=2));self.tabs.select(self.review_tab)
        return value

    def prepare_plan(self):
        self.current(); review=self.workflow.review(self.workbook,self.document,self.builder.keymaps[self.document["keymap_id"]])
        self.prepared=self.workflow.prepare(review,review["review_sha256"],authorize=lambda r:messagebox.askyesno("Prepare reviewed plan", f'Prepare {sum(len(i["diff"]) for i in r["game"].get("items",[]))} precise game row changes and matching maps? This stores backups/candidates only. Native match={r["native_match"]}. Applying and publishing remain separate.',parent=self.window))
        self.note.set("Reviewed plan prepared with original bytes. No game or overlay change applied.")

    def prepared_record(self):
        overlay.require(self.prepared is not None,"Prepare a reviewed plan first")
        record=self.workflow.load(self.prepared["plan_id"])
        overlay.require(maps.fingerprint(self.workbook)==maps.fingerprint(record["review"]["workbook"]),"Planning draft changed; prepare a new reviewed plan")
        return record

    def apply_game(self):
        record=self.prepared_record()
        value=self.workflow.apply_game(record["plan_id"],authorize=lambda r:messagebox.askyesno("Apply Game Bindings", f'Apply this exact prepared game transaction {r["plan_id"]}? The game and declared config writers must be closed. Overlay and native profiles are separate.',parent=self.window))
        self.note.set(value["status"]+" · game behavior remains unverified; overlay unchanged")

    def rollback_game(self):
        record=self.prepared_record()
        value=self.workflow.rollback_game(record["plan_id"],authorize=lambda _:messagebox.askyesno("Review exact game rollback","Restore the exact original bytes for this verified transaction? Later edits block exact rollback.",parent=self.window))
        self.note.set(value["status"]+" · overlay publication remains independent")

    def load_candidate(self):
        record=self.prepared_record();candidate=self.workflow.publication_candidate(record["plan_id"])
        self.builder.documents[candidate["game_id"]]=candidate;self.builder.choose_game(candidate["game_id"])
        self.note.set("Verified candidate loaded in the builder draft. Review it there, Save draft, then Publish Overlay separately.")

    def suspend_overlay(self):
        record=self.prepared_record()
        self.workflow.suspend_overlay(record["plan_id"],authorize=lambda _:messagebox.askyesno("Suspend this game's overlay", "Hide this game's content through a pending context before rollback? Other games, hold controls and assets remain unchanged.",parent=self.window))
        self.builder.panel.value,self.builder.panel.fingerprint=self.builder.panel.store.load()
        self.note.set("Game overlay suspended for rollback. No game/native input changed.")

    def load_original(self):
        record=self.prepared_record();candidate=self.workflow.original_overlay_candidate(record["plan_id"])
        self.builder.documents[candidate["game_id"]]=candidate;self.builder.choose_game(candidate["game_id"])
        self.note.set("Original map loaded after verified exact rollback. Review, Save draft and Publish Overlay separately.")

    def export_candidate(self):
        self.current()
        parent = filedialog.askdirectory(parent=self.window, title="Choose parent for a new candidate review folder")
        if not parent: return
        destination = Path(parent) / (self.document["game_id"] + "-preview-" + maps.fingerprint(self.workbook)[:12])
        receipt = api.export_candidate(self.workbook, self.document, self.builder.keymaps[self.document["keymap_id"]], destination, self.appearance())
        self.note.set(f'Prepared {len(receipt["images"])} offline images and map sources in {destination}. Nothing published or applied.')

    def appearance(self):
        import GameToolOverlayAppearance as looks
        value,_=self.builder.library.store.load();style=looks.effective(looks.policy(value),self.document["game_id"])
        style["view"]=self.builder.view.get();style["background"]=self.document["presentation"]["background"]
        return style

    def close(self):
        if maps.fingerprint(self.workbook) != self.expected and not messagebox.askyesno("Close planning draft", "Close without saving the current planning edits?", parent=self.window): return
        self.window.destroy()
