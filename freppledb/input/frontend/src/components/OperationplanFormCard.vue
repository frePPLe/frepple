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
import { computed } from "vue";
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from "@/stores/operationplansStore.js";
import { numberFormat, isNumeric, debouncedInputHandler, dateTimeFormat } from "@common/utils.js";
import { useBootstrapTooltips } from '@common/useBootstrapTooltips.js';

useBootstrapTooltips();

const { t: ttt } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
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

const filteredColmodel = computed(() => {

  if (!store.operationplan || !store.operationplan.colmodel) {
    return [];
  }

  const excludedKeys = [
    'delay', 'criticality', 'quantity', 'startdate', 'enddate', 'color',
    'quantity_completed', 'operationplan__delay', 'operationplan__criticality',
    'operationplan__quantity', 'operationplan__startdate', 'operationplan__enddate',
    'operationplan__color', 'operationplan__quantity_completed'
  ];

  return Object.entries(store.operationplan.colmodel || {})
      .filter(([key]) =>
          !excludedKeys.includes(key) &&
          Object.prototype.hasOwnProperty.call(store.operationplan, key) &&
          store.operationplan[key] != null
      ).sort().reverse();
});

const editable = true;
// eslint-disable-next-line no-undef
const actions = window.actions;

const opptype = {
  'MO': ttt('manufacturing order'),
  'WO': ttt('work order'),
  'PO': ttt('purchase order'),
  'DO': ttt('distribution order'),
  'STCK': ttt('stock'),
  'DLVR': ttt('delivery'),
}

const isMultipleOrNone = computed(() => store.selectedOperationplans.length !== 1);

function validateNumericField(field, value) {
  if (!isNumeric(value)) {
    validationErrors.value[field] = 'Please enter a valid number';
    return false;
  } else {
    validationErrors.value[field] = '';
    return true;
  }
}

const setEditValueDebounced = debouncedInputHandler((field, value) => {
  if (value === '') return;
  store.setEditFormValues(field, value);
}, 300);

function setEditValue(field, value) {
  setEditValueDebounced(field, value);
}

const formatDuration = window.formatDuration;
</script>


<template>
  <div class="card">
    <div class="card-header d-flex align-items-center" data-bs-toggle="collapse" data-bs-target="#widget_operationplanpanel" aria-expanded="false" aria-controls="widget_operationplanpanel">
      <h5 class="card-title text-capitalize me-auto">
        <span v-if="isMultipleOrNone"  class="">{{ ttt('selected') }}&nbsp;{{ store.selectedOperationplans.length }}</span>
        <span v-if="store.operationplan.type && !isMultipleOrNone"  class="pl3 text-capitalize">{{ opptype[store.operationplan.type] }}</span>
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>
    <div v-if="store.selectedOperationplans.length > 0" class="card-body collapse"
       :class="{ 'show': !isCollapsed }" id="widget_operationplanpanel"
       @show="store.operationplan.reference || store.operationplan.operationplan__reference">
      <table style="table-layout:fixed" class="table table-sm table-hover table-borderless" id="opplan-attributes-drvtable">
        <tbody>
        <tr v-if="store.operationplan.operation?.name || store.operationplan.name">
          <td style="width: 120px">
            <b id="thead1" class="text-capitalize">{{ ttt('name') }}&nbsp;</b>
          </td>
          <td>
            <b class="text-capitalize" v-if="store.operationplan.hasOwnProperty('operation')">
              {{store.operationplan.operation.name}}
              <a href="/detail/input/operation/key/" data-entity="input/operation" onclick="opendetail(event)">
                <span class="fa fa-caret-right"></span>
              </a>
            </b>
            <b class="text-capitalize" v-if="!store.operationplan.hasOwnProperty('operation')">
              {{store.operationplan.name}}
            </b>
          </td>
        </tr>
        <tr v-if="!isMultipleOrNone && store.operationplan.type !== 'STCK'">
          <td><b class="text-capitalize">{{ ttt('reference' )}}</b></td>
          <td id="referencerow">{{store.operationplan.reference}}</td>
        </tr>
        <tr v-if="store.operationplan.type === 'MO' && store.operationplan.owner">
          <td><b class="text-capitalize">{{ttt('owner')}}</b></td>
          <td id="ownerrow">{{store.operationplan.owner}}
            <a href="/detail/input/manufacturingorder/key/" data-entity="input/manufacturingorder" onclick="opendetail(event)">
              <span class="fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        <tr v-if="store.operationplan.item !== null && !isMultipleOrNone">
          <td><b class="text-capitalize">{{ttt('item')}}</b></td>
          <td id="itemrow">
            {{store.operationplan.item}}
            <a href="/detail/input/item/key/" data-entity="input/item" onclick="opendetail(event)">
              <span class="fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        <tr v-if="store.operationplan.item__description !== null && !isMultipleOrNone">
          <td></td>
          <td>
            <div style="max-width: 100%; white-space: nowrap; overflow:hidden"
                 :title="store.operationplan.item__description" onmouseenter="$(this).tooltip('show')">
              {{store.operationplan.item__description}}
            </div>
          </td>
        </tr>
        <tr v-if="store.operationplan.type === 'PO'">
          <td><b class="text-capitalize">{{ttt('supplier')}}</b></td>
          <td id="supplierrow">{{store.operationplan.supplier}}
            <a href="/detail/input/supplier/key/" data-entity="input/supplier" onclick="opendetail(event)">
              <span class="fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        <tr v-if="store.operationplan.supplier__description !== null && !isMultipleOrNone">
          <td></td>
          <td style="max-width: calc(100% - 120px); white-space: nowrap; overflow:hidden">
            <div style="max-width: 100%; white-space: nowrap; overflow:hidden"
                 :title="store.operationplan.supplier__description" onmouseenter="$(this).tooltip('show')">
              {{store.operationplan.supplier__description}}
            </div>
          </td>
        </tr>
        <tr v-if="store.operationplan.location !== null && !isMultipleOrNone">
          <td><b class="text-capitalize">{{ttt('location')}}</b></td>
          <td id="locationrow">{{store.operationplan.location}}
            <a href="/detail/input/location/key/" data-entity="input/location" onclick="opendetail(event)">
              <span class="fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        <tr v-if="store.operationplan.batch">
          <td><b class="text-capitalize">{{ttt('batch')}}</b></td>
          <td>{{store.operationplan.batch}}</td>
        </tr>
        <tr v-if="store.operationplan.type === 'DO'">
          <td><b class="text-capitalize">{{ttt('origin')}}</b></td>
          <td id="originrow">{{store.operationplan.origin}}
            <a href="/detail/input/location/key/" data-entity="input/location" onclick="opendetail(event)">
              <span class="fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        <tr v-if="store.operationplan.type === 'DO'">
          <td>
            <b v-if="store.operationplan.type !== 'STCK'" class="text-capitalize">{{ttt('destination')}}</b>
            <b v-if="store.operationplan.type === 'STCK'" class="text-capitalize">{{ttt('location')}}</b>
          </td>
          <td id="destinationrow">{{store.operationplan.destination}}
            <a href="/detail/input/location/key/" data-entity="input/location" onclick="opendetail(event)">
              <span class="fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        <tr v-if="store.operationplan.type !== 'STCK'">
          <td>
            <b class="text-capitalize" v-if="store.operationplan.type === 'MO' || store.operationplan.type === 'WO'">{{ttt('start date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type === 'PO'">{{ttt('ordering date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type === 'DO'">{{ttt('shipping date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.colmodel?.operationplan__startdate">{{ttt(store.operationplan.colmodel.operationplan__startdate.label)}}</b>
            <b class="text-capitalize" v-if="store.operationplan.colmodel?.startdate">{{ttt(store.operationplan.colmodel.startdate.label)}}</b>
            <small v-if="store.operationplan.colmodel?.startdate && (store.operationplan.colmodel?.startdate || isMultipleOrNone)">&nbsp;({{ ttt(store.operationplan.colmodel?.startdate.type || 'min') }})</small>
            <small v-if="store.operationplan.colmodel?.operationplan__startdate">&nbsp;({{ ttt(store.operationplan.colmodel?.operationplan__startdate.type) }})</small>
          </td>
          <td>
            <input v-if="isMultipleOrNone && store.operationplan.startdate"
                 class="form-control border-0 bg-white" type="datetime-local" v-model="store.operationplan.startdate"
                 readonly>
            <input v-if="isMultipleOrNone && !store.operationplan.startdate"
                 class="form-control border-0 bg-white" type="datetime-local" v-model="store.operationplan.start"
                 readonly>
            <input
                v-if="!isMultipleOrNone && !store.operationplan.hasOwnProperty('operationplan__startdate')"
                class="form-control" type="datetime-local" v-model="store.operationplan.start"
                @input="setEditValue('startdate', $event.target.value)" :readonly="!editable">
            <input
                v-if="!isMultipleOrNone && store.operationplan.hasOwnProperty('operationplan__startdate')"
                class="form-control" type="datetime-local" v-model="store.operationplan.operationplan__startdate"
                @input="setEditValue('startdate', $event.target.value)" :readonly="!editable">
          </td>
        </tr>
        <tr v-if="store.operationplan.setupend">
          <td><b class="text-capitalize">{{ttt('setup end date')}}</b></td>
          <td>{{store.operationplan.setupend || store.operationplan.operationplan__setupend}}</td>
        </tr>
        <tr v-if="store.operationplan.type !== 'STCK'">
          <td>
            <b class="text-capitalize" v-if="store.operationplan.type === 'MO'">{{ttt('end date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type === 'PO'">{{ttt('receipt date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type === 'DO'">{{ttt('receipt date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.colmodel?.enddate">{{ttt(store.operationplan.colmodel.enddate.label)}}</b>
            <b class="text-capitalize" v-if="store.operationplan.colmodel?.operationplan__enddate">{{ttt(store.operationplan.colmodel.operationplan__enddate.label)}}</b>&nbsp;
            <small v-if="store.operationplan.colmodel?.enddate && (store.operationplan.colmodel?.enddate || isMultipleOrNone)">&nbsp;({{ ttt(store.operationplan.colmodel?.enddate.type || 'max') }})</small>
            <small v-if="store.operationplan.colmodel?.operationplan__enddate">&nbsp;({{ ttt(store.operationplan.colmodel?.operationplan__enddate.type) }})</small>
          </td>
          <td>
            <input v-if="isMultipleOrNone && store.operationplan.enddate"
                   class="form-control border-0 bg-white"
                   type="datetime-local" v-model="store.operationplan.enddate" readonly>
            <input v-if="isMultipleOrNone && !store.operationplan.enddate"
                   class="form-control border-0 bg-white"
                   type="datetime-local" v-model="store.operationplan.end" readonly>
            <input v-if="!isMultipleOrNone && !store.operationplan.hasOwnProperty('operationplan__enddate')"
                   class="form-control" type="datetime-local" v-model="store.operationplan.end"
                   @input="setEditValue('enddate', $event.target.value)" :readonly="!editable">
            <input v-if="!isMultipleOrNone && store.operationplan.hasOwnProperty('operationplan__enddate')"
                   class="form-control" type="datetime-local" v-model="store.operationplan.operationplan__enddate"
                   @input="setEditValue('enddate', $event.target.value)" :readonly="!editable">
          </td>
        </tr>
        <tr>
          <td><b class="text-capitalize">{{ttt('quantity')}}</b>&nbsp;
            <small v-if="isMultipleOrNone && store.operationplan.colmodel && !store.operationplan.colmodel['operationplan__quantity']">({{ ttt(store.operationplan.colmodel.quantity.type) }})</small>
            <small v-if="isMultipleOrNone && store.operationplan.colmodel && store.operationplan.colmodel['operationplan__quantity']">({{ ttt(store.operationplan.colmodel.operationplan__quantity.type) }})</small>
          </td>
          <td>
            <span v-if="isMultipleOrNone">{{ numberFormat(store.operationplan.operationplan__quantity || store.operationplan.quantity || 0) }}</span>
            <input v-if="!isMultipleOrNone && !store.operationplan.hasOwnProperty('operationplan__quantity')" class="form-control" type="number" v-model="store.operationplan.quantity" @input="setEditValue('quantity', $event.target.value)" :readonly="!editable">
            <input v-if="!isMultipleOrNone && store.operationplan.hasOwnProperty('operationplan__quantity')" class="form-control" type="number" v-model="store.operationplan.operationplan__quantity" @input="setEditValue('quantity', $event.target.value)" :readonly="!editable">
          </td>
        </tr>
        <tr v-for="([key, value]) in filteredColmodel" :key="key">
          <td><b class="text-capitalize">{{ttt(value.label)}}</b>&nbsp;
            <small>({{ ttt(value.type) }})</small>
          </td>
          <td v-if="['number', 'color', 'currency', 'currencyWithBlanks'].includes(value['formatter'])">{{numberFormat(store.operationplan[key])}}</td>
          <td v-if="value['formatter'] === 'date'">{{dateTimeFormat(store.operationplan[key])}}</td>
          <td v-if="value['formatter'] === 'duration'">{{formatDuration(store.operationplan[key])}}</td>
          <td v-if="!['date', 'number', 'color', 'currency', 'currencyWithBlanks', 'duration'].includes(value['formatter'])">{{store.operationplan[key]}}</td>
        </tr>
        <tr id="statusrow" v-if="store.operationplan.type !== 'STCK' && !isMultipleOrNone">
          <td><b class="text-capitalize">{{ttt('status')}}</b></td>
          <td>
            <div class="btn-group" role="group">
              <button id="proposedBtn" v-if="(!editable && store.operationplan.status === ttt('proposed')) || editable" type="button" class="btn btn-primary text-capitalize" :class="store.operationplan.status === 'proposed' ? 'active': ''" @click="setEditValue('status', 'proposed')" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('proposed')"> <i class="fa fa-unlock"></i></button>
              <button id="approvedBtn" v-if="(!editable && store.operationplan.status === ttt('approved')) || editable" type="button" class="btn btn-primary text-capitalize" :class="store.operationplan.status === 'approved' ? 'active': ''" @click="setEditValue('status', 'approved')" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('approved')"><i class="fa fa-unlock-alt"></i></button>
              <button id="confirmedBtn" v-if="(!editable && store.operationplan.status === ttt('confirmed')) || editable" type="button" class="btn btn-primary text-capitalize" :class="store.operationplan.status === 'confirmed' ? 'active': ''" @click="setEditValue('status', 'confirmed')" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('confirmed')"><i class="fa fa-lock"></i></button>
              <button id="completedBtn" v-if="(!editable && store.operationplan.status === ttt('completed')) || editable" type="button" class="btn btn-primary text-capitalize" :class="store.operationplan.status === 'completed' ? 'active': ''" @click="setEditValue('status', 'completed')" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('completed')"><i class="fa fa-check"></i></button>
              <button id="closedBtn" v-if="(!editable && store.operationplan.status === ttt('closed')) || editable" type="button" class="btn btn-primary text-capitalize" :class="store.operationplan.status === 'closed' ? 'active': ''" @click="setEditValue('status', 'closed')" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('closed')"><i class="fa fa-times"></i></button>
              <button id="erp_incr_exportBtn" v-if="editable && actions.hasOwnProperty('erp_incr_export') && store.operationplan.status === 'proposed'" type="button" class="btn btn-primary text-capitalize" @click="actions['erp_incr_export']()">{{ttt('export')}}</button>
            </div>
          </td>
        </tr>
        <tr v-if="store.operationplan.hasOwnProperty('remark')&& store.operationplan.type !== 'STCK'">
          <td><b class="text-capitalize">{{ttt('remark')}}</b></td>
          <td><input class="form-control" v-model="store.operationplan.remark" @input="setEditValue('remark', $event.target.value)"></td>
        </tr>
        </tbody>

      </table>
    </div>
  </div>
</template>
