"""Read-only, experimental Azeron 2.0.2 layer-event follower.

No hooks, HID writes, native IPC commands, debug-port activation or remapping.
An event-tracked state is NOT a fresh native snapshot or gameplay acceptance.
Only new, timely native log transitions can establish state. Old logs never do.
"""
from __future__ import annotations
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time

VERSION = "0.1.3"
SUPPORTED_VERSION = "2.0.2.442"
INTERVAL = 0.02
MAX_BATCH = 256 * 1024
MAX_LINE = 8192
TRANSITION = re.compile(r"^(?:Switch layer on toggle hold: |Switch layer: |active profile reported: )([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})$", re.I)


def native_identity(exe):
    """Read process path/creation identity; presence alone never selects a layer."""
    if os.name != "nt":
        return None
    from ctypes import wintypes as w
    class Entry(ctypes.Structure):
        _fields_ = [("dwSize", w.DWORD), ("cntUsage", w.DWORD), ("pid", w.DWORD),
                    ("heap", ctypes.c_size_t), ("module", w.DWORD), ("threads", w.DWORD),
                    ("parent", w.DWORD), ("priority", w.LONG), ("flags", w.DWORD),
                    ("name", w.WCHAR * 260)]
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = w.HANDLE
    kernel.Process32FirstW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [w.HANDLE, ctypes.POINTER(Entry)]
    kernel.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]; kernel.OpenProcess.restype = w.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)]
    kernel.GetProcessTimes.argtypes = [w.HANDLE, *([ctypes.POINTER(w.FILETIME)] * 4)]
    kernel.CloseHandle.argtypes = [w.HANDLE]
    snap = kernel.CreateToolhelp32Snapshot(2, 0)
    if snap in (None, ctypes.c_void_p(-1).value):
        return None
    rows = []
    try:
        entry = Entry(); entry.dwSize = ctypes.sizeof(entry)
        ok = kernel.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            if entry.name.casefold() == exe.name.casefold():
                handle = kernel.OpenProcess(0x1000, False, entry.pid)
                if handle:
                    try:
                        buf = ctypes.create_unicode_buffer(32768); size = w.DWORD(len(buf))
                        stamps = [w.FILETIME() for _ in range(4)]
                        if kernel.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)) and \
                                os.path.normcase(buf.value) == os.path.normcase(str(exe)) and \
                                kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in stamps)):
                            stamp = stamps[0].dwLowDateTime | stamps[0].dwHighDateTime << 32
                            rows.append((stamp, entry.pid, entry.parent))
                    finally:
                        kernel.CloseHandle(handle)
            ok = kernel.Process32NextW(snap, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snap)
    # Multiple independent roots are ambiguous; Electron children are not roots.
    pids = {row[1] for row in rows}
    roots = [r for r in rows if r[2] not in pids]
    return tuple(roots[0][:2]) if len(roots) == 1 else None


class LayerFollower:
    def __init__(self, log, profiles, *, executable=None, version=SUPPORTED_VERSION,
                 probe=None, clock=time.monotonic, wall=time.time):
        self.log, self.profiles = Path(log), Path(profiles)
        self.executable = Path(executable) if executable else None
        self.version = version
        self.probe = probe or (lambda: native_identity(self.executable) if self.executable else None)
        self.clock, self.wall = clock, wall
        self.identity = None; self.file_identity = None; self.offset = None
        self.pending = b""; self.profile = None; self.event_at = None; self.momentary = False
        self._lock = threading.Lock(); self._stop = threading.Event(); self.thread = None
        self.result = self.unavailable("Waiting for a fresh Azeron layer event")

    def unavailable(self, reason):
        return {"provider": "Azeron native log (experimental)", "at": self.clock(),
                "available": False, "state": "Unknown", "reason": reason}

    def clear(self, reason):
        self.profile = None; self.event_at = None; self.momentary = False
        self.result = self.unavailable(reason)

    def poll(self, manifest):
        """One bounded read; for fixtures or the owned background thread, not Tk."""
        with self._lock:
            try:
                if self.version != SUPPORTED_VERSION:
                    self.clear("Unsupported Azeron version; explicit selection remains available"); return
                identity = self.probe()
                if identity is None:
                    self.identity = None; self.offset = None
                    self.clear("Azeron stopped, unavailable or ambiguous"); return
                stat = self.log.stat(); file_id = (stat.st_dev, stat.st_ino)
                if identity != self.identity or file_id != self.file_identity or self.offset is None or stat.st_size < self.offset:
                    self.identity, self.file_identity, self.offset = identity, file_id, stat.st_size
                    self.pending = b""
                    self.clear("Waiting for a fresh Azeron layer event; historical log ignored"); return
                if stat.st_size - self.offset > MAX_BATCH:
                    self.offset = stat.st_size; self.pending = b""
                    self.clear("Native event backlog; refusing an incomplete transition stream"); return
                with self.log.open("rb") as stream:
                    stream.seek(self.offset); data = stream.read(MAX_BATCH); self.offset = stream.tell()
                chunks = (self.pending + data).split(b"\n"); self.pending = chunks.pop()
                if len(self.pending) > MAX_LINE:
                    self.pending = b""; self.clear("Native event line too large"); return
                for raw in chunks:
                    if not raw.strip():
                        continue
                    if len(raw) > MAX_LINE:
                        self.clear("Native event line too large"); continue
                    try:
                        event = json.loads(raw); message = event["message"]
                        if not isinstance(message, str): raise ValueError()
                        stamp = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00"))
                        if stamp.tzinfo is None: raise ValueError()
                        event_time = stamp.timestamp()
                    except (ValueError, KeyError, TypeError, UnicodeError):
                        self.clear("Malformed native event; layer unknown"); continue
                    match = TRANSITION.fullmatch(message)
                    if match:
                        # Native millisecond timestamps/float rounding can lead
                        # receipt by a few ms, but real future/delayed data is refused.
                        if not -0.05 <= self.wall() - event_time <= 0.5 or \
                                (self.event_at is not None and event_time < self.event_at):
                            self.clear("Delayed or out-of-order native layer event"); continue
                        self.profile, self.event_at = match[1].lower(), event_time
                        self.momentary = message.startswith("Switch layer on toggle hold: ")
                    elif re.search(r"disconnect|\b(?:hardware|software) mode\b|profile switch|switch.*profile|switch layer|active.*profile|migration|device connected|\bsleep\b", message, re.I):
                        # A transition we cannot interpret must not retain an old map.
                        self.clear("Native context changed; waiting for a fresh layer event")
                if self.profile is None:
                    return
                matches = [(k, l) for k in manifest["keymaps"] for l in k["layers"]
                           if l["profile_id"].lower() == self.profile]
                if not matches:
                    self.clear("Native layer has no unambiguous registered asset revision"); return
                paths = list(self.profiles.glob("*/ProfileStorage/profile_" + self.profile + ".json"))
                if len(paths) != 1 or paths[0].is_symlink():
                    self.clear("Missing or ambiguous native profile file"); return
                if paths[0].stat().st_size > 2 * 1024 * 1024:
                    self.clear("Native profile too large"); return
                before = paths[0].stat(); raw = paths[0].read_bytes(); after = paths[0].stat()
                if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != \
                        (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    self.clear("Native profile changed during read; layer unknown"); return
                digest = hashlib.sha256(raw).hexdigest()
                matches = [(k, l) for k, l in matches if l["profile_sha256"] == digest]
                if not matches or json.loads(raw).get("id", "").lower() != self.profile:
                    self.clear("Native profile revision changed; refusing stale labels"); return
                identities = {(l["profile_sha256"], k["outputs_sha256"]) for k, l in matches}
                if len(identities) != 1:
                    self.clear("Current native profile has ambiguous registered outputs; refusing stale labels"); return
                self.result = {"provider": "Azeron native log (experimental)", "at": self.clock(), "available": True,
                               "state": "Event-tracked", "profile_id": self.profile, "profile_sha256": digest,
                               "outputs_sha256": matches[0][0]["outputs_sha256"], "event_utc": self.event_at,
                               "momentary_layer": self.momentary,
                               "reason": "Native layer event tracked; not a fresh native snapshot"}
            except (OSError, ValueError, KeyError, TypeError):
                self.offset = None; self.pending = b""; self.clear("Native reader unavailable; layer unknown")

    def snapshot(self):
        # Poll publishes a new dict atomically; do not hold Tk on native I/O.
        return dict(self.result)

    def start(self, manifest):
        if self.thread and self.thread.is_alive():
            return
        self._stop.clear()
        def run():
            while not self._stop.is_set():
                try:
                    self.poll(manifest())
                except Exception:
                    with self._lock:
                        self.clear("Native reader stopped on an unsupported state")
                    break
                self._stop.wait(INTERVAL)
        self.thread = threading.Thread(target=run, name="AzeronLayerReadOnly", daemon=True)
        self.thread.start()

    def stop(self):
        self._stop.set()
        if self.thread:
            self.thread.join(timeout=1)
        self.thread = None
        with self._lock:
            self.identity = None; self.offset = None; self.clear("Azeron layer following stopped")


def installed_follower():
    """No scan of browser/account stores; existing native paths only."""
    base = Path(os.environ.get("APPDATA", "")) / "Azeron Software"
    exe = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Azeron/Azeron Software/Azeron Software.exe"
    version = None
    try:
        # Native VERSIONINFO read is diagnostic only; no app command is sent.
        if os.name == "nt":
            lib = ctypes.WinDLL("version", use_last_error=True)
            lib.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p]
            size = lib.GetFileVersionInfoSizeW(str(exe), None)
            if 0 < size < 1024 * 1024:
                buf = ctypes.create_string_buffer(size)
                lib.GetFileVersionInfoW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
                lib.VerQueryValueW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint32)]
                pointer = ctypes.c_void_p(); length = ctypes.c_uint32()
                if lib.GetFileVersionInfoW(str(exe), 0, size, buf) and \
                        lib.VerQueryValueW(buf, "\\", ctypes.byref(pointer), ctypes.byref(length)) and length.value >= 52:
                    info = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32))
                    version = f"{info[2] >> 16}.{info[2] & 65535}.{info[3] >> 16}.{info[3] & 65535}"
    except (OSError, ValueError):
        pass
    return LayerFollower(base / "combined.log", base / "Storage/DevicesStorage", executable=exe, version=version)
