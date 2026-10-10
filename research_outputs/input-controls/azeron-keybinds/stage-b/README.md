# Stage B — conservative R3 layout candidate

Status: **design candidate; not adopted; not a native Azeron export**.
Date: 2026-10-10. Owner: `dodWhatUp/install-modes-for-games`.

## Read this first

`layout_candidate.json` is the editable source for this Stage B design. It does
not replace `../AI_MASTER.json`, and must not be imported into Azeron Software.
The prior R2 design remains in
`../extensions/2026-10-10-r2/STAGE_B_DRAFT_R2.json`.

This update does not add games. Research scope remains 94 scoped game/layout
records and 2,195 inherited binding rows. The current user action is to supply
a **fresh native Software v2 JSON export of the software profile collection**,
including all four linked layers. No additional application is needed.

## Changes from R2

- Keep four banks and 78 logical outputs, including WASD movement.
- Leave R1C1, R2C1 and R5C1 empty in secondary banks: the conservative model
  already assigns that finger to the held selector.
- NUMBERS gets alternate Ctrl and Shift positions. The model finds independent
  routes for Ctrl, Shift and Ctrl+Shift with every digit 0–9 while moving.
  This is not a measured comfort or reaction-time result.
- F1–F9 mirror the corresponding numeric positions.
- Primary Ctrl, Shift, Alt, Space, Enter and Esc stay at the same positions
  across the four proposed banks.
- Only three BASIC assignments change from R2: swap Alt/G and fill the formerly
  empty ST_D position with Backspace. T and Z are not moved to the thumb merely
  to satisfy one test. The other existing blank BASIC slot stays blank.

All position names are visual coordinates from the supplied software diagrams,
not enrolled hardware button IDs. Column-to-finger correspondence is an
explicit hypothesis; neither comfortable reach nor two-switch use by one
finger was measured.

## Audit and tradeoffs

The 107 deliberately selected static cases contain source-backed examples and
analyst stress cases, labelled separately. Many are numeric variants, so their
counts are not a representative distribution of gameplay.

| Result | R2 | R3 |
|---|---:|---:|
| Independent-finger route in the model | 63 | 90 |
| Finger/selector/thumb conflict in the model | 41 | 16 |
| Required key missing from the selected bank | 3 | 1 |

There are 33 newly model-routable cases and **six lost routes**: Alt+6, Alt+9,
Shift+F2, Shift+F5, Shift+F8 and Shift+F11. Do not hide those regressions or
turn the counts into an improvement percentage.

Remaining concerns include BASIC Shift+C/2/4 and Ctrl+1/3, NUMBERS Alt+3/6/9,
TOOLS Shift+F2/5/8/11, and arrows sharing the thumb with movement.
GW2 healing on 6 has a layered route, but the direct-BASIC requirement remains
unsatisfied. A targeted game-side rebind or a justified hotbar base is still
needed for that use case.

The optional direction-access delta replaces only BASIC's direct 1–4 copies
with up/down and left/right arrow pairs on different columns. It is not applied
and is not a new assumed game default.

## Source corrections carried forward

The previous FAIRY TAIL 2 Tab+1–4 scenario was too broad: the official manual
assigns skills to 2/3/4 and holds Tab to change the skill sheet. The compound
Tab+2/3/4 is a derived requirement, while Space+1 and Space+2 are explicitly
documented chords.

For osu!taiko, the documented large-note pairs are X+C and Z+V. The old X/V
same-column observation is not evidence that X+V must be simultaneous.
The correct pairs already have model routes in both BASIC drafts. A new
rhythm map is not justified by that earlier scenario alone.

Sources and exact qualifications are in `layout_candidate.json`; urgency and
movement stress are not attributed to telemetry.

## Reproduce

Python 3.9+ standard library is sufficient for the static cases and audit:

```text
python3 generate_cases.py
python3 validate_layout.py
python3 render_report.py
```

The validator reads the retained R2 file through its relative repository path.
A portable package instead supplies the explicitly derived comparison snapshot
`baseline_r2_for_comparison.json`. Generated `cases.json`, `validation.json`,
the HTML report and workbook are views/results, not competing source masters.

`build_workbook.py` requires the installed `artifact_tool` authoring runtime.
It uses no openpyxl, pandas or office application. The workbook is a Stage B
companion, not another 94-game research master.

The stdlib rebuild succeeded, regenerated cases were byte-identical and the
audit matched. All 120 workbook map cells and 107 case rows were checked;
formula counts matched and the formula-error scan was empty. The authored
workbook overview was rendered for visual review. The HTML contains 120
source-matched key cells and 107 cases, no external scripts/images, and blocks
network connections. Browser interaction was not tested.

## Native implementation boundary

The exact installed v2 schema, hardware IDs, keyboard layout, left/right
modifier output, stick mode and gesture behavior remain unknown.
The historical V-tap / exclusive 150 ms hold preference is preserved as
context, not overwritten or assumed to describe current v2 settings.

Before implementation, reconcile a current native export with the user's later
changes, create a separate candidate without replacing the active setup, and
then verify key-down/up, selector release, movement, duplicate-modifier handling
and game-facing behavior. Use one copy of each modifier per initial chord;
release its output before leaving the bank until transition behavior is tested.

No game/device setting, application, firmware or profile was installed.
Only a Mac was online through the remote connector; the Windows gaming device
was unavailable. No screen/video capture or global input logging occurred.

The original R1 master was recovered into a task-specific temporary directory
through a permitted text-only remote read and its exact Git blob hash matched
`f45e3d7c1fdd3279b96cbe45752fad775cc46584`. It was not reconstructed or overwritten.
R1/R2 semantic integration into that master is still separate from this design.

An unrelated draft overlay PR was left untouched. Publication of this design
does not adopt it or merge that other work.
