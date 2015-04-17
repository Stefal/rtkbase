$(document).ready(function () {

    // SocketIO namespace:
    namespace = "/test";
    var socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });

    // Center alignment

    $("#mode_value").text("Fix");
    $("#fix_value").text("3-D");
    $("#lon_value").text("60w");
    $("#lat_value").text("30");
    //$("#height_value").html("20");

    var canvas1 = $("#sat_chart_canvas");

    var sat_data1 = {
        labels: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13"],
        datasets: [
            {
                label: "Rover satellite levels",
                fillColor: "rgba(0, 255, 0, 0.9)",
                strokeColor: "rgba(220, 220, 220, 0.8)",
                highlightFill: "rgba(220, 220, 220, 0.75)",
                highlightStroke: "rgba(220, 220, 220, 1)",
                data: [65, 59, 80, 81, 56, 55, 40, 31, 12, 15, 10, 80, 60, 54, 23, 12, 25, 36]
            },
            {
                label: "Base satellite levels",
                fillColor: "rgba(151, 187, 205, 0.9)",
                strokeColor: "rgba(151, 187, 205, 0.8)",
                highlightFill: "rgba(151, 187, 205, 0.75)",
                highlightStroke: "rgba(151, 187, 205, 1)",
                data: [28, 48, 40, 19, 86, 27, 90, 31, 65, 59, 80, 81, 56, 55, 40, 31, 15, 10]
            }
        ]
    };

    drawSatChart(canvas1, sat_data1);

    // handle data broadcast

    socket.on("my response", function (msg) {

    });

    socket.on("time broadcast", function (msg) {
        $("#height_value").html("<span>Received time: #" + msg.count + " " + msg.hours + ":" + msg.minutes + ":" + msg.seconds + "</span");
    });


});
