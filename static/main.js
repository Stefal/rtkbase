// ReachView code is placed under the GPL license.
// Written by Egor Fedorov (egor.fedorov@emlid.com)
// Copyright (c) 2015, Emlid Limited
// All rights reserved.

// If you are interested in using ReachView code as a part of a
// closed source project, please contact Emlid Limited (info@emlid.com).

// This file is part of ReachView.

// ReachView is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// ReachView is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with ReachView.  If not, see <http://www.gnu.org/licenses/>.

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

	if(window.location.hash != '')
		window.location.href = "/";

    // We don't want to do extra work like updating the graph in background
    window.onfocus = onFocus;
    window.onblur = onBlur;

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

        if(active_tab == 'Status'){
            if(!$("#sat_chart_canvas").length) {
                createGraph();
            }
        }

        console.log("Active tab = " + active_tab);
    });

    createGraph();

    console.log("SAT GRAPH DEBUG");
    console.dir(satellite_graph);

    // ####################### HANDLE REACH MODES, START AND STOP MESSAGES #######################

    // handle data broadcast

    socket.on("current state", function(msg) {
        // check if the browser tab and app tab are active

        if(typeof msg.state == "undefined")
            msg.state = 'base';

        console.log("Got message containing Reach state. Currently in " + msg.state + " mode");
        console.log("Current rover config is " + msg.rover.current_config);

        // add current configs to the dropdown menu

        var select_options = $("#config_select");
        var select_options_hidden = $('#config_select_hidden');
        var to_append = "";

        for (var i = 0; i < msg.available_configs.length; i++) {
            to_append += "<option value='" + msg.available_configs[i] + "'>" + msg.available_configs[i] + "</option>";
        }

        select_options.html(to_append).trigger("create");
        select_options_hidden.html('<option value="custom">New config title</option>' + to_append).trigger("create");

        select_options.val(msg.rover.current_config);
        select_options_hidden.val(msg.rover.current_config);

        if (msg.state == "rover") {
            $('input:radio[name="radio_base_rover"]').filter('[value="rover"]').next().click();
        } else if (msg.state == "base") {
            $('input:radio[name="radio_base_rover"]').filter('[value="base"]').next().click();
        }
    });

    socket.on("available configs", function(msg) {
        var select_options = $("#config_select");
        var select_options_hidden = $('#config_select_hidden');
        var to_append = "";

        for (var i = 0; i < msg.available_configs.length; i++) {
            to_append += "<option value='" + msg.available_configs[i] + "'>" + msg.available_configs[i] + "</option>";
        }

        select_options.html(to_append).trigger("create");
        select_options_hidden.html('<option value="custom">New config title</option>' + to_append).trigger("create");
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

    socket.on("current config rover", function(msg) {
    	showRover(msg);
    });

    socket.on("current config base", function(msg) {
    	showBase(msg);
    });

    // end of document.ready
});