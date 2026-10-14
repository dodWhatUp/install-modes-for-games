"""Goal-oriented tool definitions and legacy business dispatch.

Protocol framing lives elsewhere.  These definitions are deterministic and do
not create connections, files, proposals, or execution authority by themselves.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from GameToolAutomation import capabilities
from GameToolAIContracts import output_schema
from game_mod_ops.safety import require


def tool_definition(name, description, properties, required=(), *, write=False, output=None):
    value = {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object", "properties": deepcopy(properties),
            "required": list(required), "additionalProperties": False,
        },
        "annotations": {
            "readOnlyHint": not write, "destructiveHint": False,
            "idempotentHint": not write, "openWorldHint": False,
        },
    }
    if output is not None:
        value["outputSchema"] = deepcopy(output)
    return value


def base_tools(allow_requests=False, multi_game=False):
    result = [
        tool_definition("hub_capabilities", "List code-owned supported and unavailable operations.", {}),
        tool_definition(
            "hub_context",
            "Return bounded sanitized state; never raw logs, paths, secrets or screenshots.",
            {"known_revisions": {"type": "object", "additionalProperties": {"type": "string"}}},
        ),
        tool_definition(
            "mods_preview_plan",
            "Preview the trusted Kingmaker recipe without network or writes.",
            {
                "mode": {"type": "string", "pattern": "^[a-z][a-z0-9-]{0,47}$"},
                "selected": {"type": "array", "items": {"type": "string"}, "maxItems": 100},
            },
        ),
        tool_definition(
            "hub_request_status", "Read the receipt for one locally proposed request.",
            {"request_id": {"type": "string"}}, ["request_id"],
        ),
    ]
    if allow_requests:
        result.append(tool_definition(
            "hub_propose",
            "Create a proposal for LOCAL review; never approval or execution. Reuse request_id after uncertain submission.",
            {
                "operation": {"type": "string", "enum": capabilities()["requestable"]},
                "arguments": {"type": "object"}, "request_id": {"type": "string"},
            }, ["operation", "arguments", "request_id"], write=True,
        ))
    if multi_game:
        result.append(tool_definition("hub_games", "List registered game scopes and recipe availability.", {}))
        result.extend([
            tool_definition("games_support_schema", "Read the contract for creating game support data. No code execution.", {}),
            tool_definition(
                "games_support_validate", "Validate a proposed pack and preview changed sections; does not import it.",
                {"pack": {"type": "object"}}, ["pack"],
            ),
            tool_definition(
                "games_support_template", "Generate a data-only support template, not an installed capability.",
                {
                    "game_id": {"type": "string"}, "name": {"type": "string"},
                    "adapter": {"type": "string", "enum": ["umm", "smapi", "bepinex", "directory", "external"]},
                    "executable": {"type": "string"},
                }, ["game_id", "name"],
            ),
            tool_definition(
                "games_support_details", "Read the selected game support revision, layout and capability boundaries.",
                {"game_id": {"type": "string"}}, ["game_id"],
            ),
        ])
        for definition in result:
            name = definition["name"]
            schema = definition["inputSchema"]
            if name in {"hub_context", "mods_preview_plan", "hub_request_status", "hub_propose"}:
                schema["properties"]["game_id"] = {"type": "string"}
                if name != "hub_context":
                    schema["required"].append("game_id")
            if name == "mods_preview_plan":
                definition["description"] = "Preview a registered game recipe; no network or writes."
            if name == "hub_propose":
                schema["properties"]["operation"]["enum"] = ["mods.create_plan", "mods.download", "mods.stage"]
    return result


def validate_arguments(definition: dict[str, Any], args: Any) -> None:
    require(type(args) is dict, "INVALID_ARGUMENTS", "Arguments must be an object.")
    schema = definition["inputSchema"]
    require(
        not set(args) - set(schema["properties"]) and set(schema["required"]) <= set(args),
        "INVALID_ARGUMENTS", "Missing or unexpected tool arguments.",
    )


def dispatch_base(service, name, args, *, multi_game=False):
    if name == "hub_capabilities":
        value = capabilities()
        if multi_game:
            value = {
                **value,
                "requestable": ["mods.create_plan", "mods.download", "mods.stage"],
                "multi_game": True,
                "game_id_required": True,
                "read": [
                    "capabilities", "games", "context", "preview_plan", "request_status",
                    "support_schema", "support_validate", "support_template", "support_details",
                ],
            }
        return value
    if name == "hub_games":
        return {"games": service.games()}
    if name == "games_support_schema":
        return service.support_schema()
    if name == "games_support_validate":
        return service.validate_support(**args)
    if name == "games_support_template":
        return service.support_template(**args)
    if name == "games_support_details":
        return service.game_support(**args)
    if name == "hub_context":
        return service.context(**args)
    if name == "mods_preview_plan":
        return service.preview_plan(**args)
    if name == "hub_request_status":
        return service.request_status(**args) if multi_game else service.request_status(args["request_id"])
    return service.propose(**args)


def foundation_tools():
    out = output_schema()
    bounded_id = {"type": "string", "minLength": 1, "maxLength": 192}
    return [
        tool_definition(
            "game_tools_status", "Read one compact completion and capability summary.",
            {"game_id": bounded_id, "known_revision": {"type": "string", "pattern": "^[a-f0-9]{64}$"}},
            output=out,
        ),
        tool_definition(
            "game_tools_search", "Search allowlisted packaged knowledge and return stable result IDs before fetching content.",
            {
                "query": {"type": "string", "minLength": 1, "maxLength": 256},
                "scope": {"type": "string", "enum": ["all", "docs", "schemas", "templates", "preferences"]},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            }, ["query"], output=out,
        ),
        tool_definition(
            "game_tools_fetch", "Fetch one exact allowlisted search result by stable ID and revision.",
            {
                "result_id": bounded_id,
                "revision": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                "offset": {"type": "integer", "minimum": 0, "maximum": 100000},
                "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            }, ["result_id"], output=out,
        ),
        tool_definition(
            "game_tools_resume", "Summarize open work, unknown effects and the next safe action without replay.",
            {"game_id": bounded_id, "known_revision": {"type": "string", "pattern": "^[a-f0-9]{64}$"}},
            output=out,
        ),
        tool_definition(
            "game_tools_changes", "Return changed section IDs since a self-contained read-only cursor.",
            {"cursor": {"type": "string", "maxLength": 32768}, "game_id": bounded_id},
            output=out,
        ),
        tool_definition(
            "game_tools_explain_blocker", "Explain one typed refusal and the exact safe inspection step.",
            {"code": bounded_id, "handle": bounded_id}, ["code"], output=out,
        ),
        tool_definition(
            "game_tools_status_batch", "Inspect up to 32 existing request, plan, job or resource handles; never retries them.",
            {
                "handles": {
                    "type": "array", "minItems": 1, "maxItems": 32,
                    "items": {
                        "type": "object", "additionalProperties": False,
                        "required": ["kind", "id"],
                        "properties": {
                            "kind": {"type": "string", "enum": ["request", "keybind_plan", "job", "resource"]},
                            "id": bounded_id, "game_id": bounded_id,
                        },
                    },
                },
            }, ["handles"], output=out,
        ),
        tool_definition(
            "game_tools_catalog", "Search the bundled validated component catalog; planning only and no execution.",
            {
                "query_or_goal": {"type": "string", "minLength": 1, "maxLength": 256},
                "game_id": bounded_id,
                "limit": {"type": "integer", "minimum": 1, "maximum": 30},
            }, ["query_or_goal"], output=out,
        ),
        tool_definition(
            "game_tools_reports", "Inspect explicitly shared saved-report summaries; no new provider read or benchmark.",
            {
                "record_ids": {"type": "array", "maxItems": 16, "items": bounded_id},
                "metric": bounded_id,
            }, output=out,
        ),
        tool_definition(
            "game_tools_prepare_handoff",
            "Prepare one sanitized in-memory continuation capsule; no file, upload, publication or execution occurs.",
            {
                "game_id": bounded_id,
                "include": {
                    "type": "array", "maxItems": 5, "uniqueItems": True,
                    "items": {"type": "string", "enum": ["status", "resume", "changes", "capabilities", "knowledge"]},
                },
            }, output=out,
        ),
    ]
