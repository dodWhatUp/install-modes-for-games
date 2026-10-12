"""Private stopped Linux/VZ backup; authenticated encryption before any restore.

Credentials and disks stay outside Git/Drive. Restore into a new staging path,
then clone/re-enroll with a fresh identity; never replace the original guest.
"""
import argparse
import gzip
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import tarfile
import uuid

from contracts import canonical, read_private, relative
from mac_lab import DEFAULT_ROOT, MacLab

BLOCK = 1024 * 1024
BUNDLE = ("disk", "vz-efi", "vz-identifier", "lima.yaml", "lima-version", "cidata.iso", "cloud-config.yaml")
PRIVATE = ("config.json", "transport.key", "guest_ed25519", "known_hosts")


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(BLOCK), b""):
            h.update(chunk)
    return h.hexdigest()


def mac_file(key, metadata, path):
    h = hmac.new(hashlib.sha256(b"isolatedlab-backup-auth-v1" + key).digest(), canonical(metadata), hashlib.sha256)
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(BLOCK), b""):
            h.update(chunk)
    return h.hexdigest()


def make(root, destination):
    lab = MacLab(root)
    if lab.config["backend"] != "lima":
        raise ValueError("Only the measured Lima Linux bundle layout is supported")
    with lab.lock():
        if (lab.private / "reservation.json").exists() or lab.vm()[1] != "stopped":
            raise ValueError("Backup requires a stopped guest and no workflow reservation")
        destination.mkdir(parents=True, mode=0o700, exist_ok=False)
        token = uuid.uuid4().hex
        password = __import__("base64").urlsafe_b64encode(os.urandom(32))
        keyfile = lab.private / ("backup-key-" + token)
        with keyfile.open("xb") as f:
            f.write(password)
        keyfile.chmod(0o600)
        bundle = Path(lab.config["bundle_path"])
        files = {"bundle/" + n: bundle / n for n in BUNDLE}
        files.update({"private/" + n: lab.private / n for n in PRIVATE})
        files["lima-bootstrap/user"] = Path(lab.config["lima_home"]) / "_config/user"
        files["lima-bootstrap/user.pub"] = Path(lab.config["lima_home"]) / "_config/user.pub"
        # Preserve the matching actual guest bridge source, without profiles/settings.
        source = Path(__file__).parent
        for name in ("contracts.py", "guest_bridge.py", "guest-sshd.conf", "isolatedlab-sshd.service"):
            files["source/" + name] = source / name
        for name in ("guest_agent.py", "desktop_agent.py", "desktop_demo.py"):
            files["source/" + name] = source / "upstream" / name
        for path in files.values():
            if path.is_symlink() or not path.is_file():
                raise ValueError("Checkpoint input is not a regular selected file")
        metadata = {"schema": 1, "id": token, "backend": "lima-vz", "guest": "linux-arm64",
                    "stopped_verified": True, "files": [{"path": name, "bytes": p.stat().st_size, "sha256": sha_file(p)}
                                                          for name, p in sorted(files.items())]}
        temp = destination / "stopped-backup.enc.partial"
        with temp.open("xb") as encrypted:
            process = subprocess.Popen(["/usr/bin/openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2", "-iter", "200000",
                                        "-pass", "file:" + str(keyfile)], stdin=subprocess.PIPE,
                                       stdout=encrypted, stderr=subprocess.PIPE)
            try:
                with gzip.GzipFile(fileobj=process.stdin, mode="wb", compresslevel=1) as compressed:
                    with tarfile.open(fileobj=compressed, mode="w|") as archive:
                        for name, path in sorted(files.items()):
                            archive.add(path, arcname=name, recursive=False)
                process.stdin.close()
                error = process.stderr.read(4096)
                if process.wait(timeout=30):
                    raise RuntimeError("Checkpoint encryption failed; preserve partial effects: " + error.decode(errors="replace"))
                encrypted.flush(); os.fsync(encrypted.fileno())
            finally:
                if process.poll() is None:
                    process.terminate(); process.wait(timeout=3)
                for stream in (process.stdin, process.stderr):
                    if stream and not stream.closed:
                        stream.close()
        if lab.vm()[1] != "stopped":
            raise ValueError("Guest changed state during backup; preserve failed checkpoint")
        archive = destination / "stopped-backup.enc"
        temp.rename(archive)
        metadata.update(cipher_sha256=sha_file(archive), cipher_bytes=archive.stat().st_size,
                        encryption="AES-256-CBC/PBKDF2-200000 plus independent HMAC-SHA256 verified before decryption")
        receipt = {"metadata": metadata, "hmac_sha256": mac_file(password, metadata, archive)}
        p = destination / "BACKUP-RECEIPT.json"
        with p.open("xb") as f:
            f.write(canonical(receipt)); f.flush(); os.fsync(f.fileno())
        internal = lab.private / ("backup-locator-" + token + ".json")
        internal.write_bytes(canonical({"id": token, "backup": str(destination), "keyfile": str(keyfile)})); internal.chmod(0o600)
        return {"created": True, "id": token, "cipher_bytes": metadata["cipher_bytes"], "keyfile": str(keyfile),
                "backup": str(destination), "decryption_or_restore_not_yet_verified": True}


def restore(backup, keyfile, destination):
    receipt = json.loads((backup / "BACKUP-RECEIPT.json").read_bytes())
    metadata = receipt["metadata"]
    archive = backup / "stopped-backup.enc"
    password = read_private(keyfile)
    if sha_file(archive) != metadata["cipher_sha256"] or archive.stat().st_size != metadata["cipher_bytes"]:
        raise ValueError("Encrypted checkpoint integrity failure; no decryption performed")
    if not hmac.compare_digest(mac_file(password, metadata, archive), receipt["hmac_sha256"]):
        raise ValueError("Checkpoint authentication failed; no decryption performed")
    for x in metadata["files"]:
        relative(x["path"])
    expected = {x["path"]: x for x in metadata["files"]}
    if len(expected) != len(metadata["files"]):
        raise ValueError("Duplicate checkpoint manifest entries")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    process = subprocess.Popen(["/usr/bin/openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2", "-iter", "200000",
                                "-pass", "file:" + str(keyfile), "-in", str(archive)], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    seen = set()
    try:
        with gzip.GzipFile(fileobj=process.stdout, mode="rb") as compressed:
            with tarfile.open(fileobj=compressed, mode="r|") as packet:
                for member in packet:
                    relative(member.name)
                    name = member.name
                    if not member.isfile() or name in seen or name not in expected or member.size != expected[name]["bytes"]:
                        raise ValueError("Unexpected checkpoint member")
                    seen.add(name)
                    target = destination / name
                    target.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
                    h = hashlib.sha256()
                    with target.open("xb") as out:
                        stream = packet.extractfile(member)
                        while True:
                            chunk = stream.read(BLOCK)
                            if not chunk:
                                break
                            h.update(chunk)
                            if chunk == bytes(len(chunk)):
                                out.seek(len(chunk), os.SEEK_CUR)  # preserve sparse disk blocks
                            else:
                                out.write(chunk)
                        out.truncate(member.size); out.flush(); os.fsync(out.fileno())
                    target.chmod(0o600)
                    if h.hexdigest() != expected[name]["sha256"] or sha_file(target) != expected[name]["sha256"]:
                        raise ValueError("Restored checkpoint bytes differ")
        error = process.stderr.read(4096)
        if process.wait(timeout=30) or seen != set(expected):
            raise ValueError("Checkpoint decryption/member-set failure: " + error.decode(errors="replace"))
    finally:
        if process.poll() is None:
            process.terminate(); process.wait(timeout=3)
        for stream in (process.stdout, process.stderr):
            if stream and not stream.closed:
                stream.close()
    return {"restored_bytes_verified": True, "files": len(seen), "destination": str(destination),
            "VM_started": False, "fresh_clone_and_enrollment_required": True}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=("make", "restore"))
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--destination", type=Path, required=True)
    p.add_argument("--backup", type=Path)
    p.add_argument("--keyfile", type=Path)
    a = p.parse_args()
    print(json.dumps(make(a.root, a.destination) if a.action == "make" else restore(a.backup, a.keyfile, a.destination), indent=2))
