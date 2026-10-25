import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import switcher


def fixture(base):
    base = Path(base)
    game, work = base / 'game', base / 'workspace'
    game.mkdir()
    work.mkdir()
    (game / 'NoRestForTheWicked.exe').write_bytes(b'fixture exe')
    (game / 'GameAssembly.dll').write_bytes(b'fixture assembly')
    (game / 'UserData').mkdir()
    (game / 'UserData/settings.cfg').write_bytes(b'personal settings')
    (game / 'save.dat').write_bytes(b'personal progress')
    (work / 'cache').mkdir()
    components = []
    for ident, relative in [('loader', 'version.dll'), ('a', 'Mods/A.dll'), ('b', 'Mods/B.dll')]:
        source = work / 'cache' / (ident + '.dll')
        source.write_bytes(('original ' + ident).encode())
        components.append({'id': ident, 'name': ident, 'recommended': ident == 'a',
            'url': 'https://example.com/' + ident, 'note': 'Fixture only',
            'files': [{'target': relative, 'source': 'cache/' + source.name, 'sha256': switcher.sha(source)}]})
    switcher.atomic_json(work / 'deployment.json', {'schema': 1, 'game_root': str(game),
        'game_exe_sha256': switcher.sha(game / 'NoRestForTheWicked.exe'),
        'game_markers': {'GameAssembly.dll': switcher.sha(game / 'GameAssembly.dll')},
        'components': components})
    return game, work


class Switching(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.game, self.work = fixture(self.temp.name)
        self.service = switcher.Switcher(self.work, process_check=lambda: [])

    def tearDown(self):
        self.temp.cleanup()

    def apply(self, **changes):
        desired = {'loader': False, 'a': False, 'b': False}
        desired.update(changes)
        return self.service.apply(desired, self.service.inspect()['revision'])

    def test_on_off_and_individual_round_trip_preserves_settings_saves_and_unknown_files(self):
        (self.game / 'Mods').mkdir()
        (self.game / 'Mods/Other.dll').write_bytes(b'not owned')
        self.apply(loader=True, a=True, b=True)
        self.assertTrue((self.game / 'version.dll').is_file())
        self.apply(loader=True, b=True)
        self.assertFalse((self.game / 'Mods/A.dll').exists())
        self.assertTrue((self.game / 'Mods/B.dll').exists())
        self.apply()
        self.assertEqual((self.game / 'Mods/Other.dll').read_bytes(), b'not owned')
        self.assertEqual((self.game / 'UserData/settings.cfg').read_bytes(), b'personal settings')
        self.assertEqual((self.game / 'save.dat').read_bytes(), b'personal progress')
        self.assertTrue(all(r['state'] == 'off' for r in self.service.inspect()['components']))
        self.assertEqual(self.apply()['changed'], 0)

    def test_open_game_blocks_before_any_write(self):
        self.service.process_check = lambda: [{'ProcessId': 1}]
        with self.assertRaisesRegex(RuntimeError, 'Save and exit'):
            self.apply(loader=True, a=True)
        self.assertFalse((self.game / 'version.dll').exists())
        self.assertFalse((self.work / 'recovery').exists())

    def test_modified_owned_file_is_never_overwritten(self):
        self.apply(loader=True, a=True)
        (self.game / 'Mods/A.dll').write_bytes(b'changed by another owner')
        with self.assertRaisesRegex(RuntimeError, 'modified or incomplete'):
            self.apply()
        self.assertEqual((self.game / 'Mods/A.dll').read_bytes(), b'changed by another owner')

    def test_stale_preview_blocks(self):
        state = self.service.inspect()
        (self.game / 'version.dll').write_bytes(b'external change')
        with self.assertRaisesRegex(RuntimeError, 'changed since Refresh'):
            self.service.apply({'loader': True, 'a': True, 'b': False}, state['revision'])

    def test_missing_cache_blocks_without_partial_install(self):
        (self.work / 'cache/a.dll').unlink()
        with self.assertRaisesRegex(RuntimeError, 'not been downloaded'):
            self.apply(loader=True, a=True)
        self.assertFalse((self.game / 'version.dll').exists())

    def test_mid_transaction_failure_restores_exact_previous_state(self):
        original = switcher.atomic_bytes
        failed = False
        def fail_one(path, raw):
            nonlocal failed
            if Path(path) == self.game / 'Mods/B.dll' and not failed:
                failed = True
                raise OSError('simulated write failure')
            return original(path, raw)
        with patch.object(switcher, 'atomic_bytes', side_effect=fail_one):
            with self.assertRaisesRegex(OSError, 'simulated'):
                self.apply(loader=True, a=True, b=True)
        self.assertFalse((self.game / 'Mods/A.dll').exists())
        self.assertFalse((self.game / 'Mods/B.dll').exists())
        self.assertFalse((self.game / 'version.dll').exists())
        receipt = next((self.work / 'recovery').glob('*/transaction.json'))
        self.assertEqual(json.loads(receipt.read_text())['status'], 'rolled-back')

    def test_dependency_and_changed_game_guards(self):
        with self.assertRaisesRegex(ValueError, 'require'):
            self.apply(a=True)
        (self.game / 'GameAssembly.dll').write_bytes(b'new game update')
        with self.assertRaisesRegex(RuntimeError, 'executable changed'):
            self.apply(loader=True)

    def test_game_update_still_allows_exact_owned_mods_to_be_disabled(self):
        self.apply(loader=True, a=True)
        (self.game / 'GameAssembly.dll').write_bytes(b'new game update')
        self.apply()
        self.assertFalse((self.game / 'version.dll').exists())
        self.assertFalse((self.game / 'Mods/A.dll').exists())
        self.assertEqual((self.game / 'GameAssembly.dll').read_bytes(), b'new game update')

    def test_traversal_is_rejected(self):
        data = json.loads((self.work / 'deployment.json').read_text())
        data['components'][0]['files'][0]['target'] = '../escape.dll'
        switcher.atomic_json(self.work / 'deployment.json', data)
        with self.assertRaises(ValueError):
            switcher.Switcher(self.work)


class UI(unittest.TestCase):
    @unittest.skipUnless(__import__('os').environ.get('DISPLAY'), 'GUI runs in isolated Linux Xvfb')
    def test_widget_state_and_compact_layout(self):
        import tkinter as tk
        from mod_panel import Panel
        with tempfile.TemporaryDirectory() as temp:
            game, work = fixture(temp)
            root = tk.Tk()
            panel = Panel(root, switcher.Switcher(work, process_check=lambda: []))
            root.update()
            self.assertFalse(panel.vars['a'].get())
            panel.vars['a'].set(True)
            self.assertFalse((game / 'Mods/A.dll').exists(), 'Preview must not apply')
            panel.refresh()
            self.assertFalse(panel.vars['a'].get())
            root.geometry('720x490')
            root.update()
            self.assertLess(panel.buttons[0].winfo_rootx() + panel.buttons[0].winfo_width(), root.winfo_rootx() + root.winfo_width())
            self.assertEqual(set(panel.row_actions['a']), {'github', 'nexus', 'preview', 'options'})
            panel.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
