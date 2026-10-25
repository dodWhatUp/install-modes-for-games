"""Dual-era local stdio MCP framing for Unified Game Tools.

Modern requests (2026-07-28) are stateless and carry per-request metadata.
Legacy requests (2025-11-25) retain the existing initialize lifecycle and raw
business payloads.  No HTTP listener, daemon, background queue, or new approval
path is introduced.
"""
from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from GameToolAIContracts import VERSION, output_schema
from GameToolAIFoundation import FoundationError, FoundationService
from GameToolAIKnowledge import KnowledgeError
from GameToolAITools import foundation_tools, validate_arguments
from game_mod_ops.safety import ModError

MODERN_PROTOCOL = "2026-07-28"
LEGACY_PROTOCOL = "2025-11-25"
SUPPORTED = [MODERN_PROTOCOL, LEGACY_PROTOCOL]
SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo"
PROTOCOL_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_KEY = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_KEY = "io.modelcontextprotocol/clientInfo"


class ModernEndpoint:
    def __init__(self, service, allow_requests=False, legacy_endpoint=None, source_root=None):
        self.service = service
        self.allow_requests = allow_requests
        self.multi_game = bool(getattr(service, "multi_game", False))
        if legacy_endpoint is None:
            import GameToolAI as host
            if hasattr(service, "keybinds"):
                from GameToolKeybindAI import Endpoint as KeybindEndpoint
                legacy_endpoint = KeybindEndpoint(service, allow_requests)
            else:
                legacy_endpoint = host.Endpoint(service, allow_requests)
        self.legacy = legacy_endpoint
        self.foundation = FoundationService(service, source_root=source_root)

    @staticmethod
    def _error(ident, code, message, data=None):
        error = {"code": code, "message": message}
        if data is not None:
            error["data"] = data
        return {"jsonrpc": "2.0", "id": ident, "error": error}

    @staticmethod
    def _server_meta():
        return {SERVER_INFO_KEY: {"name": "unified-game-tools", "version": VERSION}}

    def _validate_request(self, message):
        ident = message.get("id") if isinstance(message, dict) else None
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or \
                not isinstance(message.get("method"), str) or "id" not in message or \
                type(ident) not in (str, int):
            raise FoundationError("INVALID_REQUEST", "Invalid modern JSON-RPC request.")
        params = message.get("params", {})
        if not isinstance(params, dict):
            raise FoundationError("INVALID_ARGUMENTS", "Modern request params must be an object.")
        meta = params.get("_meta")
        if not isinstance(meta, dict):
            raise FoundationError("MISSING_PROTOCOL_METADATA", "Modern requests require per-request _meta.")
        version = meta.get(PROTOCOL_KEY)
        if version != MODERN_PROTOCOL:
            error = FoundationError("UNSUPPORTED_PROTOCOL_VERSION", "Unsupported protocol version.")
            error.requested = version
            raise error
        if not isinstance(meta.get(CLIENT_CAPABILITIES_KEY), dict):
            raise FoundationError("MISSING_CLIENT_CAPABILITIES", "Modern requests require client capabilities.")
        client = meta.get(CLIENT_INFO_KEY)
        if client is not None and (not isinstance(client, dict) or not isinstance(client.get("name"), str) or not isinstance(client.get("version"), str)):
            raise FoundationError("INVALID_CLIENT_INFO", "Invalid modern client identity.")
        return ident, params, meta

    def definitions(self):
        import GameToolAI as host
        definitions = [] if getattr(self.service, "keybind_only", False) else host.tools(self.allow_requests, self.multi_game)
        if hasattr(self.service, "keybinds"):
            from GameToolKeybindAI import extra_tools
            definitions += extra_tools(self.allow_requests, self.multi_game)
        definitions += foundation_tools(self.multi_game)
        envelope_schema = output_schema()
        result = []
        seen = set()
        for definition in definitions:
            item = deepcopy(definition)
            if item["name"] in seen:
                continue
            seen.add(item["name"])
            item["outputSchema"] = deepcopy(envelope_schema)
            result.append(item)
        return sorted(result, key=lambda item: item["name"])

    def _dispatch(self, name, args):
        definitions = {item["name"]: item for item in self.definitions()}
        if name not in definitions:
            raise FoundationError("CAPABILITY_UNAVAILABLE", "Tool is unavailable in this modern endpoint.")
        validate_arguments(definitions[name], args)
        if name.startswith("game_tools_"):
            return self.foundation.call(name, args), False
        try:
            if name.startswith("keybinds_"):
                if not hasattr(self.legacy, "call_keybind"):
                    raise FoundationError("CAPABILITY_UNAVAILABLE", "This endpoint has no keybind service.")
                value = self.legacy.call_keybind(name, args)
            else:
                value = self.legacy.call(name, args)
            return self.foundation.wrap_legacy(name, value, failed=False), False
        except (FoundationError, KnowledgeError, ModError, ValueError, OSError, TypeError, KeyError) as error:
            code = getattr(error, "code", "REFUSED")
            value = {"status": code, "message": "Inspect the current local state; no automatic retry or alternate executor was used."}
            return self.foundation.wrap_legacy(name, value, failed=True), True

    def handle(self, message):
        ident = message.get("id") if isinstance(message, dict) else None
        try:
            ident, params, _ = self._validate_request(message)
        except FoundationError as error:
            if error.code == "UNSUPPORTED_PROTOCOL_VERSION":
                return self._error(ident, -32022, "Unsupported protocol version", {
                    "supported": SUPPORTED, "requested": getattr(error, "requested", None),
                })
            code = -32602 if error.code in {"INVALID_ARGUMENTS", "MISSING_PROTOCOL_METADATA", "MISSING_CLIENT_CAPABILITIES", "INVALID_CLIENT_INFO"} else -32600
            return self._error(ident, code, str(error))
        method = message["method"]
        clean = {key: value for key, value in params.items() if key != "_meta"}
        if method == "server/discover":
            if clean:
                return self._error(ident, -32602, "server/discover accepts only request metadata.")
            result = {
                "resultType": "complete",
                "supportedVersions": SUPPORTED,
                "capabilities": {"tools": {"listChanged": False}, "resources": {"listChanged": False}},
                "instructions": (
                    "Use game_tools_search before game_tools_fetch. Reads and previews are evidence only. "
                    "Proposals require exact local review; no model approval, game launch, input injection, capture, or arbitrary paths exist."
                ),
                "ttlMs": 3600000,
                "cacheScope": "private",
                "_meta": self._server_meta(),
            }
        elif method == "tools/list":
            if set(clean) - {"cursor"} or clean.get("cursor") not in (None, ""):
                return self._error(ident, -32602, "This bounded deterministic tool list does not require pagination.")
            result = {
                "resultType": "complete", "tools": self.definitions(),
                "ttlMs": 300000, "cacheScope": "private", "_meta": self._server_meta(),
            }
        elif method == "tools/call":
            if set(clean) - {"name", "arguments"} or not isinstance(clean.get("name"), str):
                return self._error(ident, -32602, "Invalid tool call.")
            try:
                value, failed = self._dispatch(clean["name"], clean.get("arguments", {}))
            except (FoundationError, KnowledgeError, ModError, ValueError, OSError, TypeError, KeyError) as error:
                value = self.foundation.blocker(getattr(error, "code", "INVALID_ARGUMENTS"))
                failed = True
            result = {
                "resultType": "complete",
                "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, allow_nan=False)}],
                "structuredContent": value, "isError": failed,
                "_meta": self._server_meta(),
            }
        elif method == "resources/list":
            if set(clean) - {"cursor"}:
                return self._error(ident, -32602, "Invalid resource-list arguments.")
            try:
                value = self.foundation.knowledge.list_resources(clean.get("cursor"))
            except KnowledgeError:
                return self._error(ident, -32602, "Invalid resource cursor.")
            result = {
                "resultType": "complete", **value,
                "ttlMs": 300000, "cacheScope": "private", "_meta": self._server_meta(),
            }
        elif method == "resources/read":
            if set(clean) != {"uri"} or not isinstance(clean.get("uri"), str):
                return self._error(ident, -32602, "A resource URI is required.")
            try:
                value = self.foundation.knowledge.read_resource(clean["uri"])
            except KnowledgeError:
                return self._error(ident, -32602, "Resource not found", {"uri": clean.get("uri")})
            result = {
                "resultType": "complete", "contents": value["contents"],
                "ttlMs": 60000, "cacheScope": "private", "_meta": self._server_meta(),
            }
        else:
            return self._error(ident, -32601, "Method not found")
        return {"jsonrpc": "2.0", "id": ident, "result": result}


class DualEndpoint:
    """Select one protocol era from the first request and keep it stable."""
    def __init__(self, service, allow_requests=False, source_root=None):
        import GameToolAI as host
        if hasattr(service, "keybinds"):
            from GameToolKeybindAI import Endpoint as KeybindEndpoint
            legacy = KeybindEndpoint(service, allow_requests)
        else:
            legacy = host.Endpoint(service, allow_requests)
        self.service = service
        self.allow_requests = allow_requests
        self.source_root = source_root
        self.legacy = legacy
        self.modern = None
        self.era = None

    def _modern(self):
        if self.modern is None:
            self.modern = ModernEndpoint(
                self.service, self.allow_requests, self.legacy,
                source_root=self.source_root,
            )
        return self.modern

    @staticmethod
    def _looks_modern(message):
        # _meta also exists in legacy MCP (progress/tracing). It is not, on
        # its own, evidence that the client changed protocol eras.
        return isinstance(message, dict) and (
            message.get("method") == "server/discover" or
            isinstance(message.get("params"), dict) and isinstance(message["params"].get("_meta"), dict)
            and any(key in message['params']['_meta'] for key in (PROTOCOL_KEY,CLIENT_CAPABILITIES_KEY))
            and message['params']['_meta'].get(PROTOCOL_KEY) != LEGACY_PROTOCOL
        )

    def handle(self, message):
        if self.era is None:
            if isinstance(message, dict) and message.get("method") == "initialize":
                self.era = "legacy"
            elif self._looks_modern(message):
                self.era = "modern"
            else:
                ident = message.get("id") if isinstance(message, dict) else None
                return {"jsonrpc": "2.0", "id": ident, "error": {
                    "code": -32600,
                    "message": "Start with server/discover plus modern _meta, or initialize for the legacy protocol.",
                }}
        if self.era == "legacy":
            if self._looks_modern(message):
                ident = message.get("id") if isinstance(message, dict) else None
                return {"jsonrpc": "2.0", "id": ident, "error": {
                    "code": -32600, "message": "This stdio process already selected legacy protocol semantics.",
                }}
            if isinstance(message,dict) and isinstance(message.get('params'),dict) and '_meta' in message['params']:
                if not isinstance(message['params']['_meta'],dict):
                    return {'jsonrpc':'2.0','id':message.get('id'),'error':{'code':-32602,'message':'Request metadata must be an object.'}}
                message=deepcopy(message);message['params'].pop('_meta')
            return self.legacy.handle(message)
        if isinstance(message, dict) and message.get("method") in {"initialize", "notifications/initialized", "ping"}:
            ident = message.get("id")
            return None if "id" not in message else {"jsonrpc": "2.0", "id": ident, "error": {
                "code": -32601, "message": "Modern MCP is stateless; initialize and ping are not supported.",
            }}
        return self._modern().handle(message)
