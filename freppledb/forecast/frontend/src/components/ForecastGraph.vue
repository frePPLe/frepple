
/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

<script setup>
import {ref, watch, onMounted, onUnmounted, nextTick, computed} from 'vue';
import {useForecastsStore} from "@/stores/forecastsStore.js";
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
const store = useForecastsStore();
const graphContainer = ref(null);

// Create a computed property that tracks both buckets and bucketChanges
const graphData = computed(() => {
  const buckets = store.buckets;
  // eslint-disable-next-line
  const changes = store.bucketChanges; // just to make sure changes are caught

  return buckets;
});

const rows = store.tableRows;
const d3 = window.d3;

// Window resize handler
let resizeTimeout = null;
const handleResize = () => {
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    render();
  }, 100);
};

// Get first bucket based on rows configuration
const getFirstBucket = () => {
  if (!graphData.value || graphData.value.length === 0) return null;

  let nyearsago;
  if (rows.includes("orderstotal3ago") || rows.includes("ordersadjustment3ago") ||
    rows.includes("ordersadjustmentvalue3ago") || rows.includes("ordersadjustmentvalue3ago")) {
    // Show all buckets
    return graphData.value[0].bucket;
  } else if (rows.includes("orderstotal2ago") || rows.includes("ordersadjustment2ago") ||
    rows.includes("ordersadjustmentvalue2ago") || rows.includes("ordersadjustmentvalue2ago")) {
    nyearsago = 2;
  } else if (rows.includes("orderstotal1ago") || rows.includes("ordersadjustment1ago") ||
    rows.includes("ordersadjustmentvalue1ago") || rows.includes("ordersadjustmentvalue1ago")) {
    nyearsago = 1;
  } else {
    // Show only future periods - assuming currentbucket is available globally
    return window.currentbucket || graphData.value[0].bucket;
  }

  // First find the index of the current bucket
  let currentfcstbucket = null;
  for (const item of graphData.value) {
    if (item.bucket === (window.currentbucket || graphData.value[0].bucket)) {
      currentfcstbucket = item;
      break;
    }
  }

  if (!currentfcstbucket) return graphData.value[0].bucket;

  const startdate = new Date(currentfcstbucket.startdate);
  const enddate = new Date(currentfcstbucket.enddate);
  // Get the date right in the middle between start and end date and remove 365*nyearsago milliseconds
  const middledate = new Date(-365 * 24 * 3600 * 1000 * nyearsago +
    Math.round(startdate.getTime() + (enddate.getTime() - startdate.getTime()) / 2.0));

  for (const item of graphData.value) {
    const bucketStart = new Date(item.startdate.substring(0, 10));
    const bucketEnd = new Date(item.enddate.substring(0, 10));
    if (middledate >= bucketStart && middledate < bucketEnd) {
      return item.bucket;
    }
  }

  return graphData.value[0].bucket;
};

const formatNumber = (value) => {
  if (window.grid && window.grid.formatNumber) {
    return window.grid.formatNumber(value);
  }
  return value?.toLocaleString() || '';
};

const showTooltip = (content) => {
  if (window.graph && window.graph.showTooltip) {
    window.graph.showTooltip(content);
  }
};

const hideTooltip = () => {
  if (window.graph && window.graph.hideTooltip) {
    window.graph.hideTooltip();
  }
};

const moveTooltip = () => {
  if (window.graph && window.graph.moveTooltip) {
    window.graph.moveTooltip();
  }
};

// Main render function
const render = () => {
  if (!graphData.value || !graphContainer.value || graphData.value.length === 0) return;

  const margin = {
    top: 0,
    right: 130,
    bottom: 30,
    left: 50
  };

  const containerWidth = graphContainer.value.clientWidth;
  const containerHeight = graphContainer.value.clientHeight || 400;
  const width = containerWidth - margin.left - margin.right;
  const height = containerHeight - margin.top - margin.bottom;

  if (width <= 0 || height <= 0) return;

  const firstBucket = getFirstBucket();

  // Define X-axis
  const domainX = [];
  let bucketnamelength = 0;
  let forecastcurrentbucket = 0;
  let showBucket = false;
  const filteredGraphData = [];

  graphData.value.forEach((item, i) => {
    if (!showBucket && item.bucket === firstBucket) {
      forecastcurrentbucket -= parseInt(i);
      showBucket = true;
    }
    if (showBucket) {
      domainX.push(item.bucket);
      bucketnamelength = Math.max(item.bucket.length, bucketnamelength);
      filteredGraphData.push(item);
      if (item.currentbucket) {
        forecastcurrentbucket += parseInt(i);
      }
    }
  });

  if (filteredGraphData.length === 0) return;

  const x = d3.scale.ordinal()
    .domain(domainX)
    .rangeRoundBands([0, width], 0);
  const xWidth = x.rangeBand();

  // Define Y-axis
  const y = d3.scale.linear().rangeRound([height, 0]);

  // Clear existing content
  d3.select(graphContainer.value).selectAll("*").remove();

  const svg = d3.select(graphContainer.value)
    .append("svg")
    .attr("class", "graphcell")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

  // Get the maxima of the values
  let maxY = 0;
  let minY = 0;

  filteredGraphData.forEach(tmp => {
    const ordersTotal = tmp.orderstotal || 0;
    const ordersAdjustment = tmp.ordersadjustment || 0;
    const forecastTotal = tmp.forecasttotal || 0;

    if (ordersTotal + ordersAdjustment > maxY) {
      maxY = ordersTotal + ordersAdjustment;
    }
    if (forecastTotal > maxY) {
      maxY = forecastTotal;
    }
    if (ordersTotal < minY) {
      minY = ordersTotal;
    }
    if (forecastTotal < minY) {
      minY = forecastTotal;
    }
  });

  // Update the scale of the Y-axis by looking for the max value
  y.domain([minY, maxY]);
  const Yzero = y(0);

  svg.selectAll("g")
    .data(filteredGraphData)
    .enter()
    .append("g")
    .attr("transform", d => `translate(${x(d.bucket)},0)`)
    .each(function(d, i) {
      const bucket = d3.select(this);

      // Draw open orders bar
      const ordersOpen = d.ordersopen || 0;
      if (ordersOpen > 0) {
        const myY = y(ordersOpen);
        bucket.append("rect")
          .attr("width", xWidth)
          .attr("height", Yzero - myY)
          .attr("x", xWidth / 2)
          .attr("y", myY)
          .style("fill", "#2B95EC");
      }

      // Draw hovering tooltip
      bucket.append("rect")
        .attr("height", height)
        .attr("width", xWidth)
        .attr("fill-opacity", 0)
        .on("mouseenter", function(d) {
          const tooltipContent = i >= forecastcurrentbucket
            ? `<div style="text-align:center"><strong>${d.bucket}</strong></div>
               <table style="margin: 5px;">
                 <tr><td>${t('total orders')}</td><td style="text-align:right">${formatNumber(d.orderstotal || 0)}</td></tr>
                 <tr><td>${t('open orders')}</td><td style="text-align:right">${formatNumber(d.ordersopen || 0)}</td></tr>
                 <tr><td>${t('orders adjustment')}</td><td style="text-align:right">${(d.ordersadjustment === null || d.ordersadjustment === undefined) ? '' : formatNumber(d.ordersadjustment)}</td></tr>
                 <tr><td>${t('forecast baseline')}</td><td style="text-align:right">${formatNumber(d.forecastbaseline || 0)}</td></tr>
                 <tr><td>${t('forecast override')}</td><td style="text-align:right">${(!Object.prototype.hasOwnProperty.call(d, "forecastoverride") || d.forecastoverride === null || d.forecastoverride === undefined) ? '' : formatNumber(d.forecastoverride)}</td></tr>
                 <tr><td>${t('forecast total')}</td><td style="text-align:right">${formatNumber(d.forecasttotal || 0)}</td></tr>
                 <tr><td>${t('forecast net')}</td><td style="text-align:right">${formatNumber(d.forecastnet || 0)}</td></tr>
                 <tr><td>${t('forecast consumed')}</td><td style="text-align:right">${formatNumber(d.forecastconsumed || 0)}</td></tr>
               </table>`
            : `<div style="text-align:center"><strong>${d.bucket}</strong></div>
               <table style="margin: 5px;">
                 <tr><td>${t('total orders')}</td><td style="text-align:right">${formatNumber(d.orderstotal || 0)}</td></tr>
                 <tr><td>${t('open orders')}</td><td style="text-align:right">${formatNumber(d.ordersopen || 0)}</td></tr>
                 <tr><td>${t('orders adjustment')}</td><td style="text-align:right">${(d.ordersadjustment === null || d.ordersadjustment === undefined) ? '' : formatNumber(d.ordersadjustment)}</td></tr>
                 <tr><td>${t('past forecast')}</td><td style="text-align:right">${formatNumber(d.forecastbaseline || 0)}</td></tr>
               </table>`;

          showTooltip(tooltipContent);
        })
        .on("mouseleave", hideTooltip)
        .on("mousemove", moveTooltip);
    });

  // Create D3 lines - orders
  let line = d3.svg.line()
    .x(d => x(d.bucket) + xWidth / 2)
    .y(d => y(Math.max(0, (d.orderstotal || 0) + (d.ordersadjustment || 0))));

  svg.append("svg:path")
    .attr('class', 'graphline')
    .attr("stroke", "#8BBA00")
    .attr("d", line(filteredGraphData));

  // Create D3 lines - total forecast
  line = d3.svg.line()
    .x(d => x(d.bucket) + xWidth / 2)
    .y((d, i) => y((i >= forecastcurrentbucket) ? (d.forecasttotal || 0) : 0));

  svg.append("svg:path")
    .attr('class', 'graphline')
    .attr("stroke", "#FF0000")
    .attr("d", line(filteredGraphData));

  // Create D3 lines - past forecast
  line = d3.svg.line()
    .x(d => x(d.bucket) + xWidth / 2)
    .y((d, i) => y((i < forecastcurrentbucket) ? (d.forecasttotal || 0) : 0));

  svg.append("svg:path")
    .attr('class', 'graphline')
    .attr("stroke", "#FF7B00")
    .attr("d", line(filteredGraphData));

  // Display Y-Axis
  const yAxis = d3.svg.axis()
    .scale(y)
    .orient("left")
    .tickFormat(d3.format("s"));

  svg.append("g")
    .attr("class", "y axis")
    .call(yAxis);

  // Display X-axis for a single forecast
  const nth = Math.ceil(filteredGraphData.length / width * bucketnamelength * 10);
  const myticks = [];

  filteredGraphData.forEach((item, i) => {
    if (i % nth === 0) {
      myticks.push(item.bucket);
    }
  });

  const xAxis = d3.svg.axis()
    .scale(x)
    .tickValues(myticks)
    .orient("bottom");

  svg.append("g")
    .attr("class", "x axis")
    .attr("transform", `translate(0,${height})`)
    .call(xAxis);

  // Display legend
  const legend = svg.append("g");
  const codes = [
    [t("open orders"), "#2B95EC", 1],
    [t("total orders"), "#8BBA00", 0],
    [t("forecast total"), "#FF0000", 5],
    [t("past forecast"), "#FF7B00", 6]
  ];

  let visible = 0;
  codes.forEach((code) => {
    legend.append("rect")
      .attr("x", width + 82)
      .attr("width", 18)
      .attr("height", 18)
      .style("fill", code[1])
      .attr("transform", `translate(0,${visible * 20 + 10})`);

    legend.append("text")
      .attr("x", width + 76)
      .attr("y", 9)
      .attr("dy", ".35em")
      .style("text-anchor", "end")
      .text(code[0])
      .attr("transform", `translate(0,${visible * 20 + 10})`);

    visible += 1;
  });
};

// Watch for data changes from store.buckets and store.bucketChanges
watch(graphData, () => {
  nextTick(() => {
    render();
  });
}, { deep: true });

// watch(() => store.hasChanges, () => {
//   nextTick(() => {
//     render();
//   });
// });

// Watch for window resize
onMounted(() => {
  window.addEventListener('resize', handleResize);
  nextTick(() => {
    render();
  });
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  if (resizeTimeout) {
    clearTimeout(resizeTimeout);
  }
});
</script>

<template>
  <div id="forecastgraph" ref="graphContainer" class="forecast-graph-container"></div>
</template>

