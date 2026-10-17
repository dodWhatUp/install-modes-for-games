#!/usr/bin/env bash
set -euo pipefail
test -x /home/lab/agent/venv/bin/python
task_log="/home/lab/artifacts/browser-install-$(date -u +%Y%m%dT%H%M%SZ).log"
if env PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT=120000 /home/lab/agent/venv/bin/python -m playwright install --only-shell chromium >"$task_log" 2>&1; then
  printf 'BROWSER_INSTALL_PASS log=%s\n' "$task_log"
else
  task_exit=$?
  tail -n 30 "$task_log"
  printf 'BROWSER_INSTALL_FAIL exit=%s log=%s\n' "$task_exit" "$task_log"
  exit "$task_exit"
fi
