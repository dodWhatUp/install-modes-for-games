"""Discovery and mapping recovery in disposable files; no real game setup."""
from pathlib import Path
import json,tempfile,unittest
from unittest.mock import patch
from settings_locator import RELATIVE,SettingsLocationError,inspect_settings,resolve_settings,save_location,scan_settings

def config(width=3840,height=2160):
    return f'"ScreenWidth16by9" "{width}.000000"\r\n"ScreenHeight16by9" "{height}.000000"\r\n"HDROut" "1.000000"\r\n"UnknownSetting" "keep"\r\n'.encode()

class LocatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='native-locator-test-');self.base=Path(self.tmp.name)
        self.workspace=self.base/'controller';self.workspace.mkdir();self.local=self.base/'local';self.local.mkdir()
    def tearDown(self):self.tmp.cleanup()
    def put(self,path,data=None):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(config() if data is None else data);return path
    def resolve(self):return resolve_settings(self.workspace,roots=[self.local])
    def binding(self):return json.loads((self.workspace/'control-panel-paths.json').read_text())
    def test_standard_file_builds_its_own_mapping_without_changing_config(self):
        native=self.put(self.local/RELATIVE);original=native.read_bytes();result=self.resolve()
        self.assertEqual(Path(self.binding()['native_config_path']),Path(result['path']))
        self.assertEqual(native.read_bytes(),original)
        self.assertEqual((result['selected']['width'],result['selected']['height']),(3840,2160))
    def test_redirected_file_is_found_without_a_saved_absolute_path(self):
        native=self.put(self.local/'Packages/Example.Package/LocalCache/Local'/RELATIVE)
        self.assertEqual(Path(self.resolve()['path']),Path(inspect_settings(native)['path']))
    def test_saved_valid_selection_wins_over_another_config(self):
        chosen=self.put(self.local/'Packages/Chosen.Package/LocalCache/Local'/RELATIVE)
        self.put(self.local/RELATIVE,config(2560,1440));save_location(self.workspace,chosen)
        self.assertEqual(self.resolve()['selected']['source'],'Saved location')
        self.assertEqual(Path(self.binding()['native_config_path']),Path(inspect_settings(chosen)['path']))
    def test_conflicting_redirected_files_require_selection(self):
        self.put(self.local/'Packages/A/LocalCache/Local'/RELATIVE)
        self.put(self.local/'Packages/B/LocalCache/Local'/RELATIVE,config(2560,1440))
        with self.assertRaises(SettingsLocationError) as error:self.resolve()
        self.assertEqual(error.exception.report['status'],'ambiguous')
        self.assertFalse((self.workspace/'control-panel-paths.json').exists())
    def test_byte_identical_copies_are_not_a_conflict(self):
        for name in ['A','B']:self.put(self.local/f'Packages/{name}/LocalCache/Local'/RELATIVE)
        self.assertEqual(self.resolve()['status'],'found')
    def test_broken_mapping_is_preserved_before_automatic_rebuild(self):
        raw=b'{broken json and original bytes';(self.workspace/'control-panel-paths.json').write_bytes(raw)
        native=self.put(self.local/RELATIVE);self.resolve()
        backups=list((self.workspace/'settings-location-recovery').glob('*/control-panel-paths.json'))
        self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),raw)
        self.assertEqual(native.read_bytes(),config())
    def test_future_fields_survive_mapping_repair(self):
        (self.workspace/'control-panel-paths.json').write_text(json.dumps({'schema':1,'native_config_path':str(self.base/'gone/render.cfg'),'future':{'keep':7}}))
        self.put(self.local/RELATIVE);self.resolve();self.assertEqual(self.binding()['future'],{'keep':7})
    def test_missing_saved_file_rebinds_and_repeated_checks_do_not_rewrite(self):
        native=self.put(self.local/'Packages/A/LocalCache/Local'/RELATIVE);self.resolve()
        binding=self.workspace/'control-panel-paths.json';old=binding.read_bytes()
        self.resolve();self.assertEqual(binding.read_bytes(),old)
        native.unlink();self.put(self.local/RELATIVE,config(2560,1440));self.resolve()
        self.assertEqual(inspect_settings(Path(self.binding()['native_config_path']))['width'],2560)
    def test_empty_wrong_duplicate_and_nan_configs_are_rejected(self):
        native=self.local/RELATIVE
        for raw in [b'',b'not game settings',config()+b'"HDROut" "0"\n',config().replace(b'3840.000000',b'nan')]:
            self.put(native,raw)
            with self.assertRaises(SettingsLocationError):self.resolve()
            self.assertEqual(native.read_bytes(),raw)
    def test_no_file_is_not_replaced_with_invented_settings(self):
        with self.assertRaises(SettingsLocationError) as error:self.resolve()
        self.assertEqual(error.exception.report['status'],'missing')
        self.assertFalse((self.local/RELATIVE).exists());self.assertFalse(list(self.workspace.iterdir()))
    def test_aliases_resolving_to_the_same_physical_file_are_deduplicated(self):
        native=self.put(self.local/RELATIVE)
        alias=self.put(self.local/'Packages/A/LocalCache/Local'/RELATIVE)
        actual=Path(inspect_settings(native)['path'])
        with patch('settings_locator.physical_file',return_value=actual):
            report=scan_settings(self.workspace,roots=[self.local])
        self.assertEqual(len([c for c in report['candidates'] if c['valid']]),1)
    def test_failed_mapping_write_preserves_previous_mapping_and_game_file(self):
        native=self.put(self.local/RELATIVE);mapping=self.workspace/'control-panel-paths.json';original=b'{"schema":1,"future":"keep"}';mapping.write_bytes(original)
        with patch('settings_locator.os.replace',side_effect=OSError('fixture disk failure')):
            with self.assertRaises(OSError):save_location(self.workspace,native)
        self.assertEqual(mapping.read_bytes(),original);self.assertEqual(native.read_bytes(),config())

if __name__=='__main__':unittest.main(verbosity=2)
