# Mod Control: reusable creation and integration rules

User-requested foundation, 2026-10-25. Extend the existing shared Mod Controls
owner in Unified Game Tools. Gameplay control belongs within Mod Control, along
with content, interface, camera and appearance modifications. Reuse existing
game identities, profiles, transactions, recovery, manager handoffs and approval
services. A separate launcher may open the same shared page; it must not create
another settings database or competing deployment owner.

## Purpose and mechanism are separate

| Dimension | Examples | What it decides |
|---|---|---|
| Purpose | Gameplay, abilities, content, interface, camera, appearance, performance | How the user finds and understands a feature |
| Mechanism | Assets/content, configuration, engine plugin, loader, graphics hook/injector, external manager | Which adapter and file/runtime owner can safely apply it |
| Evidence | Documented, file/configuration verified, runtime observed, failed, unknown | What can be claimed about it |

Present **Game mods** and **Graphics tools** as distinct views under the same
selected installation. An appearance mod can belong to the game's content/mod
system; a graphics injector can also affect gameplay presentation. ReShade and
OptiScaler operate through graphics hooks, but their deployment can still add
DLLs/configuration to a game folder and affect the running process. Do not treat
them as having no file or runtime interaction. Preserve the more specific
graphics-host, temporal-input, HDR, proxy and feature-ownership rules in
[Feature Decision](FEATURE-DECISION.md) and [Graphics Controls](GRAPHICS-CONTROLS.md).

## Compact controls and truthful information

- One compact row per installed/reviewed module: enable draft, applied file state,
  separate GitHub/Nexus links, Preview and Options. Preserve readable row height;
  optional depth belongs in reusable nonmodal windows. Explicit multi-button rows
  implement this user's requested exception to the usual adjacent-utility default.
- Source buttons must identify that module's verified author pages. Disable and
  explain missing counterparts. A search result or another game's loader page
  is not a substitute for a verified source.
- Preview gives a short useful description, prerequisites and relevant author
  examples. Keep image provenance, credit and original links. Provide Fit/100%,
  navigation and panning, with a readable fallback when assets are unavailable.
  Keep cached third-party images private and outside Git; do not generate imagery
  that could be mistaken for demonstrated gameplay or local acceptance.
- Options and previews open beside the current pointer, shift within the work
  area at edges and reposition when reopened. Keyboard access and focus remain
  usable. Opening, closing or hiding does not apply or disable anything.
- Share typed draft variables between main rows and floating editors. Preserve
  drafts per installation across refresh/reopen; Reset is explicit. Show applied
  state separately. Source browsing, images, profile saving and Install/Update
  remain separate from applying settings.

## Adapters and transactions

1. Research existing mod files and documented keys. A support pack names public
   identity/layout; a control pack names known typed controls and relative paths.
   Metadata does not certify write support. Reuse known adapters; review and test
   new formats in trusted source. Imported data never loads executable adapters.
2. Connect actual folders and write ownership through the local operator. AI may
   inspect, validate and propose, but cannot register private file paths or approve
   its requests. Preserve the existing exact local-approval boundary. Never write
   registration JSON or invoke a local-only API to bypass that boundary.
3. Bound values and file sizes. Preserve unknown settings/comments, encoding,
   newlines, saves and native-manager data. Bind previews to game/schema/instance,
   source and file revisions. Stale or foreign profiles require reconciliation.
4. Use one coordinated lease and transaction for tightly related DLL/configuration
   changes. Preflight processes, dependencies, build identity and source hashes;
   snapshot exact prior bytes, apply in dependency order and read back. Activate
   the loader proxy last; remove it first when disabling. Do not swap loaded DLLs.
5. Roll back only bytes that still match this transaction's attempted values.
   Preserve an external writer and report recovery-required instead of overwriting
   it or claiming successful rollback. Retain recovery receipts; never auto-replay.
6. All Off must state its scope. A group selection affects that group's draft;
   it must not silently disable another graphics/mod owner or restore a save.
   Disabling a mod cannot undo items or progress it already saved.

## Cooperation between game mods and graphics tools

Both views share game/installation identity, build, revisions, typed drafts and
reviewed dependency/resource declarations. Use the existing inspector and AI
context instead of a new arbitrary-command channel. Coordinate declared proxy
DLLs, files, setting keys, configured hotkeys and feature ownership. Show concrete
collisions and missing dependencies in **Coordination**, and block a conflicting
apply. Unknown ownership or a clear declaration scan is not runtime compatibility.

Each graphics/native manager retains its own deployment, profile activation and
recovery owner. Opening its workflow carries the selected game and shared data
root; it does not apply another tool's settings. A combined plan may coordinate
reviewed owners, processing order and recovery, but needs explicit scoped review
and separately verified adapters. Do not enable a graphics stack merely because
a gameplay pack was connected. Do not infer a supported injector chain from two
different proxy filenames or from both files being present.

## Delivery and acceptance

Prefer **Find game & controls** before asking for a folder path. Inspect existing
local connections, known store manifests and shallow private prepared-controller
folders. Validate the expected game executable and reviewed controller identity;
rank deduplicated candidates by explicit evidence and show the executable, full
local paths, reasons and any conflicts. Scores are evidence strength, never a
statistical probability or runtime compatibility claim. Keep distinct prepared
workspaces as distinct choices. Bound the scan; do not crawl whole drives, follow
links, execute discovered code or register a location during discovery.

The native chooser must keep the scan responsive, retain manual browsing, and
revalidate evidence before **Use selected**. A top-ranked suggestion is not an
automatic selection or permission grant. The human confirms local connection
and reviewed write ownership separately; cancellation changes neither. Preserve
existing connections and drafts. Editable search/choice fields disclose their
filtered choices on a click anywhere while retaining the typing caret, keyboard
selection and Escape cancellation; opening or typing does not commit a value.

Build component updates over the exact verified incumbent release. Replace only
the component's explicit source inventory; preserve newer unrelated Hub/Studio,
settings, version pointers and stable APP LAUNCHER entries. Retain the previous
version and current-state backup. Follow the existing updater's idle/source-lease
checks rather than overriding them.

Test disposable data first: per-game scope, stale revisions, read-only ownership,
profiles, dependency/proxy/hotkey conflicts, process guards, failure/readback and
conditional recovery. Test actual widgets in the isolated lab: narrow/large-text
layout, row height, applied/draft distinction, cancelled connection/apply, popup
placement, source buttons and gallery errors/zoom/footer visibility. Verify the
normal Windows launcher separately. State physical DPI/multi-monitor, game startup,
visual quality, compatibility and performance limits honestly. No game launch,
benchmark, capture, native profile activation or cloud upload is implied by a UI
delivery or by these future creation rules.

Implemented owners: `GameToolModControls`, `GameToolModControlCatalog`,
`GameToolFloatingWindows`, `GameToolModGallery`, the original reviewed per-game
engines and their data-only support/control packs. Wicked is the first shared
file-plus-TOML example. Existing generic INI and Shadow profiles retain their
schema identity across this component update.
