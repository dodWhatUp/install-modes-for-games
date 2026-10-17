"""Structured Linux guest tools, reached through SSH and a private Unix socket.

No AI credentials, host input, TCP listener, arbitrary JavaScript or shared folders.
Browser sessions live only in the guest worker; responses declare lost state.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import socket
import subprocess
import sys
import time
import uuid

VERSION = "0.3.0"
LIMIT = 262144
WORK = Path.home() / "work"
ARTIFACTS = Path.home() / "artifacts"
STATE = Path.home() / ".local/state/codex-lab"
SOCKET = STATE / "agent.sock"
OPS = ("capabilities", "system.status", "process.list", "files.list", "files.read",
       "files.write", "process.run", "browser.open", "browser.snapshot", "browser.act",
       "browser.close", "desktop.open", "desktop.status", "desktop.launch", "desktop.snapshot",
       "desktop.act", "desktop.screenshot", "desktop.close", "agent.stop")


class RequestError(Exception):
    pass


def scoped_path(relative, root=WORK):
    if not isinstance(relative, str) or len(relative) > 2048:
        raise RequestError("Expected a workspace-relative path")
    root = root.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise RequestError("Path escapes the guest workspace")
    return target


def validate(request):
    if not isinstance(request, dict) or request.get("schema") != 1:
        raise RequestError("Expected schema 1 object")
    if request.get("op") not in OPS:
        raise RequestError("Unknown operation")
    if not isinstance(request.get("id"), str) or not 1 <= len(request["id"]) <= 100:
        raise RequestError("A short request id is required")
    if not isinstance(request.get("args", {}), dict):
        raise RequestError("args must be an object")
    value = request.get("timeout_ms", 15000)
    if type(value) is not int or not 500 <= value <= 60000:
        raise RequestError("timeout_ms must be 500..60000")
    return request


def system_status():
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            memory[key + "_bytes"] = int(value.split()[0]) * 1024
    stat = os.statvfs(WORK)
    return {"os": platform.system(), "release": platform.release(), "python": platform.python_version(),
            "uid": os.getuid(), "cpu_count": os.cpu_count(), "load_average": list(os.getloadavg()),
            "uptime_seconds": float(Path("/proc/uptime").read_text().split()[0]),
            "memory": memory, "workspace_disk_free_bytes": stat.f_bavail * stat.f_frsize,
            "workspace": str(WORK), "scope": "guest OS; no host metrics"}


def process_list():
    result = []
    for entry in sorted(Path("/proc").iterdir(), key=lambda x: x.name):
        if not entry.name.isdigit():
            continue
        try:
            # Avoid command lines/environment variables, which may contain credentials.
            values = dict(line.split(":", 1) for line in (entry / "status").read_text().splitlines())
            result.append({"pid": int(entry.name), "name": values["Name"].strip(),
                           "state": values["State"].strip(),
                           "resident_bytes": int(values.get("VmRSS", "0 kB").split()[0]) * 1024})
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if len(result) >= 256:
            break
    return {"processes": result, "limit": 256}


class Agent:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.session = None
        self.server = None
        self.lock = asyncio.Lock()
        self.desktop_process = None
        self.desktop_session = None
        self.desktop_socket = None

    async def close_desktop(self):
        if self.desktop_process:
            try:
                os.killpg(self.desktop_process.pid, signal.SIGTERM)
                await asyncio.wait_for(self.desktop_process.wait(), 3)
            except (ProcessLookupError, asyncio.TimeoutError):
                pass
            # Remove only the process group that this worker created.
            try:
                os.killpg(self.desktop_process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await self.desktop_process.wait()
        if self.desktop_socket:
            self.desktop_socket.unlink(missing_ok=True)
            self.desktop_socket.with_suffix(".xauth").unlink(missing_ok=True)
        self.desktop_process = self.desktop_session = self.desktop_socket = None

    async def desktop_call(self, request):
        op = request["op"]
        if op == "desktop.open":
            if self.desktop_process:
                raise RequestError("An active desktop session exists; close it explicitly first")
            self.desktop_session = uuid.uuid4().hex
            self.desktop_socket = STATE / ("desktop-" + self.desktop_session + ".sock")
            with (STATE / ("desktop-" + self.desktop_session + ".log")).open("xb") as output:
                self.desktop_process = await asyncio.create_subprocess_exec(
                    "/usr/bin/dbus-run-session", "--", "/usr/bin/python3",
                    str(Path(__file__).with_name("desktop_agent.py")), "--socket", str(self.desktop_socket),
                    "--session", self.desktop_session, start_new_session=True, stdout=output, stderr=output)
            for _ in range(200):
                if self.desktop_socket.exists():
                    break
                if self.desktop_process.returncode is not None:
                    raise RequestError("Desktop provider exited; inspect private guest desktop log")
                await asyncio.sleep(0.1)
            request = {"op": "desktop.status", "session": self.desktop_session}
        elif not self.desktop_process or request.get("session") != self.desktop_session:
            raise RequestError("Desktop session missing or stale; open and inspect a fresh session")
        if self.desktop_process.returncode is not None:
            await self.close_desktop()
            raise RequestError("Desktop provider exited; session lost")
        if op == "desktop.close":
            await self.close_desktop()
            return {"closed": True}
        try:
            reader, writer = await asyncio.open_unix_connection(str(self.desktop_socket), limit=LIMIT + 1)
        except (OSError, ConnectionError) as error:
            await self.close_desktop()
            raise RequestError("Desktop provider connection lost; open a fresh session") from error
        try:
            writer.write((json.dumps(request) + "\n").encode())
            await writer.drain()
            raw = await reader.readline()
            if not raw:
                await self.close_desktop()
                raise RequestError("Desktop provider exited without a response; session lost")
            if len(raw) > LIMIT:
                raise RequestError("Desktop response exceeded limit")
            response = json.loads(raw)
            if not response.get("ok"):
                raise RequestError(response.get("error", "Desktop provider failure"))
            result = response["result"]
            if op in ("desktop.open", "desktop.status"):
                result["provider_pid"] = self.desktop_process.pid
            return result
        finally:
            writer.close()
            await writer.wait_closed()

    async def close_browser(self):
        try:
            if self.browser:
                await asyncio.wait_for(self.browser.close(), 5)
        except Exception:
            pass
        finally:
            if self.playwright:
                try:
                    await asyncio.wait_for(self.playwright.stop(), 5)
                except Exception:
                    pass
            self.playwright = self.browser = self.context = self.page = self.session = None

    def require_session(self, request):
        if not self.page or request.get("session") != self.session:
            raise RequestError("Browser session missing or stale; open a fresh guest session")

    async def snapshot(self):
        text = await self.page.locator("body").inner_text(timeout=3000)
        aria = await self.page.locator("body").aria_snapshot(timeout=3000)
        return {"session": self.session, "url": self.page.url, "title": await self.page.title(),
                "text": text[:24000], "aria": aria[:24000],
                "truncated": len(text) > 24000 or len(aria) > 24000,
                "source": "browser DOM and accessibility semantics"}

    async def process_run(self, args, timeout):
        argv = args.get("argv")
        if (not isinstance(argv, list) or not 1 <= len(argv) <= 64 or
                any(not isinstance(x, str) or len(x) > 8192 for x in argv)):
            raise RequestError("argv must be a bounded list of strings")
        cwd = scoped_path(args.get("cwd", "."))
        process = await asyncio.create_subprocess_exec(*argv, cwd=cwd, start_new_session=True,
                                                      stdout=asyncio.subprocess.PIPE,
                                                      stderr=asyncio.subprocess.PIPE)
        async def drain(stream):
            data = bytearray()
            truncated = False
            while True:
                chunk = await stream.read(8192)
                if not chunk:
                    return data.decode("utf-8", errors="replace"), truncated
                room = max(0, 65536 - len(data))
                data.extend(chunk[:room])
                truncated |= len(chunk) > room
        readers = [asyncio.create_task(drain(process.stdout)), asyncio.create_task(drain(process.stderr))]
        timed_out = False
        try:
            await asyncio.wait_for(process.wait(), timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
                await asyncio.wait_for(process.wait(), 1)
            except (ProcessLookupError, asyncio.TimeoutError):
                pass
        finally:
            # Also remove children that retained output pipes after the leader exited.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await process.wait()
        output = await asyncio.wait_for(asyncio.gather(*readers), 3)
        return {"exit_code": process.returncode, "timed_out": timed_out,
                "stdout": output[0][0], "stderr": output[1][0],
                "output_truncated": output[0][1] or output[1][1], "pid": process.pid}

    async def dispatch(self, request):
        op, args = request["op"], request.get("args", {})
        if op == "capabilities":
            available = importlib.util.find_spec("playwright") is not None
            return {"version": VERSION, "ops": list(OPS), "system": "available",
                    "files": "workspace only", "processes": "guest only",
                    "browser": {"provider_installed": available, "runtime_accepted": "probe with browser.open",
                                "session_active": bool(self.page), "session": self.session},
                    "desktop_accessibility": {
                        "provider_installed": Path(__file__).with_name("desktop-provider.json").exists(),
                        "runtime_accepted": "probe desktop.open and selected app snapshot",
                        "session_active": bool(self.desktop_process), "session": self.desktop_session,
                        "scope": "apps launched into private guest D-Bus/Xvfb session"},
                    "windows": {"available": False, "reason": "Windows VM has not been provisioned"}}
        if op == "system.status":
            return system_status()
        if op == "process.list":
            return process_list()
        if op == "files.list":
            target = scoped_path(args.get("path", "."))
            entries = sorted(target.iterdir(), key=lambda x: x.name)
            return {"path": str(target), "entries": [{"name": p.name, "kind": "symlink" if p.is_symlink()
                    else "directory" if p.is_dir() else "file"} for p in entries[:256]],
                    "truncated": len(entries) > 256}
        if op == "files.read":
            target = scoped_path(args.get("path"))
            with target.open("rb") as f:
                data = f.read(65537)
            return {"text": data[:65536].decode("utf-8", errors="replace"),
                    "truncated": len(data) > 65536, "bytes_returned": min(len(data), 65536)}
        if op == "files.write":
            target = scoped_path(args.get("path"))
            text = args.get("text")
            if not isinstance(text, str) or len(text.encode("utf-8")) > 65536:
                raise RequestError("Expected text up to 64 KiB")
            # Exclusive creation: an inspection API must not silently overwrite data.
            with target.open("xb") as f:
                f.write(text.encode("utf-8"))
            data = target.read_bytes()
            return {"created": True, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if op == "process.run":
            return await self.process_run(args, request.get("timeout_ms", 15000) / 1000 - 0.2)
        if op.startswith("desktop."):
            return await self.desktop_call(request)
        if op == "browser.open":
            if self.page:
                raise RequestError("An active browser session exists; close it explicitly first")
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(viewport={"width": 1100, "height": 760},
                                                         accept_downloads=False)
            self.context.set_default_timeout(4000)
            self.page = await self.context.new_page()
            self.session = uuid.uuid4().hex
            return {"session": self.session, "browser_version": self.browser.version,
                    "headless": True, "scope": "guest browser"}
        if op == "agent.stop":
            await self.close_browser()
            await self.close_desktop()
            self.server.close()
            return {"stopped": True}
        self.require_session(request)
        if op == "browser.close":
            await self.close_browser()
            return {"closed": True}
        if op == "browser.snapshot":
            return await self.snapshot()
        action = args.get("action")
        if action == "goto":
            url = args.get("url", "")
            if not isinstance(url, str) or not url.startswith(("http://", "https://")) or len(url) > 2048:
                raise RequestError("Expected an HTTP(S) URL")
            response = await self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
            return {"url": self.page.url, "http_status": response.status if response else None}
        if action == "screenshot":
            ARTIFACTS.mkdir(exist_ok=True)
            filename = "browser-" + uuid.uuid4().hex + ".png"
            await self.page.screenshot(path=str(ARTIFACTS / filename))
            return {"artifact": filename, "source": "guest browser pixels"}
        if action not in ("fill", "click", "check", "select", "read"):
            raise RequestError("Unsupported browser action")
        role, name = args.get("role"), args.get("name")
        if not isinstance(role, str) or not isinstance(name, str) or len(name) > 512:
            raise RequestError("Select a control with its role and exact accessible name")
        locator = self.page.get_by_role(role, name=name, exact=True)
        if await locator.count() != 1:
            raise RequestError("Selector must identify exactly one control")
        if action == "fill":
            value = args.get("value")
            if not isinstance(value, str) or len(value) > 8192:
                raise RequestError("Expected a bounded string value")
            await locator.fill(value)
        elif action == "click":
            await locator.click()
        elif action == "check":
            if type(args.get("checked")) is not bool:
                raise RequestError("Expected boolean checked")
            await locator.set_checked(args["checked"])
        elif action == "select":
            if not isinstance(args.get("value"), str):
                raise RequestError("Expected a string option value")
            await locator.select_option(args["value"])
        else:
            return {"text": (await locator.inner_text())[:8192], "visible": await locator.is_visible(),
                    "enabled": await locator.is_enabled()}
        return {"action": action, "completed": True, "session": self.session}

    async def handle(self, reader, writer):
        request, started = {}, time.monotonic()
        state_lost = False
        desktop_lost = False
        try:
            raw = await asyncio.wait_for(reader.readline(), 5)
            if len(raw) > LIMIT:
                raise RequestError("Request exceeds limit")
            request = validate(json.loads(raw))
            # Reject concurrent callers; a second workflow cannot interrupt an active one.
            if self.lock.locked():
                raise RequestError("Agent busy; inspect the active request before retrying")
            async with self.lock:
                had_session = bool(self.page)
                had_desktop = bool(self.desktop_process)
                try:
                    result = await asyncio.wait_for(self.dispatch(request),
                                                    request.get("timeout_ms", 15000) / 1000)
                except asyncio.TimeoutError:
                    state_lost = request["op"].startswith("browser.")
                    if state_lost:
                        await self.close_browser()
                    desktop_lost = request["op"].startswith("desktop.")
                    if desktop_lost:
                        await self.close_desktop()
                    raise
                except Exception:
                    if request["op"] == "browser.open" and not had_session:
                        await self.close_browser()
                    if request["op"] == "desktop.open" and not had_desktop:
                        desktop_lost = True
                        await self.close_desktop()
                    elif request["op"].startswith("desktop.") and had_desktop and self.desktop_process is None:
                        desktop_lost = True
                    elif request["op"].startswith("browser.") and self.browser and (
                            not self.browser.is_connected() or (self.page and self.page.is_closed())):
                        state_lost = True
                        await self.close_browser()
                    raise
            response = {"ok": True, "result": result}
        except Exception as error:
            response = {"ok": False, "error": {"code": type(error).__name__, "message": str(error)[:2000]},
                        "browser_state_lost": state_lost, "desktop_state_lost": desktop_lost}
        response.update(schema=1, version=VERSION, id=request.get("id"), op=request.get("op"),
                        observed_at=datetime.now(timezone.utc).isoformat(),
                        elapsed_ms=round((time.monotonic() - started) * 1000))
        # Keep the receipt on each side. Private outputs are data, never new instructions.
        if request.get("id"):
            receipt = STATE / ("receipt-" + uuid.uuid4().hex + ".json")
            receipt.write_text(json.dumps(response), encoding="utf-8")
        encoded = (json.dumps(response, ensure_ascii=False) + "\n").encode()
        if len(encoded) > LIMIT:
            response = {"schema": 1, "version": VERSION, "id": request.get("id"),
                        "op": request.get("op"), "ok": False,
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                        "elapsed_ms": round((time.monotonic() - started) * 1000),
                        "error": {"code": "OutputLimit", "message": "Response exceeded 256 KiB; full private receipt retained"}}
            encoded = (json.dumps(response) + "\n").encode()
        writer.write(encoded)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def serve(self):
        STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
        WORK.mkdir(exist_ok=True)
        os.chmod(STATE, 0o700)
        self.server = await asyncio.start_unix_server(self.handle, path=str(SOCKET), limit=LIMIT + 1)
        os.chmod(SOCKET, 0o600)
        try:
            async with self.server:
                await self.server.serve_forever()
        finally:
            await self.close_browser()
            await self.close_desktop()
            SOCKET.unlink(missing_ok=True)


def call_worker(request):
    validate(request)
    raw = (json.dumps(request) + "\n").encode()
    if len(raw) > LIMIT:
        raise RequestError("Request exceeds limit")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(request.get("timeout_ms", 15000) / 1000 + 15)
        client.connect(str(SOCKET))
        client.sendall(raw)
        with client.makefile("rb") as stream:
            response = stream.readline(LIMIT + 1)
            if len(response) > LIMIT or not response.endswith(b"\n"):
                raise RequestError("Invalid or oversized agent response")
    return json.loads(response)


def ensure_worker():
    STATE.mkdir(parents=True, exist_ok=True, mode=0o700)
    if SOCKET.exists():
        try:
            result = call_worker({"schema": 1, "id": "probe", "op": "capabilities", "timeout_ms": 1000})
            if result.get("version") != VERSION:
                raise RequestError("Existing guest worker version differs; stop it before upgrading")
            return
        except ConnectionRefusedError:
            # A refused private socket has no live listener. Preserve other errors.
            SOCKET.unlink()
    # Atomic setup lock: never launch two workers or delete a live owner's lock.
    lock = STATE / "startup.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        with (STATE / "worker.log").open("ab") as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--serve"],
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                       start_new_session=True)
        (STATE / "worker-pid.json").write_text(json.dumps({"pid": process.pid, "version": VERSION}))
        end = time.monotonic() + 5
        while time.monotonic() < end:
            if process.poll() is not None:
                raise RequestError("Guest worker failed; inspect its private log")
            if SOCKET.exists():
                return
            time.sleep(0.1)
        raise RequestError("Guest worker startup deadline exceeded")
    finally:
        lock.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    request = {}
    try:
        if platform.system() != "Linux":
            raise RequestError("This accepted provider currently targets Linux guests")
        if args.serve:
            try:
                asyncio.run(Agent().serve())
            except asyncio.CancelledError:
                pass
            return 0
        request = validate(json.loads(sys.stdin.buffer.readline(LIMIT + 1)))
        ensure_worker()
        result = call_worker(request)
        print(json.dumps(result))
        return 0 if result.get("ok") else 2
    except Exception as error:
        print(json.dumps({"schema": 1, "version": VERSION, "id": request.get("id"),
                          "op": request.get("op"), "ok": False,
                          "error": {"code": type(error).__name__, "message": str(error)[:2000]}}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
