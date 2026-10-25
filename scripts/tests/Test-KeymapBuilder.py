"""Map authoring/exchange and guest Tk checks; no native writes or game input."""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolKeymapBuilder as builder
import GameToolKeymapDocument as maps
import GameToolKeymapButtons as buttons
import GameToolOverlay as overlay

spec=importlib.util.spec_from_file_location("doc_fixtures",Path(__file__).with_name("Test-KeymapDocument.py"))
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)


class Sources(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.library=builder.SourceLibrary(self.root/"data")
        manifest,source=fixtures.fixtures.fixture(self.root);manifest["keymaps"][0]["revision"]="f"*64;source.write_bytes(overlay.encode(manifest))
        self.library.store.import_manifest(source,"absent");self.doc=fixtures.document();self.keymap=manifest["keymaps"][0]
        self.saved=self.library.save_source(self.doc,self.keymap,"absent")

    def test_package_multiple_games_and_single_map_merge(self):
        another=builder.new_game(self.doc,"New game","another-game")
        value=builder.package([self.doc,another],[self.keymap]);path=self.root/"maps.txt";builder.write_new(path,value)
        self.assertEqual(builder.read_package(path,self.library.keymaps()),value)
        single=copy.deepcopy(self.doc);single["maps"]=single["maps"][:1];single["maps"][0]["cells"][0]["display_action"]="Changed"
        merged=builder.merge_maps(self.doc,single)
        self.assertEqual(len(merged["maps"]),2);self.assertEqual(merged["maps"][1],self.doc["maps"][1])
        self.assertEqual(merged["maps"][0]["cells"][0]["display_action"],"Changed")

    def test_new_game_clears_actions_but_preserves_outputs_geometry(self):
        change=builder.new_game(self.doc,"Unknown game")
        self.assertEqual(maps.output_matrix(change),maps.output_matrix(self.doc))
        self.assertEqual(change["buttons"],self.doc["buttons"])
        self.assertFalse(any(c["action"] for m in change["maps"] for c in m["cells"]))
        self.assertNotEqual(change["game_id"],self.doc["game_id"])

    def test_context_links_copy_keys_without_source_mutation(self):
        change=copy.deepcopy(self.doc);index=builder.add_context(change,"BASIC","inventory")
        self.assertEqual(index,2);self.assertEqual(len(self.doc["maps"]),2)
        self.assertEqual([c["output"] for c in change["maps"][2]["cells"]],[c["output"] for c in self.doc["maps"][0]["cells"]])
        self.assertFalse(any(c["action"] for c in change["maps"][2]["cells"]))
        with self.assertRaises(ValueError):builder.add_context(change,"BASIC","inventory")

    def test_separate_key_label_changes_no_emitted_key(self):
        change=copy.deepcopy(self.doc);change["maps"][0]["cells"][0]["display_key"]="Friendly key"
        maps.validate(change);self.assertEqual(maps.output_matrix(change),maps.output_matrix(self.doc))
        builder.write_new(self.root/"single.json",change)
        self.assertEqual(builder.read_package(self.root/"single.json",self.library.keymaps())["documents"],[change])

    def test_changed_emitted_output_is_refused(self):
        change=copy.deepcopy(self.doc);change["maps"][0]["cells"][0]["output"]="Other"
        with self.assertRaises(ValueError):self.library.save_source(change,self.keymap,self.saved)
        self.assertEqual(self.library.current("game"),self.doc)

    def test_save_and_publish_are_separate_and_history_survives(self):
        before,sha=self.library.store.load();change=copy.deepcopy(self.doc);change["maps"][0]["cells"][0]["display_action"]="New action"
        self.library.save_source(change,self.keymap,self.saved)
        self.assertEqual(self.library.store.load()[1],sha)
        self.assertTrue((self.library.root/"history/game"/(self.saved+".json")).exists())
        receipt=self.library.publish(change,self.keymap,sha,selected_map=1)
        after,_=self.library.store.load();self.assertFalse(receipt["native_changes"])
        self.assertEqual(after["preferences"]["overrides"]["game"],receipt["group_id"])
        self.assertEqual(after["preferences"]["selections"]["game"]["layer"],"MENUS")
        self.assertEqual(after["manifest"]["keymaps"],before["manifest"]["keymaps"])
        self.assertTrue(set(a["id"] for a in before["manifest"]["assets"])<=set(a["id"] for a in after["manifest"]["assets"]))
        for a in before["manifest"]["assets"]:self.assertTrue((self.library.store.directory/a["path"]).exists())

    def test_new_game_publishes_no_invented_executable(self):
        change=builder.new_game(self.doc,"New game","new-game")
        self.library.save_source(change,self.keymap,"absent");_,sha=self.library.store.load()
        self.library.publish(change,self.keymap,sha);value,_=self.library.store.load()
        self.assertFalse(any(a["game_id"]=="new-game" for a in value["manifest"]["associations"]))

    def test_chat_selected_scope_and_sources_are_explicit(self):
        path=self.root/"bindings.txt";path.write_text("Action: Jump\nKey: K\n",encoding="utf-8")
        packet=builder.ai_request(self.doc,[1],[path]);raw=maps.encoded(packet)
        self.assertEqual(overlay.decode(raw),packet)
        self.assertEqual(len(packet["selected_document"]["maps"]),1)
        self.assertNotIn(str(self.root),raw.decode())
        self.assertEqual(packet["selected_sources"][0]["lines"],["Action: Jump","Key: K"])
        self.assertEqual(builder.ai_request(self.doc,[0])["selected_sources"],[])

    def proposal(self):
        packet=builder.ai_request(self.doc,[0]);value=packet["response_schema"]
        value["changes"][0].update(action="Jump",display_action="Jump",source="Selected fixture reference")
        return value

    def test_chat_labels_are_reviewed_drafts_and_outputs_are_immutable(self):
        proposal=self.proposal();prior=copy.deepcopy(self.doc)
        changes=builder.proposal_changes(self.doc,proposal);self.assertEqual(len(changes),1)
        self.assertEqual(builder.adopt_proposal(self.doc,proposal,[]),self.doc)
        change=builder.adopt_proposal(self.doc,proposal,[0]);self.assertEqual(self.doc,prior)
        self.assertEqual(change["maps"][0]["cells"][0]["evidence"],"ai_suggestion")
        self.assertEqual(maps.output_matrix(change),maps.output_matrix(self.doc))
        self.assertEqual(self.library.current("game"),self.doc)
        proposal["changes"][0]["output"]="Other"
        with self.assertRaises(ValueError):builder.proposal_changes(self.doc,proposal)

    def test_stale_duplicate_and_command_proposals_refused(self):
        value=self.proposal();value["base_document_sha256"]="0"*64
        with self.assertRaises(ValueError):builder.proposal_changes(self.doc,value)
        value=self.proposal();value["changes"]*=2
        with self.assertRaises(ValueError):builder.proposal_changes(self.doc,value)
        value=self.proposal();value["changes"][0]["command"]="run something"
        with self.assertRaises(ValueError):builder.proposal_changes(self.doc,value)

    def test_package_malformed_collision_and_export_overwrite_refused(self):
        with self.assertRaises(ValueError):builder.package([self.doc,self.doc],[self.keymap])
        value=builder.package([self.doc],[self.keymap]);value["command"]="not accepted"
        with self.assertRaises(ValueError):builder.validate_package(value)
        builder.write_new(self.root/"out.json",self.doc)
        with self.assertRaises(FileExistsError):builder.write_new(self.root/"out.json",self.doc)

    def native(self):
        value={"metaData":{"schemeName":"azeron-profile-v1","device":8},"version":1,"id":"12345678-1234-1234-1234-123456789012","name":"Fixture BASIC", "inputs":[]}
        for bid in sorted(overlay.R8_POSITIONS):value["inputs"].append({"id":bid,"types":["1","11","11"],"metaValues":["0","0","0"],"keyValues":["KeyK","0","0","0"],"isHold":False,"isTurbo":False})
        return value

    def test_native_read_does_not_use_game_labels_or_write_profiles(self):
        value=self.native();path=self.root/"native.json";path.write_text(json.dumps(value));before=path.read_bytes()
        doc,keymap=builder.native_profiles([path],self.doc,"Native game")
        self.assertEqual(path.read_bytes(),before);self.assertFalse(any(c["action"] for c in doc["maps"][0]["cells"]))
        self.assertTrue(all(c["output"]=="K" for c in doc["maps"][0]["cells"]))
        self.assertEqual(keymap["layers"][0]["profile_sha256"],overlay.sha(before))

    def test_native_unsupported_gestures_types_and_external_layers_refused(self):
        for change in [lambda x:x["inputs"][0].update(types=["1","1","11"]),lambda x:x["inputs"][0].update(types=["999","11","11"]),lambda x:x["inputs"][0].update(keyValues="malformed"),lambda x:x["inputs"][0].update(types=["24","11","11"],isToggleOnHold=True,layeringProfileId="missing")]:
            value=self.native();change(value);path=self.root/"native.json";path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):builder.native_profiles([path],self.doc,"Native game")

    def test_button_link_save_relay_foreign_and_unlink(self):
        link={"slot":2,"game_id":"game","group_id":"group-a","layer":"BASIC","context":"gameplay","view":"Combined"}
        buttons.save(self.library.store.directory,link,"absent")
        value,_=self.library.store.load();indexed=overlay.validate_store(value)
        result={"render":True,"game_id":"game","group_id":"group-a","display_target":"studio","foreground_exe":"Gameplay.exe"}
        data=buttons.relay_data(self.library.store,indexed,result,{"Schema":"1","ExpiresUnixMs":"1000","ExpiresUnix":"1"})
        self.assertEqual(data[2]["Active"],"1");self.assertEqual(data[2]["FixedGuide"],"1")
        data=buttons.relay_data(self.library.store,indexed,{**result,"game_id":"foreign"},{"Schema":"1"})
        self.assertEqual(data[2]["Active"],"0");self.assertEqual(data[2]["Linked"],"0")
        _,sha=buttons.read(self.library.store.directory)
        with self.assertRaises(ValueError):buttons.save(self.library.store.directory,link,"absent")
        buttons.save(self.library.store.directory,link,sha,True)
        self.assertFalse(buttons.read(self.library.store.directory)[0]["links"])

    def test_button_relay_integrates_saved_fade_and_disabled_game_guard(self):
        from GameToolOverlayTransition import save
        link={"slot":1,"game_id":"game","group_id":"group-a","layer":"BASIC","context":"gameplay","view":"Keys"}
        buttons.save(self.library.store.directory,link,"absent");save(self.library.store.directory,True,120,None)
        result={"render":True,"game_id":"game","group_id":"group-a","asset_id":"asset-keys","layer_state":"Selected","display_target":"studio","foreground_exe":"Gameplay.exe"}
        overlay.relay(self.library.store,result,self.library.store.directory,now=100)
        text=(self.library.store.directory/"overlay-selection-slot-1.ini").read_text()
        self.assertIn("FadeInMs = 120",text);self.assertIn("Linked = 1",text)
        overlay.relay(self.library.store,{"render":False},self.library.store.directory,now=101)
        text=(self.library.store.directory/"overlay-selection-slot-1.ini").read_text()
        self.assertIn("Active = 0",text);self.assertIn("Linked = 0",text)


class GuestEditor(unittest.TestCase):
    def setUp(self):
        Sources.setUp(self)
        import tkinter as tk
        from GameToolKeymapBuilderUI import Builder
        self.root_ui=tk.Tk();self.root_ui.withdraw();self.addCleanup(self.root_ui.destroy)
        self.panel=SimpleNamespace(parent=self.root_ui,store=self.library.store,selectors={"game":SimpleNamespace(selected_id="game")},reload_choices=lambda:None,tick=lambda **_:None)
        self.panel.value,self.panel.fingerprint=self.library.store.load()
        self.editor=Builder(self.panel);self.root_ui.update()

    def test_real_editor_canvas_fields_draft_save_and_context(self):
        self.assertTrue(self.editor.canvas.find_withtag("button"))
        self.editor.select_button(4);self.editor.fields["display_key"].set("Key label");self.editor.fields["display_action"].set("Jump");self.editor.set_cell()
        self.assertEqual(self.library.current("game"),self.doc)
        self.assertEqual(self.editor.output.get(),"K")
        self.editor.save();cell=next(c for c in self.library.current("game")["maps"][0]["cells"] if c["button_id"]==4)
        self.assertEqual(cell["display_key"],"Key label")
        index=builder.add_context(self.editor.document,"BASIC","inventory");self.editor.map_index=index;self.editor.refresh_maps()
        self.assertEqual(self.editor.map_choice.get(),"BASIC / inventory")
        self.assertEqual(maps.output_matrix(self.editor.document)[:29],maps.output_matrix(self.doc)[:29])

    def test_key_capture_and_special_picker_are_explicit_labels_only(self):
        self.editor.select_button(4);before=copy.deepcopy(self.editor.document)
        dialog=self.editor.capture_key();self.root_ui.update();dialog.pad.focus_force();self.root_ui.update()
        dialog.pad.event_generate("<KeyPress>",keysym="F12",state=4);self.root_ui.update()
        dialog.use();self.assertEqual(self.editor.fields["display_key"].get(),"Ctrl+F12")
        self.assertEqual(self.editor.document,before);self.assertEqual(self.editor.output.get(),"K")
        self.editor.key_choice.set("Numpad Enter");self.editor.set_cell()
        self.assertEqual(maps.output_matrix(self.editor.document),maps.output_matrix(before))
        self.assertEqual(self.library.current("game"),self.doc)
        dialog=self.editor.capture_key();self.root_ui.update();dialog.pad.focus_force();self.root_ui.update()
        dialog.pad.event_generate("<KeyPress>",keysym="q");self.root_ui.update()
        other=next(b["id"] for b in self.editor.document["buttons"] if b["id"]!=4)
        self.editor.select_button(other);original=self.editor.fields["display_key"].get();dialog.use()
        self.assertEqual(self.editor.fields["display_key"].get(),original)

    def test_real_editor_drag_is_opt_in_and_publish_uses_same_store(self):
        b=self.editor.document["buttons"][0];before=(b["x"],b["y"]);self.editor.selected_button=b["id"]
        self.editor.drag=(0,0,b["x"],b["y"]);self.editor.canvas_drag(SimpleNamespace(x=20,y=20));self.assertEqual((b["x"],b["y"]),before)
        self.editor.move.set(True);self.editor.canvas_drag(SimpleNamespace(x=20,y=20));self.assertNotEqual((b["x"],b["y"]),before)
        self.editor.fields["display_action"].set("Jump");self.editor.set_cell()
        _, fingerprint = self.library.store.load()
        with self.assertRaisesRegex(ValueError, "Save draft first"): self.editor.publish()
        self.assertEqual(self.library.store.load()[1], fingerprint)
        self.editor.save();self.editor.publish()
        value,_=self.library.store.load();self.assertTrue(value["preferences"]["overrides"]["game"].startswith("builder-"))

    def test_preview_text_fits_buttons_at_large_text_scaling(self):
        self.root_ui.tk.call("tk","scaling",2.0)
        self.editor.window.geometry("860x620");self.root_ui.update()
        self.editor.document["maps"][0]["cells"][0]["display_key"]="A very long key label to fit"
        self.editor.document["maps"][0]["cells"][0]["display_action"]="A very long action description to fit"
        self.editor.redraw();self.root_ui.update()
        for button in self.editor.document["buttons"]:
            items=self.editor.canvas.find_withtag(f'button-{button["id"]}')
            rectangle=next(i for i in items if self.editor.canvas.type(i)=="rectangle")
            x,y,right,bottom=self.editor.canvas.coords(rectangle)
            for item in items:
                if self.editor.canvas.type(item)=="text":
                    left,top,r,b=self.editor.canvas.bbox(item)
                    self.assertGreaterEqual(left,x-2);self.assertGreaterEqual(top,y-2)
                    self.assertLessEqual(r,right+2);self.assertLessEqual(b,bottom+2)


if __name__=="__main__":unittest.main()
