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

# default location for rtkrcv binaries is /home/reach/RTKLIB/app/rtkrcv/gcc
# prepare RtkController, but don't start rtklib
rtkc = RtkController(socketio)

# default location for rtkrcv configs is /home/reach/RTKLIB/app/rtkrcv
# prepare ConfigManager, read the default config
conm = ConfigManager()

# default location for str2str binaries is /home/reach/RTKLIB/app/str2str/gcc
s2sc = Str2StrController()

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
def launchRtkrcv():

@socketio.on("shutdown rover", namespace="/test")
def shutdownRtkrcv():

#### rtkrcv start/stop signal handling ####

@socketio.on("start rover", namespace="/test")
def startRtkrcv():


@socketio.on("stop rover", namespace="/test")
def stopRtkrcv():


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
    # after this, to preserve the order of the options in the frontend we send a special order message
    print("Sending rover config order")

    options_order = {}

    # create a structure the corresponds to the options order
    for index, value in enumerate(conm.buff_dict_order):
        options_order[str(index)] = value

    # send the options order
    emit("current config rover order", options_order, namespace="/test")

    # send the options comments
    print("Sending rover config comments")
    print(conm.buff_dict_comments)
    emit("current config rover comments", conm.buff_dict_comments, namespace="/test")

    # now we send the whole config with values
    print("Sending rover config values")
    emit("current config rover", conm.buff_dict, namespace="/test")

@socketio.on("write config rover", namespace="/test")
def writeCurrentConfig(json):
    print("Got signal to write current rover config")
    conm.writeConfig(conm.default_rover_config, json)
    print("Reloading with new config...")

    res = rtkc.loadConfig("../" + conm.default_rover_config) + rtkc.restart()

    if res == 2:
        print("Restart successful")
    elif res == 1:
        print("rtkrcv started instead of restart")
    elif res == -1:
        print("rtkrcv restart failed")

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
        rtkc.server_not_interrupted = False

