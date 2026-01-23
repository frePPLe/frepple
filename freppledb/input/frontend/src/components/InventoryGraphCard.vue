/*
 * Copyright (C) 2025 by frePPLe bv
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

<script setup lang="js">
import { computed, onMounted, onUnmounted, watch, ref, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from "@/stores/operationplansStore.js";
import { numberFormat, debounce, adminEscape } from "@common/utils.js";

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true
});

const store = useOperationplansStore();

const props = defineProps({
  widget: {
    type: Array,
    default: () => []
  }
});

const graphContainer = ref(null);
const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const inventoryReport = computed(() => {
  return store.operationplan?.inventoryreport || [];
});

const hasInventoryReport = computed(() => {
  return inventoryReport.value.length > 0;
});

// Get URL prefix
const urlPrefix = computed(() => window.url_prefix || '');

// Draw the D3 inventory graph
function drawGraph() {
  if (!hasInventoryReport.value || !graphContainer.value || !window.d3) return;
  const d3 = window.d3;
  const timebuckets = inventoryReport.value;

  // Clear existing SVG
  d3.select(graphContainer.value).selectAll('*').remove();

  // Calculate dimensions
  const operationplanCard = document.querySelector('#attributes-operationplan .card-body');
  const margin = { top: 10, right: 10, bottom: 30, left: 40 };
  const width = Math.max((operationplanCard?.offsetWidth || 600) - margin.left - margin.right, 0);
  const height = (operationplanCard?.offsetHeight || 400) - margin.top - margin.bottom;

  // Build X-axis domain
  const domain_x = [];
  let bucketnamelength = 0;
  for (const bucket of timebuckets) {
    domain_x.push(bucket[0]);
    bucketnamelength = Math.max(bucket[0].length, bucketnamelength);
  }

  const x = d3.scale.ordinal()
      .domain(domain_x)
      .rangeRoundBands([0, width], 0);
  const x_width = x.rangeBand();

  // Build data and find min/max
  let max_y = 0;
  let min_y = 0;
  const data = [];

  for (const bctk of timebuckets) {
    data.push({
      bucket: bctk[0],
      startinv: bctk[4],
      safetystock: bctk[5],
      consumed_total: bctk[6],
      consumed_proposed: bctk[7],
      consumed_confirmed: bctk[8],
      produced_total: bctk[9],
      produced_proposed: bctk[10],
      produced_confirmed: bctk[11],
      endinv: bctk[12],
      buffer: store.operationplan?.buffer,
      startdate: bctk[1],
      enddate: bctk[2]
    });

    // Find min and max (skip first 4 elements)
    const slicedbucket = bctk.slice(4);
    const tmp_min = Math.min(...slicedbucket);
    const tmp_max = Math.max(...slicedbucket);
    if (tmp_min < min_y) min_y = tmp_min;
    if (tmp_max > max_y) max_y = tmp_max;
  }

  // Create Y-axis
  const y = d3.scale.linear()
      .domain([min_y, max_y])
      .rangeRound([height, 0]);
  const y_zero = y(0);

  // Create SVG
  const svg = d3.select(graphContainer.value)
      .append('svg')
      .attr('class', 'graphcell')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

  // Draw bars for each bucket
  svg.selectAll('g')
      .data(data)
      .enter()
      .append('g')
      .attr('transform', d => `translate(${x(d.bucket)},0)`)
      .each(function(d) {
        const bucket = d3.select(this);

        // Draw produced bars
        if (d.produced_total > 0) {
          const y_top = y(d.produced_total);
          const y_top_low = y(d.produced_confirmed);

          if (d.produced_confirmed > 0) {
            bucket.append('rect')
                .attr('width', x_width / 2)
                .attr('height', y_zero - y_top_low)
                .attr('x', x_width / 2)
                .attr('y', y_top_low)
                .style('fill', '#113C5E');
          }

          if (d.produced_proposed > 0) {
            bucket.append('rect')
                .attr('width', x_width / 2)
                .attr('height', y_top_low - y_top)
                .attr('x', x_width / 2)
                .attr('y', y_top)
                .style('fill', '#2B95EC');
          }
        }

        // Draw consumed bars
        if (d.consumed_total > 0) {
          const y_top = y(d.consumed_total);
          const y_top_low = y(d.consumed_confirmed);

          if (d.consumed_confirmed > 0) {
            bucket.append('rect')
                .attr('width', x_width / 2)
                .attr('height', y_zero - y_top_low)
                .attr('y', y_top_low)
                .style('fill', '#7B5E08');
          }

          if (d.consumed_proposed > 0) {
            bucket.append('rect')
                .attr('width', x_width / 2)
                .attr('height', y_top_low - y_top)
                .attr('y', y_top)
                .style('fill', '#F6BD0F');
          }
        }

        // Draw background rectangle with gradient for safety stock visualization
        bucket.append('rect')
            .attr('height', height)
            .attr('width', x_width)
            .attr('fill-opacity', d => {
              if (d.startinv >= 0 && (d.startinv >= d.safetystock || d.safetystock === 0)) {
                return 0;
              }
              return 0.2;
            })
            .attr('fill', d => {
              let gradient_idx;
              if (d.startinv < 0) {
                gradient_idx = 0;
              } else if (d.startinv >= d.safetystock || d.safetystock === 0) {
                return null;
              } else {
                gradient_idx = Math.round(d.startinv / d.safetystock * 165);
              }

              // Create gradient if it doesn't exist
              const gradId = `gradient_${gradient_idx}`;
              let grad = d3.select(`#${gradId}`);
              if (grad.empty()) {
                const newgrad = d3.select('#gradients')
                    .append('linearGradient')
                    .attr('id', gradId)
                    .attr('x1', 0)
                    .attr('x2', 0)
                    .attr('y1', 0)
                    .attr('y2', 1);

                newgrad.append('stop')
                    .attr('offset', '0%')
                    .attr('stop-color', 'white')
                    .attr('stop-opacity', 1);
                newgrad.append('stop')
                    .attr('offset', '40%')
                    .attr('stop-color', `rgb(255,${gradient_idx},0)`)
                    .attr('stop-opacity', 1);
                newgrad.append('stop')
                    .attr('offset', '60%')
                    .attr('stop-color', `rgb(255,${gradient_idx},0)`)
                    .attr('stop-opacity', 1);
                newgrad.append('stop')
                    .attr('offset', '100%')
                    .attr('stop-color', 'white')
                    .attr('stop-opacity', 0);
              }
              return `url(#${gradId})`;
            })
            .on('click', d => {
              if (d3.event.defaultPrevented || (d.produced_total === 0 && d.consumed_total === 0)) return;
              d3.select('#tooltip').style('display', 'none');
              window.location = `${urlPrefix.value}/data/input/operationplanmaterial/buffer/${adminEscape(d.buffer)}/?noautofilter&flowdate__gte=${d.startdate}&flowdate__lt=${d.enddate}`;
              d3.event.stopPropagation();
            })
            .on('mouseenter', d => {
              const tiptext = `
            <div style="text-align:center; font-weight:bold">${d.bucket}</div>
            <table>
              <tr><td class="text-capitalize pe-3">${ttt('start inventory')}</td><td class="text-end">${numberFormat(d.startinv)}</td></tr>
              <tr><td class="text-capitalize pe-3">${ttt('produced total')}</td><td class="text-end">+&nbsp;${numberFormat(d.produced_total)}</td></tr>
              <tr><td class="text-capitalize pe-3 px-3">${ttt('produced proposed')}</td><td class="text-end">${numberFormat(d.produced_proposed)}</td></tr>
              <tr><td class="text-capitalize pe-3 px-3">${ttt('produced confirmed')}</td><td class="text-end">${numberFormat(d.produced_confirmed)}</td></tr>
              <tr><td class="text-capitalize pe-3">${ttt('consumed total')}</td><td class="text-end">-&nbsp;${numberFormat(d.consumed_total)}</td></tr>
              <tr><td class="text-capitalize pe-3 px-3">${ttt('consumed proposed')}</td><td class="text-end">${numberFormat(d.consumed_proposed)}</td></tr>
              <tr><td class="text-capitalize pe-3 px-3">${ttt('consumed confirmed')}</td><td class="text-end">${numberFormat(d.consumed_confirmed)}</td></tr>
              <tr><td class="text-capitalize pe-3">${ttt('end inventory')}</td><td class="text-end">=&nbsp;${numberFormat(d.endinv)}</td></tr>
              <tr><td class="text-capitalize pe-3">${ttt('safety stock')}</td><td class="text-end">${numberFormat(d.safetystock)}</td></tr>
            </table>
          `;
              if (window.graph?.showTooltip) {
                window.graph.showTooltip(tiptext);
              }
            })
            .on('mouseleave', () => {
              if (window.graph?.hideTooltip) {
                window.graph.hideTooltip();
              }
            })
            .on('mousemove', () => {
              if (window.graph?.moveTooltip) {
                window.graph.moveTooltip();
              }
            });
      });

  // Draw Y-axis
  const yAxis = d3.svg.axis()
      .scale(y)
      .orient('left')
      .tickFormat(d3.format('s'));
  svg.append('g')
      .attr('class', 'y axis')
      .call(yAxis);

  // Draw zero line if needed
  if (min_y < 0 && max_y > 0) {
    svg.append('line')
        .attr('x1', 0)
        .attr('x2', width)
        .attr('y1', y(0))
        .attr('y2', y(0))
        .attr('stroke-width', 1)
        .attr('stroke', 'black')
        .attr('shape-rendering', 'crispEdges');
  }

  // Draw start inventory line
  const line = d3.svg.line()
      .x(d => x(d.bucket) + x_width / 2)
      .y(d => y(d.startinv));
  svg.append('path')
      .attr('class', 'graphline')
      .attr('stroke', '#8BBA00')
      .attr('d', line(data));

  // Draw safety stock line
  const safetyLine = d3.svg.line()
      .x(d => x(d.bucket) + x_width / 2)
      .y(d => y(d.safetystock));
  svg.append('path')
      .attr('class', 'graphline')
      .attr('stroke', '#FF0000')
      .attr('d', safetyLine(data));

  // Draw X-axis
  const nth = Math.ceil(timebuckets.length / width * bucketnamelength * 10);
  const myticks = [];
  for (let i = 0; i < timebuckets.length; i++) {
    if (i % nth === 0) myticks.push(timebuckets[i][0]);
  }
  const xAxis = d3.svg.axis()
      .scale(x)
      .tickValues(myticks)
      .orient('bottom');
  svg.append('g')
      .attr('class', 'x axis')
      .attr('transform', `translate(0,${height})`)
      .call(xAxis);
}

// Save column configuration on collapse/expand
function onCollapseToggle() {
  if (typeof window.grid !== 'undefined' && window.grid.saveColumnConfiguration) {
    window.grid.saveColumnConfiguration();
  }
}

// Watch for changes and redraw
watch([() => store.operationplan?.id, () => inventoryReport.value.length], async () => {
  if (hasInventoryReport.value) {
    await nextTick();
    drawGraph();
  }
});

onMounted(async () => {
  // Set up Bootstrap collapse listeners
  const collapseElement = document.getElementById('widget_inventorygraph');
  if (collapseElement) {
    collapseElement.addEventListener('shown.bs.collapse', onCollapseToggle);
    collapseElement.addEventListener('hidden.bs.collapse', onCollapseToggle);
  }

  // Draw initial graph
  if (hasInventoryReport.value) {
    await nextTick();
    drawGraph();
  }
});
</script>

<template>
  <div>
    <div
        class="card-header d-flex align-items-center"
        data-bs-toggle="collapse"
        data-bs-target="#widget_inventorygraph"
        aria-expanded="false"
        aria-controls="widget_inventorygraph"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('inventory') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div
        id="widget_inventorygraph"
        class="card-body collapse overflow-hidden"
        :class="{ 'show': !isCollapsed }"
    >
      <table class="table table-sm table-borderless">
        <tbody>
        <tr>
          <td role="gridcell" aria-describedby="grid_graph">
            <div ref="graphContainer" class="graph"></div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.widget-handle {
  cursor: move;
}

.card-header {
  cursor: pointer;
}

.graph {
  min-height: 300px;
}

:deep(.graphline) {
  fill: none;
  stroke-width: 2px;
}

:deep(.axis path),
:deep(.axis line) {
  fill: none;
  stroke: #000;
  shape-rendering: crispEdges;
}

:deep(.axis text) {
  font-family: sans-serif;
  font-size: 11px;
}
</style>
