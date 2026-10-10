# Agent-operated game input — workflow and integration

Recorded 2026-10-10. This is the default starting method for **user-authorized** in-game mod/menu/result checks in this project, not permission for routine play, unattended control or new tests. The latest request is documentation, packaging and handoff; live games and MFG/FrameWarp tests remain deferred.

## What the method actually is

Use the supported Windows observation/control tool to inspect the real foreground window and send a temporary trigger. The optional AHK helper receives that trigger, waits for release, checks the target/focus/modifiers/pause epoch/cooldown, then sends a short `SendEvent` keystroke. Observe the game's actual response before the next action.

The agent performed the successful v0.3.1 triggers itself; the user did not have to press each game key. This is not a chat plugin, remote command server, privileged input driver or proof of all-game support. If the supported computer-use surface is unavailable, AHK does not magically supply observation or autonomous control. Respect the active tool's permissions and stop/user-input guards; do not replace them with a hidden command channel.

**Code:** [module and host contract](../examples/game-input/README.md). **Handoff:** [message for the larger AHK chat](../examples/game-input/OTHER-CHAT-HANDOFF.txt). No particular AI model was selected or changed by this request.

## Evidence ledger: versions must not be conflated

| Artifact | Evidence | Status |
|---|---|---|
| Control Helper v0.3.1 | AHK 2.0.30 syntax validation, 20 pure tests and agent-operated live menu/field probes in both games | Historical tested baseline, preserved byte-for-byte |
| Standalone v0.4 extension | Syntax validation and 28 pure policy tests | Prepared text/Enter/Escape/hold extension; never live tested |
| GameInputModule v0.5-preview.1 | Native AHK syntax validation and 36 pure tests through standalone, compatibility and host-example entry points | Include-friendly integration candidate; no GUI/lifecycle/game acceptance yet |

Baseline SHA-256: `EAFD9509DC8B7C579915668648AD20F000D377B5018B5ECE9D4CD9B43F7A46D8`. [Exact source](../examples/game-input/baseline/ControlHelper-v031.ahk). The new module reuses the baseline route, but refactoring it does **not** transfer live verification automatically. Extended input is off by default. The immutable baseline is a rollback/reference artifact, not a second script to run alongside the module.

## Observed live results — menu-only, v0.3/v0.3.1

| Capability | Skyrim | Cyberpunk |
|---|---|---|
| Mod-menu open/close | F8 → F12 opened/closed PureDark; F13 → Delete opened/closed ReShade | F8 → Delete opened/closed ReShade; RenoDX tab accessible by mouse |
| Console-panel toggle | F16 → vkC0 opened/closed Skyrim console; no command submitted | F16 → vkC0 opened/closed actual CET and Ultra+ panels; no command submitted |
| Native selection | Down/Up moved New ↔ disabled Load without activation | Down/Up moved Settings ↔ Load Game without activation |
| Editable field | One digit, Left/Right caret and Backspace in PureDark search; console digit removed | One digit, Left/Right caret and Backspace in ReShade search |
| Native submission/back/holds | Not established | Not established |

Skyrim baseline: Steam 1.6.1170 x64/D3D11, MO2 2.5.2, SKSE64 2.2.6, Address Library v13, PureDark AIO Build 19 Hotfix 1, ReShade 6.8; windowed borderless 2560×1440. User-authorized downgrade followed confirmed 1.7.x incompatibility. Launch through the existing matching MO2/SKSE profile, not Steam Play/Update/Verify. A stock Steam manifest version is not the effective executable version.

Cyberpunk baseline: Steam 2.31 x64/D3D12 with the then-current clean ReShade/RenoDX/CET/RED4ext/Ultra+ X rc7 stack. Native DLSS remained the FG owner; OptiScaler/NR/FrameWarp were not revived. These are dated input observations, not a replacement for the separate [runtime/benchmark workstream](GAME-PERFORMANCE-MEASUREMENT.md) or its newer settings.

Neither test loaded progression or intentionally changed graphics values. Skyrim's active test profile had zero save files. Cyberpunk's directory had 221 files: 220 remained hash-identical; root `user.gls` changed during title-to-menu transition. Its exact semantics were not established. ReShade serialized only `Docking`/`Window` layout changes; other captured graphics/native/CET/Ultra+ settings matched the input baseline. Logs naturally changed. Do not say every file/save was unchanged.

## Failures, resolutions and uncertainty

| Observation | Safe response / lesson | What it does not prove |
|---|---|---|
| Direct F12/Delete/grave/text/Backspace often had no visible effect in Skyrim; helper output worked | Use the observed release-gated, 150 ms `SendEvent` route, one action at a time | Exact rejected input API, Raw Input policy, timing or privilege cause was not isolated |
| F21 rejected by the supported UI tool before delivery | Replace that temporary trigger with supported F2; live Backspace cleanup then passed | AHK or the game rejecting F21 |
| Foreground moved to Chrome/Codex; user-input guard blocked delivery | Stop, obtain a brief hands-off interval and reobserve/refocus the game | A failed game key test, or permission to disable a safety guard |
| First helper launch/self-test produced no output under SingleInstance Ignore | Exit only the old helper, confirm the new visible version; require actual test output plus exit 0 | An empty-output run passing tests |
| Skyrim F12 overlapped Steam Screenshot; D3D11On12++ and two 80000003 exits were observed | Per-game Steam overlay Off was user-authorized; stable bounded probes followed | A proven sole crash cause or absence of gameoverlayrenderer64.dll |
| Skyrim later absent after an unobserved interval | Record unknown exit cause; inspect preserved crash/runtime evidence before another run | The user closed it or the agent caused it |
| Cyberpunk launch returned no targetable window, but process stayed alive | Reobserve bounded startup; wait for its actual window | A failed launch merely from the first UI call |
| Cyberpunk Delete did not close ReShade with search focused | Click observed blank panel space, then one repeat closed it | Universal Delete failure |
| Immediate screenshot preceded a CET/menu transition | Obtain fresh evidence after a short bounded interval before repeating a toggle | A missed action from one early capture |
| Skyrim direct Quit/Return/Alt+F4 failed in that session | Steam Stop with the specifically approved confirmation closed it | Clean in-engine Quit or a spontaneous crash |
| Cyberpunk Alt+F4 had a brief shutdown delay | Confirm process/window disappearance, not just the immediate process query | Failed closure from the first query |
| Helper exit chord failed in Skyrim once but worked with Explorer foreground | Use the helper's own tray/observed Explorer route; verify its exact process exit | Permission to kill all AHK processes |
| A copied Skyrim custom-INI supplement was zero-byte due to same-basename collision | Use the uniquely named active-profile baseline and hash; never restore the bad supplement | A valid backup merely because a copy command succeeded |

Earlier PureDark NVIDIA FG initialization failed with `887A0004` and automatically persisted None/Off. A functioning F12 menu does not fix that graphics failure or prove MFG/FrameWarp evaluation, delivery, third-person behavior or performance. Those checks are deferred.

## Default operating sequence

1. Read this guide and the exact game's latest history. Check authorization and the specific observation needed. Use offline configuration/log checks first when they answer it. Identify executable/build, game/mod bindings, keyboard layout, display mode and competing hooks/remappers. For device/profile work also match the saved device registry; this helper does not enroll or remap a device.
2. Preserve the current state and a different known-good state separately. Hash the exact active files; avoid basename collisions. Keep saves, private logs and configuration backups outside public Git. Never swap loaded DLLs.
3. Prefer the existing supported control route. When direct game keys fail or the recorded helper route is appropriate, use **one** helper-family instance. Inspect `BindingPlan()` against the larger host and other scripts/game/overlay/mapper keys. Reserve temporary triggers; do not rewrite saved bindings or physical layers.
4. Start normally, without administrator/UIAccess/driver installation. Confirm the visible version and READY state. READY/Sent/beep are dispatch status, not game acceptance. Do not change privileges/security/anti-cheat to overcome a refusal. Login/license/permission actions stay user-operated under the active tool rules.
5. Obtain stable foreground and an observed safe menu/field. Send one trigger, then inspect actual response. Do not type in a console, execute commands, activate Continue/Load/New, change graphics values or accept destructive prompts unless that exact action is authorized. No guessed repeated toggles when the state is unclear.
6. If delivery fails, distinguish pre-delivery rejection, wrong field/focus, old helper version, tool-supported key limits and actual game nonresponse. Change one relevant hypothesis at a time. The user's normal Steam-overlay-Off preference applies to requested setup/tests, not an unrequested bulk migration or indiscriminate background-app shutdown.
7. Stop/cancel on user activity, unstable game, unexpected context or task completion. Verify target/helper shutdown as applicable and compare configuration/save manifests honestly. Record exact scope, versions, outcomes, uncertainty, rollback and next authorized boundary.

An external click-through/no-activate status window was observed with borderless Skyrim. Exclusive-fullscreen visibility is untested; do not change graphics/display mode merely to make it appear. Never infer focus from the panel alone.

## Text, Enter and holds: extension contract

The module's experimental opt-in allows one in-memory payload, armed for one live target HWND and pause epoch for 120 seconds. F3 dispatches once after release; Stop/Pause/Cancel/expiry disarm it. It does not activate a window or read command files, listen on a socket, run shell commands, launch games, retain payload history or install startup tasks.

Printable literal text is bounded to 1–4096 characters; `{Raw}`/`{Text}` prevent AHK macro interpretation. Control characters, newline and Tab are blocked; Enter is a separate explicit action. Raw-key and Unicode-text delivery are different transports: character acceptance depends on the game, field, font and keyboard layout. Text mode can use Unicode packets and ignores normal press-duration behavior. “Any string can be prepared” is not “every game accepts any Unicode text.” See the official [Send documentation](https://github.com/AutoHotkey/AutoHotkeyDocs/blob/v2/docs/lib/Send.htm).

Holds are restricted to arrows, Backspace and WASD, requested for 250–2000 ms. Optional repeated down events approximate typematic behavior; a single down event does not create automatic OS-style repeat. This is not analog/gamepad support or proof of engine-polled movement. Cancellation/finally/normal exit release only module-owned holds; physical input and host-owned overlapping keys must not be used concurrently. A small send burst can cross a focus transition; cancellation is best effort, not a transactional boundary or hard real-time guarantee. Forced process termination/power loss bypasses normal cleanup; see [OnExit](https://github.com/AutoHotkey/AutoHotkeyDocs/blob/v2/docs/lib/OnExit.htm).

The host owns key leases, privacy/HUD/recording policy and permitted action contexts. Module Stop does not exit the host, wipe its tray, or change existing profiles. AHK hotkeys cannot be fully audited across other scripts automatically; Start(true) acknowledges a real review rather than detecting conflicts. Disabled module hotkey variants remain disabled in the host interpreter; do not reuse them through a competing owner while active. See [Hotkey](https://github.com/AutoHotkey/AutoHotkeyDocs/blob/v2/docs/lib/Hotkey.htm).

## Remaining acceptance tests — only when requested

- No-input include/native tests first, then temporary ordinary-app checks for safe Start/Stop/restart, status visibility/click-through, unrelated host hotkeys/tray, pause/release/focus loss/expiry, literal punctuation and Unicode. Record input cleanup; a pure test does not exercise these runtime paths.
- In each game separately, main menu only: repeat the known menu/field route, type a harmless mixed-case string into an observed mod search, inspect every character, move caret and remove it without submission. Test Unicode separately. Do not try commands in the console.
- Enter only on an observed harmless submenu/button such as Credits with no save/start/settings effect; verify Escape returns. If no safely activatable target is observed, keep Enter pending instead of choosing Load/New or submitting console text.
- Hold Left/Right in a search caret for a short duration, then verify release by no continued motion. Exercise cancellation on deliberate focus loss/pause and host Stop in a normal app first. This validates a menu hold, not movement gameplay. Held movement would require a separately authorized scene.
- Revalidate the **integrated host** itself. Preserve its input observer, show Unknown rather than inferred device/layer state, exclude synthetic helper triggers/output from physical-activity evidence and recording where applicable, and respect one owner per key. Do not silently broaden to all desktop apps/games.

## Persistence, archive and rollback

The requested project default is linked from AGENTS.md, general preferences and the operating standard. Codex discovers repository instructions at run startup; this does not update all already-running chats, global account settings or the other AHK source automatically. The other chat should explicitly read the handoff/current files. See [official AGENTS.md guidance](https://learn.chatgpt.com/docs/agent-configuration/agents-md).

Canonical GitHub holds authored source and sanitized evidence. Drive holds a dated source/documentation bundle with hashes, under the existing private export-folder permissions. No third-party mod binaries, game archives, saves, personal paths, credentials or raw private logs are bundled. See [distribution](DISTRIBUTION.md).

Rollback: cancel/Stop the module through its host; remove only its optional include/host wiring after the host is closed. For standalone, exit only that helper. Do not restore whole Steam/reWASD/Azeron profiles. Preserve newer source first; the byte-identical v0.3.1 source can be run alone after the newer helper exits. No game configuration restore is required for this source/documentation integration work.
