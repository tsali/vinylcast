#!/bin/bash
# vinylcast installer — copies scripts to /opt/vinylcast, config to /etc/vinylcast,
# installs the three systemd services. Run with sudo from the repo directory.
#
# MIT License — Copyright (c) 2026 tsali
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"
OPT="/opt/vinylcast"
ETC="/etc/vinylcast"

if [ "$(id -u)" -ne 0 ]; then echo "Run with sudo."; exit 1; fi

echo "==> Installing scripts to $OPT"
install -d "$OPT"
install -m 0755 "$SRC/vinyl-controller.py" "$OPT/vinyl-controller.py"
install -m 0755 "$SRC/sonos-keepalive.py"  "$OPT/sonos-keepalive.py"
install -m 0755 "$SRC/bt-reconnect.sh"     "$OPT/bt-reconnect.sh"

echo "==> Installing config to $ETC (won't overwrite an existing config.env)"
install -d "$ETC"
if [ ! -f "$ETC/config.env" ]; then
  install -m 0640 "$SRC/config.env.example" "$ETC/config.env"
  echo "    -> created $ETC/config.env  — EDIT THIS before starting."
else
  echo "    -> $ETC/config.env already exists, left as-is."
fi

echo "==> Installing systemd units"
install -m 0644 "$SRC/systemd/"*.service /etc/systemd/system/
systemctl daemon-reload

cat <<EOF

Done. Next:
  1. Edit your config:      sudo nano $ETC/config.env
  2. Pair + trust the deck: see the README (bluetoothctl)
  3. Enable + start:
       sudo systemctl enable --now vinylcast-bt-reconnect.service
       sudo systemctl enable --now vinylcast-controller.service
       sudo systemctl enable --now vinylcast-keepalive.service
  4. Drop a needle. It should come through your speaker.

Logs:  journalctl -u vinylcast-controller -f
EOF
