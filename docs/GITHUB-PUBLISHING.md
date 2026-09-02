# GitHub Connection and Publishing

## Canonical destination

- Account: `dodWhatUp`
- Repository: `install-modes-for-games`
- Web: <https://github.com/dodWhatUp/install-modes-for-games>
- Git remote: `https://github.com/dodWhatUp/install-modes-for-games.git`
- Default branch: `main`

This is the permanent destination whenever the request concerns connecting GitHub for this game-modding knowledge base, uploading modding history, or updating previously recorded game lessons. Do not create another repository for the same purpose.

## Connection rules

1. Confirm that the current workspace is this knowledge base by finding `AGENTS.md` and the `games/`, `docs/`, and `preferences/` structure.
2. Inspect `git remote get-url origin` before changing anything.
3. If `origin` is absent, add the canonical Git remote above.
4. Treat canonical HTTPS and SSH forms as the same destination. If an existing remote points elsewhere, do not replace it silently; stop and ask before changing it.
5. Verify that the authenticated GitHub account is exactly `dodWhatUp` before creating or pushing. A connector or CLI signed in to another account is not an acceptable substitute.
6. Reuse the existing canonical repository. If it appears missing or inaccessible, verify account and permissions before considering repository creation.

## Safe update procedure

1. Read the general rules, preferences, relevant game history, and reusable lessons before editing.
2. Keep private snapshots, game files, binaries, credentials, full logs, saves, and personal paths out of Git.
3. Validate documentation, scripts, links, manifests, and the skill when relevant.
4. Fetch the canonical remote and inspect divergence. Never discard remote or local work to make a push succeed.
5. Commit the curated changes and push normally to `origin/main`. Never force-push unless the user explicitly requests it after seeing the risk.
6. Verify that local `HEAD`, `origin/main`, and the public repository resolve to the same commit.

Connecting GitHub authorizes only the requested repository operation. It does not authorize game installation, launching, mod mutation, or resuming a paused experiment.
