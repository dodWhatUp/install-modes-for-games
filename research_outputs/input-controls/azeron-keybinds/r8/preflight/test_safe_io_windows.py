"""Windows metadata regression and retained read guards; synthetic files only."""
import os
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import safe_io


def metadata(st, **changes):
    keys = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns',
            'st_birthtime_ns', 'st_mode', 'st_file_attributes')
    values = {key: getattr(st, key, None) for key in keys}
    values.update(changes)
    return SimpleNamespace(**values)


class WindowsMetadataTests(unittest.TestCase):
    def test_modified_regular_file(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'fixture.txt'
            path.write_bytes(b'initial')
            time.sleep(0.02)
            path.write_bytes(b'updated')
            raw, meta = safe_io.read_regular(path)
            self.assertEqual(raw, b'updated')
            self.assertEqual(meta['sha256'], safe_io.sha(b'updated'))

    def test_cross_api_ctime_difference_only_on_windows(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'fixture.txt'
            path.write_bytes(b'abc')
            before = path.lstat()
            opened = metadata(before, st_ctime_ns=before.st_ctime_ns + 1)
            with patch.object(safe_io, 'WINDOWS_STAT', True):
                self.assertEqual(safe_io.opened_identity(before), safe_io.opened_identity(opened))
            with patch.object(safe_io, 'WINDOWS_STAT', False):
                self.assertNotEqual(safe_io.opened_identity(before), safe_io.opened_identity(opened))

    def test_handle_ctime_change_during_read_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'fixture.txt'
            path.write_bytes(b'abc')
            original = os.fstat
            calls = 0
            def changed(fd):
                nonlocal calls
                calls += 1
                st = original(fd)
                return metadata(st, st_ctime_ns=st.st_ctime_ns + 1) if calls == 2 else st
            with patch.object(safe_io.os, 'fstat', side_effect=changed):
                with self.assertRaisesRegex(safe_io.ReviewError, 'changed during read'):
                    safe_io.read_regular(path)

    def test_identity_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'fixture.txt'
            path.write_bytes(b'abc')
            original = os.fstat
            with patch.object(safe_io.os, 'fstat', side_effect=lambda fd: metadata(original(fd), st_ino=0)):
                with self.assertRaisesRegex(safe_io.ReviewError, 'identity changed'):
                    safe_io.read_regular(path)

    def test_path_ctime_change_during_read_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'fixture.txt'
            path.write_bytes(b'abc')
            original = Path.lstat
            calls = 0
            def changed(p):
                nonlocal calls
                st = original(p)
                if p == path:
                    calls += 1
                    if calls >= 3:
                        return metadata(st, st_ctime_ns=st.st_ctime_ns + 1)
                return st
            with patch.object(Path, 'lstat', changed):
                with self.assertRaisesRegex(safe_io.ReviewError, 'changed during read'):
                    safe_io.read_regular(path)

    def test_windows_birthtime_substitution_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'fixture.txt'
            path.write_bytes(b'abc')
            original = os.fstat
            def changed(fd):
                st = original(fd)
                return metadata(st, st_birthtime_ns=(getattr(st, 'st_birthtime_ns', None) or 0) + 1)
            with patch.object(safe_io, 'WINDOWS_STAT', True), patch.object(safe_io.os, 'fstat', side_effect=changed):
                with self.assertRaisesRegex(safe_io.ReviewError, 'identity changed'):
                    safe_io.read_regular(path)

    def test_reparse_attribute_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'fixture.txt'
            path.write_bytes(b'abc')
            original = Path.lstat
            def marked(p):
                st = original(p)
                return metadata(st, st_file_attributes=0x400) if p == path else st
            with patch.object(Path, 'lstat', marked):
                with self.assertRaisesRegex(safe_io.ReviewError, 'reparse'):
                    safe_io.read_regular(path)


if __name__ == '__main__':
    unittest.main()
