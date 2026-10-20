"""MCI-12: directional policy configuration and restrictive local decisions.

Trigger eligibility never starts a scheduler, transfer, adoption or model call.
"""
from copy import deepcopy
import math

from GameToolAIContracts import stable_revision
from .contracts import require, identifier, SHA
from .vault import CLASSES, EXCLUDED
from .workspace_state import LocalState

DIMENSIONS = ("account_id", "workspace_id", "project_id", "source_device", "destination_device", "capability", "content_class")
CONTROLS = ("transfer", "adoption", "index", "context")
DEPTHS = ("none", "notice", "summary", "task_packet", "selected_details")
TRIGGERS = {"manual", "checkpoint", "reconnect", "interval", "debounced"}
LEGACY_REVISION = "legacy-body-v1"
EFFECTIVE_REVISION = "effective-config-v2"


def validate_policy(body):
    require(type(body) is dict and type(body.get("schema_version")) is int and body["schema_version"] == 1 and body.get("kind") == "GameToolsWorkspacePolicy", "Unsupported policy format.")
    require(body.get("revision_scheme", LEGACY_REVISION) in {LEGACY_REVISION, EFFECTIVE_REVISION}, "Unsupported policy revision semantics.")
    require(type(body.get("hard_exclusions")) is list and all(type(x) is str for x in body["hard_exclusions"]), "Invalid local exclusions.")
    rules = body.get("rules")
    require(type(rules) is list and len(rules) <= 128, "Policy rule count bound exceeded.")
    seen = set()
    for row in rules:
        require(type(row) is dict, "Invalid policy rule.")
        identifier(row.get("id")); require(row["id"] not in seen, "Duplicate policy rule."); seen.add(row["id"])
        scope = row.get("scope")
        require(type(scope) is dict and set(scope) == set(DIMENSIONS), "Policy needs every scope dimension.")
        for v in scope.values():
            if v != "*": identifier(v)
        require(row.get("origin") in {"destination", "central", "peer"} and type(row.get("enabled")) is bool, "Invalid rule authority/enablement.")
        require(type(row.get("controls")) is dict and set(row["controls"]) == set(CONTROLS) and all(type(v) is bool for v in row["controls"].values()), "Each effect needs an independent boolean control.")
        require(row.get("context_depth") in DEPTHS, "Unknown context depth.")
        trigger = row.get("trigger")
        require(type(trigger) is dict and trigger.get("kind") in TRIGGERS, "Unsupported trigger.")
        if trigger["kind"] in {"interval", "debounced"}:
            require(type(trigger.get("seconds")) is int and 1 <= trigger["seconds"] <= 86400, "Trigger seconds outside bound.")
    acks = body.get("central_acknowledgements", [])
    require(type(acks) is list and len(acks) <= 128 and all(type(x) is str and SHA.fullmatch(x) for x in acks), "Invalid local policy acknowledgements.")
    staged = body.get("staged_context", [])
    require(type(staged) is list and len(staged) <= 128, "Staged context count exceeds its bound.")
    for row in staged:
        require(type(row) is dict and row.get("revision_scheme", LEGACY_REVISION) in {LEGACY_REVISION, EFFECTIVE_REVISION}, "Unsupported context reference revision semantics.")
        identifier(row.get("id")); require(type(row.get("source_sha256")) is str and SHA.fullmatch(row["source_sha256"]), "Staged reference needs a revision.")
        require(row.get("depth") in DEPTHS and type(row.get("policy_revision")) is str and SHA.fullmatch(row["policy_revision"]), "Invalid staged context binding.")
    return deepcopy(body)


def policy_revision(body):
    """Versioned effective configuration; legacy hashes retain their meaning.

    All unknown body fields conservatively affect the v2 digest. Only the
    explicitly inert queue and presentation are excluded. LocalState still
    binds the entire body for compare-and-swap and audit history.
    """
    body = validate_policy(body)
    if body.get("revision_scheme", LEGACY_REVISION) == LEGACY_REVISION:
        return stable_revision(body)
    configuration = {k: v for k, v in body.items() if k not in {"staged_context", "view", "revision_scheme"}}
    return stable_revision({"kind": "GameToolsEffectivePolicyRevision", "revision_scheme": EFFECTIVE_REVISION, "configuration": configuration})


def trigger_due(trigger, event, *, now, last_fire=None, last_change=None):
    require(type(now) in {int, float} and math.isfinite(now), "Invalid evaluation clock.")
    for value in (last_fire, last_change):
        require(value is None or type(value) in {int, float} and math.isfinite(value) and value <= now, "Clock drift; inspect trigger state.")
    kind = trigger["kind"]
    if event != kind: return False
    if kind == "interval": return last_fire is not None and now - last_fire >= trigger["seconds"]
    if kind == "debounced": return last_change is not None and now - last_change >= trigger["seconds"] and (last_fire is None or last_fire < last_change)
    return True


def evaluate(body, request, *, active_turn=True, boundary="unobserved", event="manual", now=0, last_fire=None, last_change=None):
    body = validate_policy(body)
    require(type(request) is dict and set(request) == set(DIMENSIONS), "Select every policy dimension explicitly.")
    for value in request.values(): identifier(value)
    require(type(active_turn) is bool and boundary in {"unobserved", "new_turn", "on_request"}, "Unknown context boundary.")
    excluded = request["content_class"] not in CLASSES or request["content_class"] in EXCLUDED | set(body["hard_exclusions"])
    matching, ignored = [], []
    for rule in body["rules"]:
        if not all(rule["scope"][k] in {"*", request[k]} for k in DIMENSIONS): continue
        if rule["origin"] == "peer" or rule["origin"] == "central" and stable_revision(rule) not in body.get("central_acknowledgements", []):
            ignored.append(rule["id"]); continue
        matching.append(rule)
    controls = {key: bool(matching) and not excluded and all(r["enabled"] and r["controls"][key] for r in matching) for key in CONTROLS}
    depth = min((DEPTHS.index(r["context_depth"]) for r in matching), default=0) if controls["context"] else 0
    due = bool(matching) and all(trigger_due(r["trigger"], event, now=now, last_fire=last_fire, last_change=last_change) for r in matching)
    staged = controls["context"] and depth > 0 and (active_turn or boundary == "unobserved")
    return {"kind": "workspace_policy_decision", "request": deepcopy(request), "policy_revision": policy_revision(body),
            "controls": controls, "context_depth": DEPTHS[depth], "context_ready_at_reported_boundary": bool(depth and not staged),
            "context_staged": bool(staged), "trigger_eligible": due and controls["transfer"],
            "matched_rules": [r["id"] for r in matching], "ignored_unacknowledged_or_peer": ignored,
            "reason": "local_hard_exclusion" if excluded else "restrictive_intersection" if matching else "default_deny",
            "effect": "none", "boundary_evidence": "caller_reported_only", "model_context_delivery": "not_connected"}


class PolicyStore:
    def __init__(self, root): self.state = LocalState(root, "workspace-policy")

    @classmethod
    def create(cls, root):
        LocalState.create(root, "workspace-policy", {"schema_version": 1, "kind": "GameToolsWorkspacePolicy", "rules": [],
                          "hard_exclusions": sorted(EXCLUDED), "central_acknowledgements": [], "staged_context": [], "view": {"hidden_controls": []}})
        return cls(root)

    def snapshot(self):
        row = self.state.snapshot(); validate_policy(row["body"]); return row

    def propose_rule(self, rule):
        base = self.snapshot(); body = deepcopy(base["body"])
        body["rules"] = [r for r in body["rules"] if r["id"] != rule["id"]] + [deepcopy(rule)]
        validate_policy(body); return self.state.propose(body, base["revision"])

    def accept(self, proposal, accepted_sha256):
        validate_policy(proposal["body"])
        return self.state.commit(proposal, accepted_sha256)

    def acknowledge_central(self, rule_id):
        base = self.snapshot(); body = deepcopy(base["body"])
        rule = next((r for r in body["rules"] if r["id"] == rule_id and r["origin"] == "central"), None)
        require(rule is not None, "Select a central rule proposal.")
        body["central_acknowledgements"] = sorted(set(body["central_acknowledgements"]) | {stable_revision(rule)})
        return self.state.propose(body, base["revision"])

    def rollback_rule(self, rule_id, historical_revision):
        old = next((r for r in self.state.history() if r["revision"] == historical_revision), None)
        require(old is not None, "Select an existing historical revision.")
        historical = next((r for r in old["body"]["rules"] if r["id"] == rule_id), None)
        base = self.snapshot(); body = deepcopy(base["body"])
        body["rules"] = [r for r in body["rules"] if r["id"] != rule_id] + ([deepcopy(historical)] if historical else [])
        validate_policy(body); return self.state.propose(body, base["revision"])

    def stage_context(self, reference_id, source_sha256, depth):
        base = self.snapshot(); body = deepcopy(base["body"])
        row = {"id": reference_id, "source_sha256": source_sha256, "depth": depth, "policy_revision": policy_revision(body)}
        if body.get("revision_scheme") == EFFECTIVE_REVISION: row["revision_scheme"] = EFFECTIVE_REVISION
        require(not any(r["id"] == reference_id for r in body["staged_context"]), "Context reference already staged.")
        body["staged_context"].append(row); validate_policy(body)
        return self.state.propose(body, base["revision"])

    def propose_revision_upgrade(self):
        """Exact explicit upgrade; old access pins and queued rows are retained.

        Their old hashes cannot become v2 authority. Access needs a fresh pin
        and device acknowledgement; legacy queued rows require explicit restage.
        Exact per-rule central acknowledgements keep their existing meaning.
        """
        base = self.snapshot(); body = deepcopy(base["body"])
        require(body.get("revision_scheme", LEGACY_REVISION) == LEGACY_REVISION, "Policy already uses effective configuration revisions.")
        body["revision_scheme"] = EFFECTIVE_REVISION
        validate_policy(body)
        return self.state.propose(body, base["revision"])

    def restage_context(self, reference_id, source_sha256, depth):
        base = self.snapshot(); body = deepcopy(base["body"])
        require(body.get("revision_scheme") == EFFECTIVE_REVISION and any(r["id"] == reference_id for r in body["staged_context"]), "Select an existing reference under the explicit v2 scheme.")
        body["staged_context"] = [r for r in body["staged_context"] if r["id"] != reference_id]
        body["staged_context"].append({"id": reference_id, "source_sha256": source_sha256, "depth": depth,
                                       "policy_revision": policy_revision(body), "revision_scheme": EFFECTIVE_REVISION})
        validate_policy(body)
        return self.state.propose(body, base["revision"])

    def context_notice(self, reference_id, expected_policy_revision, *, active_turn=True, boundary="unobserved"):
        body = self.snapshot()["body"]
        row = next((r for r in body["staged_context"] if r["id"] == reference_id), None)
        require(row is not None and row["policy_revision"] == expected_policy_revision, "Staged context/policy drift; inspect again.")
        scheme = body.get("revision_scheme", LEGACY_REVISION)
        require(row.get("revision_scheme", LEGACY_REVISION) == scheme, "Legacy staged context requires an explicit reviewed restage under v2.")
        if scheme == LEGACY_REVISION:
            policy_without_queue = deepcopy(body); policy_without_queue["staged_context"] = [r for r in body["staged_context"] if r["id"] != reference_id]
            current_revision = stable_revision(policy_without_queue)
        else: current_revision = policy_revision(body)
        require(current_revision == expected_policy_revision, "Policy changed after staging; re-evaluate the source reference.")
        require(not active_turn and boundary in {"new_turn", "on_request"}, "Context stays staged until a reported supported boundary.")
        return {"id": row["id"], "source_sha256": row["source_sha256"], "depth": row["depth"], "state": "NOTICE_READY_NO_DELIVERY",
                "model_context_delivery": "not_connected", "effect": "none"}
