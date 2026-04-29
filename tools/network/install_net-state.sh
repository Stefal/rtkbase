#!/bin/bash

set -e

echo "[1/8] Installing dependencies..."
apt update
apt install -y network-manager tcpdump

echo "[2/8] Installing main script..."
install -m 755 net-state.sh /usr/local/bin/net-state.sh

echo "[3/8] Installing config..."
[ -f /etc/net-state.conf ] || install -m 644 net-state.conf /etc/net-state.conf

echo "[4/8] Creating log file..."
LOG_FILE="/var/log/net-state.log"

if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
    chmod 644 "$LOG_FILE"
    echo "$(date '+%F %T') [INFO] log initialized" >> "$LOG_FILE"
fi

echo "[5/8] Installing systemd units..."
install -m 644 net-state.service /etc/systemd/system/net-state.service
install -m 644 net-state-check.service /etc/systemd/system/net-state-check.service
install -m 644 net-state-check.timer /etc/systemd/system/net-state-check.timer

echo "[6/8] Installing NetworkManager dispatcher..."
install -m 755 dispatcher /etc/NetworkManager/dispatcher.d/50-net-state

echo "[7/8] Creating NetworkManager profiles..."

# Detect interface
IFACE=$(nmcli -t -f DEVICE,TYPE device | grep ethernet | head -n1 | cut -d: -f1)

if [ -z "$IFACE" ]; then
    IFACE=$(ip -o link show | awk -F': ' '$2 !~ /lo/ {print $2; exit}')
fi

echo "Detected interface: $IFACE"

# ------------------------------------------------------------
# CLIENT (existing wired connection assumed)
# ------------------------------------------------------------

echo " - ensuring default wired profile exists"
if ! nmcli -t -f NAME con show | grep -qx "Wired connection 1"; then
    echo "   (warning) no default wired profile found"
fi

# ------------------------------------------------------------
# DIRECT profile
# ------------------------------------------------------------

if nmcli -t -f NAME con show | grep -qx "mode-direct"; then
    echo " - mode-direct already exists"
else
    echo " - creating mode-direct"
    nmcli con add type ethernet ifname "$IFACE" \
        con-name mode-direct \
        ipv4.method manual \
        ipv4.addresses 192.168.10.1/24 \
        ipv4.never-default yes \
        ipv6.method ignore \
        connection.autoconnect no
fi

# ------------------------------------------------------------
# SHARED profile
# ------------------------------------------------------------

if nmcli -t -f NAME con show | grep -qx "mode-shared"; then
    echo " - mode-shared already exists"
else
    echo " - creating mode-shared"
    nmcli con add type ethernet ifname "$IFACE" \
        con-name mode-shared \
        ipv4.method shared \
        ipv6.method ignore \
        connection.autoconnect no
fi

echo "[8/8] Enabling services..."
systemctl daemon-reload
systemctl enable net-state.service
systemctl enable net-state-check.timer
systemctl start net-state-check.timer

echo ""
echo "Installation complete."
echo ""
echo "Interface: $IFACE"
echo "Logs:"
echo "  journalctl -t net-state -f"
echo "  tail -f /var/log/net-state.log"
echo ""
echo "Start service:"
echo "  systemctl start net-state.service"