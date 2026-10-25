# Shadow of War file controls

## 1.2 - Automatic settings discovery and setup recovery

The controller now finds and validates the existing `render.cfg` itself. It
checks the saved location, Windows local app-data roots and the exact game's
redirected package-cache locations. Windows file handles resolve virtual paths
to their physical files, so Desktop and packaged-app launches use the same file.
Search is bounded to those known locations, not a recursive drive/profile scan.

A valid saved selection is retained. A unique valid candidate rebuilds the local
`control-panel-paths.json` automatically, preserving previous mapping bytes and
unknown fields. Files must have unambiguous, finite native render dimensions and
HDR settings. Different conflicting candidates open a choice window instead of
being selected by modification time. Invalid/missing settings open startup
recovery with **Find automatically**, **Use selected file** and **Choose render.cfg**.
If no native configuration exists yet, **Open game in Steam** provides the game's
own first-setup route; the controller does not fabricate a native configuration.

Use **Files & tools > Find / repair settings location...** for an explicit check.
Refresh also rediscovers a vanished settings location. Repairs preserve pending
preview edits and update stale-state fingerprints; unavailable settings block
Apply. Native configuration files stay in place and retain their original bytes.

Validation: 27 disposable Windows file checks and 57 real Tk guest checks passed.
The actual Windows Desktop launch was also tested with its saved location mapping
absent: version 1.2 found the existing redirected file, rebuilt its own mapping
and displayed the current settings. The native configuration and save hashes
remained unchanged. Twelve source files matched the tested guest bytes; the
task-owned helper and VM were stopped cleanly. No game launch or real Apply was
part of this acceptance. The earlier fourteen-check path fix is historical.

## 1.1 - Mod folders, author pages and floating editors

**Mods & folders** opens one searchable selector for the installed/retained mods
and official texture DLC. Each entry shows its source, file location, configured
state and relevant mod/config/download folders. **Open folder** opens an existing
location; it never creates a missing game folder. **Read author page here** shows
the pinned author's text for the three gameplay plugins and loader inside the
app. **Open author page** opens the full source website in the default browser.
This is a text reader, not an embedded authenticated web browser.

The three gameplay rows have **Settings...** buttons for nonmodal floating
editors; the shared loader also has an editor in the mod browser. They share the
main preview, retain that preview on close, validate original plugin bounds and
offer optional **Keep this window on top**. **Apply this mod** applies only that
mod's supported fields and retains unrelated pending edits. **Save profile file**
uses the existing main profile name and persistent JSON format. These are offline
file controls; they do not inject an overlay or promise live in-game changes.

**Manager transfer...** separates **Prepare manager files**, **Open export folder**,
**Open package ZIP**, the readable handoff guide and **Open manager**. The latter
uses a detected or explicitly selected installed executable. It does not install
a manager. The ZIP is a transport container: extract it and import the four
original mod archives individually after reviewing loader and file ownership.
Preparation reads applied files, not pending edits; it does not deploy, purge,
edit a manager database or retire the existing controller. Official textures,
graphics binaries, proprietary game files and saves are excluded.

Validation: fifteen Windows disposable-file checks, sixteen existing Tk checks
and twenty-five new real-widget checks passed. The GUI suites ran in the private
Linux Xvfb lab, including compact layouts, per-mod Apply isolation, readable author
information and separate export/open actions. Native Windows Desktop opening and
the mod browser were observed separately. Actual manager import/deployment and
gameplay were not tested. Machine bindings, original archives, exports, exact
settings/save hashes and recovery remain private.

An optional native Tk front end for the reviewed local profile controller. This
extends the existing game-specific switcher, without rebuilding or modifying the
installed Unified Game Tools app. The existing metadata support pack stays under
its existing owner. Canonical authored source is here; machine paths, manifests,
source archives, saves and deployment/recovery remain private.

The interface separates **applied files**, **pending edits**, **saved profile
files** and **view preferences**. Typing or loading a profile does not change the
game. Apply holds the existing controller lease, checks ownership and stale
state, takes recovery, writes only selected values and verifies readback. Failed
writes unwind recorded changes. An open game/store/RHI blocks Apply. The window
does not need to remain running during play.

Controls cover graphics/loader/plugin on/off, Elven Speed duration and focus
rates, FOV values, multi-equip modifier/hold-toggle/sound, and native render size.
Bounds follow the original plugin menus: duration 0–10, regeneration −1–1, FOV
40–70. Experimental Luma/DLAA/NR remain separate from the recommended profile;
their recorded shutdown failure stays visible when those controls are opened.
No SR/FG capability is fabricated.

Profiles are ordinary `saved-profiles/*.json`; Apply also retains native INIs
and `last-applied-profile.json`. View flags use their own JSON. Existing menus,
original binary ownership checks, source pins and rollback snapshots are reused.
Game saves are backed up by the existing engine and never automatically restored.

**Vortex handoff** copies four pinned original gameplay archives, current gameplay
INIs, a profile and a manifest into a new private export folder. It does not deploy,
install Vortex, edit its database, retire the local controller or claim a tested
import. No proprietary game EXE/Bink runtime, official textures or save is included.
Keep one DLL loader and one writer per file when an actual handover is reviewed.
Graphics stay under RHI/reviewed local profiles.

Sources reviewed 2026-10-25:

- [Shadow of War Vortex extension](https://www.nexusmods.com/site/mods/375): Steam/GOG
  support and loader-install behavior; exact installed extension/import acceptance
  is separate.
- [Vortex external-change handling](https://github.com/Nexus-Mods/Vortex/blob/master/docs/mod-management/EXTERNAL-CHANGES.md):
  deployment links and why another writer must be reconciled.
- [Original gameplay source](https://github.com/ReaperAnon/Shadow-Of-War-Mods/tree/88aa2d6058fe7287f5b9387f1995c8522e0447a1):
  real settings, bounds and modifier semantics.

`test_controls.py` uses disposable Windows files and the same controller code,
with only its process preflight replaced by an explicit fixture-root assertion.
It covers ownership/dependencies, stale changes, open-process refusal, rollback,
file persistence and export pins. `test_gui.py` exercises real Tk widgets and
renders in the accepted Linux lab's private Xvfb display. The demo service cannot
modify a real game. Guest checks do not establish physical game/GPU/HDR behavior.

For development, run `python mod_panel.py --demo --workspace <new-fixture-folder>`.
For a reviewed installation, launch with the existing private controller workspace;
that workspace contains trusted Python code and must not be selected from an
untrusted downloaded profile. Imported profile values cannot name executable code.

## APP LAUNCHER

The package includes **Shadow of War Mods APP LAUNCHER.cmd**. The Desktop shortcut
uses the same visible name. **Files & tools > Show APP LAUNCHER** opens its folder.
Existing windows receive the new menu item when next opened normally.

For a reviewed Windows installation, the installer writes two private one-line
bindings beside the included launcher: `launcher-pythonw.txt` contains the full
existing `pythonw.exe` path, and `launcher-workspace.txt` contains the reviewed
controller workspace. The workspace must contain `graphics-profiles.json` and the
trusted controller. These local bindings are not distributed as public source.
Double-clicking the configured launcher opens the same UI without applying edits.
The root workspace also includes a named entry; the older Manage entry forwards
to it. See the [standing launcher contract](../../docs/APP-LAUNCHERS.md).

### Native settings location (1.0.1)

Setup can pin the existing reviewed native settings file using the private
workspace file `control-panel-paths.json`, with `schema: 1` and an absolute
`native_config_path` pointing to `render.cfg`. This is a trusted installation
binding, separate from imported profiles. Packaged Windows apps may see a
redirected app-data file while an Explorer-launched app sees the normal folder;
resolve the actual existing file during setup and verify from Explorer itself.
Do not create a blank render configuration or move game settings to hide a
missing-file error. Version 1.2 supersedes the original environment-only fallback
with validated automatic discovery and the recovery window described above.

The bound file and its path are included in stale-state checks. Apply also keeps
an exact native-file recovery copy independent of the legacy engine's app-data
view. Reopen the controller after changing a path binding. Fourteen disposable
file tests cover the environment mismatch, bound-file recovery, stale binding
refusal and the existing transactions. Desktop opening was observed separately;
no real profile Apply was performed for the launcher repair.
