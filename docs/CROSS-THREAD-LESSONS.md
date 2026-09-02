# Lessons Consolidated from Related Modding Tasks

Collected: 2026-09-02. These are distilled conclusions from related DOOM, Hogwarts Legacy, Bayonetta, OptiScaler, ReShade, RenoDX, DLSS, Ray Reconstruction, Frame Generation, latency, and input-buffer discussions. They intentionally omit private paths and full chat/log transcripts.

## DLSS features are separate contracts

- Updating `nvngx_dlss.dll` can provide a newer SR model to an existing integration; it does not create missing depth, motion vectors, jitter, exposure, UI masks, FG markers, or ray data.
- Official DLSS/FG overrides require the game to have the corresponding integration. They can upgrade/control an existing path but do not turn an SR-only title into a native FG/RR title.
- RR is not neural rendering and `nvngx_dlssnr.dll` must not be renamed to `nvngx_dlssd.dll`.
- A game with FSR2/XeSS/DLSS temporal inputs is a better OptiScaler candidate than a game with only TAA; a game without usable motion vectors is a development project, not a simple DLL install.

## Native versus estimated inputs

- Native Streamline FG expects dense camera/object motion, depth, HUD-less color or UI data, constants and correct presentation timing.
- Native RR also requires noisy ray-traced input and reflection/ray-specific information.
- A ReShade feeder sees the processed color frame, selected depth and a shared estimated motion-vector texture. It cannot recover all hidden/disoccluded surfaces or guarantee particle/transparency/UI separation.
- “New brain, same sensors” is the useful mental model: a newer model may help, but output is bounded by the inputs the game/bridge supplies.

## ReShade and generated frames

- In a normal compatible order, ReShade processes real rendered frames before FG; generated frames interpolate those processed real frames. ReShade does not necessarily execute its effects separately on every synthetic frame.
- 3×/4× generation magnifies resource-state, hook-order, UI and timing mistakes that may be less visible at 2×.
- A resource-unwrapping or HUD fix can solve a specific chain and also introduce a new conflict. Treat it as one test layer, not a universal cure.

## Injector ownership

- Do not let native and injected FG control the same swapchain.
- Do not run Feeder with OptiScaler or NVIDIA Smooth Motion under the current upstream warning.
- Keep HDR, SR/DLAA, RR, FG/MFG and neural owners explicit. Logical separation does not remove shared VRAM/queue/recreation interactions.

## DOOM-specific consolidated findings

- The renderer is Vulkan and the launcher is a separate graphics process. Launcher injection is not proof of game injection.
- OptiScaler's tested Vulkan neural path was inconclusive.
- Exact add-on filenames and module-relative runtime/config placement were required for Feeder/RenoDX discovery.
- The 1440p path created feature 18 and delivered more than 16,200 frames; the later 4K path crashed after thousands of frames and had prior near-saturation VRAM evidence.
- The HDR hardware warning was inconsistent with the logged HDR10/ST2084 Vulkan color space; it described the private add-on path, not native hardware capability.
- Meaningful non-zero estimated motion vectors were finally observed in the last run, but the crash prevented a complete visual-quality/stability verdict.

## Hogwarts Legacy consolidated findings

- Install graphics proxies beside the real `Phoenix\Binaries\Win64\HogwartsLegacy.exe`.
- The stable tested responsibility split was native game MFG plus OptiScaler FG disabled; forcing a second FG controller was unstable.
- Ultra Plus, alternative performance packs and arbitrary Engine.ini edits overlap. Use one integrated baseline and merge only reviewed deltas.

## Bayonetta consolidated findings

- The local Steam executable is 32-bit D3D9, despite an earlier conversation-level assumption that it was 64-bit.
- The working solution required dgVoodoo2 and a 32-bit Feeder plus 64-bit helper. This is a game-specific architecture exception.
- 100% work resolution delivered/evaluated 4K frames; 67% produced black captures. The path is full-resolution neural processing, not proven performance upscaling or MFG.
- A global Windows security change was explicitly user-authorized in that experiment and must never become default automation.

## Latency and diagnostic strategy

- Basic same-path interception may add little overhead, but cross-API/cross-process bridges, resource tracking, UI fixes, extra overlays and multiple present hooks can add measurable cost.
- Use a repeatable scene, FrameView or equivalent frame-time evidence, component logs, and a visual marker/high-speed capture when verifying whether generated frames inherit post-processing.
- Preserve failed-state logs and hashes before changing versions. Test empty/minimal presets and one owner at a time.

## Time-sensitive claims

Release names, model numbers, supported game lists, and driver overrides change quickly. Re-check NVIDIA and upstream project sources before a future install rather than treating a conversation date as permanent compatibility.
