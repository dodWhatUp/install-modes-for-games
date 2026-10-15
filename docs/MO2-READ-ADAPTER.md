# Mod Organizer 2 read-only adapter — 0.28.0-preview.1

**Status:** product commit `c0809f7ac99a776390e131859991105c2f4c88f4` passed bounded synthetic Windows, source-package and external-client acceptance; not merged, installed or connected to a real MO2 profile.

**Canonical base:** `290bea7983ccca50073c5f45ce44337cacafc32a`

## Purpose

This slice adds one bounded **read-only** Mod Organizer 2 adapter to the adopted
Game Tools planning architecture. It does not add another registry, approval
controller, journal, queue or MCP registration tool. MO2 uses the existing
`GameToolInstances` owner and the existing modern tools:

- `game_tools_instances`
- `game_tools_instance_inspect`
- `game_tools_plan_goal`
- `game_tools_conflicts`

Registration remains an explicit local operator action through
`Game-Instances.py register-mo2 --confirm`. AI clients receive only an opaque
`instance_id`; they cannot supply a game, manager or profile path.

## Ownership and record compatibility

| Concern | Owner / boundary |
|---|---|
| Game/support scope | `GameToolGameWorkspaces` and the reviewed support pack |
| Opaque installation identity | `GameToolInstances` |
| UMM legacy records | Existing schema-1 records remain readable and are still written by `register` |
| MO2 binding | Additive schema-2 record in the same private registry |
| MO2 declaration read | `GameToolMO2Read` |
| Goal DAG | `GameToolPlanning` |
| Approval, execution and receipts | Existing local owners; unchanged and not widened |

A schema-2 MO2 record privately binds one exact game directory, MO2 manager root
and MO2 profile root. Public results contain the profile label and revisions but
never those paths. Two distinct profiles may be registered for the same game and
manager. The same physical profile cannot acquire two owners, including Windows
case or 8.3 aliases.

## Accepted local registration

The local route requires:

```text
Game-Instances.py --data-dir <PRIVATE_DATA> register-mo2 \
  --instance-id <OPAQUE_ID> \
  --game-id skyrim-special-edition \
  --game-dir <EXACT_GAME_DIRECTORY> \
  --manager-root <EXACT_MO2_DIRECTORY> \
  --profile-root <EXACT_PROFILE_DIRECTORY> \
  --profile <PUBLIC_LABEL> \
  --confirm
```

Before writing registry metadata, the route verifies the reviewed game marker,
manager marker and required profile declaration. It then performs a complete
read-only inspection and repeats the game-marker check. A refusal leaves no new
record. Registration writes only the private instance record and registry lock;
it does not write the game, MO2 installation, profile, mods, plugins, saves,
input, graphics or system configuration.

## Read contract

The adapter reads only the exact registered scope:

- reviewed game executable marker metadata;
- `ModOrganizer.exe` or `ModOrganizer.ini` presence;
- required `profile/modlist.txt`;
- optional `profile/plugins.txt`;
- presence only of `profile/loadorder.txt` and `ModOrganizer.ini`.

It does **not** read the MO2 process, IPC/API, virtual file system, deployment
state, overwrite directory, downloads, archives, plugin binaries, generated game
folder, Nexus credentials or arbitrary discovered profiles. Selected files and
markers are re-read; drift returns `SOURCE_CHANGED` without automatic retry.

The marker interpretation follows exact upstream MO2 source at
[`ModOrganizer2/modorganizer@4ba22f0d…/src/profile.cpp`](https://github.com/ModOrganizer2/modorganizer/blob/4ba22f0d8b6f9e08e44008b8395cd774551b4ebe/src/profile.cpp):

| `modlist.txt` marker | Public meaning |
|---|---|
| `+` | `DECLARED_ENABLED` |
| `-` | `DECLARED_DISABLED` |
| `*` | `DECLARED_FOREIGN_ENABLED` |
| no recognized marker | `UNCLASSIFIED` |

In `plugins.txt`, `*` is `DECLARED_ENABLED`; an unmarked entry is
`DECLARED_DISABLED`. These are file declarations, not proof of effective virtual
deployment, conflict winners, overwrite order, runtime loading or gameplay.
Raw file order is preserved and labeled only as raw declaration order.

## Privacy and result identity

Public results are screened for absolute Windows, POSIX and UNC paths, root-
relative paths, `file:` URIs, home/environment expansions, embedded URL
credentials and common credential candidates. A private-looking mod/plugin name
is replaced with:

```text
[redacted-local-entry]
mo2mod:redacted-0000
```

The ordinal token is not derived from the hidden value. A redacted list is
`complete=false` and includes `redacted_name_count` plus a warning.

A raw source SHA-256 is public only when that source contains no redacted name
and every omitted comment is the exact reviewed Mod Organizer generated header.
Any other unpublished comment also produces `sha256: null` and
`raw_hash_exposed: false`; the comment itself is never returned. The public
`state_revision` still changes on private same-length source changes by using
HMAC-SHA256 keyed by the private instance nonce over public and private readback
material. This allows stale-result detection without publishing a reusable
fingerprint of hidden names or comments.

## Planning and AI boundary

- `inspect-installed` may be `READY_FOR_READS` for an explicitly registered MO2 instance.
- The inventory node is owned by `MO2ReadAdapter`.
- `game_tools_instance_inspect` returns the same typed result envelope and no new public tool is added.
- MO2 planned-versus-installed comparison is **not** accepted in this slice and returns `ADAPTER_COMPARISON_PENDING`.
- An observed ownership/conflict graph with a MO2 instance is likewise refused pending a separate comparison contract.
- UMM planned-versus-observed behavior remains unchanged.
- Legacy MCP tool names and payloads remain unchanged.
- No `register`, `path`, `game_dir`, `manager_root` or `profile_root` argument is exposed through MCP.

## Packaging and update integrity

The combined source exporter, Preview launcher and guarded updater require the
MO2 module, schema, local CLI, instance/planning owners and goal-plan schema as a
coherent set. The manifest must declare exact versions for `instances`,
`planning` and `mo2_read`, and those labels must match the exact source bytes.
A partial package or a mismatched component label is refused before staging.

Cross-platform host pins hash UTF-8 source after normalizing only `CRLF`/`CR`
to `LF`. This preserves exact source content identity while avoiding a false
difference caused solely by Git checkout line endings; a content change still
invalidates the pin. The PowerShell exporter computes source and archive SHA-256
through its own bounded byte helper and does not depend on the optional
`Get-FileHash` cmdlet.

Current candidate versions:

```text
Unified Game Tools     0.28.0-preview.1
Game Workspaces        0.2.2
Instance Registry      0.2.0
Planning               0.2.0
MO2 Read Adapter       0.2.0
Unified Updater        0.2.1
Keybinds               0.2.0-preview.1
```

## Current validation boundary

The exact product commit `c0809f7ac99a776390e131859991105c2f4c88f4` passed the separate
[Windows/source-package/external-stdio acceptance](MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.md):
13/13 suites, 344 tests, 340 passes and four explicit source-checkout package
skips; 73 PowerShell export contracts; a 400-file verified source archive;
7/7 extracted-package checks with zero skips; and 29 external stdio checks.
The external fixture proves that ordinary unpublished comments suppress raw
source hashes and that a known unsupported MO2 conflict comparison is refused
before private instance/profile reads.

R4 remains preserved as valid predecessor evidence but is superseded by the
stricter comment-fingerprint policy. Local Python 3.9/Tk limitations remain
supplemental environment evidence only; Windows Python 3.12 owns acceptance.
No real game or MO2 profile has been inspected. Synthetic acceptance does not
establish VFS state, runtime compatibility or gameplay. Real-folder read-only
acceptance, if separately authorized, remains another scope; transactions and
MO2 comparison remain blocked.
