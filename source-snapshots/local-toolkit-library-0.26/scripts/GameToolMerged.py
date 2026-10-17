"""Compose reviewed 0.24 game support and 0.2 keybinds under their existing owners."""
from __future__ import annotations
import json
from types import SimpleNamespace
from GameToolGameWorkspaces import RecipeCatalog
from GameToolAI import Endpoint as HostEndpoint
from GameToolKeybindIntegration import OPERATIONS, KeybindAutomationService
from GameToolKeybindWorkspaces import KeybindScopedAutomation, KeybindOnlyAutomation
from GameToolKeybindAI import Endpoint as KeybindEndpoint, extra_tools
from game_keybind_ops.core import Service
from game_keybind_ops.deps import require, slug, Error, object_hash
from game_keybind_ops.packs import list_packs
from game_keybind_ops.effective import list_instances

VERSION = '0.1.0'

class CapabilityCatalog(RecipeCatalog):
    def game_rows(self):
        rows = {r['id']: {**r, 'keybind_pack_available': False} for r in super().game_rows()}
        for pack in list_packs(Service(self.data_dir)):
            ident = pack.get('game_id')
            if not ident:
                continue
            row = rows.setdefault(ident, dict(id=ident, name=ident, recipe_available=False,
                recipe_revision=None, manager=None, installation='unknown',
                source='locally_imported_keybind_data_pack'))
            row['keybind_pack_available'] = True
        values = self.library.rows(rows.values()) if hasattr(self, 'library') else list(rows.values())
        return sorted(values, key=lambda r: (r['id'] != 'pathfinder-kingmaker', r['name'].casefold()))

def compose_workspace(owner):
    # The original GameWorkspaces owns support records, runner, history and data root.
    owner.catalog = CapabilityCatalog(owner.data_dir, owner.catalog.builtin)
    from GameToolLibrary import GameLibrary
    owner.library = GameLibrary(owner.data_dir)
    owner.catalog.library = owner.library
    owner.keybinds = Service(owner.data_dir)

def workspace_service(owner, game_id):
    game_id = slug(game_id)
    row = owner.catalog.recipes().get(game_id)
    if row is None:
        require(any(r['id'] == game_id and r.get('keybind_pack_available')
                    for r in owner.catalog.game_rows()), 'RECIPE_REQUIRED',
                'Import reviewed mod support or a keybind pack before opening this scope.')
    old = owner._services.get(game_id)
    # Preserve the 0.24 fresh-controller behavior when a reviewed recipe changes.
    if old is None or bool(getattr(old, 'keybind_only', False)) != (row is None) or (row and old.recipe_hash != row['revision']):
        old = (KeybindScopedAutomation(owner.data_dir, row['path'], owner.builtin_id,
                                      keybind_service=owner.keybinds) if row else
               KeybindOnlyAutomation(owner.data_dir, game_id, owner.catalog.builtin,
                                     keybind_service=owner.keybinds))
        owner._services[game_id] = old
    if row:
        require(old.recipe_hash == row['revision'], 'SOURCE_CHANGED', 'Game recipe changed; inspect retained requests.')
    return old

def review_keybind_request(owner, game_id, request_id):
    service = owner.service(game_id)
    req = service._read_request(request_id)
    row = service.request_status(request_id)
    reason = None
    try:
        service._check_current(req)
    except Error as exc:
        reason = str(exc)
    effects = {
        'keybinds.prepare': 'Stage immutable binding copies; no game file changes.',
        'keybinds.apply': 'Replace only exact locally approved binding files; retain originals.',
        'keybinds.prepare_rollback': 'Stage inverse copies; separate approval is required to apply.',
        'keybinds.draft_pack': 'Save an unreviewed data draft; no import or activation.',
        'keybinds.edit_draft': 'Save an immutable child draft; retain the original.'}
    return {**row, 'game_id': game_id, 'game_name': game_id, 'items': [],
            'current': reason is None, 'blocking_reason': reason,
            'effect': effects[req['operation']], 'manual_approval_required': True,
            'gameplay_verified': False, 'limit': 'Selected local binding data only'}

def keybind_context(owner, game_id=None, known_revision=None):
    value = {'games': owner.catalog.game_rows(),
             'instances': list_instances(owner.keybinds, game_id=game_id),
             'native_game_tested': False, 'mod_recipe_required_for_keybinds': False}
    revision = object_hash(value)
    return {'revision': revision, 'unchanged': revision == known_revision,
            **({} if revision == known_revision else value)}

class MergedEndpoint(HostEndpoint):
    """One bounded stdio endpoint; keybind proposals use the Workbench mailbox."""
    def definitions(self):
        values = extra_tools(self.allow_requests)
        for definition in values:
            schema = definition['inputSchema']
            schema['properties']['game_id'] = {'type': 'string'}
            if definition['name'] == 'keybinds_propose' and self.multi_game:
                schema['required'].append('game_id')
        return values

    def handle(self, message):
        valid = (type(message) is dict and message.get('jsonrpc') == '2.0'
                 and 'id' in message and type(message['id']) in (str, int)
                 and type(message.get('params', {})) is dict)
        if valid and self.ready and message.get('method') == 'tools/list':
            result = super().handle(message)
            if 'result' in result:
                result['result']['tools'] += self.definitions()
            return result
        if valid and self.ready and message.get('method') == 'tools/call':
            params = message.get('params', {})
            name = params.get('name')
            if type(name) is str and name.startswith('keybinds_'):
                try:
                    require(set(params) <= {'name', 'arguments'}, 'INVALID_ARGUMENTS', 'Unexpected call fields.')
                    definitions = {t['name']: t for t in self.definitions()}
                    require(name in definitions, 'CAPABILITY_UNAVAILABLE', 'Unknown keybind tool.')
                    args = params.get('arguments', {})
                    schema = definitions[name]['inputSchema']
                    require(type(args) is dict and set(schema['required']) <= set(args) <= set(schema['properties']),
                            'INVALID_ARGUMENTS', 'Missing or unexpected tool arguments.')
                    args = dict(args)
                    game = args.pop('game_id', None)
                    if game is not None:
                        require(self.multi_game, 'GAME_SCOPE_REQUIRED', 'Use the game-workspace endpoint.')
                        service = self.service.workspaces.service(game)
                    elif self.multi_game:
                        service = KeybindAutomationService(self.service.workspaces.data_dir,
                                    self.service.workspaces.catalog.builtin,
                                    keybind_service=self.service.workspaces.keybinds)
                    else:
                        service = self.service
                    value = KeybindEndpoint.call_keybind(SimpleNamespace(service=service, allow_requests=self.allow_requests), name, args)
                    failed = False
                except (Error, ValueError, OSError, TypeError, KeyError) as exc:
                    value = {'status': getattr(exc, 'code', 'REFUSED'),
                             'message': 'Inspect the same scope/request; no approval, execution or retry occurred.'}
                    failed = True
                return {'jsonrpc': '2.0', 'id': message['id'], 'result': {
                    'content': [{'type': 'text', 'text': json.dumps(value)}],
                    'structuredContent': value, 'isError': failed}}
        return super().handle(message)

class ScopedKeybindService:
    """Share the original service while keeping the visible game truthful."""
    def __init__(self, service, game):
        self._service, self._game = service, game
    def __getattr__(self, name):
        return getattr(self._service, name)
    def _target(self, target):
        require(self._service.target(target)['spec']['game_id'] == self._game(),
                'GAME_MISMATCH', 'This binding belongs to another selected game.')
    def _items(self, items):
        for item in items:
            self._target(item['target_id'])
    def _plan(self, ident):
        self._items(self._service.plan(ident)['items'])
    def register_local(self, spec):
        require(spec['game_id'] == self._game(), 'GAME_MISMATCH', 'Choose this game before registering its bindings.')
        return self._service.register_local(spec)
    def preview(self, items):
        self._items(items); return self._service.preview(items)
    def prepare(self, items, expected, **kwargs):
        self._items(items); return self._service.prepare(items, expected, **kwargs)
    def status(self, ident):
        self._plan(ident); return self._service.status(ident)
    def apply_local(self, ident, expected, **kwargs):
        self._plan(ident); return self._service.apply_local(ident, expected, **kwargs)
    def rollback_preview(self, ident, **kwargs):
        self._plan(ident); return self._service.rollback_preview(ident, **kwargs)
    def exact_rollback_preview(self, ident):
        self._plan(ident); return self._service.exact_rollback_preview(ident)
    def prepare_rollback(self, ident, expected, **kwargs):
        self._plan(ident); return self._service.prepare_rollback(ident, expected, **kwargs)
    def history(self):
        values = []
        for row in self._service.history():
            try:
                self._plan(row['plan_id']); values.append(row)
            except Error as exc:
                if exc.code != 'GAME_MISMATCH': raise
        return values
    def context(self, known_revision=None, target_id=None):
        if target_id is not None:
            self._target(target_id)
            value={'targets':[self._service.inspect_target(target_id)],'history':self.history()}
            revision=object_hash(value)
            return {'revision':revision,'unchanged':revision==known_revision,
                    **({} if revision==known_revision else value),'private_paths_included':False}
        from game_keybind_ops.core import MAX_TARGETS
        # Filter registration metadata before reading native binding files.
        ids = [p.stem for p in self._service._list(self._service.targets, MAX_TARGETS)
               if self._service.target(p.stem)['spec']['game_id'] == self._game()]
        values = [self._service.inspect_target(ident) for ident in ids]
        value = {'game_id': self._game(), 'targets': values,
                 'history': self.history(), 'gameplay_verified': False}
        revision = object_hash(value)
        return {'revision': revision, 'unchanged': revision == known_revision,
                **({} if revision == known_revision else value)}

def attach_keybinds(workbench):
    from game_keybind_ops.panel import Panel
    import tkinter as tk
    from tkinter import ttk
    class EmbeddedPanel(Panel):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.out.configure(height=8,width=65)
            # Keep stage/apply/undo visible before the optional report details.
            self.stage_button.master.pack_configure(before=self.out)
            workbench._text_widgets.append(self.out)
        def start(self, fn, done):
            self.operation_game = workbench.game_id
            def completed(value):
                done(value)
                workbench.refresh_games()
                workbench.refresh_activity()
            super().start(fn, completed)
            workbench.refresh_activity()
    service = ScopedKeybindService(workbench.model.keybinds, lambda: workbench.game_id)
    surface=ttk.Frame(workbench.tabs)
    surface.rowconfigure(0,weight=1);surface.columnconfigure(0,weight=1)
    canvas=tk.Canvas(surface,highlightthickness=0,borderwidth=0)
    canvas.configure(background=workbench.colors['bg'])
    canvas.grid(row=0,column=0,sticky='nsew')
    vertical=ttk.Scrollbar(surface,orient='vertical',command=canvas.yview)
    horizontal=ttk.Scrollbar(surface,orient='horizontal',command=canvas.xview)
    vertical.grid(row=0,column=1,sticky='ns');horizontal.grid(row=1,column=0,sticky='ew')
    canvas.configure(yscrollcommand=vertical.set,xscrollcommand=horizontal.set)
    panel = EmbeddedPanel(canvas, workbench.model.data_dir, service=service,
                          busy_guard=lambda: bool(workbench.model.runner.active()))
    item=canvas.create_window(0,0,window=panel,anchor='nw')
    def resize(event=None):
        width=max(960,canvas.winfo_width())
        if int(float(canvas.itemcget(item,'width') or 0)) != width:
            canvas.itemconfigure(item,width=width)
        canvas.configure(scrollregion=canvas.bbox('all'))
    canvas.bind('<Configure>',resize);panel.bind('<Configure>',resize)
    panel.game_box.configure(state='readonly')
    # The owning game selector controls this value; the local pane cannot drift.
    panel.game_box.configure(state='disabled')
    workbench.tabs.add(surface, text='Keybinds')
    workbench.keybind_page=surface
    return panel
