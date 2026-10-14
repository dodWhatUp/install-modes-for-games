"""Access preparation fixtures; no app, input, shortcut or profile activation."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.dont_write_bytecode=True
scripts=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(scripts))
spec=importlib.util.spec_from_file_location("access",scripts/"Create-UnifiedToolsLaunchers.py")
access=importlib.util.module_from_spec(spec); spec.loader.exec_module(access)
spec2=importlib.util.spec_from_file_location("unified_fixture",scripts/"tests/Test-GameToolUnified.py")
fixtures=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(fixtures)


class Launchers(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="launcher-contract-")
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)
        self.root=self.base/"installed"; self.studio=self.base/"Studio"; self.studio.mkdir()
        self.data=self.base/"data"; self.data.mkdir()
        self.registry=self.data/"tools.json"; self.registry.write_bytes(b"{\"private\":true}")
        self.settings=self.base/"settings.ini"; self.settings.write_bytes(b"original personal settings")
        self.runtime=self.base/"pythonw.exe"; self.runtime.write_bytes(b"runtime fixture, not executable")
        self.ahk=self.base/"AutoHotkey64.exe"; self.ahk.write_bytes(b"AHK fixture, not executable")
        initial=dict(studio_dir=str(self.studio),studio_settings=str(self.settings),data_dir=str(self.data),
                     pythonw=str(self.runtime),ahk=str(self.ahk))
        access.api.apply_release(self.root,fixtures.package(),expected_state_sha256=None,
                                 expected_studio=access.api.studio_hashes(self.studio),initial=initial,names=[])
        self.original={p:p.read_bytes() for p in (self.settings,self.registry,*self.studio.glob("*.ahk"))}
        self.output=self.base/"Access"; self.recovery=self.base/"recovery-access"
        self.addCleanup(self.assert_preserved)

    def assert_preserved(self):
        for path,raw in self.original.items(): self.assertEqual(path.read_bytes(),raw)

    def prepare(self,identity=lambda p:Path(p),names=[]):
        return access.prepare_access(self.root,self.output,self.recovery,identity=identity,names=names)

    def test_same_paths_leave_install_metadata_byte_identical(self):
        raw=(self.root/"install.json").read_bytes()
        result=self.prepare()
        self.assertEqual(raw,(self.root/"install.json").read_bytes())
        self.assertFalse(result["metadata_changed"])
        self.assertTrue(Path(result["launch_file"]).exists())
        self.assertEqual((self.recovery/"install.json.before").read_bytes(),raw)
        self.assertFalse(result["app_launched"])

    def test_real_redirected_data_is_referenced_not_copied(self):
        logical=self.base/"logical-data"; logical.mkdir()
        (logical/"tools.json").write_bytes(self.registry.read_bytes())
        value=access.api.read_install(self.root); value["data_dir"]=str(logical)
        access.api.atomic_json(self.root/"install.json",value)
        def identity(path):
            return self.registry if Path(path)==logical/"tools.json" else Path(path)
        result=self.prepare(identity)
        new=access.api.read_install(self.root)
        self.assertEqual(new,dict(value,data_dir=str(self.data)))
        self.assertEqual(result["changed_fields"],["data_dir"])
        self.assertEqual(new["current"],value["current"])

    def test_real_install_root_used_by_launcher(self):
        alias=self.base/"virtual-root"
        def identity(path):
            return self.root/"install.json" if Path(path)==alias/"install.json" else Path(path)
        plan=access.inspect_access(alias,identity=identity)
        self.assertEqual(plan["root"],self.root)
        self.assertIn(str(self.root/"Start-UnifiedTools.pyw"),access.launcher_text(plan))

    def test_tampered_bootstrap_refused(self):
        (self.root/"Start-UnifiedTools.pyw").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"Stable launcher"): self.prepare()
        self.assertFalse(self.output.exists())

    def test_source_drift_refused(self):
        (self.root/"versions"/access.api.read_install(self.root)["current"]/"scripts/Game-Tool-Hub.py").write_bytes(b"tampered")
        with self.assertRaises(ValueError): self.prepare()

    def test_registry_identity_mismatch_refused(self):
        other=self.base/"other"; other.mkdir(); (other/"tools.json").write_bytes(b"other")
        def identity(path): return other/"tools.json" if Path(path)==self.registry else Path(path)
        with self.assertRaisesRegex(ValueError,"Registry changed"): self.prepare(identity)

    def test_existing_output_not_overwritten(self):
        self.output.mkdir(); existing=self.output/"keep.txt"; existing.write_bytes(b"keep")
        with self.assertRaises(ValueError): self.prepare()
        self.assertEqual(existing.read_bytes(),b"keep")

    def test_existing_checkpoint_not_overwritten(self):
        self.recovery.mkdir()
        with self.assertRaises(ValueError): self.prepare()

    def test_active_owner_blocks_preparation(self):
        for name in ("autohotkey64.exe","skyrimse.exe","cyberpunk2077.exe","obs64.exe","presentmon.exe"):
            with self.subTest(name=name), self.assertRaises(ValueError): self.prepare(names=[name])
        self.assertFalse(self.recovery.exists())

    def test_lease_is_released_after_output_failure(self):
        with mock.patch.object(Path,"mkdir",side_effect=OSError("fixture write failure")):
            with self.assertRaises(OSError): self.prepare()
        self.assertFalse((self.studio/access.api.SOURCE_LOCK).exists())

    def test_cmd_paths_quoted_and_no_file_association(self):
        plan=dict(runtime=self.base/"space name"/"pythonw.exe",launcher=self.base/"Hebrew שלום"/"Start-UnifiedTools.pyw")
        command=access.launcher_text(plan)
        self.assertIn('start "" "',command)
        self.assertIn('" -B "',command)
        self.assertIn("DisableDelayedExpansion",command)
        self.assertIn("chcp 65001 >nul",command)
        self.assertNotIn("powershell",command.lower())

    def test_cmd_variable_and_quote_paths_refused(self):
        for character in ('%','!','"','\r','\n'):
            with self.subTest(character=repr(character)), self.assertRaises(ValueError):
                access.cmd_quote(self.base/("unsafe"+character+"path"))


if __name__=="__main__": unittest.main()
