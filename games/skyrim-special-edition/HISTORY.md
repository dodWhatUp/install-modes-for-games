# Skyrim Special Edition History

## Current state

- State: **MO2 2.5.2 installed and configured**. PureDark Skyrim Upscaler AIO Build 19 Hotfix 1 is downloaded, inspected and privately archived, but **not deployed** because official SKSE64 2.3.1 still requires Nexus sign-in.
- Last known-good: not established in this review; current files are not evidence of launchability.
- Next boundary: obtain official SKSE64 2.3.1 after Nexus sign-in, refresh the just-in-time snapshot, then deploy SKSE and the PureDark package one layer at a time through the existing MO2 profile.
- Reminder policy: no reminder or background experiment scheduled.

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
