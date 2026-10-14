"""Installer operates only on isolated authored dummy releases/settings."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "Install-GameToolsRelease.ps1"
PWSH = shutil.which("pwsh")


@unittest.skipUnless(PWSH and Path(PWSH).is_file(),
                     "PowerShell 7 is unavailable; installer execution remains unverified in this environment.")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="GameToolsInstallerFixture-"); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.release = self.root / "release"; (self.release / "scripts").mkdir(parents=True)
        self.script = self.release / "scripts/Install-GameToolsRelease.ps1"; shutil.copyfile(SCRIPT, self.script)
        self.manifest = {"component_versions": {"tool_hub": "0.11.0"}, "files": []}
        for name in ("AzeronOverlayStudio.integrated.ahk", "GameInputModule.ahk", "OverlayStudioGameInput.ahk", "StudioPictureModule.ahk", "StudioOverlayGroups.ahk"):
            path = self.release / "examples/game-input" / name; path.parent.mkdir(parents=True, exist_ok=True)
            raw = ("; Inert installer fixture " + name).encode(); path.write_bytes(raw)
            self.manifest["files"].append({"path": path.relative_to(self.release).as_posix(), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
        self.write_manifest()

    def write_manifest(self):
        (self.release / "MANIFEST.json").write_text(json.dumps(self.manifest))

    def run_script(self, *args):
        return subprocess.run([PWSH, "-NoProfile", "-File", str(self.script), *args], capture_output=True, text=True)

    def test_inspect_has_no_destination_effect(self):
        result = self.run_script(); self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["activation"], "none")

    def test_stage_and_reject_existing(self):
        target = self.root / "staged"; result = self.run_script("-Mode", "Stage", "-Destination", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        for row in self.manifest["files"]:
            self.assertEqual((target / row["path"]).read_bytes(), (self.release / row["path"]).read_bytes())
        self.assertNotEqual(self.run_script("-Mode", "Stage", "-Destination", str(target)).returncode, 0)

    def test_drift_refuses_before_staging(self):
        path = self.release / self.manifest["files"][0]["path"]; path.write_text("changed")
        target = self.root / "blocked"
        self.assertNotEqual(self.run_script("-Mode", "Stage", "-Destination", str(target)).returncode, 0)
        self.assertFalse(target.exists())

    def test_wrong_version_refuses(self):
        self.manifest["component_versions"]["tool_hub"] = "0.10.0"; self.write_manifest()
        self.assertNotEqual(self.run_script().returncode, 0)

    def test_manifest_path_traversal_refuses(self):
        self.manifest["files"][0]["path"] = "../outside.ahk"; self.write_manifest()
        self.assertNotEqual(self.run_script().returncode, 0)

    def test_upgrade_requires_expected_hashes(self):
        target = self.root / "host"; target.mkdir()
        self.assertNotEqual(self.run_script("-Mode", "UpgradeStudio", "-Destination", str(target)).returncode, 0)
        self.assertEqual(list(target.iterdir()), [])

    def test_upgrade_fixture_only_preserves_settings_and_rollback(self):
        target = self.root / "host"; target.mkdir()
        appdata = self.root / "fixture-appdata"; settings = appdata / "AzeronOverlayStudio/settings.ini"
        settings.parent.mkdir(parents=True); settings.write_text("[fixture]\nPreserve=true")
        expected = {}
        for row in self.manifest["files"]:
            name = Path(row["path"]).name.replace(".integrated", "")
            if name == "StudioOverlayGroups.ahk": expected[name] = "absent"; continue
            raw = ("; original fixture " + name).encode(); (target / name).write_bytes(raw)
            expected[name] = hashlib.sha256(raw).hexdigest()
        receipt = self.root / "expected.json"; receipt.write_text(json.dumps(expected))
        code = "$env:APPDATA=$args[0]; function Get-Process { @() }; & $args[1] -Mode UpgradeStudio -Destination $args[2] -ExpectedInstalledManifest $args[3]"
        # Fixed authored wrapper mocks only process discovery; never terminates
        # any host or reads the real APPDATA settings.
        wrapper = self.root / "fixture-wrapper.ps1"; wrapper.write_text(code)
        result = subprocess.run([PWSH, "-NoProfile", "-File", str(wrapper), str(appdata), str(self.script), str(target), str(receipt)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        saved = json.loads(result.stdout)
        self.assertEqual(settings.read_text(), "[fixture]\nPreserve=true")
        backup = Path(saved["backup"])
        for name, fingerprint in expected.items():
            if fingerprint != "absent": self.assertEqual(hashlib.sha256((backup / name).read_bytes()).hexdigest(), fingerprint)
        self.assertEqual((backup / "settings.ini").read_bytes(), settings.read_bytes())
        self.assertEqual(saved["activation"], "none")


if __name__ == "__main__": unittest.main()
