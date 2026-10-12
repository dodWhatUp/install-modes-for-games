#!/bin/sh
# Guest-only normal administration; refuse prior/unknown installation effects.
set -eu
test "$(uname -s)" = Linux
test "$HOME" = /home/lab
test -f /home/lab/.local/state/isolatedlab-mac/bridge-authorized-keys
test -f /home/lab/agent/guest-sshd.conf
test -f /home/lab/agent/isolatedlab-sshd.service
test ! -e /etc/ssh/isolatedlab_host_ed25519
test ! -e /etc/ssh/sshd_config.isolatedlab
sudo -n /usr/bin/ssh-keygen -q -t ed25519 -N '' -f /etc/ssh/isolatedlab_host_ed25519
sudo -n /usr/bin/install -m 600 /home/lab/agent/guest-sshd.conf /etc/ssh/sshd_config.isolatedlab
sudo -n /usr/bin/install -m 644 /home/lab/agent/isolatedlab-sshd.service /etc/systemd/system/isolatedlab-sshd.service
sudo -n /usr/sbin/sshd -t -f /etc/ssh/sshd_config.isolatedlab
sudo -n /usr/bin/systemctl daemon-reload
sudo -n /usr/bin/systemctl enable --now isolatedlab-sshd.service
/usr/bin/systemctl is-active isolatedlab-sshd.service
