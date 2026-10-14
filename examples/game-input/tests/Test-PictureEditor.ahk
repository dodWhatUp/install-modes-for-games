#Requires AutoHotkey v2.0
#Warn All, StdOut
; Full native host with its bounded DesktopTest guard, isolated INIs only.
#Include %A_LineFile%\..\..\AzeronOverlayStudio.integrated.ahk

try {
    acceptance := NativePictureAcceptance(studio)
    acceptance.Run()
    ExitApp(0)
} catch Error as pictureAcceptanceError {
    FileAppend("FAIL: " pictureAcceptanceError.Message " @ " pictureAcceptanceError.Line "`n", "**")
    ExitApp(1)
}

class NativePictureAcceptance {
    __New(host) {
        if !host.DesktopTest
            throw Error("Only the prepared isolated desktop fixture is accepted.")
        this.Host := host, this.UI := host.PictureEditor, this.Count := 0
        this.Before := PM_Model.Sha256(host.Config)
        this.SlotsBefore := this.Snapshot()
    }
    Check(value, name) {
        if !value
            throw Error(name)
        this.Count += 1
    }
    Snapshot() {
        text := ""
        for slot in this.Host.Slots
            for field, value in slot.OwnProps()
                text .= field "=" value "`n"
        return text
    }
    Run() {
        h := this.Host, ui := this.UI
        this.Check(ui.Mode = "Modern" && !ui.Expanded, "Modern simple view is the initial presentation")
        this.Check(!h.Bound.Length && !h.GameInput.Module, "Input remains stopped in fixture")
        this.Check(!h.FWidth.Visible && h.FWidth.Enabled, "Disclosure hides, does not disable")
        for width in [700, 840, 976, 1320] {
            h.Gui.Show("w" width " h900 NoActivate")
            ui.Width := width, ui.Height := 900, ui.Reflow()
            for name in ["FName", "FKey", "FSource", "FMode", "FFile"] {
                h.%name%.GetPos(&x, &y, &w, &height)
                this.Check(x >= 30 && x + w <= width - 28 && y >= 110, "Responsive visible field bounds at " width " / " name)
            }
            this.Check(DllCall("GetPropW", "ptr", h.Gui.Hwnd, "str", "GameTools.Studio.MinWidth", "ptr") > 0, "Owner-scoped minimum width published")
            dpi := DllCall("GetDpiForWindow", "ptr", h.Gui.Hwnd, "uint") / 96
            this.Check(DllCall("GetPropW", "ptr", h.Gui.Hwnd, "str", "GameTools.Studio.MinHeight", "ptr") = Round((width < 850 ? 811 : 777) * dpi), "Large window does not lock in a larger minimum height")
            ui.Actions["Automatic overlay groups…"].GetPos(&ax, &ay, &aw, &ah)
            h.Tabs.GetPos(&tx, &ty, &tw, &th)
            this.Check(ay + ah + 12 <= ty + th, "Bottom editor actions are not clipped by tab at " width)
            for name in ["FSource", "FMode"] {
                popup := Buffer(16, 0)
                SendMessage(0x0152, 0, popup.Ptr, h.%name%)
                this.Check(NumGet(popup, 12, "int") - NumGet(popup, 4, "int") > Round(60 * dpi), "Dropdown reflow preserves popup choices: " name)
            }
        }
        h.FName.Value := "Unsaved draft with long name — retained across layouts"
        h.FOffsetX.Value := "123"
        ui.UpdateDraftStatus()
        this.Check(InStr(ui.DraftStatus.Text, "Unsaved edits"), "Visible dirty status")
        ui.ToggleDetails()
        this.Check(h.FWidth.Visible && h.FOffsetX.Value = "123", "Expanded settings retain draft")
        ui.ToggleDetails()
        this.Check(!h.FWidth.Visible && h.FOffsetX.Value = "123", "Collapsed settings retain draft")
        h.FMode.Choose("Timed"), ui.Reflow()
        this.Check(h.FDuration.Visible && !h.FWidth.Visible, "Timed duration stays visible in simple mode")
        h.FSource.Choose("MIC"), h.OnSourceChanged()
        this.Check(h.FMicCanvas.Visible && !h.FFile.Visible && !h.FFile.Enabled && h.FMicCanvas.Enabled, "MIC source reflows without activation")
        h.FSource.Choose("Local"), h.OnSourceChanged()
        this.Check(h.FFile.Visible && !h.FMicCanvas.Visible && h.FFile.Enabled, "Local source reflows")
        ui.LayoutChoice.Choose("Classic"), ui.ChangeLayout()
        this.Check(ui.Mode = "Classic" && h.FWidth.Visible && h.FName.Value = "Unsaved draft with long name — retained across layouts", "Classic uses same draft controls")
        h.List.ModifyCol(3, 237)
        columnBefore := SendMessage(0x101D, 2, 0, h.List)
        h.Tabs.Choose(2), ui.Reflow()
        this.Check(!ui.Disclosure.Visible && !h.FName.Visible, "Other retained tabs hide Picture Buttons")
        h.Tabs.Choose(1), ui.LayoutChoice.Choose("Modern"), ui.ChangeLayout()
        this.Check(h.FName.Visible && h.FOffsetX.Value = "123", "Return to Modern retains hidden draft")
        this.Check(columnBefore > 0 && SendMessage(0x101D, 2, 0, h.List) = columnBefore, "Resizing/layout changes retain dragged table column width")
        h.DefineProp("ConfirmDiscardDraft", {Call: (instance, question := "") => false})
        try {
            h.SelectSlot(h.List, 2, true)
            this.Check(h.Selected = 1 && h.List.GetNext() = 1 && InStr(h.FName.Value, "Unsaved draft"), "Cancelled selection restores original row and draft")
        } finally h.DeleteProp("ConfirmDiscardDraft")
        h.FMode.Choose("Hold"), h.ReadSlotFields(1)
        this.Check(!InStr(ui.DraftStatus.Text, "Unsaved edits"), "Loading saved slot clears dirty indication")
        h.TestSlot()
        this.Check(IsObject(h.Pictures.PreviewGui) && !h.PictureGui && !h.Current, "Local draft preview is detached from runtime overlays")
        h.Pictures.HidePreview()
        this.Check(!h.Pictures.PreviewGui, "Preview cleans up without saving")
        h.Feedback.SetEnabled(true, 15), ui.ToggleDetails()
        for record in h.Feedback.Records {
            if record.Target = h.FOffsetX {
                record.Target.GetPos(&x, &y, &w)
                record.Badge.GetPos(&bx, &by)
                this.Check(by = y && bx = x + w - 22, "Identification follows actual field position")
                ui.ToggleDetails()
                this.Check(!record.Badge.Visible, "Collapsed field marker cannot activate hidden content")
                break
            }
        }
        this.Check(this.Snapshot() = this.SlotsBefore, "No operational slot data changed")
        this.Check(PM_Model.Sha256(h.Config) = this.Before, "Legacy INI byte-identical")
        this.Check(!FileExist(h.Pictures.Path), "No advanced sidecar created by view actions")
        FileAppend("PASS: " this.Count " native Picture Buttons UI checks; isolated fixture; no game, input, capture or settings writes.`n", "*")
    }
}
