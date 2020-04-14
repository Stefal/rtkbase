lastBaseMsg = new Object();
numOfRepetition = 0;

$(document).ready(function () {

    // SocketIO namespace:
    namespace = "/test";

    // initiate SocketIO connection
    socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

    // say hello on connect
    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });
    //console.log("main.js Asking for service status");
    //socket.emit("get services status");

    socket.on('disconnect', function(){
        console.log('disconnected');
    });

    chart = new Chart();
        chart.create();

    $(window).resize(function() {
        if(window.location.hash == ''){
            chart.resize();
        }
    });

    //$(document).on("pagebeforeshow", "#status_page", function() {
    //    setTimeout(function(){chart.resize();}, 500);
    //});


    var msg_status = {
            "lat" : "0",
            "lon" : "0",
            "height": "0"
            //"solution status": status,
            //"positioning mode": mode
        };

    updateCoordinateGrid(msg_status)
    // ####################### HANDLE SATELLITE LEVEL BROADCAST #######################

    socket.on("satellite broadcast rover", function(msg) {
        // check if the browser tab and app tab are active

            console.groupCollapsed('Rover satellite msg received:');
                for (var k in msg)
                    console.log(k + ':' + msg[k]);
            console.groupEnd();

            chart.roverUpdate(msg);
    });

    socket.on("satellite broadcast base", function(msg) {
        // check if the browser tab and app tab are active
        
            console.groupCollapsed('Base satellite msg received:');
                for (var k in msg)
                    console.log(k + ':' + msg[k]);
            console.groupEnd();

            chart.baseUpdate(msg);
    });

    // ####################### HANDLE COORDINATE MESSAGES #######################

    socket.on("coordinate broadcast", function(msg) {
        // check if the browser tab and app tab
        

            console.groupCollapsed('Coordinate msg received:');
                for (var k in msg)
                    console.log(k + ':' + msg[k]);
            console.groupEnd();

            updateCoordinateGrid(msg);
    });

    socket.on("current config rover", function(msg) {
        showRover(msg);
    });

    socket.on("current config base", function(msg) {
        showBase(msg);
    });
});