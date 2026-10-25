# Game saves, release checks and recovery coverage

When checking a game's installed version, reconcile the store manifest with a
recent game log or executable identity. Match it to the actual public branch;
a showcase or an announced beta does not establish an available game update.

Keep current-build save compatibility separate from the next major release's
reset policy. Record a user's successful character load as user-reported
acceptance, without turning that into proof that every mod or every save works.
Build-numbered save folders and timestamps support migration analysis but do
not replace a successful load.

Take an immutable checkpoint of saves, native settings, per-game launcher
settings and relevant mod/controller recovery. Hash-verify copied files and ZIP
entries. Upload private recovery to the verified private Drive destination and
download it again to compare hashes. Publish only sanitized history, authored
source and recovery coverage in GitHub; omit saves, account identifiers,
credentials, game binaries, downloaded mods, private paths and full logs.

If a connector rejects a large archive, preserve the original locally and split
it into immutable parts below the connector's limit. Record each part's name,
size and hash, and verify the reconstructed whole archive after Drive readback.
Provide a tested reassembly helper that does not change game files or relax
machine execution policy. Keep a failed pre-invocation upload distinct from a
successful stored file.

Recheck installation state immediately before copying or updating. An uninstall
can remove the executable and store manifest while leaving saves and mod files.
A snapshot of those remnants is not a base-game backup. Record the omission and
any historical manifest explicitly; do not claim full rollback coverage or a
completed reinstall from cached library metadata.

Preserve earlier checkpoints. Restore only the intended scope while the game is
closed, after preserving the destination's current state. Archive verification
is separate from a tested gameplay restoration.

Applied example: [No Rest for the Wicked checkpoint, 2026-10-25](../games/no-rest-for-the-wicked/BACKUP-2026-10-25.md).
