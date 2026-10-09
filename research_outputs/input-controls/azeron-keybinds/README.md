# Azeron Cyborg II keyboard research — Step 1

Status: **ready for layout judgment within the stated research scope**. This package is research, not an accepted device configuration.

## Start here

`AI_MASTER.json` is the single editable research master. The spreadsheet, readable HTML report, catalogue view, collection exports and aggregate counts are derivatives. Do not maintain an independently edited copy of the master in another location.

The collection contains **74 game/edition/layout records, 1,747 documented binding entries and 76 URLs directly supporting binding rows**. Two further registered URLs support context or caveats. Records span eight broad genre families. Source families comprise 47 publisher/developer records, one project-documented record, ten community records and sixteen independent reported-control records.

The schema follows Research OS portable records v1 (`schemas/master.schema.json`, method snapshot `57b12ccf2ac0aac21d40490c734164c22f39249f`). Raw binding entries and source scope are retained; normalized constituent keys and analyst interpretations are distinguishable. The raw entries include researcher classifications, so only the observed action/key/context fields are source-reported control facts. Urgency and inferred hold/repeat labels are not telemetry.

## Recommended starting architecture

Start with **one logical map family and four conceptual layers**:

| Layer | Key family | Access requirement |
|---|---|---|
| Base | Movement, raw modifiers, immediate action keys and urgent numeric duplicates | Fast or continuously held inputs remain directly accessible. |
| Numbers | Top-row 1–9, 0, minus and equals | Keep a complete mnemonic bank while duplicating urgent numbers on Base. |
| Letters / panels | Remaining letters, deliberate panels, Enter and Backspace | Key-family grouping is stable; individual games may require immediate exceptions. |
| Functions / navigation | F1–F12, navigation and necessary punctuation | Check combat, target and sustained-input uses before treating a key as slow. |

Four is a practical starting architecture, not a mathematically proven minimum. No physical IDs or native v2 profile settings are assigned. A separate Hotbar base or RTS Grid base is justified only by a demonstrated access problem. These are different patterns; a strict two-map ceiling is not supported. Specialist simulations may require more commands, while continuing to reuse the utility banks.

Assess reaction deadlines, sustained presses and simultaneous combinations before inferred repetition. Use cross-game key presence and mnemonic grouping to break ties. A function key, number or arrow can be urgent. Warframe ability numbers, GW2 healing on 6, FFXIV party-target function keys, Alien: Isolation held peeking, and RTS command grids are documented examples in the master.

Layer selection does not isolate a raw key from a game or graphics-tool listener. Keep selector positions, movement mode, cancellation and needed raw modifiers predictable. Verify the installed Software v2 behavior before depending on tap/hold timing or held-key transitions; the linked older manual is not a runtime test of v2.

Date convention: master timestamps and normalized source access dates are UTC. Original collection metadata retains the session local date, which crossed into the following calendar day.

## Coverage and interpretation

- The records are representative samples, not complete control tables for every game or a census of the PC market.
- Historical manuals, legacy guides, specific input presets and Feral Mac/Linux port documentation keep their explicit qualifiers. Current Windows defaults are not assumed.
- No current installed game was tested. The source inventory includes legacy Cyberpunk, original WoW/Skyrim manuals, a historical ESO guide, Diablo IV prelaunch and other scoped snapshots.
- PoE2's older source has unresolved preset/context collisions. Conflicting rows were omitted; the complete current combat preset remains unknown.
- Hades and Dota 2 weak tables were excluded. The 40 excluded attempt records include duplicates and four titles later covered. `coverage_audit.json` reconciles this to 35 wholly unrepresented title keys and one current-Cyberpunk scope gap; do not report 40 additional uncovered games.
- The normalizer found 1,735 fully parsed expressions, nine partial and three unparsed. Original expressions remain intact. Parsing extracts constituents, not executable chord or sequence semantics.
- Top-row and numpad keys remain distinct. Left/right modifiers retain their exact labels; the aggregate key-coverage view groups their aliases. Symbols are not silently converted to assumed US physical key positions.
- Distinct-game key presence is neither press frequency nor urgency. Missing a key from a short source table does not establish that the game never uses it.

The broad genres are Action & adventure (17), RPG & action RPG (15), Shooter (14), Strategy/tactics/MOBA (9), MMORPG (5), Survival/sandbox (6), Building/management (4), and Driving/flight simulation (4).

## Reproduce the derivatives

`build_research.py` uses the Python standard library. `build_workbook.mjs` requires the supplied `@oai/artifact-tool` runtime and authors the workbook only through that package. No new packages are required in the authoring environment.

```bash
python3 build_research.py --master AI_MASTER.json --output derived
node build_workbook.mjs derived/catalogue_view.json derived
```

An optional `--profile` JSON supplies private profile-review paragraphs for the readable report. Private profile material is not part of this public source package. Without it, the report contains the full general research and catalogue.

To revise source-level bindings and rerun normalization, edit the canonical observations/metadata, regenerate temporary collection inputs, and run the normalizer. Review the resulting counts and source notes before replacing the master:

```bash
python3 build_research.py --master AI_MASTER.json --output working --export-inputs
python3 normalize_bindings.py --input-dir working
python3 build_research.py --catalogue working/consolidated.json --output reviewed
```

The generated `working` files are intermediates, not additional masters. Retain the old master in Git history and review a diff before accepting a revision.

## Verification and next boundary

The authoring checks reconcile the complete catalogue, key-presence counts, all workbook binding IDs and raw key strings, and exported table/freeze structures. The workbook's six tabs were visually inspected. These checks cover generated artifacts; no native Excel session or device/game runtime was tested.

The next implementation boundary is to inspect the active v2 export, identify physical IDs and comfortable simultaneous presses, verify selected in-game presets and overlay conflicts, then produce a reviewable button map and separate keys/actions/combined diagrams. This package does not migrate or overwrite existing profiles.
