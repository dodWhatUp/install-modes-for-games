# R4 — audit of the unchanged R3 layout against the inherited game corpus

Status: **completed scoped offline audit; native implementation blocked on current export**.
This is an audit object, not an accepted map, native profile, or new research master.
Owner: `dodWhatUp/install-modes-for-games`.

## Inputs and scope

- R3 map: `../layout_candidate.json`, exact Git blob
  `b689507023491d7eafb28dd886a18923dbf2ae08`. The map is unchanged.
- R2 delivery input: `Azeron_Research_R2_HE.html`. The complete `const data`
  JSON payload is decoded without executing the inherited page.
- 94 scoped game/edition/layout records and 2,195 original binding rows were
  processed. Every inherited row is preserved without field changes.
- Exact input SHA-256 values and byte sizes are in `AUDIT_RECEIPT_R4.json`.
- This does not reconstruct or merge `AI_MASTER.json`. R1 and R2 retain their
  existing ownership and source qualifications.

## Results and their units

2,167 raw key expressions were parsed under the explicit parser rules; 28
remain for manual review. There are 3,106 expanded listed input variants.
These are not 3,106 independent actions, and no compatibility percentage follows.
A slash can separate different actions or alternative bindings. A missing variant
can have a usable alternative on the same row.

| Flag | Rows containing at least one flagged variant | Games |
|---|---:|---:|
| No single bank contains the chord | 1 | 1 |
| Same-finger/selector conflict in the conservative model | 26 | 17 |
| Output not in the map | 25 | 13 |
| Symbol requires keyboard-layout review | 12 | 9 |
| Stick output used for a nonmovement command | 51 | 19 |
| Expression requires manual review | 28 | 14 |

Groups overlap. Counts are diagnostics, not quality scores. The movement/command
role classification is an action-label heuristic. Some flagged commands are
perfectly reasonable to perform deliberately after releasing movement.

## Material findings

1. **Ordinary letters can be game modifiers.** Atelier Yumia documents C plus
   1/2/3/4 for party changes. C+2 and C+4 collide in the R3 finger hypothesis.
   Duplicate Ctrl/Shift positions in Numbers do not solve this requirement.
2. **Same bank matters.** The inherited Elden Ring pouch row uses E plus arrows.
   E is only on Basic and arrows only on Letters. This row was not promoted to
   a freshly verified current default. No held-key carry-over across banks is assumed.
3. **WASD existence is not independent command access.** OpenTTD documents A as
   Autorail and W as raise-land, while arrows pan the map. A stick-only route
   is not four independent digital command buttons. Evaluate a generic grid
   base or a small supported game-side adaptation only when actually needed.
4. **Regressions are not all hypothetical.** OpenTTD documents Shift+F2 and
   Shift+F8. These are among the R3 model regressions previously disclosed.
   Wo Long's Shift+C also exposes a Basic rather than Number-bank conflict.
5. **Numpad and symbols are different issues.** Numpad inputs stay distinct.
   Symbols such as plus, tilde and question mark remain keyboard-layout review,
   not an invented US-layout mapping or proof the output is impossible.
6. **Layered does not mean immediate.** GW2's documented healing key 6 still
   lacks a direct Basic copy. Its game-side remapping options can be considered
   before creating another whole mapping family.

## Targeted source checks

`source_checks.json` records seven scoped checks across six primary URLs.
Fourteen inherited rows in five games received a focused primary-source check;
the other 2,181 did not receive a fresh online source audit in R4. The sixth URL
is Azeron documentation, not a game control table.

Atelier Yumia key icons were visually inspected. Other source facts were read
from publisher/project manuals. Source fact, design inference and limitation
are separate fields. The Elden Ring finding remains explicitly inherited.

A row-isolated audit does not infer every cross-row dependency. FAIRY TAIL 2's
held Tab plus skill-key relationship remains a derived scenario in the earlier
R3 cases; the new corpus audit supplements rather than replaces those cases.

## Model and checks

One independent output per hypothesized finger; secondary banks reserve the
little finger for a held selector after recognition. Stick movement reserves
the thumb; mouse inputs belong to the other hand. Exact left/right modifier
requirements are retained, but logical routing cannot validate emitted sides.
Additional movement is a stress case, not a universal gameplay requirement.
Same-column conflict is not proof the user's real hand cannot operate both switches.

The audit passed 18 parser unit cases, 19 routing assertions, full raw-row
preservation, independent count checks and a repeat-run equivalence check.
The HTML's embedded rows match all 2,195 inputs; JavaScript syntax passed.
Opening the local file in the testing browser returned
`net::ERR_BLOCKED_BY_ADMINISTRATOR`. That browser access was not retried or
bypassed. No rendering or interactive-filter verification is claimed.
Static content/code checks are the stated fallback, not equivalent assurance.

No screenshots, global input recording, device testing or game launches occurred.
No native profile, game setting, firmware or user preference was changed.

## Reproduce and delivery

Python 3.10+ standard library is sufficient for the audit and report generation:

```text
python3 build_corpus_audit.py --corpus-html Azeron_Research_R2_HE.html --layout ../layout_candidate.json --out .
python3 test_corpus_audit.py Azeron_Research_R2_HE.html ../layout_candidate.json
python3 render_audit_report.py .
```

Obtain the named R2 delivery input from the existing private Azeron archive.
The generated `CORPUS_AUDIT_R4.json`, `SUMMARY_R4.json` and Hebrew HTML are
read-only delivery views/results, not competing editable research masters.
The portable package includes the verified R3 map as a comparison snapshot.
`QA_R4.json` records this run's results. Re-running the corpus tests rewrites its
corpus section; UI checks must not be marked passed merely by regeneration.

## Next implementation boundary

The missing input remains a **fresh native Azeron Software v2 JSON export of
the active software profile collection, including all four layers and their
links**. The current device listing exposed only a Mac, not the Windows gaming
computer. The inspected backup folder contained historical native exports,
not a fresh v2 collection. These are bounded access findings, not an exhaustive
claim about every file or computer the user owns.

Do not create another arbitrary map revision or an importable file from guessed
hardware IDs. Read the current native export, reconcile later user changes and
selected gestures, preserve it, and prepare a separate candidate. Then verify
press/release transitions and the consequential same-finger combinations before
any game-specific adoption. No new model or effort setting is required or changed.
