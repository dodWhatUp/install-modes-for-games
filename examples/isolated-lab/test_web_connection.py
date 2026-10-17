"""Local authority, duplicate action and failure/recovery behavior."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import guest_mcp
from prepare_web_connection import mcp_command
from web_mcp import Bridge, policy_mode


class WebTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.lab = Mock()
        self.lab.private = self.root
        self.lab.inside.side_effect = lambda path: Path(path).resolve()
        self.backend = Mock()
        self.backend.TOOLS = guest_mcp.TOOLS
        self.backend.REQUEST_SCHEMA = guest_mcp.REQUEST_SCHEMA
        self.backend.dispatch.return_value = Bridge.response({"ok": True, "result": {"text": "Guest Ω"}, "receipt": "private path"})
        self.policy = self.root / "policy.json"
        self.mode("read-only")
        self.bridge = Bridge(self.lab, self.backend, self.policy)

    def tearDown(self):
        self.temp.cleanup()

    def mode(self, value, dedicated=False):
        self.policy.write_text(json.dumps({"schema": 1, "mode": value, "dedicated_guest": dedicated}))

    def action(self, **changes):
        arguments = {"op": "process.run", "args": {"argv": ["echo", "hello"]}, "request_key": "request_unique_001"}
        arguments.update(changes)
        return self.bridge.dispatch("tools/call", {"name": "linux_action", "arguments": arguments})

    def test_read_only_discovery_and_runtime_enforcement(self):
        self.assertEqual({t["name"] for t in self.bridge.tools()}, {"lab_status", "linux_inspect"})
        with self.assertRaises(ValueError):
            self.action()
        self.backend.dispatch.assert_not_called()

    def test_vm_lifecycle_never_exposed_even_in_action_mode(self):
        self.mode("guest-actions", True)
        for name in ("lab_start_linux", "lab_stop_linux", "host_input"):
            with self.assertRaises(ValueError):
                self.bridge.dispatch("tools/call", {"name": name})
        self.backend.dispatch.assert_not_called()

    def test_shared_guest_cannot_enable_actions(self):
        self.mode("guest-actions")
        with self.assertRaises(ValueError):
            self.bridge.tools()

    def test_remote_argument_cannot_change_policy(self):
        with self.assertRaises(ValueError):
            self.action(mode="guest-actions", dedicated_guest=True)
        self.assertEqual(policy_mode(self.policy), "read-only")

    def test_same_key_and_payload_returns_once_after_bridge_restart(self):
        self.mode("guest-actions", True)
        first = self.action()
        self.bridge = Bridge(self.lab, self.backend, self.policy)
        self.assertEqual(self.action(), first)
        self.backend.dispatch.assert_called_once()
        self.assertNotIn("receipt", first["structuredContent"])

    def test_same_key_different_action_refused(self):
        self.mode("guest-actions", True)
        self.action()
        with self.assertRaises(ValueError):
            self.action(args={"argv": ["different"]})
        self.backend.dispatch.assert_called_once()

    def test_unknown_outcome_does_not_replay_after_restart(self):
        self.mode("guest-actions", True)
        self.backend.dispatch.side_effect = TimeoutError("private transport path")
        first = self.action()
        self.assertEqual(first["structuredContent"]["error"]["code"], "OUTCOME_UNKNOWN")
        self.bridge = Bridge(self.lab, self.backend, self.policy)
        self.assertEqual(self.action()["structuredContent"]["error"]["code"], "OUTCOME_UNKNOWN")
        self.backend.dispatch.assert_called_once()

    def test_nonzero_guest_result_remains_failure_without_replay(self):
        self.mode("guest-actions", True)
        self.backend.dispatch.return_value = Bridge.response({"ok": False, "error": {"code": "EXIT_NONZERO"}})
        self.assertTrue(self.action()["isError"])
        self.assertTrue(self.action()["isError"])
        self.backend.dispatch.assert_called_once()

    def test_local_disable_applies_to_cached_remote_catalog(self):
        self.mode("guest-actions", True)
        self.action()
        self.mode("disabled")
        with self.assertRaises(ValueError):
            self.action()
        self.backend.dispatch.assert_called_once()

    def test_invalid_keys_never_create_journal(self):
        self.mode("guest-actions", True)
        for key in (None, "../a", "x"*81, 123):
            with self.assertRaises(ValueError):
                self.action(request_key=key)
        self.assertFalse((self.root / "web-requests").exists())

    def test_unexpected_action_field_refused_before_submission(self):
        self.mode("guest-actions", True)
        with self.assertRaises(ValueError):
            self.action(host_command="arbitrary")
        self.assertFalse((self.root / "web-requests").exists())

    def test_corrupt_previous_record_is_never_replayed(self):
        self.mode("guest-actions", True)
        self.action()
        (self.root / "web-requests/request_unique_001.json").write_text("corrupt")
        with self.assertRaises(ValueError):
            self.action()
        self.backend.dispatch.assert_called_once()

    def test_command_preserves_space_and_unicode_without_host_shell(self):
        self.assertEqual(mcp_command([r"D:\Lab Space Ω\python.exe", "--config", r"D:\Lab Space Ω\private\config.json"]),
                         '"D:/Lab Space Ω/python.exe" "--config" "D:/Lab Space Ω/private/config.json"')
        for bad in ('file".py', "file\n.py", "file\0.py"):
            with self.assertRaises(ValueError):
                mcp_command([bad])


if __name__ == "__main__":
    unittest.main()
