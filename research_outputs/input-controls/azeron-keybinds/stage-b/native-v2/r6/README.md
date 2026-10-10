# Azeron R6 — reserved overlay button, compact and sparse alternatives

Status: **research revision and native candidate files completed; R6 import, physical and game tests not performed**.
The current user explicitly postponed image generation until after this research, native files and HTML prototype. No new images were generated. Earlier AI game posters are rejected as control evidence: they invented actions/keys and omitted controls.

## Canonical objects and delivery

- `DESIGN_R6.json` owns both logical variants, native position correspondence, reserved control and the source-derived sparse masks.
- `SOURCES_R6.json` separates source facts, design inferences and limits for six cognition/motor sources and seventeen game/manufacturer records.
- `GAME_READINESS_R6.json` tracks **23 title/edition scopes**, not 23 verified keyboard tables. It retains the requested franchises, exact platforms, contextual gaps and prerequisites for later action overlays.
- The native compiler and independent validator create/check a separate candidate family without installing it. Raw source backups, native profile UUIDs and generated profiles are delivered privately, not committed to this public repository.
- The existing R1/R2 catalogue remains 94 scoped records and 2,195 binding rows. R6 does not replace or reconstruct `AI_MASTER.json`.
- Private Drive folder: **Azeron profile backups**. Current files: **Azeron R6 COMPACT - 4 native profiles.zip**, **Azeron R6 SPARSE - 5 native profiles.zip**, **Azeron R6 - Research and design decisions - Hebrew.html**, **Azeron R6 - Compact overlay HTML prototype - no joystick.html**, and **Azeron R6 - Complete research profiles prototype and recovery package.zip**. Retrieve through the authenticated connector, not by asking the user to transfer them again. Stable file IDs and hashes are in `PUBLICATION_MANIFEST.json`.

The Hebrew research report is about 2,800 words, with explicit design tradeoffs and evidence qualifications. The complete private delivery includes its source, the HTML generator, original inputs, detailed audit results, native files and readback tests. This README is the compact decision record, not a claim that full current defaults or personal usage frequency are known.

## The user's corrections are hard constraints

1. Native **button 19**, the right-facing index-finger side switch, is unassigned in every R6 layer and hidden in the overlay. It is not button 31 on the thumb or button 36 beside the little finger. Its future role belongs to the user's separate overlay app.
2. A disabled native key emits no keyboard hotkey. No F13, pass-through, global hook or external application configuration is silently added. A raw-input route or an explicitly chosen emitted trigger remains an external integration decision.
3. `LETTERS` becomes **`MENUS`**: a mnemonic destination for menu/panel/information controls, not a literal collection of every unused letter. It does not assert that each included key opens a menu in every game.
4. Keep a minimal-change alternative and a **separate sparse-finger alternative**. Do not replace the former merely because the latter adds blanks.
5. No joystick drawing. Preserve the other **29 digital controls**, including little-finger side #36 and bottom #37. Empty slots remain spatially stable; only #19 is omitted.
6. All next-stage views must derive from these same IDs and output maps. A game selector changes action labels only, not key outputs. Unsupported action labels remain unknown.

## Implemented alternatives

| | COMPACT | SPARSE |
|---|---|---|
| Native profiles | 4 | 5 |
| Layers | BASIC, NUMBERS, MENUS, TOOLS | Same plus NAV |
| Logical outputs including WASD | 78 | 78 |
| Reserved #19 | Disabled throughout | Disabled throughout |
| Extra finger blanks | None beyond prior plan | Nine source-derived cells |
| New navigation selector | None | BASIC #28, held |

### COMPACT: minimal changes

Only eight mapped cells change from R5, in addition to new profile identity and the MENUS name. Alt moves from reserved #19 to previously empty BASIC #31. On NUMBERS, MENUS and TOOLS it replaces duplicated Space at #14. Space still exists on BASIC.

This is an explicit tradeoff: BASIC Alt occupies the thumb, and jumping while a secondary bank is held is not preserved by this choice. Keeping every duplicate would require a different trade or more capacity. Four layers are sufficient for this candidate, not a universally proven optimum.

### SPARSE: respect the user's previous empty finger rows

The original authored NUMBER profile disabled #38/#13/#18, MENU disabled #7/#11/#16, and MOD KEYS disabled #8/#12/#17. These were verified in active `types` fields; dormant stored key values were not treated as bindings. Their emptiness is observed; the user's reported reach difficulty is not an instrumented distance/force measurement.

SPARSE keeps those nine positions blank. Zero and extra Ctrl/Shift copies move to thumb controls in NUMBERS; L/M/O move to thumb controls in MENUS; F7–F9 move to the thumb in TOOLS. BASIC #28 opens a deliberate NAV bank, and H moves to MENUS. NAV concentrates arrows, navigation and punctuation, with finger copies of confirmation/cancellation.

Holding NAV occupies the thumb, so continuous independent thumbstick movement is **not** promised there. Some isolated chords gain routes while movement-concurrent routes are lost. The numeric/function grid symmetry for 7–9/F7–F9 is intentionally sacrificed in SPARSE. Do not describe sparse as globally faster or better.

Both families preserve current dedicated SINGLE → Layering with Toggle on hold, matching the newer authored source. V remains a direct key. The historical v1.5.6 V-tap/150 ms arrangement is not reintroduced. Secondary selectors do not nest: release to BASIC before choosing another bank.

## Research findings that changed the method

Cross-game key prevalence is not personal press frequency, hold duration or urgency. Long manuals and repeated contexts also bias counts. Action demand is separated into frequency in context, reaction deadline, hold duration, concurrent inputs, error cost and game state. Transition pairs and held chords are different graph relationships. No fabricated numerical weights or percentage-optimality score are used.

The user's MENUS correction is direct evidence of their semantic organization. Stable spatial positions and a readable one-layer view are supported as design hypotheses by the CommandMaps and spatial-memory work [H2/H3]. Shortcut-learning research motivates later actions-plus-keys views [H4], not a claim that a poster teaches muscle memory automatically. Soft-keyboard transition models [H5] suggest examining sequences, but their stylus/text-entry coefficients are not transferred to an Azeron.

Maintained-mode experiments in text editing [H1] support the possibility of reduced mode confusion, but holding a layer still consumes a physical resource. Finger independence depends on direction and force [H6]; same-column conflicts are screening flags, not proof of impossibility. Different fingers are likewise not proof of comfort. See `SOURCES_R6.json` for full source URLs, specific findings and limits.

Version and platform checks matter. PoE2's documented dodge-hold sprint [G1] creates a held-action requirement. DOOM The Dark Ages **Revelations Update 4** explicitly adds Chain Spear input behavior and changes the automap recenter default [G2]; it must not inherit DOOM Eternal labels. The older Resident Evil 6 PC manual [G15] provides real letter-modifier and directional chord examples. Bayonetta console sequels/Origins and individual DMC ports/characters require separate adapter or effective-binding records rather than a generic SERIES layout. Several primary sources establish context only, not complete default tables. No current effective game presets were read from the Windows installation in this session.

## Audits, with units and limits

The unchanged R4 parser supplied **3,106 listed input variants** from 2,195 rows; 28 raw expressions remain for manual review. These are not 3,106 independent actions or a representative usage distribution.

| Isolated modeled result | R5 | COMPACT | SPARSE |
|---|---:|---:|---:|
| Direct route | 2035 | 2031 | 1999 |
| Layer route | 717 | 722 | 755 |
| Same-finger/model conflict | 31 | 30 | 29 |
| Cross-bank only | 4 | 4 | 4 |

The remaining results are other-hand-only and output-review cases. With additional continuous movement stress, conflict counts are **402 / 410 / 551** respectively. This discloses the sparse variant's thumb cost; it is not a gameplay-performance score. Existing C+2, E+arrow, urgent numeric/function and numpad exceptions are not magically solved by native encoding.

Independent native readback checked **270 digital cells, 387 native input records and 14 directed layer links** across nine profiles. It confirmed reserved #19, family-local active references, identity disjoint from all original and R5 profiles, complete joystick/nonvisual input preservation and absence of introduced macro/turbo behavior. The source backup and R5 input files remained unchanged.

The HTML prototype contains **261 cells: 29 per layer across nine layers**. Static geometry checks and **28 event-logic assertions in a minimal DOM harness** passed. This is not a real-browser rendering test. Earlier browser access denial was not retried or bypassed. No screenshot, video, global input collection, native import or game launch occurred here.

## Parallel execution evidence: preserve R5

Draft [PR #4](https://github.com/dodWhatUp/install-modes-for-games/pull/4), head `58068c3b96a2314df77c3510218d1fbefa629f39`, separately reports that Codex loaded R5 into the app's native SOFTWARE store, with a 19→23 profile count, and observed device-to-app return-on-release for #1/#2/#36 outside games. Its Import profiles chooser was not completed. That report is evidence about **R5**, not R6, ordinary output/chord comfort, the joystick or gameplay. The PR was not merged and its proposed global/AGENTS preferences were not adopted by this work.

Treat the existing R5 and later live changes as protected. Do not tell the user to re-import R5 blindly or restore an older full backup. R6 delivery is additive and has new identities, but actual import must still check the live state first.

## Reproduction and next boundary

Python standard library builds and validates native candidates and compares routes. Node is used only for the local event-logic harness. The full delivery's `research/REPRODUCTION.md` supplies exact paths and steps. The public JSON serialization is compact; the delivery uses equivalent pretty JSON. **Validate delivered native files against the delivery's exact DESIGN_R6.json**, because its private manifest records that byte hash. A new compiler run generates new UUIDs; do not repeatedly import regenerated same-name families.

For a later authorized installation, choose one family, take a current backup, preserve existing R5/original profiles, import the individual JSONs rather than restore their ZIP, verify every target and release link, and stop after an unknown/rejected effect instead of blind retries. No live changes or launch are authorized by publication itself.

The next display stage is effective game-action reconciliation on this stable geometry, then compact per-layer images. It must preserve #19 hidden, joystick drawing absent, all other digital slots present and the exact variant/layer revision. Unknown game actions must remain explicitly unknown. No generated-poster labels may be reused as evidence.
