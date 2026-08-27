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

import { toRaw } from 'vue';
import { appConfig } from '@input/config.js';
import { operationplanService } from '@input/services/operationplanService.js';
import { dateToISO } from '@common/utils.js';

/**
 * Encapsulates save strategy: auto-save on planning board, manual save elsewhere.
 * @param {Object} store - the Pinia operationplans store
 */
export function useOperationplanSave(store) {

  function collectPayload() {
    const changes = [];
    for (const [key, value] of Object.entries(store.operationplanChanges)) {
      value.id = key;
      changes.push(toRaw({ ...value, id: key }));
    }
    return changes;
  }

  function formatChanges(changes) {
    return changes.map((x) => {
      const c = { ...x };
      delete c.end;
      delete c.start;
      if (c.startdate) c.startdate = dateToISO(c.startdate);
      if (c.enddate) c.enddate = dateToISO(c.enddate);
      if (c.operationplan__startdate) c.operationplan__startdate = dateToISO(c.operationplan__startdate);
      if (c.operationplan__enddate) c.operationplan__enddate = dateToISO(c.operationplan__enddate);
      return c;
    });
  }

  /** Auto-save batch changes to engine (planning board only) */
  async function saveBatchChanges() {
    const changes = collectPayload();
    if (changes.length === 0) return false;
    const resolveConstraints =
      window.preferences && window.preferences.resolveConstraints !== undefined
        ? window.preferences.resolveConstraints
        : 1;
    if (appConfig.isPlanningBoard && resolveConstraints) {
      await operationplanService.postToEngine({
        resolveConstraints: resolveConstraints === 1,
        propagateFwd: !changes.some(
          (change) => 'end' in change || 'enddate' in change || 'operationplan__enddate' in change
        ),
        operationplans: formatChanges(changes),
      });
    } else {
      await operationplanService.postToEngine(formatChanges(changes));
    }
    store.operationplanChanges = {};
    window.operationplanChanges = {};
    const rootEl = document.getElementById('app');
    const savedRef =
      store.operationplan?.reference || store.operationplan?.operationplan__reference;

    // For multi-select mode, the panel re-aggregation happens via the
    // 'opplan-form-changed' -> planningStore.refreshData() -> 'reaggregateSelection'

    if (rootEl && savedRef) {
      rootEl.dispatchEvent(new CustomEvent('saved', { detail: { reference: savedRef } }));
    }
    return true;
  }

  /** Manual save triggered by Save button (table/kanban) */
  async function savePendingChanges() {
    const raw = collectPayload();
    if (!raw || raw.length === 0) return;

    if (appConfig.isPlanningBoard) {
      await operationplanService.postToEngine(raw);
      store.undo();
    } else {
      const formatted = formatChanges(raw);
      try {
        await operationplanService.postOperationplanDetails(formatted);
        store.undo();
      } catch (e) {
        store.setError({
          title: 'Save failed',
          message: e.message || 'Unknown error',
          type: 'error',
        });
      }
    }
  }

  return { saveBatchChanges, savePendingChanges };
}
