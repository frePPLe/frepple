<script setup lang="js">
import { useForecastsStore } from '@/stores/forecastsStore';
import {computed} from "vue";
import ForecastSelectionCard from "@/components/ForecastSelectionCard.vue";

const store = useForecastsStore();
const dict =  {'I':'item', 'L':'location', 'C':'customer'};

const currentMeasure = computed(() => {
  if (store.currentMeasure === null) {
    store.setCurrentMeasure(store.preferences.measure || 'nodata', false);
    console.log(19, store.preferences.measure, ' measures: ',store.measures);
    return store.preferences.measure || 'nodata'
  }
  return store.currentMeasure;
});

const currentSequence = computed(() => {
  if (store.currentSequence === null) {
    store.setCurrentSequence(store.preferences.sequence || 'ILC', false);
    return store.preferences.sequence || 'ILC'
  }
  return store.currentSequence;
});

const currentHeight = computed(() => {
  if (store.dataRowHeight === null) {
    store.setCurrentHeight(store.preferences.height || 'ILC', false);
    return store.preferences.height || 400
  }
  return store.dataRowHeight;
});
console.log(29,"ForecastSelection.vue");
console.log(30,currentSequence);
console.log(31,store.measures);
console.log(32,store.preferences);
console.log(33,store.currentMeasure);
console.log(34,currentHeight);

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
          {{ store.measures[currentMeasure].label }}&nbsp;&nbsp;<span class="caret"></span>
        </button>
        <ul class="dropdown-menu">
          <li v-for="m in sortedMeasureList" :key="m.name" >
            <a v-if="!m.computed" href="#" class="dropdown-item text-capitalize" @click="store.setCurrentMeasure(m.name)">{{ m.label }}</a>
          </li>
        </ul>
      </div>
    </div>

    <div v-if="currentSequence && currentMeasure && currentHeight" class="row resizable" id="data-row" :style="{'max-height': '50vh', 'height': currentHeight + 'px', 'min-height': '150px'}" style="max-height: 50vh; height: 240px; min-height: 150px;">
      <div class="col-sm-4" v-for="panel in currentSequence" :key="panel" style="height: 100%">
        <div>panel - {{ panel }} / measure {{ currentMeasure }} / buckets {{ store.treeBuckets }}
<!--          {{ panel === 'I' ? store.itemTree : panel === 'L' ? store.locationTree : store.customerTree}}-->
          <ForecastSelectionCard v-if="panel" :panelid="panel" />
        </div>

      </div>
    </div>


  </div>
</div>
</template>

<style scoped>

</style>
