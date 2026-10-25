"""Goal-oriented presentation for the existing Hub panels.

This module owns navigation and view state only. Its registry contains stable
route IDs and descriptions, never executable commands, input, provider starts,
settings mutations or automation authority. Existing panels remain their owners.
"""
from __future__ import annotations

import hashlib
import re
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

VERSION = "0.4.1"
SIDEBAR_DEFAULT = 256
SIDEBAR_MIN = 150
SIDEBAR_MAX = 520
CONTENT_MIN = 360
DOMAINS = (
    "Performance & reports",
    "Controls & overlays",
    "Diagnose & stability",
    "Library & maintenance",
)
VIEWS = ("Goals", "Features", "Original tabs")
_ID = re.compile(r"^[a-z][a-z0-9.-]{0,79}$")
_COMPACT_LABELS = {
    "page.studio": "Studio · input & pictures",
    "page.catalog": "Catalog & FG preflight",
    "page.data": "User data & backups",
    "goal.input-pictures": "Configure input & pictures",
    "goal.prepare-stability": "Prepare stability · offline",
    "goal.graphics-plan": "Plan graphics comparison",
}


def _record(identifier, title, domain, route, summary, scope, keywords=""):
    return dict(id=identifier, title=title, domain=domain, route=route,
                summary=summary, scope=scope, keywords=keywords)


DEFAULT_FEATURES = (
    _record('page.profiles', 'Game profiles · activate & startup', DOMAINS[1], 'profiles',
            'Save the published setup for each game, activate or stop its Overlay and choose automatic startup.',
            'Runtime selection only · game/native changes retain separate reviewed owners', 'game profile auto startup activate deactivate overlay azeron'),
    _record("page.comparison", "Saved-result comparison", DOMAINS[0], "comparison",
            "Import original saved reports, retain provider definitions and compare compatible results.",
            "Saved reports only · no benchmark starts", "benchmark fps report csv frameview presentmon import"),
    _record("page.reports", "Reports & original files", DOMAINS[0], "reports",
            "Organize selected saved reports and inspect their original bytes and definitions.",
            "Saved-file workspace · capture stays stopped", "export archive benchmark results"),
    _record("page.sensors", "Sensor connections", DOMAINS[0], "sensors",
            "Inspect the existing sensor connection panel; viewing it is not a new recording or time series.",
            "Connection view · no recording starts", "cpu gpu ram vram afterburner telemetry"),
    _record("page.rtss", "RTSS connection", DOMAINS[0], "rtss",
            "Inspect the existing RTSS connection panel without starting a benchmark.",
            "Connection view · no capture starts", "rtss osd presentation framerate"),
    _record("page.studio", "Studio · input & picture controls", DOMAINS[1], "studio",
            "Open the preserved native AHK Studio controls, picture buttons and display features.",
            "Explicit Studio controls · Game Input remains Off until authorized", "ahk hotkeys input keyboard picture buttons mic hud canvas"),
    _record("page.overlays", "Overlay groups & keymaps", DOMAINS[1], "overlays",
            "View and configure display groups, keymap images and explicit display selection. Native profiles remain owned by their software.",
            "Display workspace · selection is not observed native-layer telemetry", "azeron keys actions combined layer image maps"),
    _record("page.sessions", "Offline sessions & recovery", DOMAINS[2], "sessions",
            "Prepare offline scenarios, provider-health mocks, diagnostic dry-runs and saved crash-evidence recovery.",
            "Offline preparation · no scenario, game or recorder runs", "stability crash journal diagnostics workflow rollback readiness provider health"),
    _record("page.catalog", "Catalog & comparison preflight", DOMAINS[3], "catalog",
            "Read tool relationships and prepare comparisons with the existing FG/memory gate. Unknown or Dynamic MFG blocks live performance comparisons.",
            "Read-only planning · runtime checks and comparisons deferred", "mods graphics fg mfg dynamic reshade renodx optiscaler ultra dlss"),
    _record("page.tools", "External-tool connections", DOMAINS[3], "tools",
            "Review the original tool registry and connection controls. Navigation does not launch a tool.",
            "Existing explicit actions only · no automatic launches", "library installed applications programs manager"),
    _record("page.updates", "Updates & rollback", DOMAINS[3], "updates",
            "Inspect trusted local update packages and the existing explicit in-place update or rollback controls.",
            "Explicit package controls · no background downloads or installs", "version installation maintenance upgrade"),
    _record("page.data", "User data & portable backups", DOMAINS[3], "data",
            "Inspect the shared data workspace, migration and portable-backup controls when this optional panel is available.",
            "Private data workspace · importing never grants execution authority", "profile backup restore export import cloud migration sync settings"),
    _record("page.guide", "Guide & safety boundaries", DOMAINS[3], "guide",
            "Read the existing guide and supported operations before using a feature.",
            "Information only", "help instructions how learning"),
)

DEFAULT_GOALS = (
    _record("goal.compare-saved", "Compare saved results", DOMAINS[0], "comparison",
            "Use report adapters and comparison views for results already saved by established providers.",
            "Saved results only · games, benchmarks and recording stay stopped", "fps lows frametime latency overhead benchmark report import"),
    _record("goal.organize-reports", "Organize report evidence", DOMAINS[0], "reports",
            "Find the report archive and preserve original data before an offline comparison.",
            "Saved-file review only", "export results archive csv json"),
    _record("goal.input-pictures", "Configure input & picture display", DOMAINS[1], "studio",
            "Open the preserved Studio interface for explicit picture/input configuration. This route does not start the guarded game-input module.",
            "Existing Studio settings and profiles preserved · Game Input is opt-in", "ahk keyboard hotkeys picture buttons mic canvas hud"),
    _record("goal.keymap-display", "Choose a keymap or overlay", DOMAINS[1], "overlays",
            "Open the display workspace to choose a group, keymap and view without remapping device outputs.",
            "Display selection only · native input profiles are unchanged", "azeron layer image keys actions combined"),
    _record("goal.prepare-stability", "Prepare a stability check · offline", DOMAINS[2], "sessions",
            "Review saved crash evidence and prepare a scenario or diagnostic dry-run. Live stability testing is a later authorized step.",
            "Offline preparation · no game launch, capture or scenario execution", "crash stable journal recovery provider health readiness plan"),
    _record("goal.graphics-plan", "Plan graphics comparison · read-only", DOMAINS[2], "catalog",
            "Review the catalog, dependency-preserving combinations and FG/memory preflight. Live comparisons remain blocked while effective FG is unverified or Dynamic MFG is active.",
            "Read-only plan · no graphics changes or benchmark runs", "graphics settings stable performance mfg fg dynamic dlss reshade renodx texture vram"),
    _record("goal.update", "Update without reinstalling", DOMAINS[3], "updates",
            "Open the explicit local-package update and rollback workspace. Opening this route never applies a package.",
            "Explicit update controls · user data stays separate from app versions", "version upgrade rollback maintenance install"),
    _record("goal.portable-data", "Back up or move my user data", DOMAINS[3], "data",
            "Open the optional portable user-data workspace. Old formats must be inspected and migrated through their owned schemas, not replaced blindly.",
            "Explicit data controls · cloud credentials and synchronization are separate", "export import cloud sync profiles backup restore migration settings"),
)


class FeatureRegistry:
    """Reusable static descriptions and stable route IDs, with no command fields."""

    def __init__(self, features=None, goals=None):
        self.features = self._validate(DEFAULT_FEATURES if features is None else features)
        self.goals = self._validate(DEFAULT_GOALS if goals is None else goals)
        identifiers = [r["id"] for r in self.features + self.goals]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Navigation IDs must be unique across goals and features")
        self._records = {r["id"]: r for r in self.features + self.goals}

    @staticmethod
    def _validate(records):
        values = list(records)
        if len(values) > 200:
            raise ValueError("Navigation registry exceeds 200 records per view")
        result = []
        for value in values:
            if not isinstance(value, dict) or set(value) != {"id", "title", "domain", "route", "summary", "scope", "keywords"}:
                raise ValueError("Navigation records contain descriptions only")
            if any(not isinstance(value[k], str) or len(value[k]) > 2000 for k in value):
                raise ValueError("Navigation fields must be bounded text")
            if not _ID.fullmatch(value["id"]) or not _ID.fullmatch(value["route"]):
                raise ValueError("Navigation IDs and route IDs must be stable identifiers")
            if value["domain"] not in DOMAINS or not value["title"].strip():
                raise ValueError("Navigation needs a known domain and a visible label")
            result.append(dict(value))
        return tuple(result)

    def get(self, identifier):
        record = self._records.get(identifier)
        return dict(record) if record is not None else None

    def records(self, view="Goals", query=""):
        if view not in ("Goals", "Features"):
            raise ValueError("Registry view must be Goals or Features")
        terms = str(query).casefold().split()
        source = self.goals if view == "Goals" else self.features
        return [dict(r) for r in source if all(term in " ".join(r.values()).casefold() for term in terms)]

    def feature_for_route(self, route):
        return next((dict(r) for r in self.features if r["route"] == route), None)


class Workspace:
    """Presentation shell around an existing Notebook; navigation selects only.

    Create before the Notebook, pack ``frame`` and create the existing Notebook
    under ``content``. Call ``attach(notebook, route_tabs)`` once panels exist.
    No panel is destroyed or recreated when changing navigation view or details.
    """

    def __init__(self, parent, status=None, registry=None):
        self.parent, self.root = parent, parent.winfo_toplevel()
        self.status = status
        self.registry = registry or FeatureRegistry()
        self.notebook = None
        self.modern = None
        self.route_tabs = {}
        self.current_route = None
        self.current_item = None
        self._muted = False
        self._search_before = ""
        self._notebook_binding = None
        self._key_binding = None
        self._normal_notebook_style = "TNotebook"
        self._rows = {}
        self.presentation = "Professional"
        self._available_width = 1120
        self._layout_busy = False
        self.sidebar_width = SIDEBAR_DEFAULT
        self._navigation_forced = False
        self._sash_job = None
        self._tip_job = None
        self._tip = None
        self._tip_row = None
        self._closed = False
        self.view = tk.StringVar(master=parent, value="Goals")
        self.query = tk.StringVar(master=parent)
        self.show_details = tk.BooleanVar(master=parent, value=False)
        self.show_navigation = tk.BooleanVar(master=parent, value=True)
        self.show_tabs = tk.BooleanVar(master=parent, value=False)
        self.active_label = tk.StringVar(master=parent, value="Workspace")
        self.scope_label = tk.StringVar(master=parent, value="Navigation opens an existing page only · no operation starts")
        self.result_label = tk.StringVar(master=parent)
        self.description = tk.StringVar(master=parent)

        style = ttk.Style(self.root)
        style.configure("Workspace.Treeview", rowheight=29, font=("Segoe UI", 10))
        style.configure("Workspace.Header.TLabel", font=("Segoe UI", 11, "bold"))
        self._hidden_style = "Workspace" + str(id(self)) + ".TNotebook"
        style.layout(self._hidden_style + ".Tab", [])

        self.frame = ttk.Frame(parent)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(1, weight=1)
        toolbar = self.toolbar = ttk.Frame(self.frame, padding=(10, 6))
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.columnconfigure(1, weight=1)
        self.search_label = ttk.Label(toolbar, text="Find a goal or feature")
        self.search_label.grid(row=0, column=0, sticky="w", padx=(0, 9))
        self.selector = ttk.Combobox(toolbar, textvariable=self.query, width=38)
        self.selector.grid(row=0, column=1, sticky="ew")
        self.selector.bind("<<ComboboxSelected>>", self._commit_selector)
        self.selector.bind("<Return>", self._commit_selector)
        self.selector.bind("<Escape>", self._cancel_search)
        self.selector.bind("<FocusIn>", self._search_entered)
        self.navigation_button = ttk.Button(toolbar, text="Hide sidebar", command=self.toggle_navigation, takefocus=True)
        self.navigation_button.grid(row=0, column=2, sticky="e", padx=(9, 0))
        menu_button = ttk.Menubutton(toolbar, text="View ▾")
        menu_button.grid(row=0, column=3, sticky="e", padx=(9, 0))
        view_menu = tk.Menu(menu_button, tearoff=False)
        for view in VIEWS:
            view_menu.add_radiobutton(label=view, variable=self.view, value=view, command=self._view_changed)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show navigation", variable=self.show_navigation, command=self._navigation_changed)
        view_menu.add_checkbutton(label="Show original tab bar", variable=self.show_tabs, command=self._tab_visibility)
        view_menu.add_checkbutton(label="Show route details", variable=self.show_details, command=self._visibility_changed)
        view_menu.add_separator()
        view_menu.add_command(label="Narrow sidebar", command=lambda: self.set_sidebar_width(170))
        view_menu.add_command(label="Reset sidebar width", command=lambda: self.set_sidebar_width(SIDEBAR_DEFAULT))
        view_menu.add_command(label="Reset view", command=self.reset_view)
        menu_button.configure(menu=view_menu)
        self.view_menu = view_menu

        self.splitter = ttk.Panedwindow(self.frame, orient="horizontal")
        self.splitter.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.sidebar = ttk.Frame(self.splitter, padding=(6, 3, 6, 8), width=SIDEBAR_DEFAULT)
        self.splitter.add(self.sidebar, weight=0)
        # Keep navigation compact when an unavailable/extension label is long;
        # horizontal scrolling reveals all text without squeezing the panel.
        self.sidebar.grid_propagate(False)
        self.sidebar.columnconfigure(0, weight=1)
        self.sidebar.rowconfigure(2, weight=1)
        self.view_label = ttk.Label(self.sidebar, textvariable=self.view, style="Workspace.Header.TLabel")
        self.view_label.grid(row=0, column=0, sticky="w", pady=(0, 3))
        self.result_widget = ttk.Label(self.sidebar, textvariable=self.result_label, wraplength=220)
        self.result_widget.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        self.tree = ttk.Treeview(self.sidebar, show="tree", selectmode="browse", style="Workspace.Treeview", height=12)
        self.tree.column("#0", width=242, minwidth=210, stretch=True)
        self.tree.grid(row=2, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(self.sidebar, command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.horizontal_scroll = ttk.Scrollbar(self.sidebar, orient="horizontal", command=self.tree.xview)
        self.horizontal_scroll.grid(row=3, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=self.horizontal_scroll.set)
        self.tree.tag_configure("domain", font=("Segoe UI", 10, "bold"))
        self.tree.bind("<<TreeviewSelect>>", self._tree_selected)
        self.tree.bind("<Return>", self._tree_selected)
        self.tree.bind("<Escape>", self._cancel_search)
        self.tree.bind("<Motion>", self._hover_route, add="+")
        self.tree.bind("<Leave>", self._hide_route_tip, add="+")
        self.tree.bind("<ButtonPress>", self._hide_route_tip, add="+")
        self.tree.bind("<MouseWheel>", self._hide_route_tip, add="+")
        self.tree.bind("<Button-4>", self._hide_route_tip, add="+")
        self.tree.bind("<Button-5>", self._hide_route_tip, add="+")
        self.details_box = ttk.Frame(self.sidebar, padding=(0, 9, 0, 0))
        self.details_box.grid(row=4, column=0, columnspan=2, sticky="ew")
        ttk.Label(self.details_box, text="Route details", style="Workspace.Header.TLabel").pack(anchor="w")
        self.details_text = ttk.Label(self.details_box, textvariable=self.description, wraplength=245, justify="left")
        self.details_text.pack(anchor="w", fill="x", pady=(4, 0))
        self.content = ttk.Frame(self.splitter)
        self.splitter.add(self.content, weight=1)
        self.splitter.bind("<Configure>", self._splitter_resized)
        self.splitter.bind("<ButtonRelease-1>", self._sash_released, add="+")
        self.splitter.bind("<Double-Button-1>", self._sash_reset, add="+")
        breadcrumb = self.breadcrumb = ttk.Frame(self.frame, padding=(10, 5))
        breadcrumb.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.active_widget = ttk.Label(breadcrumb, textvariable=self.active_label, style="Workspace.Header.TLabel", wraplength=1050)
        self.active_widget.pack(anchor="w")
        self.scope_widget = ttk.Label(breadcrumb, textvariable=self.scope_label, wraplength=1050)
        self.scope_widget.pack(anchor="w", pady=(3, 0))
        self._query_trace = self.query.trace_add("write", self._filter_changed)
        self.frame.bind("<Configure>", self._resize)
        self._visibility_changed()
        self._key_binding = self.root.bind("<Control-k>", self._focus_search, add="+")
        self._rebuild()

    def attach(self, notebook, route_tabs):
        if self.notebook is not None:
            raise ValueError("Workspace is already attached")
        actual = set(notebook.tabs())
        resolved = {}
        for route, tab in route_tabs.items():
            if not isinstance(route, str) or not _ID.fullmatch(route) or str(tab) not in actual:
                raise ValueError("Routes must resolve to existing Notebook panels")
            if str(tab) in resolved.values():
                raise ValueError("A Notebook page needs one stable route owner")
            resolved[route] = str(tab)
        self.notebook, self.route_tabs = notebook, resolved
        self._normal_notebook_style = notebook.cget("style") or "TNotebook"
        self._notebook_binding = notebook.bind("<<NotebookTabChanged>>", self._notebook_changed, add="+")
        self._tab_visibility()
        self._notebook_changed()
        self._rebuild()

    def route(self, identifier):
        """Select the resolved panel only; returns False on missing/disabled pages."""
        record = self._rows.get(identifier) or self.registry.get(identifier)
        if record is None:
            self._notice("Unknown navigation item; current page kept")
            return False
        target = self.route_tabs.get(record["route"])
        if self.notebook is None or target is None or target not in self.notebook.tabs():
            self._notice("Unavailable in this installation: " + record["title"] + "; current page kept")
            return False
        if self.notebook.tab(target, "state") == "disabled":
            self._notice("This existing page is disabled; current page kept")
            return False
        self.current_route, self.current_item = record["route"], record["id"]
        self.notebook.select(target)
        self._show_record(record)
        self._select_active_row()
        return True

    def set_view(self, view):
        if view not in VIEWS:
            raise ValueError("Unsupported workspace view")
        self.view.set(view)
        self._view_changed()

    def export_view(self):
        return dict(schema=1, view=self.view.get(), show_details=bool(self.show_details.get()),
                    show_navigation=bool(self.show_navigation.get()), show_original_tabs=bool(self.show_tabs.get()),
                    sidebar_width=self.sidebar_width)

    def restore_view(self, value):
        if not isinstance(value, dict) or value.get("schema") != 1 or value.get("view") not in VIEWS:
            raise ValueError("Unsupported workspace presentation schema")
        for key in ("show_details", "show_navigation", "show_original_tabs"):
            if type(value.get(key)) is not bool:
                raise ValueError("Workspace visibility must be a Boolean")
        width = value.get("sidebar_width", SIDEBAR_DEFAULT)
        if type(width) is not int or not SIDEBAR_MIN <= width <= SIDEBAR_MAX:
            raise ValueError("Sidebar width must be an integer between 150 and 520")
        self.sidebar_width = width
        self._navigation_forced = False
        self.view.set(value["view"])
        self.show_details.set(value["show_details"])
        self.show_navigation.set(value["show_navigation"])
        self.show_tabs.set(value["show_original_tabs"])
        self.query.set("")
        self._visibility_changed()
        self._tab_visibility()
        self._rebuild()

    def reset_view(self):
        self.restore_view(dict(schema=1, view="Goals", show_details=False,
                               show_navigation=True, show_original_tabs=False))

    def _original_records(self):
        if self.notebook is None:
            return []
        reverse = {tab: route for route, tab in self.route_tabs.items()}
        records = []
        for tab in self.notebook.tabs():
            title = self.notebook.tab(tab, "text")
            route = reverse.get(tab)
            if route is None:
                # Original extension pages remain accessible even before a
                # future author supplies a registered stable feature ID.
                route = "original-tab." + hashlib.sha256(str(title).encode()).hexdigest()[:16]
                if route in self.route_tabs and self.route_tabs[route] != tab:
                    route += "." + str(len(records))
                self.route_tabs[route] = tab
            feature = self.registry.feature_for_route(route)
            records.append(_record("tab." + route, title,
                feature["domain"] if feature else DOMAINS[3], route,
                feature["summary"] if feature else "Open the existing original page. Its own controls remain its owner.",
                feature["scope"] if feature else "Navigation only · existing page controls are unchanged"))
        terms = self.query.get().casefold().split()
        return [r for r in records if all(t in " ".join(r.values()).casefold() for t in terms)]

    def _rebuild(self):
        self._hide_route_tip()
        records = self._original_records() if self.view.get() == "Original tabs" else self.registry.records(self.view.get(), self.query.get())
        self._rows = {r["id"]: r for r in records}
        self._muted = True
        try:
            self.tree.delete(*self.tree.get_children())
            labels = list(DOMAINS)
            for number, domain in enumerate(DOMAINS):
                rows = [r for r in records if r["domain"] == domain]
                if not rows:
                    continue
                parent = "domain-" + str(number)
                self.tree.insert("", "end", iid=parent, text=domain, open=True, tags=("domain",))
                for record in rows:
                    available = record["route"] in self.route_tabs if self.notebook is not None else False
                    short_title = _COMPACT_LABELS.get(record["id"], record["title"])
                    text = ("Unavailable · " if not available else "") + short_title
                    self.tree.insert(parent, "end", iid=record["id"], text=text)
                    labels.append(text)
            measurement = tkfont.Font(root=self.root, family="Segoe UI", size=10)
            # Indentation + glyph padding is included. Very long future labels
            # remain scrollable instead of enlarging the whole sidebar.
            width = max(222, min(700, max((measurement.measure(t) for t in labels), default=190) + 48))
            # Fit ordinary labels at the current Windows font/DPI scale. A
            # fixed pixel sidebar clips even compact names at 150% scaling.
            self.tree.column("#0", width=width, minwidth=210, stretch=False)
            self.selector.configure(values=[r["title"] for r in records])
            self.result_label.set(f"{len(records)} routes · opens a page only" if records else "No matching routes · current page unchanged")
            self._select_active_row()
        finally:
            self._muted = False
        if self.modern is not None:
            self.modern.refresh()

    def _filter_changed(self, *_):
        self._rebuild()

    def _select_active_row(self):
        previous = self._muted
        self._muted = True
        try:
            item = self.current_item if self.current_item in self._rows else next((r["id"] for r in self._rows.values() if r["route"] == self.current_route), None)
            if item and self.tree.exists(item):
                # Treeview queues its event until after this guard is released.
                # Avoid setting an identical selection: that would feed the
                # selection -> route -> selection loop on some Tk builds.
                if self.tree.selection() != (item,):
                    self.tree.selection_set(item)
                self.tree.focus(item)
            else:
                if self.tree.selection():
                    self.tree.selection_remove(*self.tree.selection())
        finally:
            self._muted = previous

    def _tree_selected(self, _event=None):
        self._hide_route_tip()
        if self._muted:
            return
        selected = self.tree.selection()
        if selected and selected[0] in self._rows:
            record = self._rows[selected[0]]
            if record["route"] != self.current_route:
                self.route(selected[0])
        return "break" if _event is not None and getattr(_event, "keysym", None) == "Return" else None

    def _commit_selector(self, _event=None):
        query = self.query.get().strip().casefold()
        matches = [r for r in self._rows.values() if r["title"].casefold() == query]
        if not matches and len(self._rows) == 1:
            matches = list(self._rows.values())
        if len(matches) != 1:
            self._notice("Choose one matching route or refine the search; current page kept")
            return "break"
        self.route(matches[0]["id"])
        return "break"

    def _search_entered(self, _event=None):
        self._search_before = self.query.get()

    def _cancel_search(self, _event=None):
        self.query.set("")
        self._search_before = ""
        self._notice("Search cancelled · current page unchanged")
        return "break"

    def _focus_search(self, _event=None):
        focused = self.root.focus_get()
        # Never forward input to native AHK children, a modal dialog or another
        # top-level. This binding only changes focus in this Tk workspace.
        if self.root.grab_current() is not None or (focused is not None and focused.winfo_toplevel() != self.root):
            return
        if self.notebook is not None and self.route_tabs.get("studio") == self.notebook.select() and not self.home_visible:
            return
        self.selector.focus_set()
        self.selector.selection_range(0, "end")
        self._notice("Search goals or features · Enter opens one route · Escape cancels")
        return "break"

    def _notebook_changed(self, _event=None):
        if self.notebook is None:
            return
        route = next((r for r, tab in self.route_tabs.items() if tab == self.notebook.select()), None)
        if route is None:
            self._original_records()
            route = next((r for r, tab in self.route_tabs.items() if tab == self.notebook.select()), None)
        self.current_route = route
        record = self.registry.get(self.current_item) if self.current_item else None
        if record is None or record["route"] != route:
            record = self.registry.feature_for_route(route)
            self.current_item = record["id"] if record else None
        if record is not None:
            self._show_record(record)
        elif route:
            self.active_label.set("Original page / " + self.notebook.tab(self.notebook.select(), "text"))
            self.scope_label.set("Navigation only · existing page controls are unchanged")
            self.description.set("This extension remains accessible through Original tabs.")
        self._select_active_row()

    def _show_record(self, record):
        self.active_label.set(record["domain"] + " / " + record["title"])
        self.scope_label.set(record["scope"])
        self.description.set(record["summary"])
        if self.modern is not None:
            self.modern.show_page(record)

    @property
    def home_visible(self):
        return bool(self.modern is not None and self.modern.active and self.modern.home_visible)

    def reveal_selected_page(self):
        """A numbered navigation shortcut can reveal an already selected tab."""
        if self.home_visible:
            self._notebook_changed()

    def _notice(self, value):
        self.result_label.set(value)

    def _view_changed(self):
        self.query.set("")
        self._tab_visibility()
        self._rebuild()

    def _tab_visibility(self):
        if self.notebook is not None:
            show = self.show_tabs.get() or self.view.get() == "Original tabs"
            # Style layouts are theme-local. Reestablish the hidden tab layout
            # after an interface mode switches the native/modern ttk theme.
            ttk.Style(self.root).layout(self._hidden_style + ".Tab", [])
            self.notebook.configure(style=self._normal_notebook_style if show else self._hidden_style)

    def _visibility_changed(self):
        # Auto collapse is presentation only. The manual choice remains saved;
        # the search selector always offers every route at narrow widths.
        visible = self.show_navigation.get() and (self._navigation_forced or self._available_width >= 690)
        present = str(self.sidebar) in self.splitter.panes()
        if visible and not present:
            self.splitter.insert(0, self.sidebar, weight=0)
        elif not visible and present:
            self._hide_route_tip()
            self.splitter.forget(self.sidebar)
        self.navigation_button.configure(text="Hide sidebar" if visible else "Show sidebar")
        self._schedule_sash()
        if self.show_details.get():
            self.details_box.grid()
        else:
            self.details_box.grid_remove()
        if self.modern is not None and self.modern.active:
            self.modern.details_changed()

    def toggle_navigation(self):
        """Explicit Show works even below the automatic-collapse threshold."""
        visible = str(self.sidebar) in self.splitter.panes()
        self.show_navigation.set(not visible)
        self._navigation_forced = not visible
        self._visibility_changed()

    def _navigation_changed(self):
        self._navigation_forced = bool(self.show_navigation.get())
        self._visibility_changed()

    def set_sidebar_width(self, width):
        if type(width) is not int or not SIDEBAR_MIN <= width <= SIDEBAR_MAX:
            raise ValueError("Sidebar width must be an integer between 150 and 520")
        self.sidebar_width = width
        self._schedule_sash()

    def _schedule_sash(self):
        if not self._closed and self._sash_job is None:
            self._sash_job = self.frame.after_idle(self._place_sash)

    def _splitter_resized(self, event):
        if event.widget is self.splitter:
            self._schedule_sash()

    def _place_sash(self):
        self._sash_job = None
        if len(self.splitter.panes()) < 2:
            return
        # Shrinking the window must not overwrite the user's preferred width.
        limit = max(SIDEBAR_MIN, self.splitter.winfo_width() - CONTENT_MIN)
        width = min(self.sidebar_width, limit)
        self.sidebar.configure(width=width)
        self.splitter.sashpos(0, width)
        self.details_text.configure(wraplength=max(100, width - 24))
        self.result_widget.configure(wraplength=max(100, width - 24))

    def _sash_released(self, event):
        if len(self.splitter.panes()) < 2:
            return
        # Tk's class handler already moved the sash. Clamp only this owned
        # presentation pane; never resize native controls or save profiles.
        width = self.splitter.sashpos(0)
        self.sidebar_width = max(SIDEBAR_MIN, min(SIDEBAR_MAX, width))
        self._schedule_sash()

    def _sash_reset(self, event):
        if self.splitter.identify(event.x, event.y) != "":
            self.set_sidebar_width(SIDEBAR_DEFAULT)
            return "break"

    def _hover_route(self, event):
        row = self.tree.identify_row(event.y)
        if row == self._tip_row:
            return
        self._hide_route_tip()
        self._tip_row = row or None
        if row:
            self._tip_job = self.frame.after(450, lambda: self._show_route_tip(row))

    def _show_route_tip(self, row):
        self._tip_job = None
        if row != self._tip_row or not self.tree.winfo_ismapped() or not self.tree.exists(row):
            return
        record = self._rows.get(row)
        # Authored registry descriptions only; no profile values or file data.
        text = record["title"] + "\n" + record["scope"] if record else self.tree.item(row, "text")
        if not text:
            return
        tip = self._tip = tk.Toplevel(self.root)
        tip.overrideredirect(True)
        ttk.Label(tip, text=text, padding=(10, 7), wraplength=390, justify="left", relief="solid").pack()
        tip.update_idletasks()
        box = self.tree.bbox(row)
        x = min(self.sidebar.winfo_rootx() + self.sidebar.winfo_width() + 8, self.root.winfo_screenwidth() - tip.winfo_reqwidth() - 8)
        y = self.tree.winfo_rooty() + (box[1] + box[3] if box else 0)
        y = min(y, self.root.winfo_screenheight() - tip.winfo_reqheight() - 8)
        tip.geometry(f"+{max(0,x)}+{max(0,y)}")
        tip.bind("<Leave>", self._hide_route_tip)

    def _hide_route_tip(self, _event=None):
        if self._tip_job:
            self.frame.after_cancel(self._tip_job)
            self._tip_job = None
        if self._tip:
            self._tip.destroy()
            self._tip = None
        self._tip_row = None

    def _resize(self, event):
        if event.widget is self.frame:
            self._available_width = event.width
            wrap = max(240, event.width - 28)
            self.active_widget.configure(wraplength=wrap)
            self.scope_widget.configure(wraplength=wrap)
            # Put the label above the editable search field at narrow widths.
            narrow = event.width < 880
            self.search_label.grid_configure(row=0, column=0, columnspan=4 if narrow else 1)
            self.selector.grid_configure(row=1 if narrow else 0, column=0 if narrow else 1, columnspan=2 if narrow else 1)
            self.navigation_button.grid_configure(row=1 if narrow else 0)
            self.view_menu.master.grid_configure(row=1 if narrow else 0)
            self.toolbar.columnconfigure(0, weight=int(narrow))
            self.toolbar.columnconfigure(1, weight=int(not narrow))
            self._visibility_changed()

    def apply_mode_defaults(self, mode):
        self.view.set({"Modern": "Features", "Professional": "Goals", "Compact": "Features", "Classic": "Original tabs"}[mode])
        self.show_navigation.set(mode in ("Modern", "Professional"))
        self.show_tabs.set(mode == "Classic")
        self.show_details.set(False)
        self.sidebar_width = SIDEBAR_DEFAULT
        self._navigation_forced = False
        self._tab_visibility()
        self._rebuild()

    def set_presentation(self, mode):
        if mode not in ("Modern", "Professional", "Compact", "Classic"):
            raise ValueError("Unsupported presentation")
        if mode != "Modern" and self.modern is not None:
            self.modern.deactivate()
        if mode == "Modern" and self.modern is None:
            if self.notebook is None:
                raise ValueError("Modern presentation needs attached existing panels")
            from GameToolModernUI import ModernSurface
            self.modern = ModernSurface(self)
        self.presentation = mode
        # Professional has contextual heading above its work area. Compact
        # uses a minimal bottom breadcrumb; Classic keeps the original tabs.
        self.breadcrumb.grid(row=1 if mode in ("Modern", "Professional") else 2, column=0, columnspan=2, sticky="ew")
        row = 2 if mode in ("Modern", "Professional") else 1
        self.splitter.grid_configure(row=row)
        self.frame.rowconfigure(1, weight=int(row == 1))
        self.frame.rowconfigure(2, weight=int(row == 2))
        self.toolbar.configure(padding=(10, 8) if mode == "Professional" else (6, 3))
        self.breadcrumb.configure(padding=(10, 6) if mode == "Professional" else (6, 3))
        if mode == "Modern":
            self.modern.activate()
            if self.modern.home_visible:
                self.breadcrumb.grid_remove()
        self._visibility_changed()

    def close(self):
        self._closed = True
        if self.modern is not None:
            self.modern.close()
        self._hide_route_tip()
        if self._sash_job:
            self.frame.after_cancel(self._sash_job)
            self._sash_job = None
        if self.notebook is not None and self._notebook_binding:
            self.notebook.unbind("<<NotebookTabChanged>>", self._notebook_binding)
        if self._key_binding:
            self.root.unbind("<Control-k>", self._key_binding)
        if self._query_trace:
            self.query.trace_remove("write", self._query_trace)
        self._notebook_binding = self._key_binding = self._query_trace = None
