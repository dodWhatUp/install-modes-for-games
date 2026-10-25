# Editable game overlays

## Complete controls source workflow — 2026-10-25

[Game Controls & Overlay 0.27.22](GAME-CONTROLS-WORKFLOW.md) connects current
reads, action evidence, priorities, bounded placement, scoped rules, v2 intake,
exact game diffs and four-view maps. Save, Publish Overlay, Apply Game Bindings
and native software remain separate. Unapplied/stale plans cannot publish through
the guarded source owner. Private-copy trials do not install this source.

## Integrated controls planning — source addition, 2026-10-24

The builder now has a [Game Controls & Overlay planning workspace](GAME-CONTROLS-PLANNER.md).
It retains the existing renderer, appearance and native/layer owners. Its saved
workbook, reviewed response and candidate maps do not activate anything. Builder
Save draft and Publish Overlay are separate actions; publication requires a
previously saved identical draft. The October 21 installed release is unchanged.

## Visual builder — 0.27.6 preview

Open **Controls & overlays → Choose a keymap or overlay → Build / edit maps…**.
Select a game and its layer/context map, then click a numbered button in the
visual layout. The native **Emitted key** is read-only. **Key label**, **Action
label**, **Full action** and **Action source / note** are separate fields; use
**Set fields in draft** to commit those edits to the draft. Keys, Actions and
Combined previews use the same structured cells. **Move buttons** explicitly
enables dragging; **Position / finger guidance…** edits display geometry and
preserves the physical position ID. This is the Cyborg II/R8 layout, not an
arbitrary-device designer or native remapper.

Preview labels fit within their numbered buttons using canvas-pixel fonts, with
shortened text where needed; full labels remain in the inspector/source. The
inspector scrolls when Windows text scaling or a smaller window needs more room.

**New game…** reuses the selected native key layout and clears game actions to
unknown. **Link / add map…** creates another context for a native layer without
changing its outputs. **Save draft** stores the source and retains its previous
version. **Save & use overlays** additionally renders/registers the maps through
the existing guarded Studio route, keeping previous groups and images. **Links →
Link game executable…** explicitly associates the actual selected game executable;
new games are never assigned invented paths or launched by the builder.

**File** imports UTF-8 JSON from `.json` or `.txt`, exports the current map, all
maps for one game, or loaded games as one **keymap_package**. A package has schema
1, kind `keymap_package`, a `documents` list and the exact referenced `keymaps`
contracts. Each document contains one or more layer/context maps, geometry,
separate emitted keys/display keys/actions, provenance and guidance. No images
are required in the exchange file. A plain `keymap_document` remains supported
when its native keymap is already known. A single-map import merges that
layer/context and retains sibling maps. Multi-game imports load reviewable drafts;
save each selected game explicitly. Existing saved sources and active overlays
do not change merely by opening a file. Export refuses to replace an existing
file; choose a new name. The package limit is 1 MiB/16 games, with 32 maps per
document and the existing 29 visible R8 positions.

**Azeron** can generate a new game draft from the registered installed profile
files or selected native JSON exports. The supported slice is native profile v1
for Cyborg II, normal keyboard presses, unassigned positions and hold-layer
links. Include linked layer profiles. Macros, long/double press, turbo, unknown
codes and other device/action types stop the import rather than becoming guessed
keys. Native labels are not game action evidence. Exact already-registered
profile bytes reuse their original native contract. New source revisions keep
old contracts; the follower first matches the actual current profile hash and
still rejects conflicting output declarations for those same bytes. No native
profile, calibration, stick or game setting is written.

**Links → Link map to picture button…** assigns the selected map/view as a fixed
guide for that game to an existing Local Studio picture slot. The slot retains
its own key, Hold/Toggle/Timed and pass-through ownership. No new key, hook or
timer is registered. To use another physical button, first configure its unused
key and enabled Local slot in Azeron/Studio. With no fixed link, the existing
native layer selection remains the content source. Removing a fixed link restores
that route on its next press. Fresh game/native selection, TTL, foreground and
image identity checks still gate the linked relay. Fixed guides deliberately
show the chosen map; they do not claim that its layer is physically active.

## Key capture and special keys — 0.27.7

In the builder's button inspector, **Key label** is now an editable special-key
selector. Choose navigation/modifier/lock keys, F1–F24, separate numpad keys,
media keys or punctuation, or keep typing a custom display label. **Capture…**
opens a focused capture box: press the key or Ctrl/Alt/Shift combination, then
choose **Use key label**. Tab and Enter are captured in the box; Esc cancels
(choose Esc from the list). System-reserved keys may need the list instead.
Capture has no global hook and does not collect typing outside its focused box.

This edits the selected button's display label only. **Emitted key (Azeron
source)** remains read-only. **Set fields in draft**, Save and Save & use retain
their separate commitments. Changing selection while a capture is open refuses
to apply it to a different button. It does not add native outputs or modify an
Azeron profile. Guest tests cover focus, cancellation, repeat, Tab/Enter/numpad,
explicit adoption, stale target and unchanged native output matrices. Windows
key naming uses VK letter/digit codes across text layouts; Alt and NumLock masks
follow [Tk's Windows source](https://github.com/tcltk/tk/blob/core-8-6-branch/win/tkWinKey.c).
Physical keyboard and system-reserved combinations remain separate acceptance.

The destination's existing 30-map bundle was reconciled against current
Cyberpunk saved settings, installed mappings/contexts and mod shortcut files,
the retained PoE2 WASD reference and Bayonetta's publisher PC manual. Current
settings take precedence over older mapping plans. Unknown, explicit unbound,
no listed action, published default and archived reference remain distinct.
Generic Shared SPARSE6 outputs do not imply game actions. Private source hashes,
before/after coverage and recovery copies stay outside the repository.

## Chat-assisted action labels — no API

The user selected this chat plus selected map files, without an API key. In
**Chat assistance → Prepare selected maps for this chat…**, select the current
map or the game's maps and optionally choose text/JSON binding references. A
local `keymap_ai_request` contains only that selected document scope, geometry,
finger/hold guidance, source versions, response schema and selected references.
It never scans application directories, credentials or unrelated files and never
uploads or sends a message. Attach that JSON in the chosen chat or ask the chat
to read that local file. Imported file content is data, not execution authority.

The chat returns `keymap_action_proposal` JSON: schema 1, exact game/document ID,
the base document SHA-256 and changes identified by native layer, context,
button ID and unchanged emitted output. Each change has `action`,
`display_action` and `source`. Unknown actions stay unknown; genre conventions
are not effective bindings. **Review chat action-label proposal…** shows the
old/new labels and sources. Adopt only selected rows into the draft; a separate
Save or Save & use is still required. Changed source fingerprints, wrong outputs,
duplicates and execution fields are refused. Adopted labels carry **AI** /
`ai_suggestion` evidence, not gameplay acceptance.

The actual Tk builder passed guest tests for canvas/field editing, opt-in drag,
source saving and publishing through the same store. Wide/narrow guest screenshots
were reviewed. Software contracts cover JSON exchange, immutable emitted outputs,
native read-only generation, proposal scope/staleness and button-link relays.
Headless AHK tests cover existing-slot Hold/recovery/release, primary-slot fixed
guides, continuity and fade behavior. These do not establish all physical buttons,
games, compositor timing or another computer's acceptance.

## Earlier editor — 0.27.2 baseline

In the Overlay page, **Edit game map…** opens the selected game's structured map.
Choose **Whole map opaque** or **Opaque buttons, clear gaps**, adjust width, edit
a button's display label, then **Save & use overlay**. The destination default is
Combined keys/actions, centered, 35% screen width and 100% opacity. Hold #19 to
show and release to hide; game/layer changes select content without opening it.

The whole-map style covers the map rectangle. The clear-gap style keeps button
interiors opaque. Studio presents premultiplied PNG alpha through Windows
`UpdateLayeredWindow`; other legacy picture slots retain their original renderer.
The separate Hub passive/Explore preview is not a per-pixel-alpha acceptance
test. Use the Studio route for clear gaps.

## Editable source and user control

`keymap_document` schema 1 is a small UTF-8 JSON master with stable game/map,
layer/context and button IDs, native keymap revision, numbered coordinates,
finger guidance, emitted keys, full action references, short display labels,
evidence/sources, presentation and explicit AI guidance. It contains no images,
code, absolute paths, device serials, credentials or native-profile exports.
Generated PNGs are disposable derivatives for the existing guarded display route.

**Set draft label** changes the draft only. **Open JSON draft…** imports a draft
for review. **Export JSON…** exports it. **Previous maps…** opens an earlier
version as a draft. None activates until the separate Save & use action. Saves
retain immutable source history; overlay imports retain the old registry and
content-addressed images. Actual native/game keys are not changed by this editor.

The original scope was a registered R8 document editor/importer: 29 visible digital
positions, with #19 and the joystick omitted from drawing. JSON can edit geometry
and sources; this is not yet a drag-and-drop device designer or arbitrary-device
remapper. Imports must match the selected game's known output matrix and native
revision. The newer builder above extends game creation/exchange while preserving
native output ownership; new device shapes still need a reviewed baseline.

## Layout and AI guidance

Finger groups warn about simultaneous reach; they are not a measured matrix of
impossible presses. Retained R8 tradeoffs and user-reported constraints keep their
provenance. Thumb-held layers may compete with movement. Common Ctrl/Shift/Space
positions do not prove comfortable chords or held-output continuity.

Genre standards need separate research into effective keys, contexts, modifiers,
prompts and user choices. Overlay editing creates no game-binding plan. Actual
changes use the existing keybind services' scoped previews, local approval,
snapshots and undo. Imported labels, guidance and source text are data, not commands.

## Coverage and transfer

Four editable game sources contain 30 layer/context maps: Shared SPARSE6,
Cyberpunk 2077, Bayonetta gameplay/menus and PoE2's archived WASD reference.
Cyberpunk labels use current saved options, with runtime contexts/overrides still
unverified. PoE2's old record has conflicting mode indicators and this destination
has no saved game config; labels stay **REF**. Bayonetta's publisher defaults do
not prove personal mappings or installation. Unknown actions stay unknown.
Only verified installed paths receive foreground associations; this is not
all-game support. The source master retains full alternatives behind short labels.

Transfer the JSON rather than treating cached PNGs as source. Nothing is uploaded
automatically to Drive/Git. On another computer, validate outputs and explicitly
reconcile its native revision and executable associations. Do not transplant
credentials or native databases. Private maps/settings/receipts remain outside
Git and OneDrive. The source updater retains the previous app version.

Guest Tk tests, headless GDI+ pixels/resources and synthetic store tests do not
establish physical #19, compositor or game acceptance. No latency improvement or
zero runtime bitmap memory is claimed.

Native references: [UpdateLayeredWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-updatelayeredwindow),
[BLENDFUNCTION](https://learn.microsoft.com/en-us/windows/win32/api/wingdi/ns-wingdi-blendfunction).


## Ordered native keys, separate per-game actions — 0.27.15 preview

A user-requested Ordered R1 candidate separates the physical emitted-key pattern
from the game's actions. The Cyborg II/R8 geometry is retained: BASIC's top row
is 1–4 and bottom row 5–8, the middle alphabetic rows are B/C/E and F/G/H, and
the thumb row is I/J/K. W/A/S/D remain reserved for stick movement. NUMBERS uses
1–3, 4–6 and 7–9 from top to bottom. Existing modifier, layer, #19, stick,
Enter/Escape/Backspace and inactive/unknown action settings remain owned by the
native profiles. The original family is retained; candidate profiles use new
identities and references. The plan does not silently rewrite other games.

For DOOM, the saved configVersion 19 is a contextual binding file, not a generic
INI or simple `bind` CFG. The reviewed `idtech-bindset` adapter retains exact
byte spans, BOM/newlines/comments, command identities, linked input bundles and
all literal cvars. Selectors explicitly identify bindset, statement kind,
command and occurrence. Unknown versions, duplicate/missing resets and script
execution directives are refused. Moving a known multi-command key retains its
command-sharing pairs; any new sharing pair, including an unlisted collision,
is refused. Existing formats keep their previous validation behavior.

The first local DOOM plan inventories 283 binding rows and proposes 37 key-span
changes, while all mouse/controller/movement/modifier/system and non-binding
lines stay unchanged. Slayer, menus, automap, Dragon and Atlan are separate
contexts; shield/spear contextual commands remain together. No new action or
weapon-name assignment is inferred. The existing Keybinds Service owns preview,
prepare, exact local authorization, process guards, backup, atomic replacement,
readback, history and rollback. Native profiles remain Azeron's owner; imported
bytes must be reconciled before the overlay's exact native contract is selected.

The same source generates structured Keys/Actions/Combined maps using the
existing builder, with no image-to-action guessing. Shared native key geometry,
per-game command assignments and rendered images are separate records. Native
output changes require a new native revision; changing only a display label
does not remap anything. Game contexts remain manual. Switching the new native
family into another game requires a separately reviewed binding plan for that
game; retain the previous native family and existing maps for those games.

Six synthetic adapter checks and a copied-file 37-span transaction passed. The
extended suite passes 22 checks with deterministic UTF-8 subprocess output. A
legacy 109-check Windows run passed 107; two pre-existing synthetic-symlink
fixtures could not create their links without the unavailable Windows privilege.
No security setting was changed. This is format/file verification; native import,
activation, gameplay prompts, reach and simultaneous finger combinations retain
separate acceptance. Machine-specific originals, exact plans, native exports and
configuration bytes stay private. No game launch, automated gameplay, capture,
benchmark, graphics change or cloud publication is authorized by the format.

## One-click content views — 0.27.16 preview

In **Controls & overlays → Choose a keymap or overlay**, the **View** row has
four direct choices. They save immediately for the selected game:

| Choice | Button content |
|---|---|
| Key first | The existing large, bold key with the smaller action underneath |
| Action first | A large, bold action with the smaller key underneath |
| Action only | The action without emitted-key text or physical button numbers |
| Key only | The key without the action label |

The selection persists per game and follows the existing layer/context route.
It changes display only: no native profile, game binding, visibility trigger or
fade timing changes. Existing Keys, Actions and Combined identities remain valid;
ActionFirst is an additive view. Imported image-only groups require an exact
matching asset for a view; unsupported combinations retain the normal missing-
asset refusal rather than showing a stale map.

The visual builder has the same four choices. These preview the current draft;
**Save & use overlays** applies the chosen view. Publishing also retains a
previously saved view when no explicit replacement is supplied. The JSON source
still keeps keys and actions separate. Generated action-first/action-only text
fits the button and retains the full source label if shortening is required.
The choice buttons wrap for narrow windows and use native keyboard focus.

The destination's explicit DOOM preference is Action only. Current native
revisions and the game binding file are unchanged. Headless rendering and
store/routing checks, plus isolated Tk one-click/persistence/stale-state and
large-text/narrow-preview checks, are separate from physical game acceptance.

## Scoped appearance presets — 0.27.17 preview

Open **Controls & overlays → Choose a keymap or overlay → Appearance & presets…**.
Choose **Global defaults** or a game in **Save settings for**. **Action text (%)**
and **Key text (%)** are independent, from 50–200%; 100% retains the original
size. The four content layouts, background, overlay size, opacity, monitor and
position are part of the appearance. Large or long labels shorten within their
own button regions; full source labels remain in the editable JSON.

Game settings can use an independent appearance or **Use global defaults for
this game**. Editing global settings affects games using those defaults. The
explicit **Use these global defaults for all games now** choice removes game
overrides. Initial migration retains each game's existing look, including
DOOM's Action only choice; no active appearance is reset simply by opening this
editor. Fade timing stays in **Show/hide transition…**.

**Preset actions** saves the draft as a named snapshot, replaces a selected
preset, duplicates it into another game/global scope, moves it, or deletes it.
Names are unique within each scope. Copying/moving presets only organizes the
library; it never changes active game settings. Selecting a preset loads a
draft. **Apply appearance** saves and activates it for the current scope.
Applying global defaults to all games is a separate explicit choice.

Styles and presets live in the same private, versioned overlay registry as
image references. Rendering runs in a worker; the old images remain active
until a single optimistic registry commit publishes the prepared images and
settings. Cancellation before commit, source drift, a stale registry or an
unsupported editable source keeps the prior appearance. Existing image files
and preceding registry versions remain available for recovery. All four views
are prepared in advance; live input/layer routing still selects cached images.
Future builder publications retain saved typography and appearance; source
document defaults remain separate from the active overlay appearance.

Only current editable native-layout families are regenerated. Archived families
are preserved rather than rebuilt from a different native revision; select or
import their exact editable source before styling them. Image-only groups need
an editable map first. Keymaps, native profiles, game bindings, foreground
associations, visibility controls and show/hide timing are unchanged.

Older releases do not understand the optional appearance preference field.
Downgrade with the paired preceding registry (and referenced images), preserving
later edits first; reverting program code alone does not revert user data.
Headless transaction/rendering and isolated Tk preview/preset/scope/worker tests
establish software behavior, not physical-device or game acceptance.

## Portable JSON and global keymap presets — 0.27.18 preview

In **Appearance & presets… → Preset actions**, use **Export appearance JSON…**
or **Import appearance JSON…**. Export all scopes, global settings/presets,
one game, or one selected named preset. The optional saved-current-appearance
snapshots make global/game settings transferable even when they have not been
saved under a preset name. Draft edits need **Apply appearance** before export.
The versioned `overlay_appearance_package` includes only names, stable game IDs,
layout/text sizes/background/position and game labels; no image or executable
path, native profile file, credential or automatic upload is included.

Appearance import shows destination scope and each keep/add/replace result.
Keep original scopes, or explicitly map records into the global library or an
existing game. Missing destination games require that explicit mapping or local
game registration first. Conflicts offer Keep existing (default), Keep both with
renamed copies, or Replace matching names. Review and **Import reviewed presets**
save the library through the existing optimistic registry owner. Import never
applies a style; select an imported preset and **Apply appearance** separately.
Re-exporting an imported current snapshot is supported without duplicate IDs.

In **Build / edit maps… → File → Export JSON — all / game / map / global…**, choose:

- All loaded games in one `keymap_package`.
- One game's complete layers and contexts.
- One selected layer/context, retaining the normal single-map merge behavior.
- All or one saved global keymap template in a `global_keymap_package`.

Game exports contain loaded drafts, with keys, action labels, geometry, layer and
context kept separate. Imports load reviewable drafts; **Save** and **Save & use**
remain separate. These map packages retain exact native source identity references
for validation. They are personal recovery data for Drive or a private Git
repository, not sanitized public catalog data. They contain no native profile
files, executable associations or credentials. A package does not install its
referenced native profiles or prove the other computer's device matches them.

The builder's **Global presets** menu manages reusable shared-layout templates.
**Save current draft as global…** clears game action labels by default, preserving
emitted keys, geometry and layer relationships; **Keep action labels from this
game** explicitly retains them. **New game from preset…** creates a separate
in-memory draft, leaving the template, original game and active overlay intact.
Global-template JSON import has its own conflict review and never starts a game
or activates a layout. The versioned private template library retains preceding
bytes, refuses stale/concurrent writes, and is separate from runtime polling.

Exports use a new filename to preserve previous copies and are plain text JSON
with no embedded pixels. Existing image masters remain local. Cloud upload and
Git publication are separate actions; adding these controls does not enable
synchronization or transmit any files. Unknown fields, duplicate IDs/names,
invalid sizes/schema and unsupported native contract collisions are refused.

## Key and map comments — 0.27.19 preview

In **Build / edit maps… → Comments**, edit **Selected key comment…**, **This map
comment…**, or **All maps of this game…**. The selected-key inspector also offers
**Key comment…**. Key comments appear in small colored text inside their button;
map comments appear beneath the layer / view / context subtitle. A game-wide
comment appears on each layer/context; a specific map comment occupies a second
line when both are present. These comments remain visible in all four content
views, including Action only and Key only.

Choose a named palette color or enter `#RRGGBB`. Key comments allow 160 characters;
header comments allow 240. Text stays inside its reserved region and may shorten
with an ellipsis. Full text remains in the source JSON. Clear the text to remove
a comment. **Set comment in draft** changes the preview; **Save** stores the
source, while **Save & use overlays** also publishes the updated display maps.
Keys, action labels, native profile outputs and game bindings stay separate.

The optional `comment` object has exactly `text` and `color` fields, for example
`"comment": {"text": "Hold to show", "color": "#79DDF2"}`. It may appear at the
document level (all maps of the game), on a map (one layer/context), or on a cell
(one physical key). Colors in JSON use hexadecimal notation; comments are one
line. Existing documents without comments retain their previous rendered pixels.
The 512 KiB source limit also applies to saved annotated documents.

Game, selected-map and all-game JSON exports preserve comments. Saving a global
template clears game action labels and comments by default; **Keep action labels
and comments from this game** retains them explicitly. Starting a new game clears
the source game's comments. A new context retains the game-wide comment and
starts without copied map/key comments. AI action-label proposals preserve these
separate annotations. No online generation or upload is required.

Annotated documents require 0.27.19 or later. Before rolling back code, preserve
later edits and reconcile annotated sources/template libraries with compatible
backups; reverting the application alone does not revert data. This update
does not add comments to existing production maps or regenerate their images.
## Comfort, grouping, icons and key colors — 0.27.21 preview

Open **Keymap builder → Customize** or select a key and choose **Preferences,
icon / colors**. Comfort is 1–5 (5 easiest), with unknown as the initial state.
Personal group, preferred action kind, tags and notes belong to physical
positions across this game's maps. Action category, frequency and simultaneous
button requirements belong to a specific layer/context cell. Position review
sorts comfort first, personal group second, preferred kind third, then button
number, with text filtering. Same-finger and frequent/low-comfort warnings are
advisory; physical reach and actual game behavior need separate acceptance.

Choose a symbol from the icon list or type an emoji. Key/action text colors,
icon color, border color, key background color and background opacity inherit
from all game maps → map/layer → individual key. A layer scope covers its
contexts. Blank removes that override; more specific choices remain. To see the
game behind translucent keys, use the builder's clear-gap Background choice.
Whole-map opaque intentionally composites translucent fills over an opaque
panel. Text and outlines remain visible independently of background opacity.
Emoji glyph appearance depends on the receiving computer's installed fonts.

Optional document/map/cell `key_style`, map `label`, button `ergonomics`, and
cell `icon`/`organization` travel with existing game/map/global-template JSON
exports. Existing documents require no migration. Clean new-game/context
drafts clear action-specific organization and icons, retaining physical
preferences and colors; explicitly preserved template actions retain them.
Layer display names do not change native layer identity. Older readers may
refuse these optional fields, so preserve source history before downgrading.

Changes remain in the draft until Save. Save & use pre-renders all existing
views through the shared renderer. Editor preview uses those same pixels for
styled cells; runtime input timing is unchanged. No label, icon or missing
input warning creates an emitted key or writes an Azeron/game profile. Native
remapping still requires a separately reconciled profile and game-bind plan.

