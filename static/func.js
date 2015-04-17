function drawSatChart(canvas, sat_data) {
    canvas.css("width", "99%");
    canvas.css("margin", "1%");
    var ctx = canvas.get(0).getContext("2d");
    ctx.canvas.width = window.innerWidth;
    ctx.canvas.height = 0.5 * window.innerWidth;

    // define best width between bars
    var w = ctx.canvas.width;
    if (w > 1000) {
        w = 5;
    } else {
        w = 2;
    }

    new Chart(ctx).Bar(sat_data, {
        responsive: true,
        barDatasetSpacing: -1,
        barValueSpacing: w
    });
}

