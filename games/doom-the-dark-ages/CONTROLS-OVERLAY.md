# DOOM campaign and Revelations action maps

## Current active Rebuild R1 — 2026-10-26

This section supersedes the historical readiness and key tables below.
All ten changed actions were saved in DOOM and read back after normal exit
and relaunch on build 25755602. The matching thirty maps / 120 images are
published, and the saved DOOM runtime profile points to that source.

| Action in the Slayer menu | Key | BASIC position |
|---|---|---|
| Shield Throw; Meat Hook / Spear Ready | K, with Mouse3 retained | #10 |
| Weapon Quick Switch / held Wheel | L | #15 |
| Switch Off-hand Weapon | G | #7 |
| Objective Ping | C | #8 |
| Magnify | B | #4 |
| Next / Previous Melee Weapon | F / P | #17 / #18 |
| Next / Previous Shield Rune | E / O | #12 / #13 |

Use/Stab J #6, Melee/Glory I #16, Class Weapon H #11, Dossier R #22,
Ctrl #5, Shift #9, Space #14, #19 Hold, #2 WEAPONS hold and the movement
stick retain their owners. The numeric grid and all mouse alternatives remain.
See the [full menu-order HTML guide](DOOM-BINDING-GUIDE.html) for all 96 rows,
press/hold settings and the current maps. The four melee/rune selectors are
native-UI profile settings; the text CFG alone does not contain them.

The existing Actions view, appearance and activation settings are preserved.
Actual play and physical simultaneous comfort remain unverified. Contexts
`menus`, `automap`, `dragon` and `atlan` are manually selected in Game Tools;
native layer following does not infer the game's current mode. Turret bindings
are documented in the guide, with no separate Turret map context added.
The [activation history](HISTORY.md#2026-10-26--clean-rebuild-r1-applied-and-native-restart-verified)
records the file/UI boundary, checks and paired recovery requirements.

## Read-only input audit and readiness — 2026-10-25

The [revision-3 history](HISTORY.md#2026-10-25--input-source-audit-revision-3-and-play-readiness-options)
supersedes unqualified interpretations below: Shield/Spear switching is an
installed game concept, but the exact current T / `_weapswapSupport` menu label
is not yet verified. It must not be silently equated to `_nextsupportitem`.
Authenticated saved setting tokens are available privately; selected UI modes
remain provisional. Native COMBAT R2 keys are present, but proposed game changes
and preview maps are not active. A thirteen-change alternative leaves T alone.
Source-contract reconciliation, separate game apply/Overlay publication and
physical acceptance remain future operations, not completion claims.

## Latest source-only inspection — 2026-10-25

Current saved cfg values differ from all fourteen recorded R2 edits. BASIC's
raw hash differs, with parsed equality to the preserved export; the other five
COMBAT R2 files match. A fresh private-copy transaction rendered 120 views and
restored exact original bytes. Current profile copies parse to the same six-layer
outputs, but the fresh-hash contract is a private candidate. No live profile,
config or overlay was restored. See [the current source workflow](../../docs/GAME-CONTROLS-WORKFLOW.md).
The dated installation/acceptance statements below retain their original scope.

Prepared from the destination's saved configVersion 19 on 2026-10-20. The original
configuration and native Azeron profiles remain unchanged. The editable JSON is
the private source; rendered PNGs are derivatives consumed by the existing route.

## Automatic game selection

The exact installed `DOOMTheDarkAges.exe` path selects this group only while it
is foreground. Merely running the game in the background, the idTech launcher,
Steam, a stale foreground observation or another executable with the same basename
does not select DOOM actions. Focus changes retain the existing other-application
fallback choice; that fallback is a shared key layout, not an old DOOM map.

The user retained **#19 / selected layer buttons** for visibility. Focusing DOOM
does not make the overlay permanently visible. Native layer tracking, revision
checks, relay expiry and image hashes still apply. The new game's default is
`gameplay`, Combined, with the existing small centered opaque appearance.

## Context selection

Thirty maps cover six native layers in each of `gameplay`, `menus`, `automap`,
`dragon` and `atlan`. Open **Controls & overlays → Choose a keymap or overlay**,
select this game and choose **Context** for a mode-specific guide. Return to
`gameplay` for the combined campaign/Revelations guide. Mode selection is manual:
native layer following does not observe the game's menu, vehicle, campaign,
equipped support weapon or unlocks. A native layer called MENUS does not prove
an in-game menu is open.

## Shared campaign / DLC inputs

These refer to this destination's saved Slayer bindset, not universal defaults.

| Key | Saved action labels |
|---|---|
| R | Shield throw/recall; Revelations spear throw |
| G | Use/interact; Revelations spear stab |
| Shift | Sprint; Revelations spear slam |
| Ctrl | Dash / dodge |
| T | Switch support weapon: shield / spear |
| E | Charged melee / glory strike |
| Q | Recent weapon / weapon wheel; behavior follows input-style settings |
| F | Switch weapon variant |
| V | Equip BFC |
| 1–8 | Saved weapon slots; weapon-name/slot assignments are not guessed |

[id Software's Revelations notes](https://slayersclub.bethesda.net/en-US/news/doom-the-dark-ages-revelations-update-4)
document the Chain Spear input section and configurable input styles. A saved
command is not proof of ownership, an unlocked ability or observed gameplay.
The mapper preserves every command when a key has multiple context-dependent
actions. “No Slayer/Menu/Map/Dragon/Atlan bind” means no key-specific entry in
that saved bindset; engine/global shortcuts remain unverified.

Mouse buttons and joystick directions retain their existing owners and are not
newly assigned to the 29-position diagram. Their saved reference is included in
the private map guidance and binding-source record. No game binding, native
profile, Steam Input layout, mod or graphics setting was changed.

## Verification and recovery

All 90 views have verified managed hashes and no truncated action labels. Thirty
layer/context routing checks, 36 foreground guard checks and 18 native
unknown/stale/revision-mismatch checks passed with synthetic observations.
Physical in-game display, prompts and behavior remain separately unverified;
the game was not launched for this work. Exclusive-fullscreen coverage is not
claimed.

Private recovery preserves the previous registry and relevant source/settings.
To disable automatic DOOM selection, remove only its new exact executable
association using a guarded scoped edit; retain the document and assets for
review. Preserve later user changes before reverting anything. A previous app
binary does not undo map data. The historical graphics experiment remains paused.
### Intermittent display follow-up — 2026-10-20

The user reports that the map appears only sometimes. Physical/game acceptance
is therefore failed/pending, superseding the earlier unanswered acceptance
question. Scoped runtime diagnostics recorded inactive/stale route suspension
and sharing error 32. Toolkit 0.27.11 repairs the concurrent relay-file handoff;
see the [repair and bounded tests](../../docs/OVERLAY-GROUPS.md#relay-file-contention-repair--02711-preview).
Keep #19 / user-selected layer visibility, all native profiles, saved DOOM binds,
and map documents unchanged. Physical hold/release and in-game retest remain
pending; no graphics experiment or automated game-input test is resumed.

### Response follow-up — 2026-10-20

The user confirmed 0.27.11 now appears reliably, while reporting slow opening
and layer changes. The [0.27.12 response update](../../docs/OVERLAY-GROUPS.md#overlay-response-time--02712-preview)
shortens scheduling waits and reuses hash-verified metadata. The user selected a
60ms fade. Profiles, game bindings, labels, geometry and visibility choices are
preserved. Component/file fixtures are separate from physical DOOM acceptance;
no graphics experiment or automated game input is resumed.


### Current Ordered R1 configuration — Ordered R1 native keys and separate DOOM actions

The user explicitly requested ordered physical key rows, independent game-action
placement and an actual offline game binding-file update. Toolkit 0.27.15 adds a
reviewed `idtech-bindset` adapter to the existing guarded transaction service.
It inventories configVersion 19 bindsets and edits quoted key spans only, keeping
shared command bundles together and rejecting new selector collision pairs.
No cvar, mouse/controller, movement, modifier or graphics line changed.

A separate six-layer Ordered R1 Cyborg II family was imported. BASIC uses 1–4
across the top and 5–8 across the bottom, B/C/E then F/G/H in the middle, I/J/K on
the thumb row; W/A/S/D remain on the stick. NUMBERS has ascending 1–3, 4–6, 7–9
rows. Utility banks and layer/modifier/#19 behavior retain their prior owners.
The native importer regenerated profile IDs without fixing layer references;
the ten new hold links were reconciled offline. All ten pre-existing profiles
are byte-preserved, and exact imported revisions were registered.

DOOM's 37 binding edits were applied after normal Steam shutdown through the
existing Service with source/process/plan checks, whole-file backup, journal and
readback. BASIC combat actions are B BFC, C recent/wheel, E melee/strike, F use/
spear stab, G variant, H shield/spear throw, I support switch, J dossier, K magnify.
Weapon slots and fixed movement/modifier/mouse/controller bindings are retained.
Separate saved bindsets supply menus, automap, Dragon and Atlan labels. These are
saved-config claims, not observed gameplay or a universal genre recommendation.

Thirty DOOM maps and six shared maps are portable editable JSON masters, rendered
into 108 hash-checked views without truncation. DOOM's exact foreground executable
selects the new game group; Azeron and the other-application fallback use the new
shared group. All 180 preceding assets and old groups remain available. The
existing #19 Hold, optional layer choices, 48ms fade and prepared-frame route are
preserved. In-game mode selection remains manual; a MENUS layer is not detection.

Ninety DOOM layer/context/view routes, 60 fallback routes, 90 native revision
guards and three focus-exclusion fixtures passed. New adapter tests (6) and
extended tests (22) passed. Legacy suite: 107 pass, two synthetic symlink cases
blocked by Windows privilege 1314; no security settings changed. All 427 scoped
source payloads verified. GUI startup and native key labels were observed.
The user confirmed BASIC, NUMBERS, MENUS and return-to-BASIC work with #19 held.
Actual game actions, physical comfort and prompts remain pending the user's next
DOOM session. No game launch/input experiment, graphics change, benchmark or upload.

Rollback uses the existing keybind transaction's reviewed inverse after process
and current-byte checks, reselects the retained R8 BASIC family, and restores only
the prior DOOM/native-preview associations and shared fallback through current
Store guards. Preserve later edits instead of blindly copying an archived CFG.
Private machine indexes point to exact plans, hashes, source owners, portable
JSON/native export, acceptance and recovery. Other games retain old R8 bindings
and need separate plans before using Ordered R1.

### 2026-10-20 — Four overlay content views, DOOM action only

At the user's request, toolkit 0.27.16 adds one-click per-game View choices:
Key first (existing Combined), Action first (new ActionFirst), Action only and
Key only. Action first emphasizes the bold action over a small key; Action only
hides emitted keys and physical position numbers inside the cells. The builder
previews all four, applies its explicit view on Save & use, and publishing
preserves a saved view when no replacement is supplied.

The destination's DOOM selection is Action only. Ninety-six ActionFirst views
were added and 96 Actions views regenerated; all 192 existing Keys/Combined
images remain unchanged. Sources stay separate editable JSON. Full labels stay
in the source when another game's long label needs shortening; DOOM has no
truncated labels. Native profiles, saved game bindings, documents, associations,
hold/layer visibility, size/background and 48ms transition timing are unchanged.

65 headless contracts, four isolated Tk checks for one-click persistence,
stale-state refusal and four-mode narrow/large-text previews, 120 DOOM routing
fixtures, 384 asset hashes and 69 source-export contracts passed. The installed
UI's ActionFirst/Actions persistence and pinned action-only DOOM preview were
observed. The combined lab run hit its deadline during image work; separated UI
checks completed and headless rendering passed. Physical gameplay was not run.

428 scoped source files were verified, preserving unrelated work. Previous
registry/image/source recovery is retained privately. Restore/reconcile the old
registry before a source-only downgrade, since the previous parser does not
accept ActionFirst assets. Preserve later user edits and all native/game files.
The app's existing fresh-event requirement after restart remains unchanged.
No game launch/input, capture, graphics change, benchmark or cloud upload.

### Current Combat R2 configuration — 2026-10-21

The separate COMBAT R2 family is now selected, the 14-row offline DOOM binding
transaction is applied and the matching 30 DOOM / six shared maps are published.
Hold physical **#2** for the WEAPONS bank; release returns to BASIC. Weapon
slots 1–3 are #7/#11/#16, slots 4–6 are #6/#10/#15, and slots 7–8/BFC are
#8/#12/#17. These keep selection on ring/middle/index while the little finger
holds #2. The user's physical comfort order is bottom-up 2 → 4 → 3 → 5 → 1.

BASIC keeps Ctrl dash, Shift sprint/slam and Space jump, plus shield/spear throw,
variant switch, melee/strike, use/spear stab, recent weapon/wheel, shield/spear
selection and magnify. Dossier is on a noncombat thumb position; hint is on the
bottom row. Mouse and stick inputs retain their prior ownership.

DOOM actions appear only for its exact foreground executable through #19 or
the existing selected-layer choices. Normal view is Action only; alternate
second hold remains Key first. Shared keys are the other-application fallback.
The user accepted BASIC/WEAPONS return and #19 release; DOOM gameplay behavior
and comfort still need their own check. See the latest [history](HISTORY.md)
for preservation, capacity-repair evidence and paired rollback boundaries.
