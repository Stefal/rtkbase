$(document).ready(function () {

    $("#mode_value").append("mode value");
    $("#fix_value").append("3-D");
    $("#lon_value").append("60");
    $("#lat_value").append("30");
    $("#height_value").append("20");

    var canvas1 = $("#sat_chart1_canvas");
    var canvas2 = $("#sat_chart2_canvas");

    var sat_data1 = {
        labels: ["January", "February", "March", "April", "May", "June", "July", "August"],
        datasets: [
            {
                label: "My First dataset",
                fillColor: "rgba(0, 255, 0, 0.9)",
                strokeColor: "rgba(220, 220, 220, 0.8)",
                highlightFill: "rgba(220, 220, 220, 0.75)",
                highlightStroke: "rgba(220, 220, 220, 1)",
                data: [65, 59, 80, 81, 56, 55, 40, 31]
            },
            {
                label: "My Second dataset",
                fillColor: "rgba(151, 187, 205, 0.9)",
                strokeColor: "rgba(151, 187, 205, 0.8)",
                highlightFill: "rgba(151, 187, 205, 0.75)",
                highlightStroke: "rgba(151, 187, 205, 1)",
                data: [28, 48, 40, 19, 86, 27, 90, 31]
            }
        ]
    };

    var sat_data2 = {
        labels: ["January", "February", "March", "April", "May", "June", "July", "August"],
        datasets: [
            {
                label: "My First dataset",
                fillColor: "rgba(255, 0, 0, 0.9)",
                strokeColor: "rgba(220, 220, 220, 0.8)",
                highlightFill: "rgba(220, 220, 220, 0.75)",
                highlightStroke: "rgba(220, 220, 220, 1)",
                data: [65, 59, 80, 81, 56, 55, 40, 31]
            }
        ]
    };

    createSatCharts(canvas1, sat_data1, canvas2, sat_data2);

});
