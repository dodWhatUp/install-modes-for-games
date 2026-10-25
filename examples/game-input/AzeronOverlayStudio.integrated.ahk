#Requires AutoHotkey v2.0
#Warn All, StdOut
#SingleInstance Force
#Include %A_LineFile%\..\GameInputModule.ahk
#Include %A_LineFile%\..\OverlayStudioGameInput.ahk
#Include %A_LineFile%\..\StudioPictureModule.ahk
#Include %A_LineFile%\..\StudioOverlayGroups.ahk
#Include %A_LineFile%\..\StudioHubBridge.ahk

if A_Args.Length && A_Args[1] = "--game-input-self-test" {
    try {
        GI_RunSelfTests()
        OS_GI_RunSelfTests()
        ExitApp(0)
    } catch as startupDiagnosticError {
        FileAppend startupDiagnosticError.Message "`n", "**"
        ExitApp(1)
    }
}
if A_Args.Length && A_Args[1] = "--game-input-profile-check" {
    try {
        OS_GI_CheckSavedProfile()
        ExitApp(0)
    } catch as startupDiagnosticError {
        FileAppend startupDiagnosticError.Message "`n", "**"
        ExitApp(1)
    }
}
Persistent()

; Azeron Overlay Studio 2.0 (2026-10-10)
; Unified GUI for image-on-key, Multi Image Canvas hold bridge and keystroke HUD.
; Uses ordinary Windows keyboard events (e.g. Azeron Software V2 mapped to F14).
; No reWASD, injection, administrator rights, network or keystroke file recording.

studio := OverlayStudio()

class OverlayStudio {
    __New() {
        this.Version := "2.2.0-unified.24"
        this.Dir := A_AppData "\AzeronOverlayStudio"
        this.SettingsLoadError := ""
        this.LoadedSettingsSHA := ""
        if A_Args.Length = 6 && A_Args[1] = "--hub-parent" && A_Args[3] = "--hub-owner" && A_Args[5] = "--settings-dir" {
            selectedDir := RTrim(A_Args[6], "\/")
            if !RegExMatch(selectedDir, "i)^[a-z]:\\") || !DirExist(selectedDir) || !FileExist(selectedDir "\settings.ini")
                throw Error("The existing Hub settings directory is unavailable; refusing blank defaults.")
            if DllCall("GetFileAttributesW", "str", selectedDir, "uint") & 0x400
                throw Error("Linked Hub settings directory refused.")
            this.Dir := selectedDir
        }
        this.DesktopTest := false
        if A_Args.Length && A_Args[1] = "--picture-ui-fixture" {
            if A_Args.Length != 2
                throw Error("Desktop fixture requires one prepared, isolated settings directory.")
            fixture := RTrim(StrReplace(A_Args[2], "/", "\"), "\")
            SplitPath(fixture, &leaf, &parent)
            if StrLower(parent) != StrLower(RTrim(A_Temp, "\")) || !RegExMatch(leaf, "^StudioPictureUiFixture-[a-f0-9]{32}$")
                || !FileExist(fixture "\settings.ini")
                throw Error("Refused non-isolated or unprepared desktop fixture.")
            for target in [A_Temp, fixture, fixture "\settings.ini"] {
                attributes := DllCall("GetFileAttributesW", "str", target, "uint")
                if attributes = 0xFFFFFFFF || (attributes & 0x400)
                    throw Error("Refused a linked or missing desktop fixture target.")
            }
            this.Dir := fixture
            this.DesktopTest := true
        }
        DirCreate(this.Dir)
        this.Config := this.Dir "\settings.ini"
        this.LogLines := []
        this.Slots := []
        this.Bound := []
        this.Pressed := Map()
        this.Current := 0
        this.Generation := 0
        this.HideTimer := 0
        this.PictureGui := 0
        this.PictureAlpha := false
        this.Fade := PM_OverlayFade(this)
        this.MicVisibleByUs := false
        this.Enabled := true
        this.TotalEvents := 0
        this.LastEvent := "No trigger yet"
        this.Selected := 1
        this.Selecting := false
        this.Gui := 0
        this.Capturing := false
        this.KeyHook := 0
        this.HudGui := 0
        this.HudLabel := 0
        this.HudHistory := []
        this.HudDown := Map()
        this.HudDirty := false
        this.MicToggle := "^!h"
        this.Hud := {Enabled: 0, Duration: 1.6, FontSize: 26, Opacity: 85,
            Position: "BottomRight", Recent: 3, TextColor: "FFFFFF", BgColor: "202833",
            IgnoreMods: 0}
        this.LoadConfig()
        this.GameInput := OS_GameInputHost(this)
        this.Pictures := StudioPictureModule(this)
        this.GroupRoute := StudioOverlayGroups(this)
        this.HubBridge := StudioHubBridge(this)
        this.BuildGui()
        this.HubBridge.Attach()
        this.BuildTray()
        this.BindAll()
        this.WriteRuntimeStatus()
        this.StartKeyDisplay()
        this.WriteLog("Application launched. Control panel is open.")
        if !this.HubBridge.Show()
            this.Gui.Show("w976 h733")
        this.RefreshStatus()
        A_IconTip := "Azeron Overlay Studio - RUNNING (right-click for menu)"
        TrayTip("Running. Configure images and press Test. Closing this window keeps it running.",
            "Azeron Overlay Studio")
        this.TickFn := this.Tick.Bind(this)
        SetTimer(this.TickFn, 140)
        OnExit(this.Shutdown.Bind(this))
    }

    NewSlot(i) {
        return {Enabled: 0, Name: "Picture " i, Key: (i <= 11 ? ("F" (13 + i)) : "Numpad0"),
            Source: "Local", Mode: "Hold", File: "", MicCanvas: "",
            Width: 800, Opacity: 75, Position: "TopRight", OffsetX: 0,
            OffsetY: 0, Duration: 2, Pass: 0}
    }

    LoadConfig() {
        count := 4
        try count := Integer(IniRead(this.Config, "General", "SlotCount", 4))
        count := Max(1, Min(12, count))
        try this.Enabled := Integer(IniRead(this.Config, "General", "Enabled", 1)) != 0
        try this.MicToggle := IniRead(this.Config, "General", "MICToggle", "^!h")
        Loop count {
            slotNumber := A_Index
            s := this.NewSlot(slotNumber)
            for property, defaultValue in s.OwnProps() {
                try s.%property% := IniRead(this.Config, "Slot" slotNumber, property, defaultValue)
            }
            this.Slots.Push(s)
        }
        for property, defaultValue in this.Hud.OwnProps() {
            try this.Hud.%property% := IniRead(this.Config, "HUD", property, defaultValue)
        }
        try this.ValidateAll(this.Slots)
        catch Error as err {
            ; Keep old INI intact. Show a useful error, revert only in-memory settings.
            this.Slots := []
            Loop 4
                this.Slots.Push(this.NewSlot(A_Index))
            this.Enabled := true
            this.LogLines.Push("Settings failed validation; safe defaults loaded: " err.Message)
            this.SettingsLoadError := err.Message
        }
        try this.ValidateHud(this.Hud)
        catch Error as err {
            this.Hud := {Enabled: 0, Duration: 1.6, FontSize: 26, Opacity: 85,
                Position: "BottomRight", Recent: 3, TextColor: "FFFFFF",
                BgColor: "202833", IgnoreMods: 0}
            this.LogLines.Push("HUD settings reset: " err.Message)
        }
        if !this.ValidCombo(this.MicToggle)
            this.MicToggle := "^!h"
        if FileExist(this.Config)
            this.LoadedSettingsSHA := PM_Model.Sha256(this.Config)
    }

    SaveConfig() {
        temp := this.Config ".new"
        try {
            if FileExist(temp)
                FileDelete(temp)
            IniWrite(this.Slots.Length, temp, "General", "SlotCount")
            IniWrite(this.Enabled ? 1 : 0, temp, "General", "Enabled")
            IniWrite(this.MicToggle, temp, "General", "MICToggle")
            for i, s in this.Slots
                for property, value in s.OwnProps()
                    IniWrite(value, temp, "Slot" i, property)
            for property, value in this.Hud.OwnProps()
                IniWrite(value, temp, "HUD", property)
            FileMove(temp, this.Config, 1)
            this.LoadedSettingsSHA := PM_Model.Sha256(this.Config)
        } catch Error as err {
            this.WriteLog("SAVE FAILED: " err.Message)
            if FileExist(temp)
                try FileDelete(temp)
            MsgBox("Could not save settings to:`n" this.Config "`n" err.Message,
                "Azeron Overlay Studio", "Iconx")
        }
    }

    ValidateAll(slots) {
        seen := Map()
        for i, s in slots {
            s.Enabled := Integer(s.Enabled) != 0 ? 1 : 0
            s.Name := Trim(s.Name)
            if s.Name = ""
                s.Name := "Slot " i
            s.Key := Trim(s.Key)
            if !RegExMatch(s.Key, "i)^[a-z][a-z0-9]*$|^[0-9]$")
                throw Error("Slot " i ": use one key (F14, F15, Space, A, etc.).")
            key := GetKeyName(s.Key)
            if key = "" || RegExMatch(key, "i)^(?:Ctrl|Control|Alt|Shift|Win|LWin|RWin|LButton|RButton|XButton[12]|Wheel.*|Joy.*)$")
                throw Error("Slot " i ": invalid trigger key: " s.Key)
            s.Key := key
            if s.Enabled {
                lower := StrLower(key)
                if seen.Has(lower)
                    throw Error("Enabled slots " seen[lower] " and " i " share " key ".")
                seen[lower] := i
            }
            if !InStr("|Local|MIC|", "|" s.Source "|")
                throw Error("Slot " i ": invalid source.")
            if !InStr("|Hold|Toggle|Timed|", "|" s.Mode "|")
                throw Error("Slot " i ": invalid mode.")
            if !InStr("|TopLeft|TopRight|Center|BottomLeft|BottomRight|", "|" s.Position "|")
                throw Error("Slot " i ": invalid position.")
            if !this.IsWhole(s.Width, 80, 8000) || !this.IsWhole(s.Opacity, 5, 100)
                throw Error("Slot " i ": width 80-8000; opacity 5-100.")
            if !this.IsWhole(s.OffsetX, -4000, 4000) || !this.IsWhole(s.OffsetY, -4000, 4000)
                throw Error("Slot " i ": X/Y offsets must be between -4000 and 4000.")
            if !IsNumber(s.Duration) || Number(s.Duration) < 0.2 || Number(s.Duration) > 60
                throw Error("Slot " i ": duration must be 0.2-60 seconds.")
            if s.Pass != 0 && s.Pass != 1
                throw Error("Slot " i ": invalid pass-through setting.")
            s.Width := Integer(s.Width), s.Opacity := Integer(s.Opacity)
            s.OffsetX := Integer(s.OffsetX), s.OffsetY := Integer(s.OffsetY)
            s.Duration := Number(s.Duration), s.Pass := Integer(s.Pass)
            s.File := Trim(s.File)
            if s.Source = "Local" && s.Enabled {
                if !FileExist(s.File) || DirExist(s.File)
                    throw Error("Slot " i ": choose an existing picture before enabling.")
                if !RegExMatch(s.File, "i)\.(?:png|jpe?g|bmp|gif|tiff?)$")
                    throw Error("Slot " i ": expected PNG/JPG/BMP/GIF/TIF.")
            }
            s.MicCanvas := Trim(s.MicCanvas)
            if s.Source = "MIC" && s.MicCanvas != "" && !this.ValidCombo(s.MicCanvas)
                throw Error("Slot " i ": invalid MIC canvas shortcut.")
        }
        for i, s in slots {
            if !s.Enabled || s.Source != "MIC" || s.MicCanvas = ""
                continue
            ; Avoid recursively re-invoking an overlay trigger by sending its key.
            if seen.Has(StrLower(s.MicCanvas))
                throw Error("Slot " i ": MIC canvas key conflicts with an enabled trigger. Use another key.")
        }
    }

    IsWhole(v, minimum, maximum) {
        return RegExMatch(v "", "^-?\d+$") && Number(v) >= minimum && Number(v) <= maximum
    }

    ValidCombo(key) {
        ; GUI Hotkey control yields examples such as ^!h, F14, ^+F15.
        if !RegExMatch(key, "i)^[\^!+]*[a-z0-9]+$")
            return false
        plain := RegExReplace(key, "^[\^!+]+")
        return GetKeyName(plain) != ""
    }

    ComboToSend(combo) {
        key := RegExReplace(combo, "^[\^!+]+")
        mods := SubStr(combo, 1, StrLen(combo) - StrLen(key))
        if StrLen(key) = 1
            return mods key
        return mods "{" key "}"
    }

    BuildGui() {
        g := Gui("+Resize", "Azeron Overlay Studio | Images - MIC - Key display")
        this.Gui := g
        if this.DesktopTest
            g.Title .= " | ISOLATED DESKTOP TEST - no input hooks"
        g.BackColor := "F5F7FA"
        g.SetFont("s10", "Segoe UI")
        this.TitleText := g.AddText("x18 y13 w680 h27 c16293D", "AZERON OVERLAY STUDIO   |   Control panel")
        this.RunText := g.AddText("x18 y43 w930 h22 c087C4E", "Starting...")
        this.Feedback := StudioComponentFeedback(this)
        if !this.HubBridge.Parent {
            identifyToggle := g.AddButton("x872 y12 w80 h25", "? UI IDs")
            identifyToggle.OnEvent("Click", this.Feedback.ShowMenu.Bind(this.Feedback))
            this.Feedback.Targets[identifyToggle] := true
        }
        this.Feedback.RegisterNew(g, "UI-109", this)
        tabs := g.AddTab3("x15 y75 w944 h574", ["1. Picture buttons", "2. Multi Image Canvas", "3. Key display", "4. Status / log", "5. Game Input"])
        this.Tabs := tabs
        this.Feedback.RegisterNew(g, "UI-109", this)

        ; Picture slots and detailed editor.
        tabs.UseTab(1)
        g.AddText("x36 y116 w880", "Each enabled trigger can show a local picture OR a saved Multi Image Canvas tab.")
        this.List := g.AddListView("x35 y142 w905 h160 Grid -Multi", ["#", "On", "Name", "Key", "Source", "Mode", "Picture / MIC canvas"])
        this.List.ModifyCol(1, 30), this.List.ModifyCol(2, 36), this.List.ModifyCol(3, 155)
        this.List.ModifyCol(4, 75), this.List.ModifyCol(5, 85), this.List.ModifyCol(6, 75)
        this.List.ModifyCol(7, 420)
        this.List.OnEvent("ItemSelect", this.SelectSlot.Bind(this))
        g.AddButton("x36 y313 w120", "+ Add slot").OnEvent("Click", this.AddSlot.Bind(this))
        g.AddButton("x168 y313 w120", "Remove slot").OnEvent("Click", this.RemoveSlot.Bind(this))
        g.AddText("x320 y318 w600 c596577", "Select a row. Configure it below, then press Save slot.")

        g.AddText("x36 y351 w150", "Name")
        this.FName := g.AddEdit("x36 y375 w220")
        this.FEnabled := g.AddCheckBox("x275 y375 w95", "Enabled")
        g.AddText("x400 y351", "Trigger key")
        this.FKey := g.AddEdit("x400 y375 w103")
        g.AddButton("x510 y374 w113", "Record key").OnEvent("Click", this.RecordKey.Bind(this))
        g.AddText("x644 y351", "Source")
        this.FSource := g.AddDropDownList("x644 y375 w149", ["Local", "MIC"])
        this.FSource.OnEvent("Change", this.OnSourceChanged.Bind(this))
        g.AddText("x809 y351", "Mode")
        this.FMode := g.AddDropDownList("x809 y375 w130", ["Hold", "Toggle", "Timed"])

        g.AddText("x36 y413 w550", "Local picture file (PNG/JPG/BMP/GIF/TIF)")
        this.FFile := g.AddEdit("x36 y436 w664")
        g.AddButton("x710 y435 w112", "Browse...").OnEvent("Click", this.BrowsePicture.Bind(this))
        g.AddText("x36 y473", "MIC tab key (optional)")
        this.FMicCanvas := g.AddHotkey("x36 y496 w143", "")
        g.AddText("x193 y498 w400 c596577", "Used only for MIC source. Set the tab's Set switch key first.")
        this.FPass := g.AddCheckBox("x660 y496 w260", "Pass trigger to game too")

        g.AddText("x36 y541", "Width px")
        this.FWidth := g.AddEdit("x36 y563 w75")
        g.AddText("x122 y541", "Opacity %")
        this.FOpacity := g.AddEdit("x122 y563 w83")
        g.AddText("x216 y541", "Position")
        this.FPosition := g.AddDropDownList("x216 y563 w129", ["TopRight", "TopLeft", "Center", "BottomRight", "BottomLeft"])
        g.AddText("x355 y541", "Offset X")
        this.FOffsetX := g.AddEdit("x355 y563 w72")
        g.AddText("x437 y541", "Offset Y")
        this.FOffsetY := g.AddEdit("x437 y563 w72")
        g.AddText("x519 y541", "Timed sec")
        this.FDuration := g.AddEdit("x519 y563 w74")
        g.AddButton("x611 y558 w138", "SAVE SLOT").OnEvent("Click", this.SaveSlot.Bind(this))
        g.AddButton("x764 y558 w175", "PREVIEW CURRENT EDITS").OnEvent("Click", this.TestSlot.Bind(this))
        g.AddButton("x36 y601 w260", "Advanced pictures / Library").OnEvent("Click", (*) => this.Pictures.Open(this.Selected))
        g.AddButton("x309 y601 w235", "Automatic overlay groups…").OnEvent("Click", this.GroupRoute.Open.Bind(this.GroupRoute))
        g.AddText("x555 y607 w375 c596577", "Optional display route. No new trigger or remapping.")
        ; Reuse the original controls/callbacks and retain a session-only Classic
        ; layout. This presentation service never saves or activates a feature.
        this.PictureEditor := StudioPictureEditor(this, g)
        this.Feedback.RegisterNew(g, "UI-101", this, ["List", "FName", "FEnabled", "FKey", "FSource", "FMode", "FFile", "FMicCanvas", "FPass", "FWidth", "FOpacity", "FPosition", "FOffsetX", "FOffsetY", "FDuration"])
        this.Feedback.RegisterNew(g, "UI-101", this.PictureEditor)

        ; Multi Image Canvas bridge UI.
        tabs.UseTab(2)
        this.MicIntro := g.AddText("x38 y115 w875 h45", "Multi Image Canvas has separate 'Overlay Show/Hide' and 'Set switch key' actions. This bridge lets Hold work without reWASD.")
        this.MicText := g.AddText("x38 y175 w870 h28", "Checking MultiImageCanvas.exe...")
        this.MicShortcutLabel := g.AddText("x38 y226", "MIC Overlay Show/Hide shortcut:")
        this.MicHotkeyField := g.AddHotkey("x38 y254 w200", this.MicToggle)
        this.MicSaveButton := g.AddButton("x253 y252 w215", "Save MIC shortcut")
        this.MicSaveButton.OnEvent("Click", this.SaveMicShortcut.Bind(this))
        this.MicShortcutHint := g.AddText("x38 y294 w845 c596577", "Default: Ctrl+Alt+H. It must match File > Settings > Key Bindings in Multi Image Canvas.")
        this.MicTestButton := g.AddButton("x38 y344 w210", "Test MIC toggle ON/OFF")
        this.MicTestButton.OnEvent("Click", this.ManualMicToggle.Bind(this))
        this.MicHiddenButton := g.AddButton("x264 y344 w220", "Mark MIC as hidden")
        this.MicHiddenButton.OnEvent("Click", this.MarkMicHidden.Bind(this))
        this.MicWebsiteButton := g.AddButton("x502 y344 w165", "Open MIC website")
        this.MicWebsiteButton.OnEvent("Click", (*) => Run("https://github.com/tokonoha00/Multi-image-canvas"))
        this.MicGuide := g.AddText("x38 y413 w840 h135", "TO CONFIGURE A MIC SLOT:`n" .
            "1. In MIC, create a canvas tab, load its picture, right-click tab > Set switch key (e.g. F15).`n" .
            "2. Here, on Picture buttons tab, set Source = MIC, Trigger key = F18, MIC tab key = F15, Mode = Hold.`n" .
            "3. Ensure MIC's overlay starts HIDDEN. Holding F18 then shows it; releasing F18 hides it.`n" .
            "IMPORTANT: MIC only has a toggle; changing MIC overlay manually can desynchronize this bridge.")
        this.MicLocalHint := g.AddText("x38 y574 w850 cAE4B27", "If you prefer reliable on/off without synchronization, choose Source = Local (built-in picture overlay).")
        ; Retain the old feedback identifiers despite naming the layout controls.
        this.Feedback.RegisterNew(g, "UI-105", {MicText: this.MicText, MicHotkeyField: this.MicHotkeyField})
        this.MicEditor := StudioMicEditor(this, g)
        this.Feedback.RegisterNew(g, "UI-105", this.MicEditor)

        ; Keyboard HUD and style controls.
        tabs.UseTab(3)
        this.HudEnabled := g.AddCheckBox("x37 y116 w540", "Enable on-screen keypress display (keyboard inputs)")
        g.AddText("x37 y159", "Show seconds")
        this.HudDuration := g.AddEdit("x37 y185 w112")
        g.AddText("x166 y159", "Font size")
        this.HudFont := g.AddEdit("x166 y185 w110")
        g.AddText("x292 y159", "Opacity %")
        this.HudOpacity := g.AddEdit("x292 y185 w112")
        g.AddText("x423 y159", "Position")
        this.HudPosition := g.AddDropDownList("x423 y185 w175", ["BottomRight", "TopRight", "TopLeft", "BottomLeft", "Center"])
        g.AddText("x623 y159", "Recent keys (1-6)")
        this.HudRecent := g.AddEdit("x623 y185 w117")
        g.AddText("x37 y238", "Text color (hex)")
        this.HudTextColor := g.AddEdit("x37 y263 w170")
        g.AddText("x226 y238", "Background color (hex)")
        this.HudBgColor := g.AddEdit("x226 y263 w170")
        this.HudIgnoreMods := g.AddCheckBox("x422 y267 w320", "Hide standalone Ctrl/Alt/Shift keys")
        g.AddButton("x37 y326 w177", "SAVE KEY DISPLAY").OnEvent("Click", this.SaveHud.Bind(this))
        g.AddButton("x232 y326 w150", "Test display").OnEvent("Click", this.TestHud.Bind(this))
        g.AddButton("x400 y326 w140", "Clear display").OnEvent("Click", this.ClearHud.Bind(this))
        this.HudLastKey := g.AddText("x37 y395 w850 h50", "Last key observed: none")
        g.AddText("x37 y468 w840 h130", "Shows keys from Windows, including Azeron buttons mapped to keyboard keys. Does NOT read Azeron hardware button IDs or its internal layers.`n`n" .
            "Choose your own color hex codes (e.g. FFFFFF / 202833). Key history is temporary in memory. The application does not save the full keyboard stream or send it online.")
        this.Feedback.RegisterNew(g, "UI-106", this, ["HudEnabled", "HudDuration", "HudFont", "HudOpacity", "HudPosition", "HudRecent", "HudTextColor", "HudBgColor", "HudIgnoreMods"])

        ; Activity and troubleshooting.
        tabs.UseTab(4)
        this.Diagnostics := g.AddText("x38 y115 w875 h62", "")
        this.LogEdit := g.AddEdit("x37 y195 w882 h321 ReadOnly -Wrap")
        g.AddButton("x38 y537 w150", "Pause / Resume").OnEvent("Click", this.TogglePaused.Bind(this))
        g.AddButton("x199 y537 w150", "Hide overlays").OnEvent("Click", this.HideAll.Bind(this))
        g.AddButton("x360 y537 w150", "Test key capture").OnEvent("Click", this.TestCapture.Bind(this))
        g.AddButton("x521 y537 w186", "Settings folder").OnEvent("Click", (*) => Run(this.Dir))
        g.AddButton("x718 y537 w198", "Copy diagnostics").OnEvent("Click", this.CopyDiagnostics.Bind(this))
        g.AddButton("x38 y578 w235", "Import old LayerPictures.ini").OnEvent("Click", this.ImportLegacy.Bind(this))
        g.AddButton("x292 y578 w225", "Create MIC Hold preset").OnEvent("Click", this.AddMicPreset.Bind(this))
        g.AddButton("x535 y578 w188", "Hebrew setup guide").OnEvent("Click", this.OpenGuide.Bind(this))
        g.AddText("x38 y614 w876 c596577", "Actions/errors only, not full keyboard history. Hide UI minimizes to the tray.")
        this.Feedback.RegisterNew(g, "UI-107", this, ["LogEdit"])

        this.GameInput.BuildGui(g, tabs)
        this.Feedback.RegisterNew(g, "UI-108", this.GameInput, ["Extended"])
        tabs.UseTab()
        this.BottomText := g.AddText("x23 y666 w715 h36 c36536B", "")
        this.HideButton := g.AddButton("x777 y661 w90", "Hide UI")
        this.HideButton.OnEvent("Click", this.HidePanel.Bind(this))
        this.ExitButton := g.AddButton("x879 y661 w77", "EXIT")
        this.ExitButton.OnEvent("Click", (*) => ExitApp())
        this.Feedback.RegisterNew(g, "UI-109", this)
        g.OnEvent("Close", this.HubBridge.ClosePanel.Bind(this.HubBridge))
        g.OnEvent("Escape", this.HidePanel.Bind(this))
        g.Opt("+MinSize700x733")
        g.OnEvent("Size", this.PictureEditor.OnSize.Bind(this.PictureEditor))
        tabs.OnEvent("Change", this.PictureEditor.Reflow.Bind(this.PictureEditor))
        this.RefreshList()
        this.ReadSlotFields(1)
        this.LoadHudFields()
        this.RefreshLogField()
        this.PictureEditor.Reflow()
    }

    BuildTray() {
        A_TrayMenu.Delete()
        A_TrayMenu.Add("Open control panel", this.ShowPanel.Bind(this))
        A_TrayMenu.Default := "Open control panel"
        A_TrayMenu.Add("Pause / Resume", this.TogglePaused.Bind(this))
        A_TrayMenu.Add("Hide overlays", this.HideAll.Bind(this))
        A_TrayMenu.Add("Test selected picture", this.TestSlot.Bind(this))
        this.GameInput.BuildTray()
        A_TrayMenu.Add()
        A_TrayMenu.Add("Exit completely", (*) => ExitApp())
    }

    ShowPanel(*) {
        if !this.HubBridge.Show() {
            this.Gui.Show()
            WinActivate("ahk_id " this.Gui.Hwnd)
        }
        this.RefreshStatus()
    }
    HidePanel(*) {
        if this.Capturing
            return
        this.Gui.Hide()
        this.WriteLog("Control panel hidden; background triggers remain " (this.Enabled ? "on" : "off") ".")
    }

    RefreshList() {
        this.Selecting := true
        this.List.Delete()
        for i, s in this.Slots {
            detail := s.Source = "MIC" ? (s.MicCanvas = "" ? "Current MIC tab" : "MIC: " s.MicCanvas) : (s.File = "" ? "(choose a picture)" : s.File)
            this.List.Add(, i, s.Enabled ? "YES" : "no", s.Name, s.Key, s.Source, s.Mode, detail)
        }
        if this.Selected > this.Slots.Length
            this.Selected := this.Slots.Length
        this.List.Modify(this.Selected, "Select Focus Vis")
        this.Selecting := false
    }

    SelectSlot(lv, row, selected) {
        if this.Selecting || !selected || row < 1 || row > this.Slots.Length
            return
        if row != this.Selected && !this.ConfirmDiscardDraft("Discard unsaved edits and select another picture?") {
            this.Selecting := true
            try {
                lv.Modify(row, "-Select")
                lv.Modify(this.Selected, "Select Focus Vis")
            } finally this.Selecting := false
            return
        }
        this.Selected := row
        this.ReadSlotFields(row)
        this.WriteLog("Selected slot " row ": " this.Slots[row].Name)
    }

    ReadSlotFields(i) {
        this.Pictures.Suspend()
        s := this.Slots[i]
        this.FName.Value := s.Name
        this.FEnabled.Value := s.Enabled
        this.FKey.Value := s.Key
        this.FSource.Choose(s.Source)
        this.FMode.Choose(s.Mode)
        this.FFile.Value := s.File
        this.FMicCanvas.Value := s.MicCanvas
        this.FWidth.Value := s.Width
        this.FOpacity.Value := s.Opacity
        this.FPosition.Choose(s.Position)
        this.FOffsetX.Value := s.OffsetX
        this.FOffsetY.Value := s.OffsetY
        this.FDuration.Value := s.Duration
        this.FPass.Value := s.Pass
        this.OnSourceChanged()
        if this.HasOwnProp("PictureEditor")
            this.PictureEditor.UpdateDraftStatus()
    }

    OnSourceChanged(*) {
        isLocal := this.FSource.Text = "Local"
        this.FFile.Enabled := isLocal
        this.FMicCanvas.Enabled := !isLocal
        if this.HasOwnProp("PictureEditor")
            this.PictureEditor.Reflow()
    }

    ReadCurrentSlot() {
        return {Enabled: this.FEnabled.Value, Name: this.FName.Value,
            Key: this.FKey.Value, Source: this.FSource.Text, Mode: this.FMode.Text,
            File: this.FFile.Value, MicCanvas: this.FMicCanvas.Value,
            Width: this.FWidth.Value, Opacity: this.FOpacity.Value,
            Position: this.FPosition.Text, OffsetX: this.FOffsetX.Value,
            OffsetY: this.FOffsetY.Value, Duration: this.FDuration.Value,
            Pass: this.FPass.Value}
    }

    SaveSlot(*) {
        copy := []
        for i, s in this.Slots {
            if i = this.Selected
                copy.Push(this.ReadCurrentSlot())
            else
                copy.Push(s.Clone())
        }
        try {
            this.ValidateAll(copy)
            this.UnbindAll()
            this.HideCurrent()
            this.Slots := copy
            this.Pictures.LegacyChanged(this.Selected)
            this.BindAll()
            this.SaveConfig()
            this.RefreshList()
            this.ReadSlotFields(this.Selected)
            this.WriteLog("Saved slot " this.Selected ": " this.Slots[this.Selected].Name)
        } catch Error as err {
            this.WriteLog("SLOT ERROR: " err.Message)
            MsgBox(err.Message "`n`nNo settings were changed.", "Invalid slot", "Iconx")
        }
    }

    AddSlot(*) {
        if this.Slots.Length >= 12 {
            MsgBox("Maximum 12 slots.")
            return
        }
        if !this.ConfirmDiscardDraft()
            return
        this.Slots.Push(this.NewSlot(this.Slots.Length + 1))
        this.Selected := this.Slots.Length
        this.SaveConfig()
        this.RefreshList()
        this.ReadSlotFields(this.Selected)
        this.WriteLog("Added disabled slot " this.Selected ".")
    }
    RemoveSlot(*) {
        if this.Slots.Length <= 1 {
            MsgBox("At least one slot must remain.")
            return
        }
        if MsgBox("Remove slot " this.Selected "? Its saved settings will be deleted.",
            "Remove slot", "YesNo Icon?") != "Yes"
            return
        this.HideCurrent(), this.UnbindAll()
        this.Slots.RemoveAt(this.Selected)
        this.Pictures.LegacyChanged(0, true)
        this.Selected := Min(this.Selected, this.Slots.Length)
        this.BindAll(), this.SaveConfig()
        this.RefreshList(), this.ReadSlotFields(this.Selected)
        this.WriteLog("Removed a slot.")
    }

    BrowsePicture(*) {
        chosenImageFile := FileSelect(1, , "Choose your picture", "Images (*.png; *.jpg; *.jpeg; *.bmp; *.gif; *.tif; *.tiff)")
        if chosenImageFile != "" {
            this.FFile.Value := chosenImageFile
            this.FSource.Choose("Local")
            this.FEnabled.Value := 1
            this.OnSourceChanged()
        }
    }

    RecordKey(*) {
        if this.DesktopTest {
            MsgBox("Physical key capture is disabled in this isolated UI test.")
            return
        }
        this.HideCurrent()
        this.UnbindAll()
        this.StopKeyDisplay()
        this.Capturing := true
        cap := Gui("+AlwaysOnTop -MinimizeBox", "Record a trigger key")
        cap.SetFont("s12", "Segoe UI")
        cap.AddText("x24 y20 w405 h56", "Press the physical keyboard/Azeron key now.`nEscape cancels. Timeout: 8 seconds.")
        cap.Show("w453 h102")
        key := ""
        try {
            ih := InputHook("T8 V L0")
            ih.KeyOpt("{All}", "E")
            ih.Start()
            ih.Wait()
            key := ih.EndReason = "EndKey" ? ih.EndKey : ""
        } catch Error as err
            this.WriteLog("Key recording error: " err.Message)
        cap.Destroy()
        this.Capturing := false
        this.BindAll()
        this.StartKeyDisplay()
        if key != "" && key != "Escape" {
            this.FKey.Value := key
            this.WriteLog("Recorded trigger: " key " (press SAVE SLOT to apply).")
        } else
            this.WriteLog("Key recording cancelled or timed out.")
    }

    TestCapture(*) {
        this.Tabs.Choose(1)
        this.RecordKey()
        this.Tabs.Choose(4)
    }

    BindAll() {
        if this.DesktopTest || !this.Enabled || this.Capturing
            return
        try {
            for i, s in this.Slots {
                if !s.Enabled
                    continue
                key := (s.Pass ? "~" : "") "*" s.Key
                Hotkey(key, this.KeyDown.Bind(this, i), "On")
                this.Bound.Push(key)
                up := key " Up"
                Hotkey(up, this.KeyUp.Bind(this, i), "On")
                this.Bound.Push(up)
            }
            this.WriteLog("Bound " (this.Bound.Length // 2) " triggers.")
        } catch Error as err {
            this.UnbindAll()
            this.Enabled := false
            this.WriteLog("BIND ERROR: " err.Message)
            MsgBox("A hotkey could not be registered:`n" err.Message,
                "Azeron Overlay Studio", "Iconx")
        }
    }

    UnbindAll() {
        this.GameInput.StopForHost()
        if this.HasOwnProp("GroupRoute") && this.GroupRoute.HasOwnProp("Alternate")
            this.GroupRoute.Alternate.Reset()
        for key in this.Bound
            try Hotkey(key, "Off")
        this.Bound := []
        this.Pressed := Map()
    }

    KeyDown(i, *) {
        Critical()
        if !this.Enabled || this.Pressed.Has(i)
            return
        this.Pressed[i] := 0  ; Ignore repeated key-down until an up event.
        this.GroupRoute.AlternateDown(i)
        timedOverlay := this.HasOwnProp("GroupRoute") && HasMethod(this.GroupRoute, "NowMs")
            && this.GroupRoute.Enabled && i = this.GroupRoute.Slot
        overlayReceivedUtc := timedOverlay ? this.GroupRoute.NowMs() : 0
        try s := this.Pictures.ResolveSlot(i, 0, true)
        catch Error as err {
            this.HideCurrent()
            this.GroupRoute.CapturePending(i)
            this.WriteLog("PICTURE ROUTING REFUSED: " err.Message)
            return
        }
        this.TotalEvents += 1
        this.LastEvent := "DOWN " s.Key " -> " s.Name
        this.WriteLog("DOWN " s.Key " / slot " i " / " s.Mode)
        if s.Mode = "Toggle" && this.Current = i {
            this.HideCurrent(true)
            return
        }
        if s.Mode = "Hold" && this.Current = i && this.GroupRoute.KeepForLayer(i) {
            ; The native layer already owns this same frame: add the physical
            ; key's hold without hiding/recreating it or restarting its fade.
            token := this.ShowLocal(s, true) ? this.Generation : 0
            if !token
                this.HideCurrent()
        } else
            token := this.ShowSlot(i, s)
        this.Pressed[i] := {Token: token, Mode: s.Mode}
        if timedOverlay
            this.WriteLog("OVERLAY KEY TIMING: received_utc_ms=" overlayReceivedUtc
                . " handler_ms=" (this.GroupRoute.NowMs() - overlayReceivedUtc)
                . " result=" (token ? "frame_prepared" : "not_shown")
                . " fade_ms=" (s.HasOwnProp("FadeInMs") ? s.FadeInMs : 0))
        if token && s.Mode = "Timed"
            this.ArmHide(token, s.Duration)
    }

    KeyUp(i, *) {
        Critical()
        if !this.Pressed.Has(i)
            return
        pressed := this.Pressed[i]
        token := IsObject(pressed) ? pressed.Token : 0
        this.Pressed.Delete(i)
        this.GroupRoute.AlternateUp(i)
        s := this.Slots[i]  ; Release uses the actual DOWN snapshot, not a new context match.
        this.TotalEvents += 1
        this.LastEvent := "UP " s.Key " -> " s.Name
        this.WriteLog("UP " s.Key " / slot " i)
        if IsObject(pressed) && pressed.Mode = "Hold" && token && token = this.Generation && this.Current = i
            && !this.GroupRoute.KeepForLayer(i)
            this.HideCurrent(true)
    }

    ShowSlot(i, resolvedSlot := 0) {
        try s := IsObject(resolvedSlot) ? resolvedSlot : this.Pictures.ResolveSlot(i, 0, true)
        catch Error as err {
            this.HideCurrent()
            this.WriteLog("PICTURE ROUTING REFUSED: " err.Message)
            return 0
        }
        keepFade := s.Source = "Local" && s.HasOwnProp("PreserveAlpha") && s.PreserveAlpha && this.Fade.Hiding
        this.HideCurrent(false, keepFade)
        if s.Source = "Local" {
            if !this.ShowLocal(s, keepFade)
                return 0
        } else {
            if !this.ShowMIC(s)
                return 0
        }
        this.Current := i
        this.Generation += 1
        this.WriteLog("VISIBLE: slot " i " / " s.Name)
        return this.Generation
    }

    ShowLocal(s, reuse := false) {
        if !FileExist(s.File) || DirExist(s.File) {
            this.WriteLog("IMAGE MISSING: " s.File)
            TrayTip("Image missing. Open Picture buttons and select a file.", "Azeron Overlay Studio", "Icon!")
            return false
        }
        g := 0
        timedDraw := s.HasOwnProp("RouteSlot") && this.HasOwnProp("GroupRoute") && HasMethod(this.GroupRoute, "NowMs")
        drawStartedUtc := timedDraw ? this.GroupRoute.NowMs() : 0
        try {
            geometry := this.Pictures.Geometry(s)
            layoutDoneUtc := timedDraw ? this.GroupRoute.NowMs() : 0
            if s.HasOwnProp("PreserveAlpha") && s.PreserveAlpha {
                previous := reuse ? this.PictureGui : 0
                g := this.Fade.Show(s, geometry, this.PictureAlpha ? previous : 0)
                if previous && previous.Hwnd != g.Hwnd
                    PM_AlphaFrame.Dispose(previous)
                this.PictureGui := g
                this.PictureAlpha := true
                if timedDraw
                    this.WriteLog("OVERLAY DRAW TIMING: layout_ms=" (layoutDoneUtc - drawStartedUtc)
                        . " prepare_present_ms=" (this.GroupRoute.NowMs() - layoutDoneUtc))
                return true
            }
            g := Gui("-Caption +ToolWindow +AlwaysOnTop -DPIScale +E0x08000020", "Azeron picture")
            g.MarginX := 0, g.MarginY := 0
            g.BackColor := "202833"
            w := geometry.w, h := geometry.h
            pic := g.AddPicture("x0 y0 w" w " h" h, s.File)
            if w < 1 || h < 1
                throw Error("The picture has an invalid display size.")
            x := geometry.x, y := geometry.y
            g.Show("NA x" x " y" y " w" w " h" h)
            WinSetTransparent(Round(Integer(s.Opacity) * 255 / 100), "ahk_id " g.Hwnd)
            this.PictureGui := g
            this.PictureAlpha := false
            return true
        } catch Error as err {
            if g
                try g.Destroy()
            this.WriteLog("IMAGE DISPLAY ERROR: " err.Message)
            TrayTip(err.Message, "Azeron Overlay Studio", "Icon!")
            return false
        }
    }

    ShowMIC(s) {
        if this.DesktopTest
            return false
        if !ProcessExist("MultiImageCanvas.exe") {
            this.WriteLog("MIC ERROR: MultiImageCanvas.exe is not running.")
            TrayTip("Start Multi Image Canvas first (its overlay should start hidden).",
                "Azeron Overlay Studio", "Icon!")
            return false
        }
        try {
            if s.MicCanvas != "" {
                SendEvent(this.ComboToSend(s.MicCanvas))
                Sleep(70)
            }
            SendEvent(this.ComboToSend(this.MicToggle))
            this.MicVisibleByUs := true
            return true
        } catch Error as err {
            this.WriteLog("MIC send error: " err.Message)
            return false
        }
    }

    HideCurrent(animate := false, keepPicture := false, *) {
        Critical()
        if this.HasOwnProp("GroupRoute")
            this.GroupRoute.CancelPending()
        this.Generation += 1
        if this.HideTimer {
            SetTimer(this.HideTimer, 0)
            this.HideTimer := 0
        }
        if !keepPicture {
            if Type(animate) = "Integer" && animate = true
                this.Fade.Hide()
            else
                this.Fade.Close()
            if this.PictureGui && !this.Fade.Window {
                this.PictureGui.Destroy()
                this.PictureGui := 0
            }
            if !this.PictureGui
                this.PictureAlpha := false
        }
        if this.MicVisibleByUs {
            if ProcessExist("MultiImageCanvas.exe") {
                try SendEvent(this.ComboToSend(this.MicToggle))
                catch Error as err
                    this.WriteLog("MIC hide error: " err.Message)
            }
            this.MicVisibleByUs := false
        }
        if this.Current {
            this.WriteLog("HIDDEN: slot " this.Current)
            this.Current := 0
        }
    }

    HideAll(*) {
        this.HideCurrent()
        this.Pictures.Suspend()
        this.ClearHud()
        this.WriteLog("Hide all requested.")
    }

    ArmHide(token, seconds) {
        this.HideTimer := this.Expire.Bind(this, token)
        SetTimer(this.HideTimer, -Round(Number(seconds) * 1000))
    }
    Expire(token) {
        if this.Current && this.Generation = token
            this.HideCurrent(true)
    }

    TestSlot(*) {
        if !this.Slots.Has(this.Selected)
            return
        s := this.ReadCurrentSlot()
        if s.Source = "Local" {
            try this.Pictures.RenderPreview(this.Selected, s)
            catch Error as err
                MsgBox(err.Message, "Picture preview", "Icon!")
            return
        }
        ; MIC is an explicit external shortcut test, not a local draft preview.
        token := this.ShowSlot(this.Selected)
        if token {
            this.ArmHide(token, 2)
            this.WriteLog("Manual preview: slot " this.Selected " (2 seconds).")
        }
    }

    TogglePaused(*) {
        this.Pictures.Suspend()
        this.HideCurrent()
        this.UnbindAll()
        this.Enabled := !this.Enabled
        if this.Enabled {
            this.BindAll()
            this.StartKeyDisplay()
        } else {
            this.StopKeyDisplay()
            this.ClearHud()
        }
        this.SaveConfig()
        this.WriteLog(this.Enabled ? "RESUMED: triggers active." : "PAUSED: triggers disabled.")
        this.RefreshStatus()
        A_IconTip := "Azeron Overlay Studio - " (this.Enabled ? "RUNNING" : "PAUSED")
    }

    SaveMicShortcut(*) {
        combo := this.MicEditor.ReadShortcut()
        if !this.ValidCombo(combo) {
            MsgBox("Record one complete keyboard shortcut, such as Ctrl+Alt+H or F19.")
            return
        }
        if this.MicVisibleByUs
            this.HideCurrent()
        this.GameInput.StopForHost()
        this.MicToggle := combo
        this.SaveConfig()
        this.WriteLog("MIC toggle shortcut saved: " combo)
        this.MicEditor.UpdateDraftStatus()
    }

    ManualMicToggle(*) {
        if this.DesktopTest {
            MsgBox("External MIC shortcut tests are disabled in this isolated UI test.")
            return
        }
        if !ProcessExist("MultiImageCanvas.exe") {
            this.WriteLog("MIC not running. Nothing sent.")
            MsgBox("Open Multi Image Canvas before testing.")
            return
        }
        SendEvent(this.ComboToSend(this.MicToggle))
        ; A direct manual toggle makes our previous automatic assumption invalid.
        this.MicVisibleByUs := false
        this.Current := 0
        this.WriteLog("Sent MIC toggle manually. Use Mark hidden only when the overlay is actually hidden.")
    }

    MarkMicHidden(*) {
        this.MicVisibleByUs := false
        if this.Current && this.Slots[this.Current].Source = "MIC"
            this.Current := 0
        this.WriteLog("MIC synchronization reset: marked HIDDEN (no key sent).")
    }

    LoadHudFields() {
        h := this.Hud
        this.HudEnabled.Value := Integer(h.Enabled)
        this.HudDuration.Value := h.Duration
        this.HudFont.Value := h.FontSize
        this.HudOpacity.Value := h.Opacity
        this.HudPosition.Choose(h.Position)
        this.HudRecent.Value := h.Recent
        this.HudTextColor.Value := h.TextColor
        this.HudBgColor.Value := h.BgColor
        this.HudIgnoreMods.Value := Integer(h.IgnoreMods)
    }

    ValidateHud(h) {
        if !IsNumber(h.Duration) || Number(h.Duration) < 0.3 || Number(h.Duration) > 15
            throw Error("Key display duration must be 0.3-15 seconds.")
        if !this.IsWhole(h.FontSize, 12, 60) || !this.IsWhole(h.Opacity, 5, 100)
            throw Error("Key display font 12-60, opacity 5-100.")
        if !this.IsWhole(h.Recent, 1, 6)
            throw Error("Recent keys must be 1-6.")
        if !InStr("|TopRight|TopLeft|Center|BottomRight|BottomLeft|", "|" h.Position "|")
            throw Error("Invalid key display position.")
        if !RegExMatch(h.TextColor, "i)^[0-9a-f]{6}$") || !RegExMatch(h.BgColor, "i)^[0-9a-f]{6}$")
            throw Error("Enter colors as 6 hexadecimal digits, without # (e.g. FFFFFF).")
        h.FontSize := Integer(h.FontSize), h.Opacity := Integer(h.Opacity)
        h.Recent := Integer(h.Recent), h.Duration := Number(h.Duration)
        h.Enabled := Integer(h.Enabled) != 0 ? 1 : 0
        h.IgnoreMods := Integer(h.IgnoreMods) != 0 ? 1 : 0
        h.TextColor := StrUpper(h.TextColor), h.BgColor := StrUpper(h.BgColor)
    }

    SaveHud(*) {
        h := {Enabled: this.HudEnabled.Value, Duration: this.HudDuration.Value,
            FontSize: this.HudFont.Value, Opacity: this.HudOpacity.Value,
            Position: this.HudPosition.Text, Recent: this.HudRecent.Value,
            TextColor: Trim(this.HudTextColor.Value), BgColor: Trim(this.HudBgColor.Value),
            IgnoreMods: this.HudIgnoreMods.Value}
        try this.ValidateHud(h)
        catch Error as err {
            MsgBox(err.Message, "Key display settings", "Iconx")
            return
        }
        this.StopKeyDisplay(), this.DestroyHUD()
        this.Hud := h
        this.SaveConfig()
        this.StartKeyDisplay()
        this.LoadHudFields()
        this.WriteLog(h.Enabled ? "Key display ENABLED." : "Key display DISABLED.")
    }

    StartKeyDisplay() {
        if this.DesktopTest
            return
        if !this.Hud.Enabled || !this.Enabled || this.Capturing || this.KeyHook
            return
        try {
            ih := InputHook("V L0")
            ih.MinSendLevel := 1  ; Do not re-display this script's SendEvent outputs.
            ih.KeyOpt("{All}", "N")
            ih.OnKeyDown := this.HudDownEvent.Bind(this)
            ih.OnKeyUp := this.HudUpEvent.Bind(this)
            ih.Start()
            this.KeyHook := ih
            this.WriteLog("Key display started (keyboard events, no disk recording).")
        } catch Error as err
            this.WriteLog("Key display error: " err.Message)
    }
    StopKeyDisplay() {
        if this.KeyHook {
            try this.KeyHook.Stop()
            this.KeyHook := 0
        }
        this.HudDown := Map()
    }

    HudDownEvent(ih, vk, sc) {
        code := vk ":" sc
        if this.HudDown.Has(code)
            return
        this.HudDown[code] := true
        name := GetKeyName(Format("vk{:X}sc{:X}", vk, sc))
        if name = ""
            name := Format("VK{:02X}", vk)
        if this.Hud.IgnoreMods && RegExMatch(name, "i)^(?:L|R)?(?:Shift|Ctrl|Control|Alt|Win)$")
            return
        this.HudLastKey.Text := "Last key observed: " name
        this.AddHudEntry(name)
    }
    HudUpEvent(ih, vk, sc) {
        code := vk ":" sc
        if this.HudDown.Has(code)
            this.HudDown.Delete(code)
    }

    AddHudEntry(textValue) {
        this.HudHistory.Push({Text: textValue, Time: A_TickCount})
        while this.HudHistory.Length > Integer(this.Hud.Recent)
            this.HudHistory.RemoveAt(1)
        this.HudDirty := true
    }

    TestHud(*) {
        if !Integer(this.Hud.Enabled) {
            MsgBox("Enable the key display and press SAVE KEY DISPLAY first.")
            return
        }
        this.AddHudEntry("F14  [TEST]")
        this.HudRefresh()
        this.WriteLog("Key display preview shown.")
    }

    ClearHud(*) {
        this.HudHistory := []
        this.HudDirty := true
        if this.HudGui
            this.HudGui.Hide()
    }

    DestroyHUD() {
        if this.HudGui {
            this.HudGui.Destroy()
            this.HudGui := 0
            this.HudLabel := 0
        }
        this.HudHistory := []
    }

    HudRefresh() {
        if !this.Hud.Enabled
            return
        remaining := []
        for e in this.HudHistory {
            if A_TickCount - e.Time < Number(this.Hud.Duration) * 1000
                remaining.Push(e)
        }
        if remaining.Length != this.HudHistory.Length
            this.HudDirty := true
        this.HudHistory := remaining
        if !remaining.Length {
            if this.HudGui
                this.HudGui.Hide()
            return
        }
        if !this.HudDirty
            return
        this.HudDirty := false
        try {
            if !this.HudGui {
                g := Gui("-Caption +AlwaysOnTop +ToolWindow -DPIScale +E0x08000020", "Keypress HUD")
                g.MarginX := 0, g.MarginY := 0, g.BackColor := this.Hud.BgColor
                g.SetFont("s" this.Hud.FontSize " c" this.Hud.TextColor, "Segoe UI Semibold")
                this.HudLabel := g.AddText("x12 y10 w360 h250 BackgroundTrans", "")
                this.HudGui := g
            }
            displayed := ""
            for e in remaining
                displayed .= (displayed = "" ? "" : "`n") e.Text
            this.HudLabel.Text := displayed
            width := 384
            height := 18 + remaining.Length * (Integer(this.Hud.FontSize) + 13)
            this.HudLabel.Move(12, 9, width - 24, height - 14)
            MonitorGet(MonitorGetPrimary(), &left, &top, &right, &bottom)
            pos := this.Hud.Position
            x := InStr(pos, "Right") ? right - width - 28 : left + 28
            y := InStr(pos, "Bottom") ? bottom - height - 40 : top + 34
            if pos = "Center"
                x := left + (right - left - width) // 2, y := top + (bottom - top - height) // 2
            this.HudGui.Show("NA x" x " y" y " w" width " h" height)
            WinSetTransparent(Round(Number(this.Hud.Opacity) * 255 / 100), "ahk_id " this.HudGui.Hwnd)
        } catch Error as err {
            this.WriteLog("Key display draw error: " err.Message)
            this.Hud.Enabled := 0
            this.StopKeyDisplay()
            this.DestroyHUD()
        }
    }

    Tick(*) {
        this.HudRefresh()
        if this.HasOwnProp("LogDirty") && this.LogDirty && this.Gui && this.Tabs.Value = 4
            this.RefreshLogField()
        ; Refreshing the status around once per second avoids excessive GUI updates.
        if !this.HasOwnProp("LastTickStatus") || (A_TickCount - this.LastTickStatus) >= 1000 {
            this.LastTickStatus := A_TickCount
            this.RefreshStatus()
            this.WriteRuntimeStatus()
        }
    }

    WriteRuntimeStatus() {
        ; A bounded readiness receipt, never a keystroke log. Runs on the UI
        ; maintenance tick, not inside trigger/layer/fade handling.
        try {
            route := this.GroupRoute
            slot := route.Slot
            trigger := slot >= 1 && slot <= this.Slots.Length ? this.Slots[slot] : 0
            temp := this.Dir "\runtime-status.pending-" DllCall("GetCurrentProcessId", "uint")
            if FileExist(temp)
                FileDelete(temp)
            now := DateDiff(A_NowUTC, "19700101000000", "Seconds")
            for key, value in Map("Schema", 1, "PID", DllCall("GetCurrentProcessId", "uint"),
                "AtUnix", now, "Enabled", this.Enabled ? 1 : 0, "BoundTriggers", this.Bound.Length // 2,
                "OverlayTrigger", trigger && trigger.Enabled && trigger.Mode = "Hold" ? 1 : 0,
                "TriggerKey", trigger ? trigger.Key : "", "RouteEnabled", route.Enabled ? 1 : 0,
                "RoutePath", route.Path, "SettingsFile", this.Config,
                "SettingsSHA256", this.LoadedSettingsSHA, "LoadError", this.SettingsLoadError)
                IniWrite(StrReplace(StrReplace(value "", "`r", " "), "`n", " "), temp, "Runtime", key)
            FileMove(temp, this.Dir "\runtime-status.ini", 1)
        }
    }

    RefreshStatus() {
        this.GameInput.RefreshUi()
        state := this.Enabled ? "ACTIVE" : "PAUSED"
        current := this.Current ? ("Showing " this.Slots[this.Current].Name) : "No picture visible"
        this.RunText.Text := "● " state "  |  " (this.Bound.Length // 2) " enabled keys  |  " current "  |  " this.TotalEvents " input events"
        this.BottomText.Text := "Running in tray  |  Last event: " this.LastEvent
        mic := ProcessExist("MultiImageCanvas.exe") ? "RUNNING" : "NOT RUNNING"
        this.MicText.Text := "Multi Image Canvas process: " mic "  |  Sent by bridge: " (this.MicVisibleByUs ? "ON" : "OFF/unknown")
        this.Diagnostics.Text := "State: " state "  |  Bound triggers: " (this.Bound.Length // 2) .
            "  |  Active slot: " (this.Current ? this.Current : "none") "  |  MIC: " mic .
            "`nLatest input: " this.LastEvent "  |  Event count: " this.TotalEvents
    }

    WriteLog(message) {
        entry := "[" FormatTime(A_Now, "HH:mm:ss") "." Format("{:03}", A_MSec) "] " message
        this.LogLines.Push(entry)
        while this.LogLines.Length > 70
            this.LogLines.RemoveAt(1)
        ; Do not synchronously rebuild a hidden edit control inside a hotkey,
        ; fade or layer-swap critical section. The existing UI tick refreshes
        ; the Status tab; the bounded in-memory log remains current immediately.
        this.LogDirty := true
    }
    RefreshLogField() {
        content := ""
        for entry in this.LogLines
            content .= entry "`r`n"
        this.LogEdit.Value := content
        this.LogDirty := false
    }
    CopyDiagnostics(*) {
        report := "Azeron Overlay Studio " this.Version " / AHK " A_AhkVersion " / Windows " A_OSVersion "`r`n" .
            "Enabled=" this.Enabled ", bound=" (this.Bound.Length // 2) .
            ", MIC=" (ProcessExist("MultiImageCanvas.exe") ? "running" : "closed") "`r`n" .
            "Last=" this.LastEvent "`r`n"
        for entry in this.LogLines
            report .= entry "`r`n"
        A_Clipboard := report
        this.WriteLog("Diagnostics copied to clipboard (without image paths or full keyboard history).")
    }


    OpenGuide(*) {
        path := A_ScriptDir "\Setup_HE.html"
        if FileExist(path)
            Run(path)
        else
            MsgBox("Setup_HE.html not found. Extract the entire ZIP to one folder, or open README_HE.md.")
    }

    ImportLegacy(*) {
        legacyIniFile := FileSelect(1, , "Select your old LayerPictures.ini", "INI settings (*.ini)")
        if legacyIniFile = ""
            return
        if MsgBox("Importing will REPLACE current picture slots. Continue?", "Import old settings", "YesNo Icon?") != "Yes"
            return
        imported := []
        SplitPath(legacyIniFile, , &iniDir)
        Loop 4 {
            n := A_Index
            slot := this.NewSlot(n)
            slot.Name := "Imported picture " n
            for property in ["File", "Key", "Mode", "Opacity", "Width", "Position", "Duration", "Pass"] {
                try slot.%property% := IniRead(legacyIniFile, "Slot" n, property, slot.%property%)
            }
            if slot.File != "" && !RegExMatch(slot.File, "i)^(?:[a-z]:[\\]|\\\\)")
                slot.File := iniDir "\" slot.File
            slot.Enabled := slot.File != "" && FileExist(slot.File) && !DirExist(slot.File) ? 1 : 0
            imported.Push(slot)
        }
        try this.ValidateAll(imported)
        catch Error as err {
            MsgBox("Could not import settings:`n" err.Message, "Import settings", "Iconx")
            return
        }
        this.UnbindAll(), this.HideCurrent()
        this.Slots := imported, this.Selected := 1
        this.Pictures.LegacyChanged(0, true)
        this.BindAll(), this.SaveConfig(), this.RefreshList(), this.ReadSlotFields(1)
        this.Tabs.Choose(1)
        this.WriteLog("Imported previous LayerPictures.ini: " file)
        MsgBox("Imported four slots. Missing images stay disabled. Review the rows and test them.")
    }

    AddMicPreset(*) {
        index := 0
        for i, s in this.Slots {
            if !s.Enabled {
                index := i
                break
            }
        }
        if !index {
            if this.Slots.Length >= 12 {
                MsgBox("No free slot. Disable an existing slot or remove one.")
                return
            }
            this.Slots.Push(this.NewSlot(this.Slots.Length + 1))
            index := this.Slots.Length
        }
        key := ""
        for candidate in ["F18", "F19", "F20", "F21", "F22", "F23", "F24", "F14"] {
            used := false
            for s in this.Slots {
                if s.Enabled && StrLower(s.Key) = StrLower(candidate) {
                    used := true
                    break
                }
            }
            if !used {
                key := candidate
                break
            }
        }
        if key = "" {
            MsgBox("F14 and F18-F24 are already in use. Choose a free trigger key manually.")
            return
        }
        slot := this.NewSlot(index)
        slot.Enabled := 1, slot.Source := "MIC", slot.Mode := "Hold"
        slot.Key := key, slot.MicCanvas := "", slot.Name := "MIC hold (" key ")"
        this.Slots[index] := slot
        this.Pictures.LegacyChanged(index, false, true)
        this.Selected := index
        this.UnbindAll(), this.HideCurrent()
        this.BindAll(), this.SaveConfig(), this.RefreshList(), this.ReadSlotFields(index)
        this.Tabs.Choose(1)
        this.WriteLog("Created MIC Hold preset on " key ". MIC must be running with overlay initially hidden.")
        MsgBox("MIC Hold preset created using " key ".`n`n" .
            "1. Keep Multi Image Canvas open (overlay initially HIDDEN).`n" .
            "2. Press and hold " key " (or map an Azeron button to it).`n" .
            "3. Release to hide.", "MIC preset")
    }

    Shutdown(*) {
        this.Feedback.Shutdown()
        this.HubBridge.Shutdown()
        this.GroupRoute.Shutdown()
        this.Pictures.Shutdown()
        this.GameInput.StopForHost()
        SetTimer(this.TickFn, 0)
        this.HideCurrent()
        PM_PreparedSurfaceCache.Clear()
        this.StopKeyDisplay()
        this.DestroyHUD()
        this.UnbindAll()
    }

    ConfirmDiscardDraft(question := "This slot has unsaved edits. Discard them and add a new slot?") {
        draft := this.ReadCurrentSlot()
        for field, value in this.Slots[this.Selected].OwnProps() {
            if (draft.%field% "") != (value "")
                return MsgBox(question, "Unsaved picture edits", "YesNo Icon?") = "Yes"
        }
        return true
    }
}
