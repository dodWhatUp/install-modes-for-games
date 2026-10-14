#!/usr/bin/env python3
import sys
if sys.version_info < (3,10):
    raise SystemExit('Python 3.10+ with tkinter is required; no runtime will be installed automatically.')
from game_mod_ops.panel import main
if __name__=='__main__': main()
