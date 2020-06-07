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

import pexpect
from .logs import Log, LogMetadata

class Convbin:

    supported_log_formats = ["rtcm2", "rtcm3", "nov", "oem3", "ubx", "ss2", "hemis", "stq", "javad", "nvs", "binex", "rinex"]

    def __init__(self, rtklib_path):
        self.bin_path = rtklib_path
        self.child = 0

    def convertRTKLIBLogToRINEX(self, log_path, rinex_version="3.01"):

        print("Converting log " + log_path + "...")

        result = None

        # check if extension format is in the list of the supported ones
        log_format = [f for f in self.supported_log_formats if log_path.endswith(f)]

        if log_format:
            try:
                log_metadata = self.convertLogToRINEX(log_path, log_format[0], rinex_version)
            except ValueError:
                return None

            if log_metadata:
                result = Log(log_path, log_metadata)

        return result

    def convertLogToRINEX(self, log_path, format, rinex_version):

        spawn_command = " ".join([
            self.bin_path + "/convbin",
            "-r",
            format,
            "-v",
            rinex_version,
            "-od",
            "-os",
            "-oi",
            "-ot",
            "-ol",
            log_path
        ])

        print("Specified format is " + format)

        print("Spawning convbin with " + spawn_command)
        self.child = pexpect.spawn(spawn_command, echo = False)
        print("Process spawned!")
        self.child.expect(pexpect.EOF, timeout = None)

        if self.child.exitstatus != 0 and self.child.signalstatus == None:
            print("Convbin killed by external signal")
            raise ValueError

        print("Conversion process finished correctly")
        return self.parseConvbinOutput(self.child.before)

    def parseConvbinOutput(self, output):

        result_string = self.extractResultingString(output)

        if self.resultStringIsValid(result_string):
            return LogMetadata(result_string)
        else:
            return None

    def resultStringIsValid(self, result_string):
        return True if len(result_string) > 21 else False

    def extractResultingString(self, output):
        # get the last line of the convbin output

        last_line_end = output.rfind("\r\r\n")
        last_line_start = output.rfind("\r", 0, last_line_end) + 1

        return output[last_line_start:last_line_end]


if __name__ == "__main__":
    cb = Convbin("/home/reach/RTKLIB")
    rlog = cb.convertRTKLIBLogToRINEX("/home/reach/logs/rov_201601210734.ubx")
    print(rlog)
    # print("base")
    # blog = cb.convertRTKLIBLogToRINEX("/home/egor/RTK/convbin_test/ref_201601080935.rtcm3")
    # print(blog)
    # print("Kinelog")
    # kinelog = KinematicLog(rlog, blog)
    # print(kinelog)
    # kinelog.createKinematicLogPackage("lol.zip")
    # rlog.createLogPackage("lol1.zip")

