# Cyberpunk 2077 — Preferences

**Current mapping, 2026-09-13 evening:** F11 recalls personal NR settings slots 0–3, with Save Settings storing the selected slot. F7 toggles NR 25%/100% only. F8/Page Up/Page Down are unbound; user prefers NVIDIA statistics. F6 controls native DLSS separately; F9 remains Quick Load. Slot numbers are independent of the model hints inside them.

Last confirmed: 2026-09-20


## Latest requested direction — 2026-09-20 (late integration update)

- Use **RHI** as the normal management/orchestration layer whenever a future Cyberpunk graphics installation/update is requested and the exact components are supported. Prefer RHI-managed ReShade/RenoDX/Luma/OptiScaler/DLSS/Streamline deployment/version control over parallel manual copies when equivalent.
- Treat RHI as the manager, not as a new SR/RR/FG/neural owner. Preserve the existing one-owner and real-engine-input rules and keep exact underlying component versions.
- Always surface **Ultra+** as a distinct option when Cyberpunk path tracing is being configured or improved. Ultra+ is a game-specific PT/rendering overhaul that changes the underlying PT/lighting/denoising/rendering behavior; do not describe it as a normal graphics preset or generic post-process filter.
- Current upstream checkpoints recorded for discovery on 2026-09-20: RHI **2.7.4** and Cyberpunk Ultra+ **9.3.7** (released 2026-09-13). Re-check current releases at installation time.
- RHI's own Ultra+ button/link may be used as the discovery entry point, but Ultra+ remains an independent mod whose CET/RED4ext requirements and overlap with RR/NR/other PT changes must be validated before installation.
- This update changes future planning defaults only. It does not claim RHI or Ultra+ is installed in the current Cyberpunk profile.

## Latest requested direction — 2026-09-14

- Add FPS-targeted Dynamic DLSS SR in F12. The user explicitly selected **30 FPS before frame generation**. Keep the target adjustable, start with supported 50–100% render bounds, preserve SR L and existing NR slots, and use the native engine controller through the existing adapter. Do not conflate this with Dynamic MFG.
- User explicitly selected a common OptiScaler/ReShade control interface for SR, RR, MFG/Dynamic MFG and NR. Extend the existing OptiScaler installation first. This supersedes the earlier requirement that native MFG controls remain outside OptiScaler, while preserving one underlying FG implementation.
- Use latest compatible NVIDIA runtimes and documented RR/FG models; explicitly select SR model L. Preserve personal NR slots and the established keyboard mapping.
- Apply SR resolution and NR changes during gameplay, with no restart/save reload for those settings; show effective dimensions and verify actual engine changes. DLL installation and changes to the FG backend still require a closed game.
- Monthly automatic update checks are authorized through the `Monthly Cyberpunk graphics updates` task. Preserve local controls and snapshots; do not interrupt active games. No daily or per-launch update check was requested.

## Always prefer

- Preserve Cyberpunk's native DLSS SR, Ray Reconstruction, Streamline, Reflex, and RTX 50 MFG files.
- Keep exactly one FG/MFG implementation. OptiScaler may control Cyberpunk's native Streamline settings; do not add a second generated-frame output.
- Verify the RTX 50 neural runtime by both SHA-256 and a valid NVIDIA signature.
- Keep the first neural test to one FP8 pass, pre-SR, with captures and secondary experiments off.
- Preserve the executable directory and `UserSettings.json` before updates or proxy changes.
- Use Delete full menu, F12 compact NR window, F11 personal slots, F10 neural on/off, F7 NR 25%/100% and F6 native DLSS quality. Keep F8/Page Up/Page Down unbound. CET's own menu uses Insert.
- Save each NR slot explicitly and visibly report its number. Do not force direct native game-settings writes. F11 stores user-selected NR settings; native DLSS/FG remains separate.

## Prefer when compatible

- High image quality at 4K with native DLSS temporal inputs.
- Native/official named controls before numeric preset forcing.
- `dxgi.dll` for this clean install because it was absent and does not use Cyberpunk's problematic `d3d12.dll` proxy route.

## Ask before

- Enabling multipass, finished-picture placement, residual-across-RR, residual FG, hybrid precision, or OptiScaler-owned FG.
- Adding further CET-dependent mods, RED4ext, redscript, ReShade, RenoDX, or another proxy/overlay. The specific CET 1.37.1 + GraphicsHotkeys adapter for F7 was approved and installed on 2026-09-13; its runtime combination remains untested.
- Turning the global RT/path-tracing stack on as part of neural validation; test it as a separate setting group.

## Avoid

- DLSS5-Feeder or the RenoDX DLSS5 add-on alongside this OptiScaler neural consumer.
- Replacing or renaming `nvngx_dlssd.dll` as a neural runtime.
- Rapid NR/model-scale toggling while native FG is active until the reported Cyberpunk device-removal path is resolved.
- Trusting a DLL because its filename or version string says 310.8 when its hash/signature does not validate.

## Hardware/build constraints

- Recorded game/build: Cyberpunk 2077 2.31, Steam build 20383525.
- Recorded GPU/driver: RTX 5070 Ti 16 GB, 616.56.
- Original NVIDIA-signed DLSS-NR 310.8 is the RTX 50 runtime. Other RTX generations require their documented compatibility runtime and are outside this profile.
