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
import { numberFormat, dateTimeFormat, adminEscape } from "@common/utils.js";

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

const peggingDemand = computed(() => {
  return store.operationplan?.pegging_demand || [];
});

const hasPeggingDemand = computed(() => {
  return peggingDemand.value.length > 0;
});

// Get URL prefix
const urlPrefix = computed(() => window.url_prefix || '');

// Save column configuration on collapse/expand
function onCollapseToggle() {
  if (typeof window.grid !== 'undefined' && window.grid.saveColumnConfiguration) {
    window.grid.saveColumnConfiguration();
  }
}

onMounted(() => {
  // Set up Bootstrap collapse listeners
  const collapseElement = document.getElementById('widget_demandpegging');
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
        data-bs-target="#widget_demandpegging"
        aria-expanded="false"
        aria-controls="widget_demandpegging"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('demand') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div
        id="widget_demandpegging"
        class="card-body collapse"
        :class="{ 'show': !isCollapsed }"
        style="max-height: 15em; overflow: auto"
    >
      <div v-if="!hasPeggingDemand">
        {{ ttt('There is no demand requiring this supply.') }}
      </div>

      <div v-else class="table-responsive">
        <table class="table table-sm table-hover table-borderless">
          <thead>
          <tr>
            <td><b class="text-capitalize">{{ ttt('name') }}</b></td>
            <td><b class="text-capitalize">{{ ttt('item') }}</b></td>
            <td><b class="text-capitalize">{{ ttt('due') }}</b></td>
            <td><b class="text-capitalize">{{ ttt('quantity') }}</b></td>
          </tr>
          </thead>
          <tbody>
          <tr v-for="(demand, index) in peggingDemand" :key="index">
            <!-- Demand name column -->
            <td>
              {{ demand.demand?.name }}
              <a
                  :href="`${urlPrefix}${demand.demand?.forecast ? '/detail/forecast/forecast/' : '/detail/input/demand/'}${adminEscape(demand.demand?.name)}/`"
                  @click.stop
              >
                <span class=" fa fa-caret-right"></span>
              </a>
            </td>

            <!-- Item column -->
            <td>
              <span
                  v-if="demand.demand?.item?.description"
                  :title="demand.demand.item.description"
                  data-bs-toggle="tooltip"
              >
                {{ demand.demand.item.name }}
              </span>
              <span v-else style="padding-right: 3px">{{ demand.demand?.item?.name }}</span>
              <a
                  :href="`${urlPrefix}/detail/input/item/${adminEscape(demand.demand?.item?.name)}/`"
                  @click.stop
              >
                <span class=" fa fa-caret-right"></span>
              </a>
            </td>

            <!-- Due date column -->
            <td>{{ dateTimeFormat(demand.demand?.due) }}</td>

            <!-- Quantity column -->
            <td>{{ numberFormat(demand.quantity) }}</td>
          </tr>
          </tbody>
        </table>
      </div>
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

thead tr td {
  border-bottom-width: 1px;
  border-bottom-style: solid;
  border-bottom-color: #bbb;
}
</style>
