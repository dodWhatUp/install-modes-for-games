# Azeron game-specific keymap labels — requested tool

## 2026-10-12: map planning and future HTML overlay tasks

Planner revision 4.0 adds the standalone strategic V3 requested by the user:
occupied-key relocation plans, per-game rationale, priority/relationship ratings,
searchable action review, mouse exclusions and strategy JSON. Existing personal
V3 maps remain separate; new personal copies start at V4. Catalog completeness,
exact current-game menus, rebinding acceptance and gameplay remain limited as
described in the delivery record. Installed Overlay integration remains future
work under the existing requirement IDs; this is not an app installation.

Later standalone planner revision 3.0 implements named independent personal
copies, V3/V4 and later, with all layers/contexts, explicit per-key action/note
editing, restore/clear, built-in icon choices, JSON import/export and a portable
editable HTML document. Native profiles and installed Overlay behavior remain
unchanged. MAP-ICON-01's built-in per-button choice is implemented in personal
HTML maps; importing external icon artwork and installed-app integration remain
future work. See the delivery record for exact acceptance and rollback.

The user requested per-game V1 source-action maps and separate V2 suggestions,
copy-ready action lookup on key selection, reversible appearance settings and
current-layer exports. The standalone Cyborg 2 planner implements these as
presentation/planning behavior; suggestions never write Azeron or game bindings.
Unresolved action documentation must not be interpreted as a confirmed free key.
Retain verified default corrections separately from proposals and personal-game
acceptance, with game/version/family/layer/context in exported artifacts.

Backlog under GT-052 and the existing GT-044–050 overlay requirements:

- **HTML-OVERLAY-01 — future, not installed:** support self-contained single-layer
  HTML and complex game/version/layer HTML pages in the Overlay application.
  Reconcile the latest installed/source owner before implementation. Preserve PNG
  import, managed library IDs, native remapping ownership, passive Peek versus
  interactive Explore and settings. Define local content/script/resource policy,
  state selection, no-focus-steal behavior, sizing/DPI, offline dependencies,
  lifecycle cleanup and export compatibility, then test the selected real host.
  The current image contract does not execute HTML. This record schedules no
  job, starts no app and authorizes no cross-chat message.
- **MAP-ICON-01 — future:** let the user replace a button's schematic action icon
  with a validated icon choice, restore inherited defaults and retain those
  presentation overrides separately from action names, sources and bindings.
  Global icon color is already a reversible planner option.

The standalone planner's implementation/verification scope is recorded in
[the map delivery record](SPARSE6-ADDITIONAL-GAME-MAPS-2026-10-12.md).

## Goal

Keep one canonical Azeron physical map and its emitted key outputs, then show game-specific action names on the same button geometry. Switching the selected game changes the labels only; it must not silently change the Azeron profile, layer, or emitted keys.

This is a requested addition to the tools for creating and adapting PC-game keybinds. It complements the shared layered Azeron base and `templates/GAME-KEYBINDS.example.json`.

## Workflow

1. Read an Azeron Software profile export, or let the user record the verified device geometry, button IDs, physical positions, and current outputs.
2. Let the user select a game/build, keyboard layout, active mods/remappers, and the sources for native and effective game bindings.
3. Generate a ready-to-copy ChatGPT/Codex request containing only known device buttons, outputs, layers, and cited binding evidence. The request asks for game-action labels without changing the physical mapping.
4. Accept a structured response and validate every `button_id`, layer, output, game binding, source, and mapping revision against the device/profile and supplied evidence. Keep unknown or conflicting entries marked for review; never invent a binding or apply a response directly to Azeron.
5. Let the user review and save the game overlay, then render it on the shared physical map.

## Views and selection

Render three views on the same verified geometry:

- **Keys:** the physical button and emitted key/output.
- **Actions:** the selected game's action label for that button.
- **Keys + actions:** both labels together.

The default game selector should be manual. An optional later feature can associate a user-approved executable allowlist with a saved overlay and switch the displayed labels when that game is selected or focused. This remains display behavior: no key interception, input logging, background remapping, or automatic profile changes. Show an explicit unknown state when the active game/overlay cannot be identified.

## Data and evidence

Use the shared fields in `templates/GAME-KEYBINDS.example.json`: `button_id`, `position_id`, device control ID, baseline input, layer, output, action, native default, effective game binding, sources, confidence, verification state, and the `keys`, `actions`, and `keys_and_actions` diagram collections. Keep each game's action labels and source/version evidence in a separate overlay linked to the same device/profile revision.

Preserve the user's baseline and recovery export. Distinguish static/profile verification from observed gameplay prompts and behavior. Do not label a default game binding as effective when a mod, Steam Input, or another remapper changes it.

## Acceptance criteria

- One device/profile revision can be linked to multiple game overlays.
- Changing games changes action labels and the selected diagram only; the canonical physical map and outputs remain identical.
- Each diagram keeps stable button numbers and verified physical positions.
- Unknown buttons, sources, or game bindings remain visibly unknown and require review before an overlay is accepted.
- The app can produce a copy-ready ChatGPT/Codex prompt and validate a returned structured mapping before rendering it.

## Copy-ready handoff for the keymap/script app chat

Please add a feature request to the PC-game keybind creation/adaptation tool: **one canonical Azeron physical map with per-game action-label overlays**.

The physical map must stay stable: device geometry, button IDs/positions, layers, and the keys each button emits come from a verified Azeron Software profile or explicit user documentation. For each game, store a separate overlay that maps those same button IDs to game-action labels, with game/build/mod/remapper context and source evidence. Selecting another game should switch only the displayed labels and diagram, never rewrite the Azeron profile or key outputs.

Please support three views over the same geometry: **Keys**, **Actions**, and **Keys + actions**. Start with a manual game selector. You may design an optional, user-enabled executable-to-overlay association for deciding when to show a saved overlay, but keep it local and display-only: no key interception, keystroke logging, background remapping, or automatic Azeron profile switching. Show `Unknown` rather than guessing if game or overlay identity is uncertain.

Workflow: let me import/select an Azeron profile or document button positions and outputs; choose a game/build and provide native/effective game and mod bindings with sources; generate a prefilled prompt I can copy into ChatGPT or Codex; accept its structured response; validate all button IDs, layers, outputs, bindings, revisions, and sources against what I supplied; flag unknowns/conflicts for review; then render and save the overlay. Do not invent game bindings or apply returned data directly to Azeron.

Use `templates/GAME-KEYBINDS.example.json` as the existing data contract, especially the `keys`, `actions`, and `keys_and_actions` diagram views, provenance, confidence, and separate configuration/gameplay verification states. Please propose the UI flow, storage format, validation rules, and implementation plan first; preserve the existing Azeron baseline and recovery-export workflow.
