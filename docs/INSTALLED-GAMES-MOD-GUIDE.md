# Installed games: mod guide and comparisons

Reviewed **14 September 2026**. This is a sourced decision guide, not a claim that every listed mod is compatible or installed. Skyrim's basic setup is separately authorized; the remaining games are information-only in this request.

**Skyrim installation status:** Mod Organizer 2 is installed and configured with separate baseline/basic profiles. The actual foundation mods await Nexus sign-in; graphics/DLSS additionally awaits exact runtime compatibility. See [the installation record](../games/skyrim-special-edition/HISTORY.md) and [download/install checklist](../games/skyrim-special-edition/BASIC-SETUP.md). The [sanitized inventory](INSTALLED-GAMES-2026-09-14.json) records the actual relative executables and Steam builds.

## Start with the right manager

| Use | Recommended | Alternative and tradeoff |
|---|---|---|
| Skyrim SE | [Mod Organizer 2](https://github.com/ModOrganizer2/modorganizer/releases), stable 2.5.2 | [Vortex](https://www.nexusmods.com/about/vortex/) is easier for Nexus Collections; MO2's explicit file priority and separate profiles suit this repository's experiments better. This is a recommendation, not a benchmark. |
| Complete Skyrim list | A maintained [Wabbajack](https://www.wabbajack.org/) list that explicitly supports its required runtime | Wabbajack installs a curated setup, often using MO2; it is not a substitute for checking list requirements, disk space, and save compatibility. Do not merge two complete lists. |
| Cyberpunk | Vortex for supported packages; explicit manifests for root hooks | CDPR's [modding instructions](https://www.cyberpunk.net/en/modding-support) support Vortex. Keep existing OptiScaler/CET files under their present ownership. |
| NieR:Automata | NAMH for supported asset packages | Manual manifest installation gives more control over Special K/LodMod proxy chains. |
| Pathfinder: Kingmaker | Unity Mod Manager | A general download manager does not replace the game's runtime loader. |
| Dead Cells | Steam Workshop | Native Custom/Assist modes are the simpler choice for many gameplay adjustments. |
| Quake II / RTX | Separate engine and game-data profiles | A Bethesda plugin manager is unnecessary; original, remastered, and RTX engines have different mod compatibility. |
| Other installed games | Author's installer or a small file-ownership manifest | Use Vortex only when its game extension and the exact package format are supported. A downloaded archive is not an installed mod. |

## All 14 installed games

Installation means a nonzero Steam manifest plus the actual game executable found in the registered libraries. These checks do not prove launchability. GPU: RTX 5070 Ti, 16 GB; driver 616.56. No FPS gains below are locally benchmarked in this review.

| Game | Steam build | Best practical starting point | DLSS route | Guide |
|---|---|---|---|---|
| Skyrim Special Edition | 24914197; executable 1.7.104.0 | MO2 + matching SKSE + SkyUI/MCM, then conservative textures | Community Shaders + official Upscaling is the preferred target, but exact 1.7.104 compatibility remains a gate | [Full comparisons](../games/skyrim-special-edition/COMPARISONS.md) |
| Cyberpunk 2077 | 20383525 | Native graphics + selective QoL after existing hook validation | Native SR/RR/FG/MFG; existing NR experiment remains separate | [Comparisons](../games/cyberpunk-2077/COMPARISONS.md) |
| Batman: Arkham Knight | 13250859 | Preserve current Luma/OptiScaler experiment and stock fallback | Local DLAA + NR evidence; SR quality modes, RR, FG unavailable in current profile | [Comparisons](../games/batman-arkham-knight/COMPARISONS.md) |
| A Plague Tale: Requiem | 11415435 | Native DLSS; preserve the existing NR test | Native SR and FG; NR title-scene evidence only | [Comparisons](../games/a-plague-tale-requiem/COMPARISONS.md) |
| A Plague Tale: Innocence | 4336652 | Original presentation or game-specific HDR candidate | No verified SR/FG integration selected | [Comparisons](../games/a-plague-tale-innocence/COMPARISONS.md) |
| STAR WARS Jedi: Survivor | 15643690 | Native DLSS/FG, then one performance package | Native integration; keep replacement FG off initially | [Comparisons](../games/jedi-survivor/COMPARISONS.md) |
| Bayonetta | 1824749 | Original gameplay + controller/QoL choices | Historical x86-to-x64 helper provides full-resolution neural processing, not faster SR | [Comparisons](../games/bayonetta/COMPARISONS.md) |
| NieR:Automata | 7020666 | NAMH, selective Special K/LodMod and input improvements | No verified DLSS integration selected | [Comparisons](../games/nier-automata/COMPARISONS.md) |
| Pathfinder: Kingmaker | 6757524 | Unity Mod Manager + Buff Bot, optional convenience settings | No verified DLSS integration selected | [Comparisons](../games/pathfinder-kingmaker/COMPARISONS.md) |
| Quake II | 20742936 | Remaster for accessibility/content; Yamagi for classic mods | Use separate Quake II RTX route for ray-traced visuals | [Comparisons](../games/quake-ii/COMPARISONS.md) |
| Quake II RTX | 17873149 | Stock RTX first; isolated community-fork comparison | Q2RTX-MOD documents DLSS; do not attribute it to stock NVIDIA release | [Comparisons](../games/quake-ii-rtx/COMPARISONS.md) |
| Dead Cells | 23762174 | Native accessibility/Custom Mode, then Workshop | Not established; no DLSS recommendation for this 2D title | [Comparisons](../games/dead-cells/COMPARISONS.md) |
| Indivisible | 5205809 | Native controls, co-op and New Game+ | Not established; no DLSS recommendation | [Comparisons](../games/indivisible/COMPARISONS.md) |
| SENRAN KAGURA Peach Beach Splash | 3139916 | Original offline game and selective fixes | Not established; no DLSS recommendation | [Comparisons](../games/senran-kagura-peach-beach-splash/COMPARISONS.md) |

## Categories used for every game

Each game separates management/foundations; performance and stability; graphics/HDR/DLSS; QoL and controls; menus/configuration/UI; animation and movement; enemy behaviour; abilities/magic/tools; added mechanics; and new quests/campaigns/expansions. A category with no verified candidate says so. A texture pack, trainer, shader preset, or enemy rebalance is not a new campaign.

Recommendations use **Core / Strong / Optional / Experimental / Avoid**. Confidence and difficulty are independent of popularity. Unless explicitly tied to prior local history, all candidates are **untested locally**, with **Medium confidence in their documented purpose and Low confidence in the exact installed-build combination**. Performance effects are qualitative expectations, not promised gains. Release versions are pinned only where actually checked; otherwise consult the live author file page before installing. Ordinary review expires in 90 days, experimental graphics in 30 days, and any relevant game update triggers immediate re-review.

## Skyrim installation paths

| # | Goal and stack | Benefit | Important conflict | Difficulty / confidence | Rollback |
|---|---|---|---|---|---|
| 1 — Recommended and selected basic scope | MO2 + SKSE 2.3.1 + Address Library v13 + SkyUI 6.11 + MCM Helper 1.6.3; runtime-matched fixes only | Reversible foundation, inventory UI, mod configuration | Old 1.6.x DLLs and SkyUI 5 skins may not match runtime/UI 6 | 2; High for explicit SKSE/MCM support, untested locally | Disable MO2 profile; remove only manifested SKSE root additions; retain saves and prior ReShade |
| 2 — Later graphics stage | Verified compatible Community Shaders + same-release Upscaling + modest texture pack | Engine-integrated DLSS/DLAA, lighting/material improvements; optional FSR FG | 1.7.104 support gate, old Display Tweaks, existing ReShade proxy; no ENB shader core alongside CS | 3; conditional | Restore root hook snapshot and disable graphics profile |
| 3 — Replay overhaul | Foundation + one combat/perk/magic family + authored quests | New mechanics and content | Save dependency, overlapping perks/AI/quests | 4; Medium upstream, Low combined | Return to pre-overhaul save and full profile together |
| 4 — Original rendering fallback | Preserved present game/ReShade state | Familiar, smallest change | No new DLSS integration | 1; launchability untested here | Restore captured baseline |

Do not downgrade Skyrim automatically, substitute an unofficial compatibility shim, install paid packs, or replace a working hook merely to fill a DLSS checkbox. Those are materially different paths. Graphics controls inherit [the user's mapping](../preferences/GENERAL.md); unsupported actions remain unbound and explicitly documented.

## Entries that are not installed

Seven Steam entries have zero recorded installed size/build and no rendering executable: **Devil May Cry 5, DOOM: The Dark Ages, GTA V Enhanced, Path of Exile 2, Red Dead Redemption 2, Shadow of War, and TEKKEN 7**. They are queued/partial/removed, not seven working installations. Legacy folders for **CotW (identity unresolved), God of War Ragnarök, Hogwarts Legacy, Sifu, Street Fighter 6, and The Witcher 3** also lack rendering executables. DMC5's old folder contains helper/mod-manager executables only.

The previous [Hogwarts guide](../games/hogwarts-legacy/MOD-CATALOG.md) remains historical. [DOOM's paused experiment](../games/doom-the-dark-ages/HISTORY.md) remains paused. No game download, purchase, reinstall, online injection, or automatic reminder is implied by this catalog.

## What is uploaded

The Drive package contains this guide, per-game comparisons, curated repository documentation and small authored configuration/source examples. It links to original downloads. It excludes mod binaries/archives, proprietary game files, saves, credentials, private snapshots, raw logs, and machine-specific paths. The repository is the maintained source; Drive is a dated export, not an automatic synchronization service.
