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

    var log_date = log_name.split('_');
    var hours = log_date[1].slice(8, 10);
    var minutes = log_date[1].slice(10, 12);
    var day = log_date[1].slice(6, 8);
    var month = log_date[1].slice(4, 6);
    var year = log_date[1].slice(0, 4);

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

    $(".cancel-log-button").off("click");
    $(".cancel-log-button").on("click", function () {

        var log_to_delete = $(this).parent().children('.log_string').attr('id').slice(6);
        var log_parse = log_to_delete.split('_');

            if(log_parse[0] == 'rov')
                var log_state = 'rover';
            else if(log_parse[0] == 'ref')
                var log_state = 'reference';
            else if(log_parse[0] == 'bas')
                var log_state = 'base';
            else
                var log_state = 'solution';

        var log_date = log_parse[1].substr(8, 2) + ':' + log_parse[1].substr(10, 2) + ' ' + log_parse[1].substr(6, 2) + '.' + log_parse[1].substr(4, 2) + '.' + log_parse[1].substr(0, 4);
        
        $(this).parent().index('#logs_list .log_string');
        $('#popupSingleLogDelete').find( "#delete_log_index").val($(this).parent().find('.log_string').index('.log_string'));
        $('#popupSingleLogDelete').find( "#delete_log_title").val(log_to_delete);
        $('.current_delete_log_title').text(log_state);
        $('.current_delete_log_date').text(log_date);

        $('#popupSingleLogDelete').popup( "open");
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

function splitLogInformation(){
    if($('.log_string').length == '0'){
        $('.empty_logs').css('display', 'block');
    }
    else{
        $('.empty_logs').css('display', 'none');

        var currentTime = '';
        $('.log_string').each(function(){
            var log_state = '';
            var splitLogString = $(this).find("h2").text().split(',');

            var log_start_time = extractTimeFromLogName(splitLogString[0]);
            var time = log_start_time.split(' ');
            var log_name = splitLogString[0];
            var log_format = splitLogString[2];

            var paragraph_id = log_name + "_status";
            paragraph_id = paragraph_id.replace(".", "_");

            $(this).find("p").attr("id", paragraph_id);

            if(splitLogString[0].slice(0, 3) == 'rov')
                log_state = 'Rover';
            else if(splitLogString[0].slice(0, 3) == 'ref')
                log_state = 'Reference';
            else if(splitLogString[0].slice(0, 3) == 'bas')
                log_state = 'Base';
            else if(splitLogString[0].slice(0, 3) == 'cor')
                log_state = 'Correction';
            else
                log_state = 'Solution';

            $(this).css('border-bottom', '1px solid transparent');
            $(this).parent().find('.delete-log-button').css('border-bottom', '1px solid transparent');

            if(currentTime == time[0]){
                $(this).css('border-top', '1px dashed #ddd');
                $(this).parent().find('.delete-log-button').css('border-top', '1px dashed #ddd');
            }

            $(this).find("h2").text(time[0] + ' | ' + log_state);

            if(splitLogString[3] == "true") {
                console.log("Found log being converted: " + log_name);
                updateConversionStatusDialog(log_name, "This log is being converted. Please wait");
                createCancelConversionButton(log_name);
            }

            currentTime = time[0];
        });
    }
}

function addDivider(){
    $('.delete-log-button').each(function () {
        var current_id = $(this).attr("id");
        $(this).attr("id", current_id.replace(".", "_"));
    })

    var currentDate = '';

    $('#logs_list .data_divider').each(function(){

        var splitLogString = $(this).text();

        var log_start_time = extractTimeFromLogName(splitLogString);
        var date = log_start_time.split(' ');

        if(currentDate != date[1])
            $(this).find('span').text(date[1]);
       else
            $(this).remove();

        currentDate = date[1];
    });
}


function registerDownloadLogHandler(){
    $('.log_string').each(function() {
        $(this).on("click", function() {
            var log_to_process = $(this).parent().children('.log_string').attr('id').slice(6);
            console.log("Request to process log " + log_to_process);
            socket.emit("process log", {"name": log_to_process});
        });
    });
}

function registerDeleteLogHandler(){

    delete_day_log = false;

    $('.delete-log-button').click(function(){
        var log_to_delete = $(this).parent().children('.log_string').attr('id').slice(6);
        var log_parse = log_to_delete.split('_');

            if(log_parse[0] == 'rov')
                var log_state = 'rover';
            else if(log_parse[0] == 'ref')
                var log_state = 'reference';
            else if(log_parse[0] == 'bas')
                var log_state = 'base';
            else
                var log_state = 'solution';

        var log_date = log_parse[1].substr(8, 2) + ':' + log_parse[1].substr(10, 2) + ' ' + log_parse[1].substr(6, 2) + '.' + log_parse[1].substr(4, 2) + '.' + log_parse[1].substr(0, 4);

        $(this).parent().index('#logs_list .log_string');
        $('#popupSingleLogDelete').find( "#delete_log_index").val($(this).parent().find('.log_string').index('.log_string'));
        $('#popupSingleLogDelete').find( "#delete_log_title").val(log_to_delete);
        $('.current_delete_log_title').text(log_state);
        $('.current_delete_log_date').text(log_date);

        $('#popupSingleLogDelete').popup( "open");
    });

    $('.full_log_delete').click(function(){
        $('#popupLogDelete').popup( "open");
        $('#popupLogDelete').find( "#delete_index").val($(this).parent().index('.data_divider'));
    })
}
