"""Fixed CLI routes against temporary authored mocks only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / 'scripts/Game-Tool-Hub.py'


class CLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='readiness-cli-'); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name); self.source = self.folder / 'scenario.json'
        self.source.write_bytes((ROOT / 'examples/game-tool-hub/scenario.example.json').read_bytes())
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def run_cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(HUB), *map(str,args)], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, expected, result.stderr or result.stdout)
        return json.loads(result.stdout)

    def test_inspect_scenario_without_registry_or_launch(self):
        result = self.run_cli('readiness','inspect','--source',self.source)
        self.assertEqual(result['status'], 'PREPARED_NOT_AUTHORIZED'); self.assertFalse(result['runtime_verification'])
        self.assertEqual(list(self.folder.iterdir()), [self.source])

    def test_provider_mock(self):
        result = self.run_cli('readiness','inspect','--source',ROOT / 'examples/game-tool-hub/provider-health.example.json')
        self.assertEqual(result['status'], 'MOCK_HEALTHY')

    def test_unknown_context_blocked_exit_three(self):
        data = json.loads(self.source.read_text()); data['declared_readback'] = None; self.source.write_text(json.dumps(data))
        self.assertEqual(self.run_cli('readiness','inspect','--source',self.source,expected=3)['status'], 'BLOCKED')

    def test_malformed_exit_two_fixed_private_error(self):
        self.source.write_text('PRIVATE_BAD_DATA')
        result = self.run_cli('readiness','inspect','--source',self.source,expected=2)
        self.assertNotIn('PRIVATE_BAD_DATA', json.dumps(result)); self.assertFalse(result['valid'])

    def test_save_new_edited_scenario(self):
        data = json.loads(self.source.read_text()); data['revision'] = 2; data['repeat_count'] = 4
        draft = self.folder / 'draft.json'; draft.write_text(json.dumps(data)); output = self.folder / 'new.json'
        result = self.run_cli('readiness','save-scenario','--source',self.source,'--draft',draft,'--expected-sha256',self.digest,'--output',output)
        self.assertEqual(json.loads(output.read_text()), data); self.assertEqual(result['coverage'],'private_scenario_contract_only')

    def test_no_overwrite_and_stale_source(self):
        for digest in (self.digest, '0'*64):
            self.run_cli('readiness','save-scenario','--source',self.source,'--draft',self.source,'--expected-sha256',digest,'--output',self.source,expected=2)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.digest)

    def test_fixed_coordinator_journal(self):
        journal = self.folder / 'session.jsonl'
        result = self.run_cli('session','inspect-readiness','--source',self.source,'--expected-sha256',self.digest,'--journal',journal)
        self.assertEqual(result['session']['state'], 'finished'); self.assertFalse(result['action_result']['execution_authorized'])
        self.assertNotIn('MockScenario', journal.read_text())

    def test_journal_cannot_be_reused(self):
        journal = self.folder / 'session.jsonl'; journal.write_text('OLD')
        self.run_cli('session','inspect-readiness','--source',self.source,'--expected-sha256',self.digest,'--journal',journal,expected=2)
        self.assertEqual(journal.read_text(), 'OLD')

    def test_fixed_capabilities_no_runner(self):
        result = self.run_cli('session','capabilities'); self.assertIn('readiness', result['capabilities'])
        self.assertIn('benchmarks', result['unavailable']); self.assertIn('recording',result['unavailable'])


if __name__ == '__main__': unittest.main(verbosity=2)
