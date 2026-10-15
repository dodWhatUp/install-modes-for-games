# Read-only planning and UMM instances — Windows acceptance

**Date:** 2026-10-14
**Version:** `0.27.0-preview.1`
**Current tested product commit:** `e454433e81e067b1f11267a3cac18081b60512f8`
**Historical R8 tested product commit:** `dbed124f40e3d336baf49e7598c16f2d1b57189d`
**Historical R5 tested product commit:** `f37a6e4ed6321c2cae6c928bc889d0ab49dc9c39`
**Historical R4 tested product commit:** `cd444009d063b27894bf8e399d517670b30ebc47`
**Result:** **PASS** for the bounded synthetic read-only scope below.

## Current embedded-path and filtered-list boundary — R9

R9 preserves the accepted read-only architecture and closes two exact-head
review findings. Public UMM metadata now refuses short or punctuated absolute
Windows, POSIX, UNC, rooted, home/environment and file-URI paths plus URL
credentials, while ordinary relative identifiers, versions and HTTPS URLs remain
available. Filtered instance listing now computes `truncated` only from matching
public records read from one bounded registry snapshot.

The exact 715-file R9 candidate matched commit `e454433e81e067b1f11267a3cac18081b60512f8` after Git clean
filters. Windows 11 ARM64 passed **13/13 suites: 388 tests, 381 passed and seven
explicit skips**, with no timeout or automatic retry. The real source export
contained **394 files / 395 ZIP entries**, SHA-256
`369a396b00f845a74fbaa7abfe8c004bf5a0d64becd24ea003cd575e79b6fc30`; manifest SHA-256 is `8090318a4a9e3acb89ffba636780891c43ff358d7d88009604d67b9b7355c0d0`. Exported packaging passed 7/7 with zero
skips, both verify-only paths passed without creating the preview profile, and
all 12 exact host pins matched.

External modern/legacy stdio passed all **34 checks**. Four Kingmaker instances,
one support-only Wrath instance and one corrupt registry fixture were inspected.
Credential, Windows-path and short punctuated POSIX-path metadata returned typed
`INSTANCE_PRIVATE_METADATA` blockers without echo. A one-row Wrath filter stayed
`truncated=false` despite four Kingmaker records. All five synthetic game trees
remained byte-identical; only six private registry records were written, with no
job, request, proposal or execution.

The first R9 copy was accidentally invoked under the Windows system account. It
copied only the sealed candidate into an isolated system-profile test root; the
Python hash gate did not start. That known copy and its reconciliation receipt
remain preserved. A new current-user root passed the complete acceptance above;
no uncertain effect was retried or relabeled.

## Historical privacy and refusal boundary — R8

R8 preserves the accepted read-only architecture and closes two publication
boundaries found during exact-head review. Corrupt or renamed registry records
now expose only neutral ordinal placeholders; SHA revisions and filename identity
are validated; arbitrary UMM manifest text is recursively refused when it
contains an absolute path, file URI or credential candidate. Known domain
refusals remain typed result-envelope blockers, and an unexpected stdio fallback
preserves the request id instead of reporting a JSON parse error.

The exact 715-file R8 candidate matched commit `dbed124f40e3d336baf49e7598c16f2d1b57189d` after Git clean
filters. Windows 11 ARM64 passed **13/13 suites: 385 tests, 378 passed and seven
explicit skips**, with no timeout or automatic retry. The real source export
contained **394 files / 395 ZIP entries**, SHA-256
`4e5bcd4caae7752270a1b29101f873b85a9692dd04abd8b5e0419130cba252d2`;
manifest SHA-256 is
`fd442dabf9569eb84538fd20983c68fb40eec5f24d3cc7387f6eeccd803d4bc8`.
Exported packaging passed 7/7 with zero skips.

External modern/legacy stdio passed all **32 checks**. Three valid synthetic UMM
instances and one corrupt registry fixture were inspected. The corrupt filename
was not exposed; invented credential and Windows-path metadata returned typed
`INSTANCE_PRIVATE_METADATA` blockers without echo. All three game trees remained
byte-identical; only four private registry records were written, with no job,
request, proposal or execution.

R6 passed runtime gates but was refused by the source privacy gate before export
mutation because an invented path literal appeared in test source. R7 passed
source export and packaging, but its first expected domain refusal was mislabeled
as a JSON parse error; readback established unchanged games and no execution
effect. Both revisions remain preserved as evidence and were not relabeled as R8.

## Historical correction boundary — R5

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

## Subsequent canonical adoption

After the exact R9 product and receipt commits passed independent exact-head review,
PR #9 was merged with a merge commit so both boundaries remain visible in history:

- Tested product source: `e454433e81e067b1f11267a3cac18081b60512f8`
- Reviewed head / acceptance documentation: `ab9c2cdf32dd9d361aa4273aca6e10a168e864d8`
- Original canonical base: `108cb332b874583776c7a9cb1a19ce67c8cc96e5`
- Canonical merge commit: `ef38d94be4fb4847cbbeda5f8fe41455b267aeaa`

The merge changed Git publication state only. It did not install production, inspect
a real game or manager, approve a proposal, execute an operation, or expand the
recorded Windows/runtime acceptance.

## Boundaries

This acceptance uses synthetic UMM directories. It does not establish a real game or manager profile, enabled state, load order, runtime compatibility, gameplay, a specific ChatGPT/Codex product UI, production installation or any install/upgrade/disable/rollback transaction. The later `main` merge establishes source adoption only and does not change those boundaries.

Machine-local receipts are intentionally excluded from Git. The sanitized machine-readable record is [`AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.json`](AI-PLANNING-READONLY-WINDOWS-ACCEPTANCE-2026-10-14.json).
