#Requires AutoHotkey v2.0
#SingleInstance Ignore
#Include %A_ScriptDir%\GameInputModule.ahk

; EXAMPLE HOST, not a patch to Overlay Studio/your existing program.
; Including GameInputModule.ahk does nothing until this host enables it.
if A_Args.Length && A_Args[1] = "--self-test" {
    try {
        GI_RunSelfTests()
        ExitApp 0
    } catch as err {
        FileAppend err.Message "`n", "**"
        ExitApp 1
    }
}

giFeature := GameInputModule() ; Core mode. Host may explicitly opt into extended.
giHostMenu := Menu()
giHostMenu.Add("Enable after binding review", GI_HostEnable)
giHostMenu.Add("Pause/resume", ObjBindMethod(giFeature, "TogglePause"))
giHostMenu.Add("Show/hide status", ObjBindMethod(giFeature, "ToggleIndicator"))
giHostMenu.Add("Cancel action", ObjBindMethod(giFeature, "Cancel"))
giHostMenu.Add("Stop module (keep host running)", ObjBindMethod(giFeature, "Stop"))
A_TrayMenu.Add("Optional game input", giHostMenu)
; In the real host, call these methods from existing controls. Do not blindly add
; global chords or overwrite its tray, recording, physical layers or shutdown.

GI_HostEnable(*)
{
    global giFeature
    if MsgBox("Have you reviewed BindingPlan and reserved its keys in this host,"
        . " other AHK scripts, game/mods and mapper? This is not automatic detection.",
        "Enable optional game input", "YesNo Default2") = "Yes"
        giFeature.Start(true)
}
