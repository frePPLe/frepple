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

import { debounce } from '@common/utils.js';

/**
 * Bridges Vue Pinia store with legacy jQuery/jqGrid DOM CustomEvents.
 * Centralizes the 15+ event listeners that were in OperationplanDetails.vue onMounted.
 *
 * @param {Object} store  - Pinia operationplans store
 * @param {Object} callbacks - handler callbacks from the component that need local state:
 *   { onTriggerSave, onTriggerCopy, onTriggerDelete, onAttemptModeChange,
 *     onTriggerERPExport }
 */
export function useLegacyBridge(store, callbacks = {}) {
  let registrations = [];

  function on(el, event, handler) {
    el.addEventListener(event, handler);
    registrations.push({ el, event, handler });
  }

  function attach(rootEl) {
    const getGridRowData = (id) => {
      try {
        return window.jQuery('#grid').getRowData(id);
      } catch (err) {
        console.log('Cannot get row data for id', id, ':', err);
      }
      return null;
    };

    const handleSingleSelect = (e) => {
      const detail = e?.detail || {};
      store.setMultipleGanttSelectData(null);
      if (detail.execute === 'displayInfo') {
        if (detail.selectedRows.length === 0) {
          store.undo(true);
        } else if (detail.selectedRows.length > 1) {
          handleAllSelect(e, true);
        } else if (detail.selectedRows.length < 2) {
          if (detail.status !== false && !detail.forceRefresh && detail.reference == store.operationplan.reference) {
            return;
          }
          if (store._postSaveReference && store._postSaveReference === detail.reference && !detail.forceRefresh) {
            store._postSaveReference = null;
            return;
          }
          store._postSaveReference = null;
          const refs = detail.selectedReferences || detail.selectedRows;
          store.loadOperationplans(
            [detail.reference],
            detail.status,
            refs,
            window.savedData,
            detail.forceRefresh || false,
          );
        }
      } else {
        store.undo(true);
      }
    };

    const handleAllSelect = (e, isSingleSelect) => {
      const detail = e?.detail || {};

      if (detail.status === false && !isSingleSelect) {
        if (store._postSaveReference) {
          store._postSaveReference = null;
          return;
        }
        store.undo(true);
        return;
      }
      if (detail.operationplanData && detail.colModel) {
        store.processAggregatedInfo(detail.operationplanData, detail.colModel);
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

    const applyGridCellEditDebounced = debounce(({ reference, field, value }) => {
      store.applyGridCellEdit({ reference, field, value });
      window.isDataSaved = false;
    }, 10);

    const handleDisplayOnPanel = (e) => {
      const detail = e?.detail;
      if (!detail) return;
      if (detail.field && typeof detail.value !== 'undefined') {
        try {
          applyGridCellEditDebounced({
            reference: detail.reference,
            field: detail.field,
            value: detail.value,
          });
        } catch (err) {
          console.warn('Failed to apply grid cell edit from displayonpanel event', err);
        }
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

    const handleTriggerSave = () => callbacks.onTriggerSave?.();

    const handleTriggerCopy = () => callbacks.onTriggerCopy?.();

    const handleTriggerDelete = (e) => callbacks.onTriggerDelete?.(e);

    const handleTriggerUndo = () => store.undo();

    const handleSetMode = (e) => {
      const detail = e?.detail || {};
      if (detail.mode) store.setMode(detail.mode);
    };

    const handleRefreshStatus = (e) => {
      const detail = e?.detail || {};
      if (detail.status) store.setStatus(detail.status);
    };

    const saveHeightPrefDebounced = debounce(() => {
      try {
        store.savePreferences();
      } catch (e) {
        console.warn('Failed to save row height preference', e);
      }
    }, 400);

    const handleSetRowHeight = (e) => {
      const detail = e?.detail || {};
      if (detail.source === 'dragend') {
        saveHeightPrefDebounced();
      }
    };

    const handleAttemptModeChange = (e) => {
      const detail = e?.detail || {};
      if (!detail.mode || !detail.modeChangeFunction) return;
      if (store.hasChanges) {
        callbacks.onAttemptModeChange?.(detail);
      } else {
        detail.modeChangeFunction();
      }
    };

    const handleMultipleGanttSelect = (e) => {
      const detail = e?.detail;
      if (detail) store.setMultipleGanttSelectData(detail);
      else store.undo(true);
    };

    const handleSaved = (e) => {
      const ref = e?.detail?.reference || store.operationplan?.reference;
      if (ref) {
        store._postSaveReference = ref;
        if (store.selectedOperationplans.length > 1) {
          const selectedRefs = store.selectedOperationplans.map(op =>
            typeof op === 'string' ? op : (op.id || op.reference || op.operationplan__reference)
          ).filter(Boolean);
          window.__pendingReselectionRefs = selectedRefs;
        } else {
          store.loadOperationplans([ref], true, [ref], false, true);
        }
      }
    };

    const handleERPExport = (e) => callbacks.onTriggerERPExport?.(e);

    // Register all listeners
    on(rootEl, 'singleSelect', handleSingleSelect);
    on(rootEl, 'allSelect', handleAllSelect);
    on(rootEl, 'processAggregatedInfo', handleProcessAggregatedInfo);
    on(rootEl, 'displayonpanel', handleDisplayOnPanel);
    on(rootEl, 'gridCellEdited', handleGridCellEdited);
    on(rootEl, 'triggerSave', handleTriggerSave);
    on(rootEl, 'triggerCopy', handleTriggerCopy);
    on(rootEl, 'triggerDelete', handleTriggerDelete);
    on(rootEl, 'triggerUndo', handleTriggerUndo);
    on(rootEl, 'setMode', handleSetMode);
    on(rootEl, 'refreshStatus', handleRefreshStatus);
    on(rootEl, 'setRowHeight', handleSetRowHeight);
    on(rootEl, 'attemptModeChange', handleAttemptModeChange);
    on(rootEl, 'multipleGanttSelect', handleMultipleGanttSelect);
    on(rootEl, 'saved', handleSaved);
    on(rootEl, 'triggerERPExport', handleERPExport);
  }

  function detach() {
    for (const { el, event, handler } of registrations) {
      el.removeEventListener(event, handler);
    }
    registrations = [];
  }

  return { attach, detach };
}
