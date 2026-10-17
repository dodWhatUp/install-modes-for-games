"""Run after a cold boot: helper on-demand startup and real public HTTPS browser readback."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import uuid

from guest_tools import call
from lab import Lab, stamp, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    lab = Lab(args.config)
    report = {"version": "0.3.0", "checks": []}
    out = lab.artifacts / ("agent-cold-acceptance-" + stamp() + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    session = None
    session_kind = None
    try:
        probe = lab.ssh("linux", "test ! -S /home/lab/.local/state/codex-lab/agent.sock && "
                        "sha256sum /home/lab/agent/guest_agent.py /home/lab/agent/desktop_agent.py /home/lab/agent/desktop_demo.py", timeout=15)
        assert probe.returncode == 0
        hashes = {Path(line.split()[1]).name: line.split()[0] for line in probe.stdout.splitlines()}
        for name in ("guest_agent.py", "desktop_agent.py", "desktop_demo.py"):
            assert hashes[name] == hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        report["source_sha256"] = hashes
        report["worker_not_auto_started"] = True
        report["source_byte_verified"] = True
        def request(op, values=None, timeout=15000):
            payload = {"op": op, "args": values or {}, "timeout_ms": timeout}
            if session:
                payload["session"] = session
            response = call(lab, payload)
            assert response["ok"], response
            report["checks"].append({"op": op, "receipt": response["receipt"]})
            return response["result"]
        caps = request("capabilities")
        assert caps["browser"]["session_active"] is False
        assert request("system.status")["os"] == "Linux"
        session = request("browser.open", timeout=60000)["session"]
        session_kind = "browser"
        assert request("browser.act", {"action": "goto", "url": "https://example.com"},
                       timeout=30000)["http_status"] == 200
        snapshot = request("browser.snapshot", timeout=30000)
        # External page copy/layout can change; the owned local fixture tests exact content/actions.
        assert snapshot["url"].startswith("https://example.com/")
        assert snapshot["title"] and snapshot["text"] and snapshot["aria"]
        report["public_https_browser"] = "PASS actual title, text and accessibility snapshot"
        request("browser.close")
        session = session_kind = None
        assert caps["desktop_accessibility"]["provider_installed"] and not caps["desktop_accessibility"]["session_active"]
        session = request("desktop.open", timeout=30000)["session"]
        session_kind = "desktop"
        app = request("desktop.launch", {"argv": ["/usr/bin/python3", "/home/lab/agent/desktop_demo.py"]})["app"]
        time.sleep(3)
        tree = request("desktop.snapshot", {"app": app})
        assert any(n["name"] == "Project" and n.get("text") == "Baseline" for n in tree["nodes"]), tree
        report["native_accessibility_cold_boot"] = "PASS actual GTK AT-SPI tree and baseline text"
        request("desktop.close")
        session = session_kind = None
        report["outcome"] = "PASS"
    except Exception as error:
        report["outcome"] = "FAIL"
        report["error"] = type(error).__name__ + ": " + str(error)
        raise
    finally:
        try:
            if session:
                response = call(lab, {"op": session_kind + ".close", "session": session})
                assert response["ok"], response
            response = call(lab, {"op": "agent.stop"})
            assert response["ok"], response
        except Exception as error:
            report["cleanup_error"] = str(error)
            report["outcome"] = "FAIL_CLEANUP"
        write_json(out / "acceptance.json", report)
        print(json.dumps({"outcome": report.get("outcome"), "receipt": str(out),
                          "checks": len(report["checks"])}))


if __name__ == "__main__":
    main()
