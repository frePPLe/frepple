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
import {computed, ref, onUnmounted, toRaw} from "vue";
import ForecastSelectionCard from "@/components/ForecastSelectionCard.vue";
import CustomizeGrid from "@/components/CustomizeGrid.vue";

const store = useForecastsStore();
const dict =  {'I':'item', 'L':'location', 'C':'customer'};

// Add reactive references for resizing
const resizableContainer = ref(null);
const resizeHandle = ref(null);
const isResizing = ref(false);

const customizeGridRef = ref(null);

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

const currentRows = computed(() => {
  if (store.tableRows === null) {
    store.tableRows = store.preferences.rows || [];
    return store.preferences.rows
  }
  return store.tableRows;
});

const favoriteNames = ref(Object.keys(store.preferences.favorites) || []);

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

// Button event handlers
const showBucket = (event) => window.grid.showBucket();

const showImportDialog = (event) => {
  // event.preventDefault();

  if (typeof window.url_prefix !== 'undefined') {
    window.url = window.url_prefix + '/forecast/';
  }
  window.import_show('', undefined, true);
};

const showCustomizeGrid = (event) => {
  event.preventDefault();
  if (customizeGridRef.value) {
    customizeGridRef.value.showModal();
  }
};

  // ?? AngularJS code for reference
  // function savefavorite() {
  //   if (!('favorites' in $scope.preferences))
  //     $scope.preferences['favorites'] = {};
  //   var favName = angular.element(document).find("#favoritename").val();
  //   $scope.preferences['favorites'][favName] = {
  //     'measure': $scope.measure,
  //     'sequence': $scope.sequence,
  //     'rows': $scope.rows
  //   };
  //   savePreferences();
  //   favorite.check();
  // }
  // $scope.savefavorite = savefavorite;

  // function removefavorite(f, $event) {
  //   delete $scope.preferences.favorites[f];
  //   savePreferences();
  //   $event.stopPropagation();
  // }
  // $scope.removefavorite = removefavorite;

  // function openfavorite(f, $event) {
  //   $scope.measure = $scope.preferences.favorites[f]['measure'];
  //   $scope.sequence = $scope.preferences.favorites[f]['sequence'];
  //   $scope.rows = $scope.preferences.favorites[f]['rows'];
  //   $scope.grid.setPristine = true;
  // }
  // $scope.openfavorite = openfavorite;


const saveFavorite = (event) => {
  if (!('favorites' in store.preferences))
    store.preferences['favorites'] = {};
  const favName = document.querySelector("#favoritename").value;
  if (favName === '') return;
  console.log(123, favName, event);
  store.preferences['favorites'][favName] = {
    'measure': store.currentMeasure,
    'sequence': store.currentSequence,
    'rows': toRaw(store.tableRows)
  };
  store.savePreferences();
  window.favorite.check();
  favoriteNames.value.push(favName);
};

const openFavorite = (favName, event) => {
  console.log(136, favName);
  // event.preventDefault();
  if (!(favName in store.preferences.favorites)) return;
  const currentMeasure = store.preferences.favorites[favName]['measure'];
  const currentSequence = store.preferences.favorites[favName]['sequence'];
  const rows = store.preferences.favorites[favName]['rows'];
  store.setCurrentMeasure(currentMeasure);
  store.setCurrentSequence(currentSequence);
  store.tableRows = rows;
};

const removeFavorite = (favname, event) => {
  // event.preventDefault();
  delete store.preferences.favorites[favname];
  store.savePreferences();
  favoriteNames.value = favoriteNames.value.filter(f => f !== favname);
};

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
    <div class="row mb-1">
      <div class="col-auto">
        <div class="dropdown d-inline w-auto">
          <button id="selectseq" :title="$t('Select panel sequence')" class="form-control d-inline w-auto dropdown-toggle text-capitalize" name="sequence" type="button" data-bs-toggle="dropdown" aria-expanded="false">
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
        <div class="dropdown d-inline w-auto ">
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

      <div id="toolicons" class="col-auto ms-auto hor-align-right ver-align-middle">
        <div>
          <button
              type="button"
              class="btn btn-sm btn-primary me-1"
              @click="showBucket"
              data-bs-toggle="tooltip"
              data-bs-placement="top"
              title="set time horizon">
            <span class="fa fa-clock-o"></span>
          </button>
          <button
              type="button"
              class="btn btn-sm btn-primary me-1"
              data-bs-toggle="dropdown"
              aria-haspopup="true"
              aria-expanded="false">
            <div data-bs-toggle="tooltip" data-bs-placement="top" data-bs-html="true"
                 data-bs-title="Bookmark your favorite report configurations">
              <span class="fa fa-star"></span>
            </div>
          </button>
          <ul class="dropdown-menu dropdown-menu-end" id="favoritelist">
            <li v-for="favname in favoriteNames" :key="favname">
              <a class="dropdown-item" @click="openFavorite(favname, $event)">{{favname}}
                <div style="float:right"><span class="fa fa-trash-o" @click="removeFavorite(favname, $event)"></span></div>
              </a>
            </li>
            <li>
              <a class="dropdown-item d-flex" >
                <button
                    id="favoritesave"
                    @click="saveFavorite($event)"
                    type="button"
                    class="flex-fill btn btn-primary btn-sm me-1 text-capitalize">save</button>
                <input
                    class="form-control form-control-sm"
                    id="favoritename"
                    @input="checkFavorite"
                    type="text"
                    size="15">
              </a>
            </li>
          </ul>
          <button
              type="button"
              class="btn btn-sm d-none d-md-inline-block btn-primary me-1"
              @click="showImportDialog"
              data-bs-toggle="tooltip"
              data-bs-placement="top"
              title="Import CSV or Excel file">
            <span id="csvimport" class="fa fa-arrow-up"></span>
          </button>
          <button
              type="button"
              class="btn btn-sm btn-primary me-1"
              @click="showCustomizeGrid"
              data-bs-toggle="tooltip"
              data-bs-placement="top"
              data-bs-title="Customize">
            <span class="fa fa-wrench"></span>
          </button>
        </div>
      </div>
    </div>

    <div class="row resizable" v-if="currentSequence && currentMeasure && currentHeight" id="data-row" style="max-height: 50vh; min-height: 150px;" :style="{'height': (currentHeight-31) + 'px'}"
          ref="resizableContainer">
      <div :class="{'col-sm-12': currentSequence.length === 1, 'col-sm-6': currentSequence.length === 2, 'col-sm-4': currentSequence.length === 3}" v-for="panel in currentSequence" :key="panel">
        <div>
          <ForecastSelectionCard v-if="panel" :panelid="panel" />
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
    <CustomizeGrid ref="customizeGridRef" />
  </div>
</template>