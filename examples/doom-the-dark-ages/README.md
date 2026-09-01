# DOOM Tested Configuration Reference

These source/configuration examples correspond to the successful 2560×1440 Vulkan test. They are not a binary installer.

Known-good versions:

- ReShade 6.8 full add-on build for Vulkan
- RenoDX DLSS5 v4.55
- DLSS5-Feeder 0.8.0-beta.4
- Signed NVIDIA DLSS SR and NR 310.8 runtimes
- Lumenite Kernel with `DLSS5_MV_PROVIDER=3`

Keep the compiled gate in the game root and keep the companions under their exact names in `doom-addons`:

```text
doom-addon-gate.addon64
doom-addons\renodx-dlss5.addon64
doom-addons\dlss5-feed.addon64
doom-addons\dlss5-feed.cfg
doom-addons\nvngx_dlss.dll
doom-addons\nvngx_dlssnr.dll
```

The gate source is included for review. Compile it as x64 with matching ReShade add-on headers; do not download an unknown precompiled gate. Prefer an upstream process filter if the projects add one.

Use exclusive 2560×1440 on a 16 GB RTX 5070 Ti. The 4K bridge could start but failed on a later runtime recreation because VRAM headroom was too small. Display-mode indices are monitor-specific.

Read [the full DOOM guide](../../games/DOOM-THE-DARK-AGES.md) before applying these files.
