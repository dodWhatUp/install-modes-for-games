#Requires AutoHotkey v2.0
#SingleInstance Ignore
#MaxThreadsPerHotkey 1
#Include %A_LineFile%\..\GameInputModule.ahk

; Standalone adapter ONLY. Do not #Include this launcher in the larger host.
if A_Args.Length && A_Args[1] = "--self-test" {
    try {
        GI_RunSelfTests()
        ExitApp 0
    } catch as err {
        FileAppend err.Message "`n", "**"
        ExitApp 1
    }
}

KeyHistory 0 ; Standalone privacy default; the module never overrides host policy.
giSettings := GI_BuildSettings()
for giArg in A_Args {
    if giArg = "--extended"
        giSettings.EnableExtended := true
}
giModule := GameInputModule(giSettings)
; Standalone owns these temporary chords. Stop all older helper versions first.
giModule.Start(true)
giMenu := Menu()
giMenu.Add("Show/hide status", ObjBindMethod(giModule, "ToggleIndicator"))
giMenu.Add("Pause/resume output", ObjBindMethod(giModule, "TogglePause"))
giMenu.Add("Sound on/off", ObjBindMethod(giModule, "ToggleSound"))
if giSettings.EnableExtended
    giMenu.Add("Prepare one-shot input", ObjBindMethod(giModule, "OpenEditor"))
giMenu.Add("Cancel pending/active input", ObjBindMethod(giModule, "Cancel"))
giMenu.Add("Exit standalone helper", (*) => ExitApp())
A_TrayMenu.Add("Game input helper", giMenu)
A_IconTip := "GameInputModule " giSettings.Version
Hotkey "^!F8", ObjBindMethod(giModule, "ToggleIndicator")
Hotkey "^!p", ObjBindMethod(giModule, "TogglePause")
Hotkey "^!Esc", (*) => ExitApp()
if giSettings.EnableExtended
    Hotkey "^!t", ObjBindMethod(giModule, "OpenEditor")

