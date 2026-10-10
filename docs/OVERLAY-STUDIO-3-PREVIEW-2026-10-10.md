# Overlay Studio 3 — preview, coverage and next verification

Version **3.0.0-preview.1**, 2026-10-10. Current owner remains this game-controls project; do not redirect to Master Forge or the architecture project. Existing workstream: PR #2. [Earlier archive](../AZERON-OVERLAYS.md).

## Delivered artifact and exact source

[Source package and Hebrew guide](https://drive.google.com/file/d/1COZhma8Ur8iFWc1bkuAqOd4lwIudLY5z/view?usp=drivesdk).

The package contains the ready-to-run AHK source, launchers, Hebrew guide, modular editable sources, exact legacy v2 dependency, isolated native self-tests, feature-status JSON and validation evidence. It contains no personal pictures/profiles, new input driver, interpreter binary or font. Use a direct chat attachment if the private Drive account is unavailable; no public permission widening is authorized.

Generated `AzeronOverlayStudio.ahk`: **195,947 bytes**, SHA-256 `2562d2669b2fda0f78022e4c5e042aaea9b5de3cc2fa13695971cece63412a07`.

Original legacy v2 dependency remains byte-identical, SHA-256 `a9d943f2f950ab8702bc2493109ce8b9ee9ebb16ebbd6e2a59e2c406a3a844a7`. v3 uses a separate settings directory; explicit legacy import appends disabled definitions rather than replacing old settings.

**Publication boundary:** this commit records the delivery and continuation. The new exact code files are preserved in the source ZIP; they have NOT been represented as already committed to a Git code branch/main. Import those exact bytes into the existing code workstream using a verified byte-safe route, preserving newer native-profile research. The Drive package is a delivery/checkpoint, not a second editable code master. PR #2 is not merged by this documentation update.

## Requested functionality implemented in source

| Area | Implemented | Qualification |
|---|---|---|
| Picture buttons | Quick opacity presets/slider, numeric input, pixels and screen-width/screen-height/original-image percentages, Hold/Toggle/Timed, preview, live appearance edits, monitor/anchor/offset | Native Windows behavior unverified; one image at a time; dark canvas/window-wide alpha. |
| Variants | Parent/child tree, collapsed variants, per-field Own overrides, inherited changes and shared assets | Trigger/enabled/name/ID are independent; ambiguous shared triggers fail closed unless explicitly preferred. |
| Library | Managed copied files with SHA-256 dedup, shared image/profile references, usage list, search/filter, manual/dynamic sorting, relink, unused-file guard | Profile files are data-only; transient view filters/sort choices not all persisted; managed copies recommended. |
| Metadata | Device/game/exe/keymap/profile/layer/layer-key notes; profile then image fallback for empty following metadata; explicit pins | Labels are distinct from active routing. ViewGroup is visibly convenience-only and does not change behavior. |
| One help key | Foreground executable and declared layer/device routing, deterministic scoring, Unknown and ambiguous states | Native Azeron telemetry is NOT implemented; experimental Raw Input must be tested on actual hardware/output path. |
| Key display | Presets, live edits, 1–50 recent entries subject to screen fit, independent age-size/opacity, groups/include/exclude/per-key rules, Unicode symbols/colors, modifier chords | Symbols are text, not file icons. Event times are not measured hardware-to-game latency. |
| History | Freeze, recent memory history up to 200, clock/hold/gap/overlap, explicit bounded recording and separate CSV export | HUD/recording off at startup. Record limit default60 seconds, up to10,000 transitions; no automatic file keylog. |
| Radial menu | Nested native button ring, pages, 1–8/Backspace/Escape, images/single shortcut/overlay controls, no-send preview and target-focus check | Not a full reWASD input/gesture clone. Hold pictures selected from the wheel display for a timed duration. |
| Live map | User-supplied actual device picture, editable output-key markers and live highlighting | No invented official geometry, profile decoder or hidden native-layer state. |
| Inspector | Discreet dots on the main UI, stable component/object/version code and copy | Secondary dialogs are not fully instrumented; codes omit private paths/serials. |

All entries above mean **implemented source**, not completed runtime acceptance. `docs/FEATURE_STATUS.json` enumerates implemented, experimental, interface-only, partial and not-implemented parts.

## Source-observation limits

Windows Raw Input can distinguish input sources, but software remapping may expose a virtual/different/no source. Connected does not mean pressed; a device label or profile export does not reveal an active layer. This build includes an optional observation-only keyboard backend, not a filtering driver or native gamepad/analog API. Device disconnect during a hold needs runtime hardening.

Layer authority is explicit: Unknown initially; operator-selected overlay tags or emitted keyboard signals without a state file; an optional fresh local adapter INI is sole authority once selected. Stale/invalid data becomes Unknown. A producer for Azeron is NOT supplied. State-file support is a consumer contract, not successful native integration. Keymap picture selection and physical layer switching are separate operations.

MIC remains a compatibility bridge based on keyboard shortcuts and assumed toggle parity. Do not hide a native MIC failure under that bridge. The historical MIC failures were initially from an ordinary keyboard alone, not Azeron or AHK. The Local picture path does not depend on MIC.

## Real validation evidence

- Exact legacy source retained, generated build reproduced byte-for-byte, manifest/file hashes and ZIP CRC checked.
- **Real static language-server run**: thqby vscode-autohotkey2-lsp3.0.10, publisher VSIX checksum verified, Node24.21.0 on authorized Mac, isolated temporary directory. Final report for the source SHA above received **zero diagnostics** after a controlled invalid-expression probe was removed. Earlier diagnostics were corrected; a missing notification was not called success.
- **Not executed:** native AutoHotkey interpreter/self-tests, Windows GUI, game, Azeron, MIC runtime, profile import, device-native layer adapter. No screenshot/video capture or performance/VRAM measurement.

Use `Run_Tests.cmd` on Windows for the authored isolated tests. They may open temporary windows but start no real keyboard listener and send no game keys. Only an actual report establishes native test success. Follow with manual hold/release, overlapping triggers, timing, variants/files, context, privacy, radial and borderless-game checks.

## First user action and continuation

Extract, ensure AutoHotkey **v2**, run `Start_Studio.cmd`, import one local image, choose a real ordinary-keyboard key via Record key, enable, select Hold/Toggle/Timed, SAVE PICTURE and TEST. Then move focus outside the settings UI and test the real trigger. `TEST` previews for2–10 seconds; it does not prove real DOWN/UP routing. Keep only one overlay-family script running; do not terminate unrelated AHK automation.

Next acceptance remains OVL-01–OVL-07 in the existing workstream, expanded in `VALIDATION.md`. No new task queue, scheduled check, background wake-up or device listener outside the user-launched app was created. The app defaults do not modify Azeron firmware/profiles or install reWASD.

## User-wide preference capture

The user explicitly requested reusable design consideration, but also explicitly requested a **not-fully-integrated** label. The canonical source note is [Global software UX review candidate](https://github.com/dodWhatUp/global-chat-instructions/blob/main/audit/SOFTWARE_UX_REVIEW_OVERLAY_2026-10-10.md), event `pref-event-20261010-overlay-software-ux-review`.

It covers quick/precise relative controls, variants, managed shared assets, metadata versus view-only organization, truthful context, useful event visualization, explicit recording, compact nested menus, stable inspector IDs and holistic simplicity/privacy/testing. Apply as current app requirements; future software should consider relevance, not implement the whole list by default. Source capture is saved; exact inbox integration, active-matrix reconciliation and consumer adoption remain pending. Do not claim account-wide activation.

Assistant additions in this implementation: fail-closed ambiguous matching, recording bounds/off defaults, integrity-checked copies, referenced-file deletion protection, previous settings backup, disabled legacy import, no-send radial preview and sanitized diagnostics.

## Environment and write boundary

Authoring: ChatGPT/Linux plus read-only static parser execution on the authorized Mac. One registry-managed clean owner clone was created after bounded discovery found none. A credential-inspection command was blocked; it was not retried. A separate strict SSH identity check failed host verification, and no host-key override was made. No local Git source push or credential extraction followed. Native connector identity `dodWhatUp` was verified for these additive documentation writes. The source ZIP preserves exact bytes rather than recreating them through model text.

Main source base before this receipt: `2bdd112a78527f64e861f3bc2dd43bec36355518`. The later native-v2 research paths were preserved and not adopted/modified here. Global review base: `0150b1c42455a4167ec1095fbfb26a3731bbcf45`; its new candidate source note changes no active pins/rules. This receipt is not whole-project sync, code adoption or Windows success.
