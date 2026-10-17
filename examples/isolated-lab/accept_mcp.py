"""Exercise a real MCP stdio process, preserving protocol evidence privately."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import uuid

from lab import Lab, stamp, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--live", action="store_true", help="Also inspect the already-running guest")
    args = parser.parse_args()
    lab = Lab(args.config)
    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "isolated-lab-acceptance", "version": "0.2.0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "lab_status", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
            "name": "linux_inspect", "arguments": {"op": "process.run", "args": {"argv": ["false"]}}}}
    ]
    if args.live:
        requests.append({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {
            "name": "linux_inspect", "arguments": {"op": "system.status"}}})
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("guest_mcp.py")),
                             "--config", args.config], input="".join(json.dumps(r) + "\n" for r in requests),
                            capture_output=True, text=True, timeout=45)
    out = lab.artifacts / ("mcp-acceptance-" + stamp() + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    (out / "stdout.jsonl").write_text(result.stdout, encoding="utf-8")
    (out / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    replies = [json.loads(line) for line in result.stdout.splitlines()]
    assert [r["id"] for r in replies] == [1, 2, 3, 4] + ([5] if args.live else [])
    assert replies[0]["result"]["protocolVersion"] == "2025-06-18"
    assert len(replies[1]["result"]["tools"]) == 5
    assert "linux" in replies[2]["result"]["structuredContent"]
    assert "error" in replies[3] and "Mutation is not an inspection" in replies[3]["error"]["message"]
    if args.live:
        assert "result" in replies[4], replies[4]
        response = replies[4]["result"]
        assert response["isError"] is False, response
        assert response["structuredContent"]["result"]["os"] == "Linux"
    receipt = {"outcome": "PASS", "transport": "real stdio subprocess", "live_guest": args.live,
               "reply_count": len(replies), "artifact_directory": str(out)}
    write_json(out / "acceptance.json", receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
