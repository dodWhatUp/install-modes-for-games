# AI Efficiency Foundation — local source candidate 0.26.0-preview.1

**Implemented:** 2026-10-14
**Owner:** `dodWhatUp/install-modes-for-games`
**Base:** reviewed local R2 source `0.25.0-preview.2`
**Status:** source, packaging, native Windows/Tk and independent external stdio accepted; not production-installed, connected through a specific ChatGPT/Codex product UI, adopted into `main`, or game-tested

## What this slice implements

This slice adds a read-first AI foundation without changing the existing local
approval controller, request mailbox, journals, game recipes, keybind stores, or
installed profiles.

1. **Dual-era local MCP stdio.** The existing `2025-11-25` initialize lifecycle
   remains available. A separate stateless `2026-07-28` route supports
   per-request protocol metadata, `server/discover`, deterministic tool lists,
   cache metadata, required `resultType`, and packaged text resources.
2. **Stable result envelope.** Modern calls distinguish source, tests, package,
   installation, connection, execution, runtime, gameplay, and publication.
   Existing legacy calls keep their prior raw result shape.
3. **Focused packaged knowledge.** `game_tools_search` returns stable result IDs;
   `game_tools_fetch` retrieves one exact manifest-verified source. No arbitrary
   local path or whole-disk scan is accepted.
4. **Continuation tools.** `game_tools_resume`, `game_tools_changes`,
   `game_tools_status_batch`, and `game_tools_prepare_handoff` inspect existing
   jobs/requests, use self-contained read-only cursors, and prepare an in-memory
   sanitized capsule. They never replay, retry, resume, save, upload, or publish
   an operation.
5. **Typed blocker explanations.** `game_tools_explain_blocker` separates known
   effects from unknown effects and names the safe inspection action.
6. **Reuse of existing engines.** `game_tools_catalog` exposes the existing
   validated bundled catalog, and `game_tools_reports` inspects only summaries
   that were explicitly shared through the existing local route.
7. **MCP Resources.** Manifest-verified packaged Markdown/JSON sources are
   available through opaque `game-tools-knowledge://` URIs. Private runtime
   state is not a resource.

## Modern tool surface added in this slice

- `game_tools_status`
- `game_tools_search`
- `game_tools_fetch`
- `game_tools_resume`
- `game_tools_changes`
- `game_tools_explain_blocker`
- `game_tools_status_batch`
- `game_tools_catalog`
- `game_tools_reports`
- `game_tools_prepare_handoff`

The prior Hub, support-pack, mod-preview, proposal, and keybind tools remain
available. In modern mode their domain payload is wrapped in the same result
envelope; in legacy mode it is not changed.

## Safety and ownership boundaries

- No model approval, approval flag, or automatic execution was added.
- No arbitrary command, code, path, URL, game launch, input injection, capture,
  provider connection, download, cloud upload, or background listener exists.
- Search reads only text files listed in the sealed package manifest and checks
  their exact size and SHA-256 before indexing.
- Change cursors are self-contained read tokens, not sessions, permissions, or
  transaction handles.
- A timeout or unknown effect is inspected through the same handle and is never
  converted into an automatic retry.
- Git and Drive publication remain external owner operations.

## Protocol behavior

A modern request carries these fields in `params._meta`:

```json
{
  "io.modelcontextprotocol/protocolVersion": "2026-07-28",
  "io.modelcontextprotocol/clientCapabilities": {},
  "io.modelcontextprotocol/clientInfo": {
    "name": "example-client",
    "version": "1.0.0"
  }
}
```

A client may begin with `server/discover`. A legacy client begins with
`initialize` and `notifications/initialized` exactly as before. One stdio
process does not switch eras after the first request.

The implementation follows the official 2026-07-28 MCP specification for the
subset it exposes:

- <https://modelcontextprotocol.io/specification/2026-07-28/changelog>
- <https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning>
- <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
- <https://modelcontextprotocol.io/specification/2026-07-28/server/resources>

No Streamable HTTP server, authorization server, subscriptions stream, prompts,
tasks extension, or MCP App UI is included in this local slice.

## Result contract

The authoritative JSON Schema is
[`schemas/ai-result-envelope.schema.json`](../schemas/ai-result-envelope.schema.json).
A result includes:

```text
result_type / status / scope / revision / freshness
completion / evidence / effects / data
next_safe_actions / retry / privacy
```

A legacy historical receipt is adapted on read; its stored bytes are not
rewritten.

## Implemented source files

- `scripts/GameToolAIContracts.py`
- `scripts/GameToolAITools.py`
- `scripts/GameToolAIKnowledge.py`
- `scripts/GameToolAIFoundation.py`
- `scripts/GameToolAIModern.py`
- `schemas/ai-result-envelope.schema.json`
- `scripts/tests/Test-GameToolAIFoundation.py`
- `scripts/tests/Test-GameToolAIModern.py`

`GameToolAI.py` now uses the separated deterministic base tool registry and the
dual-era stdio router. `GameToolKeybindAI.py` reuses that same router and reports
the host version instead of a duplicated hard-coded version.


## Accepted after the source package was sealed

The exact Preview archive passed native Windows 11 ARM64 launcher, current-user shortcut, isolated-profile, Tk widget, scaling and clean-close acceptance. An independent external stdio client then exercised modern `2026-07-28` and legacy `2025-11-25`, including `search → fetch`, resources, resume, change cursor, batch status, in-memory handoff, a synthetic local proposal, local rejection and rejection readback. No approval or operation execution occurred. See the [sanitized report](AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md) and [structured receipt](AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.json).

## Not implemented by this slice

- Connection through a specific ChatGPT Desktop, Codex or other product UI. Independent external Windows stdio acceptance is complete.
- Goal-level plan DAG or staged multi-domain proposal bundle.
- Installed-state adapters for MO2, Vortex, RHI, Steam Input, reWASD, or Azeron.
- Planned-versus-installed diff, real transaction, upgrade, disable, or rollback.
- Remote MCP/plugin gateway or in-chat visual cards.
- Live crash companion, benchmark runner, recorder/player, or training module.

These remain later gated work. Packaging, regression, native Windows/Tk and an independent external stdio-client round trip are complete. Canonical branch review/adoption and a separate read-only installed-state adapter gate still precede any installed/game write adapter.
