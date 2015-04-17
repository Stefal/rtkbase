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
        labels: ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"],
        datasets: [
            {
                label: "Rover satellite levels",
                fillColor: "rgba(0, 255, 0, 0.9)",
                strokeColor: "rgba(220, 220, 220, 0.8)",
                highlightFill: "rgba(220, 220, 220, 0.75)",
                highlightStroke: "rgba(220, 220, 220, 1)",
                data: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
            },
            {
                label: "Base satellite levels",
                fillColor: "rgba(151, 187, 205, 0.9)",
                strokeColor: "rgba(151, 187, 205, 0.8)",
                highlightFill: "rgba(151, 187, 205, 0.75)",
                highlightStroke: "rgba(151, 187, 205, 1)",
                data: [50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
            }
        ]
    };

    // draw the satellite_graph

    var satellite_graph = new Chart(ctx).Bar(sat_data, {
        responsive: true,
        barDatasetSpacing: -1,
        barValueSpacing: bar_spacing
    });

    // handle data broadcast

    socket.on("my response", function (msg) {

    });

    socket.on("time broadcast", function (msg) {
        $("#height_value").html("<span>Received time: #" + msg.count + " " + msg.hours + ":" + msg.minutes + ":" + msg.seconds + "</span");
    });

    socket.on("satellite broadcast", function (msg) {
        $("#mode_value").html("<span>Received rover1 val is " + msg.rover0 + "</span>")

        // get all the keys of msg object
        var msg_keys = [];
        var rover_count = 0;
        var base_count = 0;

        for (var k in msg) {
            msg_keys.push(k);
            console.log(k);

            if (k.indexOf("rover") > -1) {
                console.log("Got rover message in " + k + " Data is " + msg[k] + " rover count is " + rover_count);
                satellite_graph.datasets[0].bars[rover_count].value = msg[k];
                rover_count++;
            }

            if (k.indexOf("base") > -1) {
                console.log("Got rover message in " + k + " Data is " + msg[k] + " rover count is " + rover_count);
                satellite_graph.datasets[1].bars[base_count].value = msg[k];
                base_count++;
            }

        }

        satellite_graph.update();
    });


});
