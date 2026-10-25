# Game Tools UI workflow preview 0.2

## Pin and find controls (0.2)

The design remains a parallel preview. **Always on top** is available independently
on the main window, floating settings editor and finder. It uses the ordinary
window-manager flag, saves a preview-only preference and does not repeatedly
steal focus, install an input hook or change a game overlay. It keeps the window
above ordinary desktop windows; exclusive fullscreen and secure desktops are
outside this guarantee.

**Find settings & functions** (Ctrl+F) opens a nonmodal finder. Search scopes are
This page, Selected game and All connected games. Ctrl+Shift+F starts at Selected
game. Advanced filters select Type and Relevant to (Graphics, Gameplay, Camera,
Files, Programs, Profiles, Reports or Interface). Hiding advanced filters resets
their restrictions. Empty search browses controls; unavailable connections and
partial result limits are shown. The index reads at most 64 connected installations
and 32 typed fields per installation, plus declared preview navigation/functions
and known location metadata. It does not recursively scan personal files or index
the internal menus of external programs.

Search accepts exact names/IDs, common English and Hebrew purpose terms and close
spellings. For example, “more abilities at the same time” finds Multi Equip Skills,
“camera” finds FOV controls, and “Vortex” finds file preparation. Related-purpose
matches are explained. This is a curated local vocabulary, not an AI model call
or a compatibility diagnosis. Experimental controls retain their existing labels
and limits; finding DLAA does not establish working SR or DLSS 5.

Results show the page/section, game/installation, control type and relevant topic.
Selecting **Reveal control** restores a hidden card, navigates to the correct
context and focuses its widget. It never invokes Apply, exports, launches programs
or toggles settings. Switching game contexts preserves their separate drafts.
Applied values in results are an index snapshot; refresh the index for new values.

Updates can reuse the existing separate review-data folder with `--review-data`.
Existing preview drafts, profiles, exports and view choices are retained. The
old version and shortcut recovery are preserved; the production pointer is not
switched. Windows launcher paths are read back after delivery. Actual window
stacking depends on the destination window manager and requires native observation.

This is a separate parallel review version, requested on 2026-10-25. The current
Mod Controls and Unified Game Tools source, launchers and settings stay in place.
The independent unmerged library candidate is not adopted by this preview.

Two convenient entries open the same preview at different pages:

- **Mod Controls UI Preview APP LAUNCHER** starts with game mod settings.
- **Game Tools UI Preview APP LAUNCHER** starts with app files and recovery.

Both named launchers are included in the preview folder and have matching
Desktop shortcuts. Compare & feedback can locate the current app's launchers
and the preview folder. Opening is separate from installing or updating.
The two entries keep separate view/draft files while sharing the preview's
saved profile library and export folder.

## Shared UI patterns

The game and installation selectors retain stable IDs and combine selection with
search/entry. Typing filters; Enter or a selected item commits; Escape restores
the last committed choice. A common Locations & files component is reused across
Mod Controls, program connections, profiles/overlays, reports/diagnostics and
app files/recovery. Open location, Open selected item, Copy path and Refresh files
have distinct effects. Additional folders are explicit private preview links.

Refresh files reads a bounded, nonrecursive file listing and shows additions,
changes, removals and observation time. It refreshes applied settings on the Mod
Controls page while retaining draft edits. It never starts a benchmark, capture,
game, input experiment or automatic deployment.

Sections have **× Hide** and a page-level **Show/Hide sections** menu. Hiding a
section preserves its values and does not disable a mod or feature. Graphics,
gameplay and camera/render groups can be shown independently. Floating settings
editors share the selected installation's draft. Theme, zoom, layout, feedback
and saved review profiles live in a separate private preview data folder.

## Selected program and file handoff

Destinations follow the current page: Vortex, Mod Organizer 2 or RHI for mods;
Azeron/reWASD/RTSS for profiles; spreadsheet/OBS choices for reports; and another
installed app or Portable folder where relevant. Locate program stores a
preview-only connection to an existing program. Selecting a target does not
prepare files or launch the program. Prepare files, Open prepared folder and
Open selected program are separate commands.

Mod handoffs preserve accepted original archives where the reviewed adapter has
them, current settings, a separately labeled draft profile and a hash manifest.
They use existing safe-copy and game-control services; there is no second mod
installer. The outer ZIP is transport, not an installable mod. Native game
support, loader choices, deployment and manager profile migration remain with
their original owners. A selected saved profile/report can be copied with an
explicit native-import-unsupported label; program binaries and connection files
are not exported through that path.

Saved parallel profiles do not overwrite current profiles. Explicit Apply calls
the existing Mod Controls service after preview and local confirmation, with
its original revision, idle, ownership, backup and readback guards. Opening,
refreshing, hiding sections, saving review profiles and preparing exports do not
apply settings. Real game Apply is not exercised by UI development tests.

## Comparison and adoption

Compare & feedback saves local notes and a verdict such as Like this direction
or Needs changes. It does not send a message, publish feedback, replace the main
app or adopt the design. The user will decide whether to adopt the changes.

The preview pins an exact verified incumbent source package and adds only its
review modules. It does not switch the current installed pointer, stop Studio,
replace dirty source owners or migrate native profiles. Source and per-file
hashes are verified at entry. Private machine bindings remain outside Git and
OneDrive; source-only review publication must remain separate from adoption.

GUI development acceptance belongs in the isolated Linux lab. Windows Desktop
launcher and real local read acceptance are separate. Tests use fictional
installations for Apply and export behavior; they do not establish actual game
stability, manager import, graphics or neural-rendering support.
