# Reproduce R7 without changing device profiles

Use Python 3.10+ and Node 18+. The builders use Python's standard library. Optional `check_artifacts.py` needs BeautifulSoup4 and jsonschema; these were already installed in the authoring environment. No installer, native importer or game launch is invoked by these instructions.

The exact input is `Azeron_R6_Complete_Package.zip`, SHA-256 `8d1977ee2aa0e4dccf8e9ed0636bfb91e36dd52dc1fcb4f8a813801b3bdc9205`, from the existing private Drive archive or this recovery package's `prior/` folder. Use the existing authenticated connector rather than making it public. The R6 snapshot is an input, not a current live-state backup.

1. Copy the R7 authored source files to a new working folder. Do not run in an existing live app or user's config directory.
2. Run `python prepare_inputs.py --archive PATH_TO_R6_ZIP --output NEW_INPUT_DIRECTORY`. It verifies the archive's expected hash, checks safe paths and extracts only the three named analysis inputs.
3. From the R7 source folder, run:

```text
python analyse_survey.py --input NEW_INPUT_DIRECTORY/CORPUS_AUDIT_R4.json --output .
python curate_actions.py --corpus NEW_INPUT_DIRECTORY/CORPUS_AUDIT_R4.json --design NEW_INPUT_DIRECTORY/DESIGN_R6.json
python semantic_review.py --design NEW_INPUT_DIRECTORY/DESIGN_R6.json --access-script NEW_INPUT_DIRECTORY/audit_r6_access.py
python build_atlas.py --design NEW_INPUT_DIRECTORY/DESIGN_R6.json --output Azeron_R7_Action_Atlas_HE.html
python render_markdown.py AUDIT_AND_DECISIONS_R7_HE.md Azeron_R7_Research_HE.html
node test_atlas.js
```

The checked native profile families do not need to be rebuilt. Running a native compiler would create fresh UUIDs and would be a different task. `complete_records.py` only rebuilds authored metadata snapshots; a later publication receipt must not be replaced by a pre-publication status merely because metadata was regenerated.

Run `python check_artifacts.py --corpus NEW_INPUT_DIRECTORY/CORPUS_AUDIT_R4.json --design NEW_INPUT_DIRECTORY/DESIGN_R6.json` for optional additional QA. It is not a required user installation step.

The HTML is a self-contained local view. A browser opening it changes neither Azeron nor game bindings. Its native-layer selector is **selected display state**, not live device state. Query/data tests do not prove rendering or host focus behavior. Use a permitted browser test route only; do not retry or bypass a prior access denial.
