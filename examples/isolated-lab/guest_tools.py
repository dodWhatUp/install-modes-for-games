"""Host transport for the guest agent. All execution targets the named VM."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys
import uuid

from lab import Lab, stamp, write_json

GUEST_PYTHON = "/home/lab/agent/venv/bin/python"
GUEST_AGENT = "/home/lab/agent/guest_agent.py"


def deploy(lab):
    if not lab.running("linux"):
        raise RuntimeError("Start and wait for the Linux guest before deploying")
    verified = {}
    with lab.lock("linux"):
        for name in ("guest_agent.py", "prepare_guest_browser.py", "desktop_agent.py", "desktop_demo.py"):
            source = Path(__file__).with_name(name).read_bytes()
            expected = hashlib.sha256(source).hexdigest()
            target = "/home/lab/agent/" + name
            result = lab.ssh("linux", "test ! -S /home/lab/.local/state/codex-lab/agent.sock && "
                            "umask 077 && mkdir -p /home/lab/agent && cat > " + target +
                            " && chmod 600 " + target + " && sha256sum " + target,
                            timeout=20, input=source)
            if result.returncode or not result.stdout.split() or result.stdout.split()[0] != expected:
                raise RuntimeError("Guest deployment/readback failed; stop any old worker before replacement")
            verified[name] = expected
    return {"deployed": True, "sha256": verified, "provider_dependencies": "install_guest_agent.sh required"}


def call(lab, request):
    if not isinstance(request, dict):
        raise ValueError("Request must be an object")
    request = dict(request)
    request.setdefault("schema", 1)
    request.setdefault("id", uuid.uuid4().hex)
    timeout = request.get("timeout_ms", 15000)
    if type(timeout) is not int or not 500 <= timeout <= 60000:
        raise ValueError("timeout_ms must be 500..60000")
    payload = (json.dumps(request) + "\n").encode()
    if len(payload) > 262144:
        raise ValueError("Request exceeds limit")
    if not lab.running("linux"):
        raise RuntimeError("Linux VM is stopped; start and wait-ready before guest tools")
    target = lab.artifacts / ("agent-" + stamp() + "-" + uuid.uuid4().hex[:8])
    target.mkdir(parents=True, exist_ok=False)
    write_json(target / "request.json", request)
    with lab.lock("linux"):
        try:
            result = lab.ssh("linux", shlex.quote(GUEST_PYTHON) + " " + shlex.quote(GUEST_AGENT),
                             timeout=timeout / 1000 + 25, input=payload)
            (target / "stderr.txt").write_text(result.stderr, encoding="utf-8")
            response = json.loads(result.stdout)
            if result.returncode not in (0, 2) or not isinstance(response, dict):
                raise RuntimeError("Agent transport failed")
            if response.get("id") != request["id"]:
                raise RuntimeError("Response correlation failed: " + json.dumps(response.get("error", {})))
            write_json(target / "response.json", response)
            response["receipt"] = str(target)
            return response
        except Exception as error:
            write_json(target / "transport-error.json", {"type": type(error).__name__, "message": str(error)})
            raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--deploy", action="store_true")
    parser.add_argument("--request", help="JSON request file; otherwise read one JSON object from stdin")
    args = parser.parse_args()
    try:
        lab = Lab(args.config)
        if args.deploy:
            result = deploy(lab)
        else:
            raw = Path(args.request).read_text(encoding="utf-8-sig") if args.request else sys.stdin.read(262145)
            result = call(lab, json.loads(raw))
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok", result.get("deployed", False)) else 2
    except Exception as error:
        print(json.dumps({"ok": False, "error": {"code": type(error).__name__, "message": str(error)}}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
