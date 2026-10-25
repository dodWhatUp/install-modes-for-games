#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk

class PM_Model {
}

; Headless, isolated fixture. Never registers a key or opens a window.
class RouteFixtureHost {
    __New(dir) {
        this.Dir := dir, this.Slots := [{Source: "Local", Enabled: 1}]
        this.Current := 0, this.Enabled := true, this.Logs := [], this.Shows := 0
    }
    WriteLog(text) {
        this.Logs.Push(text)
    }
    HideCurrent() {
        this.Current := 0
    }
    ShowLocal(slot) {
        this.Shows += 1
        return true
    }
}

Assert(value, message) {
    if !value
        throw Error(message)
}

RunRouteTests() {
dir := A_Temp "\StudioOverlayRouteFixture-" A_TickCount "-" DllCall("GetCurrentProcessId")
DirCreate(dir)
host := RouteFixtureHost(dir)
checks := 0
route := 0
try {
    route := StudioOverlayGroups(host)
    Assert(!route.Enabled && !FileExist(route.Config), "Absent settings must remain Off")
    checks += 1
    route.Slot := 1, route.Path := dir "\overlay-selection.ini", route.Enabled := true
    route.Save()
    route.Stop()
    Assert(IniRead(route.Config, "Route", "Enabled") = 1, "Shutdown must retain saved opt-in")
    checks += 1
    route := StudioOverlayGroups(host)
    Assert(route.Enabled && route.Slot = 1 && route.Path = dir "\overlay-selection.ini", "Saved route must restore")
    checks += 1
    route.Tick()
    Assert(host.Shows = 0 && host.Current = 0, "Layer updates without a picture trigger must not show anything")
    checks += 1
    route.Stop(), route.Save()
    route := StudioOverlayGroups(host)
    Assert(!route.Enabled, "Saved Off must survive launch")
    checks += 1
    IniWrite("preserve", route.Config, "Other", "Unknown")
    route.Save()
    Assert(IniRead(route.Config, "Other", "Unknown") = "preserve", "Save must preserve unrelated fields")
    checks += 1
    IniWrite(1, route.Config, "Route", "Enabled")
    IniWrite(99, route.Config, "Route", "Slot")
    route := StudioOverlayGroups(host)
    Assert(!route.Enabled && host.Logs.Length, "Invalid slot must fail closed")
    checks += 1
    IniWrite(1, route.Config, "Route", "Slot")
    IniWrite("relative.ini", route.Config, "Route", "Path")
    route := StudioOverlayGroups(host)
    Assert(!route.Enabled, "Relative path must fail closed")
    checks += 1
    IniWrite(dir "\overlay-selection.ini", route.Config, "Route", "Path")
    host.Slots[1].Enabled := 0
    route := StudioOverlayGroups(host)
    Assert(!route.Enabled, "Disabled picture slot must not arm")
    checks += 1
    host.Slots[1].Enabled := 1
    IniWrite(2, route.Config, "Route", "Schema")
    original := FileRead(route.Config)
    route := StudioOverlayGroups(host)
    Assert(!route.Enabled && FileRead(route.Config) = original, "Unknown schema must remain untouched")
    checks += 1
    rejected := false
    try route.Save()
    catch
        rejected := true
    Assert(rejected && FileRead(route.Config) = original, "Save must refuse unknown schema")
    checks += 1
    FileAppend("PASS " checks " headless route checks`n", "*")
} catch as err {
    FileAppend("FAIL: " err.Message " (line " err.Line ")`n", "*")
    ExitApp(1)
} finally {
    if route
        route.Stop()
    ; Cleanup is limited to this newly created task-owned fixture.
    if SubStr(StrLower(dir), 1, StrLen(A_Temp) + 27) != StrLower(A_Temp "\StudioOverlayRouteFixture-")
        throw Error("Refused fixture cleanup outside its named temporary root")
    DirDelete(dir, true)
}
ExitApp(0)

}
RunRouteTests()
