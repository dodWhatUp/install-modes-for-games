# MCI-13 — Windows account verification

The user selected **the Windows account on each computer**. The first adapter uses Windows' own PIN/Windows Hello verifier for the current signed-in account. It is implemented in source; interactive acceptance remains pending. MCI-13 stays at 5/6 and program progress stays 47/108.

## 1. Reuse and identity decision

The existing `workspace_state.principal()` observes the current Windows token SID and machine identity. `AccessStore` already owns enrollment, roles, expiry, policy acknowledgements and stop. No existing fresh Windows verification adapter was found in the task's source. The change extends these owners and the existing CLI/report rather than adding a credential database or another control center.

Windows' [UserConsentVerifier](https://learn.microsoft.com/en-us/uwp/api/windows.security.credentials.ui.userconsentverifier) verifies the current logged-in account through a configured PIN or biometric. Desktop applications use [IUserConsentVerifierInterop](https://learn.microsoft.com/en-us/windows/win32/api/userconsentverifierinterop/nf-userconsentverifierinterop-iuserconsentverifierinterop-requestverificationforwindowasync) with their own HWND. This adapter conservatively requires Windows build 22000 or later. ABI identifiers come from Microsoft's [SDK metadata](https://github.com/microsoft/win32metadata/blob/main/generation/WinSDK/RecompiledIdlHeaders/winrt/windows.security.credentials.ui.h) and desktop interop header.

Decision: verify each computer locally. Two accounts with the same visible name are not presumed to be the same identity. This is current-account re-verification, not signing into a different Windows account, linking Microsoft cloud accounts, remote authentication or network pairing. A password-only account without a configured verifier is currently unsupported; failure never falls back to session checks. Windows settings are not changed automatically.

## 2. Implemented behavior

| Entry | Behavior |
|---|---|
| `windows-account-status` | Headless availability and desktop-interface probe; no prompt or account changes. |
| `access-windows-create --state NEW_PRIVATE_ROOT` | Verify through Windows before creating a new local registry. Bootstrap roles still grant no storage access or policy acknowledgement. |
| Existing `access-preview` with action `require_windows_sign_in`, values `{}` | Prepare an inert upgrade of the selected legacy registry. Existing actor/project/generation checks apply. |
| `access-commit` | Exact preview acceptance; a protected registry or upgrade invokes Windows verification for that full proposal. It rechecks expiry/stop/authorization and refuses revision drift. |
| `resume` on a protected registry | Verify for the current registry revision, actor and exact stop marker; recheck under the existing cooperative lock. |
| `stop` | Immediate and independent of sign-in, registry decoding or network availability. |

Native results remain inside the process. The one-use proof binds the current principal, exact operation and selected local path, and expires after 60 seconds. It is never a JSON token, transfer file or persistent credential. Account aliases retain the existing local-OS subject binding; the new mode adds re-verification. Existing `access-create` and old registries remain visibly labeled as **session checks only**; they are not silently upgraded. Managed reads/writes use current enrollment and scoped policy/storage grants; they do not prompt on every file. Protected enrollment creation, administrative changes and resume do prompt.

Python never receives a password, PIN, biometric, reusable Windows token or credential-store record. Windows retains those owners. Local audit revisions contain the authentication requirement and selected configuration, not an authentication secret or reusable receipt. Same-user processes able to edit source/state remain inside the trusted local-operator boundary; this is not an OS sandbox, hardware attestation or protection from a compromised same-user process.

Decision: retain existing portable-data exclusions. Nothing about selecting Windows accounts permits copying credentials, native Codex databases, browser profiles, local permissions or machine bindings.

## 3. Verification and remaining acceptance

The native headless probe on this Windows computer returned `available`, including successful activation of the desktop interop interface. This does not establish that an interactive verification succeeded. Twenty new automated contract tests cover cancellation and unavailable results, exact operation/account/time binding, one-use proof, tampering/staleness, downgrade refusal, stop and revision drift during the prompt, expiry recheck, resume cancellation and asynchronous cleanup. Existing suites were rerun separately; see [validation](MCI-13-WINDOWS-VALIDATION.json).

The local lab records Windows as not provisioned/accepted. Linux cannot validate a native Windows authentication dialog. No host GUI interaction or unattended credential prompt was attempted. The native Tk owner window, Windows prompt, actual PIN/biometric success, cancellation and behavior on a second computer require human acceptance. Failure in those checks requires repair before item four can close.

<details><summary>Run the bounded local human acceptance</summary>

Use the existing Python runtime to run `scripts/tests/Accept-ManagedWorkspaceWindowsAccount.py --local-parent EXISTING_PRIVATE_PARENT --host-label A`. This now defaults to non-writing preflight. Add `--run-interactive` only when the human is present for both prompts. Choose a parent outside Git, OneDrive, Codex and the portable vault. The [native/physical acceptance packet](MCI-08-NATIVE-ACCEPTANCE.md) separates both hosts and the physical gates; private launchers supply the selected source/runtime paths.

1. In the first **Windows** prompt, confirm using your local PIN or biometric.
2. In the second Windows prompt, choose **Cancel**.

The interactive harness creates only a new unique synthetic access registry, requires Windows' explicit canceled result, saves a private receipt with source hashes and runtime and leaves fixture access stopped. It does not modify existing access registries, real project defaults, Codex or Windows sign-in settings. A failed/unavailable API result is not accepted as a cancellation pass. Retain the receipt for review; do not publish local identities or bindings. Repeat independently with `--host-label B` on the other computer when available; do not move the registry or proof between machines.

</details>

Decision: identity selection is resolved; the adapter is ready for interactive acceptance. MCI-13 item four remains unchecked until that acceptance succeeds. Network pairing, cloud adapters and remote operation still require their own dependent stages.
