"""Mac command bridge. Candidate: actual Parallels/guest acceptance is required."""
import argparse
import base64
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time
import uuid

from contracts import (LIMIT, VERSION, authenticate, canonical, digest, identifier,
                       publish, read_private, selected, sign, validate, vm_id)

DEFAULT_ROOT = Path.home() / ".local/share/isolatedlab"
PARALLELS = Path("/Applications/Parallels Desktop.app/Contents/MacOS")


def bounded(argv, timeout=15, data=None):
    """No shell; bound output and clean only the locally spawned process group."""
    import selectors
    p = subprocess.Popen(argv, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    sel = selectors.DefaultSelector()
    output = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout
    timed_out = truncated = False
    try:
        # Current bridges carry at most 256 KiB. A selector also bounds blocked stdin.
        if data is not None:
            os.set_blocking(p.stdin.fileno(), False)
            sel.register(p.stdin, selectors.EVENT_WRITE, ("input", memoryview(data)))
        for name in output:
            stream = getattr(p, name)
            os.set_blocking(stream.fileno(), False)
            sel.register(stream, selectors.EVENT_READ, (name, None))
        while sel.get_map():
            if time.monotonic() >= deadline:
                timed_out = True
                break
            for item, _ in sel.select(min(.1, max(0, deadline - time.monotonic()))):
                name, remaining = item.data
                if name == "input":
                    try:
                        n = os.write(item.fd, remaining[:8192])
                        remaining = remaining[n:]
                    except BrokenPipeError:
                        remaining = b""
                    if remaining:
                        sel.modify(item.fileobj, selectors.EVENT_WRITE, (name, remaining))
                    else:
                        sel.unregister(item.fileobj)
                        item.fileobj.close()
                else:
                    chunk = os.read(item.fd, 8192)
                    if not chunk:
                        sel.unregister(item.fileobj)
                        item.fileobj.close()
                    else:
                        room = max(0, LIMIT - len(output[name]))
                        output[name].extend(chunk[:room])
                        truncated |= len(chunk) > room
        if not timed_out:
            try:
                p.wait(timeout=max(.01, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
    finally:
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            p.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait()
        sel.close()
        for stream in (p.stdin, p.stdout, p.stderr):
            if stream and not stream.closed:
                stream.close()
    return {"exit_code": p.returncode, "timed_out": timed_out, "truncated": truncated,
            **{k: bytes(v).decode("utf-8", errors="replace") for k, v in output.items()}}


def checked(argv, timeout=15, data=None):
    result = bounded(argv, timeout, data)
    if result["timed_out"] or result["truncated"] or result["exit_code"]:
        raise RuntimeError("Command failed or exceeded deadline/output limit; inspect private receipt before retry")
    return result["stdout"]


def trusted_cli():
    cli = PARALLELS / "prlctl"
    if platform.system() != "Darwin" or not cli.is_file():
        raise RuntimeError("Parallels Desktop is not installed on this Mac")
    checked(["/usr/bin/codesign", "--verify", "--strict", str(PARALLELS.parent.parent)])
    identity = bounded(["/usr/bin/codesign", "-dv", "--verbose=2", str(PARALLELS.parent.parent)])
    if "TeamIdentifier=4C6364ACXT" not in identity["stderr"]:
        raise RuntimeError("Unexpected Parallels signing identity")
    return str(cli)


def preflight():
    report = {"schema": 1, "version": VERSION, "host_os": platform.system(),
              "host_arch": platform.machine(), "mac_runtime_accepted": False,
              "internal_free_bytes": shutil.disk_usage(Path.home()).free,
              "host_input_used": False, "parallels_installed": (PARALLELS / "prlctl").is_file()}
    if report["host_os"] == "Darwin":
        report["macos"] = checked(["/usr/bin/sw_vers", "-productVersion"]).strip()
        report["memory_bytes"] = int(checked(["/usr/sbin/sysctl", "-n", "hw.memsize"]))
    if report["parallels_installed"]:
        cli = trusted_cli()
        report["parallels_version"] = checked([cli, "--version"]).strip()
        report["vm_inventory_available"] = bool(checked([cli, "list", "-a", "-j"]))
        report["edition"] = "Requires installed license/edition inspection; no subscription inference"
    else:
        report["blocker"] = "Install signed Parallels Desktop and sign in; administrator/account consent is user-owned"
    return report


class MacLab:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root).resolve()
        self.private = self.root / "private"
        self.private.mkdir(parents=True, mode=0o700, exist_ok=True)
        st = self.private.stat()
        if st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise ValueError("Private state needs local owner and mode 700")
        self.config = json.loads(read_private(self.private / "config.json"))
        if self.config.get("schema") != 1 or self.config.get("backend") != "parallels":
            raise ValueError("Unsupported backend configuration")
        self.uuid = vm_id(self.config["vm_uuid"])
        self.key = read_private(self.private / "transport.key")
        if len(self.key) != 32:
            raise ValueError("Invalid local transport key")

    @contextmanager
    def lock(self):
        fd = os.open(self.private / "operation.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        finally:
            os.close(fd)

    def record(self, name, value):
        publish(self.private, name, canonical(value), digest(canonical(value)))

    def owned(self, owner):
        identifier(owner)
        record = json.loads(read_private(self.private / "reservation.json"))
        if record.get("owner") != owner or record.get("vm_uuid") != self.uuid:
            raise ValueError("VM reserved by another workflow; do not take over")

    def reserve(self, owner):
        with self.lock():
            identifier(owner)
            self.record("reservation.json", {"owner": owner, "vm_uuid": self.uuid,
                                             "created_utc": time.time(), "expires_automatically": False})
        return {"reserved": True, "owner": owner}

    def vm(self):
        cli = trusted_cli()
        rows = json.loads(checked([cli, "list", "-i", "-j", "{" + self.uuid + "}"]))
        if isinstance(rows, dict):
            rows = [rows]
        if not isinstance(rows, list) or len(rows) != 1:
            raise ValueError("Expected one exact enrolled VM")
        row = rows[0]
        # Field map is captured from actual installed CLI during enrollment, never guessed.
        fields = self.config["observed_json_fields"]
        if vm_id(row[fields["uuid"]]) != self.uuid:
            raise ValueError("VM identity changed")
        home = Path(row[fields["home"]]).resolve(strict=True)
        if str(home) != self.config["bundle_path"]:
            raise ValueError("Enrolled VM bundle path changed")
        if self.config["guest_os"] != "linux" or self.config["guest_arch"] != "arm64":
            raise ValueError("Windows/macOS guest adapters still require independent implementation and acceptance")
        return cli, row[fields["state"]].lower(), home

    def lifecycle(self, action, owner):
        with self.lock():
            self.owned(owner)
            cli, state, _ = self.vm()
            if self.config.get("lifecycle_accepted") is not True:
                raise ValueError("Headless lifecycle is not accepted on this installed version")
            if action == "start":
                if state != "stopped":
                    raise ValueError("Cold start requires stopped VM")
                argv = [cli, "start", "{" + self.uuid + "}", "--headless"]
            elif action == "stop":
                if state != "running":
                    raise ValueError("Graceful stop requires running VM")
                argv = [cli, "stop", "{" + self.uuid + "}"]
            else:
                raise ValueError("Unsupported lifecycle action")
            sleep = subprocess.Popen(["/usr/bin/caffeinate", "-i", "-w", str(os.getpid())],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                outcome = bounded(argv, timeout=60)
                final_state = self.vm()[1]
                self.record("lifecycle-" + uuid.uuid4().hex + ".json", {"action": action, "result": outcome, "state": final_state})
                expected = "running" if action == "start" else "stopped"
                if outcome["exit_code"] or outcome["timed_out"] or final_state != expected:
                    raise RuntimeError("Lifecycle effects unresolved; inspect same VM before any retry")
                return {"action": action, "state": final_state}
            finally:
                sleep.terminate()
                sleep.wait(timeout=3)

    def request(self, request, owner):
        request = dict(request, schema=1, owner=owner, vm_uuid=self.uuid)
        request.setdefault("id", uuid.uuid4().hex)
        validate(request)
        with self.lock():
            self.owned(owner)
            cli, state, _ = self.vm()
            if state != "running":
                raise ValueError("Enrolled guest is not running")
            if self.config.get("transport_accepted") is not True:
                raise ValueError("Guest transport is not accepted here")
            name = "request-" + request["id"] + ".json"
            self.record(name, request)  # exclusive ID admission prevents blind replay
            payload = canonical(sign(request, self.key))
            transport = self.config["transport"]
            encoded = base64.urlsafe_b64encode(payload).decode()
            if transport == "tools":
                command = "/home/lab/agent/venv/bin/python /home/lab/agent/guest_bridge.py " + encoded
                argv = [cli, "exec", "{" + self.uuid + "}", "--user", "lab", command]
            elif transport == "ssh":
                port = self.config["ssh_port"]
                if type(port) is not int or not 1024 <= port <= 65535:
                    raise ValueError("Invalid enrolled loopback SSH port")
                argv = ["/usr/bin/ssh", "-F", "/dev/null", "-T", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
                        "-o", "StrictHostKeyChecking=yes", "-o", "ClearAllForwardings=yes", "-o", "ConnectTimeout=5",
                        "-o", "UserKnownHostsFile=" + str(self.private / "known_hosts"),
                        "-i", str(self.private / "guest_ed25519"), "-p", str(port), "lab@127.0.0.1",
                        "/home/lab/agent/venv/bin/python /home/lab/agent/guest_bridge.py"]
            else:
                raise ValueError("Unsupported enrolled transport")
            outcome = bounded(argv, timeout=request.get("timeout_ms", 15000) / 1000 + 15,
                              data=payload if transport == "ssh" else None)
            self.record("transport-" + request["id"] + ".json", outcome)
            if outcome["timed_out"] or outcome["truncated"] or outcome["exit_code"] not in (0, 2):
                raise RuntimeError("Guest effects unknown; inspect request.status with a new ID before recovery")
            response = authenticate(json.loads(outcome["stdout"]), self.key)
            if (response.get("id"), response.get("owner"), response.get("vm_uuid")) != (request["id"], owner, self.uuid):
                raise ValueError("Response identity mismatch")
            self.record("response-" + request["id"] + ".json", response)
            return response

    def release(self, owner):
        # Guest checks its sessions before releasing; transport failure retains the host reservation.
        response = self.request({"op": "workflow.release"}, owner)
        if not response.get("ok"):
            return response
        # Keep the host reservation through graceful shutdown, including unknown stop effects.
        stopped = self.lifecycle("stop", owner)
        with self.lock():
            self.owned(owner)
            self.private.joinpath("reservation.json").unlink()
        response["shutdown"] = stopped
        return response


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("action", choices=("preflight", "status", "reserve", "release", "start", "stop", "request", "push", "pull"))
    p.add_argument("--owner")
    p.add_argument("--request", type=Path)
    p.add_argument("--project", type=Path)
    p.add_argument("--path")
    args = p.parse_args()
    try:
        if args.action in ("preflight", "status"):
            value = preflight()
        else:
            lab = MacLab(args.root)
            if args.action == "reserve":
                value = lab.reserve(args.owner)
            elif args.action == "release":
                value = lab.release(args.owner)
            elif args.action in ("start", "stop"):
                value = lab.lifecycle(args.action, args.owner)
            elif args.action == "request":
                value = lab.request(json.loads(args.request.read_bytes()), args.owner)
            elif args.action == "push":
                value = lab.request({"op": "transfer.push", "args": selected(args.project, args.path)}, args.owner)
            elif args.action == "pull":
                value = lab.request({"op": "transfer.pull", "args": {"path": args.path}}, args.owner)
                if value.get("ok"):
                    entry = value["result"]
                    data = base64.b64decode(entry["base64"], validate=True)
                    value["publication"] = publish(args.project, args.path, data, entry["sha256"])
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return 0 if value.get("ok", True) else 2
    except Exception as error:
        print(json.dumps({"ok": False, "error": type(error).__name__, "message": str(error)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
