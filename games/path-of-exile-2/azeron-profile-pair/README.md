# PoE 2 Azeron profile pair

**Latest: [GROUPED R2](../grouped-r2/README.md).** The first pair below became
visible after the user fully closed Azeron Software through Task Manager. This
folder retains the original export; current user edits are preserved privately.
Use R2 for the newer grouped skill layout.

## Status

Two native Azeron Software 2.0.2 profiles are present in the local software profile library on 2026-10-12:

- **PATH OF EXILE 2 - COMBAT** — select this as the primary profile.
- **PATH OF EXILE 2 - MENU** — linked secondary layer.

The pair was created from the current **SHARED R8 SPARSE6 - BASIC** native profile structure. Existing shared and older profiles were left in place.

## Layer control

Button **#6** (R3C2) emits **V** on a tap. Holding it for **150 ms** enters **PATH OF EXILE 2 - MENU**; releasing it returns to **PATH OF EXILE 2 - COMBAT**. The reciprocal long-press target is encoded in both profiles using the existing Azeron Software 2.0.2 profile pattern.

The thumb menu controls and shared actions remain available in both views: #28 Tab, #29 I, #22 C, #31 G, #30 P, #23 K, #41 Enter, and #20 Escape. Movement remains the W/A/S/D analog mapping from the R8 source.

## Limits and next check

The profile JSON readback confirmed 43 input records per profile, reciprocal #6 layer links, 150 ms hold values, unchanged R8 source, and the same analog-stick configuration. The app's log shows 29 software profiles loaded before this pair was written, and the same Azeron process is still running. Its close button is configured to minimize to the tray, so use **Exit** from the tray menu to fully close it, then reopen the app. The profile pair has not been selected, read back from the physical device, or checked in gameplay.

The saved proposal identifies unresolved behavior: movement mode, Ctrl's overlap with the skill-bar toggle, the proposed temporary-skill keys 6 and 7, unbound flask slots 3 and 4, and Escape's in-game action. Treat those as pending until the game prompts and behavior are checked.

Choose **PATH OF EXILE 2 - COMBAT** as the primary profile after the full application restart. If the pair still does not appear, use Azeron's profile-list menu item **Import profiles from a folder** and select the `import-folder` directory beside this README. Then verify a short #6 tap, a sustained hold, automatic return on release, and one key pressed while MENU is held.

## Recovery

A just-in-time ZIP of the original 29 profile files and both GlobalStore files was created before adding this pair and uploaded to the private Azeron Drive folder. A second local ZIP preserves the two profile JSONs before the full-title rename. The Drive file is named **Azeron profiles before POE2 COMBAT MENU 2026-10-12.zip**. The new profiles are additive; restoring the snapshot or removing only the two profiles by ID rolls back this change.
