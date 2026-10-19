# MCI-04: static request preflight and minimal wording

Outcome: implemented a local draft checker with source-cited declared defaults, conflicting declarations, missing referents, broad/action-related wording and conditional skill cues. Original, suggested and deliberately selected wording remain separate.

Decision: remove only an allowlisted standalone English-output-default line when a fresh selected source supports it, the selected context reports it loaded and no applicable default conflicts. Never remove an exclusion/action boundary, a partial sentence or the last meaningful content. Otherwise keep the original and explain the uncertainty. Imported loaded-state claims are contextual reports, not platform attestation.

Acceptance of an alternative rechecks both draft and source revision. Editing, reloading or source drift invalidates the previous result. No request is submitted, no instructions are rewritten, no model/API is called and no exact response is predicted. Semantic equivalence and quality improvement are not guaranteed by these static checks.

Validation includes positive/negative/ambiguous requests, conflicting/out-of-scope/historical rules, source drift, original/exclusion preservation, no empty rewrite, explicit acceptance and editing invalidation. The source core works independently of the pending native accessibility acceptance in MCI-03.

Next: collect human usability evidence before broad acceptance. Optional model-quality trials remain MCI-16 with their separate budget/credential gates.
