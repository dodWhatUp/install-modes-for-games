#Requires AutoHotkey v2.0
#SingleInstance Ignore
#MaxThreadsPerHotkey 1

; Control Helper v0.3.1 -- one file for release-triggered, allowlisted key tests.
; Exact foreground games only: SkyrimSE.exe and Cyberpunk2077.exe.
; F8: Skyrim F12 / Cyberpunk Delete. F13..F20 and F2: diagnostic keys.
; Ctrl+Alt+F8: show/hide status. Ctrl+Alt+P: pause/resume output.
; Ctrl+Alt+Esc: exit this script only. These controls also exist in the tray.
; No profiles/settings/saves/startup entries edited. No keyboard history retained.

BuildSettings()
{
    return {
        Version: "0.3.1", ShowIndicator: true, Beep: true,
        IndicatorX: 16, IndicatorY: 16, IndicatorWidth: 350,
        RefreshMs: 300, CooldownMs: 800
    }
}

BuildTargets()
{
    ; Extend this registry in this SAME file only after verifying the new target
    ; and its bindings. Never use a catch-all window or protected multiplayer.
    ; No Enter, quick-save/load, graphics toggle, held movement or text macro.
    skyrimActions := BuildDiagnosticKeys()
    skyrimActions.InsertAt(1, KeyAction("PureDark menu", "F8", "F12"))
    cyberpunkActions := BuildDiagnosticKeys()
    cyberpunkActions.InsertAt(1, KeyAction("ReShade menu", "F8", "Delete"))
    return [{
        Name: "Skyrim", Window: "ahk_exe SkyrimSE.exe", Enabled: true,
        Actions: skyrimActions
    }, {
        Name: "Cyberpunk", Window: "ahk_exe Cyberpunk2077.exe", Enabled: true,
        Actions: cyberpunkActions
    }]
}

KeyAction(name, trigger, output)
{
    return {Name: name, Trigger: "$" trigger, ReleaseKey: trigger,
        Key: output, PressMs: 150}
}

BuildDiagnosticKeys()
{
    ; Only trigger these after observing the correct menu/editable field.
    ; Synthetic F13+ triggers let the agent test through the normal UI tool.
    ; They pass through in other programs; no remote/background command path.
    return [
        KeyAction("ReShade menu", "F13", "Delete"),
        KeyAction("Menu down", "F14", "Down"),
        KeyAction("Menu up", "F15", "Up"),
        KeyAction("Console/CET menu", "F16", "vkC0"),
        KeyAction("Menu left", "F17", "Left"),
        KeyAction("Menu right", "F18", "Right"),
        KeyAction("Menu back", "F19", "Esc"),
        KeyAction("Search digit probe", "F20", "1"),
        ; The supported UI tool accepts F1..F20, not F21. Temporary F2 only.
        KeyAction("Remove probe digit", "F2", "Backspace")
    ]
}

; This branch runs pure policy/configuration tests BEFORE creating a GUI,
; registering hotkeys, starting timers, playing sound or sending input.
if A_Args.Length && A_Args[1] = "--self-test" {
    RunSelfTests()
    ExitApp
}

KeyHistory 0
helper := ControlHelper(BuildSettings(), BuildTargets())

class ControlHelper
{
    __New(settings, targets)
    {
        ValidateTargets(targets)
        this.Settings := settings
        this.Targets := targets
        this.Paused := false
        this.Visible := settings.ShowIndicator
        this.Epoch := 0
        this.LastSentTick := -settings.CooldownMs
        this.LastAction := "No input sent yet."
        this.DisplayCache := ""

        ; NOACTIVATE + mouse-transparent, layered status window: never focus it.
        this.Panel := Gui("+AlwaysOnTop -Caption +ToolWindow +LastFound +E0x08000020", "Control Helper status")
        this.Panel.BackColor := "18212B"
        this.Panel.MarginX := 12
        this.Panel.MarginY := 9
        this.Panel.SetFont("s10 cE5E7EB", "Segoe UI")
        width := "w" settings.IndicatorWidth
        this.Heading := this.Panel.AddText(width " r1", "AHK Control Helper")
        this.ReadyLine := this.Panel.AddText(width " r1", "")
        this.LastLine := this.Panel.AddText(width " r2", this.LastAction)
        this.Panel.SetFont("s8 cA8B3C2")
        this.Panel.AddText(width " r2", "Ctrl+Alt+F8: status | Ctrl+Alt+P: pause`nCtrl+Alt+Esc: exit | Tray: options")
        WinSetTransparent 238 ; Own hidden last-found GUI, not another window.

        this.BuildTray()
        this.RegisterActions()
        HotIf
        Hotkey "^!F8", ObjBindMethod(this, "ToggleIndicator")
        Hotkey "^!p", ObjBindMethod(this, "TogglePause")
        Hotkey "^!Esc", (*) => ExitApp()
        this.Timer := ObjBindMethod(this, "Refresh")
        this.Refresh()
        if this.Visible
            this.ShowIndicator()
        SetTimer this.Timer, settings.RefreshMs ; Status-only: never sends input.
    }

    BuildTray()
    {
        A_TrayMenu.Delete()
        A_TrayMenu.Add("Show status", ObjBindMethod(this, "ToggleIndicator"))
        A_TrayMenu.Add("Pause output", ObjBindMethod(this, "TogglePause"))
        A_TrayMenu.Add("Sound feedback", ObjBindMethod(this, "ToggleSound"))
        A_TrayMenu.Add()
        A_TrayMenu.Add("Exit helper", (*) => ExitApp())
        A_TrayMenu.Default := "Show status"
        if this.Visible
            A_TrayMenu.Check("Show status")
        if this.Settings.Beep
            A_TrayMenu.Check("Sound feedback")
    }

    RegisterActions()
    {
        for target in this.Targets {
            if !target.Enabled
                continue
            HotIfWinActive target.Window
            for action in target.Actions
                Hotkey action.Trigger, ObjBindMethod(this, "SendAction", target, action), "T1"
        }
        HotIf
    }

    ToggleIndicator(*)
    {
        this.Visible := !this.Visible
        A_TrayMenu.ToggleCheck("Show status")
        if this.Visible
            this.ShowIndicator()
        else
            this.Panel.Hide()
    }

    ShowIndicator()
    {
        this.Panel.Show("NA AutoSize x" this.Settings.IndicatorX " y" this.Settings.IndicatorY)
    }

    TogglePause(*)
    {
        this.Paused := !this.Paused
        this.Epoch += 1 ; A trigger waiting for release cannot survive a pause.
        for target in this.Targets {
            if !target.Enabled
                continue
            HotIfWinActive target.Window
            for action in target.Actions
                Hotkey action.Trigger, this.Paused ? "Off" : "On"
        }
        HotIf
        A_TrayMenu.ToggleCheck("Pause output")
        this.Refresh()
    }

    ToggleSound(*)
    {
        this.Settings.Beep := !this.Settings.Beep
        A_TrayMenu.ToggleCheck("Sound feedback")
    }

    SendAction(target, action, *)
    {
        originalWindow := WinActive(target.Window)
        originalEpoch := this.Epoch
        KeyWait action.ReleaseKey ; Keeps this thread alive; no held-key repeats.
        modifiers := GetKeyState("Ctrl", "P") || GetKeyState("Alt", "P")
            || GetKeyState("Shift", "P") || GetKeyState("LWin", "P") || GetKeyState("RWin", "P")
        sameWindow := originalWindow && WinActive("ahk_id " originalWindow)
        reason := DispatchBlockReason(this.Paused, target.Enabled, sameWindow,
            originalEpoch = this.Epoch, modifiers,
            A_TickCount - this.LastSentTick, this.Settings.CooldownMs)
        if reason != "" {
            this.LastAction := "Skipped: " reason
            this.Refresh()
            return
        }

        ; One bounded down/up keystroke. Keep the target foreground during it.
        SetKeyDelay 20, action.PressMs
        SendEvent "{" action.Key "}"
        this.LastSentTick := A_TickCount
        this.LastAction := "Sent " action.Key " at " FormatTime(, "HH:mm:ss") " -- not verified"
        this.Refresh()
        if this.Settings.Beep {
            try SoundBeep 1200, 80 ; Audio failure does not hide the visual result.
        }
    }

    Refresh(*)
    {
        targetName := ""
        hint := "Waiting: switch to Skyrim or Cyberpunk."
        for target in this.Targets {
            if target.Enabled && WinActive(target.Window) {
                targetName := target.Name
                action := target.Actions[1]
                hint := target.Name ": " action.ReleaseKey " -> " action.Key " (" action.PressMs " ms)"
                break
            }
        }
        state := HelperStatus(this.Paused, targetName)
        display := state "|" hint "|" this.LastAction
        if display = this.DisplayCache
            return
        this.DisplayCache := display
        this.Heading.Text := "AHK helper v" this.Settings.Version " | " state
        this.Heading.SetFont("c" (this.Paused ? "FBBF24" : targetName != "" ? "86EFAC" : "CBD5E1"))
        this.ReadyLine.Text := this.Paused ? "Paused: action keys pass through." : hint
        this.LastLine.Text := this.LastAction
        A_IconTip := "Control Helper v" this.Settings.Version " | " state
    }
}

HelperStatus(paused, targetName)
{
    return paused ? "PAUSED" : targetName != "" ? "READY: " targetName : "RUNNING / WAITING"
}

DispatchBlockReason(paused, enabled, sameWindow, sameEpoch, modifiers, elapsedMs, cooldownMs)
{
    if paused
        return "output paused"
    if !enabled
        return "target disabled"
    if !sameWindow
        return "target lost focus"
    if !sameEpoch
        return "pause/resume occurred during key hold"
    if modifiers
        return "release Ctrl/Alt/Shift/Win first"
    if elapsedMs < cooldownMs
        return "cooldown (800 ms by default)"
    return ""
}

ValidateTargets(targets)
{
    seen := Map()
    for target in targets {
        if !RegExMatch(target.Window, "i)^ahk_exe [a-z0-9_.-]+\.exe$")
            throw Error("Each target must name one exact executable.")
        if target.Actions.Length = 0
            throw Error("A target needs at least one verified action.")
        for action in target.Actions {
            if !RegExMatch(action.Key, "i)^(F([1-9]|1[0-9]|2[0-4])|[A-Z0-9]|Space|Tab|Esc|Enter|Delete|Backspace|vkC0|Up|Down|Left|Right|NumpadAdd|NumpadSub|NumpadMult)$")
                throw Error("Only a single named key is supported; no text or macros.")
            if action.PressMs < 25 || action.PressMs > 250
                throw Error("Press duration must be 25..250 ms.")
            if !RegExMatch(action.Trigger, "^\$[A-Za-z0-9]+$") || action.Trigger != "$" action.ReleaseKey
                throw Error("Use a hook hotkey for one unmodified release-gated key.")
            if action.ReleaseKey = action.Key
                throw Error("Trigger and output keys must differ.")
            id := StrLower(target.Window "|" action.Trigger)
            if seen.Has(id)
                throw Error("Duplicate target/trigger binding.")
            seen[id] := true
        }
    }
}

RunSelfTests()
{
    settings := BuildSettings()
    targets := BuildTargets()
    ValidateTargets(targets)
    AssertTest(settings.ShowIndicator, "indicator visible by default")
    AssertTest(targets.Length = 2 && targets[1].Window = "ahk_exe SkyrimSE.exe"
        && targets[2].Window = "ahk_exe Cyberpunk2077.exe", "exact two-game scope")
    AssertTest(targets[1].Actions.Length = 10 && targets[1].Actions[1].Key = "F12", "Skyrim menu route")
    AssertTest(targets[2].Actions.Length = 10 && targets[2].Actions[1].Key = "Delete", "Cyberpunk menu route")
    safeOutputs := true
    for target in targets {
        for action in target.Actions {
            if RegExMatch(action.Key, "i)^(Enter|F5|F6|F9|NumpadAdd|NumpadMult)$")
                safeOutputs := false
        }
    }
    AssertTest(safeOutputs, "no submit/save/load/graphics outputs")
    AssertTest(HelperStatus(false, "") = "RUNNING / WAITING", "waiting status")
    AssertTest(HelperStatus(false, "Skyrim") = "READY: Skyrim", "ready status")
    AssertTest(HelperStatus(true, "Skyrim") = "PAUSED", "paused status")
    AssertTest(DispatchBlockReason(false, true, true, true, false, 800, 800) = "", "eligible send")
    AssertTest(DispatchBlockReason(true, true, true, true, false, 800, 800) != "", "paused block")
    AssertTest(DispatchBlockReason(false, false, true, true, false, 800, 800) != "", "disabled block")
    AssertTest(DispatchBlockReason(false, true, false, true, false, 800, 800) != "", "focus-loss block")
    AssertTest(DispatchBlockReason(false, true, true, false, false, 800, 800) != "", "pause-epoch block")
    AssertTest(DispatchBlockReason(false, true, true, true, true, 800, 800) != "", "modifier block")
    AssertTest(DispatchBlockReason(false, true, true, true, false, 799, 800) != "", "cooldown block")
    invalid := BuildTargets()
    invalid[1].Window := "ahk_exe *.exe"
    AssertInvalidTargets(invalid, "catch-all target rejected")
    invalid := BuildTargets()
    invalid[1].Actions[1].Key := "{F12}{Enter}"
    AssertInvalidTargets(invalid, "multi-key payload rejected")
    invalid := BuildTargets()
    invalid[1].Actions[1].PressMs := 251
    AssertInvalidTargets(invalid, "excessive hold rejected")
    invalid := BuildTargets()
    invalid[1].Actions.Push(invalid[1].Actions[1])
    AssertInvalidTargets(invalid, "duplicate trigger rejected")
    invalid := BuildTargets()
    invalid[1].Actions[1].Key := "F8"
    AssertInvalidTargets(invalid, "feedback trigger rejected")
    ; Standard output only. No file, GUI, keyboard hook, sound, timer or input.
    FileAppend "PASS: 20 policy/configuration tests; no input or GUI.`n", "*"
}

AssertInvalidTargets(targets, name)
{
    try ValidateTargets(targets)
    catch
        return
    AssertTest(false, name)
}

AssertTest(condition, name)
{
    if !condition {
        FileAppend "FAIL: " name "`n", "**"
        ExitApp 1
    }
}
