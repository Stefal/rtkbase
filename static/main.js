// ####################### This function is used to create custom input forms #######################

function createIOTypeForm(select_id, container_id) {
    select_id = select_id + " option:selected";
    var selected_option = $(select_id).text();
    var new_form = "";
    var reg_exp = /\d/;
    var number = select_id.match(reg_exp);
    var format_select = "";
    var io_number = "_" + select_id.charAt(1) + number;

    console.log("New form for " + io_number);

    if (selected_option != "Off") {
        if (select_id.charAt(1) == "i") {
            format_select = '<label for="format' + io_number + '">Input format: </label>' +
                '<select id="format' + io_number + '">' +
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
        } else if (select_id.charAt(1) == "o") {
            format_select = '<label for="format' + io_number + '">Output format: </label>' +
                '<select id="format' + io_number + '">' +
                '<option value="llh">llh</option>' +
                '<option value="xyz">xyz</option>' +
                '<option value="enu">enu</option>' +
                '<option value="nmea">nmea</option>' +
                '</select>';
        }
    }

    switch (selected_option) {
        case "Off":
            break;
        case "Serial":
            new_form = '<label for="serial_port_value' + io_number + '">Serial Device: </label>' +
                '<input type="text" id="serial_port_value' + io_number + '" value="/dev/MFD1" data-clear-btn="true"/>' +
                '<label for="serial_port_baudrate' + io_number + '">Baudrate: </label>' +
                '<select id="serial_port_baudrate' + io_number + '"><option>9600</option><option>115200</option></select>';
            break;
        case "File":
            new_form = '<label for="file_path' + io_number + '">Absolute Path to the file</label>' +
                '<input type="text" id="file_path' + io_number + '" value="/home/root/" data-clear-btn="true"/>';
            break;
        case "TCP client":
            new_form = '<label for="tcp_client_address' + io_number + '">TCP address</label>' +
                '<input type="text" id="tcp_client_address' + io_number + '" value="192.168.1." data-clear-btn="true"/>';
            break;
        case "TCP server":
            new_form = '<label for="tcp_server_address' + io_number + '">TCP address</label>' +
                '<input type="text" id="tcp_server_address' + io_number + '" value="localhost" data-clear-btn="true"/>' +
                '<label for="tcp_server_port' + io_number + '">TCP port</label>' +
                '<input type="text" id="tcp_server_port' + io_number + '" data-clear-btn="true" data-clear-btn="true"/>';
            break;
        case "NTRIP client":
            new_form = '<label for="ntrip_client_address' + io_number + '">NTRIP address: </label>' +
                '<input type="text" id="ntrip_client_address' + io_number + '" data-clear-btn="true"/>' +
                '<label for="ntrip_client_port' + io_number + '">Port: </label>' +
                '<input type="text" id="ntrip_client_port' + io_number + '" data-clear-btn="true"/>' +
                '<label for="ntrip_mount_point' + io_number + '">Mount point</label>' +
                '<input type="text" id="ntrip_mount_point' + io_number + '" data-clear-btn="true"/>' +
                '<label for="ntrip_client_username' + io_number + '">Username: </label>' +
                '<input type="text" id="ntrip_client_username' + io_number + '" data-clear-btn="true"/>' +
                '<label for="ntrip_client_password' + io_number + '">Password: </label>' +
                '<input type="text" id="ntrip_client_password' + io_number + '" data-clear-btn="true"/>';
            break;
        case "NTRIP server":
            new_form = '';
            break;
        case "ftp":
            new_form = '<label for="ftp_path' + io_number + '">FTP path: </label>' +
                '<input type="text" id="ftp_path' + io_number + '" data-clear-btn="true"/>';
            break;
        case "http":
            new_form = '<label for="http_path' + io_number + '">HTTP path: </label>' +
                '<input type="text" id="http_path' + io_number + '" data-clear-btn="true"/>';
            break;
    }

    if (select_id != "Off") {
        new_form += format_select;
    }

    console.log("New form = " + new_form);

    //update form vars
    $(container_id).html(new_form).trigger("create");
}

function updateCoordinateGrid(msg) {
        // status
        $("#status_value").html("<span>" + msg.solution_status + "</span>");
        $("#mode_value").html("<span>" + msg.positioning_mode + "</span>");

        // coordinates
        // fix length of the strings
        var lon_value = msg.lon.substring(0, 9) + Array(9 - msg.lon.substring(0, 9).length + 1).join(" ");
        var lat_value = msg.lat.substring(0, 9) + Array(9 - msg.lat.substring(0, 9).length + 1).join(" ");
        var height_value = msg.height.substring(0, 9) + Array(9 - msg.height.substring(0, 9).length + 1 + 2).join(" ");

        $("#lon_value").html("<span style='white-space:pre;'>" + lon_value + "</span>");
        $("#lat_value").html("<span style='white-space:pre;'>" + lat_value + "</span>");
        $("#height_value").html("<span style='white-space:pre;'>" + height_value + "  " + "</span>");

        // TODO: obs values: heartbeat
}

function updateSatelliteGraphRover(msg) {
    // levels_for parameter determines if this is base or rover data
    // msg object contains satellite data in {"name0": "level0", "name1": "level1"} format

    // we want to display the top 10 results
    var number_of_satellites = 10;

    // graph has a list of datasets. rover sat values are in the first one
    var rover_dataset_number = 0;

    // first, we convert the msg object into a list of satellites to make it sortable

    var new_sat_values = [];

    for (var k in msg) {
        new_sat_values.push({sat:k, level:msg[k]});
    }

    // sort the sat levels by ascension
    new_sat_values.sort(function(a, b) {return a.level - b.level});

    // next step is to cycle through top 10 values if they exist
    // and extract info about them: level, name, and define their color depending on the level

    var new_sat_values_length = new_sat_values.length;
    var new_sat_levels = [];
    var new_sat_labels = [];
    var new_sat_fillcolors = [];

    for(var i = new_sat_values_length - number_of_satellites; i < new_sat_values_length; i++) {
        // check if we actually have enough satellites to plot:
        if (i <  0) {
            // we have less than number_of_satellites to plot
            // so we fill the first bars of the graph with zeroes and stuff
            new_sat_levels.push(0);
            new_sat_labels.push("");
            new_sat_fillcolors.push("rgba(0, 0, 0, 0.9)");
        } else {
            // we have gotten to useful data!! let's add it to the the array too

            // for some reason I sometimes get undefined here. So plot zero just to be safe
            var current_level = parseInt(new_sat_values[i].level) || 0;
            var current_fillcolor;

            // determine the fill color depending on the sat level
            switch(true) {
                case (current_level < 30):
                    current_fillcolor = "rgba(255, 0, 0, 0.9)"; // Red
                    break;
                case (current_level >= 30 && current_level <= 45):
                    current_fillcolor = "rgba(255, 255, 0, 0.9)"; // Yellow
                    break;
                case (current_level >= 45):
                    current_fillcolor = "rgba(0, 255, 0, 0.9)"; // Green
                    break;
            }

            new_sat_levels.push(current_level);
            new_sat_labels.push(new_sat_values[i].sat);
            new_sat_fillcolors.push(current_fillcolor);
        }
    }

    // now, that we have a 3 arrays of names, levels and colors we add them to the graph data structure
    satellite_graph.data.datasets[rover_dataset_number].data = new_sat_levels;
    satellite_graph.data.labels = new_sat_labels;
    satellite_graph.data.datasets[rover_dataset_number].metaData.forEach(function(bar, bar_index) {
        bar.custom = {
            backgroundColor: new_sat_fillcolors[bar_index]
        };
    });


    satellite_graph.update();
}

function cleanStatus() {
    console.log("Got signal to clean the graph")
    var empty_string_list = [];
    for (var i = 0; i < 10; i++) {
        empty_string_list[i] = "";
    }

    $.each(satellite_graph.data.datasets, function(i, dataset) {
        dataset.data = empty_string_list;
    });

    satellite_graph.data.labels = empty_string_list;
    satellite_graph.update();

    var msg = {
        "lat" : "0",
        "lon" : "0",
        "height": "0",
        "solution_status": "-",
        "positioning_mode": "rtklib stopped"
    };

    updateCoordinateGrid(msg);
}

// ####################### HANDLE WINDOW FOCUS/UNFOCUS #######################

var isActive = true;

function onFocus() {
    isActive = true;
}

function onBlur() {
    isActive = false;
}

// here we will register events for all buttons/switches and so on...
// it is guaranteed the binding will only trigger once, on the first time
// config page is opened

$(document).on("pageinit", "#config_page", function() {

    $(document).on("click", "#start_button", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        console.log("Starting " + mode);
        socket.emit("start " + mode);
    });

    $(document).on("click", "#stop_button", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        console.log("Stopping " + mode);
        socket.emit("stop " + mode);
        // after sending the stop command, we should clean the sat graph
        // and change status in the coordinate grid

        cleanStatus();
    });

    $(document).on("click", "#get_current_state_button", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        console.log("Request for " + mode + " config");
        socket.emit("read config " + mode);
    });

    $(document).on("click", "#load_and_restart_button", function(e) {
        var config_to_send = {};
        var current_id = "";
        var current_value = "";

        var mode = $("input[name=radio_base_rover]:checked").val();

        console.log("Request to load new " + mode + "config and restart");

        // first, we need to read all the needed info from config form elements
        // we create a js object with this info and send to our server

        // find all the needed fields
        console.log("Getting current form values!");

        $('input[type="text"][id*="_entry"]').each(function(i, obj){
            current_id = obj.id.substring(0, obj.id.length - 6);
            current_value = obj.value;

            console.log("id == " + current_id + " value == " + current_value);

            config_to_send[current_id] = current_value;
        });

        socket.emit("write config " + mode, config_to_send);
    });

});

// handle base/rover switching

$(document).on("change", "input[name='radio_base_rover']", function() {
    switch($(this).val()) {
        case "rover":
            console.log("Launching rover mode");
            socket.emit("stop base")
            socket.emit("launch rover");
            break;
        case "base":
            console.log("Launching base mode");
            socket.emit("shutdown rover");
            break;
    }
});

// ############################### MAIN ###############################

$(document).ready(function () {

    // We don't want to do extra work like updating the graph in background
    window.onfocus = onFocus;
    window.onblur = onBlur;

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
    socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

    // say hello on connect
    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });

    // Current active tab
    var active_tab = "Status";

    $("a.tab").click(function () {
        active_tab = $(this).text();
        console.log("Active tab = " + active_tab);
    });

    // Default values for the info boxes

    $("#mode_value").text("no link");
    $("#status_value").text("no link");
    $("#lon_value").text("0");
    $("#lat_value").text("0");
    $("#height_value").html("0");

    // Config FORM settings

    // Should be commented out for now
    // input 1 type active form

    //$("#input1_type").change(function () {
    //    createIOTypeForm("#input1_type", "#input1_type_parameters");
    //});
    //
    //// input 2 type active form
    //
    //$("#input2_type").change(function () {
    //    createIOTypeForm("#input2_type", "#input2_type_parameters");
    //});
    //
    //// output 1 type active form
    //
    //$("#output1_type").change(function () {
    //    createIOTypeForm("#output1_type", "#output1_type_parameters");
    //});
    //
    //// output 2 type active form
    //
    //$("#output2_type").change(function () {
    //    createIOTypeForm("#output2_type", "#output2_type_parameters");
    //});

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
        labels: ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
        datasets: [
            {
                label: "Rover satellite levels",
                backgroundColor: "rgba(0, 255, 0, 1)",
                borderColor: "rgba(0, 0, 0, 1)",
                borderWidth: 1,
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            },
            {
                label: "Base satellite levels",
                backgroundColor: "rgba(0, 255, 0, 1)",
                borderColor: "rgba(0, 0, 0, 1)",
                borderWidth: 1,
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        ]
    };

    var sat_options = {
        responsive: true,
        scales: {
            xAxes: [{
                display: true,
                categorySpacing: bar_spacing,
                gridLines: {
                    color: "rgba(0, 0, 0, 0)",
                },
                labels: {
                    fontSize: 10,
                },
            }],
            yAxes: [{
                display: true,
                gridLines: {
                    color: "rgba(0, 0, 0, 0.7)",
                },
                override: {
                    start: 0,
                    stepWidth: 10,
                    steps: 6
                }
            }]
        },
        tooltips: {
            enabled: false
        },
    };

    // draw the satellite_graph

    satellite_graph = new Chart(ctx, {
        type : 'bar',
        data: sat_data,
        options: sat_options
    });

    // ####################### HANDLE REACH MODES, START AND STOP MESSAGES #######################

    // handle data broadcast

    // ####################### HANDLE SATELLITE LEVEL BROADCAST #######################

    socket.on("satellite broadcast rover", function(msg) {
        // check if the browser tab and app tab are active
        if ((active_tab == "Status") && (isActive == true)) {
            console.log("satellite msg received");
            updateSatelliteGraphRover(msg);
        }
    });

    socket.on("satellite broadcast base", function(msg) {
        // check if the browser tab and app tab are active
        if ((active_tab == "Status") && (isActive == true)) {
            console.log("satellite msg received");
            updateSatelliteGraph("base", msg);
        }
    });
    // ####################### HANDLE COORDINATE MESSAGES #######################

    socket.on("coordinate broadcast", function(msg) {
        // check if the browser tab and app tab
        if ((active_tab == "Status") && (isActive == true)) {
            console.log("coordinate msg received");
            updateCoordinateGrid(msg);
        }

    });

    var rover_config_order = {};

    socket.on("current config rover order", function(msg) {
        console.log("Received current rover config order")
        rover_config_order = msg;
    });

    socket.on("current config rover", function(msg) {
        var to_append = "";
        var config_key = "";
        var config_value = "";

        console.log("Received current rover config:");

        // clean previous versions
        var form_div = $("#config_form_column_space");

        form_div.html("");

        to_append += '<div class="ui-field-contain">';

        if (!$.isEmptyObject(rover_config_order)) {
            for (var k in rover_config_order) {

                config_key = rover_config_order[k];

                if (rover_config_order[k] in msg) {
                    config_value = msg[rover_config_order[k]];

                    console.log("config rover item: " + config_key + " = " + config_value);

                    to_append += '<div class="ui-field-contain>"';
                    to_append += '<label for="' + config_key + '_entry">' + config_key + '</label>';
                    to_append += '<input type="text" id="' + config_key + '_entry" value="' + config_value + '">';
                    to_append += '</div>';
                }
            }

        }

        to_append += '</div>';

        form_div.html(to_append).trigger("create");
    });

    socket.on("current config base", function(msg) {
        var to_append = "";
        console.log("Received current base config:");

        // clean prev versions
        var form_div =$("#config_form_column_space");

        form_div.html("");

        to_append += '<div class="ui-field-contain">';

        for (var k in msg) {
            console.log("base config item: " + k + " = " + msg[k]);

            to_append += '<div class="ui-field-contain>"';
            to_append += '<label for="' + k + '_entry">' + k + '</label>';
            to_append += '<input type="text" id="' + k + '_entry" value="' + msg[k] + '">';
            to_append += '</div>';
        }

        to_append += '</div>';

        form_div.html(to_append).trigger("create");
    });

// end of document.ready

});














