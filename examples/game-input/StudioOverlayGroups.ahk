#Requires AutoHotkey v2.0
; Optional display-only adapter. No input hook, hotkey, remapping or runner.
; Constructed Off. Existing slot remains owner of Hold/Toggle/Timed behavior.
class StudioOverlayGroups {
    static Version := "0.1.0"
    __New(host) {
        this.Host := host, this.Enabled := false, this.Slot := 0
        this.Path := EnvGet("LOCALAPPDATA") "\GameToolHub\overlay-selection.ini"
        this.Timer := this.Tick.Bind(this), this.Gui := 0, this.LastAsset := ""
    }
    Open(*) {
        if this.Gui {
            this.Gui.Show()
            return
        }
        g := Gui("+Resize", "Automatic overlay groups — optional display route")
        g.SetFont("s10", "Segoe UI")
        g.AddText("w600", "Hub owns game/group/layer/view selection. Supported Azeron logs can track layer events; fresh native snapshots remain unverified. See Hub for the layer source/state. Existing picture triggers remain unchanged. #19 stays unassigned.")
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
        state := g.AddText("xm y+12 w600", "Off. Enabling affects display only; it does not rewrite settings or native profiles.")
        arm := g.AddCheckBox("xm y+8", "Enable route for this session (Off at launch)")
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
                if i < 1 || i > this.Host.Slots.Length || this.Host.Slots[i].Source != "Local"
                    throw Error("Choose an existing local picture slot.")
                this.Slot := i, this.Path := path.Value
                if !RegExMatch(this.Path, "i)^[a-z]:\\")
                    throw Error("Use an absolute local relay path.")
                this.Enabled := true
                SetTimer(this.Timer, 200)
                state.Text := "Enabled for slot " i "; waiting for fresh matching foreground relay. See Hub for Selected/Event-tracked/Unknown layer state."
            } else {
                this.Stop()
                state.Text := "Off. Original slot behavior preserved."
            }
        } catch as err {
            arm.Value := 0, this.Stop(), state.Text := err.Message
        }
    }
    Read() {
        if !FileExist(this.Path) || FileGetSize(this.Path) > 16384
            throw Error("Display relay unavailable.")
        attr := DllCall("GetFileAttributesW", "str", this.Path, "uint")
        if attr = 0xFFFFFFFF || (attr & 0x400)
            throw Error("Linked relay refused.")
        snapshot := FileRead(this.Path, "UTF-8")
        now := DateDiff(A_NowUTC, "19700101000000", "Seconds")
        expiry := Integer(IniRead(this.Path, "Overlay", "ExpiresUnix", 0))
        if IniRead(this.Path, "Overlay", "Schema", 0) != 1 || IniRead(this.Path, "Overlay", "Active", 0) != 1
            || expiry <= now || expiry > now + 2
            throw Error("Inactive or stale selection; no old action map displayed.")
        exe := IniRead(this.Path, "Overlay", "Exe", "")
        if exe = "" || StrLower(exe) != StrLower(WinGetProcessPath("A"))
            throw Error("Foreground game differs from the selection.")
        relayImage := IniRead(this.Path, "Overlay", "File", "")
        if !FileExist(relayImage) || FileGetSize(relayImage) > 16777216
            throw Error("Overlay image unavailable.")
        attrs := DllCall("GetFileAttributesW", "str", relayImage, "uint")
        hash := IniRead(this.Path, "Overlay", "SHA256", "")
        if attrs = 0xFFFFFFFF || (attrs & 0x410) || !RegExMatch(hash, "^[a-f0-9]{64}$")
            || StrLower(PM_Model.Sha256(relayImage)) != hash
            throw Error("Image identity mismatch.")
        if FileRead(this.Path, "UTF-8") != snapshot
            throw Error("Display selection changed while reading.")
        return {File: relayImage, Hash: hash, Snapshot: snapshot}
    }
    Resolve(index, legacy) {
        if !this.Enabled || index != this.Slot || legacy.Source != "Local"
            return legacy
        source := this.Read()
        result := PM_Model.Clone(legacy)
        result.File := source.File
        result.SizeMode := IniRead(this.Path, "Overlay", "size_mode", "Pixels")
        result.SizeValue := Number(IniRead(this.Path, "Overlay", "size_value", 600))
        result.Width := result.SizeValue
        result.Opacity := Number(IniRead(this.Path, "Overlay", "opacity", 85))
        result.Monitor := Integer(IniRead(this.Path, "Overlay", "monitor", 1))
        result.Position := IniRead(this.Path, "Overlay", "anchor", "TopRight")
        result.OffsetX := Number(IniRead(this.Path, "Overlay", "offset_x", 0))
        result.OffsetY := Number(IniRead(this.Path, "Overlay", "offset_y", 0))
        if !PM_Model.ExactHas("Pixels,Screen width %,Screen height %,Original %", result.SizeMode)
            || !PM_Model.ExactHas("TopLeft,TopRight,Center,BottomLeft,BottomRight", result.Position)
            || result.SizeValue < 1 || result.SizeValue > 8000 || result.Opacity < 5 || result.Opacity > 100
            || result.Monitor < 1 || result.Monitor > MonitorGetCount()
            throw Error("Invalid display geometry.")
        if FileRead(this.Path, "UTF-8") != source.Snapshot
            throw Error("Display selection changed while resolving.")
        this.LastAsset := source.Snapshot
        return result ; Never alters Mode, trigger, Enabled, MIC or native output.
    }
    Tick(*) {
        if !this.Enabled || !this.Host.Enabled || this.Host.Current != this.Slot
            return
        try {
            source := this.Read()
            ; Ignore expiry heartbeat alone; redraw only actual display changes.
            compare := RegExReplace(source.Snapshot, "m)^ExpiresUnix\s*=.*$", "")
            previous := RegExReplace(this.LastAsset, "m)^ExpiresUnix\s*=.*$", "")
            if compare != previous {
                result := this.Resolve(this.Slot, this.Host.Slots[this.Slot])
                ; Replace only the owned picture GUI; retain token/mode/release.
                if this.Host.PictureGui
                    this.Host.PictureGui.Destroy(), this.Host.PictureGui := 0
                if !this.Host.ShowLocal(result)
                    this.Host.HideCurrent()
            }
        } catch {
            this.Host.HideCurrent()
        }
    }
    Stop(*) {
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
