"""Owned guest crash/provider-loss/unresponsive-provider recovery probes.

This does not lock the host or claim a graphical OS login-lock test.
"""
import argparse
import json
from pathlib import Path
import time
import uuid

from contracts import canonical, digest, publish
from mac_lab import MacLab, DEFAULT_ROOT


def run(root, owner):
    lab = MacLab(root)
    lab.reserve(owner); lab.lifecycle("start", owner)
    from prepare_lima import wait_ssh_banner
    wait_ssh_banner(lab.config["ssh_port"])
    report = {"schema": 1, "checks": [], "host_input_used": False, "capture_used": False,
              "graphical_login_lock": "NOT_APPLICABLE_TO_PRIVATE_XVFB; WINDOWS_MACOS_UNTESTED"}

    def call(op, args=None, session=None, success=True, timeout=15000):
        req = {"op": op, "args": args or {}, "timeout_ms": timeout}
        if session: req["session"] = session
        res = lab.request(req, owner)
        if bool(res.get("ok")) != success:
            raise RuntimeError("Unexpected recovery probe result: " + op + " " + str(res.get("error")))
        report["checks"].append({"op": op, "id": res["id"], "expected_success": success})
        return res

    try:
        crash = call("process.run", {"argv": ["/usr/bin/python3", "-c",
                      "import resource,os,signal;resource.setrlimit(resource.RLIMIT_CORE,(0,0));os.kill(os.getpid(),signal.SIGABRT)"]})
        assert crash["result"]["exit_code"] != 0 and not crash["result"]["timed_out"]
        call("system.status")
        for mode in ("crash", "unresponsive"):
            opened = call("desktop.open")["result"]
            session, pid = opened["session"], opened["provider_pid"]
            app = call("desktop.launch", {"argv": ["/usr/bin/python3", "/home/lab/agent/desktop_demo.py"]}, session)["result"]
            state = call("desktop.status", session=session)["result"]
            assert state["provider_pid"] == pid
            # Record proc start time before signaling; no arbitrary/name-selected target.
            obs = call("process.run", {"argv": ["/usr/bin/python3", "-c",
                "import pathlib,json,os;p=" + str(pid) + ";s=pathlib.Path('/proc/'+str(p)+'/stat').read_text().rsplit(')',1)[1].split();print(json.dumps({'pid':p,'start':s[19],'group':os.getpgid(p)}))"]})["result"]
            identity = json.loads(obs["stdout"])
            assert identity["pid"] == pid and identity["group"] == pid
            sig = "SIGKILL" if mode == "crash" else "SIGSTOP"
            signal_code = ("import pathlib,os,signal;p=" + str(pid) + ";expected=" + repr(identity["start"]) +
                ";s=pathlib.Path('/proc/'+str(p)+'/stat').read_text().rsplit(')',1)[1].split();assert s[19]==expected and os.getpgid(p)==p;os.killpg(p,signal." + sig + ");print('OWNED_PROVIDER_SIGNALLED')")
            sent = call("process.run", {"argv": ["/usr/bin/python3", "-c", signal_code]})["result"]
            assert sent["exit_code"] == 0
            lost = call("desktop.snapshot", {"app": app["app"]}, session, success=False, timeout=600)
            # The worker declares state loss and cleans only its recorded process group.
            assert lost.get("desktop_state_lost") is True
            call("desktop.status", session=session, success=False)
            caps = call("capabilities")["result"]
            assert caps["desktop_accessibility"]["session_active"] is False
            processes = call("process.list")["result"]["processes"]
            assert not any(p["pid"] in (pid, app["pid"]) for p in processes)
            fresh = call("desktop.open")["result"]
            assert fresh["session"] != session
            call("desktop.close", session=fresh["session"])
            report[mode] = "PASS_IDENTITY_GUARDED_SIGNAL_STATE_LOSS_CLEANUP_FRESH_SESSION"
        call("agent.stop")
        caps = call("capabilities")["result"]
        assert not caps["browser"]["session_active"] and not caps["desktop_accessibility"]["session_active"]
        lab.release(owner)
        report["outcome"] = "PASS_OWNED_LINUX_RECOVERY"
    except Exception as error:
        report["outcome"] = "FAIL_PRESERVE_EFFECTS"
        report["error"] = {"type": type(error).__name__, "message": str(error)}
    raw = canonical(report)
    publish(lab.private, "recovery-" + uuid.uuid4().hex + ".json", raw, digest(raw))
    print(json.dumps(report, indent=2))
    return 0 if report["outcome"] == "PASS_OWNED_LINUX_RECOVERY" else 2


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--owner", required=True)
    a = p.parse_args()
    raise SystemExit(run(a.root, a.owner))
