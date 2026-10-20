"""Explicit local workspace/checkpoint front door; no native-state or network API."""
import argparse
import json
from pathlib import Path
import sys
import time

from GameToolUserData import _decode, _read, UserDataError
from GameToolJournal import JournalError
from game_mod_ops.safety import ModError, local_lock
from game_system_control.contracts import ContextError, require
from game_system_control.vault import VaultRegistry, volume_identity
from game_system_control.policy import PolicyStore, evaluate, policy_revision
from game_system_control.access import AccessStore


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("volume", "vault-create", "vault-attach", "vault-status", "vault-rebind", "route", "place",
                        "checkpoint-preview", "checkpoint-publish", "checkpoint-inspect", "checkpoint-restore-preview", "checkpoint-restore", "checkpoint-inspect-restore",
                        "checkpoint-package-preview", "checkpoint-package-publish", "checkpoint-receive-preview", "checkpoint-receive", "checkpoint-recovery-preview",
                        "checkpoint-rollback-preview",
                        "policy-create", "policy-status", "policy-preview", "policy-ack-preview", "policy-rollback-preview", "policy-commit", "policy-check",
                        "policy-upgrade-preview", "policy-stage-preview", "policy-restage-preview", "policy-context-notice",
                        "windows-account-status", "access-windows-create", "access-create", "access-status", "access-preview", "access-commit", "access-check", "stop", "resume", "view-context", "report"))
    parser.add_argument("--state", type=Path)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--workspace", default="workspace")
    parser.add_argument("--project", default="project")
    parser.add_argument("--account", default="local-account")
    parser.add_argument("--device", default="local-device")
    parser.add_argument("--vault-id")
    parser.add_argument("--class", dest="content_class")
    parser.add_argument("--relative")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--source-sha256")
    parser.add_argument("--expected-revision")
    parser.add_argument("--input", type=Path, help="Explicit private proposal/request JSON")
    parser.add_argument("--accept", help="Digest of the deliberately accepted preview/stop marker")
    parser.add_argument("--policy-state", type=Path)
    parser.add_argument("--access-state", type=Path)
    args = parser.parse_args(argv)
    try:
        data = _decode(_read(args.input, 2 * 1024 * 1024 if args.mode.startswith("checkpoint-") else 128 * 1024)[0]) if args.input else None
        now = time.time()
        if args.mode == "windows-account-status":
            from game_system_control.windows_account import availability
            result = availability()
        elif args.mode == "volume":
            require(args.root is not None, "Select --root."); result = volume_identity(args.root)
        else:
            require(args.state is not None, "Select --state outside Codex/OneDrive.")
            if args.mode in {"view-context", "report"}:
                from game_system_control.workspace_view import workspace_context
                result = workspace_context(args.state)
                if args.mode == "report":
                    from game_system_control.report import accessible_report
                    print(accessible_report(result, args.state)); return 0
            elif args.mode.startswith("checkpoint-"):
                require(args.policy_state is not None and args.access_state is not None and args.vault_id is not None and type(data) is dict,
                        "Checkpoint operations require existing local bindings, policy, access, vault identity and a private actor request.")
                from game_system_control.checkpoints import CheckpointService
                service = CheckpointService(VaultRegistry(args.state), PolicyStore(args.policy_state), AccessStore(args.access_state), data.get("actor"), args.vault_id)
                if args.mode == "checkpoint-preview":
                    result = service.preview_seed(data["selection"], data["destination"], data["operation_id"])
                elif args.mode == "checkpoint-publish":
                    result = service.publish_seed(data["plan"], args.accept)
                elif args.mode == "checkpoint-inspect":
                    result = service.inspect(args.relative, parent_sources=data.get("parent_sources", []))
                elif args.mode == "checkpoint-restore-preview":
                    result = service.preview_reconstruction(data["source"], data["destination"], data["operation_id"], data["package_id"], parent_sources=data.get("parent_sources", []))
                elif args.mode == "checkpoint-restore":
                    result = service.reconstruct(data["plan"], args.accept)
                elif args.mode == "checkpoint-package-preview":
                    result = service.preview_checkpoint(data["selection"], data["destination"], data["operation_id"], parent=data.get("parent"), parent_sources=data.get("parent_sources", []), representation=data["representation"], extensions=data.get("extensions"))
                elif args.mode == "checkpoint-package-publish":
                    result = service.publish_checkpoint(data["plan"], args.accept)
                elif args.mode == "checkpoint-receive-preview":
                    result = service.preview_receive(data["source"], data["destination"], data["operation_id"], data["package_id"], parent_sources=data.get("parent_sources", []))
                elif args.mode == "checkpoint-receive":
                    result = service.receive(data["plan"], args.accept)
                elif args.mode in {"checkpoint-recovery-preview", "checkpoint-rollback-preview"}:
                    result = service.preview_recovery(data["source"], data["incomplete"], data["selection"], data["destination"], data["operation_id"], data["package_id"], parent_sources=data.get("parent_sources", []), rollback=args.mode == "checkpoint-rollback-preview")
                else:
                    result = service.inspect_reconstruction(args.relative)
            elif args.mode == "vault-create":
                require(args.root is not None, "Select a new --root on a non-system volume.")
                registry = VaultRegistry.create(args.state)
                registry.enroll(args.root, args.workspace, registry.state.snapshot()["revision"])
                result = registry.inspect(registry.state.snapshot()["body"]["vaults"][0]["marker"]["vault_id"])
            elif args.mode in {"vault-attach", "vault-status", "vault-rebind", "route", "place"}:
                registry = VaultRegistry(args.state)
                if args.mode == "vault-attach":
                    if not args.state.exists(): registry = VaultRegistry.create(args.state)
                    require(args.root is not None, "Select an existing vault root.")
                    result = registry.attach(args.root, args.expected_revision or registry.state.snapshot()["revision"])
                elif args.mode == "vault-status": result = registry.inspect(args.vault_id)
                elif args.mode == "vault-rebind":
                    require(args.root is not None, "Select the relocated root.")
                    result = registry.rebind(args.vault_id, args.root, args.expected_revision)
                elif args.mode == "route": result = {"local_path": str(registry.route(args.vault_id, args.project, args.content_class, args.relative)), "effect": "none"}
                else:
                    require(args.policy_state is not None and args.access_state is not None and type(data) is dict, "Placement requires selected local policy, authorization and an explicit scoped request.")
                    access = AccessStore(args.access_state)
                    request = data.get("authorization", {})
                    require(request.get("capability") == "managed.write" and request.get("storage_id") == args.vault_id and request.get("project_id") == args.project and
                            request.get("content_class") == args.content_class and access.authorize(request, now=now)["allowed"], "Managed placement is not locally authorized.")
                    policy = PolicyStore(args.policy_state).snapshot()["body"]
                    decision = evaluate(policy, data.get("policy", {}), active_turn=True, now=now)
                    require(all(data["policy"].get(k) == v for k, v in {"account_id":request["account_id"], "workspace_id":request["workspace_id"], "project_id":args.project,
                            "destination_device":request["device_id"], "capability":"managed.write", "content_class":args.content_class}.items()), "Policy and authorization scopes differ.")
                    require(decision["controls"]["adoption"] and request.get("policy_revision") == decision["policy_revision"], "Local file adoption is disabled or the policy changed.")
                    def recheck():
                        require(access.authorize(request, now=time.time())["allowed"], "Local stop, enrollment or authorization changed before publication.")
                        require(policy_revision(PolicyStore(args.policy_state).snapshot()["body"]) == decision["policy_revision"], "Policy changed before publication.")
                    require(not args.policy_state.samefile(args.access_state) and not args.state.samefile(args.access_state) and not args.state.samefile(args.policy_state), "Bindings, policy and access need separate local stores.")
                    with local_lock(args.access_state, ".workspace-state.lock"), local_lock(args.policy_state, ".workspace-state.lock"), local_lock(args.state, ".workspace-state.lock"):
                        recheck()
                        result = registry.place(args.vault_id, args.project, args.content_class, args.relative, args.source, args.source_sha256, before_publish=recheck)
            elif args.mode.startswith("policy-"):
                policy = PolicyStore.create(args.state) if args.mode == "policy-create" else PolicyStore(args.state)
                if args.mode in {"policy-create", "policy-status"}: result = policy.snapshot()
                elif args.mode == "policy-preview": result = policy.propose_rule(data)
                elif args.mode == "policy-ack-preview": result = policy.acknowledge_central(data["rule_id"])
                elif args.mode == "policy-rollback-preview": result = policy.rollback_rule(data["rule_id"], data["historical_revision"])
                elif args.mode == "policy-commit": result = policy.accept(data, args.accept)
                elif args.mode == "policy-upgrade-preview": result = policy.propose_revision_upgrade()
                elif args.mode == "policy-stage-preview": result = policy.stage_context(data["reference_id"], data["source_sha256"], data["depth"])
                elif args.mode == "policy-restage-preview": result = policy.restage_context(data["reference_id"], data["source_sha256"], data["depth"])
                elif args.mode == "policy-context-notice": result = policy.context_notice(data["reference_id"], data["policy_revision"], active_turn=data.get("active_turn", True), boundary=data.get("boundary", "unobserved"))
                else: result = evaluate(policy.snapshot()["body"], data["request"], active_turn=data.get("active_turn", True), boundary=data.get("boundary", "unobserved"),
                                       event=data.get("event", "manual"), now=now, last_fire=data.get("last_fire"), last_change=data.get("last_change"))
            else:
                access = AccessStore.create(args.state, args.account, args.device, args.project, workspace_id=args.workspace, now=now,
                                            windows_sign_in=args.mode == "access-windows-create") if args.mode in {"access-create", "access-windows-create"} else AccessStore(args.state)
                if args.mode in {"access-create", "access-windows-create", "access-status"}: result = access.snapshot()
                elif args.mode == "access-preview": result = access.propose_change(data["actor"], data["action"], data["values"], now=now)
                elif args.mode == "access-commit": result = access.accept(data["actor"], data["proposal"], args.accept, now=now)
                elif args.mode == "access-check": result = access.authorize(data, now=now)
                elif args.mode == "stop": result = access.stop_local()
                else: result = access.resume_local(data["actor"], args.accept, now=now)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (ContextError, UserDataError, ModError, JournalError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc), "automatic_retry": False, "codex_changed": False}), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
