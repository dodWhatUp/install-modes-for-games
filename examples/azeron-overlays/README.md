# Azeron picture and keystroke overlays

Prepared 10 October 2026 for Azeron Cyborg II with Azeron Software V2 on Windows.

## Use these two tools

1. **LayerPictures.ahk**, included here, provides a chosen picture for each shortcut with explicitly defined Toggle, Hold, or Timed behavior. It requires **AutoHotkey v2**: <https://www.autohotkey.com/>.
2. **Keyviz 2.1.1-beta** displays the keys you press, with adjustable appearance, opacity and duration. Download it from the official release: <https://github.com/mulaRahul/keyviz/releases/tag/v2.1.1>.

These are ordinary desktop overlays. Start with **Borderless / Windowed Fullscreen** in the game. Visibility over an exclusive-fullscreen game is not established. Nothing in this package installs software, changes an Azeron profile, or modifies a game automatically.

The helper is a newly authored source utility, not an Azeron product or a compiled installer. Its review and remaining Windows checks are recorded in `VALIDATION.md`. Keyviz and the alternative apps below were researched from primary documentation/source, not executed on your PC.

## 1. Set up the picture helper

1. Extract the package to a folder you can write to. Install AutoHotkey **v2**, then double-click `LayerPictures.ahk`.
2. Open **Settings** from the helper's tray icon. Choose an image for each slot with **Browse**. A blank image slot is unused. PNG or JPG is a practical starting format.
3. Choose the trigger key, display mode, size, opacity, position and duration, then click **Save and close**.
4. From the tray, use **Preview saved slot 1** (or 2–4) to check the saved picture for two seconds without generating F14 from a physical keyboard. Assign the matching output to an Azeron button as described below.
5. Use the tray menu to hide the picture, disable the helper, reopen Settings, or exit.

Suggested starting configuration, subject to your currently assigned keys. The supplied defaults have empty picture paths and all four slots set to Toggle; select the modes below if you want this arrangement:

| Slot | Trigger | Picture you choose | Mode | Opacity | Width | Position | Time |
|---|---|---|---|---|---|---|---|
| 1 | F14 | Base-layer reference | Toggle | 75% | 800 px | TopRight | 2 s, used only in Timed mode |
| 2 | F15 | Second-layer reference | Hold | 75% | 800 px | TopRight | 2 s, used only in Timed mode |
| 3 | F16 | Third-layer reference | Hold | 75% | 800 px | TopRight | 2 s, used only in Timed mode |
| 4 | F17 | Extra reference | Timed | 75% | 800 px | TopRight | 2 s |

F14 is explicitly shown in Azeron's V2 manual. F15–F17 here are helper defaults: select them in Azeron's Special Keys list if your installed build exposes them, or choose other unused single keys in both apps. The helper accepts single keyboard-key names, not a shortcut chord such as Ctrl+Alt+K. Avoid repurposing the existing layer button or a game/graphics shortcut.

### What the modes mean

- **Toggle:** One press shows that picture; the next press of the same key hides it.
- **Hold:** The picture appears while its trigger is held and hides when it is released.
- **Timed:** Each fresh press shows the picture for the chosen number of seconds.

Only one picture is shown at a time. A newer picture replaces the previous one. Releasing the previous trigger must not hide the new picture. Releasing a newer Hold trigger does not restore an older picture automatically; press the desired trigger again.

Opacity is the amount you can see: **75% opacity means 25% transparent**. Start near 75%, then adjust in the game. Width controls scaling; the picture keeps its aspect ratio. The helper targets the primary monitor and offers five fixed placements, rather than arbitrary dragging or multi-monitor routing. It fades the whole rectangular picture. Transparent PNG regions may show its dark canvas; per-pixel transparency is not promised. GIFs are displayed as a static frame.

Keep **Let the trigger key also continue to the game / active app** off for a dedicated help key. Turn it on only if the same emitted key deliberately also performs an action in the game. The overlay is click-through and is designed to leave the game focused. It observes its registered triggers; it does not record your typing or send data over the network. Bindings are paused while Settings is open; uncheck the tray's **Overlays enabled** to disable both the overlay and its hotkeys.

Settings are kept in `LayerPictures.ini` beside the script. The image paths in that file refer to your own files: if you move an image, choose it again. Keep your images and INI private when sharing this source package.

## 2. Set up Keyviz

Install the Windows release, open its tray icon, then **Settings**. These labels were verified against release v2.1.1, commit `8225e4157ed170a56d37366be24573f614b9ce06`.

| Setting | Starting value | Purpose |
|---|---|---|
| General → Filter | Off | Shows ordinary game keys, not just modifier combinations |
| General → History | Off | Compact display; turn it on with Max Count 3 for a short history |
| General → Toggle Shortcut | Record Ctrl+Alt+K if unused | Enables/disables the visualization; default is Left Shift+F10 |
| Keycap → Preset | Laptop | Simple readable key boxes |
| Keycap → Text → Size | Adjust to your display | Controls label size |
| Keycap → Text → Text Color | White, 100% opacity | Keeps letters readable |
| Keycap → Color → Normal | Dark, 65–75% opacity | Semi-transparent key background |
| Keycap → Color → Highlight Modifier | On, if wanted | Reveals the separate modifier-color control |
| Keycap → Color → Modifier | Optional distinct color | Makes Shift/Ctrl/Alt easier to distinguish |
| Appearance → Alignment / Margin | A free corner, small margin | Positions the display away from HUD elements |
| Appearance → Display | Your game monitor, if shown | Selects the output display |
| Appearance → Duration | 1.6 seconds | Sets how long released keys remain visible |
| Appearance → Animation | Fade | A restrained entry/exit style |
| Appearance → Animation Speed | About 0.2 | Controls transition speed, separately from Duration |
| Mouse → Cursor Highlight → Show Clicks | Off, if distracting | Removes the ring around mouse clicks |
| Mouse → Button Indicator → Show Indicator | Off, if distracting | Removes mouse-button icons near the cursor |

The **checkerboard alpha slider / percentage field inside each color picker** sets opacity. It is not a separate global Transparency setting. The free features cover this request; Pro is not required.

**Close Settings before judging disappearance time.** The release source intentionally keeps the preview from expiring while Settings is open. A key that remains held also stays visible: Duration concerns the lingering display after input, not forcibly hiding a key you are still holding. One beta timing detail needs a Windows check: the first key in a group may not refresh its timestamp on release (`if (kIndex && kIndex >= 0)` skips index 0). It may therefore disappear immediately after a long hold. This is a code-level inference, not an observed failure on your PC; test a long-held W before relying on an exact post-release delay.

Use a normal keyboard combination for the Keyviz toggle. **Do not rely on F13–F24 for Keyviz 2.1.1**: those names are commented out in its supported key definitions. This is separate from the picture helper, which can use those keys.

Keyviz shows Windows keyboard output such as W, Shift or Space. It does not identify an Azeron physical button number, an internal layer change, a game's action name, or native analog-stick motion. Two buttons sending the same key look the same. Disable the visualization while typing anything you do not want visible on screen.

## 3. Connect the controls in Azeron Software V2

### A reliable dedicated picture-help button

1. Select your current **software profile** and a spare physical button.
2. Set its normal **Keyboard** binding. Open **Special Keys** and select **F14** for the base-picture slot.
3. In each additional layer/profile, use the same physical help-button position but assign the key for that layer's picture, such as F15 or F16 when available.
4. Keep Azeron running when using software layers. In the helper, match each trigger to its intended image.
5. For a Keyviz on/off button, set a separate Azeron Keyboard combination matching Keyviz's recorded **Ctrl+Alt+K** (or your chosen unused combination).

This gives a context-sensitive help button: after entering a layer, pressing that help button shows the corresponding image. It does **not** claim automatic image display from the layer-switch event itself.

### Native Azeron layers and the same-button limitation

V2 still implements layers through linked **software profiles**. Select the switching button, choose **Layering**, and choose the destination profile. **Toggle on hold** makes release return to the previous profile. The option configuring the destination's same button to return provides a second-press return instead. **Switch held binds on layer change** changes the outputs of other buttons that are already held; leave your existing choice until a deliberate test establishes the desired behavior.

Your recorded historical preference is to preserve a normal short tap and use a brief long hold for a momentary layer. The older record specifies button 6, tap V, 150 ms hold, and release-to-return. This package does not migrate or overwrite that record, and does not claim its exact V1.5.6 timing was revalidated in V2.

The current manual does **not establish** that one native Layering activation can also send F14. Separate Single Press and Long Press assignments are separate events, not proof of simultaneous output. Therefore a generic keyboard-overlay app cannot be told to detect a purely internal layer switch with no emitted keyboard event.

For Azeron's own current-map display, open the bottom-right **Quick Access Tools → Enable Gaming mode**. It gives a compact view of the active profile. The manual does not establish arbitrary user pictures, transparency, click-through or always-on-top game-overlay behavior for that view.

## 4. Automatic picture display when changing a layer: reWASD alternative

reWASD documents an additional keyboard mapping on a **Jump to Shift** button. This is the supported alternative if automatic picture display from the same layer-switch activation is essential. It is an optional mapping-owner change, not something installed or activated by this package.

For a momentary layer:

1. Select the intended button/activator and open **Shift mode**.
2. Choose **Jump to Shift**, the destination layer, and **Mode → Hold**.
3. In the mapping section inside that Shift-mode panel, also assign **F15**, for example.
4. In LayerPictures, set F15's image to **Hold**.
5. With a delayed jump, **Postpone the mapping** starts the key mapping together with layer activation.

To preserve a short-tap action, keep that action on Single Press and put the layer jump plus image trigger on **Long Press**. Use the existing 150 ms starting threshold only if deliberately reproducing the saved behavior; verify taps, holds and return on the actual device. Avoid stacking an Azeron software layer transition and a second reWASD transition on the same button accidentally.

A toggle layer and a held keyboard output are different states. For toggle layers, use a matching Toggle picture and understand that changing profiles by another route can desynchronize it. A momentary Hold signal is the simpler initial arrangement. **Postpone the mapping** synchronizes activation; key release and return still require the device test below.

reWASD also has **Preferences → Overlay** for its own Shift indicators/mapping display, with opacity/position/duration controls. That is a useful native status alternative, but arbitrary custom-image support is not established by that documentation. Use its ordinary windowed-overlay path for this proposal.

## 5. Ready-made alternatives

### Multi Image Canvas 1.0.8 — strongest ready-made picture option

Official downloads: <https://github.com/tokonoha00/Multi-image-canvas/releases>.

1. Extract the portable Windows x64 ZIP and run `MultiImageCanvas.exe`. Its runtime is included.
2. Create one canvas tab for each reference image, import the image and adjust its size.
3. Right-click a tab → **Set switch key...**. Single F14/F15 keys are accepted. English localization is present in this release.
4. Use the gear beside the overlay control to configure opacity and click-through. Start at 75% opacity.
5. Enable the overlay. Use the per-canvas keys to select the picture while keeping the game active.

| Default shortcut | Function |
|---|---|
| Ctrl+Alt+H | Show/hide the overlay |
| Ctrl+Alt+T | Toggle click-through |
| Ctrl+Alt+PageUp / PageDown | Increase/decrease opacity |
| A canvas's assigned switch key | Select that canvas |

**Important verified limitation:** A canvas-switch key does not reveal a hidden overlay; it changes the selected canvas while leaving it hidden. Press Ctrl+Alt+H to show it. Pressing the same canvas key is not a show/hide toggle. This is why the included helper exists. Hold-to-show and timed dismissal were not established for Multi Image Canvas. Exclusive fullscreen is explicitly unsupported.

The app has saved layouts and more image-arrangement controls than the helper. Use it if that matters more than direct one-key show/hold/timed behavior. Its portable build normally stores settings in `%APPDATA%\MultiImageCanvas`.

### Carnac 2.3.13 — simpler keystroke-display fallback

Official release: <https://github.com/Code52/carnac/releases/tag/2.3.13>.

Open the tray preferences. Under **Appearance**, set **Popup Opacity** to 0.7, **Popup Fade Delay (sec)** to 2, **Font Size** to 32, **Font Colour** to white and **Background Color** to black. Uncheck **Shortcuts Only** and **Only keys with Modifiers** to see ordinary game keys. Enable **Show Space as ␣** so Space has a visible label. Select the monitor/corner in **General**, then Save. **Ctrl+Alt+P** toggles silent mode.

This is the original Code52 release, last released in 2020. Its labels differ from the separate Carnac w/ Mouse fork. Prefer Keyviz first for a newer customizable display.

## 6. First Windows check and rollback

1. Start outside a game. Choose two clearly different pictures. Confirm Preview, each trigger, opacity and size.
2. Check Toggle twice; check Hold down/up; check Timed expiry; hold a key long enough to ensure repeat does not rapidly toggle it.
3. Show one picture, then another. Confirm an old timer or the old key's release cannot dismiss the new picture. Hide/disable and verify the tray still works.
4. Open a game in Borderless / Windowed Fullscreen. Confirm the picture leaves the game focused and mouse clicks reach the game. Check the overlay does not cover a critical HUD element.
5. In Keyviz, close Settings; press and release W, Space and Shift. Also hold W longer than Duration, then release. Confirm the labels, chosen duration and on/off shortcut, including the post-hold timing you want.
6. Only if using the reWASD route, verify that the layer and image both activate and both return on release, while a short tap retains its normal action.

If an application blocks the overlay or its input, keep that application's restrictions intact; compatibility is not universal. This package does not require game-process injection.

To stop the helper, use its tray **Exit**. Remove the new helper-key assignments or restore your pre-change Azeron export if you no longer want them. Exit Keyviz/Carnac/Multi Image Canvas through their tray or app controls. No autostart entry is created by the helper.

## Sources and evidence

- Azeron current Cyborg II manual, V2.0.0: <https://cdn.shopify.com/s/files/1/0930/2386/3123/files/Azeron_Cyborg_II_Manual_V2.0.0_1.pdf?v=1791194501>. Pages 18, 22–24, 29–31, 38–40 and 62. Current software page: <https://azeron.com/pages/software>.
- Keyviz product: <https://keyviz.org/>. Exact v2.1.1 settings source: <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src/components/settings/appearance.tsx>, <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src/components/settings/general.tsx>, <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src/components/settings/keycap.tsx>, <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src/components/ui/color-picker.tsx>.
- Keyviz supported keys and duration behavior: <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src/types/event.ts>, <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src/stores/key_event.ts>. Overlay properties: <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src-tauri/tauri.conf.json>, <https://github.com/mulaRahul/keyviz/blob/v2.1.1/src-tauri/src/app/window.rs>.
- Multi Image Canvas documentation/releases: <https://github.com/tokonoha00/Multi-image-canvas>, <https://github.com/tokonoha00/Multi-image-canvas/releases>. v1.0.8 `src/MainForm.cs` blob `dac773ab35b981bf3a4f0995c1f50e4a169633c0` establishes hidden/direct-switch behavior and F1–F24 shortcut acceptance. `src/Localization.cs` blob `2e45c21e3c64ff9b9f611c7544a5ca18c32ee1f1` establishes English labels.
- reWASD: <https://help.rewasd.com/basic-functions/shift-mode.html>, <https://help.rewasd.com/basic-functions/activators.html>, <https://help.rewasd.com/preferences/desktop-overlay.html>.
- Carnac: <https://github.com/Code52/carnac>, <https://github.com/Code52/carnac/blob/2.3.13/src/Carnac/UI/PreferencesView.xaml>.
- AutoHotkey v2 reference: <https://www.autohotkey.com/docs/v2/>. Windows overlay principles: <https://learn.microsoft.com/en-us/windows/win32/winmsg/extended-window-styles>, <https://learn.microsoft.com/en-us/windows/win32/winmsg/window-features#layered-windows>.

Repository home: `dodWhatUp/install-modes-for-games`, `examples/azeron-overlays/`. This is a setup proposal and source package; publication does not establish installed settings, a verified native Azeron configuration, or gameplay success. The Drive ZIP is a delivery snapshot of the Git-owned source.
