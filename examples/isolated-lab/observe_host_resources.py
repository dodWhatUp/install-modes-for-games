"""Read only owned QEMU resource counters; never inspect host app data or input."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
import time
from lab import Lab, available_memory_mb, process_identity, stamp, write_json


def counters(pid):
    class Memory(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (key, ctypes.c_size_t) for key in ("peak_rss", "rss", "peak_paged", "paged", "peak_nonpaged", "nonpaged", "pagefile", "peak_pagefile", "private")]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    api = ctypes.WinDLL("psapi", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    api.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]
    handle = kernel.OpenProcess(0x0410, False, pid)
    if not handle:
        raise OSError(ctypes.get_last_error(), "Cannot read owned process counters")
    try:
        mem = Memory()
        mem.cb = ctypes.sizeof(mem)
        creation, exited, kernel_time, user_time = [wintypes.FILETIME() for _ in range(4)]
        if not api.GetProcessMemoryInfo(handle, ctypes.byref(mem), mem.cb) or not kernel.GetProcessTimes(handle, *[ctypes.byref(t) for t in (creation, exited, kernel_time, user_time)]):
            raise OSError(ctypes.get_last_error(), "Cannot read owned resource data")
        cpu = sum((t.dwHighDateTime << 32) | t.dwLowDateTime for t in (kernel_time, user_time)) / 10000000
        return {"cpu_seconds": cpu, "rss_bytes": mem.rss, "peak_rss_bytes": mem.peak_rss,
                "private_bytes": mem.private, "host_available_mb": available_memory_mb()}
    finally:
        kernel.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seconds", type=int, default=1200)
    args = parser.parse_args()
    if not 1 <= args.seconds <= 3600:
        raise ValueError("Observation duration must be bounded")
    lab = Lab(args.config)
    state = json.loads(lab.state_path("linux").read_text())
    identity = state["identity"]
    if process_identity(state["pid"]) != identity:
        raise RuntimeError("Selected QEMU identity changed")
    first, started = counters(state["pid"]), time.monotonic()
    report = {"scope": "read-only counters of lab-owned QEMU, no host input or app content",
              "samples": 0, "cpu_logical_processors": os.cpu_count(), "peak_rss_bytes": 0,
              "min_host_available_mb": first["host_available_mb"], "outcome": "RUNNING"}
    out = lab.artifacts / ("host-resources-" + stamp() + ".json")
    while True:
        if process_identity(state["pid"]) != identity:
            raise RuntimeError("QEMU stopped or changed identity during observation")
        sample = counters(state["pid"])
        elapsed = time.monotonic() - started
        report.update(samples=report["samples"] + 1, elapsed_seconds=round(elapsed, 2),
                      peak_rss_bytes=max(report["peak_rss_bytes"], sample["rss_bytes"]),
                      min_host_available_mb=min(report["min_host_available_mb"], sample["host_available_mb"]))
        if elapsed > 0.5:
            report["average_cpu_percent_of_host"] = round(100 * (sample["cpu_seconds"] - first["cpu_seconds"]) / elapsed / os.cpu_count(), 2)
        if elapsed >= args.seconds:
            report["outcome"] = "PASS"
        write_json(out, report)
        if report["outcome"] == "PASS":
            print(json.dumps(report | {"receipt": str(out)}), flush=True)
            break
        time.sleep(min(10, args.seconds - elapsed))


if __name__ == "__main__":
    main()
