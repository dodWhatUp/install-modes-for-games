"""Prepare a private web facade and official tunnel profile, without activation."""
import argparse
import json
from pathlib import Path
import sys

from lab import Lab, sha256, write_json
from portable_setup import dedicated_root
from prepare_portable_linux import fetch


def mcp_command(argv):
    # tunnel-client's shlex parser accepts double-quoted Windows paths with /
    # separators. No cmd.exe / PowerShell / shell interpolation is used.
    result = []
    for item in argv:
        value = str(item).replace("\\", "/")
        if any(c in value for c in ('"', "\n", "\r", "\0")):
            raise ValueError("Unsupported command argument")
        result.append('"' + value + '"')
    return " ".join(result)


def install_client(root):
    root = dedicated_root(root)
    lock = json.loads(Path(__file__).with_name("web-connection.lock.json").read_text())
    item = lock["download"]
    downloads = dedicated_root(root / "downloads/web-connection")
    downloads.mkdir(parents=True, exist_ok=True)
    archive = fetch(item, downloads)
    import zipfile
    destination = dedicated_root(root / "tools" / ("tunnel-client-" + lock["client_version"]))
    with zipfile.ZipFile(archive) as z:
        if len(z.infolist()) > 20 or sum(i.file_size for i in z.infolist()) > 150000000:
            raise ValueError("Tunnel archive exceeds budget")
        for entry in z.infolist():
            if entry.is_dir() or "/" in entry.filename or "\\" in entry.filename or entry.filename in (".", "..") or ":" in entry.filename:
                raise ValueError("Unexpected tunnel archive path")
            data = z.read(entry)
            target = destination / entry.filename
            if target.exists() and target.read_bytes() != data:
                raise ValueError("Existing tunnel client differs; reconcile before upgrade")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            if target.read_bytes() != data:
                raise RuntimeError("Tunnel extraction readback failed")
    return destination / "tunnel-client.exe"


def prepare(config, client, python=None):
    lab = Lab(config)
    dedicated_root(lab.root)
    client = lab.inside(client)
    lock = json.loads(Path(__file__).with_name("web-connection.lock.json").read_text())
    if sha256(client) != lock["executable_sha256"]:
        raise ValueError("Official tunnel executable hash mismatch")
    runtime = lab.inside(lab.root / "source/examples/isolated-lab")
    if not (runtime / "guest_mcp.py").is_file():
        raise ValueError("Install and verify the lab runtime first")
    folder = lab.inside(lab.private / "web-connection-0.5.0")
    folder.mkdir(parents=True, exist_ok=True)
    for name in ("web_mcp.py", "Connect-WebLab.ps1"):
        data = Path(__file__).with_name(name).read_bytes()
        target = folder / name
        if target.exists() and target.read_bytes() != data:
            raise ValueError("Prepared web source changed; preserve it before preparing a new revision")
        target.write_bytes(data)
    policy = folder / "policy.json"
    if not policy.exists():
        write_json(policy, {"schema": 1, "mode": "read-only", "dedicated_guest": False})
    from web_mcp import policy_mode
    mode = policy_mode(policy)
    argv = [str(Path(python or sys.executable).resolve()), str(folder / "web_mcp.py"),
            "--config", str(lab.config_path), "--policy", str(policy), "--runtime-source", str(runtime)]
    plan = {"schema": 1, "state": "PREPARED_NOT_CONNECTED", "client": str(client),
            "client_sha256": sha256(client), "command_argv": argv, "mcp_command": mcp_command(argv),
            "profile": "isolated-lab-web", "profile_dir": str(folder / "profiles"),
            "mode": mode, "policy": str(policy), "automatic_guest_start": False,
            "health_listener": "127.0.0.1:0", "account_association": "NOT_VERIFIED",
            "web_acceptance": "NOT_TESTED", "source_sha256": {name: sha256(folder / name) for name in ("web_mcp.py", "Connect-WebLab.ps1")}}
    write_json(folder / "plan.json", plan)
    return {"plan": str(folder / "plan.json"), "state": plan["state"], "mode": mode,
            "VM_started": False, "tunnel_started": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--client", help="Previously verified private executable")
    parser.add_argument("--download-client", action="store_true")
    args = parser.parse_args()
    if bool(args.client) == args.download_client:
        raise ValueError("Select --client or --download-client")
    client = install_client(Lab(args.config).root) if args.download_client else args.client
    print(json.dumps(prepare(args.config, client)))


if __name__ == "__main__":
    main()
