#Requires AutoHotkey v2.0
#SingleInstance Force
; Layer Pictures 1.0 - Windows / AutoHotkey v2.
; Right-click the tray icon for Settings, Preview, disable, or Exit.
; Local settings only. No recording, networking, remapping, or elevation.
; A borderless/windowed game is required; exclusive fullscreen is unsupported.
; One picture at a time: the latest key wins. Hold mode does not restore old pictures.
Persistent()
app := LayerPictures()

class LayerPictures {
    __New() {
        this.Config := A_ScriptDir "\LayerPictures.ini"
        this.Slots := this.Defaults(), this.Bound := [], this.Pressed := Map()
        this.Overlay := 0, this.Current := 0, this.Generation := 0, this.Timer := 0
        this.Enabled := true, this.Editor := 0, this.Fields := []
        try {
            for i, slot in this.Slots
                for field, value in slot.OwnProps()
                    slot.%field% := IniRead(this.Config, "Slot" i, field, value)
            this.Validate(this.Slots, false)
        } catch Error as err {
            this.Slots := this.Defaults()
            TrayTip("Could not read settings. Defaults loaded; your INI was not changed.`n" err.Message, "Layer Pictures", "Icon!")
        }
        A_IconTip := "Layer Pictures - right-click for Settings"
        A_TrayMenu.Delete()
        A_TrayMenu.Add("Settings...", this.Settings.Bind(this))
        A_TrayMenu.Add("Hide picture", this.Hide.Bind(this))
        A_TrayMenu.Add("Overlays enabled", this.ToggleEnabled.Bind(this))
        A_TrayMenu.Check("Overlays enabled")
        A_TrayMenu.Add()
        Loop 4
            A_TrayMenu.Add("Preview saved slot " A_Index, this.Preview.Bind(this, A_Index))
        A_TrayMenu.Add()
        A_TrayMenu.Add("Exit", (*) => ExitApp())
        A_TrayMenu.Default := "Settings..."
        OnExit(this.Cleanup.Bind(this))
        this.Resume()
    }

    Defaults() {
        slots := []
        Loop 4
            slots.Push({File: "", Key: "F" (13 + A_Index), Mode: "Toggle", Opacity: 75,
                Width: 800, Position: "TopRight", Duration: 2, Pass: 0})
        return slots
    }

    Validate(slots, checkFiles := true) {
        seen := Map()
        for i, s in slots {
            s.Key := Trim(s.Key)
            if !RegExMatch(s.Key, "i)^[a-z0-9]+$")
                throw Error("Slot " i ": enter one key name, for example F14, Space, or NumpadAdd.")
            key := GetKeyName(s.Key)
            if key = "" || RegExMatch(key, "i)^(?:[LRM]Button|XButton[12]|Wheel.*|Joy.*|Ctrl|Control|Alt|Shift|Win)$")
                throw Error("Slot " i ": use a keyboard key; use LShift/RShift for a specific modifier.")
            if seen.Has(StrLower(key))
                throw Error("Slots " seen[StrLower(key)] " and " i " use the same key.")
            seen[StrLower(key)] := i, s.Key := key
            if !InStr("|Toggle|Hold|Timed|", "|" s.Mode "|")
                throw Error("Slot " i ": select Toggle, Hold, or Timed.")
            if !InStr("|TopLeft|TopRight|Center|BottomLeft|BottomRight|", "|" s.Position "|")
                throw Error("Slot " i ": select a listed position.")
            if !RegExMatch(s.Opacity "", "^\d+$") || s.Opacity < 1 || s.Opacity > 100
                throw Error("Slot " i ": opacity must be a whole number from 1 to 100.")
            if !RegExMatch(s.Width "", "^\d+$") || s.Width < 64 || s.Width > 8000
                throw Error("Slot " i ": width must be a whole number from 64 to 8000 pixels.")
            if !RegExMatch(s.Duration "", "^\d+(?:\.\d{1,3})?$") || s.Duration < 0.1 || s.Duration > 60
                throw Error("Slot " i ": duration must be 0.1 to 60 seconds.")
            if s.Pass != 0 && s.Pass != 1
                throw Error("Slot " i ": pass-through must be 0 or 1.")
            s.Opacity := Integer(s.Opacity), s.Width := Integer(s.Width)
            s.Duration := Number(s.Duration), s.Pass := Integer(s.Pass)
            s.File := Trim(s.File)
            if s.File = ""
                continue
            if InStr(s.File, "`n") || InStr(s.File, "`r") || RegExMatch(s.File, "i)^(?:\\\\|https?://)")
                throw Error("Slot " i ": select a local image file.")
            if !RegExMatch(s.File, "i)\.(?:png|jpe?g|bmp|gif|tiff?)$")
                throw Error("Slot " i ": supported files are PNG, JPG, BMP, GIF, and TIF.")
            if checkFiles && (!FileExist(this.Path(s.File)) || DirExist(this.Path(s.File)))
                throw Error("Slot " i ": the image file does not exist.")
        }
    }

    Path(file) => RegExMatch(file, "i)^[a-z]:[\\/]") ? file : A_ScriptDir "\" file

    BindKeys(slots, enable := true) {
        this.Unbind()
        try {
            for i, s in slots {
                if s.File = ""
                    continue ; Empty slots never consume their assigned key.
                key := (s.Pass ? "~" : "") "*" s.Key
                Hotkey(key, this.Down.Bind(this, i), enable ? "On" : "Off")
                this.Bound.Push(key)
                Hotkey(key " Up", this.Up.Bind(this, i), enable ? "On" : "Off")
                this.Bound.Push(key " Up")
            }
        } catch Error as err {
            this.Unbind()
            throw err
        }
    }

    Unbind() {
        for key in this.Bound
            Hotkey(key, "Off")
        this.Bound := [], this.Pressed := Map()
    }

    Resume() {
        if !this.Enabled || this.Editor
            return
        try this.BindKeys(this.Slots)
        catch Error as err {
            this.Enabled := false
            A_TrayMenu.Uncheck("Overlays enabled")
            TrayTip("Bindings disabled: " err.Message, "Layer Pictures", "Icon!")
        }
    }

    Down(i, *) {
        Critical()
        if !this.Enabled || this.Editor || this.Pressed.Has(i)
            return
        this.Pressed[i] := 0 ; Suppress OS key-repeat until this key is released.
        s := this.Slots[i]
        if s.Mode = "Toggle" && this.Current = i {
            this.Hide()
            return
        }
        token := this.Show(i)
        this.Pressed[i] := token
        if token && s.Mode = "Timed"
            this.ArmTimer(token, s.Duration)
    }

    Up(i, *) {
        Critical()
        if !this.Pressed.Has(i)
            return
        token := this.Pressed[i]
        this.Pressed.Delete(i)
        if this.Slots[i].Mode = "Hold" && this.Current = i && token = this.Generation
            this.Hide()
    }

    Show(i) {
        this.Hide()
        s := this.Slots[i], g := 0
        try {
            if s.File = ""
                throw Error("Slot " i " has no picture. Open Settings to choose one.")
            file := this.Path(s.File)
            MonitorGet(MonitorGetPrimary(), &left, &top, &right, &bottom)
            maxW := right - left - 32, maxH := bottom - top - 32
            g := Gui("-Caption +ToolWindow +AlwaysOnTop -DPIScale +E0x08000020", "Layer Pictures overlay")
            g.MarginX := 0, g.MarginY := 0, g.BackColor := "101010"
            pic := g.AddPicture("x0 y0 w" Min(s.Width, maxW) " h-1", file)
            pic.GetPos(,, &w, &h)
            if h > maxH {
                w := Max(1, Floor(w * maxH / h)), h := maxH
                pic.Value := "*w" w " *h" h " " file
                pic.Move(0, 0, w, h)
            }
            if w <= 0 || h <= 0
                throw Error("The picture has no displayable size.")
            x := InStr(s.Position, "Right") ? right - w - 16 : left + 16
            y := InStr(s.Position, "Bottom") ? bottom - h - 16 : top + 16
            if s.Position = "Center"
                x := left + Floor((right - left - w) / 2), y := top + Floor((bottom - top - h) / 2)
            ; Numeric HWND works on hidden windows. Transparency also makes this layered.
            WinSetTransparent(Round(s.Opacity * 255 / 100), g.Hwnd)
            g.Show("NA x" x " y" y " w" w " h" h)
            this.Overlay := g, this.Current := i
            return this.Generation
        } catch Error as err {
            if g
                g.Destroy()
            TrayTip(err.Message, "Layer Pictures", "Icon!")
            return 0
        }
    }

    Hide(*) {
        Critical()
        this.Generation += 1
        if this.Timer {
            SetTimer(this.Timer, 0)
            this.Timer := 0
        }
        if this.Overlay {
            this.Overlay.Destroy()
            this.Overlay := 0
        }
        this.Current := 0
    }

    ArmTimer(token, seconds) {
        this.Timer := this.Expire.Bind(this, token)
        SetTimer(this.Timer, -Round(seconds * 1000))
    }

    Expire(token) {
        Critical()
        if token = this.Generation
            this.Hide()
    }

    Preview(i, *) {
        Critical()
        if !this.Enabled {
            TrayTip("Enable overlays in the tray menu before previewing.", "Layer Pictures")
            return
        }
        if token := this.Show(i)
            this.ArmTimer(token, 2) ; Preview always lasts two seconds, including Hold slots.
    }

    ToggleEnabled(*) {
        Critical()
        this.Hide(), this.Unbind(), this.Enabled := !this.Enabled
        if this.Enabled {
            A_TrayMenu.Check("Overlays enabled")
            this.Resume()
        } else
            A_TrayMenu.Uncheck("Overlays enabled")
    }

    Settings(*) {
        Critical()
        if this.Editor {
            this.Editor.Show()
            return
        }
        this.Hide(), this.Unbind()
        g := Gui(, "Layer Pictures - Settings"), this.Editor := g, this.Fields := []
        g.SetFont("s10", "Segoe UI")
        g.AddText("x16 y12 w650", "Choose up to four pictures. One picture is displayed at a time.")
        tabs := g.AddTab3("x16 y42 w660 h302", ["Slot 1", "Slot 2", "Slot 3", "Slot 4"])
        for i, s in this.Slots {
            tabs.UseTab(i)
            g.AddText("x30 y78", "Local picture file (leave blank to leave this slot unused)")
            file := g.AddEdit("x30 y100 w526", s.File)
            g.AddButton("x568 y99 w92", "Browse...").OnEvent("Click", this.Browse.Bind(this, file))
            g.AddText("x30 y143", "Single key name")
            key := g.AddEdit("x30 y165 w126", s.Key)
            g.AddText("x185 y143", "Display mode")
            mode := g.AddDropDownList("x185 y165 w130", ["Toggle", "Hold", "Timed"])
            mode.Choose(s.Mode)
            g.AddText("x346 y143", "Opacity (1-100%)")
            opacity := g.AddEdit("x346 y165 w125", s.Opacity)
            g.AddText("x501 y143", "Width (pixels)")
            width := g.AddEdit("x501 y165 w140", s.Width)
            g.AddText("x30 y207", "Position on primary monitor")
            pos := g.AddDropDownList("x30 y229 w240", ["TopLeft", "TopRight", "Center", "BottomLeft", "BottomRight"])
            pos.Choose(s.Position)
            g.AddText("x306 y207", "Timed mode duration (seconds)")
            duration := g.AddEdit("x306 y229 w165", s.Duration)
            pass := g.AddCheckBox("x30 y271 w615", "Let the trigger key also continue to the game / active app")
            pass.Value := s.Pass
            g.AddText("x30 y302 w625", "Toggle: press again to hide. Hold: release to hide. Timed: auto-hide.")
            this.Fields.Push({File: file, Key: key, Mode: mode, Opacity: opacity,
                Width: width, Position: pos, Duration: duration, Pass: pass})
        }
        tabs.UseTab()
        g.AddText("x16 y359 w660 h40", "PNG/JPG/BMP/GIF/TIF. Images fit the screen and keep their proportions.`nSave, then use the tray's Preview menu. Bindings are paused while Settings is open.")
        g.AddButton("x420 y411 w140 Default", "Save and close").OnEvent("Click", this.Save.Bind(this))
        g.AddButton("x573 y411 w103", "Cancel").OnEvent("Click", this.CloseSettings.Bind(this))
        g.OnEvent("Close", this.CloseSettings.Bind(this))
        g.OnEvent("Escape", this.CloseSettings.Bind(this))
        g.Show("w692 h453")
    }

    Browse(control, *) {
        if file := FileSelect(1, , "Choose a local picture", "Pictures (*.png; *.jpg; *.jpeg; *.bmp; *.gif; *.tif; *.tiff)")
            control.Value := file
    }

    Save(*) {
        candidate := [], temp := this.Config ".new." A_TickCount
        try {
            for f in this.Fields
                candidate.Push({File: f.File.Value, Key: f.Key.Value, Mode: f.Mode.Text,
                    Opacity: f.Opacity.Value, Width: f.Width.Value, Position: f.Position.Text,
                    Duration: f.Duration.Value, Pass: f.Pass.Value})
            this.Validate(candidate)
            this.BindKeys(candidate, false) ; Reject unsupported bindings before saving anything.
            this.Unbind()
            for i, slot in candidate
                for field, value in slot.OwnProps()
                    IniWrite(value, temp, "Slot" i, field)
            FileMove(temp, this.Config, 1)
        } catch Error as err {
            if FileExist(temp)
                try FileDelete(temp)
            MsgBox(err.Message "`nSettings were not saved.", "Layer Pictures", "Icon!")
            return
        }
        this.Slots := candidate
        this.CloseSettings()
    }

    CloseSettings(*) {
        if this.Editor {
            this.Editor.Destroy()
            this.Editor := 0, this.Fields := []
        }
        this.Resume()
    }

    Cleanup(*) {
        this.Hide()
        this.Unbind()
    }
}
