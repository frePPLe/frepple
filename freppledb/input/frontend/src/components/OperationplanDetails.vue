/* * Copyright (C) 2025 by frePPLe bv * * Permission is hereby granted, free of charge, to any
person obtaining * a copy of this software and associated documentation files (the * "Software"), to
deal in the Software without restriction, including * without limitation the rights to use, copy,
modify, merge, publish, * distribute, sublicense, and/or sell copies of the Software, and to *
permit persons to whom the Software is furnished to do so, subject to * the following conditions: *
* The above copyright notice and this permission notice shall be * included in all copies or
substantial portions of the Software. * * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
KIND, * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF * MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION * OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION * WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE */

<script setup lang="js">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@/stores/operationplansStore.js';
import OperationplanFormCard from '@/components/OperationplanFormCard.vue';
import InventoryGraphCard from '@/components/InventoryGraphCard.vue';
import InventoryDataCard from '@/components/InventoryDataCard.vue';
import ProblemsCard from '@/components/ProblemsCard.vue';
import ResourcesCard from '@/components/ResourcesCard.vue';
import BuffersCard from '@/components/BuffersCard.vue';
import DemandPeggingCard from '@/components/DemandPeggingCard.vue';
import NetworkStatusCard from '@/components/NetworkStatusCard.vue';
import DownstreamCard from '@/components/DownstreamCard.vue';
import UpstreamCard from '@/components/UpstreamCard.vue';
import SupplyInformationCard from '@/components/SupplyInformationCard.vue';
import { debounce } from '@common/utils.js';

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const appElement = ref(null);
const store = useOperationplansStore();

// Use shared debouncer to throttle grid cell edits applied to the store
const applyGridCellEditDebounced = debounce((payload) => {
  try {
    store.applyGridCellEdit(payload);
  } catch (err) {
    console.warn('Debounced applyGridCellEdit failed', err);
  }
}, 10);

// const database = computed(() => window.database);
const preferences = computed(() => window.preferences || {});

const databaseerrormodal = ref(false);
const rowlimiterrormodal = ref(false);
const modalcallback = ref({ resolve: () => {} });

function save() {
  if (store.hasChanges) {
    store.saveOperationplanChanges().catch((error) => {
      console.error('Failed to save operation plan:', error);
      // Show error notification to user
      store.error = {
        title: 'Save Failed',
        showError: true,
        message: 'There was an error saving your changes.',
        details: error.message || 'Unknown error',
        type: 'error',
      };
    });
  }
}

// Enhanced undo method
function undo() {
  if (store.hasChanges) {
    store.undo();
  }
}

function getWidgetComponent(widgetName) {
  const componentMap = {
    operationplan: OperationplanFormCard,
    inventorygraph: InventoryGraphCard,
    inventorydata: InventoryDataCard,
    operationproblems: ProblemsCard,
    operationresources: ResourcesCard,
    operationflowplans: BuffersCard,
    operationdemandpegging: DemandPeggingCard,
    networkstatus: NetworkStatusCard,
    downstreamoperationplans: DownstreamCard,
    upstreamoperationplans: UpstreamCard,
    supplyinformation: SupplyInformationCard,
  };
  return componentMap[widgetName] || null;
}

function shouldShowWidget(widgetName) {
  if (!store.operationplan || store.operationplan.id === '-1') return false;

  const widgetConditions = {
    operationplan: () => true,
    inventorygraph: () => store.operationplan.inventoryreport !== undefined,
    inventorydata: () => store.operationplan.inventoryreport !== undefined,
    operationproblems: () =>
      store.operationplan.problems !== undefined || store.operationplan.info !== undefined,
    operationresources: () => store.operationplan.loadplans !== undefined,
    operationflowplans: () => store.operationplan.flowplans !== undefined,
    operationdemandpegging: () => store.operationplan.pegging_demand !== undefined,
    networkstatus: () => store.operationplan.network !== undefined,
    downstreamoperationplans: () => store.operationplan.downstreamoperationplans !== undefined,
    upstreamoperationplans: () => store.operationplan.upstreamoperationplans !== undefined,
    supplyinformation: () => store.operationplan !== undefined,
  };

  return (
    widgetName === 'operationplan' ||
    (widgetConditions[widgetName] && widgetConditions[widgetName]())
  );
}

onMounted(() => {

  const getGridRowData = (id) => {
    try {
      return window.jQuery('#grid').getRowData(id);
    } catch (err) {
      console.log('Cannot get row data for id ', id, ': ', err);
    }
    return null;
  };

  const handleSingleSelectEvent = (e) => {
    const detail = e?.detail || {};
    if (detail.execute === 'displayInfo') {
      if (detail.selectedRows.length === 0) {
        store.undo();
      } else if (detail.selectedRows.length > 1) {
        handleAllSelectEvent(e, true);
      } else if (detail.selectedRows.length < 2) {
        store.loadOperationplans([detail.reference], detail.status, detail.selectedRows, window.savedData);
      }
    } else {
      store.undo();
    }
    // Update toolbar buttons depending on selection visible on the current page
    // try {
    //   const sel = window.jQuery('#grid').jqGrid('getGridParam', 'selarrrow') || [];
    //   const selectedIds = sel.map((x) => (x && typeof x === 'object') ? (x.id || x.operationplan__reference || String(x)) : String(x));
    //   const visibleIds = (window.jQuery('#grid').jqGrid && window.jQuery('#grid').jqGrid('getDataIDs')) || [];
    //   const hasVisibleSelection = selectedIds.filter((id) => id !== 'cb' && visibleIds.includes(id)).length > 0;
    //   updateActionsToolsButtons(!hasVisibleSelection);
    // } catch (err) { /* no-op */ }
  };

  const handleAllSelectEvent = (e, isSingleSelect) => {
    const detail = e?.detail || {};
    if (detail.status === false && !isSingleSelect) {
      store.undo();
      return;
    }
    const ids = detail.selectedRows || [];
    const selectiondata = [];
    try {
      for (const id of ids) {
        const row = getGridRowData(id);
        if (row) selectiondata.push(row);
      }
      const colModel = window.jQuery('#grid').jqGrid
        ? window.jQuery('#grid').jqGrid('getGridParam', 'colModel')
        : undefined;
      store.processAggregatedInfo(selectiondata, colModel);
    } catch (err) {
      console.error('Error in All Select Event Handler', err);
    }
  };

  const handleProcessAggregatedInfo = (e) => {
    const detail = e?.detail || {};
    if (detail.selectiondata) {
      store.processAggregatedInfo(detail.selectiondata, detail.colModel);
    }
  };

  const handleTriggerSave = (e) => {
    store.undo();
  };

  const handleDisplayOnPanel = (e) => {
    // This event may carry either { rowid, reference, field, value }
    const detail = e?.detail;
    if (!detail) return;

    // If the event contains an inline field/value edit, apply it to the current operationplan immediately
    if (detail.field && typeof detail.value !== 'undefined') {
      try {
        // Use shared debouncer to avoid flooding updates while typing in grid inline editors
        applyGridCellEditDebounced({
          reference: detail.reference,
          field: detail.field,
          value: detail.value,
        });
        window.isDataSaved = false;
      } catch (err) {
        console.warn('Failed to apply grid cell edit from displayonpanel event', err);
      }
    }
  };

  const handleUndoEvent = (e) => {
    const detail = e?.detail || {};
    if (detail.execute === 'undo') {
      store.undo();
    }
  };

  const handleGridCellEdited = (e) => {
    const detail = e?.detail || {};
    if (!detail.field) return;

    store.applyGridCellEdit({
      reference: detail.reference,
      field: detail.field,
      value: detail.value,
    });
  };

  const handleRefreshStatus = (e) => {
    const detail = e?.detail || {};
    if (!detail.status) return;

    store.setStatus(detail.status);
  };

  // Attach listeners on the app root element if present, otherwise on document
  const rootEl = document.getElementById('app') || document;
  rootEl.addEventListener('singleSelect', handleSingleSelectEvent);
  rootEl.addEventListener('allSelect', handleAllSelectEvent);
  rootEl.addEventListener('processAggregatedInfo', handleProcessAggregatedInfo);
  rootEl.addEventListener('displayonpanel', handleDisplayOnPanel);
  rootEl.addEventListener('triggerSave', handleTriggerSave);
  rootEl.addEventListener('gridCellEdited', handleGridCellEdited);
  rootEl.addEventListener('refreshStatus', handleRefreshStatus);
  rootEl.addEventListener('hidden.bs.collapse', grid.saveColumnConfiguration);
  rootEl.addEventListener('shown.bs.collapse', grid.saveColumnConfiguration);

  // Save references to handlers so they can be removed on unmount
  appElement.value = {
    rootEl,
    handlers: {
      single: handleSingleSelectEvent,
      all: handleAllSelectEvent,
      proc: handleProcessAggregatedInfo,
      display: handleDisplayOnPanel,
      undo: handleUndoEvent,
      gridCellEdited: handleGridCellEdited,
      refreshStatus: handleRefreshStatus,
    },
  };

  widget.init(grid.saveColumnConfiguration);
});

onUnmounted(() => {
  const info = appElement.value;
  // if (stopNoVisibleSelectionWatch) stopNoSelectionWatch();
  if (info && info.rootEl && info.handlers) {
    try {
      info.rootEl.removeEventListener('singleSelect', info.handlers.single);
      info.rootEl.removeEventListener('allSelect', info.handlers.all);
      info.rootEl.removeEventListener('processAggregatedInfo', info.handlers.proc);
      info.rootEl.removeEventListener('displayonpanel', info.handlers.display);
      info.rootEl.removeEventListener('undo', info.handlers.display);
      info.rootEl.removeEventListener('gridCellEdited', info.handlers.gridCellEdited);
    } catch (err) {
      console.log('Failed to remove event listeners from app root element:', err);
    }
  }
});
</script>

<template>
  <div class="row">
    <div
      v-for="col in preferences.widgets"
      :key="col.name"
      class="widget-list col-12"
      :class="'col-lg-' + (col.cols?.[0].width || '6')"
      :data-widget="col.name"
      :data-widget-width="col.cols?.[0].width || '6'"
    >
      <template v-if="col.cols?.[0]">
        <template v-for="(widget, index) in col.cols[0].widgets || []" :key="index">
          <div v-if="shouldShowWidget(widget[0])" class="card widget mb-3" :data-widget="widget[0]">
            <component :is="getWidgetComponent(widget[0])" :widget="widget"/>
          </div>
        </template>
      </template>
    </div>
  </div>

  <!-- Modal -->
  <div
    id="popup2"
    class="modal"
    role="dialog"
    style="z-index: 10000; overflow-y: visible"
    tabindex="-1"
  >
    <div class="modal-dialog" :style="{ width: databaseerrormodal ? '500px' : '300px' }">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title text-capitalize">
            <span v-if="!databaseerrormodal && !rowlimiterrormodal">
              {{ ttt('unsaved changes') }}
            </span>
            <span v-else-if="rowlimiterrormodal">
              {{ ttt('gantt chart rows limit') }}
            </span>
            <span v-else-if="databaseerrormodal">
              {{ ttt('database transaction failed') }}
            </span>
          </h5>
          <button
            type="button"
            class="btn-close"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>

        <div v-if="!databaseerrormodal && !rowlimiterrormodal" class="modal-body">
          <p>{{ ttt('Do you want to save your changes first?') }}</p>
        </div>

        <div v-if="!databaseerrormodal && rowlimiterrormodal" class="modal-body">
          <p>{{ ttt('The Gantt chart is limited to ' + rowlimit + ' rows.') }}</p>
          <p>{{ ttt('Please be patient, the chart may take some time to complete.') }}</p>
        </div>

        <div
          v-if="databaseerrormodal"
          class="modal-body"
          style="height: 350px; overflow: auto"
        ></div>

        <div class="modal-footer justify-content-between">
          <input
            type="submit"
            id="cancelAbutton"
            role="button"
            @click="
              modalcallback.resolve('continue');
              rowlimiterrormodal = false;
            "
            class="btn btn-primary"
            data-bs-dismiss="modal"
            :value="ttt('Continue')"
          />
          <input
            v-if="!databaseerrormodal && !rowlimiterrormodal"
            type="submit"
            id="saveAbutton"
            role="button"
            @click="modalcallback.resolve('save')"
            class="btn btn-primary"
            data-bs-dismiss="modal"
            :value="ttt('Save')"
          />
        </div>
      </div>
    </div>
  </div>
</template>
