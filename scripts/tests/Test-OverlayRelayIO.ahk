#Requires AutoHotkey v2.0
#SingleInstance Off
#Warn All, StdOut
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk
class PM_Model {
}
class RelayIOHost {
    __New(directory) {
        this.Dir:=directory
    }
}
CheckRelayIO(ok,message) {
    if !ok
        throw Error(message)
}
RunRelayIO() {
    root:=A_Temp "\StudioRelayIOFixture-" DllCall("GetCurrentProcessId") "-" A_TickCount
    DirCreate(root)
    checks:=0
    try {
        reader:=StudioOverlayGroups(RelayIOHost(root)), reader.Path:=root "\relay.ini"
        expected:="[Overlay]`nSchema=1`nActive=0`n"
        FileAppend(expected,reader.Path,"UTF-8-RAW")
        CheckRelayIO(reader.LoadSnapshot()=expected,"Complete UTF-8 relay must be read")
        checks+=1
        stream:=FileOpen(reader.Path,"r","UTF-8")
        try {
            FileAppend(expected "LayerShow=0`n",root "\new.ini","UTF-8-RAW")
            FileMove(root "\new.ini",reader.Path,1)
            CheckRelayIO(stream.Read()=expected,"Shared handle must retain complete prior snapshot during replacement")
            checks+=1
            CheckRelayIO(InStr(reader.LoadSnapshot(),"LayerShow=0"),"New reader must see complete replacement")
            checks+=1
        } finally stream.Close()
        rejected:=false
        reader.Path:=root "\large.ini"
        FileAppend(StrReplace(Format("{:17000}","x")," ","x"),reader.Path,"UTF-8-RAW")
        try reader.LoadSnapshot()
        catch
            rejected:=true
        CheckRelayIO(rejected,"Oversized snapshots must remain refused")
        checks+=1
        reader.Path:=root "\missing.ini", rejected:=false
        try reader.LoadSnapshot()
        catch
            rejected:=true
        CheckRelayIO(rejected,"Missing snapshots must never return cached data")
        checks+=1
        FileAppend("PASS " checks " headless relay I/O checks`n","*")
    } catch as issue {
        FileAppend("FAIL " issue.Message " line " issue.Line "`n","*")
        ExitApp(1)
    } finally {
        if InStr(root,A_Temp "\StudioRelayIOFixture-")!=1
            throw Error("Fixture cleanup scope refused")
        DirDelete(root,true)
    }
    ExitApp(0)
}
RunRelayIO()
