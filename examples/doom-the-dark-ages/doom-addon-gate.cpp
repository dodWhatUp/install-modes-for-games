// ReShade add-on used by the successful DOOM: The Dark Ages Vulkan test.
// It prevents RenoDX and DLSS5-Feeder from loading into idTechLauncher.exe,
// while preserving the companions' exact upstream filenames for discovery.
// Compile as x64 with matching ReShade add-on headers and review before use.

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
        Log("Skipped RenoDX and DLSS5-Feeder: host is not DOOMTheDarkAges.exe.");
        return true;
    }

    Log("Loading Doom-only RenoDX and DLSS5-Feeder companions.");

    // RenoDX must load first so Feeder can detect its hook engine. Keep the
    // exact .addon64 names because Feeder performs adjacent-file discovery.
    g_renodx = LoadCompanion("renodx-dlss5.addon64");
    if (g_renodx == nullptr)
    {
        Log("Failed to load doom-addons\\renodx-dlss5.addon64.");
        return false;
    }

    g_feeder = LoadCompanion("dlss5-feed.addon64");
    if (g_feeder == nullptr)
    {
        Log("Failed to load doom-addons\\dlss5-feed.addon64.");
        FreeLibrary(g_renodx);
        g_renodx = nullptr;
        return false;
    }

    Log("Loaded both Doom-only companions successfully.");
    return true;
}

extern "C" __declspec(dllexport) void AddonUninit(HMODULE, HMODULE)
{
    if (g_feeder != nullptr)
    {
        FreeLibrary(g_feeder);
        g_feeder = nullptr;
    }
    if (g_renodx != nullptr)
    {
        FreeLibrary(g_renodx);
        g_renodx = nullptr;
    }
    Log("Unloaded Doom-only companions.");
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

        Log("Doom addon gate attached.");
    }
    else if (reason == DLL_PROCESS_DETACH)
    {
        reshade::unregister_addon(module);
        Log("Doom addon gate detached.");
    }
    return TRUE;
}
