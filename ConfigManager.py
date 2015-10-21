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

# This module aims to make working with RTKLIB configs easier
# It allows to parse RTKLIB .conf files to python dictionaries and backwards
# Note that on startup it reads on of the default configs
# and keeps the order of settings, stored there

class ConfigItem:

    def __init__(self, parameter = "", value = "", comment = "", description = ""):

        self.parameter = parameter
        self.value = value
        self.comment = comment
        self.description = description

    def extractFromString(self, string):
        # extract information from a config file line
        # return true, if the line

        # clear previously saved info
        self.parameter, self.value, self.comment, self.description = "", "", "", ""

        # cut the line into pieces by spaces
        separated_lines = string.split()
        length = len(separated_lines)

        # first, check if this line is empty
        if length > 0:

            # second, check if it's fully commented
            if separated_lines[0][0] != "#":

                # extract the parameter and value
                self.parameter = separated_lines[0]
                self.value = separated_lines[0][1:]

                # check if we have more info, possibly useful comment
                if length > 3 and separated_lines[2] == "#":
                    self.comment = separated_lines[3]

                    # check if we have more info, possibly description
                    if length > 5 and separated_lines[4] == "##":
                        self.description = separated_lines[5]

                return True
            else:
                # if the first symbol is "#", the line is commented
                return False
        else:
            # if length is 0, the line is empty
            return False

    def formString(self):
        # form a line to put into a RTKLIB config file:

        # we want to write values aligned for easier reading
        # hence need to add a number of spaces after the parameter
        parameter_with_trailing_spaces = self.parameter + " " * (18 - len(self.parameter))

        item = [parameter_with_trailing_spaces, "=" + self.value, "#", self.comment, "##", self.description]

        return " ".join(item)

class Config:

    def __init__(self, file_name = None):
        # we keep all the options for current config file and their order here

        # config file name
        self.current_file_name = None

        # due to how sending stuff over socket.io works, we need to keep config data
        # as a dictionary. to maintain order later in the browser we keep it in the
        # following form:
        # items = {
        #     "0": item0,
        #     "1": item1
        # }

        self.items = {}

        # if we pass the file to the constructor, then read the values
        if file_name is not None:
            self.readFromFile(file_name)

    def readFromFile(self, from_file):

        # save file name as current
        self.current_file_name = from_file

        # clear previous data
        self.items = {}

        # current item container
        item = ConfigItem()

        with open(from_file, "r") as f:
            i = 0
            for line in f:
                # we mine for info in every line of the file
                # if the info is valid, we add this item to the items dict
                if item.extractFromString(line):

                    # save the info as {"0": item0, ...}
                    self.items[str(i)] = item

                    print("DEBUG READ FROM FILE")
                    print("i == " + str(i) + " item == " + str(item))

                    i += 1

    def writeToFile(self, to_file = None):

        # by default, we write to the current file
        if to_file == None:
            to_file = self.current_file_name

        # we keep the config as a dict, which is unordered
        # now is a time to convert it to a list, so that we could
        # write it to a file maintaining the order

        # create an empty list of the same length as we have items
        items_list = [""] * len(self.items)

        # turn our dict with current items into a list in the correct order:
        for item_number in self.items:
            items_list[int(item_number)] = self.items[item_number]

        with open(to_file, "w") as f:
            line = "# rtkrcv options for rtk (v.2.4.2)"
            f.write(line + "\n\n")

            for item in items_list:
                f.write(item.formString() + "\n")

class ConfigManager:

    def __init__(self, config_path = None):

        if config_path is None:
            self.config_path = "/home/reach/RTKLIB/app/rtkrcv/"
        else:
            self.config_path = config_path

        self.default_rover_config = "reach_single_default.conf"

        self.available_configs = []
        self.updateAvailableConfigs()

        # create a buffer for keeping config data
        # read default one into buffer

        self.buffered_config = Config(self.config_path + self.default_rover_config)

    def updateAvailableConfigs(self):

        self.available_configs = []
        path_length = len(self.config_path)

        # get a list of available .conf files in the config directory
        configs = glob(self.config_path + "*.conf")

        for conf in configs:
            if conf:
                self.available_configs.append(conf[path_length:])

    def readConfig(self, from_file):

        if from_file is None:
            from_file = self.default_rover_config

        # check if this is a full path or just a name
        # if it's a name, then we use the default location
        if "/" in from_file:
            config_file_path = from_file
        else:
            config_file_path = self.config_path + from_file

        print("DEBUG READING ROVER CONFIG FROM FILE: " + config_file_path)
        self.buffered_config.readFromFile(config_file_path)

    def writeConfig(self, to_file, config_value = None):

        if config_value is None:
            config_value = self.buffered_config

        if to_file is None:
            to_file = self.default_rover_config

        # check if this is a full path or just a name
        # if it's a name, then we use the default location
        if "/" in to_file:
            config_file_path = to_file
        else:
            config_file_path = self.config_path + to_file

        # do the actual writing
        if config_value is None:
            self.buffered_config.writeToFile(to_file)
        else:
            self.config_value.writeToFile(to_file)











