"""Reviewed controls orchestration; existing keybind and overlay owners write.

Preview is read-only. Prepare stores private immutable records. Each actual
game/overlay operation requires a separate trusted local callback; JSON never
grants authority. Native-profile application remains with native software.
"""
from __future__ import annotations
import copy,os
from pathlib import Path
import GameToolControlsPlanner as planner
import GameToolKeymapDocument as maps
import GameToolKeymapBuilder as builder
import GameToolOverlay as overlay
from game_keybind_ops.authoring import planner_bridge
from game_keybind_ops import effective
from game_keybind_ops.deps import read_json, object_hash

VERSION = "0.1.0"
MARKER = "controls-reviewed-plan"


def default_profiles_root():
    return Path(os.environ.get("APPDATA", "")) / "Azeron Software/Storage/DevicesStorage" if os.name == "nt" else None


def _keys(w, source, vocabulary):
    result = {key: key for key in vocabulary}
    for alias in w["extensions"].get("key_aliases", []):
        overlay.fields(alias, "display native evidence source_revision")
        overlay.require(bool(alias["evidence"]) and alias["source_revision"] == source["revision"], "Key alias needs current source evidence")
        overlay.require(alias["native"] in vocabulary and alias["display"] not in result, "Unknown or duplicate key alias")
        result[alias["display"]] = alias["native"]
    return result


def binding_preview(w, document, service):
    """Translate stable planner identities through the existing exact bridge."""
    report = planner.preview(w, document); planner.check_sources(w, service)
    changed = [r for r in report["rows"] if r["changed"]]
    overlay.require(not any(r["blocked"] for r in report["rows"]), "Resolve blocked routes before binding preview")
    if not changed: return {"status": "NO_CHANGES", "items_request": [], "gameplay_verified": False}
    overlay.require(len(w["sources"]) == 1, "Choose one exact registered binding source")
    source = w["sources"][0]; actions = {a["id"]: a for a in w["actions"]}
    fields = {planner.action_source_id(source, f): f for f in source["snapshot"]["action_fields"]}
    crosswalk = []; assignments = []; targets = {}
    if source["kind"] == "instance":
        rec = effective.instance(service, source["id"]); values, _ = effective.read_values(service, rec)
        active, _ = effective.resolved(values)
        native = {(r["target_id"] + ":" + r["field_id"], r["context"]): r for r in active}
    for row in changed:
        overlay.require(row["id"] in fields, "Planner action lacks an exact native field link")
        field = fields[row["id"]]
        if source["kind"] == "target":
            target_id = source["id"]; record = service.target(target_id)
            spec_field = next(f for f in record["spec"]["fields"] if f["id"] == field["id"])
            # Native parser group names can contain punctuation (bindset:0).
            # A stable bridge token preserves that identity without guessing a
            # gameplay meaning or changing the native parser's collision group.
            semantic = {"action": field["id"], "context": builder.stable("source-context-", field["context"]), "slot": "primary"}
            targets[(field["id"], semantic["context"], "primary")] = (target_id, field["id"])
        else:
            r = native[(field["id"], field["context"])]; record = service.target(r["target_id"])
            spec_field = next(f for f in record["spec"]["fields"] if f["id"] == r["field_id"])
            semantic = {k: r[k] for k in ("action", "context", "slot")}
        crosswalk.append({"source_id": row["id"], "source_action": actions[row["id"]]["label"],
                          **semantic, "keys": _keys(w, source, spec_field["keys"])})
        assignments.append({"source_id": row["id"], "label": actions[row["id"]]["label"], "target_key": row["to_key"]})
    translated = planner_bridge({"assignments": assignments}, crosswalk)
    if translated["unresolved"]:
        return {"status": "UNRESOLVED_ACTIONS", "items_request": [], **translated}
    if source["kind"] == "instance":
        state = effective.inspect_instance(service, source["id"])
        result = effective.intent_preview(service, source["id"], translated["intents"], state["revision"])
    else:
        patches = {}
        for intent in translated["intents"]:
            target, fid = targets[(intent["action"], intent["context"], intent["slot"])]
            patches.setdefault(target, {})[fid] = intent["key"]
        requests = [{"target_id": target, "target_revision": service.target(target)["spec_sha256"], "changes": values}
                    for target, values in sorted(patches.items())]
        result = {**service.preview(requests), "items_request": requests,
                  "scope_note": "Exact registered file/rows only; undeclared override precedence remains unverified"}
    return {**result, "bridge": translated, "gameplay_verified": False}


def _native(keymap, profiles_root):
    result = planner.native_status(keymap, profiles_root) if profiles_root is not None else []
    return result, bool(result) and all(r["state"] == "match" for r in result)


class Workflow:
    def __init__(self, library, service, profiles_root=None):
        self.library, self.service, self.profiles_root = library, service, profiles_root
        self.root = overlay.no_links(library.root / "controls-planning" / "reviewed-plans")

    def review(self, w, document, keymap):
        game = binding_preview(w, document, self.service)
        candidate = planner.overlay_candidate(w, document)
        builder.package([candidate], [keymap])
        native, matched = _native(keymap, self.profiles_root)
        data = {"kind": "controls_change_review", "schema_version": 1, "game_id": w["game_id"],
            "workbook": copy.deepcopy(w), "document_sha256": maps.fingerprint(document),
            "candidate": candidate, "keymap": copy.deepcopy(keymap), "game": game,
            "native_files": native, "native_match": matched, "gameplay_verified": False}
        overlay.require(len(maps.encoded(data)) <= overlay.MAX_JSON, "Review exceeds 1 MiB; narrow the action scope")
        return {**data, "review_id": builder.stable("review-", maps.fingerprint(data)), "review_sha256": maps.fingerprint(data)}

    def _check_document(self, record):
        current = self.library.current(record["game_id"])
        valid = {record["document_sha256"], maps.fingerprint(record["candidate"])}
        stripped = copy.deepcopy(current); stripped["guidance"] = [g for g in stripped["guidance"] if g["id"] not in {MARKER, "controls-unapplied-proposal"}]
        expected = copy.deepcopy(record["candidate"]); expected["guidance"] = [g for g in expected["guidance"] if g["id"] not in {MARKER, "controls-unapplied-proposal"}]
        compiled = self._compiled_candidate(record, bool(record["game"].get("items_request")))
        compiled["guidance"] = [g for g in compiled["guidance"] if g["id"] not in {MARKER, "controls-unapplied-proposal"}]
        overlay.require(maps.fingerprint(current) in valid or stripped == expected or stripped == compiled, "Saved map changed after controls review")
        overlay.require(self.library.keymaps().get(record["keymap"]["id"]) == record["keymap"], "Native source contract changed after controls review")

    def _check_native(self, record):
        rows, matched = _native(record["keymap"], self.profiles_root)
        overlay.require(matched and rows == record["native_files"], "Native profile files are missing, ambiguous or changed; reconcile without weakening byte guards")

    def prepare(self, review, expected_sha256, *, authorize):
        body = {k: v for k, v in review.items() if k not in {"review_id", "review_sha256"}}
        overlay.require(maps.fingerprint(body) == expected_sha256 == review["review_sha256"], "Controls review changed")
        overlay.require(review["review_id"] == builder.stable("review-", expected_sha256), "Review identity differs")
        overlay.require(callable(authorize) and authorize(copy.deepcopy(review)) is True, "Separate local review is required before preparing")
        self._check_document(review); planner.check_sources(review["workbook"], self.service)
        source_document = self.library.current(review["game_id"])
        overlay.require(maps.fingerprint(source_document) == review["document_sha256"], "Prepare from the reviewed source draft before saving a different candidate")
        regenerated = self.review(review["workbook"], source_document, review["keymap"])
        overlay.require(regenerated["review_sha256"] == expected_sha256, "Controls review dependencies changed; regenerate the exact review")
        overlay.require(review["game"]["status"] in {"NO_CHANGES", "PREVIEW_NOT_INSTALLED"}, "Resolve native action/key translation before preparing")
        # Preparation is private staging, and may retain a native-drift warning.
        # Apply and publication separately require every exact native file.
        game = review["game"]
        plan = self.service.prepare(game["items_request"], game["preview_sha256"], plan_id=review["review_id"]) if game["items_request"] else None
        result = {"review": copy.deepcopy(review), "game_plan": plan, "plan_id": review["review_id"]}
        self.root.mkdir(parents=True, exist_ok=True); path = overlay.no_links(self.root / (result["plan_id"] + ".json"))
        if path.exists():
            previous = self.load(result["plan_id"])
            overlay.require(previous == result, "Prepared controls plan already has different data")
        else: builder.write_new(path, result)
        return result

    def load(self, identity):
        overlay.token(identity); record = planner.decode(overlay.read(overlay.no_links(self.root / (identity + ".json"))))
        review = record["review"]; body = {k: v for k, v in review.items() if k not in {"review_id", "review_sha256"}}
        overlay.require(record["plan_id"] == identity == builder.stable("review-", maps.fingerprint(body)) and
                        maps.fingerprint(body) == review["review_sha256"], "Prepared review integrity differs")
        overlay.require(bool(review["game"].get("items_request")) == bool(record["game_plan"]), "Prepared game transaction was removed or added outside review")
        if record["game_plan"]:
            actual = self.service.plan(record["game_plan"]["plan_id"])
            overlay.require(actual["plan_sha256"] == record["game_plan"]["plan_sha256"] and actual["plan_id"] == identity and
                            actual["preview_sha256"] == review["game"]["preview_sha256"] and actual["items"] == review["game"]["items"], "Prepared game plan differs")
        return record

    def apply_game(self, identity, *, authorize):
        record = self.load(identity); review = record["review"]
        self._check_document(review); self._check_native(review)
        overlay.require(record["game_plan"] is not None, "No game changes in this plan")
        plan = record["game_plan"]
        # Existing owner checks process state, before hashes, linked changes,
        # scoped dependencies, backups, journal integrity and readback.
        return self.service.apply_local(plan["plan_id"], plan["plan_sha256"], authorize=authorize)

    def rollback_game(self, identity, *, authorize, selective=False):
        record = self.load(identity); plan = record["game_plan"]
        overlay.require(plan is not None, "No game transaction to roll back")
        registry, _ = self.library.store.load()
        group_id = builder.stable("builder-", record["review"]["candidate"]["id"])
        selected = registry["preferences"]["selections"].get(record["review"]["game_id"], {})
        overlay.require(not any(g["id"] == group_id for g in registry["manifest"]["groups"]) or selected.get("context") == "rollback-pending",
                        "Suspend this game's published overlay separately before game rollback")
        view = self.service.rollback_preview(plan["plan_id"], selective=True) if selective else self.service.exact_rollback_preview(plan["plan_id"])
        overlay.require(callable(authorize) and authorize(copy.deepcopy(view)) is True, "Rollback requires its own local review")
        undo = self.service.prepare_rollback(plan["plan_id"], view["preview_sha256"], selective=selective)
        return self.service.apply_local(undo["plan_id"], undo["plan_sha256"], authorize=lambda actual: authorize(actual) is True)

    def suspend_overlay(self, identity, *, authorize):
        record = self.load(identity); value, revision = self.library.store.load(); game = record["review"]["game_id"]
        current = value["preferences"]["selections"].get(game, {"layer":"Unknown","context":"gameplay","view":"Combined"})
        request = {"game_id":game,"layer":current["layer"],"context":"rollback-pending","view":current["view"]}
        overlay.require(callable(authorize) and authorize({"before":copy.deepcopy(current),"after":request}) is True,
                        "Overlay suspension requires its own local review")
        # Existing missing-context behavior hides this game's map without
        # changing hold ownership, other games, source assets or native inputs.
        return self.library.store.update("selection", request, revision)

    def original_overlay_candidate(self, identity):
        record = self.load(identity); self._check_native(record["review"])
        if record["game_plan"]:
            state = self.service.reconcile(record["game_plan"]["plan_id"])
            overlay.require(all(f["state"] == "BEFORE" for f in state["files"]), "Exact original game state is required; reconcile later edits before restoring old map labels")
        review = record["review"]; current = self.library.current(review["game_id"])
        if maps.fingerprint(current) == review["document_sha256"]: return current
        path = overlay.no_links(self.library.root / "history" / review["game_id"] / (review["document_sha256"] + ".json"))
        original = maps.load(path)
        overlay.require(maps.fingerprint(original) == review["document_sha256"], "Original map history differs")
        return original

    def publication_candidate(self, identity):
        record = self.load(identity); review = record["review"]
        self._check_document(review); self._check_native(review)
        if record["game_plan"]:
            state = self.service.reconcile(record["game_plan"]["plan_id"])
            overlay.require(all(f["state"] == "AFTER" for f in state["files"]), "Game bindings must match the applied plan before overlay publication")
            overlay.require(self.service.status(record["game_plan"]["plan_id"])["status"] == "APPLIED_FILES_RUNTIME_UNVERIFIED", "Game operation is not completely verified")
        else: planner.check_sources(review["workbook"], self.service)
        candidate = self._compiled_candidate(review, bool(record["game_plan"]))
        candidate["guidance"] = [g for g in candidate["guidance"] if g["id"] not in {MARKER, "controls-unapplied-proposal"}]
        candidate["guidance"].append({"id": MARKER, "text": "Publication needs the exact reviewed native/game state",
                                      "evidence": "reviewed file transaction; gameplay unverified", "source": identity})
        return maps.validate(candidate)

    @staticmethod
    def _compiled_candidate(review, game_changed):
        candidate = copy.deepcopy(review["candidate"])
        for mapping in candidate["maps"]:
            for cell in mapping["cells"]:
                if cell["source"].startswith("Planning preview only"):
                    cell["source"] = "Reviewed game-file transaction; gameplay unverified" if game_changed else "Reviewed display plan; native/game inputs unchanged"
                    cell["evidence"] = "saved_config" if game_changed else "user_label"
                    if cell["action"] == "Pending binding move": cell.update(action="No reviewed binding", display_action="No binding")
        return candidate

    def check_publication(self, document):
        markers = [g for g in document["guidance"] if g["id"] == MARKER]
        if not markers: return
        overlay.require(len(markers) == 1, "Duplicate controls publication marker")
        expected = self.publication_candidate(markers[0]["source"])
        overlay.require(expected == document, "Candidate map changed since the reviewed game plan")


def discover(service, game_id, roots):
    """Known adapter discovery; candidates never become an effective owner."""
    from game_keybind_ops.discovery import discover_local
    return discover_local(game_id, roots)
