# Safe Installation, Testing, and Rollback

## Before installation

- Close the game and its launcher.
- Verify game files, then launch the stock game once.
- Record the game build, GPU driver, display mode, renderer, and current graphics settings.
- Back up user settings as well as the executable directory. Steam verification does not restore every file in AppData, Documents, or Saved Games.
- Disable automatic cloud restoration while testing settings-file changes if it keeps overwriting the local baseline.
- Do not test in multiplayer or an anti-cheat-protected executable.

## Snapshot the baseline

At minimum, record hashes and versions for these names when present:

```text
dxgi.dll
d3d9.dll
d3d11.dll
d3d12.dll
winmm.dll
nvngx_dlss.dll
nvngx_dlssd.dll
nvngx_dlssg.dll
sl.interposer.dll
sl.dlss.dll
sl.dlss_d.dll
sl.dlss_g.dll
```

Use [Get-ModFileReport.ps1](../scripts/Get-ModFileReport.ps1) to create a CSV without copying proprietary files.

## One-variable test loop

1. Create a named snapshot.
2. Change one component or one group of related settings.
3. Launch through the normal store/launcher path unless testing launcher isolation.
4. Wait through shader compilation and enter repeatable gameplay.
5. Save the relevant logs before the next launch overwrites them.
6. Record the visible result, log result, performance, and shutdown behavior.
7. If it failed, roll back before trying a different path.

Use [Experiment Log](../templates/EXPERIMENT-LOG.md) for each test.

## Proxy-DLL hygiene

Only one component should own a proxy name. If both ReShade and OptiScaler want `dxgi.dll`, use the chain-loading method documented by those projects or choose one. Do not solve a collision by randomly renaming DLLs.

Search the executable directory for abandoned proxies after every uninstall. A renamed old build can still be loaded before the component you think you are testing.

## Updating

- Remove the old install with its own uninstaller or manifest first.
- Preserve only user-authored INI/preset changes.
- Re-read release notes; add-on API versions, filenames, model contracts, and defaults change.
- Re-test from the baseline. A setup that worked with one driver or ReShade version is not automatically valid with another.

## Rollback

1. Close the game, launcher, helper process, and shader compiler processes.
2. Remove only files listed in the install manifest or experiment log.
3. Restore overwritten stock files from the baseline.
4. Restore user settings if the game cannot rebuild them cleanly.
5. Verify game files through the store.
6. Launch stock once and inspect the directory again for leftover proxy DLLs or Vulkan-layer configuration.

Avoid blanket deletion scripts. A safe rollback script must validate the exact game path and exact filenames before removal.
