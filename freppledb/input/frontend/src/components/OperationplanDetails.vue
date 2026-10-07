/*
 * Copyright (C) 2025 by frePPLe bv
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE
 */

<script setup lang="js">
import { computed, ref, nextTick, onMounted, onUnmounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@input/stores/operationplansStore.js';
import OperationplanFormCard from '@input/components/OperationplanFormCard.vue';
import InventoryGraphCard from '@input/components/InventoryGraphCard.vue';
import InventoryDataCard from '@input/components/InventoryDataCard.vue';
import ProblemsCard from '@input/components/ProblemsCard.vue';
import ResourcesCard from '@input/components/ResourcesCard.vue';
import BuffersCard from '@input/components/BuffersCard.vue';
import DemandPeggingCard from '@input/components/DemandPeggingCard.vue';
import NetworkStatusCard from '@input/components/NetworkStatusCard.vue';
import DownstreamCard from '@input/components/DownstreamCard.vue';
import UpstreamCard from '@input/components/UpstreamCard.vue';
import SupplyInformationCard from '@input/components/SupplyInformationCard.vue';
import MultipleOperationplansCard from '@input/components/MultipleOperationplansCard.vue';
import KanbanBoard from '@input/components/KanbanBoard.vue';
import InfoDialog from '@common/components/InfoDialog.vue';
import ErrorDialog from '@common/components/ErrorDialog.vue';
import { useLegacyBridge } from '@input/composables/useLegacyBridge.js';
import { getPreference, setPreferences } from '@input/services/preferences.js';

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const emit = defineEmits(['opplan-form-changed', 'resource-changed']);

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
    await $.ajax({
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

const confirmDelete = async () => {
  const sel = deleteSelectedItems.value;
  const url = deleteUrl.value;
  try {
    await $.ajax({
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

// Bumping the version changes every column's key, so Vue discards the rendered panel and mounts
// it again rather than trying to move nodes Sortable already moved.
const widgetsVersion = ref(0);

const collapsedState = ref({});

const defaultWidgets = () => [
  {
    name: 'column1',
    cols: [
      { width: 6, widgets: [['operationplan', { collapsed: false }], ['inventorygraph', { collapsed: false }]] },
    ],
  },
  {
    name: 'column2',
    cols: [
      {
        width: 6,
        widgets: [
          ['multipleGanttOperationplans', { collapsed: false }],
          ['supplyposition', { collapsed: false }],
          ['inventorydata', { collapsed: false }],
          ['operationproblems', { collapsed: false }],
          ['operationresources', { collapsed: false }],
          ['operationflowplans', { collapsed: false }],
          ['operationdemandpegging', { collapsed: false }],
        ],
      },
    ],
  },
  {
    name: 'column3',
    cols: [
      {
        width: 12,
        widgets: [
          ['networkstatus', { collapsed: false }],
          ['downstreamoperationplans', { collapsed: false }],
          ['upstreamoperationplans', { collapsed: false }],
        ],
      },
    ],
  },
];

const buildWidgets = (saved, collapsed) => {
  const source = (saved && saved.length > 0) ? saved : defaultWidgets();
  const result = source.map((col) => ({
    ...col,
    cols: col.cols.map((row) => ({
      ...row,
      widgets: row.widgets.map(([name, cfg]) => [
        name,
        { ...cfg, collapsed: collapsed[name] ?? cfg.collapsed ?? false },
      ]),
    })),
  }));

  return result;
};

const displayWidgets = computed(() => {
  void widgetsVersion.value;
  return buildWidgets(getPreference('widgets'), collapsedState.value);
});

const isKanbanMode = computed(() => store.isKanbanMode);

const unsavedChangesModal = ref(false);
const showExportDialog = ref(false);
const showExportErrorDialog = ref(false);
const exportDialogError = ref('');
const exporting = computed(() => store.exporting);

let pendingModeChange = null;

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
      ['#actions1', '#actions2', '#copy_selected', '#delete_selected'].forEach((s) => {
        const el = jQuery(s);
        if (el.length) el.prop('disabled', !hasVisible);
      });
    }
  },
  { deep: true }
);

// Pre-fetch loadplans for multi-select so shouldShowWidget can decide accurately
watch(
  () => store.selectedOperationplans,
  (selectedOps) => {
    if (selectedOps?.length > 1) {
      store.fetchMultiSelectLoadplans(selectedOps);
    }
  },
  { immediate: true }
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
    multipleGanttOperationplans: MultipleOperationplansCard,
  };
  return componentMap[widgetName] || null;
}

function handleOpplanFormChanged(detail) {
  emit('opplan-form-changed', detail);
}

function handleResourceChanged(detail) {
  emit('resource-changed', detail);
}

function shouldShowWidget(widgetName) {
  if (widgetName === 'multipleGanttOperationplans') {
    return store.multipleGanttSelectData !== null;
  }
  if (widgetName === 'operationresources') {
    if (store.operationplan?.loadplans?.length > 0) return true;
    if (store.selectedOperationplans?.length > 0) {
      const msl = store.multiSelectLoadplans;
      if (msl && Object.keys(msl).length > 0) {
        return Object.values(msl).some(lp => lp.length > 0);
      }
      if (store.selectedOperationplans.some(op => {
        if (typeof op === 'string') return false;
        return Array.isArray(op.loadplans) && op.loadplans.length > 0;
      })) return true;
    }
  }
  if (!store.operationplan || store.operationplan.id === '-1') return false;

  const widgetConditions = {
    operationplan: () => true,
    inventorygraph: () => store.operationplan.inventoryreport !== undefined,
    inventorydata: () => store.operationplan.inventoryreport !== undefined,
    operationproblems: () =>
      store.operationplan.problems !== undefined || store.operationplan.info !== undefined,
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

const confirmERPExport = async () => {
  exportDialogError.value = '';
  await store.erpExport();
  if (store.exportError) {
    if (store.exportError === 'No response from server') {
      exportDialogError.value = ttt('No response from server');
    } else if (store.exportError === 'No records with status proposed, approved or confirmed') {
      exportDialogError.value = ttt('No records with status proposed, approved or confirmed');
    } else if (store.exportError.startsWith('Server error: ')) {
      exportDialogError.value = ttt('Server error: ') + store.exportError.split(': ')[1];
    } else if (store.exportError === 'Export failed: Unexpected response format from server') {
      exportDialogError.value = ttt('Export failed: Unexpected response format from server');
    } else if (store.exportError === 'Export failed: Unknown error') {
      exportDialogError.value = ttt('Export failed: Unknown error');
    } else {
      exportDialogError.value = store.exportError;
    }
    store.exportError = null;
    showExportDialog.value = false;
    showExportErrorDialog.value = true;
  } else {
    showExportDialog.value = false;
  }
};

// Widget reordering.
//
// Sortable moves the DOM itself, which Vue never observes, so after a drop the
// rendered tree no longer matches the layout. Left to patch against that
// mismatch, Vue mounts the widget into its new column and never takes it out of
// the old one - leaving two copies of it.
//
// So a drop does two things: store the layout Sortable produced, then bump
// widgetsVersion. The version is part of every column's key below, so the bump
// makes Vue throw the whole panel away and rebuild it from the stored layout
// rather than diff it. That leaves the DOM and the vdom in agreement, which is
// what lets an ordinary later re-render - a collapse toggle, say - patch
// correctly instead of duplicating.
function widgetLayoutWithState(base) {
  const collapsed = collapsedState.value || {};
  return (base || []).map((col) => ({
    ...col,
    cols: (col.cols || []).map((row) => ({
      ...row,
      widgets: (row.widgets || []).map(([name, cfg]) => [
        name,
        { ...(cfg || {}), collapsed: collapsed[name] ?? (cfg || {}).collapsed ?? false },
      ]),
    })),
  }));
}

function widgetLayout() {
  return widgetLayoutWithState(getPreference('widgets') || defaultWidgets());
}

// The layout with the DOM's widget order applied, for right after a drag.
//
// Only the rendered widgets can be reordered and only they appear in
// getConfig(), so anything not on screen is appended to the column the document
// already had it in. That is what keeps a drag from dropping it.
function widgetLayoutFromDom() {
  const stored = getPreference('widgets') || [];
  if (typeof widget === 'undefined' || typeof widget.getConfig !== 'function') {
    return widgetLayout();
  }
  const live = widget.getConfig();
  if (!live || !live.length) return widgetLayout();

  const byName = {};
  for (const col of stored) {
    for (const [name, cfg] of col.cols?.[0]?.widgets || []) byName[name] = cfg;
  }
  const rendered = new Set();
  for (const col of live) {
    for (const [name] of col.cols?.[0]?.widgets || []) rendered.add(name);
  }

  return widgetLayoutWithState(
    live.map((col) => {
      const widgets = (col.cols?.[0]?.widgets || [])
        .filter(([name]) => byName[name])
        .map(([name]) => [name, byName[name]]);
      const original = stored.find((c) => c.name === col.name);
      for (const [name, cfg] of original?.cols?.[0]?.widgets || []) {
        if (!rendered.has(name)) widgets.push([name, cfg]);
      }
      return { ...col, cols: [{ ...(col.cols?.[0] || {}), widgets }] };
    })
  );
}

const widgetSortables = new WeakMap();

function onWidgetDragEnd(evt) {
  try {
    const next = evt && widgetLayoutFromDom();
    if (!next) return;
    setPreferences({ widgets: next });
    widgetsVersion.value++;
    // The bump above replaces every .widget-list node, orphaning the
    // Sortable instances bound to the old nodes. Re-attach to the fresh
    // nodes once Vue has re-rendered, or the next drag is impossible.
    nextTick(() => {
      try {
        initWidgetDrag();
      } catch (err) {
        console.warn('Failed to re-init widgets after reorder', err);
      }
    });
  } catch (err) {
    console.warn('Failed to persist widget reorder', err);
  }
}

// Owns the Sortable instances for the widget columns. Mirrors the kanban
// board: destroy before create, so repeated calls (mount, favorite restore)
// cannot stack handlers on the same column.
function initWidgetDrag() {
  if (typeof window.Sortable === 'undefined') return;
  document.querySelectorAll('.widget-list').forEach((el) => {
    const prev = widgetSortables.get(el);
    if (prev && typeof prev.destroy === 'function') {
      try {
        prev.destroy();
      } catch {
        /* best effort: a stale instance is harmless, a missing one is not fatal */
      }
    }
    try {
      widgetSortables.set(
        el,
        window.Sortable.create(el, {
          group: 'widgets',
          draggable: '.widget',
          handle: '.widget-handle',
          animation: 100,
          onEnd: onWidgetDragEnd
        })
      );
    } catch (err) {
      console.warn('Failed to make widget column sortable', err);
    }
  });
}

function destroyWidgetDrag() {
  if (typeof document === 'undefined') return;
  document.querySelectorAll('.widget-list').forEach((el) => {
    const inst = widgetSortables.get(el);
    if (inst && typeof inst.destroy === 'function') {
      try {
        inst.destroy();
      } catch {
        /* best effort: teardown only, never block unmount */
      }
    }
    widgetSortables.delete(el);
  });
}

// Widget DOM work for a favorite restore. Invoked by useLegacyBridge's
// single favorite-apply handler so it shares the same unsaved-changes
// gating as columns/grouping/filter.
//
// The bridge calls this *before* it persists the favorite's own patch, so the
// restored layout has to be written here rather than left to the bridge.
function applyRestoredWidgets(restored) {
  if (!restored || !restored.length) return;
  // Sync collapsed flags so buildWidgets renders them immediately
  const nextCollapsed = { ...collapsedState.value };
  for (const col of restored) {
    for (const row of col.cols || []) {
      for (const [name, cfg] of row.widgets || []) {
        if (cfg && typeof cfg.collapsed !== 'undefined') nextCollapsed[name] = cfg.collapsed;
      }
    }
  }
  collapsedState.value = nextCollapsed;
  // Write before bumping the version: displayWidgets reads the layout from the
  // document, so the restore has to be in place by the time it recomputes.
  setPreferences({ widgets: restored });
  widgetsVersion.value++;
  nextTick(() => {
    try {
      initWidgetDrag();
    } catch (err) {
      console.warn('Failed to re-init widgets after favorite restore', err);
    }
  });
}

const bridge = useLegacyBridge(store, {
  onTriggerSave: () => {
    if (store.hasChanges) {
      store.saveOperationplanChanges().catch((error) => {
        console.error('Failed to save operation plan:', error);
        store.error = {
          title: 'Save Failed',
          showError: true,
          message: 'There was an error saving your changes.',
          details: error.message || 'Unknown error',
          type: 'error',
        };
      });
    }
  },
  onTriggerCopy: () => {
    const sel = store.selectedOperationplans || [];
    if (sel.length > 0) {
      copySelectedItems.value = sel;
      copyDialogError.value = '';
      showCopyDialog.value = true;
    }
  },
  onTriggerDelete: (e) => {
    const sel = store.selectedOperationplans || [];
    const url = e?.detail?.url || window.url_prefix + '/data/operationplan/operationplan/';
    deleteUrl.value = url;
    if (sel.length === 1) {
      location.href = url + encodeURIComponent(sel[0]) + '/delete/';
    } else if (sel.length > 0) {
      deleteSelectedItems.value = sel;
      deleteDialogError.value = '';
      showDeleteDialog.value = true;
    }
  },
  onAttemptModeChange: (detail) => {
    pendingModeChange = detail.modeChangeFunction;
    unsavedChangesModal.value = true;
  },
  onTriggerERPExport: (e) => {
    const isKanban = e?.detail?.mode === 'kanban';
    showExportDialog.value = true;
    exportDialogError.value = '';
    if (isKanban) {
      const op = store.operationplan;
      if (!op || !op.reference) return;
      const status = op?.status || op?.operationplan__status;
      if (!['proposed', 'approved', 'confirmed'].includes(status)) {
        exportDialogError.value = ttt('No records with status proposed, approved or confirmed');
        store.setExporting(false);
      }
    }
  },
  onApplyFavoriteWidgets: (restored) => applyRestoredWidgets(restored),
});

const widgetToggleHandler = (e) => {
  const detail = e?.detail || {};
  if (!detail.widget) return;
  collapsedState.value = { ...collapsedState.value, [detail.widget]: detail.state };
  nextTick(() => {
    setPreferences({ widgets: widgetLayout() });
  });
};

// Django extraPreference() dispatches this synchronously and reads the
// mutated detail. Vue owns columns + widgets + filter; the template's
// extraPreference() falls back to the persisted document when Vue isn't
// mounted yet.
const collectPreferencesHandler = (e) => {
  const preferencesData = e?.detail;
  if (!preferencesData) return;
  try {
    if (store.kanbancolumns) preferencesData.columns = [...store.kanbancolumns];
  } catch (err) {
    console.warn('Failed to collect kanban columns for preferences', err);
  }
  try {
    preferencesData.widgets = widgetLayout();
  } catch (err) {
    console.warn('Failed to collect widgets for preferences', err);
  }
  try {
    // In table mode jqGrid postData is authoritative and read directly by
    // saveColumnConfiguration; only provide the filter when the grid is
    // hidden (kanban/gantt/calendar) and its postData is stale.
    if (store.mode && store.mode !== 'table') {
      const f = store.currentFilter || window.thefilter || window.initialfilter;
      if (f) preferencesData.filter = typeof f === 'string' ? f : JSON.stringify(f);
    }
  } catch (err) {
    console.warn('Failed to collect filter for preferences', err);
  }
};

onMounted(() => {
  const rootEl = document.getElementById('app') || document;
  bridge.attach(rootEl);
  appElement.value = rootEl;

  rootEl.addEventListener('widget-toggle', widgetToggleHandler);
  rootEl.addEventListener('collect-preferences', collectPreferencesHandler);

  // Persist the default layout on first load (only if not already saved).
  // No re-render: displayWidgets already falls back to defaultWidgets().
  if (!getPreference('widgets')?.length) {
    setPreferences({ widgets: defaultWidgets() });
  }

  initWidgetDrag();
});

onUnmounted(() => {
  bridge.detach();
  destroyWidgetDrag();
  if (appElement.value) {
    appElement.value.removeEventListener('widget-toggle', widgetToggleHandler);
    appElement.value.removeEventListener('collect-preferences', collectPreferencesHandler);
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

    <InfoDialog
      v-model="showExportDialog"
      :title="ttt('Export')"
      :message="ttt('Export selected records?')"
    >
      <template #actions>
        <button type="button" class="btn btn-gray" @click="showExportDialog = false">
          {{ exporting ? ttt('Close') : ttt('Cancel') }}
        </button>
        <button v-if="!exporting" type="button" class="btn btn-primary" @click="confirmERPExport">
          {{ ttt('Confirm') }}
        </button>
      </template>
    </InfoDialog>

    <InfoDialog
      v-model="store.exportSuccess"
      :title="ttt('Export successful')"
      :message="ttt('Export successful')"
      type="info"
    />

    <ErrorDialog
      v-model="showExportErrorDialog"
      :title="ttt('Export message')"
      :details="exportDialogError"
    />

    <KanbanBoard v-if="isKanbanMode" />
    <div
      v-for="col in displayWidgets"
      :key="widgetsVersion + ':' + col.name"
      class="widget-list col-12"
      :class="'col-lg-' + (col.cols?.[0].width || '6')"
      :data-widget="col.name"
      :data-widget-width="col.cols?.[0].width || '6'"
    >
      <template v-if="col.cols?.[0]">
        <template v-for="(widget, index) in col.cols[0].widgets || []" :key="widget[0] || index">
          <div v-if="shouldShowWidget(widget[0])" class="card widget mb-3" :data-widget="widget[0]">
            <component
              :is="getWidgetComponent(widget[0])"
              :widget="widget"
              @opplan-form-changed="handleOpplanFormChanged"
              @resource-changed="handleResourceChanged"
            />
          </div>
        </template>
      </template>
    </div>
  </div>
</template>
