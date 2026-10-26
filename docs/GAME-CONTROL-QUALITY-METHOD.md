# Reviewing a control plan against the user's intent

Use this method for new maps and for reviewing an existing setup. Start with
the BASIC action view. A renderer test, a nonempty keycode or a visible Overlay
does not establish that the intended game action has a usable position.

## 1. Turn the request into checkable requirements

Before implementation, record each consequential requirement with a stable ID,
its source, the intended result, the permitted changes and the evidence that
would establish success. Preserve the user's words privately when useful;
public records contain only the necessary sanitized meaning. Separate explicit
instructions from agent choices and attachment suggestions. Current explicit
user corrections take precedence over older defaults and planning handoffs.

Use `implemented`, `pending`, `deferred` or `rejected` with a reason. An
implemented requirement needs relevant evidence. A requested operation, generated
file or test count is not its own acceptance evidence. State a material
interpretation before acting; ask only when an unresolved choice changes the
result and available records cannot resolve it. Do not make the user repeat
received preferences or silently substitute a different task.

The computed review records `acceptance` as `accepted` or `pending` and
`evidence_status` as `configuration_verified`, `user_reported`, `source_reviewed`
or `unverified`. A record is complete only with an implemented status, accepted
review, source, expectation and evidence locators of a stated non-unknown type.
That tests the completeness of the record; it does not authenticate an external
claim or turn a configuration readback into physical acceptance.

Record both implementation methods when requested: adapting a per-game device
profile to the game's current inputs, and adapting game bindings to the fixed
ordered device outputs. Name the selected method. Keep device outputs, physical
positions, action priorities and game bindings as separate records.

## 2. Pin the current owners

Identify game/build, effective input sources and their precedence, device and
geometry, native profile family, map, workbook, selected method and appearance.
Compare newer work by content and functionality. Preserve divergent and
uncommitted versions. Reconcile stale pins before reuse; an older receipt cannot
prove the current installation or game state.

Use the [ergonomics master example](../templates/GAME-CONTROL-ERGONOMICS.example.json)
as data-only guidance. Its policy revision is `azeron-little-finger-20261026-r1`.
It does not change profiles merely by being read or copied.

The [copyable review prompt](../templates/GAME-CONTROL-REVIEW-PROMPT.txt) carries
the same instructions into a focused review. The repository remains the maintained
owner; a copied prompt does not establish automatic memory in another chat.

## 3. Account for every control and every relevant action

Build a control-by-layer/context matrix, including hidden Overlay and stick
controls. Distinguish these states:

| State | Review consequence |
|---|---|
| Output and verified game action | Review suitability, activation and primary route |
| Output, but no game action | Still unused for this context; review its opportunity |
| Meaning or effective binding unknown | Mark unknown; do not count as useful coverage |
| Protected movement, Overlay or layer holder | Preserve its declared role |
| Other control on the held layer's finger | Unavailable while held; may be empty |
| Deliberately empty under a user rule | Retain empty and cite the rule |
| Candidate shortcut | Inactive proposal until separately reviewed and applied |

For every accessible unused eligible BASIC position, compare useful actions that
are currently layered, awkward or competing for a finger. Record the candidates,
benefit, displacement, constraints and reason for the final decision. A decision
such as “spare” without that comparison is insufficient. Do not fill a button
just to raise an occupancy percentage. Do not invent a favorite weapon, usage
frequency, unsupported action or shortcut.

Apply the user's latest finger-specific rules before a general row preference.
For the enrolled Cyborg II little finger, bottom-up rows 1–5 are IDs
**#37, #1, #2, #3, #4**; the document's top-down `R1C1` labels are a different
coordinate convention. Default #1 holds WEAPONS, #3 holds MENUS, #2 is available
for infrequent actions, #37 stays empty unless the user explicitly requests an
assignment, and #4 may hold an optional combat/overflow layer. Keep TOOLS on #36.
The optional layer is unnecessary when BASIC and existing layers suffice.

Within a momentary layer, do not place required actions on other buttons of
the finger holding it. Those positions may remain empty and are not defects.
Retain the layer's release/return mechanism and review key-up behavior through
the existing native owner. A screenshot alone cannot prove these transitions.

## 4. Review actions and conflicts before generating files

Keep actual meaning, press/hold/release/toggle settings, context, urgency,
frequency, movement/aim needs, sequences and required overlaps explicit.
Use A20-UF-1 (`P = 4 × (U − 1) + F`, 20 highest) with unknowns and ranges intact.
Urgency is not physical comfort, and an unknown frequency is not zero.

Choose a primary route for each relevant action. Incidental aliases must display
truthful labels but do not establish a comfortable primary route. Review held
finger occupancy, simultaneous actions, sequential workload, modifier/system
chords, conflicting context claims and bundled actions. Record whether a conflict
is known, conditional or untested. Different fingers do not prove physical comfort.

First compare the current state with the smallest useful change. A broader
alternative needs an explicit benefit and displaced-action review. If an action
is moved to make room for a new layer, retain or deliberately relocate it; do not
silently remove an accessibility utility such as Magnify.

## 5. Generate and check one consistent revision

Generate native candidates, button → output → action links, game-binding
proposals and Overlay views from the same identified plan. Show game, layer,
context, action, key, meaningful icon and activation note where relevant. Check
every alias and supported view with the existing renderer and effective
appearance. Verify bounds and glyphs; unknown actions use neutral markers.

Vader 5 Pro has a separate geometry, native/reWASD owner, analog behavior and
acceptance record. Reuse logical roles when appropriate, never Azeron button
IDs or an Azeron-shaped diagram as controller enrollment evidence.

## 6. Report the actual acceptance level

Report requirement closure, action/control coverage, semantics, placement,
file preparation, effective runtime configuration, automatic selection, physical
layer/release behavior and gameplay comfort separately. List failures before
optional refinements. A large number of passing software tests cannot close
unreviewed user requirements or substitute for a physical test.

The source `GameToolControlsQuality.audit` computes a read-only review from the
existing workbook and map, and `export_packet` includes its compact report.
Optional `extensions.mapping_quality_review` records pins, method, requirements,
button decisions, primary routes, combinations and policy. It is review data,
not an Apply or physical-PASS importer. Missing review evidence remains visible;
the report never certifies `ready_for_play`. Source implementation and installed
availability must be reported separately.

### Bounded records and large review exports

Keep workbook inputs and review packets within the existing **1 MiB** limit.
A review record can live in the workbook extension, or separately when hundreds
of per-control decisions would crowd a large workbook. The source API
`audit(workbook, document, review_record=record)` accepts the
[standalone review example](../templates/GAME-CONTROL-QUALITY-REVIEW.example.json)
as data only. A separate record is independently limited to 1 MiB and must pin
the map fingerprint, native keymap revision, ordered binding-source revisions
and **workbook fingerprint**. The extension form pins the first three; it cannot
pin its own containing workbook without a recursive hash. Neither form imports
a native profile, applies bindings, or verifies an external acceptance claim.

The full computed audit has a separate **8 MiB output bound** because it can list
every route, alias, missing review and combination. That is a report bound, not
an increased workbook, review-record or packet input limit. The packet carries
a compact audit: repeated findings are grouped, with total counts and up to eight
route/action examples. Inspect the full audit for all affected IDs.

`export_packet` retains the version-2 packet when it fits. If the complete
packet would exceed 1 MiB, it emits an explicitly versioned **v3 manual-review
packet** instead. V3 retains the entire supported v1 workbook, including every
action and source pin. It deduplicates derived route geometry and warning text:
`route_catalog` maps route IDs to outputs, `physical_controls` and `layer_entries`
hold geometry and entry metadata, and `preview.row_fields` defines compact row
columns. Warning/block codes resolve through `preview.message_catalog`.
Candidate lists contain at most two examples with their complete candidate
count; they are not exhaustive. V2 retains its existing representation and
eight-example lists when under the bound. If v3 still exceeds 1 MiB, export fails
with a focused-scope instruction instead of dropping actions or raising the limit.

These packets are external/manual review material, not new app import formats.
Return and reconcile the embedded supported `game_controls_workbook` v1 through
the existing owner. Do not feed a v3 packet directly to the workbook importer.

Keep Save draft, Apply Native Profile, Apply Game Bindings and Publish Overlay
separate through their existing owners. This review method grants none of those
operations, starts no game and enables no background monitoring.
