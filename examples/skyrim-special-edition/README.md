# Skyrim helper compatibility path

The current [Skyrim-F12-Test.ahk](Skyrim-F12-Test.ahk) is a standalone compatibility launcher for [GameInputModule v0.5-preview.1](../game-input/README.md). It supports the same two exact foreground targets (Skyrim/Cyberpunk), visible status and optional one-shot extensions. Do not include the launcher in another AHK tool; include only GameInputModule.ahk.

[Workflow, tested results, failure lessons and remaining acceptance](../../docs/AGENT-GAME-INPUT.md) · [larger-AHK-chat handoff](../game-input/OTHER-CHAT-HANDOFF.txt).

The exact [v0.3.1 baseline](../game-input/baseline/ControlHelper-v031.ahk) has the historical live menu/single-key evidence. The newer refactor passes native syntax and 36 no-input tests but has not been run in the games. Arbitrary text, Enter/Escape, holds and integrated-host acceptance are pending. No MFG/FrameWarp/gameplay/performance test was resumed. Preserve one helper-family instance and exit/Stop after authorized tests; existing saved input profiles remain untouched.

The companion reWASD notes are historical; no profile is activated by this launcher.
