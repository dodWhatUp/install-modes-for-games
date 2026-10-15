# Mod Organizer 2 read-only adapter — Windows acceptance

**Date:** 2026-10-15
**Version:** `0.28.0-preview.1`
**Tested product commit:** `c0809f7ac99a776390e131859991105c2f4c88f4`
**Result:** **PASS** for the bounded synthetic read-only scope below.

## Exact source boundary

- Canonical base: `290bea7983ccca50073c5f45ce44337cacafc32a`.
- Tested product parent: `f6cda135c7d51913cf2e0dcd9c0fa32c0e6ec315`.
- R5 harness commit: `39996aadf983d78b2a05e98015a14414c8a21023`.
- Candidate: 723 tracked files, 8,788,283 bytes, aggregate SHA-256 `85013aad0c2cd7faf8ad9c093aec7a4eec14a8ee81c042a260ec5d5f670144de`.
- The later documentation commit is separate and does not expand these tested product bytes.

## Accepted behavior

- Local-only MO2 registration retains opaque public instance IDs and writes only private registry metadata.
- Exact registered game, manager and profile declarations are read without starting MO2, loading code or mutating the manager, game or profile.
- A raw source fingerprint is public only when no name is redacted and every omitted comment is the reviewed Mod Organizer generated header. Any other unpublished comment suppresses that raw hash.
- MO2 comparison and observed conflict graphs remain refused with `ADAPTER_COMPARISON_PENDING` before private instance/profile reads.
- Modern MCP exposes no registration or arbitrary path argument; legacy tool names remain unchanged.

## Native Windows gate

| Gate | Result |
|---|---:|
| Suites | 13/13 |
| Tests | 344 |
| Passed | 340 |
| Explicit package-mode skips | 4 |
| Timeouts | 0 |
| Automatic retries | 0 |
| MO2 reader | 21/21 |
| Workbench launcher | 12/12 |
| Keybind merge | 7/7 |

The four skips are the source-checkout package assertions that require a generated `MANIFEST.json`; the exported package reran all seven packaging checks with zero skips.

## Source export and extracted package

- PowerShell source-export contracts: **73 passed**.
- Exported source files: **400**.
- Archive SHA-256: `f1be9c0f8b70702faf2ef0c7caca5515f449e4631a364d08ba4fe7931b941076`.
- Manifest SHA-256: `12ca755a14e3a2c65581b1dc7ee856cf84b5f533fb8c39445c68a1169b0b7337`.
- Extracted package: **7/7**, zero skips.
- Workbench and Original `verify-only` passed without creating the preview profile.
- Exact host pins: **13/13**.

## External stdio acceptance

All **29** modern/legacy checks passed. Four valid synthetic MO2 instances and one malformed fixture were used. The public results retained normal declaration rows, redacted path/credential candidates, suppressed raw hashes for ordinary unpublished comments, and returned the typed comparison blocker before reading the malformed profile. The synthetic game/manager/profile trees stayed unchanged; only five private registry records were created. No job, request, proposal or execution occurred, and the processes exited cleanly.

## Preserved predecessor

R4 tested `f6cda135c7d51913cf2e0dcd9c0fa32c0e6ec315` and passed its bounded Windows gates. It remains valid historical evidence, but R5 supersedes it because R5 also prevents reusable raw fingerprints when omitted comments are ordinary unpublished text rather than path/token candidates. R4 was not relabeled or overwritten.

## Boundaries

This is synthetic source and client acceptance, not a real MO2 profile or effective deployment result. It does not establish VFS winners, priority, overwrite state, runtime loading, compatibility, gameplay, production installation, a specific product UI or any write transaction. The task branch is not canonical adoption until a separate reviewed merge.

Machine-local paths and raw logs remain outside Git. The sanitized machine-readable record is [`MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json`](MO2-READ-ADAPTER-WINDOWS-ACCEPTANCE-2026-10-15.json).
