#!/bin/bash

echo "Installing new packages"
opkg update
opkg install kernel-module-ftdi-sio
pip install pybluez

echo "Reconfigure bluetoothd"
/home/reach/ReachView/reach_tools/bluetoothd.py

echo "Restart bluetoothd"
systemctl daemon-reload
systemctl restart bluetooth.service