#!/bin/bash

echo "Installing new packages"
opkg update
opkg install kernel-module-ftdi-sio
pip install pybluez

echo "Reconfigure bluetoothd"
sed -i s/'ExecStart=\/usr\/lib\/bluez5\/bluetooth\/bluetoothd'/'ExecStart=\/usr\/lib\/bluez5\/bluetooth\/bluetoothd -C'/g /etc/systemd/system/bluetooth.target.wants/bluetooth.service