// here we will register events for all buttons/switches and so on...
// it is guaranteed the binding will only trigger once, on the first time
// config page is opened
$(document).on("pageinit", "#config_page", function() {

    $('.loader').css('display', 'none');
	
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

    $(document).on("change", "#config_select", function(e) {
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
            cleanStatus(mode, "started");
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

        $('.log_string').each(function(){

            var splitLogString = $(this).text().split(',');

            var log_state = splitLogString[0].slice(0, 3);
            var log_year = splitLogString[0].slice(4, 8);
            var log_month = splitLogString[0].slice(8, 10);
            var log_day = splitLogString[0].slice(10, 12);
            var log_hour = splitLogString[0].slice(12, 14);
            var log_min = splitLogString[0].slice(14, 16);
            
            if((log_state) == 'rov')
                $(this).text('Rover: ' + log_hour + ':' + log_min + ' ' + log_day + '.' + log_month + '.' + log_year + ' (' + splitLogString[1] + 'MB)');
            else
                $(this).text('Base: ' + log_hour + ':' + log_min + ' ' + log_day + '.' + log_month + '.' + log_year + ' (' + splitLogString[1] + 'MB)');
        });

    $('.delete-log-button').click(function(){
        console.log("Sending delete message");
        return false;
    });

    $(document).on("click", "#update_button", function(e) {
        console.log("Sending update message");
        socket.emit("update reachview");
    });
});

// handle base/rover switching

$(document).on("change", "input[name='radio_base_rover']", function() {

    $('.loader').css('display', 'block');

    var mode = "";
    var status = "stopped";

    var to_send = {};

    switch($(this).val()) {
        case "rover":
            $('#config_select-button').parent().parent().css('display', 'block');
            mode = "rover";
            console.log("Launching rover mode");
            socket.emit("shutdown base")
            socket.emit("launch rover");
            to_send["config_file_name"] = $("#config_select").val();
            break;
        case "base":
            $('#config_select-button').parent().parent().css('display', 'none');
            mode = "base";
            console.log("Launching base mode");
            socket.emit("shutdown rover");
            socket.emit("launch base");
        break;
    }       

    cleanStatus(mode, status);

    console.log("Request for " + mode + " config");
    socket.emit("read config " + mode, to_send);
});
