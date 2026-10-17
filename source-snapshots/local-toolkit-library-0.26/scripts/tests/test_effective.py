"""Whole-game scalar precedence, context collisions and crash/staleness guards."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).absolute().parents[1]))
from test_extensibility import Base
from game_keybind_ops.packs import *
from game_keybind_ops.effective import *
from game_keybind_ops.core import sha
from game_keybind_ops.documents import Document
from game_keybind_ops.deps import Error

class GraphBase(Base):
    def create(self,definitions=None,contexts=None,ident='installation'):
        definitions=definitions or [('first',{'use':'E'},True,100),('second',{'reload':'R'},True,100)]
        folder=self.root/('pack-'+ident);folder.mkdir();game=self.root/('native-'+ident);game.mkdir();files=[];bs={};hs={};paths={}
        for fid,native,writable,rank in definitions:
            name=fid+'.json';raw=json.dumps({'bindings':native,'volume':75}).encode();path=game/name;path.write_bytes(raw);paths[fid]=path
            f={'id':fid,'adapter':'json','locations':[{'root':'GAME_CONFIG','pattern':name}],
               'fields':[{'id':k,'action':k,'contexts':contexts or ['gameplay'],'slot':'primary','selector':{'pointer':'/bindings/'+k},'keymap':'keys','modifier_match':'exact'} for k in native],
               'inventory_complete':True,'stopped_processes':['SyntheticAbsent.exe'],'writable':writable,'priority':rank,'fingerprints':[]}
            files.append(f);bs[fid]={'root':str(game),'relative':name};hs[fid]=sha(raw)
        p={'schema_version':1,'kind':'game-keybind-pack','id':ident,'game_id':'fictional','title':'Synthetic multi-file game','version':'1.0.0',
           'keymaps':{'keys':{k:k for k in ('E','R','F','Q','V','G','Space','LCtrl','RCtrl','Ctrl','Ctrl+F','LCtrl+F','MouseLeft','MouseRight','WheelUp','MouseMiddle','Inherit')}},
           'files':files,'variants':[{'id':'keyboard','files':[f['id'] for f in files]}],'presets':[],
           'evidence':{'stage':'source-reviewed','notes':'Synthetic fixtures only; never a native game acceptance claim.','sources':[]},'fixtures':[],'exclusive_contexts':[]}
        self.write_pack(folder,p);pin=self.import_(folder)
        state=bind_instance_local(self.s,pin,ident,'keyboard',bs,hs,authorize=lambda _:True,evidence='Synthetic whole-instance review')
        return state,paths,pin,folder,p,bs,hs
    def change(self,action,key,ctx='gameplay'):return {'action':action,'context':ctx,'key':key}
    def view_changes(self,changes,ident='installation'):
        state=inspect_instance(self.s,ident);return intent_preview(self.s,ident,changes,state['revision'])

class Ownership(GraphBase):
    def test_cross_file_collision(self):
        self.create();self.failcode('CROSS_FILE_COLLISION',lambda:self.view_changes([self.change('use','R')]))
    def test_complete_crossfile_swap_and_undo(self):
        st,paths,*_=self.create();old={k:v.read_bytes() for k,v in paths.items()};p=self.apply(self.view_changes([self.change('use','R'),self.change('reload','E')]))
        self.assertEqual(json.loads(paths['first'].read_bytes())['bindings']['use'],'R')
        inv=self.s.exact_rollback_preview(p['plan_id']);up=self.s.prepare_rollback(p['plan_id'],inv['preview_sha256']);self.s.apply_local(up['plan_id'],up['plan_sha256'],authorize=lambda _:True)
        self.assertEqual({k:v.read_bytes() for k,v in paths.items()},old)
    def test_dependency_change_blocks_before_write(self):
        st,paths,*_=self.create();view=self.view_changes([self.change('use','F')]);p=self.s.prepare(view['items_request'],view['preview_sha256']);before=paths['first'].read_bytes();paths['second'].write_bytes(paths['second'].read_bytes().replace(b'75',b'80'))
        self.failcode('DEPENDENCY_CHANGED',lambda:self.s.apply_local(p['plan_id'],p['plan_sha256'],authorize=lambda _:True));self.assertEqual(paths['first'].read_bytes(),before)
    def test_dependent_writer_blocks(self):
        self.create();view=self.view_changes([self.change('use','F')]);p=self.s.prepare(view['items_request'],view['preview_sha256']);self.s.process_reader=lambda:{'syntheticabsent.exe'}
        self.failcode('PROCESS_RUNNING',lambda:self.s.apply_local(p['plan_id'],p['plan_sha256'],authorize=lambda _:True))
    def test_related_drift_changes_semantic_revision(self):
        st,paths,*_=self.create();paths['second'].write_bytes(paths['second'].read_bytes().replace(b'75',b'80'))
        self.failcode('INSTANCE_STALE',lambda:intent_preview(self.s,'installation',[self.change('use','F')],st['revision']))
    def test_read_only_owner_remains_unresolved(self):
        self.create([('defaults',{'use':'E'},False,100)]);v=self.view_changes([self.change('use','F')]);self.assertEqual(v['status'],'UNRESOLVED_ACTIONS');self.assertEqual(v['unresolved'][0]['status'],'READ_ONLY_OWNER')
    def test_ambiguous_precedence(self):
        self.failcode('OWNER_AMBIGUOUS',lambda:self.create([('one',{'use':'E'},True,100),('two',{'use':'R'},True,100)]))
    def test_edit_shadowed_source_blocked(self):
        self.create([('defaults',{'use':'E'},True,100),('user',{'use':'R'},True,200)])
        t=self.s.target('installation-defaults');items=[{'target_id':t['spec']['target_id'],'target_revision':t['spec_sha256'],'changes':{'use':'F'}}]
        self.failcode('SHADOWED_CHANGE',lambda:self.s.preview(items))
    def test_effective_owner_selected_not_lower_file(self):
        self.create([('defaults',{'use':'E'},True,100),('user',{'use':'R'},True,200)])
        v=self.view_changes([self.change('use','F')]);self.assertEqual(v['items_request'][0]['target_id'],'installation-user')
    def test_unknown_action_never_fuzzy_matches(self):
        self.create();v=self.view_changes([self.change('uss','F')]);self.assertEqual(v['status'],'UNRESOLVED_ACTIONS');self.assertFalse(v['items_request'])
    def test_partial_intent_default_is_no_changes(self):
        self.create();v=self.view_changes([self.change('use','F'),self.change('unknown','Q')]);self.assertEqual(v['status'],'UNRESOLVED_ACTIONS');self.assertFalse(v['items_request'])
    def test_shared_scalar_requires_all_contexts(self):
        self.create([('input',{'use':'E'},True,100)],contexts=['gameplay','menu']);self.failcode('LINKED_CONTEXTS',lambda:self.view_changes([self.change('use','F')]))
    def test_shared_scalar_same_key_all_contexts(self):
        self.create([('input',{'use':'E'},True,100)],contexts=['gameplay','menu']);v=self.view_changes([self.change('use','F'),self.change('use','F','menu')]);self.assertEqual(len(v['items_request']),1)
    def test_shared_scalar_conflicting_contexts(self):
        self.create([('input',{'use':'E'},True,100)],contexts=['gameplay','menu']);self.failcode('LINKED_CONTEXTS',lambda:self.view_changes([self.change('use','F'),self.change('use','Q','menu')]))
    def test_crossfile_guard_cannot_be_omitted(self):
        self.create();v=self.view_changes([self.change('use','F')]);p=self.s.prepare(v['items_request'],v['preview_sha256']);p['items'][0].pop('scope_guard');self.failcode('GUARD_REQUIRED',lambda:self.s._preflight(p))
    def test_paginated_context_and_delta(self):
        self.create();a=inspect_instance(self.s,'installation',limit=1);b=inspect_instance(self.s,'installation',offset=1,limit=1)
        self.assertEqual(a['revision'],b['revision']);self.assertEqual(a['next_offset'],1);self.assertNotEqual(a['effective_bindings'],b['effective_bindings']);self.assertTrue(inspect_instance(self.s,'installation',a['revision'])['unchanged'])
    def test_selective_undo_keeps_later_graphics(self):
        _,paths,*_=self.create();p=self.apply(self.view_changes([self.change('use','F')]))
        paths['first'].write_bytes(paths['first'].read_bytes().replace(b'75',b'90'))
        u=self.s.rollback_preview(p['plan_id'],selective=True);undo=self.s.prepare_rollback(p['plan_id'],u['preview_sha256'],selective=True);self.s.apply_local(undo['plan_id'],undo['plan_sha256'],authorize=lambda _:True)
        self.assertEqual(json.loads(paths['first'].read_bytes()),{'bindings':{'use':'E'},'volume':90})
    def test_contexts_are_not_implicitly_exclusive(self):
        a={'action':'use','slot':'primary','context':'gameplay','key':'F','modifier_match':'exact'};b={**a,'action':'menu','context':'menu'}
        self.assertTrue(conflict_set([a,b],[]));self.assertFalse(conflict_set([a,b],[['gameplay','menu']]))
    def test_generic_modifier_overlap(self):
        a={'key':'Ctrl+F','modifier_match':'exact'};self.assertTrue(key_overlap(a,{'key':'LCtrl+F','modifier_match':'exact'}));self.assertFalse(key_overlap({'key':'LCtrl+F','modifier_match':'exact'},{'key':'RCtrl+F','modifier_match':'exact'}))
    def test_subset_modifier_overlap(self):
        self.assertTrue(key_overlap({'key':'F','modifier_match':'subset'},{'key':'Ctrl+F','modifier_match':'exact'}));self.assertFalse(key_overlap({'key':'F','modifier_match':'exact'},{'key':'Ctrl+F','modifier_match':'exact'}))
    def test_applied_files_not_replayed(self):
        self.create();p=self.apply(self.view_changes([self.change('use','F')]))
        with patch.object(self.s,'replacer',side_effect=AssertionError('Must not write twice')):
            r=self.s.apply_local(p['plan_id'],p['plan_sha256'],authorize=lambda _:True)
        self.assertEqual(r['status'],'APPLIED_FILES_RUNTIME_UNVERIFIED')
    def test_registration_reentry_same_native_context(self):
        st,paths,pin,folder,p,bs,hs=self.create();again=bind_instance_local(self.s,pin,'installation','keyboard',bs,hs,authorize=lambda _:True,evidence='Synthetic whole-instance review')
        self.assertEqual(again['revision'],st['revision']);self.assertEqual(registration_status(self.s,'installation')['status'],'REGISTERED')


class MoreGuards(GraphBase):
    def test_scoped_process_state_unknown_stops(self):
        self.create();v=self.view_changes([self.change('use','F')]);p=self.s.prepare(v['items_request'],v['preview_sha256']);self.s.process_reader=lambda:None
        self.failcode('PROCESS_STATE_UNKNOWN',lambda:self.s.apply_local(p['plan_id'],p['plan_sha256'],authorize=lambda _:True))
    def test_registration_interruption_is_inspectable_and_same_request_can_finish(self):
        folder=self.sample();pin=self.import_(folder);pack=load_pin(self.s,pin);game=self.root/'native';game.mkdir();path=game/'input.json';data=(folder/pack['fixtures'][0]['before']).read_bytes();path.write_bytes(data)
        bindings={'input':{'root':str(game),'relative':path.name}};hashes={'input':sha(data)};kwargs={'authorize':lambda _:True,'evidence':'Exact synthetic intake'}
        original=self.s.register_local
        def stopped(spec):
            original(spec);raise RuntimeError('Interrupted after metadata registration, before instance completion')
        with patch.object(self.s,'register_local',side_effect=stopped),self.assertRaises(RuntimeError):bind_instance_local(self.s,pin,'partial','keyboard',bindings,hashes,**kwargs)
        self.assertEqual(registration_status(self.s,'partial')['status'],'REGISTRATION_INCOMPLETE');self.assertEqual(path.read_bytes(),data)
        # An explicit fresh local review of the IDENTICAL request, never automatic retry.
        bind_instance_local(self.s,pin,'partial','keyboard',bindings,hashes,**kwargs);self.assertEqual(registration_status(self.s,'partial')['status'],'REGISTERED');self.assertEqual(path.read_bytes(),data)
    def test_unrecognized_registration_lock_cannot_retire(self):
        from game_keybind_ops.recovery import inspect_lock
        self.s.root.mkdir(parents=True);(self.s.root/'.keybind-registration.lock').write_text('{"owner":"unknown"}')
        self.failcode('LOCK_UNRECOGNIZED',lambda:inspect_lock(self.s,lambda _: 'DEAD','registration'))
    def test_known_dead_registration_lock_archive_no_game_effect(self):
        from game_keybind_ops.recovery import inspect_lock,retire_lock_local
        self.s.root.mkdir(parents=True);p=self.s.root/'.keybind-registration.lock';raw=b'{"pid":123456,"created_unix":1,"kind":"cooperative-only"}';p.write_bytes(raw)
        r=inspect_lock(self.s,lambda _: 'DEAD','registration');self.assertTrue(r['retirement_available'])
        out=retire_lock_local(self.s,r['inspection_sha256'],authorize=lambda _:True,pid_reader=lambda _: 'DEAD',lock_kind='registration');self.assertFalse(out['game_files_modified']);self.assertFalse(p.exists());self.assertEqual(next((self.s.root/'retired-locks').glob('*/original-lock.json')).read_bytes(),raw)
    def test_named_preset_uses_current_instance(self):
        folder=self.sample();st,_,_=self.binding(folder);v=preset_preview(self.s,'installation','use-f',st['revision']);self.assertEqual(v['preset_id'],'use-f');self.assertTrue(v['items_request'])
    def test_named_preset_unknown_variant_refused(self):
        folder=self.sample();st,_,_=self.binding(folder);self.failcode('PRESET_UNKNOWN',lambda:preset_preview(self.s,'installation','missing',st['revision']))

class Sparse(GraphBase):
    def sparse_setup(self):
        folder=self.root/'sparse';folder.mkdir();game=self.root/'sparse-native';game.mkdir()
        defaults=b'{"use":"E","reload":"R"}';override=b'[Keys]\nReload = R\n';(game/'defaults.json').write_bytes(defaults);(game/'input.ini').write_bytes(override)
        keys={'E':'E','F':'F','R':'R','G':'G','MouseLeft':'MouseLeft','Inherit':'__GT_INHERIT__'}
        df={'id':'defaults','adapter':'json','locations':[{'root':'GAME_CONFIG','pattern':'defaults.json'}],
            'fields':[{'id':k,'action':k,'selector':{'pointer':'/'+k},'keymap':'keys','contexts':['gameplay']} for k in ('use','reload')],
            'inventory_complete':True,'stopped_processes':['Synthetic.exe'],'writable':False,'priority':100,'fingerprints':[]}
        uf={'id':'user','adapter':'ini-sparse','locations':[{'root':'GAME_CONFIG','pattern':'input.ini'}],
            'fields':[{'id':k.lower(),'action':k.lower(),'selector':{'section':'Keys','key':k,'occurrence':0,'part':'value','optional':True},'keymap':'keys','contexts':['gameplay'],'fallback_key':v} for k,v in [('Use','E'),('Reload','R')]],
            'inventory_complete':True,'stopped_processes':['Synthetic.exe'],'writable':True,'priority':200,'fingerprints':[]}
        p={'schema_version':1,'kind':'game-keybind-pack','id':'sparse','game_id':'fictional','title':'Sparse fixture','version':'1.0.0','keymaps':{'keys':keys},'files':[df,uf],
           'variants':[{'id':'keyboard','files':['defaults','user']}],'presets':[],'fixtures':[],
           'evidence':{'stage':'source-reviewed','notes':'Synthetic reviewed defaults/override precedence.','sources':[]}}
        self.write_pack(folder,p);pin=self.import_(folder);bind_instance_local(self.s,pin,'installation','keyboard',{'defaults':{'root':str(game),'relative':'defaults.json'},'user':{'root':str(game),'relative':'input.ini'}},{'defaults':sha(defaults),'user':sha(override)},authorize=lambda _:True,evidence='Synthetic instance')
        return game,defaults,override
    def test_sparse_materialized_above_read_only_defaults(self):
        game,defaults,override=self.sparse_setup();v=self.view_changes([self.change('use','F')]);self.assertEqual(v['items_request'][0]['target_id'],'installation-user');self.apply(v);self.assertEqual((game/'defaults.json').read_bytes(),defaults);self.assertIn(b'Use = F', (game/'input.ini').read_bytes())
    def test_sparse_selective_undo_removes_only_inserted_binding(self):
        game,_,original=self.sparse_setup();p=self.apply(self.view_changes([self.change('use','F')]));path=game/'input.ini';path.write_bytes(path.read_bytes()+b'; later note\n')
        u=self.s.rollback_preview(p['plan_id'],selective=True);up=self.s.prepare_rollback(p['plan_id'],u['preview_sha256'],selective=True);self.s.apply_local(up['plan_id'],up['plan_sha256'],authorize=lambda _:True)
        self.assertEqual(path.read_bytes(),original+b'; later note\n');self.assertEqual(next(r['key'] for r in inspect_instance(self.s,'installation')['effective_bindings'] if r['action']=='use'),'E')
    def test_read_only_defaults_are_guarded(self):
        game,_,_=self.sparse_setup();v=self.view_changes([self.change('use','F')]);p=self.s.prepare(v['items_request'],v['preview_sha256']);(game/'defaults.json').write_bytes(b'{"use":"G","reload":"R"}')
        self.failcode('DEPENDENCY_CHANGED',lambda:self.s.apply_local(p['plan_id'],p['plan_sha256'],authorize=lambda _:True))

if __name__=='__main__':unittest.main(verbosity=2)
