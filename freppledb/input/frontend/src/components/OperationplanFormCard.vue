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
import { computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@input/stores/operationplansStore.js';
import { numberFormat, debouncedInputHandler, dateTimeFormat } from '@common/utils.js';
import { useBootstrapTooltips } from '@common/useBootstrapTooltips.js';
import { useOperationplanEdit } from '@input/composables/useOperationplanEdit.js';
import { appConfig } from '@input/config.js';
import { api } from '@input/services/api.js';

const { initTooltips } = useBootstrapTooltips();

const { t: ttt } = useI18n({
  useScope: 'global', // This is crucial for reactivity
  inheritLocale: true,
});

const store = useOperationplansStore();
const edit = useOperationplanEdit(store);
const exporting = computed(() => store.exporting);

const props = defineProps({
  widget: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(['opplan-form-changed', 'widget-toggle']);

const isCollapsed = computed(() => {
  if (store.operationplan?.reference || store.operationplan?.operationplan__reference) return false;
  return props.widget[1]?.collapsed ?? false;
});

const handleToggle = () => {
  if (props.widget?.[0] && !store.operationplan?.reference && !store.operationplan?.operationplan__reference) {
    document.getElementById('app').dispatchEvent(
      new CustomEvent('widget-toggle', { detail: { widget: props.widget[0], state: !isCollapsed.value } })
    );
  }
};

const opPlanHasOwnProperty = (key) => {
  return Object.prototype.hasOwnProperty.call(store.operationplan, key);
};

const filteredColmodel = computed(() => {
  if (window.debug) console.log('filteredColmodel:', store.operationplan.colmodel);
  if (!store.operationplan || !store.operationplan.colmodel) {
    return [];
  }

  const excludedKeys = [
    'delay',
    'criticality',
    'quantity',
    'startdate',
    'enddate',
    'start',
    'end',
    'setupend',
    'color',
    'quantity_completed',
    'operationplan__delay',
    'operationplan__criticality',
    'operationplan__quantity',
    'operationplan__startdate',
    'operationplan__enddate',
    'operationplan__color',
    'operationplan__quantity_completed',
  ];

  return Object.entries(store.operationplan.colmodel || {})
    .filter(
      ([key]) =>
        !excludedKeys.includes(key) &&
        Object.prototype.hasOwnProperty.call(store.operationplan, key) &&
        store.operationplan[key] != null
    )
    .sort()
    .reverse();
});

const editable = window.editable || false;

const actions = window.actions || {};

function dispatchERPExport() {
  const app = document.getElementById('app');
  if (app) {
    app.dispatchEvent(new CustomEvent('triggerERPExport'));
  }
}

async function addOperationPlan() {
  try {
    const ref = store.operationplan.reference || store.operationplan.operationplan__reference;
    if (!ref) return;
    await api.wspost('operationplan/', {
      "propagateFwd":true,
      "resolveConstraints": 1,
      "operationplans": [{ copy: [ref] }]
    });
    emit('opplan-form-changed', [ref]);
  } catch (err) {
    console.error('Duplicate failed:', err);
  }
}

async function removeOperationPlan() {
  try {
    const ref = store.operationplan.reference || store.operationplan.operationplan__reference;
    if (!ref) return;
    await api.wspost('operationplan/', [{ delete: [ref] }]);
    store.undo();
    emit('opplan-form-changed', [ref]);
  } catch (err) {
    console.error('Remove failed:', err);
  }
}

async function splitOperationPlan() {
  try {
    const ref = store.operationplan.reference || store.operationplan.operationplan__reference;
    if (!ref) return;
    // Post to the engine
    await api.wspost('operationplan/',  {
      "propagateFwd":true,
      "resolveConstraints": 1,
      "operationplans": [{ split: [ref] }]}
    );
    // Trigger refresh of the gantt chart (or any other component that listens to this event)
    emit('opplan-form-changed', [ref]);
    // Reload the bottom panels
    document.getElementById('app').dispatchEvent(
      new CustomEvent('singleSelect', {
        detail: {
          execute: 'displayInfo',
          reference: ref,
          selectedRows: [ref]
        },
      })
    );
  } catch (err) {
    console.error('Split failed:', err);
  }
}

const opptype = {
  MO: ttt('manufacturing order'),
  WO: ttt('work order'),
  PO: ttt('purchase order'),
  DO: ttt('distribution order'),
  STCK: ttt('stock'),
  DLVR: ttt('delivery'),
};

const isMultipleOrNone = computed(() => store.selectedOperationplans.length !== 1);

watch(isMultipleOrNone, () => requestAnimationFrame(initTooltips));

const statusIcons = {
  proposed: 'fa fa-unlock',
  approved: 'fa fa-unlock-alt',
  confirmed: 'fa fa-lock',
  completed: 'fa fa-check',
  closed: 'fa fa-times',
};

const statusList = ['proposed', 'approved', 'confirmed', 'completed', 'closed'];

const statusCounts = computed(() => store.selectedStatusCounts);

const selectedCount = computed(() => store.selectedOperationplans.length);

const hasProposed = computed(() => !!store.selectedStatusCounts['proposed']);

const setEditValueDebounced = debouncedInputHandler(async (field, value) => {
  if (value === '') return;
  try {
    await edit.setEditFormValues(field, value);
  } catch (err) {
    console.error('Edit form save failed:', err);
  }
  emit('opplan-form-changed');
}, 300);

function setEditValue(field, value) {
  setEditValueDebounced(field, value);
}

async function handleSetStatus(status) {
  try {
    const saved = await edit.setStatus(status);
    if (saved) emit('opplan-form-changed');
  } catch (err) {
    console.error('Batch status change failed:', err);
  }
}

async function handleShiftGroupDates(field, value) {
  try {
    const saved = await edit.shiftGroupDates(field, value);
    if (saved) emit('opplan-form-changed');
  } catch (err) {
    console.error('Batch date shift failed:', err);
  }
}

const formatDuration = window.formatDuration;

const urlPrefix = computed(() => window.url_prefix || '');

function buildPrefixedUrl(url, reference = null) {
  if (reference === null || reference === undefined || reference === '') {
    return `${urlPrefix.value}${url}`;
  }
  const encodedReference = encodeURIComponent(reference);
  const suffix = url.endsWith('/') && !url.includes('?') ? '/' : '';
  return `${urlPrefix.value}${url}${encodedReference}${suffix}`;
}
</script>

<template>
  <div class="card">
    <div
      class="card-header d-flex align-items-center"
      @click="handleToggle"
      data-bs-toggle="collapse"
      data-bs-target="#widget_operationplanpanel"
      aria-expanded="false"
      aria-controls="widget_operationplanpanel"
    >
      <h5 class="card-title text-capitalize me-auto">
        <span v-if="isMultipleOrNone" class="">
          {{ ttt('selected') }}&nbsp;{{ store.selectedOperationplans.length }}
        </span>
        <span v-if="store.operationplan.type && !isMultipleOrNone" class="pl3 text-capitalize">
          {{ opptype[store.operationplan.type] }}
        </span>
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>
    <div
      v-if="store.operationplan?.quantity !== undefined"
      class="card-body collapse"
      :class="{ show: !isCollapsed }"
      id="widget_operationplanpanel"
      @show="store.operationplan.reference || store.operationplan.operationplan__reference"
    >
      <table
        style="table-layout: fixed"
        class="table table-sm table-hover table-borderless"
        id="opplan-attributes-drvtable"
      >
        <tbody>
          <tr v-if="store.operationplan.operation?.name || store.operationplan.name">
            <th style="width: 120px">
              <b id="thead1" class="text-capitalize">{{ ttt('name') }}&nbsp;</b>
            </th>
            <th>
              <b class="text-capitalize" v-if="opPlanHasOwnProperty('operation')">
                {{ store.operationplan.operation.name }}
                <a
                  :href="buildPrefixedUrl('/detail/input/operation/', store.operationplan.operation?.name)"
                  data-entity="input/operation"
                  @click.stop
                >
                  <span class="fa fa-caret-right"></span>
                </a>
              </b>
              <b class="text-capitalize" v-if="!opPlanHasOwnProperty('operation')">
                {{ store.operationplan.name }}
              </b>
            </th>
          </tr>
          <tr v-if="!isMultipleOrNone && store.operationplan.type !== 'STCK'">
            <td>
              <b class="text-capitalize">{{ ttt('reference') }}</b>
            </td>
            <td id="referencerow">{{ store.operationplan.reference }}</td>
          </tr>
          <tr v-if="store.operationplan.type === 'MO' && store.operationplan.owner">
            <td>
              <b class="text-capitalize">{{ ttt('owner') }}</b>
            </td>
            <td id="ownerrow">
              {{ store.operationplan.owner }}
              <a
                :href="buildPrefixedUrl('/detail/input/manufacturingorder/', store.operationplan.reference)"
                data-entity="input/manufacturingorder"
                @click.stop
              >
                <span class="fa fa-caret-right"></span>
              </a>
            </td>
          </tr>
          <tr v-if="store.operationplan.item !== null && !isMultipleOrNone">
            <td>
              <b class="text-capitalize">{{ ttt('item') }}</b>
            </td>
            <td id="itemrow">
              {{ store.operationplan.item }}
              <a
                :href="buildPrefixedUrl('/detail/input/item/', store.operationplan.item)"
                data-entity="input/item"
                @click.stop
              >
                <span class="fa fa-caret-right"></span>
              </a>
            </td>
          </tr>
          <tr v-if="store.operationplan.item__description !== null && !isMultipleOrNone">
            <td></td>
            <td>
              <div
                style="max-width: 100%; white-space: nowrap; overflow: hidden"
                :title="store.operationplan.item__description"
                onmouseenter="window.jQuery(this).tooltip('show')"
              >
                {{ store.operationplan.item__description }}
              </div>
            </td>
          </tr>
          <tr v-if="store.operationplan.type === 'PO'">
            <td>
              <b class="text-capitalize">{{ ttt('supplier') }}</b>
            </td>
            <td id="supplierrow">
              {{ store.operationplan.supplier }}
              <a
                :href="buildPrefixedUrl('/detail/input/supplier/', store.operationplan.supplier)"
                data-entity="input/supplier"
                @click.stop
              >
                <span class="fa fa-caret-right"></span>
              </a>
            </td>
          </tr>
          <tr v-if="store.operationplan.supplier__description !== null && !isMultipleOrNone">
            <td></td>
            <td style="max-width: calc(100% - 120px); white-space: nowrap; overflow: hidden">
              <div
                style="max-width: 100%; white-space: nowrap; overflow: hidden"
                :title="store.operationplan.supplier__description"
                onmouseenter="window.jQuery(this).tooltip('show')"
              >
                {{ store.operationplan.supplier__description }}
              </div>
            </td>
          </tr>
          <tr v-if="store.operationplan.location !== null && !isMultipleOrNone">
            <td>
              <b class="text-capitalize">{{ ttt('location') }}</b>
            </td>
            <td id="locationrow">
              {{ store.operationplan.location }}
              <a
                :href="buildPrefixedUrl('/detail/input/location/', store.operationplan.location)"
                data-entity="input/location"
                @click.stop
              >
                <span class="fa fa-caret-right"></span>
              </a>
            </td>
          </tr>
          <tr v-if="store.operationplan.batch">
            <td>
              <b class="text-capitalize">{{ ttt('batch') }}</b>
            </td>
            <td>{{ store.operationplan.batch }}</td>
          </tr>
          <tr v-if="store.operationplan.type === 'DO'">
            <td>
              <b class="text-capitalize">{{ ttt('origin') }}</b>
            </td>
            <td id="originrow">
              {{ store.operationplan.origin }}
              <a
                :href="buildPrefixedUrl('/detail/input/location/', store.operationplan.origin)"
                data-entity="input/location"
                @click.stop
              >
                <span class="fa fa-caret-right"></span>
              </a>
            </td>
          </tr>
          <tr v-if="store.operationplan.type === 'DO'">
            <td>
              <b v-if="store.operationplan.type !== 'STCK'" class="text-capitalize">{{
                ttt('destination')
              }}</b>
              <b v-if="store.operationplan.type === 'STCK'" class="text-capitalize">{{
                ttt('location')
              }}</b>
            </td>
            <td id="destinationrow">
              {{ store.operationplan.destination }}
              <a
                :href="buildPrefixedUrl('/detail/input/location/', store.operationplan.destination)"
                data-entity="input/location"
                @click.stop
              >
                <span class="fa fa-caret-right"></span>
              </a>
            </td>
          </tr>
          <tr v-if="store.operationplan.type !== 'STCK'">
            <td>
              <b
                class="text-capitalize"
                v-if="(store.operationplan.type === 'MO' || store.operationplan.type === 'WO') && !store.operationplan.colmodel"
                >{{ ttt('start date') }}</b
              >
              <b class="text-capitalize" v-if="store.operationplan.type === 'PO' && !store.operationplan.colmodel">{{
                ttt('ordering date')
              }}</b>
              <b class="text-capitalize" v-if="store.operationplan.type === 'DO' && !store.operationplan.colmodel">{{
                ttt('shipping date')
              }}</b>
              <b
                class="text-capitalize"
                v-if="store.operationplan.colmodel?.operationplan__startdate"
                >{{ ttt(store.operationplan.colmodel.operationplan__startdate.label) }}</b
              >
              <b class="text-capitalize" v-if="store.operationplan.colmodel?.startdate && !store.operationplan.colmodel?.operationplan__startdate">{{
                ttt(store.operationplan.colmodel.startdate.label)
              }}</b>
              <small
                v-if="
                  store.operationplan.colmodel?.startdate &&
                  !store.operationplan.colmodel?.operationplan__startdate &&
                  (store.operationplan.colmodel?.startdate || isMultipleOrNone)
                "
              >
                &nbsp;({{ ttt(store.operationplan.colmodel?.startdate.type || 'min') }})
              </small>
              <small v-if="store.operationplan.colmodel?.operationplan__startdate">
                &nbsp;({{ ttt(store.operationplan.colmodel?.operationplan__startdate.type) }})
              </small>
            </td>
            <td>
              <input
                v-if="isMultipleOrNone"
                class="form-control border-0 bg-transparent"
                type="datetime-local"
                :value="store.operationplan.startdate || store.operationplan.start"
                readonly
                @input="handleShiftGroupDates('startdate', $event.target.value)"
              />
              <input
                v-if="!isMultipleOrNone && !opPlanHasOwnProperty('operationplan__startdate')"
                class="form-control"
                type="datetime-local"
                v-model="store.operationplan.start"
                @input="setEditValue('startdate', $event.target.value)"
                :readonly="!editable"
              />
              <input
                v-if="!isMultipleOrNone && opPlanHasOwnProperty('operationplan__startdate')"
                class="form-control"
                type="datetime-local"
                v-model="store.operationplan.operationplan__startdate"
                @input="setEditValue('startdate', $event.target.value)"
                :readonly="!editable"
              />
            </td>
          </tr>
          <tr v-if="store.operationplan.setupend">
            <td>
              <b class="text-capitalize">{{ ttt('setup end date') }}</b>
            </td>
            <td>
              {{ dateTimeFormat(store.operationplan.setupend || store.operationplan.operationplan__setupend) }}
            </td>
          </tr>
          <tr v-if="store.operationplan.type !== 'STCK'">
            <td>
              <b class="text-capitalize" v-if="store.operationplan.type === 'MO' && !store.operationplan.colmodel">{{
                ttt('end date')
              }}</b>
              <b class="text-capitalize" v-if="store.operationplan.type === 'PO' && !store.operationplan.colmodel">{{
                ttt('receipt date')
              }}</b>
              <b class="text-capitalize" v-if="store.operationplan.type === 'DO' && !store.operationplan.colmodel">{{
                ttt('receipt date')
              }}</b>
              <b class="text-capitalize" v-if="store.operationplan.colmodel?.enddate && !store.operationplan.colmodel?.operationplan__enddate">{{
                ttt(store.operationplan.colmodel.enddate.label)
              }}</b>
              <b
                class="text-capitalize"
                v-if="store.operationplan.colmodel?.operationplan__enddate"
                >{{ ttt(store.operationplan.colmodel.operationplan__enddate.label) }}</b
              >&nbsp;
              <small
                v-if="
                  store.operationplan.colmodel?.enddate &&
                  !store.operationplan.colmodel?.operationplan__enddate &&
                  (store.operationplan.colmodel?.enddate || isMultipleOrNone)
                "
              >
                &nbsp;({{ ttt(store.operationplan.colmodel?.enddate.type || 'max') }})
              </small>
              <small v-if="store.operationplan.colmodel?.operationplan__enddate"
                >&nbsp;({{ ttt(store.operationplan.colmodel?.operationplan__enddate.type) }})
              </small>
            </td>
            <td>
              <input
                v-if="isMultipleOrNone"
                class="form-control border-0 bg-transparent"
                type="datetime-local"
                :value="store.operationplan.enddate || store.operationplan.end"
                readonly
                @input="handleShiftGroupDates('enddate', $event.target.value)"
              />
              <input
                v-if="!isMultipleOrNone && !opPlanHasOwnProperty('operationplan__enddate')"
                class="form-control"
                type="datetime-local"
                v-model="store.operationplan.end"
                @input="setEditValue('enddate', $event.target.value)"
                :readonly="!editable"
              />
              <input
                v-if="!isMultipleOrNone && opPlanHasOwnProperty('operationplan__enddate')"
                class="form-control"
                type="datetime-local"
                v-model="store.operationplan.operationplan__enddate"
                @input="setEditValue('enddate', $event.target.value)"
                :readonly="!editable"
              />
            </td>
          </tr>
          <tr>
            <td>
              <b class="text-capitalize">{{ ttt('quantity') }}</b
              >&nbsp;
              <small
                v-if="
                  isMultipleOrNone &&
                  store.operationplan.colmodel &&
                  !store.operationplan.colmodel['operationplan__quantity']
                "
                >({{ ttt(store.operationplan.colmodel.quantity.type) }})
              </small>
              <small
                v-if="
                  isMultipleOrNone &&
                  store.operationplan.colmodel &&
                  store.operationplan.colmodel['operationplan__quantity']
                "
                >({{ ttt(store.operationplan.colmodel.operationplan__quantity.type) }})
              </small>
            </td>
            <td>
              <span v-if="isMultipleOrNone || store.operationplan.type == 'STCK'">{{
                numberFormat(
                  store.operationplan.operationplan__quantity || store.operationplan.quantity || 0
                )
              }}</span>
              <input
                v-if="!isMultipleOrNone && !opPlanHasOwnProperty('operationplan__quantity') && store.operationplan.type !== 'STCK'"
                class="form-control"
                type="number"
                v-model="store.operationplan.quantity"
                @input="setEditValue('quantity', $event.target.value)"
                :readonly="!editable"
              />
              <input
                v-if="!isMultipleOrNone && opPlanHasOwnProperty('operationplan__quantity') && store.operationplan.type !== 'STCK'"
                class="form-control"
                type="number"
                v-model="store.operationplan.operationplan__quantity"
                @input="setEditValue('quantity', $event.target.value)"
                :readonly="!editable"
              />
            </td>
          </tr>
          <tr v-for="[key, value] in filteredColmodel" :key="key">
            <td>
              <b class="text-capitalize">{{ ttt(value.label) }}</b>
              &nbsp;
              <small>({{ ttt(value.type) }})</small>
            </td>
            <td
              v-if="
                ['number', 'color', 'currency', 'currencyWithBlanks'].includes(value['formatter'])
              "
            >
              {{ numberFormat(store.operationplan[key]) }}
            </td>
            <td v-if="value['formatter'] === 'date'">
              {{ dateTimeFormat(store.operationplan[key]) }}
            </td>
            <td v-if="value['formatter'] === 'duration'">
              {{ formatDuration(store.operationplan[key]) }}
            </td>
            <td
              v-if="
                !['date', 'number', 'color', 'currency', 'currencyWithBlanks', 'duration'].includes(
                  value['formatter']
                )
              "
            >
              {{ store.operationplan[key] }}
            </td>
          </tr>
          <tr
            id="statusrow"
            v-if="store.operationplan.type !== 'STCK' && store.selectedOperationplans.length > 0"
          >
            <td>
              <b class="text-capitalize">{{ ttt('status') }}</b>
            </td>
            <td>
              <template v-if="isMultipleOrNone">
                <div class="btn-group" role="group">
                  <button
                    v-for="s in statusList"
                    :key="s"
                    type="button"
                    class="btn btn-sm text-capitalize"
                    :class="statusCounts[s] === selectedCount ? 'btn-secondary' : 'btn-primary'"
                    :disabled="actions.hasOwnProperty('erp_incr_export') || statusCounts[s] === selectedCount"
                    @click="handleSetStatus(s)"
                    data-bs-toggle="tooltip"
                    :title="ttt(s)"
                  >
                    <i :class="statusIcons[s]"></i>&nbsp;{{ statusCounts[s] || 0 }}
                  </button>
                  <button
                    id="erp_incr_exportBtn"
                    v-if="editable && actions.hasOwnProperty('erp_incr_export') && hasProposed"
                    type="button"
                    class="btn btn-primary text-capitalize"
                    :disabled="exporting"
                    @click="dispatchERPExport()"
                  >
                    <template v-if="exporting">
                      <span class="spinner-border spinner-border-sm me-1"></span>
                      {{ ttt('Exporting...') }}
                    </template>
                    <template v-else>
                      {{ ttt('Export') }}
                    </template>
                  </button>
                </div>
              </template>
              <div v-else class="btn-group" role="group">
                <button
                  id="proposedBtn"
                  v-if="(!editable && store.operationplan.status === ttt('proposed')) || editable"
                  type="button"
                  class="btn btn-sm text-capitalize"
                  :class="[
                    store.operationplan.status === 'proposed' ? 'active' : '',
                    store.isChanged(store.operationplan.reference, 'status') &&
                    store.operationplan.status === 'proposed'
                      ? 'btn-danger'
                      : 'btn-primary',
                  ]"
                  @click="setEditValue('status', 'proposed')"
                  :disabled="actions.hasOwnProperty('erp_incr_export') || !editable"
                  data-bs-toggle="tooltip"
                  :title="ttt('proposed')"
                >
                  <i class="fa fa-unlock"></i>
                </button>
                <button
                  id="approvedBtn"
                  v-if="(!editable && store.operationplan.status === ttt('approved')) || editable"
                  type="button"
                  class="btn btn-sm text-capitalize"
                  :class="[
                    store.operationplan.status === 'approved' ? 'active' : '',
                    store.isChanged(store.operationplan.reference, 'status') &&
                    store.operationplan.status === 'approved'
                      ? 'btn-danger'
                      : 'btn-primary',
                  ]"
                  @click="setEditValue('status', 'approved')"
                  :disabled="actions.hasOwnProperty('erp_incr_export') || !editable"
                  data-bs-toggle="tooltip"
                  :title="ttt('approved')"
                >
                  <i class="fa fa-unlock-alt"></i>
                </button>
                <button
                  id="confirmedBtn"
                  v-if="(!editable && store.operationplan.status === ttt('confirmed')) || editable"
                  type="button"
                  class="btn btn-sm text-capitalize"
                  :class="[
                    store.operationplan.status === 'confirmed' ? 'active' : '',
                    store.isChanged(store.operationplan.reference, 'status') &&
                    store.operationplan.status === 'confirmed'
                      ? 'btn-danger'
                      : 'btn-primary',
                  ]"
                  @click="setEditValue('status', 'confirmed')"
                  :disabled="actions.hasOwnProperty('erp_incr_export') || !editable"
                  data-bs-toggle="tooltip"
                  :title="ttt('confirmed')"
                >
                  <i class="fa fa-lock"></i>
                </button>
                <button
                  id="completedBtn"
                  v-if="(!editable && store.operationplan.status === ttt('completed')) || editable"
                  type="button"
                  class="btn btn-sm text-capitalize"
                  :class="[
                    store.operationplan.status === 'completed' ? 'active' : '',
                    store.isChanged(store.operationplan.reference, 'status') &&
                    store.operationplan.status === 'completed'
                      ? 'btn-danger'
                      : 'btn-primary',
                  ]"
                  @click="setEditValue('status', 'completed')"
                  :disabled="actions.hasOwnProperty('erp_incr_export') || !editable"
                  data-bs-toggle="tooltip"
                  :title="ttt('completed')"
                >
                  <i class="fa fa-check"></i>
                </button>
                <button
                  id="closedBtn"
                  v-if="(!editable && store.operationplan.status === ttt('closed')) || editable"
                  type="button"
                  class="btn btn-sm text-capitalize"
                  :class="[
                    store.operationplan.status === 'closed' ? 'active' : '',
                    store.isChanged(store.operationplan.reference, 'status') &&
                    store.operationplan.status === 'closed'
                      ? 'btn-danger'
                      : 'btn-primary',
                  ]"
                  @click="setEditValue('status', 'closed')"
                  :disabled="actions.hasOwnProperty('erp_incr_export') || !editable"
                  data-bs-toggle="tooltip"
                  :title="ttt('closed')"
                >
                  <i class="fa fa-times"></i>
                </button>
                <button
                  id="erp_incr_exportBtn"
                  v-if="
                    editable &&
                    actions.hasOwnProperty('erp_incr_export') &&
                    (store.operationplan.status === 'proposed' || store.operationplan.operationplan__status === 'proposed')
                  "
                  type="button"
                  class="btn btn-primary text-capitalize"
                  :disabled="exporting || !store.operationplan?.reference"
                  @click="dispatchERPExport()"
                >
                  <template v-if="exporting">
                    <span class="spinner-border spinner-border-sm me-1"></span>
                    {{ ttt('Exporting...') }}
                  </template>
                  <template v-else>
                    {{ ttt('Export') }}
                  </template>
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="opPlanHasOwnProperty('remark') && store.operationplan.type !== 'STCK'">
            <td>
              <b class="text-capitalize">{{ ttt('remark') }}</b>
            </td>
            <td>
              <input
                class="form-control"
                v-model="store.operationplan.remark"
                @input="setEditValue('remark', $event.target.value)"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
