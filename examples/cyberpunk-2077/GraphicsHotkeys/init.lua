-- Native DLSS quality cycling for Cyberpunk 2077 2.31 / CET 1.37.1.
-- F6 is prebound in CET bindings.json; F7 belongs to OptiScaler; F9 remains Quick Load.
local modes = { "DLAA", "Quality", "Balanced", "Performance" }
local queued = false
local verification = nil
local cooldown = 0
local overlayOpen = false
local bridgeElapsed = 0
local notifications = {}

local function clearRequest()
    local file = io.open("sr-request.txt", "w")
    if file then file:close() end
end

local function notify(message, isError)
    print("[GraphicsHotkeys] " .. message)
    -- CET only permits ImGui calls in onDraw. Queue from onUpdate/hotkeys.
    if #notifications >= 4 then table.remove(notifications, 1) end
    notifications[#notifications + 1] = { message = message, isError = isError }
    local file = io.open("sr-last-result.txt", "w")
    if file then file:write(tostring(os.time()), "|", message, "\n"); file:close() end
end

registerForEvent("onDraw", function()
    if #notifications == 0 then return end
    local pending = notifications
    notifications = {}
    for _, item in ipairs(pending) do
        local ok, reason = pcall(function()
            local kind = item.isError and ImGui.ToastType.Warning or ImGui.ToastType.Info
            local toast = ImGui.Toast.new(kind, 4000, item.message)
            toast:SetTitle("DLSS Super Resolution (F6)")
            ImGui.ShowToast(toast)
        end)
        if not ok then print("[GraphicsHotkeys] Notification failed: " .. tostring(reason)) end
    end
end)

local function nextMode(current)
    -- Auto or an unfamiliar mode starts at Quality, avoiding an immediate DLAA jump.
    for index, mode in ipairs(modes) do
        if current == mode then
            return modes[index % #modes + 1]
        end
    end
    return "Quality"
end

local function readControls()
    local settings = Game.GetSettingsSystem()
    if not settings then error("Game settings are not ready") end
    local scaling = settings:GetVar("/graphics/presets", "ResolutionScaling")
    local quality = settings:GetVar("/graphics/presets", "DLSS")
    if not scaling or not quality then error("Native DLSS controls are unavailable") end
    if tostring(scaling:GetValue()) ~= "DLSS" then
        error("Select DLSS in the game's graphics settings before using F6")
    end
    local dynamic = settings:GetVar("/graphics/presets", "DynamicResolutionScaling")
    if dynamic and dynamic:GetValue() == true then
        error("Disable native dynamic resolution before cycling fixed DLSS quality")
    end
    return settings, quality
end

local function requestCycle()
    if overlayOpen then notify("Close the CET overlay before using F6", true); return end
    if cooldown > 0 or queued or verification then return end
    queued = true
end

registerHotkey("cycle_dlss_quality", "Cycle native DLSS quality (F6)", requestCycle)

registerForEvent("onInit", function()
    clearRequest() -- Never replay a request from an earlier session.
    print("[GraphicsHotkeys] Ready: F6 or the NR compact panel cycles native DLSS quality.")
end)

registerForEvent("onOverlayOpen", function() overlayOpen = true end)
registerForEvent("onOverlayClose", function() overlayOpen = false end)

registerForEvent("onUpdate", function(delta)
    cooldown = math.max(0, cooldown - delta)

    bridgeElapsed = bridgeElapsed + delta
    if bridgeElapsed >= 0.5 then
        bridgeElapsed = 0
        local file = io.open("sr-request.txt", "r")
        if file then
            local command = file:read(128)
            file:close()
            if command and command ~= "" then
                clearRequest()
                local stamp = tonumber(command:match("^cycle|(%d+)%s*$"))
                local age = stamp and os.time() - stamp
                if age and age >= 0 and age <= 3 then requestCycle() end
            end
        end
        local ok, mode = pcall(function()
            if not Game.GetPlayer() then return "Load a game" end
            local _, quality = readControls()
            return tostring(quality:GetValue())
        end)
        local status = io.open("sr-status.txt", "w")
        if status then
            status:write(tostring(os.time()), "|", ok and mode or "Select fixed DLSS in game", "\n")
            status:close()
        end
    end

    if verification then
        verification.delay = verification.delay - delta
        if verification.delay <= 0 then
            local pending = verification
            verification = nil
            local ok, result = pcall(function()
                local _, quality = readControls()
                return tostring(quality:GetValue())
            end)
            if ok and result == pending.target then
                notify("Selected DLSS: " .. result .. " (game setting confirmed)")
            else
                notify("DLSS change not confirmed; check the game's graphics menu", true)
            end
        end
        return
    end

    if not queued then return end
    queued = false
    cooldown = 2.0
    if overlayOpen then return end

    -- Changes are queued from the key callback and applied in the game update event.
    -- Do not request an immediate disk save or rewrite unrelated graphics settings.
    local ok, result = pcall(function()
        if not Game.GetPlayer() then error("Load a game before cycling DLSS quality") end
        local settings, quality = readControls()
        local previous = tostring(quality:GetValue())
        local target = nextMode(previous)
        local applied, reason = pcall(function()
            quality:SetValue(target)
            if tostring(quality:GetValue()) ~= target then
                error("This build did not accept DLSS " .. target)
            end
            settings:ConfirmChanges()
        end)
        if not applied then
            local restored = pcall(function()
                quality:SetValue(previous)
                settings:ConfirmChanges()
                if tostring(quality:GetValue()) ~= previous then error("Restore rejected") end
            end)
            error(tostring(reason) .. (restored and "; previous setting restored" or
                "; restore failed, check the game's graphics menu"))
        end
        verification = { target = target, delay = 0.5 }
        print("[GraphicsHotkeys] Requested native DLSS: " .. previous .. " -> " .. target)
        return target
    end)
    if not ok then notify(tostring(result), true) end
end)

return { cycle = requestCycle }
