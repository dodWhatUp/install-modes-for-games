"""Offline update/recovery and UI contracts. No desktop input/game launches."""
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
sys.dont_write_bytecode=True
SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
import GameToolUnified as api

def package(revision="0.12.0",suffix="first"):
    payloads={name: ("; fixture "+suffix).encode() for name in api.REQUIRED}
    payloads["scripts/Game-Tool-Hub.py"]=f'VERSION = "{revision}"\n'.encode()
    payloads[api.STUDIO["AzeronOverlayStudio.ahk"]]=b'        this.Version := "2.2.0-unified.1"\n'
    manifest={"schema_version":1,"bundle":"GameTools","component_versions":{"tool_hub":revision,"overlay_studio":"2.2.0-unified.1"},
        "files":[{"path":n,"bytes":len(raw),"sha256":api.digest(raw)} for n,raw in sorted(payloads.items())]}
    return {"manifest":manifest,"payloads":payloads,"sha256":api.digest(suffix.encode())}

def archive_bytes(release, extra=None):
    data=io.BytesIO()
    with zipfile.ZipFile(data,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("MANIFEST.json",json.dumps(release["manifest"]))
        for name,raw in release["payloads"].items(): z.writestr(name,raw)
        if extra: z.writestr(*extra)
    return data.getvalue()

class Updates(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="UnifiedTools-contract-")
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name); self.root=self.base/"installed"; self.studio=self.base/"Studio"; self.studio.mkdir()
        self.settings=self.base/"settings.ini"; self.settings.write_bytes(b"existing original settings")
        self.data=self.base/"Hub"; self.data.mkdir()
        (self.data/"overlay-groups.json").write_bytes(b"private overlay/profile fixture")
        for name in list(api.STUDIO)[:3]: (self.studio/name).write_bytes(("original "+name).encode())
        self.originals=api.studio_hashes(self.studio)
        self.initial={"studio_dir":str(self.studio),"studio_settings":str(self.settings),"data_dir":str(self.data),
                      "pythonw":str(self.base/"pythonw.exe"),"ahk":str(self.base/"AutoHotkey64.exe")}
        self.release=package()
        self.settings_raw=self.settings.read_bytes(); self.overlay_raw=(self.data/"overlay-groups.json").read_bytes()
        self.addCleanup(self.assert_preserved)

    def assert_preserved(self):
        self.assertEqual(self.settings.read_bytes(),self.settings_raw)
        self.assertEqual((self.data/"overlay-groups.json").read_bytes(),self.overlay_raw)

    def install(self):
        return api.apply_release(self.root,self.release,expected_state_sha256=None,expected_studio=self.originals,initial=self.initial,names=[])

    def upgrade(self,release=None,names=None,state_hash=None):
        v=api.read_install(self.root)
        return api.apply_release(self.root,release or package("0.12.1","second"),
            expected_state_sha256=state_hash or api.digest(api.read_bytes(self.root/"install.json")),expected_studio=v["studio_hashes"],names=names or [])

    def test_install_byte_verified_preserves_data(self):
        value=self.install()
        self.assertEqual(api.studio_hashes(self.studio),value["studio_hashes"])
        self.assertIsNone(value["previous"])
        backup=Path(value["recovery"])
        self.assertEqual((backup/"settings.ini.backup").read_bytes(),self.settings_raw)
        self.assertEqual(api.load_json(backup/"transaction.json")["phase"],"committed")
        for name in list(api.STUDIO)[:3]: self.assertEqual(api.digest((backup/name).read_bytes()),self.originals[name])

    def test_update_and_previous_rollback(self):
        first=self.install(); second=self.upgrade()
        self.assertEqual(second["previous"],first["current"])
        rolled=api.rollback_previous(self.root,expected_state_sha256=api.digest(api.read_bytes(self.root/"install.json")),names=[])
        self.assertEqual(rolled["component_versions"]["tool_hub"],"0.12.0")
        self.assertEqual(rolled["studio_hashes"],first["studio_hashes"])
        self.assertTrue((self.root/"versions"/second["current"]).exists())

    def test_launch_uses_current_pointer_and_original_data(self):
        v=self.install(); command=api.launch_command(self.root)
        self.assertIn(str(self.data),command)
        self.assertIn(str(self.root/"versions"/v["current"]/"scripts/Game-Tool-Hub.py"),command)
        self.assertIn("--unified-install",command)
        self.assertNotIn("SkyrimSE",str(command))

    def test_active_owners_block_before_mutation(self):
        for name in ("SkyrimSE.exe","CYBERPUNK2077.exe","obs64.exe","CapFrameX.exe","AutoHotkey64.exe"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                api.apply_release(self.root,self.release,expected_state_sha256=None,expected_studio=self.originals,initial=self.initial,names=[name])
        self.assertFalse(self.root.exists()); self.assertEqual(api.studio_hashes(self.studio),self.originals)

    def test_studio_drift_blocks_update(self):
        self.install(); (self.studio/"GameInputModule.ahk").write_bytes(b"newer owner changes")
        with self.assertRaises(ValueError): self.upgrade()
        self.assertEqual((self.studio/"GameInputModule.ahk").read_bytes(),b"newer owner changes")

    def test_pointer_drift_blocks_update(self):
        self.install()
        with self.assertRaises(ValueError): self.upgrade(state_hash="0"*64)

    def test_partial_swap_recovers_exact_owned_bytes(self):
        first=self.install(); state=(self.root/"install.json").read_bytes(); original=api._replace_file; count=0
        def fail_second(path,raw):
            nonlocal count
            count+=1
            if count==2: raise OSError("synthetic replacement interruption")
            return original(path,raw)
        with mock.patch.object(api,"_replace_file",side_effect=fail_second), self.assertRaises(OSError): self.upgrade()
        self.assertEqual(api.studio_hashes(self.studio),first["studio_hashes"])
        self.assertEqual((self.root/"install.json").read_bytes(),state)
        self.assertFalse((self.root/"update.lock").exists())

    def test_source_failure_refuses_destructive_rollback_on_drift(self):
        self.install(); original=api._replace_file; count=0
        def fail_and_drift(path,raw):
            nonlocal count
            count+=1
            if count==2:
                (self.studio/"AzeronOverlayStudio.ahk").write_bytes(b"concurrent user edit")
                raise OSError("synthetic conflict")
            return original(path,raw)
        with mock.patch.object(api,"_replace_file",side_effect=fail_and_drift),self.assertRaises(OSError): self.upgrade()
        self.assertEqual((self.studio/"AzeronOverlayStudio.ahk").read_bytes(),b"concurrent user edit")
        self.assertTrue((self.root/"update.lock").exists())

    def test_incomplete_transaction_blocks_launch_and_update(self):
        self.install(); (self.root/"update.lock").write_bytes(b"interrupted")
        with self.assertRaises(ValueError): api.launch_command(self.root)
        with self.assertRaises(FileExistsError): self.upgrade()

    def test_immutable_sources_and_missing_initial_rollback(self):
        v=self.install()
        with self.assertRaises(ValueError): api.rollback_previous(self.root,expected_state_sha256=api.digest(api.read_bytes(self.root/"install.json")),names=[])
        (self.root/"versions"/v["current"]/"scripts/Game-Tool-Hub.py").write_bytes(b"tampered")
        with self.assertRaises(ValueError): api.launch_command(self.root)

    def test_expected_install_hashes_fail_closed(self):
        with self.assertRaises(ValueError):
            api.apply_release(self.root,self.release,expected_state_sha256=None,expected_studio={},initial=self.initial,names=[])
        self.assertFalse(self.root.exists())

    def test_zip_verified_and_wrong_sha(self):
        raw=archive_bytes(self.release); p=self.base/"source.zip"; p.write_bytes(raw)
        self.assertEqual(api.inspect_archive(p,api.digest(raw))["payloads"],self.release["payloads"])
        for sha in ("0"*64,"missing"):
            with self.assertRaises(ValueError): api.inspect_archive(p,sha)

    def test_unsafe_duplicate_unlisted_or_reserved_archive(self):
        for name in ("scripts/../outside.py","/absolute","scripts\\bad.py","scripts/CON.py","scripts/extra.py","SCRIPTS/Game-Tool-Hub.py"):
            with self.subTest(name=name):
                raw=archive_bytes(self.release,(name,b"bad")); p=self.base/"source.zip"; p.write_bytes(raw)
                with self.assertRaises(ValueError): api.inspect_archive(p,api.digest(raw))

    def test_manifest_tamper_version_and_missing_dependency(self):
        for change in ("bytes","version","required"):
            r=package()
            if change=="bytes": r["payloads"]["scripts/Game-Tool-Hub.py"]+=b"changed"
            elif change=="version": r["manifest"]["component_versions"]["tool_hub"]="0.13.0"
            else:
                r["payloads"].pop("scripts/GameToolUnifiedPanel.py")
                r["manifest"]["files"]=[x for x in r["manifest"]["files"] if x["path"]!="scripts/GameToolUnifiedPanel.py"]
            with self.assertRaises(ValueError): api.check_manifest(r["manifest"],r["payloads"])

    def test_local_paths_refuse_relative_roots(self):
        for path in ("relative",Path(self.base.anchor)):
            with self.assertRaises(ValueError): api.local_path(path)

    def test_strict_version_pointer_tags(self):
        for tag in (".","..","hub-0.12.0-123456abcdef.","hub-0.12.0.-123456abcdef",
                    "hub-0.12.0-pre..1-123456abcdef","hub-0.12.0-pre_-123456abcdef",
                    "hub-0.12.0-/pre-123456abcdef","hub-0.12.0-123456ABCDEF",
                    "hub-0.12.0-123456abcdef/", "hub-0.12.0-123456abcdef\\"):
            with self.subTest(tag=tag),self.assertRaises(ValueError): api.version_tag(tag)
        for tag in ("hub-0.12.0-123456abcdef","hub-0.13.0-preview.2-123456abcdef"):
            self.assertEqual(api.version_tag(tag),tag)

    def test_component_version_rejects_dot_and_invalid_suffixes(self):
        for revision in (".","..","0.12.0.","0.12.0-","0.12.0-preview.","0.12.0-preview..1","0.12.0-pre_view","0.12.0-../next"):
            with self.subTest(revision=revision),self.assertRaises(ValueError):
                release=package(revision)
                api.check_manifest(release["manifest"],release["payloads"])

    def test_bootstrap_changes_transactionally_and_rolls_back(self):
        first=self.install(); bootstrap=self.root/"Start-UnifiedTools.pyw"
        initial_raw=bootstrap.read_bytes()
        self.assertEqual(initial_raw,self.release["payloads"][api.BOOTSTRAP])
        second_release=package("0.12.1","bootstrap-second")
        second=self.upgrade(second_release)
        self.assertEqual(bootstrap.read_bytes(),second_release["payloads"][api.BOOTSTRAP])
        self.assertEqual(second["bootstrap_sha256"],api.digest(bootstrap.read_bytes()))
        self.assertEqual((Path(second["recovery"])/"Start-UnifiedTools.pyw.backup").read_bytes(),initial_raw)
        rolled=api.rollback_previous(self.root,expected_state_sha256=api.digest(api.read_bytes(self.root/"install.json")),names=[])
        self.assertEqual(bootstrap.read_bytes(),initial_raw)
        self.assertEqual(rolled["bootstrap_sha256"],first["bootstrap_sha256"])

    def test_bootstrap_tamper_blocks_without_replacing_user_edit(self):
        self.install(); pointer=(self.root/"install.json").read_bytes()
        bootstrap=self.root/"Start-UnifiedTools.pyw"; bootstrap.write_bytes(b"concurrent launcher owner edit")
        before=api.studio_hashes(self.studio)
        with self.assertRaises(ValueError): self.upgrade()
        self.assertEqual(bootstrap.read_bytes(),b"concurrent launcher owner edit")
        self.assertEqual(api.studio_hashes(self.studio),before)
        self.assertEqual((self.root/"install.json").read_bytes(),pointer)
        self.assertFalse((self.root/"update.lock").exists())
        self.assertFalse((self.studio/api.SOURCE_LOCK).exists())

    def test_bootstrap_write_failure_recovers_studio_and_owned_launcher(self):
        first=self.install(); pointer=(self.root/"install.json").read_bytes()
        bootstrap=self.root/"Start-UnifiedTools.pyw"; original_bootstrap=bootstrap.read_bytes()
        original=api._replace_file
        def fail_bootstrap(path,raw):
            if Path(path)==bootstrap: raise OSError("synthetic launcher-write interruption")
            return original(path,raw)
        with mock.patch.object(api,"_replace_file",side_effect=fail_bootstrap),self.assertRaises(OSError): self.upgrade()
        self.assertEqual(api.studio_hashes(self.studio),first["studio_hashes"])
        self.assertEqual(bootstrap.read_bytes(),original_bootstrap)
        self.assertEqual((self.root/"install.json").read_bytes(),pointer)
        self.assertFalse((self.root/"update.lock").exists())
        self.assertFalse((self.studio/api.SOURCE_LOCK).exists())

    def test_bootstrap_after_replace_failure_conditional_recovery(self):
        first=self.install(); pointer=(self.root/"install.json").read_bytes()
        bootstrap=self.root/"Start-UnifiedTools.pyw"; original_bootstrap=bootstrap.read_bytes()
        original=api._replace_file
        def fail_after_owned_replace(path,raw):
            result=original(path,raw)
            if Path(path)==bootstrap and raw!=original_bootstrap:
                raise OSError("synthetic post-replacement readback failure")
            return result
        with mock.patch.object(api,"_replace_file",side_effect=fail_after_owned_replace),self.assertRaises(OSError): self.upgrade()
        self.assertEqual(api.studio_hashes(self.studio),first["studio_hashes"])
        self.assertEqual(bootstrap.read_bytes(),original_bootstrap)
        self.assertEqual((self.root/"install.json").read_bytes(),pointer)
        self.assertFalse((self.root/"update.lock").exists())
        self.assertFalse((self.studio/api.SOURCE_LOCK).exists())

    def test_actual_bootstrap_refuses_unsafe_pointer_without_launch_or_ui(self):
        self.install()
        bootstrap_path=SCRIPTS/"Start-UnifiedTools.pyw"
        bootstrap_spec=importlib.util.spec_from_loader("offline_bootstrap_fixture",SourceFileLoader("offline_bootstrap_fixture",str(bootstrap_path)))
        bootstrap_module=importlib.util.module_from_spec(bootstrap_spec)
        bootstrap_spec.loader.exec_module(bootstrap_module)
        bootstrap_module.__file__=str(self.root/"Start-UnifiedTools.pyw")
        initial=json.loads((self.root/"install.json").read_bytes())
        for tag in (".","..","hub-0.12.0-123456abcdef.","hub-0.12.0-pre..1-123456abcdef"):
            (self.root/"install.json").write_bytes(json.dumps({**initial,"current":tag}).encode())
            with self.subTest(tag=tag),mock.patch.object(bootstrap_module.sys,"argv",[bootstrap_module.__file__]), \
                    mock.patch.object(bootstrap_module.subprocess,"Popen") as launch, \
                    mock.patch.object(bootstrap_module.tk,"Tk") as hidden_ui, \
                    mock.patch.object(bootstrap_module.messagebox,"showerror") as error:
                bootstrap_module.main()
                launch.assert_not_called()
                error.assert_called_once()
                self.assertIn("Invalid version pointer",str(error.call_args))
                hidden_ui.return_value.withdraw.assert_called_once()
                hidden_ui.return_value.destroy.assert_called_once()

    def test_final_inventory_change_preserves_concurrent_edit_and_locks(self):
        first=self.install(); pointer=(self.root/"install.json").read_bytes()
        bootstrap=self.root/"Start-UnifiedTools.pyw"; bootstrap_before=bootstrap.read_bytes()
        edited=self.studio/"AzeronOverlayStudio.ahk"; original=api._replace_file
        def edit_after_last_write(path,raw):
            result=original(path,raw)
            if Path(path)==bootstrap and raw!=bootstrap_before:
                edited.write_bytes(b"concurrent owner edit after all source replacements")
            return result
        with mock.patch.object(api,"_replace_file",side_effect=edit_after_last_write),self.assertRaises(ValueError): self.upgrade()
        self.assertEqual(edited.read_bytes(),b"concurrent owner edit after all source replacements")
        for name,digest in first["studio_hashes"].items():
            if name!=edited.name: self.assertEqual(api.digest((self.studio/name).read_bytes()),digest)
        self.assertEqual(bootstrap.read_bytes(),bootstrap_before)
        self.assertEqual((self.root/"install.json").read_bytes(),pointer)
        self.assertTrue((self.root/"update.lock").exists())
        self.assertTrue((self.studio/api.SOURCE_LOCK).exists())

    def test_final_pointer_change_preserves_concurrent_pointer_and_locks(self):
        first=self.install(); state_path=self.root/"install.json"; pointer=state_path.read_bytes()
        edited_pointer=json.dumps({**json.loads(pointer),"concurrent_owner_note":"preserve this newer edit"}).encode()
        bootstrap=self.root/"Start-UnifiedTools.pyw"; bootstrap_before=bootstrap.read_bytes()
        original=api._replace_file
        def edit_pointer_after_sources(path,raw):
            result=original(path,raw)
            if Path(path)==bootstrap and raw!=bootstrap_before: state_path.write_bytes(edited_pointer)
            return result
        with mock.patch.object(api,"_replace_file",side_effect=edit_pointer_after_sources),self.assertRaises(ValueError): self.upgrade()
        self.assertEqual(state_path.read_bytes(),edited_pointer)
        self.assertEqual(api.studio_hashes(self.studio),first["studio_hashes"])
        self.assertEqual(bootstrap.read_bytes(),bootstrap_before)
        self.assertTrue((self.root/"update.lock").exists())
        self.assertTrue((self.studio/api.SOURCE_LOCK).exists())

    def test_initial_folder_race_is_exclusive_and_preserves_other_owner(self):
        original=api.acquire_source_lease
        def raced_lease(directory,purpose):
            lease=original(directory,purpose)
            self.root.mkdir()
            (self.root/"other-owner.txt").write_bytes(b"created after initial preview")
            return lease
        with mock.patch.object(api,"acquire_source_lease",side_effect=raced_lease),self.assertRaises(FileExistsError): self.install()
        self.assertEqual((self.root/"other-owner.txt").read_bytes(),b"created after initial preview")
        self.assertEqual(api.studio_hashes(self.studio),self.originals)
        self.assertFalse((self.root/"update.lock").exists())
        self.assertFalse((self.studio/api.SOURCE_LOCK).exists())

    def test_shared_studio_lease_blocks_update_from_another_install_root(self):
        first=self.install(); second_root=self.base/"other-install"
        lease=api.acquire_source_lease(self.studio,"native-studio")
        try:
            with self.assertRaises(FileExistsError):
                api.apply_release(second_root,self.release,expected_state_sha256=None,
                    expected_studio=first["studio_hashes"],initial=self.initial,names=[])
            self.assertFalse(second_root.exists())
            self.assertEqual((self.studio/api.SOURCE_LOCK).read_bytes(),lease["raw"])
            self.assertEqual(api.studio_hashes(self.studio),first["studio_hashes"])
            with self.assertRaises(ValueError): api.launch_command(self.root)
        finally:
            api.release_source_lease(lease)
        self.assertFalse((self.studio/api.SOURCE_LOCK).exists())

    def test_changed_lease_marker_is_not_removed(self):
        lease=api.acquire_source_lease(self.studio,"native-studio")
        marker=self.studio/api.SOURCE_LOCK; marker.write_bytes(b"newer source owner marker")
        with self.assertRaises(ValueError): api.release_source_lease(lease)
        self.assertEqual(marker.read_bytes(),b"newer source owner marker")

    def test_native_start_acquires_shared_ownership_and_releases_on_exit(self):
        import GameToolUnifiedPanel as panel
        first=self.install(); second_root=self.base/"second-installed"
        api.apply_release(second_root,self.release,expected_state_sha256=None,
                          expected_studio=first["studio_hashes"],initial=self.initial,names=[])
        def engine(root):
            value=panel.NativeStudio.__new__(panel.NativeStudio)
            value.api=api; value.root=root; value.viewport=mock.Mock()
            value.viewport.winfo_id.return_value=501
            value.process=None; value.lease=None; value.child=0
            return value
        first_engine=engine(self.root); second_engine=engine(second_root)
        fake_process=mock.Mock(); fake_process.poll.return_value=None; fake_process.pid=987654
        with mock.patch.object(api,"assert_idle"),mock.patch.object(panel.subprocess,"Popen",return_value=fake_process) as launch:
            first_engine.start()
            self.assertEqual(api.load_json(self.studio/api.SOURCE_LOCK)["purpose"],"native-studio")
            self.assertEqual(launch.call_count,1)
            with self.assertRaises(FileExistsError): second_engine.start()
            self.assertEqual(launch.call_count,1)
            fake_process.poll.return_value=0
            self.assertFalse(first_engine.alive())
            self.assertFalse((self.studio/api.SOURCE_LOCK).exists())
            fake_process.poll.return_value=None
            second_engine.start()
            self.assertEqual(launch.call_count,2)
            fake_process.poll.return_value=0
            self.assertFalse(second_engine.alive())
            self.assertFalse((self.studio/api.SOURCE_LOCK).exists())

    def test_native_start_launch_failure_releases_only_its_lease(self):
        import GameToolUnifiedPanel as panel
        self.install()
        engine=panel.NativeStudio.__new__(panel.NativeStudio)
        engine.api=api; engine.root=self.root; engine.viewport=mock.Mock()
        engine.viewport.winfo_id.return_value=501
        engine.process=None; engine.lease=None; engine.child=0
        with mock.patch.object(api,"assert_idle"),mock.patch.object(panel.subprocess,"Popen",side_effect=OSError("mock launch rejected")),self.assertRaises(OSError):
            engine.start()
        self.assertIsNone(engine.lease)
        self.assertFalse((self.studio/api.SOURCE_LOCK).exists())

class Wiring(unittest.TestCase):
    def test_bridge_has_no_input_transport_and_standalone_is_optional(self):
        raw=(SCRIPTS.parent/"examples/game-input/StudioHubBridge.ahk").read_text()
        for prohibited in ("SendInput(","SendEvent(","Run(","Socket", "GI_Start"):
            self.assertNotIn(prohibited,raw)
        for required in ("--hub-parent","--hub-owner","GetWindowThreadProcessId","GetParent","CheckOwner","SetTimer(this.Timer, 0)"):
            self.assertIn(required,raw)
        self.assertNotIn("A_Pid",raw)
        self.assertIn('DllCall("GetCurrentProcessId", "uint")',raw)

    def test_panel_update_is_explicit_and_stops_only_owned_child(self):
        raw=(SCRIPTS/"GameToolUnifiedPanel.py").read_text()
        self.assertIn('PostMessageW(self.child, 0x10',raw)
        for prohibited in (".terminate(",".kill(","SendInput", "shell=True", "os.system"):
            self.assertNotIn(prohibited,raw)
        self.assertIn("messagebox.askyesno",raw)
        self.assertIn("expected_state_sha256",raw)
        self.assertIn("threading.Thread",raw)

    def test_editor_uses_logical_dpi_but_overlay_remains_pixel_based(self):
        raw=(SCRIPTS.parent/"examples/game-input/StudioPictureModule.ahk").read_text()
        self.assertIn('Gui(owner " +DPIScale", "Studio 2 | Advanced Picture Buttons")',raw)
        self.assertIn('Gui("-Caption +ToolWindow +AlwaysOnTop -DPIScale',raw)

    def test_hidden_tk_ui_and_callbacks(self):
        import tkinter as tk
        from tkinter import ttk
        import GameToolUnifiedPanel as panel
        root=tk.Tk(); root.withdraw(); self.addCleanup(root.destroy)
        tabs=ttk.Notebook(root); tabs.pack()
        state={"component_versions":{"tool_hub":"0.12.0","overlay_studio":"2.2.0-unified.1"}}
        class Engine:
            def __init__(self,*args): self.stopped=False
            def alive(self): return False
            def discover(self): return 0
            def stop(self): self.stopped=True
            def reveal_requested(self): return False
        with mock.patch.object(panel,"NativeStudio",Engine),mock.patch.object(api,"read_install",return_value=state):
            view=panel.UnifiedPanel(root,tabs,Path(tempfile.gettempdir())/"unified-fixture",api,tk.StringVar())
            self.assertEqual([tabs.tab(t,"text") for t in tabs.tabs()],["Studio","Updates"])
            view.archive.set("relative"); view.expected.set("bad"); view.inspect()
            self.assertIsNone(view.preview)
            self.assertIn("SHA-256",view.details.get("1.0","end"))
            view.updating=True; self.assertFalse(view.close()); view.updating=False
            self.assertTrue(view.close()); self.assertTrue(view.engine.stopped)

if __name__=="__main__": unittest.main(verbosity=2)
