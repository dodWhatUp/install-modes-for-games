#!/bin/sh
# Run only in the newly enrolled Arm Linux guest, after checkpointing.
set -eu
test "$(uname -s)" = Linux
case "$(uname -m)" in aarch64|arm64) ;; *) exit 2 ;; esac
test "$HOME" = /home/lab
test -f /home/lab/.local/state/isolatedlab-mac/enrollment.json
test -f /home/lab/agent/guest_agent.py
test -f /home/lab/agent/guest_bridge.py
sudo -n env DEBIAN_FRONTEND=noninteractive apt-get update
sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  python3-venv dbus-x11 at-spi2-core python3-gi gir1.2-atspi-2.0 gir1.2-gtk-3.0 xvfb xauth
test -d /home/lab/agent/venv || python3 -m venv /home/lab/agent/venv
/home/lab/agent/venv/bin/pip install 'playwright==1.63.0'
# Use Playwright's own platform selection. Never run the archived x64 fallback.
/home/lab/agent/venv/bin/python -m playwright install --with-deps --only-shell chromium
/usr/bin/python3 -c 'import gi; gi.require_version("Atspi", "2.0"); from gi.repository import Atspi; print("AT_SPI_PROVIDER_INSTALLED")'
mkdir -p /home/lab/artifacts
dpkg-query -W > /home/lab/artifacts/resolved-apt.txt
/home/lab/agent/venv/bin/pip freeze > /home/lab/artifacts/resolved-python.txt
/usr/bin/python3 -c 'import json,pathlib; pathlib.Path("/home/lab/agent/desktop-provider.json").write_text(json.dumps({"installed":True,"provider":"system Python GI / AT-SPI"}))'
