"""Conservative static request checks. No model call, submission or execution."""
from __future__ import annotations

import re

from .contracts import require


def check_request(draft, view, intended_outcome=""):
    require(type(draft) is str and 0 < len(draft.strip()) <= 16384 and "\x00" not in draft, "Enter a bounded nonempty draft.")
    require(type(intended_outcome) is str and len(intended_outcome) <= 4096, "Invalid intended outcome.")
    nodes = [n for n in view["all_nodes"] if n["applicable"]]
    stale = [n["id"] for n in nodes if n["source"]["availability"] in {"stale", "unreadable", "missing"}]
    require(not stale, "Selected context has stale or inaccessible sources; reload before preflight.")
    findings, remove, lower = [], set(), draft.casefold()
    conflict_keys = {x["key"] for x in view["conflicts"]}
    for conflict in view["conflicts"]:
        checked = all(n["fresh"] for n in nodes if n["id"] in conflict["nodes"])
        findings.append({"class": "verified_source_fact" if checked else "conditional_estimate", "code": "CONFLICTING_DECLARATIONS",
                         "message": "Conflicting source declarations for " + conflict["key"] + "; review applicability before removing wording.",
                         "sources": conflict["nodes"]})
    lines = draft.splitlines(keepends=True)
    for node in nodes:
        default = node.get("default")
        if default:
            matches = [i for i, line in enumerate(lines) if line.strip().casefold() in
                       {x.casefold() for x in default.get("redundant_lines", [])}]
            if matches:
                confirmed = node["fresh"] and node["observation"] == "reported_loaded" and default["key"] not in conflict_keys
                findings.append({"class": "conditional_estimate", "code": "DEFAULT_ALREADY_DECLARED",
                                 "message": "This line repeats a selected source default. " +
                                 ("The selected context reports it loaded; an optional exact-line reduction is available." if confirmed else
                                  "Actual runtime loading is unverified; keep the original wording unless confirmed."),
                                 "sources": [node["id"]], "lines": [i + 1 for i in matches]})
                # Never remove exclusions, action boundaries, deliverables or partial sentences.
                if confirmed and default.get("category") == "presentation_preference":
                    # Imported context is data. A forged category cannot turn
                    # arbitrary commands or deliverables into removable defaults.
                    safe = {"answer in english.", "respond in english.", "please answer in english.", "ענה באנגלית.", "תענה באנגלית."}
                    if default["key"] == "response.language" and default["value"] == "English":
                        remove.update(i for i in matches if lines[i].strip().casefold() in safe)
        hits = [term for term in node.get("trigger_terms", []) if term.casefold() in lower]
        if hits:
            findings.append({"class": "conditional_estimate", "code": "DECLARED_ROUTING_CUE",
                             "message": "Possible " + node["kind"] + " relevance: " + node["label"] + ". Wording overlap does not guarantee invocation or authorize an action.",
                             "sources": [node["id"]], "matched_terms": hits})
    if re.fullmatch(r"\s*(do it|continue|fix it|תעשה את זה|תמשיך)[.!?\s]*", lower):
        findings.append({"class": "conditional_estimate", "code": "MISSING_REFERENT", "sources": [],
                         "message": "The draft depends on earlier context. Name the intended artifact or outcome if this is a fresh chat."})
    if re.search(r"\b(everything|all files|all computers|full access)\b|כל הקבצים|כל המחשבים|הכל", lower):
        findings.append({"class": "conditional_estimate", "code": "BROAD_SCOPE", "sources": [],
                         "message": "Broad wording may expand the work. Consider naming the intended projects, devices and permitted effects."})
    if re.search(r"\b(install|delete|publish|send|apply|sync|run)\b|להתקין|למחוק|לשלוח|לסנכרן|להפעיל", lower):
        findings.append({"class": "conditional_estimate", "code": "ACTION_LANGUAGE", "sources": [],
                         "message": "The draft contains action-related wording, possibly within an exclusion. Review its intended effect; this checker does not grant permission."})
    candidate = "".join(line for i, line in enumerate(lines) if i not in remove)
    if not candidate.strip():
        candidate, remove = draft, set()
    return {"kind": "static_request_preflight", "context_revision": view["revision"],
            "original": draft, "intended_outcome": intended_outcome, "candidate": candidate,
            "removed_line_numbers": [i + 1 for i in sorted(remove)], "findings": findings,
            "unknown_influences": view["unknowns"], "observed_model_trials": 0,
            "limitations": "Static declared-context checks with selected-source citations; no semantic-equivalence or exact-behavior guarantee. Loaded-state assertions come from the selected context, not platform attestation.",
            "rewrite_acceptance": "explicit_user_action_required", "submitted": False,
            "execution": "none", "model_api_calls": 0}
