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

def broadcastTime():
    count = 0
    json_data = {}
    while 1:
        time_string = time.strftime("%H:%M:%S")
        cur_time = [time_string[0:2], time_string[3:5], time_string[6:8]]

        # socketio.emit("time broadcast",
        #     {"data": "Server generated event", "count": count, "hours": cur_time[0],
        #     "minutes": cur_time[1], "seconds": cur_time[2]},
        #     namespace="/test")

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
            json_data["rover" + str(i)] = randint(35, 45)

        for i in range(0, sat_number):
            json_data["base" + str(i)] = randint(30, 40)

        socketio.emit("satellite broadcast", json_data, namespace = "/test")
        time.sleep(1)

@app.route("/")
def index():
    global time_thread
    global satellite_thread

    if time_thread is None:
        time_thread = Thread(target = broadcastTime)
        time_thread.start()

    if satellite_thread is None:
        satellite_thread = Thread(target = broadcastSatellites)
        satellite_thread.start()

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


