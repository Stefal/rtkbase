function formGeneralBlock(){

	var prefixArr = { log: '3', out: '2', inp: '3' };

	for (key in prefixArr) {
		for(var b = prefixArr[key]; b >=1; b--){
			$(".ui-field-contain.fields-field .general-settings").prepend($('#' + key + 'str' + b + '-format_entry').parent().parent().parent());
		    $(".ui-field-contain.fields-field .general-settings").prepend($('#' + key + 'str' + b + '-path_entry').parent().parent());
    		$(".ui-field-contain.fields-field .general-settings").prepend($('#' + key + 'str' + b + '-type_entry').parent().parent().parent());
		}
	}
}


/// This function adds new inputs for particular selects

function checkInputSelects(i, method){ //inp OR out OR log
	// $('#' + method + 'str' + i + '-path_entry').val('');
	$('#' + method + 'str' + i + '-path_entry').attr('type', 'hidden');
	$('#' + method + 'str' + i + '-path_entry').parent().css({'visibility':'hidden', 'border':'none'});

	$('#' + method + 'str' + i + '-path_entry').parent().parent().css('display', 'block');
	$('#' + method + 'str' + i + '-format_entry').parent().parent().parent().css('display', 'block');
	$('div.additional' + method + i).remove();

	$('#' + method + 'str' + i + '-type_entry').parent().parent().parent().css('margin-top', '50px');
	$('#inpstr1-type_entry').parent().parent().parent().css('margin-top', '0px');

	if($('#outstr1-type_entry').val() == 'off'){
		$('#outstr2-type_entry').parent().parent().parent().css('display', 'none');
		$('#outstr2-format_entry').parent().parent().parent().css('display', 'none');
		$('#outstr2-path_entry').parent().parent().css('display', 'none');
		$('#outstr2-type_entry').val('off');
		$('#outstr2-path_entry').val('');
	}
	else
		$('#outstr2-type_entry').parent().parent().parent().css('display', 'block');


	// if($('#outstr1-path_entry').val() == ''){

	switch ($('#' + method + 'str' + i + '-type_entry').val()){
		case "off":
			$('#' + method + 'str' + i + '-format_entry').parent().parent().parent().css('display', 'none');
			$('#' + method + 'str' + i + '-path_entry').parent().parent().css('display', 'none');
			break;
		case "serial":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="device' + method + i + '" data-clear-btn="true" placeholder="Device" class="config_form_field"><input type="text" id="baudrate' + method + i + '" data-clear-btn="true" placeholder="baudrate" class="config_form_field"></div>').trigger("create");
			break;
		case "file":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="path' + method + i + '" data-clear-btn="true" placeholder="Path" class="config_form_field"></div>').trigger("create");
			break;
		case "tcpcli":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="address' + method + i + '" data-clear-btn="true" placeholder="Address" class="config_form_field"><input type="text" id="port' +method + i + '" data-clear-btn="true" placeholder="Port" class="config_form_field"></div>').trigger("create");
			break;
		case "tcpsvr":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="port' + method + i + '" data-clear-btn="true" placeholder="Port" class="config_form_field"></div>').trigger("create");
			break;
		case "ntripcli":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="address' + method + i + '" data-clear-btn="true" placeholder="Address" class="config_form_field"><input type="text" id="port' + method + i + '" data-clear-btn="true" placeholder="Port" class="config_form_field"><input type="text" id="mount' + method + i + '" data-clear-btn="true" placeholder="Mount Point" class="config_form_field"><input type="text" id="username' + method + i + '" data-clear-btn="true" placeholder="Username" class="config_form_field"><input type="text" id="password' + method + i + '" data-clear-btn="true" placeholder="Password" class="config_form_field"></div>').trigger("create");
			break;
		case "ntripsvr":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="address' + method + i + '" data-clear-btn="true" placeholder="Address" class="config_form_field"><input type="text" id="port' + method + i + '" data-clear-btn="true" placeholder="Port" class="config_form_field"><input type="text" id="mount' + method + i + '" data-clear-btn="true" placeholder="Mount Point" class="config_form_field"><input type="text" id="username' + method + i + '" data-clear-btn="true" placeholder="Username" class="config_form_field"><input type="text" id="password' + method + i + '" data-clear-btn="true" placeholder="Password" class="config_form_field"></div>').trigger("create");
			break;
		case "ftp":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="address' + method + i + '" data-clear-btn="true" placeholder="Address" class="config_form_field"></div>').trigger("create");
			break;
		case "http":
			$('#' + method + 'str' + i + '-path_entry').parent().parent().append('<div class="additional' + method + i + ' additional_general"><input type="text" id="address' + method + i + '" data-clear-btn="true" placeholder="Address" class="config_form_field"></div>').trigger("create");
			break;
	}
}

/// This function generates correct strings from inputs for upload

function formString(i, method){
	switch ($('#' + method + 'str' + i + '-type_entry').val()){
		case "off":
			break;
		case "serial":
			$('#' + method + 'str' + i + '-path_entry').val($.trim($('.additional' + method + i + ' #device' + method + i).val()) + ':' + $.trim($('.additional' + method + i + ' #baudrate' + method + i).val()) + ':8:n:1:off');
			break;
		case "file":
			$('#' + method + 'str' + i + '-path_entry').val($.trim($('.additional' + method + i + ' #path' + method + i).val()));
			break;
		case "tcpcli":
			$('#' + method + 'str' + i + '-path_entry').val($.trim($('.additional' + method + i + ' #address' + method + i).val()) + ':' + $.trim($('.additional' + method + i + ' #port' + method + i).val()));
			break;
		case "tcpsvr":
			$('#' + method + 'str' + i + '-path_entry').val(':@localhost' + ':' + $.trim($('.additional' + method + i + ' #port' + method + i).val()) + '/:');
			break;
		case "ntripcli":
			$('#' + method + 'str' + i + '-path_entry').val($.trim($('.additional' + method + i + ' #username' + method + i).val()) + ':' + $.trim($('.additional' + method + i + ' #password' + method + i).val()) + '@' + $.trim($('.additional' + method + i + ' #address' + method + i).val()) + ':' + $.trim($('.additional' + method + i + ' #port' + method + i).val()) + '/' + $.trim($('.additional' + method + i + ' #mount' + method + i).val()));
			break;
		case "ntripsvr":
			$('#' + method + 'str' + i + '-path_entry').val($.trim($('.additional' + method + i + ' #username' + method + i).val()) + ':' + $.trim($('.additional' + method + i + ' #password' + method + i).val()) + '@' + $.trim($('.additional' + method + i + ' #address' + method + i).val()) + ':' + $.trim($('.additional' + method + i + ' #port' + method + i).val()) + '/' + $.trim($('.additional' + method + i + ' #mount' + method + i).val()));
			break;
		case "ftp":
			$('#' + method + 'str' + i + '-path_entry').val($.trim($('.additional' + method + i + ' #address' + method + i).val()));
			break;
		case "http":
			$('#' + method + 'str' + i + '-path_entry').val($.trim($('.additional' + method + i + ' #address' + method + i).val()));
			break;
	}
}

/// This function parses default string for particular inputs

function defaultStringToInputs(i, method){
	var splitVal = $('#' + method + 'str' + i + '-path_entry').val().split(':');

	switch ($('#' + method + 'str' + i + '-type_entry').val()){
		case "off":
			break;
		case "serial":
			$('.additional' + method + i + ' #device' + method + i).val(splitVal['0']);
			$('.additional' + method + i + ' #baudrate' + method + i).val(splitVal['1']);
			break;
		case "file":
			$('.additional' + method + i + ' #path' + method + i).val($('#' + method + 'str' + i + '-path_entry').val());
			break;
		case "tcpcli":
			$('.additional' + method + i + ' #address' + method + i).val(splitVal['0']);
			$('.additional' + method + i + ' #port' + method + i).val(splitVal['1']);
			break;
		case "tcpsvr":
			$('.additional' + method + i + ' #port' + method + i).val(splitVal['2'].substr(0, splitVal['2'].length - 1));
			break;
		case "ntripcli": //user : pass @ address : port / mount
			$('.additional' + method + i + ' #username' + method + i).val(splitVal['0']);
			var splitPass = splitVal['1'].split('@');
			$('.additional' + method + i + ' #password' + method + i).val(splitPass['0']);
			var splitAdress = splitPass['1'].split(':');
			$('.additional' + method + i + ' #address' + method + i).val(splitAdress['0']); 
			var splitPort = splitAdress['1'].split('/');
			$('.additional' + method + i + ' #port' + method + i).val(splitPort['0']); 
			$('.additional' + method + i + ' #mount' + method + i).val(splitPort['1']);
			break;
		case "ntripsvr":
			$('.additional' + method + i + ' #username' + method + i).val(splitVal['0']);
			var splitPass = splitVal['1'].split('@');
			$('.additional' + method + i + ' #password' + method + i).val(splitPass['0']);
			var splitAdress = splitPass['1'].split(':');
			$('.additional' + method + i + ' #address' + method + i).val(splitAdress['0']); 
			var splitPort = splitAdress['1'].split('/');
			$('.additional' + method + i + ' #port' + method + i).val(splitPort['0']); 
			$('.additional' + method + i + ' #mount' + method + i).val(splitPort['1']);
			break;
		case "ftp":
			$('.additional' + method + i + ' #address' + method + i).val($('#' + method + 'str' + i + '-path_entry').val());
			break;
		case "http":
			$('.additional' + method + i + ' #address' + method + i).val($('#' + method + 'str' + i + '-path_entry').val());
			break;
	}
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
    // msg object contains satellite data for rover in {"name0": "level0", "name1": "level1"} format

    // we want to display the top 10 results
    var number_of_satellites = 10;

    // graph has a list of datasets. rover sat values are in the first one
    var rover_dataset_number = 1;

    // first, we convert the msg object into a list of satellites to make it sortable

    var new_sat_values = [];

    for (var k in msg) {
        new_sat_values.push({sat:k, level:msg[k]});
    }

    // sort the sat levels by ascension
    new_sat_values.sort(function(a, b) {
        var diff = a.level - b.level;

        if (Math.abs(diff) < 3) {
            diff = 0;
        }

        return diff
    });

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
                    current_fillcolor = "rgba(255, 0, 0, 0.7)"; // Red
                    break;
                case (current_level >= 30 && current_level <= 45):
                    current_fillcolor = "rgba(255, 255, 0, 0.7)"; // Yellow
                    break;
                case (current_level >= 45):
                    current_fillcolor = "rgba(0, 255, 0, 0.7)"; // Green
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

}

function updateSatelliteGraphBase(msg) {
    // this function also updates the sat levels chart, but it handles base data
    // on the contrary from the updateSatelliteGraphRover(msg) this function adds base data to the 
    // corresponding rover satellites. In other words, we have a comparison of how the rover
    // and the base see the top 10 rover's satellies

    var base_dataset_number = 0;
    var current_level = 0;
    var current_fillcolor;

    // cycle through the graphs's labels and extract base levels for them
    satellite_graph.data.labels.forEach(function(label, label_index) {
        if (label in msg) {
            // get the sat level as an integer
            current_level = parseInt(msg[label]);

            // determine the fill color depending on the sat level
            switch(true) {
                case (current_level < 30):
                    current_fillcolor = "rgba(255, 0, 0, 0.1)"; // Red
                    break;
                case (current_level >= 30 && current_level <= 45):
                    current_fillcolor = "rgba(255, 255, 0, 0.1)"; // Yellow
                    break;
                case (current_level >= 45):
                    current_fillcolor = "rgba(0, 255, 0, 0.1)"; // Green
                    break;
            }

            satellite_graph.data.datasets[base_dataset_number].data[label_index] = current_level;
            satellite_graph.data.datasets[base_dataset_number].metaData[label_index].custom = {
                backgroundColor: "rgba(186, 186, 186, 0.8)"
            }
        } else {
            // if we don't the same satellite in the base
            satellite_graph.data.datasets[base_dataset_number].data[label_index] = 0;
        }
    });

    // we update the graph here because we want to update the rover info first
    // then update base info depending on the rover's new values
    satellite_graph.update();
}

function cleanStatus(mode, status) {

    console.log("Got signal to clean the graph")

    mode = typeof mode !== "undefined" ? mode : "rtklib stopped";
    status = typeof status !== "undefined" ? status : "-";

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
        "solution_status": status,
        "positioning_mode": mode
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

        if (mode == "base") {
            cleanStatus(mode, "started");
        }
    });

    $(document).on("click", "#stop_button", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        console.log("Stopping " + mode);
        socket.emit("stop " + mode);

        // after sending the stop command, we should clean the sat graph
        // and change status in the coordinate grid

        cleanStatus(mode, "stopped");
    });

    $(document).on("click", "#get_current_state_button", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        var config_name = $("#config_select").val();
        var to_send = {};

        if (mode == "base") {
            console.log("Request for " + mode + " config");
        } else {
            // if we are in rover mode, we need to pay attention which config is currently chosen
            var config_name = $("#config_select").val();
            console.log("Request for " + mode + "config, name is " + config_name);

            if (config_name != "") {
                to_send["config_file_name"] = config_name;
            }
        }

        socket.emit("read config " + mode, to_send);
    });

    $(document).on("click", "#load_and_restart_button", function(e) {
        var config_to_send = {};
        var current_id = "";
        var current_value = "";

        var mode = $("input[name=radio_base_rover]:checked").val();
        var config_name = $("#config_select").val();


        console.log('got signal to write config' + config_name);
        // first, we need to read all the needed info from config form elements
        // we create a js object with this info and send to our server

        // find all the needed fields

        $('input[id*="_entry"]').each(function(i, obj){
            current_id = obj.id.substring(0, obj.id.length - 6);
            current_value = obj.value;

            console.log("id == " + current_id + " value == " + current_value);

            config_to_send[current_id] = current_value;
        });

        $('select[id*="_entry"]').each(function(i, obj){
            current_id = obj.id.substring(0, obj.id.length - 6);
            current_value = obj.value;

            console.log("id == " + current_id + " value == " + current_value);

            config_to_send[current_id] = current_value;
        });

        if (mode == "base") {
            console.log("Request to load new " + mode + " config and restart");
        } else {
            // if we are in rover mode, we need to pay attention
            // to the chosen config
            console.log("Request to load new " + mode + " config with name + " + config_name + " and restart");

            config_to_send["config_file_name"] = config_name;
        }

        socket.emit("write config " + mode, config_to_send);
    });

});

$(document).on("pageinit", "#logs_page", function() {
    $(document).on("click", "#update_button", function(e) {
        console.log("Sending update message");
        socket.emit("update reachview");
    });
});

// handle base/rover switching

$(document).on("change", "input[name='radio_base_rover']", function() {

    var mode = "";
    var status = "stopped";

    var to_send = {};

    switch($(this).val()) {
        case "rover":
            mode = "rover";
            console.log("Launching rover mode");
            // $("#config_select").selectmenu("enable");
            socket.emit("shutdown base")
            socket.emit("launch rover");
            to_send["config_file_name"] = $("#config_select").val();
            break;
        case "base":
            mode = "base";
            console.log("Launching base mode");
            socket.emit("shutdown rover");
            socket.emit("launch base");
            // $("#config_select").selectmenu("disable");
        break;
    }

    cleanStatus(mode, status);

    console.log("Request for " + mode + " config");
    socket.emit("read config " + mode, to_send);



        // var mode = $("input[name=radio_base_rover]:checked").val();
        // console.log("Starting " + mode);
        // socket.emit("start " + mode);
});

// ############################### MAIN ###############################

$(document).ready(function () {

	if(window.location.hash != '')
		window.location.href = "/";
		
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

    var canvas = $("#sat_chart_canvas");
    canvas.css("width", "99%");
    canvas.css("margin", "1%");

    var ctx = canvas.get(0).getContext("2d");

    // keep aspect ratio

    ctx.canvas.width = window.innerWidth;
    ctx.canvas.height = 0.5 * window.innerWidth;


    // satellite_graph is created based on this data

    var sat_data = {
        labels: ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
        datasets: [
            {
                // base sats
                label: "Rover satellite levels",
                backgroundColor: "rgba(0, 255, 0, 1)",
                borderColor: "rgba(0, 0, 0, 1)",
                borderWidth: 1,
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            },
            {
                // rover sats
                label: "Base satellite levels",
                backgroundColor: "rgba(0, 255, 0, 1)",
                borderColor: "rgba(0, 0, 0, 1)",
                borderWidth: 1,
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        ]
    };

    // change between-bar width depending on screen width
    var bar_spacing = (ctx.canvas.width > 1000) ? 10 : 2;

    var sat_options = {
        responsive: true,
        scales: {
            xAxes: [{
                display: true,
                stacked: true,
                categorySpacing: bar_spacing,
                //spacing: -101,
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

    console.log("SAT GRAPH DEBUG");
    console.dir(satellite_graph);

    // ####################### HANDLE REACH MODES, START AND STOP MESSAGES #######################

    // handle data broadcast

    socket.on("current state", function(msg) {
        // check if the browser tab and app tab are active

        console.log("Got message containing Reach state. Currently in " + msg.state + " mode");
        console.log("Current rover config is " + msg.rover.current_config);

        // add current configs to the dropdown menu

        var select_options = $("#config_select");
        var to_append = "";

        for (var i = 0; i < msg.available_configs.length; i++) {
            to_append += "<option value='" + msg.available_configs[i] + "'>" + msg.available_configs[i] + "</option>";
        }

        select_options.html(to_append).trigger("create");

        select_options.val(msg.rover.current_config);

        if (msg.state == "rover") {
            $('input:radio[name="radio_base_rover"]').filter('[value="rover"]').next().click();
        } else if (msg.state == "base") {
            $('input:radio[name="radio_base_rover"]').filter('[value="base"]').next().click();
        }
    });

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
            updateSatelliteGraphBase(msg);
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

    var rover_config_comments = {};

    socket.on("current config rover comments", function(msg) {
        console.log("Received current rover config comments")
        rover_config_comments = msg;
    })

    socket.on("current config rover", function(msg) {
        var to_append = "";
        var config_key = "";
        var config_value = "";
        var config_comment = "";

        console.log("Received current rover config:");

        // clean previous versions
        var form_div = $("#config_form_column_space");

        form_div.html("");

        to_append += '<div class="ui-field-contain fields-field">';
        to_append += '<div class="general-settings"></div>';
        to_append += '<button class="ui-btn" id="adv-set-btn">Advanced settings</button>';
        to_append += '<div class="advanced-settings" style="display:none">';

        if (!$.isEmptyObject(rover_config_order)) {
            for (var k in rover_config_order) {

                config_key = rover_config_order[k];

                if (rover_config_order[k] in msg) {
                    config_value = msg[rover_config_order[k]];
                    config_comment = rover_config_comments[config_key] || "";

                    if (config_comment)
                        config_comment = " # " + config_comment;

                    console.log("config rover item: " + config_key + " = " + config_value);

                    to_append += '<div class="ui-field-contain>"';
                    to_append += '<label for="' + config_key + '_entry">' + config_key  + config_comment + '</label>';

                    if( (config_comment) && (config_comment.indexOf(',') >= 0) ){
                        var splitArr = '';
                        var splitArr = config_comment.split(',');

                        var topClassArr = ['inpstr1-type', 'inpstr1-format' ,'inpstr2-type', 'inpstr2-format', 'inpstr3-type', 'inpstr3-format', 'outstr1-type', 'outstr1-format' , 'outstr2-type', 'outstr2-format', 'logstr1-type', 'logstr1-format', 'logstr2-type', 'logstr2-format', 'logstr3-type', 'logstr3-format'];

                        if(jQuery.inArray(config_key, topClassArr) >= 0)
							to_append +=  '<select name="select-native-1" id="' + config_key + '_entry" class="config_form_field top_input">';
						else
							to_append +=  '<select name="select-native-1" id="' + config_key + '_entry" class="config_form_field">';
                        
                        $.each(splitArr, function(index, value){
                            value = value.replace(/[# (]+/g,'').replace(/[)]+/g,'');
                            var innerSplit = '';
                            var innerSplit = value.split(':');

                            if(innerSplit['1'] == config_value)
	                            to_append += '<option value="' + innerSplit['1'] + '" selected="selected">' + innerSplit['1'] + '</option>';
	                        else
	                        	to_append += '<option value="' + innerSplit['1'] + '">' + innerSplit['1'] + '</option>';
                        })

                        to_append += '</select>';
                    }
                    else
                        to_append += '<input type="text" data-clear-btn="true" id="' + config_key + '_entry" value="' + config_value + '" class="config_form_field" >';                    

                    to_append += '</div>';
                }
            }

        }

        to_append += '</div>';
        to_append += '</div>';

        form_div.html(to_append).trigger("create");

        formGeneralBlock();

        $(document).on("change", '.top_input', function() {
			var method = $(this).attr('id').substr(0, 3);
			var numb = $(this).attr('id').substr(6, 1);

			$('#' + method + 'str' + numb + '-path_entry').val('');
			checkInputSelects(numb, method);

		});

		$(document).on("change", '.additional_general input', function() {
			
			$(this).parent().parent().removeClass('additional_general');
			
			var method = $(this).parent().parent().attr('class').substr(10, 3);
			var numb = $(this).parent().parent().attr('class').substr(13, 1);
			
			formString(numb, method);

			$(this).parent().parent().addClass('additional_general');
		});

		$('#adv-set-btn').click( function(){
			$( ".advanced-settings" ).slideToggle('slow');
			return false;
		})

		var prefixArr = { inp: '3', out: '2', log: '3' };
		
		for (key in prefixArr) {
			for(var b = 1; b <=prefixArr[key]; b++){
				checkInputSelects(b, key);
				defaultStringToInputs(b, key);
				formString(b, key);
			}
		}
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














