/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

<script setup lang="js">
import { computed } from "vue";
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@/stores/operationplansStore.js';
import { numberFormat, dateTimeFormat } from "@common/utils.js";

const urlPrefix = computed(() => window.url_prefix || '');
const adminEscape = (str) => window.admin_escape(str);

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true
});

const store = useOperationplansStore();

const hasFlowplans = computed(() => {
  const op = store.operationplan;
  return op && op.flowplans && Array.isArray(op.flowplans) && op.flowplans.length > 0;
});

const flowplans = computed(() => {
  return store.operationplan.flowplans || [];
});

// Vue version of selectAlternateItem
function selectAlternateItem(flowplan, newItem) {
  const currentItem = flowplan.buffer?.item;

  if (newItem !== currentItem) {
    // Find and update the flowplan in the store
    const operationplan = store.operationplan;
    if (operationplan && operationplan.flowplans) {
      const flowToUpdate = operationplan.flowplans.find(flow =>
          flow.buffer?.item === currentItem
      );

      if (flowToUpdate) {
        // Update the assigned item
        flowToUpdate.buffer.item = newItem;

        // Update the grid if it exists
        updateGrid(currentItem, newItem);

        // Enable save/undo buttons
        enableSaveUndoButtons();
      }
    }
  }
}

function updateGrid(currentItem, newItem) {
  // Check if grid exists (maintaining compatibility with existing jqGrid)
  const gridElement = document.querySelector("#grid");
  if (!gridElement) return;

  const grid = window.jQuery(gridElement);
  const selrow = grid.jqGrid('getGridParam', 'selarrrow');
  const colmodel = grid.jqGrid('getGridParam', 'colModel')?.find(i => i.name === "material");

  if (!colmodel || !selrow) return;

  const cell = grid.jqGrid('getCell', selrow, 'material');

  if (colmodel.formatter === 'detail' && cell === currentItem) {
    grid.jqGrid("setCell", selrow, "material", newItem, "dirty-cell");
    grid.jqGrid("setRowData", selrow, false, "edited");
  }
  else if (colmodel.formatter === 'listdetail') {
    const items = [];
    const operationplan = store.operationplan;
    if (operationplan && operationplan.flowplans) {
      operationplan.flowplans.forEach(flowplan => {
        items.push([flowplan.buffer?.item, flowplan.quantity]);
      });
    }
    grid.jqGrid("setCell", selrow, "material", items, "dirty-cell");
    grid.jqGrid("setRowData", selrow, false, "edited");
  }
}

function enableSaveUndoButtons() {
  const saveBtn = document.querySelector("#save");
  const undoBtn = document.querySelector("#undo");

  if (saveBtn) {
    saveBtn.classList.remove("btn-primary");
    saveBtn.classList.add("btn-danger");
    saveBtn.disabled = false;
  }

  if (undoBtn) {
    undoBtn.classList.remove("btn-primary");
    undoBtn.classList.add("btn-danger");
    undoBtn.disabled = false;
  }
}

</script>

<template>
  <div>
    <div
        class="card-header d-flex align-items-center"
        data-bs-toggle="collapse"
        data-bs-target="#widget_bufferspanel"
        aria-expanded="false"
        aria-controls="widget_bufferspanel"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('items') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div
        id="widget_bufferspanel"
        class="card-body collapse"
        :class="{ 'show': !isCollapsed }"
    >
      <table class="table table-sm table-hover table-borderless">
        <thead>
        <tr>
          <td><b class="text-capitalize">{{ ttt('item') }}</b></td>
          <td><b class="text-capitalize">{{ ttt('location') }}</b></td>
          <td><b class="text-capitalize">{{ ttt('quantity') }}</b></td>
          <td><b class="text-capitalize">{{ ttt('onhand') }}</b></td>
          <td><b class="text-capitalize">{{ ttt('date') }}</b></td>
        </tr>
        </thead>
        <tbody>
        <tr v-if="!hasFlowplans">
          <td colspan="5">{{ ttt('no movements') }}</td>
        </tr>

        <tr
            v-for="(flowplan, index) in flowplans"
            :key="index"
            :class="(index===0 && flowplan.quantity > 0) ? 'border-top' : ''"
        >
          <!-- Item column - with or without alternates -->
          <td v-if="!flowplan.alternates" style="white-space: nowrap">
              <span style="padding-right: 3px"
                  v-if="flowplan.buffer?.description"
                  :title="flowplan.buffer.description"
                  data-bs-toggle="tooltip"
              >
                {{ flowplan.buffer?.item }}
              </span>
            <span v-else style="padding-right: 3px">{{ flowplan.buffer?.item }}</span>
            <a
                :href="`${urlPrefix}/detail/input/item/${adminEscape(flowplan.buffer?.item)}/`"
                @click.stop
            >
              <span class="fa fa-caret-right"></span>
            </a>
          </td>

          <td v-else style="white-space: nowrap">
            <div class="dropdown">
              <button
                  class="btn btn-primary text-capitalize"
                  data-bs-toggle="dropdown"
                  type="button"
                  style="min-width: 150px"
              >
                {{ flowplan.buffer?.item }}
              </button>
              <ul class="dropdown-menu">
                <li>
                  <a
                      role="menuitem"
                      class="dropdown-item text-capitalize"
                      @click.prevent="selectAlternateItem(flowplan, flowplan.buffer?.item)"
                  >
                    {{ flowplan.buffer?.item }}
                  </a>
                </li>
                <li v-for="(alternate, altIndex) in flowplan.alternates" :key="altIndex">
                  <a
                      role="menuitem"
                      class="dropdown-item text-capitalize"
                      @click.prevent="selectAlternateItem(flowplan, alternate)"
                  >
                    {{ alternate }}
                  </a>
                </li>
              </ul>
            </div>
          </td>

          <!-- Location column -->
          <td>{{ flowplan.buffer?.location }}</td>

          <!-- Quantity column -->
          <td>{{ numberFormat(flowplan.quantity) }}</td>

          <!-- Onhand column -->
          <td>{{ numberFormat(flowplan.onhand) }}</td>

          <!-- Date column -->
          <td style="white-space: nowrap">{{ dateTimeFormat(flowplan.date) }}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>