"""Location evidence tests use disposable stores and fictional executables."""
import importlib.util,json,shutil,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolModDiscovery import ModDiscovery
from game_mod_ops.safety import ModError
spec=importlib.util.spec_from_file_location('wicked_discovery_fixture',Path(__file__).with_name('Test-GameToolWickedControls.py'))
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
GAME='no-rest-for-the-wicked'

class Tests(unittest.TestCase):
    def setUp(self):
        self.fx=fixture.Tests();self.fx.setUp();self.base=self.fx.base
        self.steam=self.base/'Steam';self.lib=self.base/'Library';(self.steam/'steamapps').mkdir(parents=True)
        common=self.lib/'steamapps/common';common.mkdir(parents=True)
        self.game=common/'NoRestForTheWicked';shutil.copytree(self.fx.game,self.game)
        self.manifest=self.lib/'steamapps/appmanifest_1371980.acf'
        self.write_manifest()
        library=str(self.lib).replace('\\','\\\\')
        (self.steam/'steamapps/libraryfolders.vdf').write_text('"libraryfolders" { "0" { "path" "'+library+'" } }')
        self.prepared=self.base/'prepared';self.prepared.mkdir()
        self.work=self.prepared/'no-rest-for-the-wicked-fixture';shutil.copytree(self.fx.work,self.work)
        meta=json.loads((self.work/'deployment.json').read_text());meta['game_root']=str(self.game)
        (self.work/'deployment.json').write_text(json.dumps(meta))
        self.discovery=ModDiscovery(self.fx.controls,stores=[self.steam],prepared=[self.prepared])
    def write_manifest(self,folder='NoRestForTheWicked'):
        self.manifest.write_text('"AppState" { "appid" "1371980" "name" "No Rest for the Wicked" "installdir" "'+folder+'" "buildid" "123" }')
    def tearDown(self):self.fx.tearDown()
    def test_prepared_and_steam_agreement_ranks_first_and_scan_never_writes(self):
        before={str(p):p.read_bytes() for p in self.base.rglob('*') if p.is_file()}
        report=self.discovery.scan(GAME);top=report['candidates'][0]
        self.assertEqual(top['workspace'],str(self.work));self.assertEqual(top['confidence'],'High')
        self.assertGreater(top['score'],report['candidates'][1]['score'])
        self.assertTrue(any('AppID 1371980' in r for r in top['reasons']));self.assertFalse(report['files_modified'])
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.base.rglob('*') if p.is_file()})
        self.assertEqual(self.discovery.revalidate(top),top)
    def test_steam_manifest_escape_is_rejected(self):
        self.write_manifest('../outside')
        report=self.discovery.scan(GAME)
        self.assertTrue(report['warnings']);self.assertFalse(any('AppID' in r for c in report['candidates'] for r in c['reasons']))
    def test_missing_executable_does_not_offer_a_selectable_location(self):
        (self.game/'NoRestForTheWicked.exe').unlink()
        report=self.discovery.scan(GAME)
        self.assertFalse(any(c['game_dir']==str(self.game) for c in report['candidates']))
    def test_changed_store_evidence_requires_a_new_review(self):
        top=self.discovery.scan(GAME)['candidates'][0];self.write_manifest('ChangedFolder')
        with self.assertRaisesRegex(ModError,'changed'):self.discovery.revalidate(top)
    def test_unreviewed_prepared_code_is_not_offered(self):
        (self.work/'app/switcher.py').write_text('raise RuntimeError("must never run")')
        report=self.discovery.scan(GAME)
        self.assertFalse(any(c['workspace']==str(self.work) for c in report['candidates']))
        self.assertTrue(any('reviewed' in w for w in report['warnings']))
    def test_duplicate_sources_are_merged_but_other_game_paths_are_not(self):
        self.discovery.stores=[self.steam,self.steam];self.discovery.prepared=[self.prepared,self.prepared]
        report=self.discovery.scan(GAME)
        self.assertEqual(sum(c['game_dir']==str(self.game) for c in report['candidates']),1)
        self.assertEqual(len(report['candidates']),2)
    def test_unknown_appid_uses_exact_store_name_and_expected_executable(self):
        identities=self.base/'identities.json';identities.write_text('{"games":{}}')
        with patch('GameToolModDiscovery.IDENTITIES',identities):report=self.discovery.scan(GAME)
        self.assertTrue(any('Steam title matches' in r for c in report['candidates'] for r in c['reasons']))
    def test_separate_prepared_workspaces_remain_explicit_choices(self):
        second=self.prepared/'no-rest-for-the-wicked-another';shutil.copytree(self.work,second)
        rows=[c for c in self.discovery.scan(GAME)['candidates'] if c['game_dir']==str(self.game)]
        self.assertEqual({c['workspace'] for c in rows},{str(self.work),str(second)})

if __name__=='__main__':unittest.main(verbosity=2)
