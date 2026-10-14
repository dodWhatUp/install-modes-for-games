#Requires AutoHotkey v2.0
#Warn All, StdOut
; Exercise real native controls only inside the prepared inert host fixture.
#Include %A_LineFile%\..\..\AzeronOverlayStudio.integrated.ahk

try {
    acceptance := NativeMicAcceptance(studio)
    acceptance.Run()
    ExitApp(0)
} catch Error as micAcceptanceError {
    FileAppend("FAIL: " micAcceptanceError.Message " @ " micAcceptanceError.Line "`n", "**")
    ExitApp(1)
}

class NativeMicAcceptance {
    __New(host) {
        if !host.DesktopTest
            throw Error("Only the prepared isolated desktop fixture is accepted.")
        this.Host := host, this.UI := host.MicEditor, this.Count := 0
        this.Before := PM_Model.Sha256(host.Config)
        this.Saved := host.MicToggle
        this.State := host.Current "/" host.MicVisibleByUs "/" host.Enabled "/" host.TotalEvents
        this.Slots := this.Snapshot()
    }
    Check(value, name) {
        if !value
            throw Error(name)
        this.Count += 1
    }
    Snapshot() {
        result := ""
        for slot in this.Host.Slots
            for field, value in slot.OwnProps()
                result .= field "=" value "`n"
        return result
    }
    Bounds(control, width, name) {
        control.GetPos(&x, &y, &w, &height)
        this.Host.Tabs.GetPos(&tx, &ty, &tw, &th)
        this.Check(control.Visible && x >= 30 && x + w <= width - 28 && y >= 110 && y + height + 12 <= ty + th,
            "Visible control within tab: " name " / " width)
    }
    Run() {
        h := this.Host, ui := this.UI, shared := h.PictureEditor
        this.Check(ui.Mode = "Modern" && !ui.Expanded, "Modern simple initial state")
        this.Check(!h.Bound.Length && !h.GameInput.Module && !h.KeyHook, "All fixture input stopped")
        h.FName.Value := "Picture draft retained during MIC editing"
        h.List.ModifyCol(3, 239)
        column := SendMessage(0x101D, 2, 0, h.List)
        h.Tabs.Choose(2), shared.Reflow()
        this.Check(!h.MicGuide.Visible && h.MicGuide.Enabled, "Setup disclosure is visibility only")
        this.Check(InStr(ui.DraftStatus.Text, "Saved shortcut") = 1 && InStr(ui.DraftStatus.Text, "Ctrl+") && InStr(ui.DraftStatus.Text, "Alt+"), "Saved shortcut is readable")
        this.Check(ui.ShortcutIdentity("^!h") = ui.ShortcutIdentity("!^H"), "Native modifier ordering / casing has same identity")
        this.Check(h.MicTestButton.Enabled && h.MicHiddenButton.Enabled && h.MicWebsiteButton.Enabled, "Existing actions retained")
        for width in [700, 840, 976, 1320] {
            for expanded in [false, true] {
                if ui.Expanded != expanded
                    ui.ToggleGuide()
                minHeight := ui.MinimumHeight(width < 850)
                h.Gui.Show("w" width " h" Max(900, minHeight) " NoActivate")
                shared.Width := width, shared.Height := Max(900, minHeight), shared.Reflow()
                for name in ["MicIntro", "MicText", "MicHotkeyField", "MicSaveButton", "MicShortcutHint", "MicTestButton", "MicHiddenButton", "MicWebsiteButton", "MicLocalHint"]
                    this.Bounds(h.%name%, width, name)
                for name in ["Heading", "LayoutChoice", "ClassicChoice", "DraftStatus", "ActionsHeading", "Warning", "PictureButton", "Disclosure"]
                    this.Bounds(ui.%name%, width, name)
                this.Check(h.MicGuide.Visible = expanded, "Guide follows disclosure")
                if expanded
                    this.Bounds(h.MicGuide, width, "Guide")
                h.MicHotkeyField.GetPos(&hx, &hy, &hw, &hh)
                h.MicSaveButton.GetPos(&sx, &sy, &sw, &sh)
                this.Check(hx + hw + 12 <= sx, "Shortcut / Save do not overlap")
                dpi := DllCall("GetDpiForWindow", "ptr", h.Gui.Hwnd, "uint") / 96
                this.Check(DllCall("GetPropW", "ptr", h.Gui.Hwnd, "str", "GameTools.Studio.MinWidth", "ptr") = Round(700 * dpi), "MIC publishes compact width")
                this.Check(DllCall("GetPropW", "ptr", h.Gui.Hwnd, "str", "GameTools.Studio.MinHeight", "ptr") = Round(minHeight * dpi), "True minimum is independent of current window height")
                this.Check(ui.LayoutChoice.Value && !ui.ClassicChoice.Value, "Modern radio selection remains visible and exclusive")
            }
        }
        h.MicHotkeyField.Value := "^!j", ui.UpdateDraftStatus()
        draftShortcut := h.MicHotkeyField.Value
        this.Check(ui.ShortcutIdentity(ui.ReadShortcut()) = ui.ShortcutIdentity("^!j"), "Letter shortcut remains valid under active keyboard layout")
        this.Check(InStr(ui.DraftStatus.Text, "Unsaved shortcut") && h.MicToggle = this.Saved, "Editing never applies shortcut")
        ui.ClassicChoice.Value := 1, ui.LayoutChoice.Value := 0, ui.ChangeLayout()
        this.Check(h.MicGuide.Visible && !ui.Warning.Visible && !ui.Disclosure.Visible, "Classic retains complete original guide")
        this.Check(h.MicHotkeyField.Value = draftShortcut, "Classic retains dirty shortcut")
        this.Check(ui.DraftStatus.Visible && InStr(ui.DraftStatus.Text, "Unsaved shortcut"), "Classic keeps consequential draft state visible")
        for item in ui.Legacy
            this.Check(item.Control.Visible && item.Control.Enabled, "Classic original control retained")
        ui.LayoutChoice.Value := 1, ui.ClassicChoice.Value := 0, ui.ChangeLayout()
        this.Check(ui.LayoutChoice.Value && !ui.ClassicChoice.Value && ui.Mode = "Modern", "Classic roundtrip restores clear active selection")
        this.Check(h.MicHotkeyField.Value = draftShortcut && InStr(ui.DraftStatus.Text, "Unsaved shortcut"), "Modern retains dirty shortcut")
        ui.OpenPictures()
        this.Check(h.Tabs.Value = 1 && !h.MicText.Visible && !ui.DraftStatus.Visible && InStr(h.FName.Value, "retained"), "Picture navigation changes view only")
        this.Check(SendMessage(0x101D, 2, 0, h.List) = column, "Dragged Picture column width retained")
        for page in [3, 4, 5, 2] {
            h.Tabs.Choose(page), shared.Reflow()
            this.Check(h.MicHotkeyField.Value = draftShortcut && h.MicToggle = this.Saved, "Draft retained across other pages")
        }
        h.Feedback.SetEnabled(true, 15), shared.Reflow()
        foundAction := false, foundGuide := false
        for record in h.Feedback.Records {
            if record.Target = h.MicTestButton
                foundAction := record.Id = "UI-105.action-test-mic-toggle-on-off"
            if record.Target = h.MicGuide {
                foundGuide := true
                h.MicGuide.GetPos(&x, &y)
                record.Badge.GetPos(&bx, &by)
                this.Check(record.Badge.Visible && bx = x - 23 && by = y, "Guide marker follows actual text")
                ui.ToggleGuide()
                this.Check(!record.Badge.Visible && h.MicGuide.Enabled, "Hidden guide marker cannot activate content")
            }
        }
        this.Check(foundAction && foundGuide, "Existing action identifier and explanatory target retained")
        h.MicHotkeyField.Value := this.Saved, ui.UpdateDraftStatus()
        this.Check(!InStr(ui.DraftStatus.Text, "Unsaved shortcut"), "Returning to saved value clears dirty indication")
        this.Check(this.State = h.Current "/" h.MicVisibleByUs "/" h.Enabled "/" h.TotalEvents, "Overlay and trigger runtime state unchanged")
        this.Check(this.Snapshot() = this.Slots, "Operational slots unchanged")
        this.Check(PM_Model.Sha256(h.Config) = this.Before, "Legacy INI byte-identical")
        this.Check(!FileExist(h.Pictures.Path), "No advanced sidecar created")
        this.Check(!h.Bound.Length && !h.GameInput.Module && !h.PictureGui && !h.Pictures.PreviewGui, "No input or runtime overlay started")
        FileAppend("PASS: " this.Count " native Multi Image Canvas UI checks; isolated fixture; no external actions or settings writes.`n", "*")
    }
}
