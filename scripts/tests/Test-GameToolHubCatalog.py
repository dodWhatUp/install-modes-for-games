"""Isolated Hub/catalog integration contracts; run with Python -B.

Native Tk widgets belong to withdrawn test roots. Providers, launches, clipboard
and private-registry actions are mocked. No OS focus, game input or app launch.
Passing these fixtures is not live desktop/game or resource-cost acceptance.
"""
from contextlib import ExitStack
import hashlib
import importlib.util
import inspect as python_inspect
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

# Also protect a direct test invocation from writing authored-module caches.
sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
EXAMPLE = SCRIPTS.parent / "examples/game-tool-hub/catalog.example.json"


def load_source(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hub = load_source("hub_catalog_integration_contracts", "Game-Tool-Hub.py")
bridge = load_source("hub_catalog_bridge_contracts", "GameToolCatalogBridge.py")
panel_module = load_source("hub_catalog_panel_contracts", "GameToolCatalogPanel.py")


def fixture_fg(scope, game, *args, **kwargs):
    return {"schema_version": 1, "status": "NOT_APPLICABLE" if scope == "process-idle" else "PASS",
            "can_compare": True, "scope": scope, "game_id": game, "execution": "none",
            "reasons": ["Synthetic policy receipt only, not runtime evidence"], "source_revisions": {}}


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="hub-catalog-contracts-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.path = self.directory / "catalog.example.json"
        self.raw = EXAMPLE.read_bytes()
        self.path.write_bytes(self.raw)
        self.data_dir = self.directory / "private-profile"
        self.data_dir.mkdir()
        self.registry = self.data_dir / "tools.json"
        self.registry_bytes = b'{"fixture":"never read or migrated by catalog"}'
        self.registry.write_bytes(self.registry_bytes)
        self.safety = ExitStack()
        self.addCleanup(self.safety.close)
        self.forbidden = {}
        self.fg_spy = self.safety.enter_context(mock.patch.object(bridge, "_run_fg_preflight", side_effect=fixture_fg))
        for name in ("process_names", "read_afterburner", "read_rtss", "version_of",
                     "configuration", "import_report", "register_tool", "exclusive_json"):
            self.forbidden[name] = self.safety.enter_context(mock.patch.object(
                hub, name, side_effect=AssertionError(f"Forbidden external action: {name}")))
        self.forbidden["startfile"] = self.safety.enter_context(mock.patch.object(
            hub.os, "startfile", create=True, side_effect=AssertionError("Forbidden app launch")))
        for name in ("run", "Popen"):
            self.forbidden[name] = self.safety.enter_context(mock.patch.object(
                hub.subprocess, name, side_effect=AssertionError("Forbidden child process")))
        self.addCleanup(self.assert_no_external_calls)

    def assert_no_external_calls(self):
        for name, spy in self.forbidden.items():
            self.assertEqual(spy.call_count, 0, name)
        self.assertEqual(self.registry.read_bytes(), self.registry_bytes)

    def change_catalog(self):
        value = json.loads(self.path.read_bytes())
        value["components"][0]["name"] += " fixture revision"
        self.path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def assert_unmeasured_plan(self, value):
        self.assertEqual(value["execution"], "none")
        self.assertFalse(value["metrics_calculated"])
        self.assertTrue(all(metric is None for metric in value["measured_metrics"].values()))
        for case in value["cases"]:
            self.assertTrue(all(metric is None for metric in case["measured_metrics"].values()))
            self.assertEqual(case["runs"], [])


class CLIContracts(Fixtures):
    def setUp(self):
        super().setUp()
        for name in ("load_tools", "inspect", "gui", "read_form_file"):
            self.forbidden[name] = self.safety.enter_context(mock.patch.object(
                hub, name, side_effect=AssertionError(f"Catalog must not call {name}")))
        self.safety.enter_context(mock.patch.object(hub, "new_catalog_service",
            side_effect=lambda path: bridge.CatalogService(path)))

    def call_catalog(self, arguments, expected_exit=0):
        before = {str(path.relative_to(self.directory)): path.read_bytes()
                  for path in self.directory.rglob("*") if path.is_file()}
        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            result = hub.main(["--data-dir", str(self.data_dir), "--catalog-file", str(self.path),
                               "catalog", *arguments])
        self.assertEqual(result, expected_exit, output.getvalue())
        after = {str(path.relative_to(self.directory)): path.read_bytes()
                 for path in self.directory.rglob("*") if path.is_file()}
        self.assertEqual(after, before, "Catalog CLI must not create or rewrite private files")
        return json.loads(output.getvalue())

    def test_status_does_not_read_registry_providers_or_processes(self):
        result = self.call_catalog(["status"])
        self.assertEqual(result["execution"], "none")
        self.assertEqual(result["revision"], hashlib.sha256(self.raw).hexdigest())
        self.assertEqual(result["counts"]["components"], len(json.loads(self.raw)["components"]))

    def test_list_filters_use_recorded_catalog_not_live_inventory(self):
        result = self.call_catalog(["list", "--search", "RHI", "--sort", "name"])
        self.assertEqual([node["id"] for node in result["nodes"]], ["rhi"])
        self.assertEqual(result["execution"], "none")

    def test_show_retains_inert_actions_and_portable_provenance(self):
        result = self.call_catalog(["show", "rhi"])
        self.assertEqual(result["id"], "rhi")
        self.assertTrue(result["catalog_source"]["planning_only"])
        self.assertEqual(result["catalog_source"]["locator"], self.path.name)
        self.assertNotIn(str(self.directory), json.dumps(result))
        self.assertTrue(all(action["execution"] == "declaration-only"
                            for action in result["declared_actions"]))

    def test_plan_valid_2x2_never_executes_or_measures(self):
        result = self.call_catalog(["plan-overhead", "--scope", "in-game", "--game", "cyberpunk-2077",
                                   "--factor", "cp-renodx-hdr", "--factor", "cp-ultra-pt21"])
        self.assertEqual(result["status"], "prepared-not-authorized")
        self.assertEqual(len(result["cases"]), 4)
        self.assert_unmeasured_plan(result)

    def test_highest_preset_remains_blocked(self):
        result = self.call_catalog(["plan-overhead", "--scope", "in-game", "--game", "cyberpunk-2077",
                                   "--factor", "cp-ultra-highest"], expected_exit=3)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["cases"], [])
        self.assert_unmeasured_plan(result)

    def test_unknown_record_is_structured_failure_without_external_calls(self):
        result = self.call_catalog(["show", "not-a-record"], expected_exit=2)
        self.assertFalse(result["valid"])
        self.assertEqual(result["execution"], "none")
        self.assertIn("Unknown", result["error"])

    def test_bad_catalog_fails_before_private_registry_or_providers(self):
        self.path.write_text('{"bad":', encoding="utf-8")
        result = self.call_catalog(["status"], expected_exit=2)
        self.assertFalse(result["valid"])
        self.assertEqual(result["execution"], "none")

    def test_optional_module_allowlist_cannot_select_arbitrary_code(self):
        with self.assertRaises(ValueError):
            hub.load_catalog_module("../../arbitrary-command")

    def test_optional_bridge_syntax_failure_is_json_not_a_private_route(self):
        with mock.patch.object(hub, "new_catalog_service", side_effect=SyntaxError("synthetic optional bridge")):
            result = self.call_catalog(["status"], expected_exit=2)
        self.assertFalse(result["valid"])
        self.assertEqual(result["execution"], "none")
        self.assertIn("synthetic optional bridge", result["error"])

    def test_explicit_fg_check_and_plan_block_return_machine_failure_code(self):
        self.fg_spy.side_effect = lambda scope, game, *a, **kw: {
            "schema_version": 1, "status": "BLOCKED", "can_compare": False,
            "scope": scope, "game_id": game, "execution": "none", "reasons": ["Dynamic MFG unverified"]}
        result = self.call_catalog(["fg-preflight", "--scope", "in-game", "--game", "cyberpunk-2077"], 3)
        self.assertEqual(result["status"], "BLOCKED")
        result = self.call_catalog(["plan-overhead", "--scope", "in-game", "--game", "cyberpunk-2077",
                                   "--factor", "cp-renodx-hdr"], 3)
        self.assertFalse(result["comparison_ready"])
        self.assertEqual(result["cases"], [])

    def test_catalog_browse_does_not_probe_fg(self):
        for arguments in (["status"], ["list"], ["show", "rhi"]):
            self.call_catalog(arguments)
        self.fg_spy.assert_not_called()

    def test_fg_target_arguments_are_not_launches_or_output_private_paths(self):
        result = self.call_catalog(["fg-preflight", "--scope", "in-game", "--game", "cyberpunk-2077",
                                   "--executable", "fixture-renderer", "--native-settings", "fixture-config"])
        self.fg_spy.assert_called_once_with("in-game", "cyberpunk-2077", Path("fixture-renderer"), Path("fixture-config"))
        self.assertNotIn("fixture-renderer", json.dumps(result))


class NativeTkFixtures(Fixtures):
    def setUp(self):
        super().setUp()
        import tkinter as tk
        from tkinter import ttk
        self.tk, self.ttk = tk, ttk
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Native Tk unavailable; widget acceptance not established: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.clipboard = []
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_clear",
                                                   side_effect=self.clipboard.clear))
        self.safety.enter_context(mock.patch.object(self.root, "clipboard_append",
                                                   side_effect=self.clipboard.append))

    def button(self, parent, text):
        return next(widget for widget in descendants(parent)
                    if isinstance(widget, self.ttk.Button) and widget.cget("text") == text)

    def choose(self, panel, variable, identifier, choices):
        variable.set(next(label for label, value in choices.items() if value == identifier))

    def choose_game_and_scope(self, panel):
        panel.scope.set("in-game")
        self.choose(panel, panel.plan_game, "cyberpunk-2077", panel.game_ids)
        panel.plan_combos["scope"].event_generate("<<ComboboxSelected>>", when="now")
        self.assertIn("cp-renodx-hdr", panel.factor_ids.values())

    def prepare(self, panel, factor_a="rhi", factor_b=None):
        self.choose(panel, panel.factor_a, factor_a, panel.factor_ids)
        if factor_b:
            self.choose(panel, panel.factor_b, factor_b, panel.factor_ids)
        self.button(panel.parent, "Prepare plan (no execution)").invoke()

    def select_record(self, panel, identifier):
        panel.tree.selection_set(identifier)
        panel.tree.event_generate("<<TreeviewSelect>>", when="now")
        self.assertEqual(panel.last_detail["id"], identifier)


class PanelContracts(NativeTkFixtures):
    def setUp(self):
        super().setUp()
        self.parent = self.ttk.Frame(self.root)
        self.parent.pack(fill="both", expand=True)
        self.status = self.tk.StringVar(master=self.root)
        self.panel = panel_module.CatalogPanel(
            self.parent, lambda: bridge.CatalogService(self.path), self.status)

    def test_defaults_read_only_null_metrics_no_automatic_action(self):
        self.assertEqual(self.root.state(), "withdrawn")
        self.assertEqual(self.panel.scope.get(), "process-idle")
        self.assertEqual(self.panel.factor_a.get(), "None")
        self.assertEqual(self.panel.factor_b.get(), "None")
        self.assertIsNone(self.panel.last_plan)
        self.assertEqual(self.panel.detail_text.cget("state"), "disabled")
        self.assertEqual(self.panel.plan_text.cget("state"), "disabled")
        self.assertGreater(len(self.panel.tree.get_children()), 0)
        self.assertEqual(self.clipboard, [])

    def test_search_apply_button_and_clear_filters_use_native_callbacks(self):
        self.panel.filters["search"].set("RHI")
        self.button(self.parent, "Apply").invoke()
        self.assertEqual(self.panel.tree.get_children(), ("rhi",))
        self.select_record(self.panel, "rhi")
        self.button(self.parent, "Clear filters").invoke()
        self.assertGreater(len(self.panel.tree.get_children()), 1)
        self.assertIsNone(self.panel.last_detail)
        self.assertEqual(self.panel.filters["search"].get(), "")

    def test_native_filter_event_updates_game_specific_rows(self):
        self.panel.filters["kind"].set("feature")
        self.choose(self.panel, self.panel.filters["game"], "cyberpunk-2077", self.panel.game_ids)
        self.panel.combos["game"].event_generate("<<ComboboxSelected>>", when="now")
        self.assertTrue(self.panel.tree.get_children())
        self.assertTrue(all(identifier.startswith("cp-") for identifier in self.panel.tree.get_children()))

    def test_selection_detail_and_copy_are_inert_portable_data(self):
        self.select_record(self.panel, "rhi")
        self.assertIn("relationships", self.panel.last_detail)
        self.button(self.parent, "Copy record details").invoke()
        self.assertEqual(len(self.clipboard), 1)
        copied = json.loads(self.clipboard[0])
        self.assertEqual(copied["id"], "rhi")
        self.assertNotIn(str(self.directory), self.clipboard[0])
        self.assertTrue(all(action["execution"] == "declaration-only"
                            for action in copied["declared_actions"]))

    def test_idle_plan_button_and_copy_preserve_unmeasured_preview(self):
        self.prepare(self.panel)
        self.assertEqual(self.panel.last_plan["status"], "prepared-not-authorized")
        self.assertEqual(len(self.panel.last_plan["cases"]), 2)
        self.assert_unmeasured_plan(self.panel.last_plan)
        self.button(self.parent, "Copy plan").invoke()
        self.assertEqual(json.loads(self.clipboard[0]), self.panel.last_plan)

    def test_valid_2x2_widget_plan_keeps_shared_hosts_in_every_case(self):
        self.choose_game_and_scope(self.panel)
        self.prepare(self.panel, "cp-renodx-hdr", "cp-ultra-pt21")
        value = self.panel.last_plan
        self.assertEqual(value["status"], "prepared-not-authorized")
        self.assertEqual(len(value["cases"]), 4)
        needed = {"native-cyberpunk", "reshade", "cet", "red4ext", "archivexl", "redscript", "audiopoolfix"}
        for case in value["cases"]:
            self.assertTrue(needed <= set(case["always_on"]))
        self.assert_unmeasured_plan(value)

    def test_blocked_plan_is_visible_without_execution(self):
        self.choose_game_and_scope(self.panel)
        self.prepare(self.panel, "cp-ultra-highest")
        self.assertEqual(self.panel.last_plan["status"], "blocked")
        self.assertEqual(self.panel.last_plan["cases"], [])
        self.assertIn("blocked", self.panel.plan_text.get("1.0", "end"))
        self.assert_unmeasured_plan(self.panel.last_plan)

    def test_invalid_factor_selection_refuses_plan_without_invalidating_catalog(self):
        self.button(self.parent, "Prepare plan (no execution)").invoke()
        self.assertIsNone(self.panel.last_plan)
        self.assertGreater(len(self.panel.tree.get_children()), 0)
        self.select_record(self.panel, "rhi")
        self.assertIn("Plan refused", self.panel.plan_text.get("1.0", "end"))

    def test_factor_change_invalidates_previous_plan(self):
        self.prepare(self.panel)
        self.assertIsNotNone(self.panel.last_plan)
        self.panel.factor_a.set("None")
        self.panel.plan_combos["a"].event_generate("<<ComboboxSelected>>", when="now")
        self.assertIsNone(self.panel.last_plan)

    def test_source_drift_refuses_plan_and_clears_stale_records_until_reload(self):
        self.select_record(self.panel, "rhi")
        self.prepare(self.panel)
        previous = self.panel.service.revision
        self.change_catalog()
        self.button(self.parent, "Prepare plan (no execution)").invoke()
        self.assertIsNone(self.panel.last_plan)
        self.assertIsNone(self.panel.last_detail)
        self.assertEqual(self.panel.tree.get_children(), ())
        self.assertIn("reload", self.panel.source.get().lower())
        self.button(self.parent, "Reload catalog").invoke()
        self.assertNotEqual(self.panel.service.revision, previous)
        self.assertGreater(len(self.panel.tree.get_children()), 0)
        self.assertEqual(self.panel.factor_a.get(), "None")
        self.assertIsNone(self.panel.last_plan)

    def test_copy_after_source_drift_refuses_stale_data_without_touching_clipboard(self):
        self.select_record(self.panel, "rhi")
        self.change_catalog()
        self.button(self.parent, "Copy record details").invoke()
        self.assertEqual(self.clipboard, [])
        self.assertIsNone(self.panel.last_detail)
        self.assertEqual(self.panel.tree.get_children(), ())

    def test_invalid_reload_can_recover_only_after_valid_explicit_reload(self):
        self.path.write_text('{"broken":', encoding="utf-8")
        self.button(self.parent, "Reload catalog").invoke()
        self.assertEqual(self.panel.tree.get_children(), ())
        self.assertIsNone(self.panel.last_detail)
        self.assertIsNone(self.panel.last_plan)
        self.path.write_bytes(self.raw)
        self.assertEqual(self.panel.tree.get_children(), ())
        self.button(self.parent, "Reload catalog").invoke()
        self.assertGreater(len(self.panel.tree.get_children()), 0)

    def test_explicit_fg_button_blocks_without_preparing_a_plan(self):
        self.choose_game_and_scope(self.panel)
        self.fg_spy.side_effect = lambda scope, game, *a, **kw: {
            "schema_version": 1, "status": "BLOCKED", "can_compare": False,
            "scope": scope, "game_id": game, "execution": "none", "reasons": ["Unverified effective FG"]}
        self.button(self.parent, "Check FG (read only)").invoke()
        self.assertIsNone(self.panel.last_plan)
        self.assertIn("BLOCKED", self.panel.fg_status.get())
        self.assertIn("Unverified", self.panel.plan_text.get("1.0", "end"))
        self.assertEqual(self.clipboard, [])

    def test_copy_rechecks_and_refuses_newly_blocked_pass(self):
        self.choose_game_and_scope(self.panel)
        self.prepare(self.panel, "cp-renodx-hdr")
        self.assertTrue(self.panel.last_plan["comparison_ready"])
        self.fg_spy.side_effect = lambda scope, game, *a, **kw: {
            "schema_version": 1, "status": "BLOCKED", "can_compare": False,
            "scope": scope, "game_id": game, "execution": "none", "reasons": ["Changed effective FG"]}
        self.button(self.parent, "Copy plan").invoke()
        self.assertEqual(self.clipboard, [])
        self.assertFalse(self.panel.last_plan["comparison_ready"])
        self.assertIn("BLOCKED", self.panel.fg_status.get())
        self.assertEqual(self.fg_spy.call_count, 2)

    def test_path_edit_invalidates_receipt_without_inspecting_or_persisting(self):
        self.choose_game_and_scope(self.panel)
        self.prepare(self.panel, "cp-renodx-hdr")
        self.fg_spy.reset_mock()
        self.panel.executable.set("private-renderer-path")
        self.assertIsNone(self.panel.last_plan)
        self.assertIn("not checked", self.panel.fg_status.get())
        self.fg_spy.assert_not_called()
        self.button(self.parent, "Copy plan").invoke()
        self.assertEqual(self.clipboard, [])

    def test_unannounced_factor_change_refuses_copy_of_old_plan(self):
        self.prepare(self.panel)
        self.panel.factor_a.set("None")  # No synthetic selection event.
        self.button(self.parent, "Copy plan").invoke()
        self.assertIsNone(self.panel.last_plan)
        self.assertEqual(self.clipboard, [])


class FullGUIContracts(NativeTkFixtures):
    def test_overlay_controls_are_wired_without_forwarding_tool_shortcuts(self):
        self.build_gui()
        values = python_inspect.getclosurevars(self.handler).nonlocals
        panel = values["overlay_panel"]
        self.assertIsNotNone(panel)
        self.addCleanup(panel.close)
        self.focus = self.root.nametowidget(self.tabs.tabs()[8])
        self.tabs.select(self.tabs.tabs()[8])
        self.assertEqual(self.send_callback("o"), "break")
        self.assertFalse(panel.value["preferences"]["enabled"])
        self.focus = panel.selectors["game"]
        self.assertIsNone(self.send_callback("c"))  # Native text Copy retained.

    def test_readiness_child_is_wired_with_additive_overlay_tab(self):
        import tkinter as tk
        self.build_gui()
        self.assertEqual(len(self.tabs.tabs()), 12)
        self.assertEqual([self.tabs.tab(tab, "text") for tab in self.tabs.tabs()][-3:], ["Mods", "AI & automation", "System control"])
        self.assertEqual([self.tabs.tab(tab, "text") for tab in self.tabs.tabs()][:8],
                         ["Tools", "Sensors", "RTSS", "Reports", "How to use", "Catalog", "Comparison", "Sessions"])
        self.assertIsNotNone(self.session_panel.readiness_factory)
        original = tk.Toplevel
        def hidden(*args, **kwargs):
            window = original(*args, **kwargs); window.withdraw(); return window
        with mock.patch.object(self.session_panel.tk, "Toplevel", side_effect=hidden):
            child = self.session_panel.open_readiness()
        self.assertIsNotNone(child)
        self.assertIsNone(child.source)
        self.assertIsNone(child.report)
        self.assertTrue(self.session_panel.close())
        self.assertTrue(child.closed)

    def build_gui(self, missing_panel=False):
        fake_tool = {"id": "fixture-interface", "name": "Never launched fixture", "path": "",
                     "process": "fixture.exe", "open_allowed": True,
                     "installed": False, "running": False, "version": None}
        reading = {"schema": 1, "helper_version": hub.VERSION, "observed_utc": "fixture-only",
                   "mode": "learning", "capture_started_by_helper": False,
                   "tools": [fake_tool], "afterburner_configuration": {},
                   "afterburner": {"state": "fixture", "rows": [], "reason": "Synthetic read; no collection"},
                   "rtss": {"state": "fixture", "applications": []}}
        self.inspection = self.safety.enter_context(mock.patch.object(hub, "inspect", return_value=reading))
        self.safety.enter_context(mock.patch.object(hub, "load_tools", return_value=[fake_tool]))
        self.safety.enter_context(mock.patch.object(sys, "path", [str(SCRIPTS), *sys.path]))
        self.safety.enter_context(mock.patch.object(self.tk, "Tk", return_value=self.root))
        self.safety.enter_context(mock.patch.object(self.root, "mainloop", return_value=None))
        self.safety.enter_context(mock.patch.object(self.root, "deiconify", return_value=None))  # Keep this synthetic root withdrawn.
        original_bind = self.root.bind

        def capture_binding(sequence=None, func=None, add=None):
            if sequence == "<Control-KeyPress>" and func is not None:
                self.handler = func
            return original_bind(sequence, func, add)

        self.safety.enter_context(mock.patch.object(self.root, "bind", side_effect=capture_binding))
        if missing_panel:
            self.safety.enter_context(mock.patch.object(hub, "load_catalog_module", side_effect=ImportError("fixture missing module")))
        hub.gui(self.data_dir, catalog_path=self.path)
        values = python_inspect.getclosurevars(self.handler).nonlocals
        self.tabs, self.catalog_tab = values["tabs"], values["catalog_tab"]
        self.panel, self.shortcuts = values["catalog_panel"], values["shortcuts"]
        self.comparison_tab, self.comparison_panel = values["comparison_tab"], values["comparison_panel"]
        self.session_tab, self.session_panel = values["session_tab"], values["session_panel"]
        self.focus = self.root.nametowidget(self.tabs.tabs()[0])
        self.safety.enter_context(mock.patch.object(self.root, "focus_get", side_effect=lambda: self.focus))
        self.grab = self.safety.enter_context(mock.patch.object(self.root, "grab_current", return_value=None))

    def send_callback(self, key):
        # Explicit Windows-key semantics in this source-level fixture, including on Linux.
        decoder = hub.shortcut_key
        with mock.patch.object(hub, "shortcut_key", side_effect=lambda code, symbol, windows: decoder(code, symbol, True)):
            return self.handler(SimpleNamespace(keycode=ord(key.upper()), keysym="Hebrew_layout_label"))

    def test_hidden_full_gui_has_original_five_tabs_plus_catalog_and_refresh_off(self):
        self.build_gui()
        names = [self.tabs.tab(tab, "text") for tab in self.tabs.tabs()]
        self.assertEqual(names, ["Tools", "Sensors", "RTSS", "Reports", "How to use", "Catalog", "Comparison", "Sessions", "Overlays", "Mods", "AI & automation", "System control"])
        self.assertEqual(self.root.state(), "withdrawn")
        auto_boxes = [widget for widget in descendants(self.root)
                      if isinstance(widget, self.ttk.Checkbutton) and "Auto refresh" in widget.cget("text")]
        self.assertEqual(len(auto_boxes), 2)
        self.assertTrue(all(not widget.instate(["selected"]) for widget in auto_boxes))
        self.assertEqual(self.inspection.call_count, 1)

    def test_actual_bound_ctrl_1_to_6_preserve_tab_order_under_other_layout(self):
        self.build_gui()
        for index, tab in enumerate(self.tabs.tabs()[:8], 1):
            self.assertEqual(self.send_callback(str(index)), "break")
            self.assertEqual(self.tabs.select(), tab)

    def test_catalog_blocks_remembered_original_action_shortcuts(self):
        self.build_gui()
        self.send_callback("6")
        for key in ("o", "a", "s", "i", "e"):
            spy = mock.Mock(wraps=self.shortcuts[key])
            self.shortcuts[key] = spy
            self.assertEqual(self.send_callback(key), "break")
            spy.assert_not_called()
            self.assertEqual(self.tabs.select(), str(self.catalog_tab))

    def test_catalog_reload_copy_route_to_actual_panel_not_provider_refresh(self):
        self.build_gui()
        self.send_callback("6")
        with mock.patch.object(self.panel, "reload", wraps=self.panel.reload) as reload_spy:
            self.assertEqual(self.send_callback("r"), "break")
            reload_spy.assert_called_once()
        self.select_record(self.panel, "rhi")
        self.assertEqual(self.send_callback("c"), "break")
        self.assertEqual(json.loads(self.clipboard[0])["id"], "rhi")
        self.assertEqual(self.inspection.call_count, 1)

    def test_normal_entry_and_text_ctrl_a_c_are_not_intercepted(self):
        self.build_gui()
        self.send_callback("6")
        for focused in (self.panel.search_entry, self.panel.detail_text):
            self.focus = focused
            for key in ("a", "c"):
                self.assertIsNone(self.send_callback(key))
        self.assertEqual(self.clipboard, [])

    def test_missing_focus_modal_and_other_toplevel_keep_input_ownership(self):
        self.build_gui()
        original_tab = self.tabs.select()
        self.focus = None
        self.assertIsNone(self.send_callback("6"))
        self.focus = self.catalog_tab
        self.grab.return_value = object()
        self.assertIsNone(self.send_callback("6"))
        self.grab.return_value = None
        popup = self.tk.Toplevel(self.root)
        popup.withdraw()
        self.addCleanup(popup.destroy)
        self.focus = self.ttk.Entry(popup)
        self.assertIsNone(self.send_callback("6"))
        self.assertEqual(self.tabs.select(), original_tab)

    def test_optional_panel_import_failure_does_not_break_original_tabs(self):
        self.build_gui(missing_panel=True)
        self.assertIsNone(self.panel)
        self.assertEqual(len(self.tabs.tabs()), 9)
        self.send_callback("6")
        self.assertEqual(self.send_callback("o"), "break")
        self.send_callback("1")
        self.assertEqual(self.send_callback("r"), "break")
        self.assertEqual(self.inspection.call_count, 2)
        self.assertEqual(self.tabs.select(), self.tabs.tabs()[0])

    def test_bad_catalog_data_does_not_break_original_tabs(self):
        self.path.write_text('{"invalid":', encoding="utf-8")
        self.build_gui()
        self.assertIsNotNone(self.panel)
        self.assertEqual(self.panel.tree.get_children(), ())
        self.assertIn("unavailable", self.panel.source.get().lower())
        self.send_callback("3")
        self.assertEqual(self.tabs.select(), self.tabs.tabs()[2])
        self.assertEqual(self.send_callback("r"), "break")
        self.assertEqual(self.inspection.call_count, 2)

    def test_comparison_blocks_remembered_original_action_shortcuts(self):
        self.build_gui()
        self.send_callback("7")
        for key in ("o", "a", "s", "i", "e"):
            spy = mock.Mock(wraps=self.shortcuts[key])
            self.shortcuts[key] = spy
            self.assertEqual(self.send_callback(key), "break")
            spy.assert_not_called()
            self.assertEqual(self.tabs.select(), str(self.comparison_tab))
        self.assertEqual(self.inspection.call_count, 1)

    def test_comparison_reload_and_copy_do_not_refresh_live_providers(self):
        self.build_gui()
        self.send_callback("7")
        self.assertIsNotNone(self.comparison_panel)
        for key, method in (("r", "reload"), ("c", "copy_summary")):
            with mock.patch.object(self.comparison_panel, method) as spy:
                self.assertEqual(self.send_callback(key), "break")
                spy.assert_called_once()
        self.assertEqual(self.inspection.call_count, 1)

    def test_comparison_missing_module_remains_contained(self):
        self.build_gui(missing_panel=True)
        self.assertIsNone(self.comparison_panel)
        self.send_callback("7")
        for key in ("r", "c", "o", "a", "s", "i", "e"):
            self.assertEqual(self.send_callback(key), "break")
        self.send_callback("1")
        self.assertEqual(self.send_callback("r"), "break")
        self.assertEqual(self.inspection.call_count, 2)

    def test_sessions_blocks_remembered_original_shortcuts_and_reads_no_providers(self):
        self.build_gui()
        self.send_callback("8")
        self.assertIsNotNone(self.session_panel)
        self.assertIsNotNone(self.session_panel.coordinator)
        self.assertEqual(self.session_panel.current_status["state"], "idle")
        for key in ("o", "a", "s", "i", "e"):
            spy = mock.Mock(wraps=self.shortcuts[key])
            self.shortcuts[key] = spy
            self.assertEqual(self.send_callback(key), "break")
            spy.assert_not_called()
            self.assertEqual(self.tabs.select(), str(self.session_tab))
        for key, method in (("r", "reload"), ("c", "copy_summary")):
            with mock.patch.object(self.session_panel, method) as spy:
                self.assertEqual(self.send_callback(key), "break")
                spy.assert_called_once()
        self.assertEqual(self.inspection.call_count, 1)

    def test_sessions_missing_module_is_contained(self):
        self.build_gui(missing_panel=True)
        self.assertIsNone(self.session_panel)
        self.send_callback("8")
        for key in ("r", "c", "o", "a", "s", "i", "e"):
            self.assertEqual(self.send_callback(key), "break")
        self.send_callback("1")
        self.assertEqual(self.send_callback("r"), "break")
        self.assertEqual(self.inspection.call_count, 2)

    def test_sessions_keep_normal_text_ownership(self):
        self.build_gui()
        self.send_callback("8")
        for focused in (self.session_panel.phase_entry, self.session_panel.summary_text):
            self.focus = focused
            for key in ("a", "c"):
                self.assertIsNone(self.send_callback(key))
        self.assertEqual(self.clipboard, [])

    def test_hub_close_cancels_only_owned_session_and_keeps_evidence(self):
        from tkinter import filedialog
        self.build_gui()
        self.send_callback("8")
        journal_path = self.directory / "owned-close-fixture.jsonl"
        with mock.patch.object(filedialog, "asksaveasfilename", return_value=str(journal_path)):
            self.assertTrue(self.session_panel.new_session())
        self.assertEqual(self.session_panel.coordinator.status()["state"], "active")
        with mock.patch.object(self.root, "destroy") as destroyed:
            self.root.tk.call(self.root.protocol("WM_DELETE_WINDOW"))
            destroyed.assert_called_once()
        self.assertEqual(self.session_panel.coordinator.status()["state"], "cancelled")
        evidence = hub.load_catalog_module("GameToolJournal").inspect_journal(journal_path)
        self.assertTrue(evidence["valid"])
        self.assertTrue(evidence["clean_end"])
        self.assertEqual(evidence["verified_records"][-1]["kind"], "session_cancelled")
        self.assertEqual(self.inspection.call_count, 1)


if __name__ == "__main__":
    unittest.main()
