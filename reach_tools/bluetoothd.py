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

def enableBluetoothCompatibilityMode(file_path):

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

if __name__ == "__main__":
    first = "/lib/systemd/system/bluetooth.service"
    second = "/etc/systemd/system/bluetooth.target.wants/bluetooth.service"
    enableBluetoothCompatibilityMode(first)
    enableBluetoothCompatibilityMode(second)


