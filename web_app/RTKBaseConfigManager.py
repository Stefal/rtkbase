import os
from configparser import ConfigParser
from secrets import token_urlsafe

class RTKBaseConfigManager:
    """ A class to easily access the settings from RTKBase settings.conf """

    NON_QUOTED_KEYS = ("basedir", "web_authentification", "new_web_password", "web_password_hash",
                     "flask_secret_key", "archive_name", "user")

    def __init__(self, default_settings_path, user_settings_path):
        """ 
            :param default_settings_path: path to the default settings file 
            :param user_settings_path: path to the user settings file 
        """
        self.user_settings_path = user_settings_path
        self.config = self.merge_default_and_user(default_settings_path, user_settings_path)
        self.expand_path()
        self.write_file(self.config)

    def merge_default_and_user(self, default, user):
        """
            After a software update if there is some new entries in the default settings file,
            we need to add them to the user settings file. This function will do this: It loads
            the default settings then overwrite the existing values from the user settings. Then
            the function write these settings on disk.

            :param default: path to the default settings file 
            :param user: path to the user settings file
            :return: the new config object
        """
        config = ConfigParser(interpolation=None)
        config.read(default)
        #if there is no existing user settings file, config.read return
        #an empty object.
        config.read(user)
        return config


    def parseconfig(self, settings_path):
        """
            Parse the config file with interpolation=None or it will break run_cast.sh
        """
        config = ConfigParser(interpolation=None)
        config.read(settings_path)
        return config

    def expand_path(self):
        """
            get the paths and convert $BASEDIR to the real path
        """
        datadir = self.config.get("local_storage", "datadir")
        if "$BASEDIR" in datadir:
            exp_datadir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", datadir.strip("$BASEDIR/")))
            self.update_setting("local_storage", "datadir", exp_datadir)
        
        logdir = self.config.get("log", "logdir")
        if "$BASEDIR" in logdir:
            exp_logdir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../", logdir.strip("$BASEDIR/")))
            self.update_setting("log", "logdir", exp_logdir)



    def listvalues(self):
        """
            print all keys/values from all sections in the settings
        """
        for section in self.config.sections():
            print("SECTION: {}".format(section))
            for key in self.config[section]:
                print("{} : {} ".format(key, self.config[section].get(key)))

    def get_main_settings(self):
        """
            Get a subset of the settings from the main section in an ordered object
            and remove the single quotes.      
        """
        ordered_main = [{"source_section" : "main"}]
        for key in ("position", "com_port", "com_port_settings", "receiver", "receiver_format", "tcp_port"):
            ordered_main.append({key : self.config.get('main', key).strip("'")})
        return ordered_main

    def get_ntrip_settings(self):
        """
            Get a subset of the settings from the ntrip section in an ordered object
            and remove the single quotes.    
        """
        ordered_ntrip = [{"source_section" : "ntrip"}]
        for key in ("svr_addr", "svr_port", "svr_pwd", "mnt_name", "rtcm_msg"):
            ordered_ntrip.append({key : self.config.get('ntrip', key).strip("'")})
        return ordered_ntrip
    
    def get_file_settings(self):
        """
            Get a subset of the settings from the file section in an ordered object
            and remove the single quotes.       
        """
        ordered_file = [{"source_section" : "local_storage"}]
        for key in ("datadir", "file_name", "file_rotate_time", "file_overlap_time", "archive_rotate"):
            ordered_file.append({key : self.config.get('local_storage', key).strip("'")})
        return ordered_file

    def get_rtcm_svr_settings(self):
        """
            Get a subset of the settings from the file section in an ordered object
            and remove the single quotes.       
        """
        ordered_rtcm_svr = [{"source_section" : "rtcm_svr"}]
        for key in ("rtcm_svr_port", "rtcm_svr_msg"):
            ordered_rtcm_svr.append({key : self.config.get('rtcm_svr', key).strip("'")})
        return ordered_rtcm_svr

    def get_ordered_settings(self):
        """
            Get a subset of the main, ntrip and file sections from the settings file
            Return a dict where values are a list (to keeps the settings ordered)
        """
        ordered_settings = {}
        ordered_settings['main'] = self.get_main_settings()
        ordered_settings['ntrip'] = self.get_ntrip_settings()
        ordered_settings['file'] = self.get_file_settings()
        ordered_settings['rtcm_svr'] = self.get_rtcm_svr_settings()
        return ordered_settings

    def get_web_authentification(self):
        """
            a simple method to convert the web_authentification value
            to a boolean
            :return boolean
        """
        return self.config.getboolean("general", "web_authentification")

    def get_secret_key(self):
        """
            Return the flask secret key, or generate a new one if it doesn't exists
        """
        SECRET_KEY = self.config.get("general", "flask_secret_key", fallback='None')
        if SECRET_KEY is 'None' or SECRET_KEY == '':
            SECRET_KEY = token_urlsafe(48)
            self.update_setting("general", "flask_secret_key", SECRET_KEY)
        
        return SECRET_KEY

    def get(self, *args, **kwargs):
        """
            a wrapper around configparser.get()
        """
        return self.config.get(*args, **kwargs)

    def update_setting(self, section, setting, value, write_file=True):
        """
            Update a setting in the config file and write the file (default)
            If the setting is not in the NON_QUOTED_KEYS list, the method will
            add single quotes
            :param section: the section in the config file
            :param setting: the setting (like a key in a dict)
            :param value: the new value for the setting
            :param write_file: write the file or not
        """
        #Add single quotes around the value
        if setting not in self.NON_QUOTED_KEYS:
            value = "'" + value + "'"
        try:
            self.config[section][setting] = value
            if write_file:
                self.write_file()
        except Exception as e:
            print(e)
            return False

    def write_file(self, settings=None):
        """
            write on disk the settings to the config file
        """
        if settings is None:
            settings = self.config

        with open(self.user_settings_path, "w") as configfile:
            settings.write(configfile, space_around_delimiters=False)
