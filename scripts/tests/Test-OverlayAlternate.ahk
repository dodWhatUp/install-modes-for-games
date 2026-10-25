#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk
; Headless deterministic clocks/key states. No hooks, hotkeys, GUI or input.
class AltHost {
    __New(dir) {
        this.Dir := dir, this.Slots := [{Source:"Local",Enabled:1,Mode:"Hold",File:""}]
        this.Enabled := true, this.Current := 0, this.Generation := 0, this.Pressed := Map()
        this.Shows := 0, this.Hides := 0, this.Reuses := 0, this.LastFile := "", this.Route := 0
    }
    WriteLog(*) {
    }
    HideCurrent(*) {
        this.Route.CancelPending(), this.Current := 0, this.Generation += 1, this.Hides += 1
    }
    ShowSlot(index,slot) {
        this.HideCurrent(), this.Current := index, this.Generation += 1, this.Shows += 1, this.LastFile := slot.File
        return this.Generation
    }
    ShowLocal(slot,reuse := false) {
        this.Reuses += reuse, this.LastFile := slot.File
        return true
    }
}
class AltState extends StudioOverlayAlternate {
    __New(route) {
        super.__New(route), this.Now := 1000, this.States := Map()
    }
    Clock() => this.Now
    KeyHeld(key) => this.States.Get(key,false)
}
class AltRoute extends StudioOverlayGroups {
    __New(host,normal,alternate) {
        super.__New(host), host.Route := this
        this.Enabled := true, this.Slot := 1, this.Alternate := AltState(this)
        this.Prefix := "[Overlay]`nSchema=1`nActive=1`nExpiresUnixMs=101000`nExe=C:\Fixture\App.exe`nFile=" normal "`nSHA256=" PM_Model.Sha256(normal) "`nGame=game`nLayerState=Event-tracked`nLayerShow=0`nAltEnabled=1`nAltDouble=1`nAltWindowMs=300`nAltBehavior=hold`nAltChord=`nAltIdentity=" StrReplace(Format("{:064}",0),"0","a") "`nAltFile=" alternate "`nAltSHA256=" PM_Model.Sha256(alternate) "`n"
        this.Text := this.Prefix
    }
    LoadSnapshot() => this.Text
    NowMs() => 100000
    ForegroundExe() => "C:\Fixture\App.exe"
    WarmTick() {
    }
    Down() {
        if this.Host.Pressed.Has(1)
            return
        this.Host.Pressed[1] := 0, this.AlternateDown(1)
        resolved := this.Resolve(1,this.Host.Slots[1])
        token := this.Host.Current = 1 ? (this.Host.ShowLocal(resolved,true) ? this.Host.Generation : 0) : this.Host.ShowSlot(1,resolved)
        this.Host.Pressed[1] := {Token:token,Mode:"Hold"}
    }
    Up() {
        this.Host.Pressed.Delete(1), this.AlternateUp(1)
        if !this.KeepForLayer(1)
            this.Host.HideCurrent()
    }
}
AltAssert(value,message) {
    if !value
        throw Error(message)
}
RunAltChecks(normal,alternate) {
    dir := A_Temp "\OverlayAltFixture-" DllCall("GetCurrentProcessId") "-" A_TickCount
    DirCreate(dir), route := 0, count := 0
    try {
        host := AltHost(dir), route := AltRoute(host,normal,alternate), a := route.Alternate
        route.Down(), AltAssert(host.LastFile=normal && !a.Active(),"First down is immediate normal view"), count += 1
        route.Down(), AltAssert(!a.Active(),"Key repeat never counts as a second press"), count += 1
        route.Up(), a.Now += 210, route.Down()
        AltAssert(host.LastFile=alternate && a.DoubleHeld,"Second down at210ms selects alternate"), count += 1
        before := host.Hides, route.Text .= "Layer=NUMBERS`n", route.Tick()
        AltAssert(host.Current=1 && host.Hides=before && host.LastFile=alternate,"Layer swap keeps the alternate continuously visible"), count += 1
        route.Up(), AltAssert(!host.Current && !a.DoubleHeld,"Second release hides and resets alternate"), count += 1
        a.Now += 80, route.Down(), AltAssert(host.LastFile=normal,"Third press begins a new pair"), count += 1
        route.Up(), a.Now += 40, route.Down(), AltAssert(!a.DoubleHeld,"Sub60ms bounce is not a double press"), count += 1
        route.Up(), a.Now += 601, route.Down(), AltAssert(!a.DoubleHeld,"Slow repeated hold stays normal"), count += 1
        route.Up(), a.Now += 300, route.Down(), AltAssert(a.DoubleHeld,"Configured300ms boundary is accepted"), count += 1
        route.Up(), route.Text := StrReplace(route.Prefix,"AltBehavior=hold","AltBehavior=toggle")
        a.Reset(), a.Now += 800, route.Down(), route.Up(), a.Now += 200, route.Down()
        AltAssert(a.Toggle && host.LastFile=alternate,"Optional toggle changes look"), count += 1
        route.Up(), AltAssert(!host.Current && a.Toggle,"View toggle does not pin visibility"), count += 1
        a.Now += 800, route.Down(), AltAssert(host.LastFile=alternate,"Next ordinary hold uses toggled look"), count += 1
        route.Up(), route.Text := StrReplace(route.Prefix,"AltChord=","AltChord=Ctrl;XButton1"), a.Reset()
        a.States["Ctrl"] := true, route.Tick(), AltAssert(!host.Current,"Partial combination does not show"), count += 1
        a.States["XButton1"] := true, route.Tick()
        AltAssert(host.Current=1 && host.LastFile=alternate && host.Pressed.Count=0,"Keyboard plus mouse shows without synthetic Pressed entries"), count += 1
        route.Down(), a.States["XButton1"] := false, before := host.Hides, route.Tick()
        AltAssert(host.Current=1 && host.Hides=before && host.LastFile=normal,"Combination release returns to normal while dedicated Hold remains"), count += 1
        a.States["XButton1"] := true, route.Tick(), route.Up()
        AltAssert(host.Current=1,"Dedicated release retains real combination owner"), count += 1
        a.States["XButton1"] := false, route.Tick(), AltAssert(!host.Current,"Final combination release hides"), count += 1
        a.States["XButton1"] := true, route.Tick(), host.HideCurrent(), route.Tick()
        AltAssert(!host.Current,"Explicit Hide blocks held combination replay"), count += 1
        a.States["XButton1"] := false, route.Tick(), host.Current := 2, a.States["XButton1"] := true, route.Tick()
        AltAssert(host.Current=2,"Combination cannot steal a different picture slot"), count += 1
        host.Current := 0, route.Tick(), AltAssert(!host.Current,"Blocked combination waits for release"), count += 1
        a.States["XButton1"] := false, route.Tick(), a.States["XButton1"] := true, route.Tick()
        route.Text := StrReplace(route.Text,"AltEnabled=1","AltEnabled=0"), route.Tick()
        AltAssert(!host.Current,"Disabling alternate withdraws its independent visibility"), count += 1
        route.Text := route.Prefix, a.Reset(), route.Down(), route.Up(), a.Now += 200, route.Down()
        route.Text := StrReplace(route.Text,PM_Model.Sha256(alternate),StrReplace(Format("{:064}",0),"0","0"))
        failed := false
        try route.Read()
        catch
            failed := true
        AltAssert(failed,"Alternate image hash is always verified"), count += 1
        route.Up(), route.Text := StrReplace(route.Prefix,"ExpiresUnixMs=101000","ExpiresUnixMs=99000"), route.Tick()
        AltAssert(!host.Current,"Expired relay cannot create combination visibility"), count += 1
        FileAppend("PASS " count " alternate view checks; no GUI or input.`n","*")
    } finally {
        if route
            route.Stop()
        DirDelete(dir,true)
    }
}
try {
    if A_Args.Length!=2
        throw Error("Supply normal and alternate fixture PNGs")
    RunAltChecks(A_Args[1],A_Args[2]), ExitApp(0)
} catch as altError {
    FileAppend("FAIL " altError.Message " line " altError.Line " file " altError.File "`n" altError.Stack "`n","**"), ExitApp(1)
}
