#Requires AutoHotkey v2.0
; Optional Picture Buttons extension for the existing Studio 2 host.
; Adapted from the user's exact Studio 3 preview src/model/ui/library/runtime.
; Exact generated Studio 3 SHA-256:
; 2562D2669B2FDA0F78022E4C5E042AAEA9B5DE3CC2FA13695971CECE63412A07
; Construction is read-only: no GUI, directories, timers, hotkeys or input.
; The legacy INI and native device/game profiles are NEVER written here.
; Profile attachments are opaque data, not native imports or evidence of layers.

; Shared native presentation boundary; controls/data remain owned by Studio.
; Session-only layout/disclosure state does not migrate or write an INI.
class StudioNativeLayout {
    static Move(ctl, x, y, width, height) {
        ; For native dropdowns, Height is the entire popup-list height, NOT the
        ; closed field height. Preserve their default list sizing during reflow.
        if ctl.Type = "DDL" || ctl.Type = "DropDownList" || ctl.Type = "ComboBox"
            ctl.Move(Round(x), Round(y), Max(1, Round(width)))
        else
            ctl.Move(Round(x), Round(y), Max(1, Round(width)), height)
    }
}

class StudioPictureEditor {
    __New(host, gui) {
        this.Host := host, this.Gui := gui, this.Mode := "Modern", this.Expanded := false
        this.Width := 976, this.Height := 733, this.Busy := false
        this.RepaintFn := this.Repaint.Bind(this)
        this.Legacy := [], this.Labels := Map(), this.Actions := Map()
        for ctl in gui {
            ctl.GetPos(&x, &y, &w, &h)
            if y < 110 || ctl.Text = "?"
                continue
            this.Legacy.Push({Control: ctl, X: x, Y: y, W: w, H: h})
            if ctl.Type = "Text"
                this.Labels[ctl.Text] := ctl
            else if ctl.Type = "Button"
                this.Actions[ctl.Text] := ctl
        }
        this.Heading := gui.AddText("x32 y113 w420 h30 c16293D", "Picture Buttons")
        this.Heading.SetFont("s16 bold", "Segoe UI")
        this.LayoutLabel := gui.AddText("x710 y117 w66 h23", "Layout")
        this.LayoutChoice := gui.AddDropDownList("x777 y114 w163", ["Modern", "Classic"])
        this.LayoutChoice.Choose(1)
        this.LayoutChoice.OnEvent("Change", this.ChangeLayout.Bind(this))
        this.Disclosure := gui.AddButton("x32 y535 w235 h30", "Show display settings")
        this.Disclosure.OnEvent("Click", this.ToggleDetails.Bind(this))
        this.FitButton := gui.AddButton("x800 y313 w140 h30", "Fit columns")
        this.FitButton.OnEvent("Click", this.FitColumns.Bind(this))
        this.DraftStatus := gui.AddText("x32 y575 w880 h24 c36536B", "Saved slot • Preview does not save")
        host.PictureLayout := this.LayoutChoice, host.PictureDraftStatus := this.DraftStatus
        for name in StrSplit("FName,FEnabled,FKey,FMode,FFile,FMicCanvas,FPass,FWidth,FOpacity,FPosition,FOffsetX,FOffsetY,FDuration", ",") {
            ctl := host.%name%
            ctl.OnEvent(ctl.Type = "CheckBox" ? "Click" : "Change", this.DraftChanged.Bind(this))
        }
        this.ModernControls := [this.Heading, this.LayoutLabel, this.LayoutChoice, this.Disclosure, this.FitButton, this.DraftStatus]
    }
    ChangeLayout(*) {
        this.Mode := this.LayoutChoice.Text
        this.Reflow()
    }
    ToggleDetails(*) {
        this.Expanded := !this.Expanded
        this.Disclosure.Text := this.Expanded ? "Hide display settings" : "Show display settings"
        this.Reflow()
    }
    DraftChanged(control, *) {
        this.UpdateDraftStatus()
        if control = this.Host.FMode
            this.Reflow()
    }
    UpdateDraftStatus() {
        if !this.Host.Slots.Length
            return
        changed := false, draft := this.Host.ReadCurrentSlot()
        for field, value in this.Host.Slots[this.Host.Selected].OwnProps()
            if draft.%field% "" != value ""
                changed := true
        this.DraftStatus.Text := "Slot " this.Host.Selected " / " this.Host.Slots.Length " • " (changed ? "Unsaved edits — Save slot to apply" : "Saved slot") " • Preview does not save"
    }
    OnSize(gui, state, width, height) {
        if state = -1
            return
        this.Width := width, this.Height := height
        this.Reflow()
    }
    Repaint(*) {
        ; Tab3 finishes its own visibility update after Change returns. A single
        ; deferred repaint keeps newly revealed dropdown text visible. It does
        ; not reflow, recreate controls or enqueue another callback.
        if WinExist("ahk_id " this.Gui.Hwnd)
            DllCall("RedrawWindow", "ptr", this.Gui.Hwnd, "ptr", 0, "ptr", 0, "uint", 0x185)
    }
    Place(ctl, x, y, width, height := 28, visible := true) {
        StudioNativeLayout.Move(ctl, x, y, width, height)
        ctl.Visible := visible && this.Host.Tabs.Value = 1
    }
    Field(name, label, x, y, width, visible := true) {
        this.Place(this.Labels[label], x, y, width, 22, visible)
        this.Place(this.Host.%name%, x, y + 24, width, 28, visible)
    }
    FitColumns(*) {
        ; Only an explicit view action adjusts columns; resizing never discards
        ; a user's naturally dragged column widths, including horizontal scroll.
        available := Max(640, this.Width - 64)
        for index, width in [32, 42, Max(145, available * .23), 85, 82, 78, Max(170, available * .30)]
            this.Host.List.ModifyCol(index, Round(width))
    }
    Reflow(*) {
        if this.Busy || !this.Host.HasOwnProp("BottomText")
            return
        this.Busy := true
        try {
            h := this.Host, modern := this.Mode = "Modern", page := h.Tabs.Value = 1
            micPage := h.HasOwnProp("MicEditor") && h.Tabs.Value = 2
            micModern := micPage && h.MicEditor.Mode = "Modern"
            minWidth := (modern && page) || micModern ? 700 : 976
            width := Max(minWidth, this.Width)
            narrow := width < 850
            sourceLocal := h.FSource.Text = "Local"
            extra := this.Expanded ? 124 : (h.FMode.Text = "Timed" ? 62 : 0)
            tableHeight := Max(110, Min(220, this.Height - (narrow ? 701 : 667) - extra))
            y := 180 + tableHeight + 48
            ; Publish the true minimum, not the current flexible table height;
            ; otherwise enlarging once would prevent shrinking the pane again.
            minHeight := modern && page ? (narrow ? 811 : 777) + extra : 733
            if micModern
                minHeight := h.MicEditor.MinimumHeight(narrow)
            height := Max(minHeight, this.Height)
            h.Tabs.Move(15, 75, width - 32, height - 159)
            h.RunText.Move(18, 43, width - 42, 22)
            h.TitleText.Move(18, 13, width - 140, 27)
            h.BottomText.Move(23, height - 67, width - 240, 44)
            h.HideButton.Move(width - 199, height - 67, 90, 30)
            h.ExitButton.Move(width - 97, height - 67, 77, 30)
            for control in this.Gui
                if control.Type = "Button" && control.Text = "? UI IDs"
                    control.Move(width - 104, 12, 80, 25)
            for ctl in this.ModernControls
                ctl.Visible := page && (modern || ctl = this.LayoutChoice || ctl = this.LayoutLabel)
            if !modern || !page {
                for item in this.Legacy {
                    StudioNativeLayout.Move(item.Control, item.X, item.Y, item.W, item.H)
                    item.Control.Visible := page
                }
                this.LayoutLabel.Move(width - 267, 116, 65, 23)
                this.LayoutChoice.Move(width - 195, 114, 163)
                if page
                    this.Labels["Each enabled trigger can show a local picture OR a saved Multi Image Canvas tab."].Move(36, 116, width - 326, 44)
            } else {
                ; Clear prior visibility, then expose only the relevant content.
                for item in this.Legacy
                    item.Control.Visible := false
                this.Place(this.Heading, 32, 113, width - 325, 30)
                this.Place(this.LayoutLabel, width - 267, 117, 65, 22)
                this.Place(this.LayoutChoice, width - 195, 114, 163)
                subtitle := this.Labels["Each enabled trigger can show a local picture OR a saved Multi Image Canvas tab."]
                this.Place(subtitle, 32, 148, width - 64, 23)
                this.Place(h.List, 32, 180, width - 64, tableHeight)
                this.Place(this.Actions["+ Add slot"], 32, y - 36, 120, 30)
                this.Place(this.Actions["Remove slot"], 164, y - 36, 120, 30)
                this.Place(this.FitButton, width - 172, y - 36, 140, 30)
                nameWidth := narrow ? width - 198 : width - 498
                this.Field("FName", "Name", 32, y, nameWidth)
                this.Place(h.FEnabled, 48 + nameWidth, y + 24, 112)
                if !narrow {
                    this.Field("FSource", "Source", width - 340, y, 148)
                    this.Field("FMode", "Mode", width - 180, y, 148)
                }
                y += 62
                this.Field("FKey", "Trigger key", 32, y, 108)
                this.Place(this.Actions["Record key"], 152, y + 24, 118)
                if narrow {
                    this.Field("FSource", "Source", 288, y, 168)
                    this.Field("FMode", "Mode", 472, y, width - 504)
                    y += 62
                    this.Place(h.FPass, 32, y, width - 64)
                    y += 34
                } else {
                    this.Place(h.FPass, 298, y + 24, width - 330)
                    y += 62
                }
                this.Field("FFile", "Local picture file (PNG/JPG/BMP/GIF/TIF)", 32, y, width - 188, sourceLocal)
                this.Place(this.Actions["Browse..."], width - 144, y + 24, 112, 28, sourceLocal)
                this.Field("FMicCanvas", "MIC tab key (optional)", 32, y, 184, !sourceLocal)
                this.Place(this.Labels["Used only for MIC source. Set the tab's Set switch key first."], 232, y + 24, width - 264, 36, !sourceLocal)
                y += 66
                this.Place(this.Disclosure, 32, y, 230, 30)
                y += 38
                if this.Expanded {
                    cell := (width - 104) / 5
                    for index, spec in [["FWidth", "Width px"], ["FOpacity", "Opacity %"], ["FPosition", "Position"], ["FOffsetX", "Offset X"], ["FOffsetY", "Offset Y"]]
                        this.Field(spec[1], spec[2], 32 + (index - 1) * (cell + 10), y, cell)
                    y += 62
                }
                if this.Expanded || h.FMode.Text = "Timed" {
                    this.Field("FDuration", "Timed sec", 32, y, 160)
                    y += 62
                }
                this.Place(this.DraftStatus, 32, y, width - 64, 25)
                y += 31
                this.Place(this.Actions["SAVE SLOT"], 32, y, 138, 32)
                this.Place(this.Actions["PREVIEW CURRENT EDITS"], 182, y, 230, 32)
                y += 42
                this.Place(this.Actions["Advanced pictures / Library"], 32, y, (width - 76) / 2, 32)
                this.Place(this.Actions["Automatic overlay groups…"], 44 + (width - 76) / 2, y, (width - 76) / 2, 32)
            }
            if h.HasOwnProp("MicEditor")
                h.MicEditor.Reflow(width, narrow)
            ; Owner-scoped display dimensions, not a command/input channel.
            dpi := DllCall("GetDpiForWindow", "ptr", this.Gui.Hwnd, "uint") / 96
            DllCall("SetPropW", "ptr", this.Gui.Hwnd, "str", "GameTools.Studio.MinWidth", "ptr", Round(minWidth * dpi))
            DllCall("SetPropW", "ptr", this.Gui.Hwnd, "str", "GameTools.Studio.MinHeight", "ptr", Round(minHeight * dpi))
            if !h.HubBridge.Parent {
                this.Gui.Opt("+MinSize" minWidth "x" minHeight)
                if this.Width < width || this.Height < minHeight
                    this.Gui.Show("w" width " h" height " NoActivate")
            }
            if h.HasOwnProp("Feedback")
                h.Feedback.RefreshPositions()
            this.UpdateDraftStatus()
            ; Tab3's native background can otherwise leave moved dropdowns
            ; visually blank after disclosure/resize. Repaint this owned GUI,
            ; not the desktop or any overlay. Typing does not trigger reflow.
            DllCall("RedrawWindow", "ptr", this.Gui.Hwnd, "ptr", 0, "ptr", 0, "uint", 0x185)
            SetTimer(this.RepaintFn, -1)
        } finally this.Busy := false
    }
}

; MIC is a bridge to the external canvas application, not a second canvas engine.
; Reuse every original operational control/callback. Only presentation is owned
; here; moving tabs, changing layout or expanding the guide never sends keys,
; saves a shortcut, marks an overlay hidden or writes a preference/profile.
class StudioMicEditor {
    __New(host, gui) {
        this.Host := host, this.Gui := gui, this.Mode := "Modern", this.Expanded := false
        this.Legacy := []
        for name in StrSplit("MicIntro,MicText,MicShortcutLabel,MicHotkeyField,MicSaveButton,MicShortcutHint,MicTestButton,MicHiddenButton,MicWebsiteButton,MicGuide,MicLocalHint", ",") {
            ctl := host.%name%
            ctl.GetPos(&x, &y, &w, &height)
            this.Legacy.Push({Control: ctl, X: x, Y: y, W: w, H: height})
        }
        this.Heading := gui.AddText("x32 y113 w420 h30 c16293D", "Multi Image Canvas")
        this.Heading.SetFont("s16 bold", "Segoe UI")
        this.LayoutLabel := gui.AddText("x710 y117 w66 h23", "Layout")
        this.LayoutChoice := gui.AddRadio("x777 y114 w80 h28 Group Checked", "Modern")
        this.ClassicChoice := gui.AddRadio("x860 y114 w80 h28", "Classic")
        this.LayoutChoice.OnEvent("Click", this.ChangeLayout.Bind(this))
        this.ClassicChoice.OnEvent("Click", this.ChangeLayout.Bind(this))
        this.ShortcutHeading := gui.AddText("x32 y246 w600 h23 c16293D", "1. Match MIC's overlay shortcut")
        this.ShortcutHeading.SetFont("bold")
        this.DraftStatus := gui.AddText("x32 y336 w850 h25 c36536B", "")
        this.ActionsHeading := gui.AddText("x32 y414 w700 h23 c16293D", "2. Check visibility, then connect a picture slot")
        this.ActionsHeading.SetFont("bold")
        this.Warning := gui.AddText("x32 y443 w850 h40 cAE4B27", "MIC running does not prove its overlay is hidden. Manual toggles can desynchronize Hold; mark hidden only after confirming it is hidden.")
        this.PictureButton := gui.AddButton("x700 y492 w210 h32", "Go to Picture buttons")
        this.PictureButton.OnEvent("Click", this.OpenPictures.Bind(this))
        this.Disclosure := gui.AddButton("x32 y536 w270 h30", "Show canvas / Hold setup guide")
        this.Disclosure.OnEvent("Click", this.ToggleGuide.Bind(this))
        this.ModernControls := [this.Heading, this.LayoutLabel, this.LayoutChoice, this.ClassicChoice, this.ShortcutHeading,
            this.DraftStatus, this.ActionsHeading, this.Warning, this.PictureButton, this.Disclosure]
        host.MicHotkeyField.OnEvent("Change", this.UpdateDraftStatus.Bind(this))
        this.UpdateDraftStatus()
    }
    ChangeLayout(*) {
        this.Mode := this.ClassicChoice.Value ? "Classic" : "Modern"
        this.Host.PictureEditor.Reflow()
    }
    ToggleGuide(*) {
        this.Expanded := !this.Expanded
        this.Disclosure.Text := this.Expanded ? "Hide canvas / Hold setup guide" : "Show canvas / Hold setup guide"
        this.Host.PictureEditor.Reflow()
    }
    OpenPictures(*) {
        this.Host.Tabs.Choose(1)
        this.Host.PictureEditor.Reflow()
    }
    UpdateDraftStatus(*) {
        saved := this.Host.MicToggle
        ; Native Hotkey may normalize modifier order/case when assigning Value.
        ; Compare semantic identity, without rewriting either saved or draft data.
        changed := this.ShortcutIdentity(this.ReadShortcut()) != this.ShortcutIdentity(saved)
        ; Build modifier names separately; never reinterpret '+' in those names.
        readable := ""
        for pair in [["^", "Ctrl+"], ["!", "Alt+"], ["+", "Shift+"], ["#", "Win+"]]
            if InStr(saved, pair[1])
                readable .= pair[2]
        readable .= StrUpper(RegExReplace(saved, "[\^!+#]"))
        this.DraftStatus.Text := (changed ? "Unsaved shortcut — Save MIC shortcut to apply" : "Saved shortcut") " • Active: " readable
    }
    ShortcutIdentity(combo) {
        result := ""
        for symbol in ["^", "!", "+", "#"]
            if InStr(combo, symbol)
                result .= symbol
        return result StrLower(RegExReplace(combo, "[\^!+#]"))
    }
    ReadShortcut() {
        ; A native Hotkey Value can spell letter keys in the active Hebrew (or
        ; other) layout. Read this owned widget's VK for ASCII physical letters;
        ; do not change the keyboard layout or send input to any application.
        value := this.Host.MicHotkeyField.Value
        raw := SendMessage(0x0402, 0, 0, this.Host.MicHotkeyField) ; HKM_GETHOTKEY
        vk := raw & 0xFF
        if vk >= 0x41 && vk <= 0x5A {
            modifiers := raw >> 8
            return (modifiers & 2 ? "^" : "") (modifiers & 4 ? "!" : "") (modifiers & 1 ? "+" : "") Chr(vk)
        }
        return value
    }
    MinimumHeight(narrow) {
        return (narrow ? 775 : 733) + (this.Expanded ? (narrow ? 245 : 200) : 0)
    }
    Place(ctl, x, y, width, height := 28, visible := true) {
        StudioNativeLayout.Move(ctl, x, y, width, height)
        ctl.Visible := visible && this.Host.Tabs.Value = 2
    }
    Reflow(width, narrow) {
        h := this.Host, page := h.Tabs.Value = 2, modern := this.Mode = "Modern"
        for ctl in this.ModernControls
            ctl.Visible := page && (modern || ctl = this.LayoutChoice || ctl = this.ClassicChoice || ctl = this.LayoutLabel || ctl = this.DraftStatus)
        if !modern || !page {
            for item in this.Legacy {
                StudioNativeLayout.Move(item.Control, item.X, item.Y, item.W, item.H)
                item.Control.Visible := page
            }
            this.LayoutLabel.Move(width - 267, 116, 65, 23)
            this.LayoutChoice.Move(width - 195, 114, 80, 28)
            this.ClassicChoice.Move(width - 112, 114, 80, 28)
            this.DraftStatus.Move(32, 610, width - 64, 25)
            if page
                h.MicIntro.Move(38, 115, width - 330, 45)
        } else {
            this.Place(this.Heading, 32, 113, width - 325, 30)
            this.Place(this.LayoutLabel, width - 267, 117, 65, 23)
            this.Place(this.LayoutChoice, width - 195, 114, 80)
            this.Place(this.ClassicChoice, width - 112, 114, 80)
            this.Place(h.MicIntro, 32, 151, width - 64, 44)
            this.Place(h.MicText, 32, 205, width - 64, 36)
            this.Place(this.ShortcutHeading, 32, 250, width - 64, 23)
            this.Place(h.MicShortcutLabel, 32, 280, width - 64, 22)
            this.Place(h.MicHotkeyField, 32, 306, narrow ? 200 : 250, 28)
            this.Place(h.MicSaveButton, narrow ? 244 : 294, 304, 215, 32)
            this.Place(this.DraftStatus, 32, 344, width - 64, 25)
            this.Place(h.MicShortcutHint, 32, 378, width - 64, 35)
            this.Place(this.ActionsHeading, 32, 425, width - 64, 23)
            this.Place(this.Warning, 32, 453, width - 64, 40)
            buttons := [h.MicTestButton, h.MicHiddenButton, h.MicWebsiteButton, this.PictureButton]
            columns := narrow ? 2 : 4
            buttonWidth := (width - 64 - (columns - 1) * 12) / columns
            for index, ctl in buttons
                this.Place(ctl, 32 + Mod(index - 1, columns) * (buttonWidth + 12), 506 + Floor((index - 1) / columns) * 42, buttonWidth, 32)
            guideY := narrow ? 590 : 548
            this.Place(this.Disclosure, 32, guideY, 285, 30)
            this.Place(h.MicGuide, 32, guideY + 40, width - 64, narrow ? 230 : 185, this.Expanded)
            hintY := guideY + 40 + (this.Expanded ? (narrow ? 245 : 200) : 0)
            this.Place(h.MicLocalHint, 32, hintY, width - 64, 44)
        }
        this.UpdateDraftStatus()
    }
}

class PM_Model {
    static Fields := StrSplit("File,Width,Opacity,Position,OffsetX,OffsetY,Mode,Duration,SizeMode,SizeValue,Monitor,Asset,Profile,FollowAsset,Pins,Device,Game,Exe,Keymap,Layer,LayerKey,Notes", ",")
    static MetaFields := StrSplit("Device,Game,Exe,Keymap,Layer,LayerKey", ",")
    static Has(list, value) {
        for item in StrSplit(list, ",")
            if StrLower(Trim(item)) = StrLower(value)
                return true
        return false
    }
    static ExactHas(list, value) {
        for item in StrSplit(list, ",")
            if item == value
                return true
        return false
    }
    static Clone(value) {
        if value is Map {
            result := Map()
            for k, v in value
                result[k] := this.Clone(v)
            return result
        }
        if value is Array {
            result := []
            for v in value
                result.Push(this.Clone(v))
            return result
        }
        if IsObject(value) {
            result := {}
            for k, v in value.OwnProps()
                result.%k% := this.Clone(v)
            return result
        }
        return value
    }
    static Resolve(variants, id, base, visited := 0) {
        if !variants.Has(id)
            throw Error("Missing appearance variant: " id)
        if !IsObject(visited)
            visited := Map()
        if visited.Has(id) || visited.Count >= 16
            throw Error("Appearance inheritance cycle or more than 16 levels.")
        visited[id] := true
        own := variants[id]
        result := own.Parent = "" ? this.Clone(base) : this.Resolve(variants, own.Parent, base, visited)
        for field, value in own.Overrides {
            canonical := false
            for allowed in this.Fields
                if field == allowed
                    canonical := true
            if !canonical
                throw Error("Field cannot be overridden: " field)
            result[field] := value
        }
        return result
    }
    static Join(items, sep := ", ") {
        result := ""
        for item in items
            result .= (result = "" ? "" : sep) item
        return result
    }
    static ResolveMetadata(values, assets) {
        result := this.Clone(values)
        if !result["FollowAsset"]
            return result
        ; Own/pinned fields win; profile metadata precedes image metadata.
        for ref in [result["Profile"], result["Asset"]] {
            if ref = "" || !assets.Has(ref)
                continue
            for field in this.MetaFields
                if result[field] = "" && !this.Has(result["Pins"], field)
                    result[field] := assets[ref].%field%
        }
        return result
    }
    static Owns(variants, id, field, depth := 0) {
        if depth >= 16 || !variants.Has(id)
            throw Error("Invalid inheritance while resolving size fallback.")
        own := variants[id]
        return own.Overrides.Has(field) || (own.Parent != "" && this.Owns(variants, own.Parent, field, depth + 1))
    }
    static MatchesExe(rule, exe) {
        if Trim(rule) = ""
            return true
        if exe = "" || exe = "Unknown"
            return false
        for name in StrSplit(rule, ";")
            if StrLower(Trim(name)) = StrLower(exe)
                return true
        return false
    }
    static Pick(variants, base, assets, ctx, preferred := "") {
        matches := [], best := -1
        for id, variant in variants {
            s := this.ResolveMetadata(this.Resolve(variants, id, base), assets)
            if !this.MatchesExe(s["Exe"], ctx.Exe)
                continue
            if s["Layer"] != "" && (ctx.Layer = "Unknown" || StrLower(s["Layer"]) != StrLower(ctx.Layer))
                continue
            if s["Device"] != "" && (ctx.Device = "Unknown" || StrLower(s["Device"]) != StrLower(ctx.Device))
                continue
            score := (s["Exe"] != "" ? 4 : 0) + (s["Layer"] != "" ? 2 : 0) + (s["Device"] != "" ? 1 : 0)
            if score > best
                best := score, matches := [id]
            else if score = best
                matches.Push(id)
        }
        if matches.Length = 1
            return {Id: matches[1], Reason: "Unique explicit help-context match; not native layer detection."}
        if matches.Length > 1 && preferred != ""
            for id in matches
                if id = preferred
                    return {Id: id, Reason: "Explicit preferred help option among equal matches."}
        return {Id: "", Reason: matches.Length ? "Ambiguous help context; choose a variant manually." : "No help-context match; required state may be Unknown."}
    }
    static SizeFor(mode, value, iw, ih, mw, mh) {
        if Min(iw, ih, mw, mh, value) <= 0 || mw <= 32 || mh <= 32
            throw Error("Invalid image, size or monitor dimensions.")
        if !(mode == "Pixels" || mode == "Screen width %" || mode == "Screen height %" || mode == "Original %")
            throw Error("Unknown size mode.")
        w := mode = "Screen width %" ? mw * value / 100
            : mode = "Screen height %" ? mh * value / 100 * iw / ih
            : mode = "Original %" ? iw * value / 100 : value
        h := w * ih / iw
        scale := Min(1, (mw - 32) / w, (mh - 32) / h)
        return [Max(1, Round(w * scale)), Max(1, Round(h * scale))]
    }
    static Sha256(path) {
        provider := 0, hash := 0
        if !DllCall("advapi32\CryptAcquireContextW", "ptr*", &provider, "ptr", 0, "ptr", 0, "uint", 24, "uint", 0xF0000000)
            throw OSError()
        try {
            if !DllCall("advapi32\CryptCreateHash", "ptr", provider, "uint", 0x800C, "ptr", 0, "uint", 0, "ptr*", &hash)
                throw OSError()
            f := FileOpen(path, "r")
            if !f
                throw Error("Cannot read selected file.")
            try {
                buf := Buffer(524288)
                while count := f.RawRead(buf, buf.Size)
                    if !DllCall("advapi32\CryptHashData", "ptr", hash, "ptr", buf, "uint", count, "uint", 0)
                        throw OSError()
            } finally f.Close()
            digest := Buffer(32), size := 32
            if !DllCall("advapi32\CryptGetHashParam", "ptr", hash, "uint", 2, "ptr", digest, "uint*", &size, "uint", 0)
                throw OSError()
            result := ""
            Loop 32
                result .= Format("{:02x}", NumGet(digest, A_Index - 1, "uchar"))
            return result
        } finally {
            if hash
                DllCall("advapi32\CryptDestroyHash", "ptr", hash)
            DllCall("advapi32\CryptReleaseContext", "ptr", provider, "uint", 0)
        }
    }
    static ImageSize(path) {
        kind := 0, h := LoadPicture(path, "", &kind)
        if !h || kind != 0 {
            if h
                DllCall("DestroyIcon", "ptr", h)
            throw Error("Cannot decode bitmap image.")
        }
        try {
            data := Buffer(A_PtrSize = 8 ? 32 : 24, 0)
            if !DllCall("gdi32\GetObjectW", "ptr", h, "int", data.Size, "ptr", data)
                throw OSError()
            return [NumGet(data, 4, "int"), Abs(NumGet(data, 8, "int"))]
        } finally DllCall("gdi32\DeleteObject", "ptr", h)
    }
    static HashText(text) {
        provider := 0, hash := 0
        if !DllCall("advapi32\CryptAcquireContextW", "ptr*", &provider, "ptr", 0, "ptr", 0, "uint", 24, "uint", 0xF0000000)
            throw OSError()
        try {
            if !DllCall("advapi32\CryptCreateHash", "ptr", provider, "uint", 0x800C, "ptr", 0, "uint", 0, "ptr*", &hash)
                throw OSError()
            if !DllCall("advapi32\CryptHashData", "ptr", hash, "ptr", StrPtr(text), "uint", StrLen(text) * 2, "uint", 0)
                throw OSError()
            digest := Buffer(32), size := 32
            if !DllCall("advapi32\CryptGetHashParam", "ptr", hash, "uint", 2, "ptr", digest, "uint*", &size, "uint", 0)
                throw OSError()
            result := ""
            Loop 32
                result .= Format("{:02x}", NumGet(digest, A_Index - 1, "uchar"))
            return result
        } finally {
            if hash
                DllCall("advapi32\CryptDestroyHash", "ptr", hash)
            DllCall("advapi32\CryptReleaseContext", "ptr", provider, "uint", 0)
        }
    }
    static Text(value, limit := 2048) {
        if IsObject(value) || StrLen(value "") > limit || RegExMatch(value "", "[\x00-\x1f]")
            throw Error("Invalid or oversized text value.")
        return value ""
    }
    static Encode(value) {
        value := this.Text(value), result := "hex:"
        Loop StrLen(value)
            result .= Format("{:04x}", NumGet(StrPtr(value), (A_Index - 1) * 2, "ushort"))
        return result
    }
    static Decode(value) {
        if SubStr(value, 1, 4) != "hex:" || !RegExMatch(SubStr(value, 5), "^(?:[0-9a-f]{4})*$") || StrLen(value) > 8196
            throw Error("Invalid advanced text encoding.")
        result := "", encoded := SubStr(value, 5)
        Loop StrLen(encoded) // 4
            result .= Chr(Integer("0x" SubStr(encoded, (A_Index - 1) * 4 + 1, 4)))
        return this.Text(result)
    }
}

class StudioPictureModule {
    static Version := "0.1.0-preview.1"
    __New(host, options := 0) {
        this.Host := host, this.Options := IsObject(options) ? options : {}
        this.Path := this.Options.HasOwnProp("Path") ? this.Options.Path : host.Dir "\pictures-v3.ini"
        this.AssetDir := this.Options.HasOwnProp("AssetDir") ? this.Options.AssetDir : host.Dir "\picture-assets"
        this.Records := Map(), this.Assets := Map(), this.NextId := 1
        this.Gui := 0, this.PreviewGui := 0, this.PreviewTimer := 0, this.Selected := 0
        this.Editor := Map(), this.Checks := Map(), this.LoadError := "", this.Dirty := false
        this.Context := {Exe: "Unknown", Layer: "Unknown", Device: "Unknown"}
        this.SourceHash := ""
        this.EditDirty := false, this.LoadingEditor := false, this.EditVariantId := "base"
        this.ImageReader := this.Options.HasOwnProp("ImageSize") ? this.Options.ImageSize : PM_Model.ImageSize.Bind(PM_Model)
        this.MonitorReader := this.Options.HasOwnProp("MonitorBounds") ? this.Options.MonitorBounds : 0
        if FileExist(this.Path) {
            try {
                if DirExist(this.Path) || FileGetSize(this.Path) > 1048576
                    throw Error("Invalid or oversized advanced sidecar.")
                this.SourceHash := PM_Model.Sha256(this.Path)
                if !(this.Options.HasOwnProp("SkipLoad") && this.Options.SkipLoad)
                    this.Load()
            }
            catch Error as err {
                this.Records := Map(), this.Assets := Map(), this.LoadError := err.Message
            }
        }
    }
    Identity(index) {
        s := this.Host.Slots[index]
        return PM_Model.Text(s.Name) "|" PM_Model.Text(s.Key) "|" PM_Model.Text(s.Source)
    }
    BaseRecord(index) {
        if index < 1 || index > this.Host.Slots.Length
            throw Error("Legacy picture slot does not exist.")
        key := index ""
        if !this.Records.Has(key)
            this.Records[key] := {Identity: this.Identity(index), Selected: "base", Orphaned: 0, AutoHelp: 0,
                Variants: Map("base", {Id: "base", Name: "Base appearance", Parent: "", Overrides: Map()})}
        return this.Records[key]
    }
    BaseValues(index, legacyDraft := 0) {
        s := IsObject(legacyDraft) ? legacyDraft : this.Host.Slots[index]
        values := Map("File", s.File, "Width", s.Width, "Opacity", s.Opacity, "Position", s.Position,
            "OffsetX", s.OffsetX, "OffsetY", s.OffsetY, "Mode", s.Mode, "Duration", s.Duration,
            "SizeMode", "Pixels", "SizeValue", s.Width, "Monitor", "Primary", "Asset", "", "Profile", "",
            "FollowAsset", 1, "Pins", "", "Device", "", "Game", "", "Exe", "", "Keymap", "",
            "Layer", "", "LayerKey", "", "Notes", "")
        return values
    }
    AddVariant(index, name, parent := "base") {
        this.Writable()
        record := this.BaseRecord(index)
        if record.Orphaned || !record.Variants.Has(parent) || record.Variants.Count >= 64
            throw Error("Invalid parent, unresolved slot identity or variant limit reached.")
        id := "V" this.NextId
        if record.Variants.Has(id)
            throw Error("Variant ID counter collision; existing variant was preserved.")
        record.Variants[id] := {Id: id, Name: PM_Model.Text(name, 120), Parent: parent, Overrides: Map()}
        this.NextId += 1
        this.Dirty := true
        return id
    }
    SetOverride(index, id, field, value, own := true) {
        this.Writable()
        record := this.BaseRecord(index)
        if !record.Variants.Has(id) || !this.CanonicalField(field)
            throw Error("Invalid variant or override field.")
        candidate := PM_Model.Clone(record.Variants), variant := candidate[id]
        if own
            variant.Overrides[field] := PM_Model.Text(value)
        else if variant.Overrides.Has(field)
            variant.Overrides.Delete(field)
        this.ResolveValues(index, id, 0, candidate)
        record.Variants := candidate
        this.Dirty := true
    }
    CanonicalField(field) {
        for allowed in PM_Model.Fields
            if field == allowed
                return true
        return false
    }
    ResolveSlot(index, legacyDraft := 0, runtime := false) {
        legacy := PM_Model.Clone(IsObject(legacyDraft) ? legacyDraft : this.Host.Slots[index])
        if runtime && this.Host.HasOwnProp("GroupRoute") && this.Host.GroupRoute.Enabled && index = this.Host.GroupRoute.Slot
            return this.Host.GroupRoute.Resolve(index, legacy)
        record := this.BaseRecord(index)
        if record.Orphaned || record.Identity != this.Identity(index) || this.LoadError != ""
            return legacy
        selected := record.Selected
        if runtime && record.AutoHelp {
            ctx := PM_Model.Clone(this.Context)
            try ctx.Exe := WinGetProcessName("A")
            catch
                ctx.Exe := "Unknown"
            pick := PM_Model.Pick(record.Variants, this.BaseValues(index, legacyDraft), this.Assets, ctx)
            if pick.Id = ""
                throw Error(pick.Reason)
            selected := pick.Id
        }
        try values := this.ResolveValues(index, selected, legacyDraft)
        catch Error as err {
            this.Notify("Advanced appearance invalid; legacy fallback used: " err.Message)
            return legacy
        }
        for field in ["File", "Width", "Opacity", "Position", "OffsetX", "OffsetY", "Mode", "Duration"]
            legacy.%field% := values[field]
        legacy.SizeMode := values["SizeMode"], legacy.SizeValue := values["SizeValue"], legacy.Monitor := values["Monitor"]
        legacy.Display := PM_Model.Clone(values)
        return legacy
    }
    ResolveValues(index, id := "", legacyDraft := 0, candidate := 0) {
        record := this.BaseRecord(index)
        variants := IsObject(candidate) ? candidate : record.Variants
        selected := id = "" ? record.Selected : id
        values := PM_Model.Resolve(variants, selected, this.BaseValues(index, legacyDraft))
        if values["SizeMode"] = "Pixels" && !PM_Model.Owns(variants, selected, "SizeValue")
            values["SizeValue"] := values["Width"]
        values := PM_Model.ResolveMetadata(values, this.Assets)
        this.ValidateValues(values)
        if values["Asset"] != "" {
            if !this.Assets.Has(values["Asset"]) || this.Assets[values["Asset"]].Kind != "Image"
                throw Error("Image asset reference is missing or has the wrong kind.")
            values["File"] := this.AssetPath(values["Asset"])
        }
        if values["Profile"] != "" && (!this.Assets.Has(values["Profile"]) || this.Assets[values["Profile"]].Kind != "Profile")
            throw Error("Profile attachment reference is missing or has the wrong kind.")
        return values
    }
    ValidateValues(v) {
        if !PM_Model.ExactHas("Hold,Toggle,Timed", v["Mode"]) || !PM_Model.ExactHas("TopLeft,TopRight,Center,BottomLeft,BottomRight", v["Position"])
            throw Error("Invalid display mode or position.")
        if !PM_Model.ExactHas("Pixels,Screen width %,Screen height %,Original %", v["SizeMode"])
            throw Error("Invalid size mode.")
        for field in ["Opacity", "Width", "OffsetX", "OffsetY", "Duration", "SizeValue"]
            if !IsNumber(v[field])
                throw Error("Numeric value required: " field)
        if v["Opacity"] < 5 || v["Opacity"] > 100 || v["Width"] < 1 || v["Width"] > 8000
            throw Error("Opacity must be5–100 and pixel width1–8000.")
        if v["Duration"] < 0.2 || v["Duration"] > 60 || Abs(v["OffsetX"]) > 8000 || Abs(v["OffsetY"]) > 8000
            throw Error("Duration0.2–60seconds; offsets±8000pixels.")
        if v["SizeValue"] < 1 || v["SizeValue"] > (v["SizeMode"] = "Pixels" ? 8000 : 300)
            throw Error("Size1–8000pixels or1–300percent.")
        if !PM_Model.ExactHas("Primary,Active window,Mouse", v["Monitor"]) && !RegExMatch(v["Monitor"] "", "^[1-9][0-9]?$" )
            throw Error("Invalid monitor selection.")
        if v["FollowAsset"] != 0 && v["FollowAsset"] != 1
            throw Error("Invalid metadata-follow flag.")
        for field, value in v
            PM_Model.Text(value)
    }
    LegacyChanged(index := 0, reindexed := false, replaced := false) {
        this.HidePreview()
        if reindexed {
            for key, record in this.Records
                record.Orphaned := 1
            this.Dirty := true
            this.Notify("Slot list changed: advanced definitions are inactive until explicitly reconciled. No index retargeting.")
        } else if index && this.Records.Has(index "") {
            if replaced
                this.Records[index ""].Orphaned := 1
            else
                this.Records[index ""].Identity := this.Identity(index)
        }
    }
    Reconcile(index) {
        this.Writable()
        ; Explicitly reset this slot only; retain asset bytes and all other records.
        this.Records[index ""] := {Identity: this.Identity(index), Selected: "base", Orphaned: 0, AutoHelp: 0,
            Variants: Map("base", {Id: "base", Name: "Base appearance", Parent: "", Overrides: Map()})}
        this.Dirty := true
    }
    Geometry(s) {
        mode := s.HasOwnProp("SizeMode") ? s.SizeMode : "Pixels"
        value := s.HasOwnProp("SizeValue") ? s.SizeValue : s.Width
        monitor := s.HasOwnProp("Monitor") ? s.Monitor : "Primary"
        bounds := IsObject(this.MonitorReader) ? this.MonitorReader.Call(monitor) : this.ScreenBounds(monitor)
        size := this.ImageReader.Call(s.File)
        dims := PM_Model.SizeFor(mode, Number(value), size[1], size[2], bounds[3] - bounds[1], bounds[4] - bounds[2])
        x := InStr(s.Position, "Right") ? bounds[3] - dims[1] - 16 : bounds[1] + 16
        y := InStr(s.Position, "Bottom") ? bounds[4] - dims[2] - 16 : bounds[2] + 16
        if s.Position = "Center"
            x := bounds[1] + Floor((bounds[3] - bounds[1] - dims[1]) / 2), y := bounds[2] + Floor((bounds[4] - bounds[2] - dims[2]) / 2)
        return {x: x + Number(s.OffsetX), y: y + Number(s.OffsetY), w: dims[1], h: dims[2], monitor: monitor}
    }
    ScreenBounds(choice) {
        monitor := MonitorGetPrimary()
        if RegExMatch(choice "", "^[1-9][0-9]?$" ) {
            monitor := Integer(choice)
            if monitor > MonitorGetCount()
                throw Error("Selected monitor is not currently connected.")
        } else if choice = "Mouse" || choice = "Active window" {
            if choice = "Mouse" {
                previous := A_CoordModeMouse
                try {
                    CoordMode("Mouse", "Screen"), MouseGetPos(&x, &y)
                } finally CoordMode("Mouse", previous)
            } else {
                hwnd := WinExist("A")
                if !hwnd
                    throw Error("No active window for monitor selection.")
                WinGetPos(&x, &y, &w, &h, "ahk_id " hwnd)
                x += w / 2, y += h / 2
            }
            Loop MonitorGetCount() {
                MonitorGet(A_Index, &left, &top, &right, &bottom)
                if x >= left && x < right && y >= top && y < bottom
                    monitor := A_Index
            }
        }
        MonitorGet(monitor, &left, &top, &right, &bottom)
        return [left, top, right, bottom]
    }
    AssetPath(id) {
        if !this.Assets.Has(id)
            throw Error("Asset does not exist.")
        a := this.Assets[id]
        if !RegExMatch(a.Hash, "^[0-9a-f]{64}$") || !RegExMatch(a.Ext, "^[a-z0-9]{1,10}$")
            throw Error("Invalid asset locator.")
        return a.Managed ? this.AssetDir "\" a.Hash "." a.Ext : a.Path
    }
    ImportAsset(path, kind := "Image", managed := true) {
        this.Writable()
        if !FileExist(path) || DirExist(path) || FileGetSize(path) > 134217728
            throw Error("Missing file or file larger than128MB.")
        SplitPath(path, &name, , &ext), ext := StrLower(ext)
        if kind = "Image" {
            if !PM_Model.Has("png,jpg,jpeg,bmp,gif,tif,tiff", ext)
                throw Error("Select a supported image.")
            this.ImageReader.Call(path)
        } else if kind != "Profile" || !PM_Model.Has("json,ini,xml,rewasd,micl,txt,csv", ext)
            throw Error("Profile attachments must be data-only supported files.")
        hash := PM_Model.Sha256(path), id := kind "-" hash
        if this.Assets.Has(id) {
            a := this.Assets[id]
            if managed && !a.Managed {
                DirCreate(this.AssetDir)
                destination := this.AssetDir "\" hash "." a.Ext
                if !FileExist(destination)
                    FileCopy(path, destination)
                if PM_Model.Sha256(destination) != hash
                    throw Error("Managed-copy integrity failed.")
                a.Managed := 1, a.Path := "", this.Dirty := true
            }
            return id
        }
        if this.Assets.Count >= 2048
            throw Error("Asset catalog limit reached.")
        if managed {
            DirCreate(this.AssetDir)
            destination := this.AssetDir "\" hash "." ext
            if !FileExist(destination)
                FileCopy(path, destination)
            if PM_Model.Sha256(destination) != hash
                throw Error("Managed-copy integrity failed; original unchanged.")
        }
        nextOrder := 1
        for assetId, existing in this.Assets
            nextOrder := Max(nextOrder, Integer(existing.Order) + 1)
        this.Assets[id] := {Id: id, Name: PM_Model.Text(name), Kind: kind, Hash: hash, Ext: ext,
            Managed: managed ? 1 : 0, Path: managed ? "" : PM_Model.Text(path), Device: "", Game: "", Exe: "",
            Keymap: "", Layer: "", LayerKey: "", Tag: "", ViewGroup: "", Order: nextOrder}
        this.Dirty := true
        return id
    }
    AssetUsage(id) {
        uses := [], seen := Map()
        ; Count all OWN references, including inactive/orphaned and inherited variants.
        ; This conservative guard cannot orphan a reference concealed by selection.
        for key, record in this.Records {
            for variantId, variant in record.Variants {
                for field in ["Asset", "Profile"]
                    if variant.Overrides.Has(field) && variant.Overrides[field] = id {
                        ref := "Slot " key " / " variantId " / " field
                        seen[ref] := true
                    }
                try {
                    base := Integer(key) <= this.Host.Slots.Length ? this.BaseValues(Integer(key)) : this.BaseValues(1)
                    values := PM_Model.Resolve(record.Variants, variantId, base)
                    for field in ["Asset", "Profile"]
                        if values[field] = id
                            seen["Slot " key " / " variantId " / " field] := true
                }
                catch {
                    ; Invalid drafts still retain their own references above.
                }
            }
        }
        for ref in seen
            uses.Push(ref)
        return uses
    }
    SetAssetMetadata(id, updates, viewOnly := false) {
        this.Writable()
        if !this.Assets.Has(id)
            throw Error("Asset does not exist.")
        candidate := PM_Model.Clone(this.Assets[id])
        for field, value in updates {
            if !PM_Model.Has("Name,Device,Game,Exe,Keymap,Layer,LayerKey,Tag,ViewGroup", field)
                throw Error("Invalid metadata field.")
            if viewOnly && field != "ViewGroup"
                continue
            candidate.%field% := PM_Model.Text(value)
        }
        this.Assets[id] := candidate, this.Dirty := true
    }
    RelinkAsset(id, path) {
        this.Writable()
        if !this.Assets.Has(id) || !FileExist(path) || DirExist(path) || FileGetSize(path) > 134217728
            throw Error("Missing or oversized relink source.")
        a := this.Assets[id]
        if PM_Model.Sha256(path) != a.Hash
            throw Error("Different content: import as a new asset instead of replacing shared references.")
        if a.Managed {
            DirCreate(this.AssetDir)
            destination := this.AssetPath(id)
            if FileExist(destination) && PM_Model.Sha256(destination) != a.Hash
                throw Error("Existing managed copy differs. Preserve it for recovery before repair.")
            if !FileExist(destination)
                FileCopy(path, destination)
            if PM_Model.Sha256(destination) != a.Hash
                throw Error("Relink-copy verification failed.")
        } else
            a.Path := PM_Model.Text(path)
        this.Dirty := true
    }
    RemoveAsset(id) {
        this.Writable()
        if !this.Assets.Has(id)
            throw Error("Asset does not exist.")
        if this.AssetUsage(id).Length
            throw Error("Asset is still referenced; remove references first.")
        this.Assets.Delete(id), this.Dirty := true
        ; Deliberately retain managed bytes; removal is catalog-only and recoverable.
    }
    FilterAssets(query := "", field := "All", sortBy := "Name", storage := "All", usage := "All") {
        if !PM_Model.ExactHas("All,Name,Kind,Device,Game,Exe,Keymap,Layer,LayerKey,Tag,ViewGroup", field)
            throw Error("Invalid metadata filter.")
        if !PM_Model.ExactHas("Name,Manual,Game,Device,Keymap,Kind,ViewGroup,Used first", sortBy)
            throw Error("Invalid catalog sort.")
        if !PM_Model.ExactHas("All,Managed,Linked,Missing", storage) || !PM_Model.ExactHas("All,Used,Unused", usage)
            throw Error("Invalid storage or usage filter.")
        text := "", query := StrLower(Trim(query))
        for id, a in this.Assets {
            used := this.AssetUsage(id).Length
            if storage = "Managed" && !a.Managed || storage = "Linked" && a.Managed || storage = "Missing" && FileExist(this.AssetPath(id))
                continue
            if usage = "Used" && !used || usage = "Unused" && used
                continue
            value := field = "All" ? a.Name " " a.Kind " " a.Device " " a.Game " " a.Exe " " a.Keymap " " a.Layer " " a.LayerKey " " a.Tag " " a.ViewGroup : a.%field%
            if query != "" && !InStr(StrLower(value), query)
                continue
            key := sortBy = "Manual" ? Format("{:06}", a.Order) : sortBy = "Used first" ? Format("{:06}", 999999 - this.AssetUsage(id).Length) : StrLower(a.%sortBy%)
            text .= key "`t" id "`n"
        }
        result := []
        for row in StrSplit(Trim(Sort(text), "`n"), "`n")
            if row != ""
                result.Push(this.Assets[StrSplit(row, "`t")[2]])
        return result
    }
    Writable() {
        if this.LoadError != ""
            throw Error("Advanced sidecar could not be loaded; refusing overwrite: " this.LoadError)
    }
    SaveExplicit(*) {
        this.Writable()
        currentHash := FileExist(this.Path) && !DirExist(this.Path) ? PM_Model.Sha256(this.Path) : ""
        if currentHash != this.SourceHash
            throw Error("Advanced sidecar changed externally. Close/reload before saving; no overwrite.")
        previousRecords := PM_Model.Clone(this.Records)
        if this.Gui && this.Selected {
            try {
                record := this.BaseRecord(this.Selected)
                if !record.Orphaned || this.EditDirty
                    this.CommitEditor()
            }
            catch Error as err {
                this.Records := previousRecords
                throw err
            }
        }
        try {
          for key, record in this.Records {
            if !record.Variants.Has(record.Selected)
                throw Error("Selected appearance does not exist.")
            for id, variant in record.Variants {
                if record.Orphaned || Integer(key) > this.Host.Slots.Length
                    this.ValidateValues(PM_Model.Resolve(record.Variants, id, this.BaseValues(1)))
                else
                    this.ResolveValues(Integer(key), id)
            }
          }
        temp := this.Path ".new." A_TickCount
        if FileExist(temp)
            throw Error("Staging file already exists; retain it for inspection.")
        SplitPath(this.Path, , &folder)
        DirCreate(folder)
            IniWrite(1, temp, "Meta", "Schema"), IniWrite(this.NextId, temp, "Meta", "NextId")
            IniWrite(PM_Model.Encode(this.LayoutIdentity()), temp, "Meta", "HostLayout")
            IniWrite(this.LegacyHash(), temp, "Meta", "LegacyHash")
            IniWrite(this.Records.Count, temp, "Meta", "Records"), IniWrite(this.Assets.Count, temp, "Meta", "Assets")
            n := 0
            for key, record in this.Records {
                n += 1, section := "Record" n
                for field, value in Map("Slot", key, "Identity", record.Identity, "Selected", record.Selected, "Orphaned", record.Orphaned, "AutoHelp", record.AutoHelp, "Variants", record.Variants.Count)
                    IniWrite(PM_Model.Encode(value), temp, section, field)
                vnum := 0
                for id, variant in record.Variants {
                    vnum += 1, vsection := section "Variant" vnum
                    for field in ["Id", "Name", "Parent"]
                        IniWrite(PM_Model.Encode(variant.%field%), temp, vsection, field)
                    fields := []
                    for field, value in variant.Overrides {
                        fields.Push(field)
                        IniWrite(PM_Model.Encode(value), temp, vsection, "Own_" field)
                    }
                    IniWrite(PM_Model.Encode(PM_Model.Join(fields, ",")), temp, vsection, "Overrides")
                }
            }
            n := 0
            for id, asset in this.Assets {
                n += 1
                for field, value in asset.OwnProps()
                    IniWrite(PM_Model.Encode(value), temp, "Asset" n, field)
            }
            if FileGetSize(temp) > 1048576
                throw Error("Advanced sidecar exceeds1MiB limit; retained staging file is not committed.")
            if FileExist(this.Path) {
                backup := this.Path ".before-" A_NowUTC "-" A_TickCount
                FileCopy(this.Path, backup)
                if PM_Model.Sha256(backup) != PM_Model.Sha256(this.Path)
                    throw Error("Current sidecar recovery copy failed verification.")
            }
            FileMove(temp, this.Path, 1)
            this.SourceHash := PM_Model.Sha256(this.Path)
            this.Dirty := false
            this.Notify("Advanced sidecar saved explicitly. Legacy settings/device profiles unchanged.")
            return true
        } catch Error as err {
            this.Records := previousRecords
            this.EditDirty := true
            ; Do not delete failed staging/recovery files: preserve a resumable boundary.
            throw Error("Advanced save failed; legacy settings unchanged. " err.Message)
        }
    }
    Load() {
        if DirExist(this.Path) || FileGetSize(this.Path) > 1048576 || IniRead(this.Path, "Meta", "Schema", 0) != 1
            throw Error("Invalid or oversized advanced sidecar.")
        records := Map(), assets := Map(), nextId := Integer(IniRead(this.Path, "Meta", "NextId", 1)), maxVariantId := 0
        count := Integer(IniRead(this.Path, "Meta", "Records", 0))
        if count < 0 || count > 128 || nextId < 1 || nextId > 1000000
            throw Error("Invalid record count or ID counter.")
        Loop count {
            section := "Record" A_Index, key := PM_Model.Decode(IniRead(this.Path, section, "Slot", ""))
            if !RegExMatch(key, "^[1-9][0-9]*$") || records.Has(key)
                throw Error("Invalid or duplicate legacy slot reference.")
            record := {Identity: PM_Model.Decode(IniRead(this.Path, section, "Identity", "")),
                Selected: PM_Model.Decode(IniRead(this.Path, section, "Selected", "")), Orphaned: Integer(PM_Model.Decode(IniRead(this.Path, section, "Orphaned", ""))), AutoHelp: Integer(PM_Model.Decode(IniRead(this.Path, section, "AutoHelp", "hex:0030"))), Variants: Map()}
            if record.AutoHelp != 0 && record.AutoHelp != 1
                throw Error("Invalid automatic-help opt-in.")
            vcount := Integer(PM_Model.Decode(IniRead(this.Path, section, "Variants", "")))
            if vcount < 1 || vcount > 64
                throw Error("Invalid variant count.")
            Loop vcount {
                vsection := section "Variant" A_Index, id := PM_Model.Decode(IniRead(this.Path, vsection, "Id", ""))
                if !RegExMatch(id, "^(base|V[1-9][0-9]*)$") || record.Variants.Has(id)
                    throw Error("Invalid or duplicate variant ID.")
                if id != "base"
                    maxVariantId := Max(maxVariantId, Integer(SubStr(id, 2)))
                variant := {Id: id, Name: PM_Model.Decode(IniRead(this.Path, vsection, "Name", "")), Parent: PM_Model.Decode(IniRead(this.Path, vsection, "Parent", "")), Overrides: Map()}
                for field in StrSplit(PM_Model.Decode(IniRead(this.Path, vsection, "Overrides", "")), ",")
                    if field != "" {
                        if !this.CanonicalField(field)
                            throw Error("Unsupported sidecar override.")
                        variant.Overrides[field] := PM_Model.Decode(IniRead(this.Path, vsection, "Own_" field, ""))
                    }
                record.Variants[id] := variant
            }
            if !record.Variants.Has("base") || record.Variants["base"].Parent != "" || !record.Variants.Has(record.Selected)
                throw Error("Invalid base or selected variant.")
            if Integer(key) > this.Host.Slots.Length || record.Identity != this.Identity(Integer(key))
                record.Orphaned := 1
            records[key] := record
        }
        count := Integer(IniRead(this.Path, "Meta", "Assets", 0))
        if count < 0 || count > 2048
            throw Error("Invalid asset count.")
        Loop count {
            a := {Id: "", Name: "", Kind: "Image", Hash: "", Ext: "", Managed: 0, Path: "", Device: "", Game: "", Exe: "",
                Keymap: "", Layer: "", LayerKey: "", Tag: "", ViewGroup: "", Order: 0}
            assetSection := "Asset" A_Index
            for field, default in a.OwnProps()
                a.%field% := PM_Model.Decode(IniRead(this.Path, assetSection, field, ""))
            if !RegExMatch(a.Hash, "^[0-9a-f]{64}$") || a.Id != a.Kind "-" a.Hash || assets.Has(a.Id) || !PM_Model.Has("Image,Profile", a.Kind)
                throw Error("Invalid or duplicate asset identity.")
            if !RegExMatch(a.Ext, "^[a-z0-9]{1,10}$") || !RegExMatch(a.Managed, "^[01]$") || !RegExMatch(a.Order, "^[0-9]{1,6}$")
                throw Error("Invalid asset locator or order.")
            assets[a.Id] := a
        }
        this.Records := records, this.Assets := assets, this.NextId := nextId
        if nextId <= maxVariantId
            throw Error("Variant ID counter would overwrite an existing appearance.")
        recordedLayout := PM_Model.Decode(IniRead(this.Path, "Meta", "HostLayout", ""))
        recordedLegacyHash := IniRead(this.Path, "Meta", "LegacyHash", "")
        if recordedLayout != this.LayoutIdentity() || recordedLegacyHash != this.LegacyHash()
            for key, record in records
                record.Orphaned := 1
        for key, record in records {
            base := Integer(key) <= this.Host.Slots.Length ? this.BaseValues(Integer(key)) : this.BaseValues(1)
            for id, variant in record.Variants {
                values := PM_Model.ResolveMetadata(PM_Model.Resolve(record.Variants, id, base), assets)
                this.ValidateValues(values)
                for spec in [["Asset", "Image"], ["Profile", "Profile"]]
                    if values[spec[1]] != "" && (!assets.Has(values[spec[1]]) || assets[values[spec[1]]].Kind != spec[2])
                        throw Error("Missing or wrong-kind shared asset reference.")
            }
        }
    }
    LayoutIdentity() {
        text := this.Host.Slots.Length ""
        for index, slot in this.Host.Slots
            for value in [this.Identity(index), slot.File, slot.MicCanvas]
                text .= "|" StrLen(value) ":" value
        return PM_Model.HashText(text)
    }
    LegacyHash() {
        return this.Host.HasOwnProp("Config") && FileExist(this.Host.Config) && !DirExist(this.Host.Config) ? PM_Model.Sha256(this.Host.Config) : ""
    }
    Notify(message) {
        if this.Gui && this.HasOwnProp("Status")
            this.Status.Text := message
    }
    Open(slotId := 0) {
        if !slotId
            slotId := this.Host.HasOwnProp("Selected") ? this.Host.Selected : 1
        if this.Gui {
            if slotId = this.Selected {
                this.Gui.Show()
                return
            }
            if slotId != this.Selected && !this.DiscardEditor()
                return
            this.Selected := slotId
            this.LoadEditor()
            this.Gui.Show()
            return
        }
        this.Selected := slotId
        this.BaseRecord(slotId)
        owner := this.Host.HasOwnProp("Gui") && IsObject(this.Host.Gui) ? "+Owner" this.Host.Gui.Hwnd : ""
        ; Logical editor coordinates scale with fonts; pixel overlay stays unchanged.
        g := Gui(owner " +DPIScale", "Studio 2 | Advanced Picture Buttons")
        this.Gui := g, this.Editor := Map(), this.Checks := Map()
        g.SetFont("s10", "Segoe UI"), g.BackColor := "F4F6F9"
        g.AddText("x20 y12 w1000 h36", "Advanced appearances / shared library. No new triggers, native imports or game input. Save writes only the advanced sidecar.")
        this.Tabs := g.AddTab3("x15 y58 w1040 h632", ["Appearance / variants", "Shared library", "Context / help routing"])
        this.Tabs.OnEvent("Change", (*) => this.HidePreview())
        this.Tabs.UseTab(1)
        this.VariantList := g.AddListView("x30 y94 w220 h186 -Multi", ["ID", "Appearance variant"])
        this.VariantList.ModifyCol(1, 55), this.VariantList.ModifyCol(2, 157)
        this.VariantList.OnEvent("ItemSelect", this.VariantSelected.Bind(this))
        this.Button(g, "x30 y291 w106", "New variant", "NewVariantUI")
        this.Button(g, "x144 y291 w106", "Remove", "RemoveVariantUI")
        g.AddText("x30 y334 w210", "Name / parent ID")
        this.VariantName := g.AddEdit("x30 y356 w220")
        this.ParentField := g.AddEdit("x30 y392 w220")
        this.VariantName.OnEvent("Change", (*) => this.MarkEditor())
        this.ParentField.OnEvent("Change", (*) => this.MarkEditor())
        this.Button(g, "x30 y439 w220", "Reset inactive slot explicitly", "ReconcileUI")
        g.AddText("x30 y485 w220 h130", "Own means override this field only. Unchecked fields follow the parent/base. Base fields normally follow the original Studio editor. Key / Enabled / Source / Pass remain owned by Studio2.")
        this.Field(g, "File", "Image path (or choose library asset)", 273, 94, 440)
        this.Button(g, "x722 y115 w105", "Browse", "BrowseDraft")
        this.Field(g, "Asset", "Shared image asset", 273, 154, 267, ["(none)"])
        this.Field(g, "Mode", "Display mode", 554, 154, 157, ["Hold", "Toggle", "Timed"])
        this.Field(g, "Duration", "Timed seconds", 723, 154, 105)
        this.Field(g, "Opacity", "Opacity %", 273, 215, 115)
        this.OpacityQuick := g.AddDropDownList("x404 y235 w105", ["25", "40", "55", "70", "85", "100"])
        this.OpacityQuick.OnEvent("Change", (*) => this.SetEditorValue("Opacity", this.OpacityQuick.Text))
        this.OpacitySlider := g.AddSlider("x273 y276 w240 h25 Range5-100 ToolTip", 75)
        this.OpacitySlider.OnEvent("Change", (*) => this.SetEditorValue("Opacity", this.OpacitySlider.Value))
        this.Field(g, "SizeMode", "Size relative to...", 554, 215, 274, ["Pixels", "Screen width %", "Screen height %", "Original %"])
        this.Field(g, "SizeValue", "Size value", 554, 283, 128)
        this.SizeQuick := g.AddDropDownList("x698 y303 w130", ["15%", "25%", "35%", "50%", "75%", "100%", "400px", "800px", "1200px"])
        this.SizeQuick.OnEvent("Change", this.QuickSize.Bind(this))
        this.Field(g, "Position", "Anchor", 273, 343, 240, ["TopLeft", "TopRight", "Center", "BottomLeft", "BottomRight"])
        monitors := ["Primary", "Active window", "Mouse"]
        Loop MonitorGetCount()
            monitors.Push(A_Index "")
        this.Field(g, "Monitor", "Monitor", 554, 343, 274, monitors)
        this.Field(g, "OffsetX", "Offset X", 273, 408, 113)
        this.Field(g, "OffsetY", "Offset Y", 401, 408, 112)
        this.LivePreview := g.AddCheckBox("x273 y486 w555", "Update my visible preview while editing (never sends game keys)")
        this.LivePreview.Value := 1
        this.Button(g, "x273 y530 w167", "Preview unsaved", "PreviewUI")
        this.Button(g, "x451 y530 w120", "Hide preview", "HidePreview")
        this.Button(g, "x582 y530 w246", "Save all advanced changes", "SaveUI")
        this.InheritNote := g.AddText("x273 y582 w555 h65", "")
        g.AddText("x850 y94 w184", "Unsaved inline preview")
        this.Inline := g.AddPicture("x850 y124 w185 h195")
        this.InlineNote := g.AddText("x850 y330 w184 h134", "")
        this.Button(g, "x850 y492 w184", "Shared library", "ShowLibrary")

        if this.Host.HasOwnProp("Feedback")
            this.Host.Feedback.RegisterNew(g, "UI-104", this)
        this.Tabs.UseTab(2)
        this.LibraryFilter := g.AddEdit("x30 y96 w240")
        this.LibraryField := g.AddDropDownList("x282 y96 w170", ["All", "Name", "Kind", "Device", "Game", "Exe", "Keymap", "Layer", "LayerKey", "Tag", "ViewGroup"])
        this.LibraryField.Choose(1)
        this.LibrarySort := g.AddDropDownList("x464 y96 w150", ["Name", "Manual", "Game", "Device", "Keymap", "Kind", "ViewGroup", "Used first"])
        this.LibrarySort.Choose(1)
        for ctl in [this.LibraryFilter, this.LibraryField, this.LibrarySort]
            ctl.OnEvent("Change", (*) => this.RefreshLibrary())
        this.Button(g, "x630 y94 w126", "Import image", "ImportImageUI")
        this.Button(g, "x767 y94 w130", "Import profile data", "ImportProfileUI")
        this.Button(g, "x908 y94 w126", "Link file", "LinkUI")
        g.AddText("x804 y558 w230", "Storage / reference filters")
        this.StorageFilter := g.AddDropDownList("x804 y581 w110", ["All", "Managed", "Linked", "Missing"])
        this.UsageFilter := g.AddDropDownList("x925 y581 w100", ["All", "Used", "Unused"])
        this.StorageFilter.Choose(1), this.UsageFilter.Choose(1)
        this.StorageFilter.OnEvent("Change", (*) => this.RefreshLibrary())
        this.UsageFilter.OnEvent("Change", (*) => this.RefreshLibrary())
        this.LibraryList := g.AddListView("x30 y139 w1004 h243 Grid -Multi", ["Name", "Kind", "Uses", "Game", "Device", "Keymap", "View group", "Storage"])
        for i, width in [190, 80, 48, 160, 120, 120, 150, 120]
            this.LibraryList.ModifyCol(i, width)
        this.LibraryList.OnEvent("ItemSelect", this.LibrarySelected.Bind(this))
        this.LibraryRows := Map(), this.LibraryMeta := Map()
        for n, field in ["Name", "Device", "Game", "Exe", "Keymap", "Layer", "LayerKey", "Tag", "ViewGroup"] {
            x := 30 + Mod(n - 1, 3) * 252, y := 399 + ((n - 1) // 3) * 64
            g.AddText("x" x " y" y " w230", field = "ViewGroup" ? "View-only group (no behavior)" : field)
            this.LibraryMeta[field] := g.AddEdit("x" x " y" (y + 22) " w230")
        }
        this.LibraryUsage := g.AddText("x804 y403 w230 h145", "Select a file to see references.")
        this.ViewOnly := g.AddCheckBox("x30 y600 w590", "View-only organization: change group only; preserve routing metadata")
        this.ViewOnly.OnEvent("Click", this.LibraryEditMode.Bind(this))
        this.Button(g, "x30 y635 w130", "Apply metadata", "MetadataUI")
        this.Button(g, "x171 y635 w120", "Use in picture", "AssignUI")
        this.Button(g, "x302 y635 w97", "Relink same", "RelinkUI")
        this.Button(g, "x410 y635 w136", "Remove unused", "RemoveAssetUI")
        this.Button(g, "x557 y635 w60", "Up", "AssetUpUI")
        this.Button(g, "x628 y635 w60", "Down", "AssetDownUI")
        this.Button(g, "x709 y635 w325", "Save all advanced changes", "SaveUI")

        if this.Host.HasOwnProp("Feedback")
            this.Host.Feedback.RegisterNew(g, "UI-104", this)
        this.Tabs.UseTab(3)
        g.AddText("x30 y99 w980 h46", "Metadata does not import a mapper profile or detect a hardware layer. Context is explicitly supplied; Unknown remains Unknown. This help router never emits a key or changes native mappings.")
        for n, field in ["Device", "Game", "Exe", "Keymap", "Layer", "LayerKey", "Profile", "Pins", "Notes"] {
            x := 30 + Mod(n - 1, 2) * 502, y := 164 + ((n - 1) // 2) * 69
            choices := field = "Profile" ? ["(none)"] : 0
            this.Field(g, field, field = "Pins" ? "Pinned metadata fields (comma separated)" : field = "Profile" ? "Shared profile attachment (data only)" : field, x, y, 469, choices)
        }
        this.Follow := g.AddCheckBox("x30 y524 w960", "Follow empty, unpinned metadata from shared profile then image")
        this.Follow.OnEvent("Click", (*) => this.MarkEditor())
        this.AutoHelp := g.AddCheckBox("x30 y546 w960", "Opt in: route this existing picture trigger by foreground executable and explicitly supplied context")
        this.AutoHelp.OnEvent("Click", (*) => this.MarkEditor())
        g.AddText("x30 y567 w955", "Explicit help context: executable basename / layer / device. LayerKey is a note, not a detected signal.")
        this.ContextExe := g.AddEdit("x30 y590 w298", "Unknown")
        this.ContextLayer := g.AddEdit("x341 y590 w298", "Unknown")
        this.ContextDevice := g.AddEdit("x652 y590 w298", "Unknown")
        this.Button(g, "x30 y634 w200", "Choose matching help", "HelpRouteUI")
        this.Button(g, "x247 y634 w215", "Save all advanced changes", "SaveUI")
        this.HelpNote := g.AddText("x481 y636 w535 h34", "No native/context observation claimed.")
        if this.Host.HasOwnProp("Feedback")
            this.Host.Feedback.RegisterNew(g, "UI-104", this)
        this.Tabs.UseTab()
        this.Status := g.AddText("x22 y700 w1030 h42", "")
        g.OnEvent("Close", this.CloseEditor.Bind(this)), g.OnEvent("Escape", this.CloseEditor.Bind(this))
        this.LoadEditor()
        this.RefreshLibrary()
        g.Show("w1070 h752")
        if this.LoadError != ""
            this.Notify("Advanced sidecar unavailable; legacy pictures remain usable. " this.LoadError)
    }
    Button(g, options, label, method) {
        button := g.AddButton(options, label)
        button.OnEvent("Click", this.SafeCall.Bind(this, method))
        return button
    }
    SafeCall(method, *) {
        try this.%method%()
        catch Error as err {
            this.Notify(err.Message)
            MsgBox(err.Message, "Picture Buttons", "Icon!")
        }
    }
    Field(g, field, label, x, y, w, choices := 0) {
        g.AddText("x" x " y" y " w" (w - 62), label)
        ctl := IsObject(choices) ? g.AddDropDownList("x" x " y" (y + 22) " w" w, choices) : g.AddEdit("x" x " y" (y + 22) " w" w)
        check := g.AddCheckBox("x" (x + w - 59) " y" y " w59", "Own")
        ctl.OnEvent("Change", this.FieldChanged.Bind(this, field))
        check.OnEvent("Click", (*) => this.MarkEditor())
        this.Editor[field] := {Control: ctl, Choices: IsObject(choices)}, this.Checks[field] := check
        return ctl
    }
    RefreshChoices() {
        for kind, field in Map("Image", "Asset", "Profile", "Profile") {
            entry := this.Editor[field], selectedId := ""
            if entry.HasOwnProp("Ids") && entry.Control.Value >= 1 && entry.Control.Value <= entry.Ids.Length
                selectedId := entry.Ids[entry.Control.Value]
            labels := ["(none)"], ids := [""]
            for id, asset in this.Assets
                if asset.Kind = kind
                    labels.Push(asset.Name " [" SubStr(asset.Hash, 1, 8) "]"), ids.Push(id)
            entry.Ids := ids
            entry.Control.Delete(), entry.Control.Add(labels), entry.Control.Choose(1)
            for n, ref in ids
                if ref = selectedId
                    entry.Control.Choose(n)
        }
    }
    LoadEditor(id := "") {
        this.LoadingEditor := true
        try {
            record := this.BaseRecord(this.Selected)
            if id = ""
                id := record.Selected
            this.EditVariantId := id
            own := record.Variants[id], values := this.ResolveValues(this.Selected, id)
            this.RefreshChoices()
            for field, entry in this.Editor {
                value := values[field]
                if field = "Asset" || field = "Profile" {
                    entry.Control.Choose(1)
                    for n, ref in entry.Ids
                        if ref = value
                            entry.Control.Choose(n)
                } else if entry.Choices
                    entry.Control.Choose(value "")
                else
                    entry.Control.Value := value
                this.Checks[field].Value := own.Overrides.Has(field)
            }
            this.Follow.Value := values["FollowAsset"]
            this.AutoHelp.Value := record.AutoHelp
            this.VariantName.Value := own.Name, this.ParentField.Value := own.Parent
            this.ParentField.Enabled := id != "base"
            this.OpacitySlider.Value := Number(values["Opacity"])
            this.VariantList.Delete()
            row := 0
            for variantId, variant in record.Variants {
                row += 1
                this.VariantList.Add(, variantId, variant.Name)
                if variantId = id
                    this.VariantList.Modify(row, "Select Focus Vis")
            }
            this.InheritNote.Text := "Editing " id " / parent " (own.Parent = "" ? "legacy base" : own.Parent) "`n" (record.Orphaned ? "INACTIVE: identity changed; explicitly reset/reconcile this slot." : "Unsaved fields preview only; press Save to apply advanced appearance.")
            this.EditDirty := false
        } finally this.LoadingEditor := false
        this.UpdateInline()
    }
    ReadEditor() {
        record := this.BaseRecord(this.Selected), candidate := PM_Model.Clone(record.Variants)
        variant := candidate[this.EditVariantId]
        variant.Name := PM_Model.Text(this.VariantName.Value, 120)
        variant.Parent := this.EditVariantId = "base" ? "" : PM_Model.Text(this.ParentField.Value, 32)
        for field, entry in this.Editor {
            if this.Checks[field].Value {
                value := (field = "Asset" || field = "Profile") ? entry.Ids[entry.Control.Value] : entry.Choices ? entry.Control.Text : entry.Control.Value
                variant.Overrides[field] := PM_Model.Text(value)
            } else if variant.Overrides.Has(field)
                variant.Overrides.Delete(field)
        }
        if this.EditDirty || variant.Overrides.Has("FollowAsset")
            variant.Overrides["FollowAsset"] := this.Follow.Value
        this.ResolveValues(this.Selected, this.EditVariantId, 0, candidate)
        return candidate
    }
    CommitEditor() {
        candidate := this.ReadEditor(), record := this.BaseRecord(this.Selected)
        if record.Orphaned
            throw Error("This slot is inactive after a list change. Explicitly reset/reconcile first.")
        record.Variants := candidate, record.Selected := this.EditVariantId
        record.AutoHelp := this.AutoHelp.Value
        this.Dirty := true, this.EditDirty := false
    }
    FieldChanged(field, *) {
        if this.LoadingEditor
            return
        this.Checks[field].Value := 1
        this.MarkEditor()
    }
    MarkEditor(*) {
        if this.LoadingEditor
            return
        this.EditDirty := true
        this.UpdateInline()
        if this.LivePreview.Value && this.PreviewGui {
            try this.RenderPreview(this.Selected)
            catch Error as err
                this.Notify("Draft preview unavailable: " err.Message)
        }
    }
    SetEditorValue(field, value) {
        entry := this.Editor[field]
        if entry.Choices
            entry.Control.Choose(value "")
        else
            entry.Control.Value := value
        this.Checks[field].Value := 1
        this.MarkEditor()
    }
    QuickSize(*) {
        value := this.SizeQuick.Text
        this.SetEditorValue("SizeMode", InStr(value, "px") ? "Pixels" : "Screen width %")
        this.SetEditorValue("SizeValue", RegExReplace(value, "[^0-9]"))
    }
    DiscardEditor() {
        if !this.EditDirty
            return true
        return MsgBox("Discard unsaved appearance-editor edits? Library changes remain staged until explicit Save.", "Unsaved draft", "YesNo Icon?") = "Yes"
    }
    VariantSelected(lv, row, selected) {
        if this.LoadingEditor || !selected || row < 1
            return
        id := lv.GetText(row, 1)
        if id = this.EditVariantId
            return
        if !this.DiscardEditor() {
            this.LoadingEditor := true
            try {
                Loop lv.GetCount()
                    lv.Modify(A_Index, lv.GetText(A_Index, 1) = this.EditVariantId ? "Select Focus Vis" : "-Select")
            } finally this.LoadingEditor := false
            return
        }
        this.HidePreview(), this.LoadEditor(id)
    }
    NewVariantUI() {
        if !this.DiscardEditor()
            return
        box := InputBox("Name for the new appearance variant (same existing trigger).", "New appearance", "w420 h150", "Variant")
        if box.Result != "OK"
            return
        id := this.AddVariant(this.Selected, box.Value, this.EditVariantId)
        this.LoadEditor(id)
    }
    RemoveVariantUI() {
        if this.EditVariantId = "base"
            throw Error("The legacy base cannot be removed.")
        record := this.BaseRecord(this.Selected)
        for id, variant in record.Variants
            if variant.Parent = this.EditVariantId
                throw Error("Other variants inherit this appearance. Remove/reparent children first.")
        if MsgBox("Remove this advanced variant? The original Studio slot is preserved.", "Remove appearance", "YesNo Icon?") != "Yes"
            return
        record.Variants.Delete(this.EditVariantId)
        if record.Selected = this.EditVariantId
            record.Selected := "base"
        this.Dirty := true, this.HidePreview(), this.LoadEditor("base")
    }
    ReconcileUI() {
        if MsgBox("Reset advanced variants for this slot only? Shared assets and legacy settings remain untouched.", "Explicit reconciliation", "YesNo Icon?") = "Yes"
            this.Reconcile(this.Selected), this.LoadEditor("base")
    }
    BrowseDraft() {
        path := FileSelect(1, , "Choose a draft picture; no settings saved", "Images (*.png; *.jpg; *.jpeg; *.bmp; *.gif; *.tif; *.tiff)")
        if path != "" {
            this.SetEditorValue("Asset", "(none)")
            this.SetEditorValue("File", path)
        }
    }
    UpdateInline() {
        if !this.Gui || !this.HasOwnProp("Inline") || this.LoadingEditor
            return
        try {
            variants := this.ReadEditor(), values := this.ResolveValues(this.Selected, this.EditVariantId, 0, variants), path := values["File"]
            if path = "" || !FileExist(path) || DirExist(path)
                throw Error("Choose an existing Local image or library image.")
            size := this.ImageReader.Call(path), factor := Min(185 / size[1], 195 / size[2])
            this.Inline.Value := "*w" Max(1, Round(size[1] * factor)) " *h" Max(1, Round(size[2] * factor)) " " path
            this.InlineNote.Text := "Original " size[1] "×" size[2] "px`nUnsaved draft; no game key sent.`nOverlay opacity/sizing appear in Preview, not this thumbnail."
        } catch Error as err {
            this.Inline.Value := ""
            this.InlineNote.Text := "Preview unavailable: " err.Message
        }
    }
    PreviewUI() => this.RenderPreview(this.Selected)
    RenderPreview(index, legacyDraft := 0) {
        legacy := PM_Model.Clone(IsObject(legacyDraft) ? legacyDraft : this.Host.Slots[index])
        if legacy.Source != "Local"
            throw Error("Unsaved preview is Local-only. It never sends MIC or game keys.")
        record := this.BaseRecord(index)
        if record.Orphaned || this.LoadError != ""
            s := legacy
        else {
            candidate := this.Gui && index = this.Selected ? this.ReadEditor() : 0
            id := this.Gui && index = this.Selected ? this.EditVariantId : record.Selected
            values := this.ResolveValues(index, id, legacyDraft, candidate)
            s := legacy
            for field in ["File", "Width", "Opacity", "Position", "OffsetX", "OffsetY", "Mode", "Duration", "SizeMode", "SizeValue", "Monitor"]
                s.%field% := values[field]
        }
        if s.File = "" || !FileExist(s.File) || DirExist(s.File)
            throw Error("Draft image is missing.")
        geometry := this.Geometry(s)
        this.HidePreview()
        g := Gui("-Caption +ToolWindow +AlwaysOnTop -DPIScale +E0x08000020", "Studio2 unsaved picture preview")
        try {
            g.MarginX := 0, g.MarginY := 0
            g.AddPicture("x0 y0 w" geometry.w " h" geometry.h, s.File)
            g.Show("NA x" geometry.x " y" geometry.y " w" geometry.w " h" geometry.h)
            previous := A_DetectHiddenWindows
            try {
                DetectHiddenWindows(true)
                WinSetTransparent(Round(Number(s.Opacity) * 255 / 100), "ahk_id " g.Hwnd)
            } finally DetectHiddenWindows(previous)
            this.PreviewGui := g
            this.PreviewTimer := this.HidePreview.Bind(this)
            SetTimer(this.PreviewTimer, -2000)
            return true
        } catch Error as err {
            g.Destroy()
            throw err
        }
    }
    HidePreview(*) {
        if this.PreviewTimer
            SetTimer(this.PreviewTimer, 0), this.PreviewTimer := 0
        if this.PreviewGui
            this.PreviewGui.Destroy(), this.PreviewGui := 0
    }
    CloseEditor(*) {
        if !this.DiscardEditor()
            return
        this.HidePreview()
        if this.Gui
            this.Gui.Destroy(), this.Gui := 0
        this.EditDirty := false
    }
    SaveUI() {
        this.SaveExplicit()
        this.LoadEditor(this.EditVariantId), this.RefreshLibrary()
    }
    ShowLibrary() {
        this.HidePreview(), this.Tabs.Choose(2), this.RefreshLibrary()
    }
    ImportImageUI() => this.ImportUI("Image", true)
    ImportProfileUI() => this.ImportUI("Profile", true)
    LinkUI() => this.ImportUI("Image", false)
    ImportUI(kind, managed) {
        paths := FileSelect("M3", , managed ? "Copy files into private library (explicit import)" : "Link images without copying", kind = "Image" ? "Images (*.png; *.jpg; *.jpeg; *.bmp; *.gif; *.tif; *.tiff)" : "Data (*.json; *.ini; *.xml; *.rewasd; *.micl; *.txt; *.csv)")
        if !(paths is Array)
            return
        if paths.Length > 32
            throw Error("Import at most32files per action.")
        for path in paths
            this.ImportAsset(path, kind, managed)
        this.RefreshLibrary(), this.RefreshChoices()
        this.Notify("Library files staged. Explicit Save persists catalog references; originals unchanged.")
    }
    RefreshLibrary(*) {
        if !this.Gui || !this.HasOwnProp("LibraryList")
            return
        this.LibraryList.Delete(), this.LibraryRows := Map(), row := 0
        for a in this.FilterAssets(this.LibraryFilter.Value, this.LibraryField.Text, this.LibrarySort.Text, this.StorageFilter.Text, this.UsageFilter.Text) {
            row += 1, this.LibraryRows[row] := a.Id
            storage := (a.Managed ? "Managed" : "Linked") (FileExist(this.AssetPath(a.Id)) ? "" : " / Missing")
            this.LibraryList.Add(, a.Name, a.Kind, this.AssetUsage(a.Id).Length, a.Game, a.Device, a.Keymap, a.ViewGroup, storage)
        }
    }
    LibrarySelected(lv, row, selected) {
        if !selected || !this.LibraryRows.Has(row)
            return
        a := this.Assets[this.LibraryRows[row]]
        for field, ctl in this.LibraryMeta
            ctl.Value := a.%field%
        this.LibraryUsage.Text := "SHA256 " SubStr(a.Hash, 1, 16) "…`n" (a.Managed ? "Managed copy; original stays unchanged." : "Linked file; moving original requires relink.") "`nReferences:`n" PM_Model.Join(this.AssetUsage(a.Id), "`n")
        this.LibraryEditMode()
    }
    LibraryEditMode(*) {
        for field, ctl in this.LibraryMeta
            ctl.Enabled := !this.ViewOnly.Value || field = "ViewGroup"
    }
    SelectedAsset() {
        row := this.LibraryList.GetNext()
        if !row || !this.LibraryRows.Has(row)
            throw Error("Select a library file first.")
        return this.LibraryRows[row]
    }
    MetadataUI() {
        id := this.SelectedAsset(), updates := Map()
        for field, ctl in this.LibraryMeta
            updates[field] := ctl.Value
        this.SetAssetMetadata(id, updates, this.ViewOnly.Value)
        this.RefreshLibrary()
        this.Notify("Shared metadata staged; following empty fields update, pinned fields do not. Save explicitly.")
    }
    AssignUI() {
        id := this.SelectedAsset(), kind := this.Assets[id].Kind
        this.SetEditorAsset(kind = "Image" ? "Asset" : "Profile", id)
        this.Tabs.Choose(kind = "Image" ? 1 : 3)
    }
    SetEditorAsset(field, id) {
        this.LoadingEditor := true
        try {
            this.RefreshChoices()
            for n, ref in this.Editor[field].Ids
                if ref = id
                    this.Editor[field].Control.Choose(n)
        } finally this.LoadingEditor := false
        this.Checks[field].Value := 1, this.MarkEditor()
    }
    RelinkUI() {
        id := this.SelectedAsset(), path := FileSelect(1, , "Locate the SAME file (SHA256 must match)")
        if path != ""
            this.RelinkAsset(id, path), this.RefreshLibrary()
    }
    RemoveAssetUI() {
        id := this.SelectedAsset()
        if MsgBox("Forget unused catalog entry? External originals and managed bytes are retained for recovery.", "Remove unused reference", "YesNo Icon?") = "Yes"
            this.RemoveAsset(id), this.RefreshLibrary(), this.RefreshChoices()
    }
    AssetUpUI() => this.MoveAsset(-1)
    AssetDownUI() => this.MoveAsset(1)
    MoveAsset(direction) {
        id := this.SelectedAsset(), items := this.FilterAssets("", "All", "Manual")
        for n, a in items
            if a.Id = id {
                next := n + direction
                if next >= 1 && next <= items.Length {
                    other := items[next], order := a.Order
                    a.Order := other.Order, other.Order := order, this.Dirty := true
                    this.LibrarySort.Choose("Manual"), this.RefreshLibrary()
                }
                return
            }
    }
    HelpRouteUI() {
        ctx := {Exe: Trim(this.ContextExe.Value), Layer: Trim(this.ContextLayer.Value), Device: Trim(this.ContextDevice.Value)}
        for field in ["Exe", "Layer", "Device"]
            if ctx.%field% = ""
                ctx.%field% := "Unknown"
        variants := this.ReadEditor()
        pick := PM_Model.Pick(variants, this.BaseValues(this.Selected), this.Assets, ctx)
        this.Context := ctx, this.HelpNote.Text := pick.Reason
        if pick.Id != "" {
            if !this.DiscardEditor()
                return
            this.LoadEditor(pick.Id)
            this.Tabs.Choose(1)
        }
    }
    Suspend(*) {
        this.HidePreview()
        if this.Gui
            this.Gui.Hide()
    }
    Shutdown(*) {
        this.HidePreview()
        if this.Gui
            this.Gui.Destroy(), this.Gui := 0
    }
}
