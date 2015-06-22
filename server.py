from gevent import monkey
monkey.patch_all()

import time
import json
from RtkController import RtkController
from ConfigManager import ConfigManager

from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import *

from random import randint

app = Flask(__name__)
app.template_folder = "."
app.debug = False
app.config["SECRET_KEY"] = "secret!"

socketio = SocketIO(app)

rtk_location = "/Users/fedorovegor/Documents/RTKLIB/app/rtkrcv/gcc"

# prepare RtkController, run RTKLIB
print("prepare rtk")
rtkc = RtkController(rtk_location)
rtkc.start()

# prepare ConfigManager
conm = ConfigManager(socketio, rtk_location[:-3])

time_thread = None
satellite_thread = None
coordinate_thread = None

def broadcastTime():
    count = 0
    json_data = {}
    while 1:
        time_string = time.strftime("%H:%M:%S")
        cur_time = [time_string[0:2], time_string[3:5], time_string[6:8]]

        json_data = {
            "data" : "Server time",
            "count" : count,
            "hours" : cur_time[0],
            "minutes" : cur_time[1],
            "seconds" : cur_time[2]
        }

        socketio.emit("time broadcast", json_data, namespace = "/test")

        count += 1
        time.sleep(0.1)

def broadcastSatellites():
    count = 0
    sat_number = 10
    json_data = {}

    while 1:

        # update satellite levels
        rtkc.getObs()

        # add new obs data to the message
        json_data.update(rtkc.obs)

        print("Sending sat levels:\n" + str(json_data))

        socketio.emit("satellite broadcast", json_data, namespace = "/test")
        count += 1
        time.sleep(1)

def broadcastCoordinates():
    count = 0
    json_data = {}

    while 1:

        # update RTKLIB status
        rtkc.getStatus()

        json_data.update(rtkc.info)

        print("Sending RTKLIB status select information:\n" + str(json_data))

        socketio.emit("coordinate broadcast", json_data, namespace = "/test")
        count += 1
        time.sleep(1)

@app.route("/")
def index():
    global time_thread
    global satellite_thread
    global coordinate_thread

    if time_thread is None:
        time_thread = Thread(target = broadcastTime)
        time_thread.start()

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

@socketio.on("read config", namespace="/test")
def readCurrentConfig():
    print("Got signal to read the current config")

    conm.readConfig(conm.default_base_config)
    emit("current config", conm.buff_dict, namespace="/test")

@socketio.on("read default base config", namespace="/test")
def readDefaultBaseConfig():
    print("Got signal to read the default base config")

@socketio.on("temp config modified", namespace="/test")
def writeConfig(json):
    print("Received temp config to write!!!")
    print(str(json))
    conm.writeConfig("temp.conf", json)
    print("reloading config result: " + str(rtkc.loadConfig("../temp.conf")))

# @socketio.on("my event", namespace="/test")
# def printEvent():
#     print("Connected socketio message received")

if __name__ == "__main__":
    socketio.run(app, host = "0.0.0.0", port = 5000)


