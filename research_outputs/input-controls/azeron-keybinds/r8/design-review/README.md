# Universal layout design review — bounded R8 decision supplement

Read **DECISION_REVIEW_HE.md** for the complete decision and evidence qualifications; **CODEX_DECISION_BRIEF.md** is the execution delta to the existing preflight handoff. This directory is not a new profile family.

New exact findings: 24 BASIC keyboard outputs at the same positions; only BASIC #30 differs. Five common banks differ in 23/150 cells. The 32 inherited targeted cases have 28 exact input/movement/directness signatures; three distinguish family outcomes. These diagnostics are not quality scores or gameplay tests.

Recommendation is conditional: preserve the user's nine-cell sparse constraint first when it is binding; otherwise compare only useful differential tasks. Do not select CORE5 by layer count or SPARSE6 by blank count alone. Preserve existing R8 profiles and existing execution gates. No input/config/native/host changes were made.

## Reproduce the small comparison

Python 3.9+ standard library suffices. Obtain exact R8 `source/DESIGN_R8.json` and `source/AUDIT_R8.json` from the already-published private R8 recovery, or the verified prior package. No re-upload from the user is needed. Do not regenerate profiles.

```text
python review_existing.py --design PATH_TO_DESIGN_R8.json --audit PATH_TO_AUDIT_R8.json --output NEW_REVIEW_FACTS.json
```

The script refuses to overwrite the output. The exact input hashes and expected diagnostic counts are recorded in REVIEW_FACTS.json. It only reads existing source and writes the chosen new analysis output. It does not run a game, import native data or check actual hand comfort.

The HTML report is a derivative of the Markdown memo; generated delivery files are stored privately in the existing Drive folder. Git owns the authored memo and scripts. Use the stable project/Drive index for discovery. Only a scoped publication update is appropriate; no whole-project or running-session sync claim follows.

The previous safety-blocked `r8/preflight/PUBLICATION_RECEIPT.json` remains absent/pending and is not created, repaired or bypassed here. This is independent design work, not a retry of that blocked operation. Prior profiles and recovery archives remain exact. No private UUIDs, configuration files, source game assets or raw logs belong in this authored directory.
