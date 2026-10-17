"""Register only this tested guest bridge; preserve other Codex configuration."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib
import uuid

from lab import Lab, stamp, write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    lab = Lab(args.config)
    binary = shutil.which("codex")
    if not binary:
        raise RuntimeError("Codex CLI unavailable; source bridge preserved")
    bridge = lab.inside(lab.root / "source/examples/isolated-lab/guest_mcp.py")
    if not bridge.is_file():
        raise RuntimeError("Deploy and verify the authored source package first")
    command = sys.executable
    server_args = [str(bridge), "--config", str(lab.config_path)]

    def cli(*values):
        return subprocess.run([binary, "mcp", *values], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=20)

    existing = cli("get", "isolatedLab", "--json")
    if existing.returncode and "No MCP server named" not in existing.stderr:
        raise RuntimeError("Could not inspect Codex MCP state; configuration preserved")
    if existing.returncode == 0:
        transport = json.loads(existing.stdout)["transport"]
        if transport.get("command") != command or transport.get("args") != server_args:
            raise RuntimeError("isolatedLab name is owned by a different configuration; preserved it")
    config_dir = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    config_file = config_dir / "config.toml"
    if config_file.exists():
        before = config_file.read_bytes()
        previous_values = tomllib.loads(before.decode("utf-8"))
        backup = lab.inside(lab.private / ("codex-config-before-isolatedLab-" + stamp() + "-" + uuid.uuid4().hex[:8] + ".toml"))
        backup.write_bytes(before)
    else:
        backup = None
        previous_values = {}
    if existing.returncode:
        added = cli("add", "isolatedLab", "--", command, *server_args)
        if added.returncode:
            raise RuntimeError("Codex registration failed: " + added.stderr[:1000])
    # Edit only our own new table. No permissions, model, account or other server changes.
    current = config_file.read_bytes()
    text = current.decode("utf-8")
    match = re.search(r"(?ms)^\[mcp_servers\.isolatedLab\]\r?\n(.*?)(?=^\[|\Z)", text)
    if not match:
        raise RuntimeError("Registered table not found; no further configuration edits made")
    body = match.group(1)
    for key, value in (("tool_timeout_sec", "240"), ("startup_timeout_sec", "10"), ("required", "false")):
        if re.search(r"(?m)^" + key + r"\s*=", body):
            body = re.sub(r"(?m)^" + key + r"\s*=.*$", key + " = " + value, body)
        else:
            body = body.rstrip() + "\n" + key + " = " + value + "\n\n"
    updated = text[:match.start(1)] + body + text[match.end(1):]
    parsed = tomllib.loads(updated)
    def without_this_server(value):
        other = copy.deepcopy(value)
        servers = other.get("mcp_servers", {})
        servers.pop("isolatedLab", None)
        # Codex CLI omits optional empty argv arrays when serializing existing servers.
        # An omitted args list and [] both invoke the command without arguments.
        for server in servers.values():
            if server.get("args") == []:
                server.pop("args")
        if not servers:
            other.pop("mcp_servers", None)
        return other
    if without_this_server(parsed) != without_this_server(previous_values):
        raise RuntimeError("Other Codex configuration values changed; preserve and reconcile before further edits")
    registered = parsed["mcp_servers"]["isolatedLab"]
    if registered["command"] != command or registered["args"] != server_args:
        raise RuntimeError("Registered command mismatch; configuration preserved")
    if config_file.read_bytes() != current:
        raise RuntimeError("Concurrent Codex configuration edit detected; preserve and reconcile before retrying")
    temp = config_file.with_name("config.toml.isolatedLab-" + uuid.uuid4().hex + ".tmp")
    temp.write_bytes(updated.encode("utf-8"))
    os.replace(temp, config_file)
    verified = cli("get", "isolatedLab", "--json")
    if verified.returncode:
        raise RuntimeError("Codex registration readback failed")
    verification = json.loads(verified.stdout)
    transport = verification["transport"]
    assert transport["command"] == command and transport["args"] == server_args
    assert verification["tool_timeout_sec"] == 240
    receipt = {"name": "isolatedLab", "registered": True, "transport": "stdio", "tool_timeout_sec": 240,
               "initialization_starts_vm": False, "configuration_backup": str(backup) if backup else None,
               "other_configuration_semantics_preserved": True,
               "configuration_sha256": hashlib.sha256(config_file.read_bytes()).hexdigest(),
               "active_chat_catalog": "not asserted; client MCP restart may be required"}
    write_json(lab.private / ("mcp-registration-" + stamp() + ".json"), receipt)
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
