"""Compact, explicit snapshot inspection; no game or native-profile writes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog

import GameToolDoomBindingInspect as api
from GameToolCompactUI import FlowToolbar, ResponsiveGrid, ScrollableFrame, Selector, TableLayout


def derive_owner_from_path(path) -> str | None:
    """Only the explicit standard Steam role proves a path-derived account.

    An archive's arbitrary parent numbers, a currently logged-in different user
    or a similar save path do not establish ownership of the selected snapshot.
    Authentication must still validate the derived owning identity.
    """
    text = str(path)
    value = PureWindowsPath(text) if '\\' in text or re.match(r'^[A-Za-z]:', text) else PurePosixPath(text)
    parts = value.parts
    if not value.is_absolute() or len(parts) < 6:
        return None
    tail = parts[-6:]
    if (tail[0].casefold(), tail[2], tail[3].casefold(), tail[4].casefold(), tail[5].casefold()) != (
            'userdata', '3017860', 'remote', 'profile', 'profile.bin'):
        return None
    if not re.fullmatch(r'[0-9]{1,10}', tail[1]) or not 0 < int(tail[1]) <= 0xffffffff:
        return None
    return str(api.STEAM_ID64_BASE + int(tail[1]))


def read_selected_snapshot(path, identity: str) -> dict:
    """Called off Tk after explicit file selection. Returns only binding data."""
    selected = Path(path)
    if selected.name.casefold() != 'profile.bin':
        raise api.InspectError('FILE_ROLE_UNSUPPORTED', 'Select an existing Steam profile.bin snapshot.')
    with selected.open('rb') as stream:
        raw = stream.read(api.MAX_BYTES + 1)
    pin = hashlib.sha256(raw).hexdigest()
    return api.inspect_snapshot(raw, identity, expected_sha256=pin)


def filtered_rows(rows, term='', context='all', family='all'):
    term = term.casefold().strip()
    return [r for r in rows
            if (context == 'all' or str(r['context_index']) == context)
            and (family == 'all' or r.get('input_family') == family)
            and (not term or term in ' '.join(str(r.get(k, '')) for k in ('command', 'output', 'input_family', 'change')).casefold())]


def export_new_file(path, content: str, extension: str):
    """Exclusive create, even if a file appears after the save dialog closes."""
    selected = Path(path)
    if extension not in ('.json', '.csv') or selected.suffix.casefold() != extension:
        raise api.InspectError('EXPORT_TYPE_INVALID', 'Export to a new JSON or CSV file only.')
    if not isinstance(content, str):
        raise api.InspectError('EXPORT_TYPE_INVALID', 'Expected text export data.')
    with selected.open('x', encoding='utf-8', newline='') as stream:
        stream.write(content)


class InspectPanel:
    def __init__(self, parent, status=None):
        self.parent = parent
        self.status = status.set if hasattr(status, 'set') else status or (lambda text: None)
        self.current = None
        self.comparison = None
        self.diff = None
        self.paths = {}
        self.busy = False
        self.closed = False
        self.generation = 0
        self.timer = None
        self.results = queue.Queue()
        self.feedback = tk.StringVar(parent, value='Select a Steam profile.bin snapshot. Inspection does not change the game.')
        self.source_text = tk.StringVar(parent, value='No snapshot selected.')
        self.term = tk.StringVar(parent)
        self.details_visible = tk.BooleanVar(parent, value=False)
        self.details_text = tk.StringVar(parent)
        self.count_text = tk.StringVar(parent, value='No binding rows loaded.')
        self.scroll = ScrollableFrame(parent, min_width=0)
        self.scroll.pack(fill='both', expand=True)
        body = self.scroll.body
        ttk.Label(body, text='DOOM binding files', font=('Segoe UI', 18, 'bold')).pack(anchor='w')
        self.scope = ttk.Label(body, text='Read saved bindings, compare snapshots and export a reference.', wraplength=720)
        self.scope.pack(anchor='w', pady=(4, 6))
        self.blocked = ttk.Label(body, text='Game-file changes unavailable: internal checksum and changed-file acceptance remain unverified.', wraplength=720)
        self.blocked.pack(anchor='w', pady=(0, 6))
        bar = FlowToolbar(body)
        bar.pack(fill='x')
        self.open_button = bar.add('Open snapshot…', lambda: self.choose_snapshot('current'))
        self.compare_button = bar.add('Compare snapshot…', lambda: self.choose_snapshot('comparison'))
        self.export_button = ttk.Menubutton(bar, text='Export ▾', takefocus=True)
        self.export_menu = tk.Menu(self.export_button, tearoff=False, postcommand=self.update_export_menu)
        self.export_button.configure(menu=self.export_menu)
        bar.buttons.append(self.export_button)
        self.export_button.grid(row=0, column=2, sticky='w', padx=(0, 8), pady=3)
        self.source = ttk.Label(body, textvariable=self.source_text, wraplength=720)
        self.source.pack(fill='x', pady=(2, 6))
        filters = ResponsiveGrid(body, max_columns=4, min_cell=165)
        filters.pack(fill='x')
        def field(label):
            cell = ttk.Frame(filters)
            ttk.Label(cell, text=label).pack(anchor='w')
            filters.add(cell)
            return cell
        self.search_entry = ttk.Entry(field('Find action or key'), textvariable=self.term, width=28)
        self.search_entry.pack(anchor='w', fill='x')
        self.context = Selector(field('Native context'), choices=[('all', 'All contexts')], width=20, on_select=lambda _: self.render())
        self.context.pack(anchor='w', fill='x')
        self.context.select('all')
        self.family = Selector(field('Input'), choices=[('all', 'All inputs'), ('keyboard', 'Keyboard'), ('mouse', 'Mouse'), ('controller', 'Controller')],
                               width=20, on_select=lambda _: self.render())
        self.family.pack(anchor='w', fill='x')
        self.family.select('all')
        self.view = Selector(field('Show'), choices=[('current', 'Snapshot'), ('diff', 'Added / removed')], width=20, on_select=lambda _: self.render())
        self.view.pack(anchor='w', fill='x')
        self.view.select('current')
        self.term.trace_add('write', lambda *_: self.render())
        self.search_entry.bind('<Escape>', lambda _: self.term.set(''))
        table_frame = ttk.Frame(body)
        table_frame.pack(fill='both', expand=True, pady=6)
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(table_frame, columns=('context', 'command', 'output', 'family', 'change'), show='headings', height=12)
        for column, heading, width in [('context', 'Context', 75), ('command', 'Action command', 330), ('output', 'Key / input', 120),
                                       ('family', 'Input family', 110), ('change', 'Change', 95)]:
            self.table.heading(column, text=heading)
            self.table.column(column, width=width, minwidth=60, stretch=True)
        vertical = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        horizontal = ttk.Scrollbar(table_frame, orient='horizontal', command=self.table.xview)
        self.table.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.table.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        ttk.Label(table_frame, textvariable=self.count_text).grid(row=2, column=0, sticky='w', pady=2)
        self.table_layout = TableLayout(self.table)
        self.notice = ttk.Label(body, textvariable=self.feedback, wraplength=720)
        self.notice.pack(fill='x', pady=5)
        ttk.Checkbutton(body, text='Show source evidence and limits', variable=self.details_visible, command=self.toggle_details).pack(anchor='w')
        self.details = ttk.Label(body, textvariable=self.details_text, wraplength=720)
        self.footer = ttk.Label(body, text='Native context indexes and command IDs are retained. Action meanings, Xbox/reWASD button names and gameplay behavior are not inferred.', wraplength=720)
        self.footer.pack(fill='x', pady=6)
        ttk.Button(body, text='Close', command=self.request_close).pack(anchor='w', pady=4)
        for label in (self.scope, self.blocked, self.source, self.notice, self.details, self.footer):
            label.game_tools_wrap_managed = True
        body.bind('<Configure>', self.resize, add='+')
        self.scroll.bind('<Destroy>', self.destroyed, add='+')
        self.set_busy(False)
        self.timer = parent.after(80, self.drain)

    def resize(self, event):
        for label in (self.scope, self.blocked, self.source, self.notice, self.details, self.footer):
            label.configure(wraplength=max(180, event.width - 24))

    def report(self, text):
        self.feedback.set(str(text))
        self.status(str(text))

    def set_busy(self, value):
        self.busy = value
        self.open_button.configure(state='disabled' if value else 'normal')
        self.compare_button.configure(state='disabled' if value or self.current is None else 'normal')
        self.export_button.configure(state='disabled' if value or self.current is None else 'normal')

    def task(self, kind, function):
        if self.busy or self.closed:
            return
        self.set_busy(True)
        generation = self.generation
        self.report('Reading selected snapshot…' if kind != 'export' else 'Writing the selected new export…')
        def run():
            try:
                result, error = function(), None
            except Exception as exc:
                result, error = None, (getattr(exc, 'code', type(exc).__name__), str(exc))
            self.results.put((generation, kind, result, error))
        threading.Thread(target=run, daemon=True).start()

    def choose_snapshot(self, kind):
        if self.busy or self.closed:
            return
        path = filedialog.askopenfilename(parent=self.parent, title='Select an existing Steam profile.bin snapshot', filetypes=[('DOOM profile', 'profile.bin'), ('All files', '*')])
        if not path:
            return
        identity = derive_owner_from_path(path)
        derived = identity is not None
        if identity is None:
            identity = simpledialog.askstring('Owning Steam account', 'Owning SteamID64 for this selected snapshot. An archive path does not prove its account.', parent=self.parent)
            if identity is None:
                return
            identity = identity.strip()
        self.load_snapshot(path, identity, kind=kind, owner_derived=derived)

    def load_snapshot(self, path, identity, *, kind='current', owner_derived=False):
        """Explicit programmatic entry for the host/isolated synthetic fixtures."""
        if kind not in ('current', 'comparison') or (kind == 'comparison' and self.current is None):
            self.report('Open the first snapshot before selecting a comparison.')
            return
        baseline = self.current
        def read():
            evidence = read_selected_snapshot(path, identity)
            difference = api.diff_evidence(baseline, evidence) if kind == 'comparison' else None
            return {'path': str(path), 'evidence': evidence, 'difference': difference, 'owner_derived': owner_derived}
        self.task(kind, read)

    def drain(self):
        self.timer = None
        if self.closed:
            return
        while not self.results.empty():
            generation, kind, result, error = self.results.get_nowait()
            if generation != self.generation:
                continue
            self.set_busy(False)
            if error:
                code, message = error
                self.report(('Existing file preserved. Choose a new export name.' if code == 'FileExistsError' else code + ': ' + message))
            elif kind == 'export':
                self.report('Export created: ' + result)
            else:
                if kind == 'current':
                    self.current = result['evidence']
                    self.comparison = self.diff = None
                    self.paths = {'current': result['path']}
                    self.view.select('current')
                else:
                    self.comparison, self.diff = result['evidence'], result['difference']
                    self.paths['comparison'] = result['path']
                    self.view.select('diff')
                self.refresh_sources()
                self.set_busy(False)
                self.render()
                self.report('Authenticated saved binding snapshot read. Internal checksum and gameplay remain unverified.')
        self.timer = self.parent.after(80, self.drain)

    def refresh_sources(self):
        source = self.current['source']
        lines = ['Snapshot: ' + self.paths['current'] + '  ·  SHA-256 ' + source['sha256'][:12]]
        if self.comparison:
            lines.append('Comparison: ' + self.paths['comparison'] + '  ·  SHA-256 ' + self.comparison['source']['sha256'][:12])
        self.source_text.set('\n'.join(lines))
        selected = self.context.selected_id
        self.context.set_choices([('all', 'All contexts')] + [(str(i), 'Context ' + str(i) + ' · ' + str(n) + ' rows') for i, n in enumerate(self.current['context_counts'])])
        self.context.select(selected if selected in self.context.records else 'all')
        info = {'source': source, 'binding_count': self.current['binding_count'], 'capabilities': self.current['capabilities'],
                'verification': self.current['verification']}
        if self.diff:
            info['comparison'] = {k: v for k, v in self.diff.items() if k not in ('removed', 'added')}
        self.details_text.set(json.dumps(info, indent=2))

    def rows(self):
        if self.current is None:
            return []
        if self.view.selected_id != 'diff':
            return [dict(r, change='Snapshot') for r in self.current['bindings']]
        if self.diff is None:
            return []
        result = []
        for kind in ('added', 'removed'):
            for row in self.diff[kind]:
                output = row['output']
                family = 'controller' if output.startswith('JOY') else ('mouse' if output.startswith(('MOUSE', 'MWHEEL')) else 'keyboard')
                result.append(dict(row, input_family=family, change=kind.capitalize()))
        return result

    def render(self):
        if self.closed:
            return
        original = self.rows()
        rows = filtered_rows(original, self.term.get(), self.context.selected_id or 'all', self.family.selected_id or 'all')
        self.count_text.set(str(len(rows)) + ' of ' + str(len(original)) + ' rows shown')
        self.table.delete(*self.table.get_children())
        for row in rows:
            self.table.insert('', 'end', values=(row['context_index'], row['command'], row['output'], row['input_family'], row['change']))

    def toggle_details(self):
        if self.details_visible.get():
            self.details.pack(fill='x', before=self.footer, pady=5)
        else:
            self.details.pack_forget()

    def update_export_menu(self):
        self.export_menu.delete(0, 'end')
        self.export_menu.add_command(label='Snapshot JSON…', command=lambda: self.export('json'))
        self.export_menu.add_command(label='Snapshot CSV…', command=lambda: self.export('csv'))
        self.export_menu.add_command(label='Comparison JSON…', command=lambda: self.export('diff'), state='normal' if self.diff else 'disabled')

    def export(self, kind):
        if self.busy or self.current is None:
            return
        if kind not in ('json', 'csv', 'diff'):
            self.report('Choose a JSON or CSV reference export.')
            return
        extension = '.csv' if kind == 'csv' else '.json'
        if kind == 'diff' and self.diff is None:
            return
        path = filedialog.asksaveasfilename(parent=self.parent, title='Create a new binding reference export', defaultextension=extension,
                                          filetypes=[(extension[1:].upper(), '*' + extension)], confirmoverwrite=False)
        if not path:
            return
        def write():
            content = api.export_csv(self.current) if kind == 'csv' else (json.dumps(self.diff, indent=2) + '\n' if kind == 'diff' else api.export_json(self.current))
            export_new_file(path, content, extension)
            return str(path)
        self.task('export', write)

    def destroyed(self, event):
        if event.widget is self.scroll:
            self.close()

    def request_close(self):
        self.close()
        top = self.parent.winfo_toplevel()
        if isinstance(top, tk.Toplevel):
            top.destroy()
        else:
            self.scroll.destroy()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.generation += 1
        if self.timer:
            self.parent.after_cancel(self.timer)
            self.timer = None
        self.table_layout.close()
        self.scroll.close()
