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
import math
from glob import glob

from log_converter import convbin

class LogManager():

    supported_solution_formats = ["llh", "xyz", "enu", "nmea", "erb", "zip", "bz2", "tar", "tag"]

    def __init__(self, rtklib_path, log_path):

        self.log_path = log_path
        self.convbin = convbin.Convbin(rtklib_path)

        self.log_being_converted = ""

        self.available_logs = []
        self.updateAvailableLogs()

    def updateAvailableLogs(self):

        self.available_logs = []

        print("Getting a list of available logs")
        for log in glob(self.log_path + "/*"):
        
            log_name = os.path.basename(log)
            # get size in bytes and convert to MB
            log_size = self.getLogSize(log)

            potential_zip_path = os.path.splitext(log)[0] + ".zip"

            log_format = self.getLogFormat(log)
            is_being_converted = True if log == self.log_being_converted else False

            self.available_logs.append({
                "name": log_name,
                "size": log_size,
                "format": log_format,
                "is_being_converted": is_being_converted
            })

            self.available_logs.sort(key = lambda date: date['name'], reverse = True)
        
        #Adding an id to each log
        id = 0
        for log in self.available_logs:
            log['id'] = id
            id += 1

        
    """
    def getLogCompareString(self, log_name):
        name_without_extension = os.path.splitext(log_name)[0]
        print("log name: ", log_name)
        log_type, log_date = name_without_extension.split("_")
        return log_date + log_type[0:2]
    """
    def getLogSize(self, log_path):
        size = os.path.getsize(log_path) / (1024 * 1024.0)
        return "{0:.2f}".format(size)

    def getLogFormat(self, log_path):
        file_path, extension = os.path.splitext(log_path)
        extension = extension[1:]

        """
        # removed because a zip file is not necesseraly RINEX
        potential_zip_path = file_path + ".zip"
        if os.path.isfile(potential_zip_path):
            return "RINEX"
        """
        if (extension in self.supported_solution_formats or
                    extension in self.convbin.supported_log_formats):
            return extension.upper()
        else:
            return ""

    def formTimeString(self, seconds):
        # form a x minutes y seconds string from seconds
        m, s = divmod(seconds, 60)

        s = math.ceil(s)

        format_string = "{0:.0f} minutes " if m > 0 else ""
        format_string += "{1:.0f} seconds"

        return format_string.format(m, s)

    def calculateConversionTime(self, log_path):
        # calculate time to convert based on log size and format
        log_size = os.path.getsize(log_path) / (1024*1024.0)
        conversion_time = 0

        if log_path.endswith("rtcm3"):
            conversion_time = 42.0 * log_size
        elif log_path.endswith("ubx"):
            conversion_time = 1.8 * log_size

        return "{:.0f}".format(conversion_time)

    def cleanLogFiles(self, log_path):
        # delete all files except for the raw log
        full_path_logs = glob(self.log_path + "/*.rtcm3") + glob(self.log_path + "/*.ubx")
        extensions_not_to_delete = [".zip", ".ubx", ".rtcm3"]

        log_without_extension = os.path.splitext(log_path)[0]
        log_files = glob(log_without_extension + "*")

        for log_file in log_files:
            if not any(log_file.endswith(ext) for ext in extensions_not_to_delete):
                try:
                    os.remove(log_file)
                except OSError as e:
                    print ("Error: " + e.filename + " - " + e.strerror)

    def deleteLog(self, log_filename):
        # try to delete log if it exists

        #log_name, extension = os.path.splitext(log_filename)

        # try to delete raw log
        print("Deleting log " + log_filename)
        try:
            os.remove(os.path.join(self.log_path, log_filename))
        except OSError as e:
            print ("Error: " + e.log_filename + " - " + e.strerror)

        """
        print("Deleting log " + log_name + ".zip")
        try:
            os.remove(self.log_path + "/" + log_name + ".zip")
        except OSError as e:
            print ("Error: " + e.filename + " - " + e.strerror)
        """

    def getRINEXVersion(self):
        # read RINEX version from system file
        print("Getting RINEX version from system settings")
        version = "3.01"
        try:
            with open(os.path.join(os.path.expanduser("~"), ".reach/rinex_version"), "r") as f:
                version = f.readline().rstrip("\n")
        except (IOError, OSError):
            print("No such file detected, defaulting to 3.01")

        return version

    def setRINEXVersion(self, version):
        # write RINEX version to system file
        print("Writing new RINEX version to system file")

        with open(os.path.join(os.path.expanduser("~"), ".reach/rinex_version"), "w") as f:
            f.write(version)

