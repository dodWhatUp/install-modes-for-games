# Editable search and choice fields

Click the text area or arrow of an editable choice field to show its list.
The caret remains in the field: type or edit while filtered choices stay open.
Use Up/Down and Enter, or click a row, to choose it. Escape restores the prior
value; Tab or clicking outside closes the list. Opening or typing does not
create, save or apply a value. Existing explicit Add and Save actions remain.
Fixed-choice-only controls and ordinary text fields retain their purpose.

`GameToolEditableLists` supplies the shared Tk presentation adapter. CompactUI
Selectors, scrollable workspaces and toolbars install it once per application;
later dialogs and lazily created controls are covered through Tk mapping events.
It attaches to existing widgets and keeps their values, validation, stable IDs,
bindings and selection callbacks. The open suggestion window does not grab
keyboard/mouse focus. Only one list is open per application. No OS-wide hook,
configuration writer, input injection, game operation or native remapper exists.

Standalone authored Tk applications can call `install(root)`, or their existing
launcher can run `GameToolEditableLists.py --app existing_app.py` followed by the
app's original arguments. That adapter installs the behavior as the app creates
its root, without editing the native app services or the Python installation.
Delivered standalone folders include the same shared module bytes, with the
canonical script retained as the source owner. No unrelated installed software
or preserved archival app version is patched.

Overlay Studio's editable native ComboBoxes retain Windows' own edit/search
and selection behavior. Clicking the edit area opens the existing native list
through app-local window messages. Fixed lists, hotkeys, Hold/momentary layers,
map switching, profile contents and save/apply ownership remain unchanged.

This interaction is the standing preference in the maintained design guide
and the user's local instruction file. Per-machine deployment, exact baseline
hashes, backups and installed/GUI acceptance receipts remain private.

The 0.1.1 build failed during Windows Tk construction because ISO_Left_Tab is
an X11 keysym. Version 0.1.2 binds Tab/Shift-Tab everywhere and the additional
ISO_Left_Tab event only on X11. Sixteen isolated cases passed; installation and
native Windows acceptance of this correction remain pending after a human
Escape stop. A partially built window from 0.1.1 does not indicate lost profiles.
