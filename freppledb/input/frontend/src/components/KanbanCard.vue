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
import { computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@/stores/operationplansStore.js';
import { numberFormat, dateTimeFormat, adminEscape, dateFormat } from '@common/utils.js';

onMounted(() => {
  const target = document.getElementById('kanban');
});

const urlPrefix = computed(() => window.urlPrefix || '');

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const store = useOperationplansStore();

const props = defineProps({
  opplan: {
    type: Object,
    default: () => {},
  },
  opplan_index: {
    type: Number,
    default: 0,
  },
});

const mode = window.mode;
const editable = true;
const calendarmode = 'duration';

function isStart(opplan, dt) {
  const d = opplan.startdate || opplan.operationplan__startdate;
  if (!d) return false;
  else if (dt instanceof Date)
    return (
      d.getFullYear() === dt.getFullYear() &&
      d.getMonth() === dt.getMonth() &&
      d.getDate() === dt.getDate()
    );
  else return window.moment(d).isSame(dt.date, 'day');
}

function isEnd(opplan, dt) {
  let d = opplan.enddate || opplan.operationplan__enddate;
  if (!d) return false;
  // Subtract 1 microsecond to assure that an end date of 00:00:00 is seen
  // as ending on the previous day.
  if (d > (opplan.startdate || opplan.operationplan__startdate)) d = new Date(d - 1);
  if (dt instanceof Date)
    return (
      d.getFullYear() === dt.getFullYear() &&
      d.getMonth() === dt.getMonth() &&
      d.getDate() === dt.getDate()
    );
  else return window.moment(d).isSame(dt.date, 'day');
}

function isSelected(OPPreference) {
  return OPPreference === store.operationplan.reference;
}

function getStatus(op) {
  return op && op.hasOwnProperty('operationplan__status') ? op.operationplan__status : op?.status;
}

function setStatus(op, s) {
  if (!op) return;
  const field = op.hasOwnProperty('operationplan__status') ? 'operationplan__status' : 'status';
  const oldVal = op[field];
  // Use store to sync changes to OperationplanFormCard
  const ref = op.reference || op.operationplan__reference;
  store.setEditFormValues(field, s);
  store.trackOperationplanChanges(ref, field, s);
  op[field] = s;

  // Move the card between Kanban columns
  store.moveKanbanCard(ref, oldVal, s);
}

// Sync Kanban card changes to OperationplanFormCard
function changeCard(opplan, field, oldValue, newValue) {
  if (!opplan) return;
  const ref = opplan.reference || opplan.operationplan__reference;

  // Determine the old status (current status before change)
  const oldStatus = opplan.status || opplan.operationplan__status;

  // Update the kanban card display
  store.setKanbanCardValue(ref, field, oldStatus, newValue);

  // Sync to OperationplanFormCard and track for saving
  store.setEditFormValues(field, newValue);
  store.trackOperationplanChanges(ref, field, newValue);

  // If status changed, move the card between Kanban columns
  if (field === 'status' && oldStatus !== newValue) {
    store.moveKanbanCard(ref, oldStatus, newValue);
  }
}

function getStatusIcon(s) {
  switch (s) {
    case 'confirmed':
      return 'fa-lock';
    case 'approved':
      return 'fa-unlock-alt';
    case 'proposed':
      return 'fa-unlock';
    case 'completed':
      return 'fa-check';
    case 'closed':
      return 'fa-times';
    default:
      return '';
  }
}

function displayStatusIcon(op) {
  return getStatusIcon(getStatus(op));
}
</script>

// TODO The template still needs to be compiled on the fly... but if I try to do it I get the $ //
funtion redefinition error.
<template src="../../../templates/input/kanbancard.html"></template>
