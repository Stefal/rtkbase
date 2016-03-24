#!/usr/bin/python

# ReachView code is placed under the GPL license.
# Written by Egor Fedorov (egor.fedorov@emlid.com)
# Copyright (c) 2015, Emlid Limited
# All rights reserved.

# If you are interested in using ReachView code as a part of a
# closed source project, please contact Emlid Limited (info@emlid.com).

# This file is part of ReachView.

# ReachView is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# ReachView is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with ReachView.  If not, see <http://www.gnu.org/licenses/>.

import pip
import subprocess

def install_pip_packages():

    packages = ["pybluez"]

    for p in packages:
        pip.main(["install", p])

def install_opkg_packages():

    packages = ["kernel-module-ftdi-sio"]

    subprocess.check_output(["opkg", "update"])
    for p in packages:
        subprocess.check_output(["opkg", "install", p])

def restart_bt_daemon():
    subprocess.check_output(["systemctl", "daemon-reload"])
    subprocess.check_output(["systemctl", "restart", "bluetooth.service"])
    subprocess.check_output(["systemctl", "restart", "bluetooth.service"])
    subprocess.check_output(["hciconfig", "hci0", "reset"])

def enable_bt_compatibility(file_path):

    with open(file_path, "r") as f:
        data_read = f.readlines()

    data_to_write = []
    for line in data_read:
        if "ExecStart=/usr/lib/bluez5/bluetooth/bluetoothd" in line:
            to_append = "ExecStart=/usr/lib/bluez5/bluetooth/bluetoothd -C\n"
        else:
            to_append = line

        data_to_write.append(to_append)

    with open(file_path, "w") as f:
        f.writelines(data_to_write)

    restart_bt_daemon()


def update_bluetooth_service():
    first = "/lib/systemd/system/bluetooth.service"
    second = "/etc/systemd/system/bluetooth.target.wants/bluetooth.service"
    enable_bt_compatibility(first)
    enable_bt_compatibility(second)
    restart_bt_daemon()

def provision_reach():
    install_pip_packages()
    install_opkg_packages()
    update_bluetooth_service()

