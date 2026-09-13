# Batman: Arkham Knight

**2026-09-14 activation check:** the already-running game again confirmed 3840×2160 DLAA and 960×540 NR evaluation/composition. The Home/Luma menu showed Auto and preset L. The old Feeder and Lumenite shader techniques have been enabled in the preset, but the Feeder add-on remains disabled; those effects are not the current neural activation controls. No graphics settings changed during diagnosis. See the [live activation findings](batman-arkham-knight/HISTORY.md).

**Current state, 2026-09-13 late evening:** ReShade + Luma build 649 + custom OptiScaler DLSS-NR v0.7.7 are installed and have passed a short gameplay test. Luma supplies engine motion/depth/color and jitter; OptiScaler performs native-resolution DLAA and one NR pass. The old crashing Feeder chain remains disabled. See the [current history](batman-arkham-knight/HISTORY.md), [controls](batman-arkham-knight/CONTROLS.md) and [sanitized evidence](../evidence/BATMAN-ARKHAM-KNIGHT.txt).

**Active ownership:** OptiScaler `dxgi.dll` → bundled `ReShade64.dll` → `Luma-Batman Arkham Knight.addon`; signed SR and NR runtimes, with one OptiScaler neural consumer. RenoDX and Feeder are unnecessary in this tested route. Default: 3840×2160 DLAA, NR model 960×540 (25% per dimension), preset 0, one pass after SR. Approximate parked-scene results: NR off 54 FPS, 25% NR 45 FPS, full-resolution NR 28 FPS. These are observations, not a benchmark average.

**Feature limits:** native lower-resolution DLSS Quality/Balanced/Performance and F6 are unavailable in this Luma Batman implementation. RR lacks a ray-tracing input integration. DLSS FG/MFG remain disabled: this Luma run presents FP16/scRGB, which NVIDIA's [Streamline 2.14.1 guide, section 11](https://github.com/NVIDIA-RTX/Streamline/blob/v2.14.1/docs/ProgrammingGuideDLSS_G.md#110-dlss-g-and-hdr) explicitly excludes. Changing this would require a separately validated output conversion/presentation path. The GPU alone does not solve the integration requirement. `MaxFPS=90.000000` remains unchanged.

**Verification boundary:** real DLSS feature creation, engine-input delivery, NR evaluation/composition, live scale/preset/order changes, menus, a loaded Batmobile scene and clean shutdown succeeded. Sustained traversal, combat, resolution changes and alt-tab are not established. [Luma's Batman integration remains unfinished](https://github.com/Filoppi/Luma-Framework/issues/153), so this is an experimental profile with a working stock fallback.

**Latest follow-up:** the 22:09–22:12 run after a Steam-library move still created DLAA and evaluated NR, including preset recreation. Both menus now use font size 18 at 2× scale; next-launch visual verification is pending. A matching native-DX12 warning belongs to OptiScaler's optional finished-picture mode, which should stay off; the exact Home-menu warning has not been captured. See [follow-up history](batman-arkham-knight/HISTORY.md).

**Current rollback:** the private `staging/batman-repair/Restore-LumaTrial.ps1` still targets the previous Steam library. Revalidate its target path and ownership before using it after the move; its earlier dry run applies to the old location. It preserves the trial and restores the disabled-hook baseline from `luma-trial-20260913-204147`. For the text-size edit alone, use the hash-guarded private `menu-readability-20260913-221702/Restore-Menus.ps1` after closing Batman/helpers; its dry run passed at the current location. Do not use older Full/F7 scripts against the Luma layout.

## Historical installation: preserved Feeder profiles

The remaining installation and rollback details describe the earlier superseded profiles only.

**Latest change (2026-09-13):** F7 toggles NR 25%/100%. The rebuilt proxy passed 300/300 helper evaluations at each endpoint, with composition confirming 640×360 and 160×90 model sizes. Game/hotkey checks remain pending. UserInput.ini removes the inherited F7 profiling action. First undo this revision using private `Restore-F7.ps1 -Game Batman` from `f7-controls-20260913/before-f7-20260913-141908`; only then use the earlier restore scripts below. Earlier staged profiles and their ownership manifests remain the previous version until this revision is rolled back.

Status: **OptiScaler DLSS-NR + DLSS5-Feeder installed; static verification passed; isolated neural test passed; game runtime untested**.

## Environment

- Steam app 208650, installed build 13250859, reviewed 2026-09-13.
- Real executable: `Binaries\Win64\BatmanAK.exe`, x64 PE machine `8664`; D3D11 game. No native DLSS/FSR2/XeSS integration was found in the baseline.
- Executable SHA-256: `2684B84DEC2C31E5A00BFF070B00AE41D4FED4FC4BADE51E0D5BC64BFE1B83DB`.
- RTX 5070 Ti, 16303 MiB reported VRAM, NVIDIA 616.56. Desktop 3840×2160; effective game resolution, display mode, Windows HDR and driver Smooth Motion state were not runtime-verified.
- Fresh local installation with cloud save files present. No ReShade/OptiScaler proxies or third-party add-ons found before installation. Stock `EasyHook64.dll` was preserved; a DLL name alone is not evidence of an added mod.
- Single-player installation; no anti-cheat component identified in the binary inventory. No online injection or global driver changes performed.

## Why this path

The user explicitly requested OptiScaler with the DLSS 5 extension. Arkham Knight does not supply a native temporal-upscaler contract. Current Feeder documentation explicitly supports **Dagherbou's OptiScaler DLSS-NR** as a neural consumer. This is a version-specific exception to older advice that Feeder and OptiScaler conflict.

ReShade supplies color/depth and Lumenite estimates optical-flow motion. Feeder constructs a 1:1 DLAA request on a private D3D12 device; OptiScaler runs DLAA and a neural pass. This does not add engine-native motion vectors, DLSS Quality/Balanced modes, Ray Reconstruction, or frame generation, and is not an FPS-boost claim.

## Installed ownership

| Layer | Owner/version | Evidence |
|---|---|---|
| D3D11/ReShade proxy | ReShade 6.8.0.2155 full add-on build, `dxgi.dll` | Exports/version checked |
| NGX interception and neural rendering | Dagherbou OptiScaler DLSS-NR v0.2.0 + local `9737616+f7-25-100`, `winmm.dll` | Four isolated scale tests passed; game input pending |
| Input/transport | DLSS5-Feeder 1.16.0-beta.1, `dlss5-feed.addon64` | Static verification passed; game delivery pending |
| Estimated motion | Lumenite Kernel, mainline commit `f8cbbb4eccfcb7adf0d74bb358ba349272e3c1e9` | Selected before `DLSS5_Feed`; shader compilation in game pending |
| NVIDIA runtime | Signed SR 310.8 and original signed NR 310.8 | Signatures/hashes verified |
| FG/MFG | No added owner; OptiScaler FG disabled | INI verified; driver override state unverified |
| HDR/tonemapping | No added HDR mod | Game output unverified |

The complete OptiScaler runtime folder and attribution files are included. No RenoDX neural consumer, Deep Fried Chicken, extra DX11 bridge, Vulkan layer, or 32-bit helper is installed in the game. The helper used for preflight lives only in private staging.

## Configuration and controls

- `[DlssNr] Enabled=true`, `ScanExposure=false`, `WorkingScale=1.0`, `AutoCapture=false`.
- `[Upscalers] Dx12Upscaler=dlss`; `[FrameGen] Enabled=false`.
- NGX interception enabled; unrelated input hooks and GPU spoofing disabled.
- `DLSS5_MV_PROVIDER=3` belongs in the preset's `[DLSS5_Feed.fx]` section.
- Active technique order: `Lumenite_Kernel`, then `DLSS5_Feed`. Debug effects off.
- Delete: OptiScaler menu; F10: neural on/off; Home: ReShade. Page Up/Page Down: FPS display controls. Key configuration is checked, but hotkeys have not been tested in Arkham Knight.
- F7: NR model dimensions 25% ↔ 100% only; `[DlssNr] ScaleCycleKey=0x76`. **Save Settings** preserves the selected scale. Allow about one second between taps. See [controls](batman-arkham-knight/CONTROLS.md).
- F12 compact controls and F11 preset cycling require a separate custom implementation; those two controls were not added. F8 pre/post-SR and F6 native SR quality are also absent from this chain.

## Verification and next boundary

The upstream verifier reported **19 OK / 0 warnings / 0 failures**. All 35 added files matched the staging manifest; all 25 original binary-directory files remained unchanged. The isolated 640×360 test completed **300/300 evaluations**, logged neural feature 18 and `DLSS-NR running`, and exited 0. The OptiScaler log also confirms native DLSS feature creation succeeded; an earlier requirements-query warning was not a final fallback verdict.

These checks do not prove Arkham Knight gameplay works. Next: launch the game, first compare the stock profile, then ReShade and the full chain in a repeatable scene. Verify scene depth, Kernel compilation, NGX routing, repeated `frame N delivered`, neural dispatch, motion/UI, performance/VRAM, resolution recreation, alt-tab and clean shutdown. Preserve logs before changing another layer. Do not assume 4K is practical from the tiny helper test.

The F9 build subsequently passed four separate 300-frame helper runs at 100%, 75%, 67% and 50% model dimensions, with the model sizes confirmed in composition logs. All 946 original exports are retained. Actual F9 input and live cycling still require an in-game check.

## Rollback

Private staging contains `Restore-Stock.ps1`, `payload-manifest.json`, `installation-state.json`, and the `stock-before-install-20260913-124918` snapshot. The snapshot preserves original binary/configuration files, Steam state, cloud saves, and NVIDIA profile database copies. The latter are evidence, not instructions to overwrite global driver state.

`Restore-Before-F9.ps1` and the separate `before-f9-20260913-132152` snapshot restore only the earlier OptiScaler DLL/INI. The staged payload and full-stack ownership manifest now identify the custom F9 build; both restore paths passed dry runs.

Close the game, Steam and mod helpers, then run the guarded restore script. It moves only the 35 owned files and known generated mod logs/configuration into a dated disabled-profile archive; it refuses changed binaries that might belong to a later mod. Stock files, saves and game settings stay in place. The staged payload remains available for reinstall. The current baseline had not yet been launch-tested, so it is described as stock, not as a proven working gameplay baseline.

Sources: [Feeder's exact OptiScaler route](https://github.com/jlrouzies-fr/DLSS5-Feeder#alternative-optiscaler-dlss-nr), [Feeder release](https://github.com/jlrouzies-fr/DLSS5-Feeder/releases/tag/v1.16.0-beta.1), [OptiScaler release](https://github.com/Dagherbou/OptiScaler_DLSSNR/releases/tag/v0.2.0-dlssnr), [LumeniteFX](https://github.com/umar-afzaal/LumeniteFX), [ReShade](https://reshade.me/).
