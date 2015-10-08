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

from glob import glob
from os import path

class LogManager():

    def __init__(self, log_path = None):

        if log_path is None:
            self.log_path = "/home/reach/logs/"
        else:
            self.log_path = path_to_logs

        self.available_logs = []
        self.updateAvailableLogs()

    def updateAvailableLogs(self):

        # clean previous values
        self.available_logs = []

        # get a list of available .log files in the log directory
        full_path_logs = glob(self.log_path + "*.log")

        path_length = len(self.log_path)

        for log in full_path_logs:
            if log:
                # if the entry is not empty, we get file name, size and prepare them for use in templates

                log_name = log[path_length:]
                # get size in bytes and convert to MB
                log_size = path.getsize(log) / (1024*1024.0)
                log_size = str(log_size)
                right_border = log_size.find(".") + 2
                log_size = log_size[:right_border]

                self.available_logs.append({
                    "name": log_name,
                    "size": log_size
                })




