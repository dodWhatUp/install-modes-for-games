# R8 preflight: current starting point before native integration

This is an implementation/readiness supplement, **not R9 or another native mapping family**. Start here, then continue the existing `r8/CODEX_COORDINATION.md`. The exact CORE5/SPARSE6 ZIPs and the 208 source-scoped action records are unchanged. Preserve every later Windows/R5/R6/R8 state. Do not use a recovery ZIP as a native Restore Backup.

## Obtain the exact files, not another user upload

Use the existing private `Azeron profile backups` Drive folder and the current publication receipt for this `r8/preflight/` folder. The full preflight ZIP includes the unchanged R8 CORE5/SPARSE6 ZIPs and exact R8 recovery. Earlier research/exports are nested inside that recovery. Raw profiles and review receipts stay private. Git owns these authored tools and instructions.

This preparation does not select a profile family or grant another running Codex session access. Check current repository heads, native app state and actual Windows access. The last connected-device check exposed only a Mac. The original Mac main checkout and the earlier task checkout are protected; use an isolated linked task worktree when writing.

## Independent work first

1. Confirm actual computer, supported runtime and paths. No app/game/driver install is needed for these Python tools. Python 3.9+ suffices; Node is optional for the display tests. An unavailable runtime is a concrete blocker, not permission to install a substitute silently.
2. Read this tool source before running it. The one-command rehearsal validates archived inputs and creates a new task directory only:

```text
python source/run_checks.py --r8 prior/Azeron_R8_Complete_Recovery.zip --out NEW_REHEARSAL_DIRECTORY
```

3. Locate actual PoE2/Cyberpunk configs using the existing known inventory and archives. Use **`preflight/input_evidence.py`**, not the older `r8/collect_input_evidence.py`, for new evidence collection:

```text
python source/input_evidence.py --poe2-file VERIFIED_EXISTING_CONFIG.ini --out NEW_PRIVATE_POE_RECEIPT
python source/input_evidence.py --cyberpunk-settings VERIFIED_UserSettings.json --cyberpunk-mapping VERIFIED_inputUserMappings.xml --out NEW_PRIVATE_CP_RECEIPT
```

Read-only collector v2 rejects conflicting duplicate JSON/mode fields and does not publish a success-like receipt if its final source recheck fails. Source files/parents must be regular paths without symlink/reparse indirection. Unsupported paths or denied access stop that source read; do not bypass them. The output deliberately remains CONFIG_CANDIDATE_NOT_EFFECTIVE. Numeric encoding/flags and conflicting action banks must not be decoded by assumption. A valid receipt contains selected input fields only, not a full original backup.

## Inspect before importing a chosen family

The actual family choice remains unresolved unless a newer user decision exists. Complete the read-only work before asking that one consequential question. Do not install both to avoid making the choice.

Take a new complete private native backup through a supported route. Review that export against the exact candidate ZIP:

```text
python source/native_review.py --candidate profiles/Azeron_R8_CORE5_Profiles.zip --current ACTUAL_BEFORE_EXPORT.zip --family CORE5 --out NEW_PRIVATE_PREIMPORT_REVIEW
```

For SPARSE6 use its corresponding ZIP and `--family SPARSE6`. The tool supports the observed v2 backup ZIP, individual native profile JSON, a list of native profiles, or a clearly labeled review collection. It does not infer unknown export wrappers or crawl profile directories.

An identical/remapped family result means **do not re-import**. Same-name differences, ID collisions, partially present families and unresolved references require inspection. `ALL_ABSENT_IMPORT_REMAINS_A_SEPARATE_ACTION` is not an installer approval. Keep the just-in-time backup, current state and later edits; an earlier recovery snapshot is not sufficient to protect recent work.

## Authorized native integration, then independent readback

After the family choice and installation authority are clear, import only its individual JSONs additively through the supported native route. No full-store reset, forced import, repeated blind attempts or other-session interference. If the importer regenerates IDs, reconcile actual target names instead of guessing UUIDs.

Obtain a new export after the operation and compare it with both the candidate and the before snapshot:

```text
python source/native_review.py --candidate profiles/Azeron_R8_CORE5_Profiles.zip --current ACTUAL_AFTER_EXPORT.zip --before ACTUAL_BEFORE_EXPORT.zip --family CORE5 --out NEW_PRIVATE_POSTIMPORT_REVIEW
python source/render_review.py --receipt NEW_PRIVATE_POSTIMPORT_REVIEW/NATIVE_REVIEW.json --out NEW_PRIVATE_REVIEW.html
```

The review checks all original profiles for disappearance or changes, not only the new family. It separates enumerated display/time metadata from operational fields, while comparing unknown operational fields, pins, timing, active layer targets and joystick settings conservatively. Preserve and inspect every difference. Snapshots remain file evidence; app/hardware/game tests are separate.

## Physical and game checks

Use `PHYSICAL_TEST_PLAN.json` and `EXECUTION_RECEIPT.template.json` as a bounded checklist, not a new task queue. No physical test is marked passed in this package. Start with games closed and a supported native input inspector. Ask the user only for the exact physical press that remote tools cannot perform. Stop on unexpected output, stuck input, discomfort or unknown state.

Test each momentary selector and reciprocal release; Ctrl5/Shift9/Space14 outputs; primary Alt3 and T31 with movement; meaningful number/modifier combinations; and release order. NAV/SYMBOLS occupy the thumb, so they do not promise simultaneous independent stick movement. #19 remains disabled and is not yet an external trigger. Do not assign F13 or another trigger without an explicit approved integration design.

Then reconcile game actions with their actual settings, starting with PoE2/Cyberpunk. Preserve graphics-tool owners (Home/OptiScaler, Delete/ReShade, etc.) and per-game exceptions. Use safe game contexts only within existing authorization; do not load saves, reset settings, resume benchmarks or broaden input/capture privileges merely to increase the test count.

## Display and handoff

`Azeron_R8_Action_Atlas_Checked_HE.html` is a display-only derivative. It retains all 29 allowed digital slots and all R8 outputs. It adds exact left/right modifier availability from the candidate files and optional conditional tool-owner warnings. No active tool stack is detected. Live layer observation, Peek/pin, Windows browser rendering and games remain unverified. Do not retry/bypass the earlier denied browser route.

Save complete native/config receipts privately; publish only sanitized results and current continuations in the canonical gaming repository. The existing PR4/PR2 routes are coordination pointers, not proof that a live task consumed the update. Record actual consumption and execution separately. No new scheduler, queue, remapper or global preference is created.
