"""Explicit local read-only front door; does not inspect or configure Codex."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from game_system_control import VERSION
from game_system_control.contracts import ContextError
from game_system_control.explorer import build_view
from game_system_control.inventory import load_context
from game_system_control.overview import overview, journal_summary
from game_system_control.preflight import check_request

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples/system-control/context.example.json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("explore", "preflight", "overview", "journal", "gui"))
    parser.add_argument("--context", type=Path, default=EXAMPLE)
    parser.add_argument("--root", type=Path, help="Explicit local source root; default: context file's directory")
    parser.add_argument("--scope")
    parser.add_argument("--query", default="")
    parser.add_argument("--draft", help="Read-only draft text; never submitted")
    parser.add_argument("--journal", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.mode == "journal":
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
            context = load_context(args.context)
            source_root = args.root or args.context.absolute().parent
            view = build_view(context, source_root, args.scope, args.query)
            if args.mode == "preflight":
                result = check_request(args.draft or "", view)
            elif args.mode == "overview":
                from game_system_control.inventory import check_sources
                result = overview(check_sources(context, source_root))
            else:
                result = view
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ContextError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "effect": "none"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
