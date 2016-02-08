// here we will register events for all buttons/switches and so on...
// it is guaranteed the binding will only trigger once, on the first time
// config page is opened

// this function adds '.conf' to save as form if we want to enter new title
function checkConfTitle() {
    var conf = $('#config_select_hidden').val();

    if($('#config_select_hidden').val() == 'custom'){
        $('input[name=config-title]').val('');
        $('input[name=config-title]').prop('type', 'text');
        $('input[name=config-title]').parent().css({'visibility':'visible', 'border':'1px solid #ddd', 'width':'125px', 'float':'left' ,'margin-right':'10px'});
        $('.conf_tail').css('display', 'inline');
    }
    else{
        $('input[name=config-title]').val(conf.substr(0, conf.length - 5));
        $('input[name=config-title]').prop('type', 'hidden');
        $('input[name=config-title]').parent().css({'visibility':'hidden', 'border':'none'});
        $('.conf_tail').css('display', 'none');
    }
}

function extractTimeFromLogName(log_name) {
    var hours = log_name.slice(12, 14);
    var minutes = log_name.slice(14, 16);
    var day = log_name.slice(10, 12);
    var month = log_name.slice(8, 10);
    var year = log_name.slice(4, 8);

    return hours + ":" + minutes + " " + day + "." + month + "." + year;
}

function formConversionStatusDialog(dialog_id) {

    var resulting_string = '<p id="' + dialog_id + '" ';
    resulting_string += 'class="log_conversion_status_string">';
    resulting_string += 'Waiting...</p>';

    return resulting_string;
}

function updateConversionStatusDialog(log_being_converted, conversion_status) {
    var dialog_id = log_being_converted + "_status";
    dialog_id = dialog_id.replace(".", "_");
    var logs_list = $("#logs_list");

    console.log("Updating dialog id == '" + dialog_id + "' with status " + conversion_status);

    $("#" + dialog_id).html("<strong>" + conversion_status + "</strong>");
    logs_list.listview("refresh");
}

function createCancelConversionButton(log_being_converted) {
    var dialog_id = "delete_" + log_being_converted;
    dialog_id = dialog_id.replace(".", "_");
    var logs_list = $("#logs_list");

    console.log("Updating icon from delete to cancel on button " + dialog_id);
    console.log("Current icon is " + $("#" + dialog_id).attr("data-icon"));
    // dialog_id = dialog_id.replace(".", "_");

    $("#" + dialog_id).attr("data-icon", "forbidden");
    $("#" + dialog_id).addClass("ui-icon-forbidden").removeClass("ui-icon-delete");
    $("#" + dialog_id).addClass("cancel-log-button").removeClass("delete-log-button");
    $("#" + dialog_id).attr("title", "Cancel");
    $("#" + dialog_id).text("Cancel");

    logs_list.listview("refresh");

    $(".cancel-log-button").off("click");
    $(".cancel-log-button").on("click", function () {
        console.log("Sending cancel msg");
        socket.emit("cancel log conversion", {"name": log_being_converted});
    })
}

function deleteCancelConversionButton(log_being_converted) {
    var dialog_id = "delete_" + log_being_converted;
    dialog_id = dialog_id.replace(".", "_");
    var logs_list = $("#logs_list");

    console.log("Updating icon from delete to cancel on button " + dialog_id);
    console.log("Current icon is " + $("#" + dialog_id).attr("data-icon"));
    // dialog_id = dialog_id.replace(".", "_");

    $(".cancel-log-button").off("click");
    $(".cancel-log-button").on("click", function () {
        var log_to_delete = $(this).parent().children('.log_string').attr('id').slice(6);
        $(this).parent().remove();

        console.log("Delete log: " + log_to_delete);
        socket.emit("delete log", {"name": log_to_delete});

        if($('.log_string').length == '0') {
            $('.empty_logs').css('display', 'block');
        }
    })

    $("#" + dialog_id).attr("data-icon", "delete");
    $("#" + dialog_id).removeClass("ui-icon-forbidden").addClass("ui-icon-delete");
    $("#" + dialog_id).removeClass("cancel-log-button").addClass("delete-log-button");
    $("#" + dialog_id).attr("title", "Delete");
    $("#" + dialog_id).text("Delete");

    logs_list.listview("refresh");
}

function setConversionTimer(log_being_converted, time_string) {
        var msg = "Converting log to RINEX...Approximate time left: ";
        var formatted_time = Math.floor(time_string / 60) + ' minutes ' + time_string % 60 + ' seconds';

        var dialog_id = log_being_converted + "_status";
        dialog_id = dialog_id.replace(".", "_");

        $('#' + dialog_id).html("<strong>" + msg + formatted_time + "</strong>");

        console.log("Setting conversion timer for " + dialog_id);
        console.log("Timer string is " + time_string);

        var intervalID = setInterval(function() {
           --time_string;
           formatted_time = Math.floor(time_string / 60) + ' minutes ' + time_string % 60 + ' seconds';

           $('#' + dialog_id).html("<strong>" + msg + formatted_time + "</strong>");
        }, 1000);

        var timeoutID = setTimeout(function() {
           clearInterval(intervalID);
           $('#' + dialog_id).html("Your download will begin shortly");
        }, time_string * 1000);

        return [intervalID, timeoutID];
    }

$(document).on("pageinit", "#config_page", function() {

    console.info($("#config_select").val());
	var mode = $("input[name=radio_base_rover]:checked").val();
	if(mode == 'base')
		$('#config_select-button').parent().parent().css('display', 'none');
	else
		$('#config_select-button').parent().parent().css('display', 'block');

    $(document).on("click", "#start_button", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        console.log("Starting " + mode);
        socket.emit("start " + mode);

        if (mode == "base") {
            chart.cleanStatus(mode, "started");
        }

        $('#start_button').css('display', 'none');
        $('#stop_button').css('display', 'inline-block');
    });

    $(document).on("click", "#stop_button", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        console.log("Stopping " + mode);
        socket.emit("stop " + mode);

        // after sending the stop command, we should clean the sat graph
        // and change status in the coordinate grid

        chart.cleanStatus(mode, "stopped");

        $('#stop_button').css('display', 'none');
        $('#start_button').css('display', 'inline-block');
    });

    $(document).on("change", "#config_select", function(e) {
        var mode = $("input[name=radio_base_rover]:checked").val();
        var config_name = $("#config_select").val();

        var to_send = {};

        if (mode == "base") {
            console.log("Request for " + mode + " config");
        } else {
            // if we are in rover mode, we need to pay attention which config is currently chosen
            console.log("Request for " + mode + "config, name is " + config_name);

            if (config_name != "") {
                to_send["config_file_name"] = config_name;
            }
        }

        // visibility of reset button only for default configs
        if(jQuery.inArray( config_name, defaultConfigs ) >= 0)
            $('#reset_config_button').removeClass('ui-disabled');
        else
            $('#reset_config_button').addClass('ui-disabled');

        if($("#config_select").find('.extra_config').length != 0)
            $('#delete_config_button').removeClass('ui-disabled');
        else
            $('#delete_config_button').addClass('ui-disabled');

        socket.emit("read config " + mode, to_send);
    });

    $('#hide_buttons_button').click(function() {
        $(this).parent().find('ul').slideToggle('fast');
        return false;
    });

    // hide extra buttons with click out of extra buttons div
    $(document).click(function(event) {
        if ($(event.target).closest(".hidden_list").length)
            return
        else{
            $(".hidden_list").slideUp('fast');
            event.stopPropagation();
        }
    });

    $('#reset_config_button').click(function(){
        var conf_to_reset = $('#config_select').val();

        console.log("Reset config with name: " + conf_to_reset);
        socket.emit("reset config", {"name": conf_to_reset});
        $(".hidden_list").slideUp('fast');
    });

    $('#delete_config_button').click(function(){
        $( "#popupDelete" ).popup( "open");
        $(".hidden_list").slideUp('fast');

        $('#config-delete-submit').click(function(){

        var conf_to_delete = $('#config_delete_hidden').val();

        if(conf_to_delete != null){
            if(jQuery.inArray( conf_to_delete, defaultConfigs ) >= 0){
                console.log("Don't try to delete default config");
            }
            else{
                console.log("Delete conf: " + conf_to_delete);
                socket.emit("delete config", {"name": conf_to_delete});
            }
        }
        else
            console.log("Nothing to delete");

        $( "#popupDelete" ).popup( "close");
        });
    });

    function GetConfigToSend(){
        var config_to_send = {};
        var current_id = "";
        var current_parameter = "";
        var current_value = "";
        var current_description = "";
        var current_comment = "";

        $('input[id*="_entry"], select[id*="_entry"]').each(function(i, obj){
            if(($(this).attr('id') != 'outstr-type_entry') && ($(this).attr('id') != 'inpstr-type_entry')){
                current_parameter = obj.id.substring(0, obj.id.length - 6);
                current_id = parseInt($('input[id="' + current_parameter + '_order"]').val());
                current_value = obj.value;
                current_description = ($('input[id="' + current_parameter +'_check"]').val() == '1') ? $("label[for='" + current_parameter + "_entry']").text() : '';
                current_comment = ($('input[id="' + current_parameter +'_comment"]').val() != '') ? $('input[id="' + current_parameter +'_comment"]').val() : '';

                // console.log('id=' + current_parameter + ', value=' + current_value + ', description=' + current_description + ', comment=' + current_comment);

                var payload = {};
                payload['parameter'] = current_parameter;
                payload['value'] = current_value;

                if(current_description != '')
                    payload['description'] = current_description;
                if(current_comment != '')
                    payload['comment'] = current_comment;

                config_to_send[current_id] = payload;
            }
        });

        return (config_to_send);
    }

    $('#save_as_button').click(function(){
        var mode = $("input[name=radio_base_rover]:checked").val();
        var config_to_send = GetConfigToSend();

        $(".hidden_list").slideUp('fast');
        $( "#popupLogin" ).popup( "open");

        checkConfTitle();

        $('#config_select_hidden').change(function(){
            checkConfTitle();
        });

        $('#config-title-submit').click(function(){
            var confTitle = $('input[name=config-title]').val();
            var config_name = (confTitle.substr(confTitle.length - 5) == '.conf') ? confTitle.substr(0, confTitle.length - 5) : confTitle;

            var validSymbols = /^[a-zA-Z0-9_\-]+$/;

            if (!validSymbols.test(config_name)) {
                $('.space_alert').css('display', 'inline-block');
            }
            else{
                config_name += '.conf';
                $('.space_alert').css('display', 'none');
                $( "#popupLogin" ).popup( "close");

                console.groupCollapsed('Sending config to save as ' + config_name +':');
                    jQuery.each(config_to_send, function(i, val) {
                        console.groupCollapsed(val['parameter']);
                            console.log('value:' + val['value']);
                            console.log('comment: ' + val['comment']);
                            console.log('description: ' + val['description']);
                        console.groupEnd();
                    })
                console.groupEnd();

                if (mode != "base")
                    config_to_send["config_file_name"] = config_name;

             socket.emit("write config " + mode, config_to_send);
            }
        });
    });

    $('#save_button').click(function(){
        var mode = $("input[name=radio_base_rover]:checked").val();

        if (mode == "base") {
            $('#config-save-load-submit').click();
        }
        else
            $( "#popupSave" ).popup( "open");
    });

    $('#config-save-submit').click(function(){
        var mode = $("input[name=radio_base_rover]:checked").val();
        var config_name = $("#config_select").val();
        var config_to_send = GetConfigToSend();

        console.groupCollapsed('Sending config ' + config_name + ' to save:');
            jQuery.each(config_to_send, function(i, val) {
                console.groupCollapsed(val['parameter']);
                    console.log('value:' + val['value']);
                    console.log('comment: ' + val['comment']);
                    console.log('description: ' + val['description']);
                console.groupEnd();
            })
        console.groupEnd();

        if (mode != "base")
            config_to_send["config_file_name"] = config_name;

        socket.emit("write config " + mode, config_to_send);

        $( "#popupSave" ).popup( "close");
    });

    $('#config-save-load-submit').click(function(){
        var mode = $("input[name=radio_base_rover]:checked").val();
        var config_name = $("#config_select").val();
        var config_to_send = GetConfigToSend();

        if (mode == "base") {
            if(!$.isNumeric($('#base_pos_lat_entry').val()) || !$.isNumeric($('#base_pos_lon_entry').val()) || !$.isNumeric($('#base_pos_height_entry').val())){
                $( "#popupPos" ).popup( "open");
            }
            else{

                console.groupCollapsed('Sending config ' + config_name + ' to save and restart:');
                    jQuery.each(config_to_send, function(i, val) {
                        console.groupCollapsed(val['parameter']);
                            console.log('value:' + val['value']);
                            console.log('comment: ' + val['comment']);
                            console.log('description: ' + val['description']);
                        console.groupEnd();
                    })
                console.groupEnd();

                $('#start_button').css('display', 'none');
                $('#stop_button').css('display', 'inline-block');
                chart.cleanStatus('base', 'started');

                socket.emit("write and load config " + mode, config_to_send);

                $( "#popupSave" ).popup( "close");
            }
        }
        else {
            console.groupCollapsed('Sending config ' + config_name + ' to save and restart:');
                jQuery.each(config_to_send, function(i, val) {
                    console.groupCollapsed(val['parameter']);
                        console.log('value:' + val['value']);
                        console.log('comment: ' + val['comment']);
                        console.log('description: ' + val['description']);
                    console.groupEnd();
                })
            console.groupEnd();

            config_to_send["config_file_name"] = config_name;

            $('#start_button').css('display', 'none');
            $('#stop_button').css('display', 'inline-block');

            socket.emit("write and load config " + mode, config_to_send);

            $( "#popupSave" ).popup( "close");
        }
    });

});

$(document).on("pageinit", "#logs_page", function() {

    var interval_timer = "";
    var timeout_timer = "";

    $('.delete-log-button').each(function () {
        var current_id = $(this).attr("id");
        $(this).attr("id", current_id.replace(".", "_"));
    })


    if($('.log_string').length == '0'){
        $('.empty_logs').css('display', 'block');
    }
    else{
        $('.empty_logs').css('display', 'none');

        $('.log_string').each(function(){
            var log_state = '';
            var splitLogString = $(this).find("h2").text().split(',');

            var log_start_time = extractTimeFromLogName(splitLogString[0]);
            var log_name = splitLogString[0];
            var log_size = "(" + splitLogString[1] + " MB)"
            var log_format = splitLogString[2];

            var paragraph_id = log_name + "_status";
            paragraph_id = paragraph_id.replace(".", "_");

            $(this).find("p").attr("id", paragraph_id);

            if(splitLogString[0].slice(0, 3) == 'rov')
                log_state = 'Rover';
            else if(splitLogString[0].slice(0, 3) == 'ref')
                log_state = 'Reference';
            else if(splitLogString[0].slice(0, 3) == 'sol')
                log_state = 'Solution';
            else if(splitLogString[0].slice(0, 3) == 'bas')
                log_state = 'Base';

            $(this).find("h2").text(log_state + ': ' + log_start_time + " " + log_size + " " + log_format);

            if(splitLogString[3] == "True") {
                console.log("Found log being converted: " + log_name);
                updateConversionStatusDialog(log_name, "This log is being converted. Please wait");
                createCancelConversionButton(log_name);
            }
        });
    }

    $('.log_string').each(function() {
        $(this).on("click", function() {
            var log_to_process = $(this).parent().children('.log_string').attr('id').slice(6);
            console.log("Request to process log " + log_to_process);
            socket.emit("process log", {"name": log_to_process});
        });
    });

    $('.delete-log-button').click(function(){
        var log_to_delete = $(this).parent().children('.log_string').attr('id').slice(6);
        $(this).parent().remove();

        console.log("Delete log: " + log_to_delete);
        socket.emit("delete log", {"name": log_to_delete});

        if($('.log_string').length == '0') {
            $('.empty_logs').css('display', 'block');
        }
    });

    // show conversion status by adding a new list view field under the log we are  trying to convert/download
    socket.on("log conversion start", function(msg) {
        var log_being_converted = msg.name;
        var time_estimate = msg.conversion_time;

        console.log("Log conversion start for " + log_being_converted);

        // append a status window after the listview item
        updateConversionStatusDialog(log_being_converted, "Preparing to convert...");

        var timer_ids = setConversionTimer(log_being_converted, time_estimate);
        interval_timer = timer_ids[0];
        timeout_timer = timer_ids[1];

        console.log("Create cancel conversion button for log " + log_being_converted);
        createCancelConversionButton(log_being_converted);
    });

    socket.on("log conversion results", function(msg) {
        var log_being_converted = msg.name;
        var conversion_status = msg.conversion_status;
        var messages_parsed = msg.messages_parsed;

        console.log("Got conversion results:");
        console.log(log_being_converted + " " + conversion_status);

        var update_message = conversion_status + ". " + messages_parsed;
        clearInterval(interval_timer);
        clearTimeout(timeout_timer);
        updateConversionStatusDialog(log_being_converted, update_message);
        deleteCancelConversionButton(log_being_converted);
    });

    socket.on("log conversion failed", function(msg) {
        var log_being_converted = msg.name;
        var conversion_status = msg.conversion_status;
        var messages_parsed = msg.messages_parsed;

        console.log("Conversion failed!");
        console.log(log_being_converted + " " + conversion_status);

        var update_message = conversion_status + ". " + messages_parsed;
        updateConversionStatusDialog(log_being_converted, update_message);
    });

    socket.on("log download path", function(msg) {
        console.log("Log download path == " + msg.log_url_tail);

        var full_log_url = location.protocol + '//' + location.host + msg.log_url_tail;
        window.location.href = full_log_url;
    });

    socket.on("log conversion canceled", function(msg) {
        var log_being_converted = msg.name;
        console.log("Log conversion cancel confirmed!");

        clearInterval(interval_timer);
        clearTimeout(timeout_timer);
        updateConversionStatusDialog(log_being_converted, "log conversion canceled");
        deleteCancelConversionButton(log_being_converted);
    })

    socket.on("clean busy messages", function(msg) {
        console.log("Clearing busy messages");
        $(".log_conversion_status_string:contains('Please wait')").html("");
    });
});

$(document).on("click", ".settings", function() {
    console.log('Sending message for current RINEX version');
    socket.emit("read RINEX version");
  });

$(document).on("pageinit", "#settings", function() {

    $("#wifi_link").attr("href", location.protocol + '//' + location.host + ":5000");

    socket.on("current RINEX version", function(msg) {
        $('#rinex_version').val(msg['version']);
        $('#rinex_version').parent().find('span.config_form_field').text(msg['version']);
    });

    $(document).on("click", "#update_button", function(e) {
        var online = navigator.onLine;
        var updateStatus = 120;

        if (online) {
            console.log("Sending update message");

            $('.load_update').css('display', 'block');
            var intervalID = setInterval(function(){
                --updateStatus;
                $('.load_update p').text(updateStatus);
            }, 1000);

            setTimeout(function(){clearInterval(intervalID);$('.load_update').html('<span style="color:green;position:relative;top:20px;">Refresh the page</span>');}, 1000*60*2);
            socket.emit("update reachview");
        }
        else
            $('.connect').text('Internet connection is lost');

        return false;
    });

    $(document).on("click", "#reboot", function(e) {
        console.log("Sending message for reboot");
        socket.emit("reboot device");
        console.log('rebooting reach');
        $('#reboot_warning').text('Will now reboot, please, close the app.');

        return false;
    });

    $(document).on("click", "#turn_off_wifi", function(e) {
        console.log("Sending message for turning off wifi");
        socket.emit("turn off wi-fi");
        $('#off_wi-fi_warning').text('The app and wi-fi are now inactive until a power cycle.');

        return false;
    });

    $(document).on("change", "#rinex_version", function(e) {
        console.log("Sending message with rinex version:" + $(this).val());
        socket.emit("write RINEX version", {"version": $(this).val()});
        return false;
    });
})


// handle base/rover switching

$(document).on("change", "input[name='radio_base_rover']", function() {

    $('.loader').css('display', 'block');

    var mode = "";
    var status = "stopped";

    var to_send = {};

    switch($(this).val()) {
        case "rover":
            $('#config_select-button').parent().parent().css('display', 'block');
            $('#save_as_button').css('display', 'inline-block');
            $('#save_button').text('Save');
            $('#hide_buttons_button').css('display', 'inline-block');
            mode = "rover";
            console.log("Launching rover mode");
            socket.emit("shutdown base")
            socket.emit("launch rover");
            // $("#config_select").val("reach_single_default.conf");
            to_send["config_file_name"] = $("#config_select").val();
            break;
        case "base":
            $('#config_select-button').parent().parent().css('display', 'none');
            $('#save_as_button').css('display', 'none');
            $('#save_button').text('Save & Load');
            $('#hide_buttons_button').css('display', 'none');
            mode = "base";
            console.log("Launching base mode");
            socket.emit("shutdown rover");
            socket.emit("launch base");
        break;
    }

    chart.cleanStatus(mode, status);

    $('#stop_button').css('display', 'none');
    $('#start_button').css('display', 'inline-block');

    console.log("Request for " + mode + " config");
    socket.emit("read config " + mode, to_send);
});
