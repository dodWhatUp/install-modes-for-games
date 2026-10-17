"""Optional Tk catalog view. Reads/prepares only; no launch, import or execution."""
from __future__ import annotations

import json
from GameToolCompactUI import FlowToolbar, ResponsiveGrid, ScrollableFrame


class CatalogPanel:
    def __init__(self, parent, service_factory, status):
        import tkinter as tk
        from tkinter import ttk

        self.tk, self.ttk = tk, ttk
        self.parent, self.service_factory, self.status = parent, service_factory, status
        self.service = None
        self.last_detail = self.last_plan = None
        self.last_plan_request = None
        self.fg_status = tk.StringVar(value="FG preflight: not checked")
        self.executable = tk.StringVar()
        self.native_settings = tk.StringVar()
        self.source = tk.StringVar(value="Catalog not loaded")
        self.filters = {key: tk.StringVar(value="All") for key in
                        ("kind", "category", "game", "status", "installation", "relationship")}
        self.filters["search"] = tk.StringVar()
        self.filters["sort"] = tk.StringVar(value="name")
        self.game_ids = {"All": None}
        self.factor_ids = {"None": None}

        bar = ttk.Frame(parent)
        bar.pack(fill="x")
        ttk.Label(bar, text="READ-ONLY CATALOG  •  Recorded evidence, not live inventory").pack(side="left")
        ttk.Button(bar, text="Reload catalog", command=self.reload).pack(side="right")
        ttk.Label(parent, textvariable=self.source, wraplength=1000).pack(anchor="w", pady=5)
        views = ttk.Notebook(parent)
        views.pack(fill="both", expand=True)
        self.browse_scroll, self.plan_scroll = ScrollableFrame(views), ScrollableFrame(views)
        browse, planner = self.browse_scroll.body, self.plan_scroll.body
        views.add(self.browse_scroll, text="Browse records")
        views.add(self.plan_scroll, text="Prepare comparison")

        form = ResponsiveGrid(browse)
        form.pack(fill="x")
        self.combos = {}
        labels = (("kind", "Kind"), ("category", "Category"), ("game", "Game"),
                  ("status", "Evidence"), ("installation", "Recorded install"),
                  ("relationship", "Relationship"), ("sort", "Sort"))
        for index, (key, label) in enumerate(labels):
            cell = ttk.Frame(form)
            form.add(cell)
            ttk.Label(cell, text=label).pack(anchor="w")
            combo = ttk.Combobox(cell, textvariable=self.filters[key], state="readonly", width=20)
            combo.pack(fill="x")
            combo.bind("<<ComboboxSelected>>", self.apply_filters)
            self.combos[key] = combo
        search_bar = ttk.Frame(browse)
        search_bar.pack(fill="x", pady=5)
        ttk.Label(search_bar, text="Search").pack(side="left")
        self.search_entry = ttk.Entry(search_bar, textvariable=self.filters["search"])
        self.search_entry.pack(side="left", fill="x", expand=True, padx=8)
        self.search_entry.bind("<Return>", self.apply_filters)
        ttk.Button(search_bar, text="Apply", command=self.apply_filters).pack(side="left")
        ttk.Button(search_bar, text="Clear filters", command=self.clear_filters).pack(side="left", padx=5)

        panes = ttk.Panedwindow(browse, orient="vertical")
        panes.pack(fill="both", expand=True)
        table_box, detail_box = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(table_box, weight=1)
        panes.add(detail_box, weight=1)
        columns = ("Name", "Entity", "Kind", "Evidence", "Recorded install")
        self.tree = ttk.Treeview(table_box, columns=columns, show="headings", selectmode="browse", height=6)
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=280 if column == "Name" else 130, minwidth=70)
        self.tree.grid(row=0, column=0, sticky="nsew")
        table_box.rowconfigure(0, weight=1)
        table_box.columnconfigure(0, weight=1)
        vertical = ttk.Scrollbar(table_box, command=self.tree.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(table_box, orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tree.bind("<<TreeviewSelect>>", self.show_selected)
        ttk.Button(detail_box, text="Copy record details", command=self.copy_details).pack(anchor="e", pady=3)
        self.detail_text = self._text(detail_box)
        self._write(self.detail_text, "Select a record. Sources, relationships and capabilities are inert data; measurements are unmeasured.")

        ttk.Label(planner, text="PREVIEW ONLY  •  No game, capture, installer, input or settings action is run.",
                  wraplength=970).pack(anchor="w", pady=5)
        plan_form = ResponsiveGrid(planner, max_columns=2, min_cell=260)
        plan_form.pack(fill="x")
        self.scope = tk.StringVar(value="process-idle")
        self.plan_game = tk.StringVar(value="All")
        self.factor_a, self.factor_b = tk.StringVar(value="None"), tk.StringVar(value="None")
        self.plan_combos = {}
        for index, (key, label, variable) in enumerate((
            ("scope", "Cost scope", self.scope), ("game", "Exact game (in-game only)", self.plan_game),
            ("a", "Factor A", self.factor_a), ("b", "Factor B (optional)", self.factor_b))):
            cell = ttk.Frame(plan_form)
            plan_form.add(cell)
            ttk.Label(cell, text=label).pack(anchor="w")
            combo = ttk.Combobox(cell, textvariable=variable, state="readonly", width=40)
            combo.pack(fill="x")
            combo.bind("<<ComboboxSelected>>", self.plan_changed)
            self.plan_combos[key] = combo
        self.plan_combos["scope"]["values"] = ("process-idle", "in-game")
        fg_form = ResponsiveGrid(planner, max_columns=2, min_cell=260)
        fg_form.pack(fill="x")
        for index, (label, variable) in enumerate((
            ("Rendering executable (optional full path; read only)", self.executable),
            ("Native settings JSON (optional; read only)", self.native_settings))):
            cell = ttk.Frame(fg_form)
            fg_form.add(cell)
            ttk.Label(cell, text=label).pack(anchor="w")
            ttk.Entry(cell, textvariable=variable).pack(fill="x")
            variable.trace_add("write", self.invalidate_plan)
        ttk.Label(planner, textvariable=self.fg_status, wraplength=970).pack(anchor="w", pady=3)
        plan_bar = FlowToolbar(planner)
        plan_bar.pack(fill="x", pady=7)
        plan_bar.add("Check FG (read only)", self.check_fg)
        plan_bar.add("Prepare plan (no execution)", self.prepare_plan)
        plan_bar.add("Copy plan", self.copy_plan)
        self.plan_text = self._text(planner)
        self._write(self.plan_text, "Choose one factor, or two for a 2×2 preview. Required hosts stay On; CPU/GPU/RAM/VRAM values remain null until measured separately.")
        self.reload()

    def _text(self, parent):
        box = self.ttk.Frame(parent)
        box.pack(fill="both", expand=True)
        text = self.tk.Text(box, wrap="word", height=7, font=("Consolas", 9), state="disabled")
        text.pack(side="left", fill="both", expand=True)
        scroll = self.ttk.Scrollbar(box, command=text.yview)
        scroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=scroll.set)
        return text

    @staticmethod
    def _write(widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))
        widget.configure(state="disabled")

    def _refuse(self, error):
        self.last_detail = self.last_plan = None
        self.last_plan_request = None
        self.fg_status.set("FG preflight: not current; comparison blocked")
        self.tree.delete(*self.tree.get_children())
        self._write(self.detail_text, "Unavailable. Reload a valid current catalog before using records.")
        self._write(self.plan_text, "No current plan. Reload required; nothing was executed.")
        self.source.set("Catalog unavailable or changed; explicit reload required.")
        self.status.set(f"Catalog refused: {error}")

    def reload(self):
        try:
            if self.service is None:
                self.service = self.service_factory()
                summary = self.service.reload()
            else:
                summary = self.service.reload()
            options = self.service.options()
            self.game_ids = {"All": None, **{f'{g["id"]} — {g["name"]}': g["id"] for g in options["games"]}}
            for key, source_key in (("kind", "kinds"), ("category", "categories"), ("status", "statuses"),
                                    ("installation", "installations"), ("relationship", "relationships"), ("sort", "sorts")):
                choices = options[source_key] if key == "sort" else ["All", *options[source_key]]
                self.combos[key]["values"] = choices
                if self.filters[key].get() not in choices:
                    self.filters[key].set("name" if key == "sort" else "All")
            game_choices = list(self.game_ids)
            self.combos["game"]["values"] = game_choices
            self.plan_combos["game"]["values"] = game_choices
            for variable in (self.filters["game"], self.plan_game):
                if variable.get() not in self.game_ids:
                    variable.set("All")
            self.last_detail = self.last_plan = None
            self.factor_a.set("None")
            self.factor_b.set("None")
            self.source.set(f'Catalog {summary["version"]} • source SHA-256 {summary["revision"][:16]}… • explicit reload; no live inventory implied')
            self.apply_filters()
            self.plan_changed()
        except Exception as error:
            self._refuse(error)

    def clear_filters(self):
        for key, variable in self.filters.items():
            variable.set("" if key == "search" else "name" if key == "sort" else "All")
        self.apply_filters()

    def apply_filters(self, event=None):
        try:
            if self.service is None:
                raise ValueError("Catalog not loaded")
            filters = {key: (None if value.get() == "All" else value.get()) for key, value in self.filters.items()}
            filters["game"] = self.game_ids[self.filters["game"].get()]
            nodes = self.service.list_nodes(**filters)
            self.tree.delete(*self.tree.get_children())
            self.last_detail = None
            self._write(self.detail_text, "Select a current record; earlier selection cleared.")
            for node in nodes:
                self.tree.insert("", "end", iid=node["id"], values=(node["name"], node["entity"], node.get("kind", "game"),
                    node.get("status", "unknown"), node.get("installation", {}).get("status", "not applicable")))
            self.status.set(f"Catalog: {len(nodes)} matching records. No application action or measurement performed.")
        except Exception as error:
            self._refuse(error)

    def show_selected(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        try:
            self.last_detail = self.service.details(selected[0])
            self._write(self.detail_text, self.last_detail)
        except Exception as error:
            self._refuse(error)

    def plan_changed(self, event=None):
        try:
            if self.service is None:
                raise ValueError("Catalog not loaded")
            self.invalidate_plan()
            scope, game = self.scope.get(), self.game_ids[self.plan_game.get()]
            nodes = self.service.list_nodes(kind="component" if scope == "process-idle" else "feature", game=game if scope == "in-game" else None)
            if scope == "process-idle":
                nodes = [node for node in nodes if node.get("idle_process", False)]
            self.factor_ids = {"None": None, **{f'{n["id"]} — {n["name"]}': n["id"] for n in nodes}}
            for key, variable in (("a", self.factor_a), ("b", self.factor_b)):
                self.plan_combos[key]["values"] = list(self.factor_ids)
                if variable.get() not in self.factor_ids:
                    variable.set("None")
        except Exception as error:
            self._refuse(error)

    def invalidate_plan(self, *unused):
        self.last_plan = self.last_plan_request = None
        self.fg_status.set("FG preflight: not checked for current selection")
        if hasattr(self, "plan_text"):
            self._write(self.plan_text, "Selection changed. Prepare a new current plan; nothing is executed.")

    def _request_values(self):
        scope = self.scope.get()
        return {"scope": scope, "game": self.game_ids[self.plan_game.get()] if scope == "in-game" else None,
                "factors": [self.factor_ids[v.get()] for v in (self.factor_a, self.factor_b) if v.get() != "None"],
                "executable": self.executable.get().strip() or None,
                "native_settings_path": self.native_settings.get().strip() or None}

    def _show_fg(self, receipt):
        self.fg_status.set(f'FG preflight: {receipt["status"]} — ' + "; ".join(receipt.get("reasons", [])))

    def check_fg(self):
        self.invalidate_plan()
        try:
            request = self._request_values()
            request.pop("factors")
            receipt = self.service.fg_preflight(**request)
            self._show_fg(receipt)
            self._write(self.plan_text, receipt)
            self.status.set("Read-only FG check complete. No plan, game or settings action executed.")
        except Exception as error:
            self._refuse(error)

    def prepare_plan(self):
        try:
            if self.service is None:
                raise ValueError("Catalog not loaded")
            request = self._request_values()
            self.last_plan = self.service.prepare_plan(**request)
            self.last_plan_request = request
            self._show_fg(self.last_plan["fg_preflight"])
            self._write(self.plan_text, self.last_plan)
            self.status.set(f'Plan {self.last_plan["status"]}; preview only, execution none, measurements unmeasured.')
        except Exception as error:
            if self.service is not None:
                try:
                    self.service.options()
                except Exception as freshness_error:
                    self._refuse(freshness_error)
                    return
            self.last_plan = None
            self.last_plan_request = None
            self.fg_status.set("FG preflight: not current; comparison blocked")
            self._write(self.plan_text, f"Plan refused: {error}. Nothing was executed.")
            self.status.set("Plan refused; verify current source and factor selection.")

    def _copy(self, value):
        if value is None:
            self.status.set("Nothing current to copy. Select a record or prepare a plan first.")
            return
        try:
            # Recheck even if a previous view still looks current after an external edit.
            self.service.options()
            if value.get("catalog_source", {}).get("revision") != self.service.revision:
                raise ValueError("Displayed data belongs to an older catalog revision; reload required")
            root = self.parent.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False))
            self.status.set("Copied current catalog data only; no launch, upload or execution.")
        except Exception as error:
            self._refuse(error)

    def copy_details(self):
        self._copy(self.last_detail)

    def copy_plan(self):
        if self.last_plan is not None:
            try:
                if self.last_plan_request != self._request_values():
                    self.invalidate_plan()
                    self.status.set("Selection changed; prepare a fresh plan before copying.")
                    return
                if self.last_plan["scope"] == "in-game":
                    was_ready = self.last_plan["comparison_ready"]
                    # A displayed PASS is never an authorization or reusable proof.
                    self.prepare_plan()
                    if self.last_plan is None:
                        return
                    if was_ready and not self.last_plan["comparison_ready"]:
                        self.status.set("Fresh FG check blocked the plan. Clipboard unchanged; review the reasons.")
                        return
            except Exception as error:
                self._refuse(error)
                return
        self._copy(self.last_plan)

    def close(self):
        self.browse_scroll.close()
        self.plan_scroll.close()
