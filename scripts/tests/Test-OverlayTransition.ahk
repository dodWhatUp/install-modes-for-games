#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk

; Virtual presentation with the real transition controller and frame owner.
class FadeWindow {
    static Count := 0
    static Items := Map()
    __New() {
        this.Hwnd := ++FadeWindow.Count, this.Visible := false, this.Dead := false
        FadeWindow.Items[this.Hwnd] := this
    }
    Show(*) {
        this.Visible := true
    }
    Destroy() {
        if this.Dead
            throw Error("Double window disposal")
        this.Dead := true, this.Visible := false
    }
}
class FadeSurface {
    static Alive := 0
    __New(file, width, height) {
        FadeSurface.Alive += 1
        this.File := file, this.Closed := false
    }
    Present(hwnd, x, y, opacity) {
        window := FadeWindow.Items[hwnd]
        if window.Dead || this.Closed
            throw Error("Painting disposed frame")
        window.Opacity := opacity, window.File := this.File
    }
    Close() {
        if this.Closed
            throw Error("Double surface disposal")
        this.Closed := true, FadeSurface.Alive -= 1
    }
}
class FadePresenter extends PM_AlphaFrame {
    static Prepare(file, width, height) {
        return FadeSurface(file, width, height)
    }
    static NewWindow() {
        return FadeWindow()
    }
}
class FadeHost {
    __New() {
        this.PictureGui := 0, this.PictureAlpha := false, this.Hides := 0, this.Logs := []
    }
    HideCurrent(*) {
        this.Fade.Close(), this.Hides += 1
    }
    WriteLog(text) {
        this.Logs.Push(text)
    }
}
class FadeClock extends PM_OverlayFade {
    __New(host) {
        super.__New(host)
        host.Fade := this, this.Now := 1000, this.Running := false, this.ContextValid := true
    }
    Clock() {
        return this.Now
    }
    Schedule(enabled) {
        this.Running := enabled
    }
    Present(slot, geometry, existing, opacity) {
        return FadePresenter.Show(slot, geometry, existing, true, opacity, true)
    }
    CheckContext() {
        if !this.ContextValid
            throw Error("Stale or foreign selection")
    }
}
FadeCheck(condition, message) {
    if !condition
        throw Error(message)
}
RunFadeChecks() {
    host := FadeHost(), fade := FadeClock(host)
    slot := {File: "basic", Opacity: 100, FadeInMs: 120, FadeOutMs: 120}
    geometry := {x: 10, y: 20, w: 600, h: 400}
    window := fade.Show(slot, geometry), hwnd := window.Hwnd
    FadeCheck(window.Visible && window.Opacity = 4 && fade.Running, "First faint frame appears synchronously before waiting for a timer")
    fade.Now += 60, fade.Step()
    FadeCheck(window.Opacity = 52, "Halfway linear entry retains a perceptible ramp")
    start := fade.Start, duration := fade.Duration
    slot.File := "numbers", fade.Show(slot, geometry, window)
    FadeCheck(window.Hwnd = hwnd && window.File = "numbers" && window.Opacity = 52, "Layer swap preserves current opacity and HWND")
    FadeCheck(fade.Start = start && fade.Duration = duration, "Layer swap does not restart animation")
    FadeCheck(FadeSurface.Alive = 1, "Replacement releases the previous cached surface")
    fade.Now += 60, fade.Step()
    FadeCheck(window.Opacity = 100 && !fade.Running && window.Visible, "Fade settles fully opaque with no timer")
    fade.Hide(), fade.Now += 60, fade.Step()
    FadeCheck(fade.Hiding && window.Opacity = 50, "Release fades down")
    slot.File := "basic", fade.Show(slot, geometry, window)
    FadeCheck(!fade.Hiding && window.Hwnd = hwnd && window.Opacity = 50, "Rapid repress reverses without blank/new window")
    fade.Now += 60, fade.Step()
    FadeCheck(window.Opacity = 100 && !fade.Running, "Repress reaches full opacity")
    fade.Hide(), fade.Now += 120, fade.Step()
    FadeCheck(window.Dead && !fade.Window && !host.PictureGui && !fade.Running, "Fade-out destroys and detaches exactly once")
    FadeCheck(FadeSurface.Alive = 0, "Hidden state owns no surface")
    slot.FadeInMs := 0, slot.FadeOutMs := 0
    window := fade.Show(slot, geometry)
    FadeCheck(window.Opacity = 100 && !fade.Running, "Disabled transition is immediate")
    fade.Hide()
    FadeCheck(window.Dead && !fade.Window && FadeSurface.Alive = 0, "Disabled hide is immediate and releases resources")
    slot.FadeInMs := 400, slot.FadeOutMs := 400
    window := fade.Show(slot, geometry), fade.Now += 100, fade.Step()
    FadeCheck(window.Opacity > 0 && window.Opacity < 100, "Longer configured duration applies")
    fade.Close()
    FadeCheck(window.Dead && !fade.Running && !host.PictureGui, "Explicit hide cancels animation immediately")
    window := fade.Show(slot, geometry), fade.ContextValid := false, fade.Step()
    FadeCheck(window.Dead && host.Hides = 1 && !fade.Running, "Invalid context fails closed immediately")
    fade.ContextValid := true
    Loop 50 {
        window := fade.Show(slot, geometry)
        fade.Now += 40, fade.Step(), fade.Hide()
        fade.Now += 20, fade.Step(), fade.Show(slot, geometry, window)
        fade.Close()
    }
    FadeCheck(FadeSurface.Alive = 0 && !fade.Running, "Rapid repeated holds leave no surfaces or timers")
    FileAppend("PASS 17 headless transition checks; no GUI/input/capture.`n", "*")
    return
}
try {
    RunFadeChecks()
    ExitApp(0)
} catch as fadeError {
    FileAppend("FAIL " fadeError.Message " at " fadeError.Line "`n", "**")
    ExitApp(1)
}
