# DOOM: The Dark Ages — Experiment History

## Current state

- User decision: stop the experiment and do not install the game now.
- Resume policy: paused indefinitely; do not remind, schedule, launch, reinstall the experiment, or test it until explicitly requested.
- Resumable evidence: a private 2026-09-02 snapshot contains the exact crashed ReShade/RenoDX/Feeder state, sanitized inventory, logs, settings, Steam options, Vulkan registration, and restore sources. It is excluded from Git.
- Last known technical success: pinned RenoDX DLSS5 v4.55 plus DLSS5-Feeder 0.8.0-beta.4 at exclusive 2560×1440.
- Last attempted state: native HDR10 started at 2560×1440, then the Vulkan swapchain recreated at 3840×2160 and the user reported a crash.

## 2026-09-01 — OptiScaler investigation

- Goal: add the experimental neural-rendering feature while preserving DOOM's native SR, RR, and FG.
- Result: inconclusive on Vulkan. The package loaded, but available logs could not distinguish the desired neural pass from native Vulkan NGX traffic.
- Lesson: a DXGI proxy is not the owner of a Vulkan swapchain, and “DLL loaded” is not feature proof. OptiScaler was removed before the RenoDX/Feeder path.
- Compatibility rule: do not combine the tested Feeder path with OptiScaler or NVIDIA Smooth Motion.

## 2026-09-02 — RenoDX/Feeder path established

- Renderer/process: 64-bit Vulkan game plus a separate idTech launcher.
- Working architecture: global ReShade Vulkan layer → process gate → exact-name Feeder and RenoDX add-ons → private D3D12/NGX session.
- Required discovery fix: keep `renodx-dlss5.addon64` and `dlss5-feed.addon64` under their exact names and beside their module-relative config/runtime files.
- Launcher fix: isolate add-ons from the launcher; its layer-validation popup was not proof of an obsolete GPU driver.
- Positive evidence at 2560×1440: Feeder built a DLAA feature, RenoDX created feature 18, inline evaluations succeeded, and more than 16,200 frames were delivered.
- Limitation: most of that long run was a static/menu scene. It proved operation and duration, not final moving-gameplay quality.

## 2026-09-02 — 4K recreation and crash

### What was observed

- The final session began at 2560×1440 with ReShade reporting Vulkan HDR10 (`VK_COLOR_SPACE_HDR10_ST2084_EXT`).
- The swapchain then recreated at 3840×2160.
- Feeder created a 3840×2160 DLAA feature and logged delivery through frame 3,000.
- At frame 3,000 the motion probe finally showed a meaningful moving sample: mean about 1.558 pixels, maximum about 1.78 pixels, and roughly 98% non-zero vectors.
- Logging stopped abruptly after that checkpoint and the user reported that the game crashed.
- Windows Event Viewer contained no matching DOOM application-error entry in the inspected 18:45–19:00 window. Absence of an event does not disprove the crash.

### What the evidence means

- **Proven:** the 4K feature was created and evaluated for thousands of frames before the failure.
- **Strong correlation, not sole-cause proof:** an earlier 4K run reached roughly 15.4/16.3 GB VRAM and a later feature recreation raised caught access violation `0xC0000005`. The extra full-resolution bridge/neural allocations left very little headroom.
- **Still possible:** a recreation, hook-order, driver, or add-on defect contributed. Do not document “VRAM was definitely the only cause.”
- **Practical boundary:** 4K is not an accepted configuration for this 16 GB machine. The only known technical-success boundary is exclusive 2560×1440.

### HDR warning answered

Feeder used `hdr=-1` and classified the 10-bit backbuffer as SDR even though ReShade recorded an HDR10/ST2084 Vulkan color space. The “HDR disabled because of hardware limitations” message described the private add-on path/heuristic; it did not prove that the RTX 5070 Ti, display, Windows, or native DOOM HDR lacked support. See [HDR and Color-Space Verification](../../docs/HDR-AND-COLOR.md).

### Motion-vector and Lumenite question answered

Only `Lumenite_Kernel` and `DLSS5_Feed` were enabled, in that order. The other Lumenite luminance/AO/reflection/quant-motion/debug techniques were not required. Enabling all of them would add work and could change the image without giving Feeder “more real” inputs.

The selected Lumenite path writes the shared `texMotionVectors` resource consumed by Feeder. These are screen-derived/estimated vectors, not DOOM's native engine-tagged vectors. ReShade depth is likewise the selected accessible depth surface. Feeder sends post-process color, depth, and those estimated vectors into its private DLAA/NR evaluation. DOOM's native SR, RR, and FG are separate owners and are not automatically disabled, but they share memory, queues, color-space transitions, and recreation timing, so their continued operation must be reverified.

## 2026-09-02 — paused-state preservation and rollback

- Captured 35 important files plus an inventory and snapshot note (37 files total, about 227.7 MB) before mutation.
- The snapshot includes add-ons, shaders, config, short logs, user graphics settings, launcher settings, Steam app options, and ReShade Vulkan registration.
- Removed the game-root process gate, ReShade files, shaders, Feeder/RenoDX payload, and known OptiScaler payloads using exact path/file guards.
- Restored saved user graphics settings, pre-experiment launcher settings, recorded NVIDIA profile values, and removed the experimental Steam launch options.
- Steam unexpectedly marked the base installation “Files Missing, Uninstalling” during shutdown and removed it. This was not a requested deletion and the exact trigger is unresolved. A clean Steam reinstall was started rather than reconstructing a partial game directory.
- Global ReShade ProgramData files required administrator access and could not be overwritten in-session. If DOOM is installed again later, remove its stale global ReShade registration with the official installer or use a validated per-game Vulkan-layer disable before the first stock launch.
- At 19:53 on 2026-09-02, the user explicitly said not to install DOOM. The active Steam download was stopped. Steam removed the DOOM app manifest, partial download state, and all game files. Only empty `launcherData`/`streamline` directory scaffolding remained. No game launch occurred.

## Lessons promoted to general guidance

- [Feature selection and actual inputs](../../docs/FEATURE-DECISION.md)
- [HDR format versus color-space detection](../../docs/HDR-AND-COLOR.md)
- [Long tests, snapshots, and rollback](../../docs/OPERATING-STANDARD.md)
- [Safe quick-switch profiles](../../docs/QUICK-SWITCH-PROFILES.md)
