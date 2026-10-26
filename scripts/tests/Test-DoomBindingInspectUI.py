"""Headless selection/filter/export checks; Tk behavior is a guest GUI check."""
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolDoomBindingInspect as api
import GameToolDoomBindingInspectUI as ui

spec = importlib.util.spec_from_file_location('doom_inspect_test_fixtures', Path(__file__).with_name('Test-DoomBindingInspect.py'))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


class SelectionTests(unittest.TestCase):
    def test_standard_explicit_steam_role_derives_owner(self):
        expected = str(api.STEAM_ID64_BASE + 42)
        for path in [r'C:\Steam\userdata\42\3017860\remote\PROFILE\profile.bin',
                     '/tmp/Steam/userdata/42/3017860/remote/PROFILE/profile.bin']:
            self.assertEqual(ui.derive_owner_from_path(path), expected)

    def test_other_games_archive_numbers_and_relative_paths_are_not_owner_proof(self):
        for path in [r'C:\archive\42\PROFILE\profile.bin',
                     r'C:\Steam\userdata\42\782330\remote\PROFILE\profile.bin',
                     r'userdata\42\3017860\remote\PROFILE\profile.bin',
                     r'C:\Steam\userdata\not-an-account\3017860\remote\PROFILE\profile.bin',
                     '/tmp/userdata/4294967296/3017860/remote/PROFILE/profile.bin']:
            self.assertIsNone(ui.derive_owner_from_path(path))

    def test_filters_preserve_context_family_and_unfiltered_source(self):
        rows = [{'context_index':0,'command':'_throw','output':'K','input_family':'keyboard'},
                {'context_index':0,'command':'_throw','output':'MOUSE3','input_family':'mouse'},
                {'context_index':1,'command':'_throw','output':'JOY1','input_family':'controller'}]
        self.assertEqual(ui.filtered_rows(rows, 'throw', '0', 'mouse'), [rows[1]])
        self.assertEqual(ui.filtered_rows(rows, 'joy'), [rows[2]])
        self.assertEqual(len(rows), 3)
        self.assertEqual(ui.filtered_rows(rows, 'nothing'), [])

    def test_export_never_overwrites_an_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'reference.json'
            path.write_text('original', encoding='utf-8')
            with self.assertRaises(FileExistsError):
                ui.export_new_file(path, 'replacement', '.json')
            self.assertEqual(path.read_text(), 'original')

    def test_exports_only_new_json_or_csv_never_binary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, extension in [('profile.bin','.json'), ('run.exe','.csv'), ('file.txt','.txt')]:
                with self.assertRaises(api.InspectError):ui.export_new_file(root/name, 'data', extension)
                self.assertFalse((root/name).exists())
            ui.export_new_file(root/'new.json', '{"kind":"reference"}', '.json')
            ui.export_new_file(root/'new.csv', 'Action,Key\nThrow,K\n', '.csv')
            self.assertTrue((root/'new.json').is_file())
            self.assertTrue((root/'new.csv').is_file())

    @unittest.skipIf(fixtures.AESGCM is None, 'Reviewed cryptography runtime unavailable')
    def test_explicit_snapshot_read_pins_bytes_and_preserves_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'profile.bin'
            raw = fixtures.wrap(fixtures.plaintext([[('K','_throw',1)]]))
            path.write_bytes(raw)
            before = hashlib.sha256(raw).hexdigest()
            result = ui.read_selected_snapshot(path, fixtures.IDENTITY)
            self.assertEqual(result['source']['sha256'], before)
            self.assertEqual(result['bindings'][0]['output'], 'K')
            self.assertEqual(path.read_bytes(), raw)

    def test_wrong_snapshot_filename_is_rejected_before_read(self):
        with self.assertRaises(api.InspectError) as caught:
            ui.read_selected_snapshot('/does/not/exist/settings.bin', fixtures.IDENTITY)
        self.assertEqual(caught.exception.code, 'FILE_ROLE_UNSUPPORTED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
