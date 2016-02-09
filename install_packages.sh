#!/bin/bash

echo "Installing new packages"
opkg update
opkg install kernel-module-ftdi-sio
pip install pybluez
