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
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@input/stores/operationplansStore.js';
import { appConfig } from '@input/config.js';
import { adminEscape, numberFormat } from '@common/utils.js';

const emit = defineEmits(['resource-changed']);

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true,
});

const store = useOperationplansStore();

const props = defineProps({
  widget: {
    type: Array,
    default: () => [],
  },
  mode: {
    type: String,
    default: '',
  },
});

const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const handleToggle = () => {
  if (props.widget?.[0]) {
    document.getElementById('app').dispatchEvent(
      new CustomEvent('widget-toggle', { detail: { widget: props.widget[0], state: !isCollapsed.value } })
    );
  }
};

const multipleOpplans = computed(() => store.selectedOperationplans.length > 1);

const multiSelectLoadplans = computed(() => store.multiSelectLoadplans);

const loadplans = computed(() => {
  if (multipleOpplans.value && store.selectedOperationplans.length > 0) {
    const resourceMap = new Map();
    store.selectedOperationplans.forEach((op) => {
      const ref = typeof op === 'string' ? op : (op.reference || op.operationplan__reference);
      const lp = multiSelectLoadplans.value?.[ref] || op.loadplans;
      if (lp) {
        lp.forEach((l) => {
          const name = l.resource?.name;
          if (!name) return;
          if (resourceMap.has(name)) {
            const existing = resourceMap.get(name);
            existing.quantity += l.quantity || 0;
            existing.references.push(l.reference || ref);
            (l.alternates || []).forEach((a) => existing.alternates.add(a.name));
          } else {
            resourceMap.set(name, {
              resource: l.resource,
              quantity: l.quantity || 0,
              references: [l.reference || ref],
              alternates: new Set((l.alternates || []).map((a) => a.name)),
            });
          }
        });
      }
    });
    return Array.from(resourceMap.values()).map((v) => ({
      resource: v.resource,
      quantity: v.quantity,
      reference: v.references.join(', '),
      alternates: Array.from(v.alternates).map((n) => ({ name: n })),
    }));
  }
  return store.operationplan?.loadplans || [];
});

const hasLoadplans = computed(() => {
  return loadplans.value.length > 0;
});

// Get URL prefix
const urlPrefix = computed(() => window.url_prefix || '');

// Handle alternate resource selection
function selectAlternateResource(loadplan, newResource) {
  const currentResource = loadplan.resource.name;
  if (newResource === currentResource) return;

  // Find the first matching loadplan (in the case of duplicates)
  const loadplanIndex = loadplans.value.findIndex((lp) => lp.resource.name === currentResource);
  if (loadplanIndex === -1) return;

  const targetLoadplan = loadplans.value[loadplanIndex];

  // Update the assigned resource
  targetLoadplan.resource.name = newResource;

  // Update the alternate list - swap current and new resource
  if (targetLoadplan.alternates) {
    targetLoadplan.alternates = targetLoadplan.alternates.map((alt) => {
      if (alt.name === newResource) {
        return { ...alt, name: currentResource };
      }
      return alt;
    });
  }

  // Handle different modes
  if (props.mode && (props.mode.startsWith('calendar') || props.mode === 'kanban')) {
    // Update calendar or kanban card
    store.$emit?.(
      'updateCard',
      'loadplans',
      store.operationplan.loadplansOriginal,
      loadplans.value
    );
  } else {
    // Update the grid
    updateGrid(currentResource, newResource);
  }
}

function updateGrid(currentResource, newResource) {
  if (typeof window.jQuery === 'undefined') return;

  const grid = window.jQuery('#grid');
  if (!grid.length) return;

  const selrow = grid.jqGrid('getGridParam', 'selarrrow');
  if (!selrow || selrow.length === 0) return;

  // Find the column (either 'resources' or 'resource')
  const colModel = grid.jqGrid('getGridParam', 'colModel');
  let targetCol = colModel?.find((i) => i.name === 'resources');
  if (!targetCol) {
    targetCol = colModel?.find((i) => i.name === 'resource');
  }

  let refCol = colModel?.find((i) => i.name === 'reference');
  if (!refCol) refCol = colModel?.find((i) => i.name === 'operationplan__reference');

  if (!targetCol || !refCol) return;

  for (const rowId of selrow) {
    const cell = grid.jqGrid('getCell', rowId, targetCol.name);
    if (targetCol.formatter === 'detail' && cell === currentResource) {
      // Simple resource update
      grid.jqGrid('setCell', rowId, targetCol.name, newResource, 'dirty-cell');
      grid.jqGrid('setRowData', rowId, false, 'edited');
      markDirty();
    } else if (targetCol.formatter === 'listdetail') {
      // Multiple resources update
      const ref = grid.jqGrid('getCell', rowId, refCol.name);
      const resources = cell.map((lp) => [lp[0] === currentResource ? newResource : lp[0], lp[1], ref]);
      grid.jqGrid('setCell', rowId, targetCol.name, resources, 'dirty-cell');
      grid.jqGrid('setRowData', rowId, false, 'edited');
      markDirty();
    }
  }
}

function markDirty() {
  window
    .jQuery('#save, #undo')
    .removeClass('btn-primary btn-danger')
    .addClass('btn-danger')
    .prop('disabled', false);
  const handler = window.upload?.warnUnsavedChanges;
  if (typeof handler === 'function') {
    window.jQuery(window).off('beforeunload', handler);
    window.jQuery(window).on('beforeunload', handler);
  }
}

</script>

<template>
  <div>
    <div
      class="card-header d-flex align-items-center"
      @click="handleToggle"
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

    <div id="widget_resources" class="card-body collapse" :class="{ show: !isCollapsed }">
      <table class="table table-sm table-hover table-borderless">
        <thead>
          <tr>
            <td>
              <b class="text-capitalize">{{ ttt('name') }}</b>
            </td>
            <td v-if="!multipleOpplans">
              <b class="text-capitalize">{{ ttt('quantity') }}</b>
            </td>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!hasLoadplans">
            <td :colspan="multipleOpplans ? 1 : 2">{{ ttt('no resources') }}</td>
          </tr>

          <tr v-for="(loadplan, index) in loadplans" :key="index">
            <!-- Resource column - with or without alternates -->
            <td v-if="!loadplan.alternates || loadplan.alternates.length === 0">
              {{ loadplan.resource?.name }}
              <a
                :href="`${urlPrefix}/detail/input/resource/${adminEscape(loadplan.resource?.name)}/`"
                @click.stop
              >
                <span class="fa fa-caret-right"></span>
              </a>
            </td>

            <td v-else style="white-space: nowrap">
              <div class="dropdown d-inline-flex align-items-center">
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
                <a
                  :href="`${urlPrefix}/detail/input/resource/${adminEscape(loadplan.resource?.name)}/`"
                  @click.stop
                >
                  <span class="fa fa-caret-right ps-1"></span>
                </a>
              </div>
            </td>

            <td v-if="!multipleOpplans">
              {{ numberFormat(loadplan.quantity || 0) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
