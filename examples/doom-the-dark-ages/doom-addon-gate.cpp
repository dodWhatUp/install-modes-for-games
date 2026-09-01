// Experimental ReShade add-on used to prevent DOOM-only companions from
// loading into idTechLauncher.exe. It proved process isolation, but the
// renamed companion layout was not accepted by DLSS5-Feeder's own discovery.
// Review games/DOOM-THE-DARK-AGES.md before adapting this source.

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <reshade.hpp>

static HMODULE g_self = nullptr;
static HMODULE g_renodx = nullptr;
static HMODULE g_feeder = nullptr;
static char g_log_path[MAX_PATH] = {};

static const char *ExecutableName()
{
    static char path[MAX_PATH] = {};
    if (path[0] == '\0')
        GetModuleFileNameA(nullptr, path, MAX_PATH);
    const char *slash = std::strrchr(path, '\\');
    return slash != nullptr ? slash + 1 : path;
}

static void Log(const char *message)
{
    FILE *file = nullptr;
    if (fopen_s(&file, g_log_path, "a") == 0 && file != nullptr)
    {
        SYSTEMTIME time = {};
        GetLocalTime(&time);
        std::fprintf(file, "%02u:%02u:%02u.%03u  %s\n",
                     time.wHour, time.wMinute, time.wSecond,
                     time.wMilliseconds, message);
        std::fclose(file);
    }
}

static HMODULE LoadCompanion(const char *name)
{
    char path[MAX_PATH] = {};
    GetModuleFileNameA(g_self, path, MAX_PATH);
    char *slash = std::strrchr(path, '\\');
    if (slash == nullptr)
        return nullptr;
    strcpy_s(slash + 1,
             MAX_PATH - static_cast<size_t>(slash + 1 - path),
             "doom-addons\\");
    strcat_s(path, name);
    return LoadLibraryExA(path, nullptr,
                          LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR |
                          LOAD_LIBRARY_SEARCH_DEFAULT_DIRS);
}

extern "C" __declspec(dllexport) bool AddonInit(HMODULE, HMODULE)
{
    if (_stricmp(ExecutableName(), "DOOMTheDarkAges.exe") != 0)
    {
        Log("Skipped companions: host is not DOOMTheDarkAges.exe.");
        return true;
    }

    Log("Loading DOOM-only companions.");
    g_renodx = LoadCompanion("renodx-dlss5.dll");
    if (g_renodx == nullptr)
    {
        Log("Failed to load RenoDX companion.");
        return false;
    }

    g_feeder = LoadCompanion("dlss5-feed.dll");
    if (g_feeder == nullptr)
    {
        Log("Failed to load Feeder companion.");
        FreeLibrary(g_renodx);
        g_renodx = nullptr;
        return false;
    }
    Log("Loaded both DOOM-only companions successfully.");
    return true;
}

extern "C" __declspec(dllexport) void AddonUninit(HMODULE, HMODULE)
{
    if (g_feeder != nullptr)
        FreeLibrary(g_feeder);
    if (g_renodx != nullptr)
        FreeLibrary(g_renodx);
    g_feeder = nullptr;
    g_renodx = nullptr;
    Log("Unloaded DOOM-only companions.");
}

BOOL APIENTRY DllMain(HMODULE module, DWORD reason, LPVOID)
{
    if (reason == DLL_PROCESS_ATTACH)
    {
        g_self = module;
        DisableThreadLibraryCalls(module);
        char module_path[MAX_PATH] = {};
        GetModuleFileNameA(module, module_path, MAX_PATH);
        char *slash = std::strrchr(module_path, '\\');
        if (slash != nullptr)
        {
            *slash = '\0';
            std::snprintf(g_log_path, MAX_PATH,
                          "%s\\doom-addon-gate-%s.log",
                          module_path, ExecutableName());
        }
        if (!reshade::register_addon(module))
            return FALSE;
        Log("DOOM add-on gate attached.");
    }
    else if (reason == DLL_PROCESS_DETACH)
    {
        reshade::unregister_addon(module);
        Log("DOOM add-on gate detached.");
    }
    return TRUE;
}
