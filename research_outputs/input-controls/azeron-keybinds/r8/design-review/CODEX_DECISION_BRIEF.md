# Bounded design review — decision delta before R8 execution

Owner: `dodWhatUp/install-modes-for-games`. This is a design decision supplement, **not R9**, not a new native family, and not authorization to install. Continue the existing `r8/preflight/READY_FOR_CODEX.md` for tools, recovery and execution gates. Do not repeat or bypass the blocked `preflight/PUBLICATION_RECEIPT.json` write; it remains outside this task.

## New findings to use

1. **The BASIC maps have 24 identical keyboard outputs at identical positions.** Of 30 digital cells only #30 differs: CORE5 has Caps Lock; SPARSE6 has SYMBOLS. The five shared banks differ in 23 of 150 cells. Family selection is mainly about auxiliary reach, preserved blanks and learning, not two different combat bases.
2. Of the existing 32 targeted demands, only three differ in recorded route/directness outcome between these two families: Shift+F8 without movement favors SPARSE6 in the model; zero+movement and Ctrl+Shift+8+movement favor CORE5. These are not representative usage data. Same status can hide different comfort costs.
3. The 32 cases have 28 distinct exact key/movement/directness signatures. Keep their semantic contexts, but do not treat repeated physical signatures as independent quality evidence.
4. The old `meets_direct_requirement` flag only evaluates the directness clause. When no direct access was requested it can be true even for a route conflict. It is not overall success. Native availability, directness, real output and task usability are separate.
5. CORE5 aligns 1–9 and F1–F9 across the number/tool banks; SPARSE6 aligns 1–6 only. CORE5 MENUS contains Left/Right/Down but not Up Arrow. Test an actual menu workflow rather than assuming the MENUS label implies complete navigation.

The full rationale and external evidence limits are in `DECISION_REVIEW_HE.md`; exact calculations are in `REVIEW_FACTS.json`. No native output or original research record was changed.

## Conditional recommendation — do not choose by a raw score

If the user's requested nine blank finger positions remain a binding comfort constraint, **SPARSE6 is the first candidate for preference-fit evaluation**. CORE5 is the comparison candidate, not an automatic default because it has fewer banks. If those positions are acceptable for the actual tasks, and continuous movement with numeric/modifier commands matters, CORE5 may be preferable.

Do not ask the user to restate a known constraint. Do not install both to avoid resolving the choice. If neither family solves an important shared-base task, inspect a narrow reversible adaptation rather than switching between near-identical bases or adding layers blindly.

## Next actions in order

**Read-only first.** Read current effective-input evidence for PoE2 and Cyberpunk through the already-prepared v2 collector, after source/path validation. Preserve input-mode, hold/toggle, context and mod/tool-override uncertainty. A skill slot is not an equipped skill name. Do not launch games or change settings just to complete this read.

**Then narrow the experiment.** Reuse the existing preflight physical-plan IDs. The six decision groups are:
- A: output/selector/release integrity (`selector-*`, `anchor-*`, `held-output-transition`); failure blocks adoption.
- B: the recorded nine-cell comfort constraint; no repeated forced/painful presses to justify it.
- C: relevant discriminating tasks (zero/movement, required modifier-number chord, deliberate Shift+F8). Skip a stress case that has no actual task role.
- D: shared-base risks (T/movement, urgent unavailable key, ordinary-letter chords). These do not discriminate the two families.
- E: one verified menu-entry/navigation/exit loop and a brief bank-choice check; separate semantic confusion from reach difficulty.
- F: icon/text identification and eventual Peek-then-release versus sustained Peek. #19 is still reserved with no emitter assigned.

**Only after existing choice/authority gates:** fresh before-export, supported additive import of one family, independent after-export review, then safe physical and game checks. Keep known-good and current state, all original/R5/later profiles and unrelated sessions intact. Read current repo head/writers before edits. No new sync queue, scheduler, input hook, host rewrite or generic recipe execution is part of this delta.

**Learn without confounding.** Keep game binds, native family and label style stable while comparing one factor. Equalize basic familiarization, note first-attempt correctness/wrong bank/wrong key/movement interruption and reported discomfort, and use a small delayed repeat only if needed. Do not report population-level significance or long-term learning from a few presses.

## Stop/reopen rule

The analysis stage is now sufficient to start collecting consequential real data. Reopen deep design only when a concrete config, physical or task observation challenges the current assumptions. No more profile generation merely for a new revision. The 78-output vocabulary is a preserved current target, not a proven universal optimum.

Record actual readback, import, user-hand tests, game recognition and live host consumption separately. A Git link or PR comment is source coordination, not a running Windows task acknowledgment. Keep private evidence in the existing Drive route. The earlier preflight receipt denial remains unresolved and is not retried by this review.
