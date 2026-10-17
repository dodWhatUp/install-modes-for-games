#!/bin/bash
set -euo pipefail
test -f /home/lab/artifacts/bootstrap-ready
printf 'GUEST_OS='
uname -s
printf 'GUEST_HOSTNAME='
hostname
mkdir -p /home/lab/work/smoke /home/lab/artifacts
cd /home/lab/work/smoke
cat > hello.c <<'EOF'
#include <stdio.h>
int main(void) { puts("ISOLATED_BUILD_OK"); return 0; }
EOF
gcc -Wall -Wextra -Werror hello.c -o hello
test "$(./hello)" = "ISOLATED_BUILD_OK"
python3 -c 'import json; print(json.dumps({"python": "ok", "scope": "linux guest"}))'
test ! -d /mnt/c/Users
printf 'build-pass\n' > /home/lab/artifacts/acceptance-marker.txt
printf 'LINUX_BUILD_PASS\n'
