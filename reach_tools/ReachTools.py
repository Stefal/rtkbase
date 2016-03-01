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
from subprocess import check_output

def isTimeSynchronizedByNtp(self):
    out = check_output("timedatectl")
    if "NTP synchronized: yes" in out:
        return True
    else:
        return False

def gpsTimeUpdateRequired(self, solution_status):
    # we require time updated by gps if ntp sync is not available and we haven't done it yet
    if self.system_time_calibrated:
        return False
    else:
        if self.isTimeSynchronizedByNtp():
            self.system_time_calibrated = True
            return False
        else:
            if solution_status != "-":
                self.system_time_calibrated = True
                return True
            else:
                return False

def updateSystemTime(self, date, time):
    # requires a date list and a time list
    # ["YYYY", "MM", "DD"], ["hh", "mm", "ss"]
    print("##### UPDATING SYSTEM TIME #####")
    print(date)
    print(time)
    # busybox date cmd can use a following format
    # YYYY.MM.DD-hh:mm:ss
    datetime_string = ".".join(date) + "-" + ":".join(time)
    cmd = ["date", "-s", datetime_string]
    out = check_output(cmd)

def getImageVersion():

    image_version_file = "/home/reach/.reach/image_version"

    try:
        with open(image_version_file, "r") as f:
            image_version = f.readline().rstrip("\n")
    except IOError, OSError:
        print("Could not find version file inside system")
        print("This is image v1.0")
        image_version = "v1.0"

    return image_version

def getNetworkStatus():

    # get Wi-Fi mode, Master or Managed
    cmd = ["configure_edison", "--showWiFiMode"]
    cmd = " ".join(cmd)
    mode = check_output(cmd, shell = True).strip()

    ssid = "empty"
    ip_address = "empty"

    if mode == "Managed":
        # we are in managed, client mode
        # we can extract all information from "wpa_cli status"

        cmd = ["wpa_cli", "status"]
        cmd = " ".join(cmd)
        out = check_output(cmd, shell = True)

        out = out.split("\n")

        for line in out:
            if "ssid=" in line:
                ssid = line[5:]
            if "ip_address=" in line:
                ip_address = line[11:]

    if mode == "Master":
        # we are in master, AP mode
        # we can extract all info from "configure_edison"
        # with differnet parameters

        # example of the output {"hostname": "reach", "ssid": "reach:ec:e8", "default_ssid": "edison_ap"}
        cmd = ["configure_edison", "--showNames"]
        cmd = " ".join(cmd)
        out = check_output(cmd, shell = True)

        anchor = '"ssid": "'

        ssid_start_position = out.find(anchor) + len(anchor)
        ssid_stop_position = out.find('"', ssid_start_position)

        ssid = out[ssid_start_position:ssid_stop_position]

        cmd = ["configure_edison", "--showWiFiIP"]
        cmd = " ".join(cmd)
        ip_address = check_output(cmd, shell = True).strip()

    return {"mode": mode, "ssid": ssid, "ip_address": ip_address}

def getAppVersion():
    # Extract git tag as software version
    git_tag_cmd = "git describe --tags"
    app_version = check_output([git_tag_cmd], shell = True, cwd = "/home/reach/ReachView")

    return app_version

def getSystemStatus():

    system_status = {
        "network_status": getNetworkStatus(),
        "image_version": getImageVersion(),
        "app_version": getAppVersion(),
    }

    return system_status

def getAvailableSerialPorts():

    possible_ports_ports_to_use = ["ttyMFD2", "ttyUSB0"]
    serial_ports_to_use = [port for port in possible_ports_ports_to_use if os.path.exists("/dev/" + port)]

    return serial_ports_to_use

