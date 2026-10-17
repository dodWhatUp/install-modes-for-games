import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import guest_agent
from guest_mcp import dispatch


class AgentGuards(unittest.TestCase):
    def test_path_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "work"
            root.mkdir()
            with self.assertRaises(guest_agent.RequestError):
                guest_agent.scoped_path("../secret", root)
            with self.assertRaises(guest_agent.RequestError):
                guest_agent.scoped_path(str(Path(temp) / "secret"), root)

    def test_schema_operation_and_deadline_rejected(self):
        for request in ({"schema": 1, "id": "1", "op": "host.input"},
                        {"schema": 1, "id": "1", "op": "system.status", "timeout_ms": 999999},
                        {"schema": 2, "id": "1", "op": "system.status"}):
            with self.assertRaises(guest_agent.RequestError):
                guest_agent.validate(request)

    def test_read_tool_cannot_mutate(self):
        with patch("guest_mcp.call") as transport:
            with self.assertRaises(ValueError):
                dispatch(None, "tools/call", {"name": "linux_inspect", "arguments": {
                    "op": "process.run", "args": {"argv": ["echo", "no"]}}})
            transport.assert_not_called()

    def test_stale_browser_session_cannot_act(self):
        agent = guest_agent.Agent()
        agent.page = object()
        agent.session = "current"
        with self.assertRaises(guest_agent.RequestError):
            agent.require_session({"session": "old"})

    def test_stale_desktop_session_never_connects(self):
        agent = guest_agent.Agent()
        agent.desktop_process = object()
        agent.desktop_session = "current"
        with patch("guest_agent.asyncio.open_unix_connection", create=True) as connect:
            with self.assertRaises(guest_agent.RequestError):
                asyncio.run(agent.desktop_call({"op": "desktop.act", "session": "old"}))
            connect.assert_not_called()

    def test_native_mutation_cannot_use_inspection_tool(self):
        with patch("guest_mcp.call") as transport:
            with self.assertRaises(ValueError):
                dispatch(None, "tools/call", {"name": "linux_inspect", "arguments": {
                    "op": "desktop.act", "args": {"action": "invoke"}}})
            transport.assert_not_called()

    def test_transport_failure_is_a_tool_error(self):
        with patch("guest_mcp.call", side_effect=RuntimeError("operation locked")):
            result = dispatch(None, "tools/call", {"name": "linux_inspect", "arguments": {"op": "system.status"}})
        self.assertTrue(result["isError"])
        self.assertFalse(result["structuredContent"]["ok"])

    def test_mcp_initialization_does_not_start_or_query_guest(self):
        with patch("guest_mcp.call") as transport:
            result = dispatch(None, "initialize", {"protocolVersion": "2025-06-18"})
            transport.assert_not_called()
        self.assertEqual(result["protocolVersion"], "2025-06-18")

    def test_different_live_worker_version_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp)
            sock = state / "agent.sock"
            sock.touch()
            with patch("guest_agent.STATE", state), patch("guest_agent.SOCKET", sock), \
                    patch("guest_agent.call_worker", return_value={"version": "0.1.0"}), \
                    patch("guest_agent.subprocess.Popen") as launch:
                with self.assertRaises(guest_agent.RequestError):
                    guest_agent.ensure_worker()
                launch.assert_not_called()
            self.assertTrue(sock.exists())

    def test_file_creation_never_replaces_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "selected.txt"
            path.write_text("baseline")
            with patch("guest_agent.scoped_path", return_value=path):
                with self.assertRaises(FileExistsError):
                    asyncio.run(guest_agent.Agent().dispatch({"op": "files.write", "args": {
                        "path": "selected.txt", "text": "replacement"}}))
            self.assertEqual(path.read_text(), "baseline")


if __name__ == "__main__":
    unittest.main()
