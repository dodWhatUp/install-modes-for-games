"""Offline contracts, explicitly distinct from Parallels/guest runtime acceptance."""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

import contracts as c
import guest_bridge as g
import mac_lab as m
import install_local


class Contracts(unittest.TestCase):
    def test_authentication_and_tamper(self):
        key = os.urandom(32)
        envelope = c.sign({"value": "שלום 😀 $() `x` ;"}, key)
        self.assertEqual(c.authenticate(envelope, key), envelope["body"])
        envelope["body"]["value"] += "x"
        with self.assertRaises(ValueError):
            c.authenticate(envelope, key)

    def test_invalid_requests(self):
        base = {"schema": 1, "id": "request", "owner": "test", "vm_uuid": str(uuid.uuid4())}
        for changes in ({"timeout_ms": True}, {"timeout_ms": 499}, {"timeout_ms": 60001},
                        {"id": "../x"}, {"args": []}, {"schema": 2}, {"vm_uuid": "name"}):
            with self.assertRaises((ValueError, AttributeError)):
                c.validate(dict(base, **changes))

    def test_paths(self):
        for path in ("../x", "/x", "a/../x", "a//x", "a/./x", "a\\x", "C:x", "a\0x", ""):
            with self.assertRaises(ValueError):
                c.relative(path)

    def test_atomic_no_overwrite_and_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            data = "שלום 😀\n".encode()
            c.publish(temp, "src/Unicode.txt", data, c.digest(data))
            with self.assertRaises(FileExistsError):
                c.publish(temp, "src/Unicode.txt", b"replacement", c.digest(b"replacement"))
            out = c.selected(temp, "src/Unicode.txt")
            self.assertEqual(base64.b64decode(out["base64"]), data)
            self.assertFalse(list(Path(temp).rglob(".isolatedlab-*")))

    def test_bad_hash_never_creates(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                c.publish(temp, "x", b"x", "0" * 64)
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_symlink_parent_and_file_refused(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as outside:
            root = Path(temp)
            (root / "escape").symlink_to(outside, target_is_directory=True)
            (root / "file").symlink_to(Path(outside) / "secret")
            for path in ("escape/x", "file"):
                with self.assertRaises(OSError):
                    c.selected(root, path)
            with self.assertRaises(OSError):
                c.publish(root, "escape/x", b"x", c.digest(b"x"))
            self.assertFalse(list(Path(outside).iterdir()))

    def test_concurrent_publish_has_one_winner(self):
        import concurrent.futures
        with tempfile.TemporaryDirectory() as temp:
            def attempt(i):
                try:
                    c.publish(temp, "result", str(i).encode(), c.digest(str(i).encode()))
                    return True
                except FileExistsError:
                    return False
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                self.assertEqual(sum(executor.map(attempt, range(16))), 1)

    def test_private_modes(self):
        with tempfile.TemporaryDirectory() as temp:
            f = Path(temp) / "key"
            f.write_bytes(os.urandom(32))
            f.chmod(0o644)
            with self.assertRaises(ValueError):
                c.read_private(f)
            f.chmod(0o600)
            self.assertEqual(len(c.read_private(f)), 32)

    def test_process_exit_and_unicode_argv(self):
        result = m.bounded([sys.executable, "-c", "import sys; print(sys.argv[1]); sys.exit(7)", "שלום ; $()"], 5)
        self.assertEqual(result["exit_code"], 7)
        self.assertEqual(result["stdout"].strip(), "שלום ; $()")

    def test_output_is_bounded(self):
        result = m.bounded([sys.executable, "-c", "print('x'*1000000)"], 5)
        self.assertTrue(result["truncated"])
        self.assertLessEqual(len(result["stdout"]), c.LIMIT)

    def test_deadline_includes_child_holding_pipe(self):
        started = time.monotonic()
        result = m.bounded([sys.executable, "-c", "import subprocess,time; subprocess.Popen(['sleep','30']); time.sleep(30)"], .2)
        self.assertTrue(result["timed_out"])
        self.assertLess(time.monotonic() - started, 2)

    def test_blocked_stdin_is_bounded(self):
        result = m.bounded([sys.executable, "-c", "import time; time.sleep(30)"], .2, data=b"x"*c.LIMIT)
        self.assertTrue(result["timed_out"])

    def test_missing_parallels_never_mutates(self):
        with patch.object(m, "PARALLELS", Path("/nonexistent/parallels")), patch.object(m, "bounded") as execute:
            with self.assertRaises(RuntimeError):
                m.trusted_cli()
            execute.assert_not_called()

    def test_guest_bridge_refuses_host_execution(self):
        result = m.bounded([sys.executable, str(Path(g.__file__))], 5)
        self.assertEqual(result["exit_code"], 3)
        self.assertIn("only in the enrolled Arm Linux guest", result["stderr"])

    def test_signed_guest_replay_and_identity(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(g, "STATE", Path(temp)), patch.object(g, "dispatch", return_value={"ok": True, "result": "Unicode שלום"}):
            key = os.urandom(32)
            req = {"schema": 1, "id": "once", "owner": "owner", "vm_uuid": str(uuid.uuid4()), "op": "system.status"}
            config = {"vm_uuid": req["vm_uuid"]}
            result = c.authenticate(g.handle(c.sign(req, key), config, key), key)
            self.assertEqual(result["id"], "once")
            with self.assertRaises(FileExistsError):
                g.handle(c.sign(req, key), config, key)
            with self.assertRaises(ValueError):
                g.handle(c.sign(dict(req, id="wrong"), key), {"vm_uuid": str(uuid.uuid4())}, key)
            self.assertFalse((Path(temp) / "admitted-wrong.json").exists())

    def test_browser_stale_guard_never_acts(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(g, "STATE", Path(temp)), patch.object(g, "worker_call", return_value={"ok": True, "result": {"session": "s", "text": "current"}}) as worker:
            g.record("workflow.json", {"owner": "owner", "vm_uuid": "uuid"})
            with self.assertRaises(ValueError):
                g.dispatch({"owner": "owner", "vm_uuid": "uuid", "op": "browser.act", "args": {"snapshot": "stale"}})
            self.assertEqual(worker.call_count, 1)
            self.assertEqual(worker.call_args.args[0]["op"], "browser.snapshot")

    def test_other_guest_owner_preserved(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(g, "STATE", Path(temp)), patch.object(g, "worker_call") as worker:
            g.record("workflow.json", {"owner": "other", "vm_uuid": "uuid"})
            with self.assertRaises(ValueError):
                g.dispatch({"owner": "owner", "vm_uuid": "uuid", "op": "system.status"})
            worker.assert_not_called()

    def test_capture_not_admitted(self):
        self.assertNotIn("desktop.screenshot", g.ALLOWED)
        with tempfile.TemporaryDirectory() as temp, patch.object(g, "STATE", Path(temp)), patch.object(g, "worker_call") as worker:
            g.record("workflow.json", {"owner": "owner", "vm_uuid": "uuid"})
            with self.assertRaises(ValueError):
                g.dispatch({"owner": "owner", "vm_uuid": "uuid", "op": "browser.act", "args": {"action": "screenshot"}})
            worker.assert_not_called()

    def test_special_file_refused_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            fifo = Path(temp) / "fifo"
            os.mkfifo(fifo, 0o600)
            with self.assertRaises(ValueError):
                c.selected(temp, "fifo")
            with self.assertRaises(ValueError):
                c.read_private(fifo)

    def test_install_preserves_guidance_and_rejects_second_install(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src"
            (source / "skill/scripts").mkdir(parents=True)
            (source / "skill/SKILL.md").write_text("verified fixture")
            data = (source / "skill/SKILL.md").read_bytes()
            (source / "MAC-SOURCE-MANIFEST.json").write_text(json.dumps({"files": [{"path": "skill/SKILL.md", "bytes": len(data), "sha256": c.digest(data)}]}))
            agents = root / "codex/AGENTS.md"
            agents.parent.mkdir()
            agents.write_bytes(b"Existing instructions\n<!-- MANAGED DISPATCHER -->\n")
            baseline = agents.read_bytes()
            skill = root / "skills/isolated-lab"
            result = install_local.install(source, root / "lab", skill, agents)
            self.assertTrue(agents.read_bytes().startswith(baseline))
            self.assertEqual(Path(result["backup"]).read_bytes(), baseline)
            installed = agents.read_bytes()
            with self.assertRaises(FileExistsError):
                install_local.install(source, root / "lab", skill, agents)
            self.assertEqual(agents.read_bytes(), installed)

    def test_failed_shutdown_keeps_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            lab = m.MacLab.__new__(m.MacLab)
            lab.private = Path(temp)
            (lab.private / "reservation.json").write_text("preserved")
            with patch.object(lab, "request", return_value={"ok": True}), patch.object(lab, "lifecycle", side_effect=RuntimeError("unknown effects")):
                with self.assertRaises(RuntimeError):
                    lab.release("owner")
            self.assertEqual((lab.private / "reservation.json").read_text(), "preserved")


if __name__ == "__main__":
    unittest.main()
