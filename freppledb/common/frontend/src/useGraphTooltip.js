export function useGraphTooltip() {
  function showTooltip(txt) {
    var tt = window.d3.select("#tooltip");
    if (tt.empty())
      tt = window.d3.select("body")
        .append("div")
        .attr("id", "tooltip")
        .attr("role", "tooltip")
        .attr("class", "card p-2")
        .style("position", "absolute");
    tt.html('' + txt).style('display', 'block');
    moveTooltip();
  }

  function hideTooltip() {
    window.d3.select("#tooltip").style('display', 'none');
    if (window.d3.event) window.d3.event.stopPropagation();
  }

  function moveTooltip() {
    var xpos = window.d3.event.pageX + 5;
    var ypos = window.d3.event.pageY - 28;
    var xlimit = $(window).width() - $("#tooltip").width() - 20;
    var ylimit = $(window).height() - $("#tooltip").height() - 20;
    if (xpos > xlimit) {
      xpos = xlimit;
      ypos = window.d3.event.pageY + 5;
    }
    if (ypos > ylimit)
      ypos = window.d3.event.pageY - $("#tooltip").height() - 25;
    window.d3.select("#tooltip")
      .style('left', xpos + "px")
      .style('top', ypos + "px");
    if (window.d3.event) window.d3.event.stopPropagation();
  }

  return { showTooltip, hideTooltip, moveTooltip };
}
