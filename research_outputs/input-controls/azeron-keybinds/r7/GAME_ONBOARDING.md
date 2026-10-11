# Efficient game onboarding for one shared Azeron family

Status: reusable method, not installation authority. Owner: `dodWhatUp/install-modes-for-games`.
This supplements `docs/AZERON-GAME-CONTROLS.md` and the existing `templates/GAME-KEYBINDS.example.json` (schema 2). Do not create another binding master or remapping engine.

## Minimum inputs and retrieval order

Identify exact game/title/edition/build, platform, input preset (including WASD versus click-to-move), keyboard layout, character/vehicle/menu context and input-affecting mods. Reuse the current verified device geometry, native output snapshot and chosen R6 family. R5/other later live changes remain protected.

Read existing game history and saved configuration first; then a publisher/project manual or shipped input definition; then scoped firsthand evidence only if necessary and clearly qualified. A general patch note may establish a changed behavior, not a complete default table. A community table is not promoted to a verified default by copying it into JSON. Do not launch games merely to fill a spreadsheet when allowed configuration reads suffice. Access missing in one environment is not proof no backup exists.

A fresh native export is not needed to repeat the R6 authoring step. A fresh live-state snapshot is needed immediately before an authorized device mutation. Read the existing Drive recovery index yourself rather than asking the user to transfer the same files again.

## Data contract and separation

Keep schema-2 fields: `game`, `device`, `mapper`, `input_path`, `bindings[].button_id`, `position_id`, `layer`, `output`, `action`, `game_default`, `game_effective_binding`, `sources`, `gameplay_prompt`, and verification states. Add optional display metadata under a namespaced extension rather than replacing those fields:

- `display.category_id`, `display.icon_id`, `display.aliases`, optional asset reference/hash/license.
- `display.source_scope`, `display.conflicts`, `display.selection_state` and `display.evidence_state`.
- `demand.frequency` (null until observed), `demand.reaction_class` (source/user/inference), `demand.hold`, `demand.concurrent_inputs`, `demand.sequence_edges`, `demand.error_cost` and their provenance.

A source fact, an inferred access requirement and an icon/classification choice are separate records. Store exact raw key expressions. Top-row numbers are not numpad codes; left/right modifiers remain distinct in native outputs; a semantic vocabulary analysis may merge them only in a declared derived view. Do not silently convert typed symbols to US-layout scan codes.

## Efficient pass sequence

1. **Inventory the consequential actions.** Cover movement/camera, immediate combat, held modifiers, use/interaction, weapon/skill selection, menus and contextual transitions. Keep unread portions as unknown. A long title list is not coverage proof.
2. **Parse conservatively.** Separate simultaneous chords, ordered sequences, tap/hold alternatives, mutually exclusive contexts, and listed alternatives. Resolve ambiguous notation only at the original source row. Preserve unknowns; never assume `1–0` always means a ten-key range.
3. **Compare at three levels.** Deduplicated key vocabulary; normalized semantic roles; actual access/temporal requirements. Keep each game's denominator, scope and coverage. Do not rank a 10-row quick guide against a 60-row simulator manual as though missing rows meant unsupported keys.
4. **Audit the shared family first.** Reserved #19, source-derived blank masks, selectors and release behavior are hard constraints. Check direct deadline-critical inputs, sustained keys, movement plus output, and all parts of cross-bank chords. Existence in some layer is not immediate access.
5. **Propose the smallest justified change.** Try the existing route; a useful duplicate inside the same family; a coherent functional bank when it really solves the problem; a supported game-side rebind with a reversible diff; only then a separate hotbar/grid/simulation base if the control structure truly differs. Do not allocate a new family merely because the genre name changed.
6. **Render from one source.** All 29 visible IDs are retained. #19 and joystick drawing are omitted; native joystick data is unchanged. Games change labels/icons only. Unknown actions stay visibly unknown. Display the required chord/hold, not a misleading single action label.
7. **Verify in layers.** JSON/source checks; model access tests; in-app load/import checks; physical press/release and output checks; effective game recognition/prompt checks. Store each separately. All previous R5 evidence stays scoped to its exact tested route.
8. **Archive and reuse.** Git owns authored rules/code and sanitized game records. Private Drive owns native exports, original snapshots and generated delivery views. Record hashes, revisions, source scope, pending actions and restore order. Rebuild only views affected by a changed game/configuration/geometry/icon taxonomy.

## Material stopping rule

Do not scan endlessly for marginal catalogue growth. Stop the source pass when every action capable of changing the layout decision has evidence or a clearly isolated unknown, ordinary/panel coverage is adequate for the intended game stage, and further source inspection is unlikely to change the next action. Do not call the whole game complete when that condition covers only on-foot basics. Reopen affected sources after a material update, new character/vehicle/mod, user correction or failed test.

## Physical and learning acceptance

Use a brief safe task list with games closed first: source-backed urgent keys, held selectors, same-finger candidates and key-up cleanup. Stop on pain, unintended output or unknown input ownership. No global logger is needed for basic manual timing/error notes. A later opt-in learning comparison should counterbalance layout order, include familiarization and repeated tasks, measure errors as well as time, and distinguish initial discoverability from learned use. It is not a clinical assessment or a promise of faster performance.

## One-game output checklist

A sufficient handoff has the exact game scope; a small source-backed action table; native design/output fingerprint; demand exceptions; approved/unapproved changes; keys/actions/combined views; source/config/runtime test states; recovery and next action. A prepared recipe is not a command to launch, install, send input, reset defaults or start capture. Shared graphical-tool hotkeys must not be silently changed to solve a game-binding collision.
