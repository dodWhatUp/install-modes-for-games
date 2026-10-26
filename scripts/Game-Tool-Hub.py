"""Local tool coordinator. Reads existing tools; never starts a capture."""
from __future__ import annotations

import argparse
import configparser
import csv
import ctypes
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

VERSION = "0.27.34-preview.1"
HEADER = struct.Struct("<5Ii2I")
ENTRY_MIN = 1324
MAX_MAP = 16 * 1024 * 1024
RTSS_HEADER = struct.Struct("<9I")


class RtssApp(ctypes.LittleEndianStructure):
    """Authored wire-layout adapter to the installed RTSS v2 SDK, Windows packing 8."""
    _pack_ = 8
    _fields_ = [("pid", ctypes.c_uint32), ("name", ctypes.c_char * 260)] + [
        (key, ctypes.c_uint32) for key in
        ("flags", "time0", "time1", "frames", "frame_time", "stat_flags", "stat_time0",
         "stat_time1", "stat_frames", "stat_count", "minimum", "average", "maximum",
         "osd_x", "osd_y", "osd_pixel", "osd_color", "osd_frame", "screenshot_flags")
    ] + [("screenshot_path", ctypes.c_char * 260), ("background", ctypes.c_uint32),
         ("video_flags", ctypes.c_uint32), ("video_path", ctypes.c_char * 260)] + [
        (key, ctypes.c_uint32) for key in
        ("video_fps", "video_size", "video_format", "video_quality", "video_threads",
         "screenshot_quality", "screenshot_threads", "audio_flags", "video_flags_ex",
         "audio_flags2", "frame_time_min", "frame_time_avg", "frame_time_max", "frame_time_count")
    ] + [("frame_time_buffer", ctypes.c_uint32 * 1024), ("buffer_pos", ctypes.c_uint32),
         ("buffer_fps", ctypes.c_uint32), ("audio_events", ctypes.c_uint64 * 4),
         ("prerecord_limits", ctypes.c_uint32 * 2), ("stat_total_time", ctypes.c_uint64),
         ("low_buffer", ctypes.c_uint32 * 1024), ("low_1", ctypes.c_uint32),
         ("low_01", ctypes.c_uint32), ("low_positions", ctypes.c_uint32 * 2),
         ("performance_metadata", ctypes.c_uint32 * 5), ("latency_marker", ctypes.c_uint64),
         ("resolution", ctypes.c_uint32 * 2), ("instrumentation", ctypes.c_uint64 * 13)]


def decode_rtss_header(raw):
    if len(raw) < RTSS_HEADER.size:
        raise ValueError("Truncated RTSS header")
    signature, version, stride, offset, count, _, _, _, _ = RTSS_HEADER.unpack_from(raw)
    if signature != 0x52545353 or version >> 16 != 2:
        raise ValueError("RTSS shared memory is uninitialized or unsupported")
    if not (316 <= stride <= 65536 and 36 <= offset <= MAX_MAP and count <= 4096):
        raise ValueError("Invalid RTSS application layout")
    extent = offset + count * stride
    if extent > 64 * 1024 * 1024:
        raise ValueError("RTSS data exceeds the bounded reader")
    return {"version": version, "stride": stride, "offset": offset, "count": count, "extent": extent}


def decode_rtss(raw, tick_ms=None):
    header = decode_rtss_header(raw)
    if len(raw) < header["extent"]:
        raise ValueError("Truncated RTSS application array")
    apps = []
    minor = header["version"] & 65535
    for index in range(header["count"]):
        start = header["offset"] + index * header["stride"]
        def field(name, minimum_version=0, size=4):
            offset = getattr(RtssApp, name).offset
            if minor < minimum_version or offset + size > header["stride"]:
                return None
            return struct.unpack_from("<Q" if size == 8 else "<I", raw, start + offset)[0]
        pid = field("pid")
        if not pid:
            continue
        name = raw[start + 4:start + 264].split(b"\0", 1)[0].decode("cp1252", "replace")
        updated = field("time1")
        age = ((tick_ms - updated) & 0xFFFFFFFF) if tick_ms is not None and updated else None
        fresh = age is not None and age <= 2000
        count = field("stat_count")
        values = {}
        for key, introduced in (("minimum", 0), ("average", 0), ("maximum", 0),
                                ("low_1", 13), ("low_01", 13), ("buffer_fps", 5)):
            value = field(key, introduced)
            # Provider stores tenths of FPS; only unit conversion, no new statistics.
            valid = fresh if key == "buffer_fps" else bool(count)
            values[key] = {"raw": value, "fps": value / 10 if valid and value not in (None, 0xFFFFFFFF) else None}
        endpoints = []
        offset = RtssApp.instrumentation.offset
        if minor >= 21 and offset + 13 * 8 <= header["stride"]:
            names = ("input_sample", "simulation_start", "simulation_end", "render_submit_start",
                     "render_submit_end", "present_start", "present_end", "driver_start", "driver_end",
                     "os_render_queue_start", "os_render_queue_end", "gpu_render_start", "gpu_render_end")
            endpoints = [key for key, value in zip(names, struct.unpack_from("<13Q", raw, start + offset)) if value]
        apps.append({"process_id": pid, "application": name, "flags": field("flags"),
                     "api_id": field("flags") & 65535, "update_age_ms": age,
                     "fresh": fresh, "statistics_count": count, "statistics_frames": field("stat_frames"),
                     "statistics_interval_ticks": [field("stat_time0"), field("stat_time1")],
                     "statistics_recording": bool(field("stat_flags") & 1),
                     "video_capture_requested_or_active": bool((field("video_flags", 2) or 0) & 7),
                     "values": values, "latency_endpoints_present": endpoints,
                     "latency_ms": None, "run_association": None,
                     "scope": "provider interval; freshness and game/run acceptance separate",
                     "low_definition": "RTSS provider-calculated lows; method/frame coverage not inferred"})
    return {"header": header, "applications": apps}


def read_rtss():
    if os.name != "nt":
        return {"state": "unavailable", "reason": "Windows shared memory required", "applications": []}
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenFileMappingW.restype = ctypes.c_void_p
    api.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
    api.MapViewOfFile.restype = ctypes.c_void_p
    api.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    api.GetTickCount.restype = ctypes.c_uint32
    handle = api.OpenFileMappingW(4, False, "RTSSSharedMemoryV2")
    if not handle:
        return {"state": "unavailable", "reason": f"Existing RTSS read-only mapping unavailable (Windows {ctypes.get_last_error()})", "applications": []}
    view = None
    try:
        view = api.MapViewOfFile(handle, 4, 0, 0, RTSS_HEADER.size)
        if not view:
            raise ValueError("Cannot map RTSS header")
        header = decode_rtss_header(ctypes.string_at(view, RTSS_HEADER.size))
        api.UnmapViewOfFile(view)
        view = None
        view = api.MapViewOfFile(handle, 4, 0, 0, header["extent"])
        if not view:
            raise ValueError("Cannot map validated RTSS extent")
        result = decode_rtss(ctypes.string_at(view, header["extent"]), api.GetTickCount())
        if result["header"] != header:
            raise ValueError("RTSS layout changed during read; refresh again")
        result.update(state="connected", run_association=None,
                      consistency="best-effort read; no locks or OSD/capture state written")
        return result
    except (ValueError, OSError) as error:
        return {"state": "unavailable", "reason": str(error), "applications": []}
    finally:
        if view:
            api.UnmapViewOfFile(view)
        api.CloseHandle(handle)


PRESENTMON_FIELDS = {
    "MsGPULatency": "CPU frame start to GPU work start",
    "MsGPUTime": "GPU frame duration, may overlap CPU frames",
    "MsGPUBusy": "GPU execution time for frame",
    "MsGPUWait": "GPU frame time not executing work",
    "DisplayLatency": "CPU frame start to display",
    "MsClickToPhotonLatency": "earliest contributing mouse click to display (software estimate)",
    "MsAllInputToPhotonLatency": "earliest contributing keyboard/mouse input to display (software estimate)",
    "InstrumentedLatency": "application-instrumented frame start to display",
    "MsPCLatency": "PC receiving input to frame sent to display (requires application instrumentation)",
}
PRESENTMON_DOC = "https://github.com/GameTechDev/PresentMon/blob/v2.6.0/README-ConsoleApplication.md"


def report_preview(path, provider):
    """Bounded inspection of existing output. Preserve cell strings; compute no metrics."""
    if Path(path).suffix.lower() != ".csv" or "presentmon" not in provider.lower():
        return {"schema": "opaque", "reason": "No documented provider adapter selected"}
    old_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(65536)
        with Path(path).open(encoding="utf-8-sig", newline="") as incoming:
            reader = csv.reader(incoming)
            columns = next(reader, [])
            if (len(columns) > 256 or len(set(columns)) != len(columns) or
                    not {"Application", "ProcessID", "SwapChainAddress"}.issubset(columns) or
                    not any(key in columns for key in ("CPUStartTime", "CPUStartQPC", "CPUStartQPCTime", "CPUStartDateTime"))):
                return {"schema": "opaque", "reason": "Unrecognized PresentMon CSV schema"}
            samples = []
            for _ in range(5):
                row = next(reader, None)
                if row is None:
                    break
                if len(row) != len(columns):
                    return {"schema": "opaque", "reason": "Malformed CSV row; original retained"}
                samples.append(dict(zip(columns, row)))
            fields = [{"name": key, "units": "ms", "endpoints": description,
                       "available_in_preview": any(s[key].strip().lower() not in ("", "na", "n/a", "nan") for s in samples)}
                      for key, description in PRESENTMON_FIELDS.items() if key in columns]
            return {"schema": "PresentMon v2-style CSV", "provider_version": "user-declared; not inferred",
                    "documentation": PRESENTMON_DOC, "columns": columns, "samples": samples,
                    "sample_limit": 5, "latency_and_gpu_fields": fields,
                    "frame_type_column_present": "FrameType" in columns,
                    "scope": "existing report preview; not a new capture or aggregated benchmark",
                    "metrics_recalculated": False}
    except (OSError, UnicodeError, csv.Error) as error:
        return {"schema": "opaque", "reason": f"Preview unavailable: {error}"}
    finally:
        csv.field_size_limit(old_limit)


def launch_allowed(tool):
    name = Path(tool.get("path", "")).name.lower()
    return (bool(tool.get("open_allowed")) and tool.get("id") not in ("presentmon-console", "frameview-sdk")
            and not name.startswith("presentmon") and name not in ("rtsshooksloader64.exe", "rtsshooksloader.exe"))


def register_tool(registry, tools, path, label, interface_confirmed):
    path = Path(path).resolve(strict=True)
    if not interface_confirmed or not label.strip() or path.suffix.lower() != ".exe" or not path.is_file():
        raise ValueError("Choose an installed EXE, name it, and confirm it opens an interface without collection")
    candidate = {"id": uuid.uuid4().hex, "name": label.strip(), "path": str(path),
                 "process": path.name, "open_allowed": True}
    if not launch_allowed(candidate):
        raise ValueError("Known console collectors/helpers remain inventory-only")
    if any(Path(t.get("path", "")).as_posix().lower() == path.as_posix().lower() for t in tools):
        return False
    updated = tools + [candidate]
    registry.parent.mkdir(parents=True, exist_ok=True)
    if registry.exists():
        backup = registry.parent / ("tools-before-" + uuid.uuid4().hex + ".json")
        backup.write_bytes(registry.read_bytes())
    temporary = registry.parent / ("tools-" + uuid.uuid4().hex + ".tmp")
    temporary.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    os.replace(temporary, registry)
    tools[:] = updated
    return True


def shortcut_key(keycode, keysym, windows):
    # Windows virtual-key letters survive a Hebrew/other active keyboard layout.
    if windows and 48 <= keycode <= 90:
        return chr(keycode).lower()
    return keysym.lower()


def utc():
    return datetime.now(timezone.utc).isoformat()


def decode_header(raw):
    if len(raw) < HEADER.size:
        raise ValueError("Truncated Afterburner header")
    signature, version, size, count, stride, polled, gpu_count, gpu_stride = HEADER.unpack_from(raw)
    if signature != 0x4D41484D or version >> 16 != 2:
        raise ValueError("Afterburner shared memory is uninitialized or unsupported")
    if not (32 <= size <= 4096 and 0 <= count <= 10000 and ENTRY_MIN <= stride <= 8192):
        raise ValueError("Invalid Afterburner layout")
    extent = size + count * stride
    if extent > MAX_MAP:
        raise ValueError("Afterburner data exceeds the bounded reader")
    return {"signature": signature, "version": version, "header_size": size,
            "count": count, "stride": stride, "polled_unix": polled, "extent": extent}


def decode_mahm(raw):
    header = decode_header(raw)
    if len(raw) < header["extent"]:
        raise ValueError("Truncated Afterburner sensor array")
    rows = []
    for index in range(header["count"]):
        offset = header["header_size"] + index * header["stride"]
        label = raw[offset:offset + 260].split(b"\0", 1)[0].decode("cp1252", "replace")
        units = raw[offset + 260:offset + 520].split(b"\0", 1)[0].decode("cp1252", "replace")
        value, _, _, flags, gpu, source_id = struct.unpack_from("<3f3I", raw, offset + 1300)
        available = math.isfinite(value) and abs(value) < 3.4028234e38
        rows.append({"name": label, "units": units, "value": value if available else None,
                     "source_id": source_id, "gpu_index": None if gpu == 0xFFFFFFFF else gpu,
                     "in_osd": bool(flags & 1), "provider": "MSI Afterburner",
                     "scope": "unscoped live tool counter" if 0x50 <= source_id <= 0x56 else "tool sensor"})
    return {"header": header, "rows": rows}


def read_afterburner():
    if os.name != "nt":
        return {"state": "unavailable", "reason": "Windows shared memory required", "rows": []}
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenFileMappingW.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_wchar_p]
    api.OpenFileMappingW.restype = ctypes.c_void_p
    api.MapViewOfFile.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_size_t]
    api.MapViewOfFile.restype = ctypes.c_void_p
    api.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
    api.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = api.OpenFileMappingW(4, False, "MAHMSharedMemory")  # FILE_MAP_READ only
    if not handle:
        return {"state": "unavailable", "reason": f"Existing read-only mapping unavailable (Windows {ctypes.get_last_error()})", "rows": []}
    view = None
    try:
        view = api.MapViewOfFile(handle, 4, 0, 0, HEADER.size)
        if not view:
            raise ValueError("Cannot map Afterburner header")
        header = decode_header(ctypes.string_at(view, HEADER.size))
        api.UnmapViewOfFile(view)
        view = None
        view = api.MapViewOfFile(handle, 4, 0, 0, header["extent"])
        if not view:
            raise ValueError("Cannot map validated Afterburner extent")
        result = decode_mahm(ctypes.string_at(view, header["extent"]))
        if any(result["header"][key] != header[key] for key in ("version", "header_size", "count", "stride")):
            raise ValueError("Afterburner layout changed during read; refresh again")
        age = time.time() - result["header"]["polled_unix"]
        result.update(state="connected" if 0 <= age <= 5 else "stale", age_seconds=round(age, 2),
                      consistency="best-effort snapshot; provider does not promise an atomic sensor batch",
                      run_association=None)
        return result
    except (ValueError, OSError) as error:
        return {"state": "unavailable", "reason": str(error), "rows": []}
    finally:
        if view:
            api.UnmapViewOfFile(view)
        api.CloseHandle(handle)


def read_ini(path):
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    if Path(path).is_file():
        parser.read(path, encoding="utf-8-sig")
    return parser


def default_tools():
    root = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
    return [{"id": "afterburner", "name": "MSI Afterburner", "path": str(root / "MSI Afterburner/MSIAfterburner.exe"),
             "process": "MSIAfterburner.exe", "open_allowed": True},
            {"id": "rtss", "name": "RTSS", "path": str(root / "RivaTuner Statistics Server/RTSS.exe"),
             "process": "RTSS.exe", "open_allowed": True},
            {"id": "presentmon-console", "name": "PresentMon console", "path": os.environ.get("GAME_TOOL_PRESENTMON", ""),
             "process": "PresentMon-2.6.0-x64.exe", "open_allowed": False},
            {"id": "nvidia-app", "name": "NVIDIA App", "path": str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "NVIDIA Corporation/NVIDIA App/CEF/NVIDIA App.exe"),
             "process": "NVIDIA App.exe", "open_allowed": True},
            {"id": "frameview-sdk", "name": "FrameView SDK collector (no GUI)", "path": str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "NVIDIA Corporation/FrameViewSDK/bin/PresentMon_x64.exe"),
             "process": "PresentMon_x64.exe", "open_allowed": False}]


def load_tools(registry):
    tools = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else default_tools()
    for tool in default_tools():
        if tool["id"] not in {t["id"] for t in tools} and tool["path"] and Path(tool["path"]).is_file():
            if not any(Path(t.get("path", "")).as_posix().lower() == Path(tool["path"]).as_posix().lower() for t in tools):
                tools.append(tool)
    return tools


def process_names():
    if os.name != "nt":
        return set()
    result = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, timeout=8,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise OSError("Windows process inventory failed")
    return {row[0].lower() for row in csv.reader(io.StringIO(result.stdout.decode("mbcs", "replace"))) if row}


def version_of(path):
    if os.name != "nt" or not Path(path).is_file():
        return None
    api = ctypes.WinDLL("version")
    api.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
    api.GetFileVersionInfoW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    api.VerQueryValueW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint32)]
    size = api.GetFileVersionInfoSizeW(str(path), None)
    if not 0 < size < 1024 * 1024:
        return None
    data = ctypes.create_string_buffer(size)
    if not api.GetFileVersionInfoW(str(path), 0, size, data):
        return None
    pointer, length = ctypes.c_void_p(), ctypes.c_uint32()
    if not api.VerQueryValueW(data, "\\", ctypes.byref(pointer), ctypes.byref(length)) or length.value < 52:
        return None
    info = struct.unpack("<13I", ctypes.string_at(pointer, 52))
    if info[0] != 0xFEEF04BD:
        return None
    return ".".join(str(n) for n in (info[2] >> 16, info[2] & 65535, info[3] >> 16, info[3] & 65535))


def configuration(tools):
    tool = next((t for t in tools if t["id"] == "afterburner"), None)
    if not tool or not tool.get("path"):
        return {}
    folder = Path(tool["path"]).parent
    defaults = read_ini(folder / "MSIAfterburner.cfg")
    profile = read_ini(folder / "Profiles/MSIAfterburner.cfg")
    fields = ("EnableLog", "LogPath", "HwPollPeriod", "BeginRecordHotkey", "EndRecordHotkey",
              "BeginLoggingHotkey", "EndLoggingHotkey", "OSDToggleHotkey", "BenchmarkPath")
    return {key: profile.get("Settings", key, fallback=defaults.get("Settings", key, fallback=None)) for key in fields}


def inspect(tools):
    try:
        names = process_names()
        process_error = None
    except (OSError, subprocess.TimeoutExpired) as error:
        names, process_error = None, str(error)
    statuses = [{**tool, "installed": bool(tool.get("path")) and Path(tool["path"]).is_file(),
                 "running": None if names is None else tool["process"].lower() in names,
                 "version": version_of(tool.get("path", ""))} for tool in tools]
    return {"schema": 1, "helper_version": VERSION, "observed_utc": utc(), "mode": "learning",
            "capture_started_by_helper": False, "process_error": process_error, "tools": statuses,
            "afterburner_configuration": configuration(tools), "afterburner": read_afterburner(), "rtss": read_rtss()}


def exclusive_json(path, value):
    with Path(path).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def import_report(source, destination, provider, definition="Unknown; retain provider documentation"):
    source = Path(source).resolve(strict=True)
    if source.suffix.lower() not in {".csv", ".json", ".txt", ".hml"} or not source.is_file():
        raise ValueError("Choose an existing CSV, JSON, TXT or HML report")
    before = source.stat()
    if before.st_size > 256 * 1024 * 1024:
        raise ValueError("Report exceeds the 256 MiB import limit")
    folder = Path(destination) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12])
    folder.mkdir(parents=True, exist_ok=False)
    copied = folder / ("original" + source.suffix.lower())
    digest = hashlib.sha256()
    with source.open("rb") as incoming, copied.open("xb") as outgoing:
        total = 0
        while block := incoming.read(1024 * 1024):
            total += len(block)
            if total > 256 * 1024 * 1024:
                raise ValueError("Source grew past the import limit; partial copy retained")
            outgoing.write(block)
            digest.update(block)
    after = source.stat()
    unchanged = (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns)
    receipt = {"schema": 1, "imported_utc": utc(), "provider": provider, "definition": definition,
               "source_name": source.name, "source_path": str(source), "stored_file": copied.name,
               "bytes": total, "sha256": digest.hexdigest(), "source_unchanged_during_copy": unchanged,
               "metrics_recalculated": False, "run_association": None,
               "preview": report_preview(copied, provider)}
    exclusive_json(folder / "receipt.json", receipt)
    if not unchanged:
        raise ValueError("Source changed during import. Copy and failure receipt retained; close logging before retrying")
    return folder


def guide_text():
    return """Learning mode: no benchmark or capture controls are enabled here.

Tools: refresh installation/running status, select a tool and open its existing interface. Windows approvals remain manual. PresentMon console is inventory-only because launching it can start collection.

Sensors and RTSS: Refresh reads existing shared memory with read access only. Afterburner supplies sensor names, units and values. RTSS supplies application identity and its calculated FPS summaries/lows (converted from tenths of FPS). Statistics may refer to an older interval; no benchmark acceptance is inferred. Stale live FPS is unavailable. Latency instrumentation endpoint presence is not measured latency. Auto refresh is optional and saves no time series.

Reports: choose a report exported by an existing program. Import preserves original bytes plus provider, definition and SHA-256. PresentMon v2 CSV previews retain up to five original rows, GPU/latency field definitions, application/PID/swapchain and frame type where supplied. N/A and blank cells stay intact; no lows or latency are calculated. Software input-to-display estimates are not an optical measurement. HML/other formats remain opaque. Select an import to see its receipt; Ctrl+E opens its archived original in the associated application.

Catalog: Ctrl+6 opens recorded components, games, features, sources and relationships. Filters and details are read-only. Prepare comparison previews one-factor or 2x2 plans using the existing catalog engine; required hosts remain On and resource measurements stay null. Source changes require explicit Reload. Catalog capabilities and source links are inert data, not clickable launch/install/capture actions. Copy details/plan exports only catalog data, not private executable registry paths. Existing native/AHK profiles are not edited.

FG preflight: Check FG explicitly reads native settings and documented NVIDIA driver profiles where available. Preparing or copying an in-game plan rechecks automatically. Dynamic MFG active, unknown effective mode, missing/stale/conflicting or configuration-only evidence blocks comparisons. A native FG choice or disabled driver override is not runtime proof. Manager-idle scope is not applicable and reads no FG source. Optional paths stay local and are not saved. No game, collector, graphics or profile action is performed.

User control: Add tool shows a local path/name form and an explicit interface-only confirmation. Reports accepts a local file path plus program and definitions; Browse is optional. Save snapshot creates a new immutable file inside the private data folder; its location appears in the status bar. Configure each application's sensor selection, overlay and shortcuts in its own settings. This helper does not write Afterburner/RTSS profiles, overclock settings or game settings. It supplies no global hotkeys, input injection, remote server, startup task or automatic uploads.

Agent control: inspect and snapshot commands return structured JSON; import-report archives an explicitly selected report. Future adapters can import a provider's summaries with original definitions, frame classes and latency endpoints. Recording stays deferred until explicitly requested.

Local shortcuts (only while this panel is focused): Ctrl+1 Tools, Ctrl+2 Sensors, Ctrl+3 RTSS, Ctrl+4 Reports, Ctrl+5 How to use; Ctrl+R Refresh, Ctrl+O Open selected tool, Ctrl+A Add tool, Ctrl+C Copy status, Ctrl+S Save snapshot, Ctrl+I Import report, Ctrl+E Open selected original. Sensors/RTSS: Ctrl+T toggles optional refresh. Alt+F4 closes only this panel. Collectors remain blocked even if registered under another name.

Catalog uses Ctrl+6, Ctrl+R Reload and Ctrl+C Copy selected record (normal text copy/select-all is retained). Ctrl+O/A/S/I/E are blocked on Catalog so a remembered selection in another tab cannot launch, register, snapshot or import anything accidentally. Use the original tab for those existing actions.

Comparison uses Ctrl+7. Explicitly load an existing normalized provider-summary JSON, inspect run values, metadata and blocked reasons, then export a new local HTML/JSON report. The tab never collects data, starts recording, opens other programs or writes profiles. It computes only simple differences and spread across existing provider summaries; it does not calculate lows or latency from raw frames. Synthetic fixtures are labeled and cannot establish performance. Real in-game datasets remain blocked for numerical cost inference until trusted runtime FG evidence is supported; imported declarations cannot override the live Catalog gate. Process-idle datasets require matched metadata and at least three complete runs per case. Missing values, memory warnings and unmatched workloads remain visible. Ctrl+R reloads the selected data; Ctrl+C copies the current offline result. Ctrl+O/A/S/I/E do not invoke remembered Tools/Reports actions on this tab.

Closing this panel stops its optional refresh. It does not close other programs or stop an unrelated existing collector.

Saved crash evidence: Sessions → Saved crash evidence opens an inert selected-file view. Explicitly choose saved Windows event XML, Hub journal JSONL or opaque text/log files, preview hashes and an uncertain timeline, then create a new private packet outside the repository. Originals/private locators stay private; portable copy excludes payloads/names/paths. No live watcher, crash cause, verified memory exhaustion, recorder or game control is provided. CLI saved-evidence inspect/packet and session inspect-evidence use the same fixed backend. No upload or replay is automatic.

Workflow dry-runs: Sessions → Workflow dry-runs opens an inert recipe preview. Explicitly choose a data-only installation or diagnostic recipe, inspect private local targets separately from the portable change/rollback plan, then Copy or Export a new JSON outside the repository. Unknown/conflicting owners, dependency cycles/missing hosts, stopped-process declarations, backup coverage, hash drift and memory warnings remain visible. PREPARED_NOT_AUTHORIZED means only that declarations are structurally complete; it does not verify the live target, copied backups, restored behavior or effective FG. Diagnostic hypotheses rank declared support counts, not likelihood or proven cause. No Install, Apply, Launch or Rollback execution exists. workflow inspect/export and session inspect-workflow reuse the same fixed backend and do not read providers or the registry. Games, benchmarks and recording remain deferred.

Saved report adapters: on Comparison, choose Import saved reports, select supported Cyberpunk benchmark summary JSON or PresentMon GUI statistics CSV, and explicitly assign baseline/a conditions. Preview extracted values, definitions and missing metadata, then create a new private import folder and load its generated comparison dataset. Original bytes are archived/hash-verified; no hand-written normalized JSON is required. Unknown UTC/settings/FG/memory remain unknown and real rendering comparisons remain BLOCKED. Raw frame CSV, HML and unrecognized summaries are not silently converted. Agent routes inspect-saved-report and import-saved-reports use the same bounded backend without reading providers or executable registry.

Provider / scenario contracts: Sessions opens an optional private JSON editor and offline mock checker. Load a path explicitly (Browse optional), Preview unsaved edits and Save NEW scenario outside the repository. Originals are hash-pinned and never overwritten. Approval/process presence is not fresh writing; missing, partial, stale, wrong-context or gapped mock records block readiness. MOCK_HEALTHY and PREPARED_NOT_AUTHORIZED are declaration verdicts, never live capture, FG PASS or permission. Versioned phases, cache/workload readback, camera/HUD/animation tags, budgets and stop policies contain no commands, keys or save/graphics actions. Readiness CLI inspect/save-scenario and session inspect-readiness use fixed backends; no provider launch, recorder or scenario runner exists.

Sessions uses Ctrl+8. Explicitly create a new offline journal, record checkpoints and inspect saved reports/comparisons through a fixed read-only coordinator. Each acknowledged journal entry is flushed and fsynced. Inspect or recover an interrupted journal's verified complete prefix into a new evidence-only file; the original is never repaired or replayed. Cooperative ownership, cancellation and expiry affect only this session, not other apps or chats. This is process-interruption recovery, not a guarantee against every storage failure or a crash-cause diagnosis. No game input, capture, benchmark, recording or settings adapter is enabled. Ctrl+R refreshes this tab; Ctrl+C copies its sanitized summary; Ctrl+O/A/S/I/E cannot invoke remembered Tools/Reports actions. Closing the Hub releases only its own session. Session CLI capabilities, inspect, recover, inspect-report and compare use the same offline modules without registry/provider reads.
"""


def load_catalog_module(name):
    # Authored exact sibling modules only; JSON records can never select code.
    if name not in {"GameToolGameProfilesUI", "GameToolFocusUI", "GameToolModIntegration", "GameToolAppearance", "GameToolWorkspace", "GameToolUserData", "GameToolUserDataPanel", "GameToolUnified", "GameToolUnifiedPanel", "GameToolCatalogBridge", "GameToolCatalogPanel", "GameToolComparison", "GameToolComparisonPanel", "GameToolReportImport", "GameToolJournal", "GameToolCoordinator", "GameToolSessionPanel", "GameToolCrashEvidence", "GameToolEvidencePanel", "GameToolWorkflow", "GameToolWorkflowPanel", "GameToolReadiness", "GameToolReadinessPanel", "GameToolOverlay", "GameToolCompactUI", "GameToolOverlayPanel"}:
        raise ValueError("Unsupported optional authored module")
    path = Path(__file__).resolve().with_name(name + ".py")
    before = path.stat()
    with path.open("rb") as handle:
        source = handle.read(1024 * 1024 + 1)
    after = path.stat()
    if len(source) > 1024 * 1024 or len(source) != before.st_size or \
            (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != \
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
        raise ValueError("Optional catalog module exceeded its limit or changed during loading")
    spec = importlib.util.spec_from_file_location("hub_" + name, path)
    if spec is None or spec.loader is None:
        raise ImportError("Optional catalog module unavailable")
    module = importlib.util.module_from_spec(spec)
    # Compile these captured authored bytes; do not consume/write timestamp pyc caches.
    exec(compile(source, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def new_catalog_service(path=None):
    return load_catalog_module("GameToolCatalogBridge").CatalogService(path)


def journal_summary(result):
    """Portable structural evidence, not user metadata or replay authority."""
    keys = ("valid", "clean_end", "verified_count", "verified_bytes", "source_sha256", "source_bytes",
            "error", "recovery_required", "discarded_tail_bytes", "limitations", "safety_caveat")
    return {**{key: result[key] for key in keys if key in result},
            "execution": "none", "replay_allowed": False}


def gui(data_dir, draft=None, catalog_path=None, overlay_page=False, unified_install=None, interface_preview=None):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    from GameToolWindowsApp import Session
    app_session=Session('unified',unified_install or data_dir)
    if not app_session.primary:return
    data_dir.mkdir(parents=True, exist_ok=True)
    registry = data_dir / "tools.json"
    tools = load_tools(registry)
    draft = draft or {}
    if unified_install is not None and os.name == "nt":
        # Match the native AHK system-DPI-aware host before creating Tk windows;
        # avoid cross-process SetParent resetting the overlay engine's DPI mode.
        dpi_api = ctypes.WinDLL("user32", use_last_error=True)
        dpi_api.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        dpi_api.SetProcessDpiAwarenessContext(ctypes.c_void_p(-2))
    root = tk.Tk()
    app_session.attach(root)
    root.game_tools_icon_path = data_dir / 'ui-choice-icons.json'
    root.game_tools_icon_namespace = 'unified-game-tools'
    root.title(f'{"Unified Game Tools" if unified_install else "Game Tool Hub"} {VERSION} — Learning mode')
    if interface_preview in ("Focus", "Original"):
        root.title(f"Game Tools — {interface_preview} UI preview · {VERSION}")
    root.resizable(True, True)
    try:
        compact_ui = load_catalog_module("GameToolCompactUI")
    except ImportError:
        # An optional presentation module must not break original Hub pages.
        class LegacyScroll(ttk.Frame):
            def __init__(self, parent, min_width=0):
                super().__init__(parent); self.body = self
            def close(self): pass
        class LegacyToolbar(ttk.Frame):
            def add(self, text, command):
                button=ttk.Button(self,text=text,command=command)
                button.pack(side="left",padx=4); return button
        class LegacyUI:
            ScrollableFrame=LegacyScroll
            FlowToolbar=LegacyToolbar
        compact_ui=LegacyUI
    bounds = compact_ui.window_bounds(root.winfo_screenwidth(), root.winfo_screenheight()) if hasattr(compact_ui, "window_bounds") else (1360,880,760,540)
    root.geometry(f"{bounds[0]}x{bounds[1]}")
    root.minsize(bounds[2], bounds[3])
    status = tk.StringVar(value="Ready")
    status_bar = ttk.Frame(root, padding=(12, 6))
    status_bar.pack(side="bottom", fill="x")
    resize_grip = ttk.Sizegrip(status_bar)
    resize_grip.pack(side="right", anchor="se")
    status_label=ttk.Label(status_bar, textvariable=status, wraplength=1000)
    status_label.pack(side="left", anchor="w", fill="x", expand=True)
    header = ttk.Frame(root, padding=(12,8)); header.pack(fill="x")
    app_title=ttk.Label(header, text="GameTools", font=("Segoe UI", 16, "bold")); app_title.pack(side="left")
    scope_label=tk.Label(root, text="CONTROLLED WORKSPACE   •   Games, benchmarks and recording stay stopped" if unified_install else "LEARNING MODE   •   Tool connections and report management", bg="#fff0bf", fg="#604800", padx=10, pady=4, wraplength=900)
    scope_label.pack(fill="x", padx=12, pady=(0,4))
    root.game_tools_scope_banner = scope_label
    workspace = None
    if unified_install is not None or interface_preview in ("Focus", "Original"):
        try:
            workspace_api = load_catalog_module("GameToolWorkspace")
            nav_registry = None
            try:
                nav_registry = load_catalog_module("GameToolModIntegration").navigation_registry(workspace_api)
            except (ImportError, OSError, ValueError):
                pass  # Preserve the original navigation when an optional module is absent.
            workspace = workspace_api.Workspace(root, status, registry=nav_registry)
            workspace.frame.pack(fill="both", expand=True, padx=12)
        except Exception as error:
            status.set("Optional goal navigation unavailable: " + str(error))
    tabs = ttk.Notebook(workspace.content if workspace else root)
    tabs.pack(fill="both", expand=True, **({} if workspace else {"padx":22}))
    original_tabs = [ttk.Frame(tabs, padding=10) for _ in range(5)]
    original_scrolls = [compact_ui.ScrollableFrame(tab, min_width=420) for tab in original_tabs]
    for tab, scroll, name in zip(original_tabs, original_scrolls, ("Tools", "Sensors", "RTSS", "Reports", "How to use")):
        tabs.add(tab, text=name)
        scroll.pack(fill="both",expand=True)
    tool_tab, sensor_tab, rtss_tab, report_tab, guide_tab = [scroll.body for scroll in original_scrolls]
    catalog_tab = ttk.Frame(tabs, padding=12)
    tabs.add(catalog_tab, text="Catalog")
    catalog_panel = None
    try:
        catalog_panel = load_catalog_module("GameToolCatalogPanel").CatalogPanel(
            catalog_tab, lambda: new_catalog_service(catalog_path), status)
    except Exception as error:
        ttk.Label(catalog_tab, text="Optional Catalog unavailable. Original Hub tabs remain usable.",
                  wraplength=950).pack(anchor="w", pady=12)
        ttk.Label(catalog_tab, text=str(error), wraplength=950).pack(anchor="w")
    comparison_tab = ttk.Frame(tabs, padding=12)
    tabs.add(comparison_tab, text="Comparison")
    comparison_panel = None
    try:
        comparison_panel = load_catalog_module("GameToolComparisonPanel").ComparisonPanel(
            comparison_tab, status)
    except Exception as error:
        ttk.Label(comparison_tab, text="Optional Comparison unavailable. Existing Hub tabs remain usable.",
                  wraplength=950).pack(anchor="w", pady=12)
        ttk.Label(comparison_tab, text=str(error), wraplength=950).pack(anchor="w")
    session_tab = ttk.Frame(tabs, padding=12)
    tabs.add(session_tab, text="Sessions")
    session_panel = None
    try:
        session_panel = load_catalog_module("GameToolSessionPanel").SessionPanel(
            session_tab,
            lambda **options: load_catalog_module("GameToolCoordinator").Coordinator(**options),
            load_catalog_module("GameToolJournal"), status.set,
            evidence_factory=lambda parent, callback: load_catalog_module("GameToolEvidencePanel").EvidencePanel(
                parent, load_catalog_module("GameToolCrashEvidence"), callback),
            workflow_factory=lambda parent, callback: load_catalog_module("GameToolWorkflowPanel").WorkflowPanel(
                parent, load_catalog_module("GameToolWorkflow"), callback),
            readiness_factory=lambda parent, callback: load_catalog_module("GameToolReadinessPanel").ReadinessPanel(
                parent, load_catalog_module("GameToolReadiness"), callback))
    except Exception as error:
        ttk.Label(session_tab, text="Optional Sessions unavailable. Existing Hub tabs remain usable.",
                  wraplength=950).pack(anchor="w", pady=12)
        ttk.Label(session_tab, text=str(error), wraplength=950).pack(anchor="w")
    overlay_tab = ttk.Frame(tabs, padding=12)
    tabs.add(overlay_tab, text="Overlays")
    overlay_panel = None
    try:
        overlay_panel = load_catalog_module("GameToolOverlayPanel").OverlayPanel(overlay_tab, data_dir, status)
    except Exception:
        ttk.Label(overlay_tab, text="Optional overlays unavailable. Existing Hub tabs remain usable; inspect source/dependencies.").pack(anchor="w")
    mod_integration = None
    try:
        mod_integration = load_catalog_module("GameToolModIntegration").Integration(tabs, data_dir, status, focus=(interface_preview == "Focus"))
    except Exception:
        status.set("Optional Mods / AI integration unavailable; original pages remain usable.")
    if overlay_page:
        tabs.select(overlay_tab)
    unified_panel = None
    data_panel = None
    data_tab = None
    profiles_panel = None
    profiles_tab = None
    if unified_install is not None:
        try:
            unified_panel = load_catalog_module("GameToolUnifiedPanel").UnifiedPanel(
                root, tabs, unified_install, load_catalog_module("GameToolUnified"), status)
            tabs.select(unified_panel.studio_tab)
        except Exception as error:
            status.set("Unified Studio unavailable; original Hub features remain usable: " + str(error))
        data_tab = ttk.Frame(tabs, padding=12)
        tabs.add(data_tab, text="User data")
        try:
            data_panel = load_catalog_module("GameToolUserDataPanel").UserDataPanel(
                data_tab, load_catalog_module("GameToolUserData"), status, VERSION)
        except Exception as error:
            ttk.Label(data_tab,text="Optional private-data tools unavailable: " + str(error),wraplength=700).pack(anchor="w")
        if unified_panel is not None and overlay_panel is not None:
            profiles_tab = ttk.Frame(tabs,padding=12)
            tabs.add(profiles_tab,text='Game profiles')
            try:
                profiles_panel=load_catalog_module('GameToolGameProfilesUI').ProfilesPanel(
                    profiles_tab,data_dir,unified_panel,overlay_panel,status)
                tabs.select(profiles_tab)
            except Exception as error:
                ttk.Label(profiles_tab,text='Game profiles need attention: '+str(error),wraplength=700).pack(anchor='w')
    if workspace is not None:
        routes = dict(zip(("tools","sensors","rtss","reports","guide"), original_tabs))
        routes.update(catalog=catalog_tab,comparison=comparison_tab,sessions=session_tab,overlays=overlay_tab)
        if mod_integration is not None: routes.update(mod_integration.routes)
        if unified_panel is not None:
            routes.update(studio=unified_panel.studio_tab,updates=unified_panel.update_tab)
        if data_tab is not None: routes["data"] = data_tab
        if profiles_tab is not None: routes['profiles'] = profiles_tab
        workspace.attach(tabs,routes)
    state = {}
    if mod_integration is not None: mod_integration.automation.tool_snapshot = lambda: state

    def table(parent, columns):
        box = ttk.Frame(parent)
        box.pack(fill="both", expand=True)
        box.columnconfigure(0,weight=1); box.rowconfigure(0,weight=1)
        tree = ttk.Treeview(box, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=150, minwidth=80)
        tree.grid(row=0,column=0,sticky="nsew")
        scroll = ttk.Scrollbar(box, command=tree.yview)
        scroll.grid(row=0,column=1,sticky="ns")
        tree.configure(yscrollcommand=scroll.set)
        horizontal = ttk.Scrollbar(box,orient="horizontal",command=tree.xview)
        horizontal.grid(row=1,column=0,sticky="ew"); tree.configure(xscrollcommand=horizontal.set)
        return tree

    toolbar = compact_ui.FlowToolbar(tool_tab)
    toolbar.pack(fill="x", pady=(0, 10))
    registration = ttk.Frame(tool_tab)
    tool_tree = table(tool_tab, ("Tool", "Installed", "Running", "File version"))
    config_info = tk.StringVar()
    ttk.Label(tool_tab, textvariable=config_info, wraplength=900).pack(anchor="w", pady=12)
    registration.columnconfigure(1, weight=1)
    tool_path = tk.StringVar(value=draft.get("tool", {}).get("path", ""))
    tool_label = tk.StringVar(value=draft.get("tool", {}).get("name", ""))
    interface_confirmed = tk.BooleanVar(value=False)
    ttk.Label(registration, text="Installed EXE path").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    tool_path_entry = ttk.Entry(registration, textvariable=tool_path, width=70)
    tool_path_entry.grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Label(registration, text="Name").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(registration, textvariable=tool_label, width=40).grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Checkbutton(registration, text="Confirmed: this opens an interface without starting collection", variable=interface_confirmed).grid(row=2, column=1, sticky="w", padx=5, pady=5)
    sensor_bar = ttk.Frame(sensor_tab)
    sensor_bar.pack(fill="x", pady=(0, 10))
    connection = tk.StringVar(value="Not checked")
    ttk.Label(sensor_bar, textvariable=connection).pack(side="right")
    sensor_tree = table(sensor_tab, ("Source", "Value", "Unit", "Scope"))
    ttk.Label(sensor_tab, text="Values supplied by Afterburner. No game/run association; no statistics calculated here.").pack(anchor="w", pady=10)
    auto = tk.BooleanVar(value=False)
    rtss_bar = ttk.Frame(rtss_tab)
    rtss_bar.pack(fill="x", pady=(0, 10))
    rtss_connection = tk.StringVar(value="Not checked")
    ttk.Label(rtss_bar, textvariable=rtss_connection).pack(side="right")
    rtss_tree = table(rtss_tab, ("Application / PID", "Fresh", "Average FPS", "1% low", "0.1% low", "Interval samples", "Capture state"))
    rtss_detail = tk.StringVar(value="Select an application for interval and instrumentation details.")
    ttk.Label(rtss_tab, textvariable=rtss_detail, wraplength=1030).pack(anchor="w", pady=10)
    ttk.Label(rtss_tab, text="RTSS calculates these values. Historical intervals are not new benchmarks; no latency calculations here.").pack(anchor="w", pady=6)

    def rtss_selected(event=None):
        selected = rtss_tree.selection()
        if selected:
            app = state["rtss"]["applications"][int(selected[0])]
            rtss_detail.set(f'Provider interval ticks: {app["statistics_interval_ticks"]}; update age: {app["update_age_ms"]} ms. '
                f'Instrumentation endpoints present: {", ".join(app["latency_endpoints_present"]) or "none"}. '
                'Latency unavailable; game/run acceptance and base/generated frame coverage are unverified.')
    rtss_tree.bind("<<TreeviewSelect>>", rtss_selected)

    def refresh():
        try:
            state.clear()
            state.update(inspect(tools))
            tool_tree.delete(*tool_tree.get_children())
            for tool in state["tools"]:
                tool_tree.insert("", "end", iid=tool["id"], values=(tool["name"], "Yes" if tool["installed"] else "No",
                    "Unknown" if tool["running"] is None else "Yes" if tool["running"] else "No", tool["version"] or "Unknown"))
            sensor_tree.delete(*sensor_tree.get_children())
            reading = state["afterburner"]
            for row in reading["rows"]:
                sensor_tree.insert("", "end", values=(row["name"], "Unavailable" if row["value"] is None else f'{row["value"]:.3f}', row["units"], row["scope"]))
            connection.set(f'Afterburner: {reading["state"]} • {len(reading["rows"])} sources')
            rtss_tree.delete(*rtss_tree.get_children())
            rtss_reading = state["rtss"]
            for index, app in enumerate(rtss_reading["applications"]):
                values = app["values"]
                display = lambda key: "Unavailable" if values[key]["fps"] is None else f'{values[key]["fps"]:.1f}'
                capture = "Provider recording active" if app["statistics_recording"] or app["video_capture_requested_or_active"] else "No capture flag"
                rtss_tree.insert("", "end", iid=str(index), values=(f'{Path(app["application"]).name} / {app["process_id"]}',
                    "Yes" if app["fresh"] else "No / unknown", display("average"), display("low_1"), display("low_01"), app["statistics_count"], capture))
            rtss_connection.set(f'RTSS: {rtss_reading["state"]} • {len(rtss_reading["applications"])} app entries')
            cfg = state["afterburner_configuration"]
            config_info.set(f'Saved profile: logging {"off" if cfg.get("EnableLog") == "0" else "on / unknown"}; begin/end recording hotkeys: {cfg.get("BeginRecordHotkey", "unknown")} / {cfg.get("EndRecordHotkey", "unknown")}. Profiles are read only.')
            status.set(reading.get("reason", "Refreshed. Recording controls remain unavailable in learning mode."))
        except Exception as error:
            status.set(f"Connection error: {error}")

    def open_tool():
        selected = tool_tree.selection()
        if not selected:
            status.set("Select a tool on the Tools tab first.")
            return
        tool = next(t for t in tools if t["id"] == selected[0])
        if not launch_allowed(tool):
            status.set("Inventory only: this collector cannot be launched in learning mode.")
            return
        try:
            path = Path(tool["path"]).resolve(strict=True)
            if path.suffix.lower() != ".exe":
                raise ValueError("Only registered EXE applications can be opened")
            os.startfile(str(path))
            status.set("Launch requested. Approve Windows manually if prompted; refresh to verify.")
        except Exception as error:
            messagebox.showerror("Open tool", str(error))

    def add_tool():
        tabs.select(tool_tab)
        interface_confirmed.set(False)
        registration.pack(fill="x", before=tool_tree.master)
        tool_path_entry.focus_set()
        status.set("Register an installed interface. Nothing is launched by registration.")

    def register_from_form():
        try:
            added = register_tool(registry, tools, tool_path.get(), tool_label.get(), interface_confirmed.get())
            refresh()
            registration.pack_forget()
            interface_confirmed.set(False)
            status.set("Installed interface registered; no launch or capture started." if added else "Already registered; existing entry retained.")
        except (OSError, ValueError) as error:
            status.set(f"Registration refused: {error}")

    def browse_tool():
        path = filedialog.askopenfilename(title="Select an installed tool", filetypes=[("Application", "*.exe")])
        if path:
            tool_path.set(path)
            tool_label.set(Path(path).stem)
    ttk.Button(registration, text="Browse…", command=browse_tool).grid(row=0, column=2, padx=5)
    ttk.Button(registration, text="Register", command=register_from_form).grid(row=1, column=2, padx=5)
    ttk.Button(registration, text="Cancel", command=lambda: registration.pack_forget()).grid(row=2, column=2, padx=5)

    def save_snapshot():
        path = data_dir / ("connection-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:12] + ".json")
        try:
            exclusive_json(path, state)
            status.set(f"Saved private connection snapshot: {path}")
        except OSError as error:
            status.set(f"Snapshot could not be saved: {error}")

    def copy_summary():
        summary = {"observed_utc": state.get("observed_utc"), "mode": "learning", "capture_started": False,
                   "tools": [{k: t[k] for k in ("name", "installed", "running", "version")} for t in state.get("tools", [])],
                   "afterburner_state": state.get("afterburner", {}).get("state"),
                   "source_count": len(state.get("afterburner", {}).get("rows", [])),
                   "rtss_state": state.get("rtss", {}).get("state"),
                   "rtss_application_count": len(state.get("rtss", {}).get("applications", []))}
        root.clipboard_clear()
        root.clipboard_append(json.dumps(summary, indent=2))
        status.set("Copied tool status without local paths; paste wherever you choose.")

    def import_file():
        tabs.select(report_tab)
        path, provider, definition = report_path.get(), report_provider.get(), report_definition.get()
        if not path.strip() or not provider.strip():
            report_path_entry.focus_set()
            status.set("Enter an existing report path and the program that produced it, then click Import report.")
            return
        try:
            folder = import_report(path, data_dir / "imports", provider, definition)
            add_receipt(folder / "receipt.json")
            report_list.selection_clear(0, "end")
            report_list.selection_set("end")
            show_receipt()
            status.set("Original report and receipt archived privately. Metrics were not recalculated.")
        except Exception as error:
            status.set(f"Import refused: {error}")

    toolbar.add("Refresh connection", refresh)
    toolbar.add("Open selected tool", open_tool)
    toolbar.add("Add installed tool", add_tool)
    toolbar.add("Copy status", copy_summary)
    toolbar.add("Save snapshot", save_snapshot)
    ttk.Button(sensor_bar, text="Refresh connection", command=refresh).pack(side="left")
    ttk.Checkbutton(sensor_bar, text="Auto refresh every 5 seconds", variable=auto).pack(side="left", padx=12)
    ttk.Button(rtss_bar, text="Refresh connection", command=refresh).pack(side="left")
    ttk.Checkbutton(rtss_bar, text="Auto refresh every 5 seconds", variable=auto).pack(side="left", padx=12)
    ttk.Label(report_tab, text="Import an existing program's report. Original values and definitions are retained.").pack(anchor="w", pady=8)
    report_form = ttk.Frame(report_tab)
    report_form.pack(fill="x")
    report_form.columnconfigure(1, weight=1)
    report_path = tk.StringVar(value=draft.get("report", {}).get("path", ""))
    report_provider = tk.StringVar(value=draft.get("report", {}).get("provider", ""))
    report_definition = tk.StringVar(value=draft.get("report", {}).get("definition", "Unknown; retain provider documentation"))
    ttk.Label(report_form, text="Existing report path").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    report_path_entry = ttk.Entry(report_form, textvariable=report_path)
    report_path_entry.grid(row=0, column=1, sticky="ew", padx=5)
    ttk.Label(report_form, text="Program / version").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(report_form, textvariable=report_provider).grid(row=1, column=1, sticky="ew", padx=5)
    ttk.Label(report_form, text="Definitions / source").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    ttk.Entry(report_form, textvariable=report_definition).grid(row=2, column=1, sticky="ew", padx=5)
    def browse_report():
        path = filedialog.askopenfilename(title="Select an existing tool report", filetypes=[("Reports", "*.csv *.json *.txt *.hml")])
        if path:
            report_path.set(path)
    ttk.Button(report_form, text="Browse…", command=browse_report).grid(row=0, column=2, padx=5)
    report_bar = ttk.Frame(report_tab)
    report_bar.pack(fill="x", pady=10)
    ttk.Button(report_bar, text="Import report…", command=import_file).pack(side="left")
    receipts = []
    report_list = tk.Listbox(report_tab)
    report_list.pack(fill="x", pady=8, ipady=4)
    report_list.configure(height=4, exportselection=False)
    report_detail = tk.Text(report_tab, wrap="word", height=9)
    report_detail.pack(fill="both", expand=True)
    report_detail.configure(state="disabled")

    def add_receipt(path):
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
            receipts.append((path, receipt))
            report_list.insert("end", f'{receipt.get("provider", "Unknown")}: {receipt.get("source_name", "Unknown")} — {path.parent.name}')
        except (OSError, ValueError) as error:
            status.set(f"Receipt unavailable: {error}")

    def show_receipt(event=None):
        selected = report_list.curselection()
        if selected:
            report_detail.configure(state="normal")
            report_detail.delete("1.0", "end")
            report_detail.insert("1.0", json.dumps(receipts[selected[0]][1], indent=2, ensure_ascii=False))
            report_detail.configure(state="disabled")
    report_list.bind("<<ListboxSelect>>", show_receipt)

    def open_report():
        selected = report_list.curselection()
        if not selected:
            status.set("Select an imported report first.")
            return
        path, receipt = receipts[selected[0]]
        original = path.parent / ("original" + Path(receipt.get("stored_file", "")).suffix.lower())
        if original.suffix.lower() not in (".csv", ".json", ".txt", ".hml") or not original.is_file():
            messagebox.showerror("Open original", "Archived original is unavailable.")
            return
        try:
            os.startfile(str(original))
            status.set("Original report opened in its associated application; no capture started.")
        except OSError as error:
            messagebox.showerror("Open original", str(error))
    ttk.Button(report_bar, text="Open selected original", command=open_report).pack(side="left", padx=12)
    for receipt in sorted((data_dir / "imports").glob("*/receipt.json")):
        add_receipt(receipt)
    text = tk.Text(guide_tab, wrap="word", font=("Segoe UI", 11), padx=10, pady=10, height=12)
    text.insert("1.0", guide_text())
    text.configure(state="disabled")
    text.pack(fill="both", expand=True)

    # Callback closures select Notebook pages, not the new scroll-body frames.
    tool_tab, sensor_tab, rtss_tab, report_tab, guide_tab = original_tabs
    shortcuts = {}
    for index, tab in enumerate((tool_tab, sensor_tab, rtss_tab, report_tab, guide_tab, catalog_tab, comparison_tab, session_tab), 1):
        shortcuts[str(index)] = lambda t=tab: tabs.select(t)
    for key, action in (("r", refresh), ("o", open_tool), ("a", add_tool), ("c", copy_summary),
                        ("s", save_snapshot), ("i", import_file), ("e", open_report)):
        shortcuts[key] = action
    def toggle_refresh():
        if tabs.select() in (str(sensor_tab), str(rtss_tab)):
            auto.set(not auto.get())
            status.set(f'Auto refresh {"on" if auto.get() else "off"}; no time series saved.')
    shortcuts["t"] = toggle_refresh
    def handle_shortcut(event):
        focused = root.focus_get()
        key = shortcut_key(event.keycode, event.keysym, os.name == "nt")
        if focused is None or focused.winfo_toplevel() != root or root.grab_current() is not None:
            return
        if key == "k" and workspace is not None:
            surface = getattr(root, "game_tools_focus", None)
            if surface is not None and surface.active:
                return surface.focus_search(event)
            return workspace._focus_search(event)  # Physical Ctrl+K also works with Hebrew layout.
        if key in ("a", "c") and isinstance(focused, (ttk.Entry, ttk.Combobox, tk.Text)):
            return
        if workspace is not None and workspace.home_visible:
            # The hidden Notebook may still remember Tools. Home must not
            # forward its launch/capture/import shortcuts to a hidden editor.
            if key in {str(i) for i in range(1, 9)}:
                shortcuts[key]()
                workspace.reveal_selected_page()
            else:
                status.set("Home uses navigation only; open a workspace for its explicit actions.")
            return "break"
        if mod_integration is not None and tabs.select() in {str(p) for p in mod_integration.routes.values()} and key in {"r", "c", "o", "a", "s", "i", "e", "t"}:
            if key == "r":
                if tabs.select() == str(mod_integration.mods): mod_integration.mods.refresh()
                else: mod_integration.automation.refresh()
            else:
                status.set("Mods / AI use explicit controls; no remembered Tools or Reports action is forwarded.")
            return "break"
        if data_tab is not None and tabs.select() == str(data_tab) and key in {"r", "c", "o", "a", "s", "i", "e"}:
            status.set("User data uses explicit reviewed-copy actions only.")
            return "break"
        if unified_panel is not None and tabs.select() in (str(unified_panel.studio_tab), str(unified_panel.update_tab)) and key in {"r", "c", "o", "a", "s", "i", "e"}:
            status.set("Studio / Updates use their explicit controls; no remembered Tools/Reports action is forwarded.")
            return "break"
        if tabs.select() == str(overlay_tab) and key in {"r", "c", "o", "a", "s", "i", "e"}:
            if key == "r" and overlay_panel is not None:
                overlay_panel.tick(reschedule=False)
            else:
                status.set("Overlays use explicit controls only; no tool launch or capture shortcut is forwarded.")
            return "break"
        if tabs.select() == str(session_tab) and key in {"r", "c", "o", "a", "s", "i", "e"}:
            if key == "r" and session_panel is not None:
                session_panel.reload()
            elif key == "c" and session_panel is not None:
                session_panel.copy_summary()
            else:
                status.set("Sessions is offline only. Use its explicit buttons or the original Tools/Reports tab.")
            return "break"
        if tabs.select() == str(comparison_tab) and key in {"r", "c", "o", "a", "s", "i", "e"}:
            if key == "r" and comparison_panel is not None:
                comparison_panel.reload()
            elif key == "c" and comparison_panel is not None:
                comparison_panel.copy_summary()
            else:
                status.set("Comparison is offline only. Use its explicit load/export buttons or Tools/Reports for existing actions.")
            return "break"
        if tabs.select() == str(catalog_tab) and key in {"r", "c", "o", "a", "s", "i", "e"}:
            if key == "r" and catalog_panel is not None:
                catalog_panel.reload()
            elif key == "c" and catalog_panel is not None:
                catalog_panel.copy_details()
            else:
                status.set("Catalog is read-only. Use Tools or Reports for their existing actions.")
            return "break"
        if key in shortcuts:
            shortcuts[key]()
            return "break"
    root.bind("<Control-KeyPress>", handle_shortcut)

    def tick():
        if auto.get():
            refresh()
        root.after(5000, tick)

    focus_surface = None
    close_deadline = None
    def close_hub():
        nonlocal close_deadline
        if mod_integration is not None and not mod_integration.can_close():
            status.set("Cancellation requested. Close again after the bounded active operation returns; no effects are replayed.")
            return False
        if data_panel is not None and data_panel.busy:
            status.set("Wait for the explicit private-data operation to finish before closing.")
            return False
        if unified_panel is not None and not unified_panel.close():
            if not unified_panel.updating:
                if close_deadline is None: close_deadline = time.monotonic() + 6
                if time.monotonic() < close_deadline:
                    root.after(100, close_hub)
                    status.set("Closing only this app’s Studio normally…")
                else:
                    status.set("Studio has not closed normally; no forced termination. Close it before retrying.")
                    close_deadline = None
            else: status.set("Wait for the explicit source update to finish before closing.")
            return False
        try:
            if focus_surface is not None: focus_surface.close()
            if appearance is not None: appearance.close()
            if mod_integration is not None: mod_integration.close()
            for scroll in original_scrolls: scroll.close()
            if data_panel is not None: data_panel.close()
            if catalog_panel is not None: catalog_panel.close()
            if workspace is not None: workspace.close()
            if overlay_panel is not None:
                overlay_panel.close()
            if profiles_panel is not None: profiles_panel.close()
            if session_panel is not None:
                session_panel.close()
        finally:
            root.destroy()
        return True
    appearance = None
    try:
        appearance = load_catalog_module("GameToolAppearance").Appearance(
            root, header, workspace, status, data_dir / "ui-preferences.json", VERSION)
        for target,role,name in ((app_title,"app-title","Application title"),
                (scope_label,"safety-banner","Offline safety scope"),(status_label,"status","Current status")):
            appearance.markers.register(target,"UI-004."+role,name)
        if workspace:
            appearance.register_panel(workspace.frame,"UI-004",workspace,
                exclude=(workspace.content,workspace.tree,workspace.selector))
        for body, identifier in zip((s.body for s in original_scrolls),
                                   ("UI-404","UI-204","UI-205","UI-203","UI-407")):
            appearance.register_panel(body, identifier)
        for page, identifier, panel in ((catalog_tab,"UI-401",catalog_panel),
                (comparison_tab,"UI-201",comparison_panel),(session_tab,"UI-301",session_panel),
                (overlay_tab,"UI-403",overlay_panel),(data_tab,"UI-406",data_panel)):
            if page is not None: appearance.register_panel(page,identifier,panel)
        if mod_integration is not None:
            appearance.register_panel(mod_integration.mods,"UI-408",mod_integration.mods_roles)
            appearance.register_panel(mod_integration.automation,"UI-409",mod_integration.automation_roles)
        if comparison_panel is not None:
            appearance.markers.register(comparison_panel.buttons["Import saved reports"],
                "UI-202", "Comparison / saved-report import adapters", replace=True)
        if session_panel is not None:
            for caption, identifier in (("Saved crash evidence","UI-302"),("Workflow dry-runs","UI-303"),
                                       ("Provider / scenario contracts","UI-304")):
                appearance.markers.register(session_panel.buttons[caption], identifier, caption, replace=True)
        if unified_panel is not None:
            appearance.register_panel(unified_panel.studio_tab,"UI-109",unified_panel,exclude=(unified_panel.viewport,unified_panel.canvas))
            appearance.register_panel(unified_panel.update_tab,"UI-405",unified_panel)
            appearance.native_feedback = unified_panel.set_identification
            appearance.native_filter = unified_panel.set_identification_filter
        if interface_preview is not None and interface_preview not in ("Focus", "Original") and workspace is not None:
            appearance.preview(interface_preview)
    except (ImportError, OSError, ValueError) as error:
        status.set("Optional layout controls unavailable; original pages retained: " + str(error))
    if interface_preview == "Focus" and workspace is not None and appearance is not None:
        try:
            focus_surface = load_catalog_module("GameToolFocusUI").FocusSurface(
                root, header, scope_label, workspace, status, appearance, data_dir, mod_integration)
        except Exception as error:
            status.set("Focus layout unavailable; original pages retained: " + str(error))
    root.game_tools_mod_integration = mod_integration
    try:
        from GameToolChoiceIcons import context as icon_context
        if workspace: icon_context(workspace.selector, 'navigation.finder', 'Search')
        if profiles_panel:
            icon_context(profiles_panel.game, 'profiles.game', 'Game')
            icon_context(profiles_panel.profile, 'profiles.saved', 'Profile')
    except ImportError:
        pass
    root.game_tools_notebook = tabs
    if unified_panel is not None: unified_panel.on_close = close_hub
    root.protocol("WM_DELETE_WINDOW", close_hub)
    # This is an explicitly requested GUI entry point. Launchers may hide their
    # console helper; that startup flag must not leave the actual app unmapped.
    # No editor, profile, capture or input action is invoked by showing the root.
    root.deiconify()
    refresh()
    root.after(5000, tick)
    try:
        root.mainloop()
    finally:
        app_session.close()


def main(argv=None):
    # Fixed structured overlay endpoint; no arbitrary runner or input channel.
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "overlay":
        return load_catalog_module("GameToolOverlay").cli(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GameToolHub")
    parser.add_argument("--form-file", type=Path, help="Optional local JSON draft; prefill forms only, never perform an action")
    parser.add_argument("--catalog-file", type=Path, help="Optional catalog JSON; read-only, never executable")
    parser.add_argument("--overlay-page", action="store_true", help="Show the existing Hub's optional overlay page; no automatic activation")
    parser.add_argument("--unified-install", type=Path, help="Verified unified installation root; dock its preserved Studio and show explicit Updates")
    parser.add_argument("--interface-preview", choices=("Modern", "Focus", "Original"), help="Session-only preview; saved layout is unchanged")
    sub = parser.add_subparsers(dest="action")
    sub.add_parser("inspect")
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--output", type=Path, required=True)
    importing = sub.add_parser("import-report")
    importing.add_argument("--source", type=Path, required=True)
    importing.add_argument("--provider", required=True)
    importing.add_argument("--definition", default="Unknown; retain provider documentation")
    catalog = sub.add_parser("catalog", help="Read records or prepare a plan; never execute")
    catalog_sub = catalog.add_subparsers(dest="catalog_action", required=True)
    catalog_sub.add_parser("status")
    listing = catalog_sub.add_parser("list")
    for field in ("kind", "category", "game", "status", "installation", "relationship", "search"):
        listing.add_argument("--" + field)
    listing.add_argument("--sort", default="id", choices=("id", "name", "kind", "status"))
    showing = catalog_sub.add_parser("show")
    showing.add_argument("id")
    planning = catalog_sub.add_parser("plan-overhead")
    planning.add_argument("--scope", required=True, choices=("process-idle", "in-game"))
    planning.add_argument("--game")
    planning.add_argument("--factor", required=True, action="append")
    checking = catalog_sub.add_parser("fg-preflight", help="Explicit read-only effective-FG check; never run a game")
    checking.add_argument("--scope", required=True, choices=("process-idle", "in-game"))
    checking.add_argument("--game")
    for command in (planning, checking):
        command.add_argument("--executable", type=Path, help="Actual rendering executable; identify only, never launch")
        command.add_argument("--native-settings", type=Path, help="Optional native settings JSON; read only")
    comparing = sub.add_parser("compare-report", help="Compare existing normalized summaries only; never collect or execute")
    comparing.add_argument("--source", type=Path, required=True)
    comparing.add_argument("--metric", help="Optional metric ID from the dataset")
    comparing.add_argument("--output", type=Path, help="New local HTML or JSON output; never overwrite")
    comparing.add_argument("--format", choices=("json", "html"), default="json")
    report_check = sub.add_parser("inspect-saved-report", help="Read a supported saved summary only; no collection or archive writes")
    report_check.add_argument("--source", type=Path, required=True)
    report_check.add_argument("--adapter", choices=("auto", "cyberpunk_benchmark_summary", "presentmon_gui_stats"), default="auto")
    report_import = sub.add_parser("import-saved-reports", help="Create a new private immutable summary bundle; never run a game or provider")
    report_import.add_argument("--baseline", type=Path, action="append", default=[])
    report_import.add_argument("--a", type=Path, action="append", default=[])
    report_import.add_argument("--output-directory", type=Path, required=True)
    report_import.add_argument("--title", default="Saved reports")
    report_import.add_argument("--question", default="Compare saved provider summaries.")
    report_import.add_argument("--factor", default="changed_configuration")
    sessions = sub.add_parser("session", help="Offline saved-data coordination and journal evidence only")
    session_sub = sessions.add_subparsers(dest="session_action", required=True)
    session_sub.add_parser("capabilities")
    session_inspect = session_sub.add_parser("inspect", help="Inspect a journal without changing it")
    session_inspect.add_argument("--source", type=Path, required=True)
    recovering = session_sub.add_parser("recover", help="Copy verified prefix into a new evidence-only journal")
    recovering.add_argument("--source", type=Path, required=True)
    recovering.add_argument("--output", type=Path, required=True)
    recovering.add_argument("--expected-sha256", required=True)
    evidence = sub.add_parser("saved-evidence", help="Selected saved evidence only; no live logs, games or recording")
    evidence_sub = evidence.add_subparsers(dest="evidence_action", required=True)
    for command in ("inspect", "packet"):
        evidence_command = evidence_sub.add_parser(command)
        evidence_command.add_argument("--source", type=Path, required=True, action="append")
        evidence_command.add_argument("--expected-sha256", action="append", help="One hash per source, in the same order")
        if command == "packet":
            evidence_command.add_argument("--output-directory", type=Path, required=True)
    workflow = sub.add_parser("workflow", help="Data-only dry-run and rollback planning; never execute")
    workflow_sub = workflow.add_subparsers(dest="workflow_action", required=True)
    for command in ("inspect", "export"):
        workflow_command = workflow_sub.add_parser(command)
        workflow_command.add_argument("--source", type=Path, required=True)
        workflow_command.add_argument("--expected-sha256", required=command == "export")
        if command == "export":
            workflow_command.add_argument("--output", type=Path, required=True)
    readiness = sub.add_parser("readiness", help="Offline declared provider health and editable scenarios; no runner")
    readiness_sub = readiness.add_subparsers(dest="readiness_action", required=True)
    for command in ("inspect", "save-scenario"):
        contract = readiness_sub.add_parser(command)
        contract.add_argument("--source", type=Path, required=True)
        contract.add_argument("--expected-sha256", required=command == "save-scenario")
        if command == "save-scenario":
            contract.add_argument("--draft", type=Path, required=True)
            contract.add_argument("--output", type=Path, required=True)
    for command in ("inspect-report", "compare", "inspect-evidence", "inspect-workflow", "inspect-readiness"):
        command_parser = session_sub.add_parser(command, help="One explicit saved-data action in a new journal; no replay")
        command_parser.add_argument("--source", type=Path, required=True)
        command_parser.add_argument("--journal", type=Path, required=True, help="New private JSONL journal; never overwrite")
        command_parser.add_argument("--expected-sha256", required=True)
        command_parser.add_argument("--label", default="Offline saved-data inspection")
        command_parser.add_argument("--lifetime-seconds", type=int, default=900)
        if command == "inspect-report":
            command_parser.add_argument("--adapter", choices=("auto", "cyberpunk_benchmark_summary", "presentmon_gui_stats"), default="auto")
        elif command == "compare":
            command_parser.add_argument("--metric")
        elif command == "inspect-evidence":
            command_parser.add_argument("--adapter", choices=("auto", "hub_journal", "opaque_text", "windows_event_xml"), default="auto")
    args = parser.parse_args(argv)
    if args.action == "readiness":
        try:
            api = load_catalog_module("GameToolReadiness")
            if args.readiness_action == "inspect":
                result = api.inspect_source(args.source, expected_sha256=args.expected_sha256)
            else:
                core = load_catalog_module("GameToolCoordinator")
                raw, snapshot = core._capture(args.draft, api.MAX_SOURCE_BYTES)
                result = api.save_scenario(args.source, args.output, raw, args.expected_sha256)
            print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))
            return 3 if result.get("status") == "BLOCKED" else 0
        except Exception:
            print(json.dumps({"valid": False, "error_code": "READINESS_REFUSED", "execution": "none",
                "error": "Offline contract request refused; originals retained and no live action performed."}))
            return 2
    if args.action == "workflow":
        try:
            api = load_catalog_module("GameToolWorkflow")
            result = api.inspect_source(args.source, expected_sha256=args.expected_sha256) if args.workflow_action == "inspect" else api.export_plan(
                args.source, args.output, expected_sha256=args.expected_sha256)
            print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))
            return 3 if result.get("status") == "BLOCKED" else 0
        except Exception:
            print(json.dumps({"valid": False, "error_code": "WORKFLOW_REFUSED", "execution": "none",
                "error": "Offline recipe/plan request refused; originals retained and no live action performed."}))
            return 2
    if args.action == "saved-evidence":
        try:
            api = load_catalog_module("GameToolCrashEvidence")
            hashes = args.expected_sha256
            if hashes is not None and len(hashes) != len(args.source):
                raise ValueError("One expected hash per source required")
            assignments = [{"path": path, "expected_sha256": None if hashes is None else hashes[index]}
                           for index, path in enumerate(args.source)]
            result = api.build_packet(assignments) if args.evidence_action == "inspect" else \
                api.export_packet(assignments, args.output_directory)
            print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
            return 0
        except (OSError, ValueError, TypeError, ImportError, RecursionError, SyntaxError):
            print(json.dumps({"valid": False, "error_code": "SAVED_EVIDENCE_REFUSED", "execution": "none",
                "error": "Saved evidence could not be inspected/exported safely; originals retained, no live action taken."}))
            return 2
    if args.action == "session":
        coordinator = None
        try:
            if args.session_action == "capabilities":
                result = load_catalog_module("GameToolCoordinator").capabilities()
            elif args.session_action == "inspect":
                result = journal_summary(load_catalog_module("GameToolJournal").inspect_journal(args.source))
            elif args.session_action == "recover":
                result = load_catalog_module("GameToolJournal").recover_journal(
                    args.source, args.output, expected_sha256=args.expected_sha256)
            else:
                core = load_catalog_module("GameToolCoordinator")
                coordinator = core.Coordinator(owner="Hub CLI", lifetime_seconds=args.lifetime_seconds)
                coordinator.start(args.journal, label=args.label)
                if args.session_action == "inspect-report":
                    action_result = coordinator.inspect_saved_report(args.source, adapter=args.adapter,
                        expected_sha256=args.expected_sha256)
                elif args.session_action == "inspect-evidence":
                    action_result = coordinator.inspect_crash_evidence(args.source, adapter=args.adapter,
                        expected_sha256=args.expected_sha256)
                elif args.session_action == "inspect-workflow":
                    action_result = coordinator.inspect_workflow(args.source, expected_sha256=args.expected_sha256)
                elif args.session_action == "inspect-readiness":
                    action_result = coordinator.inspect_readiness(args.source, expected_sha256=args.expected_sha256)
                else:
                    action_result = coordinator.inspect_comparison(args.source, metric=args.metric,
                        expected_sha256=args.expected_sha256)
                finished = coordinator.finish()
                if finished.get("state") != "finished":
                    raise ValueError("Session completion was not acknowledged")
                result = {"action_result": action_result, "session": finished}
            print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
            if args.session_action == "inspect" and not result.get("valid"):
                return 3
            return 3 if result.get("action_result", {}).get("status") == "BLOCKED" else 0
        except (OSError, ValueError, TypeError, ImportError, RecursionError, SyntaxError) as error:
            # Loader/OS exceptions can contain private install/source locators.
            # Export only a code-owned reason token, never arbitrary error text.
            code = getattr(error, "code", None)
            if not isinstance(code, str) or not code or not all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ_" for c in code):
                code = "SESSION_REQUEST_FAILED"
            print(json.dumps({"valid": False, "error_code": code,
                "error": "Offline session request failed; inspect retained evidence and verify the selected source or optional modules.",
                "execution": "offline_only", "replay_allowed": False}, ensure_ascii=False))
            return 2
        finally:
            if coordinator is not None:
                try:
                    coordinator.close()
                except (OSError, ValueError):
                    # A failed/poisoned journal is retained as incomplete evidence.
                    # Do not mask the already-reported action failure or replay it.
                    pass
    if args.action in ("inspect-saved-report", "import-saved-reports"):
        # Explicit saved-data routes remain independent of registry/readers,
        # profile writes, runtime FG inspection and launch/capture controls.
        try:
            importer = load_catalog_module("GameToolReportImport")
            if args.action == "inspect-saved-report":
                result = importer.inspect_report(args.source, adapter=args.adapter)
                # Original locators are private, never part of portable preview.
                result.pop("private_source", None)
                result["execution"] = "none"
                print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
                return 0
            assignments = [{"path": path, "case": case} for case in ("baseline", "a")
                           for path in getattr(args, case)]
            result = importer.import_bundle(assignments, args.output_directory,
                title=args.title, question=args.question, factor=args.factor)
            print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
            # A BLOCKED comparison is a successful archive/import, not a
            # successful performance comparison. Preserve the explicit verdict.
            return 3 if result.get("status") == "BLOCKED" else 0
        except (OSError, ValueError, TypeError, ImportError, RecursionError, SyntaxError) as error:
            print(json.dumps({"valid": False, "error": str(error), "execution": "none"}, ensure_ascii=False))
            return 2
    if args.action == "compare-report":
        # Offline analysis does not load the executable registry or live providers,
        # and cannot return a trusted runtime-FG receipt to the Catalog planner.
        try:
            core = load_catalog_module("GameToolComparison")
            dataset = core.load_dataset(args.source)
            result = core.compare_dataset(dataset, args.metric)
            if args.output:
                receipt = core.export_report(args.source, args.output, format=args.format,
                    expected_sha256=dataset["_source"]["sha256"], metric_id=args.metric)
                result["export_receipt"] = receipt
            print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
            return 3 if result.get("status") == "BLOCKED" else 0
        except (OSError, ValueError, TypeError, ImportError, RecursionError, SyntaxError) as error:
            print(json.dumps({"valid": False, "error": str(error), "execution": "none"}, ensure_ascii=False))
            return 2
    if args.action == "catalog":
        # Browse routes read only authored catalog data. Explicit FG checks and
        # in-game plans additionally observe FG sources, never private registry/readers.
        try:
            service = new_catalog_service(args.catalog_file)
            if args.catalog_action == "status":
                result = service.reload()
            elif args.catalog_action == "list":
                result = {"nodes": service.list_nodes(**{field: getattr(args, field) for field in
                    ("kind", "category", "game", "status", "installation", "relationship", "search", "sort")}),
                    "revision": service.revision, "execution": "none"}
            elif args.catalog_action == "show":
                result = service.details(args.id)
            elif args.catalog_action == "fg-preflight":
                result = service.fg_preflight(args.scope, game=args.game, executable=args.executable,
                    native_settings_path=args.native_settings)
            else:
                result = service.prepare_plan(args.scope, game=args.game, factors=args.factor,
                    executable=args.executable, native_settings_path=args.native_settings)
            print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
            return 3 if result.get("status") in {"blocked", "BLOCKED"} else 0
        except (OSError, ValueError, TypeError, ImportError, RecursionError, SyntaxError) as error:
            print(json.dumps({"valid": False, "error": str(error), "execution": "none"}, ensure_ascii=False))
            return 2
    registry = args.data_dir / "tools.json"
    tools = load_tools(registry)
    if args.action == "inspect":
        print(json.dumps(inspect(tools), indent=2, allow_nan=False))
    elif args.action == "snapshot":
        exclusive_json(args.output, inspect(tools))
        print(str(args.output))
    elif args.action == "import-report":
        print(import_report(args.source, args.data_dir / "imports", args.provider, args.definition))
    else:
        draft = read_form_file(args.form_file) if args.form_file else None
        options = {"overlay_page": args.overlay_page}
        if args.unified_install is not None:
            options["unified_install"] = args.unified_install
        if args.interface_preview is not None:
            options["interface_preview"] = args.interface_preview
        gui(args.data_dir, draft, args.catalog_file, **options)


def read_form_file(path):
    if path.stat().st_size > 65536:
        raise ValueError("Form draft exceeds the 64 KiB limit")
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or set(value) - {"report", "tool"}:
        raise ValueError("Form draft accepts only report and tool fields")
    for section, keys in (("report", {"path", "provider", "definition"}), ("tool", {"path", "name"})):
        fields = value.get(section, {})
        if not isinstance(fields, dict) or set(fields) - keys or any(not isinstance(v, str) for v in fields.values()):
            raise ValueError("Invalid form draft fields; actions and confirmations cannot be prefilled")
    return value


if __name__ == "__main__":
    sys.exit(main())
