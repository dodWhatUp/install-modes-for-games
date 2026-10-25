"""Modern presentation surface. Routes select existing pages, never operations.

The original Notebook and every editor remain alive. Home/category/search views
are siblings of that Notebook; they never clone or replace a feature's engine.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, font as tkfont
from GameToolCompactUI import ScrollableFrame, FlowToolbar
from GameToolWorkspace import DOMAINS

VERSION = "0.1.3"
COLORS = dict(background="#f3f5f8", surface="#ffffff", ink="#18283b",
              muted="#526477", line="#dce3eb", accent="#076b68",
              rail="#172b40", rail_text="#edf3f9", rail_muted="#bed0e2",
              selected="#264862", hover="#e6f1ef")
CATEGORIES = (
    ("Results", "Compare results", "Import saved reports and understand the differences.",
     ("Compare saved results", "Organize report evidence")),
    ("Controls", "Set up controls", "Pictures, keymaps, overlays and your existing input tools.",
     ("Input & picture buttons", "Keymaps & overlays")),
    ("Diagnostics", "Investigate a problem", "Prepare a stability check or a graphics comparison safely.",
     ("Stability & recovery", "Plan graphics comparison")),
    ("Library", "Manage tools & data", "Keep your installation, settings and backups together.",
     ("Updates & rollback", "User data & backups")),
)


def contrast(a, b):
    """WCAG relative-luminance contrast, used by offline design tests."""
    def luminance(color):
        rgb = [int(color[i:i+2], 16)/255 for i in (1, 3, 5)]
        linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
        return sum(v*w for v, w in zip(linear, (.2126, .7152, .0722)))
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi+.05)/(lo+.05)


def apply_theme(root):
    c, s = COLORS, ttk.Style(root)
    root.configure(background=c["background"])
    s.configure(".", font=("Segoe UI", 10), background=c["background"], foreground=c["ink"])
    s.configure("TFrame", background=c["background"])
    s.configure("TLabel", background=c["background"], foreground=c["ink"])
    s.configure("TButton", padding=(12, 8), background=c["surface"], foreground=c["ink"],
                bordercolor=c["line"], lightcolor=c["surface"], darkcolor=c["surface"])
    s.map("TButton", background=[("disabled", c["background"]), ("active", c["hover"])],
          foreground=[("disabled", c["muted"])])
    s.configure("TEntry", padding=7, fieldbackground=c["surface"], foreground=c["ink"])
    s.configure("TCombobox", padding=7, fieldbackground=c["surface"], foreground=c["ink"])
    s.map("TCombobox", fieldbackground=[("readonly", c["surface"])],
          selectbackground=[("readonly", c["surface"])], selectforeground=[("readonly", c["ink"])])
    s.configure("TCheckbutton", background=c["background"], padding=(0, 4))
    s.configure("TMenubutton", padding=(10, 7), background=c["surface"])
    s.configure("TNotebook", background=c["background"], borderwidth=0)
    s.configure("TNotebook.Tab", padding=(14, 8))
    s.configure("TLabelframe", background=c["background"], bordercolor=c["line"])
    s.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=c["ink"])
    s.configure("Treeview", rowheight=32, background=c["surface"], fieldbackground=c["surface"],
                foreground=c["ink"], bordercolor=c["line"], relief="flat")
    s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), padding=(8, 9),
                background="#e9eef4", foreground=c["ink"])
    s.map("Treeview", background=[("selected", c["accent"])], foreground=[("selected", "white")])
    for name, bg in (("Modern.Surface", c["surface"]), ("Modern.Rail", c["rail"])):
        s.configure(name+".TFrame", background=bg)
        s.configure(name+".TLabel", background=bg,
                    foreground=c["ink"] if bg == c["surface"] else c["rail_text"])
    s.configure("Modern.Title.TLabel", font=("Segoe UI", 21, "bold"), foreground=c["ink"])
    s.configure("Modern.Kicker.TLabel", font=("Segoe UI", 9, "bold"), foreground=c["accent"])
    s.configure("Modern.Muted.TLabel", foreground=c["muted"])
    s.configure("Modern.Card.TFrame", background=c["surface"], bordercolor=c["line"], borderwidth=1, relief="solid")
    s.configure("Modern.CardTitle.TLabel", background=c["surface"], font=("Segoe UI", 14, "bold"))
    s.configure("Modern.CardText.TLabel", background=c["surface"], foreground=c["muted"])
    s.configure("Modern.Link.TButton", background=c["surface"], foreground=c["accent"],
                anchor="w", borderwidth=0, padding=(0, 8), font=("Segoe UI", 10, "bold"))
    s.configure("Modern.Rail.TButton", background=c["rail"], foreground=c["rail_text"],
                anchor="w", borderwidth=0, padding=(12, 11), font=("Segoe UI", 10))
    s.map("Modern.Rail.TButton", background=[("active", c["selected"])],
          foreground=[("active", c["rail_text"])])
    s.configure("Modern.Selected.TButton", background=c["selected"], foreground=c["rail_text"],
                anchor="w", borderwidth=0, padding=(12, 11), font=("Segoe UI", 10, "bold"))
    s.map("Modern.Selected.TButton", background=[("active", c["selected"])])
    s.configure("Modern.PageTitle.TLabel", font=("Segoe UI", 15, "bold"), foreground=c["ink"])


class ModernSurface:
    """An adaptive task home, small category rail and contextual detail area."""
    def __init__(self, workspace):
        self.w = w = workspace
        self.root = w.root
        self.active = self.home_visible = False
        self.domain = None
        self.closed = False
        self._job = None
        self._heading_job = None
        self._bindings = []
        self._legacy_grid = []
        self._raw_colors = []
        self._toolbars = []
        self.identifiers = []
        self.marker_callback = None
        self.marker_refresh_callback = None
        self.cards = []
        self.links = []
        self.columns = 1
        self._menu_width = w.view_menu.master.cget("width")
        self.rail = ttk.Frame(w.sidebar, style="Modern.Rail.TFrame", padding=(12, 24))
        self.rail.columnconfigure(0, weight=1)
        brand = ttk.Label(self.rail, text="WORKSPACES", style="Modern.Rail.TLabel", font=("Segoe UI", 9, "bold"))
        brand.grid(row=0, column=0, sticky="w", padx=12, pady=(0, 18))
        self.identify(brand, "UI-007.rail-heading", "Workspace navigation heading")
        self.home_button = self._rail_button("Home", lambda: self.show_home(), 1, "home")
        self.profiles_button = self._rail_button('Game profiles', self.open_profiles, 2, 'profiles')
        self.domain_buttons = []
        for i, (label, *_rest) in enumerate(CATEGORIES):
            self.domain_buttons.append(self._rail_button(label, lambda n=i: self.show_home(n), i+3, "domain-"+str(i)))
        self.rail_footer = ttk.Label(self.rail, text="Your profiles stay\nwith their own tools.",
                                    style="Modern.Rail.TLabel", foreground=COLORS["rail_muted"], justify="left")
        self.rail_footer.grid(row=8, column=0, sticky="sw", padx=12, pady=(30, 0))
        self.rail.rowconfigure(7, weight=1)
        self.identify(self.rail_footer, "UI-007.rail-status", "Navigation privacy and ownership note")

        self.dashboard = ScrollableFrame(w.content, min_width=0)
        self.dashboard.horizontal.grid_remove()
        self.body = self.dashboard.body
        self.body.columnconfigure(0, weight=1)
        self.intro = ttk.Frame(self.body, padding=(24, 22, 24, 12))
        self.intro.grid(row=0, column=0, sticky="ew")
        self.intro.columnconfigure(0, weight=1)
        self.kicker = ttk.Label(self.intro, text="YOUR GAME TOOLS", style="Modern.Kicker.TLabel")
        self.kicker.grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.title = ttk.Label(self.intro, text="What would you like to do?", style="Modern.Title.TLabel")
        self.title.grid(row=1, column=0, sticky="ew")
        self.subtitle = ttk.Label(self.intro, text="Choose a task, or find any feature above.", style="Modern.Muted.TLabel")
        self.subtitle.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self.grid = ttk.Frame(self.body, padding=(24, 8, 24, 20))
        self.grid.grid(row=1, column=0, sticky="ew")
        self.grid.bind("<Configure>", self._queue_reflow, add="+")
        self.empty = ttk.Label(self.grid, text="No matching tasks. Try another term or press Escape to clear.",
                               style="Modern.Muted.TLabel", wraplength=400)
        self.note = ttk.Label(self.body, text="Offline workspace  ·  Opening a page never starts a test or recording.",
                              style="Modern.Muted.TLabel", padding=(24, 0, 24, 24))
        self.note.grid(row=2, column=0, sticky="ew")
        for widget, role in ((self.title, "home-title"), (self.subtitle, "home-description"),
                             (self.note, "home-scope"), (self.grid, "task-grid")):
            self.identify(widget, "UI-007."+role, "Modern / "+role.replace("-", " "))

        self.top = ttk.Frame(w.breadcrumb)
        self.top.columnconfigure(1, weight=1)
        self.back = ttk.Button(self.top, text="← Home", command=self.show_home)
        self.back.grid(row=0, column=0, sticky="w", padx=(0, 14))
        self.page_title = ttk.Label(self.top, text="Home", style="Modern.PageTitle.TLabel")
        self.page_title.grid(row=0, column=1, sticky="ew")
        self.detail_button = ttk.Button(self.top, text="Show details", command=self.toggle_details)
        self.detail_button.grid(row=0, column=2, sticky="e", padx=(12, 0))
        self.detail = ttk.Label(w.breadcrumb, textvariable=w.description, style="Modern.Muted.TLabel", justify="left")
        # One presentation owner per label. Generic Appearance wrapping must
        # not fight this page's grid-based widths in an endless idle resize loop.
        for label in (self.title, self.subtitle, self.note, self.empty, self.page_title, self.detail):
            label.game_tools_wrap_managed = True
        self.reflow_font = tkfont.Font(root=self.root, family="Segoe UI", size=10)
        # The dashboard is hidden on a saved page. Its Configure event cannot
        # own the visible page heading's widths or resize scheduling.
        for widget in (w.breadcrumb,self.top):
            token=widget.bind('<Configure>',self._queue_heading,add='+')
            self._bindings.append((widget,'<Configure>',token))
        for widget, role in ((self.back, "home"), (self.page_title, "page-title"),
                             (self.detail_button, "show-details"), (self.detail, "page-details")):
            self.identify(widget, "UI-007."+role, "Modern / "+role.replace("-", " "))

    def identify(self, widget, identifier, label):
        # Feedback has one stable, bounded suffix; route names contain dots.
        identifier = identifier[:7] + "".join(c if c.isalnum() or c == "-" else "-" for c in identifier[7:].lower())
        self.identifiers = [row for row in self.identifiers if row[0] is not widget]
        self.identifiers.append((widget, identifier, label))
        if self.marker_callback:
            self.marker_callback(widget, identifier, label)

    def open_profiles(self):
        record=self.w.registry.feature_for_route('profiles')
        if record and 'profiles'in self.w.route_tabs:self.w.route(record['id'])

    def _rail_button(self, text, callback, row, role):
        button = ttk.Button(self.rail, text=text, command=callback, style="Modern.Rail.TButton")
        button.grid(row=row, column=0, sticky="ew", pady=2)
        self.identify(button, "UI-007."+role, "Modern navigation / "+text)
        return button

    def activate(self):
        if self.active:
            return
        self.active = True
        self._legacy_grid = [(child, child.grid_info()) for child in self.w.sidebar.winfo_children()
                             if child is not self.rail and child.winfo_manager() == "grid"]
        for child, _ in self._legacy_grid:
            child.grid_remove()
        self.rail.grid(row=0, column=0, columnspan=2, rowspan=5, sticky="nsew")
        self.w.sidebar.configure(style="Modern.Rail.TFrame")
        self.w.active_widget.pack_forget()
        self.w.scope_widget.pack_forget()
        self.top.pack(fill="x")
        self.w.scope_widget.pack(anchor="w", pady=(7, 0))
        self.w.scope_widget.configure(style="Modern.Muted.TLabel")
        self.w.search_label.configure(text="Find a task or feature  ·  Ctrl+K")
        self.w.view_menu.master.configure(width=7)
        self.w.toolbar.configure(padding=(16, 10))
        self.w.breadcrumb.configure(padding=(18, 12))
        self._queue_heading()
        self._color_raw()
        self._disclose_actions(self.w.content)
        self.show_home()

    def deactivate(self):
        if not self.active:
            return
        self.active = False
        self.dashboard.pack_forget()
        self.w.notebook.pack(fill="both", expand=True)
        self.home_visible = False
        self.rail.grid_remove()
        for child, info in self._legacy_grid:
            child.grid(**{key: value for key, value in info.items() if key != "in"})
        self.w.sidebar.configure(style="TFrame")
        self.top.pack_forget()
        self.detail.pack_forget()
        self.w.active_widget.pack(before=self.w.scope_widget, anchor="w")
        self.w.scope_widget.configure(style="TLabel")
        self.w.search_label.configure(text="Find a goal or feature")
        self.w.view_menu.master.configure(width=self._menu_width)
        self.w.breadcrumb.grid()
        for widget, options in self._raw_colors:
            if widget.winfo_exists():
                widget.configure(**options)
        self._raw_colors = []
        for toolbar in self._toolbars:
            if toolbar.winfo_exists():
                toolbar.set_disclosure(False)
        self._toolbars = []
        self.w._notebook_changed()

    def _disclose_actions(self, container, route="shared"):
        for child in container.winfo_children():
            owner = next((key for key, tab in self.w.route_tabs.items() if str(child) == tab), route)
            if isinstance(child, FlowToolbar):
                child.set_disclosure(True)
                self._toolbars.append(child)
                if child.more_button is not None:
                    self.identify(child.more_button, "UI-007.more-actions-"+owner, "Modern / "+owner+" secondary actions")
            self._disclose_actions(child, owner)

    def _color_raw(self):
        # Only owned display colors. Preserve text, tags, commands, bindings and
        # geometry. Native AHK children keep their own renderer and settings.
        def visit(widget):
            if isinstance(widget, (tk.Text, tk.Listbox)):
                keys = ("background", "foreground", "selectbackground", "selectforeground")
                self._raw_colors.append((widget, {k: widget.cget(k) for k in keys}))
                widget.configure(background=COLORS["surface"], foreground=COLORS["ink"],
                                 selectbackground=COLORS["accent"], selectforeground="white")
            for child in widget.winfo_children():
                visit(child)
        visit(self.w.content)

    def show_home(self, domain=None):
        if not self.active:
            return
        self.domain = domain
        self.home_visible = True
        self.w.notebook.pack_forget()
        self.dashboard.pack(fill="both", expand=True)
        self.page_title.configure(text="Home" if domain is None else CATEGORIES[domain][0])
        self.w.scope_label.set("Offline workspace  ·  Game Input requires explicit Start")
        self.w.breadcrumb.grid_remove()
        self.detail_button.grid_remove()
        self.detail.pack_forget()
        self.refresh()

    def show_page(self, record):
        if not self.active:
            return
        self.home_visible = False
        self.w.breadcrumb.grid()
        self.dashboard.pack_forget()
        self.w.notebook.pack(fill="both", expand=True)
        self.page_title.configure(text=record["title"])
        self.detail_button.grid()
        self.details_changed()
        self._queue_heading()
        self._highlight(record["domain"])

    def _highlight(self, domain=None):
        profile_page=not self.home_visible and self.w.notebook.select()==str(self.w.route_tabs.get('profiles',''))
        self.profiles_button.configure(style='Modern.Selected.TButton'if profile_page else'Modern.Rail.TButton')
        self.profiles_button.state(['!disabled']if 'profiles'in self.w.route_tabs else['disabled'])
        self.home_button.configure(style="Modern.Selected.TButton" if self.home_visible and self.domain is None else "Modern.Rail.TButton")
        for i, button in enumerate(self.domain_buttons):
            selected = self.domain == i if self.home_visible else DOMAINS[i] == domain
            button.configure(style="Modern.Selected.TButton" if selected else "Modern.Rail.TButton")

    def refresh(self):
        if not self.active:
            return
        # Search updates navigation choices, not the current editor. Home is
        # opt-in; typing while on a page never replaces its unsaved contents.
        if not self.home_visible:
            return
        focused = self.root.focus_get()
        focused_id = next((r[1] for r in self.identifiers if r[0] is focused), None)
        retired = {widget for card in self.cards for widget in [card, *card.winfo_children()]}
        self.identifiers = [r for r in self.identifiers if r[0] not in retired]
        for card in self.cards:
            card.destroy()
        self.cards, self.links = [], []
        self.empty.grid_remove()
        query = self.w.query.get().strip()
        records = list(self.w._rows.values())
        if query:
            self.title.configure(text="Search results")
            self.subtitle.configure(text=f"{len(records)} matches  ·  Select a result to open its page.")
            groups = [(r["domain"], r["title"], r["summary"], [(r, "Open page →")]) for r in records]
        elif self.domain is not None:
            self.title.configure(text=CATEGORIES[self.domain][1])
            self.subtitle.configure(text="Choose a workspace below. All actions remain explicit.")
            groups = [(r["domain"], r["title"], r["summary"], [(r, "Open workspace →")])
                      for r in self.w.registry.features if r["domain"] == DOMAINS[self.domain]]
        else:
            self.title.configure(text="What would you like to do?")
            self.subtitle.configure(text="Choose a task, or find any feature above.")
            goals = self.w.registry.goals
            groups = [(DOMAINS[i], title, summary,
                       [(goals[2*i+j], caption) for j, caption in enumerate(captions)])
                      for i, (_short, title, summary, captions) in enumerate(CATEGORIES)]
        for index, (domain, title, summary, choices) in enumerate(groups):
            card = ttk.Frame(self.grid, style="Modern.Card.TFrame", padding=20)
            card.columnconfigure(0, weight=1)
            heading = ttk.Label(card, text=title, style="Modern.CardTitle.TLabel", justify="left")
            heading.grid(row=0, column=0, sticky="ew")
            description = ttk.Label(card, text=summary, style="Modern.CardText.TLabel", justify="left")
            description.grid(row=1, column=0, sticky="ew", pady=(10, 14))
            available_choices = []
            for n, (record, caption) in enumerate(choices):
                button = ttk.Button(card, text=caption+"  →" if not caption.endswith("→") else caption,
                                    style="Modern.Link.TButton", command=lambda r=record: self.w.route(r["id"]))
                if record["route"] not in self.w.route_tabs:
                    button.state(["disabled"])
                button.grid(row=n+2, column=0, sticky="ew")
                self.links.append(button)
                available_choices.append(record["id"])
                self.identify(button, "UI-007."+record["id"], "Modern task / "+record["title"])
            card.game_tools_labels = (heading, description)
            for label in card.game_tools_labels:
                label.game_tools_wrap_managed = True
            card.game_tools_ids = available_choices
            self.identify(card, "UI-007.card-"+choices[0][0]["id"], "Modern task group / "+title)
            self.identify(heading, "UI-007.title."+choices[0][0]["id"], "Modern task title / "+title)
            self.identify(description, "UI-007.description."+choices[0][0]["id"], "Modern task description / "+title)
            self.cards.append(card)
        if not groups:
            self.empty.grid(row=0, column=0, sticky="ew", pady=20)
        self._highlight()
        self.dashboard.canvas.yview_moveto(0)
        self.reflow(max(1, self.grid.winfo_width()))
        if focused_id:
            target = next((r[0] for r in self.identifiers if r[1] == focused_id), None)
            if target:
                target.focus_set()
        if self.marker_refresh_callback:
            self.marker_refresh_callback()

    def toggle_details(self):
        self.w.show_details.set(not self.w.show_details.get())
        self.details_changed()

    def details_changed(self):
        if not self.active:
            return
        self.w.details_box.grid_remove()
        visible = self.w.show_details.get() and not self.home_visible
        if visible:
            self.detail.pack(fill="x", pady=(8, 0))
        else:
            self.detail.pack_forget()
        self.detail_button.configure(text="Hide details" if visible else "Show details")
        self._queue_heading()

    def _queue_heading(self,event=None):
        if not self.closed and self._heading_job is None:
            self._heading_job=self.top.after_idle(self._reflow_heading)

    def _reflow_heading(self):
        self._heading_job=None
        if self.closed or not self.active:return
        width=self.top.winfo_width()
        if width<=1:
            width=max(240,self.w._available_width-36)
        buttons=self.back.winfo_reqwidth()+self.detail_button.winfo_reqwidth()+26
        narrow=width-buttons<max(240,self.reflow_font.measure('Game profiles and controls'))
        info=self.page_title.grid_info()
        row=1 if narrow else 0;column=0 if narrow else 1;span=3 if narrow else 1
        if (int(info.get('row',-1)),int(info.get('column',-1)),int(info.get('columnspan',1)))!=(row,column,span):
            self.page_title.grid_configure(row=row,column=column,columnspan=span,pady=(7,0)if narrow else 0)
        self._set_wrap(self.page_title,max(180,width if narrow else width-buttons))
        detail_width=self.w.breadcrumb.winfo_width()-36
        if detail_width<=1:detail_width=width
        self._set_wrap(self.detail,max(180,detail_width))

    def _queue_reflow(self, event):
        if event.widget is self.grid and self._job is None and not self.closed:
            self._job = self.grid.after_idle(self._reflow)

    def _reflow(self):
        self._job = None
        self.reflow(self.grid.winfo_width())

    def reflow(self, width):
        minimum = max(310, self.reflow_font.measure("Configure input & picture display  →")+52)
        self.columns = 2 if width >= minimum*2+24 else 1
        for column in range(2):
            self.grid.columnconfigure(column, weight=int(column < self.columns),
                                      uniform="cards" if column < self.columns else "", minsize=0)
        for index, card in enumerate(self.cards):
            card.grid(row=index//self.columns, column=index%self.columns, sticky="nsew", padx=(0, 12), pady=(0, 16))
            wrap = max(120, (width-48)//self.columns-52)
            for label in card.game_tools_labels:
                self._set_wrap(label, wrap)
        wrap = max(160, self.body.winfo_width()-70)
        for label in (self.title, self.subtitle, self.note, self.empty):
            self._set_wrap(label, wrap)
        self._queue_heading()

    @staticmethod
    def _set_wrap(label, width):
        if label.winfo_pixels(label.cget("wraplength") or 0) != width:
            label.configure(wraplength=width)

    def close(self):
        self.closed = True
        if self._job:
            self.grid.after_cancel(self._job)
            self._job = None
        if self._heading_job:
            self.top.after_cancel(self._heading_job);self._heading_job=None
        for widget,event,token in self._bindings:
            if widget.winfo_exists():widget.unbind(event,token)
        self._bindings=[]
        self.dashboard.close()
