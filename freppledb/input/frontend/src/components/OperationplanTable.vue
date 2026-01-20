<template>
  <div class="container mt-4">
    <h2>{{ ttt('Operation Plans') }}</h2>

    <!-- jqGrid container - ensure it has the proper structure -->
    <div class="jqgrid-container">
      <table id="operationplanGrid" ref="gridContainer"></table>
      <div id="operationplanPager" ref="pagerContainer"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '../stores/operationplansStore.js';

const { t: ttt } = useI18n();

const gridContainer = ref(null);
const pagerContainer = ref(null);
const operationplansStore = useOperationplansStore();

// Define jqGrid options
const gridOptions = {
  datatype: 'local',
  colModel: [
    { label: ttt('ID'), name: 'id', width: 80 },
    { label: ttt('Operation'), name: 'operation', width: 150 },
    { label: ttt('Quantity'), name: 'quantity', width: 100 },
    { label: ttt('Status'), name: 'status', width: 100 },
    { label: ttt('Start Date'), name: 'startdate', width: 120 },
    { label: ttt('End Date'), name: 'enddate', width: 120 }
  ],
  width: '100%',
  height: 'auto',
  rowNum: 10,
  rowList: [10, 20, 30],
  pager: '#operationplanPager',
  viewrecords: true,
  caption: ttt('Operation Plans'),
  gridview: true,
  autoencode: true,
  loadComplete: function () {
    // Optional: Add any post-loading logic here
  }
};

// Initialize grid when component mounts
onMounted(() => {
  nextTick(() => {
    if (gridContainer.value) {
      // Use window.jQuery if available, otherwise load it dynamically
      const jq = window.jQuery || window.$;

      if (jq) {
        // Initialize jqGrid using the global jQuery
        jq(gridContainer.value).jqGrid(gridOptions);

        // Load data from store
        const gridData = operationplansStore.operationplans.map(plan => ({
          id: plan.id,
          operation: plan.operation,
          quantity: plan.quantity,
          status: plan.status,
          startdate: plan.startdate,
          enddate: plan.enddate
        }));

        jq(gridContainer.value).jqGrid('clearGridData').jqGrid('addRowData', 1, gridData);
      } else {
        console.error('jQuery is not available. Please ensure it is loaded before initializing jqGrid.');
      }
    }
  });
});

// Clean up when component unmounts
onBeforeUnmount(() => {
  if (gridContainer.value) {
    const jq = window.jQuery || window.$;
    if (jq) {
      jq(gridContainer.value).jqGrid('GridUnload');
    }
  }
});

// Watch for changes in operation plans
watch(
    () => operationplansStore.operationplans,
    (newPlans) => {
      if (gridContainer.value) {
        const jq = window.jQuery || window.$;
        if (jq) {
          const gridData = newPlans.map(plan => ({
            id: plan.id,
            operation: plan.operation,
            quantity: plan.quantity,
            status: plan.status,
            startdate: plan.startdate,
            enddate: plan.enddate
          }));

          jq(gridContainer.value).jqGrid('clearGridData').jqGrid('addRowData', 1, gridData);
        }
      }
    },
    { deep: true }
);
</script>
