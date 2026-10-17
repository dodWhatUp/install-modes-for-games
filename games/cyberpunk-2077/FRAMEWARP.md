# Cyberpunk 2077 — FrameWarp experiment

**Historical experiment; removed 2026-10-10.** The user selected the [clean ReShade/RenoDX/Ultra+ rebuild](CLEAN-REBUILD.md). FrameWarp's add-on, presenter and settings were quarantined. Its old On/Off controller now stops with a current-guide pointer. Do not run the historical deployment steps below without a newly selected compatibility review.

Installed 2026-10-07: [FrameWarp / XPAR v1.8.5](https://github.com/xPoiler/Reshade-Asynchronous-Reprojection/releases/tag/v1.8.5), the latest published release at installation, hosted by ReShade 6.8.0 with full add-on support. This is a Cyberpunk-compatible asynchronous-reprojection mod, **not** PureDark's Skyrim mod or a standalone Reflex 2 demo. It uses its own XPAR warp engine; it is not an official NVIDIA Reflex 2 integration.

## What changed

Added exactly these files under `bin/x64`: `dxgi.dll` (ReShade), `FrameWarp.addon64`, `FrameWarp/FrameWarpPresenter.exe`, `ReShade.ini`, and `ReShadePreset.ini`. All five matched their staged hashes. All 97 captured pre-existing game/external files remained byte-identical, including native NVIDIA SR/RR/FG, Streamline, saved graphics settings, and existing loaders. No OptiScaler, NR consumer, Latewarp, RenoDX or shader preset was added. ReShade is the required FrameWarp host, not a visual-effects profile.

Current settings were preserved, not optimized: native DLSS SR Ultra Performance, RR off, native FG x2 on, Reflex on, borderless, HDR10 PQ, no V-Sync or enabled in-game FPS limit. Installed runtimes remain native 310.1 / Streamline 2.7.1. RR remains available; its saved off state was not changed. Native DLSS is the intended input source, not a synthetic feeder.

XPAR's own moving-object frame generation is off; native FG remains the sole FG path. Optional NVIDIA Latewarp was omitted because that engine pauses while FG is enabled. More than 4x FG does not deliver every generated image through this release: it samples three generated images per real frame. Start with the preserved x2 setting.

## First launch — user validation

1. Start Cyberpunk normally. The presenter starts automatically; **do not launch `FrameWarpPresenter.exe` yourself**.
2. Press **Delete**, then open **Add-ons > XPAR**. Delete replaces upstream's default Home key, using the user's saved ReShade-menu preference. Ensure **Warp engine: XPAR** and **Enable reprojection** are selected. Keep Auto latency initially.
3. In a repeatable, safe scene, turn the camera for several seconds so the camera/weapon model can settle. Check actual DLSS camera/depth/motion input and presenter/output status in the panel; a loaded overlay alone is not proof of functioning warping.
4. Use **Show original (A/B)** to compare against native DLSS + x2 FG. Check camera motion, weapon edges, transparent HUD, menus, HDR brightness/colour, frame pacing, VRAM, alt-tab and clean game/helper shutdown. Do not judge success from an FPS counter alone.
5. If the panel reports a HAGS warning, confirm Hardware-accelerated GPU scheduling in Windows; its live status was not established during installation. If output is unexpectedly capped, inspect NVIDIA **Background Application Max Frame Rate** for both the game and presenter. No global driver setting was changed.

FrameWarp needs GPU headroom and roughly 1 GB additional VRAM at 4K, depending on options. Transparent HUD, uncovered screen edges and fast motion can show artifacts. Source supports HDR10/scRGB presenter colour spaces, but this user's HDR display path remains untested. Do not turn on extra experimental motion/FG options during the initial comparison.

F5/F6 remain native save/load; no new binding was assigned to F8/Page Up/Page Down. The historical F9/F12/NR controls depended on a CET/OptiScaler stack that is absent now: this installation does not restore or claim them. Delete is the full supported FrameWarp control surface. Detailed diagnostics are off initially; enable them only to reproduce a problem. Logs are under `bin/x64/FrameWarp/logs`, with the previous run moved to `logs/previous`; preserve both before repeated launches.

## Rollback and re-enable

Close Cyberpunk, Steam, launchers, presenter and mod managers first. Private `FrameWarp-Off.cmd` and `FrameWarp-On.cmd` in the existing Cyberpunk modding workspace call the guarded component controller. They snapshot current settings and switch **only** the three owned binaries. Mutable ReShade settings and diagnostics remain for reuse; native game runtimes and other mods are not removed. The original pre-install snapshot is `before-framewarp-20261007-100716`; older known-good snapshots remain intact.

Controller identity: `framewarp-xpar-1.8.5`, separate state directory `framewarp-state`. Do not use stale ReShade/RenoDX component records or RHI's OptiScaler uninstall for this stack. If the controller reports drift, stop and inspect; do not force deletion or overwrite a changed DLL.

Shortcut PowerShell syntax and enabled/no-drift status passed. A requested Disable/Enable verification was safely refused because Steam had reopened: no target files were changed, and FrameWarp remains enabled. End-to-end removal/re-enable is therefore not claimed as tested. Close Steam fully before using either shortcut.

## Verification boundary and known helper error

Static installation, payload hashes, x64 architecture and unchanged native files passed. No Cyberpunk launch or camera/input/presentation/HDR/stability test was performed; gameplay validation remains with the user per the saved preference.

A no-argument smoke invocation of the **staged**, not installed, presenter exited with `0xC0000409` in `ucrtbase.dll`, and produced an empty log. Source v1.8.5 starts a logging thread then returns early when `--pid` is missing, without joining the thread. This is consistent with a joinable-thread termination bug on invalid standalone invocation, an inference rather than a debugger-proven cause. Normal add-on startup supplies `--pid` and shared memory. The invalid invocation neither proves the in-game path broken nor passes runtime validation. Verified upstream binaries were not patched.

RenoDX's separate visual stage was reviewed and left absent for this isolated warping experiment, respecting the latest native-only baseline. Adding a visual profile would require a separate snapshot and combined-stack validation; it is not needed for warping.
