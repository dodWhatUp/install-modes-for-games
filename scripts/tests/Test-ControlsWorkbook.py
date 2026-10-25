"""Planning-v2 graph preservation, classification projection and bad intake."""
import copy,importlib.util,json,pathlib,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import GameToolControlsWorkbook as w2
import GameToolControlsPlanner as p
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder
spec=importlib.util.spec_from_file_location('planner_fixture',ROOT/'tests/Test-ControlsPlanner.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)


def minimal(schema, root):
    if '$ref' in schema:return minimal(root['definitions'][schema['$ref'].split('/')[-1]],root)
    if 'const' in schema:return schema['const']
    if 'enum' in schema:return 'unknown' if 'unknown' in schema['enum'] else schema['enum'][0]
    typ=schema.get('type','object')
    if type(typ) is list:
        if 'null' in typ:return None
        typ=typ[0]
    if typ=='object':return {name:minimal(schema['properties'][name],root) for name in schema.get('required',[])}
    if typ=='array':return []
    if typ=='string':return 'fixture'
    if typ in ('integer','number'):return schema.get('minimum',1)
    if typ=='boolean':return False
    return None


def workbook(app):
    schema=json.loads(w2.SCHEMA.read_text('utf-8-sig'));value=minimal(schema,schema)
    value.update(owner='dodWhatUp/install-modes-for-games',workbook_id='fixture-v2',revision='fixture-r1',required_features=sorted(w2.FEATURES))
    value['game_identity']['game_id']=app['game_id'];value['extensions']={'future_owner_field':{'paragraph':'First line\nSecond line'}}
    context=minimal(schema['definitions']['context'],schema);context.update(id='gameplay',revision=1)
    action=minimal(schema['definitions']['action'],schema);action.update(id=app['actions'][0]['id'],context_id='gameplay',label='Classified fixture',meaning='Meaning from fixture\nSecond paragraph')
    action['priority'].update(policy_revision=p.POLICY,urgency_candidates=[5],frequency_candidates=[1],score_candidates=[17],computed_priority=17)
    value['contexts']=[context];value['actions']=[action]
    return value


class WorkbookTests(unittest.TestCase):
    def setUp(self):self.doc=f.document();self.app=p.new_workbook(self.doc);self.value=workbook(self.app)

    def test_nested_bundle_priorities_and_graph_references_are_checked(self):
        schema=json.loads(w2.SCHEMA.read_text());value=copy.deepcopy(self.value)
        second=copy.deepcopy(value['actions'][0]);second['id']='second-action';value['actions'].append(second)
        bundle=minimal(schema['definitions']['bundle'],schema);bundle.update(id='bundle1',member_action_ids=[a['id'] for a in value['actions']],context_ids=['gameplay'])
        profile=minimal(schema['definitions']['bundle']['properties']['context_profiles']['items'],schema)
        profile.update(context_id='gameplay',applicable_member_action_ids=bundle['member_action_ids'])
        bundle['context_profiles']=[profile];value['bundles']=[bundle]
        w2.validate(value)
        profile['priority'].update(urgency_candidates=[5],frequency_candidates=[1],score_candidates=[17],computed_priority=1)
        with self.assertRaisesRegex(ValueError,'arithmetic'):w2.validate(value)
        profile['priority']['computed_priority']=17;w2.validate(value)
        value['contexts'][0]['entry_action_ids']=['missing-action']
        with self.assertRaisesRegex(ValueError,'actions reference'):w2.validate(value)
    def test_full_graph_is_preserved_and_classifications_project_without_bindings(self):
        before=copy.deepcopy(self.value);w2.validate(before)
        result,report=w2.import_workbook(self.value,self.app,self.doc)
        self.assertEqual(self.value,before);self.assertEqual(result['extensions']['workbook_v2']['original'],before)
        self.assertEqual(result['actions'][0]['urgency'],[5]);self.assertEqual(result['actions'][0]['output'],self.app['actions'][0]['output'])
        self.assertFalse(report['assignments_adopted']);self.assertFalse(report['shared_rules_promoted'])
        exported=w2.export_workbook(result);self.assertEqual(exported['extensions']['future_owner_field'],before['extensions']['future_owner_field'])
        self.assertFalse(exported['file_content_grants_authorization'])
    def test_paragraphs_survive_source_library_save_and_original_bytes_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp);source=root/'original.json';raw=json.dumps(self.value,ensure_ascii=False,indent=3).encode();source.write_bytes(raw)
            parsed=w2.read(source,root/'intake');result,_=w2.import_workbook(parsed,self.app,self.doc)
            lib=p.WorkbookLibrary(builder.SourceLibrary(root/'data'));lib.save(result)
            self.assertEqual(lib.load(self.app['game_id']),result)
            self.assertEqual(next((root/'intake').glob('*.json')).read_bytes(),raw)
    def test_bad_arithmetic_references_required_features_and_authority_rejected(self):
        changes=[lambda v:v['actions'][0]['priority'].update(computed_priority=20),
                 lambda v:v['actions'][0].update(context_id='not-declared'),
                 lambda v:v['required_features'].append('execute-native-code'),
                 lambda v:v.update(file_content_grants_authorization=True)]
        for change in changes:
            value=copy.deepcopy(self.value);change(value)
            with self.assertRaises(ValueError):w2.validate(value)
    def test_wrong_game_and_ambiguous_links_rejected(self):
        value=copy.deepcopy(self.value);value['game_identity']['game_id']='another-game'
        with self.assertRaises(ValueError):w2.import_workbook(value,self.app,self.doc)
        original=copy.deepcopy(self.value['actions'][0]);original['id']='other-action';self.value['actions'].append(original)
        with self.assertRaises(ValueError):w2.import_workbook(self.value,self.app,self.doc,{a['id']:self.app['actions'][0]['id'] for a in self.value['actions']})

    def test_unidentified_game_does_not_adopt_common_ids_without_explicit_link(self):
        self.value['game_identity']['game_id']=None
        result,report=w2.import_workbook(self.value,self.app,self.doc)
        self.assertEqual(report['projected_actions'],[]);self.assertEqual(result['actions'],self.app['actions'])
        confirmed,report=w2.import_workbook(self.value,self.app,self.doc,confirmed_game_id=self.app['game_id'])
        self.assertEqual(len(report['projected_actions']),1)
        self.assertIsNone(confirmed['extensions']['workbook_v2']['original']['game_identity']['game_id'])
    def test_unlinked_records_remain_visible_without_fuzzy_matching(self):
        self.value['actions'][0]['id']='unlinked';self.value['actions'][0]['native_command']='similar-looking-only'
        result,report=w2.import_workbook(self.value,self.app,self.doc)
        self.assertEqual(report['unlinked_actions'],['unlinked']);self.assertEqual(result['actions'],self.app['actions'])
    def test_duplicate_json_and_excessive_depth_rejected(self):
        with self.assertRaises(Exception):p.decode(b'{"x":1,"x":2}')
        value=[];cursor=value
        for _ in range(30):child=[];cursor.append(child);cursor=child
        with self.assertRaises(ValueError):p.bounded_data(value)

    def assigned(self):
        schema=json.loads(w2.SCHEMA.read_text());value=copy.deepcopy(self.value)
        action=next(a for a in self.app['actions'] if a['output']=='J');value['actions'][0]['id']=action['id']
        layer=minimal(schema['definitions']['layer'],schema);layer.update(id='BASIC',revision=1)
        route=minimal(schema['definitions']['route'],schema);route.update(id='r1',revision=1,layer_id='BASIC',button_id=7,context_ids=['gameplay'],output_display='G')
        assignment=minimal(schema['definitions']['assignment'],schema);assignment.update(id='assign1',revision=1,action_ids=[action['id']],context_ids=['gameplay'],route_id='r1',state='play_verified',role='primary')
        value.update(layers=[layer],routes=[route],assignments=[assignment])
        return value,schema

    def test_external_verified_assignment_only_becomes_an_explicit_proposal(self):
        value,_=self.assigned();app,_=w2.import_workbook(value,self.app,self.doc)
        result=w2.assignment_preview(app,self.doc)
        self.assertEqual(list(result['proposed'].values()),['BASIC/gameplay/7'])
        self.assertFalse(result['adopted_verification_claims']);self.assertTrue(result['blocked'])

    def test_divergent_assignments_are_not_resolved_by_timestamps_or_order(self):
        value,_=self.assigned();route=copy.deepcopy(value['routes'][0]);route.update(id='r2',button_id=11,output_display='H')
        assignment=copy.deepcopy(value['assignments'][0]);assignment.update(id='assign2',route_id='r2')
        value['routes'].append(route);value['assignments'].append(assignment)
        app,_=w2.import_workbook(value,self.app,self.doc)
        with self.assertRaisesRegex(ValueError,'Divergent'):w2.assignment_preview(app,self.doc)


if __name__=='__main__':unittest.main()
