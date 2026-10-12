"""Provision one fresh private Linux Arm guest. Existing state is never replaced.

Run only on an Arm Mac. Failed stages retain admission/effect receipts; inspect
the same job before repair. This is not a general-purpose host command tool.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import posixpath
import socket
import subprocess
import tarfile
import time
import urllib.request
import uuid

from contracts import canonical, digest, publish, read_private, sign, authenticate
from mac_lab import DEFAULT_ROOT, MacLab, bounded

RELEASE = "2.2.1"
ARCHIVE_SHA = "9e9eacce88f37e185c346bad73aa6136f738d8cdf8c3bb23cd42b071824bc66e"
CLI_SHA = "6d32fb0f880c0ea750434f2ac855a3f2129126752a301ce4d88adbd2fa599e1e"
IMAGE = "https://cloud-images.ubuntu.com/minimal/releases/noble/release-20261001/ubuntu-24.04-minimal-cloudimg-arm64.img"
IMAGE_SHA = "fbf6b15c50c474dc6dee5b3c74da212bb687a2625e877227828e6492d88dc151"
FILES = ("contracts.py", "guest_bridge.py", "install-linux-guest.sh", "guest-sshd.conf",
         "isolatedlab-sshd.service", "install-bridge-ssh.sh")
UPSTREAM = ("guest_agent.py", "desktop_agent.py", "desktop_demo.py")


def wait_ssh_banner(port, timeout=15):
    """Observe forwarding readiness without sending an authenticated operation."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1) as stream:
                stream.settimeout(1)
                if stream.recv(256).startswith(b"SSH-2.0-"):
                    return
        except OSError:
            pass
        time.sleep(.2)
    raise TimeoutError("SSH forwarding readiness unresolved; no protocol request sent")


def install_tool(root):
    target = root / "tools" / ("lima-" + RELEASE)
    if target.exists():
        if digest((target / "bin/limactl").read_bytes()) != CLI_SHA:
            raise ValueError("Existing Lima installation differs; preserve and inspect")
        return target / "bin/limactl"
    intake = root / "intake/lima"
    intake.mkdir(parents=True, mode=0o700, exist_ok=True)
    archive = intake / ("lima-" + RELEASE + ".tar.gz")
    if archive.exists():
        raise FileExistsError("Existing download effects need inspection before retry")
    url = "https://github.com/lima-vm/lima/releases/download/v" + RELEASE + "/lima-" + RELEASE + "-Darwin-arm64.tar.gz"
    with urllib.request.urlopen(url, timeout=60) as src, archive.open("xb") as out:
        while True:
            data = src.read(1024 * 1024)
            if not data:
                break
            out.write(data)
    if digest(archive.read_bytes()) != ARCHIVE_SHA:
        raise ValueError("Upstream Lima archive integrity failure")
    with tarfile.open(archive) as packet:
        members = []
        names = set()
        for member in packet.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or str(path).casefold() in names:
                raise ValueError("Unsafe or colliding upstream archive entry")
            names.add(str(path).casefold())
            if member.issym():
                link = posixpath.normpath(posixpath.join(posixpath.dirname(member.name), member.linkname))
                if member.name != "./share/doc/lima/templates" or link != "share/lima/templates":
                    raise ValueError("Unexpected upstream archive link")
                continue  # known optional documentation link, never installed
            if not (member.isfile() or member.isdir()):
                raise ValueError("Special upstream archive entry")
            members.append(member)
        target.mkdir(parents=True, mode=0o700, exist_ok=False)
        for member in members:
            path = target / member.name
            if member.isdir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as out:
                    out.write(packet.extractfile(member).read())
                path.chmod(member.mode & 0o777)
    if digest((target / "bin/limactl").read_bytes()) != CLI_SHA:
        raise ValueError("Installed Lima binary integrity failure")
    return target / "bin/limactl"


def prepare(root):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise ValueError("This preparation requires an Arm Mac")
    root = root.resolve()
    private = root / "private"
    private.mkdir(parents=True, mode=0o700, exist_ok=True)
    if private.stat().st_uid != os.getuid() or private.stat().st_mode & 0o077:
        raise ValueError("Private local state requires mode 700 and local ownership")
    # Admission is exclusive before installation/provisioning effects.
    admission = canonical({"schema": 1, "id": uuid.uuid4().hex})
    publish(private, "lima-preparation-admitted.json", admission, digest(admission))
    if (private / "config.json").exists() or (private / "lima").exists():
        raise FileExistsError("Existing lab preserved; inspect its binding rather than provision another")
    cli = install_tool(root)
    home = private / "lima"
    home.mkdir(mode=0o700)
    identity = str(uuid.uuid4())
    name = "il-" + identity[:8]
    if len(str(home / name / "ssh.sock.1234567890123456")) >= 104:
        raise ValueError("Selected private root exceeds the macOS UNIX socket path limit")
    sockets = []
    for _ in range(2):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); sockets.append(s)
    bootstrap_port, bridge_port = [s.getsockname()[1] for s in sockets]
    for s in sockets:
        s.close()
    yaml = f'''vmType: vz
arch: aarch64
images:
- location: {IMAGE}
  arch: aarch64
  digest: sha256:{IMAGE_SHA}
cpus: 2
memory: 4GiB
disk: 12GiB
plain: true
mounts: []
additionalDisks: []
networks: []
containerd: {{system: false, user: false}}
rosetta: {{enabled: false}}
ssh: {{localPort: {bootstrap_port}, loadDotSSHPubKeys: false, forwardAgent: false, forwardX11: false, overVsock: false}}
portForwards:
- {{guestPort: 2222, hostPort: {bridge_port}, hostIP: 127.0.0.1, static: true}}
video: {{display: none}}
audio: {{device: none}}
user: {{name: lab, uid: 1000, home: /home/lab, shell: /bin/bash, comment: isolatedLab owned Linux user}}
'''
    data = yaml.encode()
    publish(private, "lima-linux.yaml", data, digest(data))
    env = ["/usr/bin/env", "LIMA_HOME=" + str(home), str(cli), "--tty=false"]

    def job(stage, args, timeout=60, data=None):
        ident = uuid.uuid4().hex
        record = {"stage": stage, "id": ident, "mutation_may_have_effects": True}
        raw = canonical(record)
        publish(private, "job-" + ident + ".json", raw, digest(raw))
        result = bounded(args, timeout=timeout, data=data)
        raw = canonical(result)
        publish(private, "job-result-" + ident + ".json", raw, digest(raw))
        if result["exit_code"] or result["timed_out"] or result["truncated"]:
            raise RuntimeError(stage + " failed; inspect retained job " + ident + " before any retry")
        return result["stdout"]

    job("validate", env + ["validate", str(private / "lima-linux.yaml")])
    job("create", env + ["create", "--name=" + name, str(private / "lima-linux.yaml")], 300)
    job("cold-start", env + ["start", name], 120)
    fresh_key = os.urandom(32)
    publish(private, "transport.key", fresh_key, digest(fresh_key))
    job("fresh-ssh-identity", ["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private / "guest_ed25519")])
    files = {n: base64.b64encode((Path(__file__).parent / n).read_bytes()).decode() for n in FILES}
    files.update({n: base64.b64encode((Path(__file__).parent / "upstream" / n).read_bytes()).decode() for n in UPSTREAM})
    payload = {"files": files, "vm_uuid": identity,
               "key": base64.b64encode(read_private(private / "transport.key")).decode(),
               "pub": (private / "guest_ed25519.pub").read_text().strip()}
    bootstrap = '''import sys,json,pathlib,os,base64,platform
assert platform.system()=="Linux" and platform.machine()=="aarch64" and os.getuid()==1000
assert pathlib.Path.home()==pathlib.Path("/home/lab")
r=json.loads(sys.stdin.buffer.read())
state=pathlib.Path.home()/".local/state/isolatedlab-mac";state.mkdir(parents=True,mode=0o700,exist_ok=False)
agent=pathlib.Path.home()/"agent";agent.mkdir(mode=0o700,exist_ok=False)
for name,value in r["files"].items():
 assert "/" not in name and ".." not in name
 p=agent/name
 with p.open("xb") as f:f.write(base64.b64decode(value,validate=True))
 p.chmod(0o600)
for name,value in [("transport.key",base64.b64decode(r["key"],validate=True)),("enrollment.json",json.dumps({"schema":1,"vm_uuid":r["vm_uuid"],"guest_os":"linux","guest_arch":"arm64"}).encode()),("bridge-authorized-keys",("restrict "+r["pub"]+"\\n").encode())]:
 p=state/name
 with p.open("xb") as f:f.write(value)
 p.chmod(0o600)
print("FRESH_GUEST_ENROLLMENT_PASS")
'''
    guest = env + ["shell", name]
    job("bootstrap", guest + ["/usr/bin/python3", "-c", bootstrap], 30, canonical(payload))
    job("guest-dependencies", guest + ["/bin/sh", "/home/lab/agent/install-linux-guest.sh"], 600)
    job("dedicated-ssh-service", guest + ["/bin/sh", "/home/lab/agent/install-bridge-ssh.sh"], 60)
    host_key = job("read-service-public-key", guest + ["/bin/cat", "/etc/ssh/isolatedlab_host_ed25519.pub"]).strip()
    if not host_key.startswith("ssh-ed25519 "):
        raise ValueError("Unexpected guest service host key")
    data = ("[127.0.0.1]:" + str(bridge_port) + " " + host_key + "\n").encode()
    publish(private, "known_hosts", data, digest(data))
    bundle = home / name
    config = {"schema": 1, "backend": "lima", "vm_uuid": identity, "instance_name": name,
              "bundle_path": str(bundle), "lima_home": str(home), "lima_cli": str(cli), "lima_cli_sha256": CLI_SHA,
              "guest_os": "linux", "guest_arch": "arm64", "transport": "ssh", "ssh_port": bridge_port,
              "bootstrap_ssh_port": bootstrap_port, "guest_bridge_port": 2222,
              "vz_identifier_sha256": digest((bundle / "vz-identifier").read_bytes()),
              "lima_yaml_sha256": digest((bundle / "lima.yaml").read_bytes()),
              "resources": {"cpus": 2, "memory": 4294967296, "disk": 12884901888},
              "transport_accepted": False, "lifecycle_accepted": False}
    raw = canonical(config); publish(private, "config.json", raw, digest(raw))
    lab = MacLab(root)
    owner = "enrollment-" + identity[:8]
    lab.reserve(owner)

    def probe():
        lab.vm()  # exact identity, configuration, resources and loopback checks
        wait_ssh_banner(bridge_port)
        request = {"schema": 1, "id": uuid.uuid4().hex, "owner": owner, "vm_uuid": identity, "op": "system.status"}
        ssh = ["/usr/bin/ssh", "-F", "/dev/null", "-T", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
               "-o", "StrictHostKeyChecking=yes", "-o", "ClearAllForwardings=yes",
               "-o", "UserKnownHostsFile=" + str(private / "known_hosts"), "-i", str(private / "guest_ed25519"),
               "-p", str(bridge_port), "lab@127.0.0.1", "/home/lab/agent/venv/bin/python /home/lab/agent/guest_bridge.py"]
        raw = job("signed-identity-probe", ssh, 30, canonical(sign(request, lab.key)))
        response = authenticate(json.loads(raw), lab.key)
        if not response.get("ok") or (response["id"], response["vm_uuid"], response["owner"]) != (request["id"], identity, owner):
            raise ValueError("Fresh guest probe failed identity or result validation")
        raw = canonical(response); publish(private, "probe-" + request["id"] + ".json", raw, digest(raw))
    probe()
    job("normal-stop", env + ["stop", name], 60)
    if lab.vm()[1] != "stopped":
        raise ValueError("Shutdown state unresolved")
    job("second-cold-start", env + ["start", name], 120)
    probe()  # persistent host-key pin and authenticated guest identity after cold boot
    config.update(transport_accepted=True, lifecycle_accepted=True)
    raw = canonical(config)
    # Exclusive preparation owns this just-created file; verify prior bytes before updating gates.
    if read_private(private / "config.json") != canonical(lab.config):
        raise ValueError("Concurrent enrollment change; preserve it")
    tmp = private / ("config-accepted-" + uuid.uuid4().hex)
    tmp.write_bytes(raw); tmp.chmod(0o600); os.replace(tmp, private / "config.json")
    from accept_linux import run
    if run(root, owner):
        raise RuntimeError("Selected guest runtime failed; reservation preserved")
    MacLab(root).release(owner)
    return {"prepared": True, "backend": "lima-vz", "guest": "linux-arm64", "stopped": True,
            "human_interval": "NOT_RUN", "fresh_chat": "NOT_RUN", "backup_restore": "NOT_RUN"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    a = p.parse_args()
    print(json.dumps(prepare(a.root), indent=2))
