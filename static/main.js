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

// ####################### HANDLE WINDOW FOCUS/UNFOCUS #######################

var isActive = true;

function onFocus() {
    isActive = true;
}

function onBlur() {
    isActive = false;
}

// ############################### MAIN ###############################

$(document).ready(function () {

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
    var socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

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
                fillColor: "rgba(0, 255, 0, 1)",
                strokeColor: "rgba(0, 0, 0, 0.7)",
                data: [10, 10, 10, 0, 0, 0, 0, 0, 0, 0]
            }
        ]
    };

    var sat_options = {
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
    }

    // draw the satellite_graph

    var satellite_graph = new Chart(ctx, {
        type : 'bar',
        data: sat_data,
        options: sat_options
    });

    // handle data broadcast

    socket.on("my response", function (msg) {

    });

    // ####################### HANDLE SATELLITE LEVEL BROADCAST #######################

    socket.on("satellite broadcast", function (msg) {
        // check if the browser tab and app tab are active
        if ((active_tab == "Status") && (isActive == true)) {
            console.log("satellite msg received");

            // get all the keys of msg object
            var fc = 0;
            var current_level = 0;
            var current_sat = "";

            var new_sat_values = [];

            for (var k in msg) {
                new_sat_values.push({sat:k, level:msg[k]});
            }

            // sort the sat levels by ascension
            new_sat_values.sort(function(a, b) {return a.level - b.level});

            var i;
            var new_length = new_sat_values.length;

            // create 3 placeholders for the new graph values

            var new_values = new Array(10);
            var new_fill_colors = new Array(10);
            var new_labels = new Array(10);

            for (i = new_length - 10; i < new_length; i++) {
                if (i < 0) {
                    current_level = 0;
                    current_sat = "";
                } else {
                    current_sat = new_sat_values[i].sat;
                    current_level = parseInt(new_sat_values[i].level) || 0;

                    console.log("new sat values for number " + (10 - new_length + i) + ": " + current_sat + " " + current_level);

                    if (current_level < 0) {
                       current_level = 0;
                    } else if (current_level > 60) {
                        current_level = 59;
                    }

                    // take care of the fill color
                    switch (true) {
                        case (current_level < 30):
                            fc = "rgba(255, 0, 0, 0.9)"; // Red
                            break;
                        case (current_level >= 30 && current_level <= 45):
                            fc = "rgba(255, 255, 0, 0.9)"; // Yellow
                            break;
                        case (current_level >= 45):
                            fc = "rgba(0, 255, 0, 0.9)"; // Green
                            break;
                    }

                }

                new_values[10 - new_length + i] = current_level;
                new_fill_colors[10 - new_length + i] = fc;
                new_labels[10 - new_length + i] = current_sat;

                // $.each(satellite_graph.data.datasets, function (i, dataset) {
                //     dataset.data[10 - new_length + i] = current_level;
                //     dataset.metaData[10 - new_length + i].custom = {
                //         backgroundColor: fc
                //     };
                //     dataset.labels[10 - new_length + i] = current_sat
                // })

                // satellite_graph.labels[10 - new_length + i] = current_sat;
                // satellite_graph.datasets[0].data[10 - new_length + i].fillColor = fc;
                // satellite_graph.datasets[0].data[10 - new_length + i].value = current_level;
            }

            $.each(satellite_graph.data.datasets, function (i, dataset) {
                dataset.metaData.custom = {
                    backgroundColor: fc
                };
                dataset.data = new_values;
            });

            satellite_graph.data.labels = new_labels;

            satellite_graph.update();

            // find the ten biggest elements and put them on the graph

            //for (i = (new_length > 10) ? 9 : new_length - 1; i >= 0; i--) {
            //    current_sat = new_sat_values[i].sat;
            //    current_level = parseInt(new_sat_values[i].level);
            //
            //    if (current_level < 0) {
            //        current_level = 0;
            //    }
            //
            //    console.log("new sat values: " + current_sat + " " + current_level);
            //
            //    // take care of the fill color
            //    switch (true) {
            //        case (current_level< 30):
            //            fc = "rgba(255, 0, 0, 0.9)"; // Red
            //            break;
            //        case (current_level >= 30 && current_level <= 45):
            //            fc = "rgba(255, 255, 0, 0.9)"; // Yellow
            //            break;
            //        case (current_level >= 45):
            //            fc = "rgba(0, 255, 0, 0.9)"; // Green
            //            break;
            //    }
            //
            //
            //    satellite_graph.datasets[0].bars[i].fillColor = fc;
            //    satellite_graph.labels = current_sat;
            //    satellite_graph.datasets[0].bars[i].value = current_level;
            //}

        }
    });

    // ####################### HANDLE COORDINATE MESSAGES #######################

    socket.on("coordinate broadcast", function (msg) {
        // check if the browser tab and app tab
        if ((active_tab == "Status") && (isActive == true)) {
            console.log("coordinate msg received");

            // status
            $("#status_value").html("<span>" + msg.solution_status + "</span>");
            $("#mode_value").html("<span>" + msg.positioning_mode + "</span>");

            // coordinates
            $("#lon_value").html("<span>" + msg.lon.substring(0, 9) + "</span>");
            $("#lat_value").html("<span>" + msg.lat.substring(0, 9) + "</span>");
            $("#height_value").html("<span>" + msg.height.substring(0, 9) + "</span>");

            // obs values: heartbeat
        }

    });

    // ####################### HANDLE CONFIG FORM BUTTONS #######################

    // this part is responsible for reading current configuration

    $("#get_current_state_button").unbind().click(function() {
        console.log("Request for config!");
        socket.emit("read config");
    });

    socket.on("current config", function (msg) {
        var to_append = "";
        console.log("Received current config:");

        // clean previous versions
        var form_div = $("#config_form_column_space");

        form_div.html("");

        to_append += '<div class="ui-field-contain">';

        for (var k in msg) {
            console.log("config item: " + k + " = " + msg[k]);

            to_append += '<div class="ui-field-contain>"';
            to_append += '<label for="' + k + '_entry">' + k + '</label>';
            to_append += '<input type="text" id="' + k + '_entry" value="' + msg[k] + '">';
            to_append += '</div>';
        }

        to_append += '</div>';

        form_div.html(to_append).trigger("create");

    });

    // this part is responsible for taking the changed form elements

    $("#load_and_restart_button").click(function() {
        var config_to_send = {};
        var current_id = "";
        var current_value = "";
        console.log("Request to load new config and restart");

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

        socket.emit("temp config modified", config_to_send);

    });

});
