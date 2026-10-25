# Path of Exile 2 History

## Current state

- State: Steam build `25379396` is installed. OptiScaler `10.0.0-dev (a8eac0c4)`, build `20260921_140527`, loads as `dxgi.dll` for `PathOfExileSteam.exe` on D3D12. The live full-menu shortcut is now configured as Home (`ShortcutKey=0x24`) under the 2026-10-07 cross-game rule; static verification passed.
- Last known-good: Runtime logs previously showed OptiScaler loading with Insert (`ShortcutKey=0x2D`). Historical Delete (`0x2E`) was also statically verified but not confirmed in-game. The new Home binding is configuration-verified only.
- Paused/resume boundary: During the next normal game session, press Home once to confirm that the OptiScaler menu opens and once more to confirm that it closes. If the setting reverts again, preserve the rewritten file before diagnosing its owner.
- Reminder policy: Do not schedule or resume testing without an explicit user request.

## 2026-10-12 — Preserve chat and future development before archiving

- User request: Preserve the conversation, research, authored material and future development requests, then close/archive this chat.
- Continuation owner: [CONTINUATION-AND-DEVELOPMENT.json](CONTINUATION-AND-DEVELOPMENT.json) records design preferences, current artifact/evidence status, ten future work items and exact resume boundaries. Read current source/device state before resuming; historical requests are not automatic permission to launch games, send mail, schedule work or publish.
- Preservation scope: A separate private archive will contain a visible user/assistant-message projection from this chat's three local history segments, the authored PoE2 sources/assets, the grouped R2 and offline switch-lab delivery ZIPs, private sharing preference and a hash/coverage manifest. Raw runtime logs, hidden reasoning, system/developer instructions and unrelated chats are excluded; attachments outside copied authored assets and onboard device state are referenced/uncovered. The archive is a dated checkpoint, not global memory or continuous synchronization.
- Existing boundaries: Support email remains an unsent draft. Physical gameplay, active R2 layer/overlay acceptance, arbitrary inventory/gem switching and new-account enforcement testing remain pending. Automatic overlay integration retains the original dependency on the unified software being ready/installed, with its current owner state to be reconciled later.
- Closing boundary: Complete archive readback and sharing verification before archiving this chat. The final delivery receipt will postdate the packaged source revision; restore acceptance is separate.
- Final preservation result: [Private chat/material/development checkpoint](https://drive.google.com/file/d/1ZlmC8bWhfiV1291I64Deb9qZaMSk3fOY/view?usp=drivesdk), 2,784,307 bytes, SHA-256 `DED3BD9CF149D133097ED9013EBF4C800FC6F02B3E001174A678A5E2E729BD58`. All 86 ZIP entries and a downloaded Drive copy were verified. Contains 182 visible messages (44 user, 138 assistant), 78 authored source/asset files, two previous delivery ZIPs and ten continuation items. Reader permission for the designated mailbox is verified; no public link sharing was added. [Sanitized receipt](CHAT-PRESERVATION-2026-10-12.json) declares exclusions and checkpoint limits; private copies remain outside this repository and in Downloads. This final receipt postdates the packaged source. No restore/game test or automatic continuation was performed.

## 2026-10-12 — Self-hosting and solo-mode macro scope

- Request and evidence: Review personally hosted PoE2 servers, arbitrary mods and solo/SSF macro permission. [Research record](evidence/SELF-HOSTING-AND-SOLO-MACROS-2026-10-12.json) preserves fourteen targeted queries, seven selected original/current sources and their limits.
- Hosting distinction: The director's November 2024 interview rejects offline support; the current publisher store listing still requires broadband. No supported independent server package or verified playable public emulator was established. Running a client on a remote personal machine would still connect to GGG. Official private leagues provide hosted league administration, not arbitrary server code or a mod SDK. Current public creation text mentions optional difficulty modifiers; the launch announcement's lack of modifiers is not carried forward as current fact.
- Rules: Current developer policy requires manual invocation, a fixed function and one game-interacting action. No solo, SSF or private-league exception is stated. The terms cover both games and restrict unauthorized client/data modification and automation. Absence of PvP does not establish altered permission, detection or machine protection.
- Supported goal: Native skill selection for equipped weapon sets I/II can swap before using the chosen gem skill. This does not equip arbitrary inventory loadouts or replace gems; innate weapon skills have separate constraints. Existing Azeron/overlay work can retain manual bindings and independent displays within the published requirements.
- Boundary: Documentation only. No game, account, server deployment, league purchase, live input test, profile change or email send. Existing ZIP/lab and unsent support draft unchanged.

## 2026-10-12 — Compare enforcement patterns and possible linking signals

- Request and method: Infer what ban patterns can reveal about account/device/network linkage and detection capability. 16 additional targeted queries and original-source follow-up separate identity linkage, violation evidence and restriction scope. [Pattern analysis](evidence/SWITCH-BAN-PATTERN-ANALYSIS-2026-10-12.json) records six comparisons, a linkage matrix, mechanism hypotheses and fourteen sources. Shared factors are not treated as established causes.
- New original evidence: Jarod_GGG's December 12, 2024 reply acknowledges reports of potentially incorrect restrictions. Jacob_GGG's December 15 replies identify a separate IP-banning issue and later say it should be resolved. These are distinct historical incidents; neither establishes current ordinary-macro hardware enforcement.
- Source corrections: Original Act 3 reports include levels 38 and 40, so an exact universal level-40 trigger is unsupported. A Reddit-labelled console-ban example explicitly describes a PC account ban posted through PSN, later reportedly reversed. Another author's differing account states are confused by linking/history and are not a clean comparison. A PoE2DB search result about Predictive/Auto networking resolves to a PoE1 3.25 hotfix; it is excluded as PoE2 patch evidence. Repeated references to the same incident are not independent cases.
- Pattern findings: Same-PC main/alt differences in PoE1 weaken an unconditional immediate machine-wide restriction for those reports without excluding selective device correlation. Repeated new-account bans leave environment, network, account history and behavior confounded. Peripheral brand, OS version and software presence do not have an established standalone causal role. An action-rate kick with immediate relogin, cheating warning, product-license HWID error and account ban are separate outcomes.
- Capability versus implementation: Current policy discloses account/platform, IP, device/install, software and gameplay data. These support possible account correlation and local/gameplay checks; their exact use, weights and restriction rules remain unknown. Microsoft's injected-event flags are a platform capability, not a validated PoE2 detector. Native skills can swap equipped weapon sets, so a visible swap/cast result alone is not proof of external automation.
- Outcome and boundary: A model with separate checks fits the public evidence better than a universal hardware-blacklist explanation. No safe timing, hardware immunity, Windows isolation or individual ban probability established. Additive documentation only; existing profiles/ZIP/lab unchanged, email unsent and no live test.

## 2026-10-12 — Additional unofficial-source review

- Request and coverage: Expand independent/community evidence. 28 additional targeted queries included Reddit, Elitepvpers, d2jsp, original GitHub documentation, Steam indexed discussions and commercial claims. [Unofficial-source addendum](evidence/SWITCH-RISK-UNOFFICIAL-ADDENDUM-2026-10-12.json) records ten selected sources and access limits. OwnedCore's original GameHelper2 thread failed to fetch; no original UnknownCheats enforcement case or watched video was validated.
- Outcomes: Historical PoE1 reports include an alt banned while a main on the same PC remained usable and auto-clicker bans reportedly reversed. An Elitepvpers user reports one month without bans; another reports a nonfunctional updater. These are unaudited outcomes, not current PoE2 hardware-safety measurements.
- New distinctions: External-input developers still acknowledge detection/ban risk. Product HWID license locks differ from GGG hardware enforcement. Path of Matth discussions describe an alleged person-level exclusion and infer possible hardware/IP enforcement without isolating the mechanism; that PoE1 case does not establish ordinary PoE2 macro consequences. Seller assertions about SSF enforcement and hardware protection lack supporting case data.
- Correction: Earlier source S13 omitted December recovery replies. The PoE2 warning author and two other players report the warning disappearing after removal of old loot-filter/custom-sound files. The source record retains its previous observation and now includes the recovery reports. Reported recovery is not proof of the detector's cause or a hardware ban.
- Conclusion and boundary: Unofficial evidence does not establish automatic hardware bans for ordinary PoE2 switching macros or any guaranteed hardware protection. No safe delay, Windows/account isolation or SSF immunity was established. Research/history only; existing lab, ZIP and profiles preserved, support email unsent, no live account/input test.

## 2026-10-12 — Deep public review of hardware bans and macro enforcement

- Request: Investigate broadly across the internet without relying solely on an answer from GGG. The earlier instruction to keep the support email as an unsent local draft remains in force.
- Method and record: 32 targeted search queries covered GGG policy/forums, Reddit, Steam, original macro-project documentation, Microsoft input documentation, journalist correspondence and commercial claims. [Source-by-source review](evidence/SWITCH-RISK-DEEP-REVIEW-2026-10-12.json) records 20 selected sources, coverage limits and uncertainty. Search results are not a representative population or proof of risk percentages.
- New direct evidence: The [GGG account-system FAQ](https://www.pathofexile.com/forum/view-thread/3586288) confirms linked sub-account consequences and a PoE1 ban carrying into PoE2 on that account. It directs players to create a new account; this does not promise hardware protection or cover all independent accounts using one PC.
- Community outcomes: Reports include invitations to create new accounts, PoE2 bans near level 40 followed by restoration, peripheral-software suspicions without confirmed causes, and long-term macro use without trouble. Some examples concern PoE1. A VPN trade-site incident initially labelled a hardware ban later recovered. Repeated bans and vague third-party-software labels do not isolate a hardware cause.
- Source quality: An older macro-project author acknowledges prohibited gem-switch functions while claiming timing variation prevents identification; that assertion was not validated. Commercial hardware/controller vendors claim detector knowledge without independent evidence. A journalist's 2021 correspondence documents a fabricated accessibility ban story and a context-specific founder statement about internal policy; neither grants general current PoE2 permission.
- Conclusion: Account/sub-account consequences and hardware/OS collection are documented. No reproducible reviewed case establishes permanent hardware enforcement for an ordinary PoE2 switching macro. Enforcement remains unconfirmed rather than disproven; no ban probability, safe delay, hardware-device immunity or Windows-version isolation was established.
- Outcome and boundary: Research and additive documentation only. Existing lab/ZIP and R2 profiles were preserved; no game launch, account creation, identity change, software download, live input/anti-cheat test or email. Native skill-to-weapon-set assignment remains the supported functional route; an inventory/gem sequence is still outside the current fixed single-action macro policy.

## 2026-10-12 — Develop and test offline weapon/skill switching prototype

- Request: Develop fast weapon and ability switching, investigate hardware/Windows identification, and prepare a fresh-account test. The user clarified that protecting the current PC from a possible hardware ban is the priority.
- Current evidence: The [GGG privacy policy](https://www.pathofexile.com/legal/terms-of-use-and-privacy-policy) discloses unique hardware/install identifiers and OS information. Collection is verified; hardware-ban enforcement is unknown. No current official assurance against machine restrictions was found. Older community claims about PoE1 do not establish PoE2 protection. A fresh account, VM or different Windows version is not verified hardware isolation.
- Supported route: [Mark_GGG's native skill assignment explanation](https://www.pathofexile.com/forum/view-thread/3610245) supports skills enabled for weapon set I/II selecting that set through the game. This requires already-equipped sets and available compatible skills. [Current macro policy](https://www.pathofexile.com/developer/docs) requires fixed, manually invoked single-action inputs and provides no solo/SSF exemption; an inventory equipment/gem/rebinding sequence exceeds that scope.
- Exact addition: Created `switch-lab/` with a self-contained offline HTML prototype, pure state model, compact UI, source-derived 13-slot R2 reference, editable demo assignments, JSON export/import and a fictional inventory/gem sequence. The model demonstrates preflight, item conservation and partial completion after cancellation. No live input/network adapter or anti-cheat modification exists in the package.
- Verification: 20 offline model/artifact checks passed; 14 separately observed browser checks passed. Browser checks included Q/E set changes, distinct Ctrl+Q, focused X, unavailable skills, edit cancellation, literal text rendering, inventory stop/completion, mode-change cancellation, JSON download/import and a 390px long-label layout. A clean ZIP extraction rebuilt using the bundled reference and passed all 20 checks; its HTML matched the source master byte-for-byte. These are not gameplay or enforcement-safety results.
- Delivery: `POE2-Weapon-and-Skill-Switch-Lab-v0.1.zip` contains 16 payloads with an internal SHA-256 manifest; all payload hashes and sizes passed readback. Archive size 166,161 bytes; SHA-256 `2D5CDB12A3C76488F43D4471248E43FE02E038272D8DDDCC42BB088DFEDB1DE9`. Verified copies of the ZIP and standalone HTML were placed in the local Downloads directory. The new ZIP is separate from the existing GROUPED R2 Azeron bundle; its setup JSON is not an Azeron import.
- Live-test boundary: `NEW-ACCOUNT-TEST-PLAN.json` is prepared, not run. No account was created, entitlement purchased, game launched, or game/Azeron profile changed. A prohibited-sequence live test remains unrun because hardware protection cannot be established. `GGG-SUPPORT-QUESTION.txt` is an unsent policy question; sending requires explicit user authorization.
- User decision: Keep the GGG question as an unsent local draft. No email was sent; sending is not authorized.
- Recovery and next boundary: Close the offline page and remove only the additive lab/new bundle to discard it; existing keymaps and profiles remain the recovery baseline. A supported overlay-host integration remains pending. Native configuration requires actual character/equipment/skills readback and recovery of current game bindings before mutation. Policy clarification cannot replace observed game-function checks or guarantee future enforcement outcomes.

## 2026-10-12 — Review macro rules, detection evidence and trial-account proposal

- Request: Research permitted/prohibited macros, player reports, hardware versus software inputs, slower sequences and a possible separate test account. The user expressed willingness to accept risk; no exact implementation or live test scenario was selected.
- Current primary policy: [GGG developer Third-Party Policy](https://www.pathofexile.com/developer/docs) specifies manual invocation, a fixed non-cycling function and one game-interacting action per invocation. This strengthens the older staff evidence below. Delays do not change a full equipment/gem sequence into a permitted single action.
- Detection evidence: The [current privacy policy](https://www.pathofexile.com/legal/terms-of-use-and-privacy-policy) lists anti-cheat/security collection including processes, hardware/install identifiers, memory/driver information and gameplay data. [Microsoft documents injected keyboard-event flags](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-kbdllhookstruct); their existence does not establish PoE2's use of them. No public detection threshold, defensible ban probability or verified safe delay was identified.
- Community evidence: An [October 2026 PoE2 accessibility discussion](https://www.reddit.com/r/PathOfExile2/comments/1wuwdts/i_have_painful_issues_with_my_hands_is_there_a/) includes claims of long-term macro use without bans. An [older hardware-macro report](https://www.pathofexile.com/forum/view-thread/3036305) claims a ban later reversed. A [PoE2 third-party-software ban report](https://www.pathofexile.com/forum/view-thread/3734925) does not establish the triggering program. These are anecdotes, not confirmed causes, exemptions or risk statistics.
- Separate-account boundary: The [current Steam store](https://store.steampowered.com/app/2694490/Path_of_Exile_2/) still lists paid Early Access. A new account does not itself supply game access, and shared identity/telemetry means it is not a guaranteed isolated experiment. A successful session would establish mechanical behavior only, not future enforcement safety.
- Outcome: Research/documentation only; no account creation, purchase, macro implementation, anti-cheat change, game launch or live input test. A display-only loadout checklist, fixed manual inputs and native weapon-set switching remain the recommended approach. Offline mock testing can assess UI timing without proving online policy acceptance.

## 2026-10-12 — Research fast equipment and skill switching

- Request: Assess an addon/macro for predefined equipment sets and rapid ability changes; this was a feasibility question, not an implementation request.
- Verified source: [Mark_GGG's PoE2 explanation](https://www.pathofexile.com/forum/view-thread/3610245) confirms per-skill weapon-set checkboxes and native automatic weapon swapping when a skill is enabled only in the other set. This covers weapons already assigned to sets I/II and available skills, not arbitrary inventory equipment or unequipped gems.
- Automation boundary: [Rob_GGG's published macro guidance](https://www.pathofexile.com/forum/view-thread/1694310) disallows macros performing multiple server-side actions. This is historical PoE staff guidance, not a new PoE2-specific approval. The [current Terms of Use](https://www.pathofexile.com/legal/terms-of-use-and-privacy-policy) also restrict automated software without prior written approval. An equip/gem/rebind sequence would therefore not be a supported recommendation.
- Recommendation: Use native weapon sets with exclusive skill assignments and separately bound Azeron skill buttons. GROUPED R2 already maps COMBAT #37 to X for manual weapon swap. Azeron layers change input outputs; they do not equip inventory gear or grant skills.
- Limits: No supported full armor/gem loadout-switch interface was identified in this review. No game/Azeron configuration, input automation or gameplay test was performed. Native timing and weapon/skill requirements still apply.
- Next boundary: A separately requested setup could configure native skill-to-weapon-set assignments after inspecting the character's actual equipped weapons and available skills.

## 2026-10-12 — Regroup skills for every build (R2)

- Request: The user rejected the scattered layout and explicitly requested skills together for all builds; class-specific customization is unnecessary.
- Source: Current game `WASD_ACTION_KEYS`, current user-edited PoE2 native pair, saved Cyborg II geometry and installed Azeron 2.0.2 renderer enums. Connected HID interfaces matched the saved device signature; raw identifiers were omitted. The game and Azeron Software were running.
- Newer user state: The first pair appeared after the user ended Azeron Software through Task Manager. #1 now had an immediate momentary MENU selector; #6 had V with no layer target. Those current source files were preserved.
- Exact change: Added `PATH OF EXILE 2 - GROUPED R2 COMBAT` and `PATH OF EXILE 2 - GROUPED R2 MENU` as two new native files. All 13 skill outputs occupy three adjacent towers; Q/E/R/F and Ctrl variants share rows; T's extra is #38 because Dodge stays #14. Flasks #4/#3 and temporary skills #2/#36 are adjacent. MENU groups character panels and map/navigation panels. Thumb shortcuts remain available.
- Corrected encodings: Native `MouseButton=15` uses 1=LMB, 2=MMB, 3=RMB. Game virtual keys 1/4/2 correspond to those skill inputs. R2 #6 uses `SwitchProfile=24` under Long Press, a 150 ms delay and reciprocal hold-return targets; #1 retains immediate hold layering. Chords emit simultaneous key combinations, with no sequence/repeat macros.
- Recovery: `Azeron-before-POE2-grouped-R2-20261012-032427.zip` preserves all 31 earlier native profiles and available global JSONs; the original pre-PoE2 backup remains separate. IndexedDB and onboard hardware are outside this snapshot. Remove only IDs `0ca7e8e3-131e-5f6b-8a8d-9a0dd78c0b17` and `4943b051-848c-5389-aa4d-e835b6dfd1e2` with Azeron fully closed to discard R2.
- Artifacts: `grouped-r2/KEYBINDS-GROUPED-R2.json`, two native profiles, keys/actions/combined SVGs, two icon PNGs, concise guide, descriptive overlay handoff and installation receipt. Images derive from one record and were visually reviewed.
- Limits: Active selection, R2 UI recognition after reload, layer behavior, movement, Ctrl skill-bar interactions and gameplay prompts remain pending. Overlay-host activation remains a separate integration. Shift attack-in-place stays on the external keyboard. Existing native files and the game configuration were preserved.
- Next boundary: After the session, fully exit/reopen Azeron Software and select `PATH OF EXILE 2 - GROUPED R2 COMBAT`.

## 2026-10-12 — Add native PoE 2 Azeron profile pair (earlier checkpoint)

The user later confirmed this pair appeared after a full Task Manager exit. The
following missing-profile diagnosis and pending UI status retain their earlier scope.

- Goal: Add the prepared COMBAT/MENU map to the local Azeron Software profile library while preserving the shared profile family; leave primary selection to the user.
- Baseline: 29 local profile files, including the current SHARED R8 SPARSE6 profiles. Azeron Software 2.0.2 was running. A just-in-time ZIP of the 29 profiles and both GlobalStore files was made before adding anything; it is stored in the private Azeron Drive folder as `Azeron profiles before POE2 COMBAT MENU 2026-10-12.zip`. Drive readback showed Reader permission for the requested account.
- Exact change: Added two native software profiles, initially named `POE2 COMBAT` and `POE2 MENU`, under the local Azeron profile library. Their labels are now `PATH OF EXILE 2 - COMBAT` and `PATH OF EXILE 2 - MENU`; IDs, outputs, layers and analog settings are unchanged. Button #6 taps V, holds 150 ms to enter MENU, and returns to COMBAT on release. Existing R8 profiles were not overwritten.
- Verification: Both JSON files parse and contain 43 inputs each. Their #6 long-press references point to each other, both use a 150 ms delay and hold-to-return setting, and the analog stick block matches the R8 source. A pre-rename pair ZIP is preserved locally.
- Diagnosis: The Azeron process began before the new files were written and is still running. Its log last says `Fully loaded SW profiles: 29` at 2026-10-11T20:14:47Z; the pair was created later at 2026-10-11T22:18Z. `GlobalStore.json` has `CLOSE_MINIMIZES=True`, so closing the window does not fully stop that process. The profile list has not loaded the two new files yet. The shipped Azeron 2.0.2 UI also exposes **Import profiles from a folder**, so a two-file import directory is included as a fallback.
- Limits: The pair has not been confirmed in the app UI, selected, synchronized to onboard memory, or verified in gameplay. Existing keymap uncertainties remain, including movement mode, Ctrl overlap, temporary skill keys 6/7, unbound flask slots 3/4, and Escape behavior.
- Package update: Rebuilt the existing bundle with full-title JSON names, a two-profile import folder, updated status/setup notes, and a regenerated SHA-256 manifest. ZIP CRC and all 44 payload hashes passed. Replaced the existing Drive bundle in place; metadata readback confirmed a 722,922-byte archive and Reader permission for the designated private mailbox.
- Rollback: Restore `Azeron profiles before POE2 COMBAT MENU 2026-10-12.zip` for the original 29-profile baseline or `POE2-profiles-before-full-title-rename-2026-10-12.zip` for the old names and profile JSON bytes. Or remove only IDs `1e29fa38-5c56-4e8f-ae0a-23f32d1279ec` and `57d3d4da-d6ea-4ebe-9b81-b1dab68ee96b`.
- Next boundary: Fully exit Azeron from its tray menu and reopen so it reloads the profile folder. The user selects `PATH OF EXILE 2 - COMBAT` as primary. If absent, use **Import profiles from a folder** with the included JSON directory. Verify #6 tap, hold, release return, a held-key transition, and game prompts separately.

## 2026-10-11 — Create Azeron Cyborg II PoE 2 keymap

- Goal: Document the saved SHARED R5 Azeron layout against the current Path of Exile 2 WASD key configuration.
- Baseline: Connected Azeron Cyborg II interface matched the private 2026-10-11 R5 report; Azeron Software 2.0.2 had BASIC selected in that report. Current game config SHA-256: `80D43307923862D0C2816349362888315FDB0CDFCD68EB6B7E0D2097212269BE`. PoE 2 was not running during readback.
- Exact change: No game, Steam Input, or Azeron profile settings changed. Added `KEYBINDS.json`, `KEYMAP.md`, a standard-library SVG generator, 12 layer diagrams, and a skill-slot overview under `azeron-keymap/`.
- Observed result: The four saved profiles provide the mapped keys and hold-layer controls. The report recorded off-game checks for layer buttons #1, #2, and #36; game actions, gameplay prompts, movement, and the OptiScaler Home shortcut were not tested.
- Important uncertainty: The config selects `user_input_mode=wasd` but also has `use_wasd_to_move=false`; runtime movement mode needs confirmation. Ctrl is used for both `toggle_skill_bar` and modifier chords for skill slots 9–13, as well as Ctrl+U and Ctrl+Z.
- Rollback: No runtime rollback needed. Remove the added keymap files and `azeron-keymap/` directory to discard this documentation draft.
- Safe next boundary: During a normal user-started session, check the displayed input mode, movement, skill/flask prompts, Ctrl interactions, and held-layer return before considering any profile changes.

## 2026-10-11 — Prepare layer-specific PoE 2 overlay previews

- Goal: Prepare icon-led COMBAT and MENU overlay views for the separate POE2 profile-pair proposal, with quicker layer navigation and persistent thumb menu actions.
- Baseline: The saved SHARED R5 family and current game configuration remain the source references. The separate pair is still design-only and is not installed.
- Exact change: Added a standard-library SVG renderer, two layer-specific SVG/PNG views, an overlay manifest, and a compact navigation handoff. No game, Steam Input, or Azeron settings were changed.
- Observed result: The COMBAT and MENU PNG views rendered successfully and were visually inspected. Both show the same saved Cyborg II geometry, explicit proposal/config/unverified status labels, #6 tap/hold/release navigation, and thumb menu controls in both views. The two PNGs and source bundle were uploaded to the existing private Azeron Drive folder; metadata readback confirmed Reader access for the requested Gmail account on all three items.
- Limits: The proposal's new profile bindings, device-side layer switch, gameplay prompts, movement mode, and automatic host selection remain unverified. The script-merging task is still active; no assets were integrated into that application.
- Rollback: Remove `generate_azeron_layer_overlays.py`, `OVERLAY-NAVIGATION.md`, `overlay-manifest.json`, and the four `poe2-proposal-*-icons` SVG/PNG files. Remove the corresponding added section from `KEYMAP.md` if desired. Existing SHARED R5 files remain intact.
- Safe next boundary: After the user installs the unified overlay host and the script-merging task is complete, connect the manifest and two layer views through the host's supported interface. Verify automatic selection and manual override separately; do not install the proposed Azeron profile without a separate authorized setup step.
## 2026-10-12 — Bundle Azeron keymap and overlay files

- Goal: Package the PoE 2 Azeron mapping, diagrams, overlay previews, and generators together under clear folder and file names.
- Exact change: Created POE2-Azeron-Keymap-and-Overlays-2026-10-12.zip with 39 files, a start guide, a status note, and an internal SHA-256 manifest. Archive CRC and member hashes were verified.
- Delivery: Uploaded the ZIP to the existing private Azeron Drive folder. Drive metadata readback confirmed Reader access for the requested recipient.
- Limits: The COMBAT/MENU pair remains a proposal, not an installed Azeron profile. Gameplay prompts and automatic layer switching remain unverified; integration still waits for the separate overlay/script application.
- Configuration: No game, Steam Input, or Azeron settings changed.

## 2026-10-07 — OptiScaler full menu moved to Home

- User explicitly replaced the old menu mapping with ReShade = Delete and OptiScaler = Home across existing and future installations. The current PoE2 root contains OptiScaler but no current `ReShade64.dll` or `ReShade.ini`, so only OptiScaler was changed.
- PoE2 was closed and the INI was exclusively writable. Private snapshot `20261007-110500-before-reshade-delete-optiscaler-home` preserved the prior INI, Steam library metadata and app manifest; older Insert/Delete snapshots remain separate.
- Changed exactly `[Menu] ShortcutKey=0x2E` to `ShortcutKey=0x24`. Hash `D010DAF750B54BFF9A3054612E7734D535D68D0A023FDA4F66C6819A2F3790B2` → `A5E1247730E6CF64C3C8D2ECF05FC594478163AFACBD90D5FCD1F37A7B724A8F`.
- Static readback and byte-preserving comparison passed. No game launch occurred; Home input and persistence remain pending. Rollback restores this game's INI from the named snapshot with PoE2 closed.

## 2026-09-22 — Reapply Delete as the live OptiScaler menu key

- Goal: Change the current full OptiScaler menu shortcut from Insert back to Delete at the user's explicit request.
- Baseline: Path of Exile 2 was closed. The live `OptiScaler.ini` contained `ShortcutKey=0x2D` and had SHA-256 `C5F6E71C707A22E5C66DB6284363E970D387A80088B152AB1F973F9C71C4A5BA`.
- Exact change: Changed only the `[Menu]` setting from `ShortcutKey=0x2D` (Insert) to `ShortcutKey=0x2E` (Delete).
- Observed result: Static verification passed at line 830. The resulting file SHA-256 is `D010DAF750B54BFF9A3054612E7734D535D68D0A023FDA4F66C6819A2F3790B2`; line comparison against the snapshot found only the removed Insert line and added Delete line.
- Positive evidence: A just-in-time private snapshot named `optiscaler-menu-before-delete-20260922-031812` exists, and its copied `OptiScaler.ini` hash matches the baseline.
- Failure evidence: None during the edit. Runtime input handling remains untested because the game was not launched.
- Root cause: Not applicable to this requested control change. The cause of the earlier reversion remains unknown.
- Rollback performed: None. With the game closed, restore `OptiScaler.ini` from the named snapshot to return the menu shortcut to Insert.
- General lesson promoted to: None; the Delete control default is already documented.
- Safe next options: Confirm Delete opens and closes the OptiScaler menu in the next normal session. If it reverts, preserve the regenerated file and compare timestamps/logs before another edit.

## 2026-09-22 — Recheck live OptiScaler menu shortcut

- Goal: Check the current OptiScaler full-menu key without changing the game.
- Baseline: Steam build `25379396`; game directory `OptiScaler.ini` exists and the game process was not running. Steam remained open.
- Exact change: None. This was a read-only inspection.
- Observed result: The live `[Menu]` setting is `ShortcutKey=0x2D`, which is Insert. Current file SHA-256 is `C5F6E71C707A22E5C66DB6284363E970D387A80088B152AB1F973F9C71C4A5BA`; its last-write time is 2026-09-22 03:14:42 local time.
- Positive evidence: The value was read directly from line 830 of the installed `OptiScaler.ini`.
- Failure evidence: The previously recorded Delete value (`0x2E`) is no longer present in the live file.
- Root cause: Unknown. The file appears to have been regenerated or replaced after the earlier edit, but this check did not establish which process did it.
- Rollback performed: None; no setting was changed.
- General lesson promoted to: None.
- Safe next options: Use Insert as currently configured, or explicitly request a change back to Delete after identifying and accounting for the rewrite path.

## 2026-09-22 — Change OptiScaler menu shortcut to Delete

- Goal: Bind the full OptiScaler menu to Delete.
- Baseline: The game was closed. `OptiScaler.ini` contained `ShortcutKey=0x2D` (Insert), SHA-256 `3AD84A226C7CF4594E2BDFA639900F5D0101D57E2FFC58EB32C721172C2F1735`.
- Exact change: In `[Menu]`, changed only `ShortcutKey=0x2D` to `ShortcutKey=0x2E` (Windows `VK_DELETE`).
- Observed result: Static verification passed. The saved file contains `ShortcutKey=0x2E`, SHA-256 `5C536CF86C593879AD93D7EF9825419861C431DF4F57B278F4E5E8D8FD16C67D`; comparison with the snapshot showed no other changed line.
- Positive evidence: The pre-change file was preserved in private snapshot `optiscaler-menu-before-delete-20260922-025754`, and its hash matches the recorded baseline.
- Failure evidence: None during the file edit. Runtime input handling was not tested because the game was not launched.
- Root cause: Not applicable; this was a requested control change.
- Rollback performed: None. To roll back with the game closed, restore the snapshot's `OptiScaler.ini`, or set `[Menu]` `ShortcutKey` back to `0x2D`.
- General lesson promoted to: None; the cross-game Delete default already exists in `preferences/GENERAL.md`.
- Safe next options: Confirm Delete opens/closes the menu in the next session. If the key conflicts with a game action, restore Insert from the snapshot before choosing a different shortcut.

## 2026-09-22 — Diagnose missing ReShade/RenoDX menu on D3D12

- Goal: Determine why Home did not open ReShade and why RenoDX did not appear after the user attempted to add it.
- Baseline: Steam build `25379396`; `PathOfExileSteam.exe` using D3D12; OptiScaler `10.0.0-dev (a8eac0c4)` owns `dxgi.dll`; ReShade `6.8.0.2155` is named `ReShade64.dll`; `OptiScaler.ini` has `LoadReshade=true`; `ReShade.ini` has `KeyOverlay=36,0,0,0` (Home).
- Exact change: None. Diagnosis was read-only.
- Observed result: ReShade initialized inside the correct executable but logged `Skipping swap chain because it was created without a proxy Direct3D device` for the game's 3840x2160 D3D12 swapchain. No `.addon64` file, RenoDX-named binary, or add-on load event exists under the game directory.
- Positive evidence: OptiScaler successfully chain-loaded `ReShade64.dll`, so the ReShade binary path and Home key value are not the immediate failure.
- Failure evidence: ReShade never created a runtime for the active swapchain, so it had nowhere to draw its overlay or effects. RenoDX could not load because its game add-on binary is absent.
- Root cause: **Proven locally** for the missing menu: ReShade skipped the active D3D12 swapchain. **Proven locally** for missing RenoDX: no RenoDX add-on is installed. **Upstream-supported** compatibility limitation: the current Path of Exile 2 RenoDX discussion labels its mod DX11-only and reports the D3D12 ReShade path blocked.
- Rollback performed: None.
- General lesson promoted to: None; this is currently game/API-specific.
- Safe next options: Keep the working D3D12 OptiScaler path without RenoDX; switch to a separate DX11 ReShade + actual Path of Exile 2 RenoDX profile; or preserve the baseline and treat any D3D12 proxy-order experiment as low-confidence and separately reversible.

## 2026-09-22 — Review DLSS Neural Rendering (“DLSS 5”) paths

- Goal: Determine whether DLSS Neural Rendering can run through RenoDX or OptiScaler in the current Path of Exile 2 setup.
- Baseline: RTX 5070 Ti, driver `616.56`; D3D12; standard OptiScaler v0.9.4 (`dxgi.dll`); game provides working DLSS inputs. Installed NVIDIA SR/RR/FG runtimes report `310.9.1`. No `nvngx_dlssnr.dll` or RenoDX DLSS add-on exists in the game directory.
- Exact change: None. Review and local inspection were read-only.
- Observed result: The latest local log proves creation of a normal DLSS Super Resolution feature at 2258x1270 to 3840x2160 and reports `DLSS v310.9.1 loaded`. It does not contain creation/evaluation of the separate Neural Rendering feature, and the required NR runtime is absent. NR-named configuration/status strings alone are not activation evidence.
- Positive evidence: Upstream OptiScaler documentation lists Path of Exile 2's DLSS inputs as supported. The experimental OptiScaler-DLSSNR fork documents direct NR on games that already use DLSS, with driver 616.56 as its stated minimum for the current path.
- Failure evidence: The installed standard OptiScaler package has no NR runtime and no NR feature creation/evaluation. The current ReShade chain skips the D3D12 swapchain, so a RenoDX DLSS add-on would not currently have a functioning host. The Path of Exile 2 RenoDX visual mod remains documented as DX11-only.
- Root cause: **Proven locally** that DLSS SR is active but DLSS NR is not installed/verified. **Upstream-supported** that an experimental OptiScaler-DLSSNR implementation can drive the separate NR runtime using a game's DLSS inputs. **Unknown locally** whether that fork is stable with this exact game build, HDR mode and online runtime.
- Rollback performed: None.
- General lesson promoted to: None; the distinction between SR, RR and NR is already documented in `docs/FEATURE-DECISION.md` and `docs/COMPONENTS.md`.
- Safe next options: Preserve the current D3D12 profile and test an OptiScaler-DLSSNR profile separately; keep a separate DX11 ReShade/RenoDX visual profile; do not combine two NR consumers or treat `nvngx_dlssd.dll` as the NR runtime.

## 2026-09-22 — Review public OptiScaler and ReShade compatibility reports

- Goal: Check whether public reports distinguish OptiScaler compatibility from ReShade's D3D12 problem in Path of Exile 2.
- Baseline: Current local D3D12 chain has OptiScaler v0.9.4 as the root `dxgi.dll` proxy and chain-loads ReShade 6.8.0 as `ReShade64.dll`.
- Exact change: None. Review and local inspection were read-only.
- Observed result: OptiScaler's official Path of Exile 2 wiki lists v0.9.2 tested with `dxgi.dll` and DLSS inputs, with HDR and some FG/dynamic-resolution caveats. ReShade and RenoDX discussions separately report that ReShade does not normally hook PoE2's D3D12 path; this matches the local `Skipping swap chain because it was created without a proxy Direct3D device` result.
- Positive evidence: Local OptiScaler logs show it owns the proxy/device path and creates a DLSS feature. ReShade initializes but does not own or accept the active swapchain.
- Failure evidence: ReShade's overlay/effect runtime is absent on the active D3D12 swapchain. A community workaround proposes replacing the game's Microsoft `D3D12Core.dll` and `d3d12SDKLayers.dll` with renamed ReShade binaries, but this is not upstream-validated and would overwrite the local DirectX 12 runtime files.
- Root cause: **Proven locally** that the two tools reach different hook stages. OptiScaler attaches early as the root proxy; ReShade is chain-loaded later and rejects the already-created device/swapchain. **Community-reported** alternatives do not establish safe compatibility with the current OptiScaler stack.
- Rollback performed: None.
- General lesson promoted to: None; the one-owner proxy/swapchain rule already covers this case.
- Safe next options: Preserve OptiScaler's working D3D12 baseline; use a separate DX11 ReShade/RenoDX profile if selected; do not overwrite the game's DirectX runtime files or apply an unverified proxy reorder without a full snapshot.

## 2026-09-22 — Compare RenoDX DLSS input provenance and PoE2 DX11/DX12 paths

- Goal: Determine whether RenoDX DLSS Neural Rendering uses original game DLSS inputs, whether it can coexist with the Path of Exile 2 RenoDX HDR add-on on DX11, and what DX12 gains or loses relative to DX11.
- Baseline: No files or settings changed. The current locally verified profile remains D3D12 with working OptiScaler DLSS SR inputs; ReShade skips the active swapchain, and neither a RenoDX add-on nor the DLSS NR runtime is installed.
- Exact change: None. Research and comparison were read-only.
- Observed result: NVIDIA documents that native DLSS requires render-resolution color, depth, motion vectors, output color, and per-frame camera/jitter data. Current RenoDX diagnostics describe two distinct NR paths: a required-source path that waits for matching DLSS SR/AA/RR temporal inputs, and a Present fallback that can evaluate with dummy temporal inputs. On DX11, the required-source path still builds a D3D11-to-D3D12 extraction bridge and converts/copies motion and depth resources, so successful input reuse should be classified as captured/converted game inputs rather than untouched native integration.
- Positive evidence: The PoE2 RenoDX HDR project is explicitly DX11-only and documents tonemapping, peak-brightness, gamma, noise, sharpening, bloom, vignette and LUT controls. HDR correction and NR are conceptually separate add-on roles and may share one full-add-on ReShade host when no second neural consumer owns the path.
- Failure evidence: No upstream or local test was found proving the exact PoE2 DX11 combination of the game-specific HDR add-on plus the current RenoDX DLSS NR add-on. A current RenoDX issue shows the required-source match remaining stuck on a DX11 bridge case even though another layer reported valid DLAA inputs; disabling the requirement evaluated the Present fallback with dummy temporal inputs. The PoE2 HDR author also reports worse DX11 CPU performance and large frame-time swings during effect-heavy scenes.
- Root cause: **Upstream-supported** that DLSS requires engine temporal resources and that the PoE2 HDR add-on targets DX11. **Community-reported/upstream diagnostic** that RenoDX's DX11 NR route copies/converts resources and can fall back to dummy temporal inputs. **Unknown locally** whether PoE2's DX11 DLSS resources are recognized correctly or whether HDR and NR coexist without color-space, ordering, stability or performance problems.
- Rollback performed: None required.
- General lesson promoted to: None; input-provenance labels and one-neural-consumer ownership are already defined in the general documentation.
- Safe next options: Keep D3D12 as the performance/verified-input profile. If selected later, create a separate snapshotted DX11 experiment: validate ReShade plus PoE2 HDR first, then add exactly one RenoDX NR consumer, require matching DLSS resources, reject Present/dummy fallback as proof, and compare identical effect-heavy scenes before retaining it.

## 2026-09-22 — Review DX11 OptiScaler plus RenoDX HDR coexistence

- Goal: Determine whether standard OptiScaler can run in Path of Exile 2's DX11 renderer together with the DX11-only PoE2 RenoDX HDR add-on.
- Baseline: No game files or settings changed. The currently installed and locally verified OptiScaler profile remains D3D12; the existing `LoadReshade=true` chain initializes ReShade there but ReShade skips the active D3D12 swapchain. The PoE2 RenoDX add-on is not installed.
- Exact change: None. This was a read-only upstream compatibility review.
- Observed result: OptiScaler officially supports DirectX 11 and lists native DX11 DLSS as an output. Its official ReShade coexistence method is for OptiScaler to own the root proxy, rename the full-add-on ReShade DLL to `ReShade64.dll`, and set `LoadReshade=true`. The PoE2 RenoDX author reports that ReShade can hook the game's DX11 renderer. This makes `PoE2 DX11 DLSS inputs -> OptiScaler SR -> ReShade-hosted PoE2 RenoDX HDR -> presentation` an architecturally valid test candidate.
- Positive evidence: OptiScaler's game page lists PoE2 as compatible with DLSS inputs, and its general documentation explicitly supports DX11 plus the ReShade chain-load method. The PoE2 RenoDX HDR page explicitly targets DX11.
- Failure evidence: The PoE2 OptiScaler page does not identify which renderer was used for its test, and no exact upstream or local report was found proving standard OptiScaler plus the PoE2-specific RenoDX HDR add-on together on DX11. OptiFG is officially DX12-only. The experimental OptiScaler-DLSSNR fork has a separate DX11 limitation: NR must run through a DX12 bridge; its documented release requires selecting a bridged upscaler and cannot use native DX11 DLSS as the NR-driving output on that path.
- Root cause: **Upstream-supported** that standard OptiScaler and its ReShade loader support DX11 generally. **Inference, Medium confidence** that the two components can coexist in PoE2 DX11 because their intended owners differ (OptiScaler for SR, RenoDX for HDR), but exact combined behavior remains untested. **Unknown locally** whether PoE2's current DX11 build exposes and evaluates the expected DLSS contract through OptiScaler without color-space, timing or stability conflicts.
- Rollback performed: None required.
- General lesson promoted to: None; proxy ownership and separate visual-stage validation are already documented.
- Safe next options: Keep D3D12 unchanged as the known working profile, or create a separately snapshotted DX11 test profile with OptiScaler as the sole `dxgi.dll` owner, full-add-on ReShade chain-loaded as `ReShade64.dll`, and only the PoE2 RenoDX HDR add-on. Validate OptiScaler SR first, RenoDX HDR second, then the combined stack. Do not add a RenoDX DLSS neural consumer or assume OptiFG works on DX11.

## 2026-09-22 — Verify the persistent PoE2 DX11 selection method

- Goal: Identify the reliable way to start the Steam edition in DX11 and make DX11 the per-game default.
- Baseline: Read-only inspection found Steam app `2694490`, build `25379396`. The live `poe2_production_Config.ini` currently contains `renderer_type=DirectX12`; no setting was changed.
- Exact change: None. This was guidance and local inspection only.
- Observed result: PoE2 exposes DirectX 11 under Options > Graphics > Display Settings > Renderer and saves the selection in `Documents\My Games\Path of Exile 2\poe2_production_Config.ini`. The local file is redirected through OneDrive Documents. Current GGG forum guidance also uses `renderer_type=DirectX11` as the recovery method when the game cannot be opened.
- Positive evidence: The current local configuration contains the exact renderer key. Multiple PoE2 technical-support reports use the same value and confirm that it persists when launching normally through Steam.
- Failure evidence: No current authoritative PoE2 source was found documenting `-dx11`, `--renderer_type=DirectX11`, or another renderer command-line argument. Steam's Launch Options field cannot force a renderer unless the game implements the supplied argument.
- Root cause: **Local-tested** location and current DirectX 12 value; **community-reported on the official GGG forum** for the DirectX 11 recovery value. A Steam launch flag remains **unknown/unverified**.
- Rollback performed: None required. To return after a future switch, select DirectX 12 in-game or restore `renderer_type=DirectX12` with the game closed.
- General lesson promoted to: None.
- Safe next options: Use the in-game Renderer selector and restart, or—with the game closed—snapshot and change only `renderer_type=DirectX11`. Launch normally from Steam; the saved game configuration is already specific to PoE2. Do not add an unverified generic Steam launch argument.

## 2026-10-19 — Retained reference overlay labels, no native changes

Reconciled the six SPARSE6 overlay maps with the archived 2026-10-11 WASD keybinding record. Added the explicit reference status of unbound flask slots 3–5 where their keys occur. A current personal game config was not found at the checked destination locations or in the inspected recovery inventories, so these labels remain archived references; the saved input-mode conflict remains unresolved. No current OptiScaler/ReShade binding was invented from reference-machine history. Unknown actions stay unknown.

The existing output matrices, game associations and overlay preferences are unchanged. Private source/history snapshots preserve the prior display maps; no Azeron/game files changed or game was launched. This is display-data reconciliation, not acceptance of the R2 profiles, input mode, slotted abilities or gameplay. See [portable map editing](../../docs/KEYMAP-DOCUMENTS.md).
