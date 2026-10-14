# Multi-game support packs

**Source preview 0.24.0-preview.1 — 2026-10-13.** This extension is built on the
verified 0.23.0 Workbench source. It is not an installation on the user's Windows
computer, a new mod manager, or a new project master. The code and data belong to
`dodWhatUp/install-modes-for-games`; this private source delivery awaits that owner's
safe publication/integration route. Earlier blocked Git/remote/browser effects are
not retried by this work.

## What changed

A new game using a supported file format can now be added by importing **one JSON
support pack**, or a ZIP containing exactly `game-support.json`. The Workbench,
job engine and AI transport do not need to be rewritten. The importer generates
an internal recipe from the reviewed data. Future jobs snapshot the definition
and its revision; old jobs keep their original recipe, target markers and receipts.

This closes the gaps left by game-scoped workspaces alone: game registration,
non-combat presets, archive interpretation, named-folder inspection, declared
mod identity comparison, and a private manager handoff. The existing approval
controller, jobs, worker limits, cancellation, UI, native Studio, overlays and
report providers remain their respective owners.

### Human workflow

Open **OPEN Game Tools.cmd** from the extracted preview package. The new commands
are available through **Add game support** and **More**; no developer console is
required for ordinary import/export.

1. Ask the chat to extend a particular game. **More → Copy extension brief for
   chat** supplies the current pack and machine-readable authoring contract.
   It contains author notes and source links; review before sharing. Account
   keys, installed paths, saved reports and private application settings are not
   collected for this brief.
2. Import the returned support JSON with **Add game support**. The confirmation
   identifies the game, manager, adapter, pack version and changed sections.
   Importing does not download anything, install a loader or modify a game.
3. Choose a preset and use the existing plan/download/import/preparation controls.
   **More → Export files for mod manager** creates an ordered private handoff of
   the already accepted original archives; **Inspect game folder** records
   filesystem observations, not an in-game test.

**More → Create game template** is also available. It saves a draft JSON without
registering it. The chat should research and fill the exact fields instead of
making the user write configuration manually. **Export game support** exports
configuration only, never downloaded mod archives or user settings.

The two OPEN files use the same separate `GameToolHub-Workbench-Preview-0.24`
profile and an OS-released single-preview lease. Production data is not copied.
The existing Original interface remains available; it is not converted to a new
backend. Python 3.10+ with Tkinter must already be installed. Opening the preview
does not install a runtime, start a game, benchmark, capture or AI client.

## Implemented coverage — do not interpret names as full game support

| Included definition | Actually available | Not established |
|---|---|---|
| Pathfinder: Kingmaker | Existing researched recipe, UMM archive/inventory, named presets, ordered handoff | Native install/client/game acceptance; loader activation |
| Stardew Valley | SMAPI + Content Patcher foundation recipe, `default` preset, SMAPI manifest/archive checks, inventory and handoff | A verified downloaded release or complete user mod list; loader installation and in-game operation |
| Pathfinder: Wrath of the Righteous | UMM identity/layout definition, reusable inspection and future recipe base | A curated mod recipe or tested loader/build combination |
| Valheim | Explicitly **template-unverified** BepInEx layout and filename inventory | Loader compatibility, binary plugin identities, version/enabled state, curated mods |
| Skyrim Special Edition | MO2-oriented external-manager definition and future handoff base | Virtual profile inventory, FOMOD decisions, load order or curated mods |
| Cyberpunk 2077 | Existing RHI preference retained as an external-manager definition | New graphics-mod recipe, proxy deployment or version compatibility |

The included real planning recipes are **two**, not six complete installations.
Stardew's version-dependent files are deliberately not guessed: choose the author's
compatible SMAPI/Content Patcher release and import its original archive, or supply
an exact Nexus file selection via the existing local authorization path. Manifest
identity checks do not establish that a binary is trustworthy or works in-game.

## Extension levels

**New game, known format:** add or import a support JSON. Supply a stable game ID,
name, manager ID, target platform, allowed relative executable markers, mod folder,
optional loader markers and bounded inspection depth. Add its mod recipe when it
is researched. A metadata-only pack is valid; the UI exposes no fake ready plan.

**New mod or preset:** update the same pack's recipe items, dependencies, conflicts,
source pins, expected manifest identity/version and preset map. Examples of preset
names are `default`, `quality-of-life`, `real-time` and `turn-based`. Preset selection
is data; it is not restricted to Kingmaker combat modes.

**New manager using a supported layout:** use `umm`, `smapi`, `bepinex`, `directory`
or `external`. A custom manager name can reuse a supported adapter. Known manager
IDs cannot silently name contradictory adapters. External managers retain their
own deployment databases, virtual filesystems, installers and load order.

**Genuinely new file format or manager API:** add a small trusted Python adapter
and contract tests to the source, then a data definition. An imported pack cannot
load Python or install an executable plugin. Register its ID in `definitions.py`,
implement archive/inspection capability paths in `managers.py`, keep unknown
capabilities false, and include the module in the existing source exporter and
manifest. No replacement of Workbench, AI transport, job journals or approval logic
is required. Code extension is reviewed and packaged separately from data import.

## Data contract and ownership

A pack has exactly `schema_version`, `kind`, `pack_version`, `definition`, `recipe`,
`sources` and `notes`. The full authoring contract is in
[templates/GAME-SUPPORT-AUTHORING.json](../templates/GAME-SUPPORT-AUTHORING.json);
[a minimal template](../templates/GAME-SUPPORT.example.json) starts without a mod
recipe. This compact contract helps AI author the data; the actual runtime
validators, not a decorative schema title, decide what is accepted.

`definition` owns identity/layout once. `recipe` uses the existing mod-workflow
schema and inherits that definition in its generated internal copy. Optional item
fields include `archive_layout`, `archive_root`, `mod_id`, `required_files` and
`expected_version`. `sha256` remains an exact expected archive digest when known.
Use relative paths such as `bin/x64/Game.exe` or `My Game.exe`; no local username,
credential, arbitrary shell command or signed download URL belongs in a pack.

Shipped definitions live in `examples/game-tool-hub/game-support/`. Their derived
recipes live under the existing `mod-recipes/` path for original-host compatibility
and are verified against the canonical support JSON. They are not independent
editable masters. Imported revisions are stored privately under the existing
`mod-workflows/game-support/<game-id>/<semantic-revision>/` subtree. The one
`current.json` selection pointer changes only after the reviewed current-revision
check and local confirmation. Old versions are retained; import the desired older
pack with a new explicit review to change future plans. This never rolls back an
installed game.

The revision hash is over canonical JSON semantics; whitespace-only reformatting
is not a new semantic revision. Original imported JSON bytes are retained. The
registry uses a cooperative writer lock, pre-replacement selection comparison,
atomic pointer replacement and readback. It is not an OS-wide ban on other writers.
A corrupt source/pointer, conflicting selection or incomplete write stops the
affected registry operation for reconciliation, not a blind automatic retry.

## Archive interpretation and manager handoff

- **UMM:** retain original `Info.json` and declared assembly checks.
- **SMAPI:** identify a single `manifest.json`, require the expected `UniqueID`
  when declared, preserve its `Version`, dependencies and either `EntryDll` or
  `ContentPackFor`. Require the declared DLL in the archive. Multi-mod bundles
  with several manifests stop for explicit separation/review.
- **Generic/directory/BepInEx payload:** validate ZIP paths, sizes, entry types and
  hashes. An optional explicit `archive_root` selects a subdirectory, and all
  excluded paths are recorded separately from documentation. There is no guessed
  installation destination or execution based on filename.

All use the existing original-archive receipts and staging engine. ZIP traversal,
case collisions, links, encrypted archives, unexpected payloads and missing required
files stop preparation. Limits remain explicit: 64 active support identities,
32 local revisions per identity, 100 items per recipe, 256 MiB per archive, 512 MiB
expanded ZIP, 4,000 inspected entries, and 1–6 inspection levels. The actual network
operation retains its smaller existing budget (128 MiB aggregate); large mod packs
need the external manager or a separately reviewed budget/format extension.

The manager handoff makes **new local copies of original accepted ZIPs**, numbered
in dependency order, with their hashes and a readable `OPEN Manager Handoff.html`.
It requires all selected archives to be acquired, exact current-job review and a
new output directory. Interrupted/denied jobs are not retried. It never copies into
a game's Mods directory, injects loaders, changes external manager state, or publishes
third-party binaries to Git/Drive. Do not treat this private handoff as a redistributable
mod bundle. Closing the UI does not erase the immutable original jobs.

## Installed-folder observations

Folder inspection starts only after an explicit chosen-directory action. Executable
markers identify a plausible selected folder, **not its actual game version**.
UMM and SMAPI inspection reads manifests; BepInEx inspection records DLL filenames
only, without loading binaries or inventing GUID/version/enablement. A generic
adapter lists bounded files. An external-manager adapter reports that virtual
profile inventory requires the manager's own supported interface.

Unknown content, duplicate IDs, missing assemblies, unreadable metadata or depth
limits produce partial/inconclusive results. Before/after file-set metadata is
checked to reject changes during the inspection. This is not a cryptographic
snapshot of every binary or a persistent file watcher.

The intended-vs-observed comparison distinguishes identity not configured, identity
present, version match/difference, missing payload, ignored-folder convention,
duplicate identity and inconclusive absence. A version match is **manifest data**,
not runtime success. All results keep `runtime=NOT_VERIFIED` and enabled state
unknown. Manual check results retain their existing operator-reported labels.

## Opaque installation identity and accepted read adapter — 0.27

The 0.27 read-only slice adds a private `game-instances` registry under the
existing Game Tools data root. A local operator selects and confirms one exact
game folder through `Game-Instances.py`; the registry stores the private path and
current support-definition revision. Public AI results expose only an opaque
instance ID and path-free metadata. The AI tool surface has no registration,
`path`, `game_dir`, `root` or `directory` argument.

Only the UMM adapter is accepted by this slice. It reuses the existing bounded
folder inspector for executable/loader markers, `Mods/*/Info.json` and the
manifest-declared assembly. Other existing folder formats remain available to
their earlier support-pack workflows but are **not** silently promoted to this
instance adapter; registration returns `ADAPTER_ACCEPTANCE_PENDING` until a
separate conformance pass exists.

`game_tools_plan_goal` compiles dependencies and read steps but does not inspect
a folder by itself. `game_tools_instance_inspect` performs the explicit read.
`game_tools_conflicts` may compare exact planned UMM identity with one named
registered instance, preserving duplicate/missing/inconclusive states. None of
these tools install, enable, disable, upgrade or roll back a mod, and none treats
manifest presence as runtime success. Full contract: [read-only planning and UMM
instances](AI-PLANNING-READONLY-SLICE.md).

## AI integration

The existing multi-game local stdio route adds four **read-only** tools:
`games_support_schema`, `games_support_template`, `games_support_validate` and
`games_support_details`. They provide the authoring contract, draft data, validation
and revision/difference review, and selected game capability/layout information.
They do not import/activate a pack, download files or change game state. Free-text
review notes are excluded from automatic definition output. All tool output is
untrusted evidence/data, not instructions.

The existing proposal operations are still only `mods.create_plan`, `mods.download`
and `mods.stage`; each needs exact local approval. A recipe change makes prior
requests stale. A request mentioning a removed item stays readable with its original
requested IDs, but cannot be approved against a different recipe. AI cannot approve
itself, perform unrestricted installation/rollback, or access arbitrary local paths.
This source implements the route; no live AI client was connected or tested here.

For an authorized source-level executor, `scripts/Game-Support.py` exposes `schema`,
`list`, `scaffold`, `validate`, `import`, `export`, `inspect` and `handoff` commands.
Import requires the reviewed semantic pack digest and both expected support and
recipe revisions when replacing an existing definition. This is a local operator
CLI, not an exposed shell tool or a background server. Use `--data-dir` for the exact
approved profile. It does not discover or modify unrelated accounts or computers.

## What is deliberately not complete

Generalized live installation, existing-mod upgrades, dependency download inference,
per-store installed-profile discovery, rollback of externally managed deployments,
MO2/Vortex/RHI mutation APIs, 7z/FOMOD interpretation, and automatically choosing a
correct loader build are still separate development/acceptance work. The legacy
Kingmaker new-folder installer remains its own guarded operator-only path. The new
capabilities never pretend that path applies to other games.

The highest-value next slice is a documented manager installed-profile adapter and
an exact intended/installed change preview, followed by a separately tested
new-folder deployment and settings-preserving upgrade transaction. Reuse the
existing recovery, approvals and job identities. Do not add a generic DLL copier.

## Evidence and tests

[Validation record](GAME-SUPPORT-VALIDATION.json) distinguishes new extension tests,
regression tests, source preservation and untested native behavior. The key
acceptance test registers **three unknown synthetic games** using UMM, SMAPI and
generic layouts, then performs the real plan → archive import → preparation flow
without editing the app source. Test assemblies are harmless text and are never
executed. A real-title definition or a passing synthetic test is not in-game
acceptance. Windows UI/shortcuts, external provider transfers, PowerShell exporter
execution and live AI-client behavior remain unverified.

## Primary documentation used for format boundaries

Sources are upstream documentation, not downloaded binaries or native runtime tests.

- UMM: https://github.com/newman55/unity-mod-manager/wiki/How-to-add-a-new-game
- SMAPI/game-folder and mod install: https://stardewvalleywiki.com/Modding:Player_Guide/Getting_Started
- SMAPI manifest: https://stardewvalleywiki.com/Modding:Modder_Guide/APIs/Manifest
- Content Patcher source/manifest: https://github.com/Pathoschild/StardewMods/tree/develop/ContentPatcher
- BepInEx v5 installation, **version-specific**: https://docs.bepinex.dev/v5.4.21/articles/user_guide/installation/index.html
- MO2: https://github.com/ModOrganizer2/modorganizer
- RHI: https://github.com/RankFTW/RHI

Wrath and Valheim remain layout/template records at the stated evidence levels,
not automatic assurances derived from these generic format documents.
