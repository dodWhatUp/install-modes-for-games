# MCI-03: architecture, instruction and trigger explorer

Outcome: implemented a selected-source explorer with current-project inventory, an editable searchable selector, dependency graph/list, exact locator/hash details, scope filtering, declared-vs-reported-loaded status, conflicts, repeated defaults and explicit unknown coverage.

Codex instruction-chain discovery follows the [documented global/project root-to-directory and override order](https://learn.chatgpt.com/docs/agent-configuration/agents-md). Fallback names and byte limits are explicit inputs; the application does not edit Codex configuration. Actual platform/session authority and hidden context remain unobserved. Source hash changes invalidate preflight and accepted alternatives.

Decision: preserve the external architecture-map owner and provide this missing local instruction/capability projection in the existing toolkit. Register an additive System control route; keep existing Mods/AI routes and services.

Validation: real Tk tests in the isolated Linux display cover search/selection cancellation, keyboard commitment, graph visibility without policy changes, narrow layout/text scaling, missing sources and stale-source refusal. Visual inspection used an actual guest screenshot. Linux Tk did not expose an AT-SPI tree through the lab's native accessibility adapter; that limitation is retained, not labeled PASS. Windows UI and screen-reader acceptance remain unverified.

Next: keep MCI-03 open for platform accessibility acceptance; its source/dependency model is available to MCI-04. No host desktop test or installation is implied.
