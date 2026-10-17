"""Explicit fresh-machine Linux preparation using reviewed dependency hashes.

Download/extract tools privately, create a fresh key/config/disk. Never start a VM.
Existing runtime/configuration is preserved rather than overwritten or upgraded.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
import zipfile

from portable_setup import dedicated_root, digest, read_json, save_json, setup_lock


def fetch(entry, downloads, cache=None):
    target = downloads / entry["name"]
    if Path(entry["name"]).name != entry["name"] or not entry["url"].startswith("https://"):
        raise ValueError("Invalid locked dependency")
    if target.exists():
        if digest(target) != entry["sha256"]:
            raise RuntimeError("Existing dependency hash mismatch; preserve it and diagnose")
        return target
    if cache and (Path(cache) / entry["name"]).is_file():
        origin = Path(cache) / entry["name"]
        if digest(origin) != entry["sha256"]:
            raise RuntimeError("Selected cache dependency hash mismatch")
        temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".part")
        shutil.copyfile(origin, temporary)
    else:
        temporary = target.with_name(target.name + "." + uuid.uuid4().hex + ".part")
        deadline = time.monotonic() + 600
        request = urllib.request.Request(entry["url"], headers={"User-Agent": "isolatedLab/0.4.0"})
        with urllib.request.urlopen(request, timeout=30) as response, temporary.open("xb") as out:
            if not response.url.startswith("https://"):
                raise RuntimeError("Dependency redirected away from HTTPS")
            total = 0
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > entry["max_bytes"] or time.monotonic() > deadline:
                    raise RuntimeError("Dependency size/deadline exceeded")
                out.write(block)
    if temporary.stat().st_size > entry["max_bytes"] or digest(temporary) != entry["sha256"]:
        raise RuntimeError("Downloaded dependency changed; partial file preserved, no execution")
    os.replace(temporary, target)
    return target


def run(argv, timeout=120):
    result = subprocess.run([str(a) for a in argv], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=timeout,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError("Preparation command failed: " + result.stderr[-1000:] + result.stdout[-1000:])
    return result.stdout


def choose_ports(first_display=41):
    # Choose a coherent free triple. Lab.start repeats binding checks before launch.
    for display in range(first_display, 100):
        ports = (22200 + display, 22400 + display, 5900 + display)
        held = []
        try:
            for port in ports:
                sock = socket.socket()
                held.append(sock)
                sock.bind(("127.0.0.1", port))
            return ports[0], ports[1], display
        except OSError:
            pass
        finally:
            for sock in held:
                sock.close()
    raise RuntimeError("No free private guest port triple")


def configure(root):
    if (root / "private/config.json").exists():
        raise RuntimeError("Existing machine configuration preserved; use its status instead of fresh preparation")
    template = read_json(Path(__file__).with_name("config.example.json"))
    # Rebind every path from the portable template, never assume another drive/user.
    def relocate(value):
        if isinstance(value, dict):
            return {k: relocate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [relocate(v) for v in value]
        if isinstance(value, str) and value.startswith("D:/CodexLab"):
            return str(root).replace("\\", "/") + value[len("D:/CodexLab"):]
        return value
    config = relocate(template)
    config["vbox"] = str(Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Oracle/VirtualBox/VBoxManage.exe")
    ssh_port, qmp_port, display = choose_ports()
    config["guests"]["linux"].update(ssh_port=ssh_port, qmp_port=qmp_port, vnc_display=display)
    config["guests"]["windows"]["name"] = "CodexLab-Windows-" + uuid.uuid4().hex[:8]
    key = Path(config["guests"]["linux"]["key"])
    if key.exists() or key.with_suffix(".pub").exists():
        raise RuntimeError("Existing guest key preserved; reconcile partial preparation")
    run([shutil.which("ssh-keygen.exe"), "-q", "-t", "ed25519", "-N", "", "-C", "isolatedLab", "-f", key], 30)
    # Restrict private files to this user by SID; no localized account-name guessing.
    sid = run(["whoami.exe", "/user", "/fo", "csv", "/nh"], 10).strip().split(",")[-1].strip('"')
    if not sid.startswith("S-1-"):
        raise RuntimeError("Could not determine current user SID")
    run(["icacls.exe", key, "/inheritance:r", "/grant:r", "*" + sid + ":F"], 20)
    save_json(root / "private/config.json", config)
    return config


def prepare(root, cache=None):
    if os.name != "nt" or platform.machine().lower() not in ("amd64", "x86_64"):
        raise RuntimeError("This preparation adapter supports Windows x64 only")
    if not shutil.which("ssh.exe") or not shutil.which("ssh-keygen.exe"):
        raise RuntimeError("Windows OpenSSH Client is required; preserve runtime and resolve this prerequisite")
    root = dedicated_root(root)
    if not (root / "private/portable-install.json").is_file():
        raise RuntimeError("Install and verify the source bundle first")
    if (root / "private/config.json").exists():
        raise RuntimeError("Existing runtime preserved; fresh preparation refused")
    if shutil.disk_usage(root).free < 15 * 1024**3:
        raise RuntimeError("Preparation requires at least 15 GiB free")
    with setup_lock(root):
        downloads = root / "downloads"
        downloads.mkdir(exist_ok=True)
        entries = read_json(Path(__file__).with_name("dependencies.lock.json"))["downloads"]
        files = {}
        for entry in entries:
            print(json.dumps({"stage": "verified dependency", "name": entry["name"]}), flush=True)
            files[entry["name"]] = fetch(entry, downloads, cache)
        tools = root / "tools"
        tools.mkdir(exist_ok=True)
        # Exe installers are extracted, not installed into the host.
        seven = tools / "7zip"
        qemu = tools / "qemu"
        if seven.exists() or qemu.exists():
            raise RuntimeError("Prepared tool directory exists; reconcile partial preparation before replay")
        run([files["7zr.exe"], "x", files["7z2604-x64.exe"], "-o" + str(seven), "-y"], 60)
        run([seven / "7z.exe", "x", files["qemu-w64-setup-20260811.exe"], "-o" + str(qemu), "-y"], 180)
        if "11.1.0" not in run([qemu / "qemu-system-x86_64.exe", "--version"], 20):
            raise RuntimeError("Unexpected QEMU version")
        packages = tools / "python-packages"
        # The pinned pure-Python wheel is imported directly. No global pip mutation.
        packages.mkdir(exist_ok=True)
        wheel = files["pycdlib-1.14.0-py2.py3-none-any.whl"]
        private_wheel = packages / wheel.name
        shutil.copyfile(wheel, private_wheel)
        # prepare_linux.py expects this import directory; a .pth is not automatically
        # processed after sys.path insertion, so extract only the pycdlib package.
        with zipfile.ZipFile(private_wheel) as z:
            for i in z.infolist():
                parts = i.filename.split("/")
                if parts[0] != "pycdlib" or i.is_dir():
                    continue
                if any(x in ("", ".", "..") for x in parts) or "\\" in i.filename or ":" in i.filename:
                    raise ValueError("Unsafe dependency wheel path")
                target = packages.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(i))
        save_json(root / "private/downloads-receipt.json", {
            "ubuntu_sha256": next(e["sha256"] for e in entries if e["name"] == "ubuntu-noble-minimal.img"),
            "locked_hashes": {e["name"]: e["sha256"] for e in entries}})
        config = configure(root)
        run([sys.executable, Path(__file__).with_name("prepare_linux.py"), "--config", root / "private/config.json"], 60)
        save_json(root / "private/preparation.json", {"schema": 1, "state": "PREPARED_NOT_RUNTIME_ACCEPTED",
                  "host": platform.system(), "architecture": platform.machine(), "python": platform.python_version(),
                  "dependency_hashes": {e["name"]: e["sha256"] for e in entries}, "guest_started": False})
        return {"prepared": True, "VM_started": False, "disk": config["guests"]["linux"]["disk"],
                "next": "Start/wait-ready, deploy guest helper, install guest providers, run acceptance, cleanly stop, then register MCP"}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--lab-root", required=True)
    p.add_argument("--cache-dir", help="Optional selected downloads cache; every byte is hash-checked")
    args = p.parse_args()
    try:
        print(json.dumps(prepare(args.lab_root, args.cache_dir), indent=2))
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error), "automatic_replay": False}))
        sys.exit(2)
