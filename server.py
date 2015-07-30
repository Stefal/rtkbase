#!venv/bin/python
from gevent import monkey
monkey.patch_all()

import time
import json
from RtkController import RtkController
from ConfigManager import ConfigManager
from port import changeBaudrateTo230400

from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import *

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

# default location for RTKLIB binaries is /home/reach/RTKLIB/app/rtkrcv
# prepare ConfigManager, read the default config
conm = ConfigManager()


# default location for str2str binaries is /home/reach/RTKLIB/app/str2str/gcc

# simple preparation work
satellite_thread = None
coordinate_thread = None
rtklib_launched = None
server_not_interrupted = 1

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

@app.route("/")
def index():
    global satellite_thread
    global coordinate_thread
    global rtklib_launched

    if satellite_thread is None:
        satellite_thread = Thread(target = broadcastSatellites)
        satellite_thread.start()

    if coordinate_thread is None:
        coordinate_thread = Thread(target = broadcastCoordinates)
        coordinate_thread.start()

    return render_template("index.html")

@socketio.on("connect", namespace="/test")
def test_connect():
    emit("my response", {"data": "Connected", "count": 0})
    print("Browser client connected")

@socketio.on("disconnect", namespace="/test")
def test_disconnect():
    print("Browser client disconnected")

#### RTKLIB launch/shutdown signal handling ####

@socketio.on("launch rtklib", namespace="/test")
def launchRtklib():
    if rtkc.launch() < 0:
        print("RTKLIB launch failed")
    else:
        print("RTKLIB launch successful")

@socketio.on("shutdown rtklib", namespace="/test")
def shutdownRtklib():
    if rtkc.launch() < 0:
        print("RTKLIB launch failed")
    else:
        print("RTKLIB launch successful")

#### RTKLIB start/stop signal handling ####

@socketio.on("start rtklib", namespace="/test")
def startRtklib():
    print("Attempting to start RTKLIB...")
    res = rtkc.start()
    if res == -1:
        print("RTKLIB start failed")
    elif res == 1:
        print("RTKLIB start successful")
    elif res == 2:
        print("RTKLIB already started")

@socketio.on("stop rtklib", namespace="/test")
def stopRtklib():
    print("Attempting to stop RTKLIB...")
    res = rtkc.start()
    if res == -1:
        print("RTKLIB stop failed")
    elif res == 1:
        print("RTKLIB stop successful")
    elif res == 2:
        print("RTKLIB already stopped")

#### RTKLIB config handling ####

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

