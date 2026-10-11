# Path of Exile 2 — R8 input review, 2026-10-11

Read-only Windows collection preserved `poe2_production_Config.ini` hash `80d43307923862d0c2816349362888315fdb0cdfcd68eb6b7e0d2097212269be`. ACTION_KEYS and WASD_ACTION_KEYS each contain 97 records; 14 differ. GENERAL `user_input_mode=wasd` and `last_selected_KBM_input_mode=wasd` conflict with UI `use_wasd_to_move=false`. The effective bank remains unknown; modifier token `2` was not decoded by assumption, and skill slots do not identify equipped skill names.

Selected input receipts stay private. See the [Windows receipt](../../docs/AZERON-R8-WINDOWS-READ-2026-10-11.md) and [sanitized hashes/counts](../../evidence/AZERON-R8-WINDOWS-READ-2026-10-11.json). No game setting, native profile or overlay trigger changed. All 23 current native SOFTWARE profile files were preserved. R8 is NOT_INSTALLED.

The separate COMBAT/MENU proposal, existing diagrams and user-stopped UI work remain owned by their original workstream; its F15 trigger and installation are unresolved. This review does not replace that source or resume the stopped task. Local detailed history and newer uncommitted mapping work were left intact.

No runtime rollback is needed. Next: establish the active bank and modifier meaning through supported evidence, then record the family choice and separate installation authority before a fresh complete backup, additive import and physical checks. No gameplay, save or benchmark was opened.
