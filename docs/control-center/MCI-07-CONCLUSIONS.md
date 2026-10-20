# MCI-07 conclusions — 2026-10-20

Result: 6/6 original checklist items accepted for managed placement and local vault bindings. The native adapter supports Windows volumes; other native OS and network-share adapters remain unsupported.

| Criterion | Implementation and evidence |
|---|---|
| Logical and volume identity | New vault marker plus vault/workspace/replica/storage IDs; local bindings pin observed Windows volume GUID and directory identity. A drive letter alone is insufficient. |
| Relative managed roots | Project source, selected assets, results and continuation records route beneath projects/project-id with source/assets/outputs/continuation roots. Four classes were placed and reopened byte-for-byte on a real non-system NTFS volume. |
| No fallback / unsupported outputs | Missing or replaced storage is refused. Status inventories explicit managed routes, native Codex state that is not redirected, and existing/external tool outputs needing adapters. |
| Native ownership | Credentials, mutable runtime databases, schedules, approvals and machine-local bindings remain separate. Codex and native settings are unchanged. |
| Portable path / collision checks | Unicode, NFC/case aliases, reserved names, traversal, source drift, links, clone collisions and stale writers tested. Same-volume folder relocation and fresh local attachment passed. |
| Real synthetic placement | Native Windows acceptance exercised the public CLI with policy/authorization, four output classes, stop/revocation refusal, relocation, reopening and new local bindings without rewriting the vault marker. |

Existing selected vaults can be attached on a destination using a new local binding store. Copying another machine's binding, permission registry or credentials is unnecessary and unsupported. A directory/volume mismatch requires inspection or a distinct replica; there is no automatic first-match adoption.

Reused owners: GameToolUserData bounded paths/reads/new writes, GameToolJournal audit evidence and game_mod_ops cooperative locks. No second archive, journal, installer or sync engine was built. Append-only metadata revisions reject stale edits and incomplete audit evidence; locks are local cooperation, not distributed consensus.

The adapter uses the [Windows volume GUID API](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getvolumenameforvolumemountpointw). A GUID and digest are not sender authentication, hardware attestation or proof against an adversarial cloned OS. Actual second-computer, removable-drive disconnect, network/cloud, checkpoint exchange and parallel reconciliation acceptance remain downstream.

Decision: accept the listed source/placement criteria. Existing tool outputs and Codex project defaults are not silently redirected; managed callers must use the explicit route. Next dependent package: MCI-08 checkpoint/exchange.
