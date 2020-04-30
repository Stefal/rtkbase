#!/usr/bin/python

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

#from gevent import monkey
#monkey.patch_all()
import eventlet
eventlet.monkey_patch()

import time
import json
import os
import signal
import sys
import requests

from threading import Thread
from RTKLIB import RTKLIB
from port import changeBaudrateTo115200
from reach_tools import reach_tools, provisioner
from ServiceController import ServiceController
from RTKBaseConfigManager import RTKBaseConfigManager

#print("Installing all required packages")
#provisioner.provision_reach()

#import reach_bluetooth.bluetoothctl
#import reach_bluetooth.tcp_bridge

from threading import Thread
from flask_bootstrap import Bootstrap
from flask import Flask, render_template, session, request, flash, url_for
from flask import send_file, send_from_directory, safe_join, redirect, abort
from flask import g
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from wtforms.validators import ValidationError, DataRequired, EqualTo
from flask_socketio import SocketIO, emit, disconnect
from subprocess import check_output

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from werkzeug.urls import url_parse

app = Flask(__name__)
app.debug = False
app.config["SECRET_KEY"] = "secret!"
#app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "../logs")
app.config["DOWNLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "../data")
app.config["LOGIN_DISABLED"] = False

path_to_rtklib = "/usr/local/bin"

login=LoginManager(app)
login.login_view = 'login_page'
socketio = SocketIO(app)
bootstrap = Bootstrap(app)

rtk = RTKLIB(socketio, rtklib_path=path_to_rtklib, log_path=app.config["DOWNLOAD_FOLDER"])
services_list = [{"service_unit" : "str2str_tcp.service", "name" : "main"},
                 {"service_unit" : "str2str_ntrip.service", "name" : "ntrip"},
                 {"service_unit" : "str2str_file.service", "name" : "file"},]


#Delay before rtkrcv will stop if no user is on status.html page
rtkcv_standby_delay = 600

rtkbaseconfig = RTKBaseConfigManager(os.path.join(os.path.dirname(__file__), "../settings.conf.default"), os.path.join(os.path.dirname(__file__), "../settings.conf"))

class User(UserMixin):
    def __init__(self, username):
        self.id=username
        self.password_hash = rtkbaseconfig.get("general", "web_password_hash")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class LoginForm(FlaskForm):
    #username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Please enter the password:', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

def update_password(config_object):
    """
        Check in settings.conf if web_password entry contains a value
        If yes, this function will generate a new hash for it and
        remove the web_password value
        :param config_object: a RTKBaseConfigManager instance
    """
    new_password = config_object.get("general", "web_password")
    if new_password != "":
        config_object.update_setting("general", "web_password_hash", generate_password_hash(new_password))
        config_object.update_setting("general", "web_password", "")
        
def manager():

    while True:
        if rtk.sleep_count > rtkcv_standby_delay and rtk.state != "inactive":
            rtk.stopBase()
            rtk.sleep_count = 0
        elif rtk.sleep_count > rtkcv_standby_delay:
            print("Je voudrais bien arrêter, mais rtk.state est : ", rtk.state)
        time.sleep(1)

@socketio.on("check update", namespace="/test")
def check_update(source_url = None, current_release = None, prerelease=True, emit = True):
    """
        check if an update exists
    """
    new_release = {}
    source_url = source_url if source_url is not None else "https://api.github.com/repos/stefal/rtkbase/releases"
    current_release = current_release if current_release is not None else rtkbaseconfig.get("general", "version").strip("v").strip('-alpha').strip('-beta')
    
    try:    
        response = requests.get(source_url)
        response = response.json()
        for release in response:
            if release.get("prerelease") & prerelease or release.get("prerelease") == False:
                latest_release = release["tag_name"].strip("v").strip('-alpha').strip('-beta')
                if latest_release > current_release:
                    new_release = {"new_release" : latest_release, "url" : release.get("tarball_url")}
                break
             
    except Exception as e:
        print("Check update error: ", e)
        
    if emit:
        socketio.emit("new release", json.dumps(new_release), namespace="/test")
    print
    return new_release

@socketio.on("update rtkbase", namespace="/test")       
def update_rtkbase():
    """
        download and update rtkbase
    """
    #Check if an update is available
    update_url = check_update(emit=False).get("url")
    if update_url is None:
        return

    import tarfile
    #Download update
    update_archive = "/var/tmp/rtkbase_update.tar.gz"
    try:
        response = requests.get(update_url)
        with open(update_archive, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print("Error: Can't download update - ", e)

    #Get the "root" folder in the archive
    tar = tarfile.open(update_archive)
    for tarinfo in tar:
        if tarinfo.isdir():
            primary_folder = tarinfo.name
            break
    
    #Extract archive
    tar.extractall("/var/tmp")

    #launch update script
    rtk.shutdownBase()
    rtkbase_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    source_path = os.path.join("/var/tmp/", primary_folder)
    script_path = os.path.join(source_path, "rtkbase_update.sh")
    os.execl(script_path, "unused arg0", source_path, rtkbase_path, app.config["DOWNLOAD_FOLDER"].split("/")[-1])

# at this point we are ready to start rtk in 2 possible ways: rover and base
# we choose what to do by getting messages from the browser

#@app.route("/")
#def index():
#    rtk.logm.updateAvailableLogs()
#    return render_template("index.html", logs = rtk.logm.available_logs, system_status = reach_tools.getSystemStatus())

"""
def index():
    #if not session.get('logged_in'):
    #    return render_template('login.html')
    #else:
    rtk.logm.updateAvailableLogs()
    return render_template("index.html", logs = rtk.logm.available_logs, system_status = reach_tools.getSystemStatus())
"""

@app.before_request
def inject_release():
    g.version = rtkbaseconfig.get("general", "version")

@login.user_loader
def load_user(id):
    return User(id)

@app.route('/')
@app.route('/index')
@app.route('/status')
@login_required
def status_page():
    return render_template("status.html")

@app.route('/settings')
@login_required
def settings_page():
    data = rtkbaseconfig.get_ordered_settings()
    return render_template("settings.html", data = data)

@app.route('/logs')
@login_required
def logs_page():
    return render_template("logs.html")

@app.route("/logs/download/<path:log_name>")
@login_required
def downloadLog(log_name):
    try:
        full_log_path = rtk.logm.log_path + "/" + log_name
        return send_file(full_log_path, as_attachment = True)
    except FileNotFoundError:
        abort(404)

"""
@app.route("/logs/download/<log_name>")
def downloadLog(log_name):
    try:
        return send_from_directory(app.config["DOWNLOAD_FOLDER"], filename=log_name, as_attachment=True)
    except FileNotFoundError:
        abort(404)
"""
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
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('status_page')

        return redirect(next_page)
        
    return render_template('login.html', title='Sign In', form=loginform)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login_page'))

#### Handle connect/disconnect events ####

@socketio.on("connect", namespace="/test")
def testConnect():
    print("Browser client connected")
    rtk.sendState()

@socketio.on("disconnect", namespace="/test")
def testDisconnect():
    print("Browser client disconnected")

#### Log list handling ###

@socketio.on("get logs list", namespace="/test")
def getAvailableLogs():
    print("DEBUG updating logs")
    rtk.logm.updateAvailableLogs()
    print("Updated logs list is " + str(rtk.logm.available_logs))
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
    rtk.startBase()

@socketio.on("stop base", namespace="/test")
def stopBase():
    rtk.stopBase()

@socketio.on("on graph", namespace="/test")
def continueBase():
    rtk.sleep_count = 0
#### Free space handler

@socketio.on("get available space", namespace="/test")
def getAvailableSpace():
    rtk.socketio.emit("available space", reach_tools.getFreeSpace(path_to_gnss_log), namespace="/test")

#### Delete log button handler ####

@socketio.on("delete log", namespace="/test")
def deleteLog(json):
    rtk.logm.deleteLog(json.get("name"))
    # Sending the the new available logs
    getAvailableLogs()

#### Download and convert log handlers ####

@socketio.on("process log", namespace="/test")
def processLog(json):
    log_name = json.get("name")

    print("Got signal to process a log, name = " + str(log_name))
    print("Path to log == " + rtk.logm.log_path + "/" + str(log_name))

    raw_log_path = rtk.logm.log_path + "/" + log_name
    rtk.processLogPackage(raw_log_path)

@socketio.on("cancel log conversion", namespace="/test")
def cancelLogConversion(json):
    log_name = json.get("name")
    raw_log_path = rtk.logm.log_path + "/" + log_name
    rtk.cancelLogConversion(raw_log_path)

#### RINEX versioning ####

@socketio.on("read RINEX version", namespace="/test")
def readRINEXVersion():
    rinex_version = rtk.logm.getRINEXVersion()
    rtk.socketio.emit("current RINEX version", {"version": rinex_version}, namespace="/test")

@socketio.on("write RINEX version", namespace="/test")
def writeRINEXVersion(json):
    rinex_version = json.get("version")
    rtk.logm.setRINEXVersion(rinex_version)

#### Update ReachView ####

@socketio.on("update reachview", namespace="/test")
def updateReachView():
    print("Got signal to update!!!")
    print("Server interrupted by user to update!!")
#    rtk.shutdown()
#    bluetooth_bridge.stop()
#    socketio.server.stop()
#    os.execl("/home/reach/update.sh", "", str(os.getpid()))

#### Device hardware functions ####

@socketio.on("reboot device", namespace="/test")
def rebootRtkbase():
    print("Rebooting...")
    rtk.shutdown()
    #socketio.stop() hang. I disabled it
    #socketio.stop()
    check_output("reboot")

@socketio.on("shutdown device", namespace="/test")
def shutdownRtkbase():
    print("Shutdown...")
    rtk.shutdown()
    #socketio.stop() hang. I disabled it
    #socketio.stop()
    check_output(["shutdown", "now"])

@socketio.on("turn off wi-fi", namespace="/test")
def turnOffWiFi():
    print("Turning off wi-fi")
#    check_output("rfkill block wlan", shell = True)

#### Systemd Services functions ####

def load_units(services):
    #load unit service before getting status
    for service in services:
        service["unit"] = ServiceController(service["service_unit"])
    return services


@socketio.on("get services status", namespace="/test")
def getServicesStatus():
    print("Getting services status")
    
    for service in services_list:
        service["active"] = service["unit"].isActive()

    services_status = []
    for service in services_list: 
        services_status.append({key:service[key] for key in service if key != 'unit'})
    
    print(services_status)
    socketio.emit("services status", json.dumps(services_status), namespace="/test")

@socketio.on("services switch", namespace="/test")
def switchService(json):
    print("Received service to switch", json)
    try:
        for service in services_list:
            if json["name"] == service["name"] and json["active"] == True:
                print("Trying to start service {}".format(service["name"]))
                service["unit"].start()
            elif json["name"] == service["name"] and json["active"] == False:
                print("Trying to stop service {}".format(service["name"]))
                service["unit"].stop()

    except Exception as e:
        print(e)
    finally:
        time.sleep(5)
        getServicesStatus()

if __name__ == "__main__":
    try:
        #check if a new password is defined in settings.conf
        update_password(rtkbaseconfig)
        #check if authentification is required
        if not rtkbaseconfig.get_web_authentification():
            app.config["LOGIN_DISABLED"] = True
        #get data path
        app.config["DOWNLOAD_FOLDER"] = rtkbaseconfig.get("local_storage", "datadir")
        #load services status managed with systemd
        services_list = load_units(services_list)
        #Start a "manager" thread
        manager_thread = Thread(target=manager, daemon=True)
        manager_thread.start()

        app.secret_key = rtkbaseconfig.get_secret_key()
        socketio.run(app, host = "0.0.0.0", port = 8080)

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

