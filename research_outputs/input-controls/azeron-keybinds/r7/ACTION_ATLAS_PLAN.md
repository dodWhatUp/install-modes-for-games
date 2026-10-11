# Action Atlas: display/knowledge module for the existing game toolkit

Status: R7 local HTML query prototype implemented; host integration and live overlay are future work. Not a new remapper, shell runner, standalone task queue or replacement architecture.

## Canonical integration

Owner repository: `dodWhatUp/install-modes-for-games`.
Consume and extend the existing design in:
- `docs/GAME-TOOLS-ARCHITECTURE.md` — shared core and keymap build gate.
- `docs/GAME-TOOLS-KNOWLEDGE-INDEX.md` — source/recovery navigation.
- `docs/TOOL-RESOURCE-OVERHEAD.md` — cost definitions and existing provider ownership.
- `examples/game-tool-hub/README.md` — Python registry/read-only coordination foundation.
- `examples/game-input/OVERLAY-STUDIO-INTEGRATION.md` — actual Studio2 host lineage.
- PR4 / `docs/AZERON-GAME-KEYMAP-VIEWER-WISHLIST.md` — existing action-label request, still distinguish draft versus accepted source.
- `templates/GAME-KEYBINDS.example.json` — schema-2 mapping and three diagram views.

The toolkit owns workflows/capabilities; native Azeron/reWASD owns input transforms; the Atlas owns display metadata and source explanations. No production code, running host or registry is modified merely by publishing this plan. No unrelated Unified Personal System repository receives a duplicate master.

## Data flow

Native snapshot + verified geometry → immutable output model → game/default/effective bindings → reviewed action/category/icon annotations → validated render snapshot → passive or interactive display.

Keep each arrow explicit. An action label must cite the binding evidence that joins an exact native output to an action in the selected context. `action_id` is a semantic identity; an optional `recipe_id` links to an existing prepared tool capability and is never itself executable authority. Clicking an icon may explain an action or prepare a plan; it must not synthesize the game action or run a script.

R7 consumes exact R6 geometry. A future game switch must leave native profile and geometry/output hashes unchanged. Mismatched versions produce an unknown/stale state, not the nearest-looking map.

## Visual grammar

- Keep all 29 permitted digital controls at stable positions; include little-finger side #36 and lower #37. Hide reserved #19 and the joystick illustration only. Empty physical positions remain visible.
- Show action name plus optional pictogram, exact key/chord and optional native ID. Keys-only, actions-only and combined remain selectable.
- Category accent belongs to action semantics, not the raw letter. The same F key can be a healing action in one game and a utility in another. Bank identity stays in the header; do not give layer color and action color contradictory meanings.
- Movement, weapon switching, combat/abilities, interaction/items, menus/navigation, camera/information, communication and system have a small consistent vocabulary. Use neutral treatment for unknown/mixed contexts. Category tags are reviewed interpretation, not a game fact.
- Icons and color are optional. Keep text/shape/legend alternatives; color cannot carry meaning alone. Ensure text/icon contrast at the intended scale. Dense artwork is not automatically more recognizable than a simple symbol.
- Start with original generic vector icons. Miniature game artwork is optional later, with provenance, version/hash, usage rights and text fallback; do not scrape assets or invent game-specific icon meanings.
- A held modifier/ordinary letter and an action chord must show the requirement (e.g. Space+1), not just an action under 1. Do not hide V+direction merely because the joystick is not drawn.
- Search/filter dims nonmatches in the physical view, never reflows or sorts its buttons. A separate results list may group actions by category, bank, context or evidence quality. Unknown does not mean unsupported.

## Two interaction modes, not a held-search trap

**Peek:** a momentary, non-focus-stealing picture/overlay while the authorized trigger is held; release dismisses. No typing or clicking into the game from this display. Native #19 is only reserved so far; it emits no keyboard key. Determine its trigger integration through a supported existing host route, with an explicit approved output or raw-device adapter. Do not invent F13/F14 bindings.

**Explore:** an explicit pin/open action allows normal focus, search, filters and detail panels. Release of the peek key does not unexpectedly dismiss an intentionally pinned search. Clear mode text and one close/cancel route return focus safely. Do not require holding a hardware selector while typing a search. This mode is a future host behavior; the R7 HTML simply demonstrates ordinary manual exploration.

## Search and discovery

Use exact actions, key/chord strings, curated synonyms and localized aliases first. Result → layer selection changes the displayed bank only. Optional fuzzy/semantic matching returns existing source-backed IDs, highlights uncertainty and never creates a new binding. Add filters for category, context, character, held/tap/chord, layer, evidence status and known conflicts. Show the exact configuration/source revision and a direct detail link.

Do not infer actual active layer from a shared keyboard output. Until a reliable native adapter provides fresh events, display Selected or Unknown. Future executable associations are an opt-in allowlist, labels-only, with expiry and manual override. No process-wide keyboard interception or automatic native profile changes.

## Existing-toolkit interface proposal

Add a namespaced `keymap.atlas` capability descriptor to the shared catalog in a later reviewed integration. Minimal operations: `inspect_snapshot`, `validate_labels`, `search_actions`, `render_view`, `prepare_explanation`, `export_review`. All declare side effects NONE except an explicit file export to a chosen private directory. No arbitrary command field or network listener is necessary.

A render snapshot contains schema/revision, game/preset/context, device/geometry/native fingerprints, selected versus observed layer state, source/annotation revisions, visible controls and evidence warnings. Keep original observation clocks and expiry when actual runtime data is introduced. A rejected/stale snapshot leaves the last known view visibly stale rather than silently merging new labels with old outputs.

Batch source reads and cache by hashes. Build category indexes and layout projections away from AHK callbacks. The host callback should use a prepared lightweight snapshot, not parse manuals or invoke a model. Measure the added CPU/RAM/GPU/VRAM cost with existing toolkit providers before making a low-overhead claim; the prototype's small file size is not that measurement.

## Incremental build and acceptance

1. **Current local prototype:** manual game/context/bank; source detail; icons/color options; source-backed samples; immutable R6 output. Tests are query/data contracts, not browser or hardware acceptance.
2. **Schema adapter:** map optional Atlas display extensions onto schema-2 bindings; reject unknown IDs, altered outputs, missing sources and incomplete effective-state claims. Preserve existing template fields.
3. **Host display integration:** read-only snapshot consumption by the existing Studio lineage; preserve original methods/settings and rollback. Verify launch/stop/focus/peek/pin/cancel with the actual host before game tests.
4. **Effective game reconciliation:** prioritize PoE2 and Cyberpunk input configs/overrides, then the remaining requested scopes. Public published-default samples are an explicit alternate evidence mode, not effective controls.
5. **Optional runtime selection and recipe links:** fresh native-layer observation and user-enabled executable selection; links to existing prepared workflows, with separate authority for execution. No background activation by this roadmap.

Acceptance covers 29 IDs per view, reserved #19, no joystick illustration, blank-cell masks, profile/output-hash invariance across game switches, required chord display, stale/unknown evidence, category/icon fallback, keyboard-accessible exploration, window/focus cancellation, and preservation of actual user settings. Export after each material accepted stage; report source, native, physical and game verification separately.

## Recovery and lifecycle

R7 is additive. Keep original R6 packages and live R5/native backups as exact dated inputs. Code/annotations live in Git; private native exports/assets remain in existing Drive storage. Use the single owner index and a compact current handoff, not a second queue. Old inaccurate generated posters remain excluded from source inputs. A future integration failure rolls back only the optional Atlas adapter/view, not all native profiles or the whole toolkit.
