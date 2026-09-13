// Use NVIDIA's public DRS API to move only Cyberpunk's DLSS controls to OptiScaler.
#include <Windows.h>
#include <nvapi.h>
#include <NvApiDriverSettings.h>
#include <json.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
using Json=nlohmann::json;
void check(NvAPI_Status status,const char* call) { if(status!=NVAPI_OK) throw std::runtime_error(std::string(call)+": "+std::to_string(status)); }
int main(int argc,char** argv) {
    NvDRSSessionHandle session=nullptr;
    try {
        if(argc<2) throw std::runtime_error("Use inspect, apply snapshot.json, or restore snapshot.json");
        check(NvAPI_Initialize(),"Initialize");
        check(NvAPI_DRS_CreateSession(&session),"CreateSession");
        check(NvAPI_DRS_LoadSettings(session),"LoadSettings");
        NvDRSProfileHandle profile=nullptr;
        NVDRS_APPLICATION application{}; application.version=NVDRS_APPLICATION_VER;
        NvAPI_UnicodeString exe{}; wcscpy_s((wchar_t*)exe,NVAPI_UNICODE_STRING_MAX,L"Cyberpunk2077.exe");
        check(NvAPI_DRS_FindApplicationByName(session,exe,&profile,&application),"Find Cyberpunk profile");
        const std::pair<NvU32,NvU32> settings[]={
            {NGX_DLSSG_MODE_ID,NGX_DLSSG_MODE_DISABLED},
            {NGX_DLSSG_MULTI_FRAME_COUNT_ID,0},
            {NGX_DLSSG_DYNAMIC_MULTI_FRAME_COUNT_MAX_ID,0},
            {NGX_DLSSG_DYNAMIC_TARGET_FRAME_RATE_ID,0},
            {NGX_DLSS_SR_OVERRIDE_ID,0},
            {NGX_DLSS_RR_OVERRIDE_ID,0},
            {NGX_DLSS_FG_OVERRIDE_ID,1},
            {NGX_DLSS_FG_OVERRIDE_RENDER_PRESET_SELECTION_ID,NGX_DLSS_FG_OVERRIDE_RENDER_PRESET_SELECTION_RENDER_PRESET_B}
        };
        Json saved=Json::array();
        for(auto [id,target]:settings) {
            NVDRS_SETTING s{}; s.version=NVDRS_SETTING_VER; s.settingId=id;
            auto result=NvAPI_DRS_GetSetting(session,profile,id,&s);
            if(result!=NVAPI_SETTING_NOT_FOUND) check(result,"GetSetting");
            if(result==NVAPI_OK && s.settingType!=NVDRS_DWORD_TYPE) throw std::runtime_error("Unexpected setting type");
            const bool custom=result==NVAPI_OK && s.settingLocation==NVDRS_CURRENT_PROFILE_LOCATION && !s.isCurrentPredefined;
            saved.push_back({{"id",id},{"custom",custom},{"current",result==NVAPI_OK?s.u32CurrentValue:0},{"target",target}});
        }
        std::string mode=argv[1];
        if(mode=="inspect") std::cout<<saved.dump(2)<<"\n";
        else if(mode=="apply") {
            if(argc!=3 || std::filesystem::exists(argv[2])) throw std::runtime_error("A new snapshot filename is required");
            { std::ofstream f(argv[2]); f.exceptions(std::ios::badbit|std::ios::failbit); f<<saved.dump(2); f.close(); }
            for(auto [id,target]:settings) {
                NVDRS_SETTING s{}; s.version=NVDRS_SETTING_VER; s.settingId=id; s.settingType=NVDRS_DWORD_TYPE; s.u32CurrentValue=target;
                check(NvAPI_DRS_SetSetting(session,profile,&s),"SetSetting");
            }
            check(NvAPI_DRS_SaveSettings(session),"SaveSettings");
            std::cout<<"Applied Cyberpunk DLSS settings only\n";
        } else if(mode=="restore") {
            if(argc!=3) throw std::runtime_error("Snapshot filename required");
            std::ifstream f(argv[2]); Json before; f>>before;
            if(!before.is_array() || before.size()!=saved.size()) throw std::runtime_error("Invalid snapshot");
            for(size_t i=0;i<saved.size();++i) if(before[i].at("id")!=saved[i].at("id") || !before[i].at("custom").is_boolean() || !before[i].at("current").is_number_unsigned()) throw std::runtime_error("Invalid snapshot fields");
            for(const auto& item:before) {
                NvU32 id=item.at("id");
                if(item.at("custom")) {
                    NVDRS_SETTING s{}; s.version=NVDRS_SETTING_VER; s.settingId=id; s.settingType=NVDRS_DWORD_TYPE; s.u32CurrentValue=item.at("current");
                    check(NvAPI_DRS_SetSetting(session,profile,&s),"RestoreSetting");
                } else {auto r=NvAPI_DRS_DeleteProfileSetting(session,profile,id); if(r!=NVAPI_SETTING_NOT_FOUND) check(r,"Restore inheritance");}
            }
            check(NvAPI_DRS_SaveSettings(session),"Save restored settings");
            std::cout<<"Restored Cyberpunk DLSS settings only\n";
        } else throw std::runtime_error("Unknown mode");
        NvAPI_DRS_DestroySession(session); NvAPI_Unload(); return 0;
    } catch(const std::exception& e) { if(session) NvAPI_DRS_DestroySession(session); std::cerr<<e.what()<<"\n"; return 1; }
}
