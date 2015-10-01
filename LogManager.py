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




