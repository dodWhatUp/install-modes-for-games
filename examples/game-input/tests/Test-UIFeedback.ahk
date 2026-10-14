#Requires AutoHotkey v2.0
#Warn All, StdOut
#Include %A_LineFile%\..\..\StudioHubBridge.ahk
; Hidden, test-owned GUI only. No clipboard, hooks, input, profiles or file writes.
feedbackTestCount := 0
try {
    feedbackGui := Gui()
    feedbackHost := {Gui: feedbackGui}
    feedbackHost.FFile := feedbackGui.AddEdit("w300", "private unsaved path")
    feedbackOriginal := feedbackGui.AddButton("w200", "PREVIEW CURRENT EDITS")
    feedbackCounter := {ran: false}
    feedbackOriginal.OnEvent("Click", (*) => feedbackCounter.ran := true)
    feedbackService := StudioComponentFeedback(feedbackHost)
    feedbackService.RegisterNew(feedbackGui, "UI-101", feedbackHost, ["FFile"])
    FeedbackAssert(feedbackService.Badges.Length = 2, "Separate badges per actual control")
    FeedbackAssert(feedbackService.Records[1].Id = "UI-103.ffile", "Stable field ID")
    FeedbackAssert(feedbackService.Records[2].Id = "UI-103.action-preview-current-edits", "Stable preview ID")
    FeedbackAssert(feedbackService.Records[1].Label = "Local picture path", "Public meaningful label")
    FeedbackAssert(!feedbackService.Enabled, "Off at startup")
    feedbackService.SetEnabled(true)
    FeedbackAssert(feedbackService.Enabled, "Explicit display toggle")
    feedbackService.SetEnabled(false)
    FeedbackAssert(!feedbackService.Enabled, "Toggle can hide without disabling originals")
    feedbackService.RegisterNew(feedbackGui, "UI-101", feedbackHost, ["FFile"])
    FeedbackAssert(feedbackService.Badges.Length = 2, "No recursive badges or duplicates")
    FeedbackAssert(feedbackHost.FFile.Value = "private unsaved path", "Draft retained")
    FeedbackAssert(!feedbackCounter.ran, "No original preview action invoked")
    FeedbackAssert(DllCall("GetWindowLongW", "ptr", feedbackOriginal.Hwnd, "int", -16, "uint") & 0x04000000, "Original clips raised siblings")
    FeedbackAssert(DllCall("GetWindowLongW", "ptr", feedbackService.Badges[1].Hwnd, "int", -16, "uint") & 0x04000000, "Badge clips siblings")
    feedbackText := feedbackGui.AddText("x10 y150 w300", "Review saved reports")
    feedbackHost.StatusText := feedbackGui.AddText("x10 y180 w300", "private runtime state")
    feedbackHost.List := feedbackGui.AddListView("x10 y210 w300 h90", ["Name"])
    feedbackHost.List.Add(, "private row")
    feedbackHost.Section := feedbackGui.AddGroupBox("x10 y320 w300 h60", "Optional")
    feedbackHost.LogEdit := feedbackGui.AddEdit("x10 y390 w300 ReadOnly", "private log")
    feedbackService.RegisterNew(feedbackGui, "UI-101", feedbackHost)
    FeedbackAssert(feedbackService.Records.Length = 7, "Passive text, data and section coverage")
    FeedbackAssert(feedbackService.Records[3].Kind = 2, "Explanation classified as text")
    FeedbackAssert(feedbackService.Records[4].Kind = 2, "Status classified as text")
    FeedbackAssert(feedbackService.Records[5].Kind = 4, "Table classified as data")
    FeedbackAssert(feedbackService.Records[6].Kind = 8, "Group classified as section")
    FeedbackAssert(feedbackService.Records[7].Kind = 4, "Read-only log classified as data")
    FeedbackAssert(!InStr(feedbackService.Records[4].Id, "private") && !InStr(feedbackService.Records[4].Label, "private"), "Status value never used in metadata")
    for feedbackFilterMask in [1, 2, 4, 8, 3, 15, 0] {
        feedbackService.SetEnabled(true, feedbackFilterMask)
        for feedbackRecord in feedbackService.Records {
            visibleStyle := !!(DllCall("GetWindowLongW", "ptr", feedbackRecord.Badge.Hwnd, "int", -16, "uint") & 0x10000000)
            FeedbackAssert(visibleStyle = !!(feedbackFilterMask & feedbackRecord.Kind), "Type filter changes only marker visibility")
        }
    }
    feedbackService.SetEnabled(false, 2)
    FeedbackAssert(feedbackService.Mask = 2 && !feedbackService.Enabled, "Hide preserves selected types")
    feedbackRejected := false
    try feedbackService.SetEnabled(true, 16)
    catch
        feedbackRejected := true
    FeedbackAssert(feedbackRejected && feedbackService.Mask = 2, "Invalid filters retained unchanged")
    feedbackText.GetPos(&textX)
    feedbackService.Records[3].Badge.GetPos(&feedbackBadgeX)
    FeedbackAssert(feedbackBadgeX < textX || textX < 23, "Text marker beside content instead of covering last words")
    feedbackHost.FFile.Enabled := false
    FeedbackAssert(feedbackService.Badges[1].Enabled, "Disabled input still has an independent copy target")
    FeedbackAssert(feedbackHost.FFile.Value = "private unsaved path" && !feedbackCounter.ran, "Filters preserve draft and original action")
    feedbackService.Shutdown()
    feedbackGui.Destroy()
    FileAppend("PASS: " feedbackTestCount " UI identification tests; hidden owned GUI only, no clipboard/input/settings writes.`n", "*")
    ExitApp(0)
} catch Error as feedbackError {
    FileAppend("FAIL: " feedbackError.Message "`n", "**")
    ExitApp(1)
}
FeedbackAssert(condition, label) {
    global feedbackTestCount
    feedbackTestCount += 1
    if !condition
        throw Error(label)
}
