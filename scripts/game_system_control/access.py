"""MCI-13 local OS-session enrollment and least-privilege decisions.

This is destination-local configuration, not remote authentication or an ACL
against another process already running as the same OS user. No secrets are
stored here. Cloud/OpenAI sign-in and credential stores remain native owners.
"""
from copy import deepcopy
import math
from pathlib import Path
import time

from GameToolAIContracts import stable_revision
from GameToolUserData import _canonical, _read, _write_new, digest
from game_mod_ops.safety import local_lock
from .contracts import require, identifier, SHA
from .workspace_state import LocalState, principal
from .vault import CLASSES
from . import windows_account

ROLES = {"viewer": {"metadata.read"}, "contributor": {"metadata.read", "managed.read", "managed.write"},
         "operator": {"metadata.read", "operation.propose"},
         "policy_administrator": {"metadata.read", "policy.propose", "enrollment.manage"}}
MAX_ENROLLMENT_SECONDS = 30 * 86400


def clock(value):
    require(type(value) in {int, float} and math.isfinite(value) and value >= 0, "Invalid authorization clock.")
    return value


def validate_access(body):
    require(type(body) is dict and body.get("schema_version") == 1 and body.get("kind") == "GameToolsLocalAccess", "Unsupported local access registry.")
    require(set(body) <= {"schema_version", "kind", "workspace_id", "project_id", "accounts", "devices", "memberships", "storage_permissions", "active_policy_revision", "authentication"}, "Unknown access fields; credentials and imported sign-in receipts are unsupported.")
    identifier(body.get("project_id")); identifier(body.get("workspace_id"))
    mode = body.get("authentication", "local_os_session")
    require(type(mode) is str and mode in {"local_os_session", "windows_hello"}, "Unsupported local sign-in requirement.")
    for key in ("accounts", "devices", "memberships", "storage_permissions"):
        require(type(body.get(key)) is list and len(body[key]) <= 128, "Access registry collection bound exceeded.")
    accounts, devices, memberships, permissions = set(), set(), set(), set()
    for a in body["accounts"]:
        require(type(a) is dict and set(a) == {"id", "provider", "subject_hash"}, "Accounts contain local identity references only.")
        identifier(a.get("id")); require(a["id"] not in accounts, "Duplicate account."); accounts.add(a["id"])
        require(a.get("provider") == "local_os" and a.get("subject_hash") == principal(), "Fresh supported local OS identity is required; provider-account login is not connected.")
    for d in body["devices"]:
        require(type(d) is dict and set(d) == {"id", "account_id", "principal_hash", "status", "generation", "enrolled_at", "expires_at", "last_seen", "online", "policy_ack"}, "Devices contain enrollment metadata only.")
        identifier(d.get("id")); require(d["id"] not in devices and d.get("account_id") in accounts, "Duplicate device or missing account."); devices.add(d["id"])
        require(d.get("status") in {"active", "revoked", "retired"} and type(d.get("generation")) is int and d["generation"] >= 1, "Invalid enrollment lifecycle.")
        require(d.get("principal_hash") == principal(), "Device needs fresh local acceptance; copied peer declarations cannot sign in.")
        require(type(d.get("online")) is bool, "Device report needs explicit availability.")
        clock(d.get("enrolled_at")); clock(d.get("expires_at")); clock(d.get("last_seen"))
        require(d["enrolled_at"] < d["expires_at"] <= d["enrolled_at"] + MAX_ENROLLMENT_SECONDS, "Enrollment lifetime outside bound.")
        require(d.get("policy_ack") is None or type(d["policy_ack"]) is str and SHA.fullmatch(d["policy_ack"]), "Invalid policy acknowledgement.")
    for m in body["memberships"]:
        require(type(m) is dict and set(m) == {"account_id", "project_id", "roles"}, "Membership contains role references only.")
        identifier(m.get("project_id")); key = (m.get("account_id"), m["project_id"])
        require(m["project_id"] == body["project_id"], "Use a separate local registry for another project.")
        require(key[0] in accounts and key not in memberships, "Duplicate membership or missing account."); memberships.add(key)
        require(type(m.get("roles")) is list and bool(m["roles"]) and all(r in ROLES for r in m["roles"]), "Unsupported role.")
    for p in body["storage_permissions"]:
        require(type(p) is dict and set(p) == {"account_id", "project_id", "storage_id", "read", "write"}, "Storage permissions contain scoped grants only.")
        for key in ("storage_id", "project_id"): identifier(p.get(key))
        require(p["project_id"] == body["project_id"], "Storage grant is outside the selected project.")
        key = (p.get("account_id"), p["project_id"], p["storage_id"])
        require(key[0] in accounts and key not in permissions, "Duplicate storage permission or missing account."); permissions.add(key)
        for op in ("read", "write"):
            require(type(p.get(op)) is list and all(c in CLASSES for c in p[op]), "Unsupported storage content class.")
    revision = body.get("active_policy_revision")
    require(revision is None or type(revision) is str and SHA.fullmatch(revision), "Invalid active policy revision.")
    return deepcopy(body)


class AccessStore:
    def __init__(self, root): self.state = LocalState(root, "workspace-access")

    @classmethod
    def create(cls, root, account_id, device_id, project_id, *, now, workspace_id="workspace", windows_sign_in=False):
        for value in (account_id, device_id, project_id, workspace_id): identifier(value)
        clock(now)
        require(type(windows_sign_in) is bool, "Select the explicit Windows sign-in mode.")
        root = LocalState(root, "workspace-access").root
        require(root.parent.is_dir() and not root.exists(), "Select a new local access directory under an existing private parent.")
        if windows_sign_in:
            scope = windows_account.operation_scope(root, "create", {"account": account_id, "device": device_id, "project": project_id, "workspace": workspace_id})
            started = time.monotonic()
            windows_account.verify(scope).consume(scope)
            now += time.monotonic() - started
        body = {"schema_version": 1, "kind": "GameToolsLocalAccess", "workspace_id": workspace_id, "project_id": project_id,
                "accounts": [{"id": account_id, "provider": "local_os", "subject_hash": principal()}],
                "devices": [{"id": device_id, "account_id": account_id, "principal_hash": principal(), "status": "active",
                             "generation": 1, "enrolled_at": now, "expires_at": now + 3600, "last_seen": now, "online": True, "policy_ack": None}],
                "memberships": [{"account_id": account_id, "project_id": project_id, "roles": ["policy_administrator"]}],
                "storage_permissions": [], "active_policy_revision": None}
        if windows_sign_in: body["authentication"] = "windows_hello"
        validate_access(body); LocalState.create(root, "workspace-access", body)
        return cls(root)

    def snapshot(self):
        row = self.state.snapshot(); validate_access(row["body"]); return row

    def authorize(self, request, *, now, _ignore_stop=False):
        clock(now)
        require(type(request) is dict, "Authorization needs a scoped request.")
        for key in ("account_id", "device_id", "project_id", "capability"): identifier(request.get(key))
        if not _ignore_stop and ((self.state.root/"LOCAL-STOP.json").exists() or (self.state.root/"LOCAL-STOP.json").is_symlink()):
            return {"allowed": False, "reason": "local_stop", "effect": "none"}
        body = self.snapshot()["body"]
        if request.get("workspace_id") != body["workspace_id"] or request["project_id"] != body["project_id"]:
            return {"allowed": False, "reason": "workspace_or_project_scope_denied", "effect": "none"}
        device = next((d for d in body["devices"] if d["id"] == request["device_id"] and d["account_id"] == request["account_id"]), None)
        reason = None
        if device is None or device["status"] != "active": reason = "not_enrolled_or_revoked"
        elif type(request.get("generation")) is not int or request["generation"] != device["generation"]: reason = "stale_writer_generation"
        elif not device["enrolled_at"] <= now < device["expires_at"]: reason = "expired_or_clock_drift"
        membership = next((m for m in body["memberships"] if m["account_id"] == request["account_id"] and m["project_id"] == request["project_id"]), None)
        capabilities = set().union(*(ROLES[r] for r in membership["roles"])) if membership else set()
        if reason is None and request["capability"] not in capabilities: reason = "role_denied"
        if reason is None and request["capability"] != "metadata.read" and (not device["online"] or not 0 <= now - device["last_seen"] <= 300): reason = "offline_or_stale_device"
        if reason is None and request["capability"] in {"managed.read", "managed.write", "operation.propose"}:
            revision = body["active_policy_revision"]
            if revision is None or device["policy_ack"] != revision or request.get("policy_revision") != revision: reason = "policy_ack_required"
        if reason is None and request["capability"] in {"managed.read", "managed.write"}:
            permission = next((p for p in body["storage_permissions"] if (p["account_id"], p["project_id"], p["storage_id"]) ==
                               (request["account_id"], request["project_id"], request.get("storage_id"))), None)
            op = "read" if request["capability"] == "managed.read" else "write"
            if permission is None or request.get("content_class") not in permission[op]: reason = "storage_scope_denied"
        return {"allowed": reason is None, "reason": reason or "local_os_session_and_scopes_checked", "capability": request["capability"],
                "effect": "none", "remote_authentication": "not_connected", "execution_approval": "existing_local_owner_required",
                "authentication_requirement": body.get("authentication", "local_os_session")}

    def propose_change(self, actor, action, values, *, now):
        require(actor.get("capability") == "enrollment.manage" and self.authorize(actor, now=now)["allowed"], "Local policy-administrator approval is required.")
        base = self.snapshot(); body = deepcopy(base["body"])
        require(type(values) is dict, "An enrollment change needs values.")
        require(values.get("project_id", body["project_id"]) == body["project_id"], "Local administration is limited to its selected project.")
        if action == "account":
            ident = identifier(values.get("account_id"))
            require(not any(a["id"] == ident for a in body["accounts"]), "Account identity already exists.")
            require(values.get("provider", "local_os") == "local_os", "Provider-account sign-in is not connected; credentials cannot be transplanted.")
            body["accounts"].append({"id": ident, "provider": "local_os", "subject_hash": principal()})
        elif action == "enroll":
            ident = identifier(values.get("device_id")); lifetime = values.get("seconds", 3600)
            require(type(lifetime) is int and 1 <= lifetime <= MAX_ENROLLMENT_SECONDS, "Invalid enrollment lifetime.")
            require(not any(d["id"] == ident for d in body["devices"]), "Device identities cannot be reused, including retired identities.")
            require(values.get("provider", "local_os") == "local_os", "Fresh provider-specific sign-in is unavailable; no credentials may be transplanted.")
            account = values.get("account_id", actor["account_id"])
            require(any(a["id"] == account for a in body["accounts"]), "Account must be independently enrolled.")
            body["devices"].append({"id": ident, "account_id": account, "principal_hash": principal(), "status": "active", "generation": 1,
                                    "enrolled_at": now, "expires_at": now + lifetime, "last_seen": now, "online": True, "policy_ack": None})
        elif action in {"revoke", "retire", "renew", "heartbeat", "acknowledge"}:
            device = next((d for d in body["devices"] if d["id"] == values.get("device_id")), None)
            require(device is not None and device["status"] != "retired", "Unknown/retired device.")
            if action in {"revoke", "retire"}:
                device.update(status="revoked" if action == "revoke" else "retired", generation=device["generation"] + 1, policy_ack=None, online=False)
            elif action == "renew":
                lifetime = values.get("seconds", 3600)
                require(device["status"] == "active" and type(lifetime) is int and 1 <= lifetime <= MAX_ENROLLMENT_SECONDS, "Invalid active enrollment renewal.")
                device.update(generation=device["generation"] + 1, enrolled_at=now, expires_at=now + lifetime, last_seen=now, online=True, policy_ack=None)
            elif action == "heartbeat":
                require(device["status"] == "active" and type(values.get("online")) is bool, "Only active devices can report availability.")
                device.update(last_seen=now, online=values["online"])
            else:
                require(device["status"] == "active" and body["active_policy_revision"] is not None and values.get("policy_revision") == body["active_policy_revision"], "Acknowledge the current selected policy revision.")
                device["policy_ack"] = body["active_policy_revision"]
        elif action == "membership":
            account, project = values.get("account_id"), identifier(values.get("project_id"))
            require(any(a["id"] == account for a in body["accounts"]), "Unknown account.")
            body["memberships"] = [m for m in body["memberships"] if (m["account_id"], m["project_id"]) != (account, project)] + [{"account_id": account, "project_id": project, "roles": values.get("roles")}]
        elif action == "storage":
            row = {k: values.get(k) for k in ("account_id", "project_id", "storage_id", "read", "write")}
            body["storage_permissions"] = [p for p in body["storage_permissions"] if (p["account_id"], p["project_id"], p["storage_id"]) !=
                                           (row["account_id"], row["project_id"], row["storage_id"])] + [row]
        elif action == "pin_policy":
            body["active_policy_revision"] = values.get("policy_revision")
        elif action == "require_windows_sign_in":
            # Preview is inert. Accept always invokes the native verifier and
            # pins the full proposal, including this one-way mode change.
            body["authentication"] = "windows_hello"
        else:
            require(False, "Unknown named enrollment operation; arbitrary commands are unsupported.")
        validate_access(body)
        return self.state.propose(body, base["revision"])

    def accept(self, actor, proposal, accepted_sha256, *, now):
        require(actor.get("capability") == "enrollment.manage" and self.authorize(actor, now=now)["allowed"], "Revalidate local administration before applying a change.")
        validate_access(proposal["body"])
        base = self.snapshot()
        secure = base["body"].get("authentication") == "windows_hello"
        require(not secure or proposal["body"].get("authentication") == "windows_hello", "Windows sign-in cannot be downgraded by a proposed revision.")
        if secure or proposal["body"].get("authentication") == "windows_hello":
            require(set(proposal) == {"kind", "expected_revision", "body", "preview_sha256"} and proposal.get("kind") == self.state.kind,
                    "Select a valid access preview before sign-in.")
            require(proposal["expected_revision"] == base["revision"], "Access revision changed; prepare a new preview before sign-in.")
            require(proposal["preview_sha256"] == accepted_sha256 == digest(_canonical({k: proposal[k] for k in ("kind", "expected_revision", "body")})), "Accept the exact selected preview before sign-in.")
            scope = windows_account.operation_scope(self.state.root, "commit", {"actor": actor, "proposal": proposal, "accept": accepted_sha256})
            started = time.monotonic()
            windows_account.verify(scope).consume(scope)
            now += time.monotonic() - started
            require(self.authorize(actor, now=now)["allowed"], "Local authorization expired, changed or stopped during Windows verification.")
        return self.state.commit(proposal, accepted_sha256)

    def stop_local(self):
        # Deliberately independent of registry decoding, enrollment, policy and
        # network availability. Existing markers are never replaced.
        path = self.state.root/"LOCAL-STOP.json"
        require(self.state.root.is_dir(), "Select the existing local control directory.")
        if not path.exists(): _write_new(path, _canonical({"kind": "local_stop", "owner_principal": principal()}))
        return {"state": "LOCAL_STOPPED", "stop_sha256": digest(_read(path)[0]), "remote_action": False}

    def resume_local(self, actor, expected_stop_sha256, *, now):
        require(actor.get("capability") == "enrollment.manage" and self.authorize(actor, now=now, _ignore_stop=True)["allowed"], "Fresh local administrator approval is required to resume.")
        base = self.snapshot()
        require(digest(_read(self.state.root/"LOCAL-STOP.json")[0]) == expected_stop_sha256, "Inspect the exact local stop marker before sign-in.")
        if base["body"].get("authentication") == "windows_hello":
            scope = windows_account.operation_scope(self.state.root, "resume", {"actor": actor, "revision": base["revision"], "stop": expected_stop_sha256})
            started = time.monotonic()
            windows_account.verify(scope).consume(scope)
            now += time.monotonic() - started
            require(self.snapshot()["revision"] == base["revision"] and self.authorize(actor, now=now, _ignore_stop=True)["allowed"], "Local authorization changed or expired during Windows verification.")
        with local_lock(self.state.root, ".workspace-state.lock"):
            require(self.snapshot()["revision"] == base["revision"] and self.authorize(actor, now=now, _ignore_stop=True)["allowed"], "Revalidate current local authorization to resume.")
            path = self.state.root/"LOCAL-STOP.json"
            raw, before = _read(path)
            require(digest(raw) == expected_stop_sha256, "Local stop marker changed; inspect again.")
            require(path.stat().st_ino == before.st_ino, "Local stop identity changed.")
            path.unlink()
        return {"state": "LOCAL_RESUMED", "remote_action": False}
