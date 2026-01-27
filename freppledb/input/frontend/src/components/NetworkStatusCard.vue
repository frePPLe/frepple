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
import { computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from "@/stores/operationplansStore.js";
import {numberFormat, adminEscape} from "@common/utils.js";

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

const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const networkData = computed(() => {
  return store.operationplan?.network || [];
});

const hasNetworkData = computed(() => {
  return networkData.value.length > 0;
});

// Get URL prefix
const urlPrefix = computed(() => window.url_prefix || '');

// Build filter URLs for different order types
function buildBufferUrl(item, location) {
  return `${urlPrefix.value}/data/input/operationplanmaterial/buffer/${adminEscape(item + ' @ ' + location)}/`;
}

function buildPurchaseOrderUrl(item, location) {
  return `${buildBufferUrl(item, location)}?noautofilter&operationplan__status__in=approved,confirmed&operationplan__type=PO&quantity__gt=0`;
}

function buildDistributionOrderUrl(item, location) {
  return `${buildBufferUrl(item, location)}?noautofilter&operationplan__status__in=approved,confirmed&operationplan__type=DO`;
}

function buildManufacturingOrderUrl(item, location) {
  return `${buildBufferUrl(item, location)}?noautofilter&operationplan__status__in=approved,confirmed&operationplan__type=MO&quantity__gt=0`;
}

function buildOverdueSalesOrderUrl(item, location, dueDate) {
  return `${urlPrefix.value}/data/input/demand/?noautofilter&status__in=open,quote&item=${adminEscape(item)}&location=${adminEscape(location)}&due__lt=${adminEscape(dueDate)}`;
}

function buildSalesOrderUrl(item, location, dueDate) {
  return `${urlPrefix.value}/data/input/demand/?noautofilter&status__in=open,quote&item=${adminEscape(item)}&location=${adminEscape(location)}&due__gte=${adminEscape(dueDate)}`;
}

// Table headers
const headers = [
  'item',
  'location',
  'onhand',
  'purchase orders',
  'distribution orders',
  'manufacturing orders',
  'overdue sales orders',
  'sales orders'
];

// Save column configuration on collapse/expand
function onCollapseToggle() {
  if (typeof window.grid !== 'undefined' && window.grid.saveColumnConfiguration) {
    window.grid.saveColumnConfiguration();
  }
}

onMounted(() => {
  // Set up Bootstrap collapse listeners
  const collapseElement = document.getElementById('widget_networkstatus');
  if (collapseElement) {
    collapseElement.addEventListener('shown.bs.collapse', onCollapseToggle);
    collapseElement.addEventListener('hidden.bs.collapse', onCollapseToggle);
  }
});
</script>

<template>
  <div>
    <div
        class="card-header d-flex align-items-center"
        data-bs-toggle="collapse"
        data-bs-target="#widget_networkstatus"
        aria-expanded="false"
        aria-controls="widget_networkstatus"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('network status') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div
        id="widget_networkstatus"
        class="card-body collapse"
        :class="{ 'show': !isCollapsed }"
    >
      <table class="table table-sm table-hover table-borderless">
        <thead>
        <tr>
          <td v-for="header in headers" :key="header">
            <b class="text-capitalize">{{ ttt(header) }}</b>
          </td>
        </tr>
        </thead>
        <tbody>
        <tr v-if="!hasNetworkData">
          <td colspan="8">{{ ttt('no network information') }}</td>
        </tr>

        <tr v-for="(network, index) in networkData" :key="index">
          <!-- Item column -->
          <td>
            {{ network[0] }}
            <a
                :href="`${urlPrefix}/detail/input/item/${adminEscape(network[0])}/`"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
            <small v-if="network[1] === true">{{ ttt('superseded') }}</small>
          </td>

          <!-- Location column -->
          <td>
            {{ network[2] }}
            <a
                :href="`${urlPrefix}/detail/input/location/${adminEscape(network[2])}/`"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
          </td>

          <!-- Onhand column -->
          <td>{{ numberFormat(network[3]) }}</td>

          <!-- Purchase orders column -->
          <td>
            {{ numberFormat(network[4]) }}
            <a
                v-if="network[4] > 0"
                :href="buildPurchaseOrderUrl(network[0], network[2])"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
          </td>

          <!-- Distribution orders column -->
          <td>
            {{ numberFormat(network[5]) }}
            <a
                v-if="network[5] != 0"
                :href="buildDistributionOrderUrl(network[0], network[2])"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
          </td>

          <!-- Manufacturing orders column -->
          <td>
            {{ numberFormat(network[6]) }}
            <a
                v-if="network[6] > 0"
                :href="buildManufacturingOrderUrl(network[0], network[2])"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
          </td>

          <!-- Overdue sales orders column -->
          <td>
            {{ numberFormat(network[7]) }}
            <a
                v-if="network[7] > 0"
                :href="buildOverdueSalesOrderUrl(network[0], network[2], network[9])"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
          </td>

          <!-- Sales orders column -->
          <td>
            {{ numberFormat(network[8]) }}
            <a
                v-if="network[8] > 0"
                :href="buildSalesOrderUrl(network[0], network[2], network[9])"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
