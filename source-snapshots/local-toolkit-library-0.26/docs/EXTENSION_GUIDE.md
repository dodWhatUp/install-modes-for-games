# Extending Keybinds by adding files

## 1. Data-only game pack, preferred path

```text
my-game/
  pack.json
  AUTHORING.md
  fixtures/
    before.json
    after.json
```

The directory above is the distribution unit. Only data/documentation/text fixture
payloads are accepted. `schemas/game-pack.schema.json` helps an editor or AI produce
valid structure. The executable validator in `packs.validate_pack` and `pack-check`
is authoritative for runtime constraints that JSON Schema cannot express.

Use `pack-scaffold` to create a DRAFT. It has no inferred action IDs and cannot bind
an active instance. Use local `inventory` to inspect selectors; values are excluded
unless `--include-values` is selected. `learn-diff` compares two explicit copies
from before/after ONE known in-game setting change. It never launches the game,
performs that change, or infers its action meaning. JSON array reorder can produce
positional differences: use stable native identities after review, not those indexes
as proof. Native values and original samples may be private; sanitize fixtures before
packing/sharing them. Pack export includes declared fixtures verbatim, not redacted.

Complete the real native encoding and context inventory from current originals.
Every field has stable `id`, semantic `action`, `slot` (default primary), runtime
`contexts`, keymap and exact selector. UI layer names are not game runtime contexts.
Fields in the same scalar can affect more than one context; every affected context
must be explicit in a semantic intent. Missing/default-only/native-unknown actions
must not be fabricated. Define explicit `exclusive_contexts` only with supporting
knowledge. Different names alone do not prove that contexts cannot overlap.

`stopped_processes` is the exact executable-basename policy for game/launcher/cloud
writers. An empty policy or false inventory flag prevents active instance binding.
Do not set completeness merely to get past a gate. Supply file `fingerprints` that
check exact build/schema identifiers where available. Their absence is not proof
of compatibility; the local reviewer is still responsible for the selected build.

`modifier_match` is `exact` or conservative `subset`. Left/right modifiers remain
distinct. Native codes for virtual keys, scancodes, controller buttons, character
labels and engine names are NOT interchangeable. Use explicit keymaps. Preserve
MouseLeft, MouseRight, MouseMove and wheel actions. Middle-click must be separately
allowed by reviewed file policy. The engine relies on truthful reviewed field/key
semantics; it cannot certify a malicious or incorrectly labelled native keymap.

## 2. Stable selectors and native text preservation

```json
{"json_match":{"array":"/bindings","where":{"/action":"Jump","/device":"keyboard"},"value":"/key"}}
```

The identity must occur once. Array order may change without redirecting this
selector. Exact JSON pointers remain available. XML can use
`{"xml_match":{"tag":"bind","where":{"name":"Jump"},"attribute":"key"}}`.
It must identify a unique element across the file; arbitrary XPath is not supported.

For INI, use exact section/key/occurrence/part. `ini-sparse` supports one optional
scalar in an existing section, `optional:true`, a reviewed `fallback_key`, and
`"Inherit":"__GT_INHERIT__"` in that keymap. Materializing an override adds only
that entry; inverse removal refuses a commented entry rather than deleting its
comment. No arbitrary new file, section, include, array or save record is created.

KeyValues1 is a strict quoted-token subset with explicit name/occurrence paths;
includes, macros, conditions and unquoted dialects are rejected. JSONC supports
comments and trailing commas, not all JSON5. `ue-chord` edits Key plus the four
explicit modifier flags of existing positive ActionMappings; clear/remove directives
are rejected. Neither Unreal route implements an effective engine array hierarchy.

The parser edits precise text spans, preserving unmodified bytes and the original
supported encoding/BOM/line endings. A native schema that cannot be represented
losslessly needs a different adapter, not a guessed conversion or full serialization.

## 3. Several files and active ownership

Each file declares scalar precedence `priority`, `writable`, fields and fingerprints.
A variant chooses an exact subset of files; alternative characters/presets are not
merged automatically. All chosen files must already exist. Local `pack-discover`
uses only supplied root aliases and bounded patterns; Steam/Epic metadata helpers
inspect explicitly selected manifests only, return candidate paths and optional
Steam Proton prefix metadata. They do not prove active config ownership. These
store metadata routes were fixture-tested, not accepted against a live client.

Import a reviewed pack with `pack-import --pack-sha HASH`. It is pinned by all its
payload bytes under the existing `keybinds/packs/id/version` path. Import does not
activate, trust native semantics or touch game files. Choose active originals with
the pane or `instance-bind`. The operator confirms exact paths/variant/file hashes.
An interrupted metadata registration is visible through `registration-status`;
an identical intake may be completed only after a fresh explicit local review and
unchanged sources. A different intake cannot seize or overwrite those targets.

Effective bindings are resolved per action/slot/context using the declared scalar
precedence; shadowed owners are shown, not silently edited. Unknown list/includes
remain unsupported. Any related file hash drift blocks application, even when that
file was not in the planned edits. Known in-plan earlier writes are distinguished
from external drift during a multi-file transaction. A cross-file key swap must be
prepared together; linked native groups and nonexclusive contexts are audited.
The process guard and source hashes do not prevent every noncooperating OS writer
race. Keep the declared writers stopped; no transactional guarantee across multiple
filesystem files is claimed.

## 4. Smaller AI operations instead of repeated giant files

```json
{"changes":[{"action":"interact","context":"gameplay","slot":"primary","key":"F"}]}
```

`intent-preview` maps that exact identity to the current writable owner and produces
`items_request` accepted by the existing preview/stage/apply backend. `preset-preview`
uses a named preset for the exact pinned input variant. No fuzzy matching or implicit
partial application. Missing actions return a bounded unresolved list. The local
CLI can explicitly request a partial intent; conflict/linked-context guards still
apply. The AI endpoint does not expose an automatic partial fallback.

The Planner cache remains keyed by source SHA-256. `planner-bridge` requires a
reviewed per-variant crosswalk from source labels AND displayed keys to native
semantic identities. Generic Ctrl does not automatically become LCtrl. Only actual
assignments are converted; deferred catalog rows and context bundles are not
invented, split, or silently merged. No Azeron output is changed.

AI tools expose adapters, pack pins, instances, paged/delta contexts, named/semantic
previews and typed diagnostics. Scope-specific endpoints reject another game's
plans/targets. Creating and editing a draft goes through the SAME local approval
mailbox (`keybinds.draft_pack`, `keybinds.edit_draft`). Draft edits use a bounded
add/replace/remove subset with JSON pointers and an exact parent hash. Unlike full
RFC6902, add-to-existing objects, root replacement, move, copy and test are not
supported; use explicit replace. Identity stays fixed and stage is forced to draft.
Each approved edit saves an immutable child and parent receipt; the earlier draft
is not overwritten. A typo, changed base or invalid schema blocks the entire edit.
The 12 KB request budget remains; large packs can be built from small approved
add-field/add-key steps and read through `keybinds_draft_context` pages.

Drafts are not imported or activated automatically. A local reviewer completes
sources, fixtures and native scope before import/binding. This avoids a model
approving its own guessed schema. No automatic network research, new executable
loading, secrets collection or running-client setup is added.

## 5. A genuinely new text format

Use `examples/adapter-sdk/named_tokens.py`: explicit trusted host code calls
`register_adapter(Adapter(...))`. Parser contract 1 adds bounded Cells; renderer
returns exact replacement spans. The common Document checks spans, reparses and
verifies values. The common Service still owns staging, backups, approval, source
freshness and recovery. New adapter registration never replaces an existing one.

The example is a fictional `map action KEY` format, not a game claim. Python adapter
code is trusted code, **not a sandbox**. It is never allowed inside a data pack,
auto-loaded from metadata, or accepted from AI as a shell operation. Binary/save/
registry plugins need a separately reviewed typed storage/schema contract and
corruption tests. This text SDK must not be used to pretend those storage roles work.

## 6. Validation, versioning and troubleshooting

`pack-check` validates the whole data pack and runs its declared before→expected
fixture byte comparisons and semantic inverse. Fixtures provide format evidence,
not in-game acceptance. Export/import with `pack-export`/`pack-unpack` verifies exact
hash coverage, portable names, sizes, duplicate/case aliases, CRC, regular entries,
compression/entry budgets and no scripts. Transport hashes identify bytes, not
publisher authenticity or trust. Source attribution/local review remains required.

`pack-compare` explains file/keymap/variant differences across revisions without
upgrading active instances. Importing a new version retains old pins/metadata and
backup records. Active-instance migration, storage pruning, merging conflicts into
another writer's changed native schema and replacing an installed pack are **not
automated**. Do not delete existing history to make an update pass. First reconcile
pending operations and choose a separately reviewed owner migration.

On timeout use the SAME plan/request status and reconciliation. Do not repeat a
mutation. Known dead operations/registration locks can be inspected and archived
through the existing local lock recovery; unknown/live owners and corrupt records
remain blocked. AI has inspection, not lock retirement or automatic approval.
