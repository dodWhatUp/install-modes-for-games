# Keybinds semantic merge review — Unified Game Tools 0.25

Created: `2026-10-14T00:27:00.399980+00:00`
Focused review R2: `2026-10-14T01:50:01.422924+00:00`

## Result

`Game Tools Keybinds 0.2.0-preview.1` was semantically rebased onto the verified `Unified Game Tools 0.24.0-preview.1` host and packaged first as local candidate `0.25.0-preview.1` and, after the focused compatibility review below, revised as `0.25.0-preview.2`. The merge does not overlay the two source trees and does not replace the newer A host with B's 0.23-derived compatibility classes.

## Ownership retained

| Stable identity | Final owner | Adopted behavior |
|---|---|---|
| `host.automation.service` | `scripts/GameToolAutomation.py` | One request store, journal and exact local approval controller. Keybind operations are composed through `KeybindAutomationMixin`. |
| `host.ai.endpoint` | `scripts/GameToolAI.py` plus `scripts/GameToolKeybindAI.py` | One endpoint lifecycle and one `tools/list`; the keybind family is appended once. AI can propose but cannot approve, register arbitrary paths, launch games or inject input. |
| `host.game.workspaces` | `scripts/GameToolGameWorkspaces.py` | A remains the game identity and support-row owner. It composes support-only, keybind-only and dual-capability services. |
| `schema.game_id` | Workspace composition layer | `game-support-pack` and `game-keybind-pack` remain distinct stores and revisions under a shared `game_id`. |
| `state.data_root` | Existing host data root | Keybind data uses a separate subtree while approvals and requests remain governed by the existing host. |
| `ui.workbench.lifecycle` | `scripts/GameToolWorkbench.py` | One Keybinds tab, one Tk root, one Stop owner and one close path. |
| `export.manifest` | `scripts/Export-GameTools.ps1` and regenerated `MANIFEST.json` | The merged allowlist contains A-owned sources plus B-owned code, schemas, synthetic fixtures, research drafts and merge records. |

## Capability composition

The final workspace has three explicit modes:

1. **Support + keybinds:** `KeybindScopedAutomation` combines a reviewed mod recipe with the imported keybind capability while sharing the same approval mailbox.
2. **Support only:** the unchanged `ScopedAutomation` behavior remains available and is not falsely promoted to keybind support.
3. **Keybinds only:** `KeybindOnlyAutomation` exposes only keybind operations and refuses mod-plan operations when no reviewed mod recipe exists.

A capability-shape change after a service has been cached raises `SOURCE_CHANGED`; callers must reopen the workspace instead of receiving a silently mutated service. A recipe-only revision now preserves A 0.24 behavior: the scoped service refreshes so new plans use the new immutable recipe, while old jobs and pending requests retain their recorded bytes and become non-current where appropriate.

## Focused R2 review — adopted changes only

The second pass found and corrected five product/package issues plus one evidence-integrity issue:

1. **Recipe refresh regression:** the initial merge blocked three established A behaviors after a recipe-only update. The service now refreshes only when the capability shape is unchanged; capability additions/removals still require reopen.
2. **Current-document routing:** stale 0.23 standalone instructions were replaced by current pointers, while exact Input B handoff/pins were preserved under `docs/keybinds/history/`.
3. **Schema/runtime parity:** expressible semantic-version, identifier, path-length, process-name, evidence-note, duplicate-list and key-length limits now agree; all 27 shipped packs pass both validators.
4. **Reproducible guidance:** the mandatory UI/content design source is bundled byte-identically from canonical commit `043f3c4733788f082da98dfcb43c0972d2794c6a`; remaining unbundled links are pinned to that exact revision instead of floating `main`.
5. **Launcher portability:** the runnable preview no longer searches one user-specific Downloads path. It validates a configured/PATH Python 3.10+ interpreter and Tk before creating preview shortcuts or launching.
6. **Honest PowerShell test status:** the installer test no longer treats a nonexistent local `pwsh` fallback as an executable runtime. It reports seven explicit environment skips when PowerShell 7 is unavailable; this is not counted as native acceptance.

Deliberately **not** added: new pack-import recovery mutation, automatic game discovery, native adapters, broad refactors, bulk copies of unrelated repository documentation or another updater/daemon. The existing incomplete-import state remains fail-closed and explicit; a recovery command should wait for a bounded design and native interruption tests.

## Included B material

- Keybind planning, preview, snapshot, apply, readback, history, reconciliation and rollback source.
- Data-only extension system and ten synthetic format packs.
- Seventeen game research-draft folders and their location evidence.
- Keybind UI pane and JSON-RPC/MCP-style proposal surface.
- Component and host-integration tests, plus the new merge-conflict suite.

The B `compat/` host copies, historical validation logs, standalone launcher and standalone manifest were not adopted as final owners.

## Evidence status

The Linux/Python and Xvfb test evidence is recorded in `docs/KEYBINDS-MERGE-VALIDATION.json`. The final archive-level integrity result is recorded in the delivery receipt created after this source tree is sealed. This review does not establish native Windows, installed-client, real-game, gameplay or physical-device acceptance.
