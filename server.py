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

from gevent import monkey
monkey.patch_all()

import time
import json
import os
import signal
import sys
import ReachTools

from RTKLIB import RTKLIB
from port import changeBaudrateTo230400

from threading import Thread
from flask import Flask, render_template, session, request, send_file
from flask.ext.socketio import SocketIO, emit, disconnect
from subprocess import check_output

app = Flask(__name__)
app.template_folder = "."
app.debug = False
app.config["SECRET_KEY"] = "secret!"
app.config["UPLOAD_FOLDER"] = "../logs"

socketio = SocketIO(app)

# configure Ublox for 230400 baudrate!
changeBaudrateTo230400()

rtk = RTKLIB(socketio)

# at this point we are ready to start rtk in 2 possible ways: rover and base
# we choose what to do by getting messages from the browser

@app.route("/")
def index():
    rtk.logm.updateAvailableLogs()
    print("AVAILABLE LOGS == " + str(rtk.logm.available_logs))
    return render_template("index.html", logs = rtk.logm.available_logs, system_status = ReachTools.getSystemStatus())

@app.route("/logs/download/<path:log_name>")
def downloadLog(log_name):
    full_log_path = rtk.logm.log_path + "/" + log_name
    return send_file(full_log_path, as_attachment = True)

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

#### rtkrcv launch/shutdown signal handling ####

@socketio.on("launch rover", namespace="/test")
def launchRover():
    rtk.launchRover()

@socketio.on("shutdown rover", namespace="/test")
def shutdownRover():
    rtk.shutdownRover()

#### rtkrcv start/stop signal handling ####

@socketio.on("start rover", namespace="/test")
def startRover():
    rtk.startRover()

@socketio.on("stop rover", namespace="/test")
def stopRtkrcv():
    rtk.stopRover()

#### str2str launch/shutdown handling ####

@socketio.on("launch base", namespace="/test")
def startBase():
    rtk.launchBase()

@socketio.on("shutdown base", namespace="/test")
def stopBase():
    rtk.shutdownBase()

#### str2str start/stop handling ####

@socketio.on("start base", namespace="/test")
def startBase():
    rtk.startBase()

@socketio.on("stop base", namespace="/test")
def stopBase():
    rtk.stopBase()

#### rtkrcv config handling ####

@socketio.on("read config rover", namespace="/test")
def readConfigRover(json):
    rtk.readConfigRover(json)

@socketio.on("write config rover", namespace="/test")
def writeConfigRover(json):
    rtk.writeConfigRover(json)

@socketio.on("write and load config rover", namespace="/test")
def writeAndLoadConfig(json):
    rtk.writeConfigRover(json)
    rtk.loadConfigRover(json.get("config_file_name", None))

#### str2str config handling ####

@socketio.on("read config base", namespace="/test")
def readConfigBase(json):
    rtk.readConfigBase()

@socketio.on("write and load config base", namespace="/test")
def writeConfigBase(json):
    rtk.writeConfigBase(json)

#### Delete log button handler ####

@socketio.on("delete log", namespace="/test")
def deleteLog(json):
    rtk.logm.deleteLog(json.get("name"))

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

#### Delete config ####
@socketio.on("delete config", namespace="/test")
def deleteLog(json):
    log_name = json.get("name")
    raw_log_path = rtk.logm.log_path + "/" + log_name
    rtk.deleteConfig(json.get("name"))

#### Reset config to default ####
@socketio.on("reset config", namespace="/test")
def resetConfig(json):
    rtk.resetConfigToDefault(json.get("name"))

#### Update ReachView ####

@socketio.on("update reachview", namespace="/test")
def updateReachView():
    print("Got signal to update!!!")
    print("Server interrupted by user to update!!")
    rtk.shutdown()
    socketio.server.stop()
    os.execl("/home/reach/ReachView/update.sh", "", str(os.getpid()))

#### Device hardware functions ####

@socketio.on("reboot device", namespace="/test")
def rebootReach():
    print("Rebooting...")
    check_output("reboot")

@socketio.on("turn off wi-fi", namespace="/test")
def turnOffWiFi():
    print("Turning off wi-fi")
    check_output("rfkill block wlan", shell = True)

if __name__ == "__main__":
    try:
        socketio.run(app, host = "0.0.0.0", port = 80)

    except KeyboardInterrupt:
        print("Server interrupted by user!!")

        # clean up broadcast and blink threads
        rtk.server_not_interrupted = False
        rtk.led.blinker_not_interrupted = False
        rtk.waiting_for_single = False

        if rtk.coordinate_thread is not None:
            rtk.coordinate_thread.join()

        if rtk.satellite_thread is not None:
            rtk.satellite_thread.join()

        if rtk.led.blinker_thread is not None:
            rtk.led.blinker_thread.join()

