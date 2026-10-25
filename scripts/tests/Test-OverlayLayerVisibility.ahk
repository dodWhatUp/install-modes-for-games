#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk
; Virtual presenter with actual route/hash/expiry/ownership. No GUI/hooks/input.
class LayerHost {
    __New(dir) {
        this.Dir := dir, this.Slots := [{Source:"Local",Enabled:1,Mode:"Hold"}]
        this.Current := 0, this.Generation := 10, this.Pressed := Map(), this.Enabled := true
        this.Shows := 0, this.Hides := 0, this.Reuses := 0
    }
    WriteLog(*) {
    }
    HideCurrent(*) {
        this.Route.CancelPending(), this.Current := 0, this.Generation += 1, this.Hides += 1
    }
    ShowSlot(index, resolved) {
        this.HideCurrent(), this.Current := index, this.Generation += 1, this.Shows += 1
        return this.Generation
    }
    ShowLocal(resolved, reuse := false) {
        this.Reuses += reuse ? 1 : 0
        return true
    }
}
class LayerRoute extends StudioOverlayGroups {
    __New(host, image) {
        super.__New(host)
        this.Enabled := true, this.Slot := 1, this.Image := image, this.Clock := 100000
        this.Prefix := "[Overlay]`nSchema=1`nActive=1`nExpiresUnixMs=101000`nExe=C:\Fixture\App.exe`nFile=" image "`nSHA256=" PM_Model.Sha256(image) "`nLayerState=Event-tracked`nAsset=one`n"
        this.SetLayer(false), host.Route := this
    }
    SetLayer(enabled, key := "a") {
        this.Text := this.Prefix "LayerShow=" (enabled ? "1" : "0") "`n"
        if enabled
            this.Text .= "LayerHoldKey=" StrReplace(Format("{:064}", 0), "0", key) "`n"
    }
    NowMs() {
        return this.Clock
    }
    ForegroundExe() {
        return "C:\Fixture\App.exe"
    }
    LoadSnapshot() {
        return this.Text
    }
    Resolve(index, legacy) {
        source := this.Read(), this.LastAsset := source.Snapshot
        return legacy.Clone()
    }
}
LayerAssert(value, message) {
    if !value
        throw Error(message)
}
RunLayers(image) {
    dir := A_Temp "\LayerVisibilityFixture-" DllCall("GetCurrentProcessId") "-" A_TickCount
    DirCreate(dir), route := 0, count := 0
    try {
        host := LayerHost(dir), route := LayerRoute(host, image)
        route.Tick(), LayerAssert(!host.Current && !host.Shows, "Default Off must not show"), count += 1
        route.SetLayer(true), route.Tick()
        LayerAssert(host.Current = 1 && host.Shows = 1 && host.Pressed.Count = 0, "Native hold shows with no synthetic key-down"), count += 1
        shows := host.Shows, hides := host.Hides
        route.SetLayer(true, "b"), route.Tick()
        LayerAssert(host.Current = 1 && host.Shows = shows && host.Hides = hides && host.Reuses = 1, "Selected-to-selected replaces continuously"), count += 1
        route.SetLayer(false), route.Tick()
        LayerAssert(!host.Current && host.Pressed.Count = 0, "Layer release hides without a key-up or fake Pressed state"), count += 1
        host.Pressed[1] := {Token:0,Mode:"Hold"}, host.Current := 1
        host.Pressed[1].Token := host.Generation
        route.SetLayer(true), route.Tick(), route.SetLayer(false), route.Tick()
        LayerAssert(host.Current = 1 && host.Pressed[1].Token = host.Generation, "Releasing a layer keeps the actual dedicated Hold"), count += 1
        route.SetLayer(true), route.Tick(), host.Pressed.Delete(1)
        LayerAssert(route.KeepForLayer(1) && host.Current = 1, "Dedicated key-up retains the independent layer owner"), count += 1
        route.SetLayer(false), route.Tick()
        LayerAssert(!host.Current, "Last owner released hides"), count += 1
        route.SetLayer(true), route.Tick(), host.HideCurrent(), route.Tick()
        LayerAssert(!host.Current, "Explicit Hide cancels this native event"), count += 1
        route.SetLayer(true,"b"), route.Tick()
        LayerAssert(host.Current = 1, "Fresh layer event may show after explicit Hide"), count += 1
        host.HideCurrent(), host.Current := 2, route.SetLayer(true,"c"), route.Tick()
        LayerAssert(host.Current = 2, "Native request cannot steal another picture slot"), count += 1
        host.Current := 0, route.Tick()
        LayerAssert(!host.Current, "Closing the other slot does not replay its suppressed native event"), count += 1
        route.SetLayer(false), route.Tick(), host.Slots[1].Mode := "Toggle", route.SetLayer(true), route.Tick()
        LayerAssert(!host.Current, "Toggle/Timed slots do not gain automatic Hold ownership"), count += 1
        host.Slots[1].Mode := "Hold", route.Tick(), route.Clock := 102000, route.Tick()
        LayerAssert(!host.Current, "Expired source immediately withdraws layer visibility"), count += 1
        route.Clock := 100000, route.Tick()
        LayerAssert(host.Current = 1, "Same real hold can recover after fresh validation: " route.LayerVisibility.LastError " / " route.LayerVisibility.Blocked), count += 1
        route.Text := StrReplace(route.Text, "C:\Fixture\App.exe", "C:\Other\App.exe"), route.Tick()
        LayerAssert(!host.Current, "Foreign foreground cannot display the request"), count += 1
        route.SetLayer(true,"d"), route.Tick()
        route.Text := StrReplace(route.Text, "LayerState=Event-tracked", "LayerState=Selected"), route.Tick()
        LayerAssert(!host.Current, "Manually selected layer is not a native hold"), count += 1
        route.SetLayer(true,"g"), route.Tick()
        LayerAssert(!host.Current, "Malformed native event identity refused"), count += 1
        route.SetLayer(true,"e"), route.Text := StrReplace(route.Text, PM_Model.Sha256(image), StrReplace(Format("{:064}",0),"0","0")), route.Tick()
        LayerAssert(!host.Current, "Wrong image hash cannot auto-open"), count += 1
        route.SetLayer(true,"f"), host.Enabled := false, route.Tick()
        LayerAssert(!host.Current, "Paused host cannot auto-open"), count += 1
        host.Enabled := true, route.Tick(), route.Stop()
        LayerAssert(!host.Current && !route.Enabled, "Stop cancels automatic visibility"), count += 1
        FileAppend("PASS " count " native layer visibility checks; no GUI or input.`n", "*")
    } finally {
        if route
            route.Stop()
        LayerAssert(InStr(StrLower(dir), StrLower(A_Temp "\LayerVisibilityFixture-")) = 1, "Fixture cleanup scope")
        DirDelete(dir, true)
    }
}
try {
    if A_Args.Length != 1
        throw Error("Supply a generated fixture PNG")
    RunLayers(A_Args[1]), ExitApp(0)
} catch as layerError {
    FileAppend("FAIL " layerError.Message " line " layerError.Line "`n", "**"), ExitApp(1)
}
