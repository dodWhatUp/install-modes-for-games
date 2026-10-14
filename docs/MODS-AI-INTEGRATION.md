# Unified Game Tools — Mods and AI integration

Source integration: **Hub 0.21.0-preview.1**, 2026-10-13. Existing Studio remains
**2.2.0-unified.10** and Game Input remains **0.5-preview.3**, with every native
AHK source retained byte-for-byte. This preview is NOT deployed on the gaming PC.

## What is complete

The real `Game-Tool-Hub.py` now mounts **Mods** and **AI & automation** as additive
workspaces. Modern goals/search, Classic tabs, existing status/identification
controls and the normal close dispatcher know about them. Original pages, callback
owners, native mappings, reports, overlays and current private settings are not
replaced. Module construction opens no network connection and creates no job.

The generic `game_mod_ops` engine is reused rather than rewritten. A single
Kingmaker recipe is packaged at `examples/game-tool-hub/mod-recipes/pathfinder-kingmaker.json`.
It is the runtime source of recipe data; the older `games/.../MOD-WORKFLOW.json`
location belongs to the preceding standalone delivery. The relocation keeps this
package compatible with the **existing unmodified updater's source allowlist**.
The broader per-game history/catalog remains with its established owner.

The same receipt-backed jobs can be used from the Mods pane, the structured CLI,
and approved AI requests. The model does not need to drive a mouse to submit a
supported request, and copying context does not take screenshots.

## Start in the existing app

1. Use the existing **Updates** workflow to inspect this ZIP and its exact SHA-256.
   Preserve current settings/source recovery and stop the app's owned Studio through
   its existing normal close path before applying. Do not extract over the active
   installation or force a stopped/unknown transaction. This turn did not apply it.
2. Open **Mods** (or **Prepare my game mods**). Choose the real-time or turn-based
   Kingmaker preset. Create the plan, then explicitly download or import the original
   archives. **Stage** means private preparation, not installation.
3. Open **AI & automation** (or **Work with AI safely**). Use **Copy AI context** or
   **Save AI context**. Only selected saved-report summaries and explicitly shared
   tool status join that context; original reports are not automatically exposed.
4. To use a compatible local MCP client, press **Copy client setup** on the actual
   computer. It supplies that installation's interpreter, script and data-root paths.
   `pythonw.exe` is replaced with its existing console `python.exe` sibling for stdio;
   no interpreter is installed. The checkbox can include proposal submission.
   Paste this private configuration into a client that supports local stdio servers.
   It is not automatically connected to ChatGPT web or any other client.
5. Requests appear in the shared local proposal mailbox. Refresh manually, or enable
   the optional refresh switch while the app is open. Select a request, inspect it,
   and **Approve selected** or **Reject selected**. **Arrival never means execution**.

The generated client configuration contains private machine paths. Do not publish
it or confuse it with the path-free AI context packet. No API key, model subscription,
external AI call, client installation or background service is required for the local
code. External-client setup/acceptance is a separate step.

## Implemented control and information routes

| Route | Actual behavior | Boundary |
|---|---|---|
| Capabilities / context | Code-owned capability list and bounded, section-hashed snapshots; unchanged sections can be omitted | No arbitrary filesystem/read paths from AI; no claim of live performance |
| `mods.create_plan` | Create an immutable job using the reviewed recipe and selected IDs | Local approval; no download or install |
| `mods.download` | Use the existing provider adapters, original archive receipts and one plan | Local approval; max 128 MiB, 40 requests and 300 seconds; account/provider gates remain |
| `mods.stage` | Validate and stage up to 16 named mods from that job | Local approval; no game-file write |
| `overlays.select` / `overlays.auto` | Select an existing game/group or return its selection to Auto through the existing Store | Exact current-store hash; no remapping, new trigger, display enablement or input |
| Share report summary | Reuse the existing Cyberpunk-summary/PresentMon-stats parser and publish only fixed metric fields and coverage locally | Original bytes/path/raw settings stay with Reports; no newly calculated metrics |
| Share tool status | Project known stock tool IDs, installed/running states, file versions and original observation time from the Hub's already-read status | No additional provider/process polling; custom names, paths, PIDs and sensor samples excluded |

The AI transport exposes four read tools plus optional proposal submission. It has
**no approval/execute tool**. Mod installation and rollback remain the separate
existing guarded `Game-Mod-Ops.py` operator interface. No arbitrary shell, keyboard
input, game launch, driver, benchmark, recording or third-party-manager execution
is exposed through the AI boundary. RHI/Vortex/MO2 remain catalog/handoff candidates,
not falsely implemented universal automation adapters.

## Shared implementation rather than duplicate subsystems

`GameToolModIntegration.py` mounts existing panes and extends the host's navigation
registry with stable routes without changing its original IDs. `UI-408` and `UI-409`
are new feedback IDs; GT requirement IDs are retained. Explicit widget-role objects
avoid traversing tkinter's mutable internal child dictionaries.

`GameToolAutomation.py` uses **GameToolJournal** for approval intent/results,
**GameToolOverlay.Store** for optimistic-concurrency updates,
**GameToolReportImport** for provider-defined metrics, and **game_mod_ops.Job** for
all mod operations. No replacement sensor collector or low/latency calculator exists.
`GameToolAutomationPanel.py` reuses **FlowToolbar**, **ScrollableFrame** and
**TableLayout**. GUI and CLI receive the same results rather than independent caches.

The proposal mailbox under the existing private Hub data root is short-lived runtime
transport, not a second project task queue, research master or synchronization owner.
`mod-workflows/jobs/` is the existing operation ledger; `automation/requests/` holds
bounded proposals/receipts; `automation/shared-reports/` and `automation/shared-tool-status/`
hold only explicitly selected summaries. Source releases do not contain these folders.
The native selected-file backup feature can preserve these private records as needed;
its existing per-file/total limits still apply. There is no automatic cloud backup or
automatic deletion/retention cleaner in this preview.

## Approval, concurrency, failure and privacy

Every request has a stable caller ID, exact body hash, recipe revision and 15-minute
expiry. Downloads/staging bind the current job revision; overlay actions bind the
current store revision. Repeated IDs return existing status, while conflicting IDs,
stale state, expired approval, recipe drift or a changed receipt are refused.
The model cannot set an `approved` field or choose code to execute.

A journal intent is durably written before effects. An interrupted/unknown attempt
is never automatically replayed. Complete receipts are checked against the verified
journal's result hash and terminal record. Provider waits are shown as pending items,
not a successful download batch. The existing provider code stops on access denial,
rate limiting, unsafe redirects and integrity problems; this layer does not reroute them.

The Mods and AI panes block each other's active mutations. **Stop** requests cooperative
cancellation at a bounded network/staging boundary; it does not kill unrelated tools.
The UI clears the cancellation flag before starting its worker, so a subsequent Stop
cannot be lost through a worker-side reset. Closing during active work requests
cancellation and keeps the window available for the returned result. No background
continuation or chat wake-up is promised.

Tool output is data/evidence, not authority. Hashes detect drift, not trusted authorship
or malware. This is a local-user trust boundary, not an OS sandbox against another
program with the same filesystem/process privileges. The stdio subprocess is started
only by an explicitly configured local client, opens no listening port and supports
a bounded MCP tools subset at protocol `2025-11-25`. It is not a full protocol-conformance
or deployed-client certification. The session is capped at 256 requests / 64 KiB per
input line. Separate message results and errors remain machine-readable JSON.

## Evidence, provenance and preservation

Verified source baseline: the 150-file **0.20.2 source-and-continuation** package,
754,278 bytes, SHA-256
`c4c8eafc63731f822611e51fa532eca3873d3d5d8c73afd17388a45e97fd942e`.
Its complete original manifest is retained as `MODS-AI-BASELINE-MANIFEST.json`.
The prior standalone module's manifest is `MODS-AI-MODULE-BASELINE-MANIFEST.json`.
Both input archives and their extracted baseline directories remain unmodified.

Validation and exact preservation counts are recorded in `MODS-AI-VALIDATION.json`
and `MODS-AI-SOURCE-DELTA.json`. Tests use synthetic local game/provider data and
headless Tk widgets. No screenshots, host input, live provider transfer, Windows
installation or AHK execution is represented by these tests. The previous source's
707 native focused checks remain historical; they were not rerun or counted here.

A few test harnesses were updated for the two added tabs, explicit optional closure
state, Windows virtual-key semantics under Linux, keeping test roots withdrawn,
and loading the unchanged `.pyw` bootstrap through a standard source loader on Linux.
Original safety/preservation assertions are retained. PowerShell-dependent tests
cannot execute in this container; their missing-runtime results are not passes.

## Remaining work and recommended next slices

**First: scoped Windows update and acceptance.** Verify current installed/source
state and active owners, inspect this package through the existing updater, preserve
private data, then confirm original Studio, both new routes, normal shutdown, and
real provider authorization/download behavior. Current tool access exposes the Mac,
not the Windows gaming PC. No new installed version is claimed.

**Next: supported manager adapters.** Add one product's versioned API/export/import
adapter at a time. Extend the existing typed action registry and consent/receipt path,
not UI-click scripts that bypass manager ownership. Priorities are a UMM loader
status/import handoff, then RHI metadata/read-only status and supported profile controls.
Existing-mod upgrades require three-way settings preservation and dedicated rollback
acceptance before enabling mutation. No upgrade promise is inferred from download support.

**Later: bounded delegated sessions.** A user could approve a named recipe and total
budget once, with cancellation and result review shared across modules. This version
requires a local approval per request; standing automatic approvals, wake-up mechanisms,
remote HTTP service, screen analysis and live benchmark/input actions remain unimplemented.
Use established providers and existing GT gates for any such extension.

## Publication boundary

The source candidate is delivered privately through the established Drive route.
GitHub main remains the older `b6a460f073e763a57a6d988bf5fbffa34e2e8946` baseline.
A prior Git write and remote-Mac operation were blocked by platform checks; neither
was retried or bypassed here. Newest-source discovery is now RESOLVED; publishing
this source and accepting a Windows deployment are separate unresolved boundaries.
Do not overwrite the owner's newer local work or claim full synchronization.

## Primary technical references

- MCP stdio transport: https://modelcontextprotocol.io/specification/2025-11-25/basic/transports
- MCP tools: https://modelcontextprotocol.io/specification/2025-11-25/server/tools
- Nexus API: https://api-docs.nexusmods.com/
- Existing module author/download sources are retained in the Kingmaker recipe and `MOD-WORKFLOWS.md`.

The adapter is authored against the referenced bounded protocol behavior. These
references do not grant account access or permission to install/download anything.
