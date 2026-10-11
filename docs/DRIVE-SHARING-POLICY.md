# Drive file sharing

Reviewed 2026-10-11. The user wants intended files created in Drive to be accessible to the recipient stored in a private Drive preference record, without repeatedly restating the recipient. The exact email and its private record location are intentionally excluded from this public repository.

## Routine for new Drive deliverables

1. Create or upload the file to the intended private Drive destination.
2. Read the recipient from the private preference record and verify it matches the current user instruction when one is present.
3. For a normal, intended deliverable without secrets or unrelated personal data, grant that recipient reader access on the individual file. This allows viewing and, when the file type and owner settings permit, downloading.
4. Read back the file's permission metadata and verify that the intended recipient has reader access. Report any failure; a URL alone is not proof of access.
5. Preserve the file's existing privacy otherwise. Never create an anyone link or grant access to a folder or unrelated files as a shortcut.

Follow any action-time authorization that applies to permission expansion. The recorded preference expresses the user's intended default; it does not override a platform or tool confirmation requirement. Do not share secrets, credentials, financial or health records, unrelated personal files, or broad recovery bundles without specific approval.

## Existing Drive files

Before bulk sharing, identify the exact folder or file set, report the item count and content category, and obtain approval for that scope. Do not infer that “all files” means every item in the connected account when the account contains unrelated project material. Apply reader access to each approved file individually and verify each result. Record partial failures and retry only failed items.

## Current connector limitation

The connected Drive tools support sharing a single file to a named user. They reject folder URLs for sharing and expose no global default for future uploads. Therefore, automatic behavior currently means applying the per-file routine to each new intended deliverable after upload; it is not a Google Drive account setting. The connected Drive identity may differ from the intended recipient account, so never assume that ownership or can_download for the connector proves the recipient can access a file.

## Development queue

- Build or adopt a narrowly scoped post-upload helper that reads the private recipient preference, shares only newly created intended deliverables, and verifies permissions with an idempotent retry path.
- Add a recipient and owner identity check before each grant; surface mismatches and provider errors without widening access.
- If the connector later supports folder permissions, evaluate a dedicated output folder with inherited reader access. Do not replace per-file verification until inheritance is confirmed for the target account.
- For approved legacy migrations, inventory and categorize files first, then apply a reviewed exact allowlist and produce a permission receipt.