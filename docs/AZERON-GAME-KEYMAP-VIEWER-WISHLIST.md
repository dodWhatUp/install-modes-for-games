# Azeron game-specific keymap labels — requested tool

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

