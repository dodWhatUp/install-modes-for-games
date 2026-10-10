# Native v2 field observations from the supplied example set

Scope: Azeron Software 2.0.2 backup + 27 annotated screenshots, 2026-10-10.
These are observed serialization/UI correspondences, not a runtime implementation
specification. Feature examples are not adopted gaming preferences.

## Containers and geometry

The full backup is a ZIP with `backup-data.json` and per-device profile files.
`backup-data.json.stores` contains JSON-encoded store strings. The current
software profile index and tag definitions reside in the software-profile store.
The full backup is not assumed to be the normal single-profile import format.

Per-profile metadata identifies `schemeName: azeron-profile-v1`, `device: 8`,
`version: 1`, plus 43 native input records. The visible model-8 mapper resolves
30 digital positions and joystick input 24. This output includes checked native
button IDs, not invented physical position numbers.

New individual JSON files use that per-profile object shape. Acceptance by the
normal import handler is unverified. The augmented full backup preserves the
observed outer ZIP/store shape without claiming a tested restore.

## Layering

- `types[0] == "24"` corresponds to SINGLE / Layering.
- `layeringProfileId` stores the target profile ID.
- `isToggleOnHold == true` corresponds to Toggle on hold.
- `isBelkin == true` corresponds to Switch held binds on layer change in the
  annotated held-bind example; the actual working base and R5 candidate use false.
- "Set target button to switch back to this profile" is represented by a
  reciprocal target-button link. It is not a distinct boolean on the source
  binding: the two source examples differ in the target's same-button binding.
- A single mapping with Toggle on hold is different from selecting the LONG
  activator. Old long-press/tap splitting is not inferred from dormant delays.

## Other demonstrated fields

| Demonstration | Observed fields |
|---|---|
| Keyboard | type 1; keyValues and metaValues |
| Disabled binding | type 11 |
| Timed key hold | isHold true, holdTime 600 in the example |
| Key latch / second-press release | isHold true, holdTime 0 in the example |
| Turbo | isTurbo true, turboInterval 20 in the example |
| Single A / Long B / Double C | three type slots are 1; the corresponding keyValues arrays carry KeyA/KeyB/KeyC |
| Input sequence | type 37; sequenceTriggerSettings; isPingPongLoop distinguishes the annotated examples |
| Macro | type 16; macro repeat and steps |
| DirectInput button | type 5 |
| DirectInput D-pad | type 12 |
| Mouse button | type 15 |
| XInput D-pad | type 22 |
| Media control | type 38 |
| Mouse wheel | type 35 |
| Thumbstick toggle examples | types 13 and 14; precise runtime timing not tested |
| Next / previous / first profile examples | type 41; example keyValues 0, 1 and 2 respectively |

`isHold` is not used as a substitute for momentary layering.
The working base also contains older numeric key strings. Current examples and
other schema-only records contain DOM-style strings such as KeyA, Digit1,
ControlLeft and ShiftLeft. R5 uses current string codes for mapped digital
keys; it preserves the joystick object intact rather than normalizing its mixed
legacy/modern fields.

## Current preference evidence

Only profiles tagged `layered 1` and `FOR CHAT` were attributed to the user.
Other existing presets may demonstrate a field encoding, but are not evidence
of desired button positions, actions or gestures.

The current BASIC buttons 1, 2 and 36 are dedicated SINGLE momentary layer
selectors. An annotated image additionally calls this pattern "most of the time
my preference". This current evidence supersedes the old V/150ms implementation
for this candidate only. The old configuration remains historical evidence.

## Not inferred

No import-handler ID policy, HID delivery timing, held-key reference counting,
key-up ownership, platform-specific support, on-board persistence or gameplay
verification is inferred from these JSON fields alone. Labels may describe
intent; they are not proof of effective game actions.
