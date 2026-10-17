"""Prepare only a new, explicitly selected Windows 11 guest. No host GUI input."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from lab import Lab, write_json, sha256


def prepare(args):
    lab = Lab(args.config)
    guest = lab.guest("windows")
    iso = Path(args.iso).resolve()
    if not iso.is_file() or iso.suffix.lower() != ".iso":
        raise ValueError("Select legitimate Windows 11 installation media")
    if not Path(lab.config["vbox"]).is_file():
        raise RuntimeError("VirtualBox host installation is pending")
    preflight = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                                "(Get-CimInstance Win32_Processor).VirtualizationFirmwareEnabled"],
                               capture_output=True, text=True, timeout=15, check=True)
    if preflight.stdout.strip().lower() != "true":
        raise RuntimeError("Firmware virtualization must be enabled before provisioning")
    disk = lab.inside(guest["disk"])
    password_file = lab.inside(guest["password_file"])
    if disk.exists() or password_file.exists():
        raise RuntimeError("Existing Windows guest/private credential must be inspected; no overwrite")
    existing = lab.vbox("showvminfo", guest["name"], "--machinereadable")
    if existing.returncode == 0:
        raise RuntimeError("VM already registered; no overwrite")
    detect = lab.vbox("unattended", "detect", "--iso", str(iso), "--machine-readable", timeout=60)
    if detect.returncode:
        raise RuntimeError(detect.stderr.strip())
    if not any(x in detect.stdout.lower() for x in ["windows11", "windows 11"]):
        raise RuntimeError("Selected ISO was not detected as Windows 11; inspect media manually")
    if args.prepare_only:
        return {"prepared_only": True, "iso_sha256": sha256(iso),
                "detection": detect.stdout, "image_index": args.image_index,
                "media_kind": args.media_kind, "runtime_verified": False}
    additions = Path(lab.config["vbox"]).parent / "VBoxGuestAdditions.iso"
    if not additions.is_file():
        raise RuntimeError("Matching Guest Additions ISO is missing")
    disk.parent.mkdir(parents=True, exist_ok=True)
    password_file.write_text(secrets.token_urlsafe(24) + "!aA7", encoding="utf-8")
    steps = [
        ["createvm", "--name", guest["name"], "--basefolder", str(lab.root / "vms"),
         "--ostype", "Windows11_64", "--register"],
        ["modifyvm", guest["name"], "--memory", str(guest["memory_mb"]), "--cpus", str(guest["cpus"]),
         "--cpu-execution-cap", "75", "--firmware", "efi", "--tpm-type", "2.0",
         "--graphicscontroller", "vboxsvga", "--vram", "128", "--accelerate-3d", "off",
         "--nic1", "nat", "--clipboard-mode", "disabled", "--drag-and-drop", "disabled",
         "--audio-enabled", "off", "--usb", "off", "--usbehci", "off", "--usbxhci", "off",
         "--vrde", "off", "--boot1", "dvd", "--boot2", "disk", "--boot3", "none", "--boot4", "none"],
        ["createmedium", "disk", "--filename", str(disk), "--size", "65536", "--format", "VDI"],
        ["storagectl", guest["name"], "--name", "SATA", "--add", "sata", "--controller", "IntelAhci"],
        ["storageattach", guest["name"], "--storagectl", "SATA", "--port", "0", "--device", "0",
         "--type", "hdd", "--medium", str(disk)],
        ["unattended", "install", guest["name"], "--iso", str(iso), "--user", guest["user"],
         "--user-password-file", str(password_file), "--admin-password-file", str(password_file),
         "--full-user-name", "Lab", "--hostname", "codex-lab-windows.lab.invalid",
         "--install-additions", "--additions-iso", str(additions), "--image-index", str(args.image_index),
         "--locale", "en_US", "--country", "US", "--language", "en-US", "--time-zone", "Israel Standard Time",
         "--start-vm", "headless"]
    ]
    receipt = {"guest": "windows", "iso_sha256": sha256(iso), "media_kind": args.media_kind,
               "image_index": args.image_index, "steps_completed": 0, "runtime_verified": False}
    write_json(lab.private / "windows-provision.json", receipt)
    for step in steps:
        result = lab.vbox(*step, timeout=180)
        if result.returncode:
            receipt["failed_step"] = step[0]
            receipt["error"] = result.stderr
            write_json(lab.private / "windows-provision.json", receipt)
            raise RuntimeError("Provisioning stopped; preserve partial guest and inspect private receipt")
        receipt["steps_completed"] += 1
        write_json(lab.private / "windows-provision.json", receipt)
    guest["license"] = "evaluation_activation_pending" if args.media_kind == "evaluation" else "license_activation_pending"
    write_json(lab.config_path, lab.config)
    return receipt | {"installation_dispatched": True, "headless": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--iso", required=True)
    parser.add_argument("--media-kind", choices=["evaluation", "licensed"], required=True)
    parser.add_argument("--image-index", type=int, required=True)
    parser.add_argument("--prepare-only", action="store_true")
    try:
        print(json.dumps(prepare(parser.parse_args()), indent=2))
    except Exception as error:
        print(json.dumps({"error": type(error).__name__, "message": str(error)}))
        sys.exit(2)
