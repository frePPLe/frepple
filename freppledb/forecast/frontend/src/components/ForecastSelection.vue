<script setup lang="js">
import { useForecastsStore } from '@/stores/forecastsStore';
import {computed} from "vue";

const store = useForecastsStore();
const dict =  {'I':'item', 'L':'location', 'C':'customer'};
console.log("ForecastSelection.vue");
console.log(store.currentSequence);
console.log(store.measures);

const sortedMeasureList = computed(() => {
  return Object.values(store.measures).sort((a, b) => {
    return a.label.localeCompare(b.label);
  });
});
</script>

<template>
<div>
  <div class="row mb-1">
    <div class="col-auto">
      <div class="dropdown d-inline w-auto">
        <button bs-title="{{t('Select panel sequence')}}" class="form-control d-inline w-auto dropdown-toggle text-capitalize" id="selectseq" name="sequence" type="button" data-bs-toggle="dropdown" aria-expanded="false">
<!--          {{ $t(dict[store.currentSequence[0]]) }}{{(store.currentSequence).length > 1 ? "," : ""}}&nbsp;{{ $t(dict[store.currentSequence[1]]) }}{{(store.currentSequence).length > 2 ? "," : ""}}&nbsp;{{ $t(dict[store.currentSequence[2]]) }}&nbsp;&nbsp;<span class="caret"></span>-->
          {{ dict[store.currentSequence[0]] }}{{(store.currentSequence).length > 1 ? "," : ""}}&nbsp;{{ dict[store.currentSequence[1]] }}{{(store.currentSequence).length > 2 ? "," : ""}}&nbsp;{{ dict[store.currentSequence[2]] }}&nbsp;&nbsp;<span class="caret"></span>
        </button>
        <ul class="dropdown-menu">
          <li>
            <a class="dropdown-item text-capitalize" href="#" onclick="store.setSequence('ILC'); savePreferences();">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['L']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'LIC'; savePreferences();">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['I']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'CLI'; savePreferences();">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['L']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'ICL'; savePreferences();">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['C']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'LCI'; savePreferences();">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['C']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'CIL'; savePreferences();">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['I']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'IL'; savePreferences();">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'LI'; savePreferences();">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'IC'; savePreferences();">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'CI'; savePreferences();">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'LC'; savePreferences();">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" data-ng-click="sequence = 'CL'; savePreferences();">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
        </ul>
      </div>
      &nbsp;&nbsp;
      <div class="dropdown d-inline w-auto">
        <button :title="$t('Select panel measure')" class="dropdown-toggle form-control d-inline w-auto text-capitalize" id="selectmeasure" name="measure" :value="measure" type="button" data-bs-toggle="dropdown" aria-expanded="false">
          {{ store.measures[store.currentMeasure].label }}&nbsp;&nbsp;<span class="caret"></span>
        </button>
        <ul class="dropdown-menu">
          <li v-for="m in sortedMeasureList" :key="m.name" >
            <a v-if="!m.computed" href="#" class="dropdown-item text-capitalize" @click="store.setCurrentMeasure(m.name)">{{ m.label }}</a>
          </li>
        </ul>
      </div>
    </div>


  </div>
</div>
</template>

<style scoped>

</style>
