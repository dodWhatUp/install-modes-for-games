"""Re-enroll an authenticated stopped checkpoint in a separate private Lima namespace.

Never replaces the original guest. Failed stages preserve receipts and effects.
The staging tree must come from stopped_backup.restore; all bytes are rechecked.
"""
import argparse
import base64
import hmac
import json
import os
from pathlib import Path
import socket
import uuid

from contracts import authenticate, canonical, digest, publish, read_private, sign
from mac_lab import MacLab, bounded
from prepare_lima import CLI_SHA, wait_ssh_banner
from stopped_backup import BUNDLE, mac_file, sha_file


def restore_guest(original_root, backup, keyfile, staging, root):
    original = MacLab(original_root)
    if original.vm()[1] != "stopped" or (original.private / "reservation.json").exists():
        raise ValueError("Original guest must remain stopped and unreserved")
    receipt = json.loads((backup / "BACKUP-RECEIPT.json").read_bytes())
    metadata = receipt["metadata"]
    archive = backup / "stopped-backup.enc"
    password = read_private(keyfile)
    if sha_file(archive) != metadata["cipher_sha256"] or not hmac.compare_digest(
            mac_file(password, metadata, archive), receipt["hmac_sha256"]):
        raise ValueError("Checkpoint authentication failed")
    expected = {x["path"]: x for x in metadata["files"]}
    actual = {p.relative_to(staging).as_posix() for p in staging.rglob("*") if p.is_file()}
    if len(expected) != len(metadata["files"]) or actual != set(expected):
        raise ValueError("Restored staging file set differs")
    for name, entry in expected.items():
        from contracts import relative
        relative(name)
        p = staging / name
        if p.is_symlink() or p.stat().st_size != entry["bytes"] or sha_file(p) != entry["sha256"]:
            raise ValueError("Restored staging bytes differ")
    root = root.resolve()
    root.mkdir(mode=0o700, exist_ok=False)
    private = root / "private"; private.mkdir(mode=0o700)
    home = private / "lima"; home.mkdir(mode=0o700)
    cli = Path(original.config["lima_cli"])
    if digest(cli.read_bytes()) != CLI_SHA:
        raise ValueError("Lima binary differs")
    env = ["/usr/bin/env", "LIMA_HOME=" + str(home), str(cli), "--tty=false"]

    def job(stage, argv, timeout=60, data=None):
        ident = uuid.uuid4().hex
        raw = canonical({"stage": stage, "id": ident, "effects_may_exist": True})
        publish(private, "job-" + ident + ".json", raw, digest(raw))
        result = bounded(argv, timeout, data)
        raw = canonical(result); publish(private, "job-result-" + ident + ".json", raw, digest(raw))
        if result["exit_code"] or result["timed_out"] or result["truncated"]:
            raise RuntimeError(stage + " failed; inspect retained job " + ident)
        return result["stdout"]

    # Copy-on-write keeps the verified byte staging and original guest intact.
    imported = home / "rs"; imported.mkdir(mode=0o700)
    for n in BUNDLE:
        job("import-" + n, ["/bin/cp", "-c", str(staging / "bundle" / n), str(imported / n)])
    cfg = home / "_config"; cfg.mkdir(mode=0o700)
    for n in ("user", "user.pub"):
        data = (staging / "lima-bootstrap" / n).read_bytes()
        publish(cfg, n, data, digest(data))
    socks = []
    for _ in range(2):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); socks.append(s)
    bootstrap_port, bridge_port = [s.getsockname()[1] for s in socks]
    for s in socks: s.close()
    identity = str(uuid.uuid4()); name = "il-" + identity[:8]
    if len(str(home / name / "ssh.sock.1234567890123456")) >= 104:
        raise ValueError("Restore root is too long for macOS sockets")
    job("fresh-vz-clone", env + ["clone", "rs", name, "--ssh-port=" + str(bootstrap_port),
                                "--set", ".portForwards[0].hostPort = " + str(bridge_port)])
    bundle = home / name
    if (bundle / "vz-identifier").read_bytes():
        raise ValueError("Clone did not clear the old VZ identity")
    job("restored-cold-start", env + ["start", name], 120)
    if digest((bundle / "vz-identifier").read_bytes()) == original.config["vz_identifier_sha256"]:
        raise ValueError("Restored VM did not acquire a fresh VZ identity")
    fresh = os.urandom(32); publish(private, "transport.key", fresh, digest(fresh))
    job("fresh-client-key", ["/usr/bin/ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(private / "guest_ed25519")])
    payload = {"vm_uuid": identity, "key": base64.b64encode(fresh).decode(),
               "pub": (private / "guest_ed25519.pub").read_text().strip(),
               "source": {n: entry["sha256"] for n, entry in expected.items() if n.startswith("source/")}}
    guest = env + ["shell", name]
    rotate = '''import sys,json,pathlib,os,platform,base64,hashlib
assert platform.system()=="Linux" and platform.machine()=="aarch64" and os.getuid()==1000
assert pathlib.Path.home()==pathlib.Path("/home/lab")
r=json.loads(sys.stdin.buffer.read()); home=pathlib.Path.home()
for n,h in r["source"].items():
 p=home/"agent"/pathlib.Path(n).name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==h
for old in [home/".local/state/isolatedlab-mac",home/".local/state/codex-lab"]:
 if old.exists():old.rename(old.with_name(old.name+"-before-"+r["vm_uuid"]))
state=home/".local/state/isolatedlab-mac";state.mkdir(mode=0o700)
for n,v in [("transport.key",base64.b64decode(r["key"],validate=True)),("enrollment.json",json.dumps({"schema":1,"vm_uuid":r["vm_uuid"],"guest_os":"linux","guest_arch":"arm64"}).encode()),("bridge-authorized-keys",("restrict "+r["pub"]+"\\n").encode())]:
 p=state/n
 with p.open("xb") as f:f.write(v)
 p.chmod(0o600)
print("RESTORED_SOURCE_AND_FRESH_ENROLLMENT_PASS")
'''
    job("verify-source-and-rotate-enrollment", guest + ["/usr/bin/python3", "-c", rotate], data=canonical(payload))
    job("stop-restored-service", guest + ["sudo", "-n", "/usr/bin/systemctl", "stop", "isolatedlab-sshd.service"])
    for n in ("isolatedlab_host_ed25519", "isolatedlab_host_ed25519.pub", "sshd_config.isolatedlab"):
        job("preserve-old-service-" + n, guest + ["sudo", "-n", "/bin/mv", "/etc/ssh/" + n, "/etc/ssh/" + n + "-before-" + identity])
    job("install-fresh-service", guest + ["/bin/sh", "/home/lab/agent/install-bridge-ssh.sh"])
    pub = job("read-public-host-key", guest + ["/bin/cat", "/etc/ssh/isolatedlab_host_ed25519.pub"]).strip()
    if not pub.startswith("ssh-ed25519 "): raise ValueError("Unexpected public host key")
    data = ("[127.0.0.1]:" + str(bridge_port) + " " + pub + "\n").encode()
    publish(private, "known_hosts", data, digest(data))
    config = dict(original.config, vm_uuid=identity, instance_name=name, bundle_path=str(bundle), lima_home=str(home),
                  ssh_port=bridge_port, bootstrap_ssh_port=bootstrap_port,
                  vz_identifier_sha256=digest((bundle / "vz-identifier").read_bytes()),
                  lima_yaml_sha256=digest((bundle / "lima.yaml").read_bytes()),
                  transport_accepted=False, lifecycle_accepted=False)
    raw = canonical(config); publish(private, "config.json", raw, digest(raw))
    lab = MacLab(root); owner = "restore-" + identity[:8]; lab.reserve(owner)

    def probe():
        lab.vm()
        wait_ssh_banner(bridge_port)
        req = {"schema": 1, "id": uuid.uuid4().hex, "vm_uuid": identity, "owner": owner, "op": "system.status"}
        ssh = ["/usr/bin/ssh", "-F", "/dev/null", "-T", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
               "-o", "StrictHostKeyChecking=yes", "-o", "ClearAllForwardings=yes",
               "-o", "UserKnownHostsFile=" + str(private / "known_hosts"), "-i", str(private / "guest_ed25519"),
               "-p", str(bridge_port), "lab@127.0.0.1", "/home/lab/agent/venv/bin/python /home/lab/agent/guest_bridge.py"]
        result = authenticate(json.loads(job("signed-restored-probe", ssh, data=canonical(sign(req, fresh)))), fresh)
        if not result.get("ok") or (result["id"], result["vm_uuid"], result["owner"]) != (req["id"], identity, owner):
            raise ValueError("Restored guest signed identity mismatch")
    probe()
    job("restored-normal-stop", env + ["stop", name])
    if lab.vm()[1] != "stopped": raise ValueError("Restored shutdown unresolved")
    job("restored-second-cold-start", env + ["start", name], 120); probe()
    config.update(transport_accepted=True, lifecycle_accepted=True)
    if read_private(private / "config.json") != canonical(lab.config): raise ValueError("Concurrent restore binding edit")
    temp = private / "accepted-config.tmp"; temp.write_bytes(canonical(config)); temp.chmod(0o600)
    os.replace(temp, private / "config.json")
    from accept_linux import run
    if run(root, owner): raise RuntimeError("Restored runtime acceptance failed; preserve effects")
    MacLab(root).release(owner)
    if original.vm()[1] != "stopped": raise ValueError("Original changed state")
    return {"restored_runtime": "PASS", "fresh_vm_and_protocol_identity": True, "fresh_ssh_and_transport_keys": True,
            "cold_start_twice": True, "selected_checks": 37, "normal_stop": True, "original_preserved_stopped": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for n in ("original-root", "backup", "keyfile", "staging", "root"): p.add_argument("--" + n, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(restore_guest(a.original_root, a.backup, a.keyfile, a.staging, a.root), indent=2))
