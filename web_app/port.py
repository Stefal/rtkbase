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

from os import system

def sh(script):
    system("bash -c '%s'" % script)

# change baudrate to 230400
def br230400():
    cmd = ["echo", "-en", '"\\xb5\\x62\\x06\\x00\\x01\\x00\\x01\\x08\\x22\\xb5\\x62\\x06\\x00\\x14\\x00\\x01\\x00\\x00\\x00\\xd0\\x08\\x00\\x00\\x00\\x84\\x03\\x00\\x07\\x00\\x03\\x00\\x00\\x00\\x00\\x00\\x84\\xe8\\xb5\\x62\\x06\\x00\\x01\\x00\\x01\\x08\\x22"', ">", "/dev/ttyMFD1"]
    cmd = " ".join(cmd)
    sh(cmd)

# change baudrate to 230400 from any previous baudrates
def changeBaudrateTo115200():
    # typical baudrate values
#    br = ["4800", "9600", "19200", "38400", "57600", "115200", "230400"]
    br = ["4800", "9600", "19200", "38400", "57600", "115200"]
    cmd = ["stty", "-F", "/dev/ttyACM0"]

    for rate in br:
        cmd.append(str(rate))
        cmd_line = " ".join(cmd)
        sh(cmd_line)

#        br230400()
#        cmd.pop()
