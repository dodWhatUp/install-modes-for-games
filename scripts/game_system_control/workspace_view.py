"""Read-only foundation summaries for the existing control-center renderer."""
from datetime import datetime, timezone
from pathlib import Path

from GameToolUserData import _read, digest
from .contracts import validate_context
from .vault import VaultRegistry
from .policy import PolicyStore, LEGACY_REVISION
from .access import AccessStore, MAX_DEVICE_STALENESS_SECONDS
from .workspace_state import private_root, MAX_REVISIONS


def workspace_context(root):
    root = private_root(root)
    registry, policy, access = VaultRegistry(root/"bindings"), PolicyStore(root/"policy"), AccessStore(root/"access")
    authentication = access.snapshot()["body"].get("authentication", "local_os_session")
    rows = [("vault", registry.state.snapshot(), "bindings", "Managed vault bindings"),
            ("policy", policy.snapshot(), "policy", "Directional policy · transfer, adoption, index and context"),
            ("access", access.snapshot(), "access", "Local OS-session roles · provider sign-in not connected" if authentication == "local_os_session" else "Windows account verification · local roles and scopes")]
    sources, nodes = [], []
    for ident, record, folder, label in rows:
        relative = folder + f"/{record['generation']:08}.json"
        raw = _read(root/relative)[0]
        sources.append({"id": ident, "owner": "GameTools managed-workspace local state", "locator": relative,
                        "binding": "selected_project", "sha256": digest(raw), "availability": "available"})
        summary = ({"vaults": len(record["body"]["vaults"]), "managed_roots": ["source", "assets", "outputs", "continuation"], "fallback": "refuse"} if ident == "vault" else
                   {"rules": [{k: r[k] for k in ("id", "enabled", "controls", "context_depth", "trigger")} for r in record["body"]["rules"]], "delivery": "not_connected",
                    "revision_scheme": record["body"].get("revision_scheme", LEGACY_REVISION)} if ident == "policy" else
                   {"memberships": record["body"]["memberships"], "storage_permissions": record["body"]["storage_permissions"], "provider_sign_in": authentication,
                    "remote_authentication": "not_connected", "non_metadata_freshness_limit_seconds": MAX_DEVICE_STALENESS_SECONDS})
        summary["local_history_capacity"] = {"maximum_revisions": MAX_REVISIONS, "used": record["generation"] + 1,
                                             "remaining": MAX_REVISIONS - record["generation"] - 1, "at_capacity": record["generation"] + 1 == MAX_REVISIONS,
                                             "rollover": "not_implemented_no_automatic_reset"}
        nodes.append({"id": ident, "source_id": ident, "kind": "component", "label": label, "selected_summary": summary,
                      "scopes": ["managed-workspace"], "layer": "project", "observation": "declared", "depends_on": ["policy", "access"] if ident == "vault" else []})
    body = rows[2][1]["body"]
    stopped = (access.state.root/"LOCAL-STOP.json").exists()
    now = datetime.now(timezone.utc).timestamp()
    devices = [{"id": d["id"], "label": d["id"] + " · enrollment " + ("expired" if now >= d["expires_at"] else d["status"]),
                "availability": "reported_offline" if stopped or d["status"] != "active" or now >= d["expires_at"] or not d["online"] else "unknown",
                "last_seen": datetime.fromtimestamp(d["last_seen"], timezone.utc).isoformat()} for d in body["devices"]]
    activities = []
    for ident, record, _, label in rows:
        activities.append({"id": "summary-" + ident, "source_id": ident, "goal": label,
                           "outcome": "Revision generation " + str(record["generation"]), "blocker": "Local stop active" if stopped else "External provider authentication and live transport are not connected",
                           "changed_artifacts": [], "next_boundary": "Review explicit local policy/authorization before managed placement",
                           "retention": "source_owned", "detail_resource": None})
    return validate_context({"schema_version": 1, "kind": "GameToolsSystemContext", "scope": "managed-workspace",
                             "label": "Managed workspace foundations · selected local metadata", "sources": sources, "nodes": nodes,
                             "devices": devices, "events": [], "activities": activities, "resources": [],
                             "unknown_coverage": (["Fresh Windows verification on this registry"] if authentication == "local_os_session" else []) +
                             ["Other physical computer", "Live transport", "Native Codex chat continuity", "Actual model-context delivery"]})
