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
import { useForecastsStore } from '@/stores/forecastsStore';
import {computed, ref, onUnmounted} from "vue";
import ForecastSelectionCard from "@/components/ForecastSelectionCard.vue";

const store = useForecastsStore();
const dict =  {'I':'item', 'L':'location', 'C':'customer'};

// Add reactive references for resizing
const resizableContainer = ref(null);
const resizeHandle = ref(null);
const isResizing = ref(false);

const currentMeasure = computed(() => {
  if (store.currentMeasure === null) {
    store.setCurrentMeasure(store.preferences.measure || 'nodata', false);
    // console.log(19, store.preferences.measure, ' measures: ',store.measures);
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
    store.setCurrentHeight(store.preferences.height || 240);
    return store.preferences.height || 240
  }
  return store.dataRowHeight;
});

// console.log(29,"ForecastSelection.vue");
// console.log(30,currentSequence);
// console.log(31,store.measures);
// console.log(32,store.preferences);
// console.log(33,store.currentMeasure);
// console.log(34,currentHeight);

const sortedMeasureList = computed(() => {
  return Object.values(store.measures).sort((a, b) => {
    return a.label.localeCompare(b.label);
  });
});

// Resize functionality - now updates store dataRowHeight
const startResize = (e) => {
  if (!resizableContainer.value) return;

  isResizing.value = true;
  const startY = e.clientY;
  const startHeight = currentHeight.value; // Use store height instead of container height

  const onMouseMove = (e) => {
    if (!isResizing.value) return;

    const deltaY = e.clientY - startY;
    const newHeight = startHeight + deltaY;

    // Set height constraints
    const minHeight = 150;
    const maxHeight = window.innerHeight * 0.8;

    if (newHeight >= minHeight && newHeight <= maxHeight) {
      // Update store dataRowHeight instead of local containerHeight
      store.setCurrentHeight(newHeight);
    }
  };

  const onMouseUp = () => {
    isResizing.value = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
    document.body.style.userSelect = '';
    document.body.style.cursor = '';

    // Optionally save preferences after resize is complete
    store.savePreferences();
  };

  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
  document.body.style.userSelect = 'none';
  document.body.style.cursor = 'ns-resize';

  e.preventDefault();
};

// Cleanup on component unmount
onUnmounted(() => {
  document.body.style.userSelect = '';
  document.body.style.cursor = '';
});
</script>

<template>
  <div>
    <div
      class="row mb-1"
    >
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
              <a class="dropdown-ite text-capitalize" href="#" v-on:click="store.setCurrentSequence('CIL')">{{ $t(dict['C']) }},&nbsp;{{ $t(dict['I']) }},&nbsp;{{ $t(dict['L']) }}</a>
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

      <div v-if="currentSequence && currentMeasure && currentHeight" class="row resizable" id="data-row" style="max-height: 50vh; min-height: 150px;" :style="{'height': (currentHeight-31) + 'px'}"
           ref="resizableContainer">
        <div class="col-sm-4" v-for="panel in currentSequence" :key="panel">
          <div>
            <ForecastSelectionCard v-if="panel" :panelid="panel" />
          </div>

        </div>
      </div>
    </div>
    <div class="row">
      <div
        id="resize-handle"
        ref="resizeHandle"
        class="fa fa-bars handle col"
        style="display: block; text-align: center; clear: both; touch-action: none;"
        @mousedown="startResize"
      ></div>
    </div>
  </div>
</template>
