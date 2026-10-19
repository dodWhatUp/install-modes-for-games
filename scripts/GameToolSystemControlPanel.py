"""Human read-only views, reusing the toolkit's compact controls and readers."""
from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from GameToolCompactUI import FlowToolbar, ScrollableFrame, Selector
from game_system_control import VERSION
from game_system_control.contracts import ContextError
from game_system_control.explorer import build_view, graph_text
from game_system_control.inventory import check_sources, load_context, project_context
from game_system_control.overview import overview, fetch_detail, journal_summary
from game_system_control.preflight import check_request

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/system-control/context.example.json"


class SystemControlPanel(ttk.Frame):
    def __init__(self, parent, *, context_path=EXAMPLE, source_root=None):
        super().__init__(parent)
        self.context_path = Path(context_path)
        self.source_root = Path(source_root) if source_root else self.context_path.absolute().parent
        self.context = self.view = self.result = None
        self.accepted_draft = None
        self._rendering = False
        self.status = tk.StringVar(self, "Select a context. Nothing is submitted or executed.")
        ttk.Label(self, text="System control center", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=8, pady=5)
        self.notice = ttk.Label(self, text="Read-only source preview. Example devices and chats are invented; live connections are not observed.", wraplength=700)
        self.notice.pack(fill="x", padx=8)
        bar = FlowToolbar(self); bar.pack(fill="x", padx=8)
        bar.add("Select context…", self.choose_context)
        bar.add("View current project", self.current_project)
        bar.add("Reload selected sources", self.reload)
        bar.add("Inspect selected journal…", self.choose_journal)
        bar.add("Clear private view", self.clear)
        self.notebook = ttk.Notebook(self); self.notebook.pack(fill="both", expand=True, padx=8, pady=5)
        self.explore_tab = ttk.Frame(self.notebook)
        self.request_tab = ttk.Frame(self.notebook)
        self.activity_tab = ttk.Frame(self.notebook)
        for panel, label in ((self.explore_tab, "Architecture & instructions"), (self.request_tab, "Request check"), (self.activity_tab, "Activity & devices")):
            self.notebook.add(panel, text=label)
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self.clear_detail())
        self._explorer(); self._preflight(); self._activity()
        ttk.Label(self, textvariable=self.status, wraplength=700).pack(fill="x", padx=8, pady=5)
        self.bind("<Configure>", self._wrap, add="+")
        self.reload()

    @staticmethod
    def _text(parent, height=6):
        box = ttk.Frame(parent); box.pack(fill="both", expand=True, pady=4)
        text = tk.Text(box, height=height, wrap="word", state="disabled", takefocus=True)
        scroll = ttk.Scrollbar(box, command=text.yview); scroll.pack(side="right", fill="y")
        text.configure(yscrollcommand=scroll.set); text.pack(side="left", fill="both", expand=True)
        return text

    @staticmethod
    def _put(widget, value):
        widget.configure(state="normal"); widget.delete("1.0", "end")
        widget.insert("1.0", value); widget.configure(state="disabled")

    def _explorer(self):
        self.explore_scroll = ScrollableFrame(self.explore_tab)
        self.explore_scroll.pack(fill="both", expand=True)
        body = self.explore_scroll.body
        ttk.Label(body, text="Find or select a component / instruction").pack(anchor="w")
        self.selector = Selector(body, on_select=self.select_node)
        self.selector.pack(fill="x", pady=3)
        self.selector.variable.trace_add("write", lambda *_: self.filter_nodes())
        self.tree = ttk.Treeview(body, columns=("name", "state"), show="headings", height=5, selectmode="browse")
        self.tree.heading("name", text="Component or instruction"); self.tree.heading("state", text="Source / load")
        self.tree.column("name", width=400, minwidth=140); self.tree.column("state", width=180, minwidth=120)
        self.tree.pack(fill="both", expand=True); self.tree.bind("<<TreeviewSelect>>", self.tree_selected)
        self.show_graph = tk.BooleanVar(self, False)
        ttk.Checkbutton(body, text="Show dependency graph and list", variable=self.show_graph, command=self.toggle_graph).pack(anchor="w")
        self.graph_box = ttk.Frame(body)
        self.canvas = tk.Canvas(self.graph_box, height=180, background="#f4f6f8", takefocus=True)
        self.canvas.pack(side="left", fill="both", expand=True)
        graph_scroll = ttk.Scrollbar(self.graph_box, command=self.canvas.yview)
        graph_scroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=graph_scroll.set)
        self.graph_list = self._text(body, 4)
        self.graph_list.master.pack_forget()
        self.details = self._text(body, 8)
        self._put(self.details, "Select a component or instruction to see its owner, exact source revision, applicability and observed coverage.")

    def _preflight(self):
        self.request_scroll = ScrollableFrame(self.request_tab)
        self.request_scroll.pack(fill="both", expand=True)
        body = self.request_scroll.body
        ttk.Label(body, text="Original request · retained until you deliberately choose an alternative").pack(anchor="w")
        self.draft = tk.Text(body, height=5, wrap="word", undo=True)
        self.draft.pack(fill="x", pady=4); self.draft.bind("<<Modified>>", self.draft_changed)
        bar = FlowToolbar(body); bar.pack(fill="x")
        bar.add("Check draft", self.review_draft)
        self.accept_button = bar.add("Use suggested draft", self.accept_candidate)
        self.accept_button.configure(state="disabled")
        self.preflight_output = self._text(body, 11)
        ttk.Label(body, text="Chosen alternative · no automatic submission").pack(anchor="w")
        self.accepted_output = self._text(body, 4)

    def _activity(self):
        self.activity_scroll = ScrollableFrame(self.activity_tab)
        self.activity_scroll.pack(fill="both", expand=True)
        body = self.activity_scroll.body
        ttk.Label(body, text="Filter device and activity reports").pack(anchor="w")
        self.activity_filter = tk.StringVar(self)
        ttk.Entry(body, textvariable=self.activity_filter).pack(fill="x")
        self.activity_filter.trace_add("write", lambda *_: self.filter_activity())
        self.activity_output = self._text(body, 13)
        ttk.Label(body, text="Optional full-content reference · retrieved only by the button below").pack(anchor="w")
        self.resource = tk.StringVar(self)
        self.resource_control = ttk.Combobox(body, textvariable=self.resource, state="readonly")
        self.resource_control.pack(fill="x")
        self.resource_control.bind("<<ComboboxSelected>>", lambda _e: self.clear_detail())
        self.detail_authorized = tk.BooleanVar(self, False)
        ttk.Checkbutton(body, text="I authorize reading this selected local reference", variable=self.detail_authorized).pack(anchor="w")
        bar = FlowToolbar(body); bar.pack(fill="x")
        bar.add("Read selected detail", self.read_detail); bar.add("Forget detail", self.clear_detail)
        self.detail_output = self._text(body, 6)

    def _wrap(self, event):
        if event.widget is self:
            width = max(220, event.width - 28)
            self.notice.configure(wraplength=width)

    def choose_context(self):
        value = filedialog.askopenfilename(parent=self, title="Select a read-only context", filetypes=[("Context JSON", "*.json")])
        if not value:
            return
        # Cancel never changes the selected context, draft or previous results.
        try:
            load_context(value)
        except (ContextError, OSError) as exc:
            self.status.set(str(exc)); return
        self.project_mode = False
        self.context_path = Path(value); self.source_root = self.context_path.absolute().parent
        self.reload()

    def reload(self):
        try:
            context = project_context(self.source_root) if getattr(self, "project_mode", False) else load_context(self.context_path)
            view = build_view(context, self.source_root)
            self.context, self.view = context, view
            self.selector.set_choices([(n["id"], n["label"]) for n in view["nodes"]])
            self.selector.select(None)
            self.filter_nodes(); self.render_graph(); self.render_activity()
            self.resource_control.configure(values=[r["id"] for r in context.get("resources", [])])
            self.resource.set("")
            self.notice.configure(text=context.get("label", "Selected context") + " · source view, not a live Codex-state inspector")
            self.status.set("Sources checked. Actual runtime load, hidden context and live connections remain unobserved.")
        except (ContextError, OSError) as exc:
            self.context = self.view = None
            self.activity_state = {}
            self.selector.set_choices([]); self.tree.delete(*self.tree.get_children())
            self.canvas.delete("all")
            for widget in (self.graph_list, self.activity_output):
                self._put(widget, "")
            self.resource_control.configure(values=[]); self.resource.set("")
            self._put(self.details, str(exc)); self.status.set("Context refused; select or reload an intact source.")
        self.invalidate(); self.clear_detail()

    def current_project(self):
        self.project_mode = True
        self.source_root = Path(__file__).resolve().parents[1]
        self.reload()

    def filter_nodes(self):
        if not self.view or self._rendering:
            return
        self._rendering = True
        try:
            query = self.selector.variable.get()
            query = "" if query == self.selector.committed else query.casefold()
            chosen = self.selector.selected_id
            self.tree.delete(*self.tree.get_children())
            for n in self.view["nodes"]:
                if all(t in (n["label"] + " " + n["id"] + " " + n.get("trigger", "")).casefold() for t in query.split()):
                    self.tree.insert("", "end", iid=n["id"], values=(n["label"], n["source"]["availability"] + " / " + n["runtime_load"]))
            if chosen and self.tree.exists(chosen):
                self.tree.selection_set(chosen)
        finally:
            self._rendering = False

    def tree_selected(self, _event=None):
        selected = self.tree.selection()
        if selected and not self._rendering and selected[0] != self.selector.selected_id:
            self.selector.select(selected[0]); self.select_node(selected[0])

    def select_node(self, ident):
        if not self.view:
            return
        node = next(n for n in self.view["all_nodes"] if n["id"] == ident)
        source = node["source"]
        text = f"{node['label']}\nKind: {node['kind']} · scope applicable: {node['applicable']}\nSource: {source['owner']} / {source['locator']}\nSHA-256: {source['sha256']}\nSource verification: {source['verification']} / {source['availability']}\nRuntime: {node['runtime_load']}\nDeclared trigger: {node.get('trigger', 'none')}\nDependencies: {', '.join(node.get('depends_on', [])) or 'none'}\n\n{self.view['precedence']}\n\nUnknown: {', '.join(self.view['unknowns'])}"
        if self.view["conflicts"]:
            text += "\n\nConflicting declarations: " + json.dumps(self.view["conflicts"], ensure_ascii=False)
        if self.view["repeated_defaults"]:
            text += "\n\nRepeated defaults: " + json.dumps(self.view["repeated_defaults"], ensure_ascii=False)
        self._put(self.details, text)

    def toggle_graph(self):
        if self.show_graph.get():
            self.graph_box.pack(fill="x", before=self.details.master)
            self.graph_list.master.pack(fill="x", before=self.details.master)
        else:
            self.graph_box.pack_forget()
            self.graph_list.master.pack_forget()

    def render_graph(self):
        self.canvas.delete("all")
        if not self.view:
            return
        nodes = self.view["nodes"]
        positions = {n["id"]: (120, 26 + i * 64) for i, n in enumerate(nodes)}
        for edge in self.view["edges"]:
            if edge["from"] in positions and edge["to"] in positions:
                x, y = positions[edge["from"]]; _, target = positions[edge["to"]]
                self.canvas.create_line(x + 95, y, x + 125, y, x + 125, target, x + 95, target, arrow="last", fill="#63778b")
        for n in nodes:
            x, y = positions[n["id"]]
            self.canvas.create_rectangle(x - 95, y - 18, x + 95, y + 18, fill="white", outline="#63778b", tags=(n["id"],))
            self.canvas.create_text(x, y, text=n["id"], tags=(n["id"],))
            self.canvas.tag_bind(n["id"], "<Button-1>", lambda _e, key=n["id"]: (self.selector.select(key), self.select_node(key)))
        self.canvas.configure(scrollregion=(0, 0, 280, max(180, len(nodes) * 64 + 20)))
        self._put(self.graph_list, graph_text(self.view))

    def invalidate(self):
        self.result = None; self.accepted_draft = None
        self.accept_button.configure(state="disabled")
        self._put(self.accepted_output, "")
        self._put(self.preflight_output, "Draft or context changed. Run Check draft to refresh the comparison.")

    def draft_changed(self, _event=None):
        if self.draft.edit_modified():
            self.invalidate(); self.draft.edit_modified(False)

    def review_draft(self):
        try:
            if self.context is None:
                raise ContextError("Select an intact context first.")
            self.view = build_view(self.context, self.source_root)
            self.result = check_request(self.draft.get("1.0", "end-1c"), self.view)
            lines = ["Static checks · no model call or submission", ""]
            for f in self.result["findings"]:
                lines += [f["class"] + " / " + f["code"], f["message"], "Sources: " + ", ".join(f["sources"]), ""]
            lines += ["Candidate:", self.result["candidate"], "", self.result["limitations"]]
            self._put(self.preflight_output, "\n".join(lines))
            self.accept_button.configure(state="normal" if self.result["candidate"] != self.result["original"] else "disabled")
            self.status.set("Review complete. The original remains unchanged.")
        except (ContextError, OSError) as exc:
            self.invalidate(); self._put(self.preflight_output, str(exc))

    def accept_candidate(self):
        if self.result is None:
            return
        fresh = build_view(self.context, self.source_root)
        if fresh["revision"] != self.result["context_revision"] or self.draft.get("1.0", "end-1c") != self.result["original"]:
            self.invalidate(); self.status.set("Draft or sources changed; run the check again."); return
        self.accepted_draft = self.result["candidate"]
        self._put(self.accepted_output, self.accepted_draft)
        self.status.set("Alternative selected locally. Nothing was submitted; the original is retained.")

    def render_activity(self):
        state = overview(check_sources(self.context, self.source_root))
        self.activity_state = state
        self.filter_activity()

    def filter_activity(self):
        if self.context is None or not hasattr(self, "activity_state"):
            return
        self.clear_detail()
        state = self.activity_state
        terms = self.activity_filter.get().casefold().split()
        matches = lambda row: all(t in json.dumps(row, ensure_ascii=False).casefold() for t in terms)
        lines = ["Selected reports only · live connection not observed", ""]
        for d in state["devices"]:
            if not matches(d): continue
            lines += [f"Device: {d['label']} · {d['availability']} · {d['freshness']}"]
        for e in state["events"]:
            if not matches(e): continue
            lines += [f"{e['at']} · {e['operation_id']} · {e['state']} · {e['coverage']}", e["next_decision"]]
        for a in state["activities"]:
            if not matches(a): continue
            lines += ["", "Chat/activity goal: " + str(a["goal"]), "Outcome: " + str(a["outcome"]),
                      "Blocker: " + str(a["blocker"]), "Next: " + str(a["next_boundary"]),
                      "Changed artifacts: " + str(a["changed_artifacts"]), "Source: " + str(a["source_id"]),
                      "Retention: " + str(a["retention"]) + " · full content not loaded"]
        self._put(self.activity_output, "\n".join(lines))

    def read_detail(self):
        try:
            if self.context is None:
                raise ContextError("Select a context first.")
            result = fetch_detail(self.context, self.resource.get(), self.source_root,
                                  requested=True, authorized=self.detail_authorized.get())
            self._put(self.detail_output, result["content"])
            self.status.set("Selected detail is in memory only. Forget detail or leave this tab to clear it.")
        except (ContextError, OSError) as exc:
            self.clear_detail(); self.status.set(str(exc))

    def clear_detail(self):
        if hasattr(self, "detail_output"):
            self._put(self.detail_output, ""); self.detail_authorized.set(False)

    def choose_journal(self):
        value = filedialog.askopenfilename(parent=self, title="Inspect selected journal", filetypes=[("Journal", "*.jsonl")])
        if not value:
            return
        try:
            report = journal_summary(value)
            self._put(self.activity_output, json.dumps(report, indent=2))
            self.notebook.select(self.activity_tab)
        except (ValueError, OSError) as exc:
            self.status.set(str(exc))

    def clear(self):
        self.context = self.view = None
        self.selector.set_choices([]); self.selector.select(None)
        self.tree.delete(*self.tree.get_children()); self.canvas.delete("all")
        self.draft.delete("1.0", "end")
        for widget in (self.details, self.graph_list, self.preflight_output, self.activity_output):
            self._put(widget, "")
        self.resource_control.configure(values=[]); self.resource.set("")
        self.activity_state = {}; self.activity_filter.set("")
        self.invalidate(); self.clear_detail(); self.status.set("Private view cleared. No cache was written.")

    def close(self):
        self.clear()
