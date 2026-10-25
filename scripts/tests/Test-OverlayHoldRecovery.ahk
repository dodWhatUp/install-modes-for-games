#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk

; Headless state/clock/hash fixtures. No GUI, hooks, key registration or input.
class HoldFixtureHost {
    __New(dir) {
        this.Dir := dir, this.Slots := [{Source: "Local", Enabled: 1, Mode: "Hold"}]
        this.Enabled := true, this.Current := 1, this.Generation := 10
        this.Pressed := Map(1, {Token: 10, Mode: "Hold"})
        this.PictureGui := 0, this.Shows := 0, this.Hides := 0, this.Logs := [], this.Route := 0
    }
    WriteLog(message) {
        this.Logs.Push(message)
    }
    HideCurrent(*) {
        if this.Route
            this.Route.CancelPending()
        this.Current := 0, this.Generation += 1, this.Hides += 1
    }
    ShowSlot(index, appearance) {
        this.HideCurrent(), this.Shows += 1, this.Current := index, this.Generation += 1
        return this.Generation
    }
    ShowLocal(appearance, reuse := false) {
        this.Shows += 1
        return true
    }
}
class HoldFixtureRoute extends StudioOverlayGroups {
    __New(host) {
        super.__New(host)
        host.Route := this
        this.Enabled := true, this.Slot := 1, this.Fail := false, this.Text := "asset-a"
        this.LastAsset := "asset-a", this.Interrupt := false
    }
    Read() {
        if this.Interrupt
            this.Host.HideCurrent()
        if this.Fail
            throw Error("Fixture stale snapshot")
        return {Snapshot: this.Text}
    }
    Resolve(index, legacy) {
        this.LastAsset := this.Text
        return legacy.Clone()
    }
}
class SnapshotFixtureRoute extends StudioOverlayGroups {
    __New(host, snapshots) {
        super.__New(host)
        this.Snapshots := snapshots, this.Index := 0, this.Clock := 101001
        this.Exe := "C:\Fixture\Game.exe"
    }
    LoadSnapshot() {
        this.Index += 1
        return this.Snapshots[Min(this.Index, this.Snapshots.Length)]
    }
    NowMs() {
        return this.Clock
    }
    ForegroundExe() {
        return this.Exe
    }
}
CheckHold(value, message) {
    if !value
        throw Error(message)
}
RunHoldChecks() {
    if A_Args.Length != 1
        throw Error("Supply the generated fixture PNG path")
    dir := A_Temp "\OverlayHoldFixture-" DllCall("GetCurrentProcessId") "-" A_TickCount
    DirCreate(dir)
    route := 0, tests := 0
    try {
        fixture := A_Args[1], hash := StrLower(PM_Model.Sha256(fixture))
        snapshot := "[Overlay]`nSchema=1`nActive=1`nExpiresUnix=101`nExpiresUnixMs=101950`nFile=" fixture
            . "`nSHA256=" hash "`nExe=C:\Fixture\Game.exe`nAsset=asset-a`n"
        host := HoldFixtureHost(dir)
        route := SnapshotFixtureRoute(host, [snapshot])
        CheckHold(route.Read().File = fixture, "Fresh millisecond heartbeat must survive whole-second boundary")
        tests += 1
        legacy := StrReplace(snapshot, "ExpiresUnixMs=101950`n", "")
        legacyRejected := false
        try route.ValidateLifetime(route.ParseSnapshot(legacy))
        catch
            legacyRejected := true
        CheckHold(legacyRejected, "Fixture must reproduce the old early-expiry boundary")
        tests += 1
        heartbeat := StrReplace(StrReplace(snapshot, "ExpiresUnix=101", "ExpiresUnix=102"), "ExpiresUnixMs=101950", "ExpiresUnixMs=102000")
        route := SnapshotFixtureRoute(host, [snapshot, heartbeat])
        CheckHold(route.Read().Snapshot = heartbeat, "Heartbeat replacement must not masquerade as a changed map")
        tests += 1
        changed := StrReplace(snapshot, "Asset=asset-a", "Asset=asset-b")
        route := SnapshotFixtureRoute(host, [snapshot, changed])
        CheckHold(route.Read().Snapshot = changed, "A changing map is revalidated atomically without hiding the current frame")
        tests += 1
        route := SnapshotFixtureRoute(host, [snapshot, changed, snapshot, changed, snapshot, changed])
        refused := false
        try route.Read()
        catch
            refused := true
        CheckHold(refused, "Continuous changes beyond the bounded retry must fail closed")
        tests += 1
        for invalid in [StrReplace(snapshot, "Active=1", "Active=0"), StrReplace(snapshot, "ExpiresUnixMs=101950", "ExpiresUnixMs=101000"),
            StrReplace(snapshot, "ExpiresUnixMs=101950", "ExpiresUnixMs=104000"), StrReplace(snapshot, "ExpiresUnixMs=101950", "ExpiresUnixMs=bad"),
            StrReplace(snapshot, "Exe=C:\Fixture\Game.exe", "Exe=C:\Other\Game.exe"), StrReplace(snapshot, hash, "a" hash), snapshot "Active=1`n"] {
            route := SnapshotFixtureRoute(host, [invalid])
            refused := false
            try route.Read()
            catch
                refused := true
            CheckHold(refused, "Inactive/stale/malformed/foreign/changed-hash/duplicate snapshot must be refused")
            tests += 1
        }
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        route.Fail := true, route.Tick()
        CheckHold(host.Current = 0 && IsObject(route.PendingHold) && host.Shows = 0, "Stale data hides but retains the same held intent")
        tests += 1
        route.Fail := false, route.Text := "asset-b", route.Tick()
        CheckHold(host.Current = 1 && host.Shows = 1 && host.Pressed[1].Token = host.Generation && !route.PendingHold,
            "Fresh data resumes only that hold and repairs the token used by normal key-up")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        route.Fail := true, route.Tick(), host.Pressed.Delete(1), route.Fail := false, route.Tick()
        CheckHold(host.Current = 0 && !route.PendingHold && host.Shows = 0, "Released hold must never resume")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        route.Fail := true, route.Tick(), host.HideCurrent(), route.Fail := false, route.Tick()
        CheckHold(host.Shows = 0 && !route.PendingHold, "Explicit Hide must cancel pending recovery even while held")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        route.Fail := true, route.Tick(), host.Pressed[1] := {Token: 0, Mode: "Hold"}, route.Fail := false, route.Tick()
        CheckHold(host.Shows = 0 && !route.PendingHold, "Another press cannot inherit an old pending hold")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        route.Fail := true, route.Tick(), host.Enabled := false, route.Fail := false, route.Tick()
        CheckHold(host.Shows = 0, "Paused host must never recover a picture")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        host.Pressed[1].Mode := "Timed", route.Fail := true, route.Tick(), route.Fail := false, route.Tick()
        CheckHold(host.Shows = 0 && !route.PendingHold, "Timed and Toggle pictures do not gain hold recovery")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        host.HideCurrent(), host.Pressed[1] := 0, route.CapturePending(1), route.Tick()
        CheckHold(host.Shows = 1 && host.Current = 1 && host.Pressed[1].Token = host.Generation,
            "Initially stale hold can show after the first valid selection without another press")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        route.Interrupt := true, route.Fail := true, route.Tick()
        CheckHold(!route.PendingHold && host.Shows = 0, "Explicit Hide during validation supersedes a failing read")
        tests += 1
        host := HoldFixtureHost(dir), route := HoldFixtureRoute(host)
        route.LastAsset := snapshot, route.Text := heartbeat, route.Tick()
        CheckHold(host.Current = 1 && host.Shows = 0 && host.Hides = 0, "Heartbeat alone never redraws or hides a map")
        tests += 1
        FileAppend("PASS " tests " headless freshness/hold checks; no GUI or input.`n", "*")
    } finally {
        if route
            route.Stop()
        CheckHold(SubStr(StrLower(dir), 1, StrLen(A_Temp) + 20) = StrLower(A_Temp "\OverlayHoldFixture-"), "Fixture cleanup scope")
        DirDelete(dir, true)
    }
}
try {
    RunHoldChecks()
    ExitApp(0)
} catch as holdCheckError {
    FileAppend("FAIL " holdCheckError.Message " at " holdCheckError.Line "`n", "**")
    ExitApp(1)
}
