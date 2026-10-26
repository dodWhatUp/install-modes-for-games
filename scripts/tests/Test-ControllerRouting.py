import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import GameToolControllerRouting as api


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = api.Preferences(self.temp.name)

    def add(self, scope="global", value="", controller="local-physical", **options):
        row = api.preference("My controller", scope, value, controller, **options)
        self.store.put(row, self.store.load()[1])
        return row

    def test_open_and_resolution_are_inert(self):
        self.assertEqual(self.store.resolve()["state"], "none")
        self.assertFalse(self.store.root.exists())

    def test_precedence_and_no_driver_claim(self):
        self.add()
        self.add("genre", "rpg", "genre-controller")
        self.add("group", "living-room", "group-controller")
        game = self.add("game", "doom", "game-controller", route="rewasd-steam")
        found = self.store.resolve("doom", ["rpg"], ["living-room"])
        self.assertEqual(found["preference"]["id"], game["id"])
        self.assertEqual(found["effective_windows_priority"], "unverified")
        self.assertFalse(found["native_changes"])

    def test_equal_specificity_conflict_is_not_silently_chosen(self):
        self.add("group", "a")
        self.add("group", "b")
        self.assertEqual(self.store.resolve(groups=["a", "b"])["state"], "ambiguous")

    def test_auto_resolution_does_not_apply(self):
        row = self.add(automatic=True)
        self.assertEqual(self.store.resolve(automatic_only=True)["preference"], row)
        self.assertFalse(api.capabilities()["automatic_native_remap"])

    def test_slot_cannot_be_persistent_identity(self):
        for value in ("xinput-0", "slot1"):
            with self.assertRaises(ValueError):
                self.add(controller=value)

    def test_duplicate_scope_and_stale_save_refused(self):
        pin = self.store.load()[1]
        self.add()
        with self.assertRaises(ValueError):
            self.add()
        with self.assertRaises(ValueError):
            self.store.save(api.empty(), pin)

    def test_history_and_roundtrip_remove(self):
        row = self.add()
        value, pin = self.store.load()
        changed = copy.deepcopy(row)
        changed["route"] = "rewasd-steam"
        self.store.put(changed, pin)
        self.assertEqual(len(list((self.store.root / "history").glob("*.json"))), 1)
        self.store.remove(row["id"], self.store.load()[1])
        self.assertEqual(self.store.load()[0]["preferences"], [])

    def test_native_feeder_grouped_only_by_evidence(self):
        row = self.add()
        snapshot = {"devices": [{"id": "local-physical", "present": True},
                                {"id": "virtual", "present": True},
                                {"id": "similar", "present": True}],
                    "xinput": [{"index": 0, "present": True}, {"index": 1, "present": True}],
                    "relationships": [{"source_id": "local-physical", "target_id": "virtual", "status": "observed"},
                                      {"source_id": "local-physical", "target_id": "similar", "status": "inferred"}]}
        found = api.diagnose(snapshot, row)
        self.assertEqual({x["id"] for x in found["family"]}, {"local-physical", "virtual"})
        self.assertEqual(found["other_endpoints"][0]["id"], "similar")
        self.assertEqual(found["effective_priority"], "unverified")
        self.assertFalse(api.capabilities()["windows_device_disconnect"])

    def test_missing_controller_keeps_preference(self):
        row = self.add()
        self.assertEqual(api.diagnose({"devices": []}, row)["state"], "missing")
        self.assertEqual(self.store.load()[0]["preferences"][0], row)

    def test_stored_groups_drive_automatic_resolution_without_native_changes(self):
        row = self.add("genre", "Action", automatic=True)
        self.store.set_game_context("doom", ["Action"], ["Desk"], self.store.load()[1])
        self.assertEqual(self.store.resolve("doom", automatic_only=True)["preference"]["id"], row["id"])

    def test_acceptance_is_invalidated_by_backend_after_source_or_route_changes(self):
        row = self.add(evidence={"state": "user-reported", "note": "Works", "at": 1})
        changed = copy.deepcopy(row)
        changed["native_config_sha256"] = "a" * 64
        self.store.put(changed, self.store.load()[1])
        saved = self.store.load()[0]["preferences"][0]
        self.assertEqual(saved["evidence"]["state"], "unverified")


if __name__ == "__main__":
    unittest.main()
