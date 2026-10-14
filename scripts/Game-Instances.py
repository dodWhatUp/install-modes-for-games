"""Local operator CLI for opaque game-instance metadata and read-only UMM inspection.

AI tools do not expose registration or filesystem paths.  This CLI never writes
inside a game or manager profile; register writes only one private metadata
record beneath the selected Game Tools data root.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from GameToolGameWorkspaces import GameWorkspaces
from GameToolPlanning import PlanningService
from game_mod_ops.safety import ModError
from game_mod_ops.workflow import default_data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=default_data().parent)
    sub = parser.add_subparsers(dest="action", required=True)

    listing = sub.add_parser("list")
    listing.add_argument("--game-id")
    listing.add_argument("--limit", type=int, default=50)

    register = sub.add_parser("register")
    register.add_argument("--instance-id", required=True)
    register.add_argument("--game-id", required=True)
    register.add_argument("--game-dir", type=Path, required=True)
    register.add_argument("--store", choices=["steam", "gog", "epic", "microsoft", "other", "unknown"], default="unknown")
    register.add_argument("--build", default="unknown")
    register.add_argument("--profile")
    register.add_argument("--confirm", action="store_true")

    inspect = sub.add_parser("inspect")
    inspect.add_argument("--instance-id", required=True)
    inspect.add_argument("--game-id")

    plan = sub.add_parser("plan")
    plan.add_argument("--game-id", required=True)
    plan.add_argument("--goal", choices=sorted(__import__("GameToolPlanning").GOALS), required=True)
    plan.add_argument("--instance-id")
    plan.add_argument("--mode")
    plan.add_argument("--selected", action="append")

    conflicts = sub.add_parser("conflicts")
    conflicts.add_argument("--game-id", required=True)
    conflicts.add_argument("--instance-id")
    conflicts.add_argument("--mode")
    conflicts.add_argument("--selected", action="append")

    args = parser.parse_args(argv)
    workspaces = GameWorkspaces(args.data_dir)
    planning = PlanningService(workspaces)
    try:
        if args.action == "list":
            result = planning.list_instances(args.game_id, args.limit)
        elif args.action == "register":
            result = workspaces.instances.register_local(
                instance_id=args.instance_id,
                game_id=args.game_id,
                game_dir=args.game_dir,
                store=args.store,
                build=args.build,
                profile=args.profile,
                confirmed=args.confirm,
            )
        elif args.action == "inspect":
            result = planning.inspect_instance(args.instance_id, args.game_id)
        elif args.action == "plan":
            result = planning.goal_plan(
                args.game_id, args.goal, instance_id=args.instance_id,
                mode=args.mode, selected=args.selected,
            )
        else:
            result = planning.conflict_graph(
                args.game_id, instance_id=args.instance_id,
                mode=args.mode, selected=args.selected,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (ModError, ValueError, OSError, TypeError, KeyError) as error:
        print(json.dumps({
            "status": getattr(error, "code", "LOCAL_READ_REFUSED"),
            "message": "Inspect the exact registered scope; no automatic retry or alternate path was used.",
        }))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
