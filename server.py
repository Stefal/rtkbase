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

    while server_not_interrupted:

        # check if RTKLIB is started
        if rtkc.started is True:

            # update satellite levels
            rtkc.getObs()

            if count % 10 == 0:
                print("Sending sat levels:\n" + str(rtkc.obs))

            socketio.emit("satellite broadcast", rtkc.obs, namespace = "/test")
            count += 1
            time.sleep(1)

# this function reads current rtklib status, coordinates and obs count
def broadcastCoordinates():
    count = 0

    while server_not_interrupted:

        # check if RTKLIB is started
        if rtkc.started is True:

            # update RTKLIB status
            rtkc.getStatus()

            # add new status/coordinate data to the message

            if count % 10 == 0:
                print("Sending RTKLIB status select information:\n" + str(rtkc.info))

            socketio.emit("coordinate broadcast", rtkc.info, namespace = "/test")
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
global server_not_interrupted

satellite_thread = None
coordinate_thread = None
server_not_interrupted = True

# at this point we are ready to start rtk in 2 possible ways: rover and base
# we choose what to do by getting messages from the browser

@app.route("/")
def index():
    return render_template("index.html", current_status = "Cool!!!")

@socketio.on("connect", namespace="/test")
def testConnect():
    emit("my response", {"data": "Connected", "count": 0})
    print("Browser client connected")

@socketio.on("disconnect", namespace="/test")
def testDisconnect():
    print("Browser client disconnected")

#### rtkrcv launch/shutdown signal handling ####

@socketio.on("launch rover", namespace="/test")
def launchRtkrcv():

    print("Attempting to launch RTKLIB...")

    res = rtkc.launch()

    if res < 0:
        print("RTKLIB launch failed")
    elif res == 1:
        print("RTKLIB launch successful")
    elif res == 2:
        print("RTKLIB already launched")

@socketio.on("shutdown rover", namespace="/test")
def shutdownRtkrcv():

    print("Attempting to shutdown RTKLIB...")

    res = rtkc.shutdown()

    if res < 0:
        print("RTKLIB shutdown failed")
    elif res == 1:
        print("RTKLIB shutdown successful")
    elif res == 2:
        print("RTKLIB already shutdown")

#### rtkrcv start/stop signal handling ####

@socketio.on("start rover", namespace="/test")
def startRtkrcv():

    print("Attempting to start RTKLIB...")

    global satellite_thread
    global coordinate_thread
    global server_not_interrupted

    res = rtkc.start()

    if res == -1:
        print("RTKLIB start failed")
    elif res == 1:
        print("RTKLIB start successful")
        print("Starting coordinate and satellite thread")

        server_not_interrupted = True

        if satellite_thread is None:
            satellite_thread = Thread(target = broadcastSatellites)
            satellite_thread.start()

        if coordinate_thread is None:
            coordinate_thread = Thread(target = broadcastCoordinates)
            coordinate_thread.start()

    elif res == 2:
        print("RTKLIB already started")

@socketio.on("stop rover", namespace="/test")
def stopRtkrcv():

    global satellite_thread
    global coordinate_thread
    global server_not_interrupted

    print("Attempting to stop RTKLIB...")

    res = rtkc.stop()

    server_not_interrupted = False
    satellite_thread.join()
    satellite_thread = None
    coordinate_thread.join()
    coordinate_thread = None

    if res == -1:
        print("rtkrcv stop failed")
    elif res == 1:
        print("rtkrcv stop successful")
    elif res == 2:
        print("rtkrcv already stopped")

#### str2str start/stop handling ####
@socketio.on("start base", namespace="/test")
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

@socketio.on("stop base", namespace="/test")
def stopStr2Str():

    print("Attempting to stop str2str...")

    res = s2sc.stop()

    if res == -1:
        print("str2str stop failed")
    elif res == 1:
        print("str2str stop successful")
    elif res == 2:
        print("str2str already stopped")

#### rtkrcv config handling ####

@socketio.on("read config rover", namespace="/test")
def readCurrentConfig():
    print("Got signal to read the current rover config")
    conm.readConfig(conm.default_rover_config)
    emit("current config rover", conm.buff_dict, namespace="/test")

@socketio.on("write config rover", namespace="/test")
def writeCurrentConfig(json):
    print("Got signal to write current rover config")
    conm.writeConfig(conm.default_rover_config, json)
    print("Reloading with new config...")

    print(rtkc.loadConfig("../" + conm.default_rover_config))

#### str2str config handling ####

@socketio.on("read config base", namespace="/test")
def readCurrentBaseConfig():
    print("Got signal to read the current base config")
    emit("current config base", s2sc.readConfig())

@socketio.on("write config base", namespace="/test")
def writeCurrentBaseConfig(json):
    print("Got signal to write the base config")

    s2sc.writeConfig(json)

    print("Restarting str2str...")

    res = s2sc.stop() + s2sc.start()

    if res > 1:
        print("Restart successful")
    else:
        print("Restart failed")

# @socketio.on("my event", namespace="/test")
# def printEvent():
#     print("Connected socketio message received")

if __name__ == "__main__":
    try:
        socketio.run(app, host = "0.0.0.0", port = 5000)
    except KeyboardInterrupt:
        print("Server interrupted by user!!")
        server_not_interrupted = False

