#Requires AutoHotkey v2.0
#SingleInstance Off
#Include %A_ScriptDir%\..\..\examples\game-input\StudioOverlayGroups.ahk
class PM_Model {
}
class StatusRoute extends StudioOverlayGroups {
    NowMs() {
        return 100000
    }
}
RunStatus() {
    reader:=StatusRoute({Dir:A_Temp}),checks:=0
    for row in [Map("Schema","1","Active","0","StatusReason","Native reader delayed","ExpiresUnixMs","101000"),
                Map("Schema","1","Active","1","ExpiresUnixMs","99950") ,
                Map("Schema","2","Active","1","ExpiresUnixMs","101000")] {
        message:=""
        try reader.ValidateLifetime(row)
        catch as issue
            message:=issue.Message
        if !message
            throw Error("Invalid relay accepted")
        if checks=0 && !InStr(message,"Selection inactive: Native reader delayed")
            throw Error("Inactive reason lost")
        if checks=1 && !InStr(message,"expired by 50 ms")
            throw Error("Expiry age lost")
        if checks=2 && !InStr(message,"schema")
            throw Error("Schema reason lost")
        checks+=1
    }
    reader.ValidateLifetime(Map("Schema","1","Active","1","ExpiresUnixMs","101000"))
    checks+=1
    FileAppend("PASS " checks " precise relay status checks`n","*")
    ExitApp(0)
}
try RunStatus()
catch as issue {
    FileAppend("FAIL " issue.Message " line " issue.Line,"*")
    ExitApp(1)
}
