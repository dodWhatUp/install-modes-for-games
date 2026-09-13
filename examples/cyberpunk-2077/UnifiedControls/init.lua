-- Cyberpunk 2.31 / CET: bounded native graphics requests from OptiScaler.
-- No graphics writes on startup and no UserSettings.json rewriting.
local presetPath = "/graphics/presets"
local modes = {"DLAA", "Quality", "Balanced", "Performance", "UltraPerformance"}
local queued, pending, cooldown, elapsed, overlay = nil, nil, 0, 0, false
local notices, session, lastId, lastResult = {}, "", "", "Ready"

local function writeFile(name, text)
    local file = io.open(name, "w")
    if file then file:write(text); file:close() end
end
local function notify(text, bad)
    lastResult = text:gsub("[|\r\n]", " "):sub(1, 220)
    print("[GraphicsHotkeys] " .. lastResult)
    if #notices >= 4 then table.remove(notices, 1) end
    notices[#notices+1] = {text=lastResult, bad=bad}
    writeFile("sr-last-result.txt", tostring(os.time()) .. "|" .. lastResult)
end
local function var(name, path)
    local settings = Game.GetSettingsSystem()
    if not settings then error("Game settings are unavailable") end
    local option = settings:GetVar(path or presetPath, name)
    if not option then error("Unavailable setting: " .. name) end
    return option
end
local function value(name, path) return var(name, path):GetValue() end
local function nextMode(mode)
    -- Keep F6's established four-mode cycle; Ultra Performance is menu-only.
    for i=1,4 do if mode==modes[i] then return modes[i%4+1] end end
    return "Quality"
end
local function request(action, argument, id)
    if overlay then notify("Close the CET console first", true); return false end
    if cooldown>0 or queued or pending then return false end
    queued={action=action, argument=argument, id=id or "hotkey"}
    return true
end

-- Resolve and validate every field before changing any setting. Reverse rollback
-- includes delayed readback failures, not merely rejected SetValue calls.
local function changesFor(action, argument)
    local changes={}
    local function add(name, target, path)
        local option=var(name,path)
        changes[#changes+1]={option=option, name=name, before=option:GetValue(), target=target}
    end
    local function bounds(minimum, maximum)
        local oldMax=tonumber(value("DRS_MaxResolution"))
        if not oldMax then error("Native resolution bounds unavailable") end
        if minimum>oldMax then
            add("DRS_MaxResolution",maximum); add("DRS_MinResolution",minimum)
        else
            add("DRS_MinResolution",minimum); add("DRS_MaxResolution",maximum)
        end
    end
    if action=="cycle" or action=="quality" then
        local mode=action=="cycle" and nextMode(tostring(value("DLSS"))) or argument
        local valid=false
        for _, candidate in ipairs(modes) do if candidate==mode then valid=true end end
        if not valid then error("Unknown DLSS quality") end
        add("DynamicResolutionScaling",false)
        add("DLSS",mode)
    elseif action=="scale" then
        local percent=tonumber(argument)
        if not percent or percent%1~=0 or percent<50 or percent>100 then error("SR scale must be 50-100%") end
        -- Equal native DRS bounds request fixed engine render dimensions.
        -- The UI reports real buffer dimensions separately from this request.
        bounds(percent,percent)
        add("DynamicResolutionScaling",true)
    elseif action=="dynamic" then
        if argument=="off" then
            add("DynamicResolutionScaling",false)
        else
            local target,minimum,maximum=argument:match("^(%d+),(%d+),(%d+)$")
            target,minimum,maximum=tonumber(target),tonumber(minimum),tonumber(maximum)
            if not target or target<10 or target>240 then error("Dynamic DLSS target must be 10-240 FPS") end
            if not minimum or not maximum or minimum<50 or maximum>100 or minimum>=maximum then
                error("Dynamic DLSS requires 50% <= minimum < maximum <= 100%")
            end
            -- The engine owns the per-frame controller. Never use MFG output FPS
            -- or repeatedly switch quality modes from Lua to simulate DRS.
            bounds(minimum,maximum)
            add("DRS_TargetFPS",target)
            add("DynamicResolutionScaling",true)
        end
    elseif action=="rr" then
        if argument~="0" and argument~="1" then error("Invalid RR state") end
        if argument=="1" and value("RayTracing","/graphics/raytracing")~=true then
            error("Enable ray tracing in Cyberpunk before enabling RR")
        end
        add("DLSS_D",argument=="1")
    elseif action=="fg" then
        if argument~="0" and argument~="1" then error("Invalid FG state") end
        if tostring(value("FrameGeneration"))~="DLSS" then error("Select the DLSS FG backend in Cyberpunk and restart first") end
        add("DLSSFrameGen",argument=="1")
    else error("Unknown graphics command") end
    return changes
end
local function rollback(changes)
    local ok=true
    for i=#changes,1,-1 do
        local c=changes[i]
        if not pcall(function() c.option:SetValue(c.before) end) then ok=false end
    end
    if not pcall(function() Game.GetSettingsSystem():ConfirmChanges() end) then ok=false end
    for _, c in ipairs(changes) do
        local read,actual=pcall(function() return c.option:GetValue() end)
        if not read or actual~=c.before then ok=false end
    end
    return ok
end
local function publish()
    local ready=Game.GetPlayer()~=nil
    local function read(name,path)
        local ok,result=pcall(value,name,path)
        if not ok then return "?" end
        if type(result)=="boolean" then return result and "1" or "0" end
        return tostring(result):gsub("[|\r\n]", " "):sub(1,64)
    end
    writeFile("graphics-status.txt",table.concat({"3",session,tostring(os.time()),ready and "1" or "0",
        read("ResolutionScaling"),read("DLSS"),read("DynamicResolutionScaling"),
        read("DRS_MinResolution"),read("DRS_MaxResolution"),read("DLSS_D"),
        read("RayTracing","/graphics/raytracing"),read("DLSSFrameGen"),read("FrameGeneration"),
        read("DLSS_MultiFrameGeneration"),(cooldown>0 or pending or queued) and "1" or "0",lastId,lastResult,
        read("DRS_TargetFPS")},"|"))
    writeFile("sr-status.txt",tostring(os.time()).."|"..read("DLSS"))
end
registerHotkey("cycle_dlss_quality","Cycle DLSS quality (F6)",function() request("cycle","") end)
registerForEvent("onInit",function()
    session=tostring(os.time()).."-"..tostring(math.floor(os.clock()*1000000))
    writeFile("graphics-request.txt",""); writeFile("sr-request.txt","")
    notify("Ready: F12 controls SR, RR, FG and NR; F6 cycles DLSS quality")
    publish()
end)
registerForEvent("onOverlayOpen",function() overlay=true end)
registerForEvent("onOverlayClose",function() overlay=false end)
registerForEvent("onDraw",function()
    local draw=notices; notices={}
    for _,item in ipairs(draw) do
        pcall(function()
            local toast=ImGui.Toast.new(item.bad and ImGui.ToastType.Warning or ImGui.ToastType.Info,4500,item.text)
            toast:SetTitle("Graphics controls"); ImGui.ShowToast(toast)
        end)
    end
end)
registerForEvent("onUpdate",function(dt)
    cooldown=math.max(0,cooldown-dt)
    if pending then
        pending.delay=pending.delay-dt
        if pending.delay<=0 then
            local p=pending; pending=nil
            local ok=pcall(function()
                for _,c in ipairs(p.changes) do if c.option:GetValue()~=c.target then error("Readback mismatch") end end
            end)
            if ok and p.action=="dynamic" then
                if p.argument=="off" then notify("Native dynamic resolution disabled")
                else notify("Dynamic DLSS requested (FPS,min%,max%): "..p.argument.."; verify live dimensions and rendered FPS") end
            elseif ok then notify("Selected "..p.action..": "..p.argument.."; check live dimensions below")
            else notify("Change was rejected; "..(rollback(p.changes) and "previous settings restored" or "restore failed, check game settings"),true) end
        end
    end
    elapsed=elapsed+dt
    if elapsed>=0.25 then
        elapsed=0
        local f=io.open("graphics-request.txt","r")
        if f then
            local command=f:read(512); f:close()
            if command and command~="" then
                writeFile("graphics-request.txt","")
                local token,id,stamp,action,arg=command:match("^3|([^|]+)|([%w_-]+)|(%d+)|([%a]+)|([^|\r\n]*)%s*$")
                local age=stamp and os.time()-tonumber(stamp)
                if token==session and id~=lastId and age and age>=0 and age<=3 then
                    lastId=id
                    if not request(action,arg,id) then notify("Wait for the current graphics change to finish",true) end
                end
            end
        end
        publish()
    end
    if not queued or pending then return end
    local q=queued; queued=nil; cooldown=2
    local changes
    local ok,reason=pcall(function()
        if overlay or not Game.GetPlayer() then error("Load a game and close the CET console") end
        if tostring(value("ResolutionScaling"))~="DLSS" then error("Select DLSS upscaling in Cyberpunk first") end
        changes=changesFor(q.action,q.argument)
        for _,c in ipairs(changes) do c.option:SetValue(c.target) end
        Game.GetSettingsSystem():ConfirmChanges()
        for _,c in ipairs(changes) do if c.option:GetValue()~=c.target then error("Game rejected "..c.name) end end
    end)
    if not ok then
        local restored=not changes or rollback(changes)
        notify(tostring(reason)..(restored and "; previous settings preserved" or "; restore failed, check game settings"),true)
    else pending={changes=changes,action=q.action,argument=q.argument,delay=0.6} end
end)
return {request=request}
