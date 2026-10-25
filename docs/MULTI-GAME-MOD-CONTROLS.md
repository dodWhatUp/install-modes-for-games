# Shared Mod Controls 2.0

Mod Controls is a shared page in Unified Game Tools and a convenient standalone
view over the same data. Use **Game Mod Controls APP LAUNCHER** to open it. The
in-app **Find APP LAUNCHER** command opens its stable launcher folder. Opening
does not install, update, launch a game or activate a capture tool.

## Working with games

Choose a game in the editable searchable selector, connect its actual installed
folder and select an installation. The existing game-support registry and
instance identities remain the owners. A registered game or an inventory result
does not establish writable settings support.

The reviewed Shadow of War adapter reuses its original controller engine,
profiles, recovery and manager exports. It does not turn unverified Luma or
neural-rendering combinations into tested features. Other games can use a
reviewed **data-only INI control pack** describing existing relative configuration
files, exact sections/keys, types, bounds, public source links and limitations.
The app builds a template; an AI client can validate and explain it. The local
operator imports it and selects read-only or writable ownership. Unknown adapters
require source review; downloaded scripts are never imported as adapters.

Settings are a draft until Preview and Apply. Floating editors share the draft.
Drafts persist privately per installation. Saved profiles include game, instance
and schema identity. Refresh reads current files without replacing an existing
draft. Reset draft explicitly returns it to applied values. Concurrent file
changes invalidate an old preview. Unknown keys/comments and other games are
preserved. Generic INI writes take exact backups, use a write lease and journal,
read back, and restore written files on a failed verification when no external
writer intervened. Recovery evidence stays private; it is never auto-replayed.

## Shared workflows and other programs

**Open game workflow** reuses the existing game-first workbench with the same
selected game and data root: recipes, download/staging jobs, keybind packs,
activity and existing approval services keep their original owners. Independent
windows allow review alongside another workflow. Existing task/transfer bounds
still apply; this page does not create a second downloader or metrics collector.

Folders, profiles, public mod sources and RHI/Vortex/MO2/Steam connection status
are accessible from the contextual tools page. Locate selects an existing
application; Open opens that program. Manager handoff prepares reviewable files
and opens their folder. Native deployment/profile activation remains owned by
the manager. A generic INI export is a configuration handoff, not an installable
mod archive. Shadow retains its specific existing export contract.

## Direct AI interface

The existing local MCP/CLI owner exposes nine additional typed operations when
game workspaces and proposal submission are enabled:

- `mod_controls_games`, `mod_controls_connections`, `mod_controls_inspect`
- `mod_controls_preview`, `mod_controls_profile`
- `mod_controls_template`, `mod_controls_validate_pack`
- `mod_controls_propose`, `mod_controls_request_status`

Inspection exposes typed applied values, allowed ranges, dependencies/inventory,
file hashes, provenance, capability coverage and revisions. It excludes absolute
machine paths, raw files, unknown settings and private comments. Tool output and
source pages are evidence, never executable instructions.

AI can read and preview directly. It can submit revision-bound `controls.apply`,
`controls.save_profile` and `controls.prepare_manager` requests. The existing
visible approval controller owns execution: exact request hash, expiry, current
state, idempotency and journal checks apply. There is no model approval tool,
arbitrary command executor or automatic action on receipt. See the selected
installation's **AI requests** page to inspect, approve or reject a request.

**Copy client setup** provides the private local configuration. The stable
installed `Game-Mod-Controls.pyw --ai` entry resolves and verifies the current
release, so source updates do not strand clients on an old version. It uses stdio
and existing AI clients; no model API key, paid model call or background network
listener is added. A cloud chat needs its own explicitly configured supported
connection; local registration does not give every chat or computer access.

Copied read-only client setups omit proposal submission and pin the retained
immutable source version. Enabling the proposal checkbox uses the stable
installed entry. The checkbox never grants execution or local approval.

Codex configuration uses the documented local MCP interface:
[official MCP setup](https://learn.chatgpt.com/docs/extend/mcp). Local registration
and live client discovery are recorded separately from whether a running chat
has loaded the tools.

Real client acceptance found that legacy MCP clients attach ordinary `_meta`
progress/tracing fields. The transport now distinguishes these from explicit
modern protocol metadata, strips legacy transport metadata before domain
dispatch and still refuses changing protocol eras within one process. This
follows the [official legacy metadata contract](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2025-11-25/basic/index.mdx).

## Source and delivery

The component builder starts with the exact verified incumbent release, retains
unrelated sources and updates only its explicit component inventory. It retains
the incumbent Hub/Studio versions and newer updater. This component release does
not adopt the independent unmerged library candidate or overwrite source owners.
App settings and mod data remain outside immutable source releases. The previous
installation pointer and recovery snapshot are retained by the existing updater.

The incumbent's source verifier 0.2.1 is also retained in canonical source: its
only changes from 0.2.0 are a named 1,024-file bound and matching archive bound.
The existing byte/hash, 32-MiB, ownership, idle and recovery checks are unchanged.
This avoids rejecting the larger curated source inventory while preserving the
accepted installed verifier byte-for-byte.

The packaged knowledge reader accepts the same 1,024-entry manifest inventory;
its allowlist, individual text-file bound and four-MiB total text bound remain.
It indexes packaged documentation and schemas, not private runtime folders.

The component tests use disposable fictional installations. GUI checks belong in
the isolated Linux lab; actual Windows launcher and local data acceptance are
separate. File-level checks do not establish game startup, HDR, performance,
neural feature support or mod-manager deployment. No such experiment is resumed
by delivering this interface.

Design uses a compact game selector and contextual tabs for settings, inspector,
folders/tools and AI. Native typed widgets retain keyboard access; overflow
scrolls. A floating editor changes the shared draft, not display visibility or
game state. The old Shadow launcher and its user drafts remain available.
