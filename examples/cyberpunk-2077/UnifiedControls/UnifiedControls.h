#pragma once
#include <Config.h>
#include <State.h>
#include <hooks/Streamline_Hooks.h>
#include <imgui/imgui.h>
#include <Windows.h>
#include <array>
#include <algorithm>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace DlssNr::UnifiedControls
{
inline std::filesystem::path Adapter()
{
    wchar_t exe[32768]{};
    auto len=GetModuleFileNameW(nullptr,exe,32768);
    if(!len || len>=32768) return {};
    std::filesystem::path path(exe);
    if(_wcsicmp(path.filename().c_str(),L"Cyberpunk2077.exe")!=0) return {};
    return path.parent_path()/L"plugins/cyber_engine_tweaks/mods/GraphicsHotkeys";
}
inline void Render(Config* config,float menuScale)
{
    static const auto adapter=Adapter();
    static ULONGLONG polled=0,requested=0;
    static std::vector<std::string> status;
    const auto now=GetTickCount64();
    if(!polled || now-polled>=250)
    {
        polled=now; status.clear();
        std::ifstream input(adapter/L"graphics-status.txt");
        std::string line;
        if(std::getline(input,line) && line.size()<1024)
        {
            std::istringstream stream(line);
            std::string part;
            while(std::getline(stream,part,'|')) status.push_back(part);
        }
    }
    bool fresh=false;
    if(status.size()==18 && status[0]=="3")
    {
        try { auto age=std::time(nullptr)-std::stoll(status[2]); fresh=age>=0 && age<=3; } catch(...) {}
    }
    const bool ready=fresh && status[3]=="1" && status[4]=="DLSS";
    const bool busy=!ready || status[14]=="1" || (requested && now-requested<2000);
    auto request=[&](const char* action,const std::string& argument) {
        std::ofstream file(adapter/L"graphics-request.txt",std::ios::trunc);
        if(file) { file<<"3|"<<status[1]<<'|'<<now<<'|'<<std::time(nullptr)<<'|'<<action<<'|'<<argument; requested=now; }
    };
    ImGui::PushItemWidth(200.0f*menuScale);
    ImGui::TextUnformatted("DLSS Super Resolution");
    if(!ready) ImGui::TextDisabled("Load Cyberpunk with DLSS selected; waiting for CET.");
    bool dynamicSr=false,drsAvailable=false;
    if(ready)
    {
        try {
            const int nativeMin=std::stoi(status[7]),nativeMax=std::stoi(status[8]);
            const int nativeTarget=std::stoi(status[17]);
            drsAvailable=nativeMin>=50 && nativeMax<=100 && nativeMin<=nativeMax && nativeTarget>=10 && nativeTarget<=240;
            dynamicSr=drsAvailable && status[6]=="1" && nativeMin<nativeMax;
        } catch(...) {}
    }
    if(ImGui::CollapsingHeader("Dynamic DLSS (target FPS)",ImGuiTreeNodeFlags_DefaultOpen))
    {
        static int srTarget=30,srMinimum=50,srMaximum=100;
        static std::string drsSession;
        if(ready && drsAvailable && drsSession!=status[1])
        {
            drsSession=status[1];
            srTarget=dynamicSr?std::stoi(status[17]):30;
            srMinimum=dynamicSr?std::stoi(status[7]):50;
            srMaximum=dynamicSr?std::stoi(status[8]):100;
        }
        ImGui::BeginDisabled(busy || !drsAvailable);
        ImGui::SliderInt("Target rendered FPS",&srTarget,10,240);
        if(ImGui::SliderInt("Minimum render scale",&srMinimum,50,99,"%d%%")) srMaximum=std::max(srMaximum,srMinimum+1);
        if(ImGui::SliderInt("Maximum render scale",&srMaximum,51,100,"%d%%")) srMinimum=std::min(srMinimum,srMaximum-1);
        if(ImGui::Button("Enable / Apply Dynamic DLSS"))
            request("dynamic",std::to_string(srTarget)+","+std::to_string(srMinimum)+","+std::to_string(srMaximum));
        ImGui::SameLine();
        ImGui::BeginDisabled(!dynamicSr);
        if(ImGui::Button("Disable Dynamic DLSS")) request("dynamic","off");
        ImGui::EndDisabled();
        ImGui::EndDisabled();
        if(dynamicSr) ImGui::Text("Engine request: %s FPS, %s%% - %s%%",status[17].c_str(),status[7].c_str(),status[8].c_str());
        else if(ready && drsAvailable) ImGui::TextDisabled("Dynamic target mode: off");
        else ImGui::TextDisabled("Dynamic target mode: waiting for native settings");
        if(ready && !drsAvailable) ImGui::TextDisabled("Native target/bounds are unavailable in this session.");
        ImGui::TextWrapped("Adjust the values, then Apply. Targets real rendered FPS before frame generation. Check that the live input size changes as scene load changes.");
    }
    ImGui::BeginDisabled(busy);
    static const char* modes[]={"DLAA","Quality","Balanced","Performance","UltraPerformance"};
    if(ImGui::BeginCombo("Quality (F6)",ready?status[5].c_str():"Waiting"))
    {
        for(auto mode:modes) if(ImGui::Selectable(mode,ready && status[5]==mode)) request("quality",mode);
        ImGui::EndCombo();
    }
    const auto feature=State::Instance().currentFeature;
    static int percent=67;
    static bool scaleEditing=false;
    if(!scaleEditing && !busy)
    {
        if(status[6]=="1") { try { percent=std::clamp(std::stoi(status[7]),50,100); } catch(...) {} }
        else if(feature && feature->DisplayWidth())
            percent=std::clamp((int)std::lround(100.0*feature->RenderWidth()/feature->DisplayWidth()),50,100);
    }
    ImGui::BeginDisabled(dynamicSr);
    ImGui::SliderInt("Fixed render scale",&percent,50,100,"%d%%");
    scaleEditing=ImGui::IsItemActive();
    if(!busy && !dynamicSr && ImGui::IsItemDeactivatedAfterEdit()) request("scale",std::to_string(percent));
    ImGui::EndDisabled();
    ImGui::EndDisabled();
    if(ready && status[6]=="1") ImGui::TextDisabled("Native resolution bounds: %s%% - %s%%",status[7].c_str(),status[8].c_str());
    if(feature) ImGui::Text("Live input: %u x %u  |  Output: %u x %u",feature->RenderWidth(),feature->RenderHeight(),feature->DisplayWidth(),feature->DisplayHeight());
    auto modelLabel=[](bool enabled,uint32_t value) {
        if(!enabled || !value) return std::string("Game / per-quality setting");
        if(value<=26) return std::string(1,(char)('A'+value-1));
        return std::to_string(value);
    };
    ImGui::TextDisabled("Requested SR model: %s",modelLabel(config->RenderPresetOverride.value_or_default(),config->RenderPresetForAll.value_or_default()).c_str());
    ImGui::TextDisabled("F6 / quality selection exits dynamic scaling and keeps your model preset.");
    ImGui::Separator();
    bool rr=ready && status[9]=="1";
    ImGui::BeginDisabled(busy);
    if(ImGui::Checkbox("Ray Reconstruction",&rr)) request("rr",rr?"1":"0");
    ImGui::EndDisabled();
    if(ready && status[10]!="1") ImGui::TextDisabled("RR requires ray tracing enabled in the game.");
    ImGui::TextDisabled("Requested RR model: %s",modelLabel(config->DLSSDRenderPresetOverride.value_or_default(),config->DLSSDRenderPresetForAll.value_or_default()).c_str());
    ImGui::Separator();
    bool fg=ready && status[11]=="1";
    ImGui::BeginDisabled(busy);
    if(ImGui::Checkbox("DLSS Frame Generation",&fg)) request("fg",fg?"1":"0");
    ImGui::EndDisabled();
    auto& state=State::Instance();
    if(state.activeFgInput!=FGInput::NoFG || state.activeFgOutput!=FGOutput::NoFG)
        ImGui::TextDisabled("Use native FG routing for these MFG controls.");
    else
    {
        bool dynamic=config->FGDLSSGOverrideForceDMFG.value_or_default();
        ImGui::BeginDisabled(busy || !state.dlssgGameDMFGSupported);
        if(ImGui::Checkbox("Dynamic MFG",&dynamic))
        { config->FGDLSSGOverrideForceDMFG=dynamic; StreamlineHooks::updateDlssgOptions(); requested=now; }
        ImGui::EndDisabled();
        if(!state.dlssgGameDMFGSupported) ImGui::TextDisabled("Dynamic MFG support has not been reported by this session.");
        const int maximum=state.dlssgMfgMax.has_value()?std::clamp((int)state.dlssgMfgMax.value(),0,5):0;
        ImGui::BeginDisabled(busy || dynamic || maximum<1);
        const int ratio=config->FGDLSSGOverrideInterpolationCount.has_value()?config->FGDLSSGOverrideInterpolationCount.value()+1:0;
        const std::string label=ratio?std::to_string(ratio)+"x":"Game setting";
        if(ImGui::BeginCombo("MFG multiplier",label.c_str()))
        {
            if(ImGui::Selectable("Game setting",!ratio)) { config->FGDLSSGOverrideInterpolationCount.reset(); StreamlineHooks::updateDlssgOptions(); requested=now; }
            for(int extra=1;extra<=maximum;++extra)
            {
                const auto name=std::to_string(extra+1)+"x";
                if(ImGui::Selectable(name.c_str(),ratio==extra+1)) { config->FGDLSSGOverrideInterpolationCount=extra; StreamlineHooks::updateDlssgOptions(); requested=now; }
            }
            ImGui::EndCombo();
        }
        ImGui::EndDisabled();
        static int target=144;
        static bool targetEditing=false;
        if(!targetEditing && !busy) target=std::clamp((int)config->FGDLSSGFramerateTargetDMFG.value_or_default(),30,240);
        ImGui::BeginDisabled(busy || !dynamic || !state.dlssgGameDMFGSupported);
        ImGui::SliderInt("Dynamic target FPS",&target,30,240);
        targetEditing=ImGui::IsItemActive();
        if(!busy && ImGui::IsItemDeactivatedAfterEdit()) { config->FGDLSSGFramerateTargetDMFG=(float)target; StreamlineHooks::updateDlssgOptions(); requested=now; }
        ImGui::EndDisabled();
        if(state.dlssgDetectedInterpolationCount>0) ImGui::Text("Reported FG multiplier: %dx",state.dlssgDetectedInterpolationCount+1);
    }
    if(fresh && !status[16].empty()) { ImGui::Separator(); ImGui::TextWrapped("%s",status[16].c_str()); }
    ImGui::Separator();
    ImGui::TextDisabled("F7: NR 25%% / 100%%  |  F10: NR on/off  |  F11: saved slot");
    ImGui::PopItemWidth();
    // Reuse upstream NR sections: model, scale, skin, tone, placement and inspection.
    DlssNr::RenderMenu(config,menuScale);
}
}
