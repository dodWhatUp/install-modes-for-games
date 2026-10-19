"""Ephemeral human summaries of existing evidence; no replicated runtime store."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from GameToolJournal import inspect_journal
from .contracts import STAGES, require, timestamp, validate_context, json_value
from .inventory import selected_text, selected_bytes, bound_root


def overview(context, *, now=None, stale_after_seconds=300):
    doc = validate_context(context)
    now = datetime.now(timezone.utc) if now is None else timestamp(now)
    require(type(stale_after_seconds) is int and 0 < stale_after_seconds <= 86400, "Invalid freshness interval.")
    sources = {s["id"]: s for s in doc.get("sources", [])}
    devices = []
    for raw in doc.get("devices", []):
        row = deepcopy(raw)
        seen = timestamp(row["last_seen"]) if row.get("last_seen") else None
        age = (now - seen).total_seconds() if seen else None
        row["freshness"] = "unknown" if age is None else "future_timestamp" if age < 0 else "stale" if age > stale_after_seconds else "recent_report"
        row["live_connection"] = "not_observed"
        devices.append(row)
    events, progress = [], {}
    for raw in sorted(doc.get("events", []), key=lambda x: (timestamp(x["at"]), x["id"])):
        row = deepcopy(raw)
        state, operation = row["state"], row["operation_id"]
        previous = progress.get(operation)
        pos = STAGES.index(state) if state in STAGES else None
        expected = 0 if previous is None else previous + 1
        row["coverage"] = "ordered_declaration" if pos == expected else "partial_or_conflicting_evidence"
        row["evidence"] = "selected_source_declaration"
        row["source_available"] = sources[row["source_id"]]["availability"] == "available"
        if pos is not None and pos == expected:
            progress[operation] = pos
        row["next_decision"] = ("Review conflict; preserve both versions." if state == "conflict" else
                                "Inspect outcome before retry." if state in {"failed", "unknown"} else
                                "Review before adoption." if state == "staged" else
                                "Context use is separate from file adoption." if state in {"adopted", "indexed"} else
                                "No action is authorized by this report.")
        events.append(row)
    activities = []
    for raw in doc.get("activities", []):
        row = {k: deepcopy(raw.get(k)) for k in ("id", "goal", "outcome", "blocker", "changed_artifacts", "next_boundary", "source_id", "retention", "detail_resource")}
        row["full_content_loaded"] = False
        row["coverage"] = "selected summary only"
        row["source_available"] = sources[row["source_id"]]["availability"] == "available"
        activities.append(row)
    return {"devices": devices, "events": events, "activities": activities,
            "persistence": "none", "cache": "none", "background_collection": False,
            "retention_enforcement": "This projection writes nothing; upstream retention remains source-owned.",
            "effect": "none"}


def journal_summary(path, expected_sha256=None):
    """Explicit selected journal read through its original hash-chain validator.

    Imported data payloads, paths and bodies are omitted. Unknown event kinds
    remain journal kinds, never guessed synchronization or chat outcomes.
    """
    report = inspect_journal(path)
    require(expected_sha256 is None or report["source_sha256"] == expected_sha256, "Journal changed; inspect again.")
    return {"source_sha256": report["source_sha256"], "valid": report["valid"],
            "coverage": "complete" if report["valid"] else "verified_prefix_only",
            "error": report["error"], "clean_end": report["clean_end"],
            "events": [{"seq": r["seq"], "kind": r["kind"], "at": r["utc"], "evidence_sha256": r["sha256"]} for r in report["verified_records"]],
            "replay_allowed": False, "effect": "none"}


def fetch_detail(context, resource_id, root, *, requested=False, authorized=False):
    require(requested is True and authorized is True, "Full content requires an explicit authorized local request.")
    doc = validate_context(context)
    resource = next((r for r in doc.get("resources", []) if r["id"] == resource_id), None)
    require(resource is not None and resource["access"] == "local_selected", "Detail resource is unavailable.")
    source = next(s for s in doc["sources"] if s["id"] == resource["source_id"])
    selected_root = bound_root(root, source.get("binding"))
    require(selected_root is not None and source["availability"] == "available" and
            resource["relative"] == source["locator"], "Detail has no accepted selected-root binding.")
    kind = resource.get("content_type", "text")
    if kind == "text":
        value = selected_text(selected_root, resource["relative"], source["sha256"])
    else:
        value = selected_bytes(selected_root, resource["relative"], source["sha256"],
                               2 * 1024 * 1024 if kind == "conversation" else 16 * 1024 * 1024)
        if kind == "conversation":
            projection = json_value(value.pop("data"))
            require(type(projection) is dict and projection.get("kind") == "GameToolsConversationProjection" and
                    projection.get("schema_version") == 1, "Unsupported conversation projection; use a reviewed source adapter.")
            require(projection.get("coverage") in {"visible_messages", "selected_messages", "source_export"}, "Conversation coverage is required.")
            messages = projection.get("messages")
            require(type(messages) is list and len(messages) <= 4096, "Invalid bounded conversation messages.")
            for message in messages:
                require(type(message) is dict and message.get("role") in {"user", "assistant", "system", "developer", "tool", "unknown"} and
                        type(message.get("text")) is str, "Invalid conversation message.")
            value.update(conversation=projection, content="\n\n".join(m["role"] + ":\n" + m["text"] for m in messages),
                         coverage=projection["coverage"], native_chat_identity="not_imported")
        else:
            value["content"] = f"Attachment read in memory: {value['bytes']} bytes; SHA-256 {value['sha256']}. No application was launched."
    return {**value, "content_type": kind, "resource_id": resource_id, "persistence": "none", "effect": "read_only"}
