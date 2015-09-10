#!/usr/bin/python

from gevent import monkey
monkey.patch_all()

import time
import json
import os
import signal

from RTKLIB import RTKLIB
from port import changeBaudrateTo230400

from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, disconnect

app = Flask(__name__)
app.template_folder = "."
app.debug = False
app.config["SECRET_KEY"] = "secret!"

socketio = SocketIO(app)

# configure Ublox for 230400 baudrate!
changeBaudrateTo230400()

rtk = RTKLIB(socketio)

perform_update = False

# at this point we are ready to start rtk in 2 possible ways: rover and base
# we choose what to do by getting messages from the browser

@app.route("/")
def index():
    return render_template("index.html", current_status = "Cool!!!")

@socketio.on("connect", namespace="/test")
def testConnect():
    print("Browser client connected")

@socketio.on("disconnect", namespace="/test")
def testDisconnect():
    print("Browser client disconnected")

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

#### str2str config handling ####

@socketio.on("read config base", namespace="/test")
def readConfigBase(json):
    rtk.readConfigBase()

@socketio.on("write config base", namespace="/test")
def writeConfigBase(json):
    rtk.writeConfigBase(json)

@socketio.on("update reachview", namespace="/test")
def updateReachView():
    print("Got signal to update!!!")
    print("Server interrupted by user to update!!")
    socketio.server.stop()
    os.execl("/home/reach/ReachView/update.sh", "", str(os.getpid()))

if __name__ == "__main__":
    try:
        socketio.run(app, host = "0.0.0.0", port = 80)
    except KeyboardInterrupt:
        print("Server interrupted by user!!")
        rtk.rtkc.server_not_interrupted = False












