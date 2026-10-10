"""Local tool coordinator. Reads existing tools; never starts a capture."""
from __future__ import annotations

import argparse
import configparser
import csv
import ctypes
import hashlib
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

VERSION = "0.2.0"
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

User control: Add tool shows a local path/name form and an explicit interface-only confirmation. Reports accepts a local file path plus program and definitions; Browse is optional. Save snapshot creates a new immutable file inside the private data folder; its location appears in the status bar. Configure each application's sensor selection, overlay and shortcuts in its own settings. This helper does not write Afterburner/RTSS profiles, overclock settings or game settings. It supplies no global hotkeys, input injection, remote server, startup task or automatic uploads.

Agent control: inspect and snapshot commands return structured JSON; import-report archives an explicitly selected report. Future adapters can import a provider's summaries with original definitions, frame classes and latency endpoints. Recording stays deferred until explicitly requested.

Local shortcuts (only while this panel is focused): Ctrl+1 Tools, Ctrl+2 Sensors, Ctrl+3 RTSS, Ctrl+4 Reports, Ctrl+5 How to use; Ctrl+R Refresh, Ctrl+O Open selected tool, Ctrl+A Add tool, Ctrl+C Copy status, Ctrl+S Save snapshot, Ctrl+I Import report, Ctrl+E Open selected original. Sensors/RTSS: Ctrl+T toggles optional refresh. Alt+F4 closes only this panel. Collectors remain blocked even if registered under another name.

Closing this panel stops its optional refresh. It does not close other programs or stop an unrelated existing collector.
"""


def gui(data_dir, draft=None):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    data_dir.mkdir(parents=True, exist_ok=True)
    registry = data_dir / "tools.json"
    tools = load_tools(registry)
    draft = draft or {}
    root = tk.Tk()
    root.title(f"Game Tool Hub {VERSION} — Learning mode")
    root.geometry("1120x720")
    root.minsize(1000, 600)
    status = tk.StringVar(value="Ready")
    ttk.Label(root, textvariable=status, wraplength=1000).pack(side="bottom", anchor="w", fill="x", padx=22, pady=12)
    ttk.Label(root, text="Game Tool Hub", font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=22, pady=(18, 3))
    ttk.Label(root, text="Connect tools • Read their values • Organize reports", font=("Segoe UI", 11)).pack(anchor="w", padx=22)
    tk.Label(root, text="LEARNING MODE   •   Tool connections and report management", bg="#fff0bf", fg="#604800", padx=12, pady=10).pack(fill="x", padx=22, pady=14)
    tabs = ttk.Notebook(root)
    tabs.pack(fill="both", expand=True, padx=22)
    tool_tab, sensor_tab, rtss_tab, report_tab, guide_tab = [ttk.Frame(tabs, padding=12) for _ in range(5)]
    for tab, name in zip((tool_tab, sensor_tab, rtss_tab, report_tab, guide_tab), ("Tools", "Sensors", "RTSS", "Reports", "How to use")):
        tabs.add(tab, text=name)
    state = {}

    def table(parent, columns):
        box = ttk.Frame(parent)
        box.pack(fill="both", expand=True)
        tree = ttk.Treeview(box, columns=columns, show="headings")
        for column in columns:
            tree.heading(column, text=column)
            tree.column(column, width=150, minwidth=80)
        tree.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(box, command=tree.yview)
        scroll.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scroll.set)
        return tree

    toolbar = ttk.Frame(tool_tab)
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

    ttk.Button(toolbar, text="Refresh connection", command=refresh).pack(side="left", padx=(0, 6))
    ttk.Button(toolbar, text="Open selected tool", command=open_tool).pack(side="left", padx=6)
    ttk.Button(toolbar, text="Add installed tool", command=add_tool).pack(side="left", padx=6)
    ttk.Button(toolbar, text="Copy status", command=copy_summary).pack(side="left", padx=6)
    ttk.Button(toolbar, text="Save snapshot", command=save_snapshot).pack(side="left", padx=6)
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

    shortcuts = {}
    for index, tab in enumerate((tool_tab, sensor_tab, rtss_tab, report_tab, guide_tab), 1):
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
        if key in ("a", "c") and isinstance(focused, (ttk.Entry, tk.Text)):
            return
        if key in shortcuts:
            shortcuts[key]()
            return "break"
    root.bind("<Control-KeyPress>", handle_shortcut)

    def tick():
        if auto.get():
            refresh()
        root.after(5000, tick)

    refresh()
    root.after(5000, tick)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GameToolHub")
    parser.add_argument("--form-file", type=Path, help="Optional local JSON draft; prefill forms only, never perform an action")
    sub = parser.add_subparsers(dest="action")
    sub.add_parser("inspect")
    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--output", type=Path, required=True)
    importing = sub.add_parser("import-report")
    importing.add_argument("--source", type=Path, required=True)
    importing.add_argument("--provider", required=True)
    importing.add_argument("--definition", default="Unknown; retain provider documentation")
    args = parser.parse_args()
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
        gui(args.data_dir, draft)


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
    main()
