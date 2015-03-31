$(document).ready(function () {

    $("#mode_value").append("mode value");
    $("#fix_value").append("3-D");
    $("#lon_value").append("60");
    $("#lat_value").append("30");
    $("#height_value").append("20");

    //maintain size chart ratio

    var current_width = $(window).width();
    var current_height = $(window).height();
    var canvas1 = $("#sat_chart1_canvas");
    var canvas2 = $("#sat_chart2_canvas");

    function drawSatChart(canvas, sat_data) {
        canvas.css("width", "99%");
        canvas.css("margin", "1%");
        var ctx = canvas.get(0).getContext("2d");
        ctx.canvas.width = window.innerWidth;
        ctx.canvas.height = 0.5 * window.innerWidth;
        new Chart(ctx).Bar(sat_data);
    }

    //delay to do autoresize less often
    var delay = (function () {
        var timer = 0;
        return function (callback, ms) {
            clearTimeout(timer);
            timer = setTimeout(callback, ms);
        };
    })();

    function updateSatCharts() {
        drawSatChart(canvas1, sat_data1);
        drawSatChart(canvas2, sat_data2);
    }

    var sat_data1 = {
        labels: ["January", "February", "March", "April", "May", "June", "July"],
        datasets: [
            {
                label: "My First dataset",
                fillColor: "rgba(0, 255, 0, 0.9)",
                strokeColor: "rgba(220, 220, 220, 0.8)",
                highlightFill: "rgba(220, 220, 220, 0.75)",
                highlightStroke: "rgba(220, 220, 220, 1)",
                data: [65, 59, 80, 81, 56, 55, 40]
            }
        ]
    };

    var sat_data2 = {
        labels: ["January", "February", "March", "April", "May", "June", "July"],
        datasets: [
            {
                label: "My First dataset",
                fillColor: "rgba(255, 0, 0, 0.9)",
                strokeColor: "rgba(220, 220, 220, 0.8)",
                highlightFill: "rgba(220, 220, 220, 0.75)",
                highlightStroke: "rgba(220, 220, 220, 1)",
                data: [65, 59, 80, 81, 56, 55, 40]
            }
        ]
    };

    updateSatCharts();

    //take care of window resize
    $(window).resize(function () {

        var new_height = $(window).height(), new_width = $(window).width();

        if (new_height != current_height) {
            current_height = new_height;
        }

        if (new_width != current_width) {
            current_width = new_width;
            delay(function () {
                //alert('Resize...');
                updateSatCharts();
            }, 500);
        }

    });

});
