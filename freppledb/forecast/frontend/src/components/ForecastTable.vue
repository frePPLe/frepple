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
import {computed, onMounted, toRaw, watch} from 'vue';
import {useForecastsStore} from '../stores/forecastsStore.js';

// Store
const store = useForecastsStore();

const forecastdata = store.buckets;
const rows = store.preferences.rows;
const measures = store.measures;

// Reactive data
const currentYear = new Date().getFullYear();
const outlierString = 'Demand outlier'; // You might want to use i18n here

// Computed properties
const visibleBuckets = computed(() => {
  if (!forecastdata) return [];

  const currentBucketIndex = store.getBucketIndexFromName(store.currentBucketName) || 0;
  console.log(139, currentBucketIndex, forecastdata.length, store.currentBucketName, forecastdata[currentBucketIndex]);
  return forecastdata.slice(currentBucketIndex);
});

const preselectedIndexes = computed(() => {
  if (!forecastdata) return [];
  store.setPreselectedBucketIndexes();
  return store.preselectedBucketIndexes;
});

// Helper functions
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString();
};

const getBucket = (thisBucket, yearsAgo) => {
  if (!forecastdata?.[thisBucket]) return undefined;

  const bucket = forecastdata[thisBucket];
  const startDate = new Date(bucket.startdate);
  const endDate = new Date(bucket.enddate);

  // Get the date right in the middle between start and end date and subtract years
  const middleDate = new Date(
      Math.round(startDate.getTime() + (endDate.getTime() - startDate.getTime()) / 2.0) -
      (365 * 24 * 3600 * 1000 * yearsAgo)
  );

  for (const [index, forecastBucket] of forecastdata.entries()) {
    const bucketStart = new Date(forecastBucket.startdate);
    const bucketEnd = new Date(forecastBucket.enddate);

    if (middleDate >= bucketStart && middleDate < bucketEnd) {
      return index;
    }
  }

  return undefined;
};

const getBaseMeasureName = (measureName) => {
  return measureName.replace(/[123]ago$/, '');
};

const getCellData = (bucket, row) => {
  const measure = measures[row];
  if (!measure) return undefined;

  const bucketIndex = store.getBucketIndexFromName(bucket.bucket);

  let value, idx;

  // Handle historical measures (1ago, 2ago, 3ago)
  if (measure.name.includes('1ago')) {
    const years1ago = getBucket(bucketIndex, 1);
    if (years1ago >= 0 && forecastdata[years1ago]) {
      const baseMeasure = getBaseMeasureName(measure.name);
      value = forecastdata[years1ago][baseMeasure];
      idx = years1ago;
    }
  } else if (measure.name.includes('2ago')) {
    const years2ago = getBucket(bucketIndex, 2);
    if (years2ago >= 0 && forecastdata[years2ago]) {
      const baseMeasure = getBaseMeasureName(measure.name);
      value = forecastdata[years2ago][baseMeasure];
      idx = years2ago;
    }
  } else if (measure.name.includes('3ago')) {
    const years3ago = getBucket(bucketIndex, 3);
    if (years3ago >= 0 && forecastdata[years3ago]) {
      const baseMeasure = getBaseMeasureName(measure.name);
      value = forecastdata[years3ago][baseMeasure];
      idx = years3ago;
    }
  } else {
    // Current period measure
    value = bucket[row];
    idx = bucketIndex;
  }

  return {value, idx};
};

const onCellFocus = (bucketName, row) => {
  console.log(115, visibleBuckets.value, bucketName, row);
  const bucketIndex = store.getBucketIndexFromName(bucketName);
  store.setEditFormValues("startDate", new Date(forecastdata[bucketIndex].startdate).toISOString().split('T')[0]);
  store.setEditFormValues("endDate", new Date(forecastdata[bucketIndex].enddate).toISOString().split('T')[0]);
  store.setEditFormValues("selectedMeasure", measures[row]);
  store.setEditFormValues("mode", "set");
  store.setEditFormValues("setTo", forecastdata[bucketIndex][row]);

  store.setPreselectedBucketIndexes();
};

const getCellValue = (bucket, row) => {
  const cellData = getCellData(bucket, row, visibleBuckets.value.indexOf(bucket));
  return cellData?.value ?? null;
};

const formatCellValue = (value, measure) => {
  if (value === null || value === undefined) return '';

  if (measure.formatter === 'currency') {
    return `${grid.prefix || ''}${formatNumber(value, 2)}${grid.suffix || ''}`;
  }

  return formatNumber(value);
};

const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined) return '';
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

const isBacklogRow = (row) => row.includes('backlog');

const isOutlierBucket = (bucket) => bucket["outlier"] === 1;

const isEditCell = (bucketName, row) => {
  if (!store.editForm.selectedMeasure) return false;
  return preselectedIndexes.value.indexOf(store.getBucketIndexFromName(bucketName)) > -1 && row === store.editForm.selectedMeasure.name;
}

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
  if (!forecastdata?.attributes) return '#';

  const item = encodeURIComponent(forecastdata.attributes.item?.[0]?.[1] || 'All items');
  const location = encodeURIComponent(forecastdata.attributes.location?.[0]?.[1] || 'All locations');
  const customer = encodeURIComponent(forecastdata.attributes.customer?.[0]?.[1] || 'Generic customer');

  return `${window.url_prefix || ''}/forecast/demand/?noautofilter&item__name__ico=${item}&location__name__ico=${location}&customer__name__ico=${customer}&due__gte=${bucket.startdate}&due__lt=${bucket.enddate}`;
};

const updateCellValue = (bucket, row, event) => {
  const value = event.target.value;
  const bucketIndex = store.getBucketIndexFromName(bucket.bucket);
  store.setEditFormValues("mode", "set");
  store.setEditFormValues("setTo", value);
  store.applyForecastChanges();
  // const bucketIndex = visibleBuckets.value.indexOf(bucket);
  // const measure = getBaseMeasureName(row);
  // console.log(182, bucket, row, event.target.value);

  // Update the bucket data
  // if (bucketIndex >= 0 && forecastdata[bucketIndex]) {
  //   forecastdata[bucketIndex][measure] = value ? Number(value) : null;
  //
  //   // Mark bucket as changed in store
  //   store.bucketChanges[bucketIndex] = forecastdata[bucketIndex];
  //   store.hasChanges = true;
  // }
};

const navigateToDrilldown = (event) => {
  const href = event.target.closest('a')?.getAttribute('href');
  if (href) {
    window.location.href = href;
  }
};

const showOutlierTooltip = (event) => {
  // Handle outlier tooltip
  // You might want to implement tooltip functionality here
};

// Watch for data changes
watch(() => forecastdata, (newData) => {
  if (newData && typeof newData === 'object') {
    // Update grid settings if currency attributes are present
    if (newData.attributes?.hasOwnProperty('currency')) {
      // Handle currency formatting
    }
  }
}, {deep: true});

watch(() => grid?.setPristine, (newValue) => {
  if (newValue === true) {
    // Handle grid reset
    grid.setPristine = false;
  }
});

// Lifecycle
onMounted(() => {
  // Component mounted
});
</script>

<template>
  <div class="row mb-3">
    <div class="col-md-12">
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
              <tr v-for="(row, index) in rows" :key="index">
                <td v-if="measures[row].mode_future !== 'edit'"
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
              <tr v-for="(row, rowIndex) in rows" :key="rowIndex">
                <td v-for="(bucket, bucketIndex) in visibleBuckets" :key="bucketIndex">
                  <template v-if="getCellData(bucket, row, rowIndex) !== undefined">
                    <!-- Editable cell -->
                    <template v-if="measures[row].mode_future === 'edit'">
                      <input
                          :class="isEditCell(bucket.bucket, row) ? 'edit-cell' : ''"
                          class="smallpadding"
                          :data-index="bucketIndex"
                          :data-measure="getBaseMeasureName(row)"
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
                        <span v-if="isOutlierBucket(bucket)"
                              class="fa fa-warning text-danger"
                              :title="outlierString"
                              @mouseover="showOutlierTooltip">
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
