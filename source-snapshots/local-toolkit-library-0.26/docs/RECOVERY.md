# Recovery

Exact rollback restores retained original bytes only when current files still match
the applied copy. Selective rollback regenerates only the inverse binding changes
against current files, keeping later unrelated edits; conflicting later bindings
and shared-file ownership remain blocked. Every rollback needs a new staged inverse
and local approval through the same controller. Multi-file replacement is not atomic.

After timeout inspect the SAME request/plan with status and reconcile; no replay of
attempted/unknown effects. Only verified before/after states can participate in a
reviewed recovery. Corrupt or foreign current contents are not silently overwritten.

Pack import pins all payload bytes, not native game files. Interrupted imports stay
incomplete and cannot silently become trusted. Inspect them; retain original sources.
Pack publication does not activate an instance. Instance registration itself writes
metadata only. `registration-status --instance ID` distinguishes completed and
incomplete intakes; the same exact intake can be finished after renewed local review
only with unchanged originals and no competing owner. Different source hashes or
intent are not automatically adopted. Scoped orphan targets cannot run a plan before
the complete instance and pack guard exist.

`lock-inspect --kind operations` and `lock-inspect --kind registration` inspect ONLY
this module's known cooperating locks. `lock-retire --kind ... --inspection-sha HASH`
requires an interactive local confirmation and a verified dead owner, archives the
old lock bytes and does not replay any plan. Unknown/live owners, integrity failures
and denied access stay stopped. AI exposes lock inspection only.

No automatic active-pack migration, backup pruning, cloud conflict resolution,
whole save restore or rebuilding of exact damaged source bytes exists.
