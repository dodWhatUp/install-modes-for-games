# HDR and Color-Space Verification

An add-on message saying “HDR disabled because of hardware limitations” is not proof that the GPU, display, or game lacks HDR. It may describe only that add-on's private processing path.

## Verify the entire chain

Check independently:

1. Windows HDR state and display capability.
2. The game's HDR setting and swapchain color space.
3. Backbuffer/resource format.
4. ReShade's detected color space.
5. The add-on's HDR flag and conversion path.
6. Actual black floor, peak highlights, clipping, gamut, screenshots/captures, and metadata where available.

A 10-bit format such as `R10G10B10A2` can carry SDR or HDR. Format-only auto-detection can therefore be wrong; color-space metadata such as HDR10/ST2084 is separate evidence. Likewise, an FP16 buffer is not by itself proof of correct HDR output.

## DOOM lesson

In the 2026-09-02 DOOM experiment, ReShade reported `VK_COLOR_SPACE_HDR10_ST2084_EXT`, while the Feeder auto mode (`hdr=-1`) classified the `R10G10B10A2` path as SDR and displayed a hardware-limitation-style warning. The RTX 5070 Ti and native DOOM HDR were capable. The mismatch was between the private Feeder heuristic/path and the actual Vulkan color space, not proof of unsupported hardware.

Do not force an HDR override during an unstable run merely to silence the message. First preserve a working baseline, confirm the add-on's expected transfer function and color range, and test one override at a time. A wrong HDR override can produce double tonemapping, crushed blacks, clipped highlights, or invalid neural input.

## Avoid double processing

- If a game has correct native HDR, do not also enable Windows Auto HDR, RTX HDR, a generic HDR upgrade, and a game-specific HDR tonemapper together.
- A game-specific RenoDX profile usually knows more about the game's shaders than a generic swapchain upgrade. Prefer the specific profile when current and supported.
- ReShade effects must run in the color space they expect. Record whether each effect is before or after tonemapping.
- HDR screenshots can look SDR in ordinary viewers; use an HDR-aware capture and viewer before diagnosing the image from a screenshot.
