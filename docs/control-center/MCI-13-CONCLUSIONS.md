# MCI-13 conclusions — 2026-10-20

Result: 5/6 checklist items accepted. Fresh supported sign-in / provider-specific credential integration remains open; the task is not complete.

| Item | State and evidence |
|---|---|
| Separate identity / enrollment / membership / storage permissions | Implemented in a destination-local, workspace/project-scoped registry. Logical local account IDs bind to the current OS principal and machine, not a transplanted account session. |
| Distinct roles | Viewer, contributor, operator and policy administrator have separate capabilities. An operator proposes named operations; this grants neither arbitrary commands nor execution approval. |
| Central proposals with local restrictions | Policy proposals remain subject to destination acknowledgement, project scope, independent storage grants and hard exclusions. |
| Fresh supported sign-in and native credential owner | Pending. Local OS-session querying is implemented; it is not a new provider login. No provider account, token, browser profile or credential store was copied, created or changed. Identity-provider selection is pending. |
| Enrollment lifecycle | Local enrollment, revocation, bounded expiry/renewal, policy acknowledgement, monotonically increasing writer generation and permanent retirement implemented. |
| Least privilege / offline / stop | Role, account/project/storage scope, offline/stale device, policy drift, old generation and emergency-stop tests passed; the public CLI refused real synthetic placement after stop and revocation. |

Windows identity is freshly queried from the current process [access token](https://learn.microsoft.com/en-us/windows/win32/secauthz/access-tokens), and combined with machine-local identity. Linux fixture checks use local UID/machine identity. Neither is remote authentication or hardware attestation. Copied declarations cannot establish a fresh provider sign-in. Same-OS-user processes already able to edit these files remain within the trusted local-operator boundary; the registry is not an OS sandbox or a replacement for filesystem ACLs.

The local stop marker is checked independently of registry decoding or network availability. Resuming requires current local administration and the exact reviewed marker. Managed CLI publication locks binding/policy/access revisions and rechecks stop/authorization immediately before writing. An already in-flight filesystem write is not claimed to be forcibly rolled back.

Evidence: 18 access/presentation tests passed in Linux, plus native Windows placement/stop/revocation acceptance. Metadata uses existing file/journal/lock owners and the existing control-center renderer. No authentication or remote service was activated; fixture authorization was left stopped.

Decision: keep MCI-13 open with item four unchecked. Implement and verify an appropriate fresh sign-in adapter once the identity provider is selected. Network pairing and remote operation additionally require MCI-10/14 and actual-device acceptance.
