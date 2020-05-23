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

    //Ask server for starting rtkrcv or we won't have any data
    socket.emit("start base");

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

    var msg_status = {
            "lat" : "0",
            "lon" : "0",
            "height": "0"
            //"solution status": status,
            //"positioning mode": mode
        };

    updateCoordinateGrid(msg_status)

    // ####################### MAP ####################################################


    var map = L.map('map').setView({lon: 0, lat: 0}, 2);

    L.tileLayer('https://osm.vtech.fr/hot/{z}/{x}/{y}.png?uuid=2fc148f4-7018-4fd0-ac34-6b626cdc97a1', {
        maxZoom: 20,
        attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a> ' +
            '<a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a> ' +
            '| <a href="https://cloud.empreintedigitale.fr">Empreinte digitale</a>',
        tileSize: 256,
        
    }).addTo(map);

    // Add marker
    var locMark = L.marker({lng: 0, lat: 0}).addTo(map);

    // Move map view with marker location
    locMark.addEventListener("move", function() {
        const reduceBounds = map.getBounds().pad(-0.4);
        if (reduceBounds.contains(locMark.getLatLng()) != true) {
            console.log("location marker is outside the bound, moving the map");
            map.flyTo(locMark.getLatLng(), 20);
        }
    });

    // ####################### HANDLE SATELLITE LEVEL BROADCAST #######################

    socket.on("satellite broadcast rover", function(msg) {
            //Tell the server we are still here
            socket.emit("on graph");
            
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

        //update map marker position
        // TODO refactoring with the same instructions in graph.js
        var coordinates = (typeof(msg['pos llh single (deg,m) rover']) == 'undefined') ? '000' : msg['pos llh single (deg,m) rover'].split(',');

        var lat_value = coordinates[0].substring(0, 11) + Array(11 - coordinates[0].substring(0, 11).length + 1).join(" ");
        var lon_value = coordinates[1].substring(0, 11) + Array(11 - coordinates[1].substring(0, 11).length + 1).join(" ");

        locMark.setLatLng({lng: Number(lon_value), lat: Number(lat_value)});
    });

    socket.on("current config rover", function(msg) {
        showRover(msg);
    });

    socket.on("current config base", function(msg) {
        showBase(msg);
    });
});