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

from subprocess import check_output

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
