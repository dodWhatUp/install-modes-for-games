"""Verify this server using Codex's real MCP client, without an AI turn or new chat.

An isolated app-server process checks only isolatedLab. It does not refresh the
already-running desktop chat, whose tool catalog must be verified separately.
"""
import argparse
import json
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
import uuid

from lab import Lab, stamp, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    lab = Lab(args.config)
    out = lab.artifacts / ("codex-client-acceptance-" + stamp() + "-" + uuid.uuid4().hex[:8])
    out.mkdir(parents=True, exist_ok=False)
    codex = shutil.which("codex")
    if not codex:
        raise RuntimeError("Codex CLI unavailable")
    lines = queue.Queue()
    with (out / "stderr.txt").open("wb") as err:
        process = subprocess.Popen([codex, "app-server", "--stdio"], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=err,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        def read():
            for line in iter(process.stdout.readline, b""):
                lines.put(line)
            lines.put(None)
        threading.Thread(target=read, daemon=True).start()
        transcript = []
        def send(method, params, request_id):
            request = {"id": request_id, "method": method, "params": params}
            process.stdin.write((json.dumps(request) + "\n").encode())
            process.stdin.flush()
            end = time.monotonic() + 45
            while time.monotonic() < end:
                line = lines.get(timeout=max(0.1, end - time.monotonic()))
                if line is None:
                    raise RuntimeError("Codex diagnostic server exited")
                reply = json.loads(line)
                transcript.append(reply)
                if reply.get("id") == request_id:
                    if "error" in reply:
                        raise RuntimeError(json.dumps(reply["error"]))
                    return reply["result"]
            raise TimeoutError(method)
        try:
            send("initialize", {"clientInfo": {"name": "isolated_lab_acceptance", "version": "0.3.0"}}, 1)
            process.stdin.write(b'{"method":"initialized"}\n')
            process.stdin.flush()
            result = send("mcpServerStatus/list", {"serverName": "isolatedLab", "detail": "toolsAndAuthOnly"}, 2)
            write_json(out / "protocol.json", transcript)
            servers = result["data"]
            server = next(s for s in servers if s["name"] == "isolatedLab")
            names = set(server["tools"])
            assert server["serverInfo"]["version"] == "0.3.0", server["serverInfo"]
            expected = {"lab_status", "lab_start_linux", "lab_stop_linux", "linux_inspect", "linux_action"}
            # Client versions may qualify names with server prefixes.
            assert all(any(name == tool or name.endswith("__" + tool) for name in names) for tool in expected), server
            inspect_tool = next(tool for name, tool in server["tools"].items() if name.endswith("linux_inspect"))
            assert "desktop.snapshot" in inspect_tool["inputSchema"]["properties"]["op"]["enum"]
            skills = send("skills/list", {"cwds": [str(lab.root)], "forceReload": True}, 3)
            found = [skill for group in skills["data"] for skill in group["skills"] if skill["name"] == "isolated-lab"]
            assert len(found) == 1 and found[0]["enabled"], skills
            write_json(out / "protocol.json", transcript)
            receipt = {"outcome": "PASS", "client": "Codex app-server MCP client", "server": "isolatedLab",
                       "tool_names": sorted(names), "artifact_directory": str(out),
                       "scope": "real client initialization/discovery, no AI turn or tool mutation",
                       "native_accessibility_schema": "PASS desktop.snapshot registered",
                       "local_skill_discovery": "PASS isolated-lab enabled",
                       "active_chat_loaded_tools": "separate check; not proven by this diagnostic"}
            write_json(out / "acceptance.json", receipt)
            print(json.dumps(receipt))
        except Exception as error:
            write_json(out / "protocol.json", transcript)
            write_json(out / "acceptance.json", {"outcome": "FAIL", "error": str(error), "artifacts": str(out)})
            raise
        finally:
            process.stdin.close()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
