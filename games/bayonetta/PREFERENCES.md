# Bayonetta — Preferences

Last confirmed: 2026-09-02

- Preserve the working 32-bit game / 64-bit NGX-helper separation.
- Favor native 4K image quality, but keep a lower-resolution rollback because old D3D9/fullscreen paths can be fragile.
- Do not describe the Feeder path as a performance upscaler or frame generator.
- Keep ENB, ReShade presets, dgVoodoo, ShaderToggler, Feeder, and other proxy users in explicitly audited profiles; they can compete for `d3d9.dll`/`dxgi.dll` or reorder effects.
- Do not use trainers/cheats for a first playthrough by default. Practice and input-assistance functions can be recommended later.
- Never change global Windows security controls automatically for a mod.
