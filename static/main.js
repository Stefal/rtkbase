function createInputTypeForm(select_id, container_id) {
    select_id = select_id + " option:selected";
    var selected_option = $(select_id).text();
    var new_form = "";
    var input_number = parseInt(select_id.charAt(6)); // the number of input, to be included in all ids

    var sel = '<label for="format">Input format: </label>' +
        '<select id="format">' +
        '<option value="rtcm2">rtcm2</option>' +
        '<option value="rtcm3">rtcm3</option>' +
        '<option value="oem4">oem4</option>' +
        '<option value="oem3">oem3</option>' +
        '<option value="ubx" selected>ubx</option>' +
        '<option value="ss2">ss2</option>' +
        '<option value="hemis">hemis</option>' +
        '<option value="skytraq">skytraq</option>' +
        '<option value="sp3">sp3</option>' +
        '</select>';

    switch (selected_option) {
        case "Off":
            break;
        case "Serial":
            new_form = '<label for="serial_port_value">Serial Device: </label>' +
                '<input type="text" id="serial_port_value" value="/dev/MFD1" data-clear-btn="true"/>' +
                '<label for="serial_port_baudrate">Baudrate: </label>' +
                '<select id="serial_port_baudrate"><option>9600</option><option>115200</option></select>';
            break;
        case "File":
            new_form = '<label for="file_path">Absolute Path to the file</label>' +
                '<input type="text" id="file_path" value="/home/root/" data-clear-btn="true"/>';
            break;
        case "TCP client":
            new_form = '<label for="tcp_client_address">TCP address</label>' +
                '<input type="text" id="tcp_client_address" value="192.168.1." data-clear-btn="true"/>';
            break;
        case "TCP server":
            new_form = '<label for="tcp_server_address">TCP address</label>' +
                '<input type="text" id="tcp_server_address" value="localhost" data-clear-btn="true"/>' +
                '<label for="tcp_server_port">TCP port</label>' +
                '<input type="text" id="tcp_server_port" data-clear-btn="true" data-clear-btn="true"/>';
            break;
        case "NTRIP client":
            new_form = '<label for="ntrip_client_address">NTRIP address: </label>' +
                '<input type="text" id="ntrip_client_address" data-clear-btn="true"/>' +
                '<label for="ntrip_client_port">Port: </label>' +
                '<input type="text" id="ntrip_client_port" data-clear-btn="true"/>' +
                '<label for="ntrip_mount_point">Mount point</label>' +
                '<input type="text" id="ntrip_mount_point" data-clear-btn="true"/>' +
                '<label for="ntrip_client_username">Username: </label>' +
                '<input type="text" id="ntrip_client_username" data-clear-btn="true"/>' +
                '<label for="ntrip_client_password">Password: </label>' +
                '<input type="text" id="ntrip_client_password" data-clear-btn="true"/>';
            break;
        case "ftp":
            new_form = '<label for="ftp_path">FTP path: </label>' +
                '<input type="text" id="ftp_path" data-clear-btn="true"/>';
            break;
        case "http":
            new_form = '<label for="http_path">HTTP path: </label>' +
                '<input type="text" id="http_path" data-clear-btn="true"/>';
            break;
    }

    if (select_id != "Off") {
        new_form = sel + new_form;
    }

    //update form vars
    $(container_id).html(new_form).trigger("create");
}

$(document).ready(function () {

    // Initial formatting for the info blocks
    var grid_style = {
        backgroundColor: "Gainsboro",
        border: "1px solid black",
        textAlign: "left"
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

    // Config form settings

    // input 1 type active form
    $("#input1_type").change(function () {
        createInputTypeForm("#input1_type", "#input1_type_parameters");
    });

    // input 2 type active form
    $("#input2_type").change(function () {
        createInputTypeForm("#input2_type", "#input2_type_parameters");
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
