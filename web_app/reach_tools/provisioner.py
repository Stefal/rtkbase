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
import os
from . import reach_tools
import imp
import shutil

def install_pip_packages():

    packages = [
        ("pybluez", "bluetooth")
    ]

    for p in packages:
        try:
            imp.find_module(p[1])
        except ImportError:
            print("No module " + p[0] + " found...")
            pip.main(["install", p[0]])

def check_opkg_packages(packages):

    packages_to_check = packages

    try:
        out = subprocess.check_output(["opkg", "list-installed"])
    except subprocess.CalledProcessError:
        print("Error getting installed opkg packages")
        return None
    else:
        for p in out.split("\n"):
            if p:
                installed_package_name = p.split()[0]
                if installed_package_name in packages_to_check:
                    packages_to_check.remove(installed_package_name)

        return packages_to_check

def install_opkg_packages(packages):

    packages = check_opkg_packages(packages)

    if packages:
        print("Installing missing packages:")
        print(packages)
        try:
            subprocess.check_output(["opkg", "update"])
        except subprocess.CalledProcessError:
            print("No internet connection, so no package installs!")
            pass
        else:
            for p in packages:
                subprocess.check_output(["opkg", "install", p])

def restart_bt_daemon():
    reach_tools.run_command_safely(["rfkill", "unblock", "bluetooth"])
    reach_tools.run_command_safely(["systemctl", "daemon-reload"])
    reach_tools.run_command_safely(["systemctl", "restart", "bluetooth.service"])
    reach_tools.run_command_safely(["systemctl", "restart", "bluetooth.service"])
    reach_tools.run_command_safely(["hciconfig", "hci0", "reset"])

def enable_bt_compatibility(file_path):

    with open(file_path, "r") as f:
        data_read = f.readlines()

    need_to_update = True
    required_line = 0

    for line in data_read:
        if "ExecStart=/usr/lib/bluez5/bluetooth/bluetoothd -C" in line:
            need_to_update = False

    if need_to_update:
        data_to_write = []

        for line in data_read:
            if "ExecStart=/usr/lib/bluez5/bluetooth/bluetoothd" in line:
                to_append = "ExecStart=/usr/lib/bluez5/bluetooth/bluetoothd -C\n"
            else:
                to_append = line

            data_to_write.append(to_append)

        with open(file_path, "w") as f:
            f.writelines(data_to_write)

        reach_tools.run_command_safely(["sync"])

        restart_bt_daemon()

def update_bluetooth_service():
    first = "/lib/systemd/system/bluetooth.service"
    second = "/etc/systemd/system/bluetooth.target.wants/bluetooth.service"
    enable_bt_compatibility(first)
    enable_bt_compatibility(second)
    restart_bt_daemon()

def check_RTKLIB_integrity():
    RTKLIB_path = "/home/reach/RTKLIB/"
    reachview_binaries_path = "/home/reach/rtklib_configs/"

    RTKLIB_binaries = [
        (RTKLIB_path + "app/rtkrcv/gcc/rtkrcv", reachview_binaries_path + "rtkrcv"),
        (RTKLIB_path + "app/convbin/gcc/convbin", reachview_binaries_path + "convbin"),
        (RTKLIB_path + "app/str2str/gcc/str2str", reachview_binaries_path + "str2str")
    ]

    for b in RTKLIB_binaries:
        if not os.path.isfile(b[0]):
            print("Could not find " + b[0] + "! Copying from ReachView backup...")
            shutil.copy(b[1], b[0])

def provision_reach():
    install_pip_packages()
    packages = ["kernel-module-ftdi-sio"]
    install_opkg_packages(packages)
    update_bluetooth_service()
    check_RTKLIB_integrity()

if __name__ == "__main__":
    provision_reach()

