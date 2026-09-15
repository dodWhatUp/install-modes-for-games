# Azeron and game controls — default workflow

User instructions confirmed 2026-09-15. Apply this workflow to every game when controls, keypad profiles, related mods, or keybinding diagrams are in scope.

## Desired result

Use one consistent Azeron base setup with multiple layers. Create a separate game-specific Azeron profile only when the shared setup cannot reasonably support that game's controls. Keep common physical actions in consistent positions so muscle memory transfers between games. Adapt the game's own bindings when practical, including the bindings represented by its gameplay prompts.

The current retained software profiles are to be named **GENERAL 1**, **GENERAL 2**, **GENERAL 3**, and **EMPTY**. These names replace FPS - GENERAL 1/2/3. They are the retained starting point; this instruction does not claim that a new universal layered layout has already been designed or tested.

On Azeron Software 1.x, a logical layered setup can consist of several linked software profiles. The original Cyborg manual documents profile switching, optional return while holding a layer button, and behavior for keys held during a transition. Layers and macros require software mode. Confirm the exact model, board, software and firmware before choosing implementation or migrating versions. See the [official manual, sections 5.2.10 and 5.6](https://site-835705.mozfiles.com/files/835705/Azeron_Cyborg_Manual_V6_5.pdf).

## Archive old profiles before removing them

1. Export the live software collection immediately before cleanup. Preserve a prior known-good export separately. Also preserve onboard profiles, labels, macros, timing, joystick settings and layer dependencies where the software export does not include them.
2. Upload an importable backup to the connected Google Drive and verify it by readback. Preserve profile IDs and duplicate names; use IDs or short ID suffixes to distinguish separate copies.
3. Keep a readable reference alongside the original JSON: physical button number, press type, emitted key or sequence, existing custom action label, layer target and relevant joystick settings. Include individual profile exports for selective recovery when useful.
4. Treat old profile labels as historical user notes. They are useful suggestions, not proof of the game's current default or effective binding. Mark missing or ambiguous action names as unknown instead of guessing.
5. Only then remove the selected old software profiles, retain the agreed base profiles, and check that active layer/macro references do not point to a deleted profile. Do not interpret dormant, unused fields as active dependencies.
6. Reopen the app and export the remaining collection to verify names, bindings, active profile and persistence. Record what was actually removed and what remains on the device.

The user's archive milestone is the old collection **before creating new General profiles**. Existing profiles named FPS - GENERAL 1/2/3 were already present in the restored source; this milestone is not a claim that the archive predates their first creation.

## A single mapping record per game

Maintain a versioned mapping record that connects:

**physical Azeron button + layer + press type → emitted keyboard/mouse/controller input → effective game action → gameplay prompt**.

Use the same mapping data to generate every diagram and reference table. Record game edition/build, input mode and keyboard layout, Azeron base-profile version, relevant mods and versions, defaults, user overrides, mod overrides, sources, verification date and confidence. Preserve originals and exact rollback for any configuration edits. Use [the mapping template](../templates/GAME-KEYBINDS.example.json).

For each relevant game, check:

- Default controls from official documentation, shipped input definitions or other authoritative game-specific evidence.
- The user's actual saved keybindings and contextual controls: combat, menus, vehicles, aiming, interaction, inventory and other modes as applicable.
- Mod-added actions, mod-specific rebinding files and overlapping shortcuts. Read relevant local mod history. Incorporate mods the user names, and inspect known installed input-affecting mods when the task calls for it.
- Conflicts with overlays and the user's saved graphics controls. Never silently change shared graphics hotkeys to make a game map fit.

Do not assume that an emitted key always means the same action, that old labels match current controls, or that changing the keypad output automatically changes the game's stored binding.

## Prefer editing and checking game bindings without launching

When supported, inspect and edit the actual game keybinding configuration while the game is closed. Prefer a documented per-user override to modifying shipped game files. First preserve a just-in-time copy and hashes, identify the active file, understand its schema, and account for launcher/cloud sync or mods that can rewrite it.

After editing, parse and read back the configuration, verify intended actions and collisions, and record a reversible diff. Do not launch a game solely for inspection when the configuration can answer the question. Respect a user's request for an entirely offline edit.

Keep two separate verification fields:

- **Configuration verified:** the intended bindings are present in the effective files or supported settings interface.
- **Gameplay verified:** the game loaded those bindings, actions work in the relevant contexts, and the visible prompts agree.

An offline file check cannot establish how a live prompt renders. Some games or mods have fixed prompts, separate prompt assets, encrypted settings, mixed-input restrictions, or runtime-only remapping. Explain the specific limitation; preserve an honest pending status until observed. Do not claim success based only on changing an Azeron label.

## Three clear diagrams for each game and layer

Produce separate images with the general arrangement of the user's Azeron software layout:

1. **Keys:** actual emitted keys/buttons, modifiers, chords and relevant press behavior.
2. **Actions:** game action names, with physical button numbers as location references.
3. **Keys + actions:** both on each button, using enough space and readable type.

Use the same physical geometry, orientation, button numbering, layer colors and title format across all three. Include the thumbstick and distinguish directions, click and mode. Use one image per layer and control context when combining them would crowd the labels. Split long labels into readable lines or keyed callouts; never silently omit actions to make an image fit.

Add game/build, layer, base-profile version, mapping revision/date and verification status. Mark unknown, default-only, user-changed and mod-added actions visibly using text or symbols as well as color. Show hold/double-press behavior and layer return controls where relevant. Preserve a clean editable layout/data source so all three images can be regenerated together after a binding changes. Check every displayed label against the mapping record before delivery.

## Design suggestions to evaluate with the user

- Start with a small number of layers: core gameplay, secondary/menu actions, and optional specialist actions. Keep movement and urgent actions accessible without awkward holds.
- Prefer a consistent layer button and a predictable route back to the base layer. Choose momentary versus toggle behavior deliberately and test held-key transitions to prevent stuck inputs.
- Keep a compact per-game list of deviations from the shared base. A special game profile should document the limitation that required it and its rollback.
- Use version numbers and a short change log so images, game configuration and Azeron exports can be matched. Re-check affected mappings after an input-changing mod or game update.

These are design suggestions, not authorization to assign new keys or change every installed game now.

## Storage and future behavior

Google Drive holds recovery exports, readable historical references, diagrams, per-game mapping records and private configuration backups. GitHub holds the reusable instructions, sanitized per-game mapping records, sources, change history and user-authored diagram/layout code when appropriate. Use both when it improves access and maintenance; keep private paths, identifiers, full logs, saves and third-party binaries out of Git.

For this repository, publish only to the canonical destination in [GitHub publishing](GITHUB-PUBLISHING.md). Verify the connected identity and remote. Keep the workflow discoverable from AGENTS.md and preferences/GENERAL.md so later tasks use it without making the user repeat the instructions.

Apply the workflow when a game is requested, installed or reviewed within the authorized task. This default does not authorize a bulk migration, arbitrary game launches, reminders, or resuming paused experiments. Record limitations and the next verification step rather than presenting planned work as complete.
