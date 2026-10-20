# Managed workspace foundations

Use [stage conclusions](../../docs/control-center/WORKSPACE-FOUNDATIONS-2026-10-20.md) and [validation](../../docs/control-center/WORKSPACE-FOUNDATIONS-VALIDATION.json). Component version: 0.1.0-preview.1; local metadata format: 1. This adds source capabilities to the existing toolkit; it does not install/update Codex or the installed toolkit.

The explicit local front door is scripts/GameToolManagedWorkspace.py. Run it with an existing Python runtime and --help. There is no MCP write surface, background service or scheduled synchronization.

| Goal | Mode and required selection |
|---|---|
| Observe volume suitability | volume --root selected-existing-parent |
| Create a new vault and private bindings | vault-create --state new-private-bindings --root new-vault-on-non-system-volume --workspace logical-id |
| Attach an existing selected vault | vault-attach --state new-or-existing-private-bindings --root existing-vault; use --expected-revision for an existing registry |
| Inspect or relocate | vault-status --state bindings --vault-id id; vault-rebind additionally needs --root and --expected-revision |
| Obtain an explicit managed destination | route --state bindings --vault-id id --project id --class content-class --relative portable/name |
| Configure local policy | policy-create, policy-status, policy-preview, policy-ack-preview, policy-rollback-preview and policy-commit |
| Probe / create Windows-protected access | windows-account-status; access-windows-create --state NEW_PRIVATE_ROOT |
| Configure local roles/enrollment | access-create, access-status, access-preview, access-commit and access-check |
| Stop / reviewed local resume | stop --state access-store; resume needs the current local actor and exact --accept stop digest |
| Existing control-center views | view-context or report --state selected-parent-containing-bindings-policy-access |

Managed classes: project_source, selected_assets, selected_results and continuation_packet. Roots are relative to the selected vault. Missing/mismatched storage refuses writes; there is no OS-drive fallback. Native Codex state and outputs from external tools without explicit destination support remain with their owners.

Policy/access edits use --input private JSON. Preview output is data only; commit needs the exact --accept preview digest. The [inert rule example](policy-rule.example.json) starts disabled. Account/workspace/project/direction/capability/class scope, transfer/adoption/index/context controls and trigger/depth settings are independent. Hidden view controls do not enable or disable effects. Trigger eligibility creates no schedule.

Managed place requires --source, --source-sha256, --relative, selected vault/project/class, --policy-state, --access-state and --input containing matching authorization and policy requests. The authorization request includes account_id, workspace_id, project_id, device_id, generation, capability managed.write, storage_id, content_class and policy_revision. The policy request includes account_id, workspace_id, project_id, source_device, destination_device, capability and content_class. Exact current policy acknowledgement, storage write grant and enabled adoption are required. Existing output files are preserved.

[Windows-account verification](../../docs/control-center/MCI-13-WINDOWS-ACCOUNT.md) is implemented; human interactive acceptance is pending. Use access-windows-create for a protected new registry, or preview/commit require_windows_sign_in to upgrade an existing one. Legacy access-create remains session-only. Windows verification requires a configured local PIN/Hello; it does not fall back on failure. Do not transplant credentials, permissions, browser profiles, binding registries or mutable runtime databases. Create fresh machine-local bindings and authorization on a destination; keep them outside the portable vault, Codex and OneDrive. Existing filesystem ACLs remain OS-owned.

<details><summary>Try the bounded synthetic native-volume acceptance</summary>

Run python -B scripts/tests/Accept-ManagedWorkspace.py with --data-parent selecting an existing non-system private parent and --local-parent selecting an existing private machine-local parent. It creates new uniquely named synthetic directories only, exercises all four placement classes and stop/revocation, retains private receipts, and leaves fixture authorization stopped. It does not redirect real projects or enroll a remote computer.

</details>

<details><summary>Open the existing control-center presentation</summary>

Save view-context JSON inside the selected local parent, then use the existing scripts/GameToolSystemControl.py gui --context selected-file --root selected-local-parent, or choose that context in the existing panel. Report mode emits standalone HTML using the same accessible renderer. Save private output to a new file outside Git/OneDrive. No new GUI is installed.

</details>

Recovery: preserve any partial vault/metadata operation and inspect its journal. Stale/unknown locks and incomplete revisions are never automatically removed or replayed. Stop remains available even with corrupt authorization metadata. Rollback of one policy rule creates a new revision; it does not rewind writer generations or replace another direction. Actual checkpoint recovery, transport, native continuity and integrated multi-device release acceptance remain their dependent packages.


## Bounded MCI-08 seed source candidate — 2026-10-20

[Conclusions](../../docs/control-center/MCI-08-CHECKPOINT-CONCLUSIONS.md) and
[validation](../../docs/control-center/MCI-08-CHECKPOINT-VALIDATION.json) describe
this source/synthetic slice; it is not an installed sync feature.

New modes in the existing CLI: `checkpoint-preview`, `checkpoint-publish`,
`checkpoint-inspect`, `checkpoint-restore-preview`, `checkpoint-restore`, and
`checkpoint-inspect-restore`. Every mode selects existing `--state` bindings,
`--policy-state`, `--access-state`, `--vault-id` and a private `--input` JSON.
No fixture identity/volume override is exposed by these CLI modes. Ordinary
callers retain the current native Windows-only binding adapter and local identity.

The private JSON contains `actor` with exactly `account_id`, `workspace_id`,
`project_id`, `device_id`, `generation`. A seed preview adds `selection` (a list
of `content_class`/`relative` pairs), `operation_id`, and `destination` equal to
`checkpoint-<operation_id>`. Publication takes that exact preview as `plan` plus
`--accept <plan_sha256>`. Inspection uses `--relative checkpoint-<operation_id>`.

A reconstruction preview adds `source`, exact `package_id`, `operation_id`, and
`destination` equal to `reconstruction-<operation_id>`. Commit supplies `plan`
and its exact `--accept` digest; inspection uses the corresponding `--relative`.
Destinations must be new beneath an existing selected-results root. All included
classes need matching read grants; reconstruction also requires their write
permissions and the restrictive local adoption control. No active adoption occurs.

Portable payloads omit private roots, principals and local authorization stores.
Preview JSON is private planning data, not transferable authority. The initial
format rejects parents/deltas, tombstones, native/sensitive paths and known
instruction-discovery files. Existing destinations, interrupted attempts and
stale locks are not overwritten, retried or deleted automatically.

To run only the new benign synthetic proof, use an existing compatible Python:

```text
python -B scripts/tests/Accept-ManagedWorkspaceCheckpoint.py --output-parent EXISTING_PRIVATE_PARENT
```

Choose a parent outside Git, cloud folders, Codex and portable vaults. The runner
uses explicit fixture identity/volume, does not prompt for sign-in, retains only
synthetic evidence, and leaves fixture access stopped. It does not prove native
Windows/macOS or multi-device acceptance. Default unit command:

```text
python -B scripts/tests/Test-ManagedWorkspaceCheckpoints.py
```
