; Optional presentation bridge. No key/text channel, socket or input activation.
class StudioHubBridge {
    __New(host) {
        this.Host := host
        this.Parent := 0
        this.Owner := 0
        this.Timer := 0
        this.WheelCallback := 0
        if !A_Args.Length || A_Args[1] != "--hub-parent"
            return
        if A_Args.Length != 4 || A_Args[3] != "--hub-owner"
            throw Error("Hub docking requires an exact parent and owner pair.")
        if !RegExMatch(A_Args[2], "^[1-9][0-9]{0,18}$") || !RegExMatch(A_Args[4], "^[1-9][0-9]{0,9}$")
            throw Error("Invalid Hub docking identity.")
        this.Parent := Integer(A_Args[2])
        this.Owner := Integer(A_Args[4])
        if !this.Alive()
            throw Error("Hub parent/owner is no longer valid.")
    }
    Alive() {
        if !this.Parent || !DllCall("IsWindow", "ptr", this.Parent)
            return false
        pid := 0
        DllCall("GetWindowThreadProcessId", "ptr", this.Parent, "uint*", &pid)
        return pid = this.Owner
    }
    Attach() {
        if !this.Parent
            return
        if !this.Alive()
            throw Error("Hub closed before docking.")
        ; Apply Parent after creation (AHK documents external-parent limitations).
        this.Host.Gui.Opt("-Caption -Border +Parent" this.Parent)
        if DllCall("GetParent", "ptr", this.Host.Gui.Hwnd, "ptr") != this.Parent
            throw Error("Studio could not attach to its Hub workspace.")
        this.Timer := this.CheckOwner.Bind(this)
        SetTimer(this.Timer, 500)
        this.WheelCallback := this.ScrollViewport.Bind(this)
        OnMessage(0x020A, this.WheelCallback)
        OnMessage(0x020E, this.WheelCallback)
    }
    ScrollViewport(wParam, lParam, msg, hwnd) {
        ; Presentation only: relay a bounded wheel delta from this embedded GUI.
        ; No hotkey, text, engine command or arbitrary window target is accepted.
        if !this.Alive() || (hwnd != this.Host.Gui.Hwnd && !DllCall("IsChild", "ptr", this.Host.Gui.Hwnd, "ptr", hwnd))
            return
        if DllCall("GetPropW", "ptr", this.Parent, "str", "GameTools.Studio.ScrollOwner", "ptr") != DllCall("GetCurrentProcessId", "uint")
            return
        controlClass := WinGetClass("ahk_id " hwnd)
        if RegExMatch(controlClass, "i)Edit|ComboBox|ListView|TreeView|trackbar|updown")
            return ; Text/list/value controls keep their normal wheel behavior.
        delta := (wParam >> 16) & 0xFFFF
        if delta > 32767
            delta -= 65536
        if !delta
            return
        if msg = 0x020E
            delta := -delta
        property := msg = 0x020E || (wParam & 4) ? "GameTools.Studio.ScrollX" : "GameTools.Studio.ScrollY"
        previous := DllCall("GetPropW", "ptr", this.Parent, "str", property, "ptr")
        queued := previous ? previous - 32768 : 0
        encoded := 32768 + Max(-720, Min(720, queued + delta))
        DllCall("SetPropW", "ptr", this.Parent, "str", property, "ptr", encoded)
        return 0
    }
    CheckOwner() {
        if !this.Alive()
            ExitApp()
        ; Exact owner-bound display flag and bounded type mask, not an input API.
        if DllCall("GetPropW", "ptr", this.Parent, "str", "GameTools.Studio.ScrollOwner", "ptr") = DllCall("GetCurrentProcessId", "uint") {
            mode := DllCall("GetPropW", "ptr", this.Parent, "str", "GameTools.Studio.Identify", "ptr")
            filterValue := DllCall("GetPropW", "ptr", this.Parent, "str", "GameTools.Studio.IdentifyFilter", "ptr")
            if (mode = 1 || mode = 2) && this.Host.HasOwnProp("Feedback") && (!filterValue || (filterValue >= 16 && filterValue <= 31))
                this.Host.Feedback.SetEnabled(mode = 1, filterValue ? filterValue - 16 : 15)
        }
    }
    Show() {
        if !this.Parent
            return false
        if !this.Alive()
            ExitApp()
        this.Host.Gui.Show("x0 y0 w976 h733 NoActivate")
        DllCall("SetPropW", "ptr", this.Parent, "str", "GameTools.Studio.Reveal", "ptr", DllCall("GetCurrentProcessId", "uint"))
        top := DllCall("GetAncestor", "ptr", this.Parent, "uint", 2, "ptr")
        try WinActivate("ahk_id " top)
        return true
    }
    ClosePanel(*) {
        if this.Parent
            ExitApp()
        this.Host.HidePanel()
    }
    Shutdown() {
        if this.Alive() {
            DllCall("RemovePropW", "ptr", this.Parent, "str", "GameTools.Studio.Reveal", "ptr")
            for property in ["GameTools.Studio.ScrollOwner", "GameTools.Studio.ScrollX", "GameTools.Studio.ScrollY", "GameTools.Studio.Identify", "GameTools.Studio.IdentifyFilter"]
                DllCall("RemovePropW", "ptr", this.Parent, "str", property, "ptr")
        }
        if this.WheelCallback {
            OnMessage(0x020A, this.WheelCallback, 0)
            OnMessage(0x020E, this.WheelCallback, 0)
        }
        if this.Timer
            SetTimer(this.Timer, 0)
    }
}

; Local-only UI identification. No hooks, remapping, file writes or engine calls.
class StudioComponentFeedback {
    __New(host) {
        this.Host := host
        this.Enabled := false
        this.Targets := Map()
        this.Badges := []
        this.Records := []
        this.Toast := 0
        this.Mask := 15
    }
    RegisterNew(gui, base, owner, fields := 0) {
        known := Map()
        if IsObject(fields) {
            for name in fields
                if owner.HasOwnProp(name) && IsObject(owner.%name%)
                    known[owner.%name%] := name
        }
        ; Advanced editor dictionaries contain declared roles, not user values.
        for name, value in owner.OwnProps() {
            if IsObject(value) && HasProp(value, "Hwnd") && HasProp(value, "Type")
                && RegExMatch(value.Type, "^(Edit|Hotkey|DDL|DropDownList|CheckBox|Radio|Slider|ListView|Picture|Text|GroupBox|Tab3)$")
                known[value] := name
            else if value is Map {
                for field, entry in value {
                    if IsObject(entry) && HasProp(entry, "Control")
                        known[entry.Control] := name "-" field
                    else if IsObject(entry) && HasProp(entry, "Hwnd") && HasProp(entry, "Type")
                        known[entry] := name "-" field
                }
            }
        }
        controls := []
        for control in gui
            if !this.Targets.Has(control)
                controls.Push(control)
        for control in controls {
            this.Targets[control] := true
            label := "", role := ""
            if known.Has(control)
                role := known[control], label := role
            else if control.Type = "Button" || control.Type = "CheckBox"
                label := control.Text, role := "action-" label
            else if control.Type = "Text" {
                ; Undeclared Text at construction is authored explanation only.
                ; Dynamic status controls use their declared property above.
                label := "Text / explanation", role := "text-" SubStr(control.Text, 1, 72)
                if RegExMatch(role, "[\\/:@{}]")
                    role := "text"
            }
            else if control.Type = "GroupBox"
                label := "Section", role := "section-" control.Text
            else
                continue ; Never infer identity from editable values or logs.
            role := Trim(RegExReplace(StrLower(role), "[^a-z0-9]+", "-"), "-")
            if role = ""
                continue
            identifier := base "." role
            if base = "UI-101" {
                if role = "ffile" || InStr(role, "preview-current-edits")
                    identifier := "UI-103." role
                else if InStr(role, "advanced-pictures")
                    identifier := "UI-104." role
                else if role = "fkey" || role = "fsource" || role = "fmode" || role = "fpass"
                    identifier := "UI-102." role
            }
            pretty := Map("FName", "Picture name", "FEnabled", "Enable picture trigger", "FKey", "Trigger key", "FSource", "Picture source", "FMode", "Display mode", "FFile", "Local picture path", "List", "Picture slots", "FMicCanvas", "MIC canvas key", "FPass", "Pass trigger to game", "FWidth", "Picture width", "FOpacity", "Picture opacity", "FPosition", "Picture anchor", "FOffsetX", "Horizontal offset", "FOffsetY", "Vertical offset", "FDuration", "Timed duration")
            if pretty.Has(label)
                label := pretty[label]
            kind := control.Type = "Text" ? 2 : (control.Type = "ListView" || control.Type = "Picture") ? 4 : (control.Type = "GroupBox" || control.Type = "Tab3") ? 8 : 1
            if control.Type = "Edit" && (DllCall("GetWindowLongW", "ptr", control.Hwnd, "int", -16, "uint") & 0x0800)
                kind := 4 ; Read-only report/log, not an editable input.
            control.GetPos(&x, &y, &width, &height)
            ; Prevent a lower sibling from painting over a higher badge. This
            ; is UI clipping only, not a hook, profile edit or input redirection.
            control.Opt("+0x04000000") ; WS_CLIPSIBLINGS
            badgeX := control.Type = "Text" && x >= 23 ? x - 23 : Max(0, x + width - 22)
            badge := gui.AddButton("x" badgeX " y" y " w21 h21 Hidden +0x04000000", "?")
            badge.OnEvent("Click", this.Copy.Bind(this, identifier, label))
            this.Targets[badge] := true
            this.Badges.Push(badge)
            this.Records.Push({Target: control, Badge: badge, Id: identifier, Label: label, Kind: kind})
            badge.Visible := this.Enabled && !!(this.Mask & kind)
            if this.Enabled && (this.Mask & kind)
                this.Raise(badge)
        }
    }
    SetEnabled(enabled, mask := 15) {
        if Type(mask) != "Integer" || mask < 0 || mask > 15
            throw Error("Invalid identification display filter")
        if this.Enabled = !!enabled && this.Mask = mask
            return
        this.Enabled := !!enabled
        this.Mask := mask
        this.RefreshPositions()
    }
    RefreshPositions() {
        ; Identification follows reflow/disclosure/tab visibility. Never copy
        ; user values, invoke the original action, or reveal hidden controls.
        for record in this.Records
            try {
                record.Target.GetPos(&x, &y, &w, &h)
                record.Badge.Move(record.Target.Type = "Text" && x >= 23 ? x - 23 : Max(0, x + w - 22), y, 21, 21)
                record.Badge.Visible := this.Enabled && !!(this.Mask & record.Kind) && record.Target.Visible
                if record.Badge.Visible
                    this.Raise(record.Badge)
            }
    }
    Raise(badge) {
        ; Native overlapping sibling controls need explicit z-order, not only
        ; visibility. Otherwise a marker may paint over an action but clicks
        ; still reach that original action. Only this authored badge is raised.
        DllCall("SetWindowPos", "ptr", badge.Hwnd, "ptr", 0, "int", 0, "int", 0,
            "int", 0, "int", 0, "uint", 0x13)
        DllCall("RedrawWindow", "ptr", badge.Hwnd, "ptr", 0, "ptr", 0, "uint", 0x101)
    }
    Toggle(*) {
        this.SetEnabled(!this.Enabled, this.Mask)
    }
    ShowMenu(*) {
        choices := Menu()
        choices.Add("Show all components", this.SetView.Bind(this, true, 15))
        choices.Add("Hide all markers", this.SetView.Bind(this, false, this.Mask))
        choices.Add()
        custom := Menu()
        for bit, caption in Map(1, "Controls", 2, "Text & status", 4, "Tables & images", 8, "Sections") {
            choices.Add(caption " only", this.SetView.Bind(this, true, bit))
            custom.Add(caption, this.ToggleType.Bind(this, bit))
            if this.Mask & bit
                custom.Check(caption)
        }
        choices.Add("Choose types", custom)
        choices.Show()
    }
    SetView(enabled, mask, *) {
        this.SetEnabled(enabled, mask)
    }
    ToggleType(bit, *) {
        mask := this.Mask ^ bit
        this.SetEnabled(mask != 0, mask)
    }
    CopyValue(identifier) {
        try {
            A_Clipboard := identifier
            return true
        } catch
            return false
    }
    Copy(identifier, label, *) {
        copied := this.CopyValue(identifier)
        if this.Toast
            try this.Toast.Destroy()
        ; Name + copied ID stay together; no settings, input or clipboard read.
        this.Toast := popup := Gui("+Owner" this.Host.Gui.Hwnd " +AlwaysOnTop -MinimizeBox -MaximizeBox", "UI component ID")
        popup.SetFont("s10", "Segoe UI")
        popup.AddText("w420", label)
        popup.AddEdit("w420 ReadOnly", identifier)
        result := popup.AddText("w420", copied ? "Copied. The original control was not activated." : "Clipboard unavailable. Select the ID or retry Copy ID.")
        popup.AddButton("w90", "Copy ID").OnEvent("Click", this.RetryCopy.Bind(this, identifier, result))
        popup.AddButton("x+10 w90", "Close").OnEvent("Click", (*) => popup.Destroy())
        popup.OnEvent("Escape", (*) => popup.Destroy())
        popup.OnEvent("Close", (*) => popup.Destroy())
        popup.Show("AutoSize")
    }
    RetryCopy(identifier, result, *) {
        result.Text := this.CopyValue(identifier) ? "Copied. The original control was not activated." : "Clipboard unavailable. Select the ID or retry Copy ID."
    }
    Shutdown() {
        if this.Toast
            try this.Toast.Destroy()
    }
}
