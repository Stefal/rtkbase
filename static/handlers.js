// here we will register events for all buttons/switches and so on...
// it is guaranteed the binding will only trigger once, on the first time
// config page is opened
$(document).on("pageinit", "#config_page", function() {

    // $('.loader').css('display', 'none');

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

    $(document).on("click", ".save_configs_button", function(e) {
        var config_to_send = {};
        var current_id = "";
        var current_parameter = "";
        var current_value = "";
        var current_description = "";
        var current_comment = "";

        var mode = $("input[name=radio_base_rover]:checked").val();

        $('input[id*="_entry"]').each(function(i, obj){
            current_id = parseInt($('input[id="' + current_parameter + '_order"]').val());
            current_parameter = obj.id.substring(0, obj.id.length - 6);
            current_value = obj.value;
            current_description = ($('input[id="' + current_parameter +'_check"]').val() == '1') ? $("label[for='" + current_parameter + "_entry']").text() : '';
            current_comment = ($('input[id="' + current_parameter +'_comment"]').val() != '') ? $('input[id="' + current_parameter +'_comment"]').val() : '';

            console.log('id=' + current_parameter + ', value=' + current_value + ', description=' + current_description + ', comment=' + current_comment);

            var payload = {"parameter": current_parameter, "description": current_description, "comment": current_comment, "value": current_value}

            config_to_send[current_id] = payload;
        });

        $('select[id*="_entry"]').each(function(i, obj){
            current_id = $('input[id="' + current_parameter +'_order"]').val();
            current_parameter = obj.id.substring(0, obj.id.length - 6);
            current_value = obj.value;
            current_description = ($('input[id="' + current_parameter +'_check"]').val() == '1') ? $("label[for='" + current_parameter + "_entry']").text() : '';
            current_comment = ($('input[id="' + current_parameter +'_comment"]').val() != '') ? $('input[id="' + current_parameter +'_comment"]').val() : '';

            console.log('id=' + current_parameter + ', value=' + current_value + ', description=' + current_description + ', comment=' + current_comment);

            var payload = {"parameter": current_parameter, "description": current_description, "comment": current_comment, "value": current_value}

            config_to_send[current_id] = payload;
        });

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

        if($(this).attr('id') == 'save_as_button'){
            $( "#popupLogin" ).popup( "open");
            
            checkConfTitle();

            $('#config_select_hidden').change(function(){
            	checkConfTitle();
            });

            $('#config-title-submit').click(function(){
            	var confTitle = $('input[name=config-title]').val();
            	var config_name = (confTitle.substr(confTitle.length - 5) == '.conf') ? confTitle.substr(0, confTitle.length - 5) : confTitle;
                config_name += '.conf';

                $( "#popupLogin" ).popup( "close");
                console.log('got signal to write config ' + config_name);

	            if (mode != "base")
	                config_to_send["config_file_name"] = config_name;

            	socket.emit("write config " + mode, config_to_send);
                console.log('NEW CONFIG VALUES');
                console.log(config_to_send);
            });
        }
        else if($(this).attr('id') == 'save_button'){
            var config_name = $("#config_select").val();
            console.log('got signal to write config ' + config_name);

            if (mode != "base")
                config_to_send["config_file_name"] = config_name;

            socket.emit("write config " + mode, config_to_send);
        }
        else{
            var config_name = $("#config_select").val();
            console.log('got signal to write config ' + config_name);

            if (mode == "base") {
                console.log("Request to load new " + mode + " config and restart");
            } else {
                console.log("Request to load new " + mode + " config with name + " + config_name + " and restart");

                config_to_send["config_file_name"] = config_name;
            }

            socket.emit("write and load config " + mode, config_to_send);
        }
    });

});

$(document).on("pageinit", "#logs_page", function() {

        $('.log_string').each(function(){

            var splitLogString = $(this).text().split(',');
            var log_state = (splitLogString[0].slice(0, 3) == 'rov') ? 'Rover' :  'Base';

            $(this).text(log_state + ': ' + splitLogString[0].slice(12, 14) + ':' + splitLogString[0].slice(14, 16) + ' ' + splitLogString[0].slice(10, 12) + '.' + splitLogString[0].slice(8, 10) + '.' + splitLogString[0].slice(4, 8) + ' (' + splitLogString[1] + 'MB)');
        });

    $('.delete-log-button').click(function(){
        var log_to_delete = $(this).parent().children('.log_string').attr('href').slice(6);
        console.log("Delete log: " + log_to_delete);
        socket.emit("delete log", {"name": log_to_delete});
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
