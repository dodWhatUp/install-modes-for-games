# R8 Windows consumption and read-only input receipt — 2026-10-11

This Windows Codex chat consumed source head `b827c7f35e3aee85690842d945c0664a7ad397e9`, the full decision memo, decision brief, checked preflight, R8 publication record and existing Studio/Hub contract. **Family installed: NOT_INSTALLED.** No family was selected. This receipt does not retry or replace the blocked `preflight/PUBLICATION_RECEIPT.json`.

The existing private Drive route supplied the complete preflight and decision-review packages. All 33 preflight manifest entries and nine review entries verified; original source bytes matched the pinned Git head. CORE5, SPARSE6, R8 recovery and earlier nested recovery remain unchanged. See the [sanitized receipt](../evidence/AZERON-R8-WINDOWS-READ-2026-10-11.json) for exact hashes, counts, files read and limitations. Review calculations were consumed as existing findings, not rerun as new research.

## Current input evidence

| Source | Observed scope | Unresolved boundary |
|---|---|---|
| PoE2 config | 97 ACTION_KEYS and 97 WASD_ACTION_KEYS; 14 action records differ | GENERAL fields say `wasd`, while UI `use_wasd_to_move=false`; no active bank is selected. Modifier token `2` is undecoded. Skill slots do not reveal equipped skill names. |
| Cyberpunk UserSettings | 92 explicit IK records; Quick Save `IK_F5`, Quick Load `IK_F6` | Saved candidates do not establish effective runtime behavior. |
| Cyberpunk mappings/contexts | 855 IK mapping records, 723 action/map references; 242 overridable button joins, 227 with saved candidates | Includes, context priority, packed/mod overrides and effective remapping remain unresolved. Context XML has no direct IK records; that is not an empty control scheme. |
| Native saved store | 23 SOFTWARE profiles, including four SHARED R5; no R8 names/IDs; all saved layer targets resolve | Native app was not running. This is a bounded file snapshot, not a live app/UI export or onboard verification. |

Configured tool owners remain F12 CET/Ultra+, F9 GraphicsHotkeys and Delete ReShade. The reWASD engine was present; active device/remap state is unknown. No installed input path is inferred from process presence. No complete packed-mod input audit or effective merged game preset is claimed.

The newer separate PoE2 COMBAT/MENU proposal remains uninstalled. Its UI work stopped on user Escape, and its proposed F15 trigger is unresolved. This preparation neither resumes that work nor assigns a trigger to #19.

## Windows fixes and checks

The unmodified collector rejected both configs before reading bytes. A modified synthetic file reproduced Windows Python 3.12's path/handle `ctime` mismatch. The [safe reader](../research_outputs/input-controls/azeron-keybinds/r8/preflight/safe_io.py) now compares birthtime across those APIs, retaining independent path/path and handle/handle `ctime` checks, inode/device/size/mtime identity, regular-file checks and reparse refusal. Python documents changing Windows timestamp semantics in its [stat reference](https://docs.python.org/3.12/library/os.html#os.stat_result); the exact cross-API mismatch was observed locally.

The first rehearsal then stopped because the Atlas builder read UTF-8 JavaScript using Windows cp1252. Explicit UTF-8 source reads fixed that failure. Original immutable packages were preserved; these are separate authored source fixes. Both initial failures remain in private evidence. A 23-profile aggregate JSON review exceeded the conservative structural bound, so the same byte-preserved source files were supplied in the documented v2 ZIP layout; no bound was raised.

- Seven [Windows metadata regressions](../research_outputs/input-controls/azeron-keybinds/r8/preflight/test_safe_io_windows.py) passed, including modified-file success and rejection of identity/birthtime substitution, handle/path change and reparse metadata.
- Existing preflight: 46 passed, two symlink-creation tests skipped because the platform denied fixture creation. Mocked reparse refusal passed separately.
- Atlas: 13 additional checks, 37 query contracts and 16 DOM assertions passed. All 208 action records and native design stayed unchanged.
- Full corrected offline rehearsal passed. Both families are absent in the current supplied snapshot; neither was imported.
- Two native snapshots and final source reads verified all 23 profile files and two global files unchanged. Four input config hashes and five additional input/tool sources matched their prior reads.

Physical output, held continuity, release order, comfort, effective gameplay, live layer observation and Peek/Explore remain NOT_RUN or UNKNOWN. No game launch, save access, input dispatch, recording, debugger, setting/profile change, scheduler or background task occurred. The dirty primary checkout and unrelated source masters were not edited.

## Recovery and next boundary

The [archive receipt](../evidence/AZERON-R8-WINDOWS-ARCHIVES-2026-10-11.json) identifies the separate private evidence and authored-source checkpoints, exact hashes and owner-only permissions. Downloaded Drive bytes matched both local archives. This receipt/navigation link postdates the immutable packages; the eight-file source checkpoint does not claim to contain the entire later commit.

Private recovery covers selected input receipts and bounded native source snapshots. It excludes full original game configs, hardware/onboard state and a complete native UI backup; restoration was not tested. Existing complete recovery packages remain separate. No runtime rollback is needed; source rollback removes only this isolated compatibility patch and documentation, preserving newer work.

Next: resolve consequential PoE2 mode/modifier and Cyberpunk context/remapper uncertainty, then record one family choice and separate installation authority. SPARSE6 remains the first preference-fit candidate while nine blank finger cells are required; raw test totals do not choose a family. After that gate, take a fresh complete supported native backup, import only the chosen family's individual JSON files additively, independently review all profiles/return targets, then perform the relevant physical tests with games closed. Deferred benchmarks and separate PoE2 UI work remain deferred.
