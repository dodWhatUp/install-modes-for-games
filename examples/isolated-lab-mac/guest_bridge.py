"""Authenticated Linux guest wrapper around the byte-preserved 0.3.0 agent.

Deploy beside guest_agent.py inside the enrolled VM, never execute on the Mac.
No screenshot API is admitted by this migration's text-only scope.
"""
import base64
import fcntl
import json
import os
from pathlib import Path
import platform
import sys

from contracts import (LIMIT, authenticate, canonical, digest, identifier, publish,
                       read_private, relative, selected, sign, validate, vm_id)

STATE = Path.home() / ".local/state/isolatedlab-mac"
READS = {"capabilities", "system.status", "process.list", "files.list", "files.read",
         "browser.snapshot", "desktop.status", "desktop.snapshot"}
ALLOWED = READS | {"files.write", "process.run", "browser.open", "browser.act", "browser.close",
                  "desktop.open", "desktop.launch", "desktop.act", "desktop.close", "agent.stop",
                  "transfer.push", "transfer.pull", "request.status", "workflow.release"}


def worker_call(request):
    import guest_agent
    guest_agent.ensure_worker()
    return guest_agent.call_worker(request)


def no_sessions():
    status = worker_call({"schema": 1, "id": os.urandom(16).hex(), "op": "capabilities"})
    if not status.get("ok") or status.get("version") != "0.3.0":
        raise ValueError("Unknown or unresponsive guest worker; preserve it for recovery")
    result = status["result"]
    if result["browser"]["session_active"] or result["desktop_accessibility"]["session_active"]:
        raise ValueError("Active guest session exists; preserve its owner")


def record(name, value):
    data = canonical(value)
    return publish(STATE, name, data, digest(data))


def dispatch(request):
    owner = request["owner"]
    op = request.get("op")
    if op not in ALLOWED:
        raise ValueError("Unsupported guest operation")
    claim = STATE / "workflow.json"
    if not claim.exists():
        no_sessions()
        record("workflow.json", {"owner": owner, "vm_uuid": request["vm_uuid"]})
    current = json.loads(read_private(claim))
    if current != {"owner": owner, "vm_uuid": request["vm_uuid"]}:
        raise ValueError("Guest reserved by a different workflow")
    if op == "request.status":
        prior = identifier(request.get("args", {}).get("request_id"))
        for phase in ("response", "admitted"):
            path = STATE / (phase + "-" + prior + ".json")
            if path.is_file():
                value = json.loads(read_private(path))
                if value.get("owner") != owner:
                    raise ValueError("Receipt belongs to another owner")
                return {"ok": True, "result": {"phase": phase, "receipt": value,
                                                "replay_allowed": False}}
        return {"ok": True, "result": {"phase": "not_admitted", "replay_allowed": False}}
    if op == "workflow.release":
        for admitted in STATE.glob("admitted-*.json"):
            old = json.loads(read_private(admitted))
            if old["id"] != request["id"] and old["owner"] == owner and not (STATE / ("response-" + old["id"] + ".json")).exists():
                raise ValueError("Unresolved admitted request; inspect effects before releasing")
        no_sessions()
        claim.unlink()
        return {"ok": True, "result": {"released": True}}
    work = Path.home() / "work" / owner
    work.mkdir(mode=0o700, parents=True, exist_ok=True)
    if work.is_symlink():
        raise ValueError("Workspace replaced by symlink")
    args = dict(request.get("args", {}))
    if op == "transfer.push":
        data = base64.b64decode(args["base64"], validate=True)
        if len(data) > 65536 or args.get("bytes") != len(data):
            raise ValueError("Selected-file size mismatch or limit exceeded")
        return {"ok": True, "result": publish(work, args["path"], data, args["sha256"])}
    if op == "transfer.pull":
        return {"ok": True, "result": selected(work, args["path"])}
    if op.startswith("files."):
        path = args.get("path", ".")
        relative(path) if path != "." else None
        args["path"] = owner + ("/" + path if path != "." else "")
    if op in ("process.run", "desktop.launch"):
        cwd = args.get("cwd", ".")
        relative(cwd) if cwd != "." else None
        args["cwd"] = owner + ("/" + cwd if cwd != "." else "")
    inner = {k: v for k, v in request.items() if k not in ("owner", "vm_uuid")}
    inner["args"] = args
    if op == "browser.act":
        if args.get("action") == "screenshot":
            raise ValueError("Capture is outside this migration's text-only scope")
        observed = worker_call(dict(inner, op="browser.snapshot", args={}))
        if not observed.get("ok"):
            return observed
        if args.get("snapshot") != digest(canonical(observed["result"])):
            raise ValueError("Stale browser snapshot; observe before acting")
    result = worker_call(inner)
    if op == "browser.snapshot" and result.get("ok"):
        result["result"]["snapshot"] = digest(canonical(result["result"]))
    return result


def handle(envelope, config, key):
    request = validate(authenticate(envelope, key))
    if vm_id(request["vm_uuid"]) != vm_id(config["vm_uuid"]):
        raise ValueError("Guest enrollment identity mismatch")
    name = "admitted-" + request["id"] + ".json"
    record(name, request)  # exclusive on the guest too; unknown effects never replay
    try:
        response = dispatch(request)
    except Exception as error:
        response = {"ok": False, "error": {"code": type(error).__name__, "message": str(error)}}
    response.update(schema=1, id=request["id"], owner=request["owner"], vm_uuid=request["vm_uuid"])
    record("response-" + request["id"] + ".json", response)
    return sign(response, key)


def main():
    if platform.system() != "Linux" or platform.machine() not in ("aarch64", "arm64"):
        raise RuntimeError("This bridge runs only in the enrolled Arm Linux guest")
    config = json.loads(read_private(STATE / "enrollment.json"))
    if config.get("guest_os") != "linux" or config.get("guest_arch") != "arm64":
        raise ValueError("Guest enrollment OS/architecture mismatch")
    key = read_private(STATE / "transport.key")
    fd = os.open(STATE / "operation.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if len(sys.argv) == 2:
            raw = base64.b64decode(sys.argv[1], altchars=b"-_", validate=True)
        elif len(sys.argv) == 1:
            raw = sys.stdin.buffer.read(LIMIT + 1)
        else:
            raise ValueError("Unexpected bridge arguments")
        if len(raw) > LIMIT:
            raise ValueError("Envelope exceeds limit")
        result = handle(json.loads(raw), config, key)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["body"]["ok"] else 2
    finally:
        os.close(fd)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        # An unauthenticated or lost bridge is a transport error, never a fake receipt.
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        sys.exit(3)
