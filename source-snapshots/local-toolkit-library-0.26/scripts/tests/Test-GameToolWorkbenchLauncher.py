"""Local source/launcher contracts, not native Windows or Start-menu acceptance."""
import hashlib,importlib.machinery,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
S=Path(__file__).resolve().parents[1];sys.path.insert(0,str(S));sys.dont_write_bytecode=True
loader=importlib.machinery.SourceFileLoader('workbench_launch',str(S/'GameToolWorkbenchLaunch.pyw'))
spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
class LauncherTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  paths=['Game-Tool-Hub.py','GameToolFocusUI.py','GameToolFocusPanels.py','GameToolWorkbench.py','GameToolGameWorkspaces.py','GameToolWorkbenchLaunch.pyw','GameToolAI.py','GameToolFocusLaunch.pyw','game_mod_ops/support.py','game_mod_ops/definitions.py','game_mod_ops/managers.py','game_mod_ops/handoff.py']
  self.rows=[]
  for name in paths:
   p=self.root/'scripts'/name;p.parent.mkdir(exist_ok=True,parents=True)
   data=(S/name).read_bytes() if name=='GameToolFocusLaunch.pyw' else b'# harmless source fixture\n';p.write_bytes(data)
   self.rows.append({'path':'scripts/'+name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
  self.save()
 def save(self):(self.root/'MANIFEST.json').write_text(json.dumps({'files':self.rows}))
 def test_complete_package_verified(self):self.assertEqual(m.verify(self.root)[1]['files'],self.rows)
 def test_missing_workbench_manifest_member_refused(self):
  self.rows=[r for r in self.rows if not r['path'].endswith('GameToolWorkbench.py')];self.save()
  with self.assertRaises(ValueError):m.verify(self.root)
 def test_changed_backend_refused(self):
  (self.root/'scripts/GameToolGameWorkspaces.py').write_text('# changed')
  with self.assertRaises(ValueError):m.verify(self.root)
 def test_verify_only_creates_no_profile(self):
  with patch.object(m,'ROOT',self.root):self.assertEqual(m.main(['--verify-only']),0)
  self.assertFalse((self.root/m.PROFILE).exists())
 def test_shared_lease_excludes_second_ui(self):
  old,_=m.verify(self.root);data=self.root/'profile'
  with old.PreviewLease(data):
   with self.assertRaises(ValueError):
    with old.PreviewLease(data):pass
  with old.PreviewLease(data):pass
 def test_missing_game_support_core_refused(self):
  self.rows=[r for r in self.rows if not r['path'].endswith('game_mod_ops/support.py')];self.save()
  with self.assertRaises(ValueError):m.verify(self.root)
 def test_known_layouts_no_install_mode(self):
  with self.assertRaises(SystemExit):m.main(['--layout','Install'])

if __name__=='__main__':unittest.main(verbosity=2)
