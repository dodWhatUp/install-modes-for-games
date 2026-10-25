# No Rest for the Wicked gameplay mod controls

Nonresident file controls for a privately prepared Steam installation. Opening the
window reads state. **Main setup On**, **All Mods Off**, and **Apply selection**
perform hash-owned file transactions while the game is closed. The window can be
closed during play. The installed Unified Game Tools app is not replaced.

`switcher.py` owns the file transactions and readback. `mod_panel.py` provides the
compact native interface. The trusted, machine-local `deployment.json` names the
selected installation, frozen original sources and hashes. It is not an arbitrary
downloaded profile or executable support pack. Paths, original archives, saves,
configuration and recovery remain private and outside Git and OneDrive.

Each existing checkbox row includes compact **GitHub**, **Nexus**, **Preview** and
**Options** buttons. Source buttons open verified pages and are disabled where
no matching page is verified. Preview shows a description and an offline author
image gallery, with Fit, 100%, panning, captions, attribution and original-image
access. Options shows documented preferences and file access. Both are reusable
nonmodal windows placed beside the current pointer on every opening, clamped to
the work area. Closing retains the window's draft while the app stays open. The
separate mod selector is removed. Row heights and main window dimensions remain.

`mod_details.json` contains reviewed descriptive metadata and source URLs.
Copyrighted images are cached only in the private delivered app's `media/`
directory, outside Git. The app does not fetch images on opening. Rune Details has
verified GitHub and Nexus pages; Build Liberator and Wicked Menu have verified
Nexus pages; the loader uses its official GitHub release. Missing-source buttons
are explained locally rather than pointing to unrelated repositories or games.

`mod_options.py` edits documented Build Liberator rune/gem switches, Rune Details
display switches/mode, and Wicked Menu's menu key. **Save options** is separate
from enabling plugins and preserves pending main checkbox choices. Opening,
editing a draft or reloading never writes settings. Save requires a closed,
unchanged game, checks for stale edits, preserves unrelated TOML lines, and retains
the previous file before atomic readback. The loader exposes information/files.

The loader proxy activates last and deactivates first. Unknown or changed owned
files block changes. A game update blocks enabling pending compatibility review;
exact owned files can still be disabled. Sources, settings, saves and recovery are
preserved. Disabling a plugin does not reverse changes it already saved to gear.
The controller never starts a game, sends input, captures gameplay or restores saves.

The initial selected setup is MelonLoader 0.7.3, Build Liberator 1.0.0, Rune Details
1.1.0 and Wicked Menu 1.0-0225. A private .NET 6.0.36 runtime is placed in the
loader's documented portable runtime directory. Wicked Menu uses F12 through its
verified `WickedMenu / MenuHotkey` setting. Initial game assembly generation and
actual mod effects remain untested until the first authorized game check.

The delivered package and Desktop shortcut both use **No Rest for the Wicked Mods
APP LAUNCHER**. **Files & tools > Show APP LAUNCHER** finds it; the same menu opens
settings, loader logs and the use/verification guide. Opening the app does not
install, update or apply anything. Installation/update information remains separate.

Validation on 2026-10-25: nine Windows disposable-file checks passed, including
game-open refusal, stale state, changed-file protection, exact recovery after a
simulated write failure and disabling after a game update. The initial UI passed
an isolated Linux Tk preview/layout check. Eight actual installed-file on/off and
individual-plugin round trips passed. The normal Desktop shortcut launch and
Windows window were observed; current states and controls were visually readable.
Settings, saves and original root game files were preserved. No game was launched.

Run `python -m unittest -v test_switcher` for disposable-file checks. The real Tk
check runs under an isolated X display, for example `xvfb-run -a python3 -m unittest
-v test_switcher`. Never point fixtures at a real installation.

Version 1.2 validation: 25 isolated checks pass across the switching,
preference and GUI suites. The original UI snapshot is transferred as
`baseline_panel.py` only to the private lab. Fresh Tk roots at scaling 1.0, 1.5 and
2.0, at both 870x525 and 720x490, match all original row heights (25, 30 and 36
pixels respectively); inline buttons fit. Exact per-row URLs, reusable nonmodal
windows, draft retention and saving one mod without applying pending plugin
choices are exercised. New checks cover both source links, disabled-source state,
gallery navigation/zoom/missing assets, pointer placement and repositioning,
negative-coordinate placement arithmetic, screen-edge bounds and full footer
visibility at larger font scales. Real author images loaded and rendered in a
separate isolated preview. The footer was corrected after visual review found
clipping. This does not certify physical Windows multi-monitor/DPI behavior or
gameplay. Run `test_options`/`test_floating` headlessly and `test_inline_gui` under
the isolated display.

Author sources:

- [MelonLoader 0.7.3](https://github.com/LavaGang/MelonLoader/releases/tag/v0.7.3)
- [Build Liberator](https://www.nexusmods.com/norestforthewicked/mods/18)
- [Rune Details](https://www.nexusmods.com/norestforthewicked/mods/107)
- [Wicked Menu](https://www.nexusmods.com/norestforthewicked/mods/41)
