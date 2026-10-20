"""Explicit local read-only front door; does not inspect or configure Codex."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from game_system_control import VERSION
from game_system_control.contracts import ContextError
from game_system_control.explorer import build_view
from game_system_control.inventory import load_context, environment_context
from game_system_control.overview import overview, journal_summary
from game_system_control.preflight import check_request

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/system-control/context.example.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("explore", "preflight", "overview", "inventory", "report", "journal", "gui", "build-plan", "build-context", "build-report"))
    parser.add_argument("--context", type=Path, default=EXAMPLE)
    parser.add_argument("--root", type=Path, help="Explicit local source root; default: context file's directory")
    parser.add_argument("--scope")
    parser.add_argument("--query", default="")
    parser.add_argument("--draft", help="Read-only draft text; never submitted")
    parser.add_argument("--intended-outcome", default="")
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--global-root", type=Path, help="Explicit global instruction folder")
    parser.add_argument("--skill-root", type=Path, action="append", default=[], help="Explicit skill folder, one level only; repeatable")
    parser.add_argument("--catalog", type=Path, help="Selected capability declarations JSON")
    parser.add_argument("--cwd", default="", help="Selected project-relative working directory")
    parser.add_argument("--task", help="Optional MCI ID for a bounded build packet")
    args = parser.parse_args(argv)
    try:
        if args.mode.startswith("build-"):
            if args.root is None: raise ContextError("Select --root for the existing plan and source owners.")
            from game_system_control.build_plan import build_packet, build_context
            if args.mode == "build-plan": result = build_packet(args.root, args.task)
            else:
                if args.task: raise ContextError("Task selection applies to build-plan packets; human context/report shows the shared architecture.")
                result = build_context(args.root)
                if args.mode == "build-report":
                    from game_system_control.report import accessible_report
                    print(accessible_report(result, args.root)); return 0
        elif args.mode == "journal":
            if args.journal is None:
                raise ContextError("Select --journal explicitly.")
            result = journal_summary(args.journal)
        elif args.mode == "gui":
            import tkinter as tk
            from GameToolSystemControlPanel import SystemControlPanel
            from GameToolCompactUI import window_bounds
            root = tk.Tk(); root.title("System control center · source preview")
            from GameToolModernUI import apply_theme
            apply_theme(root)
            width, height, minimum_w, minimum_h = window_bounds(root.winfo_screenwidth(), root.winfo_screenheight())
            root.geometry(f"{min(1000, width)}x{min(760, height)}"); root.minsize(minimum_w, minimum_h)
            panel = SystemControlPanel(root, context_path=args.context, source_root=args.root)
            panel.pack(fill="both", expand=True)
            root.mainloop()
            return 0
        else:
            source_root = args.root or args.context.absolute().parent
            if args.mode == "inventory" or args.global_root or args.skill_root or args.catalog:
                if args.root is None:
                    raise ContextError("Select --root for an environment inventory.")
                context, source_root = environment_context(args.root, args.cwd, global_root=args.global_root, skill_roots=args.skill_root, catalog=args.catalog)
            else:
                context = load_context(args.context)
            view = build_view(context, source_root, args.scope, args.query)
            if args.mode == "report":
                from game_system_control.report import accessible_report
                print(accessible_report(context, source_root))
                return 0
            elif args.mode == "preflight":
                result = check_request(args.draft or "", view, args.intended_outcome)
            elif args.mode == "overview":
                from game_system_control.inventory import check_sources
                result = overview(check_sources(context, source_root))
            elif args.mode == "inventory":
                result = context
            else:
                result = view
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ContextError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "effect": "none"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
