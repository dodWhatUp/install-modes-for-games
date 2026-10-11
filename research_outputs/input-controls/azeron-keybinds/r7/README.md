# Azeron R7 — research audit and Action Atlas

Status: **source-backed local display prototype and scoped research completed; effective-game and host acceptance pending**. Owner: `dodWhatUp/install-modes-for-games`.

Start with [the research decisions](AUDIT_AND_DECISIONS_R7_HE.md), [the Atlas integration plan](ACTION_ATLAS_PLAN.md), [game onboarding](GAME_ONBOARDING.md) and [continuity](CONTINUITY_R7.md). The existing native R6 COMPACT4/SPARSE5 files are unchanged. R7 is not another native profile family.

## Deliverables and source roles

- `analyse_survey.py`: descriptive, per-game-deduplicated vocabulary analysis of the inherited R4 corpus. Output: 94 scoped records, 2,195 original rows and 4,371 pair comparisons. These are not complete controls or usage-frequency measurements.
- `curate_actions.py`: source-scoped selection, reviewed categories/gestures, two additive findings and pending game scopes. It generates 179 action records from eight publisher/project manuals: 177 inherited selected rows plus original Skyrim Slash/Skills and Tomb Raider 2013 V/fire. Original expressions remain intact.
- `semantic_review.py`: four transparent semantic-role samples and 22 demand cases. It separates raw-key overlap, action meaning and simultaneous/urgent access requirements. Neither layout is declared universally optimal.
- `atlas_core.js`, `atlas_template.html`, `build_atlas.py`: deterministic, offline, display-only Atlas. It offers Keys/Actions/Combined, manual game/context/layer, optional icons/category accents and stable-geometry search. No native output change, keyboard hook, external service or game execution.
- `atlas-extension.schema.json`: optional display extension of the existing schema-2 GAME-KEYBINDS contract, not a replacement mapping master or command interface.
- `PROJECT_PREFERENCES_R7.json`, `REQUIREMENTS_AUDIT_R7.json`: project-scoped requests, corrections and explicit unfinished boundaries. No global preference changes.
- `test_atlas.js`, `check_artifacts.py`: query/data/schema/contrast checks. Real-browser rendering, actual host integration and game input were not tested.

Generated HTML, large descriptive results and recovery/native snapshots are private delivery views in the existing Azeron Drive folder. Authored source and this audit live here. The exact R1 research master and R2 extension retain their existing owners. The R4 corpus used here is a dated derivative, not reconstructed master bytes.

## Requirements preserved

Hide and reserve native index-side #19 without assigning an invented hotkey. Keep the other 29 digital controls, including little-finger side #36 and bottom #37; omit the joystick illustration without changing its input. MENUS stays MENUS. Preserve each R6 family's blank masks, gestures and output identity. Changing a selected game changes labels only. The old AI game posters are excluded as evidence.

Icons and category colors complement text and keys; they do not replace them. Unreviewed actions are unknown. Required chords and holds stay visible. Search dims rather than moves physical controls. A future Peek mode must not steal game focus; pinned Explore is a separate interaction mode. #19's actual external trigger is not implemented.

## What improved and what remains

The new comparisons show why a common keyboard vocabulary does not imply common action positions. Published defaults can conflict with R6's physical assumptions: original Skyrim Alt sprint, Shadow's held F1 healing, ordinary-letter modifiers and thumb/movement competition need targeted evaluation. Adding a layer supplies capacity but cannot automatically solve reaction urgency or a held-finger conflict.

The method therefore keeps the universal family first: existing route, coherent duplicate or bank, then a reversible game-side adaptation, with hotbar/grid/simulator bases only for demonstrated structural differences. No new native family was generated merely to give this work a revision number.

The Atlas has 18 selectable targets: eight scoped sample sets and ten explicitly pending requested title/family targets. PoE2, current Cyberpunk effective settings and the other pending titles are not populated from guessed defaults. The eight samples are not evidence of this user's installed overrides.

## Validation receipt

Twenty-six named Atlas contract tests passed, along with 177 raw-row comparisons, two additive source records, 4,371 pair reconciliations, four semantic samples, 22 demand cases, seven invalid-schema rejection cases and two inline-JavaScript syntax checks. Full-opacity palette contrast was checked; this is not full WCAG conformance or a rendered-view test. R6 native readback was rerun on 270 visible cells, 387 inputs and 14 links without altering the source files.

No browser denial was retried, no screenshot/video or global input collection occurred, and no app/game/device settings were modified. The separate PR4 report concerns R5 loading and selector return outside games, not R6, ordinary keys, the joystick or gameplay.

## Integration and recovery

This is an additive display/knowledge module for the existing shared game toolkit: see `docs/AZERON-ACTION-ATLAS.md`, the Game Tools knowledge index, shared architecture, Hub and Studio integration. A new queue, repository, host rewrite or execution permission is not created.

[Reproduction](REPRODUCTION.md) gives exact input roles and commands. The private complete recovery contains authored outputs, unchanged R6 candidate packages and dated R6/R5 continuity archives with manifests. It preserves available artifacts and a curated conversation summary, not every inaccessible past chat message. Publication receipts are separate from the immutable archive they describe.
