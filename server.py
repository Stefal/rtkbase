#!venv/bin/python
from gevent import monkey
monkey.patch_all()

import time
import json
from RtkController import RtkController
from ConfigManager import ConfigManager
from Str2StrController import Str2StrController
from port import changeBaudrateTo230400

from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import *

# this function reads satellite levels from an exisiting rtkrcv instance
# and emits them to the connected browser as messages
def broadcastSatellites():
    count = 0
    sat_number = 10
    json_data = {}

    while server_not_interrupted:

        # check if RTKLIB is started
        if rtkc.started is True:

            # update satellite levels
            rtkc.getObs()

            # add new obs data to the message
            json_data.update(rtkc.obs)

            if count % 10 == 0:
                print("Sending sat levels:\n" + str(json_data))

            socketio.emit("satellite broadcast", json_data, namespace = "/test")
            count += 1
            time.sleep(1)

# this function reads current rtklib status, coordinates and obs count
def broadcastCoordinates():
    count = 0
    json_data = {}

    while server_not_interrupted:

        # check if RTKLIB is started
        if rtkc.started is True:

            # update RTKLIB status
            rtkc.getStatus()

            # add new status/coordinate data to the message
            json_data.update(rtkc.info)

            if count % 10 == 0:
                print("Sending RTKLIB status select information:\n" + str(json_data))

            socketio.emit("coordinate broadcast", json_data, namespace = "/test")
            count += 1
            time.sleep(1)

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

# default location for rtkrcv binaries is /home/reach/RTKLIB/app/rtkrcv/gcc
# prepare RtkController, but don't start rtklib
rtkc = RtkController()

# default location for rtkrcv configs is /home/reach/RTKLIB/app/rtkrcv
# prepare ConfigManager, read the default config
conm = ConfigManager()

# default location for str2str binaries is /home/reach/RTKLIB/app/str2str/gcc
s2sc = Str2StrController()

# simple preparation work
global satellite_thread
global coordinate_thread
global rtklib_launched
global server_not_interrupted

satellite_thread = None
coordinate_thread = None
rtklib_launched = None
server_not_interrupted = True

# at this point we are ready to start rtk in 2 possible ways: rover and base
# we choose what to do by getting messages from the browser

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("connect", namespace="/test")
def testConnect():
    emit("my response", {"data": "Connected", "count": 0})
    print("Browser client connected")

@socketio.on("disconnect", namespace="/test")
def testDisconnect():
    print("Browser client disconnected")

#### rtkrcv launch/shutdown signal handling ####

@socketio.on("launch rtkrcv", namespace="/test")
def launchRtkrcv():
    if rtkc.launch() < 0:
        print("RTKLIB launch failed")
    else:
        print("RTKLIB launch successful")

@socketio.on("shutdown rtkrcv", namespace="/test")
def shutdownRtkrcv():
    if rtkc.launch() < 0:
        print("RTKLIB launch failed")
    else:
        print("RTKLIB launch successful")

#### rtkrcv start/stop signal handling ####

@socketio.on("start rtkrcv", namespace="/test")
def startRtkrcv():

    print("Attempting to start RTKLIB...")

    res = rtkc.start()

    if res == -1:
        print("RTKLIB start failed")
    elif res == 1:
        print("RTKLIB start successful")
        print("Starting coordinate and satellite thread")

        if satellite_thread is None:
            satellite_thread = Thread(target = broadcastSatellites)
            satellite_thread.start()

        if coordinate_thread is None:
            coordinate_thread = Thread(target = broadcastCoordinates)
            coordinate_thread.start()

    elif res == 2:
        print("RTKLIB already started")

@socketio.on("stop rtkrcv", namespace="/test")
def stopRtkrcv():

    print("Attempting to stop RTKLIB...")

    server_not_interrupted = False
    satellite_thread.join()
    satellite_thread = None
    coordinate_thread.join()
    coordinate_thread = None

    res = rtkc.stop()

    if res == -1:
        print("rtkrcv stop failed")
    elif res == 1:
        print("rtkrcv stop successful")
    elif res == 2:
        print("rtkrcv already stopped")

#### str2str start/stop handling ####
@socketio.on("start str2str", namespace="/test")
def startStr2Str():

    print("Attempting to start str2str...")

    if not rtkc.started:
        res = s2sc.start()

        if res < 0:
            print("str2str start failed")
        elif res == 1:
            print("str2str start successful")
        elif res == 2:
            print("str2str already started")

    else:
        print("Can't start str2str with rtkrcv still running!!!!")

@socketio.on("stop str2str", namespace="/test")
def stopStr2Str():

    print("Attempting to stop str2str...")

    res = s2sc.stop()

    if res == -1:
        print("rtkrcv stop failed")
    elif res == 1:
        print("rtkrcv stop successful")
    elif res == 2:
        print("rtkrcv already stopped")

#### rtkrcv config handling ####

@socketio.on("read config", namespace="/test")
def readCurrentConfig():
    print("Got signal to read the current config")
    conm.readConfig(conm.default_base_config)
    emit("current config", conm.buff_dict, namespace="/test")

# @socketio.on("my event", namespace="/test")
# def printEvent():
#     print("Connected socketio message received")

if __name__ == "__main__":
    try:
        socketio.run(app, host = "0.0.0.0", port = 5000)
    except KeyboardInterrupt:
        print("Server interrupted by user!!")
        server_not_interrupted = 0

