# Review and known boundaries

Read [`README.md`](README.md), [`GAP_AUDIT.md`](GAP_AUDIT.md),
[`EXTENSION_GUIDE.md`](EXTENSION_GUIDE.md) and
[`../KEYBINDS-MERGE-VALIDATION.json`](../KEYBINDS-MERGE-VALIDATION.json).
The focused R2 review also checks schema/runtime parity, current document routing,
recipe-revision compatibility and preview launcher portability.

Implemented safeguards include related-file guards, conservative context overlap,
stable selection after array reorder, immutable draft lineage, no fake mod recipe for
keybind-only games, portable archive validation and no code import from data packs.
The JSON Schemas are editor contracts; runtime validation remains authoritative for
cross-field, filesystem and native-adapter semantics that schemas cannot express.

This is local cooperating-software safety, not an OS security sandbox. Trusted Python
adapter code and an account able to modify both code and receipts remain trusted.
Hashes are identity evidence, not publisher signatures. No live-game, native Windows
or current installed-client acceptance is claimed.
