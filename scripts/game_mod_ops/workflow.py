"""Immutable local jobs and manager staging; caller-initiated work only."""
from __future__ import annotations
import os
import time
import uuid
from pathlib import Path
from threading import Event
from .archive import inspect_zip, stage_zip, tree_audit
from .managers import inspect_archive
from .network import Http, Budget, resolve
from .recipes import validate_plan
from .safety import (ModError, require, read_json, json_new, no_links, contained,
                     local_lock, digest, copy_new, slug, object_hash)

STOP_STATES = {"ACCESS_DENIED", "HASH_MISMATCH", "UPSTREAM_CHANGED", "NETWORK_UNCERTAIN", "HTTP_FAILED",
               "RATE_LIMITED", "SOURCE_CHANGED", "DOWNLOADING", "STAGING", "INSTALLING", "ROLLING_BACK",
               "INCOMPLETE_DOWNLOAD", "BUDGET_EXCEEDED", "SIZE_LIMIT", "TIME_LIMIT", "CANCELLED", "INVALID_ZIP",
               "UNKNOWN_EFFECTS", "CONCURRENT_CHANGE", "ZIP_COLLISION", "PARTIAL_REVIEW_REQUIRED"}


def default_data() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "GameToolHub" / "mod-workflows"
    return Path.home() / ".local" / "share" / "GameToolHub" / "mod-workflows"


class Job:
    """Does not share or overwrite Hub tools.json, overlay groups, native profiles, or saves."""
    def __init__(self, path: Path):
        self.path = no_links(path)
        self.plan = validate_plan(read_json(self.path / "plan.json"))
        self.items = {i["id"]: i for i in self.plan["items"]}
    @classmethod
    def create(cls, root: Path, plan: dict):
        validate_plan(plan)
        root = no_links(root)
        path = root / "jobs" / (time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:12])
        path.mkdir(parents=True, exist_ok=False)
        (path / "events").mkdir()
        json_new(path / "plan.json", plan)
        return cls(path)
    def events(self) -> list[dict]:
        events = []
        for p in sorted((self.path / "events").glob("*.json")):
            e = read_json(p)
            require(p.name == ("%06d.json" % (len(events)+1)) and e.get("seq") == len(events) + 1 and e.get("plan_sha256") == self.plan["plan_sha256"],
                    "JOURNAL_CORRUPT", "Job journal has a gap or belongs to a different plan; stop for reconciliation.")
            events.append(e)
        return events
    def event(self, item: str, status: str, **data) -> dict:
        require(item in self.items, "UNKNOWN_ITEM", "Item is not in this job.")
        events = self.events()
        e = {"seq": len(events) + 1, "item_id": item, "status": status,
             "timestamp_unix": time.time(), "plan_sha256": self.plan["plan_sha256"], **data}
        json_new(self.path / "events" / ("%06d.json" % e["seq"]), e)
        return e
    def latest(self, item: str) -> dict:
        for e in reversed(self.events()):
            if e["item_id"] == item:
                return e
        return {"status": "PLANNED", "item_id": item}
    def checkpoint(self, item: str, status: str) -> dict | None:
        for e in reversed(self.events()):
            if e["item_id"] == item and e["status"] == status:
                return e
        return None
    def item(self, item_id: str) -> dict:
        require(item_id in self.items, "UNKNOWN_ITEM", "Item is not selected in this job.")
        return self.items[item_id]
    def reconcile_gate(self, item_id: str):
        last = self.latest(item_id)
        require(last["status"] in {"PLANNED", "WAITING_NEXUS_AUTH", "WAITING_MANUAL_DOWNLOAD",
                "WAITING_USER_DOWNLOAD", "FILE_PIN_REQUIRED", "ACQUIRED", "STAGED_NOT_INSTALLED",
                "FILES_INSTALLED_RUNTIME_UNVERIFIED"}, "RECONCILIATION_REQUIRED",
                "This item stopped or has an unfinished intent. Inspect its existing effects; automatic resubmission is forbidden.")
    def acquired(self, item_id: str) -> tuple[Path, dict]:
        e = self.checkpoint(item_id, "ACQUIRED")
        require(e is not None, "NOT_DOWNLOADED", "Acquire or import this archive first.")
        path = contained(self.path, e["archive"])
        require(digest(path) == e["sha256"], "HASH_MISMATCH", "Stored archive no longer matches its receipt.")
        return path, e
    def summary(self) -> dict:
        result = []
        for ident in self.items:
            last = self.latest(ident)
            ac = self.checkpoint(ident, "ACQUIRED")
            result.append({"id": ident, "name": self.items[ident]["name"], "status": last["status"],
                           "message": last.get("message"), "sha256": ac.get("sha256") if ac else None,
                           "integrity": ac.get("integrity") if ac else None})
        return {"schema_version": 1, "job_id": self.path.name, "game_id": self.plan["game_id"],
                "plan_sha256": self.plan["plan_sha256"], "items": result,
                "runtime_verification": "not_performed", "source": "local_operation_journal"}


def acquire(job: Job, *, allow_network: bool = False, budget: Budget | None = None,
            nexus_key: str | None = None, nxm: dict | None = None, cancel: Event | None = None,
            http: Http | None = None) -> dict:
    require(allow_network, "NETWORK_NOT_AUTHORIZED", "Downloading needs the explicit allow-network action.")
    http = http or Http(budget, cancel)
    stopped_providers = {job.items[e["item_id"]]["source"]["kind"] for e in job.events()
                         if e["status"] in {"ACCESS_DENIED", "RATE_LIMITED", "AUTH_REDIRECT_BLOCKED"}}
    with local_lock(job.path):
        for ident, item in job.items.items():
            if cancel and cancel.is_set():
                break
            if job.checkpoint(ident, "ACQUIRED"):
                job.acquired(ident)  # Verify rather than fetch a second copy.
                continue
            last = job.latest(ident)
            if last["status"] not in {"PLANNED", "WAITING_NEXUS_AUTH", "WAITING_USER_DOWNLOAD", "WAITING_MANUAL_DOWNLOAD", "FILE_PIN_REQUIRED"}:
                continue  # No implicit retry after a previous failed/unfinished request.
            provider = item["source"]["kind"]
            if provider in stopped_providers:
                job.event(ident, "PROVIDER_PAUSED", message="Another item encountered an access or rate-limit failure on this provider.")
                continue
            try:
                # Authorization and missing-input waits happen before a network intent is persisted.
                if provider == "nexus" and not nexus_key:
                    job.event(ident, "WAITING_NEXUS_AUTH", message="Supply Nexus authorization locally or import a manual download.")
                    continue
                if provider == "manual":
                    job.event(ident, "WAITING_MANUAL_DOWNLOAD", message="Use this item's official page, then import its original archive.")
                    continue
                job.event(ident, "DOWNLOADING")
                url, family, expected, identity = resolve(item, http, nexus_key, (nxm or {}).get(ident))
                path = contained(job.path, "downloads/" + slug(ident) + ".zip")
                receipt = http.download(url, family, path, item["max_download_bytes"], expected)
                inspected = inspect_archive(path,item,job.plan)
                job.event(ident, "ACQUIRED", archive=path.relative_to(job.path).as_posix(),
                          inspected=inspected, source_identity=identity, **receipt)
            except ModError as e:
                job.event(ident, e.code, message=e.message)
                if e.code in {"ACCESS_DENIED", "RATE_LIMITED"}:
                    stopped_providers.add(provider)
                if e.code in {"BUDGET_EXCEEDED", "REQUEST_LIMIT", "TIME_LIMIT", "CANCELLED"}:
                    break
            except Exception:
                job.event(ident, "UNKNOWN_EFFECTS", message="Unexpected I/O or provider response; retained state needs inspection before any retry.")
                break
    return job.summary()


def import_archive(job: Job, item_id: str, source: Path, *, confirmed_source: bool = False) -> dict:
    require(confirmed_source, "SOURCE_CONFIRMATION_REQUIRED", "Confirm that this original archive came from the selected author's official download.")
    item = job.item(item_id)
    with local_lock(job.path):
        job.reconcile_gate(item_id)
        if job.checkpoint(item_id, "ACQUIRED"):
            current, _ = job.acquired(item_id)
            require(digest(current) == digest(source), "ALREADY_DIFFERENT", "A different archive is already attached. Create a separately reviewed job.")
            return job.summary()
        require(no_links(source).stat().st_size <= item["max_download_bytes"], "SIZE_LIMIT", "Archive exceeds this recipe's item size limit.")
        ins = inspect_archive(source,item,job.plan)
        sha = ins["archive_sha256"]
        require(not item.get("sha256") or item["sha256"] == sha, "HASH_MISMATCH", "Imported archive differs from the pinned digest.")
        dest = contained(job.path, "downloads/" + slug(item_id) + ".zip")
        job.event(item_id, "DOWNLOADING", message="Copying an explicitly selected local archive, not using the network.")
        copy_new(source, dest, sha)
        job.event(item_id, "ACQUIRED", archive=dest.relative_to(job.path).as_posix(), sha256=sha,
                  bytes=dest.stat().st_size, inspected=ins, source_identity={"mode": "caller-confirmed-official-download"},
                  integrity="upstream_digest_matched" if item.get("sha256") else "locally_hashed_only")
    return job.summary()


def stage(job: Job, item_id: str) -> dict:
    item = job.item(item_id)
    with local_lock(job.path):
        job.reconcile_gate(item_id)
        archive, receipt = job.acquired(item_id)
        ins = receipt["inspected"]
        dest = contained(job.path, "staged/" + slug(item_id))
        previous = job.checkpoint(item_id, "STAGED_NOT_INSTALLED")
        if previous:
            audit = tree_audit(dest, ins["files"])
            require(audit["status"] == "MATCH", "SOURCE_CHANGED", "Previously staged content changed; it was not replaced.")
            return {"status": "STAGED_NOT_INSTALLED", "reused": True, "stage": str(dest)}
        job.event(item_id, "STAGING")
        result = stage_zip(archive, dest, ins)
        job.event(item_id, result["status"], stage=dest.relative_to(job.path).as_posix(),
                  manifest_sha256=object_hash(ins["files"]))
        return {**result, "stage": str(dest), "warning": "Files are staged privately, not installed, enabled or runtime-tested."}


def nexus_files(item: dict, key: str | None, http: Http | None = None) -> dict:
    require(item["source"]["kind"] == "nexus", "PROVIDER_UNSUPPORTED", "This is not a Nexus item.")
    require(bool(key), "WAITING_NEXUS_AUTH", "Nexus metadata requires an API key held only on this computer.")
    s = item["source"]
    h = http or Http(Budget(max_bytes=4 * 1024 * 1024, max_requests=2, seconds=30))
    data = h.json(f'https://api.nexusmods.com/v1/games/{slug(s["game"])}/mods/{int(s["mod_id"])}/files.json', "nexus-api", key)
    fields = ("file_id", "name", "file_name", "version", "category_name", "size_in_bytes", "uploaded_timestamp")
    return {"item_id": item["id"], "source_game": s["game"], "source_mod_id": s["mod_id"],
            "files": [{k: f.get(k) for k in fields} for f in data.get("files", [])],
            "next_action": "Choose an exact file ID from these metadata and make a new plan. No file was downloaded."}
