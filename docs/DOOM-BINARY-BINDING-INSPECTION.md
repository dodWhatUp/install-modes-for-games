# DOOM saved binding inspection

`scripts/GameToolDoomBindingInspect.py` reads binding evidence from an explicitly
selected, SHA-pinned Steam `profile.bin` snapshot. It adds **inspect, semantic diff
and JSON/CSV export**, not game-file Apply or profile switching. It performs no
path discovery, writes, launch, input capture, cloud synchronization or native
profile operation. The existing `game_keybind_ops` text-adapter boundary remains
unchanged; do not register this save role as a text adapter.

The normal caller is an existing Game Controls source/review owner. That owner
selects and reads the authorized local snapshot, supplies its expected SHA-256
and already-known owning SteamID64, and keeps private identity/path recovery
outside Git. The module accepts bytes and never returns the identity or full
decrypted profile. It needs the reviewed `cryptography` runtime dependency;
missing dependencies produce a typed unavailable result rather than installation.

## Compact inspection panel

The existing Controllers workspace opens `GameToolDoomBindingInspectUI.InspectPanel`
through **DOOM binding files…**. It offers one binding table, a short text search,
the existing editable context/input selectors, a comparison view and an Export
menu. Source details remain inside the content disclosure. Narrow windows keep
their content scrollable; the panel reuses the shared responsive components.

Select an existing `profile.bin` explicitly. Only a selected standard
`userdata/<account32>/3017860/remote/PROFILE/profile.bin` path supplies a derived
owner. For an unassociated archive copy, the user provides the owning SteamID64;
the panel does not guess from arbitrary numbers or another logged-in account.
Authentication checks the supplied/derived identity. Reads and parsing happen on
a background worker, with Tk updates delivered on the UI thread.

**Compare snapshot…** retains the first snapshot and shows added/removed rows.
An invalid second source does not replace the first. JSON/CSV export creates only
the explicitly selected new file, using exclusive creation; existing files and
binary extensions are refused. Opening the panel, searching, changing views or
closing it never writes a game profile. `close()` cancels its UI polling and
invalidates late worker results. The host owns the window lifetime.

Seven headless helper checks cover source-role/owner selection, filtering and
exclusive export. Native widget layout, background close and caret/dropdown
behavior require the isolated guest GUI check; headless tests do not certify them.
`scripts/tests/Test-DoomBindingInspectGUI.py` supplies eight generated-fixture Tk
cases for that guest run: worker completion, filters, editable open-list caret,
failed/successful comparison, exclusive export, late-worker close and narrow
larger-text layout. The test source creates no host input or live game fixture.

## Integration contract

| Function | Result / boundary |
|---|---|
| `capabilities()` | Explicit inspect/diff/export availability; binary write and whole-profile switch are always false |
| `inspect_snapshot(raw, identity, expected_sha256=..., game_build=...)` | `doom_binary_binding_evidence` v1 with source pins, raw command/output rows, context indexes and separate verification states |
| `diff_evidence(before, after)` | Context-specific added/removed rows, retaining duplicates; row reorder and nonbinding source changes do not masquerade as binding changes |
| `export_json(evidence)` / `export_csv(evidence)` | Data-only strings; no importable game binary or execution authority; CSV cells escape formula prefixes |
| `prepare_binary_changes(...)` | Always raises `BINARY_WRITE_UNVERIFIED`, including when passed an external approval/force flag |

Every inspection checks the selected exact source hash, identity-bound AES-GCM
authentication, reviewed header version, bounded array grammar and every used
name/string reference. Unknown encodings, ambiguity, broken references and
truncation fail closed. Input size is bounded to 2 MiB and bindings to 4,096 rows.
The reviewed contexts are recorded by native index; the reader does not invent
human action labels, Xbox/reWASD button crosswalks, priority scores or gameplay
semantics. Secondary flags remain raw tokens. The caller's game build is declared
provenance, not a build detected from the binary.

Evidence includes both the exact source hash and a semantic binding revision.
Cross-account comparisons and known different declared builds require
reconciliation. Unknown build provenance stays unknown. Exported JSON is inert
data; its fingerprint is an integrity aid, not a signature or proof of authority.
Before using it as current operational evidence, re-inspect the pinned source
through its existing local owner. A matching timestamp or edited JSON flag is
never permission to Apply.

## Verification and writer limits

Four existing private native snapshots were inspected without changing a game.
The final snapshot contains 287 rows across eight native contexts. Seven existing
Slayer rows change and four selectors are added; the other contexts remain
identical. The saved matrix matches the previously recorded native-menu restart
readback. Settings bytes are separate; a text CFG alone did not establish these
effective bindings. This is saved-file evidence with that scoped native readback,
not combat or physical-comfort acceptance.

Private offline work also reconstructs the complete syntax of eight copied binary
files byte-for-byte, and tests reference relocation/shared-literal detachment for
in-memory key edits. That experimental serializer is **not shipped here**.
The internal header checksum remains unvalidated; envelope authentication alone
does not certify a modified game profile. Whole-profile switching is also refused
because the profile contains unrelated settings and progression-related data.

The remaining writer boundary is: validate the internal checksum across independent
samples, review the lossless serializer/version bounds, integrate through the
existing guarded binary transaction owner if one is implemented, then perform a
separately scoped reversible native acceptance check. No writer, installation or
new game acceptance is implied by this source addition.

The repository tests use generated synthetic data only. Private game bytes,
identities, decrypted profiles and raw logs must not be committed. Synthetic
tests cover hash/authentication failures, malformed grammar, aliases, independent
contexts, semantic diffs, export integrity, CSV safety and denied write capability.

## Primary implementation references

- [idSaveDataResigner authenticated envelope](https://github.com/mi5hmash/idSaveDataResigner/blob/6d06b734ff81196d1d2acecea753148eeb782764/idSaveDataResignerCore/Helpers/IdDeencryption.cs)
- [Independent DOOM TDA save envelope](https://github.com/GoobyCorp/DOOM-TDA-Utilities/blob/d1dcd9c4b9046fc6ee30b102bd88853daf95fb41/DOOM_TDA_Save.py)
- [Incomplete upstream profile parser](https://github.com/GoobyCorp/DOOM-TDA-Utilities/blob/d1dcd9c4b9046fc6ee30b102bd88853daf95fb41/DOOM_TDA_Profile.py)
- [Official input menu and press-style guide](https://slayersclub.bethesda.net/en-NZ/news/doom-the-dark-ages-accessibility-guide)
- [Steam Cloud file ownership and synchronization](https://partner.steamgames.com/doc/features/cloud)
