local callbacks, hotkeys = {}, {}
local current, scaling, confirms = "Auto", "DLSS", 0
local hasPlayer, reject, logged = true, nil, {}
local failConfirm = false
local dynamic = false
local files = {}
local drawing, shown = false, {}
ImGui = {
    ToastType = { Warning = 1, Info = 2 },
    Toast = { new = function(kind, duration, message)
        assert(drawing, "ImGui must only be called from onDraw")
        return { SetTitle = function() end, message = message }
    end },
    ShowToast = function(toast)
        assert(drawing, "ImGui must only be called from onDraw")
        shown[#shown + 1] = toast.message
    end
}
io = { open = function(path, mode)
    if mode == "r" and files[path] == nil then return nil end
    if mode == "w" then files[path] = "" end
    return {
        read = function(_, size) return (files[path] or ""):sub(1, size) end,
        write = function(_, ...) for _, s in ipairs({...}) do files[path] = files[path] .. tostring(s) end end,
        close = function() end
    }
end }
registerForEvent = function(name, fn) callbacks[name] = fn end
registerHotkey = function(name, _, fn) hotkeys[name] = fn end
print = function(text) table.insert(logged, text) end
local quality = {
    GetValue = function() return current end,
    SetValue = function(_, value) if value ~= reject then current = value end end
}
local system = {
    GetVar = function(_, path, name)
        assert(path == "/graphics/presets")
        if name == "DLSS" then return quality end
        if name == "ResolutionScaling" then return { GetValue = function() return scaling end } end
        if name == "DynamicResolutionScaling" then return { GetValue = function() return dynamic end } end
        error("Unexpected setting access: " .. name)
    end,
    ConfirmChanges = function()
        if failConfirm then failConfirm = false; error("Simulated apply failure") end
        confirms = confirms + 1
    end
}
Game = {
    GetSettingsSystem = function() return system end,
    GetPlayer = function() if hasPlayer then return {} end end
}
files["sr-request.txt"] = "cycle|" .. os.time()
dofile("examples/cyberpunk-2077/GraphicsHotkeys/init.lua")
callbacks.onInit()
assert(confirms == 0 and current == "Auto", "Startup must not change settings")
assert(files["sr-request.txt"] == "", "Startup must discard old panel requests")
local function press()
    hotkeys.cycle_dlss_quality()
    callbacks.onUpdate(0.01)
end
local function settle() callbacks.onUpdate(2.1) end
for _, expected in ipairs({"Quality", "Balanced", "Performance", "DLAA", "Quality"}) do
    press()
    assert(current == expected, "Incorrect native quality cycle")
    local count = confirms
    press()
    assert(confirms == count, "Rapid key presses must not rebuild repeatedly")
    settle()
end
local count = confirms
callbacks.onOverlayOpen(); press(); settle(); callbacks.onOverlayClose()
assert(confirms == count, "CET overlay must block graphics hotkeys")
scaling = "FSR3"; press(); settle()
assert(confirms == count and current == "Quality", "Must not replace a different upscaler")
scaling = "DLSS"; hasPlayer = false; press(); settle()
assert(confirms == count, "Must not apply before a game is loaded")
hasPlayer = true; reject = "Balanced"; press(); settle()
assert(confirms == count + 1 and current == "Quality", "Rejected mode must restore and confirm previous value")
count = confirms
reject = nil; press(); settle()
assert(current == "Balanced" and confirms == count + 1, "Must recover after a rejected mode")
failConfirm = true; press(); settle()
assert(current == "Balanced", "Apply failure must restore the previous setting")
press(); settle()
assert(current == "Performance", "Must recover after an apply failure")
count = confirms
dynamic = true; press(); settle()
assert(confirms == count, "Fixed quality must not compete with dynamic resolution")
dynamic = false
files["sr-request.txt"] = "cycle|" .. os.time()
callbacks.onUpdate(0.6)
assert(current == "DLAA" and confirms == count + 1, "Compact panel must use the same native adapter")
assert(files["sr-request.txt"] == "", "Panel request must be consumed once")
settle()
count = confirms
callbacks.onUpdate(0.6)
assert(confirms == count, "Consumed requests must not replay")
for _, command in ipairs({"cycle|" .. (os.time()-10), "cycle|" .. (os.time()+10), "arbitrary_command", "cycle|1\nextra"}) do
    files["sr-request.txt"] = command
    callbacks.onUpdate(0.6)
    assert(confirms == count, "Malformed/stale/future requests must not mutate settings")
end
assert(files["sr-status.txt"]:match("|DLAA"), "Panel status must reflect native mode readback")
assert(#shown == 0, "Notifications must remain queued outside the drawing callback")
assert(files["sr-last-result.txt"]:match("game setting confirmed"), "Persist native readback result for diagnosis")
drawing = true; callbacks.onDraw(); drawing = false
assert(#shown > 0 and shown[#shown]:match("Selected DLSS: DLAA"), "Render confirmed mode visibly in onDraw")
local countShown = #shown
drawing = true; callbacks.onDraw(); drawing = false
assert(#shown == countShown, "Do not replay notifications")
return "PASS: cycle, cooldown, guards, rollback, startup, compact-panel protocol, native status and onDraw-only notifications"
