"""Unattended guest build/browser/native workload; no host desktop input."""
import argparse
import json
import time
import uuid
from accept_guest_agent import HTML, SERVER, remote_python
from guest_tools import call
from lab import Lab, available_memory_mb, stamp, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--seconds", type=int, default=1800)
    args = parser.parse_args()
    if not 60 <= args.seconds <= 3600:
        raise ValueError("Acceptance duration must be 60..3600 seconds")
    lab, tag = Lab(args.config), uuid.uuid4().hex
    out = lab.artifacts / ("background-acceptance-" + stamp() + "-" + tag[:8])
    out.mkdir(parents=True, exist_ok=False)
    report = {"version": "0.3.0", "outcome": "RUNNING", "requested_seconds": args.seconds,
              "cycles": 0, "requests": 0, "min_host_available_mb": available_memory_mb(),
              "artifact_directory": str(out), "concurrent_user_work": "PENDING; other chat controls host",
              "host_input_or_display_control": "none implemented or invoked by this harness"}
    browser = desktop = server_data = None
    receipts = (out / "requests.jsonl").open("x", encoding="utf-8")

    def request(op, arguments=None, session=None, timeout=15000):
        payload = {"op": op, "args": arguments or {}, "timeout_ms": timeout}
        if session:
            payload["session"] = session
        response = call(lab, payload)
        report["requests"] += 1
        receipts.write(json.dumps({"op": op, "ok": response["ok"], "receipt": response["receipt"],
                                  "elapsed_ms": response["elapsed_ms"]}) + "\n")
        receipts.flush()
        assert response["ok"], response
        return response["result"]

    def snapshot():
        return request("desktop.snapshot", {"app": app}, desktop)

    def node(tree, name, editable=False):
        matches = [n for n in tree["nodes"] if n["name"] == name and
                   (not editable or any(i.endswith("EditableText") for i in n["interfaces"]))]
        assert len(matches) == 1, tree
        return matches[0]

    def native_act(tree, target, action, **values):
        return request("desktop.act", {"app": app, "snapshot": tree["snapshot"], "control": target["id"],
                                       "action": action, **values}, desktop)

    try:
        caps = request("capabilities")
        assert caps["desktop_accessibility"]["provider_installed"], caps
        html, server_file = "background-" + tag + ".html", "background-server-" + tag + ".py"
        request("files.write", {"path": html, "text": HTML})
        request("files.write", {"path": server_file, "text": SERVER.replace("8765", "8785")})
        spawn = remote_python(lab, "import subprocess,json,pathlib; p=subprocess.Popen(['timeout','" +
                              str(args.seconds + 180) + "s','python3','/home/lab/work/" + server_file +
                              "'],start_new_session=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);"
                              "print(json.dumps({'pid':p.pid,'start':pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21]}))")
        server_data = json.loads(spawn)
        browser = request("browser.open", timeout=60000)["session"]
        request("browser.act", {"action": "goto", "url": "http://127.0.0.1:8785/" + html}, browser)
        request("browser.act", {"action": "check", "role": "checkbox", "name": "Enable report", "checked": True}, browser)
        desktop = request("desktop.open", timeout=30000)["session"]
        app = request("desktop.launch", {"argv": ["/usr/bin/python3", "/home/lab/agent/desktop_demo.py"]}, desktop)["app"]
        time.sleep(3)
        tree = snapshot()
        checkbox = node(tree, "Enable report")
        native_act(tree, checkbox, "invoke", name=checkbox["actions"][0])
        started = time.monotonic()
        print(json.dumps({"event": "started", "artifacts": str(out), "seconds": args.seconds}), flush=True)
        while time.monotonic() - started < args.seconds:
            available = available_memory_mb()
            report["min_host_available_mb"] = min(report["min_host_available_mb"], available)
            if available < 8192:
                raise RuntimeError("Host memory reserve below 8 GiB; acceptance stopped")
            cycle = report["cycles"] + 1
            value = "Background " + str(cycle) + " Ω"
            system = request("system.status")
            assert system["os"] == "Linux" and system["memory"]["MemAvailable_bytes"] > 128 * 1024 * 1024
            code = ("import pathlib,subprocess; p=pathlib.Path('build-" + tag + "'); p.mkdir(exist_ok=True); "
                    "src=p/'check.c'; src.write_text('#include <stdio.h>\\nint main(void){puts(\"PASS\");return 0;}\\n'); "
                    "subprocess.run(['gcc',str(src),'-o',str(p/'check')],check=True); "
                    "subprocess.run([str(p/'check')],check=True)")
            build = request("process.run", {"argv": ["python3", "-c", code]}, timeout=30000)
            assert build["exit_code"] == 0 and not build["timed_out"] and build["stdout"].strip() == "PASS", build
            request("browser.act", {"action": "fill", "role": "combobox", "name": "Project", "value": value}, browser)
            request("browser.act", {"action": "click", "role": "button", "name": "Run test"}, browser)
            result = request("browser.act", {"action": "read", "role": "status", "name": "Result"}, browser)
            assert result["text"] == value + ": PASS", result
            tree = snapshot()
            native_act(tree, node(tree, "Project", editable=True), "fill", value=value)
            tree = snapshot()
            assert node(tree, "Project", editable=True)["text"] == value
            button = node(tree, "Run test")
            native_act(tree, button, "invoke", name=button["actions"][0])
            tree = snapshot()
            assert node(tree, "Result")["text"] == value + ": PASS", tree
            report.update(cycles=cycle, elapsed_seconds=round(time.monotonic() - started, 2), last_cycle=stamp())
            write_json(out / "acceptance.json", report)
            if cycle % 5 == 0:
                print(json.dumps({"event": "progress", "cycles": cycle, "elapsed_seconds": report["elapsed_seconds"]}), flush=True)
        report["outcome"] = "PASS"
    except Exception as error:
        report.update(outcome="FAIL", error=str(error))
        raise
    finally:
        for op, session in (("browser.close", browser), ("desktop.close", desktop)):
            if session:
                try:
                    request(op, session=session)
                except Exception as error:
                    report.setdefault("cleanup_errors", []).append(str(error))
        if server_data:
            try:
                remote_python(lab, "import pathlib,os,signal; p=pathlib.Path('/proc/" + str(server_data["pid"]) + "/stat'); "
                              "p.exists() and p.read_text().split()[21]=='" + server_data["start"] + "' and os.killpg(" + str(server_data["pid"]) + ",signal.SIGTERM)")
            except Exception as error:
                report.setdefault("cleanup_errors", []).append(str(error))
        if report.get("cleanup_errors"):
            report["outcome"] = "FAIL_CLEANUP"
        receipts.close()
        write_json(out / "acceptance.json", report)
        print(json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
