"""Opt-in extension of the existing Hub approval controller; no second mailbox.

Rebased onto the 0.24.0-preview.1 host source and composed for the 0.25.0-preview.2 reviewed merge and retained by the 0.26.0-preview.1 additive host. Construction is inert. The existing
local UI can call inherited approve_local/reject_local. AI can only propose;
it cannot register targets, approve, run arbitrary code or supply filesystem paths.
No live Hub file is patched by importing this module.
"""
from __future__ import annotations
VERSION = "0.2.0-preview.1"
from pathlib import Path
from GameToolAutomation import AutomationService, capabilities as host_capabilities
from game_keybind_ops.core import Service
from game_keybind_ops.deps import require,object_hash,slug
import re
import json

OPERATIONS=('keybinds.prepare','keybinds.apply','keybinds.prepare_rollback','keybinds.draft_pack','keybinds.edit_draft')

class KeybindAutomationMixin:
    def __init__(self,data_dir,*args,keybind_service=None,**kwargs):
        super().__init__(data_dir,*args,**kwargs)
        self.keybinds=keybind_service or Service(Path(data_dir))
    def _normalize(self,operation,arguments):
        if operation not in OPERATIONS:return super()._normalize(operation,arguments)
        require(type(arguments) is dict,'INVALID_ARGUMENTS','Arguments must be a typed object.')
        require(len(json.dumps(arguments,indent=2,ensure_ascii=True).encode('utf-8'))<=12000,
                'REQUEST_BUDGET','Split large binding requests by game; this request exceeds the existing mailbox byte budget.')
        if operation=='keybinds.draft_pack':
            require(set(arguments)=={'pack'},'INVALID_ARGUMENTS','Draft pack only; no paths, approval or code.')
            from game_keybind_ops.packs import validate_pack
            validate_pack(arguments['pack'])
            return dict(arguments)
        if operation=='keybinds.edit_draft':
            require(set(arguments)=={'draft_id','draft_sha256','edits'},'INVALID_ARGUMENTS','Use a draft ID, exact base hash and bounded data edits.')
            slug(arguments['draft_id']);require(type(arguments['draft_sha256']) is str and re.fullmatch('[a-f0-9]{64}',arguments['draft_sha256']),'INVALID_ARGUMENTS','Invalid draft hash.')
            require(type(arguments['edits']) is list and 0<len(arguments['edits'])<=64,'INVALID_ARGUMENTS','Use bounded draft edits.')
            return dict(arguments)
        allowed={'keybinds.prepare':{'items','preview_sha256'},
                 'keybinds.apply':{'plan_id','plan_sha256'},
                 'keybinds.prepare_rollback':{'plan_id','preview_sha256','selective'}}[operation]
        require(set(arguments)==allowed,'INVALID_ARGUMENTS','Missing or unexpected keybind fields. No approved/path/code flags exist.')
        # Syntax-only normalization: completed request receipts remain readable after files change.
        if operation=='keybinds.prepare':
            require(type(arguments['items']) is list and 0<len(arguments['items'])<=16,'INVALID_ARGUMENTS','Expected 1–16 target edits.')
            for item in arguments['items']:
                require(type(item) is dict and set(item)=={'target_id','target_revision','changes'},'INVALID_ARGUMENTS','Invalid edit fields.')
                slug(item['target_id'])
                require(type(item['target_revision']) is str and re.fullmatch('[a-f0-9]{64}',item['target_revision']),
                        'INVALID_ARGUMENTS','Invalid target revision.')
                require(type(item['changes']) is dict and 0<len(item['changes'])<=512,'INVALID_ARGUMENTS','Invalid changes.')
        else: slug(arguments['plan_id'])
        hash_name='plan_sha256' if operation=='keybinds.apply' else 'preview_sha256'
        require(type(arguments[hash_name]) is str and re.fullmatch('[a-f0-9]{64}',arguments[hash_name]),'INVALID_ARGUMENTS','Invalid digest.')
        if operation=='keybinds.prepare_rollback':
            require(type(arguments['selective']) is bool,'INVALID_ARGUMENTS','selective must be explicit boolean.')
        return dict(arguments)
    def _check_current(self,req):
        if req['operation'] not in OPERATIONS:return super()._check_current(req)
        self._fresh_recipe()
        require(req['recipe_sha256']==self.recipe_hash,'SOURCE_CHANGED','Host recipe revision changed.')
        self._normalize(req['operation'],req['arguments'])
        self._check_game_scope(req)
        if req['operation']=='keybinds.edit_draft':
            from game_keybind_ops.authoring import draft_edit_preview
            a=req['arguments'];draft_edit_preview(self.keybinds,a['draft_id'],a['draft_sha256'],a['edits'])
        if req['operation']=='keybinds.prepare':
            a=req['arguments'];preview=self.keybinds.preview(a['items'])
            require(preview['preview_sha256']==a['preview_sha256'],'PREVIEW_STALE','Reload the binding preview.')
        elif req['operation']=='keybinds.prepare_rollback':
            a=req['arguments']
            preview=self.keybinds.rollback_preview(a['plan_id'],selective=True) if a['selective'] else self.keybinds.exact_rollback_preview(a['plan_id'])
            require(preview['preview_sha256']==a['preview_sha256'],'PREVIEW_STALE','Reload the undo preview.')
        if req['operation']=='keybinds.apply':
            p=self.keybinds.plan(req['arguments']['plan_id'])
            require(p['plan_sha256']==req['arguments']['plan_sha256'],'PLAN_CHANGED','Review the exact staged plan.')
            self.keybinds.reconcile(p['plan_id']);self.keybinds._preflight(p)
    def _execute(self,req):
        op=req['operation'];a=req['arguments']
        if op not in OPERATIONS:return super()._execute(req)
        require(self._active==req['request_id'],'LOCAL_APPROVAL_REQUIRED','No keybind execution outside the local approval controller.')
        require(not self.cancel.is_set(),'CANCELLED','Cancelled before keybind dispatch.')
        if op=='keybinds.draft_pack':
            from game_keybind_ops.authoring import save_draft
            result=save_draft(self.keybinds,a['pack'],'draft-'+object_hash(req['request_id'])[:32])
        elif op=='keybinds.edit_draft':
            from game_keybind_ops.authoring import edit_draft_local
            result=edit_draft_local(self.keybinds,a['draft_id'],a['draft_sha256'],a['edits'],'draft-'+object_hash(req['request_id'])[:32])
        elif op=='keybinds.prepare':
            result=self.keybinds.prepare(a['items'],a['preview_sha256'],plan_id='kb-'+object_hash(req['request_id'])[:32])
        elif op=='keybinds.prepare_rollback':
            result=self.keybinds.prepare_rollback(a['plan_id'],a['preview_sha256'],selective=a['selective'],plan_id='undo-'+object_hash(req['request_id'])[:32])
        else:
            # Only the existing LOCAL approve_local controller sets _active and enters _execute.
            require(self._active==req['request_id'],'LOCAL_APPROVAL_REQUIRED','No keybind execution outside the local approval controller.')
            result=self.keybinds.apply_local(a['plan_id'],a['plan_sha256'],
                     authorize=lambda _:self._active==req['request_id'],cancel=self.cancel)
            require(result['status']=='APPLIED_FILES_RUNTIME_UNVERIFIED','STOPPED_RECONCILE','Inspect the existing keybind plan after a partial/failed operation.')
        return result
    def _check_game_scope(self,req):
        game=getattr(self,'game_id',None)
        if not game:return
        op=req['operation'];a=req['arguments']
        if op=='keybinds.draft_pack':
            require(a['pack']['game_id']==game,'GAME_MISMATCH','Draft belongs to another game.');return
        if op=='keybinds.edit_draft':
            from game_keybind_ops.authoring import draft_context
            require(draft_context(self.keybinds,a['draft_id'])['game_id']==game,'GAME_MISMATCH','Another game owns this draft.');return
        items=a['items'] if op=='keybinds.prepare' else self.keybinds.plan(a['plan_id'])['items']
        require(all(self.keybinds.target(i['target_id'])['spec']['game_id']==game for i in items),'GAME_MISMATCH','A game workspace cannot change another game.')
    def propose(self,operation,arguments,*,request_id=None):
        if operation in OPERATIONS:
            # Use the same approval implementation, with this mixin's scoped validation.
            return AutomationService.propose(self,operation,arguments,request_id=request_id)
        return super().propose(operation,arguments,request_id=request_id)
    def keybind_context(self,known_revision=None):return self.keybinds.context(known_revision)

class KeybindAutomationService(KeybindAutomationMixin,AutomationService):
    pass


def capabilities():
    c=host_capabilities();c['requestable']=list(c['requestable'])+list(OPERATIONS)
    c['keybinds']={'discovery':'local_operator_only','native_formats':[r['id'] for r in __import__('game_keybind_ops.adapter_registry',fromlist=['capabilities']).capabilities()],
                  'extension_contract':'data-only game packs plus explicitly trusted adapter SDK v1',
                  'registration':'local_review_only','replacement':'exact_plan_local_approval_only',
                  'rollback':'prepare_inverse_then_separately_approve','gameplay_verified':False,
                  'host_activation':'opt_in_source_integration_not_deployed'}
    return c
