# DOOM Combat R2 — complete accessibility review

Prepared 25 October 2026. **Review only; the working game bindings, native
profiles, active maps and appearance are preserved.** The existing setup remains
usable. This review addresses unused first-layer capacity; combat comfort is
still untested.

## Coverage and evidence

The current saved inventory contains 283 binding rows / 168 command-context
pairs. The native map contains six layers, five display contexts, thirty maps
and 870 cell routes. All 31 BASIC controls, including the dedicated Overlay
button and movement stick, receive a disposition. Bindsets 2 and 6 still have
no reviewed display-context link. Four additional equipment-cycling UI actions
are documented upstream but are outside this saved binding inventory.

The installed 0.27.22-preview.1 source and current COMBAT R2 native contract are
the baseline. Prior user reports accept #19 visibility and the explicit WEAPONS
title while #2 is held. They do not establish comfortable combat or latency.
The earlier cfg-only apply was insufficient: effective binding persistence also
involves the opaque native game profile. Any later change needs native-menu and
clean-restart verification, with paired recovery for both actual owners.

The prior workbook retained a pre-publication map pin. The prepared next review
rebases to the current published compact-label map and reconciles stale action
descriptions with the later observed native-menu settings. Old provenance is
retained; no older handoff file replaces newer source.

## BASIC decisions

Physical rows are counted bottom-up; the user's preferred order is 2, 4, 3, 5, 1.

| Button/output | Current | Proposed review |
|---|---|---|
| #10 K, middle row 3 | No saved Slayer action | CORE: Switch Off-hand Weapon from #8 C |
| #8 C, ring row 5 | Switch Off-hand Weapon | CORE: becomes free; no filler action |
| #15 L, index row 3 | No saved Slayer action | EXTENDED: Next Melee Weapon |
| #18 P, index row 1 | No saved Slayer action | EXTENDED: Previous Melee Weapon |
| #12 E, middle row 5 | No saved Slayer action | EXTENDED: Next Shield Rune |
| #13 O, middle row 1 | No saved Slayer action | EXTENDED: Previous Shield Rune |
| #3 Alt, little row 4 | No saved Slayer action | Intentionally free pending modifier/chord and UI capability checks |
| #38 N, ring row 1 | No saved Slayer action | Intentionally free; no evidence justifies another shortcut |
| #17 F, index row 5 | Magnify | Retain accessibility utility until personal need is known |
| #23 Backspace, #29 Q, #31 T, #41 Enter | No saved Slayer action | Preserve contextual/side controls and stick access |
| Other BASIC controls | Working actions and layer holders | Retain |

CORE is one proposed game binding change and zero native changes. It uses a
more accessible free position and separates off-hand selection from the ring
finger used for throw/ready and Dash. That is a model-derived benefit; a required
simultaneous throw/off-hand gesture has not been established.

EXTENDED adds four selection shortcuts. The [official Update 3 notes](https://slayersclub.bethesda.net/en-US/news/doom-the-dark-ages-update-3)
document these UI actions. Their actual current keyboard assignments and exact
local binding steps need native-menu review. No engine command or supported
writer field is fabricated. Next/Previous actions are paired by finger, with
reverse actions on the least-preferred row. These are proposals, not evidence
that the user rarely cycles backwards. No personal frequency is invented.

Direct favorite-weapon shortcuts remain a separate alternative: the user's
favorite and reliable multiple-key binding support are unknown. Rebinding the
existing numeric weapon fields would break the fixed WEAPONS grid and is not
part of this proposal.

K #10 is valuable space, so Off-hand Switch must not win by default. The full
review also compares moving the paired Shield Throw / Spear Ready commands
G → K, or the paired Use / Stab commands J → K, instead. Either is two existing
keyboard rows, with mouse alternatives and the source bundle preserved. The
former could separate held Ready from ring-finger Dash; the latter reduces ring
crowding for interaction/stab. These alternatives compete for the same position
and must not be combined. Required gameplay overlap and equipment use determine
which benefit matters most. No globally optimal placement is claimed.

## Finger and sequence review

- Ring #7 throw/ready and #5 Dash still conflict **if** a required gesture keeps
  #7 held while Dash is needed. The mouse throw alternative is preserved. Moving
  Off-hand to K does not solve that pair.
- Index #14 Jump and #16 Melee still need review if sustained Jump is required.
  Mouse4 Melee is preserved. Proposed L/P equipment cycling uses the same index
  finger, so it also needs this conditional check.
- Observed Auto-Sprint is Off. The [official accessibility guide](https://slayersclub.bethesda.net/en-NZ/news/doom-the-dark-ages-accessibility-guide)
  describes pressing to start Sprint and stopping movement to end it. This
  supersedes the earlier assumption of a required continuous Shift hold.
  Sequential middle-finger workload remains; Spear Slam is a separate context.
- The #2-held numeric grid remains 1–3 at #7/#11/#16, 4–6 at #6/#10/#15,
  and 7–9 at #8/#12/#17. It avoids the little finger that holds the layer.
  Selection during another required held movement input remains conditional.
- K/E/L/O/P also occur elsewhere in the native layers. Every same-context alias
  gets a matching proposed label. Thumb/side aliases are incidental, not primary
  movement-dependent combat routes. Other game contexts retain their bindings.

Current styles remain Previous quick switch, Standard class switch, 180 ms
wheel delay, single-input keyboard Stab/Slam and held Spear Ready. Equipment
selection is not firing, striking, blocking or throwing. No DLC ownership or
equipment unlock is assumed.

## Next boundary

The private upload package includes the complete inventory, all button
decisions, output aliases, conflicts, inactive current/proposed map previews,
supported workbook, updated template and a copyable external-review message.
The local existing workflow remains the implementation owner. The external
review returns a reasoned delta; it does not install anything or automatically
promote shared rules.

Next: review CORE versus EXTENDED and return the structured review. Then a local
agent reconciles the current source and native UI, prepares the exact selected
change set and verifies authorized changes through normal exit/relaunch before
separate Overlay publication. No new combat or game-input test is performed by
this preparation.

Validation: 31 existing planner and 10 workflow tests passed. All 244 generated
current/CORE/EXTENDED views decode and have no truncated labels; three BASIC
Combined views were visually inspected. Native output matrices and all
non-gameplay context cells match the baseline. Of 969 persistent original files,
968 remain byte-identical; only the planning workbook advances to revision 9,
with revision 8 retained through the existing guarded history owner. One
auto-renewing runtime selection relay is accounted for separately, not restored
or treated as a persistent settings mutation. Exact private receipts and upload
manifest record these limits. No new physical or combat acceptance is claimed.
