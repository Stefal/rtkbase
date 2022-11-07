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
    
    //enable tooltips
    $('[data-toggle="tooltip"]').tooltip(); 
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
        console.log("change detected");
        $(this).closest("form").find("button").removeAttr("disabled");
        });

    // Send saved settings to back-end
    $("form").submit(function(e) {
        var formdata = $( this ).serializeArray();
        formdata.push({"source_form" : e.currentTarget.id});
        socket.emit("form data", formdata);
        e.preventDefault();
        $(this).closest("form").find(":submit").prop("disabled", true);
      });
    
    // ####################### HANDLE RTKBASE SERVICES    #######################

    socket.on("services status", function(msg) {
        // gestion des services
        var servicesStatus = JSON.parse(msg);
        console.log("service status: " + servicesStatus);
        
        // ################ MAiN service Switch  ######################
        //console.log("REFRESHING  service switch");
        var mainSwitch = $('#main-switch');
        // set the switch to on/off depending of the service status
        if (servicesStatus[0].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            mainSwitch.bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            mainSwitch.bootstrapToggle('off', true);
        }
        //console.log(servicesStatus[0]);
        if (servicesStatus[0].btn_color) {
            mainSwitch.bootstrapToggle('setOnStyle', servicesStatus[0].btn_color);
        }
        if (servicesStatus[0].btn_off_color) {
            mainSwitch.bootstrapToggle('setOffStyle', servicesStatus[0].btn_off_color);
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

        // ####################  NTRIP A service Switch #########################
        var ntrip_A_Switch = $('#ntrip_A-switch');
        // set the switch to on/off depending of the service status
        if (servicesStatus[1].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            ntrip_A_Switch.bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            ntrip_A_Switch.bootstrapToggle('off', true);
        }
        //console.log(servicesStatus[1]);
        if (servicesStatus[1].btn_color) {
            ntrip_A_Switch.bootstrapToggle('setOnStyle', servicesStatus[1].btn_color);
        }
        if (servicesStatus[1].btn_off_color) {
            ntrip_A_Switch.bootstrapToggle('setOffStyle', servicesStatus[1].btn_off_color);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#ntrip_A-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            //console.log("Ntrip SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "ntrip_A", "active" : switchStatus});           
        })

        // ####################  NTRIP B service Switch #########################
        var ntrip_B_Switch = $('#ntrip_B-switch');
        // set the switch to on/off depending of the service status
        if (servicesStatus[2].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            ntrip_B_Switch.bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            ntrip_B_Switch.bootstrapToggle('off', true);
        }
        //console.log(servicesStatus[2]);
        if (servicesStatus[2].btn_color) {
            ntrip_B_Switch.bootstrapToggle('setOnStyle', servicesStatus[2].btn_color);
        }
        if (servicesStatus[2].btn_off_color) {
            ntrip_B_Switch.bootstrapToggle('setOffStyle', servicesStatus[2].btn_off_color);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#ntrip_B-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            //console.log("Ntrip SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "ntrip_B", "active" : switchStatus});           
        })

        // ################  Local NTRIP Caster service Switch #####################

        var ntripcSwitch = $('#ntripc-switch');
        // set the switch to on/off depending of the service status
        if (servicesStatus[3].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            ntripcSwitch.bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            ntripcSwitch.bootstrapToggle('off', true);
        }
        
        //console.log(servicesStatus[2]);
        if (servicesStatus[3].btn_color) {
            ntripcSwitch.bootstrapToggle('setOnStyle', servicesStatus[3].btn_color);
        }
        if (servicesStatus[3].btn_off_color) {
            ntripcSwitch.bootstrapToggle('setOffStyle', servicesStatus[3].btn_off_color);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#ntripc-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            //console.log("Ntrip Caster SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "local_ntrip_caster", "active" : switchStatus});         
        })

        // ####################  RTCM server service Switch #########################

        var rtcmSvrSwitch = $('#rtcm_svr-switch');
        // set the switch to on/off depending of the service status
        if (servicesStatus[4].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            rtcmSvrSwitch.bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            rtcmSvrSwitch.bootstrapToggle('off', true);
        }
        //console.log(servicesStatus[3]);
        if (servicesStatus[4].btn_color) {
            rtcmSvrSwitch.bootstrapToggle('setOnStyle', servicesStatus[4].btn_color);
        }
        if (servicesStatus[4].btn_off_color) {
            rtcmSvrSwitch.bootstrapToggle('setOffStyle', servicesStatus[4].btn_off_color);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#rtcm_svr-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            //console.log("RTCM Server SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "rtcm_svr", "active" : switchStatus});         
        })

        // ####################  Serial RTCM service Switch #########################
        
        var rtcmSerialSwitch = $('#rtcm_serial-switch');
        // set the switch to on/off depending of the service status
        if (servicesStatus[5].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            rtcmSerialSwitch.bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            rtcmSerialSwitch.bootstrapToggle('off', true);
        }
        //console.log(servicesStatus[4]);
        if (servicesStatus[5].btn_color) {
            rtcmSerialSwitch.bootstrapToggle('setOnStyle', servicesStatus[5].btn_color);
        }
        if (servicesStatus[5].btn_off_color) {
            rtcmSerialSwitch.bootstrapToggle('setOffStyle', servicesStatus[5].btn_off_color);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#rtcm_serial-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            //console.log("Serial RTCM SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "rtcm_serial", "active" : switchStatus});           
        })
    
        // ####################  LOG service Switch #########################

        var fileSwitch = $('#file-switch');
        // set the switch to on/off depending of the service status
        if (servicesStatus[6].active === true) {
            //document.querySelector("#main-switch").bootstrapToggle('on');
            fileSwitch.bootstrapToggle('on', true);
        } else {
            //document.querySelector("#main-switch").bootstrapToggle('off');
            fileSwitch.bootstrapToggle('off', true);
        }
        //console.log(servicesStatus[5]);
        if (servicesStatus[6].btn_color) {
            fileSwitch.bootstrapToggle('setOnStyle', servicesStatus[6].btn_color);
        }
        if (servicesStatus[6].btn_off_color) {
            fileSwitch.bootstrapToggle('setOffStyle', servicesStatus[6].btn_off_color);
        }
        
        // event for switching on/off service on user mouse click
        //TODO When the switch changes its position, this event seems attached before
        //the switch finish its transition, then fire another event.
        $( "#file-switch" ).one("change", function(e) {
            var switchStatus = $(this).prop('checked');
            //console.log(" e : " + e);
            //console.log("File SwitchStatus : " + switchStatus);
            socket.emit("services switch", {"name" : "file", "active" : switchStatus});          
        })
    })

    socket.on("system time corrected", function(msg) {
        $('.warning_footer h1').text("Reach time synced with GPS!");
        setTimeout(function(){$('.warning_footer').slideUp()}, 5000);
        $('#stop_button').removeClass('ui-disabled');
        $('#start_button').removeClass('ui-disabled');
    })

    // ############### HANDLE DETECT GNSS ################

    $('#detect_receiver_button').on("click", function (){
        detectApplyBtnElt.innerText = "Apply";
        detectApplyBtnElt.setAttribute('disabled', '');
        detectApplyBtnElt.removeAttribute('data-dismiss');
        socket.emit("detect_receiver", {"then_configure" : false});
    });
   
    var detectModalElt = document.getElementById('detectModal');
    var detectBodyElt = detectModalElt.querySelector('.modal-body > p');
    var detectApplyBtnElt = detectModalElt.querySelector('#apply-button');
    var detectCancelBtnElt = detectModalElt.querySelector('#cancel-button');

    socket.on("gnss_detection_result", function(msg) {
        // open modal box with detection result and asking for configuration if detection is a success and a u-blox receiver
        response = JSON.parse(msg);
        console.log(response);
        detectApplyBtnElt.setAttribute('data-dismiss', 'modal');
        if (response['result'] === 'success') {
            detectBodyElt.innerHTML = '<b>' + response['gnss_type'] + '</b>' + ' detected on ' + '<b>' + response['port'] + '</b>' + '<br>' + '<br>' + 'Do you want to apply?';
            detectApplyBtnElt.onclick = function (){
                document.querySelector('#com_port').value = response['port'].replace(/^\/dev\//, '');
                // NEW METHOD from https://stackoverflow.com/questions/35154348/trigger-form-submission-with-javascript
                document.getElementById("main").dispatchEvent(new SubmitEvent('submit', {cancelable: true}));
                if (response['then_configure']) {
                    // We need to wait for the service stop/restart after the previous click on form save button.
                    // Yes, it's dirty...
                    setTimeout(() => { document.querySelector('#configure_receiver_button').click(); }, 2000);
                }
                // detectBodyElt.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Configuring GNSS receiver...';
                // detectApplyBtnElt.setAttribute('disabled', '');
            };
            detectApplyBtnElt.removeAttribute('disabled');
        } else {
            detectApplyBtnElt.setAttribute('disabled', '');
            detectBodyElt.innerHTML = 'No USB GNSS receiver detected';
            // TODO add a way to send the configuration even though the receiver isn't detected. It could be useful for F9P connected with Uart.
            //detectBodyElt.innerHTML = 'No GNSS receiver detected. <br> would you still like to try to configure the receiver?';
            //detectApplyBtnElt.onclick = function (){
            //    socket.emit("configure_receiver");
            //    detectBodyElt.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Configuring GNSS receiver...';
            //    detectApplyBtnElt.setAttribute('disabled', '');
            //};
            //detectApplyBtnElt.removeAttribute('disabled');
        }
        $('#detectModal').modal();
    })

    // ############### HANDLE CONFIGURE GNSS ################

    $('#configure_receiver_button').on("click", function (){
        detectApplyBtnElt.onclick = function (){}; //remove the previous attached event which launched the gnss configuration
        detectApplyBtnElt.innerText = "Close";
        detectApplyBtnElt.setAttribute('disabled', '');
        detectCancelBtnElt.remove();
        detectBodyElt.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Configuring GNSS receiver...';
        socket.emit("configure_receiver");
        $('#detectModal').modal();
    })
    socket.on("gnss_configuration_result", function(msg) {
        response = JSON.parse(msg);
        detectApplyBtnElt.removeAttribute('disabled');
        detectApplyBtnElt.setAttribute('data-dismiss', 'modal');
        detectApplyBtnElt.innerText = "Close";
        if (response['result'] === 'success') {
            detectBodyElt.innerHTML = "GNSS receiver successfully configured";
            detectApplyBtnElt.removeAttribute('data-dismiss');
            detectApplyBtnElt.onclick = function() {
                window.location.reload();
            }
        } else {
            detectBodyElt.innerHTML = "GNSS receiver configuration failed"
        }
    });
    
    // ############### HANDLE DETECT/CONFIGURE GNSS ################
    $('#detect_and_configure_receiver_button').on("click", function (){
        detectApplyBtnElt.innerText = "Apply then configure";
        detectApplyBtnElt.setAttribute('disabled', '');
        detectApplyBtnElt.removeAttribute('data-dismiss');
        detectApplyBtnElt.onclick = function (){}; //remove the previous attached event
        socket.emit("detect_receiver" ,{"then_configure" : true});
    });

    // ####################### HANDLE UPDATE #######################

    $('#check_update_button').on("click", function (){
        socket.emit("check update");
    });

    socket.on("new release", function(msg) {
        // open modal box asking for starting update
        response = JSON.parse(msg);
        console.log(JSON.stringify(response));
        if (response.error) {
            $("#updateModal .modal-title").text("Update error!");
            $("#updateModal .modal-body").append(response['error']);
            $("#updateModal").modal();
        }else if (response.new_release) {
            $("#updateModal .modal-title").text("Update available!");
            $("#updateModal .modal-body").append('<p class="text-center">Do you want to install <b>' + response['new_release'] +'</b>? <br>It will take a few minutes.</p>');                    
            var newFeaturesArray = response['comment'].split('\r\n');
            $("#updateModal .modal-body").append('<p><ul id="newFeatures">Content:</ul></p>');
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
        $("#updateModal .modal-body").text("Please wait...Downloading update...");
        $(this).prop("disabled", true);
        $(this).html('<span class="spinner-border spinner-border-sm"></span> Updating...');
        $("#cancel-button").prop("disabled", true);
        //now, we waiting for a download result message from the server
    })

    socket.on("downloading_update", function(msg) {
        response = JSON.parse(msg);
        console.log("Downloading result: " + response);
        if (response['result'] === 'true') {
            $("#updateModal .modal-body").text("Please wait...Preparing update...");
        } else {
            $("#updateModal .modal-body").text("Download failure");
            $("#start-update-button").html('Update...');
            $("#cancel-button").prop("disabled", false);
        }
    })

    socket.on("updating_rtkbase", function() {
        $("#updateModal .modal-body").text("Please wait...Updating...");
        update_countdown(600, 0);
    })
    
    function update_countdown(remaining, count) {
        if(remaining === 0)
            location.reload();
        if (count > 15 && socket.connected) {
            $("#updateModal .modal-body").text("Update Successful!");
            $("#start-update-button").html('Refresh');
            $("#start-update-button").prop("disabled", false);
            $("#start-update-button").off("click");
            $("#start-update-button").on("click", function() {
                location.reload();
            });
        }
        setTimeout(function(){ update_countdown(remaining - 1, count + 1); }, 1000);
    };
    // Cleaning update modal box when closing it

    $("#updateModal").on('hidden.bs.modal', function(){
        $("#updateModal .modal-title").text("Update");
        $("#updateModal .modal-body").text('');
        $("#start-update-button").prop("disabled", true);
      });

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

    // ####################### HANDLE HARDWARE INFORMATIONS #######################

    socket.on("sys_informations", function(infos) {
        // todo: add comments
        var sysInfos = JSON.parse(infos);
        
        var cpuTempElt = document.getElementById("cpu_temperature");
        cpuTempElt.textContent = new Intl.NumberFormat('fullwide', { minimumFractionDigits : 1 }).format(sysInfos['cpu_temp']) + ' C°';
        if (sysInfos['cpu_temp'] > 85) {
            cpuTempElt.style.color = "red";
        } else if (sysInfos['cpu_temp'] > 70) {
            cpuTempElt.style.color = "darkorange";
        }
        else {
            cpuTempElt.style.color = "#212529";
        }
        var cpuMaxTempElt = document.getElementById("max_cpu_temperature");
        cpuMaxTempElt.textContent = new Intl.NumberFormat('fullwide', { minimumFractionDigits : 1 }).format(sysInfos['max_cpu_temp']) + 'C°)';
        if (sysInfos['max_cpu_temp'] > 85) {
            cpuMaxTempElt.style.color = "red";
        } else if (sysInfos['max_cpu_temp'] > 70) {
            cpuMaxTempElt.style.color = "darkorange";
        } else {
            cpuMaxTempElt.style.color = "#212529";
        }
        
        var upTimeElt = document.getElementById("uptime");
        upTimeElt.textContent = forHumans(sysInfos['uptime']);
        
        var volumeSpaceElt = document.getElementById("vol_space_used");
        volumeSpaceElt.textContent = sysInfos['volume_free'] + 'GB';
        document.getElementById("vol_space_max").textContent = sysInfos["volume_total"] + 'GB';
        document.getElementById("vol_space_free").textContent = sysInfos["volume_percent_used"];
        if (sysInfos['volume_free'] < 0.5) {
            volumeSpaceElt.style.color = "red";
        } else {
            volumeSpaceElt.style.color = "#212529";
        }
    })
    //source: https://stackoverflow.com/a/34270811
    /**
     * Translates seconds into human readable format of seconds, minutes, hours, days, and years
     * 
     * @param  {number} seconds The number of seconds to be processed
     * @return {string}         The phrase describing the the amount of time
    */
    function forHumans ( seconds ) {
        var levels = [
            [Math.floor(seconds / 31536000), 'y'],
            [Math.floor((seconds % 31536000) / 86400), 'd'],
            [Math.floor(((seconds % 31536000) % 86400) / 3600), 'h'],
            [Math.floor((((seconds % 31536000) % 86400) % 3600) / 60), 'mn'],
            [(((seconds % 31536000) % 86400) % 3600) % 60, 's'],
        ];
        var returntext = '';
    
        for (var i = 0, max = levels.length; i < max; i++) {
            if ( levels[i][0] === 0 ) continue;
            returntext += ' ' + levels[i][0] + '' + (levels[i][0] === 1 ? levels[i][1]: levels[i][1]);
        };
        return returntext.trim();
    }
    // ####################### HANDLE REBOOT & SHUTDOWN #######################

    $("#reboot-button").on("click", function() {
        $("#rebootModal").modal();
    })
    $("#confirm-reboot-button").on("click", function() {
        $("#rebootModal .modal-body").html('<div class="align-items-center">Auto refresh in <span id="countdown"></span>s</div>');
        $(this).html('<span class="spinner-border spinner-border-sm"></span> Rebooting...');
        $(this).prop("disabled", true);
        $("#reboot-cancel-button").prop("disabled", true);
        socket.emit("reboot device");
        reboot_countdown(60, 0);
    })

    function reboot_countdown(remaining, count) {
        if(remaining === 0)
            location.reload();
        if (count > 15 && socket.connected)
            location.reload();
        document.getElementById('countdown').innerHTML = remaining;
        setTimeout(function(){ reboot_countdown(remaining - 1, count + 1); }, 1000);
    };
    $("#shutdown-button").on("click", function() {
        $("#shutdownModal").modal();
    })
    $("#confirm-shutdown-button").on("click", function() {
        $("#shutdownModal .modal-body").html('<div class="align-items-center">Shutting down...  <div class="spinner-border ml-auto" role="status" aria-hidden="true"></div></div>');
        $("#confirm-shutdown-button").prop("disabled", true);
        $("#shutdown-cancel-button").prop("disabled", true);
        socket.emit("shutdown device");
    })

    // end of document.ready
});
