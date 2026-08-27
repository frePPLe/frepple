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

import { appConfig } from '@input/config.js';
import { useOperationplanSave } from '@input/composables/useOperationplanSave.js';

const moment = window.moment;

/**
 * Orchestrates field edits, status changes, and date shifts.
 * Replaces the fat methods that were in the Pinia store.
 * @param {Object} store - the Pinia operationplans store
 */
export function useOperationplanEdit(store) {
  const { saveBatchChanges } = useOperationplanSave(store);

  function updateModel(field, value) {
    if (['status', 'operationplan__status'].includes(field)) {
      store.operationplan.status = value;
    } else if (field === 'startdate' || field === 'operationplan__startdate') {
      store.operationplan.start = value;
      store.operationplan[field] = value;
    } else if (field === 'enddate' || field === 'operationplan__enddate') {
      store.operationplan.end = value;
      store.operationplan[field] = value;
    } else if (field === 'quantity' || field === 'operationplan__quantity') {
      store.operationplan.quantity = parseFloat(value);
      store.operationplan[field] = parseFloat(value);
    } else if (field === 'quantity_completed' || field === 'operationplan__quantity_completed') {
      store.operationplan.quantity_completed = parseFloat(value);
      store.operationplan[field] = parseFloat(value);
    } else if (field === 'remark' || field === 'operationplan__remark') {
      store.operationplan.remark = value;
      store.operationplan[field] = value;
    } else {
      store.operationplan[field] = value;
    }
  }

  function syncToUI(field, value) {
    switch (store.mode) {
      case 'table':
        if (typeof window.displayongrid === 'function') {
          let rowIds = [];
          if (window.jQuery) {
            rowIds = (window.jQuery('#grid').jqGrid('getGridParam', 'selarrrow') || []).filter(Boolean);
          }
          if (rowIds.length === 0) {
            rowIds = store.selectedOperationplans.map(op =>
              typeof op === 'string' ? op : (op.id || op.reference || op.operationplan__reference)
            ).filter(Boolean);
          }
          if (rowIds.length === 0) {
            const fb = store.operationplan.reference || store.operationplan.id;
            if (fb && fb !== -1) rowIds.push(fb);
          }
          rowIds.forEach(id => window.displayongrid(id, field, value));
        }
        break;
      case 'kanban':
        store.setKanbanCardValue(
          store.operationplan.reference, field, store.operationplan.status, value
        );
        break;
    }
  }

  async function setEditFormValues(field, value) {
    syncToUI(field, value);
    store.editForm[field] = value;

    const oldStatus = store.operationplan.status;
    updateModel(field, value);

    if (['status', 'operationplan__status'].includes(field) && store.mode === 'kanban') {
      store.moveKanbanCard(store.operationplan.reference, oldStatus, value);
    }

    store.selectedOperationplans.forEach(op => {
      const ref = typeof op === 'string' ? op : (op.id || op.reference || op.operationplan__reference);
      if (ref) store.trackOperationplanChanges(ref, field, value);
    });
    if (store.selectedOperationplans.length === 0) {
      const ref = store.operationplan.reference || store.operationplan.id;
      if (ref && ref !== -1) store.trackOperationplanChanges(ref, field, value);
    }

    if (appConfig.isPlanningBoard) {
      await saveBatchChanges();
    }
  }

  async function setStatus(value) {
    if (value === 'no_action' || value === 'erp_incr_export') return false;

    store.selectedOperationplans.forEach((op) => {
      const ref = typeof op === 'string' ? op : (op.id || op.reference || op.operationplan__reference);
      const statusField = (typeof op === 'object' && Object.prototype.hasOwnProperty.call(op, 'operationplan__status'))
        ? 'operationplan__status' : 'status';
      store.trackOperationplanChanges(ref, statusField, value);
      if (typeof window.displayongrid === 'function') {
        window.displayongrid(ref, statusField, value);
      }
    });
    store.operationplan.status = value;

    store.selectedStatusCounts = {};
    store.selectedOperationplans.forEach((op) => {
      const ref = typeof op === 'string' ? op : (op.reference || op.operationplan__reference);
      const statusField = (typeof op === 'object' && Object.prototype.hasOwnProperty.call(op, 'operationplan__status'))
        ? 'operationplan__status' : 'status';
      const originalStatus = typeof op === 'string' ? undefined : op[statusField];
      const effectiveStatus = store.operationplanChanges[ref]?.[statusField] || originalStatus || 'proposed';
      if (effectiveStatus) {
        store.selectedStatusCounts[effectiveStatus] =
          (store.selectedStatusCounts[effectiveStatus] || 0) + 1;
      }
    });

    if (appConfig.isPlanningBoard) {
      return await saveBatchChanges();
    }
    return false;
  }

  async function shiftGroupDates(field, newValue) {
    if (store.selectedOperationplans.length === 0 || !newValue) return false;

    const dateField =
      field === 'startdate'
        ? (op) => op.startdate || op.operationplan__startdate || op.start
        : (op) => op.enddate || op.operationplan__enddate || op.end;

    let currentAgg = null;
    store.selectedOperationplans.forEach((op) => {
      const val = dateField(op);
      if (!val) return;
      const m = new moment(val);
      if (!m.isValid()) return;
      if (currentAgg === null) {
        currentAgg = m;
      } else if (field === 'startdate') {
        if (m.isBefore(currentAgg)) currentAgg = m;
      } else {
        if (m.isAfter(currentAgg)) currentAgg = m;
      }
    });

    if (currentAgg === null) return false;

    const newM = new moment(newValue, 'YYYY-MM-DDTHH:mm:ss');
    if (!newM.isValid()) return false;
    const delta = newM.diff(currentAgg);

    store.selectedOperationplans.forEach((op) => {
      const ref = typeof op === 'string' ? op : (op.reference || op.operationplan__reference);
      const originalDate = dateField(op);
      if (!originalDate) return;
      const origM = new moment(originalDate);
      if (!origM.isValid()) return;
      const shifted = origM.clone().add(delta, 'milliseconds');
      const shiftedStr = shifted.format('YYYY-MM-DDTHH:mm:ss');
      store.trackOperationplanChanges(ref, field, shiftedStr);
    });

    if (field === 'startdate') {
      store.operationplan.start = newValue;
      store.operationplan.startdate = newValue;
      store.operationplan.operationplan__startdate = newValue;
    } else {
      store.operationplan.end = newValue;
      store.operationplan.enddate = newValue;
      store.operationplan.operationplan__enddate = newValue;
    }

    if (appConfig.isPlanningBoard) {
      return await saveBatchChanges();
    }
    return false;
  }

  return { setEditFormValues, setStatus, shiftGroupDates };
}
