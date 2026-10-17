"""Pure FG inspector contracts: temporary fixtures and mocked NVAPI only."""

import contextlib
import ctypes
import gc
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import weakref

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameFgInspector as g


class FakeNvapi:
    """Use actual C callback signatures to exercise pointer/ABI handling."""

    def __init__(self, *, mode=0, status=None, missing=None, location=1,
                 kind=0, wrong_id=False, app_name="Cyberpunk2077.exe", count=2):
        self.calls = []
        self.status = status or {}
        self.missing = missing
        self.mode, self.location, self.kind = mode, location, kind
        self.wrong_id, self.app_name, self.count = wrong_id, app_name, count
        self.callbacks = {}
        ptr = ctypes.POINTER
        signatures = {
            "Initialize": (), "Unload": (),
            "DriverVersion": (ptr(g._U32), ptr(ctypes.c_char)),
            "CreateSession": (ptr(g._Handle),), "DestroySession": (g._Handle,),
            "LoadSettings": (g._Handle,), "GlobalProfile": (g._Handle, ptr(g._Handle)),
            "FindApplication": (g._Handle, ptr(g._U16), ptr(g._Handle), ptr(g._Application)),
            "GetSetting": (g._Handle, g._Handle, g._U32, ptr(g._Setting)),
        }
        for name, signature in signatures.items():
            callback = ctypes.CFUNCTYPE(ctypes.c_int32, *signature)(self._callback(name))
            self.callbacks[g.INTERFACE_IDS[name]] = callback

        def query(interface):
            if interface == g.INTERFACE_IDS.get(self.missing):
                return None
            callback = self.callbacks.get(interface)
            return ctypes.cast(callback, ctypes.c_void_p).value if callback else None

        self.nvapi_QueryInterface = query

    def _callback(self, name):
        def run(*args):
            self.calls.append((name, args[2] if name == "GetSetting" else None))
            status = self.status.get(name, 0)
            if status:
                return status
            if name == "DriverVersion":
                args[0][0] = 61742
            elif name == "CreateSession":
                args[0][0] = 101
            elif name == "GlobalProfile":
                args[1][0] = 102
            elif name == "FindApplication":
                args[2][0] = 103
                self.application_version = args[3].contents.version
                args[3].contents.app_name = g._utf16(self.app_name)
                self.lookup = ctypes.string_at(args[1], 4096).decode("utf-16-le").split("\0", 1)[0]
            elif name == "GetSetting":
                setting = args[3].contents
                self.setting_version = setting.version
                key = next(key for key, value in g.SETTING_IDS.items() if value == args[2])
                setting.setting_type = self.kind
                setting.location = self.location
                setting.is_predefined = 1
                setting.current.dword = {
                    "mode": self.mode, "frame_count": self.count,
                    "dynamic_max_count": 3, "dynamic_target": 120,
                }[key]
                if self.wrong_id:
                    setting.setting_id = 0
            return 0
        return run


class InspectorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="fg-inspector-test-")
        self.root = Path(self.temp.name)
        self.path = self.root / "settings.json"
        self.executable = self.root / "Cyberpunk2077.exe"
        self.executable.write_bytes(b"pure fixture; never executed")

    def tearDown(self):
        self.temp.cleanup()

    def native(self, owner="DLSS", mode="x2", *, raw=None):
        content = raw if raw is not None else json.dumps({"groups": [{"options": [
            {"name": "FrameGeneration", "value": owner},
            {"name": "DLSS_MultiFrameGeneration", "value": mode},
        ]}]}).encode()
        self.path.write_bytes(content)
        return g._read_native("cyberpunk-2077", self.path)

    def observe(self, fake=None, game="cyberpunk-2077", executable=None):
        fake = fake or FakeNvapi()
        self.native()
        with patch.object(g, "_load_system_nvapi", return_value=fake):
            value = g.inspect_fg(game, executable, self.path)
        return value, fake

    def test_import_is_inert(self):
        source = Path(g.__file__).read_bytes()
        module = types.ModuleType("InspectorInertTest")
        with patch.object(ctypes, "WinDLL", create=True, side_effect=AssertionError("DLL loaded")), \
                patch.object(Path, "open", side_effect=AssertionError("file read")), \
                patch.object(Path, "stat", side_effect=AssertionError("file stat")):
            exec(compile(source, "inert-fixture", "exec"), module.__dict__)
        self.assertEqual(module.VERSION, g.VERSION)

    def test_documented_structures_and_versions(self):
        self.assertEqual(ctypes.sizeof(g._Setting), 12320)
        self.assertEqual(ctypes.sizeof(g._Application), 20492)
        value, fake = self.observe()
        self.assertEqual(fake.setting_version, 12320 | (1 << 16))
        self.assertEqual(fake.application_version, 20492 | (4 << 16))
        self.assertEqual(value["driver"]["version"], "617.42")

    def test_only_documented_read_interfaces(self):
        self.assertEqual(set(g.INTERFACE_IDS), {"Initialize", "Unload", "DriverVersion",
                         "CreateSession", "DestroySession", "LoadSettings", "GlobalProfile",
                         "FindApplication", "GetSetting"})
        self.assertEqual(g.SETTING_IDS["mode"], 0x10308298)
        self.assertEqual(g.SETTING_IDS["frame_count"], 0x104D6667)
        self.assertEqual(g.SETTING_IDS["dynamic_max_count"], 0x10562D0F)
        self.assertEqual(g.SETTING_IDS["dynamic_target"], 0x10CF4125)

    def test_native_fixed_modes(self):
        for mode, expected in (("x2", 2), ("x3", 3), ("x4", 4)):
            with self.subTest(mode=mode):
                result = self.native(mode=mode)
                self.assertEqual((result["status"], result["configured_mode"], result["multiplier"]),
                                 ("observed", "fixed", expected))
                self.assertEqual(result["source_scope"], "caller-selected-file")

    def test_native_off_is_saved_selection_only(self):
        result = self.native(owner="Off")
        self.assertEqual(result["configured_mode"], "off")
        self.assertIsNone(result["multiplier"])
        self.assertIn("saved_native_selection_not_runtime_or_override_evidence", result["reasons"])

    def test_native_unknown_fields_do_not_guess(self):
        for owner, mode in (("FSR3", "x2"), ("DLSS", "x5"), (None, None), ("Auto", "x4")):
            with self.subTest(owner=owner, mode=mode):
                self.assertEqual(self.native(owner, mode)["status"], "unknown")

    def test_native_duplicates_refuse(self):
        for raw in (b'{"name":"FrameGeneration","name":"FrameGeneration","value":"Off"}',
                    b'[{"name":"FrameGeneration","value":"Off"},{"name":"FrameGeneration","value":"Off"}]'):
            with self.subTest(raw=raw):
                self.assertEqual(self.native(raw=raw)["status"], "unknown")

    def test_native_bom_hash_and_time(self):
        raw = b'\xef\xbb\xbf{"name":"FrameGeneration","value":"Off"}'
        result = self.native(raw=raw)
        self.assertEqual(result["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertTrue(result["source_modified_at_utc"].endswith("Z"))

    def test_native_invalid_json_and_utf8(self):
        for raw in (b'{', b'\xff', b'{"name":"FrameGeneration"}'):
            self.assertEqual(self.native(raw=raw)["status"], "unknown")

    def test_native_rejects_nonfinite_numbers_anywhere(self):
        for constant in (b"NaN", b"Infinity", b"-Infinity", b"1e999", b"-1e999"):
            with self.subTest(constant=constant):
                raw = b'{"name":"FrameGeneration","value":"Off","unrelated":' + constant + b'}'
                result = self.native(raw=raw)
                self.assertEqual(result["status"], "unknown")
                self.assertEqual(result["reasons"], ["native_settings_read_unavailable_or_invalid"])
                self.assertIsNone(result["source_sha256"])

    def test_native_bounded_file_size(self):
        self.path.write_bytes(b"x" * (g.MAX_SETTINGS_BYTES + 1))
        self.assertEqual(g._read_native("cyberpunk-2077", self.path)["status"], "unknown")

    def test_native_changed_during_read(self):
        self.native()
        real = os.fstat
        counter = [0]
        def changed(fd):
            result = real(fd)
            counter[0] += 1
            if counter[0] == 2:
                return types.SimpleNamespace(st_dev=result.st_dev, st_ino=result.st_ino,
                    st_size=result.st_size, st_mtime_ns=result.st_mtime_ns + 1)
            return result
        with patch.object(os, "fstat", side_effect=changed):
            result = g._read_native("cyberpunk-2077", self.path)
        self.assertEqual(result["reasons"], ["native_settings_changed_during_read"])

    def test_native_unsupported_paths_are_sanitized(self):
        for path in ("relative.json", r"\\private-host\secret\settings.json", self.root / "wrong.txt"):
            result = g._read_native("cyberpunk-2077", path)
            self.assertEqual(result["status"], "unknown")
            self.assertNotIn(str(path), json.dumps(result))

    @unittest.skipUnless(os.name == "nt", "Windows current-known native location")
    def test_native_current_known_scope(self):
        known = self.root / "CD Projekt Red" / "Cyberpunk 2077" / "UserSettings.json"
        known.parent.mkdir(parents=True)
        self.native()
        known.write_bytes(self.path.read_bytes())
        with patch.dict(os.environ, {"LOCALAPPDATA": str(self.root)}):
            result = g._read_native("cyberpunk-2077", None)
        self.assertEqual(result["source_scope"], "current-known-path")
        self.assertEqual(result["status"], "observed")

    def test_skyrim_native_is_unknown_not_off(self):
        result = g._read_native("skyrim-special-edition", self.path)
        self.assertEqual((result["status"], result["configured_mode"]), ("unknown", "unknown"))

    def test_exact_target_hash_lookup_and_privacy(self):
        result, fake = self.observe(executable=self.executable)
        target = result["target"]
        self.assertEqual(target["executable_match"], "exact-path")
        self.assertEqual(target["executable_path_sha256"], hashlib.sha256(
            str(self.executable.resolve()).casefold().encode()).hexdigest())
        self.assertEqual(fake.lookup, str(self.executable.resolve()))
        self.assertEqual(result["driver"]["effective_configuration"]["profile_match"], "exact-path")
        exported = json.dumps(result)
        self.assertNotIn(str(self.root), exported)
        self.assertNotIn(str(self.path), exported)

    def test_default_lookup_is_only_basename(self):
        result, fake = self.observe()
        self.assertEqual(fake.lookup, "Cyberpunk2077.exe")
        self.assertEqual(result["target"]["executable_match"], "basename-only")
        self.assertIsNone(result["target"]["executable_path_sha256"])
        self.assertIn("basename_lookup_not_exact_rendering_path", result["driver"]["reasons"])

    def test_invalid_target_does_not_load_nvapi(self):
        cases = [("unsupported", None), ({}, None), ("cyberpunk-2077", "other.exe"),
                 ("cyberpunk-2077", "folder/Cyberpunk2077.exe"),
                 ("cyberpunk-2077", r"\\host\folder\Cyberpunk2077.exe"),
                 ("cyberpunk-2077", "\0Cyberpunk2077.exe"),
                 ("cyberpunk-2077", self.root / "missing" / "Cyberpunk2077.exe")]
        with patch.object(g, "_load_system_nvapi", side_effect=AssertionError("native API read")) as load:
            for game, executable in cases:
                with self.subTest(game=game, executable=executable):
                    result = g.inspect_fg(game, executable, self.path)
                    self.assertEqual(result["driver"]["status"], "unknown")
            load.assert_not_called()

    def test_public_observation_seal(self):
        result, _ = self.observe()
        self.assertTrue(g.is_inspector_observation(result))
        self.assertFalse(g.is_inspector_observation(dict(result)))
        self.assertFalse(g.is_inspector_observation(json.loads(json.dumps(result))))
        manual = g._IssuedObservation(result)
        manual._seal = result._seal
        self.assertFalse(g.is_inspector_observation(manual))
        result["native"]["multiplier"] = 99
        self.assertFalse(g.is_inspector_observation(result))

    def test_provenance_registry_does_not_retain_observations(self):
        result, _ = self.observe()
        identity, ref = id(result), weakref.ref(result)
        del result
        gc.collect()
        self.assertIsNone(ref())
        self.assertNotIn(identity, g._issued)

    def test_override_disabled_is_not_fg_off(self):
        result, _ = self.observe(FakeNvapi(mode=0))
        self.assertEqual(result["driver"]["global"]["configured_mode"], "override-disabled")
        self.assertEqual(result["driver"]["global"]["settings"]["mode"]["raw_value"], 0)
        self.assertEqual(result["effective"]["mode"], "unknown")

    def test_all_documented_modes_remain_configuration_only(self):
        for raw, name in g.MODE_NAMES.items():
            with self.subTest(raw=raw):
                result, _ = self.observe(FakeNvapi(mode=raw))
                self.assertEqual(result["driver"]["per_application"]["configured_mode"], name)
                self.assertEqual(result["effective"]["verification"], "configured-only")
                self.assertEqual(result["runtime"]["status"], "not_observed")
                self.assertIsNone(result["driver"]["per_application"]["fixed_multiplier"])

    def test_global_and_app_inheritance_is_explicit(self):
        for raw, location in g.LOCATIONS.items():
            with self.subTest(location=location):
                result, _ = self.observe(FakeNvapi(location=raw))
                setting = result["driver"]["effective_configuration"]["settings"]["mode"]
                self.assertEqual(setting["location"], location)
                self.assertTrue(setting["predefined"])
                self.assertEqual(result["driver"]["per_application"], result["driver"]["effective_configuration"])
                self.assertIsNot(result["driver"]["per_application"], result["driver"]["effective_configuration"])

    def test_setting_not_found_is_unknown_not_zero_off(self):
        result, _ = self.observe(FakeNvapi(status={"GetSetting": -160}))
        self.assertEqual(result["driver"]["status"], "unknown")
        setting = result["driver"]["global"]["settings"]["mode"]
        self.assertEqual(setting["status"], "unknown")
        self.assertIsNone(setting["raw_value"])
        self.assertEqual(setting["nvapi_status"], -160)

    def test_unsupported_value_type_identity_or_location_refuses(self):
        for fake in (FakeNvapi(mode=5), FakeNvapi(count=16), FakeNvapi(kind=1),
                     FakeNvapi(location=4), FakeNvapi(wrong_id=True)):
            result, _ = self.observe(fake)
            self.assertEqual(result["driver"]["global"]["status"], "unknown")
            self.assertEqual(result["effective"]["mode"], "unknown")

    def test_ambiguous_profile_lookup_blocks_application(self):
        result, fake = self.observe(FakeNvapi(status={"FindApplication": -182}))
        self.assertEqual(result["driver"]["status"], "partial")
        self.assertEqual(result["driver"]["per_application"]["status"], "unknown")
        self.assertEqual(result["driver"]["application_lookup_status"], -182)
        self.assertEqual([name for name, _ in fake.calls][-2:], ["DestroySession", "Unload"])

    def test_wrong_returned_application_is_unknown(self):
        result, _ = self.observe(FakeNvapi(app_name="WrongGame.exe"))
        self.assertEqual(result["driver"]["per_application"]["status"], "unknown")

    def test_read_session_failure_still_cleans_up(self):
        result, fake = self.observe(FakeNvapi(status={"LoadSettings": -1}))
        self.assertEqual(result["driver"]["status"], "unknown")
        self.assertEqual([name for name, _ in fake.calls][-2:], ["DestroySession", "Unload"])

    def test_missing_interface_does_not_initialize(self):
        fake = FakeNvapi(missing="GetSetting")
        result, _ = self.observe(fake)
        self.assertEqual(result["driver"]["status"], "unknown")
        self.assertEqual(fake.calls, [])

    def test_cleanup_failure_marks_driver_unknown(self):
        for operation, reason in (("DestroySession", "nvapi_session_cleanup_failed"),
                                  ("Unload", "nvapi_unload_failed")):
            result, _ = self.observe(FakeNvapi(status={operation: -1}))
            self.assertEqual(result["driver"]["status"], "unknown")
            self.assertIn(reason, result["driver"]["reasons"])

    def test_external_errors_never_echo_private_paths(self):
        with patch.object(g, "_load_system_nvapi", side_effect=OSError(str(self.path))):
            result = g.inspect_fg("cyberpunk-2077", native_settings_path=self.path)
        self.assertNotIn(str(self.path), json.dumps(result))
        self.assertEqual(result["driver"]["status"], "unknown")

    def test_platform_refusal_has_no_install_or_fallback(self):
        with patch.object(os, "name", "posix"), \
                patch.object(ctypes, "WinDLL", create=True, side_effect=AssertionError("DLL load")):
            with self.assertRaises(g._NvapiError):
                g._load_system_nvapi()

    def test_native_and_driver_inputs_remain_unchanged(self):
        self.native()
        before = self.path.read_bytes()
        self.observe(executable=self.executable)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.executable.read_bytes(), b"pure fixture; never executed")

    def test_cli_output_is_observation_not_gate_pass(self):
        value = g.inspect_fg("unsupported")
        with patch.object(g, "inspect_fg", return_value=value), contextlib.redirect_stdout(io.StringIO()) as output:
            code = g.main(["--game", "cyberpunk-2077"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["runtime"]["status"], "not_observed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
