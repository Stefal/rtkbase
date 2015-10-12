function updateCoordinateGrid(msg) {
        // status
        $("#status_value").html("<span>" + msg.solution_status + "</span>");
        $("#mode_value").html("<span>" + msg.positioning_mode + "</span>");

        // coordinates
        // fix length of the strings

        var lon_value = msg.lon.substring(0, 9) + Array(9 - msg.lon.substring(0, 9).length + 1).join(" ");
        var lat_value = msg.lat.substring(0, 9) + Array(9 - msg.lat.substring(0, 9).length + 1).join(" ");

        var height_value = msg.height.substring(0, 9) + Array(9 - msg.height.substring(0, 9).length + 1 + 2).join(" ");

        $("#lon_value").html("<span style='white-space:pre;'>" + lon_value + "</span>");
        $("#lat_value").html("<span style='white-space:pre;'>" + lat_value + "</span>");
        $("#height_value").html("<span style='white-space:pre;'>" + height_value + "  " + "</span>");

        // TODO: obs values: heartbeat
}

function updateSatelliteGraphRover(msg) {
    // msg object contains satellite data for rover in {"name0": "level0", "name1": "level1"} format

    // we want to display the top 10 results
    var number_of_satellites = 10;

    // graph has a list of datasets. rover sat values are in the first one
    var rover_dataset_number = 1;

    // first, we convert the msg object into a list of satellites to make it sortable

    var new_sat_values = [];

    for (var k in msg) {
        new_sat_values.push({sat:k, level:msg[k]});
    }

    // sort the sat levels by ascension
    new_sat_values.sort(function(a, b) {
        var diff = a.level - b.level;

        if (Math.abs(diff) < 3) {
            diff = 0;
        }

        return diff
    });

    // next step is to cycle through top 10 values if they exist
    // and extract info about them: level, name, and define their color depending on the level

    var new_sat_values_length = new_sat_values.length;
    var new_sat_levels = [];
    var new_sat_labels = [];
    var new_sat_fillcolors = [];

    for(var i = new_sat_values_length - number_of_satellites; i < new_sat_values_length; i++) {
        // check if we actually have enough satellites to plot:
        if (i <  0) {
            // we have less than number_of_satellites to plot
            // so we fill the first bars of the graph with zeroes and stuff
            new_sat_levels.push(0);
            new_sat_labels.push("");
            new_sat_fillcolors.push("rgba(0, 0, 0, 0.9)");
        } else {
            // we have gotten to useful data!! let's add it to the the array too

            // for some reason I sometimes get undefined here. So plot zero just to be safe
            var current_level = parseInt(new_sat_values[i].level) || 0;
            var current_fillcolor;

            // determine the fill color depending on the sat level
            switch(true) {
                case (current_level < 30):
                    current_fillcolor = "rgba(255, 0, 0, 0.7)"; // Red
                    break;
                case (current_level >= 30 && current_level <= 45):
                    current_fillcolor = "rgba(255, 255, 0, 0.7)"; // Yellow
                    break;
                case (current_level >= 45):
                    current_fillcolor = "rgba(0, 255, 0, 0.7)"; // Green
                    break;
            }

            new_sat_levels.push(current_level);
            new_sat_labels.push(new_sat_values[i].sat);
            new_sat_fillcolors.push(current_fillcolor);
        }
    }

    // now, that we have a 3 arrays of names, levels and colors we add them to the graph data structure
    satellite_graph.data.datasets[rover_dataset_number].data = new_sat_levels;
    satellite_graph.data.labels = new_sat_labels;
    satellite_graph.data.datasets[rover_dataset_number].metaData.forEach(function(bar, bar_index) {
        bar.custom = {
            backgroundColor: new_sat_fillcolors[bar_index]
        };
    });

}

function updateSatelliteGraphBase(msg) {
    // this function also updates the sat levels chart, but it handles base data
    // on the contrary from the updateSatelliteGraphRover(msg) this function adds base data to the 
    // corresponding rover satellites. In other words, we have a comparison of how the rover
    // and the base see the top 10 rover's satellies

    var base_dataset_number = 0;
    var current_level = 0;
    var current_fillcolor;

    // cycle through the graphs's labels and extract base levels for them
    satellite_graph.data.labels.forEach(function(label, label_index) {
        if (label in msg) {
            // get the sat level as an integer
            current_level = parseInt(msg[label]);

            // determine the fill color depending on the sat level
            switch(true) {
                case (current_level < 30):
                    current_fillcolor = "rgba(255, 0, 0, 0.1)"; // Red
                    break;
                case (current_level >= 30 && current_level <= 45):
                    current_fillcolor = "rgba(255, 255, 0, 0.1)"; // Yellow
                    break;
                case (current_level >= 45):
                    current_fillcolor = "rgba(0, 255, 0, 0.1)"; // Green
                    break;
            }

            satellite_graph.data.datasets[base_dataset_number].data[label_index] = current_level;
            satellite_graph.data.datasets[base_dataset_number].metaData[label_index].custom = {
                backgroundColor: "rgba(186, 186, 186, 0.8)"
            }
        } else {
            // if we don't the same satellite in the base
            satellite_graph.data.datasets[base_dataset_number].data[label_index] = 0;
        }
    });

    // we update the graph here because we want to update the rover info first
    // then update base info depending on the rover's new values
    satellite_graph.update();
}

function cleanStatus(mode, status) {

    console.log("Got signal to clean the graph")

    mode = typeof mode !== "undefined" ? mode : "rtklib stopped";
    status = typeof status !== "undefined" ? status : "-";

    var empty_string_list = [];
    for (var i = 0; i < 10; i++) {
        empty_string_list[i] = "";
    }

    $.each(satellite_graph.data.datasets, function(i, dataset) {
        dataset.data = empty_string_list;
    });

    satellite_graph.data.labels = empty_string_list;
    satellite_graph.update();

    var msg = {
        "lat" : "0",
        "lon" : "0",
        "height": "0",
        "solution_status": status,
        "positioning_mode": mode
    };

    updateCoordinateGrid(msg);
}

function createGraph(){
    
    // Initial formatting for the info blocks

    var grid_style = {
        backgroundColor: "Gainsboro",
        border: "1px solid black",
        textAlign: "left"
    };

    $("#status_block").css(grid_style);
    $("#mode_block").css(grid_style);
    $("#lat_block").css(grid_style);
    $("#lon_block").css(grid_style);
    $("#height_block").css(grid_style);

    $("a.tab").click(function () {
        active_tab = $(this).text();
        console.log("Active tab = " + active_tab);
    });

    // Default values for the info boxes

    $("#mode_value").text("no link");
    $("#status_value").text("no link");
    $("#lon_value").text("0");
    $("#lat_value").text("0");
    $("#height_value").html("0");

    var canvas = $("#sat_chart_canvas");
    canvas.css("width", "99%");
    canvas.css("margin", "1%");

    var ctx = canvas.get(0).getContext("2d");

    // keep aspect ratio

    ctx.canvas.width = window.innerWidth;
    ctx.canvas.height = 0.5 * window.innerWidth;


    // satellite_graph is created based on this data

    var sat_data = {
        labels: ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0"],
        datasets: [
            {
                // base sats
                label: "Rover satellite levels",
                backgroundColor: "rgba(0, 255, 0, 1)",
                borderColor: "rgba(0, 0, 0, 1)",
                borderWidth: 1,
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            },
            {
                // rover sats
                label: "Base satellite levels",
                backgroundColor: "rgba(0, 255, 0, 1)",
                borderColor: "rgba(0, 0, 0, 1)",
                borderWidth: 1,
                data: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        ]
    };

    // change between-bar width depending on screen width
    var bar_spacing = (ctx.canvas.width > 1000) ? 10 : 2;

    var sat_options = {
        responsive: true,
        scales: {
            xAxes: [{
                display: true,
                stacked: true,
                categorySpacing: bar_spacing,
                //spacing: -101,
                gridLines: {
                    color: "rgba(0, 0, 0, 0)",
                },
                labels: {
                    fontSize: 10,
                },
            }],
            yAxes: [{
                display: true,
                gridLines: {
                    color: "rgba(0, 0, 0, 0.7)",
                },
                override: {
                    start: 0,
                    stepWidth: 10,
                    steps: 6
                }
            }]
        },
        tooltips: {
            enabled: false
        },
    };

    // draw the satellite_graph

    satellite_graph = new Chart(ctx, {
        type : 'bar',
        data: sat_data,
        options: sat_options
    });
}