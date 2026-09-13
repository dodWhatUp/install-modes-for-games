#pragma once
#include <Config.h>
#include <Util.h>
#include <json.hpp>
#include <Windows.h>
#include <array>
#include <cmath>
#include <fstream>
#include <limits>
#include <type_traits>
#ifndef PERSONAL_PROFILES_TEST
#include <imgui/imgui.h>
#endif

namespace DlssNr::PersonalProfiles
{
using Json = nlohmann::json;
inline std::array<Json, 4> slots;
inline int active = 0;
inline bool initialized = false, available = false;
inline std::string error;
inline ULONGLONG lastSelection = 0;
inline std::filesystem::path Path() { return Util::DllPath().parent_path() / L"DlssNrProfiles.json"; }

template<class Fn> void Visit(Config* c, Fn fn)
{
    fn("Enabled", c->DlssNrEnabled);
    fn("RunBeforeSr", c->DlssNrRunBeforeSr);
    fn("FinishedPicture", c->DlssNrFinishedPicture);
    fn("DeferredDlss", c->DlssNrDeferredDlss);
    fn("ResidualAcrossRr", c->DlssNrResidualAcrossRr);
    fn("ResidualAcrossRrBlend", c->DlssNrResidualAcrossRrBlend);
    fn("ResidualFg", c->DlssNrResidualFg);
    fn("Precision", c->DlssNrPrecision);
    fn("ResidualFgApproxCamera", c->DlssNrResidualFgApproxCamera);
    fn("Preset", c->DlssNrPreset);
    fn("Intensity", c->DlssNrIntensity);
    fn("Style", c->DlssNrStyle);
    fn("Pass2Preset", c->DlssNrPass2Preset);
    fn("Pass2Style", c->DlssNrPass2Style);
    fn("Pass3Preset", c->DlssNrPass3Preset);
    fn("Pass3Style", c->DlssNrPass3Style);
    fn("LocalStructure", c->DlssNrLocalStructure);
    fn("LocalTone", c->DlssNrLocalTone);
    fn("SkinStructure", c->DlssNrSkinStructure);
    fn("AutoMask", c->DlssNrAutoMask);
    fn("SkinProtection", c->DlssNrSkinProtection);
    fn("SkinToneEnabled", c->DlssNrSkinToneEnabled);
    fn("SkinDetail", c->DlssNrSkinDetail);
    fn("SkinColour", c->DlssNrSkinColour);
    fn("EnvironmentDetail", c->DlssNrEnvironmentDetail);
    fn("EnvironmentColour", c->DlssNrEnvironmentColour);
    fn("ShowSkinMask", c->DlssNrShowSkinMask);
    fn("Pass2Intensity", c->DlssNrPass2Intensity);
    fn("Pass2LocalStructure", c->DlssNrPass2LocalStructure);
    fn("Pass2LocalTone", c->DlssNrPass2LocalTone);
    fn("Pass2SkinStructure", c->DlssNrPass2SkinStructure);
    fn("Pass2AutoMask", c->DlssNrPass2AutoMask);
    fn("Pass3Intensity", c->DlssNrPass3Intensity);
    fn("Pass3LocalStructure", c->DlssNrPass3LocalStructure);
    fn("Pass3LocalTone", c->DlssNrPass3LocalTone);
    fn("Pass3SkinStructure", c->DlssNrPass3SkinStructure);
    fn("Pass3AutoMask", c->DlssNrPass3AutoMask);
    fn("UnlockPasses", c->DlssNrUnlockPasses);
    fn("TransferStrength", c->DlssNrTransferStrength);
    fn("ColourStrength", c->DlssNrColourStrength);
    fn("ReversibleMode", c->DlssNrReversibleMode);
    fn("ApplyModel", c->DlssNrApplyModel);
    fn("MaxRatio", c->DlssNrMaxRatio);
    fn("Transfer", c->DlssNrTransfer);
    fn("WhitePointFromExposure", c->DlssNrWhitePointFromExposure);
    fn("DebugView", c->DlssNrDebugView);
    fn("Compare", c->DlssNrCompare);
    fn("CompareSplit", c->DlssNrCompareSplit);
    fn("CompareZoom", c->DlssNrCompareZoom);
    fn("CompareSwap", c->DlssNrCompareSwap);
    fn("CompareTags", c->DlssNrCompareTags);
    fn("TagScale", c->DlssNrTagScale);
    fn("WorkingScale", c->DlssNrWorkingScale);
    fn("ScalingDownscaler", c->DlssNrScalingDownscaler);
    fn("WhitePointSource", c->DlssNrWhitePointSource);
    fn("ScanMeter", c->DlssNrScanMeter);
    fn("ScanAnchorValue", c->DlssNrScanAnchorValue);
    fn("ScanAnchorWhitePoint", c->DlssNrScanAnchorWhitePoint);
    fn("ScanAnchors", c->DlssNrScanAnchors);
    fn("ScanInverted", c->DlssNrScanInverted);
    fn("WhitePointTrim", c->DlssNrWhitePointTrim);
    fn("ScanTrim", c->DlssNrScanTrim);
    fn("Passes", c->DlssNrPasses);
    fn("WhitePointScale", c->DlssNrWhitePointScale);
    for (size_t i = 0; i < 27; ++i) {
        auto& p = c->DlssNrExtraPasses[i];
        const auto prefix = "Pass" + std::to_string(i + 4);
        fn(prefix + "Style", p.style); fn(prefix + "Intensity", p.intensity);
        fn(prefix + "LocalStructure", p.structure); fn(prefix + "LocalTone", p.tone);
        fn(prefix + "SkinStructure", p.skin); fn(prefix + "AutoMask", p.autoMask);
    }

}

inline Json Capture(Config* c)
{
    Json result = Json::object();
    Visit(c, [&](const std::string& name, auto& option) {
        const auto value = option.value_for_config();
        result[name] = value ? Json(*value) : Json(nullptr);
    });
    return result;
}

inline void Validate(Config* c, const Json& data)
{
    if (!data.is_object()) throw std::runtime_error("Settings slot is not an object");
    Visit(c, [&](const std::string& name, auto& option) {
        using T = typename std::remove_reference_t<decltype(option)>::value_type;
        const auto& value = data.at(name);
        if (value.is_null()) return;
        if constexpr (std::is_same_v<T, bool>) {
            if (!value.is_boolean()) throw std::runtime_error("Invalid boolean: " + name);
        } else if constexpr (std::is_same_v<T, std::string>) {
            if (!value.is_string() || value.get<std::string>().size() > 8192)
                throw std::runtime_error("Invalid text: " + name);
        } else {
            if (!value.is_number()) throw std::runtime_error("Invalid number: " + name);
            const auto number = value.get<double>();
            if (!std::isfinite(number) || std::abs(number) > 1000000)
                throw std::runtime_error("Out-of-range number: " + name);
            if constexpr (std::is_integral_v<T> || std::is_enum_v<T>) {
                if (number < 0 || std::floor(number) != number)
                    throw std::runtime_error("Invalid integer: " + name);
            }
            if constexpr (std::is_enum_v<T>) {
                if (number >= static_cast<double>(T::Count))
                    throw std::runtime_error("Invalid enum: " + name);
            }
        }
    });
    const auto range = [&](const char* key, double lo, double hi) {
        if (!data.at(key).is_null()) {
            const auto v = data.at(key).get<double>();
            if (v < lo || v > hi) throw std::runtime_error(std::string("Invalid ") + key);
        }
    };
    range("Preset", 0, 3); range("Style", 0, 2); range("WorkingScale", .25, 2);
    range("Passes", 1, 30); range("Pass2Preset", 0, 3); range("Pass3Preset", 0, 3);
    range("Pass2Style", 0, 2); range("Pass3Style", 0, 2);
    if (!data.at("Precision").is_null() && data.at("Precision") != 0 && data.at("Precision") != 4)
        throw std::runtime_error("Invalid precision");
}

inline void Apply(Config* c, const Json& data)
{
    Validate(c, data); // Validate the entire slot before touching any live option.
    Visit(c, [&](const std::string& name, auto& option) {
        using T = typename std::remove_reference_t<decltype(option)>::value_type;
        const auto& value = data.at(name);
        option = value.is_null() ? std::optional<T>{} : std::optional<T>{value.get<T>()};
    });
}

inline bool Ensure(Config* c)
{
    if (initialized) return available;
    initialized = true;
    try {
        const auto initial = Capture(c);
        slots.fill(initial); // Four identical starting points; no invented visual presets.
        if (std::filesystem::exists(Path())) {
            if (std::filesystem::file_size(Path()) > 262144) throw std::runtime_error("Profile file too large");
            std::ifstream stream(Path());
            Json file; stream >> file;
            if (file.at("version") != 1 || !file.at("active").is_number_integer() ||
                !file.at("slots").is_array() || file.at("slots").size() != 4)
                throw std::runtime_error("Invalid profile file format");
            const int selected = file.at("active").get<int>();
            if (selected < 0 || selected >= 4) throw std::runtime_error("Invalid saved slot number");
            std::array<Json, 4> loaded;
            for (int i = 0; i < 4; ++i) { loaded[i] = file.at("slots").at(i); Validate(c, loaded[i]); }
            slots = std::move(loaded); active = selected;
        }
        available = true;
    } catch (const std::exception& ex) {
        error = std::string("Profiles preserved; could not load: ") + ex.what();
    }
    return available;
}

inline int Active() { return active; }
inline const std::string& Error() { return error; }
inline bool Select(Config* c, int slot)
{
    if (!Ensure(c)) return false;
    if (slot < 0 || slot >= 4) { error = "Invalid slot number"; return false; }
    const auto now = GetTickCount64();
    if (lastSelection && now - lastSelection < 1000) { error = "Wait one second before changing slots"; return false; }
    try {
        Apply(c, slots[slot]);
        active = slot; lastSelection = now; error.clear();
        return true;
    } catch (const std::exception& ex) { error = ex.what(); return false; }
}

inline bool Save(Config* c)
{
    if (!Ensure(c)) return false;
    try {
        auto updated = slots;
        updated[active] = Capture(c);
        Validate(c, updated[active]);
        const Json file = {{"version", 1}, {"active", active}, {"slots", updated}};
        const auto temporary = Path().wstring() + L".tmp";
        {
            std::ofstream stream(temporary, std::ios::binary | std::ios::trunc);
            stream.exceptions(std::ios::failbit | std::ios::badbit);
            stream << file.dump(2) << '\n';
            stream.flush(); stream.close();
        }
        if (!MoveFileExW(temporary.c_str(), Path().c_str(), MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH))
            throw std::runtime_error("Could not replace profile file; previous slots remain saved");
        slots = std::move(updated); error.clear();
        return true;
    } catch (const std::exception& ex) { error = ex.what(); return false; }
}

#ifndef PERSONAL_PROFILES_TEST
inline void RenderSelector(Config* c)
{
    if (!Ensure(c)) { ImGui::TextWrapped("%s", error.c_str()); return; }
    static const char* names[] = {"Slot 0", "Slot 1", "Slot 2", "Slot 3"};
    int selected = active;
    if (ImGui::Combo("My NR settings (F11)", &selected, names, 4)) Select(c, selected);
    const bool modified = Capture(c) != slots[active];
    ImGui::TextDisabled("Slot %d%s", active, modified ? " - unsaved changes" : "");
    ImGui::TextWrapped("Save Settings stores this slot. Switching recalls its saved values.");
    if (!error.empty()) ImGui::TextWrapped("%s", error.c_str());
}
#endif
}
