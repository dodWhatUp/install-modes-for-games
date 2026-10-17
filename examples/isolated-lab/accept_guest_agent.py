"""Live acceptance against the selected Linux VM; no host desktop automation."""
import argparse
import base64
import ctypes
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time
import uuid

from guest_tools import call
from lab import Lab, stamp, write_json

HTML = '''<!doctype html><html lang="en"><meta charset="utf-8"><title>Guest helper acceptance</title>
<style>body{font:18px system-ui;max-width:680px;margin:40px auto}input,button{font:inherit}
label{display:block;margin:16px 0}details{margin-top:20px}output{display:block;margin:20px 0}</style>
<h1>Guest browser test</h1><form id="form">
<label>Project <input aria-label="Project" list="projects" value="Baseline"></label>
<datalist id="projects"><option>Baseline</option><option>Agent test</option></datalist>
<label><input type="checkbox" aria-label="Enable report"> Enable report</label>
<button>Run test</button><output role="status" aria-label="Result">Waiting</output></form>
<details><summary>Test details</summary>Runs entirely inside the Linux guest.</details>
<script>document.querySelector('form').onsubmit=e=>{e.preventDefault();
document.querySelector('output').textContent=document.querySelector('input').value+': '+
(document.querySelector('[type=checkbox]').checked?'PASS':'DISABLED')};</script></html>'''

SERVER = '''import http.server,time,os
os.chdir('/home/lab/work')
class Handler(http.server.SimpleHTTPRequestHandler):
 def do_GET(self):
  if self.path == '/slow': time.sleep(8)
  super().do_GET()
http.server.HTTPServer(('127.0.0.1',8765),Handler).serve_forever()
'''


def remote_python(lab, code):
    encoded = base64.b64encode(code.encode()).decode()
    command = "python3 -c " + shlex.quote("import base64;exec(base64.b64decode('" + encoded + "'))")
    result = lab.ssh("linux", command, timeout=15)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    lab = Lab(args.config)
    report = {"schema": 1, "version": "0.2.0", "started": stamp(), "checks": []}
    out = lab.artifacts / ("agent-acceptance-" + stamp() + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    session = None
    server = None
    foreground = ctypes.windll.user32.GetForegroundWindow()

    def request(op, arguments=None, timeout=15000, ok=True, session_override=None):
        payload = {"op": op, "args": arguments or {}, "timeout_ms": timeout}
        if session_override or session:
            payload["session"] = session_override or session
        response = call(lab, payload)
        assert response["ok"] is ok, response
        report["checks"].append({"op": op, "expected_ok": ok, "receipt": response["receipt"],
                                  "elapsed_ms": response["elapsed_ms"]})
        write_json(out / "acceptance.json", report)
        return response.get("result", response)

    try:
        caps = request("capabilities")
        assert caps["browser"]["provider_installed"] and not caps["windows"]["available"]
        status = request("system.status")
        assert status["os"] == "Linux" and status["memory"]["MemAvailable_bytes"] > 0
        processes = request("process.list")["processes"]
        assert any(p["name"].startswith("python") for p in processes)
        file = "agent-acceptance-" + uuid.uuid4().hex + ".txt"
        text = "Structured guest data: Ω\n"
        request("files.write", {"path": file, "text": text})
        assert request("files.read", {"path": file})["text"] == text
        request("files.write", {"path": file, "text": "must not replace"}, ok=False)
        assert request("files.read", {"path": file})["text"] == text
        request("files.read", {"path": "../agent/guest_agent.py"}, ok=False)
        assert any(x["name"] == file for x in request("files.list")["entries"])
        failed = request("process.run", {"argv": ["python3", "-c", "import sys; print('expected failure');sys.exit(17)"]})
        assert failed["exit_code"] == 17 and not failed["timed_out"]
        timed = request("process.run", {"argv": ["python3", "-c", "import time;time.sleep(20)"]}, timeout=1000)
        assert timed["timed_out"] and timed["exit_code"] != 0
        request("system.status")
        large = request("process.run", {"argv": ["python3", "-c", "print('x'*100000)"]})
        assert large["output_truncated"] and len(large["stdout"]) == 65536
        child = request("process.run", {"argv": ["python3", "-c",
            "import subprocess,time; p=subprocess.Popen(['python3','-c','import time;time.sleep(20)']);"
            "print(p.pid,flush=True);time.sleep(20)"]}, timeout=1500)
        assert child["timed_out"]
        child_pid = int(child["stdout"].strip())
        children = [p for p in request("process.list")["processes"] if p["pid"] == child_pid]
        assert not children or children[0]["state"].startswith("Z"), children
        pagefile = "agent-demo-" + uuid.uuid4().hex + ".html"
        request("files.write", {"path": pagefile, "text": HTML})
        serverfile = "agent-server-" + uuid.uuid4().hex + ".py"
        request("files.write", {"path": serverfile, "text": SERVER})
        # A bounded local fixture web server, wholly inside the guest, with no host port forward.
        server = json.loads(remote_python(lab,
            "import subprocess,json,pathlib\n"
            "p=subprocess.Popen(['timeout','600','python3','/home/lab/work/" + serverfile + "'],"
            "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,"
            "stderr=subprocess.DEVNULL,start_new_session=True)\n"
            "print(json.dumps({'pid':p.pid,'start':pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21]}))"))
        opened = request("browser.open", timeout=60000)
        session = opened["session"]
        request("browser.open", ok=False)  # Does not replace the user's existing browser session.
        request("browser.act", {"action": "goto", "url": "http://127.0.0.1:8765/" + pagefile}, timeout=30000)
        before = request("browser.snapshot", timeout=30000)
        assert "textbox \"Project\"" in before["aria"] or "combobox \"Project\"" in before["aria"]
        # A datalist input has the ARIA combobox role, not textbox.
        request("browser.act", {"action": "fill", "role": "combobox", "name": "Project", "value": "Agent test"})
        request("browser.act", {"action": "check", "role": "checkbox", "name": "Enable report", "checked": True})
        request("browser.act", {"action": "click", "role": "button", "name": "Run test"})
        result = request("browser.act", {"action": "read", "role": "status", "name": "Result"})
        assert result["text"] == "Agent test: PASS", result
        after = request("browser.snapshot", timeout=30000)
        assert "Agent test: PASS" in after["text"] and "[checked]" in after["aria"]
        shot = request("browser.act", {"action": "screenshot"}, timeout=30000)
        report["screenshot"] = lab.fetch("linux", shot["artifact"])
        request("browser.act", {"action": "click", "role": "button", "name": "Missing button"}, ok=False)
        assert request("browser.snapshot")["session"] == session
        request("browser.snapshot", ok=False, session_override="stale-token")
        lost = request("browser.act", {"action": "goto", "url": "http://127.0.0.1:8765/slow"},
                       timeout=1000, ok=False)
        assert lost["browser_state_lost"]
        session = None
        opened = request("browser.open", timeout=60000)
        session = opened["session"]
        assert session != after["session"]
        request("browser.close")
        session = None
        request("agent.stop")
        # Prove on-demand recovery of the worker, rather than inferring it from source.
        request("system.status")
        report["browser_version"] = opened["browser_version"]
        report["outcome"] = "PASS"
        report["foreground_sample_unchanged"] = ctypes.windll.user32.GetForegroundWindow() == foreground
        report["scope"] = "Linux structured OS/files/process/browser; native desktop and Windows excluded"
    except Exception as error:
        report["outcome"] = "FAIL"
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        try:
            if session:
                call(lab, {"op": "browser.close", "session": session})
            call(lab, {"op": "agent.stop"})
        except Exception as error:
            report["cleanup_error"] = str(error)
        if server:
            remote_python(lab, "import os,signal,pathlib\n"
                "p=" + str(server["pid"]) + "\n"
                "f=pathlib.Path('/proc/'+str(p)+'/stat')\n"
                "if f.exists() and f.read_text().split()[21]==" + repr(server["start"]) + ":\n"
                " os.killpg(p,signal.SIGTERM)\n")
        report["finished"] = stamp()
        write_json(out / "acceptance.json", report)
        print(json.dumps({"outcome": report.get("outcome"), "checks": len(report["checks"]),
                          "receipt": str(out), "screenshot": report.get("screenshot")}))


if __name__ == "__main__":
    main()
