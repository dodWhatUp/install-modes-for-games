#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
sudo -n apt-get update
sudo -n apt-get install -y --no-install-recommends dbus-x11 at-spi2-core python3-gi gir1.2-atspi-2.0 gir1.2-gtk-3.0
/usr/bin/python3 -c 'import gi; gi.require_version("Atspi", "2.0"); gi.require_version("Gtk", "3.0"); from gi.repository import Atspi, Gtk; print("AT-SPI and GTK providers installed")'
mkdir -p /home/lab/agent
/usr/bin/python3 -c 'import json,pathlib; pathlib.Path("/home/lab/agent/desktop-provider.json").write_text(json.dumps({"installed":True,"provider":"system Python GI / AT-SPI"}))'
