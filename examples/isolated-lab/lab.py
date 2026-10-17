"""Headless lab controller. Commands target guests; never host desktop input."""
import argparse
import base64
from contextlib import contextmanager
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time
import uuid


def stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def available_memory_mb():
    class Memory(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
            (field, ctypes.c_ulonglong) for field in
            ("total_phys", "available_phys", "total_page", "available_page",
             "total_virtual", "available_virtual", "available_extended")]
    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise OSError("Cannot determine current host memory headroom")
    return memory.available_phys // (1024 * 1024)


def process_identity(pid):
    """PID reuse guard for Windows process ownership."""
    if os.name != "nt":
        raise RuntimeError("This host controller currently supports Windows only")
    from ctypes import wintypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        if ctypes.get_last_error() == 87:
            return None
        raise OSError(ctypes.get_last_error(), "Cannot inspect recorded process identity")
    try:
        exit_code = wintypes.DWORD()
        if kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value != 259:
            return None
        size = wintypes.DWORD(32768)
        image = ctypes.create_unicode_buffer(size.value)
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)):
            if kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value != 259:
                return None
            raise OSError(ctypes.get_last_error())
        creation, exit_time, kernel_time, user_time = [wintypes.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(handle, *[ctypes.byref(x) for x in
                                              [creation, exit_time, kernel_time, user_time]]):
            raise OSError(ctypes.get_last_error())
        return {"pid": int(pid), "image": str(Path(image.value).resolve()),
                "creation": (creation.dwHighDateTime << 32) | creation.dwLowDateTime}
    finally:
        kernel.CloseHandle(handle)


class Lab:
    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve()
        self.config = json.loads(self.config_path.read_text(encoding="utf-8-sig"))
        if self.config.get("schema") != 1:
            raise ValueError("Unsupported config schema")
        self.root = Path(self.config["root"]).resolve()
        if not self.root.is_dir() or self.root == Path(self.root.anchor):
            raise ValueError("Lab root must be a dedicated existing directory")
        self.private = self.inside(self.root / "private")
        self.artifacts = self.inside(self.root / "artifacts")
        for name, guest in self.config["guests"].items():
            if name not in ("linux", "windows") or guest["backend"] not in ("qemu", "vbox"):
                raise ValueError("Unknown guest/backend")
            self.inside(guest["disk"])
            if not 1 <= guest["cpus"] <= 4 or not 1024 <= guest["memory_mb"] <= 8192:
                raise ValueError("Guest exceeds initial CPU/RAM budget")
            if guest["backend"] == "qemu":
                self.inside(guest["seed"])
                for key in ("ssh_port", "qmp_port"):
                    if not 1024 <= guest[key] <= 65535:
                        raise ValueError("Invalid loopback port")
                if not 1 <= guest["vnc_display"] <= 99:
                    raise ValueError("Invalid VNC display")
                if guest["accelerator"] not in ("tcg", "whpx"):
                    raise ValueError("Explicit accelerator must be tcg or whpx")

    def inside(self, path):
        path = Path(path).resolve()
        if self.root not in path.parents:
            raise ValueError("Target escapes private lab root")
        return path

    def guest(self, name):
        return self.config["guests"][name]

    def state_path(self, name):
        return self.private / (name + "-state.json")

    @contextmanager
    def lock(self, name):
        path = self.private / (name + ".lock")
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise RuntimeError("Guest has an operation lock; inspect its owner before clearing it")
        try:
            os.write(fd, json.dumps({"pid": os.getpid(), "created": stamp()}).encode())
            os.close(fd)
            yield
        finally:
            path.unlink(missing_ok=True)

    def vbox(self, *args, timeout=30):
        env = os.environ.copy()
        env["VBOX_USER_HOME"] = str(self.private / "vbox")
        return subprocess.run([self.config["vbox"], *args], capture_output=True,
                              text=True, timeout=timeout, env=env)

    def owned_process(self, name):
        state_path = self.state_path(name)
        if not state_path.exists():
            return None
        state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        identity = process_identity(state["pid"])
        if identity is None:
            return None
        if state.get("identity") != identity:
            raise RuntimeError("Process ownership cannot be verified; refusing mutation")
        if Path(identity["image"]).resolve() != Path(self.config["qemu"]).resolve():
            raise RuntimeError("Process image does not match configured QEMU")
        return identity

    def running(self, name):
        guest = self.guest(name)
        if guest["backend"] == "qemu":
            return self.owned_process(name) is not None
        if not Path(self.config["vbox"]).exists():
            return False
        result = self.vbox("showvminfo", guest["name"], "--machinereadable")
        if result.returncode:
            return False
        return bool(re.search(r'^VMState="(running|paused|stuck|saving|restoring)"$', result.stdout, re.M))

    def ssh_args(self, name):
        guest = self.guest(name)
        return ["ssh.exe", "-F", "none", "-T", "-p", str(guest["ssh_port"]), "-i", guest["key"],
                "-o", "IdentitiesOnly=yes", "-o", "ForwardAgent=no", "-o", "PermitLocalCommand=no",
                "-o", "ClearAllForwardings=yes",
                "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
                "-o", "ConnectionAttempts=1", "-o", "ServerAliveInterval=5",
                "-o", "ServerAliveCountMax=2", "-o", "StrictHostKeyChecking=accept-new",
                "-o", "UserKnownHostsFile=" + guest["known_hosts"],
                guest["user"] + "@127.0.0.1"]

    def ssh(self, name, command, timeout=15, input=None):
        if input is None:
            return subprocess.run(self.ssh_args(name) + [command], capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=timeout)
        # Windows text-mode stdin translates LF into CRLF. Send the payload as bytes.
        payload = input.encode("utf-8") if isinstance(input, str) else input
        result = subprocess.run(self.ssh_args(name) + [command], input=payload,
                                capture_output=True, text=False, timeout=timeout)
        return subprocess.CompletedProcess(result.args, result.returncode,
                                           result.stdout.decode("utf-8", errors="replace"),
                                           result.stderr.decode("utf-8", errors="replace"))

    def status(self):
        result = {}
        for name, guest in self.config["guests"].items():
            entry = {"backend": guest["backend"], "disk_exists": Path(guest["disk"]).exists(),
                     "running": False, "command_ready": False, "desktop_ready": "unverified"}
            try:
                entry["running"] = self.running(name)
                if entry["running"] and name == "linux":
                    ping = self.ssh(name, "test -f /home/lab/artifacts/bootstrap-ready && printf READY", timeout=8)
                    entry["command_ready"] = ping.returncode == 0 and ping.stdout == "READY"
                if name == "windows":
                    entry["license"] = guest.get("license", "unverified")
                    entry["hypervisor_installed"] = Path(self.config["vbox"]).exists()
                    if entry["running"] and Path(guest["password_file"]).is_file():
                        ping = self.vbox("guestcontrol", guest["name"], "run", "--exe",
                                         "C:\\Windows\\System32\\cmd.exe", "--username", guest["user"],
                                         "--passwordfile", guest["password_file"], "--timeout", "5000",
                                         "--wait-stdout", "--wait-stderr", "--", "cmd.exe", "/c",
                                         "echo CODEX_LAB_READY", timeout=8)
                        entry["command_ready"] = ping.returncode == 0 and "CODEX_LAB_READY" in ping.stdout
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                entry["error"] = str(error)
            result[name] = entry
        return result

    def wait_ready(self, name, timeout):
        if not 1 <= timeout <= 600:
            raise ValueError("Readiness deadline must be 1..600 seconds")
        if not self.running(name):
            raise RuntimeError("Guest is stopped; start it before waiting for readiness")
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            state = self.status()[name]
            if state["command_ready"]:
                return {"guest": name, "command_ready": True, "desktop_ready": "unverified"}
            if not state["running"]:
                raise RuntimeError("Guest exited before readiness; inspect its logs")
            time.sleep(min(3, max(0, end - time.monotonic())))
        raise TimeoutError("Guest readiness deadline expired; no automatic restart or replay")

    def start(self, name):
        guest = self.guest(name)
        with self.lock(name):
            if self.running(name):
                return {"already_running": True}
            if not Path(guest["disk"]).is_file():
                raise RuntimeError("Guest disk is not prepared")
            if available_memory_mb() < guest["memory_mb"] + 8192:
                raise RuntimeError("Insufficient free RAM for this guest plus an 8 GiB host reserve")
            if shutil.disk_usage(self.root).free < 10 * 1024**3:
                raise RuntimeError("Less than 10 GiB free on lab drive; inspect storage before starting")
            if guest["backend"] == "vbox":
                result = self.vbox("startvm", guest["name"], "--type", "headless", timeout=60)
                if result.returncode:
                    raise RuntimeError(result.stderr.strip())
                return {"started": True, "headless": True}
            # Fail on conflicting ports; never attach a stale unrelated listener.
            for port in [guest["ssh_port"], guest["qmp_port"], 5900 + guest["vnc_display"]]:
                with socket.socket() as sock:
                    sock.bind(("127.0.0.1", port))
            disk = str(self.inside(guest["disk"])).replace("\\", "/")
            seed = str(self.inside(guest["seed"])).replace("\\", "/")
            args = [self.config["qemu"], "-name", "CodexLab-" + name, "-machine", "q35",
                    "-accel", "tcg,thread=multi" if guest["accelerator"] == "tcg" else "whpx",
                    "-cpu", "max" if guest["accelerator"] == "tcg" else "qemu64",
                    "-smp", str(guest["cpus"]), "-m", str(guest["memory_mb"]),
                    "-drive", "file=" + disk + ",format=qcow2,if=virtio",
                    "-drive", "file=" + seed + ",format=raw,if=virtio,readonly=on",
                    "-nic", "user,model=virtio-net-pci,hostfwd=tcp:127.0.0.1:" + str(guest["ssh_port"]) + "-:22",
                    "-display", "none", "-vnc", "127.0.0.1:" + str(guest["vnc_display"]),
                    "-qmp", "tcp:127.0.0.1:" + str(guest["qmp_port"]) + ",server=on,wait=off",
                    "-serial", "file:" + str(Path(disk).parent / "serial.log").replace("\\", "/"),
                    "-monitor", "none"]
            with open(Path(disk).parent / "qemu.stdout.log", "ab") as out, \
                    open(Path(disk).parent / "qemu.stderr.log", "ab") as err:
                process = subprocess.Popen(args, stdout=out, stderr=err,
                                           creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
            identity = process_identity(process.pid)
            if identity is None:
                raise RuntimeError("QEMU exited during launch; inspect stderr")
            write_json(self.state_path(name), {"pid": process.pid, "identity": identity,
                                               "disk": guest["disk"], "started": stamp()})
            time.sleep(1)
            if process.poll() is not None:
                raise RuntimeError("QEMU exited during launch; inspect stderr")
            return {"started": True, "headless": True, "accelerator": guest["accelerator"],
                    "pid": process.pid}

    def qmp(self, name, command, arguments=None):
        if self.owned_process(name) is None:
            raise RuntimeError("Guest is stopped; refusing an unowned control connection")
        guest = self.guest(name)
        with socket.create_connection(("127.0.0.1", guest["qmp_port"]), timeout=5) as sock:
            sock.settimeout(5)
            stream = sock.makefile("rwb")
            json.loads(stream.readline())
            for request in [{"execute": "qmp_capabilities"}, {"execute": command, "arguments": arguments or {}}]:
                stream.write((json.dumps(request) + "\n").encode())
                stream.flush()
                while True:
                    response = json.loads(stream.readline())
                    if "error" in response:
                        raise RuntimeError(str(response["error"]))
                    if "return" in response:
                        break
            return response["return"]

    def stop(self, name, force=False):
        guest = self.guest(name)
        with self.lock(name):
            if not self.running(name):
                return {"stopped": True, "already_stopped": True}
            if guest["backend"] == "vbox":
                result = self.vbox("controlvm", guest["name"], "poweroff" if force else "acpipowerbutton")
                if result.returncode:
                    raise RuntimeError(result.stderr.strip())
            else:
                self.qmp(name, "quit" if force else "system_powerdown")
            end = time.monotonic() + (10 if force else 45)
            while time.monotonic() < end:
                if not self.running(name):
                    return {"stopped": True, "forced": force}
                time.sleep(1)
            raise TimeoutError("Guest did not stop; preserved its state. Explicit force-stop is available.")

    def run_script(self, name, script, timeout):
        if not 1 <= timeout <= 3600:
            raise ValueError("Timeout must be 1..3600 seconds")
        if not self.running(name):
            raise RuntimeError("Guest is stopped")
        source = Path(script).resolve()
        payload = source.read_bytes()
        if len(payload) > 1024 * 1024:
            raise ValueError("Script exceeds 1 MiB")
        job = stamp() + "-" + uuid.uuid4().hex[:8]
        outdir = self.artifacts / name / job
        outdir.mkdir(parents=True)
        with self.lock(name):
            started = time.monotonic()
            try:
                if name == "linux":
                    readiness = self.ssh(name, "test -f /home/lab/artifacts/bootstrap-ready", timeout=15)
                    if readiness.returncode:
                        raise RuntimeError("Linux bootstrap is not ready; inspect cloud-init instead of running tests")
                    target = "/home/lab/work/" + job + ".sh"
                    upload = self.ssh(name, "umask 077; cat > " + shlex.quote(target),
                                      input=payload.replace(b"\r\n", b"\n"), timeout=30)
                    if upload.returncode:
                        raise RuntimeError(upload.stderr.strip())
                    result = self.ssh(name, "timeout --signal=TERM --kill-after=5 " + str(timeout) +
                                      " bash " + shlex.quote(target), timeout=timeout + 20)
                else:
                    guest = self.guest(name)
                    encoded = base64.b64encode(payload).decode()
                    command = ("$ErrorActionPreference='Stop';try {"
                               "New-Item -ItemType Directory -Force 'C:\\lab\\work'|Out-Null;"
                               "[IO.File]::WriteAllBytes('C:\\lab\\work\\" + job + ".ps1',"
                               "[Convert]::FromBase64String('" + encoded + "'));"
                               "$global:LASTEXITCODE=0;& 'C:\\lab\\work\\" + job + ".ps1';exit $LASTEXITCODE"
                               "} catch {[Console]::Error.WriteLine($_);exit 1}")
                    encoded_command = base64.b64encode(command.encode("utf-16-le")).decode()
                    result = self.vbox("guestcontrol", guest["name"], "run",
                                       "--exe", "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                                       "--username", guest["user"], "--passwordfile", guest["password_file"],
                                       "--timeout", str(timeout * 1000), "--wait-stdout", "--wait-stderr",
                                       "--", "powershell.exe", "-NoProfile", "-NonInteractive",
                                       "-EncodedCommand", encoded_command, timeout=timeout + 20)
                receipt = {"job": job, "guest": name, "exit_code": result.returncode,
                           "timeout": name == "linux" and result.returncode == 124,
                           "exit_scope": "guest process" if name == "linux" else "VBoxManage guestcontrol result",
                           "script_sha256": hashlib.sha256(payload).hexdigest(),
                           "elapsed_seconds": round(time.monotonic() - started, 2)}
                (outdir / "stdout.txt").write_text(result.stdout, encoding="utf-8")
                (outdir / "stderr.txt").write_text(result.stderr, encoding="utf-8")
            except subprocess.TimeoutExpired:
                receipt = {"job": job, "guest": name, "exit_code": 124, "timeout": True,
                           "elapsed_seconds": round(time.monotonic() - started, 2),
                           "note": "No automatic replay; inspect guest process state"}
            except (RuntimeError, OSError) as error:
                receipt = {"job": job, "guest": name, "exit_code": 2, "timeout": False,
                           "error": str(error), "elapsed_seconds": round(time.monotonic() - started, 2),
                           "note": "No automatic replay; inspect this failure before retrying"}
            write_json(outdir / "receipt.json", receipt)
            return receipt | {"artifacts": str(outdir)}

    def screenshot(self, name):
        if not self.running(name):
            raise RuntimeError("Guest is stopped")
        path = self.artifacts / name / (stamp() + "-" + uuid.uuid4().hex[:6] + "-display.png")
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock(name):
            if self.guest(name)["backend"] == "qemu":
                raw = path.with_suffix(".ppm")
                self.qmp(name, "screendump", {"filename": str(raw).replace("\\", "/")})
                from PIL import Image
                with Image.open(raw) as image:
                    image.save(path)
                raw.unlink()
            else:
                result = self.vbox("controlvm", self.guest(name)["name"], "screenshotpng", str(path))
                if result.returncode:
                    raise RuntimeError(result.stderr.strip())
        return {"screenshot": str(path), "scope": "guest display only"}

    def fetch(self, name, filename):
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", filename):
            raise ValueError("Select one simple filename from the guest artifacts directory")
        if not self.running(name):
            raise RuntimeError("Guest is stopped")
        outdir = self.artifacts / name / (stamp() + "-fetch-" + uuid.uuid4().hex[:6])
        outdir.mkdir(parents=True)
        with self.lock(name):
            guest = self.guest(name)
            if name == "linux":
                args = self.ssh_args(name)
                # Preserve all scope options; do not depend on argument positions.
                connection = args[1:-1]
                connection.remove("-T")
                connection[connection.index("-p")] = "-P"
                scp_args = ["scp.exe", *connection,
                            args[-1] + ":/home/lab/artifacts/" + filename, str(outdir / filename)]
                result = subprocess.run(scp_args, capture_output=True, text=True, timeout=60)
            else:
                result = self.vbox("guestcontrol", guest["name"], "copyfrom",
                                   "--username", guest["user"], "--passwordfile", guest["password_file"],
                                   "--target-directory", str(outdir), "C:\\lab\\artifacts\\" + filename, timeout=60)
            if result.returncode:
                raise RuntimeError(result.stderr.strip())
        target = outdir / filename
        return {"file": str(target), "sha256": sha256(target)}

    def checkpoint(self, name, label):
        if name != "linux" or self.guest(name)["backend"] != "qemu" or not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", label):
            raise ValueError("This checkpoint operation supports Linux and a simple new label")
        with self.lock(name):
            if self.running(name):
                raise RuntimeError("Stop guest before copying its disk")
            target = self.root / "checkpoints" / label
            target.mkdir(parents=True, exist_ok=False)
            disk = self.inside(self.guest(name)["disk"])
            shutil.copy2(disk, target / "disk.qcow2")
            receipt = {"guest": name, "created": stamp(), "disk_sha256": sha256(target / "disk.qcow2"),
                       "base_sha256": sha256(self.root / "downloads" / "ubuntu-noble-minimal.img"),
                       "config": self.config, "coverage": "powered-off disk, configuration, base hash"}
            write_json(target / "checkpoint.json", receipt)
            return {"checkpoint": str(target), "sha256": receipt["disk_sha256"]}

    def restore(self, name, checkpoint):
        if name != "linux" or self.guest(name)["backend"] != "qemu":
            raise ValueError("This restore operation currently supports Linux")
        with self.lock(name):
            if self.running(name):
                raise RuntimeError("Stop guest before restoring into a new disk")
            source = self.inside(checkpoint)
            receipt = json.loads((source / "checkpoint.json").read_text())
            if sha256(source / "disk.qcow2") != receipt["disk_sha256"]:
                raise ValueError("Checkpoint disk hash mismatch")
            if sha256(self.root / "downloads" / "ubuntu-noble-minimal.img") != receipt["base_sha256"]:
                raise ValueError("Backing image hash mismatch")
            target = self.root / "vms" / name / ("restored-" + stamp() + "-" + uuid.uuid4().hex[:6] + ".qcow2")
            shutil.copy2(source / "disk.qcow2", target)
            if sha256(target) != receipt["disk_sha256"]:
                raise ValueError("Restore copy verification failed; configuration unchanged")
            write_json(self.private / ("config-before-restore-" + stamp() + ".json"), self.config)
            self.config["guests"][name]["disk"] = str(target)
            write_json(self.config_path, self.config)
            return {"restored_to_new_disk": str(target), "original_disk_preserved": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("status")
    for action in ("start", "stop", "force-stop", "screenshot"):
        item = sub.add_parser(action)
        item.add_argument("guest", choices=["linux", "windows"])
    run = sub.add_parser("run")
    run.add_argument("guest", choices=["linux", "windows"])
    run.add_argument("--script", required=True)
    run.add_argument("--timeout", type=int, default=120)
    fetch = sub.add_parser("fetch")
    fetch.add_argument("guest", choices=["linux", "windows"])
    fetch.add_argument("--name", required=True)
    ready = sub.add_parser("wait-ready")
    ready.add_argument("guest", choices=["linux", "windows"])
    ready.add_argument("--timeout", type=int, default=180)
    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("guest", choices=["linux"])
    checkpoint.add_argument("--name", required=True)
    restore = sub.add_parser("restore")
    restore.add_argument("guest", choices=["linux"])
    restore.add_argument("--checkpoint", required=True)
    args = parser.parse_args()
    try:
        lab = Lab(args.config)
        if args.action == "status":
            result = lab.status()
        elif args.action == "start":
            result = lab.start(args.guest)
        elif args.action in ("stop", "force-stop"):
            result = lab.stop(args.guest, args.action == "force-stop")
        elif args.action == "screenshot":
            result = lab.screenshot(args.guest)
        elif args.action == "run":
            result = lab.run_script(args.guest, args.script, args.timeout)
        elif args.action == "fetch":
            result = lab.fetch(args.guest, args.name)
        elif args.action == "wait-ready":
            result = lab.wait_ready(args.guest, args.timeout)
        elif args.action == "checkpoint":
            result = lab.checkpoint(args.guest, args.name)
        else:
            result = lab.restore(args.guest, args.checkpoint)
        print(json.dumps(result, indent=2))
        return result.get("exit_code", 0)
    except Exception as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
