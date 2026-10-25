# Shadow of War file controls

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
