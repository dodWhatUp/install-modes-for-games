"""Source delivery contracts, not native installer or provider acceptance."""
import importlib.machinery,importlib.util,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];S=ROOT/'scripts';sys.path.insert(0,str(S));sys.dont_write_bytecode=True
from game_mod_ops.support import SupportRegistry,compose_recipe
from game_mod_ops.safety import digest
from GameToolUnified import inspect_directory

class DeliveryTests(unittest.TestCase):
 def package_manifest(self):
  p=ROOT/'MANIFEST.json'
  if not p.is_file():
   self.skipTest('Generated package MANIFEST.json is absent in a canonical repository checkout; Test-GameSourceExport.ps1 owns the repository export contract.')
  return json.loads(p.read_text(encoding='utf-8-sig'))
 def test_shipped_registry_and_derived_recipes_match(self):
  with tempfile.TemporaryDirectory() as t:
   r=SupportRegistry(Path(t)/'no-create');rows=r.rows();self.assertEqual(len(rows),6)
   for gid,v in rows.items():
    if v['pack']['recipe'] is not None:self.assertEqual(json.loads(r.recipe_path(gid).read_text()),compose_recipe(v['pack']))
   self.assertFalse((Path(t)/'no-create').exists())
 def test_existing_updater_directory_contract(self):
  self.package_manifest();out=inspect_directory(ROOT);self.assertEqual(out['manifest']['component_versions']['tool_hub'],'0.28.0-preview.1')
 def test_every_authored_member_matches_manifest(self):
  m=self.package_manifest();names=set()
  for row in m['files']:
   p=ROOT/row['path'];self.assertNotIn(row['path'],names);names.add(row['path'])
   self.assertEqual(p.stat().st_size,row['bytes']);self.assertEqual(digest(p),row['sha256'].lower())
  self.assertIn('scripts/game_mod_ops/support.py',names);self.assertIn('templates/GAME-SUPPORT.example.json',names)
  for required in ('scripts/GameToolKeybindIntegration.py','scripts/game_keybind_ops/core.py','scripts/tests/Test-GameToolKeybindMerge.py','scripts/tests/keybinds/test_schema_contract.py','schemas/game-pack.schema.json','docs/UI-AND-CONTENT-DESIGN.md','docs/keybinds/README.md','docs/keybinds/history/INTEGRATION-HANDOFF-B-0.2.0-preview.1.md','docs/keybinds/history/DEPENDENCY_PINS-B-0.2.0-preview.1.json','docs/KEYBINDS-MERGE-VALIDATION.json','scripts/GameToolInstances.py','scripts/GameToolPlanning.py','scripts/GameToolMO2Read.py','scripts/Game-Instances.py','scripts/tests/Test-GameToolPlanning.py','scripts/tests/Test-GameToolMO2Read.py','schemas/game-tools-goal-plan.schema.json','schemas/mo2-profile-state.schema.json','docs/AI-PLANNING-READONLY-SLICE.md','docs/MO2-READ-ADAPTER.md','docs/MO2-READ-ADAPTER-VALIDATION.json','docs/MO2-READ-ADAPTER-SOURCE-DELTA.json'):
   self.assertIn(required,names)
  optional={'docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md','docs/MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json'}
  references={m.get('mo2_windows_acceptance_reference'),m.get('mo2_windows_acceptance_json_reference')}
  if references==optional:
   self.assertTrue(optional<=names);self.assertIn('included',m['runtime_status'])
  else:
   self.assertEqual(references,{None});self.assertTrue(optional.isdisjoint(names));self.assertIn('pending',m['runtime_status'])
  actual={p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in p.parts and p.suffix!='.pyc'}
  self.assertEqual(actual,names,'Manifest must be the exact authored payload inventory.')
 def test_original_exporter_inventory_includes_all_pack_members(self):
  s=(S/'Export-GameTools.ps1').read_text(encoding='utf-8-sig').split('function Get-GameSourceHash')[0]
  declared=set(re.findall(r"'((?:scripts|docs|examples|templates|preferences|schemas|game-packs)/[^']+|AGENTS.md)'",s))
  m=self.package_manifest();missing={r['path'] for r in m['files']}-declared
  self.assertEqual(missing,set(),'Source exporter must include every delivered payload.')
 def test_changed_component_versions_match_exporter_parser(self):
  m=self.package_manifest()['component_versions']
  for key,path in [('tool_hub','Game-Tool-Hub.py'),('mod_ops','game_mod_ops/__init__.py'),('game_workspaces','GameToolGameWorkspaces.py'),
                   ('workbench','GameToolWorkbench.py'),('automation','GameToolAutomation.py'),('ai_transport','GameToolAI.py'),
                   ('instances','GameToolInstances.py'),('planning','GameToolPlanning.py'),('mo2_read','GameToolMO2Read.py'),('keybinds','GameToolKeybindIntegration.py')]:
   a=re.findall(r'^VERSION\s*=\s*"([^"]+)"\s*$',(S/path).read_text(),re.M);self.assertEqual(a,[m[key]])
 def test_cli_schema_is_nonmutating(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'no-create';r=subprocess.run([sys.executable,'-B',str(S/'Game-Support.py'),'--data-dir',str(p),'schema'],capture_output=True,text=True,timeout=8)
   self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)['kind'],'game_support_authoring_contract');self.assertFalse(p.exists())
 def test_cli_can_validate_and_register_new_data_only_game(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);p=root/'new.json';data=root/'state'
   cmd=[sys.executable,'-B',str(S/'Game-Support.py'),'--data-dir',str(data)]
   r=subprocess.run(cmd+['scaffold','--game-id','cli-game','--name','CLI Game','--output',str(p)],capture_output=True,text=True,timeout=8)
   self.assertEqual(r.returncode,0,r.stderr);sha=json.loads(r.stdout)['revision'];self.assertFalse(data.exists())
   r=subprocess.run(cmd+['import','--pack',str(p),'--reviewed-sha256',sha,'--confirm'],capture_output=True,text=True,timeout=8)
   self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'REGISTERED_NOT_INSTALLED')
   self.assertEqual(SupportRegistry(data).get('cli-game')['pack']['recipe'],None)

if __name__=='__main__':unittest.main(verbosity=2)
