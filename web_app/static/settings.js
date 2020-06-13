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


// ############################### MAIN ###############################

$(document).ready(function () {

	if(window.location.hash != '')
		window.location.href = "/";

    // We don't want to do extra work like updating the graph in background

    // SocketIO namespace:
    namespace = "/test";

    // initiate SocketIO connection
    socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

    // say hello on connect
    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });
    console.log("main.js Asking for service status");
    socket.emit("get services status");

    socket.on('disconnect', function(){
        console.log('disconnected');
    });

    //Enable "Save" button when form value is changed
    $("form").on('input', 'input, select', function() {
        console.log("change detected")
          $(this).closest("form").find("button").removeAttr("disabled");
        });

    // Send saved settings to back-end
    $("form").submit(function(e) {
        var formdata = $( this ).serializeArray();
      formdata.push({"source_form" : e.currentTarget.id});
      socket.emit("form data", formdata);
      e.preventDefault();
      });
    
    // ####################### HANDLE RTKBASE SERVICES    #######################

    socket.on("services status", function(msg) {
        // gestion des services
        var servicesStatus = JSON.parse(msg);
        console.log("service status: " + servicesStatus);
        

        // ################ MAiN service Switch  ######################
        console.log("REFRESHING  service switch");

        
        // set the switch to on/off depending of the service status
        if (servicesStatus[0].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            $('#main-switch').bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            $('#main-switch').bootstrapToggle('off', true);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#main-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            console.log("Main SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "main", "active" : switchStatus});
            
        })

        // ####################  NTRIP service Switch #########################

        // set the switch to on/off depending of the service status
        if (servicesStatus[1].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            $('#ntrip-switch').bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            $('#ntrip-switch').bootstrapToggle('off', true);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#ntrip-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            console.log("Ntrip SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "ntrip", "active" : switchStatus});
            
        })

        // ####################  RTCM server service Switch #########################

        // set the switch to on/off depending of the service status
        if (servicesStatus[2].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            $('#rtcm_svr-switch').bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            $('#rtcm_svr-switch').bootstrapToggle('off', true);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#rtcm_svr-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            console.log("RTCM Server SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "rtcm_svr", "active" : switchStatus});
            
        })
    
        // ####################  LOG service Switch #########################

        // set the switch to on/off depending of the service status
        if (servicesStatus[3].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            $('#file-switch').bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            $('#file-switch').bootstrapToggle('off', true);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#file-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            console.log("File SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "file", "active" : switchStatus});
            
        })

    })

    socket.on("system time corrected", function(msg) {
        $('.warning_footer h1').text("Reach time synced with GPS!");
        setTimeout(function(){$('.warning_footer').slideUp()}, 5000);
        $('#stop_button').removeClass('ui-disabled');
        $('#start_button').removeClass('ui-disabled');
    })


    // ####################### HANDLE UPDATE #######################

    $('#check_update_button').on("click", function (){
        socket.emit("check update");
    });

    socket.on("new release", function(msg) {
        // open modal box asking for starting update
        response = JSON.parse(msg);
        console.log(response);
        if (response.new_release) {
            $("#updateModal .modal-title").text("Update available!");
            $("#updateModal .modal-body").append('<p class="text-center">Do you want to install <b>' + response['new_release'] +'</b>? <br>It will take a few minutes.</p>');                    
            var newFeaturesArray = response['comment'].split('\r\n');
            $("#updateModal .modal-body").append('<p><ul id="newFeatures">New features:</ul></p>');
            $.each( newFeaturesArray, function( index, value ){
                $("#newFeatures").append("<li>" + value.replace(/^\+ /g, "") + "</li>");
            });       
            $("#start-update-button").removeAttr("disabled");
            $("#updateModal").modal();
        } else {
            $("#updateModal .modal-title").text("No Update available!");
            $("#updateModal .modal-body").text("We're working on it. Come back later!");
            $("#updateModal").modal();
        }
        
    })

    $("#start-update-button").on("click", function () {
        //$("#updateModal .modal-title").text(("Installing update"));
        socket.emit("update rtkbase");
        $("#updateModal .modal-body").text("Please Wait...and refresh this page in a few minutes");
        $(this).prop("disabled", true);
        $(this).html('<span class="spinner-border spinner-border-sm"></span> Updating...');
        $("#cancel-button").prop("disabled", true);
    })

    // ####################### HANDLE CHANGING PASSWORD #######################

    document.getElementById('change_password').addEventListener("input", function(e) {
        pwd_check(this);
    })
    
    function pwd_check(input) {
        var new_pwd = document.getElementById('new_password');
        var confirm_pwd = document.getElementById('confirm_password');
        if (confirm_pwd.value != new_pwd.value) {
            confirm_pwd.setCustomValidity('Password Must be Matching.');
        } else {
            // input is valid -- reset the error message
            new_pwd.setCustomValidity('');
            confirm_pwd.setCustomValidity('');
    
        }
    }


    socket.on("password updated", function() {
        //open modal box for logout
        $("#passwordChangedModal").modal();
    })

    // ####################### HANDLE REBOOT SHUTDOWN #######################

    $("#reboot-button").on("click", function() {
        $("#rebootModal").modal();
    })
    $("#confirm-reboot-button").on("click", function() {
        socket.emit("reboot device");
    })
    $("#shutdown-button").on("click", function() {
        $("#shutdownModal").modal();
    })
    $("#confirm-shutdown-button").on("click", function() {
        socket.emit("shutdown device");
    })

    // end of document.ready
});
