#!/bin/bash
set -euo pipefail
for n in $(seq 1 12); do
    test "$(/home/lab/work/smoke/hello)" = ISOLATED_BUILD_OK
    test "$(cat /home/lab/artifacts/acceptance-marker.txt)" = build-pass
    printf 'HEALTH_PASS_%s\n' "$n"
    sleep 5
done
