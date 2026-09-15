# Azeron and game controls — default workflow

User instructions confirmed 2026-09-15. Apply this workflow to every game when controls, keypad profiles, related mods, or keybinding diagrams are in scope.

## Desired result

Use one consistent Azeron base setup with multiple layers. Create a separate game-specific Azeron profile only when the shared setup cannot reasonably support that game's controls. Keep common physical actions in consistent positions so muscle memory transfers between games. Adapt the game's own bindings when practical, including the bindings represented by its gameplay prompts.

The current retained software profiles are to be named **GENERAL 1**, **GENERAL 2**, **GENERAL 3**, and **EMPTY**. These names replace FPS - GENERAL 1/2/3. They are the retained starting point; this instruction does not claim that a new universal layered layout has already been designed or tested.

On Azeron Software 1.x, a logical layered setup can consist of several linked software profiles. The original Cyborg manual documents profile switching, optional return while holding a layer button, and behavior for keys held during a transition. Layers and macros require software mode. Confirm the exact model, board, software and firmware before choosing implementation or migrating versions. See the [official manual, sections 5.2.10 and 5.6](https://site-835705.mozfiles.com/files/835705/Azeron_Cyborg_Manual_V6_5.pdf).

## Preferred layer-button behavior

User clarified 2026-09-15: preserve a normal action on a short tap of the layer button. Enter the secondary layer only after a brief long press, keep it active while the button remains held, and return automatically to the base layer when released. Do not require a second press to return.

The current chosen control is **GENERAL 1 button #6**: tap retains keyboard **V** (historical label: melee), hold for **150 ms** enters **GENERAL 2**, and release returns to **GENERAL 1**. Treat 150 ms as the selected starting threshold; adjust it only in response to the user's testing. Do not replace the normal tap binding with a dedicated immediate layer switch unless the user changes this preference.

In Azeron 1.5.6, assign the target profile under **Long Press → Layering**, enable **Toggle on hold**, and retain the normal action under **Single Press**. Do not use the second-press return option as the return mechanism. Leave Double Press disabled unless separately requested. The installed 1.5.6 software handler distinguishes a short tap from a long hold: with this combination, the tap output occurs on release before the threshold, while a long hold executes the long-press action. Thus an action on initial button-down and an exclusive hold action cannot both be promised without a timing tradeoff. Verify this behavior again after software/firmware changes.

Test quick taps, sustained holds, repeated transitions, and another bound button pressed while the layer is held. Confirm release returns to the originating base profile without a second press, unintended tap action, or stuck output. Check game recognition separately; do not claim the historical V/melee label proves a particular game's effective binding.

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

## Steam layouts and reinstalling a previously configured game

User extension confirmed 2026-09-15: restoring the game's own bindings is a default step when configuring or reinstalling any game with an existing saved keybinding setup.

Steam Input layouts and the game's own keybinding settings are separate records. Steam Input can translate supported controller inputs into keyboard, mouse or controller output, or use a game's native Steam Input actions. A saved Steam layout alone does not establish that the game restored its keyboard bindings or prompts. Do not assume every Azeron keyboard key is exposed as a remappable Steam controller input. Check the actual device/input mode and avoid adding a second remapping layer without a purpose. See [Valve's legacy-mode documentation](https://partner.steamgames.com/doc/features/steam_controller/legacy_mode).

Where Steam Input is applicable, save a personal layout, record its exact game/AppID, controller/input type, layout name/version and verified restore reference, and retain an export if available. Do not publish it as a community layout unless asked. Keep the game's own binding files and mod bindings in the recovery archive as well. Steam Cloud synchronizes only files selected by the game/developer; verify whether keybinding files are included rather than treating Cloud as a complete backup. See [Steam Cloud documentation](https://partner.steamgames.com/doc/features/cloud).

Default reinstall/configuration sequence:

1. Identify the exact game, edition, store/AppID and build. Search Drive and the repository for its prior mapping record, configuration backups, Steam layout, mods, diagrams and history.
2. Inspect the reinstalled game's active binding files or supported settings interface and relevant mod configurations. Compare saved mappings with current defaults, schema changes and any newer user changes. Preserve the current state before writing; do not replace newer changes blindly.
3. As part of the authorized keybinding setup, restore or adapt both the shared Azeron setup and the game's own bindings so the intended physical-button-to-action mapping agrees. Restore Steam Input only if it is part of that setup. Handle launcher/Cloud rewrites and missing mod actions explicitly.
4. Prefer supported edits with the game closed. Read back and validate the effective configuration. If a game stores bindings only through its UI, explain that limitation and use the game UI when the requested task permits it. Do not claim visible gameplay prompts are verified without observing them.
5. Check layer links, modifiers, contextual actions and overlapping mod/overlay hotkeys. Record configuration, gameplay and prompt verification separately. Keep unresolved actions visibly pending.
6. Regenerate keys, actions and combined diagrams from the reconciled mapping record. Save the final version, recovery export, restore instructions and change history to Drive and sanitized records to GitHub, as appropriate.

## Three clear diagrams for each game and layer

Produce separate images with the general arrangement of the user's Azeron software layout:

1. **Keys:** actual emitted keys/buttons, modifiers, chords and relevant press behavior.
2. **Actions:** game action names, with physical button numbers as location references.
3. **Keys + actions:** both on each button, using enough space and readable type.

Use the same physical geometry, orientation, button numbering, layer colors and title format across all three. Include the thumbstick and distinguish directions, click and mode. Use one image per layer and control context when combining them would crowd the labels. Split long labels into readable lines or keyed callouts; never silently omit actions to make an image fit.

Add game/build, layer, base-profile version, mapping revision/date and verification status. Mark unknown, default-only, user-changed and mod-added actions visibly using text or symbols as well as color. Show hold/double-press behavior and layer return controls where relevant. Preserve a clean editable layout/data source so all three images can be regenerated together after a binding changes. Check every displayed label against the mapping record before delivery.

## Design suggestions to evaluate with the user

- Start with a small number of layers: core gameplay, secondary/menu actions, and optional specialist actions. Keep movement and urgent actions accessible without awkward holds.
- Keep the chosen layer button consistent and follow the short-tap/long-hold/automatic-return preference above. Test held-key transitions to prevent stuck inputs.
- Keep a compact per-game list of deviations from the shared base. A special game profile should document the limitation that required it and its rollback.
- Use version numbers and a short change log so images, game configuration and Azeron exports can be matched. Re-check affected mappings after an input-changing mod or game update.

These are design suggestions, not authorization to assign new keys or change every installed game now.

## Storage and future behavior

Google Drive holds recovery exports, readable historical references, diagrams, per-game mapping records and private configuration backups. GitHub holds the reusable instructions, sanitized per-game mapping records, sources, change history and user-authored diagram/layout code when appropriate. Use both when it improves access and maintenance; keep private paths, identifiers, full logs, saves and third-party binaries out of Git.

For this repository, publish only to the canonical destination in [GitHub publishing](GITHUB-PUBLISHING.md). Verify the connected identity and remote. Keep the workflow discoverable from AGENTS.md and preferences/GENERAL.md so later tasks use it without making the user repeat the instructions.

Apply the workflow when a game is requested, installed or reviewed within the authorized task. This default does not authorize a bulk migration, arbitrary game launches, reminders, or resuming paused experiments. Record limitations and the next verification step rather than presenting planned work as complete.
