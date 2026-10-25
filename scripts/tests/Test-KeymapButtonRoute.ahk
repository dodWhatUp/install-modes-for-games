#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioPictureModule.ahk
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk
; Real snapshot/hash/lifetime/slot routing, virtual display, no GUI/input/hooks.
class LinkHost {
    __New(dir) {
        this.Dir:=dir, this.Slots:=[], this.Pressed:=Map(), this.Current:=0, this.Generation:=10
        Loop 2
            this.Slots.Push({Source:"Local",Enabled:1,Mode:"Hold",Key:"F" (13+A_Index),Name:"fixture",Opacity:100})
        this.Enabled:=true,this.Logs:=[],this.Shows:=0,this.Reuses:=0,this.Route:=0
    }
    WriteLog(message) {
        this.Logs.Push(message)
    }
    HideCurrent(*) {
        this.Route.CancelPending(),this.Current:=0,this.Generation+=1
    }
    ShowSlot(index, slot) {
        this.HideCurrent(),this.Current:=index,this.Generation+=1,this.Shows+=1
        return this.Generation
    }
    ShowLocal(slot,reuse:=false) {
        this.Shows+=1,this.Reuses+=reuse?1:0
        return true
    }
}
class LinkReader extends StudioLinkedMapRoute {
    NowMs() {
        return 100000
    }
    ForegroundExe() {
        return "C:\Fixture\Game.exe"
    }
}
class LinkParent extends StudioOverlayGroups {
    NewChild(index,path) {
        return LinkReader(this,index,path)
    }
}
LinkAssert(condition,message) {
    if !condition
        throw Error(message)
}
LinkSnapshot(path,image,active:=1,linked:=1,state:="first") {
    value:="[Overlay]`nSchema=1`nLinked=" linked "`nActive=" active "`nExpiresUnixMs=101000`nExe=C:\Fixture\Game.exe`nFile=" image "`nSHA256=" PM_Model.Sha256(image)
        . "`nLayerState=" state "`nsize_mode=Pixels`nsize_value=600`nopacity=100`nmonitor=1`nanchor=Center`noffset_x=0`noffset_y=0`nFadeInMs=120`nFadeOutMs=120`n"
    if FileExist(path)
        FileDelete(path)
    FileAppend(value,path,"UTF-8")
}
RunLinkedRoutes(image) {
    dir:=A_Temp "\KeymapButtonRouteFixture-" DllCall("GetCurrentProcessId") "-" A_TickCount
    DirCreate(dir), parent:=0
    try {
        host:=LinkHost(dir),parent:=LinkParent(host),host.Route:=parent
        parent.Enabled:=true,parent.Slot:=1,parent.Path:=dir "\overlay-selection.ini"
        path:=dir "\overlay-selection-slot-2.ini"
        LinkAssert(parent.Resolve(2,host.Slots[2])=host.Slots[2],"Unlinked slot retains its original owner")
        LinkSnapshot(path,image)
        result:=parent.Resolve(2,host.Slots[2])
        LinkAssert(result.RouteSlot=2 && result.Mode="Hold" && result.Key="F15" && result.File=image,"Fixed map uses existing slot trigger/mode")
        LinkAssert(result.FadeInMs=120 && result.FadeOutMs=120,"Linked map retains fade preference")
        host.Current:=2,host.Pressed[2]:={Token:host.Generation,Mode:"Hold"},token:=host.Generation
        LinkSnapshot(path,image,1,1,"updated"),parent.Tick()
        LinkAssert(host.Reuses=1 && host.Current=2 && host.Generation=token,"Linked map refresh keeps release token and display window")
        LinkSnapshot(path,image,0),parent.Tick()
        LinkAssert(host.Current=0 && parent.Children[2].PendingHold,"Invalid linked map hides and remembers only the actual hold")
        LinkSnapshot(path,image),parent.Tick()
        LinkAssert(host.Current=2 && host.Pressed[2].Token=host.Generation,"Same held linked button recovers through existing release owner")
        host.Pressed.Delete(2),host.HideCurrent(),parent.Tick()
        LinkAssert(host.Current=0 && !parent.Children[2].PendingHold,"Released button cannot recover")
        LinkSnapshot(path,image,1,0),parent.Tick()
        LinkAssert(!parent.Children.Has(2),"Explicit unlink removes the scoped reader")
        primary:=dir "\overlay-selection-slot-1.ini",LinkSnapshot(primary,image)
        result:=parent.Resolve(1,host.Slots[1])
        LinkAssert(result.RouteSlot=1 && parent.Children.Has(1),"Primary button may explicitly select a fixed guide")
        host.Current:=1,host.Pressed[1]:={Token:host.Generation,Mode:"Hold"},parent.Tick()
        LinkAssert(host.Current=1,"Primary fixed guide is not overwritten by the automatic layer route")
        LinkAssert(parent.ReadForSlot(1).Values["Linked"]="1","Fade validation reads the same slot source")
        parent.Stop()
        LinkAssert(!parent.Enabled && host.Current=0,"Route Off hides linked maps without new timers/hotkeys")
        parent.Enabled:=true
        LinkAssert(parent.Resolve(1,host.Slots[1]).RouteSlot=1 && parent.Children[1].Enabled,"Re-enable restores the linked reader, never a static fallback")
        FileAppend("PASS 13 linked-button route checks; virtual display only.`n","*")
    } finally {
        if parent
            parent.Stop()
        DirDelete(dir,true)
    }
}
try {
    RunLinkedRoutes(A_Args[1])
    ExitApp(0)
} catch as linkError {
    FileAppend("FAIL " linkError.Message " at " linkError.Line "`n","**")
    ExitApp(1)
}
