# Native Azeron Software v2 candidate — R5

Status: **four native-structure profile files generated; not imported or hardware-tested**.
Date: 2026-10-10. Owner: `dodWhatUp/install-modes-for-games`.

## Current input is sufficient

The user supplied the current full backup ZIP and an annotated screenshot archive.
No further export is needed to prepare candidate files. The previous "waiting for
native export" boundary is resolved. The backup identifies Azeron Software 2.0.2,
Cyborg II model code 8 and product ID 4855, with 18 software profile files.

The user's explicit correction is tag-based: only `layered 1` (called LAYER 1 in
the chat) and `FOR CHAT` identify user-authored profiles. Five profiles have
`layered 1`; one has `FOR CHAT`. The other 12 profiles are not evidence of user
preferences. `FOR CHAT` is a feature/schema demonstration, not a gameplay layout.
The extra `LAYER - 1 ?` profile is retained as a demonstration-linked object, not
silently selected as the production base.

## Deliverables and source roles

The private Drive archive contains:
- `Azeron_SHARED_R5_Profiles.zip`: delivery package with four individual native
  profile JSON candidates and the Hebrew guide. Extract it; do not use this
  delivery ZIP in the software's backup restore action.
- `Azeron_Backup_PLUS_SHARED_R5.zip`: alternative full backup candidate retaining
  all 18 original profile file bytes and adding four profiles, for 22 total.
- `Azeron_SHARED_R5_Complete_Package.zip`: private continuity/recovery package.
- The exact source backup and annotated screenshots, stored privately.

The generated profile names are `SHARED R5 - BASIC`, `SHARED R5 - NUMBERS`,
`SHARED R5 - LETTERS`, and `SHARED R5 - TOOLS`. All four have newly generated IDs.
The individual profile files omit unresolved global tag references. The augmented
backup registers a new `SHARED R5` tag for its four new files only.

Raw native profiles, the full application store, original UUIDs, device identity
and screenshot archives are not published here. This directory owns the reusable
compiler, validator, schema observations and sanitized validation results.
R3 remains the reviewed design source; R4 remains its corpus audit.
Neither `AI_MASTER.json` nor the inherited game catalogue was replaced.

## Implemented mapping

The 30 visible spatial positions now resolve to native IDs using the exported
model-8 UI button mapper and recognisable source bindings. This verifies the
software geometry, not finger comfort or real switch reach.

The new base follows the reviewed R3 keyboard map with 78 distinct logical outputs
including WASD. Primary Ctrl, Shift and Alt are explicitly left-side native codes.
All four candidates inherit the complete joystick input and profile settings from
the user's current `LAYER - 1 BASIC`. Extra nonvisual native input records are
preserved, not re-enrolled or assigned new actions.

The current authored source and its annotated preferred example use dedicated
**SINGLE -> Layering with Toggle on hold**, not the old V-tap/150ms long-press
setup. This is a current-project implementation observation, not a global
preference change. V remains an ordinary direct key.

| Base native button | Target |
|---|---|
| 2 | SHARED R5 - NUMBERS |
| 1 | SHARED R5 - LETTERS |
| 36 | SHARED R5 - TOOLS |

Each target contains a reciprocal link on the same native button. The intended
behavior is momentary entry with return on release. `isBelkin` is false, matching
the user's "Switch held binds on layer change" setting. Runtime behavior remains
unverified.

Two other layer selectors are disabled inside each secondary bank: release to
Basic before choosing another bank. These six selector cells are the only
intentional implementation differences from the R3 logical design. No nested
momentary-layer semantics are assumed. No macros, turbo, input sequences,
key latches, double-press actions or separate long-press actions were introduced
on the 30 visible controls.

## Validation and limits

Independent file readback checked all 120 mapped cells, 172 input records,
six layer links and native IDs/pins, fresh profile identity, profile settings,
complete joystick preservation and the absence of introduced active macros/turbo.
All 18 original profile files in the augmented archive compare byte-for-byte
identically with the source. Other application stores remain unchanged; the
software profile store only appends the new order records and tag. Original
active profile and mode are preserved.

The source archive timestamp remains the timestamp of that source snapshot,
not a claim that the augmented archive represents a later live state.

Single-profile import acceptance, importer ID remapping, full-backup restore,
physical press/release behavior and gameplay have **not** been tested.
An attempted read-only official-application import-handler inspection was blocked
by the platform. That operation was stopped, not retried or bypassed. Generation
therefore relies on the supplied native backup and screenshots, with a lower
assurance level than a real importer test.

Known R3/R4 game-access exceptions are not automatically fixed by native encoding.
A modifier or ordinary-letter chord on one finger, a cross-bank chord, and an
urgent numeric/F-key action remain separate design decisions.

## Import choice and next verification

Prefer the four individual JSON files, importing into SOFTWARE and preserving
the original maps. Multi-select all four only if the actual import dialog supports
it; otherwise import individually. The precise installed v2 menu path is not
asserted. If the app rejects a file or proposes replacing original profiles,
stop that route and retain the exact error rather than repeatedly reimporting.

After all four are present, select `SHARED R5 - BASIC` and check the three target
names plus their same-button reciprocal links. Import may regenerate IDs; this
behavior is unknown. A missing target can be selected again by its SHARED R5 name.
The user-supplied UI option "Set target button to switch back to this profile"
can be used to recreate the paired return link. Verify both ends' hold settings.

The optional full-backup ZIP is for backup restore, **not an additive merge**.
It may rewind app/profile changes made since the supplied snapshot. Do not restore
it over later work merely to avoid verifying three links. Take a fresh backup
before any import/restore and choose one route, not both. The full-backup route
has not been run and does not establish complete on-board recovery.

Next required user action: import the four candidates without replacing originals,
then check that each of buttons 1, 2 and 36 enters the correct bank and returns on
release with games closed. Native acceptance and hold/release observations will
determine whether any narrowly scoped correction is needed. No new export is
requested by this milestone.

## Reproduction

Python 3 standard library only; source ZIP and exact R3 design are required:

```text
python3 build_native_profiles.py --source-backup INPUT.zip --design ../layout_candidate.json --output NEW_OUTPUT_DIRECTORY
python3 validate_native_profiles.py INPUT.zip NEW_OUTPUT_DIRECTORY
```

The compiler refuses an existing output directory and unknown app/design versions.
Each new run generates fresh profile IDs. Do not repeatedly import independently
generated families with the same names. The original files are read-only inputs;
generated files are not installed automatically.
