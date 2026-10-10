# Azeron / AHK / Multi Image Canvas — workstream entry

**Newest source candidate:** [Overlay Studio 3.0.0-preview.1 — feature coverage, delivery, validation and next checks](OVERLAY-STUDIO-3-PREVIEW-2026-10-10.md).

**Earlier history and original files:** [Azeron overlays archive and source locators](../AZERON-OVERLAYS.md).

This pointer makes the same workstream discoverable from `docs/` alongside `AZERON-GAME-CONTROLS.md` and `INPUT-DEVICE-REGISTRY.md`. It is navigation, not another editable master.

Key constraints: Azeron Software V2 plus AutoHotkey v2 **without reWASD**; hold-to-show/release-to-hide plus optional Toggle/Timed; multiple images and context; a visible GUI and diagnostics. Historical MIC failures initially occurred with an ordinary keyboard, not Azeron or AHK.

The v3 preview adds quick opacity/relative sizing, inherited variants, shared managed files/profile metadata, richer key HUD/history, experimental context/raw input, a nested wheel, user-image live markers and component inspector IDs. Its exact code is preserved in the linked source package. A real language-server static check returned zero diagnostics, but **native AHK/Windows/game/device execution is not verified**. Native Azeron layer telemetry remains unimplemented.

Earlier artifacts `LayerPictures.ahk`, `Azeron_Hold_MultiImageCanvas.ahk` and Studio 2.0.0-beta remain in the archive. Do not run them all together or treat the old package as v3. Existing development task: PR #2, with expanded OVL-01–OVL-07 checks; no new task queue or background automation. General software UX preferences are a linked pending source capture, not an activated global policy.
