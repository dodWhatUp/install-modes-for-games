# Workspace foundations — 2026-10-20

Implemented in dependency order: MCI-07 after MCI-02; MCI-12 after MCI-02/03; MCI-13 after MCI-02, then connected their local controls to managed placement. Codex installation/configuration, native databases and installed toolkit were not changed.

| Stage | Accepted | Conclusion |
|---|---:|---|
| [MCI-07](MCI-07-CONCLUSIONS.md) | 6/6 | Windows non-system-volume binding, explicit managed roots, new-copy placement, attachment/rebinding, clone/path/drift refusal |
| [MCI-12](MCI-12-CONCLUSIONS.md) | 6/6 | Independent directional policy, effect controls, trigger eligibility, context-reference staging, exact acknowledgements and granular rollback |
| [MCI-13](MCI-13-CONCLUSIONS.md) | 5/6 | Local OS-session roles, scopes, enrollment lifecycle and stop; fresh supported sign-in remains pending |

Program progress: 47/108 original items accepted; seven packages complete, one partial and ten planned. P0 remains 30/30. Next boundary is the MCI-13 sign-in choice; MCI-08 checkpoint/exchange is independently eligible. No automatic future run is installed.

Reuse review retained UserData file/archive ownership, Journal audit ownership, cooperative locks, existing projection contracts and the existing control-center report renderer. [Exact inventory](MCI-07-12-13-INVENTORY.json) records source hashes and basis. The new local revision helper supplies only the missing metadata compare-and-swap protocol; it does not replace archives, sync, tasks or approval execution.

[Validation](WORKSPACE-FOUNDATIONS-VALIDATION.json): 208 tests passed in the isolated Linux guest, including 58 new foundation tests and 150 reused-component regressions, with no skips. The 58 new cases also ran on Windows: 56 passed and two environment cases skipped; Linux covered those cases. Source-export contract suite: 69 passed. Native Windows acceptance placed/reopened four synthetic content classes on an observed non-system NTFS volume, relocated and freshly attached the vault, detected a clone, and refused placement after stop/revocation.

Review found and corrected a journal terminal-event mismatch, stop-marker enumeration, portable clone-ID encoding, volume-root metadata handling and stale-body proposal rebasing. Failed prototype receipts and final raw logs remain private. Final code was byte-verified before guest execution.

The source front door is [GameToolManagedWorkspace](../../scripts/GameToolManagedWorkspace.py). [Usage](../../examples/managed-workspace/README.md) distinguishes managed placement, local configuration and read-only reporting. The existing System control panel can load a generated private context; there is no second GUI/report engine. Source CLI tests do not establish Windows GUI/human usability acceptance.

Limits: one actual computer was exercised. Native volume enrollment currently supports Windows only. No actual moved-drive trip between computers, native Codex chat continuation, remote authentication/execution, network/cloud transport, automatic tool-output redirection or native model-context delivery is claimed. Bindings, account identifiers, roots and raw evidence stay private outside Git/OneDrive.


## Windows identity continuation

The user selected the Windows account on each computer. The [native Windows adapter](MCI-13-WINDOWS-ACCOUNT.md) now extends the existing local access owner. Headless availability passed and operation-bound verification is implemented; human success/cancel and second-computer acceptance remain pending. MCI-13 remains 5/6; program count stays 47/108. Earlier statements that identity selection or the adapter were pending describe the preceding checkpoint.
