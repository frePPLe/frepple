/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

<script setup>
import {computed, nextTick, watch} from 'vue';
import {useI18n} from 'vue-i18n';
import {useForecastsStore} from '../stores/forecastsStore.js';

const { t: ttt, locale, availableLocales } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});

const store = useForecastsStore();

const formatNumber = window.grid.formatNumber;

const forecastData = computed(() => store.buckets);
const measures = store.measures;

const outlierString = ttt('Demand outlier');

// Computed properties
const visibleBuckets = computed(() => {
  if (!forecastData.value) return [];

  const currentBucketIndex = store.getBucketIndexFromName(store.currentBucketName) || 0;
  return forecastData.value.slice(currentBucketIndex);
});

const preselectedIndexes = computed(() => {
  if (!forecastData.value) return [];
  store.setPreselectedBucketIndexes();
  return store.preselectedBucketIndexes;
});

// Helper functions
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

const getCellData = (bucket, row) => {
  const measure = measures[row];
  if (!measure) return undefined;

  const bucketIndex = store.getBucketIndexFromName(bucket.bucket);

  let value, idx, outlier;

  // Handle historical measures (1 year ago, 2 years ago, 3 years ago)
  if (measure.name.endsWith('1ago')) {
    const years1ago = store.getBucket(bucketIndex, 1);
    if (years1ago >= 0 && forecastData.value[years1ago]) {
      const baseMeasure = store.getBaseMeasureName(measure.name);
      value = forecastData.value[years1ago][baseMeasure];
      idx = years1ago;
      outlier = forecastData.value[years1ago]['outlier'];
    }
  } else if (measure.name.endsWith('2ago')) {
    const years2ago = store.getBucket(bucketIndex, 2);
    if (years2ago >= 0 && forecastData.value[years2ago]) {
      const baseMeasure = store.getBaseMeasureName(measure.name);
      value = forecastData.value[years2ago][baseMeasure];
      idx = years2ago;
      outlier = forecastData.value[years2ago]['outlier'];
    }
  } else if (measure.name.endsWith('3ago')) {
    const years3ago = store.getBucket(bucketIndex, 3);
    if (years3ago >= 0 && forecastData.value[years3ago]) {
      const baseMeasure = store.getBaseMeasureName(measure.name);
      value = forecastData.value[years3ago][baseMeasure];
      idx = years3ago;
      outlier = forecastData.value[years3ago]['outlier'];
    }
  } else {
    value = bucket[row];
    idx = bucketIndex;
    outlier = bucket['outlier'];
  }

  return {value, idx, outlier};
};

const onCellFocus = (bucketName, row) => {
  const bucketIndex = store.getBucketIndexFromName(bucketName);
  store.setEditFormValues("startDate", forecastData.value[bucketIndex].startdate.split(' ')[0]);
  store.setEditFormValues("endDate", forecastData.value[bucketIndex].enddate.split(' ')[0]);
  store.setEditFormValues("selectedMeasure", measures[row]);
  store.setEditFormValues("mode", "set");
  store.setEditFormValues("setTo", forecastData.value[bucketIndex][row]);

  store.setPreselectedBucketIndexes();
};

const getCellValue = (bucket, row) => {
  if (isDirtyCell(bucket.bucket, row)) return store.bucketChanges[store.getBucketIndexFromName(bucket.bucket)][row];
  const cellData = getCellData(bucket, row, visibleBuckets.value.indexOf(bucket));
  return cellData?.value ?? null;
};

const formatCellValue = (value, measure) => {
  if (value === null || value === undefined) return '';

  if (measure.formatter === 'currency') {
    return `${store.currency[0] || ''}${formatNumber(value, 0)}${store.currency[1] || ''}`;
  }

  return formatNumber(value);
};

const isBacklogRow = (row) => row.includes('backlog');

const isOutlierBucket = (bucket, row) => {
  const cellData = getCellData(bucket, row, visibleBuckets.value.indexOf(bucket));
  return cellData.outlier === 1;
};

const isEditCell = (bucketName, row) => {
  if (!store.editForm.selectedMeasure) return false;
  return preselectedIndexes.value.indexOf(store.getBucketIndexFromName(bucketName)) > -1 && row === store.editForm.selectedMeasure.name;
};

const isDirtyCell = (bucketName, row) => {
  if (!store.editForm.selectedMeasure) return false;
  const bucketIndex = store.getBucketIndexFromName(bucketName).toString();

  return Object.keys(store.bucketChanges).includes(bucketIndex) && store.bucketChanges[bucketIndex][row] !== undefined;
};

const shouldShowDrilldownLink = (row, bucket) => {
  const value = getCellValue(bucket, row);
  if (!value || value === 0) return false;

  const drilldownMeasures = [
    'ordersopen', 'ordersopenvalue', 'orderstotal', 'orderstotalvalue',
    'orderstotal1ago', 'orderstotalvalue1ago',
    'orderstotal2ago', 'orderstotalvalue2ago',
    'orderstotal3ago', 'orderstotalvalue3ago'
  ];

  return drilldownMeasures.includes(measures[row]?.name);
};

const getDrilldownUrl = (row, bucket) => {
  if (!forecastData.value) return '#';

  const item = encodeURIComponent(store.item.Name || 'All items');
  const location = encodeURIComponent(store.location.Name || 'All locations');
  const customer = encodeURIComponent(store.customer.Name || 'Generic customer');

  let startdate = bucket.startdate.split("-");
  let enddate = bucket.enddate.split("-");
  if (row.endsWith('1ago')) {
    startdate[0] = parseInt(startdate[0]) - 1;
    enddate[0] = parseInt(enddate[0]) - 1;
  } else if (row.endsWith('2ago')) {
    startdate[0] = parseInt(startdate[0]) - 2;
    enddate[0] = parseInt(enddate[0]) - 2;
  } else if (row.endsWith('3ago')) {
    startdate[0] = parseInt(startdate[0]) - 3;
    enddate[0] = parseInt(enddate[0]) - 3;
  }
  startdate = startdate.join("-");
  enddate = enddate.join("-");
  return `${window.url_prefix || ''}/forecast/demand/?noautofilter&item__name__ico=${item}&location__name__ico=${location}&customer__name__ico=${customer}&due__gte=${startdate}&due__lt=${enddate}`;
};

import { debouncedInputHandler } from "@common/utils.js";

const updateCellValueDebounced = debouncedInputHandler((bucket, row, value) => {
  store.setEditFormValues("mode", "set");
  store.setEditFormValues("setTo", value);
  store.applyForecastChanges();
}, 300);

const updateCellValue = (bucket, row, event) => {
  const value = event.target.value;
  updateCellValueDebounced(bucket, row, value);
};

// Add this watcher to force input field updates when bucketChanges are updated
watch(() => JSON.stringify(store.bucketChanges), () => {
  // Force Vue to update the DOM for all affected inputs
  nextTick(() => {
    const inputs = document.querySelectorAll('input.ng-dirty');
    inputs.forEach(input => {
      const bucketIndex = input.getAttribute('data-index');
      const measure = input.getAttribute('data-measure');
      if (bucketIndex && measure &&
          store.bucketChanges[store.getBucketIndexFromName(visibleBuckets.value[bucketIndex].bucket)]) {
        input.value = store.bucketChanges[store.getBucketIndexFromName(visibleBuckets.value[bucketIndex].bucket)][measure] || input.value;
      }
    });
  });
});

const navigateToDrilldown = (event) => {
  const href = event.target.closest('a')?.getAttribute('href');
  if (href) {
    window.location.href = href;
  }
};

</script>

<template>
  <div class="row mb-3">
    <div class="col">
      <div class="panel" id="forecastgrid" style="background-color: transparent;">
        <div class="forecast-grid-container">
          <!-- Row labels table -->
          <div class="pull-left" style="border-top-left-radius: 6px; border-bottom-left-radius: 6px;">
            <table class="table-sm table-hover" id="forecasttabletags">
              <thead class="thead-default">
              <tr>
                <th style="background-color: #aaa; border-top-left-radius: 6px">&nbsp;</th>
              </tr>
              </thead>
              <tbody>
              <tr v-for="row in store.tableRows" :key="row">
                <td v-if="measures[row]['mode_future'] !== 'edit'"
                    style="white-space: nowrap; text-transform: capitalize;">
                  {{ measures[row].label || row }}
                </td>
                <td v-else style="white-space: nowrap; text-transform: capitalize;">
                  {{ measures[row].label || row }}
                  <input style="width: 0" class="invisible">
                </td>
              </tr>
              </tbody>
            </table>
          </div>

          <!-- Data table -->
          <form
              id="forecasttable"
              name="forecasttable"
              style="overflow-x: scroll; border-top-right-radius: 6px; border-bottom-right-radius: 6px;"
          >
            <table class="table-sm table-hover" id="fforecasttable">
              <thead class="thead-default" id="fforecasttablehead">
              <tr id="row0">
                <th
                    v-for="(bucket, bucketIndex) in visibleBuckets"
                    :key="bucketIndex"
                    class="text-center text-nowrap"
                    style="background-color: #aaa"
                    :title="`${formatDate(bucket.startdate)} - ${formatDate(bucket.enddate)}`"
                >
                  {{ bucket.bucket }}
                </th>
              </tr>
              </thead>
              <tbody id="forecasttablebody">
              <tr v-for="(row, rowIndex) in store.tableRows" :key="rowIndex">
                <td v-for="(bucket, bucketIndex) in visibleBuckets" :key="bucketIndex">
                  <template v-if="getCellData(bucket, row, rowIndex) !== undefined">
                    <!-- Editable cell -->
                    <template v-if="measures[row].mode_future === 'edit'">
                      <input
                          :class="{'edit-cell' : isEditCell(bucket.bucket, row), 'ng-dirty': isDirtyCell(bucket.bucket, row)}"
                          class="smallpadding"
                          :data-index="bucketIndex"
                          :data-measure="store.getBaseMeasureName(row)"
                          type="number"
                          :value="getCellValue(bucket, row)"
                          :tabindex="rowIndex"
                          @input="updateCellValue(bucket, row, $event)"
                          @focus="onCellFocus(bucket.bucket, row)"
                      >
                      <br>
                    </template>
                    <!-- Read-only cell -->
                    <template v-else>
                      <div class="text-center text-nowrap">
                        <span v-if="isBacklogRow(row) && getCellValue(bucket, row) > 0" class="red">
                          {{ formatCellValue(getCellValue(bucket, row), measures[row]) }}
                        </span>
                        <span v-else>
                            {{ formatCellValue(getCellValue(bucket, row), measures[row]) }}
                        </span>

                        <!-- Drilldown links -->
                        <a v-if="shouldShowDrilldownLink(row, bucket)"
                           :href="getDrilldownUrl(row, bucket)"
                           @click.prevent.stop="navigateToDrilldown">
                          <span class="ps-1 fa fa-caret-right"></span>
                        </a>

                        <!-- Outlier warning -->
                        <span v-if="isOutlierBucket(bucket, row)"
                              class="fa fa-warning text-danger"
                              :title="outlierString"
                              data-bs-toggle="tooltip">
                          </span>
                      </div>
                    </template>
                  </template>
                  <template v-else>
                    <!-- Empty cell -->
                  </template>
                </td>
              </tr>
              </tbody>
            </table>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
