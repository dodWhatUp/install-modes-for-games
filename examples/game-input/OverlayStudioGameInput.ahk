#Requires AutoHotkey v2.0

; Optional adapter for the existing Overlay Studio 2 host, not a replacement host.
; Include GameInputModule first. No automatic activation or settings/profile writes.
class OS_GameInputHost {
    __New(host) {
        this.Host := host
        this.Module := false
        this.Management := ["$^!t", "$^!Esc"]
        this.ManagementBound := []
    }

    BuildGui(g, tabs) {
        tabs.UseTab(5)
        g.AddText("x38 y115 w870 h48", "Optional agent-operated input for Skyrim / Cyberpunk. OFF at launch. Existing pictures, MIC, key display and saved profiles are preserved.")
        this.Extended := g.AddCheckbox("x38 y178 w850", "Enable one-shot text, Enter, Escape and bounded held-key tests")
        g.AddButton("x38 y222 w160", "Start Game Input").OnEvent("Click", this.Start.Bind(this))
        g.AddButton("x210 y222 w150", "Stop Game Input").OnEvent("Click", this.Stop.Bind(this))
        g.AddButton("x372 y222 w150", "Pause / Resume").OnEvent("Click", this.Pause.Bind(this))
        g.AddButton("x534 y222 w150", "Show / Hide status").OnEvent("Click", this.Indicator.Bind(this))
        g.AddButton("x38 y268 w220", "Prepare one-shot input").OnEvent("Click", this.Prepare.Bind(this))
        g.AddButton("x270 y268 w200", "Cancel queued / held input").OnEvent("Click", this.Cancel.Bind(this))
        this.Status := g.AddText("x38 y323 w860 h62", "OFF - no game input registered.")
        g.AddText("x38 y402 w870 h152", "While active: F8 = PureDark (Skyrim) / ReShade (Cyberpunk); F13 = ReShade; F14/F15 = Down/Up; F16 = console-panel toggle only; F17/F18 = Left/Right; F19 = Escape; F20 = digit 1; F2 = Backspace; F3 = armed one-shot input. Ctrl+Alt+T prepares; Ctrl+Alt+Esc stops ONLY Game Input, not Studio.`n`nNothing is sent from this panel. Focus an observed safe game field/menu, then release the trigger. Never submit console commands or activate saves, Continue/New, purchases or graphics values during input tests.")
        g.AddText("x38 y568 w860 h60 cAE4B27", "Collision checks include enabled picture triggers and MIC outputs. Editing/rebinding host controls stops Game Input. Host shutdown releases module-owned holds. Synthetic SendEvent outputs remain excluded by the existing key-display filter.")
    }

    BuildTray() {
        trayMenu := Menu()
        trayMenu.Add("Open Game Input tab", this.OpenTab.Bind(this))
        trayMenu.Add("Start (uses tab opt-in)", this.Start.Bind(this))
        trayMenu.Add("Prepare once", this.Prepare.Bind(this))
        trayMenu.Add("Cancel pending / active input", this.Cancel.Bind(this))
        trayMenu.Add("Stop Game Input only", this.Stop.Bind(this))
        A_TrayMenu.Add("Game Input (optional)", trayMenu)
        this.Tray := trayMenu
    }

    OpenTab(*) {
        this.Host.ShowPanel()
        this.Host.Tabs.Choose(5)
    }

    Start(*) {
        if this.Module && this.Module.Started
            return
        try {
            if !this.Host.Enabled || this.Host.Capturing
                throw Error("Resume Studio and finish key capture before starting Game Input.")
            settings := GI_BuildSettings()
            settings.EnableExtended := !!this.Extended.Value
            settings.Beep := false
            module := GameInputModule(settings)
            conflict := OS_GI_ConflictReason(this.Host.Slots, this.Host.MicToggle, module)
            if conflict != ""
                throw Error(conflict "`nExisting profiles were not changed. Stop or reconfigure the optional module, not your saved layout.")
            this.Module := module
            module.Start(true)
            this.Extended.Enabled := false
            HotIf
            Hotkey this.Management[1], this.Prepare.Bind(this), "On"
            this.ManagementBound.Push(this.Management[1])
            Hotkey this.Management[2], this.Stop.Bind(this), "On"
            this.ManagementBound.Push(this.Management[2])
            this.Host.WriteLog("Game Input started; exact two-game scope, no payload logging or profile writes.")
            this.RefreshUi()
        } catch as err {
            this.Stop()
            this.Host.WriteLog("Game Input start refused: " err.Message)
            MsgBox(err.Message, "Game Input not started", "Icon!")
        }
    }

    Stop(*) {
        try {
            if this.Module && this.Module.Started
                this.Module.Stop()
        } finally {
            HotIf
            for key in this.ManagementBound
                try Hotkey key, "Off"
            this.ManagementBound := []
            if this.HasOwnProp("Extended")
                this.Extended.Enabled := true
            this.RefreshUi()
        }
    }

    StopForHost(*) {
        if this.Module && this.Module.Started {
            this.Stop()
            this.Host.WriteLog("Game Input stopped before host pause/capture/rebind/shutdown.")
        }
    }

    Prepare(*) {
        if !this.Module || !this.Module.Started || this.Module.Paused || !this.Module.Settings.EnableExtended {
            this.OpenTab()
            this.Host.WriteLog("Prepare unavailable: explicitly enable extended input and start/unpause Game Input.")
            return
        }
        this.Module.OpenEditor()
    }

    Cancel(*) {
        if this.Module && this.Module.Started
            this.Module.Cancel()
        this.RefreshUi()
    }

    Pause(*) {
        if this.Module && this.Module.Started
            this.Module.TogglePause()
        this.RefreshUi()
    }

    Indicator(*) {
        if this.Module && this.Module.Started
            this.Module.ToggleIndicator()
    }

    RefreshUi(*) {
        if !this.HasOwnProp("Status")
            return
        if !this.Module || !this.Module.Started {
            this.Status.Text := "OFF - no game input active. Studio features remain available."
            return
        }
        s := this.Module.Snapshot()
        this.Status.Text := "GameInputModule " s.Version " | " (s.Paused ? "PAUSED" : "ACTIVE")
            . " | extended=" s.Extended " | armed=" s.Armed " | busy=" s.Busy "`n" s.LastAction
    }
}

OS_GI_ConflictReason(slots, micToggle, module) {
    reserved := Map()
    for binding in module.BindingPlan() {
        reserved[OS_GI_KeyId(LTrim(binding.Trigger, "$"))] := true
        if binding.Output != "prepared"
            reserved[OS_GI_KeyId(binding.Output)] := true
    }
    ; Literal text can output any printable key. Do not activate a global picture
    ; or MIC key accidentally, or use letters as module triggers in this host.
    for s in slots {
        if !s.Enabled
            continue
        key := OS_GI_KeyId(s.Key)
        vk := GetKeyVK(s.Key)
        printable := vk = 0x20 || (vk >= 0x30 && vk <= 0x5A) || (vk >= 0xBA && vk <= 0xE2)
        if reserved.Has(key) || (module.Settings.EnableExtended && printable)
            return "Enabled picture trigger " s.Key " overlaps Game Input."
        if s.Source = "MIC" {
            for combo in [s.MicCanvas, micToggle] {
                plain := OS_GI_KeyId(RegExReplace(combo, "^[\^!+]+"))
                if reserved.Has(plain) || OS_GI_IsManagementCombo(combo)
                    return "An enabled MIC output overlaps a Game Input shortcut."
            }
        }
    }
    if OS_GI_IsManagementCombo(micToggle)
        return "The saved MIC toggle owns a Game Input management shortcut."
    return ""
}

OS_GI_KeyId(key) {
    ; GetKeyName("t") can return a Hebrew character in the active layout.
    ; Stable VK identity also reconciles Esc/Escape without rewriting labels.
    vk := GetKeyVK(key)
    return vk ? Format("vk{:X}", vk) : StrLower(key)
}

OS_GI_IsManagementCombo(combo) {
    key := OS_GI_KeyId(RegExReplace(combo, "^[\^!+]+"))
    return InStr(combo, "^") && InStr(combo, "!") && !InStr(combo, "+")
        && (key = OS_GI_KeyId("Esc") || key = OS_GI_KeyId("t"))
}

OS_GI_RunSelfTests() {
    settings := GI_BuildSettings()
    settings.EnableExtended := true
    module := GameInputModule(settings)
    safe := [{Enabled: 1, Key: "F7", Source: "Local"}, {Enabled: 0, Key: "F15", Source: "Local"}]
    GI_AssertTest(OS_GI_ConflictReason(safe, "^!h", module) = "", "F7 baseline plus dormant F15 preserved")
    safe[1].Key := "F15"
    GI_AssertTest(OS_GI_ConflictReason(safe, "^!h", module) != "", "active picture trigger collision rejected")
    safe[1].Key := "A"
    GI_AssertTest(OS_GI_ConflictReason(safe, "^!h", module) != "", "printable picture trigger collision rejected")
    safe[1].Key := "F7"
    GI_AssertTest(OS_GI_ConflictReason(safe, "^!t", module) != "", "MIC management ownership preserved")
    safe[1].Source := "MIC", safe[1].MicCanvas := "F13"
    GI_AssertTest(OS_GI_ConflictReason(safe, "^!h", module) != "", "MIC output feedback rejected")
    GI_AssertTest(!module.Started && !module.Panel && !module.Editor && module.Bindings.Length = 0,
        "host collision review has no activation side effects")
    GI_AssertTest(OS_GI_KeyId("Esc") = OS_GI_KeyId("Escape"), "key aliases normalized")
    GI_AssertTest(OS_GI_IsManagementCombo("!^Escape"), "modifier order and Escape alias protected")
    FileAppend "PASS: 8 Overlay Studio integration policy tests; no host/profile writes or input.`n", "*"
}

; Read-only acceptance of the installed INI, without the host constructor,
; GUI, hotkeys, timers, tray or any settings writes. This is a separate opt-in
; diagnostic because the portable policy tests must not require a local INI.
OS_GI_CheckSavedProfile() {
    config := A_AppData "\AzeronOverlayStudio\settings.ini"
    if !FileExist(config)
        throw Error("No installed Studio settings to check.")
    stub := {Config: config, Slots: [], LogLines: [], Enabled: true, MicToggle: "^!h",
        Hud: {Enabled: 0, Duration: 1.6, FontSize: 26, Opacity: 85,
            Position: "BottomRight", Recent: 3, TextColor: "FFFFFF", BgColor: "202833", IgnoreMods: 0}}
    ObjSetBase(stub, OverlayStudio.Prototype)
    stub.LoadConfig()
    for n, slot in stub.Slots {
        expectedKey := IniRead(config, "Slot" n, "Key", "")
        FileAppend "Slot " n ": loaded=" slot.Key " enabled=" slot.Enabled " expected=" expectedKey "`n", "*"
    }
    for n, slot in stub.Slots {
        GI_AssertTest(slot.Key = GetKeyName(IniRead(config, "Slot" n, "Key", "")), "saved slot " n " key loaded")
        GI_AssertTest(slot.Enabled = Integer(IniRead(config, "Slot" n, "Enabled", 0)), "saved slot " n " enabled state loaded")
        GI_AssertTest(slot.File = IniRead(config, "Slot" n, "File", ""), "saved slot " n " file loaded")
    }
    GI_AssertTest(stub.Hud.Enabled = Integer(IniRead(config, "HUD", "Enabled", 0)), "saved HUD enabled state loaded")
    FileAppend "PASS: installed Studio profile read-only load check; no input or settings writes.`n", "*"
}
