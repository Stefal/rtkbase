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

import os
import subprocess

def getImageVersion():

    image_version_file = "/home/pi/.reach/image_version"

    try:
        with open(image_version_file, "r") as f:
            image_version = f.readline().rstrip("\n")
    except (IOError, OSError):
        print("Could not find version file inside system")
        print("This is image v1.0")
        image_version = "v1.0"

    return image_version

def getNetworkStatus():

    # get Wi-Fi mode, Master or Managed
#    cmd = ["configure_edison", "--showWiFiMode"]
#    cmd = " ".join(cmd)
#    mode = subprocess.check_output(cmd, shell = True).strip()

#    mode = "Managed"
#    ssid = "empty"
#    ip_address = "empty"

    mode = "Master"
    ssid = "RTK_test"
    ip_address = "192.168.43.1"

#    if mode == "Managed":
        # we are in managed, client mode
        # we can extract all information from "wpa_cli status"

#        cmd = ["wpa_cli", "status"]
#        cmd = " ".join(cmd)
#        out = subprocess.check_output(cmd, shell = True)

#        out = out.split("\n")

#        for line in out:
#            if "ssid=" in line:
#                ssid = line[5:]
#            if "ip_address=" in line:
#                ip_address = line[11:]

#    if mode == "Master":
        # we are in master, AP mode
        # we can extract all info from "configure_edison"
        # with differnet parameters

        # example of the output {"hostname": "reach", "ssid": "reach:ec:e8", "default_ssid": "edison_ap"}
#        cmd = ["configure_edison", "--showNames"]
#        cmd = " ".join(cmd)
#        out = subprocess.check_output(cmd, shell = True)

#        anchor = '"ssid": "'

#        ssid_start_position = out.find(anchor) + len(anchor)
#        ssid_stop_position = out.find('"', ssid_start_position)

#        ssid = out[ssid_start_position:ssid_stop_position]

#        cmd = ["configure_edison", "--showWiFiIP"]
#        cmd = " ".join(cmd)
#        ip_address = subprocess.check_output(cmd, shell = True).strip()

    return {"mode": mode, "ssid": ssid, "ip_address": ip_address}

def getAppVersion():
    # Extract git tag as software version
#    git_tag_cmd = "git describe --tags"
#    app_version = subprocess.check_output([git_tag_cmd], shell = True, cwd = "/home/reach")
    app_version = 1.0

    return app_version

def getSystemStatus():

    system_status = {
        "network_status": getNetworkStatus(),
        "image_version": getImageVersion(),
        "app_version": getAppVersion(),
    }

    return system_status

def getAvailableSerialPorts():

    possible_ports_ports_to_use = ["ttyACM0", "ttyUSB0"]
    serial_ports_to_use = [port for port in possible_ports_ports_to_use if os.path.exists("/dev/" + port)]

    return serial_ports_to_use

def getLogsSize(logs_path):
    #logs_path = "/home/pi/logs/"
    size_in_bytes = sum(os.path.getsize(logs_path + f) for f in os.listdir(logs_path) if os.path.isfile(logs_path + f))
    return size_in_bytes/(1024*1024)

def getFreeSpace(logs_path):
    space = os.statvfs(os.path.expanduser("~"))
    free = space.f_bavail * space.f_frsize / 1024000
    total = space.f_blocks * space.f_frsize / 1024000

    used_by_logs = getLogsSize(logs_path)
    total_for_logs = free + used_by_logs
    percentage = (float(used_by_logs)/float(total_for_logs)) * 100
    total_for_logs_gb = float(total_for_logs) / 1024.0

    result = {
        "used": "{0:.0f}".format(used_by_logs),
        "total": "{0:.1f}".format(total_for_logs_gb),
        "percentage": "{0:.0f}".format(percentage)
    }

    print("Returning sizes!")
    print(result)

    return result

def run_command_safely(cmd):
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        out = None

    return out



















