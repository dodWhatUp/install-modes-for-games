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

VERSION = "0.1.0"
HEADER = struct.Struct("<5Ii2I")
ENTRY_MIN = 1324
MAX_MAP = 16 * 1024 * 1024


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
             "process": "PresentMon-2.6.0-x64.exe", "open_allowed": False}]


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
            "afterburner_configuration": configuration(tools), "afterburner": read_afterburner()}


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
               "metrics_recalculated": False, "run_association": None}
    exclusive_json(folder / "receipt.json", receipt)
    if not unchanged:
        raise ValueError("Source changed during import. Copy and failure receipt retained; close logging before retrying")
    return folder


def guide_text():
    return """Learning mode: no benchmark or capture controls are enabled here.

Tools: refresh installation/running status, select a tool and open its existing interface. Windows approvals remain manual. PresentMon console is inventory-only because launching it can start collection.

Sensors: Refresh connection reads MSI Afterburner's existing MAHM shared memory with read access only. Names, units and values come from Afterburner. The helper does not calculate FPS lows or latency. Live counters have no associated game/run; they are not benchmark results. Auto refresh is optional and does not save a time series.

Reports: choose a report exported by an existing program. Import preserves the original bytes plus provider, definition and SHA-256. No metrics are recalculated. Imports remain private on this computer. Current Afterburner HML is archived as an opaque file; text/CSV conversion is not implemented.

User control: register another installed EXE through Add tool. Configure each application's sensor selection, overlay and shortcuts in its own settings. This helper does not write Afterburner/RTSS profiles, overclock settings or game settings. It supplies no global hotkeys, input injection, remote server, startup task or automatic uploads.

Agent control: inspect and snapshot commands return structured JSON; import-report archives an explicitly selected report. Future adapters can import a provider's summaries with original definitions, frame classes and latency endpoints. Recording stays deferred until explicitly requested.

Closing this panel stops its optional refresh. It does not close other programs or stop an unrelated existing collector.
"""


def gui(data_dir):
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, simpledialog
    data_dir.mkdir(parents=True, exist_ok=True)
    registry = data_dir / "tools.json"
    tools = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else default_tools()
    root = tk.Tk()
    root.title(f"Game Tool Hub {VERSION} — Learning mode")
    root.geometry("1040x700")
    root.minsize(850, 560)
    status = tk.StringVar(value="Ready")
    ttk.Label(root, textvariable=status, wraplength=1000).pack(side="bottom", anchor="w", fill="x", padx=22, pady=12)
    ttk.Label(root, text="Game Tool Hub", font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=22, pady=(18, 3))
    ttk.Label(root, text="Connect tools • Read their values • Organize reports", font=("Segoe UI", 11)).pack(anchor="w", padx=22)
    tk.Label(root, text="LEARNING MODE   •   Tool connections and report management", bg="#fff0bf", fg="#604800", padx=12, pady=10).pack(fill="x", padx=22, pady=14)
    tabs = ttk.Notebook(root)
    tabs.pack(fill="both", expand=True, padx=22)
    tool_tab, sensor_tab, report_tab, guide_tab = [ttk.Frame(tabs, padding=12) for _ in range(4)]
    for tab, name in zip((tool_tab, sensor_tab, report_tab, guide_tab), ("Tools", "Sensors", "Reports", "How to use")):
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
    tool_tree = table(tool_tab, ("Tool", "Installed", "Running", "Version"))
    config_info = tk.StringVar()
    ttk.Label(tool_tab, textvariable=config_info, wraplength=900).pack(anchor="w", pady=12)
    sensor_bar = ttk.Frame(sensor_tab)
    sensor_bar.pack(fill="x", pady=(0, 10))
    connection = tk.StringVar(value="Not checked")
    ttk.Label(sensor_bar, textvariable=connection).pack(side="right")
    sensor_tree = table(sensor_tab, ("Source", "Value", "Unit", "Scope"))
    ttk.Label(sensor_tab, text="Values supplied by Afterburner. No game/run association; no statistics calculated here.").pack(anchor="w", pady=10)
    auto = tk.BooleanVar(value=False)

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
            cfg = state["afterburner_configuration"]
            config_info.set(f'Saved profile: logging {"off" if cfg.get("EnableLog") == "0" else "on / unknown"}; begin/end recording hotkeys: {cfg.get("BeginRecordHotkey", "unknown")} / {cfg.get("EndRecordHotkey", "unknown")}. Profiles are read only.')
            status.set(reading.get("reason", "Refreshed. Recording controls remain unavailable in learning mode."))
        except Exception as error:
            status.set(f"Connection error: {error}")

    def open_tool():
        selected = tool_tree.selection()
        if not selected:
            return
        tool = next(t for t in tools if t["id"] == selected[0])
        if tool["id"] == "presentmon-console" or not tool.get("open_allowed", False):
            messagebox.showinfo("Inventory only", "This console collector cannot be launched in learning mode.")
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
        path = filedialog.askopenfilename(title="Select an installed tool", filetypes=[("Application", "*.exe")])
        if not path:
            return
        label = simpledialog.askstring("Tool name", "Name shown in this panel:", initialvalue=Path(path).stem)
        if not label:
            return
        if not messagebox.askyesno("Register installed tool", "Does this program open a normal interface without starting collection? Register only interface programs here."):
            return
        tools.append({"id": uuid.uuid4().hex, "name": label, "path": path, "process": Path(path).name, "open_allowed": True})
        save_registry()
        refresh()

    def save_registry():
        if registry.exists():
            backup = data_dir / ("tools-before-" + uuid.uuid4().hex + ".json")
            backup.write_bytes(registry.read_bytes())
        temporary = data_dir / ("tools-" + uuid.uuid4().hex + ".tmp")
        temporary.write_text(json.dumps(tools, indent=2), encoding="utf-8")
        os.replace(temporary, registry)

    def save_snapshot():
        path = filedialog.asksaveasfilename(title="Save connection snapshot", initialdir=str(data_dir), defaultextension=".json")
        if path:
            try:
                exclusive_json(path, state)
                status.set("Connection snapshot saved privately. No capture was started.")
            except Exception as error:
                messagebox.showerror("Save snapshot", str(error))

    def copy_summary():
        summary = {"observed_utc": state.get("observed_utc"), "mode": "learning", "capture_started": False,
                   "tools": [{k: t[k] for k in ("name", "installed", "running", "version")} for t in state.get("tools", [])],
                   "afterburner_state": state.get("afterburner", {}).get("state"),
                   "source_count": len(state.get("afterburner", {}).get("rows", []))}
        root.clipboard_clear()
        root.clipboard_append(json.dumps(summary, indent=2))
        status.set("Copied tool status without local paths; paste wherever you choose.")

    def import_file():
        path = filedialog.askopenfilename(title="Select an existing tool report", filetypes=[("Reports", "*.csv *.json *.txt *.hml")])
        if not path:
            return
        provider = simpledialog.askstring("Report source", "Which program produced this report?")
        if not provider:
            return
        definition = simpledialog.askstring("Metric definitions", "Source definitions / version, if known:", initialvalue="Unknown; retain provider documentation")
        if definition is None:
            return
        try:
            folder = import_report(path, data_dir / "imports", provider, definition)
            report_list.insert("end", f"{provider}: {Path(path).name} — {folder.name}")
            status.set("Original report and receipt archived privately. Metrics were not recalculated.")
        except Exception as error:
            messagebox.showerror("Import report", str(error))

    ttk.Button(toolbar, text="Refresh connection", command=refresh).pack(side="left", padx=(0, 6))
    ttk.Button(toolbar, text="Open selected tool", command=open_tool).pack(side="left", padx=6)
    ttk.Button(toolbar, text="Add installed tool", command=add_tool).pack(side="left", padx=6)
    ttk.Button(toolbar, text="Copy status", command=copy_summary).pack(side="left", padx=6)
    ttk.Button(toolbar, text="Save snapshot", command=save_snapshot).pack(side="left", padx=6)
    ttk.Button(sensor_bar, text="Refresh connection", command=refresh).pack(side="left")
    ttk.Checkbutton(sensor_bar, text="Auto refresh every 5 seconds", variable=auto).pack(side="left", padx=12)
    ttk.Label(report_tab, text="Import an existing program's report. Original values and definitions are retained.").pack(anchor="w", pady=8)
    ttk.Button(report_tab, text="Import report…", command=import_file).pack(anchor="w", pady=10)
    report_list = tk.Listbox(report_tab)
    report_list.pack(fill="both", expand=True)
    for receipt in sorted((data_dir / "imports").glob("*/receipt.json")):
        report_list.insert("end", receipt.parent.name)
    text = tk.Text(guide_tab, wrap="word", font=("Segoe UI", 11), padx=10, pady=10, height=12)
    text.insert("1.0", guide_text())
    text.configure(state="disabled")
    text.pack(fill="both", expand=True)

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
    tools = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else default_tools()
    if args.action == "inspect":
        print(json.dumps(inspect(tools), indent=2, allow_nan=False))
    elif args.action == "snapshot":
        exclusive_json(args.output, inspect(tools))
        print(str(args.output))
    elif args.action == "import-report":
        print(import_report(args.source, args.data_dir / "imports", args.provider, args.definition))
    else:
        gui(args.data_dir)


if __name__ == "__main__":
    main()
