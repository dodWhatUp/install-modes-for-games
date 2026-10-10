#Requires AutoHotkey v2.0

; Include-safe GameInputModule v0.5-preview.1. No auto-start or global hotkeys.
; Host owns tray, shortcuts, privacy policy and shutdown. See README.md.
; v0.3.1 baseline has live evidence; this refactor requires runtime revalidation.

GI_BuildSettings()
{
    return {
        Version: "0.5-preview.1", ShowIndicator: true, Beep: true,
        EnableExtended: false,
        IndicatorX: 16, IndicatorY: 16, IndicatorWidth: 350,
        RefreshMs: 300, CooldownMs: 800
    }
}

GI_BuildTargets(extended := false)
{
    ; Extend this explicit registry only after verifying the new target
    ; and its bindings. Never use a catch-all window or protected multiplayer.
    ; Prepared actions are explicit, one-shot and bound to a live game window.
    ; No quick-save/load, graphics toggle, console command or auto-launch.
    skyrimActions := GI_BuildDiagnosticKeys(extended)
    skyrimActions.InsertAt(1, GI_KeyAction("PureDark menu", "F8", "F12"))
    cyberpunkActions := GI_BuildDiagnosticKeys(extended)
    cyberpunkActions.InsertAt(1, GI_KeyAction("ReShade menu", "F8", "Delete"))
    return [{
        Name: "Skyrim", Window: "ahk_exe SkyrimSE.exe", Enabled: true,
        Actions: skyrimActions
    }, {
        Name: "Cyberpunk", Window: "ahk_exe Cyberpunk2077.exe", Enabled: true,
        Actions: cyberpunkActions
    }]
}

GI_KeyAction(name, trigger, output)
{
    return {Name: name, Trigger: "$" trigger, ReleaseKey: trigger,
        Key: output, PressMs: 150}
}

GI_BuildDiagnosticKeys(extended := false)
{
    ; Only trigger these after observing the correct menu/editable field.
    ; Synthetic F13+ triggers let the agent test through the normal UI tool.
    ; They pass through in other programs; no remote/background command path.
    actions := [
        GI_KeyAction("ReShade menu", "F13", "Delete"),
        GI_KeyAction("Menu down", "F14", "Down"),
        GI_KeyAction("Menu up", "F15", "Up"),
        GI_KeyAction("Console/CET menu", "F16", "vkC0"),
        GI_KeyAction("Menu left", "F17", "Left"),
        GI_KeyAction("Menu right", "F18", "Right"),
        GI_KeyAction("Menu back", "F19", "Esc"),
        GI_KeyAction("Search digit probe", "F20", "1"),
        ; The supported UI tool accepts F1..F20, not F21. Temporary F2 only.
        GI_KeyAction("Remove probe digit", "F2", "Backspace")
    ]
    if extended
        actions.Push({Name: "Prepared one-shot input", Trigger: "$F3", ReleaseKey: "F3",
            Key: "prepared", PressMs: 150})
    return actions
}

class GameInputModule
{
    __New(settings := unset, targets := unset)
    {
        if !IsSet(settings)
            settings := GI_BuildSettings()
        if !IsSet(targets)
            targets := GI_BuildTargets(settings.EnableExtended)
        GI_ValidateTargets(targets)
        for target in targets {
            for action in target.Actions {
                if action.Key = "prepared" && !settings.EnableExtended
                    throw Error("Prepared input requires explicit EnableExtended opt-in.")
            }
        }
        this.Settings := settings
        this.Targets := targets
        this.Paused := false
        this.Visible := settings.ShowIndicator
        this.Epoch := 0
        this.LastSentTick := -settings.CooldownMs
        this.LastAction := "No input sent yet."
        this.DisplayCache := ""
        this.Prepared := false
        this.Busy := false
        this.OwnedDown := Map()
        this.Editor := false
        this.Started := false
        this.Panel := false
        this.Bindings := []
        this.Timer := ObjBindMethod(this, "Refresh")
        this.ExitCallback := ObjBindMethod(this, "Stop")
        ; Construction/include is inert: no GUI, hook, timer, input or tray change.
    }

    BindingPlan()
    {
        plan := []
        for target in this.Targets {
            if target.Enabled {
                for action in target.Actions
                    plan.Push({Window: target.Window, Trigger: action.Trigger, Output: action.Key})
            }
        }
        return plan
    }

    Start(bindingsReviewed := false)
    {
        if this.Started
            return false
        ; AHK cannot reliably enumerate another script's hotkeys. This is a host
        ; acknowledgement, NOT automatic collision detection. Audit BindingPlan.
        if !bindingsReviewed
            throw Error("Review/reserve BindingPlan in the host before Start(true).")
        GI_ValidateTargets(this.Targets)
        this.Started := true
        this.Paused := false
        this.Epoch += 1
        this.DisplayCache := ""
        this.LastAction := "Started. No input sent."
        try {
            this.BuildPanel()
            this.RegisterActions()
            OnExit this.ExitCallback
            this.Refresh()
            if this.Visible
                this.ShowIndicator()
            SetTimer this.Timer, this.Settings.RefreshMs
        } catch as err {
            this.Stop()
            throw err
        }
        return true
    }

    Stop(*)
    {
        this.Started := false
        this.Paused := true
        this.Epoch += 1
        this.Prepared := false
        this.ReleaseOwned()
        SetTimer this.Timer, 0
        OnExit this.ExitCallback, 0
        try {
            for binding in this.Bindings {
                HotIfWinActive binding.Window
                Hotkey binding.Trigger, "Off"
            }
        } finally {
            HotIf
            this.Bindings := []
        }
        this.CloseEditor()
        if this.Panel
            this.Panel.Destroy()
        this.Panel := false
        ; Never ExitApp, terminate games, wipe tray, or release host/user holds.
    }

    BuildPanel()
    {
        settings := this.Settings

        ; NOACTIVATE + mouse-transparent, layered status window: never focus it.
        this.Panel := Gui("+AlwaysOnTop -Caption +ToolWindow +E0x08000020", "Control Helper status")
        this.Panel.BackColor := "18212B"
        this.Panel.MarginX := 12
        this.Panel.MarginY := 9
        this.Panel.SetFont("s10 cE5E7EB", "Segoe UI")
        width := "w" settings.IndicatorWidth
        this.Heading := this.Panel.AddText(width " r1", "AHK Control Helper")
        this.ReadyLine := this.Panel.AddText(width " r1", "")
        this.LastLine := this.Panel.AddText(width " r2", this.LastAction)
        this.Panel.SetFont("s8 cA8B3C2")
        this.Panel.AddText(width " r2", "Host controls pause/stop/prepare.`nF3 dispatch requires experimental opt-in.")
        WinSetTransparent 238, "ahk_id " this.Panel.Hwnd

    }

    Snapshot()
    {
        return {Version: this.Settings.Version, Started: this.Started,
            Paused: this.Paused, Busy: this.Busy, Armed: !!this.Prepared,
            Extended: this.Settings.EnableExtended, LastAction: this.LastAction}
    }

    RegisterActions()
    {
        try {
            for target in this.Targets {
                if !target.Enabled
                    continue
                HotIfWinActive target.Window
                for action in target.Actions {
                    Hotkey action.Trigger, ObjBindMethod(this, "SendAction", target, action), "T1"
                    this.Bindings.Push({Window: target.Window, Trigger: action.Trigger})
                }
            }
        } finally {
            HotIf
        }
    }

    ToggleIndicator(*)
    {
        if !this.Started
            return
        this.Visible := !this.Visible
        if this.Visible
            this.ShowIndicator()
        else
            this.Panel.Hide()
    }

    ShowIndicator()
    {
        if this.Started && this.Panel
            this.Panel.Show("NA AutoSize x" this.Settings.IndicatorX " y" this.Settings.IndicatorY)
    }

    TogglePause(*)
    {
        if !this.Started
            return
        this.Paused := !this.Paused
        this.Epoch += 1 ; A trigger waiting for release cannot survive a pause.
        this.Prepared := false
        this.ReleaseOwned()
        try {
            for binding in this.Bindings {
                HotIfWinActive binding.Window
                Hotkey binding.Trigger, this.Paused ? "Off" : "On"
            }
        } finally {
            HotIf
        }
        this.Refresh()
    }

    ToggleSound(*)
    {
        this.Settings.Beep := !this.Settings.Beep
    }

    SendAction(target, action, *)
    {
        if !this.Started
            return
        originalWindow := WinActive(target.Window)
        originalEpoch := this.Epoch
        if !KeyWait(action.ReleaseKey, "T3") {
            this.LastAction := "Skipped: trigger release timed out (3 seconds)"
            this.Refresh()
            return
        }
        modifiers := GetKeyState("Ctrl", "P") || GetKeyState("Alt", "P")
            || GetKeyState("Shift", "P") || GetKeyState("LWin", "P") || GetKeyState("RWin", "P")
        sameWindow := originalWindow && WinActive("ahk_id " originalWindow)
        reason := GI_DispatchBlockReason(this.Paused || !this.Started, target.Enabled, sameWindow,
            originalEpoch = this.Epoch, modifiers,
            A_TickCount - this.LastSentTick, this.Settings.CooldownMs)
        if reason != "" {
            this.LastAction := "Skipped: " reason
            this.Refresh()
            return
        }

        if this.Busy {
            this.LastAction := "Skipped: another bounded action is active"
            this.Refresh()
            return
        }
        if action.Key = "prepared" {
            this.SendPrepared(target, originalWindow, originalEpoch)
            return
        }

        ; One bounded down/up keystroke. Keep the target foreground during it.
        this.Busy := true
        try {
            SetKeyDelay 20, action.PressMs
            SendEvent "{" action.Key "}"
            this.LastAction := "Sent " action.Key " at " FormatTime(, "HH:mm:ss") " -- not verified"
        } finally {
            this.Busy := false
            this.LastSentTick := A_TickCount
        }
        this.Refresh()
        if this.Settings.Beep {
            try SoundBeep 1200, 80 ; Audio failure does not hide the visual result.
        }
    }

    OpenEditor(*)
    {
        if !this.Started || this.Paused || !this.Settings.EnableExtended
            throw Error("Start/unpause and explicitly opt into extended input first.")
        if this.Busy {
            this.LastAction := "Finish/cancel current action before preparing another."
            this.Refresh()
            return
        }
        this.Prepared := false
        if this.Editor
            this.Editor.Destroy()
        selected := 1
        names := []
        for index, target in this.Targets {
            names.Push(target.Name)
            if WinActive(target.Window)
                selected := index
        }
        this.Editor := Gui("+AlwaysOnTop +ToolWindow", "GameInputModule " this.Settings.Version " - Prepare once")
        this.Editor.SetFont("s10", "Segoe UI")
        this.Editor.AddText("w650", "Nothing is sent here. Arm once, focus the game and safe field/menu, then release F3.")
        this.Editor.AddText("w650", "Do not send Enter to consoles, saves, purchases or confirmation prompts.")
        this.Editor.AddText("w100", "Target game")
        this.TargetChoice := this.Editor.AddDropDownList("x+10 w230 Choose" selected, names)
        this.Editor.AddText("xm w100", "Action")
        this.KindChoice := this.Editor.AddDropDownList("x+10 w230 Choose1", ["Text", "Enter", "Escape", "Hold key"])
        this.Editor.AddText("xm w650", "Literal printable text (max 4096; no newline/Tab/control characters; Enter is separate)")
        this.TextEdit := this.Editor.AddEdit("w650 r2 Limit4096", "")
        this.Editor.AddText("xm w100", "Text transport")
        this.TransportChoice := this.Editor.AddDropDownList("x+10 w230 Choose1", ["Raw keys", "Unicode text"])
        this.Editor.AddText("xm w100", "Held key")
        this.HoldChoice := this.Editor.AddDropDownList("x+10 w230 Choose1", ["Left", "Right", "Up", "Down", "Backspace", "W", "A", "S", "D"])
        this.Editor.AddText("xm w100", "Duration ms")
        this.DurationEdit := this.Editor.AddEdit("x+10 w100 Number", "2000")
        this.RepeatCheck := this.Editor.AddCheckbox("x+10 Checked", "Typematic repeat (down events, one final release)")
        this.Editor.AddText("xm w650", "Holds: 250-2000 ms, cancel on focus loss/pause/exit. No persistent profiles or payload files.")
        this.Editor.AddButton("xm w230", "Arm once (120 seconds)").OnEvent("Click", ObjBindMethod(this, "ArmPrepared"))
        this.Editor.AddButton("x+10 w150", "Cancel").OnEvent("Click", ObjBindMethod(this, "CloseEditor"))
        this.EditorError := this.Editor.AddText("xm w650 r2", "")
        this.Editor.OnEvent("Close", ObjBindMethod(this, "CloseEditor"))
        this.Editor.OnEvent("Escape", ObjBindMethod(this, "CloseEditor"))
        this.Editor.Show()
        this.TextEdit.Focus()
    }

    CloseEditor(*)
    {
        if this.Editor
            this.Editor.Destroy()
        this.Editor := false
    }

    ArmPrepared(*)
    {
        target := this.Targets[this.TargetChoice.Value]
        window := WinExist(target.Window)
        if !window {
            this.EditorError.Text := "Selected game is not running. Launch it normally first."
            return
        }
        payload := {Kind: this.KindChoice.Text, Text: this.TextEdit.Value,
            Transport: this.TransportChoice.Text, Key: this.HoldChoice.Text,
            HoldMs: this.DurationEdit.Value, Repeat: this.RepeatCheck.Value,
            Window: window, Target: target.Window, Epoch: this.Epoch,
            Expires: A_TickCount + 120000}
        try GI_ValidatePrepared(payload)
        catch as err {
            this.EditorError.Text := err.Message
            return
        }
        try this.Arm(payload)
        catch as err {
            this.EditorError.Text := err.Message
            return
        }
        this.CloseEditor()
        this.Refresh()
    }

    Arm(payload)
    {
        ; Explicit host/UI call, NOT a polling/file/network/shell command endpoint.
        if !this.Started || this.Paused || this.Busy || !this.Settings.EnableExtended
            throw Error("Prepared input unavailable: stopped/paused/busy or no extended opt-in.")
        GI_ValidatePrepared(payload)
        allowed := false
        for target in this.Targets {
            if target.Enabled && target.Window = payload.Target
                && WinExist("ahk_id " payload.Window) && WinExist(target.Window " ahk_id " payload.Window) {
                allowed := true
                break
            }
        }
        if !allowed
            throw Error("Arm requires one live window of an enabled exact executable.")
        ; Copy only the allowed fields; caller cannot mutate this queued request.
        this.Prepared := {Kind: payload.Kind, Window: payload.Window, Target: payload.Target,
            Epoch: this.Epoch, Expires: A_TickCount + 120000,
            Text: payload.HasOwnProp("Text") ? payload.Text : "",
            Transport: payload.HasOwnProp("Transport") ? payload.Transport : "Raw keys",
            Key: payload.HasOwnProp("Key") ? payload.Key : "Left",
            HoldMs: payload.HasOwnProp("HoldMs") ? payload.HoldMs : 250,
            Repeat: payload.HasOwnProp("Repeat") ? !!payload.Repeat : false}
        this.LastAction := "Armed " payload.Kind " once (120 s). No input sent."
        this.Refresh()
    }

    Cancel(*)
    {
        this.Prepared := false
        this.Epoch += 1
        this.ReleaseOwned()
        this.LastAction := "Cancelled pending/active input."
        this.Refresh()
    }

    SendPrepared(target, window, epoch)
    {
        if !this.Prepared {
            this.LastAction := "Skipped: prepare/arm input with Ctrl+Alt+T first"
            this.Refresh()
            return
        }
        payload := this.Prepared
        this.Prepared := false ; Consume once, including stale/wrong-window attempts.
        if !this.Settings.EnableExtended || payload.Window != window || payload.Target != target.Window
            || payload.Epoch != epoch || A_TickCount > payload.Expires {
            this.LastAction := "Skipped: armed action expired or target/epoch changed"
            this.Refresh()
            return
        }
        this.Busy := true
        completed := false
        this.LastSentTick := A_TickCount
        try {
            if payload.Kind = "Text" {
                SetKeyDelay 25, 80
                Loop Parse payload.Text {
                    if !this.StillEligible(window, epoch)
                        break
                    ; Per-character guard; Raw prevents braces/modifier syntax injection.
                    SendEvent (payload.Transport = "Raw keys" ? "{Raw}" : "{Text}") A_LoopField
                    if A_Index = StrLen(payload.Text)
                        completed := true
                }
            } else if payload.Kind = "Enter" || payload.Kind = "Escape" {
                if this.StillEligible(window, epoch) {
                    SetKeyDelay 20, 150
                    SendEvent "{" (payload.Kind = "Enter" ? "Enter" : "Esc") "}"
                    completed := true
                }
            } else {
                if GetKeyState(payload.Key, "P")
                    throw Error("Release the physical hold-test key first.")
                SetKeyDelay -1, -1
                started := A_TickCount
                repeatAt := started + 350
                this.OwnedDown[payload.Key] := true
                SendEvent "{" payload.Key " down}"
                this.LastAction := "Holding " payload.Key " for <= " payload.HoldMs " ms -- not verified"
                this.Refresh()
                while A_TickCount - started < payload.HoldMs {
                    if !this.StillEligible(window, epoch)
                        break
                    if payload.Repeat && A_TickCount >= repeatAt {
                        SendEvent "{" payload.Key " down}"
                        repeatAt := A_TickCount + 80
                    }
                    Sleep 20
                }
                completed := this.StillEligible(window, epoch)
            }
        } finally {
            this.ReleaseOwned()
            this.Busy := false
            this.LastSentTick := A_TickCount
            this.LastAction := (completed ? "Sent " : "Cancelled ") payload.Kind
                . " at " FormatTime(, "HH:mm:ss") " -- observe game; not verified"
            this.Refresh()
        }
    }

    StillEligible(window, epoch)
    {
        return this.Started && !this.Paused && this.Epoch = epoch && WinActive("ahk_id " window)
            && !GetKeyState("Ctrl", "P") && !GetKeyState("Alt", "P")
            && !GetKeyState("Shift", "P") && !GetKeyState("LWin", "P") && !GetKeyState("RWin", "P")
    }

    ReleaseOwned(*)
    {
        ; Releases only keys this helper explicitly held. Never activates a window.
        for key in this.OwnedDown {
            try SendEvent "{" key " up}"
        }
        this.OwnedDown.Clear()
    }

    Refresh(*)
    {
        if !this.Started || !this.Panel
            return
        if this.Prepared && A_TickCount > this.Prepared.Expires
            this.Prepared := false
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
        state := GI_HelperStatus(this.Paused, targetName)
        display := state "|" hint "|" this.LastAction
        if display = this.DisplayCache
            return
        this.DisplayCache := display
        this.Heading.Text := "AHK helper v" this.Settings.Version " | " state
        this.Heading.SetFont("c" (this.Paused ? "FBBF24" : targetName != "" ? "86EFAC" : "CBD5E1"))
        this.ReadyLine.Text := this.Paused ? "Paused: action keys pass through." : hint
        this.LastLine.Text := this.LastAction
    }
}

GI_HelperStatus(paused, targetName)
{
    return paused ? "PAUSED" : targetName != "" ? "READY: " targetName : "RUNNING / WAITING"
}

GI_DispatchBlockReason(paused, enabled, sameWindow, sameEpoch, modifiers, elapsedMs, cooldownMs)
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

GI_ValidateTargets(targets)
{
    seen := Map()
    for target in targets {
        if !RegExMatch(target.Window, "i)^ahk_exe [a-z0-9_.-]+\.exe$")
            throw Error("Each target must name one exact executable.")
        if target.Actions.Length = 0
            throw Error("A target needs at least one verified action.")
        for action in target.Actions {
            if action.Key != "prepared" && !RegExMatch(action.Key, "i)^(F([1-9]|1[0-9]|2[0-4])|[A-Z0-9]|Space|Tab|Esc|Enter|Delete|Backspace|vkC0|Up|Down|Left|Right|NumpadAdd|NumpadSub|NumpadMult)$")
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

GI_ValidatePrepared(payload)
{
    if payload.Kind = "Text" {
        if StrLen(payload.Text) < 1 || StrLen(payload.Text) > 4096
            throw Error("Enter 1-4096 printable characters.")
        if RegExMatch(payload.Text, "[\x00-\x1F\x7F]")
            throw Error("Control characters/newlines are blocked; use a separate observed key action.")
        if payload.Transport != "Raw keys" && payload.Transport != "Unicode text"
            throw Error("Unsupported text transport.")
    } else if payload.Kind = "Hold key" {
        if !RegExMatch(payload.Key, "i)^(Left|Right|Up|Down|Backspace|W|A|S|D)$")
            throw Error("Held key is outside the diagnostic allowlist.")
        if !IsNumber(payload.HoldMs) || payload.HoldMs < 250 || payload.HoldMs > 2000
            throw Error("Hold duration must be 250-2000 ms.")
    } else if payload.Kind != "Enter" && payload.Kind != "Escape"
        throw Error("Unsupported prepared action.")
}

GI_RunSelfTests()
{
    settings := GI_BuildSettings()
    targets := GI_BuildTargets(true)
    GI_ValidateTargets(targets)
    GI_AssertTest(settings.ShowIndicator, "indicator visible by default")
    GI_AssertTest(targets.Length = 2 && targets[1].Window = "ahk_exe SkyrimSE.exe"
        && targets[2].Window = "ahk_exe Cyberpunk2077.exe", "exact two-game scope")
    GI_AssertTest(targets[1].Actions.Length = 11 && targets[1].Actions[1].Key = "F12", "Skyrim menu route")
    GI_AssertTest(targets[2].Actions.Length = 11 && targets[2].Actions[1].Key = "Delete", "Cyberpunk menu route")
    safeOutputs := true
    for target in targets {
        for action in target.Actions {
            if RegExMatch(action.Key, "i)^(Enter|F5|F6|F9|NumpadAdd|NumpadMult)$")
                safeOutputs := false
        }
    }
    GI_AssertTest(safeOutputs, "no submit/save/load/graphics outputs")
    GI_AssertTest(GI_HelperStatus(false, "") = "RUNNING / WAITING", "waiting status")
    GI_AssertTest(GI_HelperStatus(false, "Skyrim") = "READY: Skyrim", "ready status")
    GI_AssertTest(GI_HelperStatus(true, "Skyrim") = "PAUSED", "paused status")
    GI_AssertTest(GI_DispatchBlockReason(false, true, true, true, false, 800, 800) = "", "eligible send")
    GI_AssertTest(GI_DispatchBlockReason(true, true, true, true, false, 800, 800) != "", "paused block")
    GI_AssertTest(GI_DispatchBlockReason(false, false, true, true, false, 800, 800) != "", "disabled block")
    GI_AssertTest(GI_DispatchBlockReason(false, true, false, true, false, 800, 800) != "", "focus-loss block")
    GI_AssertTest(GI_DispatchBlockReason(false, true, true, false, false, 800, 800) != "", "pause-epoch block")
    GI_AssertTest(GI_DispatchBlockReason(false, true, true, true, true, 800, 800) != "", "modifier block")
    GI_AssertTest(GI_DispatchBlockReason(false, true, true, true, false, 799, 800) != "", "cooldown block")
    invalid := GI_BuildTargets()
    invalid[1].Window := "ahk_exe *.exe"
    GI_AssertInvalidTargets(invalid, "catch-all target rejected")
    invalid := GI_BuildTargets()
    invalid[1].Actions[1].Key := "{F12}{Enter}"
    GI_AssertInvalidTargets(invalid, "multi-key payload rejected")
    invalid := GI_BuildTargets()
    invalid[1].Actions[1].PressMs := 251
    GI_AssertInvalidTargets(invalid, "excessive hold rejected")
    invalid := GI_BuildTargets()
    invalid[1].Actions.Push(invalid[1].Actions[1])
    GI_AssertInvalidTargets(invalid, "duplicate trigger rejected")
    invalid := GI_BuildTargets()
    invalid[1].Actions[1].Key := "F8"
    GI_AssertInvalidTargets(invalid, "feedback trigger rejected")
    ; Standard output only. No file, GUI, keyboard hook, sound, timer or input.
    probe := {Kind: "Text", Text: "Mixed Case 123 ! {} ^+#", Transport: "Raw keys"}
    GI_ValidatePrepared(probe)
    GI_AssertTest(true, "literal arbitrary text accepted")
    probe.Transport := "Unicode text"
    GI_ValidatePrepared(probe)
    GI_AssertTest(true, "Unicode transport accepted")
    probe.Text := "test`nenter"
    GI_AssertInvalidPrepared(probe, "embedded Enter blocked")
    probe.Text := ""
    GI_AssertInvalidPrepared(probe, "empty payload blocked")
    probe := {Kind: "Hold key", Key: "Left", HoldMs: 2000}
    GI_ValidatePrepared(probe)
    GI_AssertTest(true, "bounded hold accepted")
    probe.HoldMs := 2001
    GI_AssertInvalidPrepared(probe, "unbounded hold blocked")
    probe.HoldMs := 1000
    probe.Key := "F5"
    GI_AssertInvalidPrepared(probe, "save hold blocked")
    GI_ValidatePrepared({Kind: "Enter"})
    GI_ValidatePrepared({Kind: "Escape"})
    GI_AssertTest(true, "separate explicit Enter/Escape accepted")
    GI_AssertTest(!settings.EnableExtended, "experimental input is off by default")
    inert := GameInputModule()
    GI_AssertTest(!inert.Started && !inert.Panel && !inert.Editor && inert.Bindings.Length = 0,
        "constructor has no activation side effects")
    GI_AssertTest(inert.BindingPlan().Length = 20, "default binding plan contains only baseline keys")
    try {
        inert.Start()
        GI_AssertTest(false, "unreviewed binding registration blocked")
    } catch as err {
        GI_AssertTest(!inert.Started, "unreviewed binding registration blocked")
    }
    try {
        inert.OpenEditor()
        GI_AssertTest(false, "editor unavailable while stopped")
    } catch {
        GI_AssertTest(!inert.Editor, "editor unavailable while stopped")
    }
    try {
        inert.Arm({Kind: "Enter"})
        GI_AssertTest(false, "arming blocked while stopped")
    } catch {
        GI_AssertTest(!inert.Prepared, "arming blocked while stopped")
    }
    settings.EnableExtended := true
    extended := GameInputModule(settings)
    GI_AssertTest(extended.BindingPlan().Length = 22, "F3 exists only after opt-in")
    rejected := false
    try GameInputModule(GI_BuildSettings(), GI_BuildTargets(true))
    catch
        rejected := true
    GI_AssertTest(rejected, "prepared target rejected without opt-in")
    FileAppend "PASS: 36 policy/configuration tests; no input, GUI, hooks or running timers.`n", "*"
}

GI_AssertInvalidPrepared(payload, name)
{
    try GI_ValidatePrepared(payload)
    catch
        return
    GI_AssertTest(false, name)
}

GI_AssertInvalidTargets(targets, name)
{
    try GI_ValidateTargets(targets)
    catch
        return
    GI_AssertTest(false, name)
}

GI_AssertTest(condition, name)
{
    if !condition {
        throw Error("FAIL: " name)
    }
}
