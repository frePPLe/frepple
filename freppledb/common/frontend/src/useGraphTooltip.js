/*
 * Copyright (C) 2026 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

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
