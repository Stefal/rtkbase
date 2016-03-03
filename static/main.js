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

var defaultConfigs = ['reach_single_default.conf', 'reach_kinematic_default.conf', 'reach_base_default.conf'];

var isActive = true;
lastBaseMsg = new Object();
numOfRepetition = 0;

// ############################### MAIN ###############################

$(document).ready(function () {

	if(window.location.hash != '')
		window.location.href = "/";

    // We don't want to do extra work like updating the graph in background
    window.onfocus = true;
    window.onblur = false;

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

    chart = new Chart();
    chart.create();

    $(window).resize(function() {
        if(window.location.hash == ''){
            chart.resize();
        }
    });

    $(document).on("pagebeforeshow", "#status_page", function() {
        setTimeout(function(){chart.resize();}, 500);
    });

    // ####################### HANDLE REACH MODES, START AND STOP MESSAGES #######################

    // handle data broadcast

    socket.on("current state", function(msg) {
        // check if the browser tab and app tab are active

        if(typeof msg.state == "undefined")
            msg.state = 'base';

        console.log("Got message containing Reach state. Currently in " + msg.state + " mode");
        console.log("Current rover config is " + msg.rover.current_config);


        console.groupCollapsed('Current state received:');
            for (var k in msg){
                if((k == 'started') || (k == 'state') || (k == 'system_time_correct'))
                    console.log(k + ':' + msg[k]);
                else{
                    console.groupCollapsed(k);
                        for (var m in msg[k])
                            console.log(m + ':' + msg[k][m]);
                    console.groupEnd();   
                }     
            }
        console.groupEnd();
        // add current configs to the dropdown menu

        var select_options = $("#config_select");
        var select_options_hidden = $('#config_select_hidden');
        var delete_options_hidden = $('#config_delete_hidden');
        var available_configs_list = $('.available_configs');
        var to_append = "";
        var to_send = {};
        var mode = "";
        var status = "stopped";

        for (var i = 0; i < msg.available_configs.length; i++) {
            if(jQuery.inArray( msg.available_configs[i], defaultConfigs ) >= 0)
                to_append += "<option value='" + msg.available_configs[i] + "' class='default_config'>" + msg.available_configs[i] + "</option>";
            else
                to_append += "<option value='" + msg.available_configs[i] + "' class='extra_config'>" + msg.available_configs[i] + "</option>";
        }

        select_options.html(to_append).trigger("create");
        delete_options_hidden.html(to_append).trigger("create");
        select_options_hidden.html('<option value="custom">New config title</option>' + to_append).trigger("create");

        delete_options_hidden.find('.default_config').remove();

        select_options.val(msg.rover.current_config);

        if (msg.state == "rover") {
            $('input:radio[name="radio_base_rover"]').filter('[value="rover"]').attr( 'checked', true );
            $('#config_select-button').parent().parent().css('display', 'block');
            $('#save_as_button').css('display', 'inline-block');
            $('#save_button').text('Save');
            $('#hide_buttons_button').css('display', 'inline-block');
            mode = "rover";
            to_send["config_file_name"] = $("#config_select").val();
        } else if (msg.state == "base") {
            $('input:radio[name="radio_base_rover"]').filter('[value="base"]').attr( 'checked', true );
            $('#config_select-button').parent().parent().css('display', 'none');
            $('#save_as_button').css('display', 'none');
            $('#save_button').text('Save & Load');
            $('#hide_buttons_button').css('display', 'none');
            mode = "base";
        }

        var msg_status = {
            "lat" : "0",
            "lon" : "0",
            "height": "0",
            "solution_status": status,
            "positioning_mode": mode
        };

        updateCoordinateGrid(msg_status)

        socket.emit("read config " + mode, to_send);

        if(jQuery.inArray( msg.rover.current_config, defaultConfigs ) >= 0)
            $('#reset_config_button').removeClass('ui-disabled');
        else
            $('#reset_config_button').addClass('ui-disabled');

        if(select_options.find('.extra_config').length != 0)
            $('#delete_config_button').removeClass('ui-disabled');
        else
            $('#delete_config_button').addClass('ui-disabled');

        if(msg.started == 'yes'){
            $('#start_button').css('display', 'none');
            $('#stop_button').css('display', 'inline-block');
            chart.cleanStatus(msg.state, "started");
        }
        else{
            $('#stop_button').css('display', 'none');
            $('#start_button').css('display', 'inline-block');
        }

        if(msg.system_time_correct == false){
            $('.warning_footer h1').text("Waiting for GPS time...Is antenna connected?");
            $('.warning_footer').slideDown();
            $('#stop_button').addClass('ui-disabled');
            $('#start_button').addClass('ui-disabled');
        }

    });

    socket.on("system time corrected", function(msg) {
        $('.warning_footer h1').text("Reach time synced with GPS!");
        setTimeout(function(){$('.warning_footer').slideUp()}, 5000);
        $('#stop_button').removeClass('ui-disabled');
        $('#start_button').removeClass('ui-disabled');
    })

    socket.on("available configs", function(msg) {
        var select_options = $("#config_select");
        var select_options_hidden = $('#config_select_hidden');
        var delete_options_hidden = $('#config_delete_hidden');
        var available_configs_list = $('.available_configs');
        var oldVal = select_options.val();
        var oldNum = select_options.children('option').length;
        var to_append = "";

        for (var i = 0; i < msg.available_configs.length; i++) {
            if(jQuery.inArray( msg.available_configs[i], defaultConfigs ) >= 0)
                to_append += "<option value='" + msg.available_configs[i] + "' class='default_config'>" + msg.available_configs[i] + "</option>";
            else
                to_append += "<option value='" + msg.available_configs[i] + "' class='extra_config'>" + msg.available_configs[i] + "</option>";
        }

        select_options.html(to_append).trigger("create");
        delete_options_hidden.html(to_append).trigger("create");
        select_options_hidden.html('<option value="custom">New config title</option>' + to_append).trigger("create");
        delete_options_hidden.find('.default_config').remove();

        var newNum = select_options.children('option').length;

        if(newNum<oldNum){
            available_configs_list.val('reach_single_default.conf');
            available_configs_list.parent().find('span').html('reach_single_default.conf');
        }
        else if(newNum >= oldNum){
            available_configs_list.val(oldVal);
            available_configs_list.parent().find('span').html(oldVal);
        }

        delete_options_hidden.val(delete_options_hidden.find('option:first-child').val());
        delete_options_hidden.parent().find('span').html(delete_options_hidden.find('option:first-child').val());

        available_configs_list.change();
    });

    // ####################### HANDLE SATELLITE LEVEL BROADCAST #######################

    socket.on("satellite broadcast rover", function(msg) {
        // check if the browser tab and app tab are active
        if ((active_tab == "Status") && (isActive == true)) {

            console.groupCollapsed('Rover satellite msg received:');
                for (var k in msg)
                    console.log(k + ':' + msg[k]);
            console.groupEnd();

            chart.roverUpdate(msg);
        }
    });

    socket.on("satellite broadcast base", function(msg) {
        // check if the browser tab and app tab are active
        if ((active_tab == "Status") && (isActive == true)) {
            console.groupCollapsed('Base satellite msg received:');
                for (var k in msg)
                    console.log(k + ':' + msg[k]);
            console.groupEnd();

            chart.baseUpdate(msg);
        }
    });

    // ####################### HANDLE COORDINATE MESSAGES #######################

    socket.on("coordinate broadcast", function(msg) {
        // check if the browser tab and app tab
        if ((active_tab == "Status") && (isActive == true)) {

            console.groupCollapsed('Coordinate msg received:');
                for (var k in msg)
                    console.log(k + ':' + msg[k]);
            console.groupEnd();

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
