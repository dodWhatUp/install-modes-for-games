import contextlib
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from contracts import canonical, digest
import lima_backend as backend
import stopped_backup as recovery
import prepare_lima
from install_local import install, upgrade


class LimaGuards(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "lima"; self.home.mkdir(mode=0o700)
        self.bundle = self.home / "il-test"; self.bundle.mkdir()
        self.cli = self.root / "limactl"; self.cli.write_bytes(b"verified-test-binary")
        for name in ("lima.yaml", "vz-identifier"):
            (self.bundle / name).write_bytes(name.encode())
        self.config = {"instance_name": "il-test", "lima_home": str(self.home), "bundle_path": str(self.bundle),
                       "lima_cli": str(self.cli), "lima_cli_sha256": digest(self.cli.read_bytes()),
                       "lima_yaml_sha256": digest((self.bundle / "lima.yaml").read_bytes()),
                       "vz_identifier_sha256": digest((self.bundle / "vz-identifier").read_bytes()),
                       "resources": {"cpus": 2, "memory": 4294967296, "disk": 12884901888},
                       "bootstrap_ssh_port": 50001, "ssh_port": 50002}
        self.row = {"name": "il-test", "dir": str(self.bundle), "status": "Running", "vmType": "vz", "arch": "aarch64",
                    "cpus": 2, "memory": 4294967296, "disk": 12884901888, "sshAddress": "127.0.0.1", "sshLocalPort": 50001,
                    "config": {"os": "Linux", "plain": True, "rosetta": {"enabled": False},
                               "audio": {"device": "none"}, "video": {"display": "none"},
                               "ssh": {"forwardAgent": False, "forwardX11": False, "loadDotSSHPubKeys": False},
                               "containerd": {"system": False, "user": False}}}
        self.patches = [patch.object(backend.platform, "system", return_value="Darwin"),
                        patch.object(backend.platform, "machine", return_value="arm64")]
        for p in self.patches: p.start()

    def tearDown(self):
        for p in self.patches: p.stop()
        self.temp.cleanup()

    def observe(self, row=None):
        return backend.observe(self.config, lambda argv: json.dumps(row or self.row) + "\n")

    def test_exact_scoped_backend_and_separate_bridge_port(self):
        argv = backend.command(self.config, "list", "il-test")
        self.assertEqual(argv[:2], ["/usr/bin/env", "LIMA_HOME=" + str(self.home)])
        self.assertIn("--tty=false", argv)
        self.assertEqual(self.observe()[1], "running")

    def test_changed_binary_or_machine_identity_refused(self):
        self.cli.write_bytes(b"changed")
        with self.assertRaises(ValueError): self.observe()
        self.cli.write_bytes(b"verified-test-binary")
        (self.bundle / "vz-identifier").write_bytes(b"different-machine")
        with self.assertRaises(ValueError): self.observe()

    def test_wrong_instance_or_path_refused(self):
        for key, value in (("name", "different"), ("dir", str(self.root))):
            row = copy.deepcopy(self.row); row[key] = value
            with self.assertRaises(ValueError): self.observe(row)

    def test_changed_resource_or_loopback_endpoint_refused(self):
        for key, value in (("cpus", 4), ("memory", 8589934592), ("sshLocalPort", 50003), ("sshAddress", "0.0.0.0")):
            row = copy.deepcopy(self.row); row[key] = value
            with self.assertRaises(ValueError): self.observe(row)

    def test_host_sharing_or_interactive_devices_refused(self):
        changes = [("mounts", [{"location": "~"}]), ("plain", False), ("video", {"display": "cocoa"}),
                   ("ssh", {"forwardAgent": True}), ("containerd", {"system": True})]
        for key, value in changes:
            row = copy.deepcopy(self.row); row["config"][key] = value
            with self.assertRaises((ValueError, KeyError)): self.observe(row)


class RecoveryAndInstallation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.private = self.root / "private"; self.private.mkdir(mode=0o700)
        self.bundle = self.root / "bundle"; self.bundle.mkdir()
        self.home = self.root / "lima"; (self.home / "_config").mkdir(parents=True)
        for name in recovery.BUNDLE:
            (self.bundle / name).write_bytes(bytes(2 * 1024 * 1024) if name == "disk" else name.encode())
        for name in recovery.PRIVATE:
            p = self.private / name; p.write_bytes(name.encode()); p.chmod(0o600)
        for name in ("user", "user.pub"): (self.home / "_config" / name).write_bytes(name.encode())
        outer = self

        class Lab:
            def __init__(self, root):
                self.private = outer.private
                self.config = {"backend": "lima", "bundle_path": str(outer.bundle), "lima_home": str(outer.home)}
            def lock(self): return contextlib.nullcontext()
            def vm(self): return None, "stopped", outer.bundle

        self.fake = Lab

    def tearDown(self): self.temp.cleanup()

    def make(self):
        with patch.object(recovery, "MacLab", self.fake):
            return recovery.make(self.root, self.root / "encrypted")

    def test_authenticated_encrypted_sparse_roundtrip_and_collision(self):
        made = self.make(); dest = self.root / "restored"
        result = recovery.restore(Path(made["backup"]), Path(made["keyfile"]), dest)
        self.assertTrue(result["restored_bytes_verified"])
        self.assertEqual((dest / "bundle/disk").read_bytes(), (self.bundle / "disk").read_bytes())
        with self.assertRaises(FileExistsError): recovery.restore(Path(made["backup"]), Path(made["keyfile"]), dest)

    def test_tamper_or_wrong_key_refused_before_decryption(self):
        made = self.make(); archive = Path(made["backup"]) / "stopped-backup.enc"
        wrong = self.private / "wrong-key"; wrong.write_bytes(b"wrong"); wrong.chmod(0o600)
        with patch.object(recovery.subprocess, "Popen", side_effect=AssertionError("must not decrypt")):
            with self.assertRaises(ValueError): recovery.restore(Path(made["backup"]), wrong, self.root / "no-restore")
        with archive.open("r+b") as f: f.seek(32); f.write(b"tampered")
        with patch.object(recovery.subprocess, "Popen", side_effect=AssertionError("must not decrypt")):
            with self.assertRaises(ValueError): recovery.restore(Path(made["backup"]), Path(made["keyfile"]), self.root / "no-restore")
        self.assertFalse((self.root / "no-restore").exists())

    def test_reservation_blocks_backup_before_output_creation(self):
        (self.private / "reservation.json").write_text("other-owner")
        with self.assertRaises(ValueError): self.make()
        self.assertFalse((self.root / "encrypted").exists())

    def test_existing_enrollment_never_installs_or_replaces(self):
        before = (self.private / "config.json").read_bytes()
        with patch.object(prepare_lima.platform, "system", return_value="Darwin"), patch.object(prepare_lima.platform, "machine", return_value="arm64"), patch.object(prepare_lima, "install_tool", side_effect=AssertionError("must not install")):
            with self.assertRaises(FileExistsError): prepare_lima.prepare(self.root)
        self.assertEqual((self.private / "config.json").read_bytes(), before)

    def test_upgrade_preserves_later_skill_edits(self):
        source = self.root / "minimal-source"; (source / "skill").mkdir(parents=True)
        (source / "skill/SKILL.md").write_text("original skill")
        data = (source / "skill/SKILL.md").read_bytes()
        manifest = {"schema": 1, "version": "test", "files": [{"path": "skill/SKILL.md", "bytes": len(data), "sha256": digest(data)}]}
        (source / "MAC-SOURCE-MANIFEST.json").write_bytes(canonical(manifest))
        root = self.root / "installed"; skill = self.root / "skills/isolated-lab"; agents = self.root / "instructions/AGENTS.md"
        install(source, root, skill, agents)
        (skill / "SKILL.md").write_text("later user edit")
        with self.assertRaises(ValueError): upgrade(source, root, skill)
        self.assertEqual((skill / "SKILL.md").read_text(), "later user edit")


if __name__ == "__main__": unittest.main()
