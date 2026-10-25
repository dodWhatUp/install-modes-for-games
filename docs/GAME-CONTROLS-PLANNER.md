# Game Controls & Overlay planning

## Current continuation — 0.27.22 source, 2026-10-25

The [completed source workflow](GAME-CONTROLS-WORKFLOW.md) now includes the
stable-action game bridge, retained v2 graph/assignment intake, bounded
recommendations, scoped rules, research exchange and separately reviewed
apply/rollback/publication. DOOM and a second-genre fallback were rehearsed on
private copies. Installed applications and live game/native data are unchanged.

The sections below preserve the **historical first-stage record**. Its pending
features describe 24 October's first slice; use the current workflow above for
present capabilities and remaining live-review/physical acceptance boundaries.

Source implementation, 24 October 2026. This extends the existing keymap
builder, SourceLibrary, map renderer and `game_keybind_ops` readers. It does
not introduce another application, input handler, source master or remapper.
Requirement lineage: GT-048–053 / GT-058–059; the supplied 24 October handoff
adds the A20-UF-1 planning method and COMBAT R2 constraints.

## Open and use

In a source build containing this change, open **Controls & overlays → Choose
a keymap or overlay → Build / edit maps… → Game Controls & Overlay…**.
The installed October 21 release does not contain this source addition.
No installation or live-data migration is performed by development/tests.

1. **Sources:** start from the selected builder draft and its exact native
   contract. Read an existing registered binding target or reviewed effective
   instance for this game. A target establishes saved scalar rows only; an
   instance resolves its explicitly declared precedence through the existing
   `effective` owner. Neither proves game prompts, Steam Input transforms or
   undocumented override files. Source selection replaces the current planning
   action list only after its local dialog; saved revisions remain available.
2. **Actions & priority:** search by action, native command, context or key;
   filter Unknown, Conflicts or Changed; double-click or press Enter to edit.
   Record meaning, activation, categories, U/F candidates, movement requirement
   and evidence. Map a source context to an overlay context explicitly. A
   `bindset-0` name alone does not establish `gameplay`. Bundled actions retain
   independent meanings but move together within their source context.
3. **Preview & export:** review current/proposed keys and routes, all exact
   output occurrences, displacement, blocked constraints and unknowns. Select
   any map/layer/context in the side-by-side preview; it uses the existing
   selected view and renderer. Export a pinned review packet for offline chat
   assistance, or a new folder containing candidate map JSON, all four PNG
   views per map, hashes and a preview receipt. Import a reviewed application
   workbook; review it before Save. No API key or automatic upload is used.
4. **Save planning draft** stores only planning data. The existing builder's
   **Save draft** saves map data; **Publish Overlay** now requires that draft
   to have been saved separately. Game binding and native profile application
   are absent from the planning surface. Future apply integration must use the
   existing trusted transaction controller and its own review.

The initial workflow deliberately retains current placements. Feasible routes
are alternatives, ordered by current placement, direct access, the user's
ordinal row preference and stable identity. They are not a globally optimal
arrangement or a calibrated ergonomic measurement. Unknown action semantics
and frequency require evidence before a meaningful recommendation is possible.

## Priorities and constraints

`P = 4 × (U − 1) + F`, with U1–U5 and F1–F4. Twenty is the greatest access
need. A critical rare action scores 17; frequent paused-menu work can score 8.
Blank evidence remains unknown. Partial evidence retains exact score candidates
and their range. A user override remains separate, with its own reason.

Bundles preserve the most demanding urgency; shared unique activation frequency
remains unknown until measured/reported separately. Member frequencies are not
summed, scores are not averaged and different contexts are not combined.

Physical identity, output, layer, source context, game action and overlay label
remain distinct. Routes preserve #19, #24, #2 and movement anchors #5/#9/#14.
The bottom-up row order is 2 → 4 → 3 → 5 → 1, without invented numeric comfort
distances. A held layer occupying the target finger is blocked. A proposed
movement-dependent route outside the main finger grid is blocked by the user's
thumb/stick constraint. Other simultaneous same-finger relationships are
warnings requiring review, rather than universal physical impossibility claims.

Exact output duplicates such as BASIC #10 K / WEAPONS #23 K are all listed.
Aliases never imply that the thumb route is the recommended primary combat
route. Generic/sided modifiers and transformations remain unverified rather
than being silently normalized. Context sharing needs an explicit exclusivity
record with evidence. Proposed output collisions and bundle splits block
candidate generation; no constraint is silently relaxed.

## Data, stale sources and recovery

The additive application contract is `game_controls_workbook`, schema 1.
The handoff's `azeron_game_workbook`, schema 2, is an engineering interchange
proposal and is intentionally rejected by this importer. Its broader rule,
research and per-field evidence models require a reviewed adapter, not a silent
schema downgrade. The example template documents the smaller app contract;
the UI creates real drafts from the selected map.

Planning lives at `keymap-documents/controls-planning/<game-id>.json`, adjacent
to SourceLibrary, outside the renderer's top-level map documents. Saving uses
an edit lock, exact expected revision, original revision history, atomic file
replacement and readback. Optional extension data survives saves. Pending
shared changes remain game-local proposals; no rule is promoted across games.

Map content, saved map revision, native contract revision, rules revision and
selected binding source hashes are pinned. A changed builder/saved map or
binding file requires reconciliation before save/export/import. Reviewed
responses cannot change source pins, native output, action identity, source
context or binding-bundle identity. Unknown required schema/rules fail closed.

On Windows, profile file hashes are checked through the existing native storage
layout. Missing/ambiguous profiles remain unverified; byte drift stays drift,
including formatting-only drift. Read-only planning may preserve/export that
observation against the saved contract. It confers no publication/apply
readiness and never relaxes the existing native/runtime guards.

Candidate folders are exclusively created, never overwritten. Their
`PREVIEW.json` is a preview receipt, not a live overlay registry. The existing
builder remains the publication owner. Candidate labels carry suggestion
provenance, retain native output matrices, comments, styles and geometry, and
cover Keys / Actions / Combined / ActionFirst. Failed exports can leave a
partial offline folder; use a new destination after correcting the cause.

Rollback for this source stage is to return to the preserved baseline commit.
Planning revisions can be recovered from their private history. No live
registry, assets, native profile, game file or installed pointer needs undo.
Do not import a candidate to production while its game bindings are merely
proposals or its source dependencies are stale.

## Reconciled starting state

Canonical remote `main` was freshly checked at
`9683b32ca6260b060f4727937f26e6a4a96d50de`. The local canonical checkout already
contained newer Windows source changes. They are preserved in linked-task
baseline `94dcd2d`; the older Mac `290bea7` and unadopted 0.26 candidate were
not used as development baselines.

The user's explicit version-precedence follow-up is recorded in `AGENTS.md`:
the attached ZIP supplies requirements, corresponding newer verified source
supplies the baseline, and divergent content/functionality must be reconciled
without overwriting uncommitted work or choosing by timestamps. This stage
followed that rule from intake; none of the handoff's similarly named planning
files replaced product modules. The separate unrelated canonical knowledge-index
append observed during development was preserved in its owner checkout.

Installed Hub: `0.27.21-preview.2-049bb560b82f`; Studio:
`2.2.0-unified.22`. Of 230 installed Python/PowerShell/AHK files compared,
225 matched the canonical source byte-for-byte. The five differences were
the broader canonical export list, newer selected-file knowledge access,
System Control integration and its two matching tests. The canonical versions
were retained; none removed the newer overlay/keymap owners.

Fresh private read-only evidence establishes:

- The active registry still has the recorded October 21 hash; six game/shared
  source families plus the shared COMBAT R2 document are retained, including
  the 30 DOOM maps and 528 existing images.
- Five COMBAT R2 native profiles match their exact contract hashes. BASIC's
  raw hash differs; parsed data equals the preserved six-profile export.
  This narrows the difference but does not bypass byte guards or prove a fresh
  physical-device state. The comparison is diagnostic, not schema-aware native
  acceptance.
- The current DOOM config hash is
  `33f74beef38ffcaf9ff8796b32014632f09b4a54b13b29c1200a0cb81682815a`.
  All fourteen rows from the prior R2 transaction differ from its desired
  values. No restoration was attempted; cause and game-effective precedence
  remain unestablished.
- There are two registered DOOM targets for that same file and no registered
  effective instance. These are alternate historical recipes, not two
  independent effective files or permission to replay either transaction.
- The target reader extracts 283 current saved action rows. On this host the
  initial read-only preview took approximately 0.28 seconds; this is offline
  planning cost, not overlay/input latency.

Exact paths, original handoff, native/game bytes, hashes and test receipts stay
in machine-local private evidence. They are not copied into public source.

## Acceptance and next boundary

The test suite covers rare-critical/paused-frequent priorities, unknown/range
evidence, bundles, context exclusivity, #2 holder conflicts, #19 protection,
thumb movement constraints, K aliases, displacement, simultaneous warnings,
stale map/native/source guards, actual idtech reader fixtures, saved history,
review import and exclusive candidate exports. GUI acceptance uses the isolated
Linux lab, including source/builder navigation, filtering, keyboard editing,
narrow layout, saving isolation and all four map preview views. Windows UI,
physical holds, focus/click-through and gameplay are separate acceptance.

Recorded checks for this stage:

| Checks | Result |
|---|---|
| New planner/source/storage/export tests | 29 passed on Windows, synthetic files |
| New planner GUI | 4 passed in isolated Linux |
| Existing builder GUI, including separate Save/Publish | 4 passed in isolated Linux |
| Existing overlay panel GUI | 14 passed in isolated Linux |
| Existing effective-binding graph | 31 passed on Windows |
| Existing idtech bindset adapter | 6 passed on Windows |
| Existing JSON schema contracts | 10 passed in isolated Linux |
| Source-export contracts | 70 passed on Windows |

Existing builder/document/views/comments/customization/exchange/appearance,
alternate-view/fallback/layer/prepared-frame/response tests were also exercised.
Two broad legacy adapter suites encounter four Windows fixture limitations:
three require unavailable symlink creation privilege, and one requires a
case-sensitive filesystem. All four affected cases passed in Linux; this does
not establish those host-only capabilities. The host lacks test-only
`jsonschema`, so schema checks ran in the guest. One combined GUI batch reached
its deadline after both four-test suites passed; the remaining fourteen-test
panel suite passed in a separate bounded run. Failure/timeout receipts are
retained privately. A stale overlay GUI assertion was updated to check the
existing radio-choice component as well as editable selectors.

Packaging also exposed an existing exporter assumption that every Python
`VERSION` uses double quotes. It now accepts matching single or double quotes;
the added contract verifies the existing alternate-view editor's version.
The source checkpoint is byte-verified; it is not an installed update.

The next implementation slice is a reviewed stable-action crosswalk into
`game_keybind_ops.authoring.planner_bridge` plus its existing preview/rollback
owners. First reconcile the current DOOM rows and effective-source precedence;
keep the exact native drift visible. Then research/classify the actual commands,
review a bounded proposed diff and compare its matching candidate maps. Applying
that diff or publishing maps requires its own reviewed operation. Full handoff
v2 import, richer scoped rule editing, automated discovery/research and a global
placement optimizer remain future source work. No blanket game migration or
installation is implied.
