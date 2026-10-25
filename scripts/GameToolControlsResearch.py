"""Evidence-bound action research exchange and unsupported-game checklists.

No API key, automatic game launch, capture, input logging or network execution.
The same stable actions and pinned sources serve external assisted research.
"""
from __future__ import annotations
import copy
from urllib.parse import urlparse
import GameToolControlsPlanner as p
import GameToolKeymapDocument as maps
import GameToolOverlay as overlay

VERSION = "0.1.0"
FIELDS = ("meaning", "activation", "categories", "urgency", "frequency", "needs_movement")


def request_packet(w, action_ids=None):
    p.validate(w); selected = set(action_ids) if action_ids is not None else {a["id"] for a in w["actions"]}
    overlay.require(selected <= {a["id"] for a in w["actions"]}, "Research request contains an unknown action")
    rows = []
    fields={p.action_source_id(source,f):f for source in w["sources"] for f in source["snapshot"]["action_fields"]}
    for a in w["actions"]:
        if a["id"] not in selected: continue
        missing = [name for name in FIELDS if a[name] in (None, "", [], "unknown")]
        rows.append({"action_id":a["id"],"native_label":fields.get(a["id"],{}).get("label",a["label"]),"display_label":a["label"],"source_context":a["context"],
            "saved_key":a["output"],"bundle_id":a["bundle_id"],"questions":missing,
            "decision":"Clarify action meaning, access demand and simultaneous-use requirements before placement"})
    return {"kind":"controls_action_research_request","schema_version":1,"game_id":w["game_id"],
        "workbook_sha256":maps.fingerprint(w),"source_revisions":[s["revision"] for s in w["sources"]],
        "actions":rows,"policy":p.POLICY,"constraints":{"row_order":list(p.ROW_ORDER),"protected_buttons":sorted(p.ANCHORS),
            "mouse_and_stick":"preserve","native_layer_is_game_context":False},
        "reply_contract":"controls_action_research_reply v1: game_id, workbook_sha256, source_revisions, actions [{action_id, annotations, citations, uncertainty}]",
        "instructions":"Research every selected command in its exact context. Cite each nontrivial interpretation. Keep frequency unknown without user/context evidence; distinguish select from immediate activation, press/hold/toggle and bundled actions. Do not return code, native output edits or apply authority."}


def adopt_reply(w, reply, document, *, replace_conflicts=False):
    p.preview(w,document);p.bounded_data(reply)
    overlay.fields(reply,"kind schema_version game_id workbook_sha256 source_revisions actions")
    overlay.require(reply["kind"]=="controls_action_research_reply" and reply["schema_version"]==1 and
                    reply["game_id"]==w["game_id"] and reply["workbook_sha256"]==maps.fingerprint(w) and
                    reply["source_revisions"]==[s["revision"] for s in w["sources"]],"Research response is stale or for another source/game")
    overlay.require(type(reply["actions"]) is list and len(reply["actions"])<=2048,"Research reply count limit")
    result=copy.deepcopy(w);actions={a["id"]:a for a in result["actions"]};seen=set();conflicts=[]
    for row in reply["actions"]:
        overlay.fields(row,"action_id annotations citations uncertainty")
        overlay.require(row["action_id"] in actions and row["action_id"] not in seen,"Unknown or duplicate researched action")
        seen.add(row["action_id"]);overlay.require(type(row["annotations"]) is dict and set(row["annotations"])<=set(FIELDS),"Research can only annotate semantics and demand")
        overlay.require(type(row["citations"]) is list and 1<=len(row["citations"])<=16,"Action annotations need citations or a labeled user report/inference")
        citations=[]
        for citation in row["citations"]:
            overlay.fields(citation,"kind locator claim checked_at")
            overlay.require(citation["kind"] in {"official_documentation","local_source","user_report","inference"},"Unknown evidence kind")
            for key in ("locator","claim","checked_at"):maps.text(citation[key],1000)
            if citation["kind"]=="official_documentation":
                url=urlparse(citation["locator"]);overlay.require(url.scheme in {"http","https"} and bool(url.netloc),"Official citation needs its source URL")
            citations.append(citation["kind"]+": "+citation["locator"]+" — "+citation["claim"])
        a=actions[row["action_id"]]
        for field,value in row["annotations"].items():
            prior=a[field]
            if prior not in (None,"",[],"unknown") and prior!=value:
                conflicts.append({"action_id":a["id"],"field":field,"before":prior,"proposed":value})
                if not replace_conflicts:continue
            a[field]=copy.deepcopy(value)
        a["evidence"]=list(dict.fromkeys(a["evidence"]+citations))[:32]
        result["extensions"].setdefault("action_research",{})[a["id"]]=copy.deepcopy(row)
    p.validate(result)
    return result,{"actions_annotated":len(seen),"conflicts":conflicts,"outputs_changed":False,"authorization_imported":False}


def manual_checklist(w,document):
    report=p.preview(w,document)
    return {"kind":"controls_manual_binding_checklist","schema_version":1,"game_id":w["game_id"],
        "workbook_sha256":maps.fingerprint(w),"status":"MANUAL_REVIEW_REQUIRED",
        "rows":[{"action_id":r["id"],"action":r["label"],"source_context":r["context"],"current":r["from_key"],
                 "proposed":r["to_key"],"warnings":r["blocked"]+r["warnings"],"verified_in_game":False}
                for r in report["rows"] if r["changed"]],
        "instructions":"Use the actual game's supported controls UI only in an authorized manual session. Verify menu/context, bundled meanings and prompts. This checklist cannot edit unsupported binary/UI-only storage or certify a saved file as effective."}
