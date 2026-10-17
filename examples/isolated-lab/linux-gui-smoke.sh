#!/bin/bash
set -euo pipefail
# Input goes only to this private X server in the guest.
xvfb-run -a -s '-screen 0 1024x768x24 -nolisten tcp' bash <<'EOF'
set -euo pipefail
mkdir -p /home/lab/artifacts
rm -f /home/lab/artifacts/gui-result.txt
xterm -geometry 85x24+30+30 -title 'Codex isolated Linux test' -e bash --noprofile --norc &
term=$!
trap 'kill "$term" 2>/dev/null || true' EXIT
for n in $(seq 1 50); do
    window=$(xdotool search --onlyvisible --name 'Codex isolated Linux test' 2>/dev/null | head -n 1 || true)
    test -n "$window" && break
    sleep .2
done
test -n "$window"
xdotool windowfocus --sync "$window"
xdotool type --clearmodifiers --delay 20 "printf GUI_INPUT_PASS > /home/lab/artifacts/gui-result.txt"
xdotool key --clearmodifiers Return
for n in $(seq 1 50); do
    test -f /home/lab/artifacts/gui-result.txt && break
    sleep .2
done
test "$(cat /home/lab/artifacts/gui-result.txt)" = GUI_INPUT_PASS
import -window root /home/lab/artifacts/linux-gui.png
printf 'LINUX_GUEST_GUI_INPUT_AND_SCREENSHOT_PASS\n'
EOF
