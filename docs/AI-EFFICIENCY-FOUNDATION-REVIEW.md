# AI Efficiency Foundation review — Unified Game Tools 0.26.0-preview.1

**Date:** 2026-10-14
**Canonical owner:** `dodWhatUp/install-modes-for-games`
**Base:** reviewed local R2 source `0.25.0-preview.2`
**Status:** adopted into canonical `main` by PR #7 / `cef163dee0bba0395611b1e3c15be972fa7db175` after independent review; not production-installed and no runtime acceptance was expanded by the merge

## Result

The first AI-efficiency implementation slice is now source-complete. It keeps the
existing automation, approval, journal, game-support and keybind owners, and adds a
separate read-first facade rather than replacing those engines.

Implemented capabilities:

1. A dual-era stdio endpoint: legacy `2025-11-25` remains byte-shape compatible;
   modern `2026-07-28` is stateless and uses per-request metadata.
2. One typed result envelope with distinct source, test, package, installation,
   connection, execution, runtime, gameplay and publication states.
3. Manifest-verified `search → fetch` over allowlisted packaged Markdown/JSON.
4. Opaque MCP resources for the same packaged knowledge, with no arbitrary path.
5. Compact status, resume, change-feed and bounded batch inspection.
6. Typed blocker explanations with explicit no-retry behavior for unknown effects.
7. Read-only access to the existing component catalog and explicitly shared report
   summaries.
8. A sanitized in-memory handoff capsule. The tool does not save, upload, publish or
   execute the capsule.
9. Modern wrapping for existing Hub, support-pack, mod-preview and keybind tools.
10. Lazy construction of the modern knowledge layer, so a legacy client does not
    acquire a new manifest dependency merely by opening its historical endpoint.

## Ownership preserved

| Stable owner | Preserved behavior |
|---|---|
| `GameToolAutomation` | Proposal mailbox, exact local approval and execution boundary |
| `GameToolJournal` | Existing immutable receipts and no-replay evidence |
| `GameToolGameWorkspaces` | Game scope, support recipes and service composition |
| `GameToolKeybindIntegration` | Keybind prepare/apply/readback/rollback operations |
| `GameToolAI.Endpoint` | Legacy protocol lifecycle and raw legacy result payloads |
| `GameToolAIModern` | New protocol framing only; no new execution authority |
| `GameToolAIKnowledge` | Read-only, manifest-sealed packaged knowledge |
| Git / Drive routes | Publication remains outside Game Tools |

## Public modern tools added

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

No approval, arbitrary command, arbitrary path, game launch, input injection,
recording, download, cloud credential, background server or unattended queue was
added.

## Design decisions

### Additive protocol adapter

Business tool definitions and dispatch were extracted from protocol framing. The
legacy endpoint remains directly testable. A dual endpoint selects one protocol era
from the first request and does not switch semantics mid-process.

### Focused context instead of full snapshots

Search returns snippets and stable IDs. Fetch returns only the requested source range
and exact revision. The source must appear in `MANIFEST.json`, be a regular non-link
file, match its declared length and SHA-256, and remain under an allowlisted source
category.

### Continuation without replay

Resume and batch status inspect existing handles. Change cursors are self-contained,
sealed read tokens, not sessions or authority. Unknown effects always return an
inspection route with `retry.allowed=false`.

### Handoff without another persistence owner

The handoff tool produces one deterministic sanitized capsule and content hash in
memory. A file export remains a separate local reviewed action, while Git and Drive
remain the canonical publication routes.

## Native Windows and external stdio acceptance

After the immutable source package was sealed, the exact Preview SHA-256 was transferred to an authorized Windows 11 ARM64 VM. Official per-user Python 3.12.10 ARM64 with Tk 8.6.15 was installed in that isolated test environment. Workbench and Original `VerifyOnly` passed without side effects; both native windows opened and closed normally; current-user shortcuts were created; the dedicated Preview profile was the only Game Tools profile changed. An in-process Tk audit verified the four Workbench tabs, Keybinds content, Stop/More controls, 100% → 200% → 100% scaling and clean close.

A separate external Windows stdio client exercised modern and legacy protocol paths. One synthetic proposal reached only `AWAITING_LOCAL_APPROVAL`, was rejected locally, and was read back as `REJECTED`; no operation was approved or executed. The first harness attempt used the wrong returned change-cursor field; its pending request was inspected and rejected before a new isolated run. See the [sanitized acceptance report](AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md).

The canonical repository test pass also makes its third-party test dependencies explicit in `scripts/tests/requirements.txt`: `jsonschema==4.26.0` validates result schemas and `Pillow==12.3.0` creates synthetic image fixtures. Neither is imported by the standard-library/Tk product runtime.

The source-checkout tests create a bounded ordinary-file package fixture with a generated temporary manifest. Production and CLI defaults still require the sealed package `MANIFEST.json`; no repository fallback, arbitrary path or unsigned runtime mode was added.

## Canonical branch seal

The reconciled R7 source passed its complete Windows focused gate and real PowerShell 5.1 export, then was committed as `42dc939bd37ff37e5af2cb429bce6d0aeb3eb29d` on `task/ai-efficiency-foundation-reconcile-20261014`. This commit is the immutable tested product-source boundary; later receipt updates are documentation-only. The branch is not merged into `main`.

## Deliberately deferred

- Connection through a specific ChatGPT/Codex product UI and remote plugin deployment.
- Goal-level multi-domain plan DAG and staged proposal bundle.
- Installed-state adapters for MO2, Vortex, RHI, Steam Input, reWASD or Azeron.
- Planned-versus-installed diffs and real install/upgrade/rollback transactions.
- Live crash companion, benchmark runner, recorder/player and training module.

Those are not required to accept this read-first foundation and would materially
increase risk if mixed into the same change.
