#!/usr/bin/env python3
"""Optional Game Tool Hub module entry point; Python 3.10+; standard library only."""
import sys
if sys.version_info < (3, 10):
    raise SystemExit('Python 3.10 or later is required. No runtime or package will be installed automatically.')
from game_mod_ops.cli import main
if __name__ == '__main__':
    raise SystemExit(main())
