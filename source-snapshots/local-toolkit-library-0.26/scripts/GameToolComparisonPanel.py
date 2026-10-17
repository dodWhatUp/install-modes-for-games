"""Optional local-only comparison view for normalized provider summaries.

Loading and exporting are explicit. This view never starts a collector, recorder,
game, browser, process, input helper or profile migration. Imported declarations
are evaluated by the comparison core, not treated as runtime FG evidence.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from GameToolCompactUI import FlowToolbar


def _load_authored(name):
    """Load one fixed authored sibling, never a report-supplied module path."""
    if name not in ("GameToolComparison", "GameToolReportImport"):
        raise ValueError("Unsupported optional authored module")
    source = Path(__file__).with_name(name + ".py")
    before = source.stat()
    with source.open("rb") as handle:
        captured = handle.read(1024 * 1024 + 1)
    after = source.stat()
    if len(captured) > 1024 * 1024 or len(captured) != before.st_size or \
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != \
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("Optional authored module exceeded its source limit or changed while loading")
    spec = importlib.util.spec_from_file_location("game_tool_comparison_panel_" + name, source)
    if spec is None or spec.loader is None:
        raise ImportError("Optional authored module unavailable")
    module = importlib.util.module_from_spec(spec)
    # Execute only the captured UTF-8 authored bytes, not a timestamp pyc cache.
    exec(compile(captured.decode("utf-8-sig"), str(source), "exec", dont_inherit=True), module.__dict__)
    return module


def _load_core():
    return _load_authored("GameToolComparison")


def _load_importer():
    return _load_authored("GameToolReportImport")


class ComparisonPanel:
    """Embedded Tk view; constructor makes no data, clipboard or dialog request."""

    def __init__(self, parent, status, *, core=None, importer=None):
        import tkinter as tk
        from tkinter import ttk

        self.tk, self.ttk = tk, ttk
        self.parent, self.status = parent, status
        self.core = core
        self.importer = importer
        self.import_wizard = None
        self.last_import_error = None
        self.source_path = None
        self.source_sha256 = None
        self.dataset = self.result = None
        self.stale = False
        self.metric_ids = {}
        self.run_ids = {}
        self.source = tk.StringVar(master=parent, value="No dataset loaded. Choose an existing normalized summary JSON.")
        self.verdict = tk.StringVar(master=parent, value="OFFLINE REPORTING ONLY — no game, benchmark or recording is started.")
        self.metric = tk.StringVar(master=parent)

        ttk.Label(parent, text="OFFLINE COMPARISONS • Explicit local files only").pack(anchor="w")
        top = FlowToolbar(parent)
        top.pack(fill="x", pady=3)
        self.buttons = {}
        for index, (label, callback) in enumerate((("Import saved reports", self.open_import_wizard),
                                ("Load summary JSON", self.choose_file), ("Reload source", self.reload),
                                ("Copy summary", self.copy_summary), ("Export JSON", self.export_json),
                                ("Export HTML", self.export_html))):
            button = top.add(label, callback)
            self.buttons[label] = button
        ttk.Label(parent, textvariable=self.source, wraplength=1080).pack(anchor="w", pady=4)
        ttk.Label(parent, textvariable=self.verdict, wraplength=1080).pack(anchor="w", pady=4)
        picker = ttk.Frame(parent)
        picker.pack(fill="x", pady=3)
        ttk.Label(picker, text="Provider-defined metric").pack(side="left")
        self.metric_combo = ttk.Combobox(picker, textvariable=self.metric, state="readonly", width=68)
        self.metric_combo.pack(side="left", fill="x", expand=True, padx=8)
        self.metric_combo.bind("<<ComboboxSelected>>", self.metric_changed)

        self.tabs = ttk.Notebook(parent)
        self.tabs.pack(fill="both", expand=True)
        summary = ttk.Frame(self.tabs, padding=5)
        raw = ttk.Frame(self.tabs, padding=5)
        provenance = ttk.Frame(self.tabs, padding=5)
        self.tabs.add(summary, text="Case summaries and contrasts")
        self.tabs.add(raw, text="Raw runs and blockers")
        self.tabs.add(provenance, text="Definitions and provenance")

        panes = ttk.Panedwindow(summary, orient="vertical")
        panes.pack(fill="both", expand=True)
        case_box, contrast_box, chart_box = (ttk.Frame(panes) for _ in range(3))
        panes.add(case_box, weight=1)
        panes.add(contrast_box, weight=1)
        panes.add(chart_box, weight=2)
        self.case_tree = self._tree(case_box, ("Case", "Complete repeats", "Mean", "Minimum", "Maximum"), 4)
        self.contrast_tree = self._tree(contrast_box, ("Contrast", "Absolute delta", "Percent delta"), 4)
        self.chart = tk.Canvas(chart_box, background="#fafafa", height=160, highlightthickness=0)
        self.chart.pack(fill="both", expand=True)
        self.chart.bind("<Configure>", self._draw_chart)
        ttk.Label(summary, text="Repeat spread is descriptive, not statistical significance. Missing values stay unavailable; no lows or latency are recomputed.",
                  wraplength=1050).pack(anchor="w", pady=4)

        raw_panes = ttk.Panedwindow(raw, orient="vertical")
        raw_panes.pack(fill="both", expand=True)
        raw_table, raw_detail = ttk.Frame(raw_panes), ttk.Frame(raw_panes)
        raw_panes.add(raw_table, weight=1)
        raw_panes.add(raw_detail, weight=2)
        self.raw_tree = self._tree(raw_table, ("Run", "Case", "Repeat", "Status", "Selected raw value"), 7)
        self.raw_tree.bind("<<TreeviewSelect>>", self.show_run)
        self.run_text = self._text(raw_detail)
        self.provenance_text = self._text(provenance)
        self._write(self.run_text, "Raw reported values remain visible when comparison is blocked. Select a run to inspect its declared state and reasons.")
        self._write(self.provenance_text, "No current source or metric definition. Loading does not verify a game's effective FG or grant permission to run anything.")
        self._draw_chart()
        try:
            if self.core is None:
                self.core = _load_core()
        except Exception as error:
            self.verdict.set("Comparison core unavailable; existing Hub tools are unaffected.")
            self._status(f"Comparison module unavailable: {error}")

    def _status(self, text):
        if hasattr(self.status, "set"):
            self.status.set(text)
        elif callable(self.status):
            self.status(text)

    def _tree(self, parent, columns, height):
        tree = self.ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse", height=height)
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=230 if column in ("Run", "Contrast", "Status") else 150, minwidth=80)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical = self.ttk.Scrollbar(parent, command=tree.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = self.ttk.Scrollbar(parent, orient="horizontal", command=tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        return tree

    def _text(self, parent):
        widget = self.tk.Text(parent, wrap="none", height=8, font=("Consolas", 9), state="disabled")
        widget.grid(row=0, column=0, sticky="nsew")
        vertical = self.ttk.Scrollbar(parent, command=widget.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = self.ttk.Scrollbar(parent, orient="horizontal", command=widget.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        widget.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        return widget

    @staticmethod
    def _write(widget, value):
        if not isinstance(value, str):
            value = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    @staticmethod
    def _number(value):
        return "unavailable" if value is None else f"{value:.6g}" if isinstance(value, (float, int)) else str(value)

    def choose_file(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(parent=self.parent.winfo_toplevel(), title="Load existing normalized summary JSON",
                                          filetypes=(("Normalized summary JSON", "*.json"),))
        return self.load_from_path(path) if path else False

    def _get_importer(self):
        # Optional report adapters are loaded only after an explicit import
        # action. Their absence must not break manual normalized JSON loading.
        if self.importer is None:
            self.importer = _load_importer()
        return self.importer

    def open_import_wizard(self, *, show=True):
        """Open an owned modal preview; construction and cancellation write nothing."""
        try:
            importer = self._get_importer()
            if self.import_wizard is None or not self.import_wizard.window.winfo_exists():
                self.import_wizard = SavedReportImportWizard(self, importer)
                feedback = getattr(self.parent.winfo_toplevel(),"game_tools_feedback",None)
                if feedback is not None:
                    feedback.register_panel(self.import_wizard.window,"UI-202",self.import_wizard)
            if show:
                self.import_wizard.show()
            return self.import_wizard
        except Exception as error:
            self._status(f"Saved-report import unavailable; current comparison retained: {error}")
            return None

    def import_saved_reports(self, assignments, output_directory, *, title="Saved reports",
                             question="Compare saved provider summaries.", factor="changed_configuration"):
        """Explicitly archive selected original bytes, then use the guarded loader.

        Preview/build refusals preserve the current comparison. If a completed
        bundle cannot be loaded, the existing loader clears unvalidated numeric
        views; the immutable bundle and receipt are still available for review.
        """
        self.last_import_error = None
        try:
            receipt = self._get_importer().import_bundle(assignments, output_directory,
                                                       title=title, question=question, factor=factor)
            if not isinstance(receipt, dict) or not isinstance(receipt.get("dataset_path"), (str, Path)):
                raise ValueError("Importer returned no valid normalized dataset receipt")
            expected = receipt.get("dataset_sha256")
            if not isinstance(expected, str) or len(expected) != 64 or set(expected.lower()) - set("0123456789abcdef"):
                raise ValueError("Importer returned no valid normalized dataset hash")
        except Exception as error:
            self.last_import_error = str(error)
            self._status(f"Saved-report import refused; current comparison retained: {error}")
            return None
        if not self.load_from_path(receipt["dataset_path"], expected_sha256=expected):
            self._status("Saved-report bundle created, but its dataset could not be validated. No comparison was accepted.")
            return receipt
        self._status("Saved originals archived and normalized dataset loaded. Runtime FG remains unverified; no game, benchmark or recording was started.")
        return receipt

    def load_from_path(self, path, *, expected_sha256=None):
        """Validate/recompute an explicit local dataset; no provider is consulted."""
        try:
            self.source_path = Path(path)
            self.source_sha256 = None
            if self.core is None:
                raise ValueError("Comparison core unavailable")
            loaded = self.core.load_dataset(path)
            if expected_sha256 is not None and loaded["_source"]["sha256"] != expected_sha256.lower():
                raise ValueError("Normalized import changed after publication; archived receipt hash does not match")
            result = self.core.compare_dataset(loaded)
            source = loaded["_source"]
            self.dataset, self.result = loaded, result
            self.source_path = Path(source["path"])
            self.source_sha256 = source["sha256"]
            self.stale = False
            self.source.set(f"{self.source_path.name} • SHA-256 {self.source_sha256} • loaded snapshot, not a live source or measurement")
            self.metric_ids = {f'{metric["id"]} — {metric.get("label", metric["id"])} [{metric["unit"]}]': metric["id"]
                               for metric in result.get("metrics", [])}
            self.metric_combo["values"] = list(self.metric_ids)
            self.metric.set(next(iter(self.metric_ids), ""))
            self._refresh_views()
            self._status(f'Offline comparison {result["status"]}. No game, collector, benchmark or recording was started.')
            return True
        except Exception as error:
            self._clear(error)
            return False

    def reload(self):
        if self.source_path is None:
            self._status("No source to reload. Load a normalized summary JSON explicitly.")
            return False
        return self.load_from_path(self.source_path)

    def _clear(self, error):
        self.dataset = self.result = None
        self.metric_ids, self.run_ids = {}, {}
        self.metric_combo["values"] = ()
        self.metric.set("")
        for tree in (self.case_tree, self.contrast_tree, self.raw_tree):
            tree.delete(*tree.get_children())
        self.verdict.set("UNAVAILABLE — source refused; no comparison or action performed.")
        self.source.set("Source unavailable; choose a valid JSON or explicitly reload the previously selected source.")
        self._write(self.run_text, f"Source refused: {error}")
        self._write(self.provenance_text, "No current validated dataset.")
        self._draw_chart()
        self._status(f"Offline comparison refused: {error}")

    def _source_current(self):
        if self.result is None or self.source_path is None or self.source_sha256 is None or self.stale:
            self._status("No current comparison. Explicit reload is required.")
            return False
        try:
            # The fixed core checks only this bounded local source; this is not
            # a live provider, profile read, watcher, or changed-byte acceptance.
            self.core.assert_source_current(self.source_path, self.source_sha256)
            return True
        except Exception as error:
            self.stale = True
            self.verdict.set("STALE SOURCE — explicit reload required; exports, clipboard and numeric comparison suppressed.")
            self.source.set(f"{self.source_path.name} changed or is unavailable. Displayed raw rows are historical only.")
            self.case_tree.delete(*self.case_tree.get_children())
            self.contrast_tree.delete(*self.contrast_tree.get_children())
            self._draw_chart()
            self._status(f"Source changed; nothing copied or exported: {error}")
            return False

    def metric_changed(self, event=None):
        if self._source_current():
            self._refresh_views()

    def _metric_id(self):
        return self.metric_ids.get(self.metric.get())

    def _comparable(self):
        return (self.result is not None and not self.stale
                and self.result.get("status") in ("COMPARABLE", "PARTIAL")
                and any(row["metric_id"] == self._metric_id() for row in self.result.get("case_summaries", [])))

    def _refresh_views(self):
        result = self.result
        if result is None:
            return
        label = "SYNTHETIC FIXTURE — NOT MEASURED TOOL COSTS • " if result.get("synthetic_fixture") else "IMPORTED PROVIDER SUMMARY • "
        self.verdict.set(label + result["status"] + f' • {len(result.get("raw_runs", []))} retained runs; '
                         + f'{len(result.get("gates", []))} gates. Full blockers and warnings are in the read-only detail tabs.')
        metric_id = self._metric_id()
        for tree in (self.case_tree, self.contrast_tree, self.raw_tree):
            tree.delete(*tree.get_children())
        if self._comparable():
            for row in result.get("case_summaries", []):
                if row["metric_id"] == metric_id:
                    self.case_tree.insert("", "end", values=(row["case"], row["n"], self._number(row["mean"]),
                                                               self._number(row["min"]), self._number(row["max"])))
            for row in result.get("comparisons", []):
                if row["metric_id"] == metric_id:
                    self.contrast_tree.insert("", "end", values=(row["contrast"], self._number(row["delta"]),
                                                                   self._number(row.get("percent"))))
        self.run_ids = {}
        for index, row in enumerate(result.get("raw_runs", [])):
            identifier = f"run-{index}"
            self.run_ids[identifier] = row
            metrics = row.get("metrics", row.get("values", {}))
            value = metrics.get(metric_id) if isinstance(metrics, dict) else None
            self.raw_tree.insert("", "end", iid=identifier, values=(row["id"], row["case"], row.get("repeat", "unavailable"),
                                                                      row.get("status", "unknown"), self._number(value)))
        self._write(self.run_text, {"gates": result.get("gates", []), "warnings": result.get("warnings", []),
                                   "status": result["status"], "execution": "none"})
        self._write(self.provenance_text, {key: value for key, value in result.items()
                                          if key not in ("raw_runs", "case_summaries", "comparisons")})
        self._draw_chart()

    def show_run(self, event=None):
        selected = self.raw_tree.selection()
        if selected and selected[0] in self.run_ids:
            self._write(self.run_text, {"historical_only": self.stale, "run": self.run_ids[selected[0]]})

    def _draw_chart(self, event=None):
        if not hasattr(self, "chart"):
            return
        if self.result is not None and not self.stale and not self._source_current():
            return
        self.chart.delete("all")
        width = max(self.chart.winfo_width(), 480)
        height = max(self.chart.winfo_height(), 150)
        if not self._comparable():
            self.chart.create_text(width / 2, height / 2, text="No comparable numeric chart.\nLoad a valid source; review blockers or reload changed bytes.",
                                   width=width - 30, fill="#555555", tags="blocked")
            return
        rows = [row for row in self.result.get("case_summaries", []) if row["metric_id"] == self._metric_id()]
        rows = [row for row in rows if row.get("mean") is not None]
        if not rows:
            self.chart.create_text(width / 2, height / 2, text="No provider value for the selected metric.", tags="blocked")
            return
        minimum = min(0, min(row["mean"] for row in rows))
        maximum = max(0, max(row["mean"] for row in rows))
        scale = maximum - minimum or 1
        plot_width = max(width - 360, 90)
        zero_x = 120 + (-minimum / scale) * plot_width
        step = max(28, (height - 30) / len(rows))
        title = "Synthetic fixture — not measured costs" if self.result.get("synthetic_fixture") else "Imported mean and repeat range; descriptive only"
        self.chart.create_text(10, 10, text=title, anchor="nw", fill="#444444")
        for index, row in enumerate(rows):
            y = 28 + index * step
            value_x = 120 + ((row["mean"] - minimum) / scale) * plot_width
            self.chart.create_text(10, y + 10, text=row["case"], anchor="w", tags="case")
            self.chart.create_rectangle(min(zero_x, value_x), y, max(zero_x, value_x), y + 20,
                                        fill="#2c7697", outline="", tags="bar")
            self.chart.create_text(130 + plot_width, y + 10, anchor="w", text=f'{self._number(row["mean"])} [{self._number(row["min"])}–{self._number(row["max"])}]', tags="value")

    def copy_summary(self):
        if not self._source_current():
            return False
        try:
            selected = self.core.compare_dataset(self.dataset, metric_id=self._metric_id())
            encoded = json.dumps(selected, indent=2, ensure_ascii=False, allow_nan=False)
            root = self.parent.winfo_toplevel()
            root.clipboard_clear()
            root.clipboard_append(encoded)
            self._status("Copied selected provider-metric offline summary only. No upload, launch, recording or benchmark.")
            return True
        except Exception as error:
            if not self._source_current():
                return False
            self._status(f"Offline summary copy refused: {error}")
            return False

    def export_to_path(self, path, format="json"):
        if not self._source_current():
            return None
        try:
            receipt = self.core.export_report(self.source_path, path, format=format, expected_sha256=self.source_sha256,
                                               metric_id=self._metric_id())
            self._status(f"Offline {format.upper()} report saved as a new local file. Nothing was opened or uploaded.")
            return receipt
        except Exception as error:
            # Refusing an existing target must not discard a valid current view.
            if not self._source_current():
                return None
            self._status(f"Offline report export refused: {error}")
            return None

    def _export_dialog(self, format):
        if not self._source_current():
            return None
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(parent=self.parent.winfo_toplevel(), title=f"Save new offline {format.upper()} report",
                                           defaultextension=f".{format}", confirmoverwrite=False,
                                           filetypes=((f"{format.upper()} report", f"*.{format}"),))
        return self.export_to_path(path, format) if path else None

    def export_json(self):
        return self._export_dialog("json")

    def export_html(self):
        return self._export_dialog("html")


class SavedReportImportWizard:
    """Owned, explicit one-factor saved-summary import with read-only previews.

    Case assignments and the tested factor are user declarations, not proof of
    loaded game components. Missing metadata stays unknown. There is no option
    to mark FG verified, set a synthetic origin or start a live provider.
    """

    MAX_REPORTS = 32

    def __init__(self, panel, importer):
        self.panel, self.importer = panel, importer
        tk, ttk = panel.tk, panel.ttk
        self.window = tk.Toplevel(panel.parent.winfo_toplevel())
        self.window.withdraw()
        self.window.title("Import saved provider summaries — offline only")
        self.window.geometry("1000x720")
        self.window.minsize(640, 480)
        self.window.transient(panel.parent.winfo_toplevel())
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)
        self.window.bind("<Escape>", lambda event: self.cancel())
        self.records = {}
        self.next_id = 0
        self.receipt = None
        self.title = tk.StringVar(master=self.window, value="Saved reports")
        self.question = tk.StringVar(master=self.window, value="Compare saved provider summaries.")
        self.factor = tk.StringVar(master=self.window, value="changed_configuration")
        self.case = tk.StringVar(master=self.window, value="unassigned")
        self.notice = tk.StringVar(master=self.window, value="No reports selected. Preview reads only the files you choose; Cancel writes nothing.")

        body = ttk.Frame(self.window, padding=10)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="SUMMARY REPORTS ONLY • No game, benchmark, provider or recording is started.").pack(anchor="w")
        ttk.Label(body, text="Supported adapters inspect saved JSON/CSV summaries, not raw frame traces. Assign every report explicitly to baseline or a. Unknown metadata and runtime FG remain unverified.",
                  wraplength=950).pack(anchor="w", pady=5)
        settings = ttk.Frame(body)
        settings.pack(fill="x", pady=3)
        self.entries = {}
        for row, (label, variable) in enumerate((("Report title", self.title), ("Comparison question", self.question),
                                               ("Tested factor ID (declaration)", self.factor))):
            ttk.Label(settings, text=label).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
            entry = ttk.Entry(settings, textvariable=variable)
            entry.grid(row=row, column=1, sticky="ew", pady=2)
            self.entries[label] = entry
        settings.columnconfigure(1, weight=1)
        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=5)
        self.buttons = {}
        for label, callback in (("Add saved reports", self.choose_reports), ("Remove selected", self.remove_selected)):
            button = ttk.Button(actions, text=label, command=callback)
            button.pack(side="left", padx=(0, 6))
            self.buttons[label] = button
        ttk.Label(actions, text="Selected case (one or more rows):").pack(side="left", padx=5)
        self.case_combo = ttk.Combobox(actions, textvariable=self.case, values=("unassigned", "baseline", "a"),
                                       state="readonly", width=12)
        self.case_combo.pack(side="left")
        self.case_combo.bind("<<ComboboxSelected>>", self.assign_selected)

        panes = ttk.Panedwindow(body, orient="vertical")
        panes.pack(fill="both", expand=True)
        table_box, detail_box = ttk.Frame(panes), ttk.Frame(panes)
        panes.add(table_box, weight=1)
        panes.add(detail_box, weight=2)
        self.tree = panel._tree(table_box, ("Saved report", "Case", "Adapter", "Preview"), 7)
        self.tree.configure(selectmode="extended")
        self.tree.bind("<<TreeviewSelect>>", self.show_selected)
        self.detail = panel._text(detail_box)
        panel._write(self.detail, "Choose reports to inspect provider-defined values, metric definitions, source identity and limitations. Nothing is normalized or archived until Create import and load.")
        ttk.Label(body, textvariable=self.notice, wraplength=950).pack(anchor="w", pady=5)
        bottom = ttk.Frame(body)
        bottom.pack(fill="x")
        for label, callback in (("Create import and load", self.create_import), ("Cancel", self.cancel)):
            button = ttk.Button(bottom, text=label, command=callback)
            button.pack(side="right", padx=4)
            self.buttons[label] = button

    def show(self):
        self.window.deiconify()
        # Tk modal ownership prevents Hub shortcuts from acting on remembered
        # rows while this wizard owns the input. No global/native input hook.
        self.window.grab_set()

    def choose_reports(self):
        from tkinter import filedialog
        selected = filedialog.askopenfilenames(parent=self.window, title="Select existing saved summary reports",
                                               filetypes=(("Saved JSON/CSV summaries", "*.json *.csv"),))
        return self.add_paths(selected) if selected else False

    def add_paths(self, paths):
        """Inspect explicit files without accepting a precomputed verdict."""
        paths = tuple(paths)
        if len(paths) + len(self.records) > self.MAX_REPORTS:
            self.notice.set("At most 32 saved reports can be selected. Remove reports before adding more; nothing was read or written.")
            return False
        added = False
        for path in paths:
            key = f"report-{self.next_id}"
            self.next_id += 1
            record = {"path": str(path), "case": "unassigned", "preview": None, "error": None}
            try:
                record["preview"] = self.importer.inspect_report(path)
            except Exception as error:
                record["error"] = str(error)
            self.records[key] = record
            preview = record["preview"]
            self.tree.insert("", "end", iid=key, values=(Path(path).name, "unassigned",
                preview.get("adapter", "unknown") if preview else "refused",
                f'{len(preview.get("issues", []))} limitations' if preview else "source refused"))
            added = True
            self.tree.selection_set(key)
            self.show_selected()
        self._notice()
        return added

    def _notice(self):
        counts = {case: sum(record["case"] == case for record in self.records.values())
                  for case in ("baseline", "a", "unassigned")}
        refused = sum(record["preview"] is None for record in self.records.values())
        self.notice.set(f'{len(self.records)} reports • baseline {counts["baseline"]} • a {counts["a"]} • unassigned {counts["unassigned"]} • refused {refused}. '
                        "Assignments are declarations only. Raw values remain visible; rendering comparisons stay blocked without trusted FG evidence.")

    def show_selected(self, event=None):
        selected = self.tree.selection()
        if not selected or selected[0] not in self.records:
            return
        record = self.records[selected[0]]
        cases = {self.records[key]["case"] for key in selected if key in self.records}
        self.case.set(next(iter(cases)) if len(cases) == 1 else "unassigned")
        self.panel._write(self.detail, {"report_name": Path(record["path"]).name,
                                       "selected_report_count": len(selected),
                                       "case_assignment": record["case"],
                                       "assignment_evidence": "user declaration only",
                                       "preview": record["preview"], "refusal_reason": record["error"],
                                       "execution": "none", "runtime_verification": False})

    def assign_selected(self, event=None):
        selected = self.tree.selection()
        case = self.case.get()
        if not selected or selected[0] not in self.records or case not in ("unassigned", "baseline", "a"):
            return False
        for key in selected:
            if key not in self.records:
                continue
            self.records[key]["case"] = case
            values = list(self.tree.item(key, "values"))
            values[1] = case
            self.tree.item(key, values=values)
        self.show_selected()
        self._notice()
        return True

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected or selected[0] not in self.records:
            return False
        for key in selected:
            if key in self.records:
                del self.records[key]
                self.tree.delete(key)
        self.case.set("unassigned")
        self.panel._write(self.detail, "Report removed from this preview only. Its original file is unchanged.")
        self._notice()
        return True

    def assignments(self):
        if not self.records:
            raise ValueError("Choose existing saved reports before creating an import")
        result = []
        for record in self.records.values():
            if record["case"] == "unassigned":
                raise ValueError("Assign every selected report explicitly to baseline or a")
            if record["preview"] is None:
                raise ValueError("Remove refused reports; inspect the preview's source refusal reason")
            preview = record["preview"]
            result.append({"path": record["path"], "case": record["case"], "adapter": preview["adapter"],
                           "expected_sha256": preview["private_source"]["sha256"]})
        return result

    def create_import(self, output_directory=None):
        try:
            assignments = self.assignments()
        except Exception as error:
            self.notice.set(f"Import not created: {error}. Current comparison retained.")
            return None
        if output_directory is None:
            from tkinter import filedialog
            # A save-name dialog picks an exact NEW directory name, not an
            # existing directory whose user-owned contents could be overwritten.
            output_directory = filedialog.asksaveasfilename(parent=self.window,
                title="Choose a NEW import folder name (not a file; must not exist)",
                initialfile="saved-report-import", confirmoverwrite=False,
                filetypes=(("New import folder name", "*"),))
            if not output_directory:
                self.notice.set("Destination cancelled. No import was written; current comparison retained.")
                return None
        receipt = self.panel.import_saved_reports(assignments, output_directory, title=self.title.get(),
                                                  question=self.question.get(), factor=self.factor.get())
        if receipt is None:
            reason = self.panel.last_import_error or "The saved-report adapter refused this request"
            self.notice.set(f"Import refused: {reason[:250]}. Preview and current comparison retained.")
            selected = self.tree.selection()
            record = self.records.get(selected[0]) if selected else None
            self.panel._write(self.detail, {"import_refusal": reason, "selected_report": record,
                                           "execution": "none", "runtime_verification": False})
            return None
        self.receipt = receipt
        self.cancel()
        return receipt

    def cancel(self):
        if self.window.winfo_exists():
            if self.window.grab_current() is self.window:
                self.window.grab_release()
            self.window.destroy()
        if self.panel.import_wizard is self:
            self.panel.import_wizard = None
