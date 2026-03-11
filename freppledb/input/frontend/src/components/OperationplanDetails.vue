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
import { computed, ref, onMounted, onUnmounted, watch } from 'vue';
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
import KanbanBoard from '@/components/KanbanBoard.vue';
import { debounce } from '@common/utils.js';
import InfoDialog from '@common/components/InfoDialog.vue';

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const appElement = ref(null);
const store = useOperationplansStore();
const showCopyDialog = ref(false);
const copySelectedItems = ref([]);
const copyDialogError = ref('');

const showDeleteDialog = ref(false);
const deleteSelectedItems = ref([]);
const deleteDialogError = ref('');
const deleteUrl = ref('');

const confirmCopy = async () => {
  const sel = copySelectedItems.value;
  try {
    const response = await $.ajax({
      url: location.pathname,
      data: JSON.stringify([{ copy: sel }]),
      type: 'POST',
      contentType: 'application/json',
      success: function () {
        $('#delete_selected, #copy_selected, #edit_selected').prop('disabled', true);
        $('.cbox, #cb_grid.cbox').prop('checked', false);
        showCopyDialog.value = false;
        copySelectedItems.value = [];
        store.loadKanbanData();
      },
      error: function (result) {
        if (result.status == 401) {
          location.reload();
          return;
        }
        copyDialogError.value = result.responseText;
      },
    });
  } catch (err) {
    copyDialogError.value = err.message || 'Copy failed';
  }
};

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

const isKanbanMode = computed(() => store.isKanbanMode);

const unsavedChangesModal = ref(false);

let pendingModeChange = null;

const handleAttemptModeChange = (e) => {
  const detail = e?.detail || {};
  if (!detail.mode || !detail.modeChangeFunction) return;

  if (store.hasChanges) {
    pendingModeChange = detail.modeChangeFunction;
    unsavedChangesModal.value = true;
  } else {
    detail.modeChangeFunction();
  }
};

const confirmModeChange = () => {
  unsavedChangesModal.value = false;
  if (pendingModeChange) {
    store
      .saveOperationplanChanges()
      .then(() => {
        // Only proceed with mode change if save was successful (no more pending changes)
        if (!store.hasChanges) {
          pendingModeChange();
        }
        pendingModeChange = null;
      })
      .catch((err) => {
        console.error('Failed to save operation plan before mode change:', err);
        pendingModeChange = null;
      });
  }
};

const cancelModeChange = () => {
  unsavedChangesModal.value = false;
  pendingModeChange = null;
};

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

// Watch for changes and enable/disable SAVE and UNDO buttons
watch(
  () => store.hasChanges,
  (hasChanges) => {
    if (typeof jQuery !== 'undefined') {
      if (hasChanges) {
        jQuery('#save, #undo')
          .removeClass('btn-primary btn-danger')
          .addClass('btn-danger')
          .prop('disabled', false);
      } else {
        jQuery('#save, #undo')
          .removeClass('btn-danger')
          .addClass('btn-primary')
          .prop('disabled', true);
      }
    }
  }
);

// Watch for selection changes and update legacy buttons
watch(
  () => store.selectedOperationplans,
  (selected) => {
    // Update button states for kanban mode
    if (typeof jQuery !== 'undefined' && store.mode === 'kanban') {
      const hasVisible = selected && selected.length > 0;
      ['#actions1', '#actions2', '#segments1', '#copy_selected', '#delete_selected'].forEach(
        (s) => {
          const el = jQuery(s);
          if (el.length) el.prop('disabled', !hasVisible);
        }
      );
    }
  },
  { deep: true }
);

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
  const saveHeightPrefDebounced = debounce(() => {
    try {
      store.savePreferences();
    } catch (e) {
      console.warn('Failed to save row height preference', e);
    }
  }, 400);

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
        store.loadOperationplans(
          [detail.reference],
          detail.status,
          detail.selectedRows,
          window.savedData
        );
      }
    } else {
      store.undo();
    }
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
    store.saveOperationplanChanges().catch((err) => {
      console.error('Failed to save operation plan:', err);
    });
  };

  const handleTriggerCopy = async (e) => {
    const sel = store.selectedOperationplans || [];
    if (sel.length > 0) {
      copySelectedItems.value = sel;
      copyDialogError.value = '';
      showCopyDialog.value = true;
    }
  };

  const handleTriggerDelete = async (e) => {
    const sel = store.selectedOperationplans || [];
    const url = e?.detail?.url || window.url_prefix + '/data/operationplan/operationplan/';
    deleteUrl.value = url;
    if (sel.length === 1) {
      // Redirect to Django delete page for single item
      location.href = url + encodeURIComponent(sel[0]) + '/delete/';
    } else if (sel.length > 0) {
      deleteSelectedItems.value = sel;
      deleteDialogError.value = '';
      showDeleteDialog.value = true;
    }
  };

  const confirmDelete = async () => {
    const sel = deleteSelectedItems.value;
    const url = deleteUrl.value;
    try {
      const response = await $.ajax({
        url: url,
        data: JSON.stringify([{ delete: sel }]),
        type: 'POST',
        contentType: 'application/json',
        success: function () {
          $('#delete_selected, #copy_selected, #edit_selected').prop('disabled', true);
          $('.cbox, #cb_grid.cbox').prop('checked', false);
          showDeleteDialog.value = false;
          deleteSelectedItems.value = [];
          store.loadKanbanData();
        },
        error: function (result) {
          if (result.status == 401) {
            location.reload();
            return;
          }
          deleteDialogError.value = result.responseText;
        },
      });
    } catch (err) {
      console.error('Delete failed:', err);
      deleteDialogError.value = err.message || 'Delete failed';
    }
  };

  const handleTriggerUndo = (e) => {
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
    window.isDataSaved = false;
    store.applyGridCellEdit({
      reference: detail.reference,
      field: detail.field,
      value: detail.value,
    });
  };

  const handleSetMode = (e) => {
    const detail = e?.detail || {};
    if (detail.mode) {
      store.setMode(detail.mode);
    }
  };

  const handleRefreshStatus = (e) => {
    const detail = e?.detail || {};
    if (!detail.status) return;

    store.setStatus(detail.status);
  };

  const handleSetRowHeight = (e) => {
    const detail = e?.detail || {};
    const h = Math.max(150, Math.floor(Number(detail.height) || 0));
    if (!h) return;

    // Update DOM height defensively (resizable already sets it, but this keeps both paths in sync)
    // try {
    //   window.jQuery && window.jQuery('#content-main').css('height', h + 'px');
    // } catch (_) {}

    // Update store so it’s persisted and reflected in preferences
    // store.setDataRowHeight(h);

    // Persist on drag end, avoid excessive saves while dragging
    if (detail.source === 'dragend') {
      saveHeightPrefDebounced();
    }
  };

  // Attach listeners on the app root element if present, otherwise on document
  const rootEl = document.getElementById('app') || document;
  rootEl.addEventListener('singleSelect', handleSingleSelectEvent);
  rootEl.addEventListener('allSelect', handleAllSelectEvent);
  rootEl.addEventListener('processAggregatedInfo', handleProcessAggregatedInfo);
  rootEl.addEventListener('displayonpanel', handleDisplayOnPanel);
  rootEl.addEventListener('triggerSave', handleTriggerSave);
  rootEl.addEventListener('triggerCopy', handleTriggerCopy);
  rootEl.addEventListener('triggerDelete', handleTriggerDelete);
  rootEl.addEventListener('triggerUndo', handleTriggerUndo);
  rootEl.addEventListener('gridCellEdited', handleGridCellEdited);
  rootEl.addEventListener('refreshStatus', handleRefreshStatus);
  rootEl.addEventListener('hidden.bs.collapse', grid.saveColumnConfiguration);
  rootEl.addEventListener('shown.bs.collapse', grid.saveColumnConfiguration);
  rootEl.addEventListener('setMode', handleSetMode);
  rootEl.addEventListener('setRowHeight', handleSetRowHeight);
  rootEl.addEventListener('attemptModeChange', handleAttemptModeChange);

  // Save references to handlers so they can be removed on unmount
  appElement.value = {
    rootEl,
    handlers: {
      single: handleSingleSelectEvent,
      all: handleAllSelectEvent,
      proc: handleProcessAggregatedInfo,
      display: handleDisplayOnPanel,
      undo: handleUndoEvent,
      triggerSave: handleTriggerSave,
      triggerCopy: handleTriggerCopy,
      triggerDelete: handleTriggerDelete,
      triggerUndo: handleTriggerUndo,
      gridCellEdited: handleGridCellEdited,
      refreshStatus: handleRefreshStatus,
      setMode: handleSetMode,
      handleSetRowHeight: handleSetRowHeight,
      attemptModeChange: handleAttemptModeChange,
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
      info.rootEl.removeEventListener('triggerSave', info.handlers.triggerSave);
      info.rootEl.removeEventListener('triggerCopy', info.handlers.triggerCopy);
      info.rootEl.removeEventListener('triggerDelete', info.handlers.triggerDelete);
      info.rootEl.removeEventListener('triggerUndo', info.handlers.triggerUndo);
      info.rootEl.removeEventListener('gridCellEdited', info.handlers.gridCellEdited);
      info.rootEl.removeEventListener('setMode', info.handlers.setMode);
      info.rootEl.removeEventListener('setRowHeight', info.handleSetRowHeight);
      info.rootEl.removeEventListener('attemptModeChange', info.handlers.attemptModeChange);
    } catch (err) {
      console.log('Failed to remove event listeners from app root element:', err);
    }
  }
});
</script>

<template>
  <div class="row">
    <InfoDialog
      v-model="unsavedChangesModal"
      :title="ttt('Save or cancel your changes first')"
      :message="ttt('There are unsaved changes on this page.')"
      type="warning"
    >
      <template #actions>
        <button type="button" class="btn btn-primary" @click="cancelModeChange">
          {{ ttt('Return to page') }}
        </button>
        <button type="button" class="btn btn-danger" @click="confirmModeChange">
          {{ ttt('Save') }}
        </button>
      </template>
    </InfoDialog>

    <InfoDialog
      v-model="showCopyDialog"
      :title="ttt('Copy data')"
      :message="
        ttt('You are about to duplicate %s objects').replace('%s', copySelectedItems.length)
      "
      :details="copyDialogError"
      :type="copyDialogError ? 'error' : 'info'"
    >
      <template #actions>
        <button type="button" class="btn btn-gray" @click="showCopyDialog = false">
          {{ ttt('Cancel') }}
        </button>
        <button type="button" class="btn btn-primary" @click="confirmCopy">
          {{ ttt('Confirm') }}
        </button>
      </template>
    </InfoDialog>

    <InfoDialog
      v-model="showDeleteDialog"
      :title="ttt('Delete data')"
      :message="
        ttt('You are about to delete %s objects AND ALL RELATED RECORDS!').replace(
          '%s',
          deleteSelectedItems.length
        )
      "
      :details="deleteDialogError"
      :type="deleteDialogError ? 'error' : 'warning'"
    >
      <template #actions>
        <button type="button" class="btn btn-gray" @click="showDeleteDialog = false">
          {{ ttt('Cancel') }}
        </button>
        <button type="button" class="btn btn-primary" @click="confirmDelete">
          {{ ttt('Confirm') }}
        </button>
      </template>
    </InfoDialog>

    <KanbanBoard v-if="isKanbanMode" />
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
            <component :is="getWidgetComponent(widget[0])" :widget="widget" />
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
