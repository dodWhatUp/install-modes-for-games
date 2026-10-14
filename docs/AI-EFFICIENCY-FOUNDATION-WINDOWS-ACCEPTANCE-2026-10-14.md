# AI Efficiency Foundation — Windows and external stdio acceptance

**Date:** 2026-10-14
**Source Preview SHA-256:** `bf2989da32f197f021283aef06368e7f028cfe7e23619c5d766715f2e242f977`
**Result:** **PASS** within the bounded scope below.

## What passed

- The exact Preview archive SHA-256 matched before extraction; 387 files were extracted in a new current-user test directory.
- `VerifyOnly` passed for Workbench and Original with no profile or shortcut creation.
- Workbench and Original opened as native Windows/Tk processes and closed normally without force.
- The separate `GameToolHub-Workbench-Preview-0.26.0-preview.1-AIFoundation-Keybinds` profile was the only Game Tools profile written; all other Game Tools profiles retained their fingerprints.
- Current-user Desktop and Start-menu shortcuts were created without overwriting an existing shortcut.
- Native Tk construction exposed exactly `Mods`, `AI requests`, `Manual checks`, and `Keybinds`; Stop, More, Keybind content, 100% → 200% → 100% scaling, narrow geometry and clean close all passed.
- An independent Windows stdio client completed modern `2026-07-28` discovery and legacy `2025-11-25` initialization. The modern surface returned 15 deterministic tools with output schemas and 88 resources on the first page.
- `search → fetch`, resource read, status, resume, change cursor, blocker explanation, batch status and in-memory handoff passed.
- One synthetic proposal entered only the local approval mailbox, was read back as `AWAITING_LOCAL_APPROVAL`, then was rejected locally and read back as `REJECTED`. No approval or operation execution occurred.

## Reconciled first harness failure

The first external-client harness reached the pending proposal but used the wrong field name when reading the returned change cursor. Before any retry, the same request mailbox was inspected, the pending synthetic proposal was rejected locally, and the absence of a Mods execution directory was verified. The corrected harness then used a new isolated data root and passed. The machine-readable record preserves both outcomes.

## Canonical task-branch seal

The reconciled **R7** source was copied to a new Windows directory and verified against its complete inventory before execution. The candidate contains 708 payload files plus its inventory; no file was missing, changed or unexpected. The exact product source was committed as `42dc939bd37ff37e5af2cb429bce6d0aeb3eb29d` on `task/ai-efficiency-foundation-reconcile-20261014`.

- Candidate aggregate SHA-256: `773ea9f590ab20ff9ec510d015eec80d8d74e07e4a1e18e693f746090bfd6fba`
- Inventory-file SHA-256: `fb15687c018a647bfc10dd808e6683ce17d20b8893998b89c9822f6d2d77aa9c`
- Focused native gate: **11/11 suites**, 295 tests run, 290 passed and 5 environment skips.
- Native Windows PowerShell 5.1 export: 387 files, full ZIP entry verification, archive SHA-256 `264ea4eb59a3bbf2b7e41aa41a5f97fd31db9b5f05596cbf56509cfa352d4956` and manifest SHA-256 `e178e30d6fa5140445cc3a19048b8340da6828e997357870d00805e38e6c5c2a`.
- R4 and R5 stopped on two bounded portability/contract findings; each effect was inspected before a new candidate was created. R6 passed, and R7 reran the full gate after the narrow Git allowlist change.

## Environment

| Item | Accepted value |
|---|---|
| OS | Windows 11 ARM64 |
| Python | 3.12.10 ARM64, official per-user package |
| Tk | 8.6.15 |
| PowerShell | 5.1 |
| Native scaling checks | 100%, 200%, then 100% |

## Boundaries

This acceptance does **not** establish connection through a specific ChatGPT or Codex product UI, production installation, a real game or manager, physical input, capture, gameplay, remote HTTP/plugin deployment, or main-branch adoption. UI Automation did not expose Tk descendants, so native widget content was verified by a separate in-process Tk audit rather than a screenshot or a claim of human visual-quality review.

The complete private machine receipts are excluded from Git because they contain machine-local paths. The sanitized structured result is in [`AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.json`](AI-EFFICIENCY-FOUNDATION-WINDOWS-ACCEPTANCE-2026-10-14.json).
