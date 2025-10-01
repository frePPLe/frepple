<script setup lang="js">
import {ref, computed, onMounted} from "vue";
import {useForecastsStore} from "@/stores/forecastsStore.js";
import { isNumeric } from "@common/utils.js";

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

function validateField(field, value) {
  if (!isNumeric(value)) {
    validationErrors.value[field] = 'Please enter a valid number';
    return false;
  } else {
    validationErrors.value[field] = '';
    return true;
  }
}

function setSelectedMeasure(measure) {
  store.editForm.selectedMeasure = measure;
  changeEdit();
}

function setStartDate(event) {
  store.editForm.startDate = event.target.value;
  changeEdit();
}

function setEndDate(event) {
  store.editForm.endDate = event.target.value;
  changeEdit();
}

function setEditMode(mode) {
  store.editForm.mode = mode;
  changeEdit();
}

function setEditValue(field, value) {
  store.editForm[field] = value;
  validateField(field, value);
  changeEdit();
}

function applyEdit() {
  console.log('applyEdit', store.editForm.value);
  // Add your apply logic here
}

function changeEdit() {
  if (store.editForm.selectedMeasure?.label === undefined) {
    activateApply.value = false;
    return;
  }

  let result = false;
  console.log('changeEdit', store.editForm.value);

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

  // Also check that there are no validation errors
  const hasValidationErrors = Object.values(validationErrors.value).some(error => error !== '');
  activateApply.value = result && !hasValidationErrors;
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title text-capitalize mb-0"><span class="">edit</span></h5>
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
              <span class="">Apply</span>
            </button>
          </td>
          <td>
            <form class="mb-3 pristine valid">
              Update
              <div class="dropdown" style="display:inline-block">
                <button
                  type="button"
                  class="dropdown-toggle form-control d-inline w-auto"
                  data-bs-toggle="dropdown"
                  id="editmeasure"
                  name="editmeasure"
                  aria-haspopup="true"
                  aria-expanded="false"
                  style="min-width:200px"
                >
                  {{ store.editForm.selectedMeasure?.label || 'Select measure' }}&nbsp;&nbsp;<span class="caret"></span>
                </button>
                <ul class="dropdown-menu" aria-labelledby="editmeasure">
                  <li v-for="m in sortedEditableMeasureList" :key="m.label">
                    <a class="dropdown-item" @click="setSelectedMeasure(m)" href="#">
                      <span class="ng-binding ng-scope">{{m.label}}</span>
                    </a>
                  </li>
                </ul>
              </div>
              &nbsp;from&nbsp;
              <input
                id="editstartdate"
                type="date"
                class="form-control d-inline w-auto pristine untouched valid not-empty"
                :value="store.editForm.startDate"
                @input="setStartDate"
                style="background: white !important"
              >
              &nbsp;till&nbsp;
              <input
                id="editenddate"
                type="date"
                class="form-control d-inline w-auto pristine untouched valid not-empty"
                :value="store.editForm.endDate"
                @input="setEndDate"
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
                  value="set"
                >
                Set to
                <input
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

            <div class="radio mb-3">
              <label>
                <input
                  class="form-check-input nodirty align-text-bottom pristine untouched valid not-empty"
                  type="radio"
                  :checked="store.editForm.mode === 'increase'"
                  @change="setEditMode('increase')"
                  name="optradio"
                  value="increase"
                >
                Increase by
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

            <div class="radio mb-3">
              <label>
                <input
                  class="form-check-input nodirty align-text-bottom pristine untouched valid not-empty"
                  type="radio"
                  :checked="store.editForm.mode === 'increasePercent'"
                  @change="setEditMode('increasePercent')"
                  name="optradio"
                  value="increasePercent"
                >
                Increase by
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
