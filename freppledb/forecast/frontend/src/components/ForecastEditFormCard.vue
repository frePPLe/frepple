<script setup lang="js">
import {ref, computed, onMounted} from "vue";
import { useI18n } from 'vue-i18n';
import {useForecastsStore} from "@/stores/forecastsStore.js";
import { isNumeric } from "@common/utils.js";
import { useBootstrapTooltips } from '@common/useBootstrapTooltips.js'

useBootstrapTooltips();

const { t: ttt, locale, availableLocales } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});

const store = useForecastsStore();

let activateApply = ref(false);

// Validation states for each input
const validationErrors = ref({
  setTo: '',
  increaseBy: '',
  increaseByPercent: ''
});

const sortedEditableMeasureList = computed(() => {
  return Object.values(store.measures).filter(x => x.editable).sort((a, b) => {
    return a.label.localeCompare(b.label);
  });
});

// Initialize selectedMeasure when component mounts
onMounted(() => {
  if (sortedEditableMeasureList.value.length > 0 && !store.editForm.selectedMeasure?.label) {
    store.editForm.selectedMeasure = sortedEditableMeasureList.value[0];
  }
  store.editForm.mode = "set";
});

function validateNumericField(field, value) {
  if (!isNumeric(value)) {
    validationErrors.value[field] = 'Please enter a valid number';
    return false;
  } else {
    validationErrors.value[field] = '';
    return true;
  }
}

function setSelectedMeasure(measure) {
  store.setEditFormValues("selectedMeasure", measure);
  changeEdit();
}

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

import { debouncedInputHandler } from "@common/utils.js";

const setEditValueDebounced = debouncedInputHandler((field, value) => {
  if (value === '') return;
  if (store.editForm.selectedMeasure?.formatter === 'number' || store.editForm.selectedMeasure?.formatter === 'currency') {
    validateNumericField(field, value);
    store.setEditFormValues(field, parseFloat(value));
  } else {
    store.setEditFormValues(field, value);
  }
  changeEdit();
}, 300);

function setEditValue(field, value) {
  setEditValueDebounced(field, value);
}

function applyEdit() {
  store.applyForecastChanges();
}

function changeEdit() {
  if (store.editForm.selectedMeasure?.label === undefined) {
    activateApply.value = false;
    return;
  }

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
  store.preselectedBucketIndexes.value = store.getBucketIndexesFromFormDates();
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title text-capitalize mb-0"><span class="">{{ttt("edit")}}</span></h5>
    </div>
    <div class="card-body">
      <table>
        <tbody>
        <tr>
          <td style="vertical-align:top; padding: 15px">
            <button
              id="applyedit"
              type="submit"
              @click="applyEdit()"
              class="btn btn-primary"
              :disabled="!activateApply"
            >
              <span class="">{{ ttt('Apply') }}</span>
            </button>
          </td>
          <td>
            <form class="mb-3 pristine valid">
              {{ ttt('Update') }}
              <div class="dropdown" style="display:inline-block">
                <button
                  type="button"
                  class="dropdown-toggle form-control d-inline w-auto text-capitalize"
                  data-bs-toggle="dropdown"
                  id="editmeasure"
                  name="editmeasure"
                  aria-haspopup="true"
                  aria-expanded="false"
                  style="min-width:200px"
                >
                  {{ store.editForm.selectedMeasure?.label || ttt('select measure') }}&nbsp;&nbsp;<span class="caret"></span>
                </button>
                <ul class="dropdown-menu" aria-labelledby="editmeasure">
                  <li v-for="m in sortedEditableMeasureList" :key="m.label">
                    <a class="dropdown-item" @click="setSelectedMeasure(m)" href="#">
                      <span class="ng-binding ng-scope">{{m.label}}</span>
                    </a>
                  </li>
                </ul>
              </div>
              &nbsp;{{ ttt('from') }}&nbsp;
              <input
                id="editstartdate"
                type="date"
                class="form-control d-inline w-auto pristine untouched valid not-empty"
                :value="store.editForm.startDate"
                @input="setStartDate"
                style="background: white !important"
              >
              &nbsp;{{ ttt('till') }}&nbsp;
              <input
                id="editenddate"
                type="date"
                class="form-control d-inline w-auto pristine untouched valid not-empty"
                :value="store.editForm.endDate"
                @input="setEndDate"
                :min="store.editForm.startDate"
                style="background: white !important"
              >
            </form>

            <div class="radio mb-3">
              <label>
                <input
                  class="form-check-input nodirty align-text-bottom pristine untouched valid not-empty"
                  type="radio"
                  :checked="store.editForm.mode === 'set'"
                  @change="setEditMode('set')"
                  name="optradio"
                  :value="set"
                >
                {{ ttt('Set to') }}
                <input
                  id="editset"
                  type="text"
                  class="form-control d-inline pristine untouched valid empty"
                  :class="{ 'is-invalid': validationErrors.setTo }"
                  :value="store.editForm.setTo"
                  @input="setEditValue('setTo', $event.target.value)"
                  @focus="setEditMode('set')"
                  style="width:8rem; background: white !important"
                >
              </label>
              <div v-if="validationErrors.setTo" class="invalid-feedback d-block" style="font-size: 0.875em; margin-left: 2rem;">
                {{ validationErrors.setTo }}
              </div>
            </div>

            <div v-if="store.editForm.selectedMeasure && (store.editForm.selectedMeasure.formatter == 'number' || store.editForm.selectedMeasure.formatter == 'currency')" class="radio mb-3">
              <label>
                <input
                  class="form-check-input nodirty align-text-bottom pristine untouched valid not-empty"
                  type="radio"
                  :checked="store.editForm.mode === 'increase'"
                  @change="setEditMode('increase')"
                  name="optradio"
                  value="increase"
                >
                {{ ttt('Increase by') }}
                <input
                  type="text"
                  class="form-control d-inline pristine untouched valid empty"
                  :class="{ 'is-invalid': validationErrors.increaseBy }"
                  :value="store.editForm.increaseBy"
                  @input="setEditValue('increaseBy', $event.target.value)"
                  @focus="setEditMode('increase')"
                  style="width:8rem; background: white !important"
                >
              </label>
              <div v-if="validationErrors.increaseBy" class="invalid-feedback d-block" style="font-size: 0.875em; margin-left: 2rem;">
                {{ validationErrors.increaseBy }}
              </div>
            </div>

            <div v-if="store.editForm.selectedMeasure && (store.editForm.selectedMeasure.formatter == 'number' || store.editForm.selectedMeasure.formatter == 'currency')" class="radio mb-3">
              <label>
                <input
                  class="form-check-input nodirty align-text-bottom pristine untouched valid not-empty"
                  type="radio"
                  :checked="store.editForm.mode === 'increasePercent'"
                  @change="setEditMode('increasePercent')"
                  name="optradio"
                  value="increasePercent"
                >
                {{ ttt('Increase by') }}
                <input
                  type="text"
                  class="form-control d-inline pristine untouched valid empty"
                  :class="{ 'is-invalid': validationErrors.increaseByPercent }"
                  :value="store.editForm.increaseByPercent"
                  @input="setEditValue('increaseByPercent', $event.target.value)"
                  @focus="setEditMode('increasePercent')"
                  style="width:3rem; background: white !important"
                > %
              </label>
              <div v-if="validationErrors.increaseByPercent" class="invalid-feedback d-block" style="font-size: 0.875em; margin-left: 2rem;">
                {{ validationErrors.increaseByPercent }}
              </div>
            </div>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
