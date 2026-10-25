# History

## 2026-10-25 - Renewed DLSS SR and DLSS 5 request: compatibility recheck

A fresh read after the renewed installation request found the previous RenoDX
profile and three gameplay plugins active, with Luma/DLAA and Generic neural
rendering disabled. The RTX 5090/621.01 combination is unchanged. Existing DLSS
and NR runtimes have valid NVIDIA Authenticode signatures and deployment-matching
hashes; installed runtime files do not establish active feature delivery.

Latest Luma is still `latest-761`. Its normal Shadow of War archive digest remains
`74336c1c7124dc033146c26ac5baee4bc07856898573871a569d60301b37d1b7`.
The freshly fetched game source at `dc471fa590c24a12a36be3e527ec45d2595466bd`
matches the previous review and still requires TAA with 100% internal/render
resolution: a native-resolution DLAA path, not supported lower-resolution SR.
No newer supported game-specific SR path or release fixing the recorded local
shutdown failure was established.

The selected RHI Generic 8.5.0-rc10 archive retains its published digest. Its
installed native-DX11 configuration consumes a DLSS contract; it cannot create
the missing working integration. The prior Luma exit fault and cancelled NR run
remain the current runtime evidence. NIGos Bridge v1.4.12 documents a synthetic
alternative for games without DLSS, using native-size DLAA and estimated motion.
That would be a different DLSS-5-only experiment, not true SR; it was not installed.

No game, store, manager, driver or display setting changed and no game launched.
The previous profile, switches and recovery remain intact. Requested working SR
plus DLSS 5 is **not achieved**. The next boundary is a supported SR integration
and diagnosis of the existing Luma failure, or a separately selected alternative
neural-rendering trial. Exact metadata/source hashes and local evidence are private.

Primary sources: [Luma release](https://github.com/Filoppi/Luma-Framework/releases/tag/latest-761),
[game source](https://github.com/Filoppi/Luma-Framework/blob/dc471fa590c24a12a36be3e527ec45d2595466bd/Source/Games/Middle-earth%20Shadow%20of%20War/main.cpp),
[RHI mirror](https://github.com/RankFTW/rhi-repo/releases/tag/renodx-dlss5-8.5.0-rc10),
[Bridge contract](https://github.com/NIGos/dlss5-bridge).

## 2026-10-25 - Shared multi-game Mod Controls and AI interface

The user requested a multi-game controller integrated with the general game app,
reusing its workflows, external programs and direct AI access. Mod Controls 2.0
adds a shared Hub page and a stable standalone APP LAUNCHER over the same game
registry, installation identities, profiles, typed settings and approval owner.
Shadow reuses its reviewed controller engine and recovery; other games can
connect reviewed data-only INI control packs. Support is capability-specific,
not universal automatic mod installation or manager deployment.

The real Shadow installation exposes 17 typed controls. Its Desktop shortcut was
opened through Explorer and displayed applied settings without the earlier
render.cfg error. The native configuration SHA-256 stayed
`700db74e4240084afa593f3988f75658c0f0530ebfeaec3ecf0ee5c1aece7281`.
No game settings were applied and no game was launched for this integration.
The older Shadow controller windows and their drafts remain available.

Twelve disposable service tests, nine isolated Tk tests, the shared workspace
suite, modern protocol suite and source updater checks passed. Real Codex
client discovery found 35 shared tools including nine Mod Controls operations.
It exposed an ordinary legacy-metadata compatibility failure; the repaired
transport has explicit regression coverage and retains protocol-era boundaries.
AI reads/previews are direct; changes are revision-bound proposals for visible
local review, never model-approved execution. No model API key or paid model
call was added.

The component update preserves unrelated incumbent code, the newer verifier,
Studio bytes, data roots and the previous baseline. A running old Hub keeps its
draft editors until its next normal restart; the new standalone view is already
available. [Architecture, limits and access](../../docs/MULTI-GAME-MOD-CONTROLS.md),
[sanitized validation](../../docs/MOD-CONTROLS-VALIDATION-2026-10-25.json).

## 2026-10-25 - Automatic native-settings discovery and mapping rebuild

The user asked the program to handle the earlier missing-render.cfg problem itself. Controller 1.2 adds a bounded locator for the saved mapping, normal Windows local app-data roots and the game's exact package-cache locations. An open Windows file handle resolves virtual spellings to the physical file. Validation checks native width/height/HDR keys, duplicate/nonfinite values and size limits. A valid saved selection wins; unique/byte-identical candidates can rebuild the mapping automatically, while conflicting different files require an explicit choice.

Mapping updates preserve previous bytes and unknown fields, use a controller-local lock and atomic readback, and never move/reset the native settings. Startup recovery can search again or select a validated existing file; its Steam action opens the game details page for first setup rather than launching a game automatically. The same repair UI is available under Files & tools. Refresh can recover a disappeared location; repair keeps pending drafts and unavailable settings block Apply. This is deterministic game-specific discovery, not an autonomous code-generation service or universal repair engine.

Twenty-seven Windows disposable-file checks and 57 isolated real-Tk checks passed, including corrupt/stale/missing mappings, redirected paths, candidate conflicts, atomic-write failure, first-open retry/cancel and preserved pending edits. All twelve final source files matched guest hashes. The normal Desktop launcher was then opened with the old mapping safely backed up and absent: the Explorer-launched 1.2 process found the real redirected render.cfg and rebuilt its own mapping, with the previous native path/hash preserved. The current settings were visible. Game settings, saves and loaded mod files stayed unchanged; no game launch or real Apply occurred. Prior windows/drafts and the original mapping remain recoverable. The task-owned helper/VM were stopped cleanly. Exact machine paths and receipts remain private.

## 2026-10-25 - Mod folders, in-app author text, manager package and floating settings

The user requested mod-folder links, source pages visible inside Mod Control, preparation/open actions for a standard manager and floating mod settings. Controller 1.1 adds one searchable mod browser with configured state, source URLs and existing mod/config/download/native-settings folders. The three installed gameplay plugins and shared loader have a read-only author-text reader pinned to the reviewed original GitHub source; full websites open separately. Third-party page text is never executed.

Nonmodal settings editors share the main preview, support optional always-on-top and validate the original plugin bounds. Apply this mod writes only that mod's selected fields and preserves unrelated drafts; closing a floating editor keeps the preview. Saved profiles retain the existing JSON owner/format. Graphics continue to use their reviewed profiles, RHI and the in-game Delete menu; no live-game overlay or new graphics feature was added.

The manager panel prepares four hash-pinned original archives, applied gameplay INIs, a profile, manifest, guide and verified transport ZIP. Separate actions open the export folder, ZIP, guide and a detected or chosen installed manager. The ZIP is not presented as directly deployable; import the original archives individually after ownership review. A fresh real export was prepared and verified locally. No Vortex installation/import/deployment, second loader, manager-database change or writer-ownership transfer occurred.

Fifteen disposable Windows file checks passed. Sixteen existing and twenty-five new real Tk checks passed in the isolated Linux lab; the latter cover search commitment/cancel, in-app reading, folder selection, floating preview/close, per-mod Apply with unrelated drafts retained, applied-status refresh, persistent profiles and export/open separation. A resize callback and a clipped manager button were corrected before final verification. Exact final source hashes matched the guest; the task-owned helper and guest were stopped cleanly. The actual Desktop shortcut opened the upgraded Windows UI and its mod browser. The older window had two unsaved preview edits and was preserved separately. Protected settings/save hashes stayed unchanged; no real Apply or game launch was performed. Private deployment/recovery receipts retain exact paths, byte checks and the export package.

## 2026-10-25 - Desktop launcher native-settings path repair

The user reported an `Errno 2` dialog for `render.cfg` when opening the delivered launcher. The initial setup-time file check missed a Windows context difference: its apparent local app-data path resolved to the packaged Codex app's physical cache, while the Explorer-launched controller looked in the normal local app-data folder. Resolving an open file handle identified the existing reviewed file; this is observed filesystem evidence, not a missing-config guess.

Controller 1.0.1 reads an explicit private workspace path binding before its environment default. The binding points to the existing file; no native configuration was created, copied into another game location, reset or applied. Missing/invalid bindings produce a clear error. Fingerprints include the binding and file location; transactions retain a native-file recovery copy independent of the legacy backend's app-data view.

All fourteen disposable Windows file tests passed, including a different Desktop environment, exact bound-file recovery and stale-binding refusal. The actual Desktop `.lnk` was then opened through Explorer; its new Python process was an Explorer child, and the window displayed RenoDX, all three configured gameplay plugins and 3840x2160 without the missing-file error. The seven protected settings/save file hashes remained unchanged. No game launch or real profile Apply occurred. Existing windows were preserved; the corrected window was left available. Source and installed service bytes match; recovery and exact machine paths remain private.

## 2026-10-25 - Included APP LAUNCHER and standing delivery rule

At the user's request, the primary Desktop shortcut is **Shadow of War Mods APP LAUNCHER**. A same-named double-click entry is included in the control-panel package and workspace root. The old Manage entry forwards to the included launcher. **Files & tools > Show APP LAUNCHER** locates it after the next normal open. Runtime/workspace bindings and just-in-time recovery remain private. Existing windows were left running to preserve pending edits.

Launcher paths, target/arguments, bindings and installed/source bytes were read back; the small menu addition was syntax-checked. The earlier ten file checks, sixteen isolated Tk checks and native Windows observation remain historical acceptance for their recorded hashes. No new GUI, game launch or profile Apply was used to verify this naming update. The standing [delivery contract](../../docs/APP-LAUNCHERS.md) is recorded in repository instructions/preferences and copied to private Drive; other installed apps have not been bulk-renamed.



## 2026-10-25 — Graphical file controls and prepared Vortex handoff

The user requested a more convenient interface for precise control, persistent file results, an option to transfer to a regular mod manager, and an explanation of stability/resource cost. A thin native Tk front end was added to the existing reviewed local profile controller. Authored source is under `examples/shadow-of-war-controls`; private paths, payloads, installation and recovery remain outside Git/OneDrive. The installed Unified Game Tools app and independent source masters were not rebuilt or replaced.

The existing Desktop shortcut and double-click entry now open graphical controls. The old numbered console remains a separate fallback. The window distinguishes applied files from pending edits; supports graphics/loader/individual plugin states, exact Elven Speed/FOV/multi-equip settings and render dimensions; and stores reusable JSON profiles. Save/load does not apply changes. Apply uses the existing lease, process/ownership checks, a current-file fingerprint, recovery, transactional writes and readback. Unknown external changes are refused. Existing native INIs and `last-applied-profile.json` survive UI closure; view preferences have a separate file and do not toggle features. Official texture ownership stays in Steam.

Plugin bounds follow the pinned original menus: focus regeneration −1–1, duration 0–10 and FOV 40–70. Supported modifier choices map to the original ImGui keys. Experimental controls retain the Luma exit-fault warning and do not imply true SR or neural delivery. RHI remains the graphics owner; the local controller remains the gameplay/profile writer.

**Manager handoff, export-verified:** four pinned original gameplay archives, current gameplay INIs, a profile, hashes and a readable guide were copied to a new private Vortex handoff folder. The original loader archive matches its published GitHub digest; the older plugin archives lack published digests and retain their locally pinned original-download hashes. No proprietary game EXE/original Bink runtime, official texture archives or campaign save is exported. No Vortex installation, import, deployment, purge, manager-database edit or ownership transfer was performed. The [current author extension](https://www.nexusmods.com/site/mods/375) supports Steam/GOG and can install loaders automatically, so actual handover must preserve the selected loaderfix/Bink arrangement, retire conflicting local write ownership and avoid a second DLL loader. [Vortex's deployment documentation](https://github.com/Nexus-Mods/Vortex/blob/master/docs/mod-management/EXTERNAL-CHANGES.md) explains linked files and detection of edits by other tools.

**Checks:** ten Windows disposable-file tests passed, including dependency/ownership validation, refusal while a store is open, stale binary changes, preservation of loader-only disables, mid-transaction failure recovery, profile persistence and export pins. Sixteen real Tk widget/callback checks passed in the accepted Linux lab's private Xvfb display, including narrow layout, pending versus applied settings, saved profiles surviving reopen, invalid-value blocking and visibility not changing features. Final source transfers were SHA-256 matched; an earlier text-transfer encoding defect and a stale Tk callback on destruction were corrected before final acceptance. The task-owned guest/helper were cleanly stopped. The native Windows window then opened and showed the current real settings; no host test pressed Apply.

**Resource observation:** one five-second idle sample of this panel showed about 39.9 MiB working set and 21.7 MiB private bytes, with zero measured process CPU-time increase during that sample. This is one idle observation of this panel, not a Vortex measurement or a game/FPS result. It has no resident injector/service and can close before play; deployed mods retain their own runtime cost and stability risks.

Real game-file fingerprints and the campaign-save hash matched before/after interface installation and handoff creation. No game was launched. Previous RenoDX + three gameplay plugins remain configured on; Luma/NR remain off after the earlier exit fault. Machine bindings index the GUI receipt, exact source hashes, saved profiles, handoff, shortcut recovery, resource observation and lab receipts. Actual Vortex migration and real-game changes through the new Apply flow remain untested, while its transaction engine was exercised on disposable files.

## 2026-10-25 — Physical display reverified after user clarification

The user answered the delayed questions: Steam was connected/open, the earlier permission prompt was not visible, and the physical desktop still looked normal. Those old prompts had already cleared; no new authentication/security action was requested or automated.

A fresh read-only system report, taken without opening another computer-control session, verified PG32UCDP **3840×2160/240 Hz**, PQ/BT.2020 and `AdvancedColorSupported AdvancedColorEnabled`. WMI again identified the active monitor. This supersedes the pending physical-display recovery boundary below. The prior 1024×768 SDR result is a transient test/control-session observation, not proof of persistent physical-desktop degradation. The exact cause/session transition is not isolated; no Windows resolution/HDR repair was necessary or applied.

The game was closed. Its native render configuration still contained the test-session 1024×768 values, so a separate just-in-time backup was preserved and only `ScreenWidth16by9`/`ScreenHeight16by9` were corrected to 3840/2160. Borderless, TAA, native HDROut and every other byte were preserved. Save hashes still match. Steam was left open and no game was launched. This establishes saved configuration, not an in-game 4K/HDR test.

The previous RenoDX + three gameplay plugins remain active; Luma and Generic NR remain disabled. This clarification does not clear the separately recorded Luma driver fault on shutdown or establish DLAA/NR creation, repeated evaluation, delivery or moving-scene quality. Next useful boundary is fault diagnosis and physical-path game acceptance, rather than repeated monitor/Steam permission questions. Private receipts and machine bindings were reconciled without overwriting the original failure evidence.

## 2026-10-25 — Authorized menu checks, Luma shutdown fault and rollback

The user authorized all helpful steps after the main-menu/HDR-restart proposal. This continued testing authority; it did not require asking again to launch the staged profiles. Steam repeatedly raised a Valve Client Service UAC prompt. No agent input was sent to those security prompts; they later cleared and launches proceeded. No campaign or benchmark was started.

**Stock, menu-scope pass:** title/main menu/options rendered, Borderless was already selected, TAA and Ultra textures were observed. Render scale started at 88% and was changed to 100%, retaining the first-generated native configuration separately. Steam tracked a normal exit code 0. The game surface was 1024×768, so this is not a 4K/performance result.

**Previous selected profile, menu-scope pass:** RenoDX 26.1023.0600 registered and replaced shaders; all three gameplay plugins logged initialization/address discovery and their menu. Elven Speed/FOV hooks reported `MH_OK`; Multi Equip Skills finished loading. F12 and Delete opened/closed their panels using a temporary exact-game guarded input adapter; native menu mouse controls worked. Steam tracked exit code 0 and ReShade logged finished shutdown. Equipped skill combinations and moving gameplay remain untested. The original large gameplay-panel layout extended outside the small control surface and was preserved. Optional unselected Lilium HDR tools showed errors on this SDR path; this is distinct from RenoDX registration/shader replacement.

**Luma, startup/menu pass but shutdown failure:** only Luma owned the graphics/shader profile; the RenoDX visual DLL was parked. Its panel showed DLSS, preset L, SDR, and the explicit TAA/100%-only requirement. NGX/DLSS runtimes loaded, which does not prove feature evaluation. Fresh logs did not establish repeated DLAA evaluation/delivery. Darker menu output and intermittent multiple character outlines were observed; their cause and moving-scene quality were not isolated. After in-engine Quit, Steam recorded `-1073741819` (`0xC0000005`). Windows Application Error 1000 and WER 1001 identify `nvwgf2umx.dll` 32.0.16.2101, offset `0x777797`, matching the Luma process and exit timestamp. This identifies the faulting module, not sole root cause. The active gameplay loader and an NVIDIA overlay banner remain confounders; no driver, global overlay or security setting was changed.

The neural profile had been staged and its Steam launch queued before the shutdown event was found. The queued launch was cancelled; Steam's process log contains no subsequent game process. No NR creation/evaluation/delivery is claimed. Crash evidence, complete logs/configs and original source pins are retained privately. The previous graphics + three plugins were restored through the checked controller. Luma and NR remain installed/off; the guide and controller warn about the observed exit failure.

**Display boundary:** a fresh pre-launch report showed the PG32UCDP at 3840×2160/240 Hz, HDR/PQ. During stock/previous testing, before Luma ran, Windows exposed 1024×768/60 Hz SDR with unknown HDR support. Settings later identified the same cached monitor name but reported HDR unsupported, offered no 4K resolution, and normal Detect found no other display; WMI returned no monitor identification. Cause is unresolved, and the agent asked for the physical monitor/connection state. No unavailable display mode was forced. Luma's documented HDR disable/relaunch path was not exercised, and physical HDR restoration/acceptance is not claimed.

The campaign save remained hash-identical after all three runs. The temporary menu helper was stopped; the existing Studio host/mappings remained in place. Stock/previous normal exits and the Luma fault are separate evidence levels. Current blockers are the display path and optional Luma failure, not missing test authorization. The private runtime receipt and machine binding index exact stages, hashes, rollback and evidence.

## 2026-10-24 — UHD textures and optional Luma/neural profile

The user authorized checking the texture pack and installing compatible Luma/DLSS SR/DLSS 5 components, with independent switches and restoration of the previous installation.

**Texture result, local-tested:** Steam initially listed seven DLC items without the free High Resolution Texture Pack. The official pack was added, downloaded and observed complete, then checked enabled in the DLC UI. App/depot 561950, manifest `1157446448995806717`, adds five `uhdmip*.arch06` archives totaling 17,281,814,274 bytes. Steam shows 13.2 GiB downloaded and 16.09 GiB installed. The pre-existing `highmip.arch06` is unchanged. Its independent on/off owner remains Steam's DLC checkbox; the switcher links to those controls rather than renaming official archives or rewriting Steam manifests.

**Correction from exact source:** Luma latest-761 is pinned to `dc471fa590c24a12a36be3e527ec45d2595466bd`. The game-specific source says TAA and **100% internal/render resolution only**. This is DLAA-style native-resolution AA, not proven lower-resolution DLSS SR. The earlier wiki's generic “DLSS Only” label was insufficient to recommend true SR. No Quality/Performance or dynamic SR mode is invented. The supported preset is explicitly L/12. Its sampler upgrade is disabled because the author identifies darker textures and metallic armor defects in rain.

The same release performs HDR shader/resource upgrades and can disable Windows HDR and relaunch the game when the first process starts with HDR already enabled. This behavior is inherent in its game integration and was disclosed before any launch. Luma's HDR/shader ownership overlaps RenoDX, so the optional profile parks the RenoDX visual add-on and uses Luma's supplied ReShade host. The previous profile restores its exact ReShade binary and INI. No display setting has been changed by file installation.

**Neural candidate, configured but untested:** Generic `renodx-dlss5.addon64` 8.5.0-rc10 from RHI's pinned release mirror; archive digest `A745040CB2E93E3A1500A6C5A322972ACC4C5C667108FCEA31C748285D6364A9`. This is distinct from ShortFuse's separately distributed consumer. The selected binary has a built-in DX11 route; `DX11Source=native`, NGX-only interception, Upscaled hook, one pass and 100% working resolution are configured. No second bridge, optical-flow feeder, OptiScaler or FG/RR owner is deployed. Luma supplies captured engine color/depth/motion/jitter at its DLAA hook; photo mode has a documented dummy-motion path and is not a complete engine-motion contract.

The cached NR 310.8.3 file returned Authenticode `HashMismatch` and was not deployed. A preserved local original 310.8.0 returned **Valid, NVIDIA Corporation**, SHA-256 `E16BCF15E16E13F527491CDF7845B2FE6521A738D8F7C9C721866A8496E1FC8E`, and was copied without altering its source or another game's active files. The Luma-bundled 310.9.16 DLSS runtime also has a valid NVIDIA signature. The separate NIGos bridge was researched/downloaded for provenance comparison but is not installed beside this consumer.

**Controls and preservation, local-tested:** The existing Desktop entry now exposes previous/Luma profiles, independent DLAA/neural switches and original gameplay/group controls. Original menu choices 1/2 remain previous recommended On / all third-party mods Off. File round trips for Luma, NR, DLAA, previous graphics and stock/recommended passed; previous `dxgi.dll`, `ReShade.ini`, both Bink filenames and the executable match the pre-Luma baseline. Profiles, current saves, external/native settings and exact positions/hashes have separate recovery. Steam's overlay was disabled for this game through observed UI, following the saved preference and resolving the F12 screenshot conflict; Steam Cloud stayed enabled. RHI automatic ReShade/RenoDX updates are held for this game only, preserving unrelated settings and other games. The trial is managed by the local profile controller; RHI retains the original visual installation record.

Delete remains the shared graphics panel, F12 the existing gameplay menu, and Generic's configurable NR toggle is set to F10. The unmodified consumer does not provide the requested exact F7 two-scale cycle or F11 four personal slots; those controls are recorded unavailable rather than advertised. No SR resolution shortcut is configured because this release lacks true SR.

**Current boundary:** official textures are installed/on; previous RenoDX graphics and the original three gameplay mods are active; Luma/NR files are installed/off. Startup, HDR transitions, DLAA evaluation, NR creation/evaluation/delivery and combined game stability are untested. The user was asked whether to authorize a main-menu-only check or test manually. No authorization is assumed from silence, and no game, campaign, benchmark or capture has been started. Private machine bindings index the extension receipt, exact payload manifests and pre-Luma recovery.

Sources: [official textures](https://store.steampowered.com/app/561950/), [Luma release](https://github.com/Filoppi/Luma-Framework/releases/tag/latest-761), [pinned game source](https://github.com/Filoppi/Luma-Framework/blob/dc471fa590c24a12a36be3e527ec45d2595466bd/Source/Games/Middle-earth%20Shadow%20of%20War/main.cpp), [Generic release mirror](https://github.com/RankFTW/rhi-repo/releases/tag/renodx-dlss5-8.5.0-rc10), [bridge author contract](https://github.com/NIGos/dlss5-bridge).

## 2026-10-24 — Selected graphics, multiple skills and movement/FOV installation

The user requested graphics and gameplay/QoL additions, especially concurrent abilities and unusual options, with easy on/off control. After three numbered paths, the user explicitly selected option 1: graphics + multiple skills + movement/FOV. Expanded combat/progression modifications were not selected.

### Observed baseline

- Steam manifest build 3095001; rendering executable version 1.0.8874.0, PE machine 0x8664. The upstream graphics path and RHI identify DX11.
- RTX 5090, driver 621.01, 32 GB dedicated VRAM; active PG32UCDP output at 3840×2160/240 Hz with Advanced Color enabled and PQ/BT.2020 color space. This is display/configuration evidence, not in-game HDR acceptance.
- No existing gameplay loader or graphics proxy in the rendering folder. Original Bink runtime and game executable were preserved byte-for-byte. A Steam save existed; the native local configuration folder did not yet exist.
- Preserved a separate baseline and just-in-time snapshots of the rendering folder, Steam save, app manifest and relevant RHI settings/ownership records. Baseline means preserved current files, not a runtime-tested known-good installation on this PC.

### Installation

1. Refreshed RHI 2.8.7 discovery. Its initial four-game cache was stale; the completed scan found the actual thirteen installed game folders, including this game. The attempted manual-add dialog was cancelled, so no duplicate game entry was created. Only this game's install controls were used.
2. Closed Steam normally. Installed ReShade 6.8.0 full add-on support and the exact game-specific RenoDX through RHI. RHI records RenoDX build 26.1023.0600, from the original `mqhaji/renodx` snapshot URL. SHA-256: `9764329523BC7ACB4C044DA5CA636E0F92A510770FD42DE43CEAD3EA5BA6A323`, matching the GitHub release asset digest. RHI's shader tools were copied but no cinematic shader preset was enabled.
3. Closed RHI. Deployed ReaperAnon's original `loaderfix` release, published 2026-10-10, which upstream describes as fixing menu crashes/non-operation. Retained the stock runtime under the documented Bink forwarder name; did not modify the executable.
4. Installed Multi Equip Skills, Elven Speed and FOV Extender from the author's 1.0.0 release. Each selected source patch signature appeared exactly once in this executable. Static signature matching is a compatibility preflight, not evidence that runtime initialization or hooks succeed.
5. Configured the supported gameplay menu to F12 using the loader's actual ImGui key format, ReShade to Delete, and skill multi-equip to held Left Ctrl. Elven Speed uses duration 2 / regeneration 0; FOV uses 45/60. Original source archives and source revisions remain private and unchanged.
6. Added a private double-click PowerShell console switcher plus a verified Desktop shortcut. All operational files and recovery copies remain outside OneDrive; the Desktop contains only the launcher shortcut. The first attempt to use the common Desktop was denied by Windows, so the shortcut was placed on the user's actual Desktop. No permission or persistent security setting was changed.

### Verification and rollback

**local-tested, file level:** All Mods Off → Recommended On; independent Multi Equip Skills Off → On; Graphics Off → On; original Bink SHA-256 restored in Off mode; deployment hashes/settings and save preservation. The switcher takes current-state recovery copies, validates exact ownership/hash pairs, serializes its own operations and blocks switching while the game/store/RHI/helpers are open. Unknown or updated binaries require review rather than blind replacement.

All Mods Off parks the graphics host and loader and restores the exact original runtime. Original mod assets and settings remain available for re-enable. In-game plugin checkbox state is separately owned by the loader; the desktop menu reports file availability. No save is automatically restored. Equipped skill state may persist in saves; restoring an older backup can lose subsequent campaign progress and needs Steam Cloud reconciliation.

**Not tested:** game startup, first generated native settings, borderless/HDR behavior, loader/ReShade combined presentation, F12/Delete response, skill combinations, moving gameplay, stability, performance or live plugin unload/reload. The author's RenoDX page requests borderless and other overlays off. The first-run guide states this boundary. No benchmark, capture, native input-profile change, driver-profile change, cloud upload, reminder or game launch occurred.

### Research boundaries

Luma's current upstream wiki lists Shadow of War as work in progress and DLSS-only. It was researched but not deployed over the selected RenoDX setup. No engine-integrated SR/RR/FG/MFG or neural renderer was claimed. The original catalog records progression, intelligence and combat alternatives separately, including the author's quest-progression warning for full Uruk intel. No expansion-scale addition was established by this review.

Next boundary: the user launches normally from Steam and checks Borderless/HDR, the two menus, a moving scene and clean exit. A separate authorized runtime task can investigate failures. The preserved old library candidate, unrelated toolkit source changes and other game installations remain untouched.

Sources reviewed 2026-10-24: [loader](https://github.com/ReaperAnon/Middle-Earth-Mod-Loader), [loader release](https://github.com/ReaperAnon/Middle-Earth-Mod-Loader/releases/tag/loaderfix), [gameplay collection](https://github.com/ReaperAnon/Shadow-Of-War-Mods), [RenoDX author page](https://www.nexusmods.com/middleearthshadowofwar/mods/130), [RenoDX maintained list](https://github.com/clshortfuse/renodx/wiki/Mods), [RHI](https://github.com/RankFTW/RHI), [Luma](https://github.com/Filoppi/Luma-Framework/wiki).
