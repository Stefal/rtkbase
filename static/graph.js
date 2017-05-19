function Chart() {

// orig set for 20 satellites

//    this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//    this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//    this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];

// set for 21
//    this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//    this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//    this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];
//    this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];
//    this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];



    this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}];
    this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}];
    this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];

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
        var margin = {top: 30, right: 10, bottom: 30, left: 40};
        //  the size of the overall svg element
        var width = $("#bar-chart").width() - margin.left - margin.right,
            barWidth = width*0.03,
            barOffset = width*0.01;

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
            .style({stroke: "black"})
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
            .style("font-size","13px");
    }

    this.resize = function(){

        var margin = {top: 30, right: 10, bottom: 30, left: 40};
        var width = $("#bar-chart").width() - margin.left - margin.right;

        var barWidth = width*0.03;
        var barOffset = width*0.01;
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

    this.roverUpdate = function(msg){

        // msg object contains satellite data for rover in {"name0": "level0", "name1": "level1"} format

        // we want to display the top ? results
        var number_of_satellites = 24;

        // graph has a list of datasets. rover sat values are in the first one
        var rover_dataset_number = 1;

        // first, we convert the msg object into a list of satellites to make it sortable

        var new_sat_values = [];

        for (var k in msg) {
            new_sat_values.push({sat:k, level:msg[k]});
        }

        // sort the sat levels by ascension
//        new_sat_values.sort(function(a, b) {
//            var diff = a.level - b.level;
//            if (Math.abs(diff) < 3) {
//                diff = 0;
//            }
//            return diff
//         });

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
                    case (current_level < 20):
                        current_fillcolor = "#FF766C"; // Red
                        break;
                    case (current_level >= 20 && current_level <= 33):
                        current_fillcolor = "#FFEA5B"; // Yellow
                        break;
                    case (current_level >= 33):
                        current_fillcolor = "#44D62C"; // Green
                        break;
                }

                new_sat_levels.push(current_level);
                new_sat_labels.push(new_sat_values[i].sat);
                new_sat_fillcolors.push(current_fillcolor);
            }
        }

        for (var i = 0; i < new_sat_levels.length; i++) {
            this.chartdata[i]['value'] = new_sat_levels[i];
            this.chartdata[i]['color'] = new_sat_fillcolors[i];
            this.labeldata[i] = new_sat_labels[i];
        };

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

        this.labels.data(this.labeldata)
            .text(function(d) {
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
            this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];

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
//        this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//        this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//        this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];

//        this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//        this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}];
//        this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];


        this.chartdata = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}];
	this.chartdata1 = [{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'},{'value':'', 'color':'rgba(255,0,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(0,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}, {'value':'', 'color':'rgba(255,255,0,0.5)'}];
//	this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];
        this.labeldata = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''];


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
        // status
        $("#status_value").html("<span>" + msg['solution status'] + "</span>");
        $("#mode_value").html("<span>" + msg['positioning mode'] + "</span>");

        // coordinates
        var coordinates = (typeof(msg['pos llh single (deg,m) rover']) == 'undefined') ? '000' : msg['pos llh single (deg,m) rover'].split(',');

        var lat_value = coordinates[0].substring(0, 11) + Array(11 - coordinates[0].substring(0, 11).length + 1).join(" ");
        var lon_value = coordinates[1].substring(0, 11) + Array(11 - coordinates[1].substring(0, 11).length + 1).join(" ");
        var height_value = coordinates[2].substring(0, 11) + Array(11 - coordinates[2].substring(0, 11).length + 1 + 2).join(" ");

        $("#lat_value").html("<span style='white-space:pre;'>" + lat_value + "</span>");
        $("#lon_value").html("<span style='white-space:pre;'>" + lon_value + "</span>");
        $("#height_value").html("<span style='white-space:pre;'>" + height_value + "  " + "</span>");
}
