#!/usr/bin/python

# This Flask app is a heavily modified version of Reachview
# modified to be used as a front end for GNSS base
# author: Stéphane Péneau
# source: https://github.com/Stefal/rtkbase

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

from gevent import monkey
monkey.patch_all()

import time
import json
import os
import shutil
import sys
import requests
import tempfile
import argparse
import html

from threading import Thread
from RTKLIB import RTKLIB
from ServiceController import ServiceController
from RTKBaseConfigManager import RTKBaseConfigManager
import network_infos

#print("Installing all required packages")
#provisioner.provision_reach()

#import reach_bluetooth.bluetoothctl
#import reach_bluetooth.tcp_bridge

from flask_bootstrap import Bootstrap4
from flask import Flask, render_template, session, request, flash, url_for
from flask import send_from_directory, redirect, abort
from flask import g
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from wtforms.validators import ValidationError, DataRequired, EqualTo
from flask_socketio import SocketIO, emit, disconnect
import urllib
import subprocess
import psutil
import distro
import socket

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.utils import safe_join
import gunicorn.app.base

app = Flask(__name__)
app.debug = False
app.config["SECRET_KEY"] = "secret!"
#app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "../logs")
app.config["DOWNLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "../data")
app.config["LOGIN_DISABLED"] = False
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 128
app.config['UPLOAD_EXTENSIONS'] = ['.conf', '.txt', 'ini']

rtkbase_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
path_to_rtklib = "/usr/local/bin" #TODO find path with which or another tool

login=LoginManager(app)
login.login_view = 'login_page'
socketio = SocketIO(app, async_mode = 'gevent')
bootstrap = Bootstrap4(app)

#Get settings from settings.conf.default and settings.conf
rtkbaseconfig = RTKBaseConfigManager(os.path.join(rtkbase_path, "settings.conf.default"), os.path.join(rtkbase_path, "settings.conf"))

rtk = RTKLIB(socketio,
            rtklib_path=path_to_rtklib,
            log_path=app.config["DOWNLOAD_FOLDER"],
            )

services_list = [{"service_unit" : "str2str_tcp.service", "name" : "main"},
                 {"service_unit" : "str2str_ntrip_A.service", "name" : "ntrip_A"},
                 {"service_unit" : "str2str_ntrip_B.service", "name" : "ntrip_B"},
                 {"service_unit" : "str2str_local_ntrip_caster.service", "name" : "local_ntrip_caster"},
                 {"service_unit" : "str2str_rtcm_svr.service", "name" : "rtcm_svr"},
                 {'service_unit' : 'str2str_rtcm_serial.service', "name" : "rtcm_serial"},
                 {"service_unit" : "str2str_file.service", "name" : "file"},
                 {'service_unit' : 'rtkbase_archive.timer', "name" : "archive_timer"},
                 {'service_unit' : 'rtkbase_archive.service', "name" : "archive_service"},
                 {'service_unit' : 'rtkbase_raw2nmea.service', "name" : "raw2nmea"},
                 {'service_unit' : 'rtkbase_gnss_web_proxy.service', "name": "RTKBase Reverse Proxy for Gnss receiver Web Server"},
                 {'service_unit' : 'configure_gps.service', "name" : "configure_gps"},
                 ]

#Delay before rtkrcv will stop if no user is on status.html page
rtkcv_standby_delay = 600
connected_clients = 0

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

class User(UserMixin):
    """ Class for user authentification """
    def __init__(self, username):
        self.id=username
        self.password_hash = rtkbaseconfig.get("general", "web_password_hash")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoginForm(FlaskForm):
    """ Class for the loginform"""
    #username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Please enter the RTKBase password:', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

def update_password(config_object):
    """
        Check in settings.conf if web_password entry contains a value
        If yes, this function will generate a new hash for it and
        remove the web_password value
        :param config_object: a RTKBaseConfigManager instance
    """
    new_password = config_object.get("general", "new_web_password")
    if new_password != "":
        config_object.update_setting("general", "web_password_hash", generate_password_hash(new_password))
        config_object.update_setting("general", "new_web_password", "")

def manager():
    """ This manager runs inside a separate thread
        It checks how long rtkrcv is running since the last user leaves the
        status web page, and stop rtkrcv when sleep_count reaches rtkrcv_standby delay
        And it sends various system informations to the web interface
    """
    max_cpu_temp = 0
    cpu_temp_offset = int(rtkbaseconfig.get("general", "cpu_temp_offset"))
    services_status = getServicesStatus(emit_pingback=False)
    main_service = {}
    while True:
        # Make sure max_cpu_temp is always updated
        cpu_temp = get_cpu_temp() + cpu_temp_offset
        max_cpu_temp = max(cpu_temp, max_cpu_temp)

        if connected_clients > 0:
            # We only need to emit to the socket if there are clients able to receive it.
            updated_services_status = getServicesStatus(emit_pingback=False)
            main_service = updated_services_status[0]
            if  services_status != updated_services_status:
                services_status = updated_services_status
                socketio.emit("services status", json.dumps(services_status), namespace="/test")
                #print("service status", services_status)

            try:
                interfaces_infos = network_infos.get_interfaces_infos()
            except Exception:
                # network-manager not installed ?
                interfaces_infos = None

            volume_usage = get_volume_usage()
            sys_infos = {"cpu_temp" : cpu_temp,
                        "max_cpu_temp" : max_cpu_temp,
                        "uptime" : get_uptime(),
                        "volume_free" : round(volume_usage.free / 10E8, 2),
                        "volume_used" : round(volume_usage.used / 10E8, 2),
                        "volume_total" : round(volume_usage.total / 10E8, 2),
                        "volume_percent_used" : volume_usage.percent,
                        "network_infos" : interfaces_infos}
            socketio.emit("sys_informations", json.dumps(sys_infos), namespace="/test")

        if rtk.sleep_count > rtkcv_standby_delay and rtk.state != "inactive" or \
                 main_service.get("active") == False and rtk.state != "inactive":
            print("DEBUG Stopping rtkrcv")
            if rtk.stopBase() == 1:
                rtk.sleep_count = 0
        elif rtk.sleep_count > rtkcv_standby_delay:
            print("I'd like to stop rtkrcv (sleep_count = {}), but rtk.state is: {}".format(rtk.sleep_count, rtk.state))
        time.sleep(1)

def repaint_services_button(services_list):
    """
       set service color on web app frontend depending on the service status:
       status = running => green button
        status = auto-restart => orange button (alert)
        result = exit-code => red button (danger)
    """ 
    for service in services_list:
        if service.get("status") == "running":
            service["btn_color"] = "success"
        #elif service.get("status") == "dead":
        #    service["btn_color"] = "danger"
        elif service.get("result") == "exit-code":
            service["btn_color"] = "warning"
        elif service.get("status") == "auto-restart":
            service["btn_color"] = "warning"

        if service.get("state_ok") == False:
            service["btn_off_color"] = "outline-danger"
        elif service.get("state_ok") == True:
            service["btn_off_color"] = "outline-secondary"

    return services_list

def old_get_cpu_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as ftemp:
            current_temp = int(ftemp.read()) / 1000
        print(current_temp)
    except:
        print("can't get cpu temp")
        current_temp = 75
    return current_temp

def get_cpu_temp():
    try:
        temps = psutil.sensors_temperatures()
        current_cpu_temp = round(temps.get('cpu_thermal')[0].current, 1)
    except:
        current_cpu_temp = 0
    return current_cpu_temp

def get_uptime():
    return round(time.time() - psutil.boot_time())

def get_volume_usage(volume = rtk.logm.log_path):
    try:
        volume_info = psutil.disk_usage(volume)
    except FileNotFoundError:
        volume_info = psutil.disk_usage("/")
    return volume_info

def get_sbc_model():
    """
        Try to detect the single board computer used
        :return the model name or unknown if not detected
    """
    answer = subprocess.run(["cat", "/proc/device-tree/model"], encoding="UTF-8", stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=False)
    if answer.returncode == 0:
        sbc_model = answer.stdout.split("\n").pop().strip()
    else:
        sbc_model = "unknown"
    return sbc_model

@socketio.on("check update", namespace="/test")
def check_update(source_url = None, current_release = None, prerelease=rtkbaseconfig.getboolean("general", "prerelease"), return_emit = True):
    """
        Check if a RTKBase update exists
        :param source_url: the url where we will try to find an update. It uses the github api.
        :param current_release: The current RTKBase release
        :param prerelease: True/False Get prerelease or not
        :param emit: send the result to the web front end with socketio
        :return The new release version inside a dict (release version and url for this release)
    """
    ## test
    #new_release = {'url' : 'http://localhost', 'new_release' : "3.9", "comment" : "blabla"}
    #if emit:
    #    socketio.emit("new release", json.dumps(new_release), namespace="/test")
    #return new_release
    ## test
    new_release = {}
    source_url = source_url if source_url is not None else "https://api.github.com/repos/stefal/rtkbase/releases"
    current_release = current_release if current_release is not None else rtkbaseconfig.get("general", "version").strip("v")
    current_release = current_release.split("-beta", 1)[0].split("-alpha", 1)[0].split("-rc", 1)[0].split("b", 1)[0]

    try:
        response = requests.get(source_url)
        response = response.json()
        for release in response:
            if release.get("prerelease") & prerelease or release.get("prerelease") == False:
                latest_release = release.get("tag_name").strip("v").replace("-beta", "").replace("-alpha", "").replace("-rc", "")
                if latest_release > current_release and latest_release <= rtkbaseconfig.get("general", "checkpoint_version"):
                    new_release = {"new_release" : release.get("tag_name"), "comment" : release.get("body")}
                    #find url for rtkbase.tar.gz
                    for i, asset in enumerate(release["assets"]):
                        if "rtkbase.tar.gz" in asset["name"]:
                            new_release["url"] = asset.get("browser_download_url")
                            break
                    break

    except Exception as e:
        print("Check update error: ", e)
        new_release = { "error" : repr(e)}

    if return_emit:
        socketio.emit("new release", json.dumps(new_release), namespace="/test")
    return new_release

@socketio.on("update rtkbase", namespace="/test")
def update_rtkbase(update_file=False):
    """
        Check if a RTKBase update exists, download it and update rtkbase
        if update_file is a link to a file, use it to update rtkbase (mainly used for dev purpose)
    """

    shutil.rmtree("/var/tmp/rtkbase", ignore_errors=True)
    import tarfile

    if not update_file:
        #Check if an update is available
        update_url = check_update(return_emit=False).get("url")
        if update_url is None:
            return
        #Download update
        update_archive = download_update(update_url)
    else:
        #update from file
        update_file.save("/var/tmp/rtkbase_update.tar.gz")
        update_archive = "/var/tmp/rtkbase_update.tar.gz"
        print("update stored in /var/tmp/")

    if update_archive is None:
        socketio.emit("downloading_update", json.dumps({"result": 'false'}), namespace="/test")
        return
    else:
        socketio.emit("downloading_update", json.dumps({"result": 'true'}), namespace="/test")

    #Get the "root" folder in the archive
    tar = tarfile.open(update_archive)
    for tarinfo in tar:
        if tarinfo.isdir():
            primary_folder = tarinfo.name
            break
    #Delete previous update directory
    try:
        os.rmdir("/var/tmp/rtkbase")
    except FileNotFoundError:
        print("/var/tmp/rtkbase directory doesn't exist")

    #Extract archive
    tar.extractall("/var/tmp")

    source_path = os.path.join("/var/tmp/", primary_folder)
    script_path = os.path.join(source_path, "tools", "rtkbase_update.sh")
    data_dir = app.config["DOWNLOAD_FOLDER"].split("/")[-1]
    current_release = rtkbaseconfig.get("general", "version").strip("v")
    standard_user = rtkbaseconfig.get("general", "user")
    #launch update verifications
    answer = subprocess.run([script_path, source_path, rtkbase_path, data_dir, current_release, standard_user, "--checking"], encoding="UTF-8", stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=False)
    if answer.returncode != 0:
        socketio.emit("updating_rtkbase_stopped", json.dumps({"error" : answer.stderr.splitlines()}), namespace="/test")
        print("Checking OS release failed. Update aborted!")
    else : #if ok, launch update script
        print("Launch update")
        socketio.emit("updating_rtkbase", namespace="/test")
        rtk.shutdownBase()
        time.sleep(1)
        #update_service=ServiceController('rtkbase_update.service')
        #update_service.start()
        subprocess.Popen([script_path, source_path, rtkbase_path, data_dir, current_release, standard_user])
        #os.execl('/var/tmp/rtkbase_update.sh', "unused arg0", source_path, rtkbase_path, data_dir, current_release, standard_user)

def download_update(update_path):
    update_archive = "/var/tmp/rtkbase_update.tar.gz"
    try:
        response = requests.get(update_path)
        with open(update_archive, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print("Error: Can't download update - ", e)
        return None
    else:
        return update_archive

@app.before_request
def inject_release():
    """
        Insert the RTKBase release number as a global variable for Flask/Jinja
    """
    g.version = rtkbaseconfig.get("general", "version")
    g.sbc_model = get_sbc_model()

@login.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
@app.route('/index')
@app.route('/status')
@login_required
def status_page():
    """
        The status web page with the gnss satellites levels and a map
    """
    base_position = rtkbaseconfig.get("main", "position").replace("'", "").split()
    base_coordinates = {"lat" : base_position[0], "lon" : base_position[1]}
    return render_template("status.html", base_coordinates = base_coordinates, tms_key = {"maptiler_key" : rtkbaseconfig.get("general", "maptiler_key")})

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    """
        The settings page where you can manage the various services, the parameters, update, power...
    """
    # POST method when updating with a manual file
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            update_rtkbase(uploaded_file)
        else:
            print("wrong update file")
        return ('', 204)
    # variable needed when the gnss receiver offer a web interface
    host_url =  urllib.parse.urlparse(request.host_url)
    gnss_rcv_url = urllib.parse.ParseResult(scheme=host_url.scheme,
                                            netloc="{}:{}".format(host_url.hostname, rtkbaseconfig.get("main", "gnss_rcv_web_proxy_port")),
                                            path=host_url.path,
                                            params=host_url.params, query=host_url.query,
                                            fragment=host_url.fragment)
    #TODO use dict and not list
    main_settings = rtkbaseconfig.get_main_settings()
    main_settings.append(gnss_rcv_url.geturl())
    ntrip_A_settings = rtkbaseconfig.get_ntrip_A_settings()
    ntrip_B_settings = rtkbaseconfig.get_ntrip_B_settings()
    local_ntripc_settings = rtkbaseconfig.get_local_ntripc_settings()
    rtcm_svr_settings = rtkbaseconfig.get_rtcm_svr_settings()
    rtcm_client_settings = rtkbaseconfig.get_rtcm_client_settings()
    rtcm_udp_svr_settings = rtkbaseconfig.get_rtcm_udp_svr_settings()
    rtcm_udp_client_settings = rtkbaseconfig.get_rtcm_udp_client_settings()
    rtcm_serial_settings = rtkbaseconfig.get_rtcm_serial_settings()
    file_settings = rtkbaseconfig.get_file_settings()

    return render_template("settings.html", main_settings = main_settings,
                                            ntrip_A_settings = ntrip_A_settings,
                                            ntrip_B_settings = ntrip_B_settings,
                                            local_ntripc_settings = local_ntripc_settings,
                                            rtcm_svr_settings = rtcm_svr_settings,
                                            rtcm_client_settings = rtcm_client_settings,
                                            rtcm_udp_svr_settings = rtcm_udp_svr_settings,
                                            rtcm_udp_client_settings = rtcm_udp_client_settings,
                                            rtcm_serial_settings = rtcm_serial_settings,
                                            file_settings = file_settings,
                                            os_infos = distro.info(),)

@app.route('/logs')
@login_required
def logs_page():
    """
        The data web pages where you can download/delete the raw gnss data
    """
    return render_template("logs.html")

@app.route("/logs/download/<path:log_name>")
@login_required
def downloadLog(log_name):
    """ Route for downloading raw gnss data"""
    try:
        return send_from_directory(rtk.logm.log_path, log_name, as_attachment = True)
    except FileNotFoundError:
        abort(404)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('status_page'))
    loginform = LoginForm()
    if loginform.validate_on_submit():
        user = User('admin')
        password = loginform.password.data
        if not user.check_password(password):
            return abort(401)

        login_user(user, remember=loginform.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urllib.parse.urlsplit(next_page).netloc != '':
            next_page = url_for('status_page')

        return redirect(next_page)

    return render_template('login.html', title='Sign In', form=loginform)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login_page'))

@app.route('/diagnostic')
@login_required
def diagnostic():
    """
    Get services journal and status
    """
    getServicesStatus()
    rtkbase_web_service = {'service_unit' : 'rtkbase_web.service', 'name' : 'RTKBase Web Server', 'active' : True}
    logs = []
    for service in services_list + [rtkbase_web_service]:
        sysctl_status = subprocess.run(['systemctl', 'status', service['service_unit']],
                                stdout=subprocess.PIPE,
                                universal_newlines=True,
                                check=False)
        journalctl = subprocess.run(['journalctl', '--since', '7 days ago', '-u', service['service_unit']], 
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True,
                                 check=False)
        
        #Replace carrier return to <br> for html view
        sysctl_status = html.escape(sysctl_status.stdout.replace('\n', '<br>'))
        journalctl = html.escape(journalctl.stdout.replace('\n', '<br>'))
        active_state = "Active" if service.get('active') == True else "Inactive"
        logs.append({'name' : service['service_unit'], 'active' : active_state, 'sysctl_status' : sysctl_status, 'journalctl' : journalctl})
        
    return render_template('diagnostic.html', logs = logs)


@app.route('/api/v1/infos', methods=['GET'])
def get_infos():
    """Small api route to get basic informations about the base station"""

    infos = {"app" : "RTKBase",
             "app_version" : rtkbaseconfig.get("general", "version"), 
             "url" : html.escape(request.base_url),
             "fqdn" : socket.getfqdn(),
             "uptime" : get_uptime(),
             "hostname" : socket.gethostname()}
    return json.dumps(infos)

#### Handle connect/disconnect events ####

@socketio.on("connect", namespace="/test")
def clientConnect():
    global connected_clients
    connected_clients += 1
    print("Browser client connected")
    if rtkbaseconfig.get("general", "updated", fallback="False").lower() == "true":
        rtkbaseconfig.remove_option("general", "updated")
        rtkbaseconfig.write_file()
        socketio.emit("update_successful", json.dumps({"result": 'true'}), namespace="/test")
    rtk.sendState()

@socketio.on("disconnect", namespace="/test")
def clientDisconnect():
    global connected_clients
    connected_clients -=1
    print("Browser client disconnected")

#### Log list handling ###

@socketio.on("get logs list", namespace="/test")
def getAvailableLogs():
    #print("DEBUG updating logs")
    rtk.logm.updateAvailableLogs()
    #print("Updated logs list is " + str(rtk.logm.available_logs))
    rtk.socketio.emit("available logs", rtk.logm.available_logs, namespace="/test")

#### str2str launch/shutdown handling ####

@socketio.on("launch base", namespace="/test")
def launchBase():
    rtk.launchBase()

@socketio.on("shutdown base", namespace="/test")
def shutdownBase():
    rtk.shutdownBase()

#### str2str start/stop handling ####

@socketio.on("start base", namespace="/test")
def startBase():
    saved_input_type = rtkbaseconfig.get("main", "receiver_format").strip("'")
    #check if the main service is running and the gnss format is correct. If not, don't try to start rtkrcv with startBase() 
    if services_list[0].get("active") is False or saved_input_type not in ["rtcm2","rtcm3","nov","oem3","ubx","ss2","hemis","stq","javad","nvs","binex","rt17","sbf", "unicore"]:
        print("DEBUG: Can't start rtkrcv as main service isn't enabled or gnss format is wrong")
        result = {"result" : "failed"}
        socketio.emit("base starting", json.dumps(result), namespace="/test")
        return
    # We must start rtkcv before trying to modify an option
    rtk.startBase()
    saved_input_path = "localhost" + ":" + rtkbaseconfig.get("main", "tcp_port").strip("'")
    if rtk.get_rtkcv_option("inpstr1-path") != saved_input_path:
        rtk.set_rtkcv_option("inpstr1-path", saved_input_path)
        rtk.set_rtkcv_pending_refresh(True)
    if rtk.get_rtkcv_option("inpstr1-format") != saved_input_type:
        rtk.set_rtkcv_option("inpstr1-format", saved_input_type)
        rtk.set_rtkcv_pending_refresh(True)

    if rtk.get_rtkcv_pending_status():
        print("REFRESH NEEDED !!!!!!!!!!!!!!!!")
        rtk.startBase()

@socketio.on("stop base", namespace="/test")
def stopBase():
    rtk.stopBase()

@socketio.on("on graph", namespace="/test")
def continueBase():
    rtk.sleep_count = 0

#### Delete log button handler ####

@socketio.on("delete log", namespace="/test")
def deleteLog(json_msg):
    rtk.logm.deleteLog(json_msg.get("name"))
    # Sending the the new available logs
    getAvailableLogs()

#### Detect GNSS receiver button handler ####

@socketio.on("detect_receiver", namespace="/test")
def detect_receiver(json_msg):
    print("Detecting gnss receiver")
    #print("DEBUG json_msg: ", json_msg)
    answer = subprocess.run([os.path.join(rtkbase_path, "tools", "install.sh"), "--user", rtkbaseconfig.get("general", "user"), "--detect-gnss", "--no-write-port"], encoding="UTF-8", stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=False)
    if answer.returncode == 0 and "/dev/" in answer.stdout:
        #print("DEBUG ok stdout: ", answer.stdout)
        try:
            device_info = next(x for x in answer.stdout.splitlines() if x.startswith('/dev/')).split(' - ')
            port, gnss_type, speed, firmware = [x.strip() for x in device_info]
            result = {"result" : "success", "port" : port, "gnss_type" : gnss_type, "port_speed" : speed, "firmware" : firmware}
            result.update(json_msg)
        except Exception:
            result = {"result" : "failed"}
    else:
        #print("DEBUG Not ok stdout: ", answer.stdout)
        result = {"result" : "failed"}
    #result = {"result" : "failed"}
    #result = {"result" : "success", "port" : "/dev/ttybestport", "gnss_type" : "F12P", "port_speed" : "115200", "firmware" : "1.55"}
    result.update(json_msg) ## get back "then_configure" key/value
    socketio.emit("gnss_detection_result", json.dumps(result), namespace="/test")

@socketio.on("apply_receiver_settings", namespace="/test")
def apply_receiver_settings(json_msg):
    print("Applying gnss receiver new settings")
    print(json_msg)
    rtkbaseconfig.update_setting("main", "com_port", json_msg.get("port").strip("/dev/"), write_file=False)
    rtkbaseconfig.update_setting("main", "com_port_settings", json_msg.get("port_speed") + ':8:n:1', write_file=False)
    rtkbaseconfig.update_setting("main", "receiver", json_msg.get("gnss_type"), write_file=False)
    rtkbaseconfig.update_setting("main", "receiver_firmware", json_msg.get("firmware"), write_file=True)

    socketio.emit("gnss_settings_saved", json.dumps(json_msg), namespace="/test")

@socketio.on("configure_receiver", namespace="/test")
def configure_receiver(brand="", model=""):
    # only some receiver could be configured automaticaly
    # After port detection, the main service will be restarted, and it will take some time. But we have to stop it to
    # configure the receiver. We wait a few seconds before stopping it to remove conflicting calls.
    time.sleep(4)
    main_service = services_list[0]
    if main_service.get("active") is True:
        main_service["unit"].stop()
        restart_main = True
    else:
        restart_main = False

    print("configuring {} gnss receiver model {}".format(brand, model))
    answer = subprocess.run([os.path.join(rtkbase_path, "tools", "install.sh"), "--user", rtkbaseconfig.get("general", "user"), "--configure-gnss"], encoding="UTF-8", stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=False)
    #print("DEBUG - stdout: ", answer.stdout)
    #print("DEBUG - returncode: ", answer.returncode)

    if answer.returncode == 0: # and "Done" in answer.stdout:
        result = {"result" : "success"}
        rtkbaseconfig.reload_settings()
    else:
        result = {"result" : "failed"}
    if restart_main is True:
        #print("DEBUG: Restarting main service after F9P configuration")
        main_service["unit"].start()
    #result = {"result" : "success"}
    socketio.emit("gnss_configuration_result", json.dumps(result), namespace="/test")

#### Settings Backup Restore Reset ####

@socketio.on("reset settings", namespace="/test")
def reset_settings():
    switchService({"name":"main", "active":False})
    rtkbaseconfig.merge_default_and_user(os.path.join(rtkbase_path, "settings.conf.default"), os.path.join(rtkbase_path, "settings.conf.default"))
    rtkbaseconfig.expand_path()
    rtkbaseconfig.write_file()
    update_std_user(services_list)
    socketio.emit("settings_reset", namespace="/test")

@app.route("/logs/download/settings")
@login_required
def backup_settings():
    settings_file_name = str("RTKBase_{}_{}_{}.conf".format(rtkbaseconfig.get("general", "version"), rtkbaseconfig.get("ntrip_A", "mnt_name_a").strip("'"), time.strftime("%Y-%m-%d_%HH%M")))
    #return send_file(os.path.join(rtkbase_path, "settings.conf"), as_attachment=True, download_name=settings_file_name)
    return send_from_directory(rtkbase_path, "settings.conf", as_attachment=True, download_name=settings_file_name)


@socketio.on("restore settings", namespace="/test")
def restore_settings_file(json_msg):
    #print("DEBUG: type: ", type(json_msg))
    #print("DEBUG: print msg: ", msg)
    #print("DEBUG: filename: ", json_msg["filename"])
    try:
        if not json_msg["filename"].lower().endswith(".conf"):
            raise TypeError("Wrong file type")
        if not "[general]" in json_msg["data"].decode():
            raise ValueError(("Not a valid RTKBase settings file"))
        tmp_file = tempfile.NamedTemporaryFile()
        with open(tmp_file.name, 'wb') as file:
            file.write(json_msg["data"])
        rtkbaseconfig.restore_settings(os.path.join(rtkbase_path, "settings.conf.default"), tmp_file.name)
    except TypeError as e:
        #print("DEBUG: ", e)
        result= {"result" : "failed", "msg" : "The file should be a .conf filetype"}
    except ValueError as e:
        #print("DEBUG: ", e)
        result= {"result" : "failed", "msg" : "The file is invalid"}
    except Exception as e:
        #print("DEBUG: Settings restoration error")
        #print("DEBUG: ", e)
        result= {"result" : "failed", "msg" : "Unknown error"}
    else:
        result= {"result" : "success", "msg" : "Successful restoration, You will be redirect to the login page in 5 seconds"}
        restartServices()
    finally:
        socketio.emit("restore_settings_result", json.dumps(result), namespace="/test")

#### Convert ubx file to rinex ####

@socketio.on("rinex conversion", namespace="/test")
def rinex_ign(json_msg):
    #print("DEBUG: json convbin: ", json_msg)
    rinex_type = {"rinex_ign" : "ign", "rinex_nrcan" : "nrcan", "rinex_30s_full" : "30s_full", "rinex_1s_full" : "1s_full"}.get(json_msg.get("rinex-preset"))
    convpath = os.path.abspath(os.path.join(rtkbase_path, "tools", "convbin.sh"))
    convbin_user = rtkbaseconfig.get("general", "user").strip("'")
    #print("DEBUG", convpath, json_msg.get("filename"), rtk.logm.log_path, rinex_type)
    answer = subprocess.run(["sudo", "-u", convbin_user, convpath, json_msg.get("filename"), rtk.logm.log_path, rinex_type], encoding="UTF-8", stderr=subprocess.PIPE, stdout=subprocess.PIPE, check=False)
    if answer.returncode == 0 and "rinex_file=" in answer.stdout:
        rinex_file = answer.stdout.split("\n").pop().strip("rinex_file=")
        result = {"result" : "success", "file" : rinex_file}
    else:
        result = {"result" : "failed", "msg" : answer.stderr}
    #print("DEBUG: ", result)
    socketio.emit("rinex ready", json.dumps(result), namespace="/test")

#### Download and convert log handlers ####

@socketio.on("process log", namespace="/test")
def processLog(json_msg):
    log_name = json_msg.get("name")

    print("Got signal to process a log, name = " + str(log_name))
    print("Path to log == " + rtk.logm.log_path + "/" + str(log_name))

    raw_log_path = rtk.logm.log_path + "/" + log_name
    rtk.processLogPackage(raw_log_path)

@socketio.on("cancel log conversion", namespace="/test")
def cancelLogConversion(json_msg):
    log_name = json_msg.get("name")
    raw_log_path = rtk.logm.log_path + "/" + log_name
    rtk.cancelLogConversion(raw_log_path)

#### RINEX versioning ####

@socketio.on("read RINEX version", namespace="/test")
def readRINEXVersion():
    rinex_version = rtk.logm.getRINEXVersion()
    rtk.socketio.emit("current RINEX version", {"version": rinex_version}, namespace="/test")

@socketio.on("write RINEX version", namespace="/test")
def writeRINEXVersion(json_msg):
    rinex_version = json_msg.get("version")
    rtk.logm.setRINEXVersion(rinex_version)

#### Device hardware functions ####

@socketio.on("reboot device", namespace="/test")
def rebootRtkbase():
    print("Rebooting...")
    rtk.shutdown()
    #socketio.stop() hang. I disabled it
    #socketio.stop()
    subprocess.check_output("reboot")

@socketio.on("shutdown device", namespace="/test")
def shutdownRtkbase():
    print("Shutdown...")
    rtk.shutdown()
    #socketio.stop() hang. I disabled it
    #socketio.stop()
    subprocess.check_output(["shutdown", "now"])

@socketio.on("turn off wi-fi", namespace="/test")
def turnOffWiFi():
    print("Turning off wi-fi")
#    subprocess.check_output("rfkill block wlan", shell = True)

#### Systemd Services functions ####

def load_units(services):
    """
        load unit service before getting status
        :param services: A list of systemd services (dict) containing a service_unit key:value
        :return The dict list updated with the pystemd ServiceController object

        example: 
            services = [{"service_unit" : "str2str_tcp.service"}]
            return will be [{"service_unit" : "str2str_tcp.service", "unit" : a pystemd object}]
        
    """
    for service in services:
        service["unit"] = ServiceController(service["service_unit"])
    return services

def update_std_user(services):
    """
        check which user run str2str_file service and update settings.conf
        :param services: A list of systemd services (dict) containing a service_unit key:value
    """
    service = next(x for x in services_list if x["name"] == "file")
    user = service["unit"].getUser()
    rtkbaseconfig.update_setting("general", "user", user)

def restartServices(restart_services_list=None):
    """
        Restart already running services
        This function will refresh all services status, then compare the global services_list and 
        then restart_services_list to find the services we need to restart.
        #TODO I don't really like this global services_list use.
    """
    if restart_services_list == None:
        restart_services_list = [unit["name"] for unit in services_list if unit["name"] not in ("archive_timer", "archive_service")]
    #Update services status
    for service in services_list:
        service["active"] = service["unit"].isActive()

    #Restart running services
    for restart_service in restart_services_list:
        for service in services_list:
            if service["name"] == restart_service and service["active"] is True:
                print("Restarting service: ", service["name"])
                if service["name"] == "main":
                    #the main service should be stopped during at least 1 second to let rtkrcv stop too.
                    #another solution would be to call rtk.stopbase()
                    #service["unit"].stop()
                    #time.sleep(1.5)
                    #service["unit"].start()
                    rtk.stopBase()
                    service["unit"].restart()
                else:
                    service["unit"].restart()

    #refresh service status
    time.sleep(1)
    getServicesStatus()

@socketio.on("get services status", namespace="/test")
def getServicesStatus(emit_pingback=True):
    """
        Get the status of services listed in services_list
        (services_list is global)
        
        :param emit_pingback: whether or not the services status is sent to clients 
            (defaults to true as the socketio.on() should receive back the information)
        :return The gathered services status list
    """

    #print("Getting services status")
    for service in services_list:
        try:
            #print("unit qui déconne : ", service["name"])
            service["active"] = service["unit"].isActive()
            service["status"] = service["unit"].status()
            service["result"] = service["unit"].get_result()
            if service.get("result") == "success" and service.get("status") == "running":
                service["state_ok"] = True
            elif service.get("result") == "exit-code":
                service["state_ok"] = False
            else:
                service["state_ok"] = None

        except Exception as e:
            print("Error getting service info for: {} - {}".format(service['name'], e))
            pass

    services_status = []
    for service in services_list:
        services_status.append({key:service[key] for key in service if key != 'unit'})

    services_status = repaint_services_button(services_status)
    #print(services_status)
    if emit_pingback:
        socketio.emit("services status", json.dumps(services_status), namespace="/test")
    return services_status

@socketio.on("services switch", namespace="/test")
def switchService(json_msg):
    """
        Start or stop some systemd services
        As a service could need some time to start or stop, there is a 5 seconds sleep
        before refreshing the status.
        param: json_msg: A json var from the web front end containing one or more service
        name with their new status.
    """
    #print("Received service to switch", json_msg)
    try:
        for service in services_list:
            if json_msg["name"] == service["name"] and json_msg["active"] == True:
                print("Trying to start service {}".format(service["name"]))
                service["unit"].start()
            elif json_msg["name"] == service["name"] and json_msg["active"] == False:
                print("Trying to stop service {}".format(service["name"]))
                service["unit"].stop()

    except Exception as e:
        print(e)
    # finally not needed anymore since the service status is refreshed continuously
    # with the manager
    #finally:
    #    time.sleep(5)
    #    getServicesStatus()

@socketio.on("form data", namespace="/test")
def update_settings(json_msg):
    """
        Get the form data from the web front end, and save theses values to settings.conf
        Then restart the services which have a dependency with these parameters.
        param json_msg: A json variable containing the source form and the new paramaters
    """
    #print("received settings form", json_msg)
    source_section = json_msg.pop().get("source_form")
    #print("section: ", source_section)
    if source_section == "change_password":
        if json_msg[0].get("value") == json_msg[1].get("value"):
            rtkbaseconfig.update_setting("general", "new_web_password", json_msg[0].get("value"))
            update_password(rtkbaseconfig)
            socketio.emit("password updated", namespace="/test")

        else:
            print("ERROR, WRONG PASSWORD!")
    else:
        for form_input in json_msg:
            #print("name: ", form_input.get("name"))
            #print("value: ", form_input.get("value"))
            rtkbaseconfig.update_setting(source_section, form_input.get("name"), form_input.get("value"), write_file=False)
        rtkbaseconfig.write_file()

        #Restart service if needed
        if source_section == "main":
            restartServices(("main", "ntrip_A", "ntrip_B", "local_ntrip_caster", "rtcm_svr", "rtcm_client", "rtcm_udp_svr", "rtcm_udp_client", "file", "rtcm_serial", "raw2nmea"))  
        elif source_section == "ntrip_A":
            restartServices(("ntrip_A",))
        elif source_section == "ntrip_B":
            restartServices(("ntrip_B",))
        elif source_section == "local_ntrip_caster":
            restartServices(("local_ntrip_caster",))
        elif source_section == "rtcm_svr":
            restartServices(("rtcm_svr",))
        elif source_section == "rtcm_client":
            restartServices(("rtcm_client",))
        elif source_section == "rtcm_udp_svr":
            restartServices(("rtcm_udp_svr",))
        elif source_section == "rtcm_udp_client":
            restartServices(("rtcm_udp_client",))
        elif source_section == "rtcm_serial":
            restartServices(("rtcm_serial",))
        elif source_section == "local_storage":
            restartServices(("file",))

def arg_parse():
    parser = argparse.ArgumentParser(
        description="RTKBase Web server",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Enable web server debug mode",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="port used for the web server",
        default=None
    )
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args=arg_parse()
    try:
        #check if a new password is defined in settings.conf
        update_password(rtkbaseconfig)
        #check if authentification is required
        if not rtkbaseconfig.get_web_authentification():
            app.config["LOGIN_DISABLED"] = True
        #get data path
        app.config["DOWNLOAD_FOLDER"] = rtkbaseconfig.get("local_storage", "datadir").strip("'")
        #load services status managed with systemd
        services_list = load_units(services_list)
        #Update standard user in settings.conf
        update_std_user(services_list)
        #Start a "manager" thread
        manager_thread = Thread(target=manager, daemon=True)
        manager_thread.start()

        app.secret_key = rtkbaseconfig.get_secret_key()
        #socketio.run(app, host = "::", port = args.port or rtkbaseconfig.get("general", "web_port", fallback=80), debug=args.debug) # IPv6 "::" is mapped to IPv4
        gunicorn_options = {
        'bind': ['%s:%s' % ('0.0.0.0', args.port or rtkbaseconfig.get("general", "web_port", fallback=80)),
                    '%s:%s' % ('[::1]', args.port or rtkbaseconfig.get("general", "web_port", fallback=80)) ],
        'workers': 1,
        'worker_class': 'gevent',
        'graceful_timeout': 10,
        'loglevel': 'debug' if args.debug else 'warning',
        }
        #start gunicorn
        StandaloneApplication(app, gunicorn_options).run()

    except KeyboardInterrupt:
        print("Server interrupted by user!!")

        # clean up broadcast and blink threads
        rtk.server_not_interrupted = False
#        rtk.led.blinker_not_interrupted = False
        rtk.waiting_for_single = False

        if rtk.coordinate_thread is not None:
            rtk.coordinate_thread.join()

        if rtk.satellite_thread is not None:
            rtk.satellite_thread.join()

#        if rtk.led.blinker_thread is not None:
#            rtk.led.blinker_thread.join()
