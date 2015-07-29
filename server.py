#!/home/reach/ReachView/venv/bin/python
from gevent import monkey
monkey.patch_all()

import time
import json
from RTKLIB import RTKLIB
from port import changeBaudrateTo230400

from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import SocketIO, emit, disconnect

# This is the main ReachView module.
# Here we start the Flask server and handle socket.io messages
# But before this some preparation is done:
# 1. Prepare the flask-socketio server to be run
# 2. Change Ublox UART baudrate to 230400 from default 9600
# 3. Prepare to launch RTKLIB instance with the default reach rover config file
# 4. Launch ConfigManager to read and write config files for RTKLIB
#    Note, that we use the /path/to/RTKLIB/app/rtkrcv directory for config files
# 5. Server launches threads, reading status info from running RTKLIB
# 6. Server handles config file requests: reading existing ones and writing new ones
#    Through the ConfigManager

app = Flask(__name__)
app.template_folder = "."
app.debug = False
app.config["SECRET_KEY"] = "secret!"

socketio = SocketIO(app)

# configure Ublox for 230400 baudrate!
changeBaudrateTo230400()

rtk = RTKLIB(socketio)

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

# @socketio.on("my event", namespace="/test")
# def printEvent():
#     print("Connected socketio message received")

if __name__ == "__main__":
    try:
        socketio.run(app, host = "0.0.0.0", port = 5000)
    except KeyboardInterrupt:
        print("Server interrupted by user!!")
        rtk.rtkc.server_not_interrupted = False

