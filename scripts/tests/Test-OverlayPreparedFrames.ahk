#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk

class PreparedFixtureGeometry extends StudioPictureModule {
    __New() {
    }
    Geometry(slot) {
        return {w: 600, h: 400}
    }
}
class PreparedFixtureHost {
    __New(dir) {
        this.Dir := dir, this.Current := 0, this.Generation := 9, this.Pressed := Map()
        this.Slots := [{Source:"Local",Enabled:1,Mode:"Hold"}], this.Pictures := PreparedFixtureGeometry()
        this.Logs := []
    }
    WriteLog(message) {
        this.Logs.Push(message)
    }
}
class PreparedFixtureRoute extends StudioOverlayGroups {
    __New(host,path,hash) {
        super.__New(host)
        this.Slot := 1, this.Valid := true
        this.Source := {Values:Map("WarmCount","2","WarmFile1",path,"WarmSHA2561",hash,"WarmFile2",path,"WarmSHA2562",hash)}
    }
    LoadSnapshot() {
        return "[Overlay]`nfixture-current-context"
    }
    Read(*) {
        if !this.Valid
            throw Error("Fixture stale/foreign context")
        return this.Source
    }
    Resolve(index,legacy) {
        return legacy.Clone()
    }
}

; Real GDI image preparation only: no GUI, timer, hotkey, display or input.
PreparedCheck(condition,message) {
    if !condition
        throw Error(message)
}
PreparedClock() {
    static frequency := 0
    if !frequency
        DllCall("QueryPerformanceFrequency", "int64*", &frequency)
    count := 0
    DllCall("QueryPerformanceCounter", "int64*", &count)
    return count * 1000 / frequency
}
RunPreparedChecks() {
    if A_Args.Length != 1
        throw Error("Pass a dedicated writable fixture PNG, never a native/user source.")
    path := A_Args[1], raw := FileRead(path,"RAW"), hash := PM_Model.Sha256(path)
    cache := PM_PreparedSurfaceCache, cache.Clear()
    first := cache.Acquire(path,hash,600,400), firstBitmap := first.Surface.Bitmap
    misses := cache.Misses
    second := cache.Acquire(path,hash,600,400)
    PreparedCheck(second.Surface.Bitmap = firstBitmap && cache.Misses = misses, "Same verified pixels reused without decode")
    first.Close()
    PreparedCheck(second.Surface.Hdc != 0 && second.Surface.Bitmap = firstBitmap,"One lease closing preserves another")
    cache.Clear()
    PreparedCheck(second.Surface.Hdc != 0 && cache.Bytes = 0,"Eviction/clear preserves the outstanding window lease")
    second.Close()
    cache.MaxEntries := 2, cache.MaxBytes := 1024
    held := cache.Acquire(path,hash,10,10)
    one := cache.Acquire(path,hash,11,10), one.Close()
    two := cache.Acquire(path,hash,12,10), two.Close()
    PreparedCheck(cache.Entries.Count <= 2 && cache.Bytes <= 1024,"Entry and pixel-byte bounds enforced")
    PreparedCheck(held.Surface.Hdc != 0,"Evicted held surface remains live")
    held.Close(), cache.Clear(), cache.MaxEntries := 8, cache.MaxBytes := 32*1024*1024
    item := cache.Acquire(path,hash,600,400), item.Close()
    writer := FileOpen(path,"a"), writer.Write("x"), writer.Close()
    refused := false
    try cache.Acquire(path,hash,600,400)
    catch
        refused := true
    writer := FileOpen(path,"w"), writer.RawWrite(raw), writer.Close()
    PreparedCheck(refused,"A cached image still refuses changed current file bytes")
    item := cache.Acquire(path,hash,600,400), item.Close()
    PreparedCheck(cache.Entries.Count = 1,"Restored exact source reuses its valid prepared surface")
    cache.Clear(), host := PreparedFixtureHost(A_ScriptDir), route := PreparedFixtureRoute(host,path,hash)
    misses := cache.Misses, route.WarmTick(), route.NextWarm := 0, route.WarmTick()
    PreparedCheck(route.WarmDone && cache.Misses = misses + 1,"Idle preparation deduplicates layers before any press")
    PreparedCheck(host.Current = 0 && host.Generation = 9 && host.Pressed.Count = 0,"Preparation never shows a map or owns a hold")
    cache.Clear(), route.WarmDone := false, route.WarmIndex := 1, route.NextWarm := 0
    host.Pressed[1] := {Mode:"Hold"}, misses := cache.Misses, route.WarmTick()
    PreparedCheck(cache.Misses = misses,"Held input prevents background preparation")
    host.Pressed.Clear(), route.Valid := false, route.NextWarm := 0, route.WarmTick()
    PreparedCheck(cache.Entries.Count = 0 && !route.WarmDone,"Invalid context does not prepare hints")
    cold := [], warm := []
    Loop 8 {
        start := PreparedClock(), image := PM_AlphaSurface(path,896,614), image.Close()
        cold.Push(PreparedClock()-start)
    }
    item := cache.Acquire(path,hash,896,614), item.Close()
    Loop 8 {
        start := PreparedClock(), image := cache.Acquire(path,hash,896,614), image.Close()
        warm.Push(PreparedClock()-start)
    }
    FileAppend("PASS 12 prepared-surface/idle-owner checks; no GUI/input. Cold prepare ms: " JoinPrepared(cold) " | Warm acquire ms: " JoinPrepared(warm) "`n", "*")
    cache.Clear()
}
JoinPrepared(values) {
    text := ""
    for sampleValue in values
        text .= (text = "" ? "" : ",") Round(sampleValue,2)
    return text
}
try {
    RunPreparedChecks()
    ExitApp(0)
} catch as preparedError {
    FileAppend("FAIL " preparedError.Message " at " preparedError.Line "`n", "**")
    PM_PreparedSurfaceCache.Clear()
    ExitApp(1)
}
