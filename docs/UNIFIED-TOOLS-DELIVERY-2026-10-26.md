# Unified Game Tools updates — 2026-10-26

This source checkpoint includes the Windows dropdown correction, profile-restore
idempotence, responsive headings, compact persistent header and configurable
choice-field icons. It reconciles source owner `ea2de50` with published main
`cab772a9`, preserving Mod Controls 2.2, both interface views, the controls
workflow, reWASD support, native owners and recovery.

## Latest presentation changes

Saved-page headings now reflow from their visible page width, including before
Home has ever been opened. Narrow layouts retain useful editor space. The
**Layout** choice remains distinct from the **Existing / New** interface choice.

The permanent top area combines finder/navigation/View controls. View retains
Layout, Interface, Identify UI, All tools and Show APP LAUNCHER through their
existing owners. An explicit disclosure restores expanded app controls. New
retains a View row and preserves both interfaces' drafts and original routes.

Choice/search fields have subtle locally drawn icons, kept separate from their
values and stable IDs. Clicking an icon or pressing Alt+I opens the picker.
Automatic, presets, No icon, Start/End, Save icon and Cancel remain explicit.
No icon keeps a quiet outlined slot. Opening or typing does not save a preference
or apply a game/native/Overlay value. The latest Windows correction converts
native Tcl dimensions through Tk's pixel converter before reserving icon space.

Profile restoration now recognizes an already-effective setup and avoids
inventing redundant default-group overrides or rewriting Overlay settings.
The earlier Windows `ISO_Left_Tab` startup failure has a platform-aware fix;
subsequent Windows typing/filtering, Backspace and Escape checks passed.

## Source, installation and acceptance

At this publication's read-only inventory, the installed version was
**0.27.28-preview.2**, with choice icons 0.1.1, editable lists 0.1.3,
compact header 0.1.0 and profiles 0.2.1. All 614 installed source payload hashes
were verified. The reconciled runtime code matches those payloads after Git
line-ending normalization. Historical documentation and export metadata remain
separate from runtime code and current acceptance.

The icon implementation's initial guest checks passed 13 icon, 16 editable-list
and 27 Modern UI cases. The Windows Tcl-object correction then passed 14 icon
and 16 dropdown cases; native icon rendering and a clear startup log were
confirmed, with picker interaction checks still in progress. Responsive headings had 24 GUI checks; the subsequent
compact header had 27 and an integration fixture using unchanged InterfaceViews
1.0.1. These are separate dated suites, not one combined native acceptance count.
Windows confirmed earlier dropdown behavior, responsive rendering and compact
header/menu contents. Full native submenu interaction and final icon picker/
persistence checks must retain their own current acceptance evidence; source or
guest checks alone do not establish them.

Publication performs no app start/stop, host input, game/Overlay action,
installation, rollback, profile activation or settings write. The running game
and installed version remain under their existing owners. Read-only before/after
checks cover the installation pointer and 44 scoped protected files; unexpected
concurrent changes must be reported, never silently restored.

## Backup boundary

The Drive checkpoint contains exact published source blobs and sanitized
documentation with a fresh manifest and per-file hashes. Existing checkpoints
and the earlier delivery note are retained. It excludes machine bindings,
installed manifests, user preferences/drafts, native profiles, game files/saves,
credentials, downloaded binaries and raw logs. File-only restoration and archive
integrity are distinct from full machine/game/native-profile recovery.

See [choice-field icons](CHOICE-FIELD-ICONS.md), [responsive/compact UI](RESPONSIVE-UI.md),
[editable choices](EDITABLE-CHOICE-LISTS.md), [interface views](UNIFIED-INTERFACE-VIEWS.md),
and the [previous checkpoint](UNIFIED-TOOLS-DELIVERY-2026-10-25.md).
