# Verification and remaining Windows checks

Date: 10 October 2026. Helper version: 1.0.

## Completed

- The helper was authored as an AutoHotkey v2 source utility. An independent static review found no blocking defect in the callbacks, slot indices, validation, INI replacement, enable/disable handling, or overlay construction.
- Code review checked that a new picture invalidates an older timeout, an older key release cannot hide a newer picture, repeated keydown does not repeatedly toggle, and empty slots do not consume keys.
- GUI construction uses a borderless topmost window, no-activate style, no-activate Show, and whole-window opacity with click-through. These are implementation properties, not observed gameplay results.
- Settings pause all helper bindings; tray disable hides the picture and unregisters its hotkeys. The script has no typing log, network-request, game-remapping, installation, elevation, or startup-registration code.
- The guide was checked against the exact Keyviz 2.1.1 release source, original Carnac 2.3.13 source, current Azeron V2 manual, reWASD documentation, and Multi Image Canvas v1.0.8 source. Corrections include Keyviz's duration versus animation-speed distinction, its color-picker opacity control, its F13–F24 limitation, and Multi Image Canvas's inability to reveal a hidden overlay through a canvas-switch key.

## Not executed in this environment

The authoring environment is a Linux ChatGPT workspace. Windows, AutoHotkey, Wine, PowerShell and .NET execution were unavailable. No application was installed on the user's PC, no Azeron profile was changed, and no Windows/gameplay or visual capture test was performed. Static review does not establish runtime success.

## Specific limits

- Four single-key triggers; primary monitor; five fixed positions; one picture at a time.
- Whole-window opacity, with a dark canvas. Transparent PNG pixels may show that canvas. GIFs use a still frame.
- Exclusive-fullscreen compatibility is not supplied. Start with Borderless / Windowed Fullscreen.
- Enabling bindings while a trigger remains held can interpret its next key-repeat as a new press. Release the trigger before closing Settings or re-enabling overlays.
- A generic key listener cannot detect a native Azeron layer switch with no keyboard output. The dedicated help-button route works from explicit keys; the optional reWASD route must be configured and tested separately.
- Keyviz 2.1.1-beta has a possible post-hold timing quirk inferred from its source: the first key in a group skips the release-timestamp update. This was not reproduced on the user's machine. Test long-hold/release if a full post-release delay matters.

## Next action

On Windows, extract the package, install AutoHotkey v2, launch `LayerPictures.ahk`, choose two pictures, save, and use the tray previews. Then follow the short desktop and borderless-game checks in the guide. Install Keyviz from its official release and apply the proposed settings. These are the remaining runtime checks, not additional research requirements.

## Scope and continuity

Canonical project: `dodWhatUp/install-modes-for-games`. Initially inspected base: `c89119e6fb87acd485f78120fd772b08c2656a55`. Before saving, main advanced to `8afe64c96b6fba7dff030ed0ab23cebf06b81392`. The path-only comparison identified the new Azeron Step 1 research and an added controls-guide link. The current controls guide and research README were reread; their four conceptual layers remain a proposal, with no conflicting native key assignments. This package preserves that update and starts from the newer base. Global guidance observed at `0150b1c42455a4167ec1095fbfb26a3731bbcf45`. The owner tree was checked for a manifest, accepted instruction pins, routing files and pending corrections; none were present. Relevant controls and device-registry records were read. No instruction source was installed, repinned or modified.

The historical button-6 / tap-V / 150-ms-hold preference remains a historical baseline; no V2 hardware verification or adoption is claimed. The separate Master Forge device project was not changed.

Git holds the editable source. `Setup.html` is a derived readable view of `README.md`; the ZIP and Drive copy are delivery snapshots. Publication of a draft branch is separate from merging, installing, changing settings or completing the Windows test.
