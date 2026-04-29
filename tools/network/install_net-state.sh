#!/bin/bash

set -e

echo "[1/6] Installing dependencies..."
apt update
apt install -y network-manager tcpdump

echo "[2/6] Installing script..."
install -m 755 net-state.sh /usr/local/bin/net-state.sh

echo "[3/6] Installing config..."
[ -f /etc/net-state.conf ] || cp net-state.conf /etc/net-state.conf

echo "[4/6] Installing systemd units..."
install -m 644 net-state.service /etc/systemd/system/net-state.service
install -m 644 net-state-check.service /etc/systemd/system/net-state-check.service
install -m 644 net-state-check.timer /etc/systemd/system/net-state-check.timer

echo "[5/6] Installing dispatcher..."
install -m 755 50-net-state /etc/NetworkManager/dispatcher.d/50-net-state

echo "[6/6] Enabling services..."
systemctl daemon-reload
systemctl enable net-state.service
systemctl enable net-state-check.timer
systemctl start net-state-check.timer

echo "Installation complete."
echo ""
echo "Logs:"
echo "  journalctl -t net-state -f"
echo ""
echo "Start manually:"
echo "  systemctl start net-state.service"