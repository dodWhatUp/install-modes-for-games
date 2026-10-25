#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk

; Headless GDI+ pixels and resource lifecycle only. No GUI, input or screen read.
AssertAlpha(ok, message) {
    if !ok
        throw Error(message)
}
PixelAt(surface, x, y) {
    return NumGet(surface.Bits, (y * surface.Width + x) * 4, "uint")
}
RunAlphaTests() {
    if A_Args.Length != 1
        throw Error("Supply the generated RGBA fixture path.")
    fixture := A_Args[1], count := 0
    surface := PM_AlphaSurface(fixture, 12, 4)
    try {
        AssertAlpha(PixelAt(surface, 1, 2) = 0, "Transparent pixels must remain zero")
        count += 1
        AssertAlpha(PixelAt(surface, 5, 2) = 0xFFFF0000, "Solid red must stay opaque")
        count += 1
        AssertAlpha(PixelAt(surface, 10, 2) = 0x80008000, "Half-alpha green must be premultiplied")
        count += 1
    } finally surface.Close()
    AssertAlpha(!surface.Hdc && !surface.Bitmap && !surface.Token && !surface.Module, "Close releases all resources")
    count += 1
    surface.Close() ; Idempotent close.
    baseline := DllCall("GetGuiResources", "ptr", DllCall("GetCurrentProcess", "ptr"), "uint", 0, "uint")
    Loop 40 {
        surface := PM_AlphaSurface(fixture, 120, 40)
        try {
            AssertAlpha(PixelAt(surface, 10, 20) = 0, "Scaled clear background must stay clear")
            AssertAlpha(PixelAt(surface, 55, 20) = 0xFFFF0000, "Scaled opaque content must remain readable")
        } finally surface.Close()
    }
    count += 2
    invalid := false
    try surface := PM_AlphaSurface(fixture ".missing", 12, 4)
    catch
        invalid := true
    AssertAlpha(invalid, "Missing image must fail closed")
    count += 1
    finalCount := DllCall("GetGuiResources", "ptr", DllCall("GetCurrentProcess", "ptr"), "uint", 0, "uint")
    AssertAlpha(finalCount <= baseline + 1, "Repeated display and failed decode must not leak GDI objects")
    count += 1
    invalid := false
    try surface := PM_AlphaSurface(fixture, 8192, 8192)
    catch
        invalid := true
    AssertAlpha(invalid, "Oversized surface must be refused before allocation")
    count += 1
    FileAppend("PASS " count " alpha surface checks (headless; no windows).`n", "*")
}
try {
    RunAlphaTests()
    ExitApp(0)
} catch as alphaTestError {
    FileAppend("FAIL " alphaTestError.Message " at " alphaTestError.Line "`n", "**")
    ExitApp(1)
}
