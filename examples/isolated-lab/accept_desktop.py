"""Real native GTK/AT-SPI acceptance, including stale state and frozen-app recovery."""
import argparse
import json
import time
import uuid

from guest_tools import call
from lab import Lab, stamp, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    lab = Lab(args.config)
    out = lab.artifacts / ("desktop-acceptance-" + stamp() + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    report = {"version": "0.3.0", "outcome": "RUNNING", "checks": []}
    session = None
    groups = []
    def request(op, arguments=None, expected=True, timeout=15000, override=None):
        payload = {"op": op, "args": arguments or {}, "timeout_ms": timeout}
        if session:
            payload["session"] = override or session
        response = call(lab, payload)
        report["checks"].append({"op": op, "ok": response["ok"], "receipt": response["receipt"]})
        write_json(out / "acceptance.json", report)
        assert response["ok"] is expected, response
        return response.get("result", response)
    try:
        opened = request("desktop.open", timeout=30000)
        session = opened["session"]
        groups.append(opened["provider_pid"])
        request("desktop.open", expected=False)
        assert request("desktop.status")["session"] == session
        launched = request("desktop.launch", {"argv": ["/usr/bin/python3", "/home/lab/agent/desktop_demo.py"]})
        app = launched["app"]
        time.sleep(3)
        def snapshot():
            return request("desktop.snapshot", {"app": app})
        def control(tree, name, role=None):
            selected = [n for n in tree["nodes"] if n["name"] == name and (role is None or n["role"] == role)
                        and (name != "Project" or any(i.endswith("EditableText") for i in n["interfaces"]))]
            assert len(selected) == 1, tree
            return selected[0]
        def act(tree, label, action, **values):
            node = control(tree, label)
            return request("desktop.act", {"app": app, "snapshot": tree["snapshot"],
                                           "control": node["id"], "action": action, **values})
        tree = snapshot()
        assert control(tree, "Project")["text"] == "Baseline"
        act(tree, "Project", "fill", value="Native test Ω")
        request("desktop.act", {"app": app, "snapshot": tree["snapshot"], "control": control(tree, "Project")["id"],
                                "action": "fill", "value": "must reject stale state"}, expected=False)
        tree = snapshot()
        assert control(tree, "Project")["text"] == "Native test Ω"
        toggle = control(tree, "Enable report")
        assert "checked" not in toggle["states"] and toggle["actions"]
        act(tree, "Enable report", "invoke", name=toggle["actions"][0])
        tree = snapshot()
        assert "checked" in control(tree, "Enable report")["states"]
        run = control(tree, "Run test")
        act(tree, "Run test", "invoke", name=run["actions"][0])
        tree = snapshot()
        assert control(tree, "Result")["text"] == "Native test Ω: PASS", tree
        shot = request("desktop.screenshot")["artifact"]
        report["screenshot"] = lab.fetch("linux", shot)
        request("desktop.status", override="stale-session", expected=False)
        assert request("desktop.status")["session"] == session
        request("desktop.snapshot", {"app": "unknown-app"}, expected=False)
        request("process.run", {"argv": ["/bin/kill", "-STOP", str(launched["pid"])]})
        lost = request("desktop.snapshot", {"app": app}, timeout=500, expected=False)
        assert lost["desktop_state_lost"], lost
        session = None
        processes = request("process.list")["processes"]
        assert not any(p["pid"] == launched["pid"] and not p["state"].startswith("Z") for p in processes), processes
        reopened = request("desktop.open", timeout=30000)
        session = reopened["session"]
        groups.append(reopened["provider_pid"])
        killed = request("process.run", {"argv": ["/bin/kill", "-TERM", str(reopened["provider_pid"])]})
        assert killed["exit_code"] == 0, killed
        time.sleep(1)
        lost = request("desktop.status", expected=False)
        assert lost["desktop_state_lost"], lost
        session = None
        reopened = request("desktop.open", timeout=30000)
        session = reopened["session"]
        groups.append(reopened["provider_pid"])
        request("desktop.close")
        session = None
        cleanup = request("process.run", {"argv": ["python3", "-c",
            "import pathlib,json; groups=" + repr(groups) + "; live=[]; "
            "exec(\"for p in pathlib.Path('/proc').iterdir():\\n if not p.name.isdigit(): continue\\n try: s=(p/'stat').read_text().rsplit(')',1)[1].split()\\n except FileNotFoundError: continue\\n if int(s[2]) in groups and s[0]!='Z': live.append(int(p.name))\"); print(json.dumps(live))"]})
        assert cleanup["exit_code"] == 0 and json.loads(cleanup["stdout"]) == [], cleanup
        report.update(outcome="PASS", artifact_directory=str(out),
                      scope="Native GTK accessibility; guest only; other applications need provider-specific acceptance")
    except Exception as error:
        report.update(outcome="FAIL", error=str(error))
        raise
    finally:
        if session:
            try:
                request("desktop.close")
            except Exception as error:
                report["cleanup_error"] = str(error)
        write_json(out / "acceptance.json", report)
        print(json.dumps({k: v for k, v in report.items() if k != "checks"} | {"check_count": len(report["checks"])}))


if __name__ == "__main__":
    main()
