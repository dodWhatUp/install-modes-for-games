# Azeron research R2 — extension, QA and Stage B draft

Date: 2026-10-10. Status: **READY_FOR_DESIGN_WITH_GAPS**.
This is the existing input-controls workstream, not a new master, device enrollment, installation or adopted profile.

## Start with these records

- `EXTENSION_MANIFEST_R2.json` defines the additive extension, source index and row schema.
- `GAMES_A_R2.json` and `GAMES_B_R2.json` contain its 20 game records and 448 binding rows. Trailing empty fields are omitted; use the manifest's row_fields. Row identity is game ID plus its one-based row ordinal, e.g. add_nioh3_001.
- `STAGE_B_DRAFT_R2.json` contains all 30 visual positions for each of four banks, explicit invariants, target keys and unresolved conditions.
- The existing `../../AI_MASTER.json` is unchanged. Exact original master bytes were not available in this authoring runtime. Do not overwrite it with a model reconstruction.

The combined workbook/report use the original uploaded workbook (74 records / 1,747 raw binding rows) plus this extension, producing **94 records / 2,195 bindings**. They are derivatives, not a second canonical master. The extension has 22 distinct source URLs; the combined source registry has 100, including context-only references.

Derived delivery snapshots in the existing private Azeron archive:
- Workbook: https://drive.google.com/file/d/1T7uqzcW_eOFFCLdTlgp5oFJ8FSkBE9SE/view
- Hebrew report: https://drive.google.com/file/d/1_YaADoy9dvlk-j3EaFqZEHts8E2Be0-c/view

## What was added

Nioh 3; FAIRY TAIL 2; Wo Long Complete Edition; NOBUNAGA'S AMBITION: Awakening; Atelier Yumia; Control Resonant; REMATCH; Paralives early-access layout; Resident Evil Requiem; PRAGMATA; Hollow Knight: Silksong; Split Fiction; StarRupture early-access layout; Tony Hawk's Pro Skater 3 + 4; Cronos: The New Dawn; Heroes of Might and Magic: Olden Era; Indiana Jones and the Great Circle; NetHack 3.6.7; osu! standard/taiko; Kunitsu-Gami.

Five added games use publisher manuals, two use project guides, and thirteen use original observed-control/test reports from Prima. The latter are firsthand reports, not official support, and share an outlet/method dependence. Era labels are grouping aids, not a certified release-date table. Rulesets and collections are not split into extra games to increase the count.

## Verification actually performed

All 2,195 binding IDs are unique. No missing core game/action/key/source fields or exact duplicate groups were found. Original raw key expressions and their context/gesture notes are retained. The 448 new rows were extracted this revision, with explicit source type and locator. Source subsets are not promoted to complete installed presets.

A targeted second source pass matched key/action pairs for **111 old rows**:
- Warframe: 18, https://www.warframe.com/en/game/quickstart
- Final Fantasy XIV: 30, https://na.finalfantasyxiv.com/game_manual/operation/
- Alien: Isolation: 19, https://www.feralinteractive.com/en/manuals/alienisolation/latest/steam/
- Shadow of the Tomb Raider: 23, https://www.feralinteractive.com/en/manuals/shadowofthetombraider/latest/linux/
- Guild Wars 2: 6, https://www.guildwars2.com/en/new-player-guide/
- League of Legends: 15, https://support.riotgames.com/en-us/league-of-legends/gameplay/league-of-legends-keyboard-wasd-input-faq

The other **1,636 old rows were not re-read online**. Port, legacy and preset qualifiers remain. Shadow's aiming context and LoL's optional-WASD/default-click distinction were already present: do not falsely report those as newly discovered omissions.

Constituent-key parsing is not an executable chord/sequence parser. New tokens were identified, but old partial expressions remain qualified. NetHack case and layout-dependent symbols stay distinct; numpad inputs are not top-row digits. No personal press-frequency telemetry, input latency, hand comfort, hardware rollover or gameplay testing was performed.

Workbook checks: nine sheets, eight filterable tables, headline formulas and all 100 key-coverage rows matched independent counts. Formula error scan found no matches. Overview and Stage B preview ranges were visually inspected; ZIP structure passed. This is not a native Excel/device runtime test.

## Corrections and design requirements

1. The previous M/I/J/Home-to-1/2/3/4 suggestion could move urgent numbers into thumb positions competing with the stick. The new draft uses finger-grid number positions, but does not claim they are the easiest physical switches.
2. In the supplied original Number bank, 1/2/3 overlap the Basic Ctrl/Shift/Space switches. Having both codes somewhere does not establish Ctrl+1 or Shift+2. The draft removes same-switch overlap; same-finger combinations still need testing.
3. Tab, V, number keys, function keys and arrows can be urgent or sustained. FAIRY TAIL 2 uses held Tab with skill numbers; Wo Long has Shift+C; Yumia has Shift+number support inputs; rhythm/trick games need direct timed channels.
4. Preserve game-native tap/hold semantics such as Cronos number selection versus held fabrication. Historical 150ms exclusive V layer selection is not changed or assumed valid for v2. Indiana's V parry and Alien's held V identify possible conflicts.
5. Keep action labels separate from emitted keys: Control Resonant's action named Shift is reported on F.
6. Layering does not isolate graphics shortcuts from game listeners. Do not change shared graphics hotkeys silently.
7. The Tools screenshot's Xbox stick differs from the other WASD banks. The draft proposes consistency; it does not change the active device.
8. NetHack eight directions and case-sensitive commands are not equivalent to a WASD stick. THPS movement plus arrow tricks and osu simultaneous notes can justify narrowly scoped direct-input variants.

## Conditional architecture comparison

Assumptions: 30 digital positions, L-1 direct bank selectors repeated per layer, four invariants (Ctrl/Shift/Alt/Esc), four independent stick outputs, one output per switch and no free tap/hold multiplexing.

Upper output capacity = L * (30 - (L-1) - 4) + 4 + 4.
Three banks: 80; four: 100; five: 118. The draft target has 78 codes and four extra immediate 1-4 duplicates, requiring 82 placements under this accounting.

Thus three falls short by two only under these assumptions. Dropping outputs/duplicates or changing access/gestures can make three viable. Four remains the leading candidate, not a universal minimum or measured optimum. Five is justified only by real specialist demand.

## Stage B: concrete but not accepted

R1C1-R5C4 are visual row/column positions, not hardware IDs. L3/R3 flank the third row; TH_U/L/C/R/D are the thumb cluster; ST_RU/RD are right of the stick; ST_D is below it.

All 120 map cells are specified or explicitly unassigned. The union covers 78 target keycodes including WASD. Ctrl/Shift/Alt/Esc and selector positions are stable across banks. Tools intentionally lacks Space/Enter. B/H/N move to thumb positions only as a candidate. Shift+C, Shift+2, Alt+Space and osu X/V share visual columns and remain concurrency risks.

Twenty static scenarios cover FAIRY TAIL 2, Nioh, Wo Long, Yumia, Kunitsu, Cronos, REMATCH, THPS, Silksong, NetHack, osu, FFXIV targets, GW2 healing, Shadow held consumables, Alien held peeking, Olden Era modifier-mouse operations, action/key identity, numeric switch overlap, graphics listeners and stick consistency. A hypothetical combined action is not silently promoted to a documented game requirement. Zero scenarios have hardware/runtime verification.

## Remaining / next action

Do not call Stage A a complete census or fully current-default audit. Current complete Cyberpunk/PoE2 presets and other earlier gaps remain unresolved. ARC/Nightreign ambiguous rows were excluded; Indiana's misspelled sprint row was omitted; blocked sources were not bypassed.

Read the current v2 export, resolve physical button IDs and active selector gestures, then test the small set of critical concurrent/held inputs before adopting or generating an importable map. Keep game-side rebinds and narrowly scoped Hotbar/Grid/direction variants available. Do not modify games or profiles as a side effect of reading this research.

For later semantic integration, obtain original AI_MASTER bytes through an authorized working route, compare the recorded baseline blob to the current master, append the extension with compatible IDs/schema, preserve later edits, and regenerate derivatives. Until then this is a clearly registered additive delta in the same owner. The unrelated Azeron overlay draft PR is not merged by this work.
