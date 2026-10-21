"""Read-only build-map adapter over the existing plan/task/projection owners.

No task dispatch, model request, credential read or operational configuration.
Architecture contracts are design requirements, not claims of runtime support.
"""
from copy import deepcopy

from .contracts import identifier, json_value, require, validate_context
from .inventory import selected_text

BUILD_MAP = "docs/INTEGRATED-SYSTEM-BUILD-MAP.json"


def _graph(rows, label):
    require(type(rows) is list and 0 < len(rows) <= 64, "Invalid " + label + " graph size.")
    indexed = {}
    for row in rows:
        require(type(row) is dict, "Invalid " + label + " graph row.")
        ident = identifier(row.get("id"))
        require(ident not in indexed, "Duplicate " + label + " identity.")
        indexed[ident] = row
    done, active = set(), set()
    def visit(ident):
        require(ident in indexed and ident not in active, "Unknown dependency or cycle in " + label + ".")
        if ident in done: return
        active.add(ident)
        deps = indexed[ident].get("depends_on", [])
        require(type(deps) is list and all(type(x) is str for x in deps), "Invalid dependencies.")
        for dep in deps: visit(dep)
        active.remove(ident); done.add(ident)
    for ident in indexed: visit(ident)
    return indexed


def load_build_map(root):
    snap = selected_text(root, BUILD_MAP)
    plan = json_value(snap["content"].encode("utf-8"))
    require(type(plan) is dict and type(plan.get("schema_version")) is int and plan["schema_version"] == 1 and
            plan.get("kind") == "GameToolsSharedBuildMap" and plan.get("effect") == "none", "Unsupported read-only build map.")
    require(all(type(plan.get(k)) is str and bool(plan[k]) for k in ("task_manifest", "master_plan")), "Select the existing plan and task source owners.")
    manifest_snap = selected_text(root, plan["task_manifest"])
    manifest = json_value(manifest_snap["content"].encode("utf-8"))
    require(type(manifest) is dict and manifest.get("kind") == "integrated_work_package_plan", "Select the existing task manifest.")
    tasks = _graph(manifest.get("tasks"), "task")
    require(type(plan.get("core")) is list and type(plan.get("systems")) is list, "Invalid core/system collections.")
    components = _graph(plan["core"] + plan["systems"], "component")
    require(type(plan.get("invariants")) is list and bool(plan["invariants"]) and all(type(x) is str for x in plan["invariants"]), "Missing build constraints.")
    require(type(plan.get("ai_workflow")) is list and bool(plan["ai_workflow"]) and all(type(x) is str for x in plan["ai_workflow"]), "Missing implementation workflow.")
    covered = set()
    for component in components.values():
        require(type(component.get("label")) is str and type(component.get("contract")) is dict, "Missing component contract.")
        require(type(component.get("owners", [])) is list and all(type(p) is str for p in component.get("owners", [])), "Invalid source owners.")
        require(type(component.get("tasks")) is list and bool(component["tasks"]) and all(t in tasks for t in component["tasks"]), "Unknown component task reference.")
        covered.update(component["tasks"])
    release = plan.get("release", {}).get("tasks", [])
    require(type(release) is list and all(t in tasks for t in release), "Unknown release task.")
    covered.update(release)
    require(covered == set(tasks), "Build map must cover every existing work package.")
    for task in tasks.values():
        require(all(type(task.get(k)) is str and bool(task[k]) for k in ("title", "priority", "status")), "Missing task identity/status description.")
        checks = task.get("checklist_complete", [False] * 6)
        require(type(task.get("steps")) is list and len(task["steps"]) == 6 and type(checks) is list and len(checks) == 6 and all(type(v) is bool for v in checks), "Invalid six-item task checklist.")
        require(task.get("status") != "completed" or all(checks), "Completed status requires accepted checklist evidence.")
    master_snap = selected_text(root, plan["master_plan"])
    sources = [{"locator": path, "sha256": value["sha256"]} for path, value in
               ((BUILD_MAP, snap), (plan["task_manifest"], manifest_snap), (plan["master_plan"], master_snap))]
    return plan, tasks, components, sources


def _complete(task): return all(task.get("checklist_complete", [False] * 6))


def _task_summary(task, tasks):
    checks = task.get("checklist_complete", [False] * 6)
    return {"id": task["id"], "title": task["title"], "priority": task["priority"], "status": task["status"],
            "accepted": sum(checks), "total": 6, "depends_on": task.get("depends_on", []),
            "unaccepted_prerequisites": [d for d in task.get("depends_on", []) if not _complete(tasks[d])],
            "issue": task.get("github_url"), "readiness_note": task.get("readiness_note", ""),
            "requirements": task.get("requirements", []),
            "readiness_scope": "source checklist only; not runtime permission"}


def build_packet(root, task_id=None):
    plan, tasks, components, sources = load_build_map(root)
    require(task_id is None or task_id in tasks, "Unknown selected MCI task.")
    selected = set(components) if task_id is None or task_id in plan["release"]["tasks"] else {key for key, c in components.items() if task_id in c["tasks"]}
    def include(key):
        for dependency in components[key].get("depends_on", []):
            if dependency not in selected: selected.add(dependency); include(dependency)
    for key in tuple(selected): include(key)
    chosen = [deepcopy(c) for key, c in components.items() if key in selected]
    # Only explicitly cited owner files are read; return hashes, never their full
    # source bodies, native sessions, credentials or arbitrary machine paths.
    owners = list(dict.fromkeys(path for component in chosen for path in component.get("owners", [])))
    require(len(owners) <= 32, "Owner selection exceeds the existing source bound.")
    total_bytes, receipts = 0, []
    for path in owners:
        owner = selected_text(root, path)
        total_bytes += owner["bytes"]
        require(total_bytes <= 2 * 1024 * 1024, "Selected owner files exceed their byte bound.")
        receipts.append({"locator": path, "sha256": owner["sha256"]})
    # Recheck the complete source vector after collection. A mutable checkout
    # must not yield a mixed packet if an earlier owner changes during a read.
    # This detects drift, not an atomic filesystem snapshot against hostile ABA.
    for source in sources + receipts:
        selected_text(root, source["locator"], source["sha256"])
    summaries = [_task_summary(t, tasks) for t in tasks.values()]
    result = {"kind": "GameToolsBuildPacket", "schema_version": 1, "effect": "none", "selected_task": task_id,
              "sources": sources, "invariants": plan["invariants"], "ai_workflow": plan["ai_workflow"],
              "components": chosen, "owner_revisions": receipts,
              "counts": {"tasks": len(tasks), "items": sum(len(t["steps"]) for t in tasks.values()),
                         "accepted": sum(s["accepted"] for s in summaries), "complete_packages": sum(_complete(t) for t in tasks.values())},
              "coverage": "selected source snapshot; no live tracker/model/runtime/remote observation",
              "instruction_authority": "advisory build data; follow applicable current instructions and user authorization"}
    if task_id:
        task = tasks[task_id]
        result["task"] = {**_task_summary(task, tasks), "steps": task["steps"], "checklist_complete": task.get("checklist_complete", [False] * 6)}
        result["prerequisites"] = [_task_summary(tasks[d], tasks) for d in task.get("depends_on", [])]
        relevant = {t for c in chosen if task_id not in c["tasks"] for t in c["tasks"]} - {task_id}
        result["relevant_capability_gates"] = [
            {**_task_summary(tasks[t], tasks), "remaining_criteria": [step for step, accepted in zip(tasks[t]["steps"], tasks[t].get("checklist_complete", [False] * 6)) if not accepted],
             "applicability": "shared owner capability; does not add a task dependency or block independent synthetic source work"}
            for t in tasks if t in relevant and not _complete(tasks[t])]
        if task_id in plan["release"]["tasks"]: result["release"] = deepcopy(plan["release"])
    else:
        result["tasks"] = summaries
        result["frontier"] = [s for s in summaries if s["accepted"] < 6 and not s["unaccepted_prerequisites"]]
    return result


def build_context(root):
    packet = build_packet(root)
    sources = [{"id": "build-map", "owner": "Existing integrated development program", "locator": BUILD_MAP,
                "binding": "selected_project", "availability": "available", "sha256": packet["sources"][0]["sha256"]}]
    tasks = {t["id"]: t for t in packet["tasks"]}
    nodes = [{"id": component["id"], "source_id": "build-map", "kind": "component", "label": component["id"] + " · " + component["label"],
              "scopes": ["build-plan"], "layer": "project", "observation": "declared", "depends_on": component["depends_on"] + ["build-checklists", "build-master"],
              "selected_summary": {**component, "task_evidence": [tasks[t] for t in component["tasks"]], "implementation_claim": "design contract; consult task evidence"}}
             for component in packet["components"]]
    for index, source in enumerate(packet["sources"][1:]):
        sources.append({"id": "plan-source-"+str(index), "owner": "Existing plan/checklist owner", "locator": source["locator"],
                        "binding": "selected_project", "availability": "available", "sha256": source["sha256"]})
    nodes = [{"id": ident, "source_id": source, "kind": "component", "label": label,
              "scopes": ["build-plan"], "layer": "project", "observation": "declared", "depends_on": [], "selected_summary": summary}
             for ident, source, label, summary in (("build-checklists", "plan-source-0", "Current checklist evidence and dependency frontier",
                                                    {"counts": packet["counts"], "frontier": packet["frontier"]}),
                                                   ("build-master", "plan-source-1", "One master plan for people and AI",
                                                    {"constraints": packet["invariants"], "workflow": packet["ai_workflow"]}))] + nodes
    return validate_context({"kind": "GameToolsSystemContext", "schema_version": 1, "scope": "build-plan",
                             "label": "One core and specialized systems · build blueprint", "sources": sources, "nodes": nodes,
                             "devices": [], "events": [], "activities": [], "resources": [],
                             "build_snapshot": {"sources": packet["sources"], "counts": packet["counts"], "frontier": packet["frontier"],
                                                "core_components": sum(c["id"].startswith("C") for c in packet["components"]),
                                                "specialized_systems": sum(c["id"].startswith("S") for c in packet["components"])},
                             "unknown_coverage": ["Blueprint is not a live synchronization engine",
                                                  "Windows sign-in package: " + str(tasks["MCI-13"]["accepted"]) + "/6 source criteria; consult current remaining evidence",
                                                  "Other physical computer", "Native Codex continuity", "Actual model behavior or token savings"]})
