"""Reusable native editable selection/search control; typing never saves."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from types import SimpleNamespace
from GameToolEditableLists import install as install_editable_lists, attach as attach_editable_list

VERSION = "0.5.0"


def window_bounds(screen_width, screen_height):
    """A resizable first-run window that fits the reported logical screen."""
    width = max(320, min(1360, screen_width - 80))
    height = max(240, min(880, screen_height - 100))
    return width, height, min(620, width), min(430, height)


class TableLayout:
    """Shared table presentation only; native separator dragging stays intact.

    Initial widths adapt to the viewport. A manual drag stops auto fitting;
    column/header commands explicitly fit or reset without touching table rows,
    selection, heading sort callbacks or the owning panel's values.
    """
    def __init__(self, tree):
        self.tree = tree
        self.columns = tuple(tree.cget("columns"))
        self.original = {c: {key: tree.column(c, key) for key in ("width", "minwidth", "stretch", "anchor")} for c in self.columns}
        self.automatic = True
        self.selected_column = None
        self._job = None
        self.menu = tk.Menu(tree, tearoff=False)
        self.menu.add_command(label="Fit this column to text", command=self.fit_selected)
        self.menu.add_command(label="Fit columns to window", command=self.fit_window)
        self.menu.add_command(label="Restore original widths", command=self.reset)
        # Keep the legacy class-binding divider drag. Lower only an excessive
        # minimum; no heading command or user data is replaced.
        for column in self.columns:
            tree.column(column, minwidth=min(60, int(self.original[column]["minwidth"])), stretch=False)
        self.bindings = [(event, tree.bind(event, callback, add="+")) for event, callback in (
            ("<Configure>", self._configure), ("<ButtonPress-1>", self._press),
            ("<Double-Button-1>", self._double), ("<Button-3>", self._context),
            ("<Shift-F10>", self._keyboard_menu), ("<Destroy>", self._destroy))]
        tree.game_tools_column_layout = self

    def display_columns(self):
        columns = self.tree.cget("displaycolumns")
        if columns == ("#all",) or columns == "#all":
            return self.columns
        return tuple(self.columns[int(c)] if str(c).isdigit() else c for c in columns)

    def column_at(self, x):
        column = self.tree.identify_column(x)
        columns = self.display_columns()
        index = int(column[1:]) - 1 if column.startswith("#") else -1
        return columns[index] if 0 <= index < len(columns) else None

    def _configure(self, event):
        if event.widget is self.tree and self.automatic and self._job is None:
            self._job = self.tree.after_idle(self._fit_automatic)

    def _fit_automatic(self):
        self._job = None
        if self.automatic and self.tree.winfo_exists():
            self._fit_window()

    def _fit_window(self):
        columns = self.display_columns()
        width = self.tree.winfo_width() - 4
        if not columns or width < 100:
            return
        minimum = [int(self.tree.column(c, "minwidth")) for c in columns]
        extra = max(0, width - sum(minimum))
        weights = [int(self.original[c]["width"]) for c in columns]
        total = max(1, sum(weights))
        remaining = extra
        for index, column in enumerate(columns):
            share = remaining if index == len(columns) - 1 else int(extra * weights[index] / total)
            remaining -= share
            self.tree.column(column, width=minimum[index] + share, stretch=False)

    def fit_window(self):
        self.automatic = True
        self._fit_window()

    def reset(self):
        self.automatic = False
        for column, values in self.original.items():
            self.tree.column(column, **values)

    def fit_selected(self):
        if self.selected_column in self.columns:
            self.fit_text(self.selected_column)

    def fit_text(self, column):
        if column not in self.columns:
            return
        self.automatic = False
        font_name = ttk.Style(self.tree).lookup(self.tree.cget("style") or "Treeview", "font") or "TkDefaultFont"
        font = tkfont.Font(root=self.tree, font=font_name)
        heading = self.tree.heading(column, "text")
        # Bounded existing display values, measured locally, never copied or
        # stored in preferences/logs. Don't scan unbounded report databases.
        values = [self.tree.set(row, column) for row in self.tree.get_children()[:200]]
        size = max((font.measure(str(value)[:512]) for value in [heading, *values]), default=60) + 28
        self.tree.column(column, width=max(60, min(800, size)), stretch=False)

    def _press(self, event):
        if self.tree.identify_region(event.x, event.y) == "separator":
            self.automatic = False

    def _double(self, event):
        if self.tree.identify_region(event.x, event.y) == "separator":
            self.fit_text(self.column_at(event.x))
            return "break"

    def _context(self, event):
        if self.tree.identify_region(event.x, event.y) not in ("heading", "separator"):
            return
        self.selected_column = self.column_at(event.x)
        self.menu.entryconfigure(0, state="normal" if self.selected_column else "disabled")
        self.menu.post(event.x_root, event.y_root)
        return "break"

    def _keyboard_menu(self, event):
        self.selected_column = None
        self.menu.entryconfigure(0, state="disabled")
        self.menu.post(self.tree.winfo_rootx() + 12, self.tree.winfo_rooty() + 12)
        return "break"

    def _destroy(self, event):
        if event.widget is self.tree:
            self.close()

    def close(self):
        if self._job:
            self.tree.after_cancel(self._job)
            self._job = None
        for event, binding in self.bindings:
            self.tree.unbind(event, binding)
        self.bindings = []
        if self.menu.winfo_exists():
            self.menu.destroy()


def enhance_tables(container):
    """Attach once to owned heading tables; navigation is not a data table."""
    layouts = []
    for widget in container.winfo_children():
        if isinstance(widget, ttk.Treeview) and "headings" in str(widget.cget("show")) and widget.cget("columns"):
            layout = getattr(widget, "game_tools_column_layout", None) or TableLayout(widget)
            layouts.append(layout)
        layouts.extend(enhance_tables(widget))
    return layouts

class ScrollableFrame(ttk.Frame):
    """Reusable bounded-height workspace; scrolls only its own Tk descendants."""
    def __init__(self, parent, min_width=0):
        super().__init__(parent)
        install_editable_lists(self)
        self.root = self.winfo_toplevel()
        self.canvas = tk.Canvas(self, highlightthickness=0, yscrollincrement=18, xscrollincrement=18, bg="#edf2f7")
        self.min_width = min_width
        self._wheel_remainder = 0
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.columnconfigure(0, weight=1); self.rowconfigure(0, weight=1)
        self.canvas.grid(row=0,column=0,sticky="nsew")
        self.scrollbar.grid(row=0,column=1,sticky="ns")
        self.horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.horizontal.grid(row=1,column=0,sticky="ew")
        self.canvas.configure(xscrollcommand=self.horizontal.set)
        self.body = ttk.Frame(self.canvas)
        self.item = self.canvas.create_window(0,0,window=self.body,anchor="nw")
        self.body.bind("<Configure>",lambda _:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(self.item,width=max(self.min_width,e.width)))
        self.binding = self.root.bind("<MouseWheel>",self.wheel,add="+")
        self.focus_binding = self.root.bind("<FocusIn>",self.reveal_focus,add="+")

    def wheel(self,event):
        if not self.binding:
            return None
        if str(event.widget).startswith(str(self.body)+".") or event.widget is self.body or event.widget is self.canvas:
            owner = event.widget
            while owner is not None and not isinstance(owner, ScrollableFrame):
                owner = getattr(owner,"master",None)
            if owner is not self:
                return None  # An inner workspace owns its own scrolling.
            if isinstance(event.widget,(tk.Text,tk.Listbox,ttk.Treeview,ttk.Combobox,ttk.Spinbox)):
                return None  # These controls keep their own scrolling.
            if event.delta:
                self._wheel_remainder += event.delta
                steps = int(self._wheel_remainder / 120)
                self._wheel_remainder -= steps * 120
                if steps:
                    method = self.canvas.xview_scroll if getattr(event,"state",0) & 1 else self.canvas.yview_scroll
                    method(-steps * 3,"units")
                return "break"

    def reveal_focus(self, event):
        widget = event.widget
        owner = getattr(widget,"master",None)
        while owner is not None and not isinstance(owner,ScrollableFrame):
            owner = getattr(owner,"master",None)
        if owner is not self or not self.winfo_ismapped():
            return
        top = widget.winfo_rooty() - self.body.winfo_rooty()
        height = self.body.winfo_height()
        visible_top = self.canvas.canvasy(0)
        visible_bottom = visible_top + self.canvas.winfo_height()
        if height > 0 and (top < visible_top or top + widget.winfo_height() > visible_bottom):
            target = top if top < visible_top else top + widget.winfo_height() - self.canvas.winfo_height() + 12
            self.canvas.yview_moveto(max(0,target) / height)

    def close(self):
        if self.binding:
            self.root.unbind("<MouseWheel>",self.binding)
            self.binding = None
        if self.focus_binding:
            self.root.unbind("<FocusIn>",self.focus_binding)
            self.focus_binding = None


class FlowToolbar(ttk.Frame):
    """Wrap original action widgets without replacing callbacks or values."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        install_editable_lists(self)
        self.buttons = []
        self.disclosure = False
        self.more_button = self.more_menu = None
        self.bind("<Configure>", self.reflow)

    def add(self, text, command):
        button = ttk.Button(self,text=text,command=command)
        self.buttons.append(button)
        button.grid(row=0,column=len(self.buttons)-1,sticky="w",padx=(0,8),pady=3)
        return button

    def reflow(self, event):
        if event.widget is not self: return
        column = row = used = 0
        shown = self.buttons
        if self.disclosure and len(shown) > 4:
            for button in shown[2:]:
                button.grid_remove()
            shown = shown[:2] + [self.more_button]
        elif self.more_button is not None:
            self.more_button.grid_remove()
        for button in shown:
            width = button.winfo_reqwidth() + 8
            if column and used + width > max(1,event.width):
                row += 1; column = used = 0
            button.grid_configure(row=row,column=column)
            column += 1; used += width

    def set_disclosure(self, enabled):
        """Modern presentation only; preserve original Button commands/states.

        Secondary commands invoke their existing Button, so disabled guards and
        the owning panel's explicit confirmations remain in force.
        """
        self.disclosure = bool(enabled)
        if self.disclosure and len(self.buttons) > 4 and self.more_button is None:
            self.more_button = ttk.Menubutton(self, text="More actions ▾", takefocus=True)
            self.more_menu = tk.Menu(self.more_button, tearoff=False, postcommand=self._refresh_more)
            self.more_button.configure(menu=self.more_menu)
        self.reflow(SimpleNamespace(widget=self, width=max(1, self.winfo_width())))

    def _refresh_more(self):
        self.more_menu.delete(0, "end")
        for button in self.buttons[2:]:
            self.more_menu.add_command(label=button.cget("text"), command=button.invoke,
                                      state="disabled" if button.instate(["disabled"]) else "normal")


class ResponsiveGrid(ttk.Frame):
    """Reflow existing field groups; never reconstruct controls or values."""
    def __init__(self, parent, max_columns=4, min_cell=190, **kwargs):
        super().__init__(parent, **kwargs)
        self.cells = []
        self.max_columns, self.min_cell = max_columns, min_cell
        self.bind("<Configure>", self.reflow)

    def add(self, cell):
        if cell.master is not self:
            raise ValueError("Responsive fields must belong to this container")
        self.cells.append(cell)
        cell.grid(row=0, column=len(self.cells)-1, sticky="ew", padx=4, pady=3)
        self.reflow(SimpleNamespace(widget=self, width=max(1, self.winfo_width())))
        return cell

    def reflow(self, event):
        if event.widget is not self or not self.cells:
            return
        # Account for actual theme/font scaling rather than shrinking text.
        required = max(self.min_cell, min(400, max(c.winfo_reqwidth() for c in self.cells) + 8))
        columns = max(1, min(self.max_columns, event.width // required))
        for column in range(self.max_columns):
            self.columnconfigure(column, weight=int(column < columns), minsize=0)
        for index, cell in enumerate(self.cells):
            cell.grid_configure(row=index // columns, column=index % columns)


class Selector(ttk.Combobox):
    def __init__(self, parent, choices=(), on_select=None, on_add=None, **kwargs):
        self.variable = tk.StringVar(parent)
        super().__init__(parent, textvariable=self.variable, state="normal", **kwargs)
        self.on_select, self.on_add = on_select, on_add
        self.records, self.labels, self.selected_id, self.committed = {}, {}, None, ""
        self.changing = False
        self.set_choices(choices)
        self.variable.trace_add("write", self.filter)
        self.bind("<<ComboboxSelected>>", self.commit)
        self.bind("<Return>", self.commit)
        self.bind("<Escape>", self.cancel)
        attach_editable_list(self)

    def set_choices(self, choices):
        self.records = {key: f"{label} [{key}]" for key, label in choices}
        self.labels = {label: key for key, label in self.records.items()}
        self.configure(values=list(self.records.values()) + (["Add new…"] if self.on_add else []))

    def filter(self, *_):
        if not self.changing:
            term = self.variable.get().casefold()
            self.configure(values=[label for label in self.records.values() if term in label.casefold()] +
                           (["Add new…"] if self.on_add else []))

    def select(self, key):
        self.changing = True
        try:
            self.selected_id = key
            self.committed = self.records.get(key, "")
            self.variable.set(self.committed)
            self.configure(values=list(self.records.values()) + (["Add new…"] if self.on_add else []))
        finally:
            self.changing = False

    def commit(self, *_):
        text = self.variable.get()
        if text == "Add new…" and self.on_add:
            self.cancel(); self.on_add(); return "break"
        key = self.labels.get(text)
        matches = [k for k, label in self.records.items() if label.casefold() == text.casefold() or
                   k.casefold() == text.casefold()]
        if key is None and len(matches) == 1:
            key = matches[0]
        if key is not None:
            self.select(key)
            if self.on_select:
                self.on_select(key)
        # Uncommitted query remains a query; no entity is created.
        return "break"

    def cancel(self, *_):
        self.select(self.selected_id)
        return "break"


class ChoiceButtons(ttk.Frame):
    """A few directly selectable choices, wrapping at the current font scale."""
    def __init__(self, parent, choices=(), on_select=None, variable=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.variable = variable if variable is not None else tk.StringVar(self)
        self.on_select = on_select
        self.records, self.buttons = {}, {}
        self.set_choices(choices)
        self.bind("<Configure>", self.reflow)

    @property
    def selected_id(self):
        return self.variable.get() if self.variable.get() in self.records else None

    def set_choices(self, choices):
        records = dict(choices)
        if records == self.records:
            return
        for button in self.buttons.values():
            button.destroy()
        self.records, self.buttons = records, {}
        for key, label in records.items():
            button = ttk.Radiobutton(self, text=label, value=key, variable=self.variable,
                                     command=lambda k=key: self.on_select(k) if self.on_select else None)
            self.buttons[key] = button
        self.reflow()

    def select(self, key):
        self.variable.set(key if key in self.records else "")

    def reflow(self, event=None):
        if event is not None and event.widget is not self:
            return
        width = max(1, event.width if event else self.winfo_width())
        row = column = used = 0
        for button in self.buttons.values():
            required = button.winfo_reqwidth() + 12
            if column and used + required > width:
                row += 1; column = used = 0
            button.grid(row=row, column=column, sticky="w", padx=(0, 12), pady=2)
            used += required; column += 1


class VisibilityMenu(ttk.Menubutton):
    def __init__(self, parent, states, callback):
        super().__init__(parent, text="Show/Hide controls", takefocus=True)
        self.menu = tk.Menu(self, tearoff=False)
        self.configure(menu=self.menu)
        self.states = {name: tk.BooleanVar(self, value=value) for name, value in states.items()}
        for name, var in self.states.items():
            self.menu.add_checkbutton(label="Show " + name, variable=var,
                                      command=lambda: callback(self.values()))
        self.menu.add_separator()
        self.menu.add_command(label="Reset view", command=lambda: self.reset(callback))

    def values(self):
        return {name: var.get() for name, var in self.states.items()}

    def reset(self, callback):
        for name, var in self.states.items():
            var.set(name == "associations")
        callback(self.values())
