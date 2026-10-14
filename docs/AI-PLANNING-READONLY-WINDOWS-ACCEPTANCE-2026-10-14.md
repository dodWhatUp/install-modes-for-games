# Read-only planning and UMM instances — Windows acceptance

**Date:** 2026-10-14
**Version:** `0.27.0-preview.1`
**Current tested product commit:** `f37a6e4ed6321c2cae6c928bc889d0ab49dc9c39`
**Historical R4 tested product commit:** `cd444009d063b27894bf8e399d517670b30ebc47`
**Result:** **PASS** for the bounded synthetic read-only scope below.

## Current correction boundary — R5

R5 preserves the R4 architecture and corrects five reviewed source paths. Windows
case and 8.3 aliases now resolve to one physical instance without weakening link
refusal; `inspect-installed` and `review-keybinds` no longer invent a mod recipe;
support-only UMM definitions can inspect an explicitly registered instance; mode
validation and public read effects now use their owning contracts.

The exact 715-file R5 candidate matched commit `f37a6e4ed6321c2cae6c928bc889d0ab49dc9c39` after the repository's
Git clean filters. Windows 11 ARM64 passed **13/13 suites: 374 tests, 367 passed
and seven explicit skips**, with no timeout or automatic retry. The real source
export contained **394 files / 395 ZIP entries**, SHA-256
`e96ad5d012f03b1ee09a716b5e979d1385feaabb5d7bca7c30baa6ee81b6e3c9`;
manifest SHA-256 is
`445a4e74a0b6966b2e8a12500a6e4b11ce9f6af2ff8b39e23ff62107ec94c5d5`.
Exported packaging passed 7/7 with zero skips. External modern/legacy stdio passed
all 27 checks, including exact goal read effects; the synthetic game tree remained
byte-identical and only one private instance record was written.

An initial mixed R5 copy was isolated before Windows transfer because seven
historical documents did not match the current worktree. A first independent
readback compared checkout CRLF bytes directly with normalized Git blobs; the
preserved R2 readback applied Git clean filters and passed. Neither attempt had a
product effect. The R4 record below remains historical evidence rather than being
rewritten.

## Historical R4 acceptance

## Accepted behavior

- Candidate R4 contained **715 payload files**; every file matched the sealed inventory and no extra file appeared.
- Windows 11 ARM64 ran **13/13 suites**: **370 tests**, **363 passed**, **7 environment/package skips**, no timeout and no automatic retry.
- The real PowerShell source export produced **394 source files**. Every ZIP entry was re-hashed; archive SHA-256 is `d843f59e4f148f01f26e29eaaa7895a27aa6bd1ec79403df44ccc82f475ef513` and manifest SHA-256 is `7782f1f91c232cafc7d09607c4a674c4d52f9a34598af73ceb92763c117521d5`.
- The exported source reran all seven package checks with **zero skips**. Workbench and Original `verify-only` passed without creating the 0.27 preview profile, and all 12 exact host pins matched.
- An independent Windows stdio client exercised modern `2026-07-28` and legacy `2025-11-25`. Modern exposed **38 tools**, including the four read-only planning tools; legacy exposed **24 tools** and did not acquire them.
- A local operator CLI registered one synthetic UMM fixture. Public results omitted its path; the fixture's four files retained aggregate SHA-256 `b44c883159970e6573b45cc8846e9f5ee41b60ae18db5af1ed06ffd430bc388a` before and after registration and all MCP reads.
- The only private data written was the existing registry lock plus one opaque instance record. No job, proposal, execution, production profile, game file, manager profile, input or capture was created.

## Environment skips

Seven skips remain explicit rather than being counted as product passes:

1. Two Game Support link fixtures and one Automation link fixture could not create a Windows symlink because the standard test account lacks that privilege. The product's link refusal is still exercised on systems where fixture creation is permitted.
2. Four source-checkout package checks require a generated `MANIFEST.json`. They were rerun against the exported source and passed 7/7 with zero skips.

## Reconciled predecessor attempts

R1, R2 and R3 were retained as immutable evidence and were not overwritten or automatically retried:

- **R1:** the test searched raw JSON text for an unescaped Windows path; structured record data was correct.
- **R2:** two existing security tests failed before product invocation because Windows refused fixture symlink creation.
- **R3:** the exporter truthfully said 0.27 required validation but did not explicitly preserve the word `pending` required by its metadata contract. The metadata was strengthened; the test was not weakened.

Each reconciliation recorded no product effect. R4 is a new candidate with its own inventory and acceptance.

## Boundaries

This acceptance uses a synthetic UMM directory. It does not establish a real game or manager profile, enabled state, load order, runtime compatibility, gameplay, a specific ChatGPT/Codex product UI, production installation or any install/upgrade/disable/rollback transaction. Task-branch publication and later review do not equal `main` adoption.

Machine-local receipts are intentionally excluded from Git. The sanitized machine-readable record is [`AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.json`](AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.json).
