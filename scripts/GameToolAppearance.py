"""Shared presentation modes and explicit, local UI feedback. No engine commands.

All layouts reuse the same live widgets. Presentation preferences are separate
from profiles, reports and input settings; feedback copies only selected labels.
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk
from GameToolCompactUI import FlowToolbar, enhance_tables

VERSION = "0.5.4"
MODES = ("Modern", "Professional", "Compact", "Classic")
MARKER_TYPES = ((1,"Controls"),(2,"Text & status"),(4,"Tables & images"),(8,"Sections"))


def marker_mask(value):
    if type(value) is not int or not 0 <= value <= 15:
        raise ValueError("Invalid identification display filter")
    return value


def marker_kind(target):
    if isinstance(target,(ttk.Label,tk.Label)): return 2
    if isinstance(target,(ttk.Treeview,tk.Listbox,tk.Text,tk.Canvas)): return 4
    if isinstance(target,(ttk.Frame,tk.Frame,ttk.LabelFrame,tk.LabelFrame,ttk.Notebook)): return 8
    return 1
# Permanent identifiers: never renumber/reuse an ID when a feature is removed.
ITEMS = (
    ("UI-001", "Interface / layout selector", "shell"),
    ("UI-002", "Search goals and features", "shell"),
    ("UI-003", "Grouped navigation and View menu", "shell"),
    ("UI-004", "Current page heading and safety scope", "shell"),
    ("UI-005", "Responsive layout and scrolling", "shell"),
    ("UI-006", "Feature IDs and feedback copy", "shell"),
    ("UI-007", "Modern task home and category workspaces", "shell"),
    ("UI-101", "Studio / Picture buttons / slot list", "studio"),
    ("UI-102", "Studio / Picture buttons / key, source and mode", "studio"),
    ("UI-103", "Studio / Picture buttons / image and preview", "studio"),
    ("UI-104", "Studio / Advanced Picture Buttons", "studio"),
    ("UI-105", "Studio / MultiImageCanvas", "studio"),
    ("UI-106", "Studio / Key display / HUD", "studio"),
    ("UI-107", "Studio / Status and log", "studio"),
    ("UI-108", "Studio / guarded Game Input", "studio"),
    ("UI-109", "Studio / native viewport scrollbars", "studio"),
    ("UI-201", "Saved-result comparison", "comparison"),
    ("UI-202", "Comparison / saved-report import adapters", "comparison"),
    ("UI-203", "Reports / original files", "reports"),
    ("UI-204", "Sensors / read-only connections", "sensors"),
    ("UI-205", "RTSS / read-only connections", "rtss"),
    ("UI-301", "Sessions / crash-safe journal", "sessions"),
    ("UI-302", "Sessions / crash evidence", "sessions"),
    ("UI-303", "Sessions / workflow dry-runs and rollback plans", "sessions"),
    ("UI-304", "Sessions / provider health and scenario contracts", "sessions"),
    ("UI-401", "Catalog / tools and relationships", "catalog"),
    ("UI-402", "Catalog / effective FG and memory preflight", "catalog"),
    ("UI-403", "Overlay groups, keymaps and associations", "overlays"),
    ("UI-404", "External-tool registry and connections", "tools"),
    ("UI-405", "Updates / inspect, update and rollback", "updates"),
    ("UI-406", "User data / migration and portable backups", "data"),
    ("UI-407", "Guide / safety boundaries", "guide"),
    ("UI-408", "Mods / ordered downloads and staging", "mods"),
    ("UI-409", "AI / approved requests and shared context", "automation"),
)


def component_id(base, role):
    """Stable declared role, never a widget index, value or screen coordinate."""
    if base not in {row[0] for row in ITEMS}:
        raise ValueError("Unknown feature ID")
    role = re.sub(r"[^a-z0-9]+", "-", role.casefold()).strip("-")
    if not role or len(role) > 96:
        raise ValueError("Invalid component role")
    return base + "." + role


class ComponentMarkers:
    """Presentation-only badges owned by their target's layout container.

    No global click interception or command forwarding. A badge is a separate
    button; its only operation is copying public metadata. Placing relative to
    the target preserves pack/grid, scroll clipping and all original callbacks.
    """
    def __init__(self, root, status):
        self.root, self.status = root, status
        self.enabled = False
        self.records = {}
        self.tip = None
        self.last_copied = None
        self.closed = False
        self.sequence = 0
        self.mask = 15
        self.kinds = {}
        self.spacing = {}
        self.notice = None

    def register(self, target, identifier, label, replace=False, kind=None):
        if not re.fullmatch(r"UI-\d{3}(?:\.[a-z0-9-]{1,96})?", identifier) or \
                identifier.split(".")[0] not in {r[0] for r in ITEMS}:
            raise ValueError("Unknown component identifier")
        if not label or len(label) > 240:
            raise ValueError("Invalid public component label")
        key = str(target)
        if key in self.records:
            if not replace: return self.records[key][1]
            self.records[key][1].destroy()
            self.records.pop(key)
        kind = marker_kind(target) if kind is None else marker_mask(kind)
        if not kind: raise ValueError("A component must have a display type")
        # Sibling, not a child of an Entry/Treeview: native field semantics stay
        # intact. place(in_=target) tracks geometry even inside scrolled bodies.
        self.sequence += 1
        badge = tk.Button(target.master, text="?", name="feedback_" + str(self.sequence),
            bg="#164f86", fg="white", activebackground="#2672b5", activeforeground="white",
            font=("Segoe UI", 9, "bold"), relief="flat", bd=0, cursor="hand2",
            takefocus=True, command=lambda: self.copy(identifier, label))
        badge.bind("<Enter>", lambda _: self.describe(badge, identifier, label))
        badge.bind("<Leave>", lambda _: self.hide_tip())
        badge.bind("<FocusOut>", lambda _: self.hide_tip())
        self.records[key] = (target, badge, identifier, label)
        self.kinds[key] = kind
        if isinstance(target,ttk.Label) and key not in self.spacing:
            self.spacing[key] = target.cget("padding")
        elif isinstance(target,tk.Label) and key not in self.spacing:
            self.spacing[key] = (target.cget("padx"),target.cget("pady"))
        if self.enabled and self.mask & kind:
            self._space(target,True)
            self._place(target, badge)
        return badge

    def _space(self,target,visible):
        """Reserve a marker gutter on text, restoring exact original padding."""
        original = self.spacing.get(str(target))
        if original is None: return
        if isinstance(target,ttk.Label):
            parts = list(map(target.winfo_pixels,target.tk.splitlist(original))) or [0]
            if len(parts)==1: parts *= 4
            elif len(parts)==2: parts *= 2
            elif len(parts)==3: parts.append(parts[1])
            target.configure(padding=(parts[0],parts[1]+2,parts[2]+26,parts[3]+2) if visible else original)
        else:
            target.configure(padx=target.winfo_pixels(original[0])+13 if visible else original[0],
                             pady=target.winfo_pixels(original[1])+2 if visible else original[1])

    @staticmethod
    def _place(target, badge):
        badge.place(in_=target, relx=1, x=-2, y=0, anchor="ne", width=21, height=21)
        badge.lift()

    def set_enabled(self, enabled, mask=None):
        if mask is not None: self.mask = marker_mask(mask)
        self.enabled = bool(enabled)
        self.hide_tip()
        for key, (target, badge, _, _) in list(self.records.items()):
            if not target.winfo_exists() or not badge.winfo_exists():
                if badge.winfo_exists(): badge.destroy()
                self.records.pop(key)
                self.kinds.pop(key,None); self.spacing.pop(key,None)
            elif self.enabled and self.mask & self.kinds[key]:
                self._space(target,True)
                self._place(target, badge)
            else:
                badge.place_forget()
                self._space(target,False)

    def copy(self, identifier, label):
        # Do not read any field, profile, image, path, log or clipboard value.
        copied = self._copy(identifier,label)
        self.show_notice(identifier,label,copied)
        return copied

    def _copy(self,identifier,label):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(identifier)
        except tk.TclError:
            self.status.set("Could not copy the component ID; nothing was activated.")
            return False
        self.last_copied = identifier
        self.status.set(f"Copied {identifier} — {label}. Paste it with your feedback. No control was activated.")
        self.hide_tip()
        return True

    def show_notice(self,identifier,label,copied):
        self.hide_tip()
        if self.notice is not None and self.notice.winfo_exists(): self.notice.destroy()
        self.notice = popup = tk.Toplevel(self.root)
        popup.title("UI component ID")
        popup.transient(self.root); popup.resizable(False,False)
        box=ttk.Frame(popup,padding=12); box.pack(fill="both",expand=True)
        result=tk.StringVar(popup,value="Copied — paste this ID with your feedback." if copied else
            "Clipboard unavailable. Select the ID below or retry Copy ID.")
        ttk.Label(box,text=label,wraplength=420).pack(anchor="w")
        entry=ttk.Entry(box,width=48)
        entry.insert(0,identifier); entry.configure(state="readonly")
        entry.pack(fill="x",pady=8)
        ttk.Label(box,textvariable=result,wraplength=420).pack(anchor="w")
        actions=FlowToolbar(box); actions.pack(fill="x",pady=(8,0))
        def retry():
            result.set("Copied — paste this ID with your feedback." if self._copy(identifier,label)
                       else "Clipboard unavailable. Select the ID below or retry Copy ID.")
        actions.add("Copy ID",retry); actions.add("Close",popup.destroy)
        popup.bind("<Escape>",lambda _: popup.destroy())
        popup.update_idletasks()
        x=max(0,min(self.root.winfo_rootx()+40,self.root.winfo_screenwidth()-popup.winfo_reqwidth()-8))
        y=max(0,min(self.root.winfo_rooty()+80,self.root.winfo_screenheight()-popup.winfo_reqheight()-8))
        popup.geometry(f"+{x}+{y}")

    def describe(self, badge, identifier, label):
        self.hide_tip()
        if not self.enabled or not badge.winfo_viewable(): return
        self.tip = tip = tk.Toplevel(badge)
        tip.overrideredirect(True)
        tip.transient(badge.winfo_toplevel())
        tk.Label(tip, text=f"{label}\n{identifier} • click ? to copy", bg="#fff4cd", fg="#172b42",
            justify="left", wraplength=360, padx=9, pady=6).pack()
        tip.update_idletasks()
        x = min(badge.winfo_rootx(), max(0, self.root.winfo_screenwidth()-tip.winfo_reqwidth()-8))
        y = min(badge.winfo_rooty()+24, max(0, self.root.winfo_screenheight()-tip.winfo_reqheight()-8))
        tip.geometry(f"+{max(0,x)}+{max(0,y)}")

    def hide_tip(self):
        if self.tip is not None:
            if self.tip.winfo_exists(): self.tip.destroy()
            self.tip = None

    def close(self):
        self.closed = True
        self.hide_tip()
        if self.notice is not None and self.notice.winfo_exists(): self.notice.destroy()
        for target, badge, _, _ in self.records.values():
            if target.winfo_exists(): self._space(target,False)
            if badge.winfo_exists(): badge.destroy()
        self.records.clear()
        self.kinds.clear(); self.spacing.clear()


def wrap_labels(container):
    """Reflow existing explanatory labels; no content or form value is edited."""
    for widget in container.winfo_children():
        if isinstance(widget, (ttk.Label, tk.Label)) and not getattr(widget, "game_tools_wrap_managed", False):
            value = widget.cget("wraplength")
            maximum = widget.winfo_pixels(value) if value else 0
            if maximum > 0:
                def resize(event, label=widget, limit=maximum):
                    if event.widget is label.master and label.winfo_exists():
                        width = max(180, min(limit, event.width-label.winfo_x()-12))
                        if label.winfo_pixels(label.cget("wraplength")) != width:
                            label.configure(wraplength=width)
                widget.master.bind("<Configure>", resize, add="+")
        wrap_labels(widget)


def feedback_text(ids, mode, route, version):
    """Only explicit public UI metadata, never screenshots or form contents."""
    if mode not in MODES:
        raise ValueError("Unknown layout")
    selected = set(ids)
    known = {item[0] for item in ITEMS}
    if not selected or selected - known:
        raise ValueError("Choose known feature IDs")
    lines = [f"GameTools {version} | Layout: {mode} | Page: {route or 'workspace'}"]
    lines.extend(f"{identifier} — {label}" for identifier, label, _ in ITEMS if identifier in selected)
    lines.append("My feedback: ")
    return "\n".join(lines)


class ViewPreferences:
    """Bounded version-independent JSON; fail closed on drift/future schemas."""
    def __init__(self, path):
        self.path = Path(path)
        self.raw = self.path.read_bytes() if self.path.exists() else None
        self.value = {"schema_version": 1, "mode": "Professional", "views": {}}
        self.read_only = False
        self.reason = ""
        if self.raw is not None:
            try:
                if len(self.raw) > 65536:
                    raise ValueError("View preferences exceed the size limit")
                value = json.loads(self.raw)
                if not isinstance(value, dict) or value.get("schema_version") != 1:
                    raise ValueError("Unknown preference schema; original retained")
                if value.get("mode") not in MODES or not isinstance(value.get("views", {}), dict):
                    raise ValueError("Invalid view preferences; original retained")
                self.value = value
            except (ValueError, UnicodeError) as error:
                self.read_only, self.reason = True, str(error)

    def save(self, mode, views):
        if mode not in MODES or not isinstance(views, dict):
            raise ValueError("Invalid presentation choices")
        if self.read_only:
            raise ValueError(self.reason)
        current = self.path.read_bytes() if self.path.exists() else None
        if current != self.raw:
            raise ValueError("View preferences changed elsewhere; original retained")
        value = dict(self.value, schema_version=1, mode=mode, views=views)
        raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if len(raw) > 65536:
            raise ValueError("View preferences exceed the size limit")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".ui-view-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            # Recheck after serialization; never overwrite a known newer owner.
            if (self.path.read_bytes() if self.path.exists() else None) != self.raw:
                raise ValueError("View preferences changed during save; original retained")
            os.replace(temporary, self.path)
            self.raw, self.value = raw, value
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


class Appearance:
    def __init__(self, root, header, workspace, status, path, version):
        self.root, self.workspace, self.status, self.version = root, workspace, status, version
        self.preferences = ViewPreferences(path)
        self.mode = tk.StringVar(root, value=self.preferences.value["mode"])
        self.views = dict(self.preferences.value.get("views", {}))
        self.current = None
        self.preview_only = False
        banner = getattr(root, "game_tools_scope_banner", None)
        self.banner = banner
        self.banner_original = {key: banner.cget(key) for key in ("text", "background", "foreground", "pady")} if banner else None
        self.dialog = None
        self.markers = ComponentMarkers(root, status)
        self.native_feedback = None
        self.native_filter = None
        root.game_tools_feedback = self
        self.style = ttk.Style(root)
        self.classic_theme = self.style.theme_use()
        self.classic_background = root.cget("background")
        self.classic_foreground = self.style.lookup("TLabel", "foreground") or "black"
        self.controls = ttk.Frame(header)
        self.controls.pack(side="right", padx=8)
        ttk.Label(self.controls, text="Layout").pack(side="left", padx=(0, 5))
        self.selector = ttk.Combobox(self.controls, textvariable=self.mode,
            values=MODES, state="readonly", width=14)
        self.selector.pack(side="left")
        self.selector.bind("<<ComboboxSelected>>", lambda _: self.change(self.mode.get()))
        self.help_button = ttk.Button(self.controls, text="? Identify UI ▾", command=self.identification_menu)
        self.help_button.pack(side="left", padx=(8, 0))
        self.filter_vars = {bit:tk.BooleanVar(root,value=True) for bit,_ in MARKER_TYPES}
        self.marker_menu = tk.Menu(self.help_button,tearoff=False)
        self.marker_menu.add_command(label="Show all components",command=lambda: self.set_identification(True,15))
        self.marker_menu.add_command(label="Hide all markers",command=lambda: self.set_identification(False))
        self.marker_menu.add_separator()
        for bit,name in MARKER_TYPES:
            self.marker_menu.add_command(label=name+" only",command=lambda b=bit:self.set_identification(True,b))
        custom=tk.Menu(self.marker_menu,tearoff=False)
        for bit,name in MARKER_TYPES:
            custom.add_checkbutton(label=name,variable=self.filter_vars[bit],command=self.apply_marker_filters)
        self.marker_menu.add_cascade(label="Choose types…",menu=custom)
        self.custom_marker_menu = custom
        self.markers.register(self.selector, "UI-001", "Interface / layout selector")
        if workspace:
            for widget, identifier, label in (
                (workspace.selector,"UI-002","Search goals and features"),
                (workspace.tree,"UI-003","Grouped navigation"),
                (workspace.active_widget,"UI-004","Current page heading")):
                self.markers.register(widget, identifier, label)
        self.change(self.mode.get(), persist=False)
        self.compact_header = None
        if workspace:
            from GameToolCompactHeader import CompactHeader
            self.compact_header = CompactHeader(root, header, workspace, self)
        wrap_labels(root)
        enhance_tables(root)
        if self.preferences.read_only:
            status.set("View preferences kept unchanged: " + self.preferences.reason)

    def toggle_identification(self):
        self.set_identification(not self.markers.enabled)

    def identification_menu(self):
        self.markers.hide_tip()
        self.marker_menu.post(self.help_button.winfo_rootx(),self.help_button.winfo_rooty()+self.help_button.winfo_height())

    def apply_marker_filters(self):
        mask=sum(bit for bit,var in self.filter_vars.items() if var.get())
        self.set_identification(bool(mask),mask)

    def set_identification(self,enabled,mask=None):
        if mask is not None:
            marker_mask(mask)
            for bit,var in self.filter_vars.items(): var.set(bool(mask & bit))
        mask=self.markers.mask if mask is None else mask
        enabled=bool(enabled and mask)
        self.markers.set_enabled(enabled,mask)
        mode="All" if mask==15 else "Custom"
        self.help_button.configure(text=f"? Identify UI: {mode} ▾" if enabled else "? Identify UI ▾")
        if self.native_feedback:
            self.native_feedback(enabled)
        if self.native_filter:
            self.native_filter(mask)
        self.status.set("Identification ON ("+", ".join(name for bit,name in MARKER_TYPES if mask & bit)+") — click ? to copy. Normal controls still work."
                        if enabled else "Identification OFF — floating markers hidden; original controls unchanged.")

    def register_panel(self, container, base, panel=None, exclude=()):
        """Bind authored roles and static captions, not guessed current values.

        Existing base IDs remain valid. Sub-IDs use declared Python attributes,
        dictionary keys or authored button captions; they do not depend on tab
        order/geometry. Generic unlabelled fields are not guessed or assigned a
        misleading ordinal. A section marker remains available for that area.
        """
        enhance_tables(container)
        title = next(label for identifier,label,_ in ITEMS if identifier == base)
        excluded = set(map(str,exclude))
        descendants = []
        def walk(widget):
            if str(widget) in excluded: return
            for child in widget.winfo_children():
                if str(child) in excluded or child in [r[1] for r in self.markers.records.values()]: continue
                descendants.append(child); walk(child)
        walk(container)
        members = set(descendants)
        field_types = (ttk.Entry,ttk.Combobox,ttk.Spinbox,tk.Text,ttk.Treeview,tk.Listbox,tk.Canvas,ttk.Label,tk.Label,ttk.LabelFrame)
        labels = [w for w in descendants if isinstance(w,(ttk.Label,tk.Label)) and
                  not w.cget("textvariable") and w.cget("text")]
        anchor = labels[0] if labels else container
        if anchor.winfo_toplevel() is not anchor:
            self.markers.register(anchor,base,title,kind=marker_kind(anchor)|8)
        variables = {}
        def declared(role, value, depth=0):
            if isinstance(value,tk.Variable): variables[str(value)] = role
            elif isinstance(value,tk.Misc) and value in members and isinstance(value,field_types + (ttk.Button,ttk.Checkbutton,ttk.Menubutton)):
                self.markers.register(value,component_id(base,role),title + " / " + role.replace("_"," ").replace("."," / "))
            elif isinstance(value,dict) and depth < 2:
                for key,child in value.items():
                    if isinstance(key,str): declared(role+"."+key,child,depth+1)
            elif hasattr(value,"control") and isinstance(value.control,tk.Misc):
                declared(role,value.control,depth+1)
        if panel is not None:
            for role,value in vars(panel).items(): declared(role,value)
        for child in descendants:
            if str(child) in self.markers.records: continue
            if isinstance(child,(ttk.Button,ttk.Checkbutton,ttk.Menubutton)):
                # Authored fixed caption only. Variable captions could contain
                # private data, so are never read or used for identity.
                if not child.cget("textvariable") and child.cget("text"):
                    caption = str(child.cget("text"))
                    self.markers.register(child,component_id(base,"action-"+caption),title+" / "+caption)
            elif isinstance(child,(ttk.Entry,ttk.Combobox,ttk.Spinbox)):
                variable = str(child.cget("textvariable"))
                if variable in variables:
                    role = variables[variable]
                    self.markers.register(child,component_id(base,role),title+" / "+role.replace("_"," "))
            elif isinstance(child,(ttk.Label,tk.Label)):
                # Variables are identified by declared roles, never their values.
                variable=str(child.cget("textvariable"))
                caption="" if variable else str(child.cget("text"))
                role=variables.get(variable,"status-text") if variable else "text-"+caption[:72]
                # Error/path-bearing text gets a public area ID, not a value ID.
                if not role.strip("text-") or re.search(r"[\\/:@{}]",caption): role="text"
                self.markers.register(child,component_id(base,role),title+" / "+("Text / status" if variable or role=="text" else caption[:110]))
            elif isinstance(child,(ttk.Treeview,tk.Listbox,tk.Text,tk.Canvas)):
                self.markers.register(child,component_id(base,"data-view"),title+" / Table, image or report view")
            elif isinstance(child,ttk.LabelFrame):
                self.markers.register(child,component_id(base,"section"),title+" / Section")

    def change(self, mode, persist=True):
        if mode not in MODES:
            raise ValueError("Unsupported interface")
        if persist:
            self.preview_only = False
        workspace = self.workspace
        if workspace and self.current:
            self.capture_view()
        self.mode.set(mode)
        self.style.theme_use(self.classic_theme if mode == "Classic" else "clam")
        modern = mode != "Classic"
        background = "#edf2f7" if mode == "Professional" else "#f7f9fc"
        self.root.configure(bg=background if modern else self.classic_background)
        # Reconfigure shared styles, not engines or existing page constructors.
        self.style.configure("TFrame", background=background if modern else self.classic_background)
        self.style.configure("TLabel", background=background if modern else self.classic_background,
            foreground="#24364b" if modern else self.classic_foreground, font=("Segoe UI", 10))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6) if mode == "Professional" else (7, 3))
        self.style.configure("TNotebook", background=background, tabmargins=(2, 2, 2, 0))
        self.style.configure("TNotebook.Tab", padding=(12, 7) if mode == "Professional" else (7, 3))
        self.style.configure("Treeview", font=("Segoe UI", 10), rowheight=30 if mode == "Professional" else 25,
            background="#ffffff", fieldbackground="#ffffff", foreground="#24364b")
        self.style.map("Treeview", background=[("selected", "#235da5")], foreground=[("selected", "white")])
        self.style.configure("Workspace.Header.TLabel", font=("Segoe UI", 12, "bold"), foreground="#16477c")
        self.style.configure("Workspace.Treeview", rowheight=31 if mode == "Professional" else 25,
            background="#e4ecf5" if mode == "Professional" else "#ffffff", fieldbackground="#e4ecf5" if mode == "Professional" else "#ffffff")
        if mode == "Modern":
            from GameToolModernUI import apply_theme, COLORS
            apply_theme(self.root)
            if self.banner:
                self.banner.configure(text="OFFLINE WORKSPACE  ·  Game Input requires explicit Start",
                                      bg=COLORS["hover"], fg=COLORS["accent"], pady=6)
        elif self.banner:
            self.banner.configure(**self.banner_original)
        if workspace:
            # Preserve query and scroll explicitly: restore_view is also used by
            # Reset view, whose normal search reset must not leak into switching.
            query, scroll = workspace.query.get(), workspace.tree.yview()
            stored = self.views.get(mode)
            if stored:
                try: workspace.restore_view(stored)
                except ValueError: workspace.apply_mode_defaults(mode)
            else:
                workspace.apply_mode_defaults(mode)
            workspace.query.set(query)
            workspace.set_presentation(mode)
            if mode == "Modern":
                workspace.modern.marker_callback = self.markers.register
                workspace.modern.marker_refresh_callback = lambda: self.markers.set_enabled(self.markers.enabled)
                for widget, identifier, label in workspace.modern.identifiers:
                    self.markers.register(widget, identifier, label)
            if scroll: workspace.tree.yview_moveto(scroll[0])
        self.current = mode
        compact = getattr(self, 'compact_header', None)
        if compact:
            compact.refresh()
        if persist:
            if self.save():
                self.status.set(f"{mode} layout • existing pages, edits, profiles and engines kept")

    def save(self):
        if self.preview_only:
            return False
        if self.workspace and self.current:
            self.capture_view()
        try:
            self.preferences.save(self.mode.get(), self.views)
            return True
        except (OSError, ValueError) as error:
            self.status.set("Layout changed for this session only: " + str(error))
            return False

    def preview(self, mode):
        """A launch-time preview does not overwrite the user's saved layout.

        Explicit Interface selection commits normally and ends preview mode.
        """
        self.change(mode, persist=False)
        self.preview_only = True
        self.status.set(mode + " preview • saved layout unchanged; choose Interface to keep this layout")

    def capture_view(self):
        original = self.views.get(self.current, {})
        self.views[self.current] = dict(original if isinstance(original, dict) else {}, **self.workspace.export_view())

    def feedback(self):
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.lift(); return
        self.dialog = window = tk.Toplevel(self.root)
        window.title("GameTools — feature IDs and feedback")
        width, height = 760, 540
        x = max(0, self.root.winfo_x() + (self.root.winfo_width()-width)//2)
        y = max(0, self.root.winfo_y() + (self.root.winfo_height()-height)//2)
        window.geometry(f"{width}x{height}+{x}+{y}"); window.minsize(510, 360)
        window.transient(self.root)  # Non-modal: switch layouts with this open.
        box = ttk.Frame(window, padding=12); box.pack(fill="both", expand=True)
        box.columnconfigure(0, weight=1); box.rowconfigure(3, weight=1)
        ttk.Label(box, text="Tell me what you like or want changed", font=("Segoe UI", 13, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(box, text="Select one or several rows (Ctrl / Shift). IDs stay the same in every layout.", wraplength=650).grid(row=1, column=0, columnspan=2, sticky="ew", pady=6)
        query = tk.StringVar(window)
        entry = ttk.Entry(box, textvariable=query); entry.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tree = self.feedback_tree = ttk.Treeview(box, columns=("id", "label"), show="headings", selectmode="extended")
        tree.heading("id", text="Feature ID"); tree.heading("label", text="Feature / location")
        tree.column("id", width=100, minwidth=90, stretch=False); tree.column("label", width=560, minwidth=200)
        tree.grid(row=3, column=0, sticky="nsew")
        y = ttk.Scrollbar(box, command=tree.yview); y.grid(row=3, column=1, sticky="ns"); tree.configure(yscrollcommand=y.set)
        x = ttk.Scrollbar(box, orient="horizontal", command=tree.xview); x.grid(row=4, column=0, sticky="ew"); tree.configure(xscrollcommand=x.set)
        route = self.workspace.current_route if self.workspace else None
        selected = set(next(([i] for i, _, r in ITEMS if r == route), []))
        def rebuild(*_):
            selected.difference_update(tree.get_children())
            selected.update(tree.selection())
            tree.delete(*tree.get_children())
            terms = query.get().casefold().split()
            for identifier, label, _ in ITEMS:
                if all(t in (identifier + " " + label).casefold() for t in terms):
                    tree.insert("", "end", iid=identifier, values=(identifier, label))
            visible = [i for i in tree.get_children() if i in selected]
            if visible: tree.selection_set(visible); tree.see(visible[0])
        query.trace_add("write", rebuild); rebuild()
        info = tk.StringVar(window, value="Copy is local only. Nothing is sent to a chat automatically.")
        def copy(context):
            ids = tree.selection()
            if not ids:
                info.set("Select at least one visible feature row first."); return
            route_now = self.workspace.current_route if self.workspace else None
            value = feedback_text(ids, self.mode.get(), route_now, self.version) if context else ", ".join(sorted(ids))
            self.root.clipboard_clear(); self.root.clipboard_append(value)
            info.set("Copied " + str(len(ids)) + " feature ID(s). Paste in your chat with your comments or screenshot.")
        actions = FlowToolbar(box); actions.grid(row=5, column=0, columnspan=2, sticky="ew", pady=8)
        actions.add("Copy IDs", lambda: copy(False))
        actions.add("Copy feedback + layout", lambda: copy(True))
        actions.add("Close", window.destroy)
        ttk.Label(box, textvariable=info, wraplength=650).grid(row=6, column=0, columnspan=2, sticky="ew")
        wrap_labels(window)
        entry.focus_set()

    def close(self):
        if self.compact_header:
            self.compact_header.close()
        if self.native_feedback:
            self.native_feedback(False)
        self.markers.close()
        self.marker_menu.unpost()
        self.save()
        if self.dialog is not None and self.dialog.winfo_exists():
            self.dialog.destroy()
