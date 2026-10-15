"""Read-only AI efficiency foundation over existing Game Tools services.

The facade adds compact status, search/fetch, resume, change cursors, blocker
explanations, batch inspection, catalog reads and shared-report inspection.  It
never approves, executes, launches, downloads, records, injects input, or reads
an AI-supplied filesystem path.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from GameToolAIContracts import (
    completion_matrix, decode_cursor, encode_cursor, explain_blocker,
    result_envelope, stable_revision,
)
from GameToolAIKnowledge import KnowledgeError, KnowledgeIndex
from GameToolAutomation import AutomationService
from game_mod_ops.safety import ModError, require


class FoundationError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _scope(game_id=None, **extra):
    value = {"game_id": game_id, **extra}
    return {key: item for key, item in value.items() if item is not None}


def _manifest(root: Path) -> dict:
    path = root / "MANIFEST.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise FoundationError("PACKAGE_UNAVAILABLE", "Package manifest could not be read.") from None
    if not isinstance(value, dict) or not isinstance(value.get("files"), list):
        raise FoundationError("PACKAGE_UNAVAILABLE", "Package manifest is unsupported.")
    return value


def _completion(*, connected=True, proposal=False):
    return completion_matrix(
        source="verified",
        tests="partially_verified",
        package="verified",
        installation="unknown",
        connection="verified" if connected else "unknown",
        execution="prepared" if proposal else "not_started",
        runtime="not_started",
        gameplay="not_started",
        publication="not_started",
    )


def _status_from_request(value: dict) -> str:
    status = value.get("status") if isinstance(value, dict) else None
    return status if isinstance(status, str) and status else "UNKNOWN"


class FoundationService:
    def __init__(self, service, source_root: Path | None = None):
        self.service = service
        self.multi_game = bool(getattr(service, "multi_game", False))
        self.root = Path(source_root or Path(__file__).resolve().parents[1]).absolute()
        self.manifest = _manifest(self.root)
        self.knowledge = KnowledgeIndex(self.root)
        self._catalog = None
        self._planning = None

    def _context(self, game_id=None, known_revisions=None):
        known_revisions = known_revisions or {}
        if self.multi_game:
            return self.service.context(game_id=game_id, known_revisions=known_revisions)
        require(game_id is None, "INVALID_ARGUMENTS", "This endpoint has no game-scoped workspace selector.")
        return self.service.context(known_revisions=known_revisions)

    def _requests(self, game_id=None):
        if self.multi_game:
            if game_id is None:
                return [], "Select one game to inspect its proposal mailbox."
            scoped = self.service.workspaces.service(game_id)
            return scoped.list_requests(), None
        return self.service.list_requests(), None

    def _shared_reports(self):
        if self.multi_game:
            base = AutomationService(self.service.workspaces.data_dir)
            return base.context()["sections"]["reports"]
        return self.service.context()["sections"]["reports"]

    def _catalog_service(self):
        if self._catalog is None:
            from GameToolCatalogBridge import CatalogService
            self._catalog = CatalogService()
        return self._catalog

    def _planning_service(self):
        require(self.multi_game and hasattr(self.service, "workspaces"),
                "CAPABILITY_UNAVAILABLE",
                "Read-only game planning requires the multi-game workspace endpoint.")
        if self._planning is None:
            from GameToolPlanning import PlanningService
            self._planning = PlanningService(self.service.workspaces)
        return self._planning

    def _envelope(self, *, result_type="read", status="OK", data=None, game_id=None,
                  revision=None, next_actions=None, effects=None, completion=None,
                  retry=None, evidence=None, freshness=None, **scope_extra):
        return result_envelope(
            result_type=result_type, status=status, data=data,
            scope=_scope(game_id, **scope_extra), revision=revision,
            freshness={"observed_utc": _utc_now(), **(freshness or {})},
            completion=completion or _completion(), evidence=evidence or [],
            effects=effects, next_safe_actions=next_actions or [], retry=retry,
        )

    def status(self, game_id=None, known_revision=None):
        context = self._context(game_id)
        sections = context.get("sections", {})
        jobs = sections.get("jobs", [])
        games = sections.get("games")
        data = {
            "kind": "game_tools_status",
            "game_id": game_id,
            "games": games if isinstance(games, list) else None,
            "open_jobs": jobs,
            "capabilities": sections.get("capabilities", {}),
            "context_revisions": context.get("revisions", {}),
            "knowledge": self.knowledge.metadata(),
            "package": {
                "bundle": self.manifest.get("bundle"),
                "tool_hub": self.manifest.get("component_versions", {}).get("tool_hub"),
                "canonical_reference_revision": self.manifest.get("canonical_reference_revision"),
                "native_windows_acceptance": False,
                "real_game_acceptance": False,
            },
        }
        revision = stable_revision(data)
        if known_revision == revision:
            data = {"unchanged": True, "revision": revision}
        actions = []
        if jobs:
            actions.append("Inspect the existing job or request handle before preparing another operation.")
        if not actions:
            actions.append("Use game_tools_search or a domain preview tool for the next bounded read.")
        return self._envelope(
            status="UNCHANGED" if known_revision == revision else "CURRENT",
            data=data, game_id=game_id, revision=revision, next_actions=actions,
            evidence=[{
                "id": "package-manifest", "level": "documented",
                "revision": stable_revision(self.manifest),
            }],
        )

    def search(self, query, scope="all", limit=8):
        value = self.knowledge.search(query, scope, limit)
        return self._envelope(
            status="MATCHES_FOUND" if value["results"] else "NO_MATCHES",
            data=value, revision=stable_revision(value),
            next_actions=["Fetch only the exact result IDs needed for the current task."],
            effects={"read": ["packaged_knowledge"], "write": [], "network": False, "unknown": False},
            evidence=[{"id": "knowledge-index", "level": "tested", "revision": self.knowledge.revision}],
        )

    def fetch(self, result_id, revision=None, offset=0, limit=120):
        value = self.knowledge.fetch(result_id, revision, offset, limit)
        return self._envelope(
            status="FETCHED", data=value, revision=value["revision"],
            next_actions=[] if value["next_offset"] is None else [
                f"Fetch the same result_id with offset {value['next_offset']} only if more lines are needed."
            ],
            effects={"read": ["packaged_knowledge"], "write": [], "network": False, "unknown": False},
            evidence=[{"id": result_id, "level": "documented", "revision": value["revision"]}],
        )

    def resume(self, game_id=None, known_revision=None):
        context = self._context(game_id)
        sections = context.get("sections", {})
        jobs = sections.get("jobs", [])
        requests, request_note = self._requests(game_id)
        pending = []
        unknown_effects = []
        for row in requests:
            if not isinstance(row, dict):
                continue
            status = _status_from_request(row)
            item = {key: row.get(key) for key in ("request_id", "status", "request_sha256", "operation") if row.get(key) is not None}
            if status not in {"COMPLETED", "REJECTED", "EXPIRED"}:
                pending.append(item)
            if "UNKNOWN" in status or "RECONCILE" in status:
                unknown_effects.append(item)
        for row in jobs:
            status = _status_from_request(row)
            if "UNKNOWN" in status or "RECONCILE" in status:
                unknown_effects.append({"kind": "job", **{key: row.get(key) for key in ("job_id", "game_id", "status")}})
        data = {
            "kind": "game_tools_resume",
            "open_work": {"jobs": jobs, "requests": pending},
            "unknown_effects": unknown_effects,
            "request_scope_note": request_note,
            "handles": [
                {"kind": "request", "id": row["request_id"], **({"game_id": game_id} if game_id else {})}
                for row in pending if row.get("request_id")
            ] + [
                {"kind": "job", "id": row["job_id"], "game_id": row.get("game_id", game_id)}
                for row in jobs if isinstance(row, dict) and row.get("job_id")
            ],
            "context_revisions": context.get("revisions", {}),
        }
        revision = stable_revision(data)
        unchanged = known_revision == revision
        actions = []
        if unknown_effects:
            actions.append("Inspect the same handles with game_tools_status_batch; do not resubmit uncertain operations.")
        elif pending:
            actions.append("Review the pending proposal locally or inspect its current receipt.")
        elif jobs:
            actions.append("Inspect the existing job before preparing another plan.")
        else:
            actions.append("No open operation was found; start with a read or preview for the selected goal.")
        if request_note:
            actions.append(request_note)
        return self._envelope(
            status="UNCHANGED" if unchanged else ("RECONCILIATION_REQUIRED" if unknown_effects else "RESUME_READY"),
            data={"unchanged": True, "revision": revision} if unchanged else data,
            game_id=game_id, revision=revision, next_actions=actions,
            effects={"read": ["context", "request_receipts"], "write": [], "network": False, "unknown": bool(unknown_effects)},
            retry={"allowed": False, "inspect_handle": data["handles"][0]["id"] if unknown_effects and data["handles"] else None},
        )

    def changes(self, cursor=None, game_id=None):
        previous = {}
        if cursor is not None:
            try:
                previous = decode_cursor(cursor)
            except ValueError as error:
                raise FoundationError("INVALID_CURSOR", str(error)) from None
            if previous.get("game_id") != game_id:
                raise FoundationError("INVALID_CURSOR", "Change cursor belongs to another game scope.")
        known = previous.get("revisions", {})
        context_known = {key: value for key, value in known.items() if key != "requests"}
        context = self._context(game_id, context_known)
        revisions = dict(context.get("revisions", {}))
        requests, request_note = self._requests(game_id)
        revisions["requests"] = stable_revision(requests if request_note is None else {"unavailable": request_note})
        changed_sections = sorted(context.get("sections", {}))
        if known.get("requests") != revisions["requests"]:
            changed_sections.append("requests")
        changed_sections = sorted(set(changed_sections))
        changed_ids = []
        for section, value in context.get("sections", {}).items():
            if isinstance(value, list):
                for row in value[:128]:
                    if isinstance(row, dict):
                        ident = row.get("job_id") or row.get("game_id") or row.get("id")
                        if isinstance(ident, str):
                            changed_ids.append({"section": section, "id": ident})
        if known.get("requests") != revisions["requests"]:
            for row in requests[:128]:
                if isinstance(row, dict) and isinstance(row.get("request_id"), str):
                    changed_ids.append({"section": "requests", "id": row["request_id"]})
        new_cursor = encode_cursor({"game_id": game_id, "revisions": revisions})
        data = {
            "changed_sections": changed_sections,
            "changed_ids": changed_ids,
            "new_cursor": new_cursor,
            "truncated": False,
            "revisions": revisions,
        }
        return self._envelope(
            status="CHANGED" if changed_sections else "UNCHANGED",
            data=data, game_id=game_id, revision=stable_revision(data),
            next_actions=[] if not changed_sections else ["Fetch or inspect only the changed sections relevant to the current task."],
            effects={"read": ["context_revisions"], "write": [], "network": False, "unknown": False},
        )

    def blocker(self, code, handle=None):
        value = explain_blocker(code, handle)
        retry = {"allowed": bool(value["retry"]), "inspect_handle": handle if not value["effects_known"] else None}
        return self._envelope(
            result_type="blocked", status=code, data=value,
            revision=stable_revision(value),
            next_actions=[value["user_action"]],
            effects={"read": [], "write": [], "network": False, "unknown": not value["effects_known"]},
            retry=retry,
        )

    def _request_status(self, ident, game_id=None):
        if self.multi_game:
            require(game_id is not None, "INVALID_ARGUMENTS", "A game_id is required for request status.")
            return self.service.request_status(ident, game_id)
        return self.service.request_status(ident)

    def _keybind_status(self, ident, game_id=None):
        keybinds = getattr(self.service, "keybinds", None)
        require(keybinds is not None, "CAPABILITY_UNAVAILABLE", "This endpoint has no keybind plan store.")
        value = keybinds.status(ident)
        if game_id and isinstance(value, dict):
            plan = keybinds.plan(ident)
            targets = [keybinds.target(row["target_id"])["spec"]["game_id"] for row in plan["items"]]
            require(all(item == game_id for item in targets), "GAME_MISMATCH", "Another game owns this plan.")
        return value

    def status_batch(self, handles):
        require(type(handles) is list and 1 <= len(handles) <= 32, "INVALID_ARGUMENTS", "Choose between one and 32 handles.")
        context_cache = {}
        results = []
        for handle in handles:
            if type(handle) is not dict or set(handle) - {"kind", "id", "game_id"} or not {"kind", "id"} <= set(handle):
                results.append({"handle": handle, "status": "INVALID_ARGUMENTS", "effects_known": True})
                continue
            kind, ident, game_id = handle["kind"], handle["id"], handle.get("game_id")
            try:
                if kind == "request":
                    value = self._request_status(ident, game_id)
                elif kind == "keybind_plan":
                    value = self._keybind_status(ident, game_id)
                elif kind == "job":
                    key = game_id or "__all__"
                    if key not in context_cache:
                        context_cache[key] = self._context(game_id)
                    rows = context_cache[key].get("sections", {}).get("jobs", [])
                    value = next((row for row in rows if row.get("job_id") == ident), None)
                    if value is None:
                        raise FoundationError("HANDLE_NOT_FOUND", "Job handle was not found.")
                elif kind == "instance":
                    value = self._planning_service().instances.public(ident)
                    if game_id is not None:
                        require(value.get("game_id") == game_id, "GAME_MISMATCH",
                                "Registered instance belongs to another game scope.")
                elif kind == "resource":
                    value = self.knowledge.fetch(ident, limit=20)
                else:
                    raise FoundationError("INVALID_ARGUMENTS", "Unknown handle kind.")
                state = _status_from_request(value)
                results.append({
                    "handle": deepcopy(handle), "status": state,
                    "effects_known": not ("UNKNOWN" in state or "RECONCILE" in state),
                    "value": value,
                })
            except (FoundationError, ModError, KnowledgeError, ValueError, OSError, KeyError) as error:
                code = getattr(error, "code", "HANDLE_NOT_FOUND")
                results.append({
                    "handle": deepcopy(handle), "status": code,
                    "effects_known": code not in {"UNKNOWN_EFFECTS_RECONCILE", "RECONCILIATION_REQUIRED"},
                    "message": "Inspect the exact owning scope; no retry was performed.",
                })
        data = {"results": results, "changed_cursor": encode_cursor({"batch_revision": stable_revision(results)})}
        unknown = any(not row["effects_known"] for row in results)
        return self._envelope(
            status="RECONCILIATION_REQUIRED" if unknown else "BATCH_INSPECTED",
            data=data, revision=stable_revision(data),
            next_actions=["Inspect entries with unknown effects before preparing any replacement operation."] if unknown else [],
            effects={"read": ["existing_handles"], "write": [], "network": False, "unknown": unknown},
            retry={"allowed": False, "inspect_handle": next((row["handle"].get("id") for row in results if not row["effects_known"] and isinstance(row["handle"], dict)), None)},
        )

    def catalog(self, query_or_goal, game_id=None, limit=12):
        require(type(limit) is int and 1 <= limit <= 30, "INVALID_ARGUMENTS", "Invalid catalog result limit.")
        catalog = self._catalog_service()
        filters = {"search": query_or_goal, "sort": "id"}
        if game_id is not None:
            filters["game"] = game_id
        rows = catalog.list_nodes(**filters)[:limit]
        compact = []
        for row in rows:
            compact.append({key: row.get(key) for key in (
                "id", "name", "entity", "kind", "status", "installation", "categories", "games"
            ) if row.get(key) is not None})
        data = {
            "query": query_or_goal, "game_id": game_id, "candidates": compact,
            "catalog_revision": catalog.revision, "planning_only": True,
            "execution": "none", "unsupported": [] if compact else ["No bundled catalog match."],
        }
        return self._envelope(
            status="MATCHES_FOUND" if compact else "NO_MATCHES",
            data=data, game_id=game_id, revision=stable_revision(data),
            next_actions=["Inspect an exact candidate with the existing catalog UI before adopting a stack."] if compact else [],
            effects={"read": ["bundled_catalog"], "write": [], "network": False, "unknown": False},
            evidence=[{"id": "catalog", "level": "documented", "revision": catalog.revision}],
        )

    def reports(self, record_ids=None, metric=None):
        record_ids = [] if record_ids is None else record_ids
        require(type(record_ids) is list and len(record_ids) <= 16 and all(isinstance(item, str) for item in record_ids),
                "INVALID_ARGUMENTS", "Invalid report record list.")
        reports = self._shared_reports()
        selected = [row for row in reports if not record_ids or row.get("report_id") in set(record_ids)]
        require(not record_ids or len(selected) == len(set(record_ids)), "HANDLE_NOT_FOUND", "One or more shared report IDs were not found.")
        rows = []
        for report in selected:
            metrics = report.get("metrics", [])
            if metric is not None:
                metrics = [row for row in metrics if row.get("id") == metric]
            rows.append({
                "report_id": report.get("report_id"), "adapter": report.get("adapter"),
                "provider": report.get("provider"), "coverage": report.get("coverage"),
                "metrics": metrics, "runtime_acceptance": False,
            })
        comparison = None
        if len(rows) >= 2 and metric:
            descriptors = []
            values = []
            for row in rows:
                match = next((item for item in row["metrics"] if item.get("id") == metric), None)
                if match is None:
                    break
                descriptors.append({key: match.get(key) for key in ("id", "unit", "definition", "frame_class")})
                values.append(match.get("value"))
            if len(values) == len(rows) and all(item == descriptors[0] for item in descriptors) and all(type(value) in (int, float) for value in values):
                baseline = values[0]
                comparison = {
                    "metric": metric, "baseline": baseline,
                    "values": values,
                    "deltas_from_first": [value - baseline for value in values],
                    "descriptive_only": True,
                }
        data = {
            "records": rows, "comparison": comparison,
            "comparison_ready": comparison is not None,
            "new_provider_read": False, "benchmark_executed": False,
        }
        return self._envelope(
            status="REPORTS_INSPECTED", data=data, revision=stable_revision(data),
            next_actions=[] if comparison is not None or len(rows) < 2 else [
                "Select one metric with identical provider definitions before calculating a descriptive delta."
            ],
            effects={"read": ["explicitly_shared_report_summaries"], "write": [], "network": False, "unknown": False},
        )

    def instances(self, game_id=None, limit=50):
        value = self._planning_service().list_instances(game_id, limit)
        revision = stable_revision(value)
        return self._envelope(
            status="INSTANCES_LISTED" if value["instances"] else "NO_REGISTERED_INSTANCES",
            data=value, game_id=game_id, revision=revision,
            next_actions=[
                "Use one existing opaque instance ID, or register an exact installation through the local Game-Instances.py route."
            ] if not value["instances"] else [
                "Inspect only the exact registered instance needed for the current goal."
            ],
            effects={"read": ["private instance metadata without paths"], "write": [],
                     "network": False, "unknown": False},
            evidence=[{"id": "instance-registry", "level": "tested", "revision": revision}],
        )

    def instance_inspect(self, instance_id, game_id=None):
        value = self._planning_service().inspect_instance(instance_id, game_id)
        actual_game = value["instance"]["game_id"]
        adapter = value["adapter_contract"]["adapter"]
        completion = completion_matrix(
            source="verified", tests="partially_verified", package="verified",
            installation="partially_verified", connection="verified",
            execution="not_started", runtime="not_started", gameplay="not_started",
            publication="not_started",
        )
        if adapter == "mo2":
            next_actions = [
                "Review declared profile rows and warnings; virtual deployment, runtime loading and conflict winners remain unknown."
            ]
            evidence_id = "mo2-read-adapter"
        else:
            next_actions = [
                "Review manifest warnings and ownership conflicts before treating absence as conclusive."
            ]
            evidence_id = "umm-read-adapter"
        return self._envelope(
            status="INSTANCE_INSPECTED", data=value, game_id=actual_game,
            instance_id=instance_id, revision=value["observation_revision"],
            next_actions=next_actions,
            effects={"read": value["adapter_contract"]["reads"],
                     "write": [], "network": False, "unknown": False},
            completion=completion,
            evidence=[{
                "id": evidence_id, "level": "observed",
                "revision": value["observation_revision"],
            }],
        )

    def plan_goal(self, game_id, goal, instance_id=None, mode=None, selected=None):
        value = self._planning_service().goal_plan(
            game_id, goal, instance_id=instance_id, mode=mode, selected=selected,
        )
        blocked = value["status"] == "BLOCKED"
        actions = [
            "Resolve only the listed blockers, then compile a fresh read-only plan."
        ] if blocked else [
            "Execute the next read node explicitly; this plan creates no job or proposal."
        ]
        return self._envelope(
            result_type="preview", status=value["status"], data=value,
            game_id=game_id, instance_id=instance_id, plan_id=value["plan_id"],
            revision=value["plan_revision"], next_actions=actions,
            effects={"read": value["effects"]["read"],
                     "write": [], "network": False, "unknown": False},
            evidence=[{
                "id": "goal-plan", "level": "tested", "revision": value["plan_revision"],
            }],
        )

    def conflicts(self, game_id, instance_id=None, mode=None, selected=None):
        value = self._planning_service().conflict_graph(
            game_id, instance_id=instance_id, mode=mode, selected=selected,
        )
        actions = [] if value["status"] == "CLEAR" else [
            "Review blocker issues first; advisory conflicts do not authorize automatic changes."
        ]
        return self._envelope(
            status=value["status"], data=value, game_id=game_id,
            instance_id=instance_id, revision=value["graph_revision"],
            next_actions=actions,
            effects={"read": value["effects"]["read"], "write": [],
                     "network": False, "unknown": False},
            evidence=[{
                "id": "ownership-graph", "level": "tested",
                "revision": value["graph_revision"],
            }],
        )

    def prepare_handoff(self, game_id=None, include=None):
        include = ["status", "resume", "changes", "capabilities", "knowledge"] if include is None else include
        allowed = {"status", "resume", "changes", "capabilities", "knowledge"}
        require(
            type(include) is list and len(include) <= 5 and len(include) == len(set(include)) and
            all(isinstance(item, str) and item in allowed for item in include),
            "INVALID_ARGUMENTS", "Invalid handoff include list.",
        )
        status = self.status(game_id) if "status" in include else None
        resume = self.resume(game_id) if "resume" in include else None
        changes = self.changes(game_id=game_id) if "changes" in include else None
        capsule = {
            "schema_version": 1,
            "kind": "game_tools_handoff_capsule",
            "scope": _scope(game_id),
            "package": {
                "bundle": self.manifest.get("bundle"),
                "tool_hub": self.manifest.get("component_versions", {}).get("tool_hub"),
                "canonical_reference_revision": self.manifest.get("canonical_reference_revision"),
                "manifest_revision": stable_revision(self.manifest),
            },
            "records": {},
            "privacy": {
                "source_relative_references_only": True,
                "paths_included": False,
                "credentials_included": False,
                "raw_logs_included": False,
            },
            "effects": {"file_created": False, "uploaded": False, "published": False, "executed": False},
        }
        if status is not None:
            capsule["records"]["status"] = {"revision": status["revision"], "data": status["data"]}
        if resume is not None:
            capsule["records"]["resume"] = {"revision": resume["revision"], "data": resume["data"]}
        if changes is not None:
            capsule["records"]["changes"] = {"revision": changes["revision"], "data": changes["data"]}
        if "capabilities" in include:
            context = self._context(game_id)
            capsule["records"]["capabilities"] = context.get("sections", {}).get("capabilities", {})
        if "knowledge" in include:
            capsule["records"]["knowledge"] = self.knowledge.metadata()
        content_hash = stable_revision(capsule)
        data = {
            "capsule": capsule,
            "content_hash": content_hash,
            "privacy_preview": deepcopy(capsule["privacy"]),
            "local_save_action": {
                "performed": False,
                "available_through_this_tool": False,
                "requires_separate_local_reviewed_export": True,
            },
        }
        return self._envelope(
            result_type="preview", status="HANDOFF_PREPARED", data=data, game_id=game_id,
            revision=content_hash,
            next_actions=[
                "Use the capsule directly for continuation, or request a separate local reviewed export before saving bytes."
            ],
            effects={"read": ["current_sanitized_records"], "write": [], "network": False, "unknown": False},
            completion=_completion(),
            evidence=[{"id": "package-manifest", "level": "documented", "revision": stable_revision(self.manifest)}],
        )

    def call(self, name: str, args: dict):
        if name == "game_tools_status":
            return self.status(**args)
        if name == "game_tools_search":
            return self.search(**args)
        if name == "game_tools_fetch":
            return self.fetch(**args)
        if name == "game_tools_resume":
            return self.resume(**args)
        if name == "game_tools_changes":
            return self.changes(**args)
        if name == "game_tools_explain_blocker":
            return self.blocker(**args)
        if name == "game_tools_status_batch":
            return self.status_batch(**args)
        if name == "game_tools_catalog":
            return self.catalog(**args)
        if name == "game_tools_reports":
            return self.reports(**args)
        if name == "game_tools_instances":
            return self.instances(**args)
        if name == "game_tools_instance_inspect":
            return self.instance_inspect(**args)
        if name == "game_tools_plan_goal":
            return self.plan_goal(**args)
        if name == "game_tools_conflicts":
            return self.conflicts(**args)
        if name == "game_tools_prepare_handoff":
            return self.prepare_handoff(**args)
        raise FoundationError("CAPABILITY_UNAVAILABLE", "Unknown foundation tool.")

    def wrap_legacy(self, name: str, value: Any, *, failed=False):
        result_type = "proposal" if name.endswith("propose") else ("preview" if "preview" in name or "template" in name or "validate" in name else "read")
        status = "REFUSED" if failed else (_status_from_request(value) if isinstance(value, dict) and value.get("status") else "OK")
        effects = {
            "read": ["existing_domain_service"],
            "write": ["local_proposal_mailbox"] if result_type == "proposal" and not failed else [],
            "network": False,
            "unknown": bool(failed and status in {"UNKNOWN_EFFECTS_RECONCILE", "RECONCILIATION_REQUIRED"}),
        }
        completion = _completion(proposal=result_type == "proposal" and not failed)
        return self._envelope(
            result_type="blocked" if failed else result_type,
            status=status, data=value, revision=stable_revision(value),
            next_actions=["Inspect the same handle; no automatic retry was performed."] if failed else [],
            effects=effects, completion=completion,
        )
