"""Scoped-rule propagation, bounded recommendations, research and reconciliation."""
import copy,importlib.util,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import GameToolControlsPlanner as p
import GameToolControlsRules as rules
import GameToolControlsOptimizer as optimizer
import GameToolControlsResearch as research
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder
s=importlib.util.spec_from_file_location('workflow_fixture',ROOT/'tests/Test-ControlsWorkflow.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)


def rule(scope='game',field='forbidden_buttons',value=None):
    return {'id':'fixture-rule','revision':1,'scope':{'level':scope,'target_ids':[] if scope=='global' else ['synthetic-doom']},
            'field':field,'value':[7] if value is None else value,'acceptance':'accepted','reason':'Explicit fixture preference'}


class AdvancedTests(unittest.TestCase):
    def test_research_request_uses_selected_finger_policy_without_releasing_movement(self):
        self.w['baseline']['rules_revision']=p.LITTLE_FINGER_RULES
        constraints=research.request_packet(self.w)['constraints']
        self.assertEqual(constraints['physical_rules_revision'],p.LITTLE_FINGER_RULES)
        self.assertNotIn(2,constraints['protected_buttons'])
        self.assertTrue({3,4,5,9,14,19,24,37}<=set(constraints['protected_buttons']))
        self.assertTrue(constraints['finger_specific_rules_take_precedence'])

    def setUp(self):f.WorkflowTests.setUp(self)
    def test_scoped_rules_are_not_silently_global_or_active_while_proposed(self):
        r=rule();self.w['extensions']['rules']=[r]
        self.assertTrue(any(row['blocked'] for row in p.preview(self.w,self.doc)['rows']))
        r['scope']['target_ids']=['another-game'];self.assertFalse(any(row['blocked'] for row in p.preview(self.w,self.doc)['rows']))
        r['scope']['target_ids']=['synthetic-doom'];r['acceptance']='proposed'
        self.assertFalse(any(row['blocked'] for row in p.preview(self.w,self.doc)['rows']))
    def test_shared_rules_have_revision_history_review_and_no_auto_adoption(self):
        books=p.WorkbookLibrary(self.library);books.save(self.w)
        other_doc=copy.deepcopy(self.doc);other_doc['game_id']='another-game';other_doc['id']='another-map'
        other=p.new_workbook(other_doc, rules_revision=p.RULES);books.save(other)
        lib=rules.Library(self.library);old=lib.read()
        with self.assertRaises(ValueError):lib.save([rule('global')],old['sha256'],authorize=lambda _:False)
        new=lib.save([rule('global')],old['sha256'],authorize=lambda _:True)
        self.assertEqual(len(lib.impact(new)),2)
        self.assertNotIn('shared_rules_snapshot',books.load('synthetic-doom')['extensions'])
        with self.assertRaisesRegex(ValueError,'changed'):lib.save([],old['sha256'],authorize=lambda _:True)
        self.assertTrue((lib.root/'shared-rules-history'/(old['sha256']+'.json')).exists())
    def classify(self):
        for a in self.w['actions']:
            a['proposed_route']=None
            if a['context']=='bindset:0' and a['label'] in ('_shield','_spear','_hint'):
                a.update(meaning='Synthetic known meaning',activation='press',needs_movement=True,urgency=[5] if a['label']!='_hint' else [1],frequency=[1])
    def test_optimizer_proposes_feasible_improvement_without_applying(self):
        self.classify();before=copy.deepcopy(self.w);result=optimizer.recommend(self.w,self.doc,max_states=200,seconds=1)
        self.assertEqual(self.w,before);self.assertFalse(result['native_or_game_changes'])
        proposed={x['action_id']:x['route'] for x in result['proposals']}
        shield=next(a for a in self.w['actions'] if a['label']=='_shield');spear=next(a for a in self.w['actions'] if a['label']=='_spear')
        self.assertEqual(proposed[shield['id']],'BASIC/gameplay/7');self.assertEqual(proposed[spear['id']],'BASIC/gameplay/7')
        self.assertFalse(any(r['blocked'] for r in p.preview(result['candidate'],self.doc)['rows']))
    def test_optimizer_reports_budget_and_unknowns(self):
        self.classify();result=optimizer.recommend(self.w,self.doc,max_states=1,seconds=1)
        self.assertTrue(result['search_limited']);self.assertIn('bounded',result['claim'])
        for a in self.w['actions']:a['urgency']=[];a['frequency']=[]
        result=optimizer.recommend(self.w,self.doc)
        self.assertFalse(result['proposals']);self.assertTrue(result['withheld'])
    def test_locked_native_mouse_cannot_become_keyboard_proposal(self):
        a=next(a for a in self.w['actions'] if a['label']=='_attack');a.update(overlay_context='gameplay',proposed_route='BASIC/gameplay/7')
        row=next(r for r in p.preview(self.w,self.doc)['rows'] if r['id']==a['id'])
        self.assertIn('Native binding field is locked',row['blocked'])
    def test_reconcile_preserves_annotations_and_clears_changed_bundle_proposals(self):
        shield=next(a for a in self.w['actions'] if a['label']=='_shield');shield['meaning']='Keep user evidence'
        raw=self.config.read_bytes().replace(b'"R" "_shield"',b'"U" "_shield"').replace(b'"R" "_spear"',b'"U" "_spear"');self.config.write_bytes(raw)
        fresh=p.source_snapshot(self.service,'target','fixture-idtech','synthetic-doom')
        changed,diff=p.reconcile_source(self.w,fresh,self.doc)
        after=next(a for a in changed['actions'] if a['id']==shield['id'])
        self.assertEqual(after['meaning'],'Keep user evidence');self.assertEqual(after['output'],'U');self.assertIsNone(after['proposed_route'])
        self.assertEqual(len(diff),2);self.assertEqual(self.config.read_bytes(),raw)
    def reply(self):
        a=self.w['actions'][0]
        return {'kind':'controls_action_research_reply','schema_version':1,'game_id':self.w['game_id'],
          'workbook_sha256':maps.fingerprint(self.w),'source_revisions':[s['revision'] for s in self.w['sources']],
          'actions':[{'action_id':a['id'],'annotations':{'meaning':'Source-defined action','urgency':[5],'frequency':[]},
             'citations':[{'kind':'inference','locator':'synthetic fixture','claim':'Labeled test inference, not measured use','checked_at':'2026-10-24'}], 'uncertainty':'Frequency unknown'}]}
    def test_research_exchange_preserves_bindings_and_does_not_invent_frequency(self):
        packet=research.request_packet(self.w);self.assertEqual(len(packet['actions']),len(self.w['actions']))
        candidate,report=research.adopt_reply(self.w,self.reply(),self.doc)
        self.assertEqual(candidate['actions'][0]['frequency'],[]);self.assertEqual(candidate['actions'][0]['output'],self.w['actions'][0]['output'])
        self.assertFalse(report['authorization_imported'])
    def test_research_staleness_and_unrelated_changes_rejected(self):
        reply=self.reply();reply['workbook_sha256']='f'*64
        with self.assertRaises(ValueError):research.adopt_reply(self.w,reply,self.doc)
        reply=self.reply();reply['actions'][0]['annotations']['output']='F24'
        with self.assertRaises(ValueError):research.adopt_reply(self.w,reply,self.doc)
    def test_research_conflicts_need_review(self):
        self.w['actions'][0]['meaning']='Existing user meaning'
        candidate,report=research.adopt_reply(self.w,self.reply(),self.doc)
        self.assertTrue(report['conflicts']);self.assertEqual(candidate['actions'][0]['meaning'],'Existing user meaning')
        candidate,_=research.adopt_reply(self.w,self.reply(),self.doc,replace_conflicts=True)
        self.assertEqual(candidate['actions'][0]['meaning'],'Source-defined action')


if __name__=='__main__':unittest.main()
