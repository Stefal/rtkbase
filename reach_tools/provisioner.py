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

def install_pip_packages():

    packages = ["pybluez"]

    for p in packages:
        pip.main(["install", p])

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
                print(p)
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

def run_command_safely(cmd):
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        pass

def restart_bt_daemon():
    run_command_safely(["rfkill", "unblock", "bluetooth"])
    run_command_safely(["systemctl", "daemon-reload"])
    run_command_safely(["systemctl", "restart", "bluetooth.service"])
    run_command_safely(["systemctl", "restart", "bluetooth.service"])
    run_command_safely(["hciconfig", "hci0", "reset"])

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

        restart_bt_daemon()

def update_bluetooth_service():
    first = "/lib/systemd/system/bluetooth.service"
    second = "/etc/systemd/system/bluetooth.target.wants/bluetooth.service"
    enable_bt_compatibility(first)
    enable_bt_compatibility(second)
    restart_bt_daemon()

def provision_reach():
    install_pip_packages()
    packages = ["kernel-module-ftdi-sio"]
    install_opkg_packages(packages)
    update_bluetooth_service()

if __name__ == "__main__":
    provision_reach()

