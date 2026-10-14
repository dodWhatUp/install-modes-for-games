# Game Tools Workbench — verified workflow changes

Source preview: **Hub 0.23.0-preview.1**, Workbench/Game Workspaces 0.1.0.
Date: 2026-10-13. Owner: `dodWhatUp/install-modes-for-games`.
Base: the exact 0.22.0 Focus source, not the older GitHub Hub 0.2.0.
This is a new optional front end over the existing mod engine and approval service.
It is not an installed release, a new mod manager, or a verified live AI connection.

## Open and try

Extract the complete preview ZIP. **OPEN Game Tools.cmd** opens Workbench;
**OPEN Original UI.cmd** preserves the original panels. Both use the same isolated
`GameToolHub-Workbench-Preview-0.23` profile, not production data. One preview owns
that profile at a time. Existing Python 3.10+ with Tkinter is required; no runtime
is installed. The launcher uses an existing verified runtime when available.

On the first empty workbench, **Try samples** creates two clearly fictional game
workspaces using harmless text files only, after confirmation. Sample Alpha is
prepared; Sample Beta is downloaded. Select Beta and **Prepare selected**. Switch
between the games; test a proposal in **AI requests → Test approval flow**, inspect
it and reject or approve it. No actual game, mod binary, download or client is
needed. Existing samples are reused. They must not be counted as game evidence.

## What was wrong in the source

These are source-derived findings, not claims about the unobserved Windows install.

| Observed source issue | Implemented change | Expected benefit / current proof |
|---|---|---|
| `GameToolModIntegration` constructed one mod pane and one Kingmaker-oriented automation service. | `GameToolGameWorkspaces` selects an explicit registered recipe and namespace per game, retaining original Job files and approval schema. | Independent game drafts, saved plans and requests; tested with two distinct fictional recipes. |
| `peer_busy` blocked the whole original Mods/AI pairing. | Workbench has one task per game, at most two local tasks and one transfer; manual review remains available. | Different-game local work continues during a transfer. These are source-level concurrency tests, not simultaneous real installations. |
| Existing jobs depended on manual folder selection and were not grouped by game. | A game's saved plans are listed automatically from the already-owned mod job directory, with readable dates/state and stable IDs. | No private whole-disk scan and no repeated folder hunting. |
| Technical JSON was a poor default approval presentation. | A readable inspector shows target game, exact action/items, effects, limits, current-source status and receipt, with optional technical details. | Human review of the same guarded request; AI cannot approve itself. |
| File preparation and later gameplay checks lacked a shared operator view. | Mods, AI requests and Manual checks are adjacent tabs in each game workspace. | File states and human observations remain explicitly different. |
| The old workflow was difficult to try without provider setup. | Opt-in two-game text-only sample workflow using the real local plan/import/stage functions. | Tests actual local workflow without exposing or copying production data. |

Original Focus/Modern/Classic panels remain available. No AHK/native profile,
remapping, game settings, capture or statistical provider was replaced.

## Layout changes and their reason

The large navigation area is now a game list; the center is the selected game's
working table; the right inspector holds detail for the selected item or request.
The center gets most of the space. On smaller windows the side regions collapse
and remain reachable through labelled Games/Inspect controls. Header controls
reflow instead of forcing the center to one pixel wide. A final 200% zoom check
found that the More button could still be clipped at narrow widths; the controls
themselves now wrap based on their requested sizes, with a regression test for
every visible header control.

There is one main contextual action and a short set of supporting actions rather
than a permanent wall of buttons. Essential table columns are the default; version
information can be revealed, columns resized and sorted without changing install
order. Exact source and diagnostic details stay available rather than disappearing.
Dark and Light are genuine palette choices. Compact/Comfortable spacing and
80–200% text/control zoom remain separate; zoom does not change operational state.
The activity drawer appears when there is activity rather than reserving an empty
region all the time. Game changes preserve draft selections, filters and mode.

These changes address a concrete task. They are not evidence that a theme alone is
pleasant, that this is a new native Windows design system, or that user visual
acceptance is complete. Native Windows rendering and assistive-technology checks
remain necessary. A future toolkit migration is not justified just by renaming a
preview or adding another theme.

## AI and manual operation share the existing engine

The optional `GameToolAI.py --workspaces` route adds `hub_games` and requires
`game_id` for preview/proposal/status. It accepts the existing three mod operations:
`mods.create_plan`, `mods.download`, `mods.stage`. It does not add an approve tool,
install/rollback tool, arbitrary commands, game inputs or a network listener.
The original single-game/overlay AI route remains compatible.

**Copy for chat** exports a bounded game-scoped context. Per-section hashes allow
unchanged sections to be omitted in subsequent calls. Credentials, raw logs, source
URLs, private paths and free-text manual notes are excluded. The explicit local
client-setup copy contains private machine paths; keep it local. Creating that
configuration does not connect a client. No cloud call is made by the workbench.

After a local approval, the original expiry, exact hash, recipe/job revision,
exclusive operation journal and no-replay rules still apply. Another game cannot
reuse a job through its own scope. The worker captures target game and job before
starting, so switching the visible game cannot redirect a late result. Stop is
cooperative at the original safe boundaries, not process killing.

Downloads retain the existing per-action ceiling: 128 MiB, 40 requests and five
minutes. Only one transfer runs at a time. No automatic scheduling, waiting queue,
unattended approval, rate-limit workaround or blind retry was introduced.

## Manual checks are evidence, not decorations

A human can record whether the manager lists a mod, whether the game starts, and
whether the requested feature works. Notes stay local. A reported pass is labelled
**Reported pass**; it never changes download/staging events or claims independent
runtime verification. The check is bound to the reviewed job revision and becomes
stale when that job changes. It does not know about all external game-folder edits;
therefore even “same job revision” is not proof the installed files are unchanged.

A separately invoked **Inspect game folder** uses the existing Kingmaker-only
read-only adapter. It checks executable/mod metadata and loader presence, saves
an immutable inspection receipt, and does not claim enabled, loaded or working.
Other games explicitly say that their inspection adapter is unavailable.

## What remains missing

Kingmaker is the only included ready mod recipe. Cyberpunk and Skyrim retain their
existing catalog identities but do not acquire invented mod recipes or installation
support. Other reviewed data-only recipes can be imported explicitly, without code
execution or replacing a conflicting recipe. The samples are not additional real
game support. Discovery is bounded and does not scan unrelated drives.

This workbench prepares files; it still does not install the UMM loader, safely
upgrade existing mods, or expose unrestricted game-file writes to an AI. Existing
separate guarded installation CLI/manual UMM boundaries remain. No live Nexus
account/provider download, Windows update, native Studio, or AI-client deployment
was validated in this turn. No game/benchmark/recording was resumed.

## Ranked improvements — only where the benefit is concrete

| Priority | Candidate | Benefit / acceptance needed |
|---|---|---|
| P0 | Native Windows launch, scaling, updater and local client acceptance | Close the source-to-working-app gap. Prove actual launch, read-only connection, recovery and preserved settings before reporting deployment. |
| P1 | Supported manager adapters for installed state, enable/disable, safe upgrades and rollback | Address the biggest functional gap. Require exact game instance/build, stopped target, manager-owned file contracts, before/after hashes and scoped backups. Do not replace a manager's own state behind its back. |
| P1 | A readable planned-versus-installed change review | The implemented plan comparison compares intentions only. Add reviewed actual file state and show additions/removals/settings before a permitted mutation. |
| P1 | More individually verified game recipes | Grow coverage using each game's authoritative manager/build conventions. One generic recipe does not establish support for all games. |
| P2 | Connection test with source/client/device identities | Make “the tool is installed”, “client connected” and “operation permitted” visibly separate, backed by a supported response rather than a saved setup file. |
| P2 | Shared-resource scheduling after manager support | Per-game locking is enough for current private preparation, not shared DLLs, Vortex/MO2 profiles or real game installs. Add verified ownership of shared destinations before broader parallel writes. |
| P2 | Persisted column/workspace layouts and accessible native polish | Add only from repeated tasks and user feedback; preserve original layouts. Native focus, screen-reader and real Windows 200% checks remain, rather than treating tiny text as compact design. |
| Deferred | Rewrite in another UI framework; unrestricted AI control; animated dashboards; running every mod concurrently | These have no demonstrated benefit sufficient to justify a rewrite or broader risk in this slice. An alternative framework needs a measured requirement first. |

## Primary design references and interpretation

External guidance, distinct from observed source defects:

- [IBM Carbon data tables](https://carbondesignsystem.com/components/data-table/usage/), accessed 2026-10-13: put table actions/search in context, provide appropriate row density and progressive detail, and allocate useful width to the main table. Applied as short table actions, essential columns and separate inspector—not as a claim to implement Carbon's React components.
- [Microsoft list/details](https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/list-details), accessed 2026-10-13: keep a collection and its current detail related and adapt presentation to width. Applied to game list/work area/inspector and narrow-window fallbacks.
- [W3C resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) and [target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html): enlargement and operable controls matter; compactness is not the same as tiny type or undiscoverable icon-only actions. These web standards are design checks here, not desktop WCAG certification.

## Validation, ownership and rollback

See `WORKBENCH-VALIDATION.json` and `WORKBENCH-SOURCE-DELTA.json` for exact tests,
changed source identities and limits. The new tests execute real widget callbacks,
local file staging and approval receipts using owned temporary data. They do not
use screenshots, a real game, a connected AI or provider account.

Source remains a candidate under the existing game owner. The previous game-Git
and remote workspace blocks were not retried or bypassed. Drive is a versioned
private delivery snapshot, not a competing editable master. Global proactive-tool
PR20 and existing one-click preference adoption remain separate states.

Rollback: close Workbench after its active operations stop, then use Original UI
or the untouched installed launcher. Preserve the new preview profile for review;
never restore all production data or delete another program's settings to undo
this optional source preview. Both preview launchers share one OS-released lock.
