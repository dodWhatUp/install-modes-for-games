"""Real official tunnel-client local proxy -> selected facade -> lab status.

No OpenAI account, credential, guest start or guest action. Local HTTP is an
ephemeral vendor-provided test transport, never the production connection.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request
import uuid

from lab import Lab, stamp, write_json


def rpc(url, request, session=None):
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "MCP-Protocol-Version": "2025-06-18"}
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(url, data=json.dumps(request).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        payload = response.read(2097153).decode()
        if len(payload) > 2097152:
            raise RuntimeError("Test response exceeds budget")
        if "text/event-stream" in response.headers.get("Content-Type", ""):
            values = [json.loads(line[5:].strip()) for line in payload.splitlines() if line.startswith("data:")]
            result = next((r for r in values if r.get("id") == request.get("id")), {})
        else:
            result = json.loads(payload) if payload else {}
        return result, response.headers.get("Mcp-Session-Id") or session


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--plan", required=True)
    args = parser.parse_args()
    lab = Lab(args.config)
    plan = json.loads(Path(args.plan).read_text())
    folder = lab.inside(lab.artifacts / ("web-local-acceptance-" + stamp() + "-" + uuid.uuid4().hex[:8]))
    folder.mkdir(parents=True)
    connection = folder / "connection.json"
    log = (folder / "vendor-client.log").open("w", encoding="utf-8")
    client = subprocess.Popen([plan["client"], "dev", "proxy", "--backend", "go", "--mcp-command", plan["mcp_command"],
                               "--duration", "20s", "--response-timeout", "15s", "--url-file", str(connection),
                               "--health-url-file", str(folder / "health.url")], stdout=log, stderr=log,
                              creationflags=subprocess.CREATE_NO_WINDOW)
    replies = []
    try:
        deadline = time.monotonic() + 12
        while not connection.exists():
            if client.poll() is not None or time.monotonic() > deadline:
                raise RuntimeError("Local vendor proxy failed readiness; inspect its private log")
            time.sleep(.1)
        metadata = json.loads(connection.read_text())
        write_json(folder / "metadata-fields.json", {"fields": list(metadata)})
        url = metadata.get("mcp_url") or metadata.get("url")
        if not isinstance(url, str) or not url.startswith("http://127.0.0.1:"):
            raise RuntimeError("Vendor proxy did not return an expected loopback MCP URL")
        session = None
        requests = [
            {"id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "isolatedLab-local-web-test", "version": "0.5.0"}}},
            {"method": "notifications/initialized"},
            {"id": 2, "method": "tools/list"},
            {"id": 3, "method": "tools/call", "params": {"name": "lab_status", "arguments": {}}},
            {"id": 4, "method": "tools/call", "params": {"name": "linux_action", "arguments": {"op": "process.run", "args": {"argv": ["false"]}, "request_key": "blocked_test_0001"}}},
            {"id": 5, "method": "tools/call", "params": {"name": "linux_inspect", "arguments": {"op": "process.run"}}},
            {"id": 6, "method": "tools/call", "params": {"name": "lab_stop_linux", "arguments": {}}}]
        for request in requests:
            reply, session = rpc(url, {"jsonrpc": "2.0", **request}, session)
            if "id" in request:
                replies.append(reply)
        write_json(folder / "replies.json", replies)
        assert replies[0]["result"]["serverInfo"]["name"] == "isolatedLab-web"
        assert {t["name"] for t in replies[1]["result"]["tools"]} == {"lab_status", "linux_inspect"}
        assert "linux" in replies[2]["result"]["structuredContent"]
        assert all("error" in r for r in replies[3:]), replies[3:]
        client.wait(timeout=25)
        assert client.returncode == 0, "Vendor proxy did not exit cleanly"
        receipt = {"outcome": "PASS", "checks": 6, "transport": "real official Windows tunnel-client local dev proxy + stdio facade",
                   "guest_actions": False, "VM_started": False, "OpenAI_account_connected": False,
                   "ChatGPT_web_acceptance": "PENDING_ACCOUNT_ACTIVATION", "artifact_directory": str(folder)}
        write_json(folder / "acceptance.json", receipt)
        print(json.dumps(receipt))
    finally:
        if client.poll() is None:
            client.terminate()
            client.wait(timeout=10)
        log.close()


if __name__ == "__main__":
    main()
