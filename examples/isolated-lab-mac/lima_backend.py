"""Exact, private Lima/VZ enrollment; no host GUI, mounts or implicit recovery."""
import json
import os
from pathlib import Path
import platform

from contracts import digest, identifier


def command(config, *args):
    """Only the enrolled binary and private instance namespace are admitted."""
    cli = Path(config["lima_cli"])
    home = Path(config["lima_home"])
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError("The VZ backend requires this Arm Mac")
    if cli.is_symlink() or digest(cli.read_bytes()) != config["lima_cli_sha256"]:
        raise ValueError("Enrolled Lima binary changed")
    if home.is_symlink() or str(home.resolve(strict=True)) != str(home):
        raise ValueError("Enrolled Lima namespace changed")
    st = home.stat()
    if st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ValueError("Lima namespace requires the local owner and mode 700")
    return ["/usr/bin/env", "LIMA_HOME=" + str(home), str(cli), "--tty=false", *args]


def observe(config, checked):
    name = identifier(config["instance_name"])
    raw = checked(command(config, "list", "--all-fields", "--json", name))
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if len(rows) != 1:
        raise ValueError("Expected one exact enrolled Lima instance")
    row = rows[0]
    bundle = Path(row["dir"])
    if (row["name"] != name or bundle.is_symlink()
            or str(bundle.resolve(strict=True)) != config["bundle_path"]
            or bundle.parent != Path(config["lima_home"])):
        raise ValueError("Lima instance identity/path changed")
    for filename, key in (("vz-identifier", "vz_identifier_sha256"), ("lima.yaml", "lima_yaml_sha256")):
        p = bundle / filename
        if p.is_symlink() or digest(p.read_bytes()) != config[key]:
            raise ValueError("Enrolled VM identity or isolation configuration changed")
    guest = row["config"]
    if (row["vmType"] != "vz" or row["arch"] != "aarch64"
            or guest["os"] != "Linux" or guest.get("plain") is not True
            or guest.get("mounts", []) or guest.get("additionalDisks", [])
            or guest.get("networks", []) or guest["rosetta"].get("enabled")
            or guest["audio"]["device"] != "none" or guest["video"]["display"] != "none"
            or guest["ssh"].get("forwardAgent") or guest["ssh"].get("forwardX11")
            or guest["ssh"].get("loadDotSSHPubKeys")
            or guest["containerd"].get("system") or guest["containerd"].get("user")):
        raise ValueError("Enrolled guest isolation is not intact")
    if any(row[key] != config["resources"][key] for key in ("cpus", "memory", "disk")):
        raise ValueError("Enrolled resource limits changed")
    if row["status"] == "Running" and (row.get("sshAddress") != "127.0.0.1"
            or row.get("sshLocalPort") != config.get("bootstrap_ssh_port", config["ssh_port"])):
        raise ValueError("Enrolled loopback transport changed")
    return str(Path(config["lima_cli"])), row["status"].lower(), bundle
