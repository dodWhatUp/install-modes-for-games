# Choice-field icons

Choice/search fields have a small neutral icon inside the field, separate from
their text and IDs. Click the icon, or focus the field and press Alt+I, to open
the picker. Choose a preset, Automatic or No icon, choose Start or End, then
Save icon. Cancel and Escape discard the icon draft. No icon retains a quiet
outlined add slot. Short fixed-choice fields omit the decoration to retain space.

Defaults describe the field: search, game, profile, device, folder, layers,
image, settings and safety. The picker also offers a favorite star. Icons are
drawn locally and have no downloaded image or emoji-font dependency. Native
dropdown arrows, editable text, filtering, selection events, validation and
explicit Add/Save actions retain their original owners. Padding clicks retain
the editable suggestion list instead of posting a grabbing native popdown.

For a known selected choice, customization follows its stable Selector ID;
duplicate readable names remain separate and renaming keeps its icon. Empty or
uncommitted text customizes the field's empty-entry slot. Plain native choices
without IDs use their exact value. The original field value is never prefixed
with icon characters. Saving is rejected if the selected target changed while
the picker was open.

The Unified app uses a separate `ui-choice-icons.json` in its existing data
directory. Other maintained Tk entry points use the private local GameTools
icon preference file. No preference file is created on startup. Keys are scoped
hashes rather than copied names, IDs or paths. Malformed/future formats and
concurrent changes are retained. Only Save icon writes this presentation file;
game bindings, native profiles, Overlay and mod settings are outside its owner.

Owners can call `GameToolChoiceIcons.context(widget, stable_field_id, role)` for
stable semantic identity. Hub search and the game/profile selectors do so. Other
fields use existing component IDs, public labels and their owning view, falling
back to their widget path when no semantic owner is available. Generic unlabeled
fields therefore cannot promise icon retention through a structural redesign.

Guest checks cover icon editing/cancellation, duplicate IDs and rename retention,
empty slots, both positions, small fields, style changes, readonly behavior,
late-created shared variables, stale selections, preference conflicts and the
unchanged editable-dropdown/Modern UI suites. Windows delivery remains a
separate acceptance check; it must not interrupt an active game or native owner.

The 0.27.28-preview.2 fix normalizes Windows Tcl pixel objects and dimensional
padding through Tk's pixel converter before reserving icon space. Direct Python
integer conversion does not support those native objects.
