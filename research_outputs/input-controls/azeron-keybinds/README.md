# Azeron cross-game controls — current research and design

## Current revision: R6 research, native candidates and HTML prototype

Read [R6 decision record and delivery](stage-b/native-v2/r6/README.md) first.
It implements reserved index-side **button 19**, renames LETTERS to **MENUS**,
and supplies two separate native candidate families: **COMPACT (4 layers)** and
**SPARSE (5 layers)**. The sparse alternative leaves nine additional finger
cells empty using the authored source masks. Both retain 78 logical outputs,
but their simultaneous-movement accessibility differs. No R6 import or game
execution was performed here.

The keys-only HTML prototype preserves all 29 remaining digital controls per
layer, including the little-finger side and bottom controls, while omitting
button 19 and the joystick drawing. It is not a live layer detector. Earlier
AI-generated game posters are rejected as mapping evidence.

The research adds six cognition/motor and seventeen game/manufacturer source
records and tracks 23 requested game/edition scopes. Those scopes are **not**
23 complete verified default tables. Current effective game keys remain an
explicit prerequisite for final action labels. The original 94-record/2,195-row
research corpus is retained rather than silently replaced.

Private delivery locations and hashes are in the
[R6 publication manifest](stage-b/native-v2/r6/PUBLICATION_MANIFEST.json).
Read [current execution handoff](stage-b/native-v2/CODEX_IMPORT_HANDOFF.md)
before any later authorized device change. Publication is not installation.

**Related live evidence:** draft [Codex PR4](https://github.com/dodWhatUp/install-modes-for-games/pull/4)
reports R5 loaded in the app's native store and live #1/#2/#36 return-on-release
outside games. Preserve that R5 and later work. The report does not validate
R6, game behavior, or the Import profiles file chooser. No PR merge or adoption
of its proposed instruction changes was performed in this revision.

## Prior delivery: R5 native-profile candidates

Read [R5 native v2 files, schema notes and import boundary](stage-b/native-v2/README.md).
The current 2.0.2 backup and annotated screenshots have now been received.
No further export is needed to prepare candidate files. Four separately named
SHARED R5 native-structure profiles were generated, with native button IDs,
six paired layer links and the current dedicated single-press hold behavior.
Only tags `layered 1` and `FOR CHAT` identify user-authored source profiles;
the other presets are not preference evidence. All originals remain unchanged.

The four-JSON delivery and optional augmented full backup are in the private
Azeron Drive archive. Their original authoring milestone checked file structure;
see the newer related live report above rather than repeating an obsolete
instruction to import R5. Full-backup restore is not a merge and may rewind
changes since the snapshot.

## Prior corpus audit: R4, design unchanged

Read [R4 corpus audit](stage-b/corpus-audit/README.md) alongside the R3 design.
All 2,195 inherited R2 binding rows were processed; 2,167 expressions parsed
and 28 remain for manual review. The audit identifies same-bank gaps,
ordinary-letter modifiers, stick/command-role conflicts and real instances of
R3 regressions. It does not add games, change the map or verify all current
source defaults. Fourteen rows received targeted primary-source rechecks.
The export prerequisite recorded during R4 was resolved by R5 above.

## Design reference: Stage B R3

Read [Stage B R3: candidate maps, audit and implementation boundary](stage-b/README.md)
for the reviewed design. Four proposed banks retain 78 logical outputs.
The 107-case conservative finger-group audit reports 90 model routes, 16
conflicts and one missing direct input; it is not a hardware or gameplay test.

R3's design JSON remains non-importable. R5 is its separate native-structure
implementation candidate; R6 is a later, separately identified design revision.
No active device profile was changed by this R6 authoring session.

## Research sources and versions

- [R1 research master](AI_MASTER.json): 74 game/edition/layout records and
  1,747 binding observations. This editable baseline remains unchanged.
- [R2 extension and coverage audit](extensions/2026-10-10-r2/R2_UPDATE.md):
  20 additional records and 448 bindings, yielding a combined derived view
  of 94 records and 2,195 bindings.
- [R2 extension manifest](extensions/2026-10-10-r2/EXTENSION_MANIFEST_R2.json)
  identifies the additive records and their sources.
- [R2 map proposal](extensions/2026-10-10-r2/STAGE_B_DRAFT_R2.json) remains
  available for comparison; it was not installed.
- [Stage B design source](stage-b/layout_candidate.json) is a separate
  design object, not a competing research-facts master.

The full prior R1/R2 README, including reproduction instructions and source
qualifications, is preserved at the verified pre-R3 revision:
[historical research guide](https://github.com/dodWhatUp/install-modes-for-games/blob/5b1e015dbbe9b31f25d2e6b557c3758fc55219ba/research_outputs/input-controls/azeron-keybinds/README.md).
This root file is a navigation index; historical source files were not deleted.

## Evidence boundaries

The catalogue is a representative documented sample, not complete current
defaults for every game. R2 rechecked 111 earlier rows against sources; 1,636
earlier rows were not re-read online. Old manuals, port documentation,
prelaunch/early-access tables and preset ambiguities retain their qualifiers.
Key presence is not observed press frequency or urgency.

R1 has 76 direct binding-source URLs and two context URLs. Its exact master
blob remains `f45e3d7c1fdd3279b96cbe45752fad775cc46584`. R2 was published
as an additive extension rather than reconstructing unavailable source bytes.
Exact R1 bytes were recovered and hash-verified during R3, but no consolidated
master replacement has been published.

Git holds editable owner records; spreadsheets and HTML are derived delivery
views. Source publication, design acceptance, native configuration, physical
comfort and gameplay verification are separate states.
