# DOOM: The Dark Ages

Status: **partial / not yet working for DLSS neural rendering**.

The useful result is diagnostic: the Vulkan/ReShade/process-isolation chain worked, but the private D3D12 NGX session reported DLSS Super Resolution unavailable, so no neural frames were delivered.

## Stock baseline recorded before experiments

- 64-bit Vulkan game with `DOOMTheDarkAges.exe` and a separate `idTechLauncher.exe`
- Stock Streamline `2.11.1.0`
- Stock DLSS SR, RR, and FG DLLs `310.6.0.0`
- RTX 5070 Ti, driver 616.56

The baseline preserved the complete stock `streamline\production` directory and user graphics configuration before any test.

## Experiment A: OptiScaler DLSSNR build

The first experiment added OptiScaler as `winmm.dll` without replacing DOOM's stock Streamline files. It selected the `ffx_12` Vulkan-on-D3D12 bridge, disabled OptiScaler frame generation, and enabled the experimental neural-rendering pass.

This did not provide conclusive neural-rendering proof. The package documentation in the archive said its Vulkan neural path was not wired at that time. Repeated successful Vulkan NGX evaluation messages could be the game's existing DLSS path, so this experiment must not be labeled working.

OptiScaler was fully backed up and removed before the Feeder experiment. This separation matters because current DLSS5-Feeder documentation warns against running it with OptiScaler or NVIDIA Smooth Motion.

## Experiment B: ReShade + RenoDX + DLSS5-Feeder

The intended chain was:

```text
DOOM Vulkan frame
  → ReShade Vulkan layer
  → Lumenite motion vectors + DLSS5_Feed
  → Feeder Vulkan/D3D12 shared-resource transport
  → NGX DLAA contract
  → RenoDX DLSS5 neural hook
  → result returned to Vulkan
```

### What worked

- ReShade 6.8.0 loaded as a Vulkan layer.
- A small process gate skipped RenoDX and Feeder in `idTechLauncher.exe`.
- The gate loaded both companions only in `DOOMTheDarkAges.exe`.
- The Feeder hook added the one missing Vulkan device extension; all required external-memory, external-semaphore, memory-requirement, and timeline-semaphore capabilities were present.
- ReShade found and compiled the Feeder and Lumenite effects.
- Feeder recognized Lumenite Kernel, motion vectors, depth, and reversed depth.
- `NVSDK_NGX_D3D12_Init` returned success.

### Final blocker

The same Feeder log then reported:

```text
DLSS 5 add-on: renodx-dlss5.addon64 not found next to this add-on
NGX capabilities: SuperSampling.Available=0
stopped: DLSS is not available on this GPU/driver
```

The gate loaded renamed companions (`renodx-dlss5.dll` and `dlss5-feed.dll`) from a subfolder. That solved launcher pollution, but it broke Feeder's exact adjacent-filename discovery. NGX also failed its Super Resolution availability check on the private D3D12 session.

The evidence does not prove which of those two conditions is the sole root cause. It does prove that Vulkan extensions were not the final blocker.

See [the sanitized evidence](../evidence/DOOM-THE-DARK-AGES.txt).

## Next clean diagnostic sequence

1. Restore the stock baseline and verify the game.
2. Install the current Feeder release using its exact documented filenames and directory layout.
3. Keep `renodx-dlss5.addon64`, `dlss5-feed.addon64`, `nvngx_dlss.dll`, and `nvngx_dlssnr.dll` under the names expected by the release.
4. Test the real game executable without the custom gate if possible. If the launcher must remain in the path, use an upstream process-filtering option before renaming add-ons.
5. Confirm the private D3D12 device selects the NVIDIA adapter and the DLSS runtime is trusted/signed.
6. Stop immediately if `SuperSampling.Available=0`; do not tune motion vectors or neural settings until it becomes `1`.
7. After feature creation, require `frame N delivered` plus RenoDX feature-18 evaluation messages before calling it working.

The [experimental configuration](../examples/doom-the-dark-ages/) is retained for analysis, not as a recommended installer.

## DOOM-specific cautions

- The game already ships DLSS SR/RR/FG. Do not replace its entire `streamline\production` directory for an unrelated Feeder experiment.
- NVIDIA profile override IDs are undocumented and version-sensitive. The test used a fixed 4× MFG override temporarily, then restored all six fields to zero.
- A model DLL in the original experiment had `HashMismatch` Authenticode status. It is excluded from this repository and should not be reused.
- The Vulkan layer sees the launcher too. Add-ons that create devices or hooks in the launcher can cause loops, repeated device creation, or early initialization.

## Rollback

1. Close DOOM and `idTechLauncher.exe`.
2. Remove the ReShade Vulkan registration for this game using ReShade's setup tool.
3. Remove only the Feeder/RenoDX/gate files added to the game root and their shader files.
4. Restore the stock `streamline\production` snapshot and graphics settings.
5. Restore NVIDIA App/profile overrides to their recorded values.
6. Verify game files and launch stock once.
