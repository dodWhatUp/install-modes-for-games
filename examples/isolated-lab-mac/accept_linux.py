"""Measured text-only guest acceptance. Never replay a failed/unknown mutation."""
import argparse
import base64
import json
from pathlib import Path
import time
import uuid

from contracts import canonical, digest, publish, selected
from mac_lab import MacLab, DEFAULT_ROOT


def run(root, owner):
    lab = MacLab(root)
    if (lab.private / "reservation.json").exists():
        lab.owned(owner)
    else:
        lab.reserve(owner)
    run_id = uuid.uuid4().hex
    report = {"schema": 1, "run_id": run_id, "backend": lab.config["backend"],
              "guest_os": "linux", "guest_arch": "arm64", "checks": [],
              "capture_used": False, "host_input_used": False, "human_interval": "NOT_RUN"}
    browser = desktop = app = None

    def call(op, args=None, session=None, expect=True, timeout_ms=15000):
        request = {"op": op, "args": args or {}, "timeout_ms": timeout_ms}
        if session:
            request["session"] = session
        response = lab.request(request, owner)
        if bool(response.get("ok")) != expect:
            raise RuntimeError("Unexpected " + op + " outcome: " + str(response.get("error")))
        report["checks"].append({"operation": op, "id": response["id"], "expected_success": expect,
                                 "matched": True})
        return response.get("result", response)

    def snapshot():
        return call("browser.snapshot", session=browser)

    def browser_action(args, expect=True):
        args = dict(args, snapshot=snapshot()["snapshot"])
        return call("browser.act", args, browser, expect)

    def native():
        return call("desktop.snapshot", {"app": app}, desktop)

    def native_action(control_name, action, **values):
        tree = native()
        nodes = [n for n in tree["nodes"] if n["name"] == control_name
                 and (action != "fill" or "EditableText" in n["interfaces"])]
        if len(nodes) != 1:
            raise RuntimeError("Native control is not unique: " + control_name)
        args = {"app": app, "snapshot": tree["snapshot"], "control": nodes[0]["id"], "action": action, **values}
        return call("desktop.act", args, desktop)

    try:
        system = call("system.status")
        assert system["os"] == "Linux" and system["cpu_count"] == 2
        call("capabilities")
        fixture = Path(__file__).parent / "fixtures"
        folder = "fixture-" + run_id
        entry = selected(fixture, "build.py")
        entry["path"] = folder + "/build.py"
        call("transfer.push", entry)
        call("transfer.push", entry, expect=False)  # never replace an existing source
        built = call("process.run", {"argv": ["/usr/bin/python3", "build.py"], "cwd": folder})
        assert built["exit_code"] == 0 and "BUILD_PASS" in built["stdout"]
        result = call("transfer.pull", {"path": folder + "/dist/build-result.json"})
        data = base64.b64decode(result["base64"], validate=True)
        assert json.loads(data)["built"] is True
        destination = Path(root) / "results" / run_id
        destination.mkdir(parents=True, mode=0o700, exist_ok=False)
        publish(destination, "build-result.json", data, result["sha256"])
        unicode = call("process.run", {"argv": ["/usr/bin/python3", "-c", "print('שלום — λ')"]})
        assert unicode["stdout"].strip() == "שלום — λ"
        deadline = call("process.run", {"argv": ["/usr/bin/python3", "-c", "import time;time.sleep(10)"]}, timeout_ms=600)
        assert deadline["timed_out"] and deadline["exit_code"] != 0
        call("transfer.pull", {"path": "../escape"}, expect=False)
        desktop = call("desktop.open")["session"]
        # Fixture server belongs to the same private guest session/process group.
        server = call("desktop.launch", {"argv": ["/usr/bin/python3", "-m", "http.server", "8765", "--bind", "127.0.0.1"],
                                          "cwd": folder + "/dist"}, desktop)
        app = call("desktop.launch", {"argv": ["/usr/bin/python3", "/home/lab/agent/desktop_demo.py"]}, desktop)["app"]
        # Observation can be retried; this does not repeat launch or action effects.
        for _ in range(10):
            response = lab.request({"op": "desktop.snapshot", "session": desktop, "args": {"app": app}}, owner)
            if response.get("ok"):
                break
            time.sleep(.2)
        else:
            raise RuntimeError("Native fixture exposed no accessibility tree")
        native_action("Project", "fill", value="שלום λ")
        native_action("Enable report", "invoke", name="click")
        old = native()
        native_action("Run test", "invoke", name="click")
        result = native()
        assert any(n.get("text") == "שלום λ: PASS" for n in result["nodes"])
        node = next(n for n in old["nodes"] if n["name"] == "Run test")
        call("desktop.act", {"app": app, "snapshot": old["snapshot"], "control": node["id"], "action": "invoke", "name": "click"}, desktop, expect=False)
        browser = call("browser.open")["session"]
        browser_action({"action": "goto", "url": "http://127.0.0.1:8765/"})
        browser_action({"action": "fill", "role": "textbox", "name": "Project", "value": "שלום λ"})
        browser_action({"action": "check", "role": "checkbox", "name": "Enable report", "checked": True})
        old = snapshot()
        browser_action({"action": "click", "role": "button", "name": "Run test"})
        assert "שלום λ: PASS" in snapshot()["text"]
        call("browser.act", {"action": "click", "role": "button", "name": "Run test", "snapshot": old["snapshot"]}, browser, expect=False)
        call("browser.close", session=browser)
        browser = None
        call("desktop.close", session=desktop)
        desktop = None
        caps = call("capabilities")
        assert not caps["browser"]["session_active"] and not caps["desktop_accessibility"]["session_active"]
        processes = call("process.list")
        assert not any(p["pid"] == server["pid"] for p in processes["processes"])
        report["outcome"] = "PASS_SELECTED_LINUX_RUNTIME"
    except Exception as error:
        report.update(outcome="FAIL_PRESERVE_AND_INSPECT", error=str(error),
                      active_browser=browser, active_desktop=desktop, app=app)
        # Retain reservation and sessions after unknown effects; no automatic replay.
    data = canonical(report)
    publish(lab.private, "acceptance-" + run_id + ".json", data, digest(data))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["outcome"].startswith("PASS") else 2


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--owner", required=True)
    args = p.parse_args()
    raise SystemExit(run(args.root, args.owner))
