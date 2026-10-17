# Integration with the existing gaming utility

**Current integration supersedes the source-location gap below:** see [Hub 0.21.0-preview.1](MODS-AI-INTEGRATION.md). The newest 0.20.2 source was found and the actual Hub source now mounts both workspaces. The following standalone 0.1.0 boundary is historical, not the current integration status.

## Historical standalone delivery

## Scope and current source boundary

Add a **Mods** capability to the existing Game Tool Hub architecture. Reuse its
host, tool catalog, authorization/session concepts, status surface and import/export
routes; retain the established providers for metrics and the native software for
input remapping. Do not replace the Hub with this source package.

The accessible canonical GitHub main was
`b6a460f073e763a57a6d988bf5fbffa34e2e8946`. It contains Hub 0.2.0 source and later
SPARSE6 documentation that records a separate **0.11.0** preview. The accessible
SPARSE6 recovery ZIP contains assets, settings and receipts, **not that app's source**.
No source matching the user's just-uploaded newest app was resolved in the bounded
GitHub/Drive/Project searches. Absence from those searches does not prove that no
new upload exists. See the source-resolution receipt for identities and coverage.

Therefore this change supplies tested module source and an explicit mounting seam,
not a claimed upgrade of 0.11.0 or any newer build. It does not edit or downgrade
old `scripts/Game-Tool-Hub.py`, replace the user's current app, merge unrelated
branches, resume input experiments, capture a screen or start a benchmark.

## Components

| Layer | Implementation / owner |
|---|---|
| Reusable operations | `scripts/game_mod_ops/`: recipe validation, bounded provider adapters, safe archives, local job receipts, UMM adapter |
| Agent interface | `scripts/Game-Mod-Ops.py`: structured JSON results for named operations; no arbitrary command endpoint |
| Optional user panel | `scripts/Game-Mod-Panel.py`, `game_mod_ops.panel.attach(...)` |
| Per-game knowledge | `examples/game-tool-hub/mod-recipes/pathfinder-kingmaker.json`; existing game catalog/history remain canonical for broader findings |
| Other-game template | `templates/MOD-WORKFLOW.example.json`; manager/source capabilities are explicit rather than presumed |
| Existing overlays/input/telemetry | Their existing source owners and settings, unchanged |

Private operation jobs live below the chosen Hub data root in their own module
namespace. This is a scoped execution journal, not a duplicate task queue or
replacement master database. The host may supply a private data root; do not put
jobs, downloads or recovery in a shared source directory.

## Source-level mounting seam

For a verified **Tk Notebook** host using Python 3.10+:

```python
from game_mod_ops.panel import attach
mods_pane = attach(existing_notebook, recipe_path=kingmaker_recipe_path,
                   data_root=private_hub_data_root / "mod-workflows")
# In the host's existing close dispatcher:
# if not mods_pane.can_close(): return
# Continue the original host cleanup only after the pane can close.
```

This adds one tab without removing the existing ones. The pane performs no
network or game operations on construction. The host must compose close/cancel
handling with its existing lifecycle, not replace the full close handler.
A non-Tk or older-Python host should reuse the CLI/operation service and implement
its own thin view; do not force a GUI framework migration or assume this seam was
already mounted in an unseen 0.11.0 source.

`examples/game-tool-hub/MOD-WORKFLOWS-CAPABILITIES.json` is a **declaration**, not
an autoload configuration for a presumed plugin API. Reconcile its identities with
the newest host's existing catalog once that source is available. Do not register
another manager for files already owned by UMM, Vortex, MO2 or RHI.

## Chat workflow

The chat reads the game's current recipe and recommendations, requests a plan,
then delegates only the authorized operation through the available local executor.
It reads the returned receipt before the next phase. It must not infer that a
Nexus key, remote desktop permission, Mod Manager Download click, install approval,
game launch or measurement permission exists merely because a recipe names it.

Download grouping and profile selection use the reviewed plan, not text scraped
from a web page. Keep signed links and credentials ephemeral. Add successful
provider/manager lessons to the existing game history, with exact versions,
observed outcome and remaining gaps; update reusable procedures only for genuinely
shared lessons. Do not rescan all past chats on each operation.

## Hook into the wider feature set

- **Dynamic overlays:** show sanitized phase/progress/status through the host's
  existing display path after integration. Do not repurpose native keys, infer
  physical SPARSE6 layers or replace registered overlay assets.
- **PC/input controls:** route only explicit supported actions through the existing
  executor; this module adds no global keyboard hooks or hidden input socket.
- **Performance comparisons:** record the exact mod/profile manifest as an input
  to a later run. Installing a mod must not trigger a benchmark. Existing providers
  still supply lows, latency, CPU/GPU/RAM/VRAM and definitions. Existing fixed-FG,
  memory and paired-workload gates continue to govern those tests.
- **Diagnosis:** start with inventory, dependency and file-drift evidence. Do not
  call drift corruption or blame a mod for a crash without relevant runtime evidence.
- **Updates:** compare metadata on use or under an already authorized job. A newer
  release is a candidate; pins, settings and working files do not change silently.

## Next acceptance gates

1. Resolve the **exact newest app source ZIP or Git commit/path** and its originating
   handoff. Compare source hashes and current catalog/lifecycle APIs; preserve all
   later work. A display/recovery ZIP is not an app source bundle.
2. Mount this module in an isolated copy of that version, run its full original
   test suite plus these contracts, check existing tabs/actions and verify that
   native profile/overlay/settings bytes remain unchanged.
3. On the authorized Windows target, validate process inventory and one official
   download without installing. Obtain Nexus authorization locally when needed.
4. Under explicit installation scope, test UMM bootstrap, one new mod, save-aware
   recovery and actual game/UMM behavior. Treat benchmarks/gameplay automation as
   separate later work, not implicit continuation of installation.

No further source rewrite is needed merely to add another game recipe. New sites,
manager deployment formats and game-specific patches do need bounded maintenance
and renewed evidence. “Build once and reuse” is the goal, not a promise that upstream
interfaces never change.
