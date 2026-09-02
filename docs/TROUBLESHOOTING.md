# Troubleshooting by Symptom

## No overlay and no log

Likely causes:

- The files are beside a launcher instead of the rendering executable.
- ReShade or the add-on has the wrong bitness.
- The proxy name does not match the API the game loads.
- Vulkan ReShade was installed as a DXGI proxy instead of a Vulkan layer.
- Anti-cheat or security software blocked injection.

Check the process name and renderer before changing configuration values.

## Overlay loads, but the feature does nothing

An overlay proves only that the injection framework loaded.

- OptiScaler needs a supported temporal-upscaler input path.
- RenoDX DLSS5 needs real or synthetic NGX evaluations to hook.
- A no-DLSS game needs Feeder or another documented bridge.
- Feeder needs the color input, depth texture, motion vectors, compatible NGX runtime, and RenoDX add-on.

Look for positive evidence, not just the absence of errors.

## ReShade reports missing technique or textures

Expected Feeder resources include `DLSS5_Feed`, `DLSS5_MV`, and `DLSS5_Depth`. A typical startup may report them missing briefly while effects compile, but the next status should report them found.

If they stay missing:

- Confirm `DLSS5_Feed.fx` is in `reshade-shaders\Shaders`.
- Confirm the effect search path points to that directory.
- Confirm the motion-vector provider compiled and is enabled before Feeder.
- Reload effects from the ReShade overlay and read the compile errors in `ReShade.log`.

Do not copy shader files from this repository; obtain them from their authors so versions and licenses remain intact.

## Black frame or only the HUD is visible

Common causes:

- Wrong depth orientation.
- Invalid or missing motion vectors.
- Experimental work-resolution scaling that the path cannot support.
- The effect runs against a launcher/minimal swapchain rather than the game.
- Two components are writing to the same swapchain.
- Exclusive-fullscreen swapchain recreation broke the effect runtime.

Return to 100% work resolution, automatic HDR/depth detection, windowed or borderless mode, and one injection layer. Disable the neural pass while keeping the motion-vector debug view active.

The Bayonetta 67% work-resolution experiment produced black captures; the verified delivery run used 100%.

## Crash during startup or menu entry

- Remove duplicate `dxgi.dll`, `winmm.dll`, `d3d9.dll`, or global Vulkan hooks.
- Disable Steam, NVIDIA, Discord, RTSS, and similar overlays for one diagnostic run.
- In OptiScaler, `DisableOverlays=true` stabilized the Hogwarts test environment.
- Do not force OptiScaler frame generation while the game's native DLSSG/MFG path is also active.
- Isolate add-ons from launchers that create their own graphics devices.

If the game works after disabling an overlay, re-enable overlays one at a time. “All overlays off” is a diagnostic state, not necessarily a permanent requirement.

## Feeder says `SuperSampling.Available=0`

NGX initialized, but DLSS Super Resolution was unavailable to the device/session. Verify:

- Supported NVIDIA GPU and current driver.
- A trusted, correctly named `nvngx_dlss.dll` where the Feeder instructions expect it.
- RenoDX and Feeder are discoverable under the exact upstream filenames.
- The helper/private D3D12 device is using the NVIDIA adapter.
- The process is not also running OptiScaler or NVIDIA Smooth Motion.

This appeared in the first DOOM: The Dark Ages Vulkan test after the process gate renamed and relocated the add-ons. A later clean test kept the exact `.addon64` filenames, placed the signed 310.8 SR/NR runtimes beside them, and reached feature creation and delivery. Therefore `Available=0` was a session/layout/runtime problem in that test, not proof that the RTX GPU lacked DLSS support. Vulkan external-memory/semaphore requirements were already present, so changing unrelated Vulkan extensions would not address it.

## Feature works once, then fails after Alt-Tab or runtime recreation

Treat the second feature creation as a fresh memory allocation. In the DOOM 4K test, the first neural session worked, but VRAM reached about 15.4/16.3 GB and a later recreation raised a caught access violation. The game survived while the neural pass stopped.

- Lower the real output/backbuffer resolution; changing only an internal work percentage may not help.
- Verify the effective size in the Feeder log. Borderless mode can match the desktop and ignore a requested smaller size.
- Leave memory headroom for runtime recreation instead of tuning only for the first successful feature creation.
- A longer create delay changes timing, not available VRAM.

The stable DOOM test used exclusive 2560×1440 instead of a 4K borderless/desktop-sized backbuffer.

## Feeder works but motion looks smeared

- Confirm the log recognizes the selected provider.
- Verify the provider technique runs before `DLSS5_Feed`.
- Test motion-vector sign and X/Y scale.
- Disable MSAA/SSAA.
- Remember that estimated motion vectors are weaker than engine-native vectors and can include the HUD.

Use static and moving scenes. A neural pass can look impressive in a still image while being temporally unstable in motion.

## Logs disagree with the screen

Trust the narrowest evidence:

1. Correct process and renderer loaded.
2. Required add-on registered.
3. Required resources found.
4. Feature created.
5. Feature evaluated repeatedly.
6. Frames delivered and presented.
7. Shutdown completed without a hang.

Do not treat impossible counters such as `9999 FPS` as performance results. They indicate an overlay/present-hook measurement problem.

## Add-on says HDR is unsupported, but native HDR works

Separate the game's output from the add-on's private feature path. A 10-bit backbuffer can be SDR or HDR, and a format-only heuristic may miss Vulkan HDR10/ST2084 color-space metadata. Confirm Windows, game, swapchain color space, ReShade log, and add-on HDR state independently. Do not force HDR until the expected transfer function is known; see [HDR and Color-Space Verification](HDR-AND-COLOR.md).

## Crash after thousands of successful frames

Successful creation is not stability proof. Correlate the final log timestamp with VRAM/RAM, swapchain or resolution recreation, alt-tab, scene transition, and Event Viewer/WER. Preserve the exact state before rollback. If VRAM is near capacity, lower the actual backbuffer—not only an internal scale—and leave headroom for a second allocation during recreation.
