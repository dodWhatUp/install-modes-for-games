"""Behavior checks for lab failure paths, using temporary private fixture files."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from lab import Lab, write_json, sha256


class LabSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "private").mkdir()
        (self.root / "vms" / "linux").mkdir(parents=True)
        self.config = {
            "schema": 1, "root": str(self.root), "qemu": str(self.root / "qemu.exe"),
            "qemu_img": str(self.root / "qemu-img.exe"), "vbox": str(self.root / "VBoxManage.exe"),
            "guests": {"linux": {
                "backend": "qemu", "disk": str(self.root / "vms/linux/disk.qcow2"),
                "seed": str(self.root / "vms/linux/seed.iso"), "memory_mb": 4096, "cpus": 2,
                "accelerator": "tcg", "ssh_port": 22241, "qmp_port": 22441, "vnc_display": 41,
                "user": "lab", "key": str(self.root / "private/key"),
                "known_hosts": str(self.root / "private/known_hosts")
            }}
        }
        self.path = self.root / "private/config.json"
        write_json(self.path, self.config)

    def tearDown(self):
        self.tmp.cleanup()

    def test_utf8_output_survives_windows_locale(self):
        import sys
        lab = Lab(self.path)
        code = "import sys;sys.stdout.buffer.write(bytes.fromhex('f09f9881'))"
        with patch.object(lab, "ssh_args", return_value=[sys.executable, "-c", code]):
            result = lab.ssh("linux", "ignored")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "\U0001f601")

    def test_fetch_preserves_scope_and_correct_port_after_ssh_options_change(self):
        import subprocess
        lab = Lab(self.path)
        def copy(argv, **kwargs):
            self.assertEqual(argv[0], "scp.exe")
            self.assertEqual(argv[argv.index("-F") + 1], "none")
            self.assertEqual(argv[argv.index("-P") + 1], "22241")
            self.assertNotIn("-T", argv)
            self.assertNotIn("-p", argv)
            self.assertIn("ForwardAgent=no", argv)
            self.assertIn("PermitLocalCommand=no", argv)
            self.assertIn("lab@127.0.0.1:/home/lab/artifacts/small.png", argv)
            Path(argv[-1]).write_bytes(b"test artifact")
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch.object(lab, "running", return_value=True), patch("lab.subprocess.run", side_effect=copy):
            receipt = lab.fetch("linux", "small.png")
        self.assertEqual(sha256(receipt["file"]), receipt["sha256"])

    def test_rejects_escape_and_oversized_resource_budget(self):
        self.config["guests"]["linux"]["disk"] = str(self.root.parent / "escape.qcow2")
        write_json(self.path, self.config)
        with self.assertRaises(ValueError):
            Lab(self.path)
        self.config["guests"]["linux"]["disk"] = str(self.root / "vms/linux/disk.qcow2")
        self.config["guests"]["linux"]["memory_mb"] = 65000
        write_json(self.path, self.config)
        with self.assertRaises(ValueError):
            Lab(self.path)

    def test_does_not_touch_unowned_pid(self):
        lab = Lab(self.path)
        write_json(lab.state_path("linux"), {"pid": 123, "identity": {"pid": 123, "creation": 1}})
        with patch("lab.process_identity", return_value={"pid": 123, "creation": 2}):
            with self.assertRaises(RuntimeError):
                lab.owned_process("linux")

    def test_stopped_guest_cannot_connect_qmp(self):
        lab = Lab(self.path)
        with patch("lab.socket.create_connection") as connection:
            with self.assertRaises(RuntimeError):
                lab.qmp("linux", "quit")
            connection.assert_not_called()

    def test_duplicate_operation_lock_preserves_owner(self):
        lab = Lab(self.path)
        with lab.lock("linux"):
            first = (lab.private / "linux.lock").read_bytes()
            with self.assertRaises(RuntimeError):
                with lab.lock("linux"):
                    pass
            self.assertEqual(first, (lab.private / "linux.lock").read_bytes())
        self.assertFalse((lab.private / "linux.lock").exists())

    def test_checkpoint_refuses_live_disk(self):
        lab = Lab(self.path)
        with patch.object(lab, "running", return_value=True):
            with self.assertRaises(RuntimeError):
                lab.checkpoint("linux", "baseline")
        self.assertFalse((lab.root / "checkpoints").exists())

    def test_corrupt_checkpoint_preserves_configuration_and_disk(self):
        lab = Lab(self.path)
        source = self.root / "checkpoints/baseline"
        source.mkdir(parents=True)
        (source / "disk.qcow2").write_bytes(b"corrupt")
        write_json(source / "checkpoint.json", {"disk_sha256": "wrong", "base_sha256": "wrong"})
        before = self.path.read_bytes()
        with patch.object(lab, "running", return_value=False):
            with self.assertRaises(ValueError):
                lab.restore("linux", source)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(list((self.root / "vms/linux").iterdir()), [])

    def test_nonzero_guest_exit_is_retained(self):
        lab = Lab(self.path)
        script = self.root / "selected.sh"
        script.write_text("exit 17")
        import subprocess
        replies = [subprocess.CompletedProcess([], 0, "", ""),
                   subprocess.CompletedProcess([], 0, "", ""),
                   subprocess.CompletedProcess([], 17, "intentional failure", "")]
        with patch.object(lab, "running", return_value=True), patch.object(lab, "ssh", side_effect=replies):
            result = lab.run_script("linux", script, 3)
        self.assertEqual(result["exit_code"], 17)
        receipt = json.loads((Path(result["artifacts"]) / "receipt.json").read_text())
        self.assertEqual(receipt["exit_code"], 17)
        self.assertEqual(receipt["script_sha256"], sha256(script))

    def test_memory_pressure_blocks_launch_before_any_process(self):
        lab = Lab(self.path)
        Path(lab.guest("linux")["disk"]).write_bytes(b"fixture disk")
        with patch("lab.available_memory_mb", return_value=1000), patch("lab.subprocess.Popen") as launch:
            with self.assertRaises(RuntimeError):
                lab.start("linux")
            launch.assert_not_called()

    def test_script_transfer_uses_binary_stdin(self):
        lab = Lab(self.path)
        import subprocess
        response = subprocess.CompletedProcess([], 0, b"ok", b"")
        with patch("lab.subprocess.run", return_value=response) as transport:
            result = lab.ssh("linux", "cat > selected.sh", input=b"echo test\n")
        self.assertFalse(transport.call_args.kwargs["text"])
        self.assertEqual(transport.call_args.kwargs["input"], b"echo test\n")
        self.assertEqual(result.stdout, "ok")


if __name__ == "__main__":
    unittest.main()
