function Chart() {
//set for 37
    this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}];
    this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}];
    this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];

    this.height = parseInt(55*5);
    this.roverBars = '';
    this.baseBars = '';
    this.labels = '';
    this.svg = '';
    this.vAxis = '';
    this.verticalGuide = '';
    this.xScale = '';
    this.hAxis = '';
    this.horizontalGuide = '';

    this.create = function(){

        var grid_style = {
            borderRight: "1x solid #ddd",
            borderTop: "1px solid #ddd",
            textAlign: "left",
            borderCollapse: 'collapse',
            fontSize: '15px'
        };

        $("#status_block").css({borderRight: '1px solid #ddd'});
        $("#mode_block").css({borderRight: '1px solid #ddd'});
        $("#lat_block").css(grid_style);
        $("#lon_block").css(grid_style);
        $("#height_block").css(grid_style);
        $('.ui-grid-b .ui-bar').css({borderBottom: '1px solid #ddd',borderRight: '1px solid #ddd'});

        // Default values for the info boxes

        $("#mode_value").text("no link");
        $("#status_value").text("no link");
        $("#lon_value").text("0");
        $("#lat_value").text("0");
        $("#height_value").html("0");

        var height = 55*5;
        var margin = {top: 30, right: 10, bottom: 30, left: 35};
        //  the size of the overall svg element
        var width = $("#bar-chart").width() - margin.left - margin.right,
            barWidth = width*0.022,
            barOffset = width*0.005;

        this.svg = d3.select('#bar-chart').append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .style('background', 'white');

        var yScale = d3.scale.linear()
        .domain([0, 55])
        .range([0, height])

        this.xScale = d3.scale.ordinal()
            .rangeBands([0, width])

        var verticalGuideScale = d3.scale.linear()
            .domain([0, 55])
            .range([height, 0])

        this.vAxis = d3.svg.axis()
            .scale(verticalGuideScale)
            .orient('left')
            .ticks(10)
            .tickSize(-width, 0, 0)

        this.verticalGuide = d3.select('svg').append('g')
        this.vAxis(this.verticalGuide)
        this.verticalGuide.attr('transform', 'translate(' + 30 + ', ' + margin.top + ')')
        this.verticalGuide.selectAll('path')
            .style({fill: 'none', stroke: "black"})
        this.verticalGuide.selectAll('line')
            .style({stroke: "rgba(0,0,0,0.2)"})


        this.hAxis = d3.svg.axis()
            .scale(this.xScale)
            .orient('bottom')

        this.horizontalGuide = d3.select('svg').append('g')
        this.hAxis(this.horizontalGuide)
        this.horizontalGuide.attr('transform', 'translate(' + 30 + ', ' + (height + margin.top) + ')')
        this.horizontalGuide.selectAll('path')
            .style({fill: 'none', stroke: "black"})
        this.horizontalGuide.selectAll('line')
            .style({stroke: "black"});

        this.roverBars = this.svg.append('g')
            .attr('transform', 'translate(' + margin.left + ', ' + margin.top + ')')
            .selectAll('rect').data(this.chartdata)
            .enter().append('rect')
            .style("fill", function(data) { return data.color; })
            .style({stroke: "grey"})
            .attr('width', barWidth/2)
            .attr('height', function (data) {
                return 5*data.value;
            })
            .attr('x', function (data, i) {
                return i * (barWidth + barOffset);
            })
            .attr('y', function (data) {
                return (55*5 - 5*data.value);
            });

        this.baseBars = this.svg.append('g')
            .attr('transform', 'translate(' + margin.left + ', ' + margin.top + ')')
            .selectAll('rect').data(this.chartdata1)
            .enter().append('rect')
            .style("fill", function(data) { return data.color; })
            .style({stroke: "black"})
            .attr('width', barWidth/2)
            .attr('height', function (data) {
                return 5*data.value;
            })
            .attr('x', function (data, i) {
                return i * (barWidth + barOffset) + barWidth/2;
            })
            .attr('y', function (data) {
                return (55*5 - 5*data.value);
            });

        this.labels = this.svg.append("g")
            .attr('transform', 'translate(' + margin.left + ', ' + margin.top + ')')
            .attr("class", "labels")
            .selectAll("text")
            .data(this.labeldata)
            .enter()
            .append("text")
            .attr("dx", function(d, i) {
                return (i * (barWidth + barOffset)) + barWidth/2-14
            })
            .attr("dy", height + 20)
            .text(function(d) {
                return d;
            })
            .style("font-size","10px");
    }

    this.resize = function(){

        var margin = {top: 30, right: 10, bottom: 30, left: 35};
        var width = $("#bar-chart").width() - margin.left - margin.right;

        var barWidth = width*0.022;
        var barOffset = width*0.005;
        this.svg.attr('width', width + margin.left + margin.right)

        this.roverBars.attr("width", barWidth/2)
        .attr('x', function (data, i) {
            return i * (barWidth + barOffset);
        })
        this.baseBars.attr("width", barWidth/2)
        .attr('x', function (data, i) {
            return i * (barWidth + barOffset) + barWidth/2;
        })
        this.labels.attr("dx", function(d, i) {
            return (i * (barWidth + barOffset)) + barWidth/2-14;
        })
        this.vAxis.tickSize(-width, 0, 0)
        this.vAxis(this.verticalGuide)

        this.xScale.rangeBands([0, width])
        this.hAxis.scale(this.xScale)
        this.hAxis(this.horizontalGuide)
    }

    this.roverUpdate = function (msg) {

        // msg object contains satellite data for rover in {"name0": "level0", "name1": "level1"} format

        // TODO: make responsive to bar chart size
        // The maximum number of bars that fit in the bar chart.
        const NUMBER_OF_SATELLITES = 37;

        // The keys of the msg object as an array.
        var keys = Object.keys(msg);

        // Extract info from the msg: level, name, and define their color depending on the level,
        // we then show the entry in the bar chart.
        for (var i = 0; i < NUMBER_OF_SATELLITES; i++) {

            // Check if there is still enough satellites to plot.
            if (i < keys.length) {
                var name = keys[i];
                this.labeldata[i] = name;

                // for some reason I sometimes get undefined here. So plot zero just to be safe
                var level = parseInt(msg[name]) || 0;
                this.chartdata[i]['value'] = level;

                // Set the color of the bar depending on the level.
                if (level < 20) {
                    this.chartdata[i]['color'] = "#FF1403"; // Red
                } else if (level >= 20 && level <= 33) {
                    this.chartdata[i]['color'] = "#FFDE00"; // Yellow
                } else if (level > 33) {
                    this.chartdata[i]['color'] = "#62C902"; // Green
                }
            } else {
                // If there are not enough satellites to plot, hide the bar.
                this.chartdata[i]['value'] = 0;
                this.labeldata[i] = "";
            }
        }

        this.roverBars.data(this.chartdata)
            .transition()
            .attr('height', function (data) {
                return 5 * data.value;
            })
            .attr('y', function (data) {
                return (55 * 5 - 5 * data.value);
            })
            .style("fill", function (data) { return data.color; })
            .duration(300);

        this.labels.data(this.labeldata)
            .text(function (d) {
                return d;
            });
    }

    this.baseUpdate = function(msg){
        var base_dataset_number = 0;
        var current_level = 0;
        var current_fillcolor;
        var new_sat_levels = [];
        // var new_sat_labels = [];
        var new_sat_fillcolors = [];

        // cycle through the graphs's labels and extract base levels for them
        this.labeldata.forEach(function(label, label_index) {
            if (label in msg) {
                // get the sat level as an integer
                current_level = parseInt(msg[label]);

                new_sat_levels.push(current_level);
                new_sat_fillcolors.push("#d9d9d9");

            } else {
                // if we don't the same satellite in the base
                new_sat_levels.push(0);
                new_sat_fillcolors.push("#d9d9d9");
            }

        });
        for (var i = 0; i < new_sat_levels.length; i++) {
            this.chartdata1[i]['value'] = new_sat_levels[i];
            this.chartdata1[i]['color'] = new_sat_fillcolors[i];
        };

        if(JSON.stringify(msg) == JSON.stringify(lastBaseMsg)){
            numOfRepetition++;
        }
        else{
           lastBaseMsg = msg;
           numOfRepetition = 0;
        }

        if(numOfRepetition >= 5)
	this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}];

        this.baseBars.data(this.chartdata1)
        .transition()
        .attr('height', function (data) {
            return 5*data.value;
        })
        .attr('y', function (data) {
            return (55*5 - 5*data.value);
        })
        .style("fill", function(data) { return data.color; })
        .duration(300);
    }

    this.cleanStatus = function(mode, status) {

        this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}];
	this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}];
        this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];

        console.log("Got signal to clean the graph")

        mode = typeof mode !== "undefined" ? mode : "rtklib stopped";
        status = typeof status !== "undefined" ? status : "-";

        var empty_string_list = [];
        for (var i = 0; i < 10; i++) {
            empty_string_list[i] = "";
        }

        this.roverBars.data(this.chartdata)
        .transition()
        .attr('height', function (data) {
            return 5*data.value;
        })
        .attr('y', function (data) {
            return (55*5 - 5*data.value);
        })
        .style("fill", function(data) { return data.color; })
        .duration(300);

        this.baseBars.data(this.chartdata)
        .transition()
        .attr('height', function (data) {
            return 5*data.value;
        })
        .attr('y', function (data) {
            return (55*5 - 5*data.value);
        })
        .style("fill", function(data) { return data.color; })
        .duration(300);

        this.labels.data(this.labeldata)
            .text(function(d) {
                return d;
            });

        var msg = {
            "lat" : "0",
            "lon" : "0",
            "height": "0",
            "solution status": status,
            "positioning mode": mode
        };

        updateCoordinateGrid(msg)
    }

}

function updateCoordinateGrid(msg) {
        // coordinates
        var coordinates = (typeof(msg['pos llh single (deg,m) rover']) == 'undefined') ? '000' : msg['pos llh single (deg,m) rover'].split(',');

        var lat_value = coordinates[0].substring(0, 11) + Array(11 - coordinates[0].substring(0, 11).length + 1).join(" ");
        var lon_value = coordinates[1].substring(0, 11) + Array(11 - coordinates[1].substring(0, 11).length + 1).join(" ");
        var height_value = coordinates[2].substring(0, 11) + Array(11 - coordinates[2].substring(0, 11).length + 1 + 2).join(" ");
        $("#lat_value").html(lat_value + " °");
        $("#lon_value").html(lon_value + " °");
        $("#height_value").html(height_value + "m");
        $("#solution_status").html(msg['solution status']);
}
