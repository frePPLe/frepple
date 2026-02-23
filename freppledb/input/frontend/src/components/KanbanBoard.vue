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
import {computed, onMounted, toRaw, ref} from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@/stores/operationplansStore.js';
import KanbanCard from '@/components/KanbanCard.vue';
import { Operationplan } from '@/models/operationplan.js';

onMounted(async () => {
  // const target = document.getElementById('kanban');
  // console.log('KanbanBoard mounted');
  // console.log('Target element #kanban:', target);
  // console.log('Store mode:', store.mode);
  // console.log('Is kanban mode:', store.isKanbanMode);
  // console.log('Window mode:', window.mode);
  // console.log('Preferences mode:', window.preferences?.mode);
  window.setHeights();
  try {
    await store.loadKanbanData().then(() => window.setHeights());
  } catch (error) {
    console.error('Failed to load kanban data:', error);
  }
});

// const urlPrefix = computed(() => window.url_prefix || '');
const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const store = useOperationplansStore();

const kanbancolumns = computed(() => store.kanbancolumns);
const visibleKanbancolumns = computed(() => {
  const result = kanbancolumns.value.filter(col => !hiddenColumns.value.includes(col));
  window.preferences.columns = result;
  store.setPreferences(window.reportkey, window.preferences);
  return result;
});

const hiddenColumns = ref([]);

const kanbanoperationplans = computed(() => {
  const result = {};
  kanbancolumns.value.forEach((col) => {
    const tmp = store.kanbanoperationplans[col];
    if (tmp && tmp.rows) {
      for (const x of tmp.rows) {
        x.type = x.operationplan__type || x.type || "PO";
        if (Object.prototype.hasOwnProperty.call(x, "enddate"))
          x.enddate = new Date(x.enddate);
        if (Object.prototype.hasOwnProperty.call(x, "operationplan__enddate"))
          x.operationplan__enddate = new Date(x.operationplan__enddate);
        if (Object.prototype.hasOwnProperty.call(x, "startdate"))
          x.startdate = new Date(x.startdate);
        if (Object.prototype.hasOwnProperty.call(x, "operationplan__startdate"))
          x.operationplan__startdate = new Date(x.operationplan__startdate);
        if (Object.prototype.hasOwnProperty.call(x, "quantity"))
          x.quantity = parseFloat(x.quantity);
        if (Object.prototype.hasOwnProperty.call(x, "operationplan__quantity"))
          x.operationplan__quantity = parseFloat(x.operationplan__quantity);
        if (Object.prototype.hasOwnProperty.call(x, "quantity_completed"))
          x.quantity_completed = parseFloat(x.quantity_completed);
        if (Object.prototype.hasOwnProperty.call(x, "operationplan__quantity_completed"))
          x.operationplan__quantity_completed = parseFloat(x.operationplan__quantity_completed);
        if (Object.prototype.hasOwnProperty.call(x, "operationplan__status"))
          x.status = x.operationplan__status;
        if (Object.prototype.hasOwnProperty.call(x, "operationplan__origin"))
          x.origin = x.operationplan__origin;
        [x.color, x.inventory_status] = formatInventoryStatus(x);
      }
    }
    result[col] = tmp;
  })
  return result;
});

// console.log(78, 'kanbanoperationplans:', toRaw(kanbanoperationplans));

function hideColumn(col) {
  hiddenColumns.value.push(col);
}

function getHeight(gutter) {
  window.setHeights();
}

function formatInventoryStatus(opplan) {
  if (opplan.color === undefined || opplan.color === '')
    return [undefined, ""];
  const thenumber = parseInt(opplan.color);

  if (opplan.inventory_item || opplan.leadtime) {
    if (!isNaN(thenumber)) {
      if (thenumber >= 100 && thenumber < 999999)
        return ["rgba(0,128,0,0.5)", Math.round(opplan.computed_color) + "%"];
      else if (thenumber === 0)
        return ["rgba(255,0,0,0.5)", Math.round(opplan.computed_color) + "%"];
      else if (thenumber === 999999)
        return [undefined, ""];
      else
        return ["rgba(255," + Math.round(thenumber / 100 * 255) + ",0,0.5)", Math.round(opplan.computed_color) + "%"];
    }
  } else {
    let thedelay = Math.round(parseInt(opplan.delay) / 8640) / 10;
    if (isNaN(thedelay))
      thedelay = Math.round(parseInt(opplan.operationplan__delay) / 8640) / 10;
    if (parseInt(opplan.criticality) === 999 || parseInt(opplan.operationplan__criticality) === 999)
      return [undefined, ""];
    else if (thedelay < 0)
      return ["rgba(0,128,0,0.5)", (-thedelay) + ' ' + ttt("days early")];
    else if (thedelay === 0)
      return ["rgba(0,128,0,0.5)", ttt("on time")];
    else if (thedelay > 0) {
      if (thenumber > 100 || thenumber < 0)
        return ["rgba(255,0,0,0.5)", thedelay + ' ' + ttt("days late")];
      else
        return ["rgba(255," + Math.round(thenumber / 100 * 255) + ",0,0.5)", thedelay + ' ' + ttt("days late")];
    }
  }
  return [undefined, ""];
}

function selectCard(opplan) {
  if (store.operationplan.reference && store.operationplan.reference == opplan.reference && opplan.selected) return;
  if (store.operationplan.operationplan__reference && store.operationplan.operationplan__reference == opplan.reference && opplan.selected) return;
  opplan.selected = true;
  store.loadOperationplans([opplan.reference], true, [opplan.reference], true);
  // store.displayInfo(opplan);
  // angular.element(document).find("#delete_selected, #gridactions").prop("disabled", false);
}


</script>

<template>
  <Teleport to="#kanban" v-if="store.mode === 'kanban'">
      <div class="row">
        <div v-for="col in visibleKanbancolumns" :key="col" :data-column="col" class="col gy-3">
          <div class="card kanbancolumn" :class="{ 'hidden': hiddenColumns.includes(col) }">
            <div draggable="true" class="card-header">
              <div class="dropdown float-end">
                <a
                  class="dropdown-toggle"
                  style="cursor: pointer"
                  data-bs-toggle="dropdown"
                  aria-haspopup="true"
                  aria-expanded="true"
                  ><i class="fa fa-ellipsis-h"></i
                ></a>
                <ul class="dropdown-menu dropdown-menu-right" style="min-width: 0">
                  <li>
                    <a class="dropdown-item text-capitalize" @click="hideColumn(col)">
                      {{ ttt('hide') }}
                    </a>
                  </li>
                </ul>
              </div>
              <h3 class="card-title text-capitalize">
                {{ col }}&nbsp;&nbsp;
                <span class="badge">{{ kanbanoperationplans[col]?.records }}
                  <span
                    style="font-size: 65%"
                    v-if="kanbanoperationplans[col]?.records > kanbanoperationplans[col]?.rows.length"
                    >{{ kanbanoperationplans[col]?.rows.length }} {{ ttt('shown') }}</span
                  >
                </span>
              </h3>
            </div>
            <div
              class="card-body column-body d-none"
              style="overflow-y: auto;"
            >
              <template v-if="kanbanoperationplans[col]">
                <div
                  class="card-kanban"
                  v-for="(opplan,index) in kanbanoperationplans[col].rows"
                  :key=opplan
                  :data-index="index"
                  @click="selectCard(opplan)"
                >
                <KanbanCard :opplan="opplan" :opplan_index="index"/>
              </div>
            </template>
            </div>
          </div>
        </div>
      </div>
  </Teleport>
</template>
