# Game Tools A+B Keybinds — backup and repository reconciliation (2026-10-18)

**Canonical editable owner:** [`dodWhatUp/install-modes-for-games`](https://github.com/dodWhatUp/install-modes-for-games). This is a dated reconciliation receipt, **not** a replacement source master, another application, an instruction stack, or permission to install software or modify games.

## Verified private preservation

- Existing owner-only Drive parent: `install-modes-for-games — 2026-09-14`.
- New private preservation folder: [2026-10-18 A+B Keybinds](https://drive.google.com/drive/folders/1yzpA1_KqtB0MCIEr9Fldrb-88sba4dJq).
- [Immutable A+B transport archive](https://drive.google.com/file/d/1MAa380GAcyVJLVnCuJWgJzobHScx6kFW/view): `GameTools_A_and_B_One_ZIP_For_Merger_2026-10-13.zip`, 7,096,159 bytes, SHA-256 `fd3cb621c83220f15c7fa5d51efe2916bba9ced70d8505d57f404300b498a4b2`.
- The downloaded authenticated Drive copy matched the exact SHA-256 and size. ZIP CRC and nested manifests passed: transport **7/7**, Input A package **62/62**, Input B package **40/40**, Input A app source **221/221**, Input B Keybinds source **171/171**, and V3 research **146/146**. This establishes **byte-preservation**, not software recovery or game acceptance.
- Permission metadata returned `shared=false` and an owner-only permission; sharing was not widened. Historic archive links and versions were not overwritten or deleted.
- Original A and B remain separately addressable inside the transport ZIP; prior Drive Input A and Azeron archives remain in their existing locations. The raw Planner exists inside B's V3 research ZIP. Do **not** commit this private transport ZIP, user-supplied HTML, historic profile exports, saves or raw private evidence to this public repository.

## Reconciliation with the *later* repository source

Read-only observation: `main` at `169d7570ac34822153ea1407d27b77d62df7607d` (2026-10-17). The [Keybinds semantic merge review](KEYBINDS-MERGE-REVIEW.md), [intake](KEYBINDS-MERGE-INTAKE.json), [source delta](KEYBINDS-MERGE-SOURCE-DELTA.json) and [validation](KEYBINDS-MERGE-VALIDATION.json) show that A 0.24 + B 0.2 were **already reconciled and incorporated** into the subsequent product lineage. No second A+B merge is needed merely to archive the source inputs.

A comparison of Git blob SHA-1 values confirmed that all **19** original `scripts/game_keybind_ops/*.py` source files in Input B are **byte-identical** to the current `main` equivalents. Three B host-bridge files (`GameToolKeybindAI.py`, `GameToolKeybindIntegration.py`, `GameToolKeybindWorkspaces.py`) are intentionally **not** byte-identical: they were rebased to the later shared host. Do not blindly restore B's older bridges or B's 0.23 compatibility copies.

Later owners/states are distinct:

- The repository root is the adopted **0.27** application source, including later read-only planning and AI-efficiency work. Its newer changes take precedence over historical A 0.24/B 0.2 source snapshots.
- The [cross-computer checkpoint](CROSS-COMPUTER-CONTINUATION-2026-10-17.md) records an **observed** reference-PC installed pointer to 0.25; this is not a current inspection of all PCs.
- The `source-snapshots/local-toolkit-library-0.26/` candidate remains separately preserved and **unadopted**. Preserve it for its independent library/goal-navigation review rather than replacing 0.27.
- Input A's `game_support_pack` and Input B's `game-keybind-pack` have distinct schema ownership/revision histories under shared `game_id`. One `GameToolAutomation`, `GameToolJournal`, `GameToolGameWorkspaces`, `GameToolWorkbench` and local approval owner must remain.
- V3 covers 17 games / 23 variants, but all named game keybind packs remain **research drafts**, not native-game-certified adapters. The present archiving operation created or installed no replacement game files.

## What this operation does *not* establish

No live Windows/game/Azeron or ChatGPT MCP verification was performed now; no production profile, game file, native mapper or installed app was changed. GitHub repository data is publicly visible, while linked Drive raw snapshots retain private permissions. A private Drive snapshot is a recovery reference, not an alternative editable Git master or an automatically synchronized mirror of the entire current `main` (the existing 2026-10-17 private Git bundle has its own observed commit and coverage).

Any future **source** change must be developed against current repository head and active worktrees/branches, validated, and published through the canonical owner. Treat this document as a verified locator and scoped historical audit, not a command to replay old integrations.
