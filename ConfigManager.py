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

from reach_tools import reach_tools

import os
from glob import glob
from shutil import copy, Error

# This module aims to make working with RTKLIB configs easier
# It allows to parse RTKLIB .conf files to python dictionaries and backwards
# Note that on startup it reads on of the default configs
# and keeps the order of settings, stored there

class Config:

    def __init__(self, file_name = None, items = None):
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
        # where item is also a dictionary:
        # item0 = {
        #     "parameter": "p",
        #     "value": "v",
        #     "comment": "c",
        #     "description": "d"
        # }

        if items is None:
            self.items = {}
        else:
            self.items = items

        # if we pass the file to the constructor, then read the values
        if file_name is not None:
            self.readFromFile(file_name)

    def formStringFromItem(self, item):
        # form a line to put into a RTKLIB config file:

        # item must be a dict, described in the __init__ method comments!

        # we want to write values aligned for easier reading
        # hence need to add a number of spaces after the parameter
        if item:
            parameter_with_trailing_spaces = item["parameter"] + " " * (18 - len(item["parameter"]))

            s = [parameter_with_trailing_spaces, "=" + item["value"]]

            if "comment" in item:
                s.append("#")
                s.append(item["comment"])

            if "description" in item:
                s.append("##")
                s.append(item["description"])

            return " ".join(s)
        else:
            return ""

    def extractItemFromString(self, string):
        # extract information from a config file line
        # return true, if the line

        # create an empty item
        item = {}

        # cut the line into pieces by spaces
        separated_lines = string.split()
        length = len(separated_lines)

        # first, check if this line is empty
        if length > 0:

            # second, check if it's fully commented
            if separated_lines[0][0] != "#":

                # extract the parameter and value
                item["parameter"] = separated_lines[0]
                item["value"] = separated_lines[1][1:]

                # check if we have more info, possibly useful comment
                if length > 3 and separated_lines[2] == "#":
                    item["comment"] = separated_lines[3]

                    # check if we have more info, possibly description
                    if length > 5 and separated_lines[4] == "##":
                        # in order to have a description with spaces, we take all what's left
                        # after the "##" symbols and create a single line out of it:
                        description = separated_lines[5:]
                        description = " ".join(description)
                        item["description"] = description

                # check if we have only a description, rather than a comment and description
                if length >3 and separated_lines[2] == "##":
                    description = separated_lines[3:]
                    description = " ".join(description)
                    item["description"] = description

                # add information about available serial connections to input and output paths
                if "path" in item["parameter"]:
                    item["comment"] = self.formSelectCommentFromList(reach_tools.getAvailableSerialPorts())

        # we return the item we managed to extract form from string. if it's empty,
        # then we could not parse the string, hence it's empty, commented, or invalid
        return item

    def formSelectCommentFromList(self, items_list):
        comment = ""

        if items_list:
            comment = "("

            for index, item in enumerate(items_list):
                comment += str(index) + ":" + str(item) + ","

            comment = comment[:-1] + ")"

        return comment

    def parseBluetoothEntries(self, config_dict):
        # check if anything is set as a tcpsvr with path :8143
        # and change it to bluetooth
        entries_with_bt_port = {k: v for (k, v) in config_dict.items() if v["value"] == "localhost:8143"}

        for entry in entries_with_bt_port.keys():
            # can be log or out or in
            io_field = entries_with_bt_port[entry]["parameter"].split("-")[0]

            # find the corresponding io type
            io_type_entries = {k: v for (k, v) in config_dict.items() if io_field + "-type" in v["parameter"]}

            for key in io_type_entries.keys():
                config_dict[key]["value"] = "bluetooth"

        return config_dict

    def processConfig(self, config_dict):
        # sometimes, when reading we need to handle special situations, like bluetooth connection

        config_dict = self.parseBluetoothEntries(config_dict)

        return config_dict

    def readFromFile(self, from_file):

        # save file name as current
        self.current_file_name = from_file

        # clear previous data
        self.items = {}
        items_dict = {}

        # current item container
        item = {}

        with open(from_file, "r") as f:
            i = 0
            for line in f:
                # we mine for info in every line of the file
                # if the info is valid, we add this item to the items dict
                item = self.extractItemFromString(line)

                if item:
                    # save the info as {"0": item0, ...}
                    items_dict[str(i)] = item

                    i += 1

        self.items = self.processConfig(items_dict)

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
            # some of the fields are not numbers and need to be treated separately
            try:
                int_item_number = int(item_number)
            except ValueError:
                pass
            else:
                items_list[int_item_number] = self.items[item_number]

        with open(to_file, "w") as f:
            line = "# rtkrcv options for rtk (v.2.4.2)"
            f.write(line + "\n\n")

            for item in items_list:
                f.write(self.formStringFromItem(item) + "\n")

class ConfigManager:

    def __init__(self, rtklib_path, config_path):

        self.config_path = config_path

        self.default_rover_config = "rtkbase_single_default.conf"
        self.default_base_config = "rtkbase_base_default.conf"

        self.available_configs = []
        self.updateAvailableConfigs()

        # create a buffer for keeping config data
        # read default one into buffer

        self.buffered_config = Config(os.path.join(self.config_path, self.default_rover_config))

    def updateAvailableConfigs(self):

        self.available_configs = []

        # get a list of available .conf files in the config directory
        configs = glob(self.config_path + "*.conf")
        self.available_configs = [os.path.basename(config) for config in configs]


        # we do not show the base config
        try:
            self.available_configs.remove(self.default_base_config)
        except:
            pass

    def readConfig(self, from_file):

        if from_file is None:
            from_file = self.default_rover_config

        # check if this is a full path or just a name
        # if it's a name, then we use the default location
        if "/" in from_file:
            config_file_path = from_file
        else:
            config_file_path = self.config_path + from_file

        self.buffered_config.readFromFile(config_file_path)

    def writeConfig(self, to_file = None, config_values = None):

        if to_file is None:
            to_file = self.default_rover_config

        # check if this is a full path or just a name
        # if it's a name, then we use the default location
        if "/" not in to_file:
            to_file = self.config_path + to_file

        # do the actual writing

        # if we receive config_values to write, then we create another config instance
        # and use write on it
        if config_values is None:
            self.buffered_config.writeToFile(to_file)
        else:
            conf = Config(items = config_values)
            conf.writeToFile(to_file)

    def resetConfigToDefault(self, config_name):
        # try to copy default config to the working configs directory
        if "/" not in config_name:
            default_config_value = self.config_path + config_name
        else:
            default_config_value = config_name

        try:
            copy(default_config_value, self.config_path)
        except IOError as e:
            print("Error resetting config " + config_name + " to default. Error: " + e.filename + " - " + e.strerror)
        except OSError as e:
            print('Error: %s' % e)

    def deleteConfig(self, config_name):
        # try to delete config if it exists
        if "/" not in config_name:
            config_name = self.config_path + config_name

        try:
            os.remove(config_name)
        except OSError as e:
            print ("Error: " + e.filename + " - " + e.strerror)

    def readItemFromConfig(self, property, from_file):
        # read a complete item from config, found by "parameter part"

        conf = Config(self.config_path + from_file)

        # cycle through this config to find the needed option
        for item_number in conf.items:
            if conf.items[item_number]["parameter"] == property:
                # in case we found it
                return conf.items[item_number]

        # in case we didn't
        return None

    def writeItemToConfig(self, item, to_file):
        # write a complete item to the file

        # first we read the whole file
        conf = Config(self.config_path + to_file)

        # then we substitute the one property
        # cycle through this config to find the needed option
        for item_number in conf.items:
            if conf.items[item_number]["parameter"] == item["parameter"]:
                # in case we found it
                conf.items[item_number] = item

                # rewrite the file again:
                self.writeConfig(to_file, conf.items)
                return 1
                break

        # in case we didn't find it
        return None













