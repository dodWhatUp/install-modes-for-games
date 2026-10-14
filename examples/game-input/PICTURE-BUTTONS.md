# Picture Buttons integration in the existing Studio host

## Multi Image Canvas editor continuation — 2026-10-12

Studio **2.2.0-unified.10 / Hub 0.20.2** adds Modern/Classic presentation to
the MIC connection page, sharing the existing native host and original actions.
Shortcut setup and visibility guidance are grouped; saved/unsaved shortcut
status stays visible. **Show canvas / Hold setup guide** reveals all original
instructions. **Go to Picture buttons** navigates without saving or toggling.
The layout reflows at narrow widths without resetting Picture drafts/columns
or changing overlays. This does not redesign the external MIC canvas program.

The active keyboard layout can localize a native Hotkey's letter text. Reading
the owned widget's physical letter VK avoids an invalid shortcut on explicit
Save; comparison is modifier-order/case tolerant. No keyboard layout is changed.
219 inert native MIC fixtures passed; visible Modern/Classic radio selectors
expose the active layout without requiring a popup. The shared sizing helper preserves
dropdown popup height, including Picture Buttons' selectors (62 native checks).
External shortcut/Hold and game behavior remain untested/deferred. See the
[shared editor contract](../../docs/UNIFIED-UI-DESIGN.md#native-multi-image-canvas--2026-10-12-hub-0202).

## Native editor continuation — 2026-10-12

Studio **2.2.0-unified.7 / Hub 0.19.2** adds a Modern primary Picture Buttons
layout around the existing controls, actions and storage. Name/trigger/source/
mode and Preview/Save remain visible; optional placement fields use **Show display
settings**. Timed mode reveals its required duration even when detail is hidden.
Local/MIC source choices reveal the matching field, without emitting a shortcut.
**Layout → Classic** restores the original form using the same unsaved controls.
These native layout/disclosure choices are session-only and never rewrite an INI.

The native pane adapts to width and the Hub provides scrolling below the readable
minimum. Table columns remain naturally draggable; resizing retains their widths,
while **Fit columns** is an explicit presentation action. An unsaved-status line
and selection-discard confirmation prevent silently losing a draft. Floating UI
identification follows the actual positions and hides with collapsed controls.
Advanced appearances/library/context, MIC, HUD, status, Game Input and all runtime
overlays retain their existing implementations; this slice does not claim their
separate forms have been fully redesigned. Physical/game/DPI acceptance remains
separate from desktop fixture tests. No capture or benchmark is started.

Final local acceptance: 54 native primary-editor fixture checks and the existing
73 model/73 feedback checks passed. Actual installed startup loaded the four
saved slots without input events; normal shutdown and persistent settings/profile
hashes were verified. The last production screenshot/click pass was incomplete
because the control provider could not capture the monitor or obtain coordinate
geometry. Fixture success is not claimed as complete production visual or game
acceptance. See the [dated receipt](../../docs/GAME-TOOL-CONNECTIONS.md#2026-10-12--native-picture-buttons-redesign-installed).

The Picture Buttons module extends the existing Studio 2 app; it does not install or launch the separate Studio 3 preview. Existing MIC, keyboard display, tray controls and optional Game Input remain owned by the host. Game Input still starts Off.

## Entry points and preview

The original Picture buttons tab remains available. **PREVIEW CURRENT EDITS** reads the current local-picture fields without saving, rebinding keys or sending MIC shortcuts. **Advanced pictures / Library** opens the advanced editor in the same AHK process. Explicit Save is separate from Preview.

Advanced appearance settings belong in a separate versioned sidecar, not a replacement native device profile or a rewrite of the original Studio settings. Initial loading and preview must not write either configuration. Existing enabled/disabled states, shortcut outputs, MIC settings and HUD settings are preserved.

## Source and scope

The source adaptation is based on the author's exact Studio 3 preview source package, generated AHK SHA-256 `2562d2669b2fda0f78022e4c5e042aaea9b5de3cc2fa13695971cece63412a07`. Pure model helpers are adapted into a host-owned module; the Studio 3 entry point and its unrelated listeners are not executed.

Picture scope covers quick and precise opacity controls, relative sizing, monitor/anchor/offset placement, detached preview, appearance variants, a shared managed/linked file library and display metadata. Profile attachments are data only. View-only grouping is organization, not routing or remapping. A declared device/layer is not evidence of actual hardware or an Azeron internal layer.

The original twelve-slot trigger system remains the input owner. Appearance variants do not change trigger keys, enabled states, pass-through or native mappings. Game tests, benchmarks, advanced HUD/radial/live-map work and native layer telemetry are outside this integration task.

## Acceptance and recovery

Native fixture checks and observed desktop UI results must be recorded separately. A pure geometry or inheritance test is not live preview, physical key or gameplay acceptance. Do not run the main host's `#SingleInstance Force` diagnostic filename while that same host is running.

Before installation, preserve current installed source and Studio settings plus the prior known-good checkpoint. Stop the app normally before deployment, verify installed source equals the reviewed repository source, then reopen the same entry point. Do not restore the entire device/profile collection to undo this optional module.

This initial integration note is a build-stage description; completed checks and remaining limitations will be appended after validation.
