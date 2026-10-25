"""Purpose matching, typed scopes and read-only discovery on fictional games."""
import importlib.util,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolUIReviewSearch import catalog,search,SCOPES,section_for,row
spec=importlib.util.spec_from_file_location('review_search_fixture',Path(__file__).with_name('Test-GameToolUIReview.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class Tests(unittest.TestCase):
    def setUp(self):self.f=fixture.Tests();self.f.setUp();self.model=self.f.model
    def tearDown(self):self.f.tearDown()
    def rows(self,scope=SCOPES[1],page='mods'):return catalog(self.model,scope,page,'fixture-one','fixture-one')[0]
    def test_page_scope_does_not_index_other_game_or_page(self):
        rows=self.rows(SCOPES[0]);self.assertTrue(all(r['page']=='mods' for r in rows));self.assertEqual({r['instance'] for r in rows if 'instance' in r},{'fixture-one'})
        self.assertFalse(any('field_id' in r for r in self.rows(SCOPES[0],'reports')))
    def test_game_scope_does_not_leak_other_game_and_all_scope_finds_it(self):
        self.assertEqual({r['game_id'] for r in self.rows() if 'game_id' in r},{'fixture-one'});self.assertEqual({r['game_id'] for r in self.rows(SCOPES[2]) if 'game_id' in r},{'fixture-one','fixture-two'})
    def test_search_by_native_id_and_filters(self):
        hits,_=search(self.rows(),'amount',kind='Setting');self.assertEqual(hits[0]['field_id'],'amount');self.assertEqual(search(self.rows(),'amount',kind='Switch')[1],0)
    def test_handoff_synonyms_and_topic_filter(self):
        hits,_=search(self.rows(),'transfer to Vortex',topic='Programs');self.assertTrue(any(r.get('action_id')=='export' for r in hits))
    def test_meaning_matches_multiple_abilities_phrase(self):
        rows=[row('Multi Equip Skills','mods','settings-0','Switch','Gameplay','Equip multiple skills or abilities at the same time.',field_id='multi-skills')]
        hits,total=search(rows,'more abilities at the same time');self.assertEqual(total,1);self.assertIn('Related purpose',hits[0]['match'])
    def test_named_manager_only_matches_declared_destinations(self):
        hits,_=search(self.rows(),'Vortex');self.assertTrue(hits);self.assertTrue(all(r['page'] in {'mods','profiles','tools'} for r in hits))
    def test_hebrew_purpose_and_spelling_are_supported(self):
        rows=self.rows();self.assertTrue(any(r.get('action_id')=='pin' for r in search(rows,'תמיד למעלה')[0]));self.assertTrue(any(r.get('action_id')=='refresh' for r in search(rows,'refersh')[0]))
    def test_no_results_and_empty_query_browse_with_limit(self):
        self.assertEqual(search(self.rows(),'unfindable-zqx')[1],0);hits,total=search(self.rows(),' ',limit=2);self.assertEqual(len(hits),2);self.assertGreater(total,2)
    def test_section_mapping_uses_actual_groups_not_fixed_index(self):
        self.assertEqual(section_for([{'id':'amount'}],{'id':'amount'}),'settings-0')
        schema=[{'id':'graphics'},{'id':'width'},{'id':'enabled'}];self.assertEqual(section_for(schema,schema[2]),'settings-2')
    def test_index_does_not_read_folder_contents_or_mutate_sources(self):
        before=self.f.source_bytes()
        with patch.object(self.model,'refresh_files',side_effect=AssertionError('Content scan forbidden')):self.rows(SCOPES[2])
        self.assertEqual(self.f.source_bytes(),before)
    def test_failed_connection_keeps_other_results_with_warning(self):
        inspect=self.model.inspect
        with patch.object(self.model,'inspect',side_effect=lambda ident:(_ for _ in ()).throw(OSError('fixture unavailable')) if ident=='fixture-two' else inspect(ident)):
            rows,warnings=catalog(self.model,SCOPES[2],'mods','fixture-one','fixture-one')
        self.assertTrue(any('field_id' in r for r in rows));self.assertTrue(any('fixture unavailable' in w for w in warnings))

if __name__=='__main__':unittest.main(verbosity=2)
