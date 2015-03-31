function drawSatChart(canvas, sat_data) {
    canvas.css("width", "99%");
    canvas.css("margin", "1%");
    var ctx = canvas.get(0).getContext("2d");
    ctx.canvas.width = window.innerWidth;
    ctx.canvas.height = 0.5 * window.innerWidth;
    new Chart(ctx).Bar(sat_data, {
        responsive: true,
        barDatasetSpacing: -1
    });
}

function createSatCharts(canvas1, sat_data1, canvas2, sat_data2) {
    drawSatChart(canvas1, sat_data1);
    drawSatChart(canvas2, sat_data2);
}
