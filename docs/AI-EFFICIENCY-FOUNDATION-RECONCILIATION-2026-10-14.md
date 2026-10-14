# AI Efficiency Foundation — canonical-source reconciliation

**Date:** 2026-10-14
**Repository:** `dodWhatUp/install-modes-for-games`
**Canonical base:** `043f3c4733788f082da98dfcb43c0972d2794c6a`
**Imported source archive SHA-256:** `ad4bcddbd76845bf35bdb67e1eee529dcab921263a742a596eec93fb6d41afd6`

## Result

The sealed 0.26 source archive was not copied over the repository wholesale. Its 380 authored payloads were compared by SHA-256 against the canonical base and classified before writing:

| Class | Count | Treatment |
|---|---:|---|
| New source paths | 329 | Added from the verified source archive |
| Source-owned overlapping paths | 15 | Adopted as the current product/test implementation |
| Canonical-main overlapping paths | 7 | Preserved because they were semantically identical, later canonical records, or safer owners |
| Semantic merges | 3 | Reconciled field/section by field/section |
| Archive-only files | 1 | Excluded from Git |

## Material conflict resolutions

- `preferences/GENERAL.md`: the package omitted the later RHI and renderer-overhaul defaults and contained a conflicting Cyberpunk F6/F9 statement. The canonical current defaults were preserved; only non-conflicting toolkit-continuity, delivery, layering and Dynamic SR guidance was added.
- `docs/AZERON-GAME-CONTROLS.md`: the package omitted the current cross-game keyboard-catalogue section, so the canonical file was retained.
- `docs/GAME-TOOLS-KNOWLEDGE-INDEX.md`: the integrated 0.26 index was adopted, then the canonical Azeron R5 closure and GPU architecture research sections were restored.
- `AGENTS.md`: current project rules remained the owner. Only additive 0.26 routing and safety text was merged.
- `MANIFEST.json`: the source archive manifest is generated delivery metadata and was not imported as editable repository source.
- `docs/AZERON-GAME-KEYMAP-VIEWER-WISHLIST.md`: adopted from canonical owner branch `codex/azeron-shared-r5-2026-10-11` at commit `58068c3b96a2314df77c3510218d1fbefa629f39` / blob `106a7a07b584664a002f96fc573e304efd91685d`; only line endings were normalized.
- Missing relative pointers to private PoE2/Azeron/IsolatedLab records were not reconstructed. They were routed to existing public reviews, exact PR/commit references and private owner-held Drive records.

## Post-package evidence

The source package predated native Windows acceptance. The exact Preview subsequently passed native Windows/Tk and independent modern/legacy external stdio-client acceptance. See [`AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md`](AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.md).

## Boundary

This is a task-branch candidate. It does not merge `main`, install production, modify a game/profile/device, approve a proposal, or publish archive binaries into Git. The machine-readable classification is in [`AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.json`](AI-EFFICIENCY-FOUNDATION-RECONCILIATION-2026-10-14.json).
