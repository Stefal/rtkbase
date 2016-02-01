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

import glob
import zipfile
import os

class LogMetadata:

    message_names = {
        "OBS": "OBS",
        "NAV": "GPS nav",
        "GNAV": "GLONASS nav",
        "HNAV": "GEO nav",
        "QNAV": "QZSS nav",
        "LNAV": "Galileo nav",
        "SBAS": "SBAS log",
        "Errors": "Errors"
    }

    def __init__(self, convbin_output):

        self.start_timestamp = 0
        self.stop_timestamp = 0

        self.navigation_messages = {
            "OBS": "0",
            "NAV": "0",
            "GNAV": "0",
            "HNAV": "0",
            "QNAV": "0",
            "LNAV": "0",
            "SBAS": "0",
            "Errors": "0"
        }

        self.extractDataFromString(convbin_output)

    def __str__(self):
        to_print = "Log start time: " + self.formatTimestamp(self.start_timestamp) + "\n"
        to_print += "Log stop time:  " + self.formatTimestamp(self.stop_timestamp) + "\n"
        to_print += "Navigation messages parsed:\n"
        to_print += self.formValidMessagesString()

        return to_print

    def formatTimestamp(self, timestamp):
        # 19800106000000
        timestamp = str(timestamp)

        # date
        human_readable_timestamp = timestamp[:4] + "-" + timestamp[4:6] + "-" + timestamp[6:8]
        # time
        human_readable_timestamp += " " + timestamp[8:10] + ":" + timestamp[10:12] + ":" + timestamp[12:14]

        return human_readable_timestamp

    def countValidMessages(self):

        valid_messages = 0

        for msg_type, msg_count in self.navigation_messages.items():
            if msg_type is not "Errors":
                valid_messages += int(msg_count)

        return valid_messages

    def formValidMessagesString(self):

        correct_order = ["OBS", "NAV", "GNAV", "HNAV", "QNAV", "LNAV", "SBAS", "Errors"]

        to_print = "Messages inside: "

        for msg in correct_order:
            msg_type = msg
            msg_count = self.navigation_messages[msg_type]
            if int(msg_count) > 0:
                to_print += self.message_names[msg_type] + ": " + msg_count + ", "

        return to_print[:-2]

    def extractDataFromString(self, data_string):
        # example string:
        # 2016/01/08 09:35:02-01/08 11:24:58: O=32977 N=31 G=41 E=2

        data_list = data_string.split(" ")
        data_list = filter(None, data_list)

        # first 3 parts mark the time properties
        # the next elemets show message counts

        self.extractTimeDataFromString(data_list[:3])
        self.extractMessageCountFromString(data_list[3:])

    def extractTimeDataFromString(self, data_list):
        # example string(split into a list by spaces)
        # 2016/01/08 09:35:02-01/08 11:24:58:

        # remove all the extra punctuation
        raw_data = "".join(data_list)
        raw_data = raw_data.translate(None, "/:\r")

        start_timestamp = raw_data.split("-")[0]
        stop_timestamp = raw_data.split("-")[1]

        stop_year = self.calculateStopYear(start_timestamp, stop_timestamp)

        self.start_timestamp = start_timestamp
        self.stop_timestamp = stop_year + stop_timestamp

    def calculateStopYear(self, start_timestamp, stop_timestamp):
        # calc stop year for the stop timestamp

        start_year = int(start_timestamp[:4])
        start_month = int(start_timestamp[4:6])

        stop_month = int(stop_timestamp[0:2])

        # we assume logs can't last longer than a year
        stop_year = start_year if start_month <= stop_month else start_year + 1

        return str(stop_year)

    def extractMessageCountFromString(self, data_list):
        # example string(split into a list by spaces)
        # O=32977 N=31 G=41 E=2

        msg_dictionary = {
            "O": "OBS",
            "N": "NAV",
            "G": "GNAV",
            "H": "HNAV",
            "Q": "QNAV",
            "L": "LNAV",
            "S": "SBAS",
            "E": "Errors"
        }

        for entry in data_list:
            split_entry = entry.split("=")
            msg_type = msg_dictionary[split_entry[0]]
            msg_count = split_entry[1]

            # append the resulting data
            self.navigation_messages[msg_type] = msg_count


class Log:

    rinex_file_extensions = [".obs", ".nav", ".gnav", ".hnav", ".qnav", ".lnav", ".sbs"]

    def __init__(self, log_path, log_metadata):

        self.log_path = log_path
        self.log_name = os.path.splitext(os.path.basename(self.log_path))[0]

        self.log_metadata = log_metadata

        self.RINEX_files = self.findRINEXFiles(os.path.dirname(self.log_path))

        self.log_package_path = ""

    def __str__(self):

        to_print = "Printing log info:\n"
        to_print += "Full path to log == " + self.log_path + "\n"
        to_print += "Available RINEX files: "
        to_print += str(self.RINEX_files) + "\n"
        to_print += str(self.log_metadata) + "\n"
        to_print += "ZIP file layout:\n"
        to_print += str(self.prepareLogPackage())

        return to_print

    def isValid(self):
        # determine whether the log has valuable RINEX info
        return True if self.log_metadata.countValidMessages() else False

    def findRINEXFiles(self, log_directory):

        files_in_dir = glob.glob(log_directory + "/*")
        rinex_files_in_dir = []

        for f in files_in_dir:
            filename = os.path.basename(f)
            name, extension = os.path.splitext(filename)

            if extension in self.rinex_file_extensions:
                if name == self.log_name:
                    rinex_files_in_dir.append(f)

        return rinex_files_in_dir

    def prepareLogPackage(self):
        # return a list of tuples [("abspath", "wanted_path_inside_zip"), ... ]
        # with raw and RINEX logs:w

        files_list = []
        # add raw log
        files_list.append((self.log_path, "Raw/" + os.path.basename(self.log_path)))

        for rinex_file in self.RINEX_files:
            rinex_files_paths = (rinex_file, "RINEX/" + os.path.basename(rinex_file))
            files_list.append(rinex_files_paths)

        return files_list

    def createLogPackage(self, package_destination=None):
        # files_list is a list of tuples [("abspath", "wanted_path_inside_zip"), ... ]

        if package_destination is None:
            package_destination = os.path.dirname(self.log_path) + "/" + self.log_name + ".zip"
        file_tree = self.prepareLogPackage()

        with zipfile.ZipFile(package_destination, "w") as newzip:
            for f in file_tree:
                newzip.write(f[0], f[1])

            newzip.writestr("readme.txt", str(self.log_metadata))

        # delete unzipped files
        self.deleteLogFiles()

        return package_destination

    def deleteLogFiles(self):

        all_log_files = self.RINEX_files
        # all_log_files.append(self.log_path)

        for log in all_log_files:
            try:
                os.remove(log)
            except:
                pass


class KinematicLog:

    def __init__(self, rover_log, base_log):

        self.rover_log = rover_log
        self.base_log = base_log

    def __str__(self):

        return str(self.rover_log) + "\n" + str(self.base_log)

    def createKinematicLogPackage(self, package_destination):

        rover_file_tree = self.rover_log.prepareLogPackage()
        base_file_tree = self.base_log.prepareLogPackage()

        with zipfile.ZipFile(package_destination, "w") as newzip:
            for f in rover_file_tree:
                newzip.write(f[0], "Rover/" + f[1])

            newzip.writestr("Rover/readme.txt", str(self.rover_log.log_metadata))

            for f in base_file_tree:
                newzip.write(f[0], "Base/" + f[1])

            newzip.writestr("Base/readme.txt", str(self.base_log.log_metadata))
