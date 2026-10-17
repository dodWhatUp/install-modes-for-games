# Independent component switching

`scripts/Manage-ModComponents.ps1` manages explicit file ownership for small mod components.
It can disable an earlier independent component while retaining later components. It never
restores a whole game tree or recursively deletes a target directory. This complements a
game-aware mod manager; two managers must not deploy into the same owned paths.

The script is for Windows PowerShell 5.1 or PowerShell 7 on Windows. Keep its private state,
downloaded packages, snapshots and root mappings outside this repository. They may contain
proprietary game/configuration bytes and private paths. None belong in Git.

## Package and root mapping

Create a private `roots.json` with absolute existing directories:

```json
{
  "game": "D:\\Games\\ExampleGame",
  "user": "C:\\Users\\Example\\AppData\\Local\\ExampleGame"
}
```

Use narrow roots. Roots cannot overlap each other, the state directory, or the repository.
Reparse points (including junctions and symlinks), drive roots and UNC paths are rejected.

Each separately switchable package has `component.json` and its listed payload files:

```json
{
  "schemaVersion": 1,
  "id": "example-mod-1.0",
  "version": "1.0",
  "source": "https://example.org/original-release",
  "dependencies": ["example-framework-2.0"],
  "requiredStoppedProcesses": ["ExampleGame", "ExampleLauncher"],
  "files": [
    {
      "root": "game",
      "path": "mods/example/config.ini",
      "payload": "payload/mods/example/config.ini"
    }
  ],
  "capture": [
    {"root": "user", "path": "UserSettings.json"}
  ]
}
```

`files` maps exact destination files; archives are extracted and reviewed separately.
The script does not execute installers or package scripts. `capture` preserves additional
configuration as snapshot context without editing it or claiming ownership. Nonexistent
capture files are recorded as absent. Use file roots/captures for launch configuration and
relevant external settings. Driver profiles, registry values and other non-file settings
still need their own reviewed export/restore procedure.

IDs use lowercase letters, digits, dots, underscores and dashes. IDs are immutable after
import: give a new version a new ID. Dependencies name imported IDs and must already be
enabled before this component can be enabled. Requirements already satisfied by unmanaged
software must be verified separately; do not invent a managed dependency.

## Commands

In PowerShell, use a common parameter map with actual private paths:

```powershell
$manager = 'C:\path\to\repository\scripts\Manage-ModComponents.ps1'
$common = @{
    StateRoot = 'D:\Modding\ExampleGame\component-state'
    RootsFile = 'D:\Modding\ExampleGame\roots.json'
}
& $manager @common -Command Import -PackagePath 'D:\Modding\ExampleGame\packages\example-mod-1.0'
& $manager @common -Command Status
& $manager @common -Command Plan -ComponentId example-mod-1.0 -Operation Enable
& $manager @common -Command Enable -ComponentId example-mod-1.0
& $manager @common -Command Disable -ComponentId example-mod-1.0
& $manager @common -Command Snapshot
& $manager @common -Command CaptureCurrent -ComponentId example-mod-1.0
```

Import only copies reviewed payload bytes into the private content-addressed store and
records metadata. It does not change game files. `Status` lists activation and drift;
`Plan` verifies dependencies, conflicts, payload hashes and process blockers, then reports
exact additions/replacements/removals without target writes.

Enable/Disable require the game, Steam, supported launchers, mod managers and known shader
helpers to be closed. Package process names extend the guard. Processes whose executable
is inside a managed root also block changes. Do not launch those processes during a switch.
The script does not stop them or launch the game.

Immediately before a mutation the script snapshots the affected files and capture entries,
including existence, SHA-256, length, timestamp, file/product versions, source and component
version. Every successful mutation produces a verified after snapshot. A SHA-256 blob is
stored once even if repeated snapshots reference it. This avoids full game-directory copies.
The first observed baseline per managed file remains separately recorded in `state.json`;
it is **not** a claim that that baseline was gameplay-tested. Existing known-good snapshots
from other work remain necessary and are never replaced.

Disable restores that component's pre-enable content, or removes only the exact files it
added. Unrelated components and files remain. Empty directories and generated files not
listed in the package remain deliberately untouched. Timestamps are restored where recorded;
ACLs/alternate data streams and arbitrary filesystem metadata are not backed up/restored.
This is a content manager, not a full-volume backup tool.

## Conflicts, personal edits and recovery

- Active overlap is rejected, including identical bytes. Shared frameworks should have one
  owner; dependent packages should omit their duplicates. Two modifications to the same
  configuration require a reviewed combined configuration component, not competing files.
- Enabled dependencies cannot be disabled while an enabled dependent requires them.
- If owned files change externally, Disable refuses to overwrite/remove them and snapshots
  the current bytes. Status identifies the drift. Explicit `CaptureCurrent` accepts the
  current owned files as that component's next enabled payload, records a local revision,
  and preserves both the previous payload and original pre-enable rollback baseline. It
  requires an enabled component, refuses missing owned files, and never writes game files.
  Use it only when those edits are intentional; accepting modified DLLs/scripts is also
  accepting their contents for future activation. Disable still restores the original
  pre-enable baseline; re-enable reinstalls the captured choices. There is no force-overwrite flag.
- Inactive targets may have changed since the last activation. A new Enable snapshots that
  current state and will restore it on its corresponding Disable.
- A write failure rolls back only the attempted component's changes, provided their bytes
  still match that attempt. Concurrent external edits are preserved and block rollback.
- An interruption leaves `pending.json`; further writes are blocked. Inspect `Status`, close
  processes, then run `-Command Recover`. Recovery snapshots current bytes, accepts only
  the recorded before/after states, restores the prior files and state, and keeps the journal
  if anything remains ambiguous. Unknown drift is never silently discarded.

State and target writes use a process lock and atomic per-file replacement. This prevents
two controller instances from competing; it cannot make multi-file changes one filesystem
transaction or prevent another program from racing a switch. The journal supplies explicit
recovery for partial changes. Keep the game/store closed throughout the operation.

`Snapshot` preserves current owned files and capture entries without changing activation or
accepting drift. With `-ComponentId`, it limits the component scope. Optional `-SnapshotFiles`
accepts a private JSON file containing an array of additional `{ "root": "user", "path":
"UserSettings.json" }` entries. This is suitable for mutable settings that should survive
mod toggles. Keep such settings in `capture` rather than `files` when the mod does not need
to own/restore their entire content. Snapshot can also preserve evidence while an interrupted
transaction awaits recovery.

A standalone controller copy may live in a separate private `tools` folder. Its state must
be a different directory and cannot contain the controller itself. The source-checkout
version additionally prevents state/target paths from overlapping this repository.

## Isolated verification

```powershell
& 'C:\path\to\repository\scripts\tests\Test-ModComponents.ps1'
```

The fixture suite covers independent out-of-order removal, original-file restoration,
external context snapshots, preserved drift, ownership/dependency guards, traversal/ADS/
reserved-name rejection, junction escape prevention, a late locked-file failure and rollback,
corrupt CAS refusal, explicit local-revision capture, standalone snapshots and
interrupted-transaction recovery. Only process inventory is mocked
in a private fixture copy so an active Steam session does not block isolated filesystem tests.
A separate assertion executes the production process guard. The small fixture is retained
under the system temp directory as local test evidence. No live game files are touched.
