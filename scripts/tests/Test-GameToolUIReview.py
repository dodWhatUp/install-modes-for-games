"""Separate data, native formats, chosen-manager exports and source preservation."""
import importlib.util,json,sys,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolUIReviewModel import ReviewModel,folder_snapshot,file_delta
from game_mod_ops.safety import ModError
spec=importlib.util.spec_from_file_location('review_fixture',Path(__file__).with_name('Test-GameToolModControls.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

class Tests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.Tests();self.f.setUp();self.model=ReviewModel(self.f.data,self.f.base/'parallel',controls=self.f.controls)
    def tearDown(self):self.f.tearDown()
    def source_bytes(self):return {str(p):p.read_bytes() for root in [self.f.data,*self.f.roots.values()] for p in root.rglob('*') if p.is_file()}
    def test_source_game_and_controller_roots_cannot_be_review_data(self):
        for target in [self.f.data,self.f.data/'inside',self.f.base,self.f.roots['fixture-one'],self.f.roots['fixture-one']/'review']:
            with self.assertRaises(ModError):ReviewModel(self.f.data,target,controls=self.f.controls)
    def test_inspection_and_view_persistence_leave_current_data_and_games_unchanged(self):
        before=self.source_bytes();state=self.model.inspect('fixture-one');self.model.view['drafts']['fixture-one']={'amount':'4.5'};self.model.save_view()
        second=ReviewModel(self.f.data,self.model.root,controls=self.f.controls);self.assertEqual(second.view['drafts']['fixture-one']['amount'],'4.5');self.assertEqual(state['values']['amount'],2.0);self.assertEqual(self.source_bytes(),before)
    def test_refresh_reports_file_add_modify_remove(self):
        folder=self.f.base/'files';folder.mkdir();(folder/'one.txt').write_text('one');first=folder_snapshot(folder);(folder/'one.txt').write_text('longer');(folder/'two.txt').write_text('new');second=folder_snapshot(folder);d=file_delta(first,second)
        self.assertEqual(d['added'],['two.txt']);self.assertEqual(d['changed'],['one.txt']);(folder/'one.txt').unlink();self.assertEqual(file_delta(second,folder_snapshot(folder))['removed'],['one.txt'])
    def test_folder_refresh_is_bounded(self):
        folder=self.f.base/'files';folder.mkdir()
        for i in range(8):(folder/str(i)).write_text(str(i))
        value=folder_snapshot(folder,limit=3);self.assertEqual(len(value['entries']),3);self.assertTrue(value['truncated'])
    def test_saved_profile_is_parallel_and_roundtrips(self):
        before=self.source_bytes();s=self.model.inspect('fixture-one');self.model.save_profile('fixture-one','candidate',{'amount':4.5},s['revision']);self.assertEqual(self.model.load_profile('fixture-one','review:candidate')['amount'],4.5);self.assertEqual(self.source_bytes(),before)
    def test_profile_cannot_cross_instances(self):
        s=self.model.inspect('fixture-one');path=self.model.save_profile('fixture-one','candidate',{},s['revision']);other=self.model.root/'profiles/fixture-two';other.mkdir();(other/path.name).write_bytes(path.read_bytes())
        with self.assertRaises(ModError):self.model.load_profile('fixture-two','review:candidate')
    def test_manager_choice_changes_handoff_metadata_and_preserves_source(self):
        before=self.source_bytes();s=self.model.inspect('fixture-one')
        for manager in ['vortex','mod-organizer-2','rhi','folder']:
            result=self.model.export_settings('fixture-one',manager,{'amount':7.0},s['revision']);folder=Path(result['folder']);manifest=json.loads((folder/'HANDOFF-MANIFEST.json').read_text());self.assertEqual(manifest['manager'],manager);self.assertFalse(manifest['deployed'] if 'deployed' in manifest else manifest['manager_deployed'])
            with zipfile.ZipFile(folder/'Manager Files.zip') as archive:self.assertIsNone(archive.testzip());self.assertEqual(json.loads(archive.read('DRAFT-PROFILE.json'))['values']['amount'],7.0)
        self.assertEqual(self.source_bytes(),before)
    def test_stale_export_refused_before_copy(self):
        s=self.model.inspect('fixture-one');self.f.path('fixture-one').write_bytes(self.f.initial['fixture-one']+b'; other writer\n')
        with self.assertRaises(ModError):self.model.export_settings('fixture-one','vortex',{},s['revision'])
        self.assertFalse((self.model.root/'exports').exists())
    def test_selected_saved_resource_export_is_a_copy_not_native_import(self):
        path=self.f.base/'profile.json';path.write_text('{"sample":true}');row={'path':path,'label':'Profile'};result=self.model.export_resource(row,'vortex');self.assertFalse(result['native_import_supported']);self.assertEqual((Path(result['folder'])/'profile.json').read_bytes(),path.read_bytes())
        with self.assertRaises(ModError):self.model.export_resource({'path':self.f.roots['fixture-one']/'Fixture.exe','label':'Program'},'vortex')
    def test_selected_extra_location_is_private_to_review(self):
        before=self.source_bytes();self.model.add_location('reports',self.f.base);rows=self.model.resources('reports');self.assertEqual(rows[-1]['path'],self.f.base);self.assertEqual(self.source_bytes(),before)
    def test_feedback_does_not_adopt_or_send(self):
        path=self.model.feedback('Prefer the compact groups','Like this direction');value=json.loads(path.read_text());self.assertFalse(value['adopted']);self.assertEqual(value['notes'],'Prefer the compact groups')
    def test_the_two_launchers_keep_independent_view_and_draft_files(self):
        left=ReviewModel(self.f.data,self.model.root,controls=self.f.controls,view_name='view-mods.json');right=ReviewModel(self.f.data,self.model.root,controls=self.f.controls,view_name='view-files.json')
        left.view['drafts']['fixture-one']={'amount':'8'};left.save_view();right.view['page']='reports';right.save_view();self.assertEqual(json.loads(left.view_path.read_text())['drafts']['fixture-one']['amount'],'8');self.assertEqual(json.loads(right.view_path.read_text())['page'],'reports')
    def test_explicit_apply_reuses_the_original_service(self):
        state=self.model.inspect('fixture-one')
        with patch.object(self.f.controls,'_closed',return_value=None):self.model.apply_current('fixture-one',{'enabled':False},state['revision'])
        self.assertFalse(self.f.controls.inspect('fixture-one')['values']['enabled']);self.assertEqual(self.f.path('fixture-two').read_bytes(),self.f.initial['fixture-two'])

if __name__=='__main__':unittest.main(verbosity=2)
