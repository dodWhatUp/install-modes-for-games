# Keybinds 0.2.0-preview.1 — integration handoff

## Exact owners and bases

Canonical owner: `dodWhatUp/install-modes-for-games`; **not** the architecture repo.
Existing owner source/read guidance is unchanged by this local candidate. The
read-only path comparison from prior Git main `d44f9cee6782d1228d20610a08b404ee44a3aff8`
to `043f3c4733788f082da98dfcb43c0972d2794c6a` showed unrelated research changes.
No branch, merge, repo initialization, repin, deployment or Git write was performed.
Prior Git/remote safety blocks remain stopped. Do not bypass them for this handoff.

Add-on base: `GameTools_Keybinds_0.1.0-preview.1_Source_and_Handoff_2026-10-13.zip`,
SHA-256 `1106d7746af4572c9948a98e9f27c11a490c8fe644426a2c537e3e5552f601b1`.
This package is its full updated add-on source, not an application update ZIP.

Current host used for compatibility testing: **0.23.0-preview.1**, not 0.21 or the
old Hub 0.2.0 in the knowledge repo. Exact source:
https://drive.google.com/file/d/19Zq9XyDkkz0SuqgMrwnP6Lvjdn-VwjLn/view
Archive SHA-256 `bc7ea76ba5379b83dddc9a7f78e80710e46a5227eca073db131e3257dc0c8d37`.
201 host payloads + manifest verified; host source remains untouched.
Current continuation owner record:
https://drive.google.com/file/d/1sbAoFn3o2SYfOhphZccMn9S2VGbpPdVA/view
Read it again at integration time for later work. The source preview is not proof
of the user's current installed Windows version. Preserve later/concurrent work.

## What to read

`README.md`, `docs/GAP_AUDIT.md`, `docs/EXTENSION_GUIDE.md`,
`validation/final/VALIDATION.json`, `validation/SOURCE_PRESERVATION.json`,
`validation/SOURCE_DELTA.json`, `docs/DEPENDENCY_PINS.json`, and the owning
Workbench review, main game-tools knowledge index and existing GT checklist.
Historical `validation/previous-0.1` is retained explicitly as dated evidence.
Do not create another canonical master, queue, approval store or game ID namespace.

## Integration actions — source composition, not live overwrite

1. In the existing owner's isolated task copy, verify current host and this add-on
   manifest. Reconcile competing writers and existing keybind/controller integrations.
   `scripts/check_host.py --host HOST` reports exact tested dependencies; a difference
   requires focused review, not auto-replacement or copying compat modules over host.
2. Add `scripts/game_keybind_ops`, `GameToolKeybindIntegration.py`,
   `GameToolKeybindAI.py`, `GameToolKeybindWorkspaces.py` and the operator CLI. Keep
   host GameToolJournal, GameToolAutomation, GameToolAI and game_mod_ops/safety as
   owners. The compat copies are byte-identical fallback derivatives for standalone
   testing only. Do not install them over current host modules.
3. Mount `game_keybind_ops.panel.attach(..., service=shared_service,
   busy_guard=existing_guard)` in the current UI. Reuse existing Stop/close lifecycle.
   It now includes pack onboarding controls and a compact Authoring menu. Associate
   the same selected game identity with the host inspector; do not create new game
   stores. Keep originals, overlays, Azeron native profiles and existing modes intact.
4. For game-scoped automation, compose `KeybindGameWorkspaces` in place of the
   original factory in the **source task copy**, retaining its runner and mod
   catalog. `game_rows()` combines existing IDs with imported keybind packs;
   `keybind_context()` supplies their bounded view. A keybind-only game has no
   fabricated mod recipe and cannot create mod or overlay operations. Existing
   mod-enabled scopes retain original mod planning. The inherited generic approval
   controller pins the actual bootstrap recipe as a transport dependency only;
   it is not exposed as another game's mod content.
5. Route keybind request reviews/approval through this composition's
   `request_review`/`approve_request`, the same local queue and the existing runner.
   Do not call the writer from AI. New endpoints only preview/read/propose;
   `keybinds.draft_pack` and `keybinds.edit_draft` require local approval and create
   unreviewed immutable drafts, never imported/activated native configurations.
6. Runtime game packs can live in the owner's existing
   `examples/game-tool-hub/keybind-packs/` source area, one data folder per game.
   Explicit local imports pin them under the SAME host data root `keybinds/packs`;
   active originals are locally bound to immutable `instances` records. These are
   derived local execution records, not a second research master. Use existing
   owner routes for knowledge, source and private backups; do not commit raw game
   configs, private paths, saves, credentials, proprietary binaries or archives.
7. Update the owner's existing source exporter allowlist and tests to include these
   additions only after reviewing current root rules. This outer ZIP is not accepted
   as a full application update package. No installer, scheduled task, game launch,
   driver change, auto-updater or screen capture is authorized by its contents.
8. Run the unchanged original host tests plus this module's tests and appropriate
   Workbench/UI source integration tests. Then, through an authorized Windows route,
   test launch, local approval/Stop, known current config copy and exact rollback.
   Windows, actual game acceptance and live MCP/ChatGPT client binding remain separate.

## Extensibility contract delivered

Data pack schema 1, explicit native codec per shared keymap, stable identities,
contexts/slots/variants, scalar effective-file precedence, optional read-only defaults,
sparse override insertion, named/semantic intents, pinned revisions and fixture tests.
Ten built-in text routes + explicit trusted text-adapter SDK. All use the same
transaction/backups/approval/journal and declared process guards. Pack ZIP import
cannot load code, write a game or self-approve. A new hypothetical game was processed
end-to-end with only a new pack folder while all source Python hashes stayed identical.

The 17 inherited research drafts remain unready and include their prior evidence.
No current game config, binary/save schema, Registry writer, full Unreal array/include
resolver, active-instance pack upgrade or real-game support was invented.

## Tests and acceptance

**472 test methods passed** in the final reproduction:
109 original core, 22 original extended, 9 original pane, 35 original AI integration;
78 new extensibility, 31 new effective/registration/preset, 9 new pane and 27 new
Workbench/AI/draft tests; 52 original host automation, 59 host journal and 41 host
workspaces regressions, run unmodified. The 145 new methods include ten format
roundtrips, a new game without core edits, cross-file swaps/dependency drift,
selective sparse undo, game-scope isolation, incremental draft base preservation,
strict pack ZIP handling and new Tk callbacks. Original separate-process stdio
and interruption suites were rerun, not reclassified as live client acceptance.

This is a Linux source-level and fixture test result, not all host suites or real
Windows/gameplay validation. No actual installed application, profile or game file
was modified. Native tests, game-specific semantics and current client integration
remain pending. Module development can continue without asking for the Planner,
Azeron backup or previously resolved host source again.

## Next boundary

The reusable extension infrastructure is delivered and tested. The owning chat can
integrate these source modules into its newest verified Workbench task copy and
onboard games with current real originals. No new input is needed to begin source
integration. Real-game acceptance later needs the relevant current originals and
an authorized Windows test route. Execution remains local; no background continuation,
new setting, deployment, automatic trust, sync or Git publication is implied.
