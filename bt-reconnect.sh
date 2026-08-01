#!/bin/bash
# vinylcast — keep the Bluetooth turntable (A2DP source) linked to this Pi (sink).
#
# The turntable must be PAIRED and TRUSTED first (see README). When it's powered
# on / in range this reconnects it and holds the link; harmless while it's off.
# Polls every RECONNECT_POLL_SEC; only acts when disconnected.
#
# Config from environment (see config.env.example).
#
# MIT License — Copyright (c) 2026 tsali

: "${BT_MAC:?BT_MAC not set (see config.env)}"
POLL="${RECONNECT_POLL_SEC:-20}"

while true; do
  if ! bluetoothctl info "$BT_MAC" 2>/dev/null | grep -q "Connected: yes"; then
    bluetoothctl connect "$BT_MAC" >/dev/null 2>&1
  fi
  sleep "$POLL"
done
