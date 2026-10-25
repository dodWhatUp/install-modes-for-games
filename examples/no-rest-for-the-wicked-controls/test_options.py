import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import mod_options
from mod_options import ModOptions
import switcher
from test_switcher import fixture


def prepared(base):
    game, work = fixture(base)
    manifest = json.loads((work / 'deployment.json').read_text())
    names = [('loader', 'MelonLoader 0.7.3'), ('build-liberator', 'Build Liberator 1.0.0'),
             ('rune-details', 'Rune Details 1.1.0')]
    for component, (ident, name) in zip(manifest['components'], names):
        component.update(id=ident, name=name)
    extra = dict(manifest['components'][-1])
    extra.update(id='wicked-menu', name='Wicked Menu 1.0-0225', url='https://example.com/wicked-menu',
                 files=[dict(extra['files'][0], target='Mods/C.dll')])
    manifest['components'].append(extra)
    switcher.atomic_json(work / 'deployment.json', manifest)
    return game, work


class Preferences(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.game, self.work = prepared(self.temp.name)
        self.service = switcher.Switcher(self.work, process_check=lambda: [])
        self.options = ModOptions(self.service)
        self.path = self.options.path
        self.original = (b'# User preferences\r\n[WickedMenu]\r\nMenuHotkey = "F12" # chosen key\r\n\r\n'
            b'[BuildLiberator]\r\nFreelySwitchRunes = true\r\nFreelySwitchGems = true\r\n\r\n'
            b'[OtherMod]\r\nKeepThis = "untouched"\r\n')
        self.path.write_bytes(self.original)

    def tearDown(self):
        self.temp.cleanup()

    def save(self, ident, changes):
        return self.options.save(ident, changes, self.options.read(ident)['revision'])

    def test_read_and_noop_never_write(self):
        self.assertEqual(self.options.read('wicked-menu')['values']['MenuHotkey'], 'F12')
        self.assertEqual(self.save('wicked-menu', {'MenuHotkey': 'F12'})['changed'], 0)
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertFalse((self.work / 'recovery').exists())

    def test_only_target_key_changes_and_backup_is_exact(self):
        result = self.save('wicked-menu', {'MenuHotkey': 'F10'})
        expected = self.original.replace(b'"F12" # chosen key', b'"F10" # chosen key')
        self.assertEqual(self.path.read_bytes(), expected)
        self.assertEqual((Path(result['recovery']) / 'MelonPreferences.cfg').read_bytes(), self.original)
        self.assertEqual(self.options.read('build-liberator')['values']['FreelySwitchGems'], True)

    def test_add_missing_section_and_key_preserves_other_tables(self):
        self.save('rune-details', {'Mode': 'Detailed', 'AddSettingsRows': False})
        raw = self.path.read_bytes()
        self.assertTrue(raw.startswith(self.original))
        self.assertIn(b'[RuneDetails]\r\nMode = "Detailed"\r\nAddSettingsRows = false\r\n', raw)
        self.save('build-liberator', {'FreelySwitchRunes': False})
        self.assertFalse(self.options.read('build-liberator')['values']['FreelySwitchRunes'])
        self.assertEqual(self.options.read('rune-details')['values']['Mode'], 'Detailed')

    def test_stale_settings_and_running_game_refuse_writes(self):
        state = self.options.read('wicked-menu')
        self.path.write_bytes(self.original + b'# external edit\r\n')
        with self.assertRaisesRegex(RuntimeError, 'changed since'):
            self.options.save('wicked-menu', {'MenuHotkey': 'F10'}, state['revision'])
        self.service.process_check = lambda: [{'ProcessId': 1}]
        with self.assertRaisesRegex(RuntimeError, 'Save and exit'):
            self.save('wicked-menu', {'MenuHotkey': 'F10'})
        self.assertEqual(self.path.read_bytes(), self.original + b'# external edit\r\n')

    def test_invalid_or_undocumented_options_refuse_writes(self):
        for ident, changes in [('wicked-menu', {'MenuHotkey': 'Unreviewed'}),
                               ('wicked-menu', {'GodMode': True}),
                               ('build-liberator', {'FreelySwitchRunes': 1}),
                               ('loader', {'Enabled': True})]:
            with self.assertRaises(ValueError):
                self.save(ident, changes)
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_write_failure_restores_previous_preferences(self):
        write = mod_options.atomic_bytes
        failed = False
        def fail_once(path, raw):
            nonlocal failed
            if Path(path) == self.path and not failed:
                failed = True
                raise OSError('simulated preference write failure')
            return write(path, raw)
        with patch.object(mod_options, 'atomic_bytes', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.save('wicked-menu', {'MenuHotkey': 'F10'})
        self.assertEqual(self.path.read_bytes(), self.original)
        receipt = next((self.work / 'recovery').glob('*/transaction.json'))
        self.assertEqual(json.loads(receipt.read_text())['status'], 'rolled-back')

    def test_missing_file_defaults_bom_and_changed_game(self):
        self.path.unlink()
        self.assertEqual(self.options.read('wicked-menu')['values']['MenuHotkey'], 'F1')
        self.save('wicked-menu', {'MenuHotkey': 'F12'})
        self.path.write_bytes(b'\xef\xbb\xbf' + self.path.read_bytes())
        self.save('wicked-menu', {'MenuHotkey': 'F10'})
        self.assertTrue(self.path.read_bytes().startswith(b'\xef\xbb\xbf'))
        before = self.path.read_bytes()
        (self.game / 'GameAssembly.dll').write_bytes(b'updated game')
        with self.assertRaisesRegex(RuntimeError, 'game changed'):
            self.save('wicked-menu', {'MenuHotkey': 'F11'})
        self.assertEqual(self.path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
