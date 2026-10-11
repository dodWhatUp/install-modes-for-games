# Reproduce the R8 candidate files and offline checks

Use a new private working folder with a copy of the R8 source. Python 3.9+ and Node are sufficient for native compilation, the model and query/event tests. The optional static HTML checker uses already-installed BeautifulSoup4. No installer is included. Do not execute these commands in the live game or Azeron configuration directory.

Input: the exact prior `Azeron_R7_Complete_Recovery.zip`, SHA-256 `91d9c4d0fee4c2ebed54e38f4dbe8d0a8889d49b73824756150159d06ae65a6f`. It is included under `prior/` in the complete R8 recovery and remains at its existing private Drive identity. It contains the exact R6/R5 source roles, not the current Windows state.

```text
python prepare_inputs.py --r7-archive PATH_TO_R7_ZIP --out NEW_INPUTS
python design_r8.py --r6 NEW_INPUTS/r6/research/DESIGN_R6.json --out DESIGN_R8.json
python compile_profiles.py --source NEW_INPUTS/r6/inputs/r5/profiles/01_SHARED_R5_BASIC.json --design DESIGN_R8.json --out NEW_NATIVE
python validate_profiles.py --source NEW_INPUTS/r6/inputs/r5/profiles/01_SHARED_R5_BASIC.json --design DESIGN_R8.json --native NEW_NATIVE --prior NEW_INPUTS/r6/inputs/r5/profiles --prior NEW_INPUTS/r6/native --original NEW_INPUTS/r6/inputs/r5/SOURCE_original_backup.zip --output QA_NATIVE_R8.json
python extend_actions.py --prior NEW_INPUTS/r7/REVIEWED_ACTIONS_R7.json --design DESIGN_R8.json
python audit_designs.py --r6 NEW_INPUTS/r6/research/DESIGN_R6.json --r8 DESIGN_R8.json --corpus NEW_INPUTS/r6/inputs/r4/CORPUS_AUDIT_R4.json --scenarios NEW_INPUTS/r7/SEMANTIC_AND_DEMAND_REVIEW_R7.json --model NEW_INPUTS/r6/research/audit_r6_access.py
python build_atlas.py --design DESIGN_R8.json --output ../Azeron_R8_Action_Atlas_HE.html
python render_markdown.py RESEARCH_R8_HE.md ../Azeron_R8_Research_HE.html
node test_atlas.js ../Azeron_R8_Action_Atlas_HE.html
node test_ui_events.js ../Azeron_R8_Action_Atlas_HE.html
python test_collector.py
python check_artifacts.py --html ../Azeron_R8_Action_Atlas_HE.html --prior-actions NEW_INPUTS/r7/REVIEWED_ACTIONS_R7.json
```

The native compiler refuses an existing output folder. Identical exact source/design inputs produce identical IDs and files; changed design bytes produce a distinct candidate. That does not authorize repeated imports or prove importer collision handling. Never treat a delivery ZIP as an Azeron backup-restore ZIP.

The DOM test is a minimal fixture executing the authored event handlers, not a browser engine. CSS row arithmetic and code tests do not prove actual visual rendering, game focus or hardware behavior. The previous denied browser route was not retried.

The source collector is a separate preparation tool. It does not run during the reproduction steps except against synthetic fixtures. Use `CODEX_COORDINATION.md` before actual private configuration reading. `INPUT_EVIDENCE.json` is not a complete original-source backup and must never be marked effective merely because extraction succeeded.

Publication receipts postdate the immutable delivery archive they describe. Do not overwrite a later receipt with a pre-publication placeholder during reproduction. Referenced prior source/architecture records stay with their existing canonical owners.
