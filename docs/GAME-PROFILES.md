# Game profiles

Open **Game profiles** in the Unified Game Tools sidebar or original tabs.
Choose a game and **New setup uses**: Azeron / published Overlay, or reWASD /
controller or other device. Then **Save current setup** to name it.
Several named setups can be retained per game; the newest saved setup is its
automatic default, marked `(auto)`. Selecting a profile alone changes nothing.

**Activate** starts the existing Studio if needed and selects the profile's
already published Overlay group, view and context. **Deactivate** stops profile
display and automatic activation until explicitly activated again. Saved setups
remain available. Other Studio features retain their owner and process.

The page reports loaded trigger count, the Hold slot, relay configuration and
native-layer status. A running Studio process is not a ready Overlay. Its own
fresh, PID-bound receipt confirms which existing settings bytes it loaded. The
Hub resolves the settings file's actual Windows path and passes its directory
explicitly to Studio, avoiding packaged/unpackaged AppData divergence. No blank
settings file replaces a missing source. Stale receipts or changed settings show
Needs attention; no synthetic hardware events or stale native-layer replay occur.

## reWASD and other controllers

The reWASD setup stores a native `.rewasd` reference, exact SHA-256, readable
device name, optional native device/group ID and slot 1–4. It discovers native
configs in reWASD's Public Documents Profiles folder, previews supported schema
3 JSON without rewriting any fields, and saves a byte-exact private recovery
copy. Unknown native fields, Shift/activator settings, axes, deadzones, output
type and timing remain in their original bytes. New names and file selection
are drafts until **Save setup**; Cancel is inert. An unlisted game can be named
through the Game selector's Add action, without creating a second game install.

These profiles need no published Azeron map and never run Azeron validation.
Existing Azeron profile records remain valid without migration. Multiple saved
controller setups can coexist with the same game's Azeron setups; saving a
controller profile does not replace its automatic Azeron default.

**Activate** selects a controller setup and stops unrelated Azeron images. It
does not apply the native config or claim a physical controller is connected.
Open **reWASD controls** for **Review Apply to slot** or **Review Remap Off**.
Each shows the exact config/hash, device ID and affected slot or device before
the local user confirms. Apply requires the saved config and recovery bytes to
match; changed configs require **Update selected**. Remap Off remains available
when the config file is missing/changed and affects all slots of the linked
device. No reset, clear-slot, Steam setting change or driver install is exposed.
Commands use fixed supported verbs and structured argv, never imported shell
text. A successful native command is recorded as physically unverified.

For native device/group ID, use reWASD's device context menu → **Copy device ID**.
USB VID/PID and a `.rewasd` hardware-section ID are not this identifier. Leaving
it blank permits save/preview but blocks Apply and Remap Off. Do not infer a
connected device or correct output from a saved alias or cached device list.

Automatic native switching belongs to reWASD **Autodetect** and its **Background
Agent**: associate the actual gameplay executable, choose the native config and
slot, and review removal on exit and startup/restore in reWASD. The Game Tools
startup toggles do not enable native remapping. The controller controls explain
these steps and open the installed native application. No second native polling
switcher, profile activation loop or silent application is introduced. Supported
commands and ownership follow the [official command-line guide](https://www.help.rewasd.com/interface/command-line.html)
and [Autodetect guide](https://www.help.rewasd.com/basic-functions/autodetect.html).

Controller-shaped Keys / Actions / Combined Overlay generation remains a later
device-enrollment stage: verify physical geometry, extra button outputs, layers
and real game bindings first. Azeron geometry/images are never reused for an
unverified controller. Saving a default virtual Xbox 360 config alone does not
create custom mappings, new game actions or weapon/spell slots.

## Automatic operation

- **Restore active profile when Game Tools opens** restores the last activated
  setup when profiles were left enabled.
- **Use each game's saved default when that game is focused** uses the existing
  exact gameplay-executable associations. Unrelated applications do not select a
  different game's profile. A manual profile for the same game stays selected.
- **Open Unified Game Tools when I sign in to Windows** creates one fixed owned
  Startup launcher. Turning it off removes only that exact entry. Other programs
  and foreign entries remain untouched. Startup opens the existing stable app;
  it does not install updates, launch games, arm Game Input or apply game files.

The supplied **Unified Game Tools APP LAUNCHER** opens the current installed
version. **Show APP LAUNCHER** opens its app folder. Open and Install/Update
remain separate. Useful earlier launcher aliases remain valid.

## Saved scope and limits

A profile stores references to the published game map, native contract, selected
group/view/context and effective appearance fingerprint. Updating a published
map or appearance requires **Update selected** before reactivation. Changes
to source/native files and images fail closed rather than publishing stale labels.
Profile history preserves previous definitions, with exact edit guards.

Activation selects the existing display state; it does not publish images,
rewrite game bindings, activate a different Azeron native profile or apply mod /
graphics settings. Those owners keep their existing separately reviewed Apply
operations. Use the current shared native family in Azeron; the running native
software and fresh layer events are still required. No universal game-context
detection or physical hardware success is implied by saving a profile.

For DOOM, retain the accepted Combat R2 setup. Pending ergonomic review revision
9 is not activated by a runtime profile. Physical #19 Hold and #2 WEAPONS return
must be verified separately after the runtime repair; combat comfort remains
distinct from source/readiness tests.

## Source acceptance — 2026-10-25

0.27.24-preview.1 adds the controller profile option over the preserved
0.27.23 runtime profile/Studio-settings repair. The focused checks pass:
10 saved-Overlay profile cases, 11 reWASD discovery/backup/review/command cases,
11 isolated Tk cases, 2 Hub loader regressions, and 34 existing transactional
updater cases. Installed acceptance found a missing page allowlist entry that
the panel-only tests did not exercise; the exact declared Profiles UI module is
now allowed, and unknown module names remain refused. The native
reWASD 9.5 help/version commands were read without applying a config. Wide/narrow
page and controller editor screenshots were inspected in the isolated Linux
guest. No physical controller, license capability, game prompt or actual
reWASD apply/off operation is accepted by these source/guest checks.

Design follows the existing searchable selectors, short contextual editor,
shared responsive table controls and scrollable page. Device identity and native
operation details are shown in a separate review because those values belong to
one consequential native action, rather than general startup settings.
