function maxStrLen(data) {
    var max = 0;
    for(var i=0; i<data.length; i++) {
        if(data[i].name.length > max) {
            max = data[i].name.length;
        }
        if(data[i].origValue.length > max) {
            max = data[i].origValue.length;
        }
    }
    return max;
}

function calculateBarWidth(data) {
    var w = 0;
    w = maxStrLen(data);
    w = w * 10;
    return w;
    //return maxStrLen(data)*10;
}

function calculateBarGraphWidth(data) {
    return (calculateBarWidth(data) + 10) * data.length;
}

function barGraph2(data) {
    var barWidth = calculateBarWidth(data);
    var width = (barWidth + 10) * data.length;
    var height = 200;

    var x = d3.scale.linear().domain([0, data.length]).range([0, width]);
    //var y = d3.scale.linear().domain([d3.min(data, function(datum) {return datum.value;}), d3.max(data, function(datum) { return datum.value;})]).rangeRound([0, height]);

    var y;

    var minValue = d3.min(data, function(datum) { return datum.value; });
    if (data.length == 1) {
        minValue = 0;
    }

    y = d3.scale.linear().domain([minValue, d3.max(data, function(datum) { return datum.value;})]).rangeRound([0, height]);

    // add the canvas to the DOM
    var barDemo = d3.select(".chart").
        attr("width", width).
        attr("height", height+100);

    barDemo.selectAll("rect").
        data(data).
        enter().
        append("rect").
        attr("x", function(datum, index) { return x(index); }).
        attr("y", function(datum) {
            if(datum.value >= 0.0) {
                return height - y(datum.value);
            } else {
                return height - y(0.0);
            }
        }).
        attr("height", function(datum) {
            if(datum.value >= 0.0) {
                if(minValue < 0)  {
                    return y(datum.value) - y(0.0);
                } else {
                    return y(datum.value) - y(minValue);
                }
            } else {
                return y(0.0) - y(datum.value);
            }
        }).
        attr("width", barWidth).
        attr("fill", "#2d578b");

    barDemo.selectAll("text").
        data(data).
        enter().
        append("text").
        attr("x", function(datum, index) { return x(index) + barWidth; }).
        attr("y", function(datum) { return height - y(datum.value); }).
        attr("dx", -barWidth/2).
        attr("dy", "1.2em").
        attr("text-anchor", "middle").
        text(function(datum) { return datum.origValue;}).
        attr("fill", "black");

    barDemo.selectAll("text.yAxis").
        data(data).
        enter().append("text").
        attr("x", function(datum, index) { return x(index) + barWidth; }).
        attr("y", height).
        attr("dx", -barWidth/2).
        attr("text-anchor", "middle").
        attr("style", "font-size: 12; font-family: Helvetica, sans-serif").
        text(function(datum) { return datum.name;}).
        attr("transform", "translate(0, 36)").
        attr("class", "yAxis").
        attr("fill", "black");
}

function lineGraph(data) {
    var margin = { top: 20, right: 30, bottom: 30, left: 40};
    var width = window.innerWidth - margin.left - margin.bottom;
    var height = 300 - margin.top - margin.bottom;

    var x = d3.scale.linear().domain([0, data.length]).range([0, width]);
    var yMin = d3.min(data, function(datum) {return datum.value;});
    var yMax = d3.max(data, function(datum) {return datum.value;});
    console.log("yMin: "+yMin);
    console.log("yMax: "+yMax);
    var y = d3.scale.linear().domain([yMin, yMax]).range([height, 0]);

    var xAxis = d3.svg.axis().
        scale(x).
        orient("bottom");

    var yAxis = d3.svg.axis().
        scale(y).
        orient("left");

    var line = d3.svg.line().
        x(function(d, i) { return x(i); }).
        y(function(d) { return y(d.value)});

    var lineGraph = d3.select(".chart").
        attr("width", width + margin.left + margin.right).
        attr("height", height + margin.top + margin.bottom).
        append("g").
        attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    lineGraph.append("g").
        attr("class", "x axis").
        attr("transform", "translate(0," + height + ")").
        call(xAxis);

    lineGraph.append("g").
        attr("class", "y axis").
        call(yAxis);

    /*
    lineGraph.selectAll("circle").
        data(data).
        enter().
        append("circle").
        attr("cx", function(datum, index) { return x(index); }).
        attr("cy", function(datum) { return height - y(datum.value); }).
        attr("r", 2.5).
        attr("fill", "#2d578b");
    */
    lineGraph.append("path").
        attr("d", line(data)).
        attr("stroke", "blue").
        attr("stroke-width", 2).
        attr("fill", "none");
}
