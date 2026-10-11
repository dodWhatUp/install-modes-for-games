# R8 preflight supplement — unchanged profiles, safer handoff

Owner: `dodWhatUp/install-modes-for-games`; native baseline R8 source `b4fe0a476d70244a8afe259b64814a78178825a3`, publication `806f52e59ee8e5e16b20a40837134297b41144a9`.

Read **READY_FOR_CODEX.md** first. This supplement completes independently testable preparation before the actual Windows/native/game stage. It does not create R9 profiles or invalidate the existing research.

## Implemented

- `native_review.py`: read-only presence/ID/name/operational-state comparison against the exact CORE5/SPARSE6 ZIPs, plus before/after preservation checks. It detects correct importer ID remapping, broken targets, same-name differences, partial imports, duplicate IDs and changes to existing profiles. It never imports, writes the live store or says the supplied export is current.
- `input_evidence.py` and `safe_io.py`: current collector v2 with duplicate-property/mode rejection, regular-file/parent checks, bounded reads, redacted pointers and final verification before usable receipt publication. Historical R8 v1 is preserved, not overwritten.
- `run_checks.py`: one offline rehearsal command. No new installed dependencies; Python tests/native readback/build and available Node tests are recorded separately. Missing Node stays NOT_RUN.
- `atlas_checks.js`, `atlas_checked_adapter.js`, `build_checked_atlas.py`: optional checked Atlas derivative. Right-side modifiers cannot be satisfied by a left-only candidate field. Inactive stored fields do not count as emitted input. Tool-owner overlap is conditional policy, not detected live state. All native output/geometry and 208 action records remain unchanged.
- `render_review.py`: private, script-free HTML view of a native review receipt.
- Test/receipt templates: a source-derived physical checklist, execution status template and explicit unresolved gates.

## Material findings and corrections

Three old collector edge cases were reproduced using synthetic input: duplicate JSON values silently kept only the last entry; conflicting repeated mode fields did the same; failure of the final read itself could leave an already-written receipt without a stale marker. New collection rejects the first two and writes only `COLLECTION_FAILED.json` for a failed final recheck. No actual user game file was observed to suffer these problems, and no saved profile was corrupted by the tests.

A fourth display edge case was checked: a generic logical `Ctrl` is not evidence of Right Ctrl. Exact native candidate projections now support the displayed same-bank check. Generic Ctrl remains acceptable when the source is generic; a required side stays exact. This is still code availability, not physical or runtime acceptance.

## Evidence boundaries

The 11 candidate profiles/330 digital cells/473 native inputs/18 links were read back again and deterministically rebuilt, with no delivered native bytes changed. Both native families were also compared against the supplied 18-profile HISTORICAL backup, not the live Windows store. Preflight tests use synthetic faults and exact archived inputs; no live Windows config was available. The existing 208 source-scoped action records are unchanged; there are no new complete game tables in this supplement.

All supplied original and R8 files remain unchanged. JSON operational comparison is not byte-for-byte native export equality; metadata and operational changes are separated explicitly. Private receipts can contain profile names/IDs and belong in Drive, not public Git. Real-browser rendering, native import, physical reach, game behavior and another Codex task's actual consumption are not claimed.

## Primary technical documentation

Python JSON documentation explains duplicate-name handling and `object_pairs_hook`: https://docs.python.org/3/library/json.html . The custom rejection is an application decision; it does not establish a game's override rules.

Python XML security notes: https://docs.python.org/3/library/xml.html#xml-security . The collector continues to reject DTD/entity declarations and applies size/structure bounds. This is not a general security certification.

Microsoft virtual-key table distinguishes generic and left/right modifier codes: https://learn.microsoft.com/en-us/windows/win32/inputdev/virtual-key-codes . It does not prove that PoE2's unresolved flags use Windows semantics; the collector still does not assume that.

The tool-overlap hints are grounded in the existing owner `docs/GRAPHICS-CONTROLS.md` at the R8 publication revision, not detected software state.

## Delivery and continuity

Authored tools and sanitized QA live here; native payloads, historical review receipts, exact prior recovery and generated views remain private. The full preflight package includes the unchanged profile ZIPs and R8 recovery so no user transfer or new profile creation is needed. `PUBLICATION_RECEIPT.json` records actual upload/readback and source-coordination states after publication, separately from the immutable archive. The earlier copy-ready Codex opening remains usable: read the current R8 coordination entry, which points here first.
