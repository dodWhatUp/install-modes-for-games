# Codex execution handoff — Azeron Cyborg II, SHARED R5
**Scope:** Run a non-destructive import and verification of the already-created four candidate Software v2 profiles, if the *actual Windows gaming computer* and authenticated private Drive access are available. This is an execution handoff, not a request to design another mapping or research more games.

## Canonical sources (retrieve yourself; no user file handoff)
- Repo: `dodWhatUp/install-modes-for-games`. Read `AGENTS.md`, `docs/AZERON-GAME-CONTROLS.md`, `docs/INPUT-DEVICE-REGISTRY.md`, and the [R5 format and validation guide](README.md).
- **Private Google Drive**, inside folder **Azeron profile backups**. Find exact file **Azeron SHARED R5 - Four native profile candidates.zip** (27,326 bytes). This is the intended delivery package. Extract locally to a task-specific directory; import the **four individual JSON files** from its `profiles/` folder. NEVER restore the delivery ZIP as a backup.
- Find **Azeron SHARED R5 - Hebrew import guide and numbered maps.html** for the numbered-button diagrams.
- Find **Azeron SHARED R5 - Native profiles source evidence and recovery.zip** only if source provenance, recovery, or schema audit is necessary; it includes an optional augmented full backup that is **not** an additive merge and may rewind later changes. Do not restore it as a shortcut.
- No original native backups, profile UUIDs, or private archives belong in public Git. Do not change Drive sharing permissions. Do not ask the user to re-upload files already in Drive. If Codex cannot use the authenticated Drive connector, report the specific connection/access needed; an unshared link alone is not proof that an agent can download it.

## Baseline and intent
The supplied backup reported Azeron Software 2.0.2, Cyborg II model code 8. Confirm installed machine/version afresh before acting. The source ZIP had 18 software profiles. Only profiles tagged `layered 1` / `LAYER 1` or `FOR CHAT` were user-authored. The `FOR CHAT` profile is a feature demonstration, not a gameplay preference. Preserve **all** existing profiles regardless of authorship.
Four newly generated independent candidate profiles have distinct IDs:
- `SHARED R5 - BASIC`
- `SHARED R5 - NUMBERS`
- `SHARED R5 - LETTERS`
- `SHARED R5 - TOOLS`
On BASIC the candidate mapping intends native button **2 → NUMBERS**, **1 → LETTERS**, **36 → TOOLS**, with a held, momentary layer and return on release, using reciprocal same-button links. This is based on **SINGLE → Layering / Toggle on hold** in the newer source, not the historical V-tap / 150-ms v1.5.6 configuration. V remains a regular direct key. The authoring and static readback checks passed; native importer acceptance and physical behavior have **not** been tested. The existing R3/R4 conflicts (e.g. same-finger chords, cross-bank E+arrows, urgent 6) remain known limitations.

## Execute only if preconditions are met
1. Identify the Windows computer running the actual Azeron app and the Cyborg II. Do not assume a Mac connection is sufficient. Confirm permitted text-based/app-native interaction. **No screen captures, video, global keylogging, arbitrary driver injection, or unapproved new software.**
2. Inspect the active SOFTWARE profile list and check for pre-existing `SHARED R5` imports (match IDs and names). **Never duplicate an earlier successful import**. Create and verify a just-in-time backup of the current live state *before import*, stored privately; ensure rollback is clear.
3. Verify the downloaded package has four JSONs and matches the expected names/schema; review the original native source and R5 validations if there is any doubt. Do not use the optional full-restore ZIP. Do not overwrite, delete or rename old profiles; do not modify onboard slots, device firmware, games, Steam Input, reWASD or graphics hotkeys.
4. Import the four candidate JSONs as **additional SOFTWARE profiles**, multi-select only if the installed import dialog explicitly supports it, otherwise individually. If the importer refuses a file, suggests replacing existing work, or effects are uncertain, **stop, inspect the resulting list, report the exact text/state, and do not blindly retry**.
5. Check profile names/IDs and the target of each of BASIC's native buttons **2, 1, 36**. Check each reciprocal return link in the target. The importer may remap IDs; if so, reconcile links *by verified SHARED R5 profile names*. Only make narrow and reversible necessary corrections, never guess target IDs.
6. With games closed, select BASIC for testing and have the user physically press/hold/release each selector (or instruct exactly what to press if remote execution cannot manipulate physical switches). Validate: enters correct layer; stays active while held; returns to BASIC on release without second press; no stray tap output; repeated switching; no stuck/held key; joystick mode stays intended. Check raw Ctrl/Shift/Alt and samples of number/F-key chords, recognizing ergonomics still requires the user's feedback. Do not claim physical verification from the presence of JSON fields alone.
7. When successful, take a new native export (if supported), compare actual resulting profiles and links against the candidate, and store the live export, recovery backup and exact results **privately** in the existing Drive folder. Put a **sanitized concise** results/handoff in the canonical Git repo only when repository permissions and applicable instructions permit. Preserve unrelated open PRs/worktrees. Report completed/failed/pending checks separately.

## If execution is blocked
Finish all non-destructive preparation that is independently possible. If the only accessible host is a Mac, or private Drive is unavailable in the Codex context, **do not claim installation**. State one concrete next enabling action (e.g., connect the Windows gaming PC or enable the Google Drive connector for this Codex session), without asking the user to move or upload the same files again. A user may need to perform the physical button presses; provide precise one-step directions at that point.

**Successful completion requires verified in-app import and 3 held-layer return tests.** Publication of candidate JSON and Git documentation is not that evidence.
