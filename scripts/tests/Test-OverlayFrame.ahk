#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk

; Virtual windows/surfaces exercise the real presenter/route without a GUI,
; input hooks, key registration, capture, native profiles or host display access.
class FrameFixtureState {
    static Windows := Map()
    static Creates := 0
    static Shows := 0
    static Destroys := 0
    static Closes := 0
    static FailPrepare := false
    static FailPresent := false
    static Events := []
    static Record(kind) {
        visible := 0
        for id, window in this.Windows
            if window.Visible
                visible += 1
        this.Events.Push({Kind: kind, Visible: visible})
    }
}
class FrameFixtureWindow {
    __New() {
        FrameFixtureState.Creates += 1
        this.Hwnd := FrameFixtureState.Creates
        this.Visible := false, this.Content := "", this.Dead := false
        FrameFixtureState.Windows[this.Hwnd] := this
        FrameFixtureState.Record("create")
    }
    Show(options) {
        this.Visible := true, FrameFixtureState.Shows += 1
        FrameFixtureState.Record("show")
    }
    Destroy() {
        this.Visible := false, this.Dead := true, FrameFixtureState.Destroys += 1
        FrameFixtureState.Record("destroy")
    }
}
class FrameFixtureSurface {
    __New(file, width, height) {
        this.File := file, this.Width := width, this.Height := height
        this.Closed := false
    }
    Present(hwnd, x, y, opacity) {
        FrameFixtureState.Record("present-start")
        if FrameFixtureState.FailPresent
            throw Error("Fixture presentation failure")
        target := FrameFixtureState.Windows[hwnd]
        target.Content := this.File, target.X := x, target.Y := y
        target.Width := this.Width, target.Height := this.Height, target.Opacity := opacity
        FrameFixtureState.Record("present-commit")
    }
    Close() {
        CheckFrame(!this.Closed, "Surface must close exactly once")
        this.Closed := true, FrameFixtureState.Closes += 1
        FrameFixtureState.Record("close-surface")
    }
}
class FrameFixturePresenter extends PM_AlphaFrame {
    static Prepare(file, width, height) {
        FrameFixtureState.Record("prepare")
        if FrameFixtureState.FailPrepare
            throw Error("Fixture decoding failure")
        return FrameFixtureSurface(file, width, height)
    }
    static NewWindow() {
        return FrameFixtureWindow()
    }
}
class FrameFixtureHost {
    __New(dir) {
        this.Dir := dir, this.Slots := [{Source: "Local", Enabled: 1, Mode: "Hold", File: "map-a", Opacity: 100}]
        this.Enabled := true, this.Current := 1, this.Generation := 10
        this.Pressed := Map(1, {Token: 10, Mode: "Hold"}), this.Logs := []
        this.Geometry := {x: 100, y: 100, w: 600, h: 400}
        this.PictureGui := FrameFixturePresenter.Show(this.Slots[1], this.Geometry)
    }
    WriteLog(message) {
        this.Logs.Push(message)
    }
    HideCurrent() {
        this.Route.CancelPending()
        this.Current := 0, this.Generation += 1
        if this.PictureGui
            this.PictureGui.Destroy(), this.PictureGui := 0
    }
    ShowLocal(slot, reuse := false) {
        this.PictureGui := FrameFixturePresenter.Show(slot, this.Geometry, reuse ? this.PictureGui : 0)
        return true
    }
}
class FrameFixtureRoute extends StudioOverlayGroups {
    __New(host) {
        super.__New(host)
        this.Enabled := true, this.Slot := 1, this.LastAsset := "map-a", this.Text := "map-b"
    }
    Read() {
        return {Snapshot: this.Text}
    }
    Resolve(index, legacy) {
        result := legacy.Clone(), result.File := this.Text
        this.LastAsset := this.Text
        return result
    }
}
CheckFrame(ok, message) {
    if !ok
        throw Error(message)
}
RunFrameChecks() {
    dir := A_Temp "\OverlayFrameFixture-" DllCall("GetCurrentProcessId") "-" A_TickCount
    DirCreate(dir)
    route := 0, tests := 0
    try {
        slot := {File: "first-map", Opacity: 100}, geometry := {x: 10, y: 20, w: 600, h: 400}
        window := FrameFixturePresenter.Show(slot, geometry), hwnd := window.Hwnd
        CheckFrame(window.Visible && window.Content = "first-map", "First frame is prepared and presented before showing")
        tests += 1
        start := FrameFixtureState.Events.Length
        Loop 20 {
            slot.File := "map-" A_Index
            returned := FrameFixturePresenter.Show(slot, geometry, window)
            CheckFrame(returned.Hwnd = hwnd && returned.Visible && returned.Content = slot.File, "Each swap retains the visible window")
        }
        tests += 1
        for index, event in FrameFixtureState.Events
            if index > start
                CheckFrame(event.Visible = 1, "No blank interval while decoding, presenting or disposing a replacement")
        tests += 1
        CheckFrame(FrameFixtureState.Creates = 1 && FrameFixtureState.Shows = 1 && FrameFixtureState.Destroys = 0,
            "Valid replacement must not create/show/hide/destroy another window")
        tests += 1
        CheckFrame(FrameFixtureState.Closes = 21, "Every off-screen surface is released")
        tests += 1
        geometry := {x: -50, y: 30, w: 700, h: 500}
        FrameFixturePresenter.Show(slot, geometry, window)
        CheckFrame(window.Hwnd = hwnd && window.X = -50 && window.Width = 700 && window.Visible,
            "Geometry and pixels change in one presentation on the same window")
        tests += 1
        old := window.Content, FrameFixtureState.FailPrepare := true, failed := false
        try FrameFixturePresenter.Show({File: "bad-map", Opacity: 100}, geometry, window)
        catch
            failed := true
        FrameFixtureState.FailPrepare := false
        CheckFrame(failed && window.Visible && window.Content = old && !window.Dead, "Failed preparation leaves the current window intact for owner policy")
        tests += 1
        FrameFixtureState.FailPresent := true, failed := false
        try FrameFixturePresenter.Show({File: "bad-present", Opacity: 100}, geometry, window)
        catch
            failed := true
        CheckFrame(failed && window.Visible && window.Content = old && !window.Dead, "Failed commit must not destroy the reused window")
        tests += 1
        failed := false, destroys := FrameFixtureState.Destroys
        try FrameFixturePresenter.Show(slot, geometry)
        catch
            failed := true
        FrameFixtureState.FailPresent := false
        CheckFrame(failed && FrameFixtureState.Destroys = destroys + 1, "Failed initial presentation cleans up only its new window")
        tests += 1
        window.Destroy()
        legacy := FrameFixtureWindow(), legacy.Visible := true, starts := FrameFixtureState.Events.Length
        replacement := FrameFixturePresenter.Show(slot, geometry, legacy, false)
        CheckFrame(replacement.Visible && legacy.Dead && replacement.Hwnd != legacy.Hwnd, "Legacy handoff disposes the previous window only after showing the new one")
        tests += 1
        for index, event in FrameFixtureState.Events
            if index > starts
                CheckFrame(event.Visible >= 1, "Legacy handoff never exposes a blank frame")
        tests += 1
        replacement.Destroy()
        host := FrameFixtureHost(dir), route := FrameFixtureRoute(host), host.Route := route
        current := host.PictureGui.Hwnd, generation := host.Generation, token := host.Pressed[1].Token
        starts := FrameFixtureState.Events.Length, destroys := FrameFixtureState.Destroys
        route.Tick()
        CheckFrame(host.PictureGui.Hwnd = current && host.PictureGui.Content = "map-b" && host.PictureGui.Visible,
            "Real route replaces a layer on its existing window")
        tests += 1
        CheckFrame(host.Current = 1 && host.Generation = generation && host.Pressed[1].Token = token,
            "Layer replacement does not disturb the held trigger or release token")
        tests += 1
        CheckFrame(FrameFixtureState.Destroys = destroys, "Route must not destroy the old frame before preparing the replacement")
        tests += 1
        for index, event in FrameFixtureState.Events
            if index > starts
                CheckFrame(event.Visible = 1, "Route keeps an opaque frame present during every swap stage")
        tests += 1
        host.HideCurrent(), host.Pressed.Delete(1), route.Tick()
        CheckFrame(host.Current = 0 && !host.PictureGui, "Explicit release/hide remains hidden")
        tests += 1
        FileAppend("PASS " tests " headless frame continuity checks; no windows or input.`n", "*")
    } finally {
        if route
            route.Stop()
        CheckFrame(SubStr(StrLower(dir), 1, StrLen(A_Temp) + 21) = StrLower(A_Temp "\OverlayFrameFixture-"), "Fixture cleanup scope")
        DirDelete(dir, true)
    }
}
try {
    RunFrameChecks()
    ExitApp(0)
} catch as frameCheckError {
    FileAppend("FAIL " frameCheckError.Message " at " frameCheckError.Line "`n", "**")
    ExitApp(1)
}
