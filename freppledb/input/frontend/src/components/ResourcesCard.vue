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
import { computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from "@/stores/operationplansStore.js";
import {numberFormat} from "@common/utils.js";

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true
});

const store = useOperationplansStore();

const props = defineProps({
  widget: {
    type: Array,
    default: () => []
  },
  mode: {
    type: String,
    default: ''
  }
});

const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const loadplans = computed(() => {
  return store.operationplan?.loadplans || [];
});

const hasLoadplans = computed(() => {
  return loadplans.value.length > 0;
});

// Get URL prefix
const urlPrefix = computed(() => window.url_prefix || '');

// Admin escape function
function adminEscape(str) {
  if (typeof window.admin_escape === 'function') {
    return window.admin_escape(str);
  }
  return encodeURIComponent(str);
}

// Handle alternate resource selection
function selectAlternateResource(loadplan, newResource) {
  const currentResource = loadplan.resource.name;
  if (newResource === currentResource) return;

  // Find the first matching loadplan (in the case of duplicates)
  const loadplanIndex = loadplans.value.findIndex(lp => lp.resource.name === currentResource);
  if (loadplanIndex === -1) return;

  const targetLoadplan = loadplans.value[loadplanIndex];

  // Update the assigned resource
  targetLoadplan.resource.name = newResource;

  // Update the alternate list - swap current and new resource
  if (targetLoadplan.alternates) {
    targetLoadplan.alternates = targetLoadplan.alternates.map(alt => {
      if (alt.name === newResource) {
        return { ...alt, name: currentResource };
      }
      return alt;
    });
  }

  // Handle different modes
  if (props.mode && (props.mode.startsWith('calendar') || props.mode === 'kanban')) {
    // Update calendar or kanban card
    store.$emit?.('updateCard', 'loadplans', store.operationplan.loadplansOriginal, loadplans.value);
  } else {
    // Update the grid
    updateGrid(currentResource, newResource);
  }
}

function updateGrid(currentResource, newResource) {
  if (typeof window.jQuery === 'undefined') return;

  const $ = window.jQuery;
  const grid = $('#grid');
  if (!grid.length) return;

  const selrow = grid.jqGrid('getGridParam', 'selarrrow');
  if (!selrow || selrow.length === 0) return;

  // Find the column (either 'resources' or 'resource')
  const colModel = grid.jqGrid('getGridParam', 'colModel');
  let targetCol = colModel?.find(i => i.name === 'resources');
  if (!targetCol) {
    targetCol = colModel?.find(i => i.name === 'resource');
  }

  if (!targetCol) return;

  const cell = grid.jqGrid('getCell', selrow[0], targetCol.name);

  if (targetCol.formatter === 'detail' && cell === currentResource) {
    // Simple resource update
    grid.jqGrid("setCell", selrow[0], targetCol.name, newResource, "dirty-cell");
    grid.jqGrid("setRowData", selrow[0], false, "edited");
    markDirty();
  } else if (targetCol.formatter === 'listdetail') {
    // Multiple resources update
    const resources = loadplans.value.map(lp => [
      lp.resource.name,
      lp.quantity,
      lp.reference
    ]);
    grid.jqGrid("setCell", selrow[0], targetCol.name, resources, "dirty-cell");
    grid.jqGrid("setRowData", selrow[0], false, "edited");
    markDirty();
  }
}

function markDirty() {
  const $ = window.jQuery;
  $("#save, #undo").removeClass("btn-primary btn-danger").addClass("btn-danger").prop("disabled", false);
  $(window).off('beforeunload', window.upload?.warnUnsavedChanges);
  $(window).on('beforeunload', window.upload?.warnUnsavedChanges);
}

// Save column configuration on collapse/expand
function onCollapseToggle() {
  if (typeof window.grid !== 'undefined' && window.grid.saveColumnConfiguration) {
    window.grid.saveColumnConfiguration();
  }
}

onMounted(() => {
  // Set up Bootstrap collapse listeners
  const collapseElement = document.getElementById('widget_resources');
  if (collapseElement) {
    collapseElement.addEventListener('shown.bs.collapse', onCollapseToggle);
    collapseElement.addEventListener('hidden.bs.collapse', onCollapseToggle);
  }
});
</script>

<template>
  <div>
    <div
        class="card-header d-flex align-items-center"
        data-bs-toggle="collapse"
        data-bs-target="#widget_resources"
        aria-expanded="false"
        aria-controls="widget_resources"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('resource') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div
        id="widget_resources"
        class="card-body collapse"
        :class="{ 'show': !isCollapsed }"
    >
      <table class="table table-sm table-hover table-borderless">
        <thead>
        <tr>
          <td><b class="text-capitalize">{{ ttt('name') }}</b></td>
          <td><b class="text-capitalize">{{ ttt('quantity') }}</b></td>
        </tr>
        </thead>
        <tbody>
        <tr v-if="!hasLoadplans">
          <td colspan="2">{{ ttt('no resources') }}</td>
        </tr>

        <tr v-for="(loadplan, index) in loadplans" :key="index">
          <!-- Resource column - with or without alternates -->
          <td v-if="!loadplan.alternates">
            {{ loadplan.resource?.name }}
            <a
                :href="`${urlPrefix}/detail/input/resource/${adminEscape(loadplan.resource?.name)}/`"
                @click.stop
            >
              <span class=" fa fa-caret-right"></span>
            </a>
          </td>

          <td v-else style="white-space: nowrap">
            <div class="dropdown">
              <button
                  class="form-control w-auto dropdown-toggle"
                  data-bs-toggle="dropdown"
                  type="button"
                  style="min-width: 150px"
              >
                {{ loadplan.resource?.name }}
              </button>
              <ul class="dropdown-menu">
                <li>
                  <a
                      role="menuitem"
                      class="dropdown-item text-capitalize"
                      @click.prevent="selectAlternateResource(loadplan, loadplan.resource?.name)"
                  >
                    {{ loadplan.resource?.name }}
                  </a>
                </li>
                <li v-for="(alternate, altIndex) in loadplan.alternates" :key="altIndex">
                  <a
                      role="menuitem"
                      class="dropdown-item text-capitalize"
                      @click.prevent="selectAlternateResource(loadplan, alternate.name)"
                  >
                    {{ alternate.name }}
                  </a>
                </li>
              </ul>
            </div>
          </td>

          <!-- Quantity column -->
          <td>{{ numberFormat(loadplan.quantity) }}</td>
        </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.widget-handle {
  cursor: move;
}

.card-header {
  cursor: pointer;
}

thead tr td {
  border-bottom-width: 1px;
  border-bottom-style: solid;
  border-bottom-color: #bbb;
}
</style>