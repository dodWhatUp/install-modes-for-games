# Controller keymap drafts

Controller tools can prepare game-specific drafts from the user's current
reWASD schema-3 configuration. Native input, game bindings and the published
Azeron Overlay keep their existing owners. No controller Apply or automatic
activation is introduced by the draft editor.

Read a native profile, choose a layer and game context, annotate a control with
its action and icon, and use **Update row**. **Save draft**, **Preview** and
**Export** are separate operations. Clicking or typing in a choice field never
saves. Previews use the same editable source and have an independent action-icon
visibility choice. Prior saved versions remain in the draft history.

The reference has a neutral controller front/back silhouette. Rear positions,
standard-button passthrough, physical Shift access and input acceptance remain
explicitly unverified. Azeron's 29-cell renderer/registry is not given invented
controller button IDs. Exports are review JSON, searchable HTML and an offline
SVG reference; none is automatically sent to a live Overlay consumer.

## Evidence and game labels

Every explicit native mapping retains its original condition, activation and
output data. Shared output labels and native reWASD radial commands are not
silently promoted to game actions. The native default/pass-through mapping is
not fully enumerated by these files and remains unknown.

For DOOM, the existing game-controls workbook supplies the saved JOY action
catalog, priorities, uncertainty and icons. Automatic labels are limited to an
exact directional-name match between reWASD DpadUp/Down/Left/Right and DOOM's
JOY_DPAD_UP/DOWN/LEFT/RIGHT. This is a configuration-level semantic crosswalk,
not physical acceptance. JOY1–JOY10 and trigger-number correspondences are not
assumed. Bundled meanings and unresolved questions remain visible. Other games
can receive explicit per-control/context user annotations without native edits.

Shadow of War's accepted October 26 route uses its per-game Steam Input gamepad
template over the reWASD virtual Xbox output. The later user-selected PATH OF
EXCIL 2 configuration supersedes the older applied-profile assumption. Keep
that accepted route and both native profile versions; neither this editor nor
a stale older Steam-Input-Off note authorizes changing it.

The previously saved No Rest controller setup can reference a now-missing
Config 1 file and an unlinked device ID. Preserve that record as history and
show its stale/unavailable status instead of silently replacing it with a
similarly named configuration.

## Owners and checks

`GameToolControllerKeymaps` reuses `GameToolRewasd.inspect` for bounded native
reads and the existing A20 priority routine. `DraftLibrary` saves only the
controller-keymap-drafts namespace using source/edit fingerprints and history.
Save and export refuse changed native sources, altered native inventories and
stale game-workbook/source pins. The unverified neutral reference is
`examples/controller-keymaps/vader-5-pro-reference.json`; it is not a registered
device record. `KeymapsPanel(parent, directory,
status=None)` embeds in Controller tools; `set_source(game_id, game_name,
config_path)` is its optional parent adapter, and `close()` releases ownership.

Local configuration verification, guest UI acceptance and physical/controller
gameplay acceptance are separate fields. Completing a draft does not complete
enrollment, a live Shift provider, native Autodetect or live Overlay routing.
