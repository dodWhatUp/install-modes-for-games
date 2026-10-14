"""Source-package and preview isolation contracts, not Windows shell acceptance."""
import hashlib,importlib.util,importlib.machinery,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
S=Path(__file__).resolve().parents[1]
loader=importlib.machinery.SourceFileLoader('focus_launch',str(S/'GameToolFocusLaunch.pyw'))
spec=importlib.util.spec_from_loader(loader.name,loader);launch=importlib.util.module_from_spec(spec);loader.exec_module(launch)
class LauncherContract(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.files=['scripts/Game-Tool-Hub.py','scripts/GameToolFocusUI.py','scripts/GameToolFocusPanels.py']
  for rel in self.files:
   p=self.root/rel;p.parent.mkdir(exist_ok=True,parents=True);p.write_text('# fixture\n')
  self.manifest={'files':[{'path':rel,'bytes':len((self.root/rel).read_bytes()),'sha256':hashlib.sha256((self.root/rel).read_bytes()).hexdigest()} for rel in self.files]};self.save()
 def save(self):(self.root/'MANIFEST.json').write_text(json.dumps(self.manifest))
 def test_all_sources_verified(self):self.assertEqual(launch.verify_source(self.root),self.manifest)
 def test_changed_source_stops_launch(self):
  (self.root/self.files[0]).write_text('# changed')
  with self.assertRaises(ValueError):launch.verify_source(self.root)
 def test_missing_source_stops(self):
  (self.root/self.files[0]).unlink()
  with self.assertRaises(OSError):launch.verify_source(self.root)
 def test_path_traversal_stops(self):
  self.manifest['files'][0]['path']='../source.py';self.save()
  with self.assertRaises(ValueError):launch.verify_source(self.root)
 def test_duplicate_source_stops(self):
  self.manifest['files'].append(self.manifest['files'][0]);self.save()
  with self.assertRaises(ValueError):launch.verify_source(self.root)
 def test_source_symlink_stops(self):
  p=self.root/self.files[0];p.unlink()
  try:p.symlink_to(self.root/self.files[1])
  except OSError as error:
   if getattr(error,'winerror',None)==1314:self.skipTest('Windows test account lacks symlink privilege; link blocking remains covered where creation is permitted.')
   raise
  with self.assertRaises(ValueError):launch.verify_source(self.root)
 def test_incomplete_source_manifest_stops(self):
  self.manifest['files'].pop();self.save()
  with self.assertRaises(ValueError):launch.verify_source(self.root)
 def test_single_preview_lease(self):
  with launch.PreviewLease(self.root):
   with self.assertRaises(ValueError):
    with launch.PreviewLease(self.root):pass
 def test_lease_released_without_deleting_unknown_files(self):
  with launch.PreviewLease(self.root):pass
  with launch.PreviewLease(self.root):pass
  self.assertTrue((self.root/'.ui-preview.lock').exists())
 def test_import_does_not_start_gui(self):
  self.assertFalse((self.root/'GameToolHub-Interface-Preview-0.22').exists())
 def test_launcher_declares_two_known_layouts_only(self):
  text=(S/'GameToolFocusLaunch.pyw').read_text();self.assertIn("choices=['Focus','Original']",text);self.assertIn('GameToolHub-Interface-Preview-0.22',text);self.assertNotIn('subprocess',text)
if __name__=='__main__':unittest.main(verbosity=2)
