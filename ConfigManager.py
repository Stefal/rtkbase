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

        # clear previously saved info
        self.parameter, self.value, self.comment, self.description = ""

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

    def formString(self):
        # form a line to put into a RTKLIB config file:

        # we want to write values aligned for easier reading
        parameter_with_trailing_spaces = self.parameter + " " * (18 - len(self.parameter))

        item = [parameter_with_trailing_spaces, "=" + self.value, "#", self.comment, "##", self.description]

        return " ".join(item)

class Config:

    def __init__(self, file_name = None, items_list = None):
        # we keep all the options for current config file and their order here

        # config file name
        self.file_name = ""

        # items in the correct order
        self.items_list = []

    def readFromFile(self, from_file):

        # clear previous data
        self.items_list = []

        # item placeholder
        item = ConfigItem()

        with open(from_file, "r") as f:
            for line in f:
                # we mine for info in every line of the file
                item.extractFromString(line)
                self.items_list.append(item)

    def writeToFile(self, to_file):

        with open(to_file, "w") as f:
            line = "# rtkrcv options for rtk (v.2.4.2)"
            f.write(line + "\n\n")

            for item in self.items_list:
                f.writeline(item.formString() + "\n")

class ConfigManager:

    def __init__(self, config_path = None):

        if config_path is None:
            self.config_path = "/home/reach/RTKLIB/app/rtkrcv/"
        else:
            self.config_path = config_path

        self.default_rover_config = "reach_single_default.conf"

        self.available_configs = []
        self.updateAvailableConfigs()

        self.buff_dict_comments = {}
        self.buff_dict_human_comments = {}
        self.buff_dict = {}
        self.buff_dict_order = []
        self.readConfig(self.default_rover_config) # we do this to load config order from default reach base config

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

        self.buff_dict_order = []

        self.buff_dict = {}
        self.buff_dict_comments = {}
        self.buff_dict_human_comments = {}

        with open(config_file_path, "r") as f:
            for line in f:
                separated_lines = line.split() # separate lines with spaces, get rid of extra whitespace
                length = len(separated_lines)

                # check if the line is empty or commented
                if length > 0:
                    if separated_lines[0][0] != "#":
                        param = separated_lines[0] # get first part of the line, before the equal sign
                        val = separated_lines[1][1:] # get the second part of the line, discarding "=" symbol

                        if length > 3:
                            comments = separated_lines[3]
                            # some of the options are comments only
                            # frontend need to check if the comment has ":" in it
                            # then, it can be used to generate a dropdown menu
                            # if ":" in options:

                            self.buff_dict_comments[param] = comments

                            if length > 5:
                                # some lines will have a ## comment after the first one
                                # to add more information and be more informative for ReachView
                                human_comment = separated_lines[5]

                                self.buff_dict_human_comments[param] = human_comment

                        self.buff_dict[param] = val
                        self.buff_dict_order.append(param) # this is needed to conserve the order of the parameters in the config file

            self.buff_dict["config_file_name"] = from_file

    def writeConfig(self, to_file, dict_values = None):

        if dict_values is None:
            dict_values = self.buff_dict

        if to_file is None:
            to_file = self.default_rover_config

        # check if this is a full path or just a name
        # if it's a name, then we use the default location
        if "/" in to_file:
            config_file_path = to_file
        else:
            config_file_path = self.config_path + to_file

        print("Printing config we are about to write to " + config_file_path + "\n" + str(dict_values))

        with open(config_file_path, "w") as f:
            line = "# rtkrcv options for rtk (v.2.4.2)"
            f.write(line + "\n\n")

            for key in self.buff_dict_order:

                k = str(key)
                if k in dict_values:
                    v = str(dict_values[key])

                    line = k + " " * (19 - len(k)) + "=" + v

                    print("line = " + line)
                    # check if comments are available
                    if key in self.buff_dict_comments:
                        line += " # " + self.buff_dict_comments[key]

                    f.write(line + "\n")

