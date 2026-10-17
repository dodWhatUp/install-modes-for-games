# PoE2 weapon and skill switch lab — v0.1

Open **POE2-Switch-Lab.html** in a browser. It is one self-contained offline file.
The lab uses the 13 fixed skills and #37/X from the existing GROUPED R2 map.
The demo names, weapon-set assignments and available flags are examples, not a
readback or modification of the player's character.

## Try it

1. Click **E / #11**: the model selects weapon set II and uses Skill 5.
2. Click **Q / #12**: it returns to I and uses Skill 4.
3. Use **Edit skill names and weapon-set assignments** to rename available
   abilities and choose I, II or both. Apply commits edits; Cancel discards drafts.
4. Focus the keyboard test box to check the R2 keyboard outputs, including Ctrl
   combinations and X. Mouse skill cards are clickable; physical mouse/HID
   identity recognition is not implemented. Repeat key events are ignored.
5. Choose **Inventory equipment + gem simulation** to demonstrate a complete
   three-step loadout replacement. Its optional delay controls this offline
   model only; it is not an anti-detection setting.

Save/load JSON affects this lab only. **POE2-Switch-Setup-v1.json is not a native
Azeron profile import.** Keep the two existing GROUPED R2 native profiles.

## What is feasible

The supported combat route is two already-equipped native weapon sets with
their available skills assigned in PoE2's expanded skill details. One skill
request can make the game select the appropriate weapon set. Actual attribute,
weapon, Spirit, passive and timing requirements still apply. Not every inventory
gem can be made available without equipping it.

A generic inventory sequence is technically demonstrable in a model. A live
single-button sequence equipping multiple items/gems and rebinding abilities
would exceed the current macro rule. There is no live input adapter in this
package, and no client-memory/API/packet or anti-cheat modification.

## Protecting this PC

GGG's current privacy policy discloses both hardware identifiers and OS
information. That establishes collection, **not verified hardware-ban use**.
No current official assurance against hardware bans was found. Community
claims that GGG does not use them are not a guarantee for PoE2.

A fresh account, different Windows version or a VM does not establish guaranteed
hardware isolation. Solo/SSF uses the online service; no macro-policy exemption
for solo play was identified. The current store still lists paid Early Access.

**NEW-ACCOUNT-TEST-PLAN.json** is prepared, not executed. It separates native
function checks from a prohibited-sequence test blocked by the user's PC
protection requirement. **GGG-SUPPORT-QUESTION.txt** is a reviewable policy
question; it has not been sent.

## Evidence and tests

**OFFLINE-TEST-RESULTS.json** records model tests; **BROWSER-REVIEW.json**, when
present, records separately observed browser acceptance. Neither is a live
gameplay, physical-device, account-safety or hardware-ban result. The model
does not reproduce game latency/animation or identify actual skills/items.

The inventory model preflights ownership, conserves demo items and preserves
completed steps when cancelled. Changing mode, hiding the page or losing focus
stops pending timed steps. Restore initial demo resets only fictional items.

The UI keeps prepared skills together, distinguishes active I/II with text and
colour, uses a native mode selector, and places edits/research behind named
disclosures. Labels and status remain visible. Session edits are not persisted
automatically; explicit JSON export preserves them. Keyboard capture is scoped
to the focused test box, and user-entered names render as text.

## Integration boundary

This is a separate prototype, not an installed overlay-host extension. A later
supported integration can reuse the source R2 slots for a display-only skill/
loadout view. Its selected weapon set must be labelled **Selected**, not
**Observed**, until a supported real state source is demonstrated. Native skill
assignments require inspection of the actual character before configuration.

Build: `node build.cjs`. Model tests: `node test.cjs`.
The build uses the repository's existing R2 master when available, otherwise the
included frozen **R2-REFERENCE-KEYS.json**. That reference contains the source
revision/hash and derived fixed keys; it is not an Azeron import. These commands
write inside this lab directory.
No packages or third-party executables are required. Serve locally for browser
review with `node serve.cjs`; the standalone HTML also opens directly.

## Sources reviewed 2026-10-12

- [GGG native skill/weapon assignment](https://www.pathofexile.com/forum/view-thread/3610245).
- [GGG Third-Party Policy](https://www.pathofexile.com/developer/docs).
- [GGG privacy/terms: hardware and OS information](https://www.pathofexile.com/legal/terms-of-use-and-privacy-policy).
- [Steam: current access and network requirements](https://store.steampowered.com/app/2694490/Path_of_Exile_2/).
- [Community claim against hardware bans — unconfirmed for PoE2](https://www.pathofexile.com/forum/view-thread/3522234).

## Rollback

No live configuration changed. Closing the browser stops the demo. Removing the
switch-lab folder and its separate ZIP removes these additive prototype files.
