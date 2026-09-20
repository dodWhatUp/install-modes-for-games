# Master Forge left — control history

## 2026-09-20 — Shared gaming base in profile 2 / B

Requested a gaming layout using only the left Master Forge half, stored in the second profile. The user confirmed a direct USB data connection and explicitly selected a dedicated momentary pinky-out layer control with V on a separate direction. This is a device-specific exception to the earlier 150 ms tap/hold preference; the current manager does not expose that dual-role setting.

- Identified the left half through the official Serial API as `FORGE M4G S3`, firmware `3.0.0`; the separate right half reports `M4GR S3`, firmware `2.1.0`. No firmware was changed. Device Manager showed version `2.8.0`.
- Exported browser profiles A and B before editing. A contained an existing uncommitted draft: A1 physical ID 7 displayed `?`, whereas a direct device read returned action 301 (`-`). Preserved both the browser draft and actual device configuration privately. B matched the device and contained action 1023 in all positions before this task.
- Browser connections repeatedly disappeared and the browser import chooser did not complete. No requested mappings were applied through the browser. Used the vendor's documented Serial protocol, with the current manager's 921600 baud rate and Windows DTR/RTS enabled. Both ports answered identity queries. The initial 115200/default-handshake probe timed out; this does not prove a physical USB fault.
- Captured all three profiles' 4 × 90 mappings, all supported settings and the 500-entry chord library immediately before mutation. Saved a separate just-in-time snapshot and verified that the live state had not changed.
- Wrote 32 left directions in B1 and 32 in B2. Upper thumb supplies WASD; index south is Space, middle south Shift, ring south Ctrl. Pinky west is Numeric Layer (550) in both layers, and pinky south is V. This uses the vendor's momentary layer behavior. Layer warp remained off because movement is identical across layers and held gameplay actions should not be replaced by secondary actions.
- In B only, disabled Chording (setting 49), Autocorrect attempts (54), and Arpeggiates (81). Added one previously absent shared-library chord, E+O+U → Profile B (651), followed by No Key Pressed (256). Existing A keymaps/settings were preserved. B2 Aux 1 east returns to Profile A (650).
- Committed settings/layout once, closed the serial connection and read back all 1080 mapping positions, all supported settings, and the complete 501-entry library. The requested B layout/settings matched; A/C, B right-side mappings and B3/B4 were unchanged; all original 500 chords were preserved.
- Generated keys, suggested actions, and combined diagrams for both layers from one mapping record, plus a Hebrew connection/usage guide and a focus-only local key tester. Suggested game actions are not verified per-game bindings. No game was launched or modified.

### Verification boundary

Configuration and commit acknowledged; complete independent serial readback passed. Physical press/release, entry/exit chord behavior, held-key layer transitions, USB power-cycle persistence and gameplay remain pending until observed or reported. Device geometry is grounded in the official manager and manual; this is not a fully physically verified enrollment.

### Rollback

Select B in Device Manager, restore the private `profile-B-before.json` through Settings → Backup → Restore, and Apply. Delete only the added E+O+U chord from Library if reverting entry behavior as well. Backup import merges chord entries and does not necessarily remove additions. A/C and the right device do not need restoration. A private rollback script snapshots the current state, restores only the 64 changed positions and three settings, commits once, and removes the one added chord. Reconnect the device to return to its startup profile if necessary; power-cycle behavior has not been tested in this session.

### Resumable next boundary

Use the prepared local tester to check E+O+U entry, WASD press/release, Space/Shift/Ctrl, pinky-out hold and automatic return, holding movement across layer changes, and B2 Aux 1 east exit. Record physical observations separately from configuration verification. For a specific game, reconcile the game's effective bindings before relabeling actions or changing files. No background monitor or reminder was created.

### Sources

- [Official Master Forge guide](https://docs.charachorder.com/Master%20Forge.html)
- [Serial API](https://docs.charachorder.com/SerialAPI.html)
- [Device Manager](https://github.com/CharaChorder/DeviceManager), inspected source commit `33ce9b1ba725e44d0a878037ba397ad176e6a1d3`
- [Official M4G geometry](https://github.com/CharaChorder/DeviceManager/blob/master/src/lib/assets/layouts/m4g.layout.yml)
- [CCOS 3.0.0 metadata](https://charachorder.io/firmware/m4g_s3/3.0.0/meta.json), actions and settings linked by that metadata; reviewed 2026-09-20

## 2026-09-20 — Full keyboard and desktop expansion v2

- User requested full one-handed keyboard, pointer control, Windows shortcuts and layer/profile/macro instruction. Reused the known left-device identity and snapshot; A/B/C contents matched the prior verified state.
- Final: 256 C assignments (four layers, both logical banks), B2 index-east Profile C entry, three C setting changes (autocorrect 0, minimum chord keys 1, arpeggiates 0), three pseudo macros Copy/Paste/Screenshot. Other settings, A, remaining B controls and all original 501 library entries were preserved. Final library count 504.
- The first candidate used 18 layer-specific pseudo macros. Exact-version vendor ZERO tests exposed primary-map chord lookup, so it was fully rolled back and replaced with three invariant macro positions plus regular modifier shortcuts. No unused trial macros remain.
- Rollback initially timed out because firmware's CML C4 reply concatenated deleted-count 1 to the input hexadecimal token. Readback confirmed deletion had occurred. The response parser was corrected and the rollback resumed from snapshots. Chords were verified by exact-key CML C2 lookups with a total-count cross-check, avoiding assumptions about enumeration after deletes.
- Final commit followed by a separately reopened serial connection verified every one of 1080 assignments, all profile settings and all 504 exact chord outputs. Same-commit vendor simulation passed direct macro output/release, momentary/toggle layers and all three macros in a latched layer. Held-layer macro did not emit; guide excludes that behavior.
- Coverage audit found all standard keyboard functions present and zero existing word-chord input collisions. This is configuration coverage; physical mirrored directions, simultaneous ergonomics, mouse actions, reconnect and actual gameplay remain unobserved.
- Generated Hebrew HTML guide with search/local opt-in tester and 24 separate keys/actions/combined diagrams for four layers and two banks. Verified rendered diagram, eight-row table, image loading and Backslash search in Chrome.
- Recovery: private before/configured exports for A/B/C, immediate snapshots, exact manifest, serial rollback script, simulator evidence, guide and diagrams. Rollback restores the prior unused C and the B2 F, removes only three added pseudo chords and checks the prior library. The original A browser draft remains archived separately.
- Next boundary: user D/B/D mirror test, layer return, native macros, mouse drag/release, reconnect, then game-specific action validation. No background monitoring or reminders.
