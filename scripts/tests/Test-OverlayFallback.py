"""Other-app selection/relay and opt-in GUI contracts; no host input or game launch."""
import copy,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api
import GameToolOverlayFallback as fallback
spec=importlib.util.spec_from_file_location("overlay_fixture",Path(__file__).with_name("Test-GameToolOverlay.py"))
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)


class Routing(unittest.TestCase):
    def setUp(self):
        fixtures.CoreTests.setUp(self)
        self.value["preferences"]["display_target"]="studio"
        self.browser={"exe":r"C:\Apps\Browser.exe","pid":42,"at":10,"own":False}

    def choose(self,foreground=None,**kwargs):
        return api.choose(self.value,self.browser if foreground is None else foreground,now=10,fallback_group="group-b",**kwargs)

    def test_other_apps_get_explicit_fallback_and_games_keep_their_map(self):
        result=self.choose();self.assertTrue(result["render"]);self.assertEqual(result["group_id"],"group-b")
        self.assertEqual(result["selection_scope"],"fallback")
        result=self.choose(self.fg);self.assertEqual(result["group_id"],"group-a");self.assertEqual(result["selection_scope"],"association")
        self.value["preferences"]["overrides"]["game"]="group-a"
        self.assertEqual(self.choose()["group_id"],"group-b");self.assertFalse(self.choose()["manual_override"])
        self.assertTrue(self.choose(self.fg)["manual_override"])

    def test_own_app_supported_for_studio_only(self):
        own={**self.browser,"own":True}
        self.assertTrue(self.choose(own)["render"])
        self.value["preferences"]["display_target"]="hub"
        self.assertFalse(self.choose(own)["render"]);self.assertFalse(self.choose()["render"])

    def test_no_implicit_fallback_and_off_switches_still_work(self):
        self.assertFalse(api.choose(self.value,self.browser,now=10)["render"])
        self.value["preferences"]["enabled"]=False;self.assertFalse(self.choose()["render"])
        self.value["preferences"].update(enabled=True,display=False)
        self.assertFalse(self.choose()["render"]);self.assertEqual(self.choose()["group_id"],"group-b")

    def test_unavailable_stale_foreground_and_ambiguous_games_never_fall_back(self):
        self.assertFalse(api.choose(self.value,None,now=10,fallback_group="group-b")["render"])
        for at in (8,11):self.assertFalse(self.choose({**self.browser,"at":at})["render"])
        other=copy.deepcopy(self.value["manifest"]["associations"][0]);other.update(id="other",default_group="group-b")
        self.value["manifest"]["associations"].append(other)
        self.assertFalse(self.choose(self.fg)["render"]);self.assertIn("Ambiguous",self.choose(self.fg)["reason"])

    def test_native_unavailable_stale_and_foreign_still_refuse(self):
        for native in ({"available":False},{"at":8},{"at":10,"profile_id":"wrong","profile_sha256":"c"*64,"outputs_sha256":"a"*64}):
            self.assertFalse(self.choose(native=native)["render"])

    def test_layer_changes_exact_images_without_opening_a_picture(self):
        value=self.value;group=next(g for g in value["manifest"]["groups"] if g["id"]=="group-b")
        for old in list(value["manifest"]["assets"]):
            new={**old,"id":"menu-"+old["id"],"layer":"MENUS","profile_id":"installed-MENUS"}
            value["manifest"]["assets"].append(new);group["asset_ids"].append(new["id"])
        native=dict(at=10,state="Event-tracked",provider="fixture",available=True,profile_id="installed-BASIC",profile_sha256="c"*64,outputs_sha256="a"*64)
        basic=self.choose(native=native);native["profile_id"]="installed-MENUS";menus=self.choose(native=native)
        self.assertEqual(basic["asset_id"],"asset-combined");self.assertEqual(menus["asset_id"],"menu-asset-combined")
        self.assertEqual(menus["layer_state"],"Event-tracked")
        # Python only publishes content. The existing F24 Studio slot decides
        # visibility, so no synthetic trigger or layer key is introduced.
        self.assertNotIn("trigger",menus)

    def test_missing_group_or_exact_context_never_reuses_a_game_image(self):
        result=api.choose(self.value,self.browser,now=10,fallback_group="missing")
        self.assertFalse(result["render"])
        self.value["preferences"]["selections"]["game"]["context"]="missing"
        self.assertIsNone(self.choose()["asset_id"])

    def test_saved_fallback_relay_has_actual_foreground_and_same_image_guards(self):
        self.hash=self.store.write(self.value,self.hash)["sha256"]
        fallback.save(self.store,"group-b",None)
        result=api.checked_selection(self.store,self.value,self.browser,now=10)
        self.assertTrue(result["render"]);self.assertEqual(result["foreground_exe"],self.browser["exe"])
        api.relay(self.store,result,self.root/"relay",now=100)
        relay=(self.root/"relay/overlay-selection.ini").read_text()
        self.assertIn("Exe = "+self.browser["exe"],relay);self.assertIn("Active = 1",relay)
        self.assertIn("ExpiresUnixMs = 101000",relay)
        asset=next(a for a in self.value["manifest"]["assets"] if a["id"]==result["asset_id"])
        (self.store.directory/asset["path"]).write_bytes(b"drift")
        self.assertFalse(api.checked_selection(self.store,self.value,self.browser,now=10)["render"])

    def test_sidecar_save_retains_registry_and_previous_bytes_and_rejects_stale(self):
        before=self.store.path.read_bytes();value,raw=fallback.read(self.store.directory)
        self.assertIsNone(value["group_id"]);self.assertIsNone(raw)
        _,saved=fallback.save(self.store,"group-b",raw)
        self.assertEqual(self.store.path.read_bytes(),before)
        with self.assertRaises(ValueError):fallback.save(self.store,None,None)
        fallback.save(self.store,None,saved)
        self.assertEqual((self.store.directory/("overlay-fallback-before-"+api.sha(saved)+".json")).read_bytes(),saved)
        with self.assertRaises(ValueError):fallback.save(self.store,"missing",fallback.read(self.store.directory)[1])

    def test_invalid_sidecar_disables_only_fallback_and_no_commands_are_accepted(self):
        path=self.store.directory/"overlay-fallback.json"
        path.write_text(json.dumps(dict(schema_version=1,kind="overlay_fallback",group_id="group-b",command="anything")))
        self.assertFalse(api.checked_selection(self.store,self.value,self.browser,now=10)["render"])
        self.assertTrue(api.checked_selection(self.store,self.value,self.fg,now=10)["render"])


class Editor(unittest.TestCase):
    def setUp(self):
        Routing.setUp(self)
        import tkinter as tk
        self.root_ui=tk.Tk();self.root_ui.withdraw();self.addCleanup(self.root_ui.destroy)
        self.saved=mock.Mock();self.editor=fallback.FallbackEditor(self.root_ui,self.store,self.saved)
        self.root_ui.update()

    def test_search_and_cancel_make_no_changes(self):
        self.editor.group.variable.set("Fixture");self.root_ui.update()
        self.assertFalse((self.store.directory/"overlay-fallback.json").exists())
        self.editor.window.destroy();self.assertFalse(self.saved.called)

    def test_save_existing_choice_then_off_preserves_every_original_registry_byte(self):
        before=self.store.path.read_bytes();self.editor.group.select("group-b");self.editor.commit()
        self.assertEqual(fallback.read(self.store.directory)[0]["group_id"],"group-b");self.assertEqual(self.store.path.read_bytes(),before)
        self.assertTrue(self.saved.called)
        editor=fallback.FallbackEditor(self.root_ui,self.store);editor.group.select("__off__");editor.commit()
        self.assertIsNone(fallback.read(self.store.directory)[0]["group_id"])

    def test_uncommitted_search_cannot_save_old_choice(self):
        self.editor.group.variable.set("unmatched-query");self.editor.commit()
        self.assertTrue(self.editor.message.get());self.assertFalse(self.saved.called)
        self.assertFalse((self.store.directory/"overlay-fallback.json").exists())


if __name__=="__main__":unittest.main()
