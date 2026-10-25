"""Atomic relay contention regression. No live store, hotkeys or input."""
from pathlib import Path
import sys, tempfile, unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api


def windows_error(code):
    error=OSError('synthetic Windows file contention')
    error.winerror=code
    return error


class RelayIOTests(unittest.TestCase):
    def test_brief_windows_contention_preserves_atomic_publication(self):
        for code in (5,32,33):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                dest=Path(temp)/'overlay-selection.ini'
                api.write_relay(dest,{'Schema':'1','Active':'0','ExpiresUnixMs':'1000'})
                before=dest.read_bytes(); replace=api.os.replace; calls=[]
                def contend(source,target):
                    self.assertEqual(dest.read_bytes(),before)
                    calls.append(source)
                    if len(calls)<3:raise windows_error(code)
                    return replace(source,target)
                with patch.object(api.os,'replace',side_effect=contend),patch.object(api.time,'sleep') as wait:
                    api.write_relay(dest,{'Schema':'1','Active':'1','ExpiresUnixMs':'2000'})
                self.assertEqual(len(calls),3)
                self.assertEqual([c.args[0] for c in wait.call_args_list],[.005,.01])
                self.assertIn(b'ExpiresUnixMs = 2000',dest.read_bytes())
                self.assertEqual(list(Path(temp).iterdir()),[dest])

    def test_persistent_lock_keeps_previous_complete_snapshot_and_cleans_temp(self):
        with tempfile.TemporaryDirectory() as temp:
            dest=Path(temp)/'overlay-selection.ini'
            api.write_relay(dest,{'Schema':'1','Active':'0','ExpiresUnixMs':'1000'})
            before=dest.read_bytes()
            with patch.object(api.os,'replace',side_effect=windows_error(32)) as replace,patch.object(api.time,'sleep') as wait:
                with self.assertRaises(OSError):
                    api.write_relay(dest,{'Active':'1','ExpiresUnixMs':'2000'})
            self.assertEqual(replace.call_count,5)
            self.assertAlmostEqual(sum(c.args[0] for c in wait.call_args_list),.05)
            self.assertEqual(dest.read_bytes(),before)
            self.assertEqual(list(Path(temp).iterdir()),[dest])

    def test_other_io_errors_are_not_retried(self):
        for error in [windows_error(2),OSError('non-Windows failure')]:
            with self.subTest(error=error),patch.object(api.os,'replace',side_effect=error) as replace,patch.object(api.time,'sleep') as wait:
                with self.assertRaises(OSError):api.replace_relay('source','target')
                self.assertEqual(replace.call_count,1)
                wait.assert_not_called()


if __name__=='__main__':unittest.main()
