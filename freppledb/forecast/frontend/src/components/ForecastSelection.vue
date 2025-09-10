<script setup lang="js">
import { useForecastsStore } from '@/stores/forecastsStore';
import {computed} from "vue";

const store = useForecastsStore();
const dict =  {'I':'item', 'L':'location', 'C':'customer'};

const currentSequence = computed(() => {
  if (store.currentSequence === null) {
    return store.preferences.sequence || 'ILC'
  }
  return store.currentSequence;
});

const measure = computed(() => {
  return store.currentMeasure;
})

console.log("ForecastSelection.vue");
console.log(currentSequence);
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
        <button id="selectseq" bs-title="{{t('Select panel sequence')}}" class="form-control d-inline w-auto dropdown-toggle text-capitalize" name="sequence" type="button" data-bs-toggle="dropdown" aria-expanded="false">
<!--          {{ $t(dict[currentSequence[0]]) }}{{(currentSequence).length > 1 ? "," : ""}}&nbsp;{{ $t(dict[currentSequence[1]]) }}{{(currentSequence).length > 2 ? "," : ""}}&nbsp;{{ $t(dict[currentSequence[2]]) }}&nbsp;&nbsp;<span class="caret"></span>-->
          {{ dict[currentSequence[0]] }}{{(currentSequence).length > 1 ? "," : ""}}&nbsp;{{ dict[currentSequence[1]] }}{{(currentSequence).length > 2 ? "," : ""}}&nbsp;{{ dict[currentSequence[2]] }}&nbsp;&nbsp;<span class="caret"></span>
        </button>
        <ul class="dropdown-menu">
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('ILC')">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['L']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('LIC')">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['I']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('CLI')">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['L']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('ICL')">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['C']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('LCI')">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['C']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('CIL')">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['I']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('IL')">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('LI')">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('IC')">{{ $t(dict['I']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('CI')">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['I']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('LC')">{{ $t(dict['L']) }},&nbsp;{{ $t(dict['C']) }}</a>
          </li>
          <li>
            <a class="dropdown-item text-capitalize" href="#" v-on:click="store.setCurrentSequence('CL')">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['L']) }}</a>
          </li>
        </ul>
      </div>
      &nbsp;&nbsp;
      <div class="dropdown d-inline w-auto">
        <button id="selectmeasure" :title="$t('Select panel measure')" class="dropdown-toggle form-control d-inline w-auto text-capitalize" name="measure" :value="measure" type="button" data-bs-toggle="dropdown" aria-expanded="false">
          {{ store.measures[store.currentMeasure].label }}&nbsp;&nbsp;<span class="caret"></span>
        </button>
        <ul class="dropdown-menu">
          <li v-for="m in sortedMeasureList" :key="m.name" >
            <a v-if="!m.computed" href="#" class="dropdown-item text-capitalize" @click="store.setCurrentMeasure(m.name)">{{ m.label }}</a>
          </li>
        </ul>
      </div>
    </div>

    <div class="row resizable" id="data-row" :style="{'max-height': '50vh', 'height': datarowheight + 'px', 'min-height': '150px'}" style="max-height: 50vh; height: 240px; min-height: 150px;">
      <div class="col-sm-4" v-for="panel in currentSequence" :key="panel" style="height: 100%">
        <div>panel - {{ panel }}</div>
        {{ panel === 'I' ? store.itemTree : panel === 'L' ? store.locationTree : store.customerTree}}


    </div><!-- end ngRepeat: panel in sequence track by $index -->
    </div>


  </div>
</div>
</template>

<style scoped>

</style>
