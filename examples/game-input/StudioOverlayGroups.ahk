#Requires AutoHotkey v2.0
; Optional display-only adapter. No input hook, hotkey, remapping or runner.
; The slot owns Hold/Toggle/Timed; optional native layer visibility shares Hold.
class StudioOverlayGroups {
    static Version := "0.1.13"
    static PollMs := 15
    __New(host) {
        StudioEditableListPopup.Enable()
        this.Host := host, this.Enabled := false, this.Slot := 0
        this.Path := EnvGet("LOCALAPPDATA") "\GameToolHub\overlay-selection.ini"
        this.Timer := this.Tick.Bind(this), this.Gui := 0, this.LastAsset := ""
        this.Config := host.Dir "\overlay-groups-route.ini"
        this.PendingHold := 0, this.LastError := ""
        this.Children := Map(), this.IsChild := false
        this.LayerVisibility := StudioLayerVisibility(this)
        this.Alternate := StudioOverlayAlternate(this)
        this.LoadSaved()
    }
    Validate(slot, path) {
        if slot < 1 || slot > this.Host.Slots.Length || this.Host.Slots[slot].Source != "Local"
            || !this.Host.Slots[slot].Enabled
            throw Error("Choose an enabled local picture slot.")
        if !RegExMatch(path, "i)^[a-z]:\\")
            throw Error("Use an absolute local relay path.")
    }
    LoadSaved() {
        if !FileExist(this.Config)
            return
        try {
            attr := DllCall("GetFileAttributesW", "str", this.Config, "uint")
            if (attr & 0x410) || FileGetSize(this.Config) > 16384
                throw Error("Invalid saved overlay route.")
            if IniRead(this.Config, "Route", "Schema", 0) != 1
                throw Error("Unknown overlay-route settings schema.")
            enabled := IniRead(this.Config, "Route", "Enabled", 0)
            if enabled != 0 && enabled != 1
                throw Error("Invalid saved overlay-route enablement.")
            if !enabled
                return
            slot := Integer(IniRead(this.Config, "Route", "Slot", 0))
            path := IniRead(this.Config, "Route", "Path", "")
            this.Validate(slot, path)
            this.Slot := slot, this.Path := path, this.Enabled := true
            SetTimer(this.Timer, StudioOverlayGroups.PollMs)
        } catch as err {
            this.Stop()
            this.Host.WriteLog("SAVED OVERLAY ROUTE REFUSED: " err.Message)
        }
    }
    Save() {
        original := FileExist(this.Config) ? FileRead(this.Config, "UTF-8") : ""
        if original != "" && IniRead(this.Config, "Route", "Schema", 0) != 1
            throw Error("Preserve unknown overlay-route settings before changing them.")
        temp := this.Config ".pending-" A_TickCount
        if FileExist(temp)
            throw Error("Overlay route save is already pending.")
        try {
            if FileExist(this.Config)
                FileCopy(this.Config, temp)
            IniWrite(1, temp, "Route", "Schema")
            IniWrite(this.Enabled ? 1 : 0, temp, "Route", "Enabled")
            IniWrite(this.Slot, temp, "Route", "Slot")
            IniWrite(this.Path, temp, "Route", "Path")
            current := FileExist(this.Config) ? FileRead(this.Config, "UTF-8") : ""
            if current != original
                throw Error("Overlay route settings changed while saving.")
            FileMove(temp, this.Config, 1)
        } catch {
            if FileExist(temp)
                FileDelete(temp)
            throw
        }
    }
    Open(*) {
        if this.Gui {
            this.Gui.Show()
            return
        }
        g := Gui("+Resize", "Automatic overlay groups — optional display route")
        g.SetFont("s10", "Segoe UI")
        g.AddText("w600", "Hub selects the map for the current game and layer. The picture slot controls Hold, Toggle or Timed. By default layer changes do not open it; Hub can also show selected native hold layers on a Hold slot. Native mappings and trigger keys are configured separately.")
        g.AddText("xm y+12", "Existing LOCAL picture slot (no new trigger)")
        slot := g.AddComboBox("xm y+5 w150", [])
        rows := []
        for i, s in this.Host.Slots
            if s.Source = "Local"
                rows.Push(i)
        slot.Add(rows)
        slot.Text := this.Slot ? this.Slot : this.Host.Selected
        g.AddText("xm y+12", "Private Hub display relay path")
        path := g.AddEdit("xm y+5 w600", this.Path)
        state := g.AddText("xm y+12 w600", this.Enabled ? "Saved route enabled; press its picture key to show the current map." : "Off. Enable an existing picture slot to show the current map from its trigger.")
        arm := g.AddCheckBox("xm y+8", "Enable this route (saved for next launch)")
        arm.Value := this.Enabled
        arm.OnEvent("Click", (*) => this.Configure(arm, slot, path, state))
        g.AddButton("xm y+12", "Hide controls").OnEvent("Click", (*) => g.Hide())
        g.OnEvent("Close", (*) => g.Hide())
        this.Gui := g
        g.Show()
    }
    Configure(arm, slot, path, state) {
        try {
            if arm.Value {
                i := Integer(slot.Text)
                this.Validate(i, path.Value)
                this.Slot := i, this.Path := path.Value
                this.Enabled := true
                this.Save()
                SetTimer(this.Timer, StudioOverlayGroups.PollMs)
                state.Text := "Saved for slot " i "; press its picture key to show the current map. See Hub for layer source/state."
            } else {
                this.Stop()
                this.Save()
                state.Text := "Saved Off. Original slot behavior preserved."
            }
        } catch as err {
            arm.Value := 0, this.Stop(), state.Text := err.Message
        }
    }
    LoadSnapshot() {
        Loop 4 {
            try {
                attr := DllCall("GetFileAttributesW", "str", this.Path, "uint")
                if attr = 0xFFFFFFFF || (attr & 0x410)
                    throw Error("Missing or linked display relay refused.")
                ; FileOpen shares read/write/delete by default. Unlike FileRead,
                ; this permits the Hub's atomic heartbeat replacement while this
                ; handle reads one complete old/new snapshot. No stale cache.
                stream := FileOpen(this.Path, "r", "UTF-8")
                try {
                    if stream.Length > 16384
                        throw Error("Display relay oversized.")
                    return stream.Read()
                } finally stream.Close()
            } catch OSError as err {
                if !(err.Number = 5 || err.Number = 32 || err.Number = 33) || A_Index = 4
                    throw
                Sleep(5) ; Bounded 15ms retry for the in-flight rename only.
            }
        }
    }
    ParseSnapshot(snapshot) {
        values := Map(), values.CaseSense := "Off", section := false
        Loop Parse LTrim(snapshot, Chr(0xFEFF)), "`n", "`r" {
            line := Trim(A_LoopField)
            if line = ""
                continue
            if line = "[Overlay]" && !section {
                section := true
                continue
            }
            if !section || !RegExMatch(line, "^([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$", &match)
                || values.Has(match[1])
                throw Error("Invalid display relay snapshot.")
            values[match[1]] := Trim(match[2])
        }
        if !section
            throw Error("Display relay section missing.")
        return values
    }
    NowMs() {
        time := Buffer(8)
        DllCall("GetSystemTimePreciseAsFileTime", "ptr", time)
        return Floor(NumGet(time, 0, "int64") / 10000) - 11644473600000
    }
    ForegroundExe() {
        return WinGetProcessPath("A")
    }
    ContentKey(snapshot) {
        return RegExReplace(snapshot, "mi)^ExpiresUnix(?:Ms)?\s*=.*$", "")
    }
    ValidateLifetime(values) {
        if values.Get("Schema", "0") != 1
            throw Error("Unsupported display relay schema.")
        if values.Get("Active", "0") != 1 {
            reason := SubStr(StrReplace(StrReplace(values.Get("StatusReason", "No active map from publisher"), "`r", " "), "`n", " "), 1, 200)
            throw Error("Selection inactive: " reason)
        }
        now := this.NowMs()
        if values.Has("ExpiresUnixMs") {
            expiry := values["ExpiresUnixMs"]
            if !RegExMatch(expiry, "^[0-9]{1,16}$") || Integer(expiry) > now + 2000
                throw Error("Invalid display relay expiry.")
            if Integer(expiry) <= now
                throw Error("Display relay heartbeat expired by " (now - Integer(expiry)) " ms.")
        } else {
            expiry := values.Get("ExpiresUnix", "0"), seconds := Floor(now / 1000)
            if !RegExMatch(expiry, "^[0-9]{1,13}$") || Integer(expiry) > seconds + 2
                throw Error("Invalid legacy display relay expiry.")
            if Integer(expiry) <= seconds
                throw Error("Legacy display relay heartbeat expired.")
        }
    }
    Read(retries := 2) {
        snapshot := this.LoadSnapshot(), values := this.ParseSnapshot(snapshot)
        this.ValidateLifetime(values)
        exe := values.Get("Exe", "")
        if exe = "" || StrLower(exe) != StrLower(this.ForegroundExe())
            throw Error("Foreground game differs from the selection.")
        alternate := false
        if this.HasOwnProp("Alternate") {
            this.Alternate.Configure(values)
            alternate := this.Alternate.Select(values)
        }
        relayImage := values.Get("File", "")
        if !FileExist(relayImage) || FileGetSize(relayImage) > 16777216
            throw Error("Overlay image unavailable.")
        attrs := DllCall("GetFileAttributesW", "str", relayImage, "uint")
        hash := values.Get("SHA256", "")
        if attrs = 0xFFFFFFFF || (attrs & 0x410) || !RegExMatch(hash, "^[a-f0-9]{64}$")
            || StrLower(PM_Model.Sha256(relayImage)) != hash
            throw Error("Image identity mismatch.")
        latest := this.LoadSnapshot()
        if this.ContentKey(latest) != this.ContentKey(snapshot) {
            if retries > 0
                return this.Read(retries - 1)
            throw Error("Display selection changed while reading.")
        }
        values := this.ParseSnapshot(latest), this.ValidateLifetime(values)
        if this.HasOwnProp("Alternate") {
            this.Alternate.Configure(values)
            alternate := this.Alternate.Select(values)
        }
        if StrLower(exe) != StrLower(this.ForegroundExe())
            throw Error("Foreground game differs from the selection.")
        if values.Get("File", "") != relayImage || values.Get("SHA256", "") != hash {
            if retries > 0
                return this.Read(retries - 1)
            throw Error("Alternate view changed while reading.")
        }
        return {File: relayImage, Hash: hash, Snapshot: latest (alternate ? "`nRuntimeAlternate=1`n" : ""), Values: values}
    }
    Resolve(index, legacy) {
        if !this.IsChild && this.Enabled {
            child := this.Child(index)
            if child
                return child.Resolve(index, legacy)
        }
        if !this.Enabled || index != this.Slot || legacy.Source != "Local"
            return legacy
        source := this.Read()
        result := PM_Model.Clone(legacy)
        result.File := source.File
        result.RouteImageHash := source.Hash
        result.PreserveAlpha := true ; Clear PNG background; slot opacity still applies to visible pixels.
        result.SizeMode := source.Values.Get("size_mode", "Pixels")
        result.SizeValue := Number(source.Values.Get("size_value", 600))
        result.Width := result.SizeValue
        result.Opacity := Number(source.Values.Get("opacity", 85))
        result.Monitor := Integer(source.Values.Get("monitor", 1))
        result.Position := source.Values.Get("anchor", "TopRight")
        result.OffsetX := Number(source.Values.Get("offset_x", 0))
        result.OffsetY := Number(source.Values.Get("offset_y", 0))
        for field in ["FadeInMs", "FadeOutMs"] {
            value := source.Values.Get(field, "0")
            if !RegExMatch(value, "^[0-9]{1,3}$") || Integer(value) > 400
                throw Error("Invalid overlay transition duration.")
            result.%field% := Integer(value)
        }
        result.DisplayExe := source.Values.Get("Exe", "")
        result.RouteSlot := index
        if !PM_Model.ExactHas("Pixels,Screen width %,Screen height %,Original %", result.SizeMode)
            || !PM_Model.ExactHas("TopLeft,TopRight,Center,BottomLeft,BottomRight", result.Position)
            || result.SizeValue < 1 || result.SizeValue > 8000 || result.Opacity < 5 || result.Opacity > 100
            || result.Monitor < 1 || result.Monitor > MonitorGetCount()
            throw Error("Invalid display geometry.")
        this.LastAsset := source.Snapshot
        return result ; Never alters Mode, trigger, Enabled, MIC or native output.
    }
    Child(index) {
        if this.IsChild || index < 1 || index > this.Host.Slots.Length
            return 0
        SplitPath(this.Path, , &directory)
        path := directory "\overlay-selection-slot-" index ".ini"
        linked := false
        if FileExist(path) {
            if !this.Children.Has(index)
                this.Children[index] := this.NewChild(index, path)
            reader := this.Children[index]
            reader.Enabled := this.Enabled
            try linked := reader.ParseSnapshot(reader.LoadSnapshot()).Get("Linked", "0") = "1"
            catch
                linked := true ; A malformed existing link must not fall back to a static picture.
        }
        if !linked && this.Children.Has(index) {
            reader := this.Children[index]
            if this.Host.Current = index && reader.LastAsset != ""
                this.Host.HideCurrent()
            reader.PendingHold := 0
            this.Children.Delete(index)
        }
        return linked ? this.Children[index] : 0
    }
    NewChild(index, path) {
        return StudioLinkedMapRoute(this, index, path)
    }
    OwnerForSlot(index) {
        child := !this.IsChild ? this.Child(index) : 0
        return child ? child : this
    }
    ReadForSlot(index) {
        return this.OwnerForSlot(index).Read()
    }
    CancelPending(all := true) {
        this.PendingHold := 0
        if all && this.HasOwnProp("LayerVisibility")
            this.LayerVisibility.Cancel()
        if all && this.HasOwnProp("Alternate")
            this.Alternate.Cancel()
        if all && !this.IsChild
            for index, child in this.Children
                child.CancelPending()
    }
    HoldIntent() {
        if !this.Host.HasOwnProp("Pressed") || !this.Host.Pressed.Has(this.Slot)
            return 0
        pressed := this.Host.Pressed[this.Slot]
        return IsObject(pressed) && pressed.Mode = "Hold" ? pressed : 0
    }
    KeepForLayer(index) {
        return !this.IsChild && ((this.HasOwnProp("Alternate") && this.Alternate.Keep(index))
            || (this.HasOwnProp("LayerVisibility") && this.LayerVisibility.Keep(index)))
    }
    AlternateDown(index) {
        if !this.IsChild && this.Enabled && index = this.Slot && !this.Child(index)
            && this.Host.Slots[index].Mode = "Hold" && this.HasOwnProp("Alternate")
            this.Alternate.OnDown()
    }
    AlternateUp(index) {
        if !this.IsChild && index = this.Slot && this.HasOwnProp("Alternate")
            this.Alternate.OnUp()
    }
    CapturePending(index) {
        if !this.IsChild && this.Enabled {
            child := this.Child(index)
            if child {
                child.CapturePending(index)
                return
            }
        }
        if this.Enabled && index = this.Slot && this.Host.Slots[index].Mode = "Hold" {
            this.Host.Pressed[index] := {Token: 0, Mode: "Hold"}
            this.PendingHold := this.Host.Pressed[index]
        }
    }
    WarmTick() {
        ; At most one decode per idle slice. Never prepare extra layers while
        ; a picture/hold is active; hotkeys keep their original ownership.
        if this.Host.Current || !this.Host.HasOwnProp("Pictures") || !HasMethod(this.Host.Pictures, "WarmRouteImage")
            || (this.Host.HasOwnProp("Pressed") && this.Host.Pressed.Count)
            || (this.Host.HasOwnProp("Fade") && this.Host.Fade.Window)
            return
        now := DllCall("GetTickCount64", "uint64")
        if this.HasOwnProp("NextWarm") && now < this.NextWarm
            return
        this.NextWarm := now + 100
        try {
            signature := this.ContentKey(this.LoadSnapshot())
            if this.HasOwnProp("WarmSignature") && signature = this.WarmSignature && this.WarmDone
                return
            source := this.Read()
            count := source.Values.Get("WarmCount", "0")
            if !RegExMatch(count, "^[0-8]$") || Integer(count) = 0
                return
            altCount := source.Values.Get("AltWarmCount", "0")
            if !RegExMatch(altCount, "^[0-8]$")
                throw Error("Invalid alternate preparation count.")
            if !this.HasOwnProp("WarmSignature") || signature != this.WarmSignature
                this.WarmSignature := signature, this.WarmIndex := 1, this.WarmDone := false
            base := this.Resolve(this.Slot, this.Host.Slots[this.Slot])
            while this.WarmIndex <= Integer(count) + Integer(altCount) {
                warmOrdinal := this.WarmIndex
                slot := PM_Model.Clone(base)
                prefix := "Warm"
                if warmOrdinal > Integer(count) {
                    warmOrdinal -= Integer(count), prefix := "AltWarm"
                    for field in ["size_mode", "size_value", "opacity", "monitor", "anchor", "offset_x", "offset_y"] {
                        property := Map("size_mode","SizeMode","size_value","SizeValue","opacity","Opacity","monitor","Monitor","anchor","Position","offset_x","OffsetX","offset_y","OffsetY")[field]
                        if source.Values.Has("Alt_" field)
                            slot.%property% := source.Values["Alt_" field]
                    }
                }
                slot.File := source.Values.Get(prefix "File" warmOrdinal, "")
                slot.RouteImageHash := source.Values.Get(prefix "SHA256" warmOrdinal, "")
                prepared := this.Host.Pictures.WarmRouteImage(slot)
                this.WarmIndex += 1
                if prepared
                    return
            }
            this.WarmDone := true
            this.Host.WriteLog("OVERLAY PREPARED: " count " layer images; bounded pixel cache.")
        } catch {
            ; Preparation is optional. Every actual show still validates the
            ; fresh selection, foreground, source bytes and hold generation.
            this.WarmDone := false
        }
    }
    Tick(*) {
        if !this.Enabled || !this.Host.Enabled
            return
        if !this.IsChild {
            Loop this.Host.Slots.Length {
                child := this.Child(A_Index)
                if child {
                    if A_Index = this.Slot && this.LayerVisibility.Token
                        this.LayerVisibility.End()
                    child.Tick()
                }
            }
            if this.Children.Has(this.Slot)
                return ; Fixed picture guides never gain native-layer visibility.
            this.Alternate.Tick()
            this.LayerVisibility.Tick()
        }
        this.WarmTick()
        held := this.HoldIntent(), active := this.Host.Current = this.Slot
        if !active && (!held || !this.PendingHold || ObjPtr(held) != ObjPtr(this.PendingHold)) {
            this.CancelPending(false)
            return
        }
        generation := this.Host.Generation
        try {
            source := this.Read()
            if !active || this.ContentKey(source.Snapshot) != this.ContentKey(this.LastAsset) {
                result := this.Resolve(this.Slot, this.Host.Slots[this.Slot])
                previousCritical := A_IsCritical
                Critical("On")
                try {
                    if !this.Enabled || !this.Host.Enabled
                        return
                    if active {
                        if this.Host.Current != this.Slot || this.Host.Generation != generation
                            return
                        ; Keep the existing visible window until the replacement
                        ; surface is ready; do not expose the desktop between maps.
                        if !this.Host.ShowLocal(result, true)
                            this.Host.HideCurrent()
                    } else {
                        current := this.HoldIntent()
                        if !current || !this.PendingHold || ObjPtr(current) != ObjPtr(held)
                            || ObjPtr(current) != ObjPtr(this.PendingHold) || result.Mode != "Hold"
                            return
                        token := this.Host.ShowSlot(this.Slot, result)
                        if token {
                            current.Token := token
                            this.Host.WriteLog("OVERLAY RESUMED: same held picture trigger; fresh selection.")
                        }
                    }
                } finally Critical(previousCritical)
            }
            this.LastError := ""
        } catch as err {
            ownsActive := active && this.Host.Current = this.Slot && this.Host.Generation = generation
            ownsPending := !active && held && this.PendingHold && ObjPtr(held) = ObjPtr(this.PendingHold)
            if !ownsActive && !ownsPending
                return ; A release, explicit Hide or another press superseded this read.
            if ownsActive
                this.Host.HideCurrent()
            current := this.HoldIntent()
            if held && current && ObjPtr(held) = ObjPtr(current)
                this.PendingHold := current
            errorKey := RegExReplace(err.Message, "expired by [0-9]+ ms\.", "expired.")
            if this.LastError != errorKey
                this.Host.WriteLog("OVERLAY SUSPENDED: " err.Message)
            this.LastError := errorKey
        }
    }
    Stop(*) {
        this.CancelPending()
        if !this.IsChild
            for index, child in this.Children
                child.Stop()
        if this.Enabled && this.Host.Current = this.Slot
            this.Host.HideCurrent()
        this.Enabled := false
        SetTimer(this.Timer, 0)
    }
    Shutdown(*) {
        this.Stop()
        if this.Gui
            this.Gui.Destroy(), this.Gui := 0
    }
}

; App-local window messages only. Standard editable ComboBoxes keep their own
; editing/search/selection behavior; clicking their edit field opens the list.
class StudioEditableListPopup {
    static Callback := 0
    static Enable() {
        if !this.Callback {
            this.Callback := this.Click.Bind(this)
            OnMessage(0x201, this.Callback)
        }
    }
    static Click(wParam, lParam, msg, hwnd) {
        try {
            if WinGetClass(hwnd) != "Edit"
                return
            parent := DllCall("GetParent", "ptr", hwnd, "ptr")
            if !parent || WinGetClass(parent) != "ComboBox"
                return
            style := DllCall("GetWindowLongW", "ptr", parent, "int", -16, "uint")
            if (style & 3) = 2 && DllCall("IsWindowEnabled", "ptr", parent)
                PostMessage(0x14F, 1, 0, , parent) ; CB_SHOWDROPDOWN after caret handling.
        }
        ; Never consume a click or alter a value / trigger / native mapping.
    }
}

; Independent visibility owner: native layer OR dedicated picture key.
; Reuses the parent's timer and renderer. Never creates a key press or emits input.
class StudioLayerVisibility {
    __New(route) {
        this.Route := route, this.Key := "", this.Blocked := "", this.Token := 0, this.Managed := false
        this.LastError := ""
    }
    Configured() {
        route := this.Route, host := route.Host, i := route.Slot
        return route.Enabled && host.Enabled && i >= 1 && i <= host.Slots.Length
            && host.Slots[i].Enabled && host.Slots[i].Source = "Local" && host.Slots[i].Mode = "Hold"
            && !route.Children.Has(i)
    }
    Request(source := 0) {
        route := this.Route
        values := source ? source.Values : route.ParseSnapshot(route.LoadSnapshot())
        flag := values.Get("LayerShow", "0")
        if flag = "0"
            return ""
        if flag != "1" || values.Get("LayerState", "") != "Event-tracked"
            || !RegExMatch(values.Get("LayerHoldKey", ""), "^[a-f0-9]{64}$")
            throw Error("Invalid native layer visibility request.")
        route.ValidateLifetime(values)
        if StrLower(values.Get("Exe", "")) != StrLower(route.ForegroundExe())
            throw Error("Foreground differs from native layer visibility request.")
        return values["LayerHoldKey"]
    }
    Cancel() {
        if !this.Managed && this.Key != ""
            this.Blocked := this.Key, this.Token := 0
    }
    Hide(animate := false) {
        this.Managed := true
        try this.Route.Host.HideCurrent(animate)
        finally this.Managed := false
    }
    End() {
        host := this.Route.Host, i := this.Route.Slot
        if this.Token && host.Current = i && host.Generation = this.Token {
            held := this.Route.HoldIntent()
            if held
                held.Token := host.Generation ; The dedicated Hold remains the owner.
            else if !this.Route.HasOwnProp("Alternate") || !this.Route.Alternate.Keep(i)
                this.Hide(true)
        }
        this.Key := "", this.Blocked := "", this.Token := 0
    }
    Keep(index) {
        if !this.Configured() || index != this.Route.Slot || this.Route.Host.Current != index
            return false
        try {
            source := this.Route.Read(), key := this.Request(source)
            if key = "" || key = this.Blocked
                return false
            this.Key := key, this.Token := this.Route.Host.Generation
            return true
        } catch
            return false
    }
    Tick() {
        host := this.Route.Host, i := this.Route.Slot
        try {
            this.LastError := ""
            key := this.Configured() ? this.Request() : ""
            if key = "" {
                this.End()
                return
            }
            this.Key := key
            if key = this.Blocked
                return ; Explicit Hide / another slot wins until a new layer event.
            if host.Current && host.Current != i {
                this.Blocked := key, this.Token := 0
                return ; Never steal another picture's visibility.
            }
            if host.Current = i {
                this.Token := host.Generation
                return
            }
            source := this.Route.Read()
            if this.Request(source) != key
                return ; Recheck an in-flight layer/foreground change before display.
            resolved := this.Route.Resolve(i, host.Slots[i])
            if this.Request({Values: this.Route.ParseSnapshot(this.Route.LastAsset)}) != key
                return
            previousCritical := A_IsCritical
            Critical("On")
            try {
                if !this.Configured() || host.Current || key = this.Blocked
                    return
                this.Managed := true
                try this.Token := host.ShowSlot(i, resolved)
                finally this.Managed := false
                held := this.Route.HoldIntent()
                if held && this.Token
                    held.Token := this.Token
            } finally Critical(previousCritical)
        } catch as err {
            this.LastError := err.Message
            ; Bad/expired/foreign data withdraws automatic visibility. The normal
            ; route retains its existing independent held-key recovery behavior.
            held := this.Route.HoldIntent()
            if this.Token && host.Current = i && host.Generation = this.Token {
                this.Hide()
                current := this.Route.HoldIntent()
                if held && current && ObjPtr(current) = ObjPtr(held)
                    this.Route.PendingHold := held
            }
            this.Token := 0
        }
    }
}

; Shares the parent's opt-in and the existing slot's Hold/Toggle/Timed owner.
; This reader registers no timer, hotkey or input hook of its own.
class StudioLinkedMapRoute extends StudioOverlayGroups {
    __New(parent, index, path) {
        this.Host := parent.Host, this.Enabled := parent.Enabled, this.Slot := index, this.Path := path
        this.IsChild := true, this.Children := Map(), this.PendingHold := 0, this.LastError := ""
        this.LastAsset := "", this.Gui := 0, this.Timer := this.Tick.Bind(this)
    }
}

; Display state only. Reuses the existing picture key, timer and renderer.
; Combination state is observed; this class registers/suppresses/emits no keys.
class StudioOverlayAlternate {
    __New(route) {
        this.Route := route, this.Identity := "", this.Enabled := false
        this.LastDown := -10000, this.Released := false, this.DoubleHeld := false
        this.Toggle := false, this.Chord := [], this.ChordHeld := false
        this.Blocked := false, this.Token := 0, this.Managed := false
    }
    Clock() => DllCall("GetTickCount64", "uint64")
    KeyHeld(key) => GetKeyState(key, "P")
    Reset() {
        this.LastDown := -10000, this.Released := false, this.DoubleHeld := false
        this.Toggle := false, this.ChordHeld := false, this.Blocked := false
    }
    Configure(values) {
        enabled := values.Get("AltEnabled", "0") = "1"
        identity := enabled ? values.Get("AltIdentity", "") "|" values.Get("Exe", "") : ""
        if enabled {
            window := values.Get("AltWindowMs", "300"), double := values.Get("AltDouble", "0")
            behavior := values.Get("AltBehavior", "hold"), chord := values.Get("AltChord", "")
            if !RegExMatch(values.Get("AltIdentity", ""), "^[a-f0-9]{64}$")
                || !RegExMatch(window, "^[0-9]{3}$") || Integer(window) < 150 || Integer(window) > 600
                || !(double = "0" || double = "1") || !(behavior = "hold" || behavior = "toggle")
                throw Error("Invalid alternate view controls.")
            keys := chord = "" ? [] : StrSplit(chord, ";"), seen := Map()
            if keys.Length && (keys.Length < 2 || keys.Length > 4)
                throw Error("Alternate combination requires 2–4 buttons.")
            for key in keys {
                if !RegExMatch(key, "^(?:[A-Z0-9]|F(?:[1-9]|1[0-9]|2[0-4])|Ctrl|Shift|Alt|RControl|RShift|RAlt|Space|Tab|Enter|Escape|Backspace|Delete|Insert|Home|End|PgUp|PgDn|Up|Down|Left|Right|Numpad[0-9]|LButton|RButton|MButton|XButton[12])$") || seen.Has(key)
                    throw Error("Unsupported alternate combination button.")
                seen[key] := true
            }
        }
        if identity != this.Identity
            this.Reset(), this.Identity := identity
        this.Enabled := enabled
        if enabled
            this.WindowMs := Integer(window), this.Double := double = "1", this.Behavior := behavior, this.Chord := keys
    }
    Observe() {
        route := this.Route, values := route.ParseSnapshot(route.LoadSnapshot())
        route.ValidateLifetime(values)
        if StrLower(values.Get("Exe", "")) != StrLower(route.ForegroundExe())
            throw Error("Alternate foreground differs.")
        this.Configure(values)
        return values
    }
    OnDown() {
        try {
            this.Observe()
            if !this.Enabled || !this.Double
                return
            now := this.Clock(), delta := now - this.LastDown
            if this.Released && delta >= 60 && delta <= this.WindowMs {
                if this.Behavior = "toggle"
                    this.Toggle := !this.Toggle
                else
                    this.DoubleHeld := true
                this.LastDown := -10000 ; A third press starts a new pair.
            } else
                this.LastDown := now, this.DoubleHeld := false
            this.Released := false
        } catch {
            this.Reset(), this.Enabled := false ; Optional gestures never refuse normal Hold.
        }
    }
    OnUp() {
        this.DoubleHeld := false, this.Released := true
    }
    Active() => this.Enabled && (this.DoubleHeld || this.Toggle || this.ChordHeld)
    Select(values) {
        if !this.Active()
            return false
        if values.Get("AltFile", "") = "" || !RegExMatch(values.Get("AltSHA256", ""), "^[a-f0-9]{64}$")
            throw Error("Alternate image identity missing.")
        values["File"] := values["AltFile"], values["SHA256"] := values["AltSHA256"]
        for field in ["size_mode", "size_value", "opacity", "monitor", "anchor", "offset_x", "offset_y"]
            if values.Has("Alt_" field)
                values[field] := values["Alt_" field]
        return true
    }
    Configured() {
        route := this.Route, host := route.Host, i := route.Slot
        return this.Enabled && route.Enabled && host.Enabled && i >= 1 && i <= host.Slots.Length
            && host.Slots[i].Enabled && host.Slots[i].Source = "Local" && host.Slots[i].Mode = "Hold"
            && !route.Children.Has(i)
    }
    Cancel() {
        if !this.Managed && this.ChordHeld
            this.Blocked := true, this.Token := 0
    }
    Keep(index) {
        return this.Configured() && index = this.Route.Slot && this.ChordHeld && !this.Blocked
    }
    End() {
        route := this.Route, host := route.Host, i := route.Slot
        if this.Token && host.Current = i && host.Generation = this.Token {
            held := route.HoldIntent()
            if held
                held.Token := host.Generation
            else if !route.KeepForLayer(i) {
                this.Managed := true
                try host.HideCurrent(true)
                finally this.Managed := false
            }
        }
        this.Token := 0
    }
    Tick() {
        route := this.Route, host := route.Host, i := route.Slot
        try {
            this.Observe()
            down := this.Configured() && this.Chord.Length > 0
            if down
                for key in this.Chord
                    if !this.KeyHeld(key) {
                        down := false
                        break
                    }
            this.ChordHeld := down
            if !down {
                this.End(), this.Blocked := false
                return
            }
            if this.Blocked
                return
            if host.Current && host.Current != i {
                this.Blocked := true, this.Token := 0
                return ; Another picture owner wins until this combination is released.
            }
            if host.Current = i {
                this.Token := host.Generation
                return
            }
            resolved := route.Resolve(i, host.Slots[i])
            if !this.Configured() || !this.ChordHeld || this.Blocked
                return
            this.Managed := true
            try this.Token := host.ShowSlot(i, resolved)
            finally this.Managed := false
            held := route.HoldIntent()
            if held && this.Token
                held.Token := this.Token
        } catch {
            this.ChordHeld := false
            this.End()
        }
    }
}
