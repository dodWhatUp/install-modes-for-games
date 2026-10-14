# AI Efficiency Foundation limitations

## Not established

- Connection through a specific ChatGPT Desktop, Codex or other product UI. Native Windows/Tk and an independent external stdio client passed; product-specific configuration and UI behavior remain separate.
- Streamable HTTP, remote authentication, plugin deployment or MCP App UI.
- Production installation or migration from an existing local profile.
- Real game, manager, RHI, Steam Input, reWASD, Azeron or physical-device state.
- Installation, upgrade, disable, rollback or runtime/gameplay verification.
- Adoption into the canonical repository `main` branch. The validated source exists only on a task branch until reviewed and merged.

## Evidence boundaries

- The modern and legacy protocol routes passed an independent external Windows stdio-client run. This does not establish a specific ChatGPT/Codex product connection or remote transport.
- Search/resources validate only curated package files. They do not index private
  runtime state, unrelated repositories, cloud drives or the whole computer.
- `game_tools_catalog` is planning evidence. It does not prove a component is
  installed, compatible or active in one game.
- `game_tools_reports` reads only summaries already shared through the existing local
  route. It performs no new provider connection or benchmark.
- The handoff capsule is an in-memory preview; no file or cloud artifact is created by
  that tool.
- One broad `FocusHost` GUI suite stopped during
  `test_navigation_and_zoom_do_not_change_plan` after six earlier cases passed. The
  process state was inspected, no process remained, and it was not retried.
- The earlier R2 `GameModPanel` bounded timeout remains inherited and was not rerun in
  this slice because the affected source was unchanged.
- PowerShell 7 remains unavailable in the Linux packaging environment. This no longer blocks Windows acceptance: the final candidate passed 67 source-export contracts and a real source export under native Windows PowerShell 5.1.

## Safety retained

A client may read, preview or place a proposal into the existing local mailbox when
that connection was explicitly proposal-enabled. It cannot approve, execute,
register arbitrary paths, start a game, inject input, capture, download or publish.
Unknown effects are never converted into an automatic retry.

## Canonical candidate boundary

The exact tested product source is commit `42dc939bd37ff37e5af2cb429bce6d0aeb3eb29d`. Its R7 inventory contained 708 payload files and passed the native focused gate. Any later documentation-only receipt commit does not expand runtime acceptance. The branch still requires pull-request review and main-branch adoption.
