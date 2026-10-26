# Game Controls & Overlay — 0.27.22 source workflow

Installation status, 25 October: the user subsequently approved the
[application-only update](GAME-TOOL-CONNECTIONS.md#2026-10-25--approved-controls-application-update).
All 528 installed payloads and preserved settings verified; no binding or Overlay
publication operation occurred. The source-stage account below remains historical.
The later requested Windows [planner UI check](GAME-TOOL-CONNECTIONS.md#later-same-day-requested-windows-controls-screen-check)
also passed without saved-state changes; physical/gameplay acceptance remains separate.

Completed source stages on 25 October 2026, continuing the 24 October handoff.
This extends the existing builder, SourceLibrary, renderer, game_keybind_ops and
guarded updater. The installed 0.27.21 application remains unchanged until a
separately reviewed update. Native profiles remain owned by Azeron software.

## One workspace, separate operations

In a build containing this source, open **Controls & overlays → Build / edit
maps… → Game Controls & Overlay…**.

1. **Sources:** read an existing registered target/instance, discover candidates
   through the bounded location catalog, or reconcile a changed saved source.
   Reconciliation retains annotations and clears proposals on changed bundles.
   A target proves selected saved rows; an instance resolves only its declared
   precedence. Neither proves a universal engine/mod/Steam Input pipeline.
2. **Actions & priority:** search/filter, edit evidence and U/F candidates, retain
   unknowns and bundles. **Planning tools** prepares focused research, suggests
   positions, edits scoped rules, reviews shared updates/v2 assignments and
   highlights routes in the existing builder. Filter typing reuses its preview.
   No research, parsing or rendering enters live input polling.
3. **Preview & export:** compare maps, inspect precise game diffs, export source
   candidates and all four image views. Preview/export reuse effective game/global
   appearance scales; comments, icons, colors and geometry remain in the source.
4. **Prepare reviewed plan:** immutable private review pins the map, workbook,
   source rows, native files and existing keybind preview. The owner service
   prepares original/candidate bytes. Editing dependencies requires a new review.
   Preparation does not apply input or publish an overlay.
5. **Apply Game Bindings:** a separate local review delegates to the existing
   writer's process, source/recipe, linked-field, collision, backup, journal and
   readback checks. Exact native files must still match. JSON does not authorize
   this call; missing or formatting-drifted files do not become verified flags.
6. **Load verified candidate in builder:** only after complete game-file
   verification, or unchanged pinned sources for display-only work. Review,
   **Save draft**, then **Publish Overlay** separately. Publication rechecks
   the plan and game/native files. Unapplied exports cannot publish through
   SourceLibrary. No automatic native profile operation is introduced.
7. **Rollback:** separately suspend this game's overlay before undoing a
   published game plan. Existing missing-context behavior hides its content
   without changing hold owners, other games or assets. Exact undo restores
   original bytes through the existing service. After original readback, load
   the original map from history, Save and Publish separately. Selective undo
   remains in the service; later edits need reconciliation before old labels
   can be republished.

**Apply Native Profile** is a separate native-software/manual boundary. There is
no Apply All, automatic install, game launch, capture or cloud upload.

## Contracts and research

| Contract | Role |
|---|---|
| game_controls_workbook v1 | Additive app draft with exact source/map pins |
| azeron_game_workbook v2 | Full supplied planning graph, retained losslessly |
| game_controls_review_packet v2 | Compact offline request with one route catalog |
| controls_action_research_request/reply v1 | Stable IDs, citations, uncertainty/conflict review |
| Existing keymap package/document v1 | Existing renderer/publication sources |
| Existing keybind plans | Sole game-file transaction and recovery owner |

V2 intake uses the pinned supplied schema, bounded local refs, structural checks
and semantic ID/priority checks. Original bytes are retained by hash; unknown
required versions/features fail with an explanation. Optional extension data and
the full original graph survive round trips. No remote schema is loaded.

Classifications project through exact IDs or exact native command plus native
context. An unidentified game requires explicit linking; common IDs/labels do
not silently transfer meanings across games. Assignment review requires exact
existing layer/context/output links. External accepted/file-verified/play-verified
states remain claims. Divergent assignments need reconciliation; timestamps and
array order do not select a winner. Native outputs/recipes/source pins are not
imported, and shared rules are not promoted by importing a workbook.

Research can annotate meaning, activation, categories, U/F and movement needs,
with citations or labeled reports/inferences. Conflicting annotations need
review. Outputs and authority cannot be changed. Per-user frequency is never
invented. Unsupported binary/UI-only games receive discovery/manual checklists.

## Recommendations and rules

For a complete first-layer and cross-layer audit, follow the
[complete accessibility review](GAME-CONTROLS-COMPLETE-REVIEW.md). Account for
every unused accessible position, protected control, required held combination,
incidental output alias and UI-only action outside the parser. Keep completeness
separate from physical/gameplay acceptance. The updated workbook template stores
this review as optional extension data; no new automatic app gate is implied.

Before exporting a later review, rebase the workbook against the current source
document after publication. Preserve the old pin as provenance. Newer native-menu
evidence must also supersede provisional action descriptions, with historical
notes retained. A matching cfg alone does not prove effective runtime bindings
when the game persists them in a different store.

A20-UF-1 is ordinal: P = 4 × (U − 1) + F; 20 means greatest access need. Ranges
and unknowns remain explicit. Bundles retain highest urgency, with unknown
unique-activation frequency where needed. A wholly unknown bundle gets no score.

The bounded deterministic search respects protected controls, locked fields,
mouse ownership, thumb/movement needs, the #2 holding finger, context overlap,
direct access and accepted rules. It compares simultaneous-finger review,
direct/layered access, ordinal 2 → 4 → 3 → 5 → 1 row preference, scoped placement,
unnecessary moves and stable ties. It reports withheld actions, state/time limits
and best-found status. It is not calibrated physical cost or universal global
optimality. Recommendations require explicit adoption into the draft.

Rules have action/game/context/genre/global scope, revision, acceptance and reason.
Proposed rules do not constrain the active plan. Shared saves need local review
and exact revision, retain history, and show affected saved games. Other games do
not adopt updates automatically. A game draft cannot replace newer shared rules.

## Rehearsal and acceptance boundaries

[Validation summary](GAME-CONTROLS-VALIDATION.json): 196 distinct Python tests,
70 source-export contracts and independent Draft7 structural cases passed.
GUI checks ran only in the isolated Linux guest; private game trials used copies.

| Stage | Result |
|---|---|
| Source/installation reconciliation | Newer Windows source preserved; ZIP remains specification data |
| Scoped DOOM discovery | cfg contains bindings; adjacent local file has no binding/include lines in the check |
| Planning/translation | Unknowns, aliases, bundles, locks, holds and multi-file dependencies tested |
| DOOM private-copy trial | Fresh 14-row apply/readback, 30 maps × four views, exact original-byte rollback |
| Native source candidate | Current file copies parse to the same six-layer outputs; fresh exact hashes, no live adoption |
| Bayonetta second-genre path | Manual fallback; 12 maps × four views; unsupported storage remains unknown |
| Application delivery | Existing updater/source package checked on private fixtures; installation separate |

Current live DOOM values differ from all fourteen prior R2 edits. This rehearsal
is a comparison, not authority to restore those values. BASIC's bytes differ
while its parsed data matches the preserved export; its fresh native contract
exists only as a private candidate. Existing live registry, images, native
profiles, installed pointer and game configurations were not adopted or changed.

The publisher documents separate remapping menus for Slayer, Atlan, Dragon,
Turret, Menu and AutoMap, plus configurable hold/toggle behavior. This does not
prove current per-user styles or file precedence.
[Official accessibility guide](https://slayersclub.bethesda.net/en-US/news/doom-the-dark-ages-accessibility-guide).
Revelations adds separate Chain Spear bindings and input styles; availability
does not prove ownership/unlocks or current activation mode.
[Official Update 4 notes](https://slayersclub.bethesda.net/en-ZA/news/doom-the-dark-ages-relevations-update-4).

Windows gameplay, human ergonomics, actual #19/#2 gestures, focus/click-through,
compositor latency and unknown effective sources remain separate acceptance.
Existing AHK/native-layer/appearance/alternate-view runtime owners are unchanged.
Exact private files, copies, failures and readbacks stay in local bindings.

## Packaging and recovery

### Later Windows activation — 2026-10-25

After the planning-only stages above, the user separately requested activation.
The existing guarded fourteen-row cfg transaction succeeded on disk, but a clean
DOOM restart still showed old native bindings. This is observed counterevidence
to treating that saved cfg as the sole effective owner. Native settings menus
were used to install the intended twelve visible action assignments; a second
clean restart verified persistence. Steam's opaque native profile changed and
was preserved in paired recovery. No binary-profile writer was introduced.

Both existing native-contract owners were reconciled to unchanged profile data
with fresh exact hashes. Reviewed publication generated all 120 DOOM views with
compact labels, no truncation and unchanged appearance/Auto/hold preferences.
The saved workbook retains the native UI readback and source-authority warning.
The agent's temporary focus-guarded input host was closed after use.

**Reusable requirement:** keep saved-file transaction status separate from
effective runtime verification. A byte-perfect apply/readback does not prove
game adoption; contradictory UI evidence takes precedence. Preserve newly found
native-profile storage before UI mutation and include it in rollback planning.
Do not infer opaque binary values or label a cfg-only inverse full recovery.
The current adapter still checks files only; native UI evidence is a separate
verification record. Physical #2/#19 and gameplay acceptance remain pending.

Later physical follow-up: the user reported the requested DOOM #2/#19 sequence
works and the relay reports Event-tracked. Physical Overlay acceptance is now
user-reported PASS; combat, comfort and measured latency remain untested.

A real multi-layer test exposed oversized request exports. Packet v2 stores
routes once, gives eight ranked examples plus an explicit total per action, and
checks the existing 1 MiB bound before creating folders. Unchanged reference
drafts preserve exact map content. Planning paragraphs survive save/import.

The larger canonical source exceeds the old updater's 512-file cap. The reviewed
helper uses a fixed 1,024-file bound while retaining its 32 MiB budget, hashes,
path/link/version checks, leases and recovery. An approved update uses the verified
candidate helper; it does not replace the old source before approval. The old
installed inspector can refuse this larger source package.

Source rollback returns to 0ed2d29 for the initial read-only stage. Live user data
is independent of release folders. A later app update commits its immutable
pointer last and preserves the previous version. The source checkpoint is not
full native/game recovery or an executed installation.

## Later source stage — computed quality review, 2026-10-26

The [quality method](GAME-CONTROL-QUALITY-METHOD.md) adds a read-only source audit
for instruction/evidence closure, all-control decisions, eligible unused-button
opportunities, primary routes, source-action coverage and held-finger conflicts.
It honors the new versioned little-finger policy without silently migrating
historical workbooks. Software checks and recorded claims never import physical
PASS or make the report certify play readiness. This source-stage note does not
establish installed availability, native profile application or publication.

Keep all existing workbook and packet input bounds at **1 MiB**. Review records
may stay in the optional workbook extension, or be supplied to the source audit
as an independently bounded [standalone record](../templates/GAME-CONTROL-QUALITY-REVIEW.example.json)
that pins the current map, native contract, source revisions and workbook hash.
This keeps a large workbook unchanged while recording each control decision.
The full derived audit is separately bounded to **8 MiB**; compact packet
findings retain totals and sample IDs rather than pretending the samples are
the complete inventory.

Small review exports retain the **v2** packet representation. When that complete
packet exceeds 1 MiB, an explicit **v3 manual-review packet** retains every
action and source pin in the embedded supported v1 workbook while deduplicating
route geometry and diagnostic text. Its named columns, code catalog, candidate
examples and total counts are explained by the packet and quality method. V3
remains within 1 MiB or fails with a focused-export instruction. No actions are
silently removed. V2/v3 packets are review formats, not app importers; return the
supported v1 workbook for existing reviewed intake. The standalone audit record
also grants no Save, Apply, native import or Publish operation.
