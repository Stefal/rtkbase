$(document).ready(function () {

    $("#mode_value").append("mode value");
    $("#fix_value").append("3-D");
    $("#lon_value").append("60");
    $("#lat_value").append("30");
    $("#height_value").append("20");

    var sat_data = {
        labels: ["January", "February", "March", "April", "May", "June", "July"],
        datasets: [
            {
                label: "My First dataset",
                fillColor: "rgba(220,220,220,0.5)",
                strokeColor: "rgba(220,220,220,0.8)",
                highlightFill: "rgba(220,220,220,0.75)",
                highlightStroke: "rgba(220,220,220,1)",
                data: [65, 59, 80, 81, 56, 55, 40]
            }
        ]
    };

    function drawSatChart(sd) {
        var ctx = $("#sat_chart").get(0).getContext("2d");
        ctx.canvas.width = window.innerWidth;
        ctx.canvas.height = window.innerHeight;
        var sat_bar_chart = new Chart(ctx).Bar(sd);
    }

    drawSatChart(sat_data);


    // take care of window resize
    $(window).resize(function () {
        drawSatChart(sat_data);
    });

});
