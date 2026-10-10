# Azeron cross-game controls — current research and design

## Current work: Stage B R3

Read [Stage B R3: candidate maps, audit and implementation boundary](stage-b/README.md)
for the current design. Four proposed banks retain 78 logical outputs.
The 107-case conservative finger-group audit reports 90 model routes, 16
conflicts and one missing direct input; it is not a hardware or gameplay test.

**Next required input:** a current native JSON export of the Azeron Software v2
software profile collection, including the four linked layers. No active
profile has been modified, and the design JSON is not importable.

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
This root file is now a navigation index; historical source files were not deleted.

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
