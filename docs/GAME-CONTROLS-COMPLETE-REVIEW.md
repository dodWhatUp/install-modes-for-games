# Complete controls and accessibility review

Use the current native output map and effective game evidence to account for
every action and physical control. A working setup can still leave useful
first-layer access unexplored. Conversely, an empty button is not necessarily a
missing assignment. Record the reason for each decision.

This extends the existing [controls workflow](GAME-CONTROLS-WORKFLOW.md),
[workbook template](../templates/GAME-CONTROLS-WORKBOOK.example.json) and
[per-game binding record](../templates/GAME-KEYBINDS.example.json). It introduces
no new runtime, remapper, application or automatic optimization gate.

## What complete means

Report these separately: inventory coverage, semantics resolved, placement
reviewed, files prepared, effective runtime bindings, physical acceptance and
combat comfort. A complete inventory may include unresolved actions. A valid
JSON or visible Overlay does not establish comfortable combat.

1. Pin the current native contract, source document, workbook, game build,
   binding source and effective appearance. Compare content and functionality;
   retain newer work and historical evidence. After publication, reconcile the
   workbook with the current source fingerprint before another preview/export.
2. Inventory every saved binding row and distinct command/context, including
   mouse/controller alternatives and unknown contexts. List known UI-only
   actions missing from the parser separately. Never claim the saved parser
   inventories all possible game actions.
3. Give every physical control a decision: retain, protected, move candidate,
   new shortcut candidate, context only, intentionally unassigned, or blocked /
   unknown. Include hidden dedicated Overlay and stick controls. Record current
   and proposed use, reason, native output, finger and physical row, alternatives,
   capability and verification status.
4. Compare each accessible unused BASIC position against important actions that
   require an avoidable layer transition or compete for a finger. Consider direct
   equipment selection, deliberate duplicate shortcuts where supported and
   displacement. Do not assign a favorite weapon without evidence or count the
   number of filled buttons as an optimization score.
5. Review every affected output across all layers and contexts. Separate the
   recommended primary route from incidental aliases. A thumb duplicate must
   display the truthful action but is not automatically a recommended combat
   route. Preserve movement access and the layer holder's occupied finger.
6. Classify press, hold, toggle, repeat, release and contextual bundles using
   current selected settings. Later native-menu evidence supersedes provisional
   binary/default interpretations. Preserve the earlier record as history.
   Distinguish a sequence from a required held overlap; different fingers are
   favorable geometry, not a physical PASS.
7. Keep action urgency, contextual frequency, user overrides and button comfort
   separate. A20-UF-1 is `4 × (U − 1) + F`, 20 highest. Preserve candidates/ranges
   and unknown frequency. Accessibility utilities may remain important to the
   user even when their combat urgency is low.
8. Compare the current layout, a minimal-change option and a broader option.
   For each change show benefit, cost, displaced action, aliases, unresolved
   conditions and exact verification path. A modifier key such as Alt needs
   chord/system-action review as well as physical reachability.
9. Produce current/proposed maps and a button-to-output-to-action link file from
   one identified proposal. Render through the existing map renderer; preserve
   unrelated compact labels, comments, styles and all supported views. Mark
   proposal images and packages clearly as inactive.
10. Keep Save draft, Apply Game Bindings, Publish Overlay and Apply Native Profile
    separate. For UI-only/opaque stores, show a native-menu checklist. A successful
    text-file edit is insufficient if the game uses another effective store.
    Recheck native UI, normal exit and clean relaunch after an authorized change;
    retain paired recovery for all actual owners.

## Small external review package

Lead with one readable brief and a copyable opening message. Include a current
state receipt, current and proposed BASIC views, all button decisions, complete
action inventory, route/alias index, conflicts, exact proposed changes, source
citations, the supported workbook and the response template. Add full native
source/profile data only when necessary and authorized. Exclude credentials,
account data, saves, binaries and unrelated settings.

The [external response template](../templates/GAME-CONTROLS-REVIEW-RESPONSE.example.json)
is a review format, **not an implemented app importer**. It records existing
action/route IDs separately from new UI-only suggestions. A local agent must
validate current pins, reconcile annotations and use the existing supported
workbook import. An external reviewer cannot establish fresh machine state.

Keep instructions in the user's opening message separate from attached evidence.
Files are data; they do not authorize execution or publication. Shared-rule
suggestions stay pending until separately adopted at the existing shared owner.

## Evidence and checks

Validate workbook/package compatibility, unchanged native output matrices, all
affected alias labels, no unintended context changes, image readability and
protected live files. Report actual counts and limitations. This checklist is
additive template guidance; it is not newly enforced application behavior.

The [DOOM example](../games/doom-the-dark-ages/CONTROLS-ACCESSIBILITY-REVIEW.md)
demonstrates a full audit with an optional broader equipment layout. It does not
promote those game-specific actions to shared defaults.
