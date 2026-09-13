# Skyrim Special Edition History

## Current state

- State: **MO2 2.5.2 installed and configured**; basic mods are **not installed yet** because Nexus downloads require sign-in.
- Last known-good: not established in this review; current files are not evidence of launchability.
- Next boundary: obtain matching foundation packages after Nexus sign-in, refresh the just-in-time snapshot and validate each installed layer.
- Reminder policy: no reminder or background experiment scheduled.

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
