# Skyrim Special Edition Preferences

Last confirmed: 2026-10-10.

## Always prefer

Compare multiple useful options per category; include performance, QoL, configuration/UI, graphics, animation/movement, enemy behaviour, abilities/magic/tools, mechanics and actual new playable content. State explicitly when no qualifying candidate was verified.

## Prefer when compatible

MO2 + matching SKSE, Address Library, SkyUI and MCM Helper. Later additions should fit the user's preference for image quality with performance/VRAM headroom. Preserve original balance and story for a first playthrough; separate overhauls and save-dependent content.

## Graphics controls

Inherit [general preferences](../../preferences/GENERAL.md) and [graphics controls](../../docs/GRAPHICS-CONTROLS.md). ReShade uses Delete; any future compatible OptiScaler full menu uses Home. The ReShade setting is installed and statically verified; runtime input remains pending. A supported integration is required before exposing SR/RR/FG/NR actions; an INI cannot supply missing inputs.

## Scope and constraints

User explicitly authorized installing Skyrim's basic setup and PureDark, then explicitly requested the runtime downgrade and removal of incompatible mods. The selected target is now Steam 1.6.1170 with matching SKSE64 2.2.6. Prefer recoverable archiving of incompatible versions over permanent deletion. The user specifically wants NVIDIA MFG and FrameWarp in **third person**, and on 2026-10-10 authorized in-game display/performance validation. Keep NR off for the initial MFG/FrameWarp test. Native third-person support comes first; optional camera mods are a separate test, not a dependency to install automatically. Exact game-build support and save compatibility remain gates. No game purchase, online injection, global permission changes or automatic reminder is implied.

For automated input testing on 2026-10-10, the user selected **reWASD in a separate profile, without purchase and without changing existing profiles**, and wanted the agent to perform game input. Further third-person feature testing was conditional on that input route working. Preserve physical-device profiles and remap/group state; this choice is not permission to disconnect/hide devices, replace the shared controls base, elevate tools or activate a new license/trial.

Later on 2026-10-10, the user requested a **small separate AHK test script that they will launch manually**, with no existing-profile changes. Test only F12 menu delivery first; continue third-person MFG/FrameWarp validation only if it works. The temporary F8 trigger is diagnostic while the script runs, not a new persistent graphics hotkey or shared-controls preference.

The user then requested an **active-status indication shown by default, with a visibility option**, and a more extensible helper kept in the **same AHK file** for future games/desktop actions. Preserve exact-target scoping and no existing-profile changes; this is not authorization to run unattended commands, register universal app actions or claim game input works before observation.

The later scope clarification prioritizes **agent keyboard delivery and opening/operating mod menus only**. Defer graphics troubleshooting, MFG/FrameWarp/third-person performance tests and further helper development until separately resumed. Reply in **English regardless of the user's message language**. The user prefers Steam overlay Off in almost all play sessions and authorized disabling it or relevant interfering apps for this exceptional diagnosis; only Skyrim's per-game toggle was changed. Do not infer permission for routine agent control while playing, account/security changes or changes to existing control profiles.
