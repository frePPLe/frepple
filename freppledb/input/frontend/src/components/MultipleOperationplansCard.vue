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
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@input/stores/operationplansStore.js';
import { adminEscape, dateTimeFormat } from '@common/utils.js';

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const store = useOperationplansStore();

const props = defineProps({
  widget: {
    type: Array,
    default: () => [],
  },
});

const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const handleToggle = () => {
  if (props.widget?.[0]) {
    document.getElementById('app').dispatchEvent(
      new CustomEvent('widget-toggle', { detail: { widget: props.widget[0], state: !isCollapsed.value } })
    );
  }
};

const selectData = computed(() => store.multipleGanttSelectData);

const entityType = computed(() => selectData.value?.entityType || null);

const isResource = computed(() => entityType.value === 'resource');
const isBuffer = computed(() => entityType.value === 'buffer');
const isDemand = computed(() => entityType.value === 'demand');

const rows = computed(() => {
  if (!selectData.value) return [];
  if (isResource.value) return selectData.value.operationplans || [];
  if (isBuffer.value) return selectData.value.flowplans || [];
  if (isDemand.value) return selectData.value.pegging || [];
  return [];
});

const hasRows = computed(() => rows.value.length > 0);

function getRef(row) {
  if (isResource.value) return row.reference;
  if (isBuffer.value) return row.operationplan?.reference;
  if (isDemand.value) return row.operationplan?.reference;
  return '';
}

function getOperation(row) {
  if (isResource.value) return row.operation?.name;
  if (isBuffer.value) return row.operationplan?.operation?.name;
  if (isDemand.value) return row.operationplan?.operation?.name;
  return '';
}

function getQuantity(row) {
  return row.quantity;
}

function getOnhand(row) {
  if (isBuffer.value) return row.onhand;
  return '';
}

function getStartDate(row) {
  if (isResource.value) return dateTimeFormat(row.start);
  if (isDemand.value) return dateTimeFormat(row.operationplan?.start);
  return '';
}

function getEndDate(row) {
  if (isResource.value) return dateTimeFormat(row.end);
  if (isDemand.value) return dateTimeFormat(row.operationplan?.end);
  return '';
}

function getDate(row) {
  if (isBuffer.value) return row.date;
  return '';
}

const urlPrefix = window.url_prefix || '';

function getDetailUrl(row) {
  const ref = getRef(row);
  if (!ref) return '';
  let ordertype;
  if (isResource.value) ordertype = row.ordertype;
  else if (isBuffer.value) ordertype = row.operationplan?.ordertype;
  else if (isDemand.value) ordertype = row.operationplan?.ordertype;
  if (ordertype === 'STCK') return '';
  const path = ({
    PO: 'purchaseorder',
    DO: 'distributionorder',
    WO: 'workorder',
  })[ordertype] || 'manufacturingorder';
  return `${urlPrefix}/detail/input/${path}/${adminEscape(ref)}/`;
}

function getOperationUrl(row) {
  const op = getOperation(row);
  if (!op) return '';
  return `${urlPrefix}/detail/input/operation/${adminEscape(op)}/`;
}
</script>

<template>
  <div v-if="selectData">
    <div
      class="card-header d-flex align-items-center"
      @click="handleToggle"
      data-bs-toggle="collapse"
      data-bs-target="#widget_multiple_gantt"
      aria-expanded="false"
      aria-controls="widget_multiple_gantt"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('operationplans') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div
      id="widget_multiple_gantt"
      class="card-body collapse"
      :class="{ show: !isCollapsed }"
    >
      <div class="table-responsive">
        <table class="table table-hover table-sm table-borderless">
          <thead>
            <tr>
              <th><b class="text-capitalize">{{ ttt('reference') }}</b></th>
              <th><b class="text-capitalize">{{ ttt('operation') }}</b></th>
              <th><b class="text-capitalize">{{ ttt('quantity') }}</b></th>
              <th v-if="isBuffer">
                <b class="text-capitalize">{{ ttt('onhand') }}</b>
              </th>
              <th v-if="isBuffer">
                <b class="text-capitalize">{{ ttt('date') }}</b>
              </th>
              <th v-if="!isBuffer">
                <b class="text-capitalize">{{ ttt('start') }}</b>
              </th>
              <th v-if="!isBuffer">
                <b class="text-capitalize">{{ ttt('end') }}</b>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!hasRows">
              <td :colspan="isBuffer ? 5 : 5">
                {{ ttt('no operations planned') }}
              </td>
            </tr>
            <tr v-for="(row, index) in rows" :key="index">
              <td>
                {{ getRef(row) }}
                <a v-if="getDetailUrl(row)" :href="getDetailUrl(row)">
                  <span class="fa fa-caret-right"></span>
                </a>
              </td>
              <td>
                {{ getOperation(row) }}
                <a v-if="getOperationUrl(row)" :href="getOperationUrl(row)">
                  <span class="fa fa-caret-right"></span>
                </a>
              </td>
              <td>{{ getQuantity(row) }}</td>
              <td v-if="isBuffer">{{ getOnhand(row) }}</td>
              <td v-if="isBuffer">{{ getDate(row) }}</td>
              <td v-if="!isBuffer">{{ getStartDate(row) }}</td>
              <td v-if="!isBuffer">{{ getEndDate(row) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
