from gevent import monkey
monkey.patch_all()

import time
import json
from threading import Thread
from flask import Flask, render_template, session, request
from flask.ext.socketio import *

app = Flask(__name__)
app.template_folder = "."
app.debug = True
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)
proc = None

def createTimePackage(cur_time, dt, cnt):
    # time is passed as a [hours, minutes, seconds] list
    data = {}
    data["hours"] = str(cur_time[0])
    data["minutes"] = str(cur_time[1])
    data["seconds"] = str(cur_time[2])
    data["data"] = str(dt)
    data["count"] = str(cnt)

    json_data = json.dumps(data)

    return json_data

def broadcastTime():
    count = 0
    while 1:
        time_string = time.strftime("%H:%M:%S")
        cur_time = [time_string[0:2], time_string[3:5], time_string[6:8]]
        #json_data = createTimePackage(cur_time, "time", count)
        time.sleep(0.1)

        #print("Sending json package " + json_data)
        socketio.emit("time broadcast",
            {"data": "Server generated event", "count": count, "hours": cur_time[0],
            "minutes": cur_time[1], "seconds": cur_time[2]},
            namespace="/test")

        count += 1

@app.route("/")
def index():
    global proc
    if proc is None:
        proc = Thread(target = broadcastTime)
        proc.start()
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


