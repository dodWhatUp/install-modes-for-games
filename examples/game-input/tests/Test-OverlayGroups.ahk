#Requires AutoHotkey v2.0
#SingleInstance Off
#NoTrayIcon
#Warn All, StdOut
#Include %A_LineFile%\..\..\StudioPictureModule.ahk
#Include %A_LineFile%\..\..\StudioOverlayGroups.ahk
; Inert module construction/policy fixtures, never the main host or any keys.
try {
    host := {Slots: [{Source: "Local", File: "fixture.png", Mode: "Hold", Key: "F7", Enabled: 1}], Current: 0, Enabled: true}
    route := StudioOverlayGroups(host)
    if route.Enabled || route.Slot != 0 || route.Gui
        throw Error("Not inert at construction")
    original := host.Slots[1]
    fixtureResult := route.Resolve(1, original)
    if fixtureResult != original || fixtureResult.Key != "F7" || fixtureResult.Mode != "Hold"
        throw Error("Disabled route changed original behavior")
    route.Stop()
    route.Shutdown()
    if route.Enabled || route.Gui
        throw Error("Cleanup failed")
    if !InStr(route.Path, "GameToolHub\overlay-selection.ini")
        throw Error("Wrong fixed display relay contract")
    FileAppend("PASS 4 inert display-route contracts; no GUI/game/input acceptance.`n", "*")
    ExitApp(0)
} catch as fixtureError {
    FileAppend("FAIL " fixtureError.Message "`n", "**")
    ExitApp(1)
}
