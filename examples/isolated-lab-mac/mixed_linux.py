"""User-present 5-minute mixed interval; announce and obtain readiness first."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import subprocess
import time
import uuid

from accept_linux import run
from contracts import canonical, digest, publish
from mac_lab import DEFAULT_ROOT


def mixed(root, owner):
    start = time.monotonic()
    report = {"schema": 1, "started_utc": time.time(), "workloads": [],
              "human_report": "PENDING_SEPARATE_USER_REPORT", "host_input_used": False, "capture_used": False}
    lease = subprocess.Popen(["/usr/bin/caffeinate", "-i", "-w", str(__import__("os").getpid())],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while time.monotonic() - start < 300:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = run(root, owner)
            entry = json.loads(output.getvalue())
            report["workloads"].append({"run_id": entry["run_id"], "outcome": entry["outcome"], "checks": len(entry["checks"])})
            if code:
                report["outcome"] = "FAILED_PRESERVE_AND_INSPECT"
                break
            time.sleep(min(20, max(0, 300 - (time.monotonic() - start))))
        else:
            report["outcome"] = "PASS_TECHNICAL_INTERVAL_HUMAN_PENDING"
    finally:
        lease.terminate()
        lease.wait(timeout=3)
    report["elapsed_seconds"] = round(time.monotonic() - start, 2)
    report["ended_utc"] = time.time()
    data = canonical(report)
    publish(Path(root) / "private", "mixed-" + uuid.uuid4().hex + ".json", data, digest(data))
    print(json.dumps(report, indent=2))
    return 0 if report["outcome"].startswith("PASS") else 2


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--owner", required=True)
    a = p.parse_args()
    raise SystemExit(mixed(a.root, a.owner))
