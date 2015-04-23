$(document).ready(function () {

    // Initial formatting for the info blocks
    var grid_style = {
        backgroundColor: "Gainsboro",
        border: "1px solid black",
        textAlign: "left",
    };

    $("#status_block").css(grid_style);
    $("#mode_block").css(grid_style);
    $("#lat_block").css(grid_style);
    $("#lon_block").css(grid_style);
    $("#height_block").css(grid_style);

    // SocketIO namespace:
    namespace = "/test";

    // initiate SocketIO connection
    var socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });

    // Center alignment

    $("#mode_value").text("no link");
    $("#status_value").text("no link");
    $("#lon_value").text("0");
    $("#lat_value").text("0");
    $("#height_value").html("0");

    // Config form settigns

    // input 1 type active form
    $("#input1_type").change(function () {
        switch ($("#input1_type option:selected").text()) {
            case "Off":
                break;
            case "Serial":
                break;
            case "File":
                break;
            case "TCP client":
                break;
            case "TCP server":
                break;
            case "NTRIP client":
                break;
            case "ftp":
                break;
            case "http":
                break;
        }
    });

    // This canvas contains the satellite_graph

    var canvas = $("#sat_chart_canvas");
    canvas.css("width", "99%");
    canvas.css("margin", "1%");

    var ctx = canvas.get(0).getContext("2d");

    // keep aspect ratio
    ctx.canvas.width = window.innerWidth;
    ctx.canvas.height = 0.5 * window.innerWidth;

    // change between-bar width depending on screen width
    var bar_spacing = (ctx.canvas.width > 1000) ? 5 : 2;

    // satellite_graph is created based on this data
    var sat_data = {
        labels: ["2", "4", "7", "10", "12", "14", "18", "20", "23", "31"],
        datasets: [
            {
                label: "Rover satellite levels",
                fillColor: "rgba(0, 255, 0, 1)",
                strokeColor: "rgba(0, 0, 0, 0.7)",
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            },
            {
                label: "Base satellite levels",
                fillColor: "rgba(151, 187, 205, 1)",
                strokeColor: "rgba(0, 0, 0, 0.7)",
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        ]
    };

    // draw the satellite_graph
    var satellite_graph = new Chart(ctx).Bar(sat_data, {
        responsive: true,

        barDatasetSpacing: -1,
        barValueSpacing: bar_spacing,

        scaleOverride: true,
        scaleSteps: 6,
        scaleStepWidth: 10,
        scaleStartValue: 0,
        scaleLineColor: "rgba(0, 0, 0, 0.8)",
        scaleGridLineColor: "rgba(0, 0, 0, 0.7)",
        scaleShowVerticalLines: false,

        showTooltips: false
    });

    // handle data broadcast
    socket.on("my response", function (msg) {

    });

    socket.on("time broadcast", function (msg) {
        console.log("time msg received");
    });

    socket.on("satellite broadcast", function (msg) {
        console.log("satellite msg received");

        // get all the keys of msg object
        var rover_count = 0;
        var base_count = 0;
        var fc = 0;

        // cycle through all the data of the incoming message
        for (var k in msg) {

            var msg_data = msg[k];

            // if this is a rover satellite level, then update the rover part of the satellite graph
            if (k.indexOf("rover") > -1) {

                // var rover_number = k.charAt(5); // get satellite number for this value
                satellite_graph.datasets[0].bars[rover_count].value = msg_data;

                // take care of the fill color
                switch (true) {
                    case (msg_data < 30):
                        fc = "rgba(255, 0, 0, 0.9)"; // Red
                        break;
                    case (msg_data >= 30 && msg_data <= 45):
                        fc = "rgba(255, 255, 0, 0.9)"; // Yellow
                        break;
                    case (msg_data >= 45):
                        fc = "rgba(0, 255, 0, 0.9)"; // Green
                        break;
                }

                satellite_graph.datasets[0].bars[rover_count].fillColor = fc;
                rover_count++;
            }

            // if this is a base satellite level, update the base part of the satellite graph
            if (k.indexOf("base") > -1) {

                // var base_number_ = k.charAt(4); // get satellite number for this value
                satellite_graph.datasets[1].bars[base_count].value = msg_data;

                // take care of the fill color
                switch (true) {
                    case (msg_data < 30):
                        fc = "rgba(255, 0, 0, 1)"; // Red
                        break;
                    case (msg_data >= 30 && msg_data <= 45):
                        fc = "rgba(255, 255, 0, 1)"; // Yellow
                        break;
                    case (msg_data >= 45):
                        fc = "rgba(0, 255, 0, 1)"; // Green
                        break;
                }
                console.log("Color is " + fc + "Value is " + msg_data);

                satellite_graph.datasets[1].bars[base_count].fillColor = fc;
                base_count++;
            }
        }

        satellite_graph.update();
    });

    socket.on("coordinate broadcast", function (msg) {
        console.log("coordinate msg received");

        // status
        $("#status_value").html("<span>" + msg.fix + "</span>");
        $("#mode_value").html("<span>" + msg.mode + "</span>");

        // coordinates
        $("#lon_value").html("<span>" + msg.lon.toFixed(8) + "</span>");
        $("#lat_value").html("<span>" + msg.lat.toFixed(8) + "</span>");
        $("#height_value").html("<span>" + msg.height.toFixed(8) + "</span>");

    });
});
