#!/usr/bin/env bash
set -euo pipefail
# Run only inside the selected Linux guest, after its stopped-disk checkpoint.
sudo env DEBIAN_FRONTEND=noninteractive apt-get update -qq
sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv
test -d /home/lab/agent/venv || python3 -m venv /home/lab/agent/venv
/home/lab/agent/venv/bin/pip install 'playwright==1.63.0'
if env PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=120000 /home/lab/agent/venv/bin/python -m playwright install --with-deps --only-shell chromium; then
  printf 'STANDARD_BROWSER_INSTALL_PASS\n'
else
  printf 'Standard downloader failed; trying the exact registered headless shell with TLS-verified Python.\n'
  /home/lab/agent/venv/bin/python /home/lab/agent/prepare_guest_browser.py
fi
/home/lab/agent/venv/bin/python -c 'import playwright; print("GUEST_BROWSER_PROVIDER_INSTALLED")'
