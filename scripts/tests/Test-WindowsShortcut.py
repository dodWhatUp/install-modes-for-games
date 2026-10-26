"""Real ShellLink read/write over disposable owned files; never opens a GUI."""
import os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolWindowsShortcut import read,write
from GameToolWindowsApp import icon_path

@unittest.skipUnless(os.name=='nt','Native Windows ShellLink acceptance')
class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='game-tools-shell-test-');self.folder=Path(self.temp.name)
        self.path=self.folder/'Fictional game app.lnk'
        self.spec={'target':str(Path(sys.executable).with_name('pythonw.exe')),'arguments':'-B "fictional app.py" --context "a b"',
          'working_directory':str(self.folder),'description':'Owned fixture','icon':str(icon_path('unified').resolve()),'app_id':'GameTools.ShortcutFixture'}
    def tearDown(self):self.temp.cleanup()
    def test_new_shortcut_roundtrip_preserves_exact_arguments_and_identity(self):
        actual=write(self.path,**self.spec)
        for key,value in self.spec.items():self.assertEqual(actual[key],value)
        self.assertEqual(read(self.path),actual)
    def test_existing_shortcut_uses_writable_clone_and_preserves_original_until_commit(self):
        before=write(self.path,**self.spec);old=self.path.read_bytes()
        actual=write(self.path,**dict(self.spec,description='Updated icon label'),expected=before)
        self.assertEqual(actual['description'],'Updated icon label');self.assertNotEqual(self.path.read_bytes(),old)
        for key in ('target','arguments','working_directory','icon','app_id'):self.assertEqual(actual[key],before[key])
        self.assertEqual(list(self.folder.glob('*.pending-*')),[])
    def test_changed_baseline_is_rejected_without_touching_the_shortcut(self):
        before=write(self.path,**self.spec);raw=self.path.read_bytes()
        with self.assertRaises(ValueError):write(self.path,**self.spec,expected=dict(before,description='wrong baseline'))
        self.assertEqual(self.path.read_bytes(),raw)
    def test_failed_precondition_retains_existing_bytes(self):
        before=write(self.path,**self.spec);raw=self.path.read_bytes()
        with self.assertRaises(ValueError):write(self.path,**dict(self.spec,icon=str(self.folder/'missing.ico')),expected=before)
        self.assertEqual(self.path.read_bytes(),raw)

if __name__=='__main__':unittest.main(verbosity=2)
