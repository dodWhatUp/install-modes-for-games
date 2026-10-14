"""Modern 2026-07-28 and legacy MCP compatibility fixtures."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.dont_write_bytecode = True

import GameToolAI as host
from GameToolAIModern import DualEndpoint, MODERN_PROTOCOL
from GameToolAutomation import AutomationService
from GameToolAITestPackage import build_ai_test_package


class ModernProtocolContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.service = AutomationService(self.root / "private")
        self.package = build_ai_test_package(SCRIPTS.parent, self.root / "package")
        self.endpoint = DualEndpoint(self.service, False, source_root=self.package)
        self.meta = {
            "io.modelcontextprotocol/protocolVersion": MODERN_PROTOCOL,
            "io.modelcontextprotocol/clientCapabilities": {},
            "io.modelcontextprotocol/clientInfo": {"name": "fixture", "version": "1.0.0"},
        }

    def request(self, ident, method, **params):
        return self.endpoint.handle({
            "jsonrpc": "2.0", "id": ident, "method": method,
            "params": {"_meta": self.meta, **params},
        })

    def tool(self, ident, name, arguments=None):
        return self.request(ident, "tools/call", name=name, arguments=arguments or {})

    def test_discover_is_stateless_and_names_both_supported_eras(self):
        result = self.request(1, "server/discover")["result"]
        self.assertEqual(result["resultType"], "complete")
        self.assertEqual(result["supportedVersions"], ["2026-07-28", "2025-11-25"])
        self.assertIn("tools", result["capabilities"])
        self.assertIn("resources", result["capabilities"])
        self.assertEqual(result["cacheScope"], "private")

    def test_unsupported_version_is_typed(self):
        self.meta["io.modelcontextprotocol/protocolVersion"] = "1900-01-01"
        result = self.request(1, "server/discover")
        self.assertEqual(result["error"]["code"], -32022)
        self.assertIn(MODERN_PROTOCOL, result["error"]["data"]["supported"])

    def test_modern_request_requires_meta_and_client_capabilities(self):
        endpoint = DualEndpoint(self.service, source_root=self.package)
        result = endpoint.handle({"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {}})
        self.assertEqual(result["error"]["code"], -32602)
        bad = dict(self.meta)
        bad.pop("io.modelcontextprotocol/clientCapabilities")
        result = DualEndpoint(self.service, source_root=self.package).handle({
            "jsonrpc": "2.0", "id": 2, "method": "server/discover", "params": {"_meta": bad},
        })
        self.assertEqual(result["error"]["code"], -32602)

    def test_tools_are_deterministic_and_have_output_schema(self):
        first = self.request(1, "tools/list")["result"]
        second = self.request(2, "tools/list")["result"]
        self.assertEqual(first["tools"], second["tools"])
        names = [item["name"] for item in first["tools"]]
        self.assertEqual(names, sorted(names))
        self.assertIn("game_tools_search", names)
        self.assertIn("hub_context", names)
        self.assertTrue(all("outputSchema" in item for item in first["tools"]))
        self.assertEqual(first["resultType"], "complete")
        self.assertIn("ttlMs", first)

    def test_foundation_tool_returns_envelope(self):
        result = self.tool(1, "game_tools_search", {"query": "local approval", "limit": 2})["result"]
        self.assertFalse(result["isError"])
        value = result["structuredContent"]
        self.assertEqual(value["schema_version"], 1)
        self.assertEqual(value["result_type"], "read")
        self.assertFalse(value["privacy"]["paths_included"])
        self.assertNotIn(str(self.root), json.dumps(value))
        self.assertEqual(json.loads(result["content"][0]["text"]), value)

    def test_existing_tool_is_wrapped_only_for_modern_clients(self):
        result = self.tool(1, "hub_context")["result"]["structuredContent"]
        self.assertEqual(result["result_type"], "read")
        self.assertEqual(result["data"]["kind"], "ai_context")
        self.assertIn("completion", result)

    def test_proposal_enabled_modern_connection_creates_only_local_review_request(self):
        endpoint = DualEndpoint(self.service, True, source_root=self.package)
        request = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {
                "_meta": self.meta, "name": "hub_propose",
                "arguments": {
                    "operation": "mods.create_plan",
                    "arguments": {"mode": "real-time", "selected": ["unity-mod-manager"]},
                    "request_id": "modern-proposal-fixture",
                },
            },
        }
        result = endpoint.handle(request)["result"]
        value = result["structuredContent"]
        self.assertFalse(result["isError"])
        self.assertEqual(value["result_type"], "proposal")
        self.assertEqual(value["status"], "AWAITING_LOCAL_APPROVAL")
        self.assertEqual(value["effects"]["write"], ["local_proposal_mailbox"])
        self.assertFalse(self.service.mods_root.exists())
        self.assertEqual(self.service.request_status("modern-proposal-fixture")["status"], "AWAITING_LOCAL_APPROVAL")

    def test_prepare_handoff_tool_is_preview_only(self):
        result = self.tool(1, "game_tools_prepare_handoff", {"include": ["status", "knowledge"]})["result"]
        self.assertFalse(result["isError"])
        value = result["structuredContent"]
        self.assertEqual(value["result_type"], "preview")
        self.assertFalse(value["data"]["local_save_action"]["performed"])
        self.assertEqual(value["effects"]["write"], [])
        self.assertNotIn(str(self.root), json.dumps(value))

    def test_proposal_tool_not_present_in_read_only_connection(self):
        result = self.tool(1, "hub_propose", {})["result"]
        self.assertTrue(result["isError"])
        self.assertEqual(result["structuredContent"]["result_type"], "blocked")
        self.assertFalse(self.service.requests.exists())

    def test_resources_list_and_read(self):
        listed = self.request(1, "resources/list")["result"]
        self.assertEqual(listed["resultType"], "complete")
        self.assertTrue(listed["resources"])
        uri = listed["resources"][0]["uri"]
        read = self.request(2, "resources/read", uri=uri)["result"]
        self.assertEqual(read["resultType"], "complete")
        self.assertEqual(read["contents"][0]["uri"], uri)
        self.assertNotIn(str(self.root), json.dumps(read))

    def test_resource_not_found_is_invalid_params_not_empty(self):
        result = self.request(1, "resources/read", uri="game-tools-knowledge://000000000000000000000000")
        self.assertEqual(result["error"]["code"], -32602)
        self.assertNotIn("result", result)

    def test_initialize_and_ping_are_not_modern_methods(self):
        self.request(1, "server/discover")
        result = self.endpoint.handle({"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}})
        self.assertEqual(result["error"]["code"], -32601)

    def test_legacy_era_does_not_construct_modern_knowledge_index(self):
        with mock.patch("GameToolAIModern.ModernEndpoint", side_effect=AssertionError("modern should stay lazy")):
            endpoint = DualEndpoint(self.service, source_root=self.package)
            initialized = endpoint.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            self.assertIn("result", initialized)
            self.assertIsNone(endpoint.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
            result = endpoint.handle({
                "jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "hub_context", "arguments": {}},
            })
            self.assertEqual(result["result"]["structuredContent"]["kind"], "ai_context")

    def test_legacy_direct_endpoint_retains_raw_shapes_and_tool_count(self):
        endpoint = host.Endpoint(self.service)
        endpoint.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        endpoint.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools = endpoint.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})["result"]["tools"]
        self.assertEqual(len(tools), 4)
        value = endpoint.handle({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "hub_context", "arguments": {}},
        })["result"]["structuredContent"]
        self.assertEqual(value["kind"], "ai_context")
        self.assertNotIn("completion", value)

    def test_dual_endpoint_does_not_switch_era_mid_process(self):
        self.request(1, "server/discover")
        result = self.endpoint.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {}})
        self.assertEqual(result["error"]["code"], -32601)


    def test_modern_workspace_lists_keybind_and_foundation_tools_once(self):
        from GameToolGameWorkspaces import WorkspaceAI
        service = WorkspaceAI(self.root / "workspace")
        endpoint = DualEndpoint(service, False, source_root=self.package)
        result = endpoint.handle({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list",
            "params": {"_meta": self.meta},
        })["result"]
        names = [item["name"] for item in result["tools"]]
        self.assertIn("keybinds_context", names)
        self.assertIn("game_tools_resume", names)
        self.assertEqual(len(names), len(set(names)))

    def test_workspace_modern_surface_adds_readonly_planning_without_legacy_registration(self):
        from GameToolGameWorkspaces import WorkspaceAI
        service = WorkspaceAI(self.root / "workspace-planning")
        endpoint = DualEndpoint(service, False, source_root=self.package)
        tools = endpoint.handle({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list",
            "params": {"_meta": self.meta},
        })["result"]["tools"]
        names = {item["name"] for item in tools}
        expected = {
            "game_tools_instances", "game_tools_instance_inspect",
            "game_tools_plan_goal", "game_tools_conflicts",
        }
        self.assertTrue(expected <= names)
        self.assertFalse(any("register" in name for name in names))
        for item in tools:
            self.assertFalse({"path", "game_dir", "root", "directory"} &
                             set(item["inputSchema"]["properties"]))
        planned = endpoint.handle({
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {
                "_meta": self.meta, "name": "game_tools_plan_goal",
                "arguments": {"game_id": "pathfinder-kingmaker", "goal": "review-mods"},
            },
        })["result"]
        self.assertFalse(planned["isError"])
        self.assertEqual(planned["structuredContent"]["result_type"], "preview")
        self.assertEqual(planned["structuredContent"]["effects"]["write"], [])
        self.assertFalse((self.root / "workspace-planning/game-instances").exists())
        legacy = host.Endpoint(service)
        legacy.handle({"jsonrpc": "2.0", "id": 3, "method": "initialize", "params": {}})
        legacy.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
        legacy_names = {item["name"] for item in legacy.handle({
            "jsonrpc": "2.0", "id": 4, "method": "tools/list", "params": {},
        })["result"]["tools"]}
        self.assertFalse(expected & legacy_names)

    def test_modern_stdio_has_one_json_response_per_request(self):
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "server/discover", "params": {"_meta": self.meta}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {"_meta": self.meta}},
        ]
        output = io.BytesIO()
        host.stdio(
            self.service,
            input_stream=io.BytesIO(b"\n".join(json.dumps(row).encode() for row in messages) + b"\n"),
            output_stream=output,
            source_root=self.package,
        )
        rows = [json.loads(row) for row in output.getvalue().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["result"]["resultType"] == "complete" for row in rows))


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ModernProtocolContracts)
    )
    raise SystemExit(not result.wasSuccessful())
