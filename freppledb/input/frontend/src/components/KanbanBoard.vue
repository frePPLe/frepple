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
import {computed, onMounted, ref, nextTick} from "vue";
import { useI18n } from "vue-i18n";
import { useOperationplansStore } from "@/stores/operationplansStore.js";
import KanbanCard from "@/components/KanbanCard.vue";

const sortableInstances = new WeakMap();

const { t: ttt } = useI18n({
  useScope: "global",
  inheritLocale: true,
});

const store = useOperationplansStore();

onMounted(async () => {
  window.setHeights();
  try {
    await store.loadKanbanData();
    await nextTick();
    window.setHeights();

    if (typeof window.Sortable !== 'undefined') {
      const columnBodies = document.querySelectorAll('.column-body');
      columnBodies.forEach((el) => {
        // Destroy previous instance if we created one earlier
        const prev = sortableInstances.get(el);
        if (prev && typeof prev.destroy === 'function') {
          try { prev.destroy(); } catch (_) {}
        }

        const inst = window.Sortable.create(el, {
          group: 'kanban',
          draggable: '.card-kanban',
          ghostClass: 'sortable-ghost',
          dragClass: 'sortable-drag',
          animation: 150,
          onEnd: (evt) => {
            const reference = evt.item
              ?.querySelector('[data-reference]')
              ?.getAttribute('data-reference');
            const oldStatus = evt.from.getAttribute('data-column');
            const newStatus = evt.item.parentElement.getAttribute('data-column');
            if (!reference || !newStatus || !oldStatus) return;

            // Mark data as unsaved for legacy UI buttons
            window.isDataSaved = false;

            // Track change for save
            store.trackOperationplanChanges(reference, 'status', newStatus);

            if (newStatus !== oldStatus) {
              const oldIndex = evt.oldIndex;      // use Sortable’s index
              const newIndex = evt.newIndex;// Find the card by reference instead of using oldIndex
              const rows = store.kanbanoperationplans[oldStatus].rows;
              const cardIndex = rows.findIndex(row => row.reference == reference);
              if (cardIndex === -1) {
                console.error('Card not found in source column:', reference);
                return;
              }
              const cardData = rows.splice(cardIndex, 1)[0];
              // Keep both fields in sync if present
              cardData.status = newStatus;
              if (Object.prototype.hasOwnProperty.call(cardData, 'operationplan__status')) {
                cardData.operationplan__status = newStatus;
              }
              cardData.dirty = true;

              // If the current operationplan is the one being moved, update it
              // if (store.operationplan.reference === reference || store.operationplan.operationplan__reference === reference) {
              store.setKanbanStatus(oldStatus, oldIndex, newStatus, newIndex, reference);
              // }

              if (!store.kanbanoperationplans[newStatus]) {
                store.kanbanoperationplans[newStatus] = { rows: [], records: 0 };
              }
              store.kanbanoperationplans[newStatus].rows.splice(newIndex, 0, cardData);

              // Update counters
              store.kanbanoperationplans[oldStatus].records--;
              store.kanbanoperationplans[newStatus].records++;
            } else {
              // Reorder inside same column
              const rows = store.kanbanoperationplans[oldStatus].rows;
              const [moved] = rows.splice(evt.oldIndex, 1);
              rows.splice(evt.newIndex, 0, moved);
            }
          },
        });

        sortableInstances.set(el, inst);
      });

      const columnsContainer = document.querySelector('#kanban .kanban-columns');
      if (columnsContainer) {
        const prevCol = sortableInstances.get(columnsContainer);
        if (prevCol && typeof prevCol.destroy === 'function') {
          try { prevCol.destroy(); } catch (_) {}
        }

        const instCols = window.Sortable.create(columnsContainer, {
          animation: 150,
          draggable: '.kanban-col',        // direct children of the row
          handle: '.card-header',          // drag columns by their header
          ghostClass: 'sortable-ghost',
          dragClass: 'sortable-drag',
          onEnd: (evt) => {
            if (evt.oldIndex === evt.newIndex) return;

            // Reorder only the visible columns (those rendered in the v-for)
            const visible = [...visibleKanbancolumns.value];
            const [moved] = visible.splice(evt.oldIndex, 1);
            visible.splice(evt.newIndex, 0, moved);

            // Rebuild full list: visible first, then any hidden columns (keep their order)
            const hidden = store.kanbancolumns.filter(
              (c) => hiddenColumns.value.includes(c) && !visible.includes(c)
            );
            store.kanbancolumns = [...visible, ...hidden];

            // Persist preference: component already stores only the visible order
            window.preferences.columns = visible;
            store.setPreferences(window.reportkey, window.preferences);
          },
        });

        sortableInstances.set(columnsContainer, instCols);
      }
    }
  } catch (error) {
    console.error('Failed to load kanban data:', error);
  }
});

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

function hideColumn(col) {
  hiddenColumns.value.push(col);
}

function formatInventoryStatus(opplan) {
  if (opplan.color === undefined || opplan.color === "")
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
      return ["rgba(0,128,0,0.5)", (-thedelay) + " " + ttt("days early")];
    else if (thedelay === 0)
      return ["rgba(0,128,0,0.5)", ttt("on time")];
    else if (thedelay > 0) {
      if (thenumber > 100 || thenumber < 0)
        return ["rgba(255,0,0,0.5)", thedelay + " " + ttt("days late")];
      else
        return ["rgba(255," + Math.round(thenumber / 100 * 255) + ",0,0.5)", thedelay + " " + ttt("days late")];
    }
  }
  return [undefined, ""];
}

function selectCard(opplan) {
  if (store.operationplan.reference && store.operationplan.reference == opplan.reference && opplan.selected) return;
  if (store.operationplan.operationplan__reference && store.operationplan.operationplan__reference == opplan.reference && opplan.selected) return;
  opplan.selected = true;
  store.loadOperationplans([opplan.reference], true, [opplan.reference], true);
}
</script>

<template>
  <Teleport to="#kanban" v-if="store.mode === 'kanban'">
    <div class="row kanban-columns"> <!-- added kanban-columns -->
      <div
        v-for="col in visibleKanbancolumns"
        :key="col"
        :data-column="col"
        class="col gy-3 kanban-col"
      >
        <div class="card kanbancolumn" :class="{ 'hidden': hiddenColumns.includes(col) }">
          <div draggable="true" class="card-header"> <!-- used as Sortable handle -->
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
                    {{ ttt("hide") }}
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
                    >{{ kanbanoperationplans[col]?.rows.length }} {{ ttt("shown") }}</span
                    >
                  </span>
            </h3>
          </div>
          <div
            class="card-body column-body d-none"
            style="overflow-y: auto;"
            :data-column="col"
          >
            <template v-if="kanbanoperationplans[col]">
              <div
                class="card-kanban"
                v-for="(opplan, index) in kanbanoperationplans[col].rows"
                :key="opplan.reference || opplan.id"
                :data-index="index"
                @click="selectCard(opplan)"
              >
                <KanbanCard :opplan="opplan" :opplan_index="index" />
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

