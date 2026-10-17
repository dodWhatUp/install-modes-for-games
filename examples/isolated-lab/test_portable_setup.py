"""Observable import/install/upgrade/recovery invariants in temporary private dirs."""
import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import portable_setup as setup
from prepare_portable_linux import choose_ports, fetch


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "Lab Space Ω"
        self.skill = self.base / "personal/isolated-lab"

    def tearDown(self):
        self.temp.cleanup()

    def bundle(self, version="0.4.0", extra=None, corrupt=None):
        contents = {setup.PREFIX + n: b"source\n" for n in
                    ("lab.py", "Lab.ps1", "guest_mcp.py", "LAB-ROOT-README.md", "LAB-ROOT-AGENTS.template.md", "skill/scripts/resolve_lab.py")}
        contents[setup.PREFIX + "skill/SKILL.md"] = b"---\nname: isolated-lab\ndescription: A test skill\n---\n"
        contents[setup.PREFIX + "release.json"] = json.dumps({"schema": 1, "version": version}).encode()
        if extra:
            contents.update(extra)
        manifest = {"version": version, "files": [{"path": n, "bytes": len(d), "sha256": hashlib.sha256(d).hexdigest()} for n, d in contents.items()]}
        if corrupt:
            contents[next(iter(contents))] = corrupt
        target = self.base / (version + ".zip")
        with zipfile.ZipFile(target, "w") as z:
            for n, d in contents.items():
                z.writestr(n, d)
            z.writestr("SOURCE-MANIFEST.json", json.dumps(manifest))
        return target, setup.digest(target)

    def install(self, version="0.4.0", **options):
        bundle, sha = self.bundle(version)
        return setup.install(bundle, sha, self.root, self.skill, **options)

    def test_relocated_install_has_local_binding_and_unaccepted_runtime(self):
        result = self.install()
        binding = setup.read_json(self.skill / "machine.json")
        self.assertEqual(Path(binding["lab_root"]), self.root)
        self.assertFalse(result["VM_started"])
        self.assertTrue(setup.verify_install(self.root)["ok"])
        self.assertEqual(setup.read_json(self.root / "private/acceptance.json")["linux"], "NOT_TESTED_ON_THIS_HOST")

    def test_wrong_archive_hash_writes_nothing(self):
        bundle, _ = self.bundle()
        with self.assertRaises(ValueError):
            setup.install(bundle, "0" * 64, self.root, self.skill)
        self.assertFalse(self.root.exists())

    def test_corrupt_manifest_writes_nothing(self):
        bundle, sha = self.bundle(corrupt=b"edited")
        with self.assertRaises(ValueError):
            setup.install(bundle, sha, self.root, self.skill)
        self.assertFalse(self.root.exists())

    def test_reject_traversal(self):
        with self.assertRaises(ValueError):
            setup.verify_bundle(*self.bundle(extra={setup.PREFIX + "../private/key.json": b"x"}))

    def test_reject_windows_absolute_path(self):
        with self.assertRaises(ValueError):
            setup.verify_bundle(*self.bundle(extra={"C:/private/key.json": b"x"}))

    def test_reject_backslash(self):
        with self.assertRaises(ValueError):
            setup.safe_name(setup.PREFIX + "..\\private\\key.json")

    def test_reject_reserved_device(self):
        with self.assertRaises(ValueError):
            setup.safe_name(setup.PREFIX + "CON.json")

    def test_reject_binary(self):
        with self.assertRaises(ValueError):
            setup.verify_bundle(*self.bundle(extra={setup.PREFIX + "secret.exe": b"x"}))

    def test_reject_machine_binding_in_bundle(self):
        with self.assertRaises(ValueError):
            setup.verify_bundle(*self.bundle(extra={setup.PREFIX + "skill/machine.json": b"{}"}))

    def test_reject_private_tree(self):
        with self.assertRaises(ValueError):
            setup.verify_bundle(*self.bundle(extra={setup.PREFIX + "private/config.json": b"{}"}))

    def test_reject_case_duplicate(self):
        with self.assertRaises(ValueError):
            setup.verify_bundle(*self.bundle(extra={setup.PREFIX + "LAB.py": b"x"}))

    def test_reject_directory_entry(self):
        with self.assertRaises(ValueError):
            setup.verify_bundle(*self.bundle(extra={setup.PREFIX + "folder/": b""}))

    def test_unknown_nonempty_root_preserved(self):
        self.root.mkdir()
        (self.root / "keep.txt").write_text("keep")
        with self.assertRaises(ValueError):
            self.install()
        self.assertEqual((self.root / "keep.txt").read_text(), "keep")

    def test_existing_skill_requires_explicit_adoption(self):
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("name: isolated-lab\nold")
        with self.assertRaises(RuntimeError):
            self.install()
        self.assertTrue((self.skill / "SKILL.md").read_text().endswith("old"))

    def test_source_local_edit_is_preserved(self):
        self.install()
        source = self.root / "source/examples/isolated-lab/lab.py"
        source.write_text("user edit")
        with self.assertRaises(RuntimeError):
            self.install("0.5.0", upgrade=True)
        self.assertEqual(source.read_text(), "user edit")

    def test_version_upgrade_requires_flag(self):
        self.install()
        with self.assertRaises(RuntimeError):
            self.install("0.5.0")
        self.assertEqual(setup.read_json(self.root / "source/examples/isolated-lab/release.json")["version"], "0.4.0")

    def test_upgrade_rollback_restores_source_and_receipt(self):
        self.install()
        config = self.root / "private/config.json"
        config.write_text('{"test": "private preserved"}')
        with patch.object(setup, "ensure_stopped"):
            upgraded = self.install("0.5.0", upgrade=True)
            setup.rollback(self.root, upgraded["transaction"])
        self.assertEqual(setup.read_json(self.root / "source/examples/isolated-lab/release.json")["version"], "0.4.0")
        self.assertTrue(setup.verify_install(self.root)["ok"])
        self.assertEqual(config.read_text(), '{"test": "private preserved"}')

    def test_rollback_refuses_later_edit(self):
        self.install()
        upgraded = self.install("0.5.0", upgrade=True)
        (self.skill / "SKILL.md").write_text("later edit")
        with self.assertRaises(RuntimeError):
            setup.rollback(self.root, upgraded["transaction"])
        self.assertEqual((self.skill / "SKILL.md").read_text(), "later edit")

    def test_busy_guest_refuses_source_change(self):
        self.install()
        (self.root / "private/config.json").write_text("{}")
        response = __import__('subprocess').CompletedProcess([], 0, '{"linux":{"running":true}}', '')
        with patch.object(setup.subprocess, "run", return_value=response):
            with self.assertRaises(RuntimeError):
                self.install("0.5.0", upgrade=True)

    def test_occupied_setup_lock_preserved(self):
        self.root.mkdir(parents=True)
        (self.root / "source/examples/isolated-lab").mkdir(parents=True)
        (self.root / "source/examples/isolated-lab/lab.py").write_text("source")
        (self.root / "private").mkdir()
        lock = self.root / "private/portable-setup.lock"
        lock.write_text("other owner")
        with self.assertRaises(FileExistsError):
            self.install()
        self.assertEqual(lock.read_text(), "other owner")

    def test_private_cache_hash_failure_never_copies(self):
        downloads = self.base / "downloads"
        downloads.mkdir()
        cache = self.base / "cache"
        cache.mkdir()
        (cache / "file.img").write_bytes(b"wrong")
        with self.assertRaises(RuntimeError):
            fetch({"name": "file.img", "url": "https://example.com/file", "sha256": "0" * 64}, downloads, cache)
        self.assertFalse((downloads / "file.img").exists())

    def test_occupied_guest_lock_preserved(self):
        self.install()
        (self.root / "private/config.json").write_text("{}")
        lock = self.root / "private/linux.lock"
        lock.write_text("guest owner")
        with self.assertRaises(FileExistsError):
            self.install("0.5.0", upgrade=True)
        self.assertEqual(lock.read_text(), "guest owner")

    def test_skill_only_update_keeps_runtime_files(self):
        self.install()
        config = self.root / "private/config.json"
        config.write_text(json.dumps({"root": str(self.root)}))
        runtime_source = self.root / "source/examples/isolated-lab/release.json"
        before = runtime_source.read_bytes()
        result = setup.bind_skill(*self.bundle("0.5.0"), self.root, self.skill, adopt_existing=True)
        self.assertFalse(result["running_source_changed"])
        self.assertEqual(runtime_source.read_bytes(), before)
        self.assertEqual(setup.read_json(self.skill / "machine.json")["workflow_version"], "0.5.0")

    def test_fresh_free_ports_avoid_existing_listener(self):
        # Use an actually available test triple rather than assume the shared lab is stopped.
        first_ssh, _, first_display = choose_ports()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", first_ssh))
            ssh, qmp, display = choose_ports(first_display)
            self.assertNotEqual(ssh, first_ssh)
            self.assertNotEqual(qmp, ssh)
            self.assertGreater(display, first_display)

    def test_synchronized_root_refused(self):
        with self.assertRaises(ValueError):
            setup.dedicated_root(self.base / "OneDrive/Lab")

    def test_git_root_refused(self):
        (self.base / ".git").mkdir()
        with self.assertRaises(ValueError):
            setup.dedicated_root(self.root)


if __name__ == "__main__":
    unittest.main()
