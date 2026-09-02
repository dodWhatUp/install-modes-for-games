# Reversible and Quick-Switch Profiles

The goal is fast switching without losing provenance or allowing incompatible hooks to coexist.

## Recommended local layout

Keep proprietary binaries outside Git in a private state directory:

```text
<private-state>\<game>\
├─ baseline-stock\
├─ snapshots\<timestamp>-<state>\
├─ profiles\
│  ├─ stock\manifest.json
│  ├─ graphics-safe\manifest.json
│  └─ experimental-neural\manifest.json
└─ logs\
```

Each manifest records source URL, release/version, SHA-256, destination relative path, stock/add/replace status, dependencies, conflicts, configuration deltas, and restore source. The public repository stores only sanitized example manifests and scripts—never the binaries.

Start from [the example manifest](../templates/PROFILE-MANIFEST.example.json) and run the read-only [manifest validator](../scripts/Test-ModProfileManifest.ps1) before writing a game-specific switch script. A mutating switcher should be generated only after exact profile ownership and baseline restore files are known.

## Safe switch algorithm

1. Refuse to continue if the game, launcher, helper, store client that owns edited settings, or shader compiler is running.
2. Validate the exact game root and expected executable hash/name.
3. Snapshot the live files that differ from the target profile.
4. Stage target files in a temporary directory on the same volume and verify hashes.
5. Remove only files owned by the current profile; restore replaced stock files from the verified baseline.
6. Move the staged profile into place, then apply minimal configuration-key edits.
7. Scan for duplicate proxy names and incompatible owners.
8. Write a switch report and provide an immediate rollback command.

Do not swap DLLs while they are loaded. Do not keep disabled copies under names that a loader may still discover. A “stock” profile must also restore launch options, environment variables, global Vulkan registration, driver overrides, and user configuration when those were changed.

## Configuration strategy

- Store only changed keys and their original values.
- Merge INI/VDF/JSON carefully; do not replace a complete user file for one setting.
- Separate general profiles from hardware-specific and game-build-specific overlays.
- Use mutually exclusive feature ownership labels such as `fg-owner=native`, `neural-owner=feeder`, and `hdr-owner=game` so a preflight check can reject an unsafe combination.
