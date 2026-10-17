"""Opt-in Workbench 0.23 composition: same identities, runner and approvals.
Keybind-only games do not require fabricated mod recipes. The inherited approval
controller still pins its real bootstrap recipe as a transport dependency; it is
never offered as a mod recipe for a keybind-only scope. No live host is patched.
"""
from GameToolGameWorkspaces import GameWorkspaces,ScopedAutomation
from GameToolAutomation import AutomationService,RECIPE
from GameToolKeybindIntegration import KeybindAutomationMixin,OPERATIONS
from game_keybind_ops.core import Service
from game_keybind_ops.deps import require,slug,object_hash,Error
from game_keybind_ops.packs import list_packs
from game_keybind_ops.effective import list_instances

class KeybindScopedAutomation(KeybindAutomationMixin,ScopedAutomation):
    pass

class KeybindOnlyAutomation(KeybindAutomationMixin,AutomationService):
    keybind_only=True
    def __init__(self,data_dir,game_id,bootstrap_recipe=RECIPE,**kwargs):
        super().__init__(data_dir,bootstrap_recipe,**kwargs)
        self.game_id=slug(game_id)
        self.root=self.data_dir/'automation'/'game-scopes'/self.game_id
        self.requests=self.root/'requests'
    def propose(self,operation,arguments,*,request_id=None):
        require(operation in OPERATIONS,'CAPABILITY_UNAVAILABLE','This is a keybind-only workspace, not a mod or overlay executor.')
        return super().propose(operation,arguments,request_id=request_id)
    def preview_plan(self,*args,**kwargs):
        raise Error('MOD_RECIPE_REQUIRED','No mod recipe is registered for this game. Keybinding operations remain available.')

class KeybindGameWorkspaces(GameWorkspaces):
    def game_rows(self):
        rows={r['id']:{**r,'keybind_pack_available':False} for r in self.catalog.game_rows()}
        for p in list_packs(Service(self.data_dir)):
            if 'game_id' not in p:continue
            ident=p['game_id']
            row=rows.setdefault(ident,{'id':ident,'name':ident,'recipe_available':False,'recipe_revision':None,'manager':None,
                                      'installation':'unknown','source':'locally_imported_keybind_data_pack'})
            row['keybind_pack_available']=True
        return sorted(rows.values(),key=lambda r:r['name'].casefold())
    def service(self,game_id):
        game_id=slug(game_id);recipes=self.catalog.recipes();row=recipes.get(game_id)
        if row is None:
            require(any(r['id']==game_id and r['keybind_pack_available'] for r in self.game_rows()),'PACK_REQUIRED','Import a game definition before opening a keybind-only scope.')
        if game_id not in self._services:
            self._services[game_id]=(KeybindScopedAutomation(self.data_dir,row['path'],self.builtin_id) if row else
                                     KeybindOnlyAutomation(self.data_dir,game_id,self.catalog.builtin))
        service=self._services[game_id]
        require(bool(getattr(service,'keybind_only',False))==(row is None),'SOURCE_CHANGED','Game capabilities changed. Reconcile pending requests before recreating its controller.')
        if row:require(service.recipe_hash==row['revision'],'SOURCE_CHANGED','A workspace mod recipe changed. Reconcile its owner.')
        return service
    def approve_request(self,game_id,request_id,expected_hash,cancel):
        service=self.service(game_id);req=service._read_request(request_id)
        if req['operation'] not in OPERATIONS:return super().approve_request(game_id,request_id,expected_hash,cancel)
        service.cancel=cancel
        return service.approve_local(request_id,expected_hash)
    def request_review(self,game_id,request_id):
        service=self.service(game_id);req=service._read_request(request_id)
        if req['operation'] not in OPERATIONS:return super().request_review(game_id,request_id)
        row=service.request_status(request_id);reason=None
        try:service._check_current(req)
        except Error as e:reason=str(e)
        effects={'keybinds.prepare':'Stage immutable native copies; no game configuration changes.',
                 'keybinds.apply':'Replace ONLY the approved plan files; original bytes are retained.',
                 'keybinds.prepare_rollback':'Stage inverse copies; no game change until separate approval.',
                 'keybinds.edit_draft':'Save an immutable child draft; preserve its base, no game writes.',
                 'keybinds.draft_pack':'Save an unreviewed draft definition; no import, activation or game change.'}
        return {**row,'game_id':game_id,'game_name':game_id,'current':reason is None,'blocking_reason':reason,
                'effect':effects[req['operation']],'manual_approval_required':True,'gameplay_verified':False}
    def keybind_context(self,game_id=None,known_revision=None):
        # Separate namespace inside the same workspaces object, not a second queue.
        value={'games':self.game_rows(),'instances':list_instances(Service(self.data_dir),game_id=game_id),
               'native_game_tested':False,'mod_recipe_required_for_keybinds':False}
        revision=object_hash(value)
        return {'revision':revision,'unchanged':revision==known_revision,**({} if revision==known_revision else value)}
