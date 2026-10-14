"""Explicit, read-only FG configuration observations; never runtime verification.

No DLL load, settings read, network request or observation occurs on import.
NVAPI declarations/IDs are checked against NVIDIA's public SDK revision below.
DRS configuration, native saved settings and in-game delivery are separate facts.
Disabled overrides are NOT equivalent to FG Off. Raw frame-count fields are not
converted to multipliers: the public DRS enum alone does not define that mapping.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import ntpath
import os
from pathlib import Path
import re
from datetime import datetime, timezone
from types import MappingProxyType
import weakref

VERSION = "0.1.0"
SCHEMA_VERSION = 1
NVAPI_REVISION = "70d337db9186e968eab622f7e786de7e437faf3d"
NVAPI_SOURCE = f"https://github.com/NVIDIA/nvapi/blob/{NVAPI_REVISION}/"
STREAMLINE_SOURCE = "https://github.com/NVIDIA-RTX/Streamline/blob/main/include/sl_dlss_g.h"
SUPPORTED_GAMES = MappingProxyType({
    "cyberpunk-2077": "Cyberpunk2077.exe",
    "skyrim-special-edition": "SkyrimSE.exe",
})
MAX_SETTINGS_BYTES = 2 * 1024 * 1024

# Public NvApiDriverSettings.h, not private NVIDIA App reverse-engineering.
SETTING_IDS = MappingProxyType({
    "mode": 0x10308298,  # NGX_DLSSG_MODE_ID
    "frame_count": 0x104D6667,  # NGX_DLSSG_MULTI_FRAME_COUNT_ID
    "dynamic_max_count": 0x10562D0F,  # NGX_DLSSG_DYNAMIC_MULTI_FRAME_COUNT_MAX_ID
    "dynamic_target": 0x10CF4125,  # NGX_DLSSG_DYNAMIC_TARGET_FRAME_RATE_ID
})
MODE_NAMES = MappingProxyType({
    0: "override-disabled", 1: "off", 2: "on", 3: "auto", 4: "dynamic",
})
LOCATIONS = MappingProxyType({
    0: "current_profile", 1: "global_profile", 2: "base_profile",
    3: "default_profile",
})
# Only documented read/session-lifecycle entry points are bound.
INTERFACE_IDS = MappingProxyType({
    "Initialize": 0x0150E828, "Unload": 0xD22BDD7E,
    "DriverVersion": 0x2926AAAD, "CreateSession": 0x0694D52E,
    "DestroySession": 0xDAD9CFF8, "LoadSettings": 0x375DBD6B,
    "GlobalProfile": 0x617BFF9F, "FindApplication": 0xEEE566B2,
    "GetSetting": 0x73BF8338,
})


def _utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


class _IssuedObservation(dict):
    __slots__ = ("_seal", "__weakref__")


_issued = weakref.WeakValueDictionary()


def _issue(value):
    result = _IssuedObservation(value)
    result._seal = hashlib.sha256(_canonical(result)).digest()
    _issued[id(result)] = result
    return result


def is_inspector_observation(value):
    """In-process provenance/tamper check, not a security boundary against code.

    Constructors, copied/imported JSON and mutated observations are not issued.
    Consumers must share the canonical GameFgInspector module object. Even an
    issued observation is configuration evidence, not permission or a PASS.
    """
    try:
        return (type(value) is _IssuedObservation
                and _issued.get(id(value)) is value
                and value._seal == hashlib.sha256(_canonical(value)).digest())
    except (AttributeError, TypeError, ValueError, RecursionError):
        return False


def _unknown_setting(reason):
    return {"status": "unknown", "raw_value": None, "enum_name": None,
            "location": "unknown", "predefined": None, "reasons": [reason]}


def _unknown_layer(reason):
    return {"status": "unknown", "configured_mode": "unknown",
            "fixed_multiplier": None, "frame_count_raw": None,
            "dynamic_target_raw": None, "dynamic_max_count_raw": None,
            "profile_match": "unknown", "source_id": "nvapi-system-drs",
            "settings": {name: _unknown_setting(reason) for name in SETTING_IDS},
            "reasons": [reason]}


def _target(game, executable):
    target = {"game_id": "unsupported", "executable": None,
              "executable_match": "unknown", "executable_path_sha256": None}
    if not isinstance(game, str) or game not in SUPPORTED_GAMES:
        return target, None, ["unsupported_game_adapter"]
    expected = SUPPORTED_GAMES[game]
    target.update(game_id=game, executable=expected)
    if executable is None:
        target["executable_match"] = "basename-only"
        return target, expected, ["rendering_executable_full_path_not_supplied"]
    try:
        supplied = os.fspath(executable)
    except TypeError:
        return target, None, ["invalid_executable_argument"]
    if not isinstance(supplied, str) or "\x00" in supplied or len(supplied) > 2047:
        return target, None, ["invalid_executable_argument"]
    if ntpath.basename(supplied).casefold() != expected.casefold():
        return target, None, ["executable_does_not_match_game"]
    if supplied.casefold() == expected.casefold():
        target["executable_match"] = "basename-only"
        return target, expected, ["rendering_executable_full_path_not_supplied"]
    path = Path(supplied)
    # No UNC/device paths, URLs, relative lookup, execution or binary loading.
    if (not path.is_absolute() or supplied.startswith(("\\\\", "//"))
            or (os.name == "nt" and not re.match(r"^[A-Za-z]:[\\/]", supplied))):
        return target, None, ["executable_requires_local_absolute_path"]
    try:
        if path.is_symlink() or not path.is_file():
            return target, None, ["rendering_executable_unavailable_or_linked"]
        resolved = str(path.resolve(strict=True))
    except (OSError, ValueError):
        return target, None, ["rendering_executable_unavailable_or_linked"]
    target["executable_match"] = "exact-path"
    target["executable_path_sha256"] = hashlib.sha256(
        resolved.casefold().encode("utf-8")).hexdigest()
    return target, resolved, []


def _duplicate_checked(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite(value):
    raise ValueError("nonfinite JSON number")


def _finite_float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite JSON number")
    return result


def _stat_identity(stat):
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def _read_native(game, supplied_path):
    result = {"status": "unknown", "configured_mode": "unknown",
              "multiplier": None, "source_id": "native-settings-json",
              "source_sha256": None, "source_modified_at_utc": None,
              "source_scope": "unknown", "reasons": []}
    if game != "cyberpunk-2077":
        result["reasons"] = ["native_fg_adapter_unavailable_mod_owners_not_inspected"]
        return result
    if supplied_path is None:
        local = os.environ.get("LOCALAPPDATA") if os.name == "nt" else None
        if not local:
            result["reasons"] = ["native_settings_path_unavailable"]
            return result
        supplied_path = Path(local) / "CD Projekt Red" / "Cyberpunk 2077" / "UserSettings.json"
        result["source_scope"] = "current-known-path"
    else:
        result["source_scope"] = "caller-selected-file"
    try:
        path = Path(supplied_path)
        if (not path.is_absolute() or str(path).startswith(("\\\\", "//"))
                or path.is_symlink() or path.suffix.lower() != ".json"):
            raise ValueError("unsupported settings path")
        before = path.stat()
        if not path.is_file() or before.st_size > MAX_SETTINGS_BYTES:
            raise ValueError("unsupported settings file")
        with path.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            content = handle.read(MAX_SETTINGS_BYTES + 1)
            closed = os.fstat(handle.fileno())
        after = path.stat()
        if (len(content) > MAX_SETTINGS_BYTES or _stat_identity(before) != _stat_identity(opened)
                or _stat_identity(opened) != _stat_identity(closed)
                or _stat_identity(closed) != _stat_identity(after)):
            result["reasons"] = ["native_settings_changed_during_read"]
            return result
        tree = json.loads(content.decode("utf-8-sig"), object_pairs_hook=_duplicate_checked,
                          parse_constant=_reject_nonfinite, parse_float=_finite_float)
        fields = {}

        def visit(node):
            if isinstance(node, dict):
                name = node.get("name")
                if name in ("FrameGeneration", "DLSS_MultiFrameGeneration"):
                    if name in fields or "value" not in node:
                        raise ValueError("ambiguous native FG field")
                    fields[name] = node["value"]
                for value in node.values():
                    visit(value)
            elif isinstance(node, list):
                for value in node:
                    visit(value)

        visit(tree)
        owner = fields.get("FrameGeneration")
        mode = fields.get("DLSS_MultiFrameGeneration")
        if owner == "DLSS" and mode in ("x2", "x3", "x4"):
            result.update(status="observed", configured_mode="fixed", multiplier=int(mode[1:]))
        elif owner == "Off":
            result.update(status="observed", configured_mode="off")
        else:
            result["reasons"].append("native_fg_fields_missing_unsupported_or_ambiguous")
        result["source_sha256"] = hashlib.sha256(content).hexdigest()
        result["source_modified_at_utc"] = datetime.fromtimestamp(
            after.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z")
        result["reasons"].append("saved_native_selection_not_runtime_or_override_evidence")
    except (OSError, ValueError, TypeError, RecursionError):
        result["reasons"] = ["native_settings_read_unavailable_or_invalid"]
    return result


# Sized Windows SDK ABI, portable for mocked tests; wchar_t differs off Windows.
_U32 = ctypes.c_uint32
_U16 = ctypes.c_uint16
_Handle = ctypes.c_void_p
_Unicode = _U16 * 2048


class _Binary(ctypes.Structure):
    _pack_ = 4
    _fields_ = [("length", _U32), ("data", ctypes.c_ubyte * 4096)]


class _Value(ctypes.Union):
    _pack_ = 4
    _fields_ = [("dword", _U32), ("binary", _Binary), ("unicode", _Unicode),
                ("qword", ctypes.c_uint64)]


class _Setting(ctypes.Structure):
    _pack_ = 4
    _fields_ = [("version", _U32), ("name", _Unicode), ("setting_id", _U32),
                ("setting_type", _U32), ("location", _U32),
                ("is_predefined", _U32), ("predefined_valid", _U32),
                ("predefined", _Value), ("current", _Value)]


class _Application(ctypes.Structure):
    _fields_ = [("version", _U32), ("is_predefined", _U32),
                ("app_name", _Unicode), ("friendly_name", _Unicode),
                ("launcher", _Unicode), ("file_in_folder", _Unicode),
                ("flags", _U32), ("command_line", _Unicode)]


def _utf16(value):
    data = value.encode("utf-16-le")
    if len(data) > 4094:
        raise ValueError("NVAPI name too long")
    return _Unicode.from_buffer_copy(data + bytes(4096 - len(data)))


def _from_utf16(value):
    return bytes(value).decode("utf-16-le").split("\x00", 1)[0]


class _NvapiError(Exception):
    def __init__(self, operation, code):
        self.operation = operation
        self.code = code


def _load_system_nvapi():
    if os.name != "nt" or ctypes.sizeof(_Handle) != 8:
        raise _NvapiError("platform", None)
    kernel = ctypes.WinDLL("kernel32.dll", winmode=0x00000800)
    get_directory = kernel.GetSystemDirectoryW
    get_directory.argtypes = [ctypes.c_wchar_p, _U32]
    get_directory.restype = _U32
    buffer = ctypes.create_unicode_buffer(32768)
    length = get_directory(buffer, len(buffer))
    if not 0 < length < len(buffer):
        raise _NvapiError("system_directory", None)
    library_path = Path(buffer.value) / "nvapi64.dll"
    if not library_path.is_absolute() or not library_path.is_file() or library_path.is_symlink():
        raise _NvapiError("system_library", None)
    # An exact observed system library, never supplied DLLs or game-local NVAPI.
    return ctypes.WinDLL(str(library_path), winmode=0x00000800)


class _NvapiReader:
    def __init__(self):
        self.library = _load_system_nvapi()
        self.query = self.library.nvapi_QueryInterface
        self.query.argtypes = [_U32]
        self.query.restype = _Handle
        ptr = ctypes.POINTER
        signatures = {
            "Initialize": (), "Unload": (),
            "DriverVersion": (ptr(_U32), ctypes.POINTER(ctypes.c_char)),
            "CreateSession": (ptr(_Handle),), "DestroySession": (_Handle,),
            "LoadSettings": (_Handle,), "GlobalProfile": (_Handle, ptr(_Handle)),
            "FindApplication": (_Handle, ptr(_U16), ptr(_Handle), ptr(_Application)),
            "GetSetting": (_Handle, _Handle, _U32, ptr(_Setting)),
        }
        self.functions = {}
        for name, signature in signatures.items():
            address = self.query(INTERFACE_IDS[name])
            if not address:
                raise _NvapiError("interface_unavailable", INTERFACE_IDS[name])
            self.functions[name] = ctypes.CFUNCTYPE(ctypes.c_int32, *signature)(address)

    def _call(self, name, *args):
        status = self.functions[name](*args)
        if status != 0:
            raise _NvapiError(name, status)

    def _setting(self, session, profile, key):
        setting = _Setting()
        setting.version = ctypes.sizeof(_Setting) | (1 << 16)
        setting.setting_id = SETTING_IDS[key]
        status = self.functions["GetSetting"](session, profile, setting.setting_id,
                                               ctypes.byref(setting))
        if status != 0:
            result = _unknown_setting("drs_setting_unavailable")
            result["nvapi_status"] = status
            return result
        if setting.setting_type != 0 or setting.location not in LOCATIONS:
            return _unknown_setting("drs_setting_type_or_location_unsupported")
        if setting.setting_id != SETTING_IDS[key]:
            return _unknown_setting("drs_setting_identity_mismatch")
        raw = int(setting.current.dword)
        result = {"status": "observed", "raw_value": raw,
                  "enum_name": MODE_NAMES.get(raw) if key == "mode" else None,
                  "location": LOCATIONS[setting.location],
                  "predefined": bool(setting.is_predefined), "reasons": []}
        valid = ((key == "mode" and raw in MODE_NAMES)
                 or (key == "frame_count" and raw <= 15)
                 or (key == "dynamic_max_count" and raw <= 0x00FFFFFF)
                 or (key == "dynamic_target" and raw <= 0x01000000))
        if not valid:
            result.update(status="unknown", reasons=["drs_value_not_in_documented_enum"])
        return result

    def _layer(self, session, profile, profile_match):
        result = _unknown_layer("drs_settings_unavailable")
        settings = {key: self._setting(session, profile, key) for key in SETTING_IDS}
        complete = all(item["status"] == "observed" for item in settings.values())
        result.update(status="observed" if complete else "unknown", settings=settings,
                      profile_match=profile_match, reasons=[] if complete else ["drs_setting_coverage_incomplete"])
        result["configured_mode"] = settings["mode"]["enum_name"] or "unknown"
        for field, key in (("frame_count_raw", "frame_count"),
                           ("dynamic_max_count_raw", "dynamic_max_count"),
                           ("dynamic_target_raw", "dynamic_target")):
            result[field] = settings[key]["raw_value"]
        result["reasons"].append("drs_configuration_not_runtime_delivery")
        return result

    def observe(self, executable, match):
        driver = {"status": "unknown", "version": None,
                  "global": _unknown_layer("global_profile_unavailable"),
                  "per_application": _unknown_layer("application_profile_unavailable"),
                  "effective_configuration": _unknown_layer("effective_configuration_unavailable"),
                  "reasons": [], "library_identity": "Windows system nvapi64.dll"}
        session = _Handle()
        initialized = False
        try:
            self._call("Initialize")
            initialized = True
            version, branch = _U32(), ctypes.create_string_buffer(64)
            try:
                self._call("DriverVersion", ctypes.byref(version), branch)
                driver["version"] = f"{version.value // 100}.{version.value % 100:02d}"
            except _NvapiError:
                driver["reasons"].append("driver_version_unavailable")
            self._call("CreateSession", ctypes.byref(session))
            if not session.value:
                raise _NvapiError("session_handle", None)
            self._call("LoadSettings", session)
            profile = _Handle()
            try:
                self._call("GlobalProfile", session, ctypes.byref(profile))
                if not profile.value:
                    raise _NvapiError("global_handle", None)
                driver["global"] = self._layer(session, profile, "global-profile")
            except _NvapiError:
                driver["reasons"].append("global_profile_read_unavailable")
            application, profile = _Application(), _Handle()
            application.version = ctypes.sizeof(_Application) | (4 << 16)
            try:
                self._call("FindApplication", session, _utf16(executable),
                           ctypes.byref(profile), ctypes.byref(application))
                app_name = ntpath.basename(_from_utf16(application.app_name))
                if (not profile.value or app_name.casefold() != ntpath.basename(executable).casefold()):
                    raise _NvapiError("application_identity", None)
                layer = self._layer(session, profile, match)
                driver["per_application"] = layer
                # GetSetting's settingLocation identifies current/global/base/default inheritance.
                driver["effective_configuration"] = json.loads(json.dumps(layer))
                if match != "exact-path":
                    driver["reasons"].append("basename_lookup_not_exact_rendering_path")
            except _NvapiError as error:
                driver["reasons"].append("application_profile_lookup_unavailable_or_ambiguous")
                driver["application_lookup_status"] = error.code
            layers = (driver["global"], driver["per_application"])
            driver["status"] = ("observed" if all(x["status"] == "observed" for x in layers)
                                else "partial" if any(x["status"] == "observed" for x in layers)
                                else "unknown")
        except _NvapiError as error:
            driver["reasons"].append("nvapi_read_session_unavailable")
            driver["nvapi_status"] = error.code
        finally:
            if session.value:
                if self.functions["DestroySession"](session) != 0:
                    driver["status"] = "unknown"
                    driver["reasons"].append("nvapi_session_cleanup_failed")
            if initialized:
                if self.functions["Unload"]() != 0:
                    driver["status"] = "unknown"
                    driver["reasons"].append("nvapi_unload_failed")
        return driver


def inspect_fg(game, executable=None, native_settings_path=None):
    """Read one supported game's saved settings/current DRS, without mutation.

    Optional paths are only bounded inputs, never persisted/exported. This API
    never enters a game's process or calls Streamline; it cannot establish live
    FG delivery, all mod owners or fixed/adaptive effective runtime behavior.
    """
    observed_at = _utc_now()
    target, lookup, reasons = _target(game, executable)
    native = _read_native(target["game_id"], native_settings_path)
    driver = {"status": "unknown", "version": None,
              "global": _unknown_layer("nvapi_read_unavailable"),
              "per_application": _unknown_layer("nvapi_read_unavailable"),
              "effective_configuration": _unknown_layer("nvapi_read_unavailable"),
              "reasons": ["nvapi_read_unavailable"]}
    if lookup:
        try:
            driver = _NvapiReader().observe(lookup, target["executable_match"])
        except (_NvapiError, OSError, AttributeError, ValueError, TypeError):
            # Never include native exceptions: they may contain private paths.
            pass
    reasons.extend(["runtime_fg_mode_not_observed", "fg_mod_owner_coverage_unavailable",
                    "configured_state_cannot_pass_effective_fg_preflight"])
    sources = [
        {"id": "nvapi-public-header", "kind": "primary-documentation",
         "version": NVAPI_REVISION, "observed_at_utc": None,
         "url": NVAPI_SOURCE + "NvApiDriverSettings.h"},
        {"id": "streamline-public-header", "kind": "primary-documentation",
         "version": "reference-only-not-runtime", "observed_at_utc": None,
         "url": STREAMLINE_SOURCE},
        {"id": "native-settings-json", "kind": "configured-observation",
         "version": "cyberpunk-usersettings-v1", "observed_at_utc": observed_at,
         "status": native["status"]},
        {"id": "nvapi-system-drs", "kind": "configured-observation",
         "version": driver["version"], "observed_at_utc": observed_at,
         "status": driver["status"]},
    ]
    return _issue({
        "schema_version": SCHEMA_VERSION,
        "provider": {"name": "GameFgInspector", "version": VERSION, "read_only": True},
        "observed_at_utc": observed_at, "target": target, "native": native,
        "driver": driver,
        "effective": {"mode": "unknown", "fixed_multiplier": None,
                      "dynamic_mfg": "unknown", "verification": "configured-only"},
        "runtime": {"status": "not_observed", "mode": None, "coverage": None},
        "sources": sources, "reasons": reasons,
        "next_steps": ["Use supported current native/global/per-game readback to resolve configured unknowns.",
                       "Effective FG and owner verification need a separately authorized runtime adapter.",
                       "Keep ordinary rendering-cost comparisons blocked; do not change settings automatically."],
    })


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, choices=tuple(SUPPORTED_GAMES))
    parser.add_argument("--executable")
    parser.add_argument("--native-settings-path")
    args = parser.parse_args(argv)
    result = inspect_fg(args.game, args.executable, args.native_settings_path)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0  # Successful observation can be unknown; this is NOT a gate PASS.


if __name__ == "__main__":
    raise SystemExit(main())
