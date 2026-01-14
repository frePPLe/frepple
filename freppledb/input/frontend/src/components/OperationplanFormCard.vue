/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

<script setup lang="js">
import {ref, computed} from "vue";
import { useI18n } from 'vue-i18n';
import {useOperationplansStore} from "@/stores/operationplansStore.js";
import { isNumeric, debouncedInputHandler } from "@common/../../static/utils.js";
import { useBootstrapTooltips } from '@common/useBootstrapTooltips.js';
import {numberFormat} from "../../../../common/frontend/src/utils.js";
useBootstrapTooltips();

const { t: ttt } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});

const store = useOperationplansStore();

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
      );
});

let activateApply = ref(false);

// Validation states for each input
const validationErrors = ref({
  setTo: '',
  increaseBy: '',
  increaseByPercent: ''
});

const editable = true;
// eslint-disable-next-line no-undef
const actions = window.actions;

const opptype = {
  'MO': ttt('manufacturing order'),
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

// function setSelectedMeasure(measure) {
//   store.setEditFormValues("selectedMeasure", measure);
//   changeEdit();
// }

function setStartDate(event) {
  store.setEditFormValues("startDate", event.target.value);
  changeEdit();
}

function setEndDate(event) {
  store.setEditFormValues("endDate", event.target.value);
  changeEdit();
}

function setEditMode(mode) {
  store.setEditFormValues("mode", mode);
  changeEdit();
}

const setEditValueDebounced = debouncedInputHandler((field, value) => {
  if (value === '') return;
  store.setEditFormValues(field, value);
  changeEdit();
}, 300);

function setEditValue(field, value) {
  setEditValueDebounced(field, value);
}

function applyEdit() {
  store.applyOperationplanChanges();
}

function changeEdit() {
  if (store.editForm.selectedMeasure?.label === undefined) {
    activateApply.value = false;
    return;
  }
  result = isNumeric(store.editForm.setTo) && parseFloat(store.editForm.setTo) >= 0;

  let result = false;

  switch (store.editForm.mode) {
    case 'set':
      result = isNumeric(store.editForm.setTo) && parseFloat(store.editForm.setTo) >= 0;
      break;
    case 'increase':
      result = isNumeric(store.editForm.increaseBy);
      break;
    case 'increasePercent':
      result = isNumeric(store.editForm.increaseByPercent);
      break;
    default:
      result = false;
      break;
  }

  // check validation errors
  const hasValidationErrors = Object.values(validationErrors.value).some(error => error !== '');
  activateApply.value = result && !hasValidationErrors;
}
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
    <div class="card-body collapse show" id="widget_operationplanpanel" @show="store.operationplan.reference || store.operationplan.operationplan__reference">
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
        <tr v-if="store.operationplan.type == 'MO' && store.operationplan.owner">
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
        <tr v-if="store.operationplan.type == 'DO'">
          <td><b class="text-capitalize">{{ttt('origin')}}</b></td>
          <td id="originrow">{{store.operationplan.origin}}
            <a href="/detail/input/location/key/" data-entity="input/location" onclick="opendetail(event)">
              <span class="fa fa-caret-right"></span>
            </a>
          </td>
        </tr>
        <tr v-if="store.operationplan.type == 'DO'">
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
            <b class="text-capitalize" v-if="store.operationplan.type == 'MO' || isMultipleOrNone">{{ttt('start date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type == 'PO'">{{ttt('ordering date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type == 'DO'">{{ttt('shipping date')}}</b>
<!--            <b class="text-capitalize" v-if="store.operationplan.colmodel?.operationplan__startdate">{{ttt(store.operationplan.colmodel.operationplan__startdate.label)}}</b>&nbsp;-->
<!--            <b class="text-capitalize" v-if="store.operationplan.colmodel?.startdate">{{ttt(store.operationplan.colmodel.startdate.label)}}</b>-->
            <small v-if="store.operationplan.colmodel?.startdate || isMultipleOrNone">({{ ttt(store.operationplan.colmodel?.startdate.type || 'min') }})</small>
            <small v-if="store.operationplan.colmodel?.operationplan__startdate">({{ ttt(store.operationplan.colmodel?.operationplan__startdate.type) }})</small>
          </td>
          <td>
            <input v-if="isMultipleOrNone && store.operationplan.startdate"
                 class="form-control border-0 bg-white" type="datetime-local" v-model="store.operationplan.startdate"
                 readonly>
            <input
                v-if="!isMultipleOrNone && !store.operationplan.hasOwnProperty('operationplan__startdate')"
                class="form-control" type="datetime-local" v-model="store.operationplan.start"
                @input="setEditValue('startdate', $event.target.value)" :readonly="!editable">
            <input
                v-if="!isMultipleOrNone && store.operationplan.hasOwnProperty('operationplan__startdate')"
                class="form-control" type="datetime-local" v-model="store.operationplan.operationplan__startdate"
                @input="setEditValue('enddate', $event.target.value)" :readonly="!editable">
          </td>
        </tr>
        <tr v-if="store.operationplan.setupend">
          <td><b class="text-capitalize">{{ttt('setup end date')}}</b></td>
          <td>{{store.operationplan.setupend || store.operationplan.operationplan__setupend}}</td>
        </tr>
        <tr v-if="store.operationplan.type !== 'STCK'">
          <td>
            <b class="text-capitalize" v-if="store.operationplan.type == 'MO' || isMultipleOrNone">{{ttt('end date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type == 'PO'">{{ttt('receipt date')}}</b>
            <b class="text-capitalize" v-if="store.operationplan.type == 'DO'">{{ttt('receipt date')}}</b>
<!--            <b class="text-capitalize" v-if="store.operationplan.colmodel?.enddate">{{ttt(store.operationplan.colmodel.enddate.label)}}</b>-->
<!--            <b class="text-capitalize" v-if="store.operationplan.colmodel?.operationplan__enddate">{{ttt(store.operationplan.colmodel.operationplan__enddate.label)}}</b>&nbsp;-->
            <small v-if="store.operationplan.colmodel?.enddate || isMultipleOrNone">({{ ttt(store.operationplan.colmodel?.enddate.type || 'max') }})</small>
            <small v-if="store.operationplan.colmodel?.operationplan__enddate">({{ ttt(store.operationplan.colmodel?.operationplan__enddate.type) }})</small>
          </td>
          <td>
            <input v-if="isMultipleOrNone && store.operationplan.enddate"
                   class="form-control border-0 bg-white"
                   type="datetime-local" v-model="store.operationplan.enddate" readonly>
            <input v-if="!isMultipleOrNone && !store.operationplan.hasOwnProperty('store.operationplan__enddate')"
                   class="form-control" type="datetime-local" v-model="store.operationplan.end"
                   @input="setEditValue('enddate', $event.target.value)" :readonly="!editable">
            <input v-if="!isMultipleOrNone && store.operationplan.hasOwnProperty('store.operationplan__enddate')"
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
            <input v-if="!isMultipleOrNone && !store.operationplan.hasOwnProperty('store.operationplan__quantity')" class="form-control" type="number" v-model="store.operationplan.quantity" @input="setEditValue('quantity', $event.target.value)" :readonly="!editable">
            <input v-if="!isMultipleOrNone && store.operationplan.hasOwnProperty('store.operationplan__quantity')" class="form-control" type="number" v-model="store.operationplan.operationplan__quantity" @input="setEditValue('quantity', $event.target.value)" :readonly="!editable">
          </td>
        </tr>
        <tr v-for="([key, value]) in filteredColmodel" :key="key">
          <td><b class="text-capitalize">{{ttt(value.label)}}</b>&nbsp;
            <small>({{ ttt(value.type) }} - {{key}})</small>
          </td>
          <td v-if="['number', 'color', 'currency', 'currencyWithBlanks'].includes(value['formatter'])">{{numberFormat(store.operationplan[key])}}</td>
          <td v-if="value['formatter'] === 'date'">{{store.operationplan[key]}}</td>
          <td v-if="!['date', 'number', 'color', 'currency', 'currencyWithBlanks'].includes(value['formatter'])">{{store.operationplan[key]}}</td>
        </tr>
        <tr id="statusrow" v-if="store.operationplan.type !== 'STCK'">
          <td><b class="text-capitalize">{{ttt('status')}}</b></td>
          <td>
            <div class="btn-group" role="group">
              <button id="proposedBtn" v-if="(!editable && store.operationplan.status === ttt('proposed')) || editable" type="button" class="btn btn-primary" :class="['text-capitalize', {'active': store.operationplan.status == 'proposed'}]" @click="store.operationplan.status = 'proposed'" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('proposed')"> <i class="fa fa-unlock"></i></button>
              <button id="approvedBtn" v-if="(!editable && store.operationplan.status === ttt('approved')) || editable" type="button" class="btn btn-primary" :class="['text-capitalize', {'active': store.operationplan.status == 'approved'}]" @click="store.operationplan.status = 'approved'" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('approved')"><i class="fa fa-unlock-alt"></i></button>
              <button id="confirmedBtn" v-if="(!editable && store.operationplan.status === ttt('confirmed')) || editable" type="button" class="btn btn-primary" :class="['text-capitalize', {'active': store.operationplan.status == 'confirmed'}]" @click="store.operationplan.status = 'confirmed'" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('confirmed')"><i class="fa fa-lock"></i></button>
              <button id="completedBtn" v-if="(!editable && store.operationplan.status === ttt('completed')) || editable" type="button" class="btn btn-primary" :class="['text-capitalize', {'active': store.operationplan.status == 'completed'}]" @click="store.operationplan.status = 'completed'" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('completed')"><i class="fa fa-check"></i></button>
              <button id="closedBtn" v-if="(!editable && store.operationplan.status === ttt('closed')) || editable" type="button" class="btn btn-primary" :class="['text-capitalize', {'active': store.operationplan.status === 'closed'}]" @click="store.operationplan.status = 'closed'" :disabled="actions.hasOwnProperty('erp_incr_export') || !editable" data-bs-toggle="tooltip" :title="ttt('closed')"><i class="fa fa-times"></i></button>
              <button id="erp_incr_exportBtn" v-if="editable && actions.hasOwnProperty('erp_incr_export')&& store.operationplan.status === 'proposed'" type="button" class="btn btn-primary text-capitalize" @click="actions['erp_incr_export']()">{{ttt('export')}}</button>
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
