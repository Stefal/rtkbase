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
        self.default_settings_path = default_settings_path
        self.config = None
        self.merge_default_and_user(default_settings_path, user_settings_path)
        self.expand_path()
        self.write_file(self.config)

    def merge_default_and_user(self, default, user):
        """
            After a software update if there is some new entries in the default settings file,
            we need to add them to the user settings file. This function will do this: It loads
            the default settings then overwrite the existing values from the user settings.

            :param default: path to the default settings file 
            :param user: path to the user settings file
            :return: the new config object
        """
        config = ConfigParser(interpolation=None)
        config.read(default)
        #if there is no existing user settings file, config.read return
        #an empty object.
        config.read(user)
        self.config=config

    def restore_settings(self, default, to_restore):
        """
            Restore backuped settings. Some settings have to be removed in case of restore from
            and older release.

            :param default: path to the default settings file 
            :param to_restore: path to the settings file to restore
        """
        restore_config = ConfigParser(interpolation=None)
        restore_config.read(to_restore)
        restore_config.remove_option("general", "version")
        restore_config.remove_option("general", "checkpoint_version")
        #we don't know if the actual user is the same as the one in the config file
        restore_config.remove_option("general", "user")
        if not os.path.exists(restore_config.get("local_storage", "datadir")):
            restore_config.remove_option("local_storage", "datadir")
        if not os.path.exists(restore_config.get("log", "logdir")):
            restore_config.remove_option("log", "logdir")
        #write restored settings to the current settings
        for section in restore_config.sections():
            for k, v in restore_config[section].items():
                try:
                    if self.config[section].get(k) is not None:
                        self.config[section][k] = v
                    else:
                        raise ValueError(k)
                except KeyError as e:
                    #this section is skipped
                    print("ignored section:", e)
                    pass
                except ValueError as e:
                    print("ignored key", e)

        self.write_file()

    def reload_settings(self, settings_path=None):
        """
            Parse the config file with interpolation=None or it will break run_cast.sh
        """
        settings_path = self.user_settings_path if settings_path is None else settings_path
        config = ConfigParser(interpolation=None)
        config.read(settings_path)
        self.config=config

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
        for key in ("position", "com_port", "com_port_settings", "receiver", "receiver_firmware", "receiver_format", "antenna_info", "tcp_port", "gnss_rcv_web_ip", "gnss_rcv_web_proxy_port"):
            ordered_main.append({key : self.config.get('main', key).strip("'")})
        return ordered_main

    def get_ntrip_A_settings(self):
        """
            Get a subset of the settings from the ntrip A section in an ordered object
            and remove the single quotes.    
        """
        ordered_ntrip = [{"source_section" : "ntrip_A"}]
        for key in ("svr_addr_A", "svr_port_A", "svr_pwd_A", "mnt_name_A", "rtcm_msg_A", "ntrip_A_receiver_options"):
            ordered_ntrip.append({key : self.config.get('ntrip_A', key).strip("'")})
        return ordered_ntrip
    
    def get_ntrip_B_settings(self):
        """
            Get a subset of the settings from the ntrip B section in an ordered object
            and remove the single quotes.    
        """
        #TODO need refactoring with get_ntrip_A_settings
        ordered_ntrip = [{"source_section" : "ntrip_B"}]
        for key in ("svr_addr_B", "svr_port_B", "svr_pwd_B", "mnt_name_B", "rtcm_msg_B", "ntrip_B_receiver_options"):
            ordered_ntrip.append({key : self.config.get('ntrip_B', key).strip("'")})
        return ordered_ntrip

    def get_local_ntripc_settings(self):
        """
            Get a subset of the settings from the local ntrip section in an ordered object
            and remove the single quotes.    
        """
        ordered_local_ntripc = [{"source_section" : "local_ntrip_caster"}]
        for key in ("local_ntripc_user", "local_ntripc_pwd", "local_ntripc_port", "local_ntripc_mnt_name", "local_ntripc_msg", "local_ntripc_receiver_options"):
            ordered_local_ntripc.append({key : self.config.get('local_ntrip_caster', key).strip("'")})
        return ordered_local_ntripc
    
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
        for key in ("rtcm_svr_port", "rtcm_svr_msg", "rtcm_receiver_options"):
            ordered_rtcm_svr.append({key : self.config.get('rtcm_svr', key).strip("'")})
        return ordered_rtcm_svr

    def get_rtcm_client_settings(self):
        """
            Get a subset of the settings from the file section in an ordered object
            and remove the single quotes.       
        """
        ordered_rtcm_client = [{"source_section" : "rtcm_client"}]
        for key in ("rtcm_client_addr", "rtcm_client_port", "rtcm_client_user", "rtcm_client_pwd", "rtcm_client_msg", "rtcm_client_receiver_options"):
            ordered_rtcm_client.append({key : self.config.get('rtcm_client', key).strip("'")})
        return ordered_rtcm_client

    def get_rtcm_udp_svr_settings(self):
        """
            Get a subset of the settings from the file section in an ordered object
            and remove the single quotes.       
        """
        ordered_rtcm_udp_svr = [{"source_section" : "rtcm_udp_svr"}]
        for key in ("rtcm_udp_svr_port", "rtcm_udp_svr_msg", "rtcm_udp_svr_receiver_options"):
            ordered_rtcm_udp_svr.append({key : self.config.get('rtcm_udp_svr', key).strip("'")})
        return ordered_rtcm_udp_svr

    def get_rtcm_udp_client_settings(self):
        """
            Get a subset of the settings from the file section in an ordered object
            and remove the single quotes.       
        """
        ordered_rtcm_udp_client = [{"source_section" : "rtcm_udp_client"}]
        for key in ("rtcm_udp_client_addr", "rtcm_udp_client_port", "rtcm_udp_client_msg", "rtcm_udp_client_receiver_options"):
            ordered_rtcm_udp_client.append({key : self.config.get('rtcm_udp_client', key).strip("'")})
        return ordered_rtcm_udp_client
       
    def get_rtcm_serial_settings(self):
        """
            Get a subset of the settings from the file section in an ordered object
            and remove the single quotes.       
        """
        ordered_rtcm_serial = [{"source_section" : "rtcm_serial"}]
        for key in ("out_com_port", "out_com_port_settings", "rtcm_serial_msg", "rtcm_serial_receiver_options"):
            ordered_rtcm_serial.append({key : self.config.get('rtcm_serial', key).strip("'")})
        return ordered_rtcm_serial

    def get_ordered_settings(self):
        """
            Get a subset of the main, ntrip and file sections from the settings file
            Return a dict where values are a list (to keeps the settings ordered)
        """
        ordered_settings = {}
        ordered_settings['main'] = self.get_main_settings()
        ordered_settings['ntrip_A'] = self.get_ntrip_A_settings()
        ordered_settings['ntrip_B'] = self.get_ntrip_B_settings()
        ordered_settings['local_ntripc'] = self.get_local_ntripc_settings()
        ordered_settings['file'] = self.get_file_settings()
        ordered_settings['rtcm_svr'] = self.get_rtcm_svr_settings()
        ordered_settings['rtcm_client'] = self.get_rtcm_client_settings()
        ordered_settings['rtcm_udp_svr'] = self.get_rtcm_udp_svr_settings()
        ordered_settings['rtcm_udp_client'] = self.get_rtcm_udp_client_settings()
        ordered_settings['rtcm_serial'] = self.get_rtcm_serial_settings()
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
        if SECRET_KEY == 'None' or SECRET_KEY == '':
            SECRET_KEY = token_urlsafe(48)
            self.update_setting("general", "flask_secret_key", SECRET_KEY)
        
        return SECRET_KEY

    def sections(self, *args, **kwargs):
        """
            a wrapper around configparser.sections()
        """
        return self.config.sections()

    def get(self, *args, **kwargs):
        """
            a wrapper around configparser.get()
        """
        return self.config.get(*args, **kwargs)
    
    def getboolean(self, *args, **kwargs):
        """
            a wrapper around configparser.getboolean()
        """
        return self.config.getboolean(*args, **kwargs)

    def remove_option(self, *args, **kwargs):
        """
            a wrapper around configparser.remove_option()
        """
        return self.config.remove_option(*args, **kwargs)
    
    def remove_section(self, *args, **kwargs):
        """
            a wrapper around configparser.remove_section()
        """
        return self.config.remove_section(*args, **kwargs)
    
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
