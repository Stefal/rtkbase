from gevent import monkey
monkey.patch_all()

import time
import json
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import *

from random import randint

app = Flask(__name__)
app.template_folder = "."
app.debug = True
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)
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

        json_data = {
            "data" : "Satellite levels"
        }

        for i in range(0, sat_number):
            json_data["rover" + str(i)] = randint(42, 45)

        for i in range(0, sat_number):
            json_data["base" + str(i)] = randint(41, 44)

        socketio.emit("satellite broadcast", json_data, namespace = "/test")
        count+=1
        time.sleep(1)

def broadcastCoordinates():
    count = 0
    json_data = {}

    while 1:

        json_data = {
            "fix" : "fix", # current fix mode
            "mode" : "kinematic", # current rover mode
            "lat" : 60.085981 + float(randint(1,10)) / 10000000,
            "lon" : 30.420639 + float(randint(1,10)) / 10000000,
            "height" : 16 + float(randint(1000,10000)) / 10000000
        }

        socketio.emit("coordinate broadcast", json_data, namespace = "/test")
        count+=1
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

# @socketio.on("my event", namespace="/test")
# def printEvent():
#     print("Connected socketio message received")

if __name__ == "__main__":
    socketio.run(app)


