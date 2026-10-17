"""AT-SPI adapter for apps launched into one private guest D-Bus/Xvfb session.

No attachment to an existing desktop. No host input, global clipboard, or OCR.
The parent guest agent owns and bounds this entire process group.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid

LIMIT = 262144
WORK = Path.home() / "work"
ARTIFACTS = Path.home() / "artifacts"


def workspace(relative):
    if not isinstance(relative, str) or len(relative) > 2048:
        raise ValueError("Expected workspace-relative path")
    root = WORK.resolve()
    target = (root / relative).resolve()
    if target != root and root not in target.parents:
        raise ValueError("Path escapes workspace")
    return target


class Desktop:
    def __init__(self, session):
        import gi
        gi.require_version("Atspi", "2.0")
        from gi.repository import Atspi
        self.api = Atspi
        Atspi.set_timeout(1500, 3000)
        self.session = session
        self.apps = {}
        self.snapshots = {}

    def owned(self, app_id):
        app = self.apps.get(app_id)
        if not app or app["process"].poll() is not None:
            raise ValueError("Application missing or exited; launch and inspect a fresh app")
        desktop = self.api.get_desktop(0)
        for index in range(desktop.get_child_count()):
            node = desktop.get_child_at_index(index)
            if node.get_process_id() == app["process"].pid:
                return node
        raise ValueError("Application has not exposed an AT-SPI tree on this private bus")

    def tree(self, app_id):
        nodes, controls = [], {}
        truncated = False
        def visit(node, path, depth):
            nonlocal truncated
            if len(nodes) >= 200 or depth > 12:
                truncated = True
                return
            role = node.get_role_name()
            states = [state.value_nick for state in node.get_state_set().get_states()]
            info = {"id": path, "role": role, "name": node.get_name()[:512], "states": states,
                    "interfaces": list(node.get_interfaces())}
            actions = node.get_action_iface()
            if actions:
                info["actions"] = [self.api.Action.get_action_name(actions, i) for i in range(min(self.api.Action.get_n_actions(actions), 16))]
            text = node.get_text_iface()
            if text and role != "password text":
                info["text"] = self.api.Text.get_text(text, 0, min(self.api.Text.get_character_count(text), 8192))
            nodes.append(info)
            controls[path] = node
            for i in range(min(node.get_child_count(), 200)):
                child = node.get_child_at_index(i)
                if child:
                    visit(child, path + "/" + str(i), depth + 1)
        visit(self.owned(app_id), "0", 0)
        digest = hashlib.sha256(json.dumps(nodes, sort_keys=True).encode()).hexdigest()
        return {"session": self.session, "app": app_id, "pid": self.apps[app_id]["process"].pid,
                "snapshot": digest, "nodes": nodes, "truncated": truncated,
                "source": "AT-SPI accessibility properties, text and actions"}, controls

    def dispatch(self, request):
        if request.get("session") != self.session:
            raise ValueError("Desktop session missing or stale")
        op, args = request["op"], request.get("args", {})
        if op == "desktop.status":
            return {"session": self.session, "display": os.environ["DISPLAY"], "scope": "private guest session",
                    "apps": [{"app": app_id, "pid": app["process"].pid, "exit_code": app["process"].poll()}
                             for app_id, app in self.apps.items()]}
        if op == "desktop.launch":
            argv = args.get("argv")
            if not isinstance(argv, list) or not 1 <= len(argv) <= 64 or any(not isinstance(a, str) or len(a) > 8192 for a in argv):
                raise ValueError("Expected bounded argv list")
            if len(self.apps) >= 16:
                raise ValueError("Session app limit reached; close the session")
            app_id = uuid.uuid4().hex
            # Avoid unbounded app logs. Use process.run for bounded command output.
            proc = subprocess.Popen(argv, cwd=workspace(args.get("cwd", ".")),
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.apps[app_id] = {"process": proc}
            return {"app": app_id, "pid": proc.pid, "stdout": "discarded; use process.run for bounded command output"}
        if op == "desktop.screenshot":
            target = ARTIFACTS / ("desktop-" + uuid.uuid4().hex + ".png")
            subprocess.run(["import", "-window", "root", str(target)], check=True, timeout=5)
            return {"artifact": target.name, "source": "private guest X display"}
        app_id = args.get("app")
        tree, controls = self.tree(app_id)
        if op == "desktop.snapshot":
            return tree
        if op != "desktop.act":
            raise ValueError("Unknown desktop operation")
        if args.get("snapshot") != tree["snapshot"]:
            raise ValueError("Accessibility state changed; inspect before acting")
        target = controls.get(args.get("control"))
        if target is None:
            raise ValueError("Control absent from current bounded tree")
        if target.get_role_name() == "password text":
            raise ValueError("Password controls are excluded")
        action = args.get("action")
        if action == "fill":
            value = args.get("value")
            if not isinstance(value, str) or len(value) > 8192:
                raise ValueError("Expected bounded text value")
            iface = target.get_editable_text_iface()
            if not iface or not self.api.EditableText.set_text_contents(iface, value):
                raise ValueError("Control does not support setting editable text")
        elif action == "invoke":
            iface = target.get_action_iface()
            names = [self.api.Action.get_action_name(iface, i) for i in range(self.api.Action.get_n_actions(iface))] if iface else []
            name = args.get("name")
            if not isinstance(name, str) or names.count(name) != 1:
                raise ValueError("Select exactly one exposed action name from the snapshot")
            if not self.api.Action.do_action(iface, names.index(name)):
                raise ValueError("Application refused accessibility action")
        else:
            raise ValueError("Supported actions are fill and invoke")
        return {"completed": True, "action": action, "app": app_id, "inspect_required": True}

    def close(self):
        for app in self.apps.values():
            if app["process"].poll() is None:
                app["process"].terminate()


def serve(path, session):
    # -displayfd allocates an unused display; -nolisten tcp and -auth isolate X.
    read_fd, write_fd = os.pipe()
    auth = path.with_suffix(".xauth")
    auth.touch(mode=0o600)
    cookie = os.urandom(16).hex()
    # Allocate under Xvfb, then add the cookie before any application is launched.
    xvfb = subprocess.Popen(["Xvfb", "-displayfd", str(write_fd), "-screen", "0", "1100x760x24", "-nolisten", "tcp", "-auth", str(auth)],
                            pass_fds=(write_fd,), stdout=subprocess.DEVNULL, stderr=sys.stderr)
    os.close(write_fd)
    with os.fdopen(read_fd) as stream:
        display = ":" + stream.readline().strip()
    if display == ":" or xvfb.poll() is not None:
        raise RuntimeError("Private guest X server failed")
    subprocess.run(["xauth", "-f", str(auth), "add", display, ".", cookie], check=True, timeout=5)
    os.environ.update(DISPLAY=display, XAUTHORITY=str(auth), NO_AT_BRIDGE="0", GTK_MODULES="gail:atk-bridge", GSETTINGS_BACKEND="memory")
    desktop = Desktop(session)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(path))
            os.chmod(path, 0o600)
            server.listen(2)
            while True:
                connection, _ = server.accept()
                with connection:
                    connection.settimeout(5)
                    raw = connection.makefile("rb").readline(LIMIT + 1)
                    if len(raw) > LIMIT:
                        response = {"ok": False, "error": "Request too large"}
                    else:
                        try:
                            response = {"ok": True, "result": desktop.dispatch(json.loads(raw))}
                        except Exception as error:
                            response = {"ok": False, "error": type(error).__name__ + ": " + str(error)[:2000]}
                    encoded = (json.dumps(response) + "\n").encode()
                    if len(encoded) > LIMIT:
                        encoded = b'{"ok":false,"error":"Desktop response exceeded limit"}\n'
                    connection.sendall(encoded)
    finally:
        desktop.close()
        xvfb.terminate()
        path.unlink(missing_ok=True)
        auth.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--session", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    serve(Path(args.socket), args.session)
