# Skyrim Special Edition History

## Current state

- State: **MO2 2.5.2, SKSE64 2.3.1 and Address Library v13 are installed** for Steam runtime 1.7.104. PureDark Skyrim Upscaler AIO Build 19 Hotfix 1 is installed and configured as an MO2 mod but deliberately **disabled** because the current plugin does not support Skyrim 1.7.x.
- Last known-good: the pre-change state is preserved in private snapshot `20261007-095312-pre-skse-puredark-b19hf1`. SKSE injection was observed, but a clean SKSE-only main-menu/gameplay result is not yet established.
- Next boundary: wait for PureDark to publish explicit 1.7.104/1.7.x compatibility, then refresh the snapshot, replace only the PureDark mod, and retest in stages. Do not downgrade Skyrim silently.
- Reminder policy: no reminder or background experiment scheduled.

## 2026-10-07 — SKSE installed; PureDark blocked by confirmed 1.7.x incompatibility

- Downloaded the official Nexus Steam package `SKSE64 2.3.1` for runtime 1.7.104; archive SHA-256 `7BAD616ED360823A027F8828801D91E3A4AA2EACD952023AF7F3E31ADB2AE250`. Installed `skse64_loader.exe` and `skse64_1_7_104.dll` in the game root, placed the 62 required `.pex` files in the MO2 mod `SKSE64 2.3.1 Scripts`, and added an SKSE launcher entry to MO2.
- Downloaded Address Library All in One v13 for 1.7.104; archive SHA-256 `BE0C7C07FB63FD1C1403690D4797C7A8FDF8799118ACCEB605F285D7B0EE055F`. The required `versionlib-1-7-104-0.bin` has SHA-256 `8AAB3DD251D135B849BD983F86A4A205C920FA3E81F8E30C0E63CCFEF9423842` and remains enabled through MO2.
- Installed PureDark Build 19 Hotfix 1 as a separate MO2 mod. Prepared settings select DLSS Quality, NVIDIA DLSS FG, Dynamic MFG targeting the active display refresh, x4 manual fallback, first-person PD FrameWarp, F12 for the unified menu and F10 for DLSS NR. DLSS NR remains off initially. Numpad `+` toggles FrameWarp and numpad `*` toggles FG. F6/F7/F11 and a second Delete menu binding are not available in this binary and were not fabricated.
- Just-in-time snapshot `20261007-095312-pre-skse-puredark-b19hf1` preserves the root manifest and ReShade configuration, MO2 profile/configuration, user INIs, Steam manifest/local configuration, process state, GPU evidence and archive hashes.
- Runtime evidence: SKSE 2.3.1 recognized `SkyrimSE.exe` 1.7.104.0, injected its matching DLL and reached `loading plugin "SkyrimUpscaler"`. PureDark then stopped with `[critical] failed to open address library file`. The same handled failure reproduced with Address Library visible through MO2, with the exact library copied physically into `Data/SKSE/Plugins`, and with Skyrim's working directory forced explicitly. The physical duplicate was removed after it proved ineffective.
- Upstream confirmation: in PureDark's Discord bug thread, a user reported the same failure on Build 19 and PureDark replied on 2026-10-03: `Not compatible with 1.7.xxx yet`. This establishes an upstream runtime-compatibility block, not a missing local Address Library file.
- Safe final state: PureDark remains installed/configured but disabled; SKSE scripts and Address Library remain enabled; existing ReShade 6.8.0.2155 is unchanged; no Community Shaders, competing FG owner or RTSS process was introduced. Effective HAGS and NVIDIA Smooth Motion state remain unverified.
- Rollback: disable the two enabled MO2 foundation mods if necessary, delete only `skse64_loader.exe` and `skse64_1_7_104.dll` from the root, remove the MO2 executable entry, and restore the named snapshot. The failed physical Address Library workaround was already removed and is recoverable from the downloaded archive/MO2 mod.

## 2026-10-07 — PureDark AIO Build 19 Hotfix 1 prepared

- Confirmed the Patreon-linked Discord membership and official `Upscaler User` access. Downloaded `SkyrimUpscalerAIOBuild19-Hotfix1.zip` from PureDark's `skyrim-downloads` forum; 293,378,393 bytes, SHA-256 `A1278908205EC6C6442E204EEB504264AB6D2FEAA95E79026F534511C109FE6C`.
- The package contains an SKSE plugin plus its `UpscalerBasePlugin` runtime. Its default configuration selects DLSS upscaling, DLSS frame generation, x2 FG, and first-person PD FrameWarp; Dynamic MFG is available but disabled by default. Hotkeys are `End` for the menu, numpad `+` for FrameWarp, numpad `*` for FG, and numpad `-` for DLSS NR.
- Local target remains Steam build 24914197, `SkyrimSE.exe` 1.7.104.0, RTX 5070 Ti and NVIDIA 616.56. Existing root ReShade 6.8.0 matches Hotfix 1's stated requirement. Current profile settings are borderless; no ENB, Community Shaders, SKSE or competing FG owner was found.
- Archive inspection found signed NVIDIA/Intel/Streamline components and unsigned mod/AMD components. `nvngx_dlssnr.dll` reported `HashMismatch` through Windows Authenticode; this is recorded as an inspection result, not a malware conclusion. The attempted Defender custom scan returned an error and therefore did not verify the archive.
- No game or MO2 files were changed. Installation stopped at the prerequisite boundary because the official SKSE64 2.3.1 package for Steam 1.7.104 is Nexus-hosted and the current Nexus session is a guest. No older SKSE, downgrade or unofficial substitute was installed.
- The private Drive archive and full hash manifest are documented in [the PureDark archive index](../../docs/PUREDARK-ARCHIVE-2026-10-07.md). Paid archives and Discord CDN URLs remain outside Git.
- Planned first test after SKSE is available: stock launch, SKSE launch, AIO with DLSS SR only, DLSS FG/MFG, then PD FrameWarp. Keep RTSS off for the first pass, NVIDIA Smooth Motion off, ReShade updated at 6.8.0 full add-on support, and only one FG owner active.
- Rollback: disable the MO2 PureDark mod, remove only manifested SKSE root files if SKSE itself must be reverted, and restore the just-in-time root/profile snapshot. No rollback is needed yet because deployment did not occur.

## 2026-09-14 — Installed-library review

- Goal: compare performance, QoL, UI, graphics/DLSS, animation, AI, abilities, mechanics and content expansions for every installed game.
- Baseline evidence: Steam build 24914197 and real executable `SkyrimSE.exe` were found. GPU RTX 5070 Ti; driver 616.56.
- Exact change: added sourced [comparisons](COMPARISONS.md), catalog and playthrough recommendations. Downloaded official MO2 2.5.2 into a private staging area and extracted it into a new dedicated manager directory. Preserved Skyrim root files, settings and 154 user-data/save files in a private baseline snapshot before configuration.
- Observed result: research and file-presence checks only; no performance benchmark or newly modded gameplay success.
- Failure evidence: Nexus guest session prevents downloading the selected foundation. Initial hidden manager launch exposed no window; closed that newly started process and reopened through the native app tool.
- Rollback performed: none; original Skyrim/ReShade files remain in place.
- Reusable lesson: exact executable/build and engine-specific capabilities take priority over generic DLL or manager recommendations.
- Safe next options: follow [recommendations](RECOMMENDATIONS.md) and the dated compatibility gates; do not install every catalog entry.

## 2026-09-14 — Manager installation verified

- Source: [official MO2 2.5.2 release](https://github.com/ModOrganizer2/modorganizer/releases/tag/v2.5.2), `Mod.Organizer-2.5.2.7z`, 149,660,212 bytes. SHA-256: `E6376EFD87FD5DDD95AEE959405E8F067AFA526EA6C2C0C5AA03C5108BF4A815`.
- Installed `ModOrganizer.exe` version 2.5.2; SHA-256: `442B354A8F34754DA0048654C44D27F51628FEBA54CE46C3187CF58D6C43E622`. The official archive's executable is unsigned; provenance is the official release URL, not a claimed signature verification.
- Created a dedicated portable Steam Skyrim SE instance outside game/cloud directories. Verified the main manager window, correct game directory, 10 official plugins and profile status. No Vortex deployment or existing game hooks were replaced.
- Profiles: `00 - Baseline` and `01 - Basic - awaiting downloads`, both with local INIs and local saves; automatic archive invalidation selected. Copied existing user INIs into these profiles. Existing saves remain in their original location and private snapshot; neither new profile imports them automatically.
- Private snapshot `baseline-20260914-003324`: original root files and hashes, game-file inventory, Steam manifest/local configuration, user configuration and saves. Preserved manager configuration separately before creating the two profiles. This is a current-state backup, not a verified last-known-good launch.
- Root hash recheck after manager setup: **zero changed pre-existing game root files**. SkyrimSE.exe SHA-256: `846EFCCF0C1374D71F892907F46549560F2FCB0A75CB87A3EED438BAA0F1402F`.
- Steam Skyrim launch options: none observed in the relevant application configuration block. Display mode/HDR and actual current driver output remain unverified because no game launch was performed.
- Download blocker: Nexus explicitly requires sign-in; the sign-in page was left ready for the user. The author's alternate SKSE archive lists older builds only, so no incompatible substitute was installed.
- SKSE, Address Library, SkyUI, MCM Helper, performance fixes and DLSS/Community Shaders: **not installed by this task**. No gameplay or performance validation occurred; another game was active during preparation.
- Rollback now: close MO2 and use the original Steam launch path; Skyrim root files need no restoration because they were not changed. The new manager directory can be retained as an inactive staging setup. Do not delete saves or apply a root-file rollback unnecessarily.
- Resume from [basic setup checklist](BASIC-SETUP.md). Refresh runtime/source checks if the game updates while awaiting downloads. No reminder or automatic resume was scheduled.
