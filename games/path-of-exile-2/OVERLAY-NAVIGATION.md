# Path of Exile 2 — Azeron overlay handoff

**Latest assets:** [GROUPED R2 guide](grouped-r2/README.md), icon PNGs and
`grouped-r2/overlay-handoff.json`. R2 files are added to the native library;
active selection, physical transitions and host integration remain pending.
The first pair's visibility was user-confirmed after a full Task Manager exit.
The text below retains the earlier R1 preview checkpoint.

**Asset revision:** `2026-10-11-poe2-combat-menu-r1`

**State:** preview assets prepared; Azeron profile pair not installed; gameplay prompts and automatic layer detection not verified.

## Prepared views

- `azeron-keymap/overlay/poe2-proposal-combat-icons.png` and `.svg`
- `azeron-keymap/overlay/poe2-proposal-menu-icons.png` and `.svg`
- `overlay-manifest.json` records the game, device, revision, layer names, source files and selection rules.

Each view uses the saved Azeron Cyborg II geometry from SHARED R5. Finger keys show the active proposed layer; the thumb menu shortcuts remain available in both views. Vector icons and text labels identify actions without relying on emoji-font support. Status tags keep newly proposed mappings distinct from game-config entries and unresolved behavior.

## Proposed fast navigation

1. Start on **COMBAT**. Tap Azeron #6 to emit V; hold it for the proposed 150 ms threshold to enter **MENU**; release to return to **COMBAT**.
2. Keep the thumb shortcuts available on either layer for Map, Inventory, Character, Skills, Passives, Chat and Cosmetics. This avoids a layer switch for common menu panels.
3. When the unified overlay host is ready, select the matching view using game executable + overlay revision + reported Azeron layer. Show a visible `COMBAT` or `MENU` badge so the user can tell which mapping is active.
4. In the host, use one searchable key/action field to find either an output key or an action name. Keep a small Favorites or Recent section for frequently checked actions.
5. Provide a manual `COMBAT` / `MENU` override and a visible `Return to Auto` action. Preserve automatic selection as the default; do not assign another global hotkey until existing conflicts are checked.

These are integration suggestions only. No overlay-host code, global hotkey, Azeron profile or game setting was changed for this handoff.

## Read the status tags

- `PROPOSED`: output assignment belongs to the new profile-pair proposal and is not installed.
- `CFG`: action/key is present in the inspected local game configuration; gameplay prompt is still unobserved.
- `OVERLAP`: the saved modifier is also assigned to another game action.
- `KEY ONLY` or `ACTION ?`: saved output has no confirmed action in the inspected config.
- `MODE ?`: the saved stick output is known, but the active movement mode still needs an in-game check.
- `MOD PENDING`: the shortcut is recorded in settings but runtime input was not confirmed.

## Sources and limits

The mapping is derived from `KEYBINDS.json`, `KEYMAP-PROPOSAL.json`, the saved 2026-10-11 SHARED R5 readback and the inspected PoE 2 config. The SHARED R5 family remains the baseline. No new importable Azeron profile was created. Verify the layer transition, movement mode, skill/flask actions, prompts, Ctrl overlap, and mod menu shortcut in a normal user-started game session before relying on the proposal.
