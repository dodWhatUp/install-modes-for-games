#Requires AutoHotkey v2.0
#SingleInstance Off
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk
; Real hash/size checks, task-owned copy only, no window/hook/input.
RunResponse() {
    root:=A_Temp "\OverlayResponseFixture-" DllCall("GetCurrentProcessId") "-" A_TickCount
    DirCreate(root)
    checks:=0
    try {
        path:=root "\map.png"
        FileCopy(A_Args[1],path)
        hash:=PM_Model.Sha256(path),expected:=PM_Model.ImageSize(path)
        first:=PM_Model.VerifiedImageSize(path,hash)
        if first[1]!=expected[1] || first[2]!=expected[2]
            throw Error("Decoded dimensions differ")
        checks+=1
        first[1]:=99999
        second:=PM_Model.VerifiedImageSize(path,hash)
        if second[1]!=expected[1]
            throw Error("Caller mutated shared dimension cache")
        checks+=1
        module:=StudioPictureModule({Dir:root},{ImageSize:(*) => [99999,1],MonitorBounds:(*) => [0,0,1920,1080]})
        slot:={File:path,RouteImageHash:hash,Width:800,Opacity:100,Position:"Center",OffsetX:0,OffsetY:0}
        geometry:=module.Geometry(slot),dims:=PM_Model.SizeFor("Pixels",800,expected[1],expected[2],1920,1080)
        if geometry.w!=dims[1] || geometry.h!=dims[2] || geometry.x!=Floor((1920-dims[1])/2)
            throw Error("Routed geometry ignored hash-verified dimensions")
        checks+=1
        FileAppend("modified",path),refused:=false
        try PM_Model.VerifiedImageSize(path,hash)
        catch
            refused:=true
        if !refused
            throw Error("Changed bytes reused old dimensions")
        checks+=1
        FileDelete(path),refused:=false
        try PM_Model.VerifiedImageSize(path,hash)
        catch
            refused:=true
        if !refused
            throw Error("Missing file reused old dimensions")
        checks+=1
        FileAppend("PASS " checks " headless image dimension cache checks`n","*")
    } catch as issue {
        FileAppend("FAIL " issue.Message " line " issue.Line "`n","*")
        ExitApp(1)
    } finally {
        if InStr(root,A_Temp "\OverlayResponseFixture-")!=1
            throw Error("Cleanup scope refused")
        DirDelete(root,true)
    }
    ExitApp(0)
}
RunResponse()
