# SHARED R5 live import and verification results

Date: 2026-10-11  
Device: Azeron Cyborg II, model code 8 / product code 4855  
Software: Azeron Software 2.0.2

## Result

The four candidate profiles are present in the app's SOFTWARE collection:

- SHARED R5 - BASIC
- SHARED R5 - NUMBERS
- SHARED R5 - LETTERS
- SHARED R5 - TOOLS

The app showed 19 SOFTWARE profiles before the addition and 23 afterward. Each new profile is marked as a software profile, has 43 inputs, and has a distinct profile identity. The four were appended without replacing the existing profile files.

The profiles became visible after being placed in Azeron's existing per-profile software store using its native JSON format, then loaded by Azeron Software. The app's Import profiles file chooser was opened but the file selection could not be completed through the available computer-control interface. Therefore the app has loaded and recognizes the profiles, but acceptance by the Import profiles dialog was not verified. Do not blindly import the same IDs again; inspect the existing SOFTWARE list first.

## Link and runtime checks

Static readback of the loaded profile files verified the BASIC links:

- Button 1 → LETTERS (hold)
- Button 2 → NUMBERS (hold)
- Button 36 → TOOLS (hold)

Each secondary profile's matching selector links back to BASIC on release.

With no game process active, Azeron's live event log registered repeated press/release cycles for buttons 1, 2, and 36. The live layer-change entries matched LETTERS, NUMBERS, and TOOLS on press and BASIC on release. The app's current accessible state after those cycles showed BASIC selected.

This verifies the live device-to-app layer transitions outside a game. It does not verify in-game prompts or gameplay behavior. Normal key outputs, modifier/chord ergonomics, joystick-mode behavior, and the absence of unintended output from every other mapped button were not part of this test.

## Recovery

A fresh pre-change storage backup and a four-profile export package were saved privately to the existing Drive folder. The Drive report includes private recovery links and hashes. No profile UUIDs, private paths, raw logs, or recovery archives are stored in this public repository.

The companion request for a per-game action-label overlay on one stable physical map is documented in [AZERON-GAME-KEYMAP-VIEWER-WISHLIST.md](../../../../../docs/AZERON-GAME-KEYMAP-VIEWER-WISHLIST.md). Selecting a game's overlay is display-only and must not remap or switch the Azeron profile.
