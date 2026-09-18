# Ray Reconstruction and denoiser-route coverage

Research cutoff: **18 September 2026**. Status: **useful route audit; incomplete global census**. This is a research record, not an installation instruction or a claim that all candidate games were tested.

## Result and counting contract

| Category | Count | Meaning |
|---|---:|---|
| A: official Ray Reconstruction | 32 | Official RR availability list, excluding the Half-Life 2 RTX demo and adding the September 15 releases. |
| B: current implementation-specific RR mod | 1 | Quake II RTX community renderer; author-documented beta, not locally tested. |
| C: directly documented denoiser controls | 25 | At least a relevant bypass is documented. Some bypass only selected effects or retain GI history. |
| C-reported | 1 | Crysis 3 Remastered, reported DF example; exact original procedure not independently recovered. |
| U: unresolved candidates | 47 | No suitable current route established in this audit. NOT proof that no mod or setting exists. |
| Working inventory | 106 | Named candidates with unequal evidence depth, not 106 uniformly verified significant-RT implementations. |

**22 of the C entries also have an Ultra+ author-documented RR option.** They remain provisional because this audit did not establish the exact RR feature creation/evaluation and required-input path. This does not prove the author is wrong. It prevents a setting named `rayreconstruction` from being treated as equivalent to a verified implementation.

A permissive count accepting all 22 claims would be **A32 / B23 / C3 / C-reported1 / U47**. Do not add the 22 to the denominator or double-count their bypass routes. The conservative total is **32 + 1 + 25 + 1 + 47 = 106**. Direct documentation supports a route for 58 entries, with one additional reported example.

## Scope

The intended significance filter is scene-wide lighting/GI, path tracing, or recurring reflections that noticeably influence normal gameplay. Tiny AO/shadow additions and isolated car-showroom effects are not the target. This is not a measured perceptual threshold. Lesser-known official entries and the unresolved candidate tail still require individual effect-breadth checks; Halloween's exact RT effect breadth is explicitly provisional.

Software Lumen is included in the broad working inventory because it can materially determine lighting and presents the denoising question. It is not hardware RT. The detailed snapshot marks software-Lumen-inclusive entries and hardware-enabling workarounds separately. No hardware-only grand total is asserted. Early access is allowed. Stand-alone demos and the open-ended RTX Remix conversion ecosystem are outside the principal count. Metro Exodus editions and HITMAN's renamed edition are counted once; genuinely separate sequels are separate entries.

**The number of all released significant-RT games that truly lack every route remains unanswered. Do not turn U47 into a definitive no-options count.** Many U entries are candidate-level rather than fully audited negatives. No game, mod binary, NGX evaluation, benchmark, or moving gameplay scene was tested locally.

## Delivery snapshots

- [Searchable full HTML report and all 106 entries](https://drive.google.com/file/d/1nIGRP22spRzUcEW3fptgbV5elx7lWH5N/view?usp=drivesdk)
- [Structured JSON inventory, sources, confidence and scope](https://drive.google.com/file/d/1VVcEfSOilRRZKaJ_Kb6fqICY3jq95r74/view?usp=drivesdk)

Git owns this editable research record. The Drive files are dated delivery snapshots, not competing live instruction owners. Preserve the evidence limits on future reuse.

## A: 32 official-RR entries

Alan Wake 2; Avatar: Frontiers of Pandora; Backrooms: Escape Together; Call of Duty: Black Ops 7; Crimson Desert; Cyberpunk 2077; Death Relives; Directive 8020; DOOM: The Dark Ages; Enlisted; EVERSPACE 2; F1 25; FBC: Firebreak; Hogwarts Legacy; I Am Jesus Christ; Incursion Red River; Indiana Jones and the Great Circle; Marvel's Spider-Man 2; NARAKA: BLADEPOINT; NTE (Neverness to Everness); Portal with RTX; PRAGMATA; Resident Evil Requiem; Samson; Star Wars Outlaws; Subliminal; Sword of Justice; The First Descendant; War Thunder; **007 First Light; Active Matter; Halloween: The Game**.

Sources: [NVIDIA August 25 list](https://www.nvidia.com/en-us/geforce/news/gamescom-2026-dlss-4-5-ray-reconstruction-release-announcements-trailers/) and [September 15 availability update](https://www.nvidia.com/en-us/geforce/news/007-first-light-path-tracing-dlss-4-5-ray-reconstruction-update-out-now/). Arithmetic: 30 listed in August minus the [Half-Life 2 RTX two-area demo](https://store.steampowered.com/app/2477290/HalfLife_2_RTX/) plus 3 September titles = 32. Availability is not proof that every game mode and every RT effect is covered by RR. Do not retain NARAKA's obsolete initial limited-area restriction after its later [developer RT update](https://www.narakathegame.com/news/update/20250429/33459_1231772.html).

## B: current implementation-specific mod

**Quake II RTX:** [Q2RTX with DLSS / MFG / RR](https://www.moddb.com/mods/q2rtx-with-dlss-mfg-rr-support), public beta 0.95 dated September 11. Its author documents Streamline integration, dedicated RR controls, diagnostic logging, RR fixes and Preset F. This is not the stock NVIDIA renderer or every older DLSS-labelled Q2RTX fork. It remains a beta; exact user-build compatibility is untested.

## C: 25 documented bypass routes

### Three without promotion to an additional current RR claim

| Game | Documented route | Important limit |
|---|---|---|
| Control / Ultimate Edition | [Control Unfiltered](https://github.com/speedlemur/control-unfiltered), RenoDX/ReShade shader bypass | SR L/M experiment, not RR. Author notes motion smearing and possible loss of some AO. |
| Ghostwire: Tokyo | [Ultra+](https://theultraplace.com/games/ghostwiretokyo/): RTReflectionDenoiser=off and RTShadowDenoiser=off | Selected effects; no RR implementation established by these settings. |
| The Ascent | [Ultra+](https://theultraplace.com/games/theascent/): Denoising=none | Reflection-denoising control, not proof of RR. |

### Twenty-two with provisional RR claims as well

Each page documents a game-specific denoiser mode, often including both `none` and `rayreconstruction`. These are mod-author claims, not local feature-validation results.

| Game | Source | Scope / caveat |
|---|---|---|
| Black Myth: Wukong | [Ultra+](https://theultraplace.com/games/wukong/) | Separate Lumen/non-RT and full-PT controls. Explicit RTShadow_Denoiser=off is partial; generic Denoiser=none does not prove full PT denoiser removal. |
| Silent Hill 2 (2024) | [Ultra+](https://theultraplace.com/games/silenthill2/) | Lumen, including hardware path; a GI-history-preserving option is not completely unfiltered lighting. |
| Silent Hill f | [Ultra+](https://theultraplace.com/games/silenthillf/) | Lumen-inclusive; hardware path not established here. |
| Oblivion Remastered | [Ultra+](https://theultraplace.com/games/oblivion/) | Hardware-Lumen controls; exact build requires testing. |
| Metal Gear Solid Delta: Snake Eater | [Ultra+](https://theultraplace.com/games/metalgearsoliddelta/) | Hardware path via workaround. Hardware enabling and RR enabling are different operations. |
| Avowed | [Ultra+](https://theultraplace.com/games/avowed/) | Lumen; some RT-shadow additions have geometry caveats. |
| S.T.A.L.K.E.R. 2 | [Ultra+](https://theultraplace.com/games/stalker2/) | Software-Lumen-inclusive; no native hardware-RT claim implied. |
| Immortals of Aveum | [Ultra+](https://theultraplace.com/games/immortalsofaveum/) | Software-Lumen-inclusive. |
| RoboCop: Rogue City | [Ultra+](https://theultraplace.com/games/robocop/) | Use a maintained package, not an assumed-compatible old Nexus build. |
| RoboCop: Rogue City — Unfinished Business | [Ultra+](https://theultraplace.com/games/robocopunfinishedbusiness/) | Separate game; Lumen-inclusive. |
| WUCHANG: Fallen Feathers | [Ultra+](https://theultraplace.com/games/wuchang/) | Hardware options via game-specific workaround. |
| Hell is Us | [Ultra+](https://theultraplace.com/games/hellisus/) | Software-Lumen-inclusive. |
| Clair Obscur: Expedition 33 | [Ultra+](https://theultraplace.com/games/expedition33/) | Software-Lumen-inclusive. |
| Still Wakes the Deep | [Ultra+](https://theultraplace.com/games/stillwakesthedeep/) | Lumen denoiser controls do not establish a hardware renderer. |
| Echoes of the End | [Ultra+](https://theultraplace.com/games/echoesoftheend/) | Lumen-inclusive; output quality untested. |
| INDUSTRIA 2 | [Ultra+](https://theultraplace.com/games/industria2/) | Hardware-Lumen options documented; GI-history variant remains temporal. |
| The Outer Worlds 2 | [Ultra+](https://theultraplace.com/games/theouterworlds2/) | Author warns higher hardware-Lumen modes can break visuals. |
| Grounded 2 | [Ultra+](https://theultraplace.com/games/grounded2/) | Early access; Lumen-inclusive. |
| The Last Caretaker | [Ultra+](https://theultraplace.com/games/thelastcaretaker/) | Early access; per-build route. |
| Eternal Strands | [Ultra+](https://theultraplace.com/games/eternalstrands/) | Lumen-inclusive. |
| Cronos: The New Dawn | [Ultra+](https://theultraplace.com/games/cronosthenewdawn/) | Lumen-inclusive; older RR preset notes may be stale. |
| Nobody Wants to Die | [Ultra+](https://theultraplace.com/games/nobodywantstodie/) | Hardware-Lumen options exposed by mod; retained GI history is not complete denoiser removal. |

Consult the current [Ultra+ compatibility status](https://theultraplace.com/game-status/). A family listing or a config label does not guarantee current-build compatibility.

## C-reported: one additional example

**Crysis 3 Remastered:** the reported Digital Foundry denoiser-off example. [Original video locator](https://www.youtube.com/watch?v=Lv8tJoiApd8). The original video was not directly readable during this audit, so the exact command and current-build procedure were not independently recovered. Do not count it among the 25 directly documented bypasses or invent a console command.

## U: 47 unresolved candidates, not proven negatives

Metro Exodus / Enhanced Edition; The Witcher 3 current next-gen version; Dying Light 2; Watch Dogs: Legion; GTA V Enhanced; Assassin's Creed Shadows; Spider-Man Remastered; Miles Morales; Ratchet & Clank: Rift Apart; HITMAN 3 / World of Assassination; Jedi: Survivor; Guardians of the Galaxy; Deliver Us the Moon; Deliver Us Mars; Ghostrunner; Ghostrunner 2; Bright Memory: Infinite; Battlefield V; DOOM Eternal; Crysis Remastered; Crysis 2 Remastered; The Medium; Observer: System Redux; F.I.S.T.; F1 22; F1 23; F1 24; Forza Motorsport; Fortnite; THE FINALS; Darktide; Returnal; The Callisto Protocol; Deathloop; Minecraft Bedrock RTX; DESORDRE; ICARUS; Chernobylite; Severed Steel; Lords of the Fallen (2023); Mafia: The Old Country; Borderlands 4; The Alters; Sword of the Sea; Hellblade II; The Talos Principle 2; Jusant.

The detailed snapshot distinguishes focused source review from candidate-only review. Positive significant-RT eligibility and negative route coverage are not equally established across this tail. Important narrower findings:

- [Fatshark's Darktide response](https://forums.fatsharkgames.com/t/dlss4-5-denoiser-issue/118444) says the suggested noise/AO controls do not disable its RT reflection denoiser; no supported off control was exposed there. This is not proof against every future mod.
- Reviewed Ultra+ pages for [Jedi: Survivor](https://theultraplace.com/games/survivor/), [Returnal](https://theultraplace.com/games/returnal/), [The Callisto Protocol](https://theultraplace.com/games/callistoprotocol/) and [Lords of the Fallen](https://theultraplace.com/games/lordsofthefallen/) do not establish a bypass merely by exposing quality/sample/noise controls.
- The Alters and Sword of the Sea have packages marked as needing updates in the checked status source. Existing but stale support should not be advertised as a currently verified route.

## Model distinction and practical meaning

NVIDIA's [RR programming guide](https://github.com/NVIDIA-RTX/Streamline/blob/main/docs/ProgrammingGuideDLSS_RR.md) requires appropriate ray-traced inputs and describes RR replacing the SR path. A newer DLL cannot manufacture missing integration. Generic RenoDX HDR work, ReShade post-processing and generative neural rendering are not automatically RR.

The February SR Preset-L discussion predates the August 25 RR 4.5 release. **SR L/M and RR F are different model paths.** RR incorporates upscaling; it is not simply the normal SR-L model placed after another independent denoiser. A useful comparison is stock filtering versus SR L with the exact bypass versus integrated RR F, on the same moving scene. Denoiser-off may improve stationary detail while making motion, disocclusions or highlights worse. Do not promise better quality or FPS without measurement.

## Expected category changes

| Candidate | Transition | Evidence / condition |
|---|---|---|
| The Witcher 3 | U to A | [NVIDIA announced](https://www.nvidia.com/en-eu/geforce/news/wardogs-pubg-battlegrounds-honeycomb-dlss/) a free Remastered upgrade for **29 September**, with path tracing and RR. Future as of this cutoff; verify release before promotion. |
| Original Control | C to B | The [original RR listing](https://www.nexusmods.com/control/mods/140?tab=description) is removed. A [redistributor](https://www.nexusmods.com/site/mods/2224) advertises a Control package, but its payload was not validated. A maintained or validated release is the trigger; no date is promised. |
| Ultra+ claim entries | C to B for validated cases | Exact-package and RR-evaluation/input proof could resolve existing uncertainty. This is not necessarily a future feature release. |
| The Alters / Sword of the Sea | U to C or B | A compatible maintained update and validation, not merely an old mod page. |
| Older closed renderers | Sometimes U to C before B | Engineering inference: bypassing selected shaders can require less work than building all RR inputs. No title-specific release promise. |

[Control Resonant](https://www.nvidia.com/en-eu/geforce/news/control-resonant-september-24-dlss-4-5-path-tracing/), announced for September 24 with path tracing and RR, is a new game rather than an original-Control upgrade. 007 First Light is already in A, not a future transition.

## Separate renderer-addition expansion

[Minecraft Java Caustica](https://www.curseforge.com/minecraft/mc-mods/caustica) is an author-documented alpha renderer with path tracing and RR; it is not a Bedrock RTX patch. [RTX Remix supports RR](https://www.nvidia.com/en-us/geforce/news/rtx-remix-dlss-3-5-ray-reconstruction/), but every compatible classic game or unfinished conversion is not automatically a completed playable RR title. These are outside the 106 principal rows and require separate completeness and compatibility criteria.

## Validation and operational boundary

The generated HTML and JSON were checked for 106 unique games, A32/B1/C25/C-reported1/U47, and 22 provisional RR claims contained within C. Category arithmetic is verified; visual quality, binaries and compatibility are not. No game, driver, save, mod installation, scheduled task, or machine setting was changed. This additive report does not alter Global, Research OS, existing game records or paused experiments. Do not claim full repository/worktree parity, integration of other active task heads, or complete cross-chat archiving from publication of this report alone.
