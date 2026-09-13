# Batman: Arkham Knight Preferences

**Current selection, 2026-09-13:** the user requested every DLSS feature that can work well together, including interoperability between add-ons. This authorized the reversible Luma + OptiScaler trial. Keep one owner per feature; installing RenoDX as a second neural consumer would not add a missing feature. Preserve the user-confirmed working stock baseline.

**Current mapping:** Delete full menu, F12 compact menu, F11 numeric NR preset cycle, F10 NR on/off, F8 real before/after SR, F7 NR dimensions 25% ↔ 100%, F9 reserved. These OptiScaler actions passed live checks. F6 is unavailable because there is no live engine-resolution adapter. Home is configured for ReShade but its automated opening check was unsuccessful. F7's inherited profiling binding remains removed through UserInput.ini. See [controls](CONTROLS.md).

**Practical default:** keep DLAA with 25% NR, preset 0, one pass after SR; full 4K NR cost about 28 FPS in the tested scene. Do not add FG/MFG while the active FP16/scRGB output remains incompatible with the selected Streamline runtime. Do not invent SR/RR modes. No FPS-cap change selected or applied.

**Overlay readability:** user reported tiny unreadable text. Local ReShade and OptiScaler fonts were raised to 18 at 2× scale (approximately 36 pixels); readability at the next launch remains to be confirmed. Keep these larger Batman menu settings when preserving this profile.

## Historical selections before the Luma trial

Last confirmed: 2026-09-13.

- User-selected goal: OptiScaler with DLSS 5 neural rendering.
- Use the upstream-documented Feeder/Dagherbou chain because the game lacks a native temporal-upscaler integration.
- Preserve stock rendering/configuration and existing cloud saves. Keep experiments reversible.
- No extra frame-generation, HDR, performance, gameplay, cosmetic or post-processing mods were selected.
- Delete/F10 and Page Up/Page Down follow general controls. Home belongs to ReShade.
- User requested F9 for NR resolution, F8 for ordering and F7 for SR quality, then authorized implementation where possible. F9 is installed with a 100/75/67/50% cycle; F8/F7 remain unavailable in this chain. Save the chosen scale through OptiScaler's **Save Settings**.
- F12 compact controls and F11 preset cycling are absent from this exact upstream fork; do not substitute another build solely for those controls without validating the Feeder chain.
- RTX 5070 Ti 16 GB, driver 616.56. Runtime quality/performance must be checked before recommending full-resolution 4K NR.
