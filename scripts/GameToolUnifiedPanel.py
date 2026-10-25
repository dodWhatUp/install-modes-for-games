"""Unified presentation of the existing native Studio and Hub. Windows only.

Native controls, overlays and input ownership remain in their original AHK
engine. Docking is app presentation, not an agent input/command bypass.
"""
from __future__ import annotations
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import queue
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GameToolCompactUI import ScrollableFrame, FlowToolbar

VERSION = "0.5.0"

def native_viewport_size(available, minimum):
    """Presentation only. Bound owner-reported pixel minima and tiny canvases."""
    if len(minimum) != 2 or any(type(v) is not int or not 300 <= v <= 4096 for v in minimum):
        minimum = (976, 733)
    return tuple(max(m, min(8192, int(a))) for a, m in zip(available, minimum))

class NativeStudio:
    def __init__(self, api, install_root, viewport):
        self.api, self.root, self.viewport = api, Path(install_root), viewport
        self.process = None
        self.lease = None
        self.child = 0
        self.user = ctypes.WinDLL("user32", use_last_error=True)
        self.user.GetWindow.argtypes = [wintypes.HWND, wintypes.UINT]
        self.user.GetWindow.restype = wintypes.HWND
        self.user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self.user.GetWindowThreadProcessId.restype = wintypes.DWORD
        self.user.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        self.user.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
        self.user.GetPropW.argtypes = [wintypes.HWND, ctypes.c_wchar_p]
        self.user.GetPropW.restype = wintypes.HANDLE
        self.user.SetPropW.argtypes = [wintypes.HWND, ctypes.c_wchar_p, wintypes.HANDLE]
        self.user.RemovePropW.argtypes = [wintypes.HWND, ctypes.c_wchar_p]
        self.user.RemovePropW.restype = wintypes.HANDLE
        self.user.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]

    def alive(self):
        alive = self.process is not None and self.process.poll() is None
        if not alive and self.lease is not None:
            self.api.release_source_lease(self.lease)
            self.lease = None
        return alive

    def start(self, reveal=True):
        self.reveal_on_start = reveal
        if self.alive():
            if reveal: self.show()
            return
        value = self.api.read_install(self.root)
        if (self.root / "update.lock").exists():
            raise ValueError("An update transaction requires inspection before Studio starts.")
        self.lease = self.api.acquire_source_lease(value["studio_dir"], "native-studio")
        try:
            self.api.assert_idle()  # Do not compete with another AHK owner or deferred tests.
            self.api.verify_current(self.root, value)
            from GameToolGameProfiles import resolved_file
            # Pass the actual existing settings owner across the packaged /
            # unpackaged process boundary. Never create blank replacement data.
            self.settings_file = resolved_file(value['studio_settings'])
            self.viewport.update_idletasks()
            self.process = subprocess.Popen([value["ahk"], "/ErrorStdOut=UTF-8",
                str(Path(value["studio_dir"]) / "AzeronOverlayStudio.ahk"),
                "--hub-parent", str(self.viewport.winfo_id()), "--hub-owner", str(os.getpid()),
                "--settings-dir", str(self.settings_file.parent)],
                cwd=value["studio_dir"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            self.api.release_source_lease(self.lease)
            self.lease = None
            raise
        self.child = 0

    def discover(self):
        if not self.alive():
            self.child = 0; return 0
        # Enumerate ONLY immediate children of this app-owned viewport and PID.
        child = self.user.GetWindow(self.viewport.winfo_id(), 5)
        while child:
            pid = wintypes.DWORD()
            self.user.GetWindowThreadProcessId(child, ctypes.byref(pid))
            if pid.value == self.process.pid:
                self.child = child
                self.user.SetPropW(self.viewport.winfo_id(), "GameTools.Studio.ScrollOwner", self.process.pid)
                return child
            child = self.user.GetWindow(child, 2)
        return 0

    def readiness(self):
        from GameToolGameProfiles import runtime_status
        if not self.alive(): return {'fresh':False,'reason':'Studio stopped'}
        return runtime_status(self.settings_file,self.process.pid)

    def size(self):
        if not self.child:
            return None
        rect = wintypes.RECT()
        if self.user.GetClientRect(self.child, ctypes.byref(rect)):
            return rect.right, rect.bottom
        return None

    def show(self):
        if self.discover():
            self.user.ShowWindow(self.child, 5)  # Show only own native child.

    def fit_viewport(self, available):
        if not self.child or not self.alive():
            return
        minimum = tuple(int(self.user.GetPropW(self.child, "GameTools.Studio." + key) or 0)
                        for key in ("MinWidth", "MinHeight"))
        desired = native_viewport_size(available, minimum)
        if self.size() != desired:
            # Exact discovered child/PID; no focus, key, settings or overlay action.
            self.user.SetWindowPos(self.child, None, 0, 0, *desired, 0x16)

    def reveal_requested(self):
        parent = self.viewport.winfo_id()
        if self.alive() and self.child and self.user.GetPropW(parent, "GameTools.Studio.Reveal") == self.process.pid:
            self.user.RemovePropW(parent, "GameTools.Studio.Reveal")
            return True
        return False

    def stop(self):
        if self.discover():
            self.user.PostMessageW(self.child, 0x10, 0, 0)  # Normal WM_CLOSE/Shutdown.

    def scroll_requests(self):
        if not self.alive() or not self.child:
            return (0, 0)
        parent = self.viewport.winfo_id()
        values = []
        for name in ("GameTools.Studio.ScrollX", "GameTools.Studio.ScrollY"):
            value = self.user.RemovePropW(parent, name)
            values.append(value - 32768 if value and 32048 <= value <= 33488 else 0)
        return tuple(values)

    def set_identification(self, enabled):
        # Only a Boolean presentation flag on this app-owned viewport. No
        # arbitrary target, click, key, text, profile or command payload exists.
        if self.alive() and self.child:
            parent = self.viewport.winfo_id()
            self.user.SetPropW(parent, "GameTools.Studio.Identify", 1 if enabled else 2)

    def set_identification_filter(self, mask):
        if type(mask) is not int or not 0 <= mask <= 15:
            raise ValueError("Invalid identification display filter")
        if self.alive() and self.child:
            self.user.SetPropW(self.viewport.winfo_id(), "GameTools.Studio.IdentifyFilter",16+mask)

class UnifiedPanel:
    def __init__(self, root, tabs, install_root, api, status):
        self.root, self.tabs, self.install_root, self.api, self.status = root, tabs, Path(install_root), api, status
        self.closed = False; self.closing = False; self.updating = False; self.restart_needed = False
        self.on_close = None
        self.messages = queue.Queue(); self.preview = None
        self.studio_tab = ttk.Frame(tabs, padding=8)
        self.update_tab = ttk.Frame(tabs, padding=12)
        tabs.add(self.studio_tab, text="Studio"); tabs.add(self.update_tab, text="Updates")
        bar = FlowToolbar(self.studio_tab); bar.pack(fill="x")
        bar.add("Start / Show Studio", self.start)
        bar.add("Stop Studio", self.stop)
        self.engine_status = tk.StringVar(value="Studio stopped • existing data retained • Game Input OFF at startup")
        ttk.Label(self.studio_tab, textvariable=self.engine_status, wraplength=700).pack(anchor="w", pady=3)
        ttk.Label(self.studio_tab, text="Full native Studio 2.2 • Picture buttons, previews, MIC, key display, status and Game Input. Scroll if needed.",
                  wraplength=1000).pack(anchor="w", pady=5)
        area = ttk.Frame(self.studio_tab); area.pack(fill="both", expand=True)
        area.rowconfigure(0, weight=1); area.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(area, highlightthickness=0, bg="#f3f5f7", xscrollincrement=18, yscrollincrement=18)
        x = ttk.Scrollbar(area, orient="horizontal", command=self.canvas.xview)
        y = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=x.set, yscrollcommand=y.set)
        self.canvas.grid(row=0,column=0,sticky="nsew"); y.grid(row=0,column=1,sticky="ns"); x.grid(row=1,column=0,sticky="ew")
        self.viewport = tk.Frame(self.canvas, width=976, height=733, bg="#f3f5f7")
        self.viewport.pack_propagate(False)
        self.canvas_item = self.canvas.create_window(0,0,window=self.viewport,anchor="nw",width=976,height=733)
        self.canvas.configure(scrollregion=(0,0,976,733))
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.viewport.bind("<MouseWheel>", self.wheel)
        self._scroll_remainder = [0, 0]
        self.identification = False
        self.identification_filter = 15
        self.engine = NativeStudio(api, install_root, self.viewport)
        self.build_updates()
        self.timer = root.after(250, self.tick)
        # Only unified mode starts its preserved Studio. No Game Input auto-arm.
        root.after(150, lambda: self.start(reveal=False))

    def build_updates(self):
        self.update_scroll = ScrollableFrame(self.update_tab, min_width=620)
        self.update_scroll.pack(fill="both",expand=True)
        body = self.update_scroll.body
        ttk.Label(body, text="Update in place — no uninstall required", font=("Segoe UI",14,"bold")).pack(anchor="w")
        ttk.Label(body, text="Choose a trusted local GameTools ZIP and its expected SHA-256. Inspect first, then update explicitly. Settings, profiles and overlay assets stay in place. No automatic downloads.",
                  wraplength=1000).pack(anchor="w",pady=8)
        form = ttk.Frame(body); form.pack(fill="x")
        self.archive = tk.StringVar(); self.expected = tk.StringVar()
        ttk.Label(form,text="Package ZIP").grid(row=0,column=0,sticky="w")
        ttk.Entry(form,textvariable=self.archive).grid(row=0,column=1,sticky="ew",padx=8,pady=4)
        ttk.Button(form,text="Browse",command=self.browse).grid(row=0,column=2)
        ttk.Label(form,text="Expected SHA-256").grid(row=1,column=0,sticky="w")
        ttk.Entry(form,textvariable=self.expected).grid(row=1,column=1,sticky="ew",padx=8,pady=4)
        form.columnconfigure(1,weight=1)
        bar=FlowToolbar(body); bar.pack(fill="x",pady=8)
        for text,action in (("Inspect package",self.inspect),("Update",self.update),
                            ("Roll back previous version",self.rollback),("Restart unified app",self.restart)):
            bar.add(text, action)
        self.details=tk.Text(body,wrap="word",height=12,font=("Segoe UI",10))
        self.details.pack(fill="both",expand=True)
        self.describe_install()

    def scroll(self, axis, delta):
        self._scroll_remainder[axis] += delta
        steps = int(self._scroll_remainder[axis] / 120)
        self._scroll_remainder[axis] -= steps * 120
        if steps:
            # Horizontal WM_MOUSEHWHEEL uses the opposite sign from vertical.
            (self.canvas.xview_scroll if axis == 0 else self.canvas.yview_scroll)(-steps * 3, "units")

    def wheel(self, event):
        self.scroll(0 if getattr(event,"state",0) & 1 else 1, event.delta)
        return "break"

    def display(self, text):
        self.details.configure(state="normal"); self.details.delete("1.0","end")
        self.details.insert("1.0",text); self.details.configure(state="disabled")

    def describe_install(self):
        v=self.api.read_install(self.install_root)
        versions=v["component_versions"]
        self.display(f'Installed: Hub {versions["tool_hub"]} • Studio {versions["overlay_studio"]}\n'
            f'Previous unified version: {v.get("previous") or "none — initial recovery backup is retained"}\n\n'
            'Updates replace only authored code. Existing settings, native profiles, pictures and Hub reports are not reset.\n'
            'The old standalone Studio launcher still works, but do not run both engines at once.\n'
            'SHA-256 verifies bytes, not who published them. Use a trusted package.\n'
            'Game/benchmark/capture owners and all AHK hosts must be stopped before a source switch.\n'
            'Games, benchmarks, recording and deferred MFG/FrameWarp tests remain stopped.')

    def browse(self):
        path=filedialog.askopenfilename(parent=self.root,title="Select trusted authored GameTools ZIP",filetypes=[("ZIP package","*.zip")])
        if path: self.archive.set(path)

    def inspect(self):
        if self.updating: return
        try:
            release=self.api.inspect_archive(Path(self.archive.get()),self.expected.get().strip())
            state_raw=self.api.read_bytes(self.install_root/"install.json")
            state=self.api.read_install(self.install_root)
            self.api.verify_current(self.install_root,state)
            self.preview={"archive":self.archive.get(),"sha":release["sha256"],"state_sha":self.api.digest(state_raw),
                          "studio_hashes":state["studio_hashes"],"versions":release["manifest"]["component_versions"]}
            versions=self.preview["versions"]
            changed=sum(self.api.digest(release["payloads"][source])!=state["studio_hashes"][name] for name,source in self.api.STUDIO.items())
            self.display(f'VERIFIED local package • {len(release["payloads"])} source files\n'
                f'Hub {state["component_versions"]["tool_hub"]} → {versions["tool_hub"]}\n'
                f'Studio {state["component_versions"]["overlay_studio"]} → {versions["overlay_studio"]}\n'
                f'{changed} of six owned Studio source files differ.\nSHA-256: {release["sha256"]}\n\n'
                'Inspect did not install or stop anything. Update stops only this Hub’s Studio normally, rechecks owners/source drift, '
                'creates recovery copies and commits the new version pointer last. Restart applies the new Hub code. No data migration.')
            self.status.set("Update inspected; no code changed.")
        except Exception as e:
            self.preview=None; self.status.set("Update inspection blocked: "+str(e)); self.display(str(e))

    def start(self, reveal=True):
        if self.closed or self.closing or self.updating: return
        if self.restart_needed:
            self.status.set("Restart the unified app before starting its updated Studio."); return
        try: self.engine.start(reveal=reveal)
        except Exception as e: self.status.set("Studio start blocked: "+str(e))

    def stop(self):
        self.engine.stop()

    def set_identification(self, enabled):
        self.identification = bool(enabled)
        self.engine.set_identification(self.identification)

    def set_identification_filter(self, mask):
        if type(mask) is not int or not 0 <= mask <= 15:
            raise ValueError("Invalid identification display filter")
        self.identification_filter = mask
        self.engine.set_identification_filter(mask)

    def update(self):
        if not self.preview or self.preview["archive"]!=self.archive.get() or self.preview["sha"]!=self.expected.get().strip().lower():
            self.status.set("Inspect this exact package and SHA-256 first."); return
        if not messagebox.askyesno("Update unified tools", "Stop this Hub’s Studio normally and install the inspected source update? Settings, profiles and assets will not be reset.", parent=self.root): return
        self.begin_change(False)

    def rollback(self):
        if self.updating: return
        try:
            state=self.api.read_install(self.install_root)
            if not state.get("previous"): raise ValueError("No previous unified version; use the recorded initial backup for the original standalone source.")
            self.preview={"state_sha":self.api.digest(self.api.read_bytes(self.install_root/"install.json"))}
        except Exception as e: self.status.set(str(e)); return
        if messagebox.askyesno("Roll back source version", "Restore the previous unified code version without replacing settings, profiles or overlays?",parent=self.root):
            self.begin_change(True)

    def begin_change(self, rollback):
        if self.updating: return
        self.updating=True; self.stop(); self.deadline=time.monotonic()+6
        def wait_for_stop():
            if self.closed: return
            if self.engine.alive():
                if time.monotonic()>self.deadline:
                    self.updating=False; self.status.set("Studio did not close normally; update blocked, no forced termination."); return
                self.root.after(100,wait_for_stop); return
            preview=dict(self.preview)
            def work():
                try:
                    if rollback:
                        value=self.api.rollback_previous(self.install_root,expected_state_sha256=preview["state_sha"])
                    else:
                        release=self.api.inspect_archive(Path(preview["archive"]),preview["sha"])
                        value=self.api.apply_release(self.install_root,release,expected_state_sha256=preview["state_sha"],expected_studio=preview["studio_hashes"])
                    self.messages.put((True,value))
                except Exception as e: self.messages.put((False,str(e)))
            threading.Thread(target=work,daemon=True).start()
            self.status.set("Updating owned source; recovery and source checks in progress…")
        wait_for_stop()

    def restart(self):
        if self.updating: return
        self.stop(); deadline=time.monotonic()+6
        def wait():
            if self.engine.alive():
                if time.monotonic()>deadline:
                    self.status.set("Studio has not stopped normally; restart blocked."); return
                self.root.after(100,wait); return
            try:
                command=self.api.launch_command(self.install_root)
                if self.on_close is None:
                    raise ValueError("Host lifecycle callback is unavailable; close normally before relaunch.")
                if not self.on_close():
                    return
                # Wait for this process through a stable launcher, not a timed race.
                subprocess.Popen([command[0],"-B",str(self.install_root/"Start-UnifiedTools.pyw"),"--wait-pid",str(os.getpid())],cwd=str(self.install_root))
            except Exception as e: self.status.set("Restart blocked: "+str(e))
        wait()

    def tick(self):
        if self.closed: return
        child=self.engine.discover()
        if child:
            if hasattr(self.engine,"set_identification"):
                self.engine.set_identification(getattr(self,"identification",False))
            if hasattr(self.engine,"set_identification_filter"):
                self.engine.set_identification_filter(getattr(self,"identification_filter",15))
            if self.engine.reveal_requested():
                if getattr(self.engine,'reveal_on_start',True):self.tabs.select(self.studio_tab)
                self.engine.reveal_on_start=True
            if hasattr(self.engine, "fit_viewport"):
                self.engine.fit_viewport((self.canvas.winfo_width(), self.canvas.winfo_height()))
            size=self.engine.size()
            if size and size[0]>0 and size[1]>0:
                self.viewport.configure(width=size[0],height=size[1])
                self.canvas.itemconfigure(self.canvas_item,width=size[0],height=size[1])
                self.canvas.configure(scrollregion=(0,0,*size))
            if hasattr(self.engine, "scroll_requests"):
                xdelta, ydelta = self.engine.scroll_requests()
                if xdelta: self.scroll(0, xdelta)
                if ydelta: self.scroll(1, ydelta)
            self.engine_status.set("Studio running • saved features retained • Game Input requires explicit Start")
        elif self.engine.alive(): self.engine_status.set("Studio starting…")
        else: self.engine_status.set("Studio stopped • Start / Show restores the panel")
        try:
            ok,value=self.messages.get_nowait()
            self.updating=False
            if ok:
                self.restart_needed=True; self.preview=None; self.describe_install()
                self.status.set("Source update verified. Restart unified app to use the new version.")
            else: self.status.set("Update blocked/failed: "+value); self.display(value)
        except queue.Empty: pass
        self.timer=self.root.after(250,self.tick)

    def close(self):
        if self.updating:
            return False
        self.closing = True
        self.stop()
        if self.engine.alive():
            return False  # Host retries bounded normal shutdown before destroying parent.
        self.closed=True
        self.root.after_cancel(self.timer)
        self.update_scroll.close()
        self.stop()  # Owner watchdog also handles parent destruction; no profile save.
        return True
