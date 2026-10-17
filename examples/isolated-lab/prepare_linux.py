"""Prepare a new Ubuntu QEMU guest without host installation or desktop input."""
import argparse
import io
import json
from pathlib import Path
import subprocess
import sys
from lab import sha256


def prepare(config_path):
    config = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
    root = Path(config["root"]).resolve()
    guest = config["guests"]["linux"]
    disk = Path(guest["disk"]).resolve()
    seed = Path(guest["seed"]).resolve()
    if root not in disk.parents or root not in seed.parents or disk.exists() or seed.exists():
        raise ValueError("Guest disk and seed must both be new and inside the private lab root")
    base = root / "downloads" / "ubuntu-noble-minimal.img"
    receipt = json.loads((root / "private" / "downloads-receipt.json").read_text(encoding="utf-8-sig"))
    if sha256(base) != receipt["ubuntu_sha256"]:
        raise ValueError("Ubuntu image no longer matches the verified download receipt")
    key = Path(guest["key"] + ".pub").read_text().strip()
    if not key.startswith("ssh-ed25519 "):
        raise ValueError("Expected the dedicated lab SSH public key")
    disk.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([config["qemu_img"], "create", "-f", "qcow2", "-F", "qcow2",
                    "-b", str(base), str(disk), "32G"], check=True, timeout=30)
    sys.path.insert(0, str(root / "tools" / "python-packages"))
    import pycdlib
    user_data = f"""#cloud-config
hostname: codex-lab-linux
manage_etc_hosts: true
users:
  - name: lab
    groups: [sudo]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: true
    ssh_authorized_keys:
      - {key}
ssh_pwauth: false
disable_root: true
package_update: true
packages: [openssh-server, python3, git, build-essential, xvfb, xdotool, x11-apps, xterm, xauth, imagemagick]
runcmd:
  - [systemctl, enable, --now, ssh]
  - [mkdir, -p, /home/lab/work, /home/lab/artifacts]
  - [chown, -R, 'lab:lab', /home/lab/work, /home/lab/artifacts]
  - [sh, -c, 'printf ready > /home/lab/artifacts/bootstrap-ready']
final_message: Codex lab bootstrap completed after $UPTIME seconds
"""
    iso = pycdlib.PyCdlib()
    iso.new(interchange_level=3, joliet=3, vol_ident="CIDATA", rock_ridge="1.09")
    for filename, iso_name, content in [
        ("user-data", "USER_DAT.;1", user_data),
        ("meta-data", "META_DAT.;1", "instance-id: codex-lab-linux-v1\nlocal-hostname: codex-lab-linux\n")
    ]:
        data = content.encode()
        iso.add_fp(io.BytesIO(data), len(data), iso_path="/" + iso_name,
                   joliet_path="/" + filename, rr_name=filename)
    iso.write(guest["seed"])
    iso.close()
    print(json.dumps({"prepared": True, "disk": str(disk), "seed": guest["seed"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    prepare(parser.parse_args().config)
