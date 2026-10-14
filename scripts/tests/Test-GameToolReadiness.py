"""Authored mocks only; no live provider, game, benchmark or recording."""
from copy import deepcopy
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
def load(name):
    spec = importlib.util.spec_from_file_location('readiness_test_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
API, CORE = load('GameToolReadiness'), load('GameToolCoordinator')
P = json.loads((ROOT / 'examples/game-tool-hub/provider-health.example.json').read_text())
S = json.loads((ROOT / 'examples/game-tool-hub/scenario.example.json').read_text())
def raw(data):
    return json.dumps(data, ensure_ascii=False).encode('utf-8')


class Contracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='readiness-mock-'); self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name); self.source = self.folder / 'source.json'
        self.source.write_bytes(raw(S)); self.expected = hashlib.sha256(self.source.read_bytes()).hexdigest()

    def test_provider_mock_health_is_not_execution_or_runtime(self):
        result = API.plan_bytes(raw(P))
        self.assertEqual(result['status'], 'MOCK_HEALTHY')
        self.assertFalse(result['runtime_verification']); self.assertFalse(result['execution_authorized'])
        self.assertEqual(result['fg_preflight'], 'not_performed'); self.assertEqual(result['execution'], 'none')
        self.assertEqual(result['details']['last_record_age_ms'], 1000)
        self.assertEqual(result['details']['interval_min_ms'], 1000)

    def test_scenario_preparation_never_issues_fg_pass(self):
        result = API.plan_bytes(raw(S)); self.assertEqual(result['status'], 'PREPARED_NOT_AUTHORIZED')
        self.assertEqual(result['details']['duration_ms'], 60000)
        self.assertEqual(result['fg_preflight'], 'not_performed'); self.assertFalse(result['runtime_verification'])

    def test_summary_aliases_private_identifiers(self):
        p = deepcopy(P); p['provider']['id'] = 'PrivateIdentity'
        s = deepcopy(S); s['scenario_id'] = 'PrivateScenario'; s['phases'][0]['id'] = 'PrivatePhase'
        for data in (p, s):
            self.assertNotIn('Private', json.dumps(API.plan_bytes(raw(data))))

    def test_unknown_fields_commands_and_type_confusion_refused(self):
        for base in (P, S):
            for name in ('command', 'script', 'launch', 'permission'):
                data = deepcopy(base); data[name] = 'PRIVATE_COMMAND'
                with self.assertRaises(API.ReadinessError) as error: API.plan_bytes(raw(data))
                self.assertNotIn('PRIVATE_COMMAND', str(error.exception))
        for schema in (True, '1', 2, 0):
            data = deepcopy(P); data['schema_version'] = schema
            with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))

    def test_json_duplicates_nonfinite_empty_and_truncation_refused(self):
        for value in (b'', b'{}', b'{', b'{"schema_version":1,"schema_version":1}', b'{"x":NaN}', b'\xff', b' ' * (API.MAX_SOURCE_BYTES + 1), '[not bytes]'):
            with self.assertRaises(API.ReadinessError): API.plan_bytes(value)

    def test_nested_and_excessive_lists_refused(self):
        for mutate in (lambda d: d['stream'].update(records=[d['stream']['records'][0]] * 1025),
                       lambda d: d['provider'].update(capabilities=['capture'] * 65)):
            data = deepcopy(P); mutate(data)
            with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))

    def test_declared_cadence_unknown_remains_unavailable(self):
        data = deepcopy(P); data['stream']['records'] = []; data['stream']['expected_interval_ms'] = None
        report = API.plan_bytes(raw(data)); self.assertIsNone(report['details']['interval_min_ms'])
        self.assertIsNone(report['details']['last_record_age_ms']); self.assertIn('UNKNOWN_CADENCE', report['blockers'])

    def test_duplicate_phase_and_action_budget_refused(self):
        data = deepcopy(S); data['phases'].append(deepcopy(data['phases'][0]))
        with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))
        data = deepcopy(S); data['phases'][0]['actions'][1]['duration_ms'] = 60001
        with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))

    def test_stop_policy_and_unsafe_flags_refused(self):
        for key in ('on_focus_loss','on_provider_failure','on_memory_warning','on_cancel'):
            data = deepcopy(S); data['stop'][key] = False
            with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))
        for key in ('save_access','quest_changes','graphics_changes'):
            data = deepcopy(S); data['safety'][key] = True
            with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))

    def test_deadline_and_mode_action_refused(self):
        data = deepcopy(S); data['stop']['deadline_ms'] = 59999
        with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))
        for mode, action in (('builtin','camera_rotation'),('route_action','builtin_scene')):
            data = deepcopy(S); data['mode'] = mode; data['phases'][0]['actions'][1]['kind'] = action
            with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))

    def test_key_text_command_action_payloads_refused(self):
        for key in ('keys','text','command','executable','save_path'):
            data = deepcopy(S); data['phases'][0]['actions'][0][key] = 'PRIVATE'
            with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))

    def test_clock_domain_and_numeric_boolean_refused(self):
        for path, value in ((['clock','domain'],'utc'),(['clock','now_ms'],True),
                            (['stream','records',0,'sequence'],True),(['lifecycle','armed'],1)):
            data = deepcopy(P); cursor = data
            for key in path[:-1]: cursor = cursor[key]
            cursor[path[-1]] = value
            with self.assertRaises(API.ReadinessError): API.plan_bytes(raw(data))

    def test_future_schema_refused_without_implicit_migration(self):
        data = deepcopy(S); data['schema_version'] = 2
        with self.assertRaises(API.ReadinessError) as error: API.plan_bytes(raw(data))
        self.assertEqual(error.exception.code, 'SCHEMA_UNSUPPORTED')

    def test_latency_route_separates_endpoints_and_motion(self):
        for action in ('camera_rotation', 'camera_translation', 'hud', 'animation'):
            data = deepcopy(S); data['mode'] = 'route_action'
            data['phases'][0]['actions'][1]['kind'] = action
            data['measurement'].update(purpose='latency', endpoint='software_response', calibration='declared', meaningful_input=True)
            result = API.plan_bytes(raw(data)); self.assertEqual(result['status'], 'PREPARED_NOT_AUTHORIZED')
            data['measurement']['endpoint'] = 'physical_input_to_pixel'
            result = API.plan_bytes(raw(data)); self.assertFalse(result['runtime_verification'])
            self.assertEqual(result['details']['endpoint'], 'physical_input_to_pixel')

    def test_latency_without_input_or_calibration_blocked(self):
        data = deepcopy(S); data['measurement'].update(purpose='latency', endpoint='software_response', calibration='planned')
        result = API.plan_bytes(raw(data)); self.assertIn('NO_MEANINGFUL_INPUT', result['blockers'])
        self.assertIn('ENDPOINT_OR_CALIBRATION_UNPREPARED', result['blockers'])

    def test_source_read_is_bounded_pinned_and_inert(self):
        original = self.source.read_bytes()
        result = API.inspect_source(self.source, self.expected)
        self.assertEqual(result['source_sha256'], self.expected); self.assertEqual(self.source.read_bytes(), original)
        self.source.write_bytes(original + b' ')
        with self.assertRaises(API.ReadinessError): API.inspect_source(self.source, self.expected)

    def test_missing_directory_and_large_source_refused(self):
        for path in (self.folder / 'missing.json', self.folder):
            with self.assertRaises(API.ReadinessError): API.inspect_source(path)
        self.source.write_bytes(b' ' * (API.MAX_SOURCE_BYTES + 1))
        with self.assertRaises(API.ReadinessError): API.inspect_source(self.source)

    def test_save_new_private_scenario_retains_original_and_edits(self):
        data = deepcopy(S); data['revision'] = 2; data['repeat_count'] = 5
        output = self.folder / 'new.json'; original = self.source.read_bytes()
        receipt = API.save_scenario(self.source, output, raw(data), self.expected)
        self.assertEqual(json.loads(output.read_text()), data); self.assertEqual(self.source.read_bytes(), original)
        self.assertEqual(receipt['coverage'], 'private_scenario_contract_only')
        self.assertEqual(receipt['export_sha256'], hashlib.sha256(output.read_bytes()).hexdigest())
        self.assertFalse(receipt['restore_tested']); self.assertFalse(receipt['runtime_verification'])

    def test_incomplete_draft_can_be_saved_but_stays_blocked(self):
        data = deepcopy(S); data['declared_readback'] = None
        receipt = API.save_scenario(self.source, self.folder / 'partial.json', raw(data), self.expected)
        self.assertEqual(receipt['status'], 'BLOCKED')

    def test_save_no_overwrite_or_repository_write(self):
        for output in (self.source, ROOT / 'examples/game-tool-hub/scenario-new.json'):
            with self.assertRaises(API.ReadinessError): API.save_scenario(self.source, output, raw(S), self.expected)
        self.assertEqual(hashlib.sha256(self.source.read_bytes()).hexdigest(), self.expected)
        self.assertFalse((ROOT / 'examples/game-tool-hub/scenario-new.json').exists())

    def test_save_stale_source_or_missing_hash_refused(self):
        for digest in (None, 'x', '0' * 64):
            with self.assertRaises(API.ReadinessError): API.save_scenario(self.source, self.folder / 'new.json', raw(S), digest)
        self.assertFalse((self.folder / 'new.json').exists())

    def test_cannot_save_provider_or_unsafe_scenario(self):
        data = deepcopy(S); data['safety']['save_access'] = True
        for draft in (P, data):
            with self.assertRaises(API.ReadinessError): API.save_scenario(self.source, self.folder / 'new.json', raw(draft), self.expected)
        self.assertFalse((self.folder / 'new.json').exists())

    def test_clone_requires_a_pinned_scenario_original(self):
        self.source.write_bytes(raw(P)); digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        with self.assertRaises(API.ReadinessError): API.save_scenario(self.source, self.folder / 'new.json', raw(S), digest)
        self.assertFalse((self.folder / 'new.json').exists())

    def test_coordinator_fixed_readiness_journal_has_no_payload(self):
        c = CORE.Coordinator(); self.addCleanup(c.close); journal = self.folder / 'session.jsonl'
        c.start(journal); result = c.inspect_readiness(self.source, self.expected); c.finish()
        self.assertEqual(result['status'], 'PREPARED_NOT_AUTHORIZED')
        text = journal.read_text(); self.assertIn('readiness', text)
        self.assertNotIn('MockScenario', text); self.assertNotIn(str(self.source), text)
        self.assertNotIn('phase_preview', text)

    def test_coordinator_cancelled_and_expired_do_not_dispatch(self):
        clock = [0.0]; c = CORE.Coordinator(lifetime_seconds=1, clock=lambda: clock[0])
        self.addCleanup(c.close); c.start(self.folder / 'expired.jsonl'); clock[0] = 2.0
        with self.assertRaises(CORE.CoordinatorError): c.inspect_readiness(self.source)
        c = CORE.Coordinator(); self.addCleanup(c.close); c.start(self.folder / 'cancel.jsonl'); c.cancel()
        with self.assertRaises(CORE.CoordinatorError): c.inspect_readiness(self.source)

    def test_no_live_executor_imports_or_methods(self):
        tree = ast.parse((ROOT / 'scripts/GameToolReadiness.py').read_text())
        imports = {n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
        self.assertFalse(imports & {'subprocess', 'ctypes', 'socket', 'keyboard', 'pynput'})
        for name in ('launch', 'capture', 'run_scenario', 'dispatch'): self.assertFalse(hasattr(API, name))


def blocker_test(base, path, value, code):
    def test(self):
        data = deepcopy(base); cursor = data
        for key in path[:-1]: cursor = cursor[key]
        cursor[path[-1]] = value
        result = API.plan_bytes(raw(data)); self.assertEqual(result['status'], 'BLOCKED')
        self.assertIn(code, result['blockers']); self.assertFalse(result['runtime_verification'])
    return test


for name, path, value, code in (
    ('not_discovered', ['lifecycle','discovered'], False, 'NOT_DISCOVERED'),
    ('disconnected', ['lifecycle','connected'], False, 'DISCONNECTED'),
    ('approval_pending', ['lifecycle','approval'], 'pending', 'APPROVAL_PENDING'),
    ('approval_denied', ['lifecycle','approval'], 'denied', 'APPROVAL_DENIED'),
    ('approval_unknown', ['lifecycle','approval'], 'unknown', 'APPROVAL_UNKNOWN'),
    ('approved_not_started', ['lifecycle','process'], 'not_started', 'PROCESS_NOT_STARTED'),
    ('producer_exit', ['lifecycle','process'], 'exited', 'PROCESS_EXITED'),
    ('not_armed', ['lifecycle','armed'], False, 'NOT_ARMED'),
    ('cancelled', ['lifecycle','cancelled'], True, 'CANCELLED'),
    ('closed_stream', ['stream','closed'], True, 'STREAM_STOPPED'),
    ('partial_write', ['stream','complete_write'], False, 'PARTIAL_WRITE'),
    ('dropped_records', ['stream','dropped_records'], 1, 'DROPPED_RECORDS'),
    ('missing_fields', ['stream','missing_fields'], ['FrameTime'], 'MISSING_FIELDS'),
    ('no_output', ['stream','records'], [], 'INSUFFICIENT_RECORDS'),
    ('stale_output', ['clock','now_ms'], 13000, 'STALE_RECORDS'),
    ('wrong_target', ['stream','records',1,'target_id'], 'Other', 'CONTEXT_MISMATCH'),
    ('wrong_run', ['stream','records',1,'run_id'], 'Other', 'CONTEXT_MISMATCH'),
    ('wrong_phase', ['stream','records',1,'phase_id'], 'Other', 'CONTEXT_MISMATCH'),
    ('future_output', ['stream','records',1,'at_ms'], 11000, 'FUTURE_RECORD'),
    ('cadence_gap', ['stream','records',0,'at_ms'], 6000, 'CADENCE_GAP'),
    ('sequence_gap', ['stream','records',1,'sequence'], 3, 'SEQUENCE_GAP_OR_REORDER'),
    ('time_reorder', ['stream','records',1,'at_ms'], 7000, 'TIME_REORDER'),
    ('unknown_version', ['provider','version'], None, 'UNKNOWN_PROVIDER_VERSION'),
    ('no_capture_capability', ['provider','capabilities'], ['connect'], 'CAPTURE_CAPABILITY_UNDECLARED')):
    setattr(Contracts, 'test_provider_' + name, blocker_test(P, path, value, code))

for name, path, value, code in (
    ('unknown_workload', ['requested_workload','build'], None, 'UNKNOWN_WORKLOAD'),
    ('missing_readback', ['declared_readback'], None, 'READBACK_UNKNOWN_OR_MISMATCHED'),
    ('mismatched_settings', ['declared_readback','settings_sha256'], 'b'*64, 'READBACK_UNKNOWN_OR_MISMATCHED'),
    ('unknown_cache', ['cache','shader_cache'], 'unknown', 'CACHE_EVIDENCE_UNKNOWN'),
    ('missing_cache_source', ['cache','source_revision'], None, 'CACHE_EVIDENCE_UNKNOWN'),
    ('too_few_repeats', ['repeat_count'], 1, 'INSUFFICIENT_REPEATS'),
    ('unknown_provider', ['measurement','provider_id'], None, 'PROVIDER_OR_FRAME_CLASS_UNKNOWN'),
    ('unknown_frame_class', ['measurement','frame_class'], 'unknown', 'PROVIDER_OR_FRAME_CLASS_UNKNOWN'),
    ('latency_scope_mismatch', ['measurement','endpoint'], 'software_response', 'LATENCY_SCOPE_MISMATCH')):
    setattr(Contracts, 'test_scenario_' + name, blocker_test(S, path, value, code))


if __name__ == '__main__': unittest.main(verbosity=2)
