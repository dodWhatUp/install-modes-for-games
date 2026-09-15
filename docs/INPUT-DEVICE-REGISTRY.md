# Device identification and physical control maps

User preference confirmed 2026-09-15. This extends [the all-game control workflow](AZERON-GAME-CONTROLS.md) to reWASD, Azeron and other supported keyboards/keypads. The goal is to identify a device once, preserve the user's preset and reuse an accurate physical map on later requested tasks. This document defines the process; it is not evidence that a new device has already been enrolled.

## What to save

Use [the device template](../templates/INPUT-DEVICE.example.json). Maintain one registry record per physical device and separate versioned geometry/baseline records when needed. Use a stable user-facing alias independent of its current USB port. Each game record references that alias and the verified revisions.

- **Identity:** manufacturer/model, connection mode, vendor/product IDs, relevant interfaces and HID usages, software/firmware versions, plus a private local identity record where available. Keep unique serials, raw Windows device paths, container identifiers and mapper-specific machine identifiers out of public Git. Store them locally and in the connected Drive; publish only an opaque alias and sanitized device capabilities. Do not publish hashes of unique hardware identifiers as a substitute for privacy.
- **Physical geometry:** handedness, orientation, editable diagram source, button/axis positions and stable position IDs. Device-specific numbers and labels are separate fields. An ID such as `index-upper` is an example, not a verified location on this user's device.
- **Baseline:** the user's existing onboard/firmware and remapper setup, native importable exports, versions, hashes, active mode, stick calibration, date and known-good verification. Preserve both the current state and a different known-good state. Record which physical control emits which code before further remapping.
- **Logical layout:** shared base version, correspondence between physical position and logical role, layers, gesture timing and backend-specific adaptation. Keep changes to a device adaptation distinct from changes to the shared logical base.
- **Verification:** observed source device, press and release, output, layer/gesture, confidence, date and unresolved positions. Mark a complete map only after its controls have been identified; geometry alone is insufficient.

Use `devices/<alias>/DEVICE.json` and `devices/<alias>/HISTORY.md` for useful sanitized records in this repository when enrollment occurs. Keep private recognition data and native backups in Drive and a local companion directory outside the repository. Record retrievable references in the private archive index. Empty templates are not enrolled devices.

## First connection or a changed preset

1. When the user identifies a newly connected keypad, inspect the current device inventory and mapper's detection state. Confirm which entry belongs to that physical device. Prefer stable available identifiers together with its interface/capability signature. VID/PID or a product name alone may describe several identical units; a port change alone does not mean a new keypad. Do not assign the saved mapping to an ambiguous device.
2. Check whether the installed reWASD version supports the device natively or exposes it as a keyboard, mouse, controller or composite device. Identify all relevant interfaces and initialize/group only those that belong together. reWASD's [Device detection mode](https://help.rewasd.com/interface/device-detection.html) can correlate a deliberate physical button press with the detected device. Do not clear all existing device data as a routine enrollment step.
3. Export the user's preset before any changes. If the user configured it first, treat that as the starting baseline and compare its actual output with its labels. Record which outputs are firmware/onboard and which depend on software running. A remapper's saved label is not proof of a physical location or observed output.
4. Establish the shape from an existing verified diagram, device documentation or a user-provided photo when needed. Ask for a physical action only when observation cannot establish the mapping: identify one position, press/release it once and record the corresponding device/input. Include thumbstick directions, axes, click, switches and extra buttons. Do not infer unseen positions from a visually similar model. Complete missing controls in small groups and maintain a visible pending list.
5. Check whether distinct physical buttons produce distinct remapper-visible inputs. If two positions emit the same indistinguishable code on the same interface, software cannot reliably give them different actions from that input alone. Explain the need for distinguishable baseline outputs where the device supports them, preserve the original and agree any necessary reassignment before applying it. Likewise, a digital direction pad cannot supply true analog travel merely because the diagram shows a stick.
6. Adapt the shared logical base to the verified positions. Keep separate native Azeron/reWASD/other-tool exports; do not treat their file formats as interchangeable. Preserve the chosen normal-tap/long-hold/release-return behavior on the corresponding physical position where supported. Record any missing buttons, axis differences, rollover limits or unsupported gestures as explicit exceptions.
7. Validate source and final output without modifying unrelated devices: quick taps, held releases, layer transitions with another key held, modifiers, axes/deadzones and relevant combinations. Use a bounded intentional input check; do not collect unrelated typing or leave a recorder running. Reopen/reapply as appropriate, verify persistence and export the verified result. A device disconnect makes affected observations inconclusive.
8. Save the registry, baseline, native adaptation, editable geometry, verification and rollback in Drive, with sanitized records in Git. Link each game mapping and its three diagrams to the exact revisions. Keep earlier versions available for recovery and suggestions.

## Later requested game/control tasks

Read the saved registry and compare it with currently connected devices before selecting a map. For one unambiguous match with a compatible baseline, reuse the alias, physical positions and shared layout without asking the user to name it again. Check the active mapper/device/group and output mode; the same keypad in a different firmware mode can expose different inputs.

Ask a focused identification question only when a device is unknown, several candidates match, recognition data is unavailable or observed mappings conflict. Revalidate affected controls after firmware, factory reset, preset changes, changed interface modes or mapper updates. Preserve newer user changes. A missing device cannot be verified by a stale remembered entry.

The agent performs these checks during an active authorized task. It does not automatically wake whenever a USB device is connected. Native reWASD [Autodetect](https://help.rewasd.com/basic-functions/autodetect.html) can select saved configurations by focused application when configured and its Background agent is enabled; that is separate from the agent recognizing hardware. Record and test both device selection and application selection instead of assuming either proves the other.

## Clear user handoffs

Whenever a physical action or inaccessible setting is required, give one short instruction stating **the exact action, why, expected indication, and what to report**. For example: identify the topmost index-finger button, press and release it once while detection is active, then report if no device highlights. Do not ask the user to provide information already available in a saved record or a reliable read-only inspection.

Typical handoffs are connecting the new device, identifying an uncertain physical control, providing its shape when no reliable reference exists, completing an account/license/restart step, and testing gameplay actions or prompts that cannot be established from configuration files. Obtain a photo as a normal attachment request, not through a text-only question tool. Continue independent research, backups and documentation while waiting. State exactly what remains pending and do not call a configuration-only check a completed gameplay test.

## Mapping and image data

The device record connects physical positions to baseline outputs. The [per-game record](../templates/GAME-KEYBINDS.example.json) connects those positions through the active mapper to game-facing keys, actions, mod overrides and prompts. Keep a single authoritative mapping per revision and generate all three companion pictures from it: keys, actions, and combined. Use the actual device shape even if the mapper shows a generic keyboard.

For a second device with the same geometry, reuse the editable layout only after verifying position correspondence. For a different shape, create a separate geometry with the same logical roles where practical. Preserve numbered references, layer/context, tap/hold labels, version and unknown-state markers. Never fill in a key or action merely to complete a picture.
