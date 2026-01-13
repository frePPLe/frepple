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
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from "@/stores/operationplansStore.js";
import { numberFormat } from "@common/utils.js";

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true
});

const store = useOperationplansStore();

const operationplan = computed(() => store.operationplan || {});
const rawInventory = computed(() => operationplan.value.inventoryreport || []);

// const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const rowLabels = [
  ttt('start inventory'),
  ttt('safety stock'),
  ttt('total consumed'),
  ttt('consumed proposed'),
  ttt('consumed confirmed'),
  ttt('total produced'),
  ttt('produced proposed'),
  ttt('produced confirmed'),
  ttt('end inventory')
];

const inventoryreport = computed(() => {
  return (rawInventory.value || []).map((inv, colIndex) => {
    // inv is an array where:
    // inv[0] = label
    // inv[1] = start date
    // inv[2] = end date
    // inv[3] = italic flag (truthy)
    // inv.slice(4) => row values (0..8)
    const values = Array.isArray(inv) ? inv.slice(4).map(v => (v === null || v === undefined) ? '' : v) : [];

    const first = values[0] ?? 0;
    const second = values[1] ?? 0;
    let isRed = false;
    if (first < second || first < 0) isRed = true;

    let gradientBackground = false;
    let gradient_idx = null;
    if (isRed) {
      gradient_idx = 0;
      gradientBackground = true;
    } else if (values[0] >= values[1] || values[1] === 0) {
      gradientBackground = false;
    } else {
      gradient_idx = Math.round((values[0] / values[1]) * 165);
      gradientBackground = true;
    }

    const style = gradientBackground ? `background: linear-gradient(white 0%, rgba(255,${gradient_idx},0,0.2) 40%, rgba(255,${gradient_idx},0,0.2) 60%, white 100%);` : 'background: var(--bs-card-bg);';

    const title = `${inv[1] ? inv[1] : ''} - ${inv[2] ? inv[2] : ''}`;

    return {
      label: inv[0] || '',
      italic: !!inv[3],
      title: title,
      values: values,
      style,
      isRed
    };
  });
});

function formatCell(val, rIdx) {
  if (val === '' || val === null || val === undefined) return '';
  const numeric = Number(val);
  // in the original directive: if not first or last column and value == 0 => blank
  if ((rIdx !== 0 && rIdx !== 8) && numeric === 0) return '';
  return numberFormat(numeric);
}
</script>

<template>
  <div>
    <div
        class="card-header d-flex align-items-center"
        data-bs-toggle="collapse"
        data-bs-target="#widget_inventorydata"
        aria-expanded="false"
        aria-controls="widget_inventorydata"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('inventory') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div class="card-body collapse" :class="isCollapsed ? '' : 'show'" id="widget_inventorydata">
      <div  id="inventory_table" class="table-responsive">
        <table class="table table-sm table-hover table-borderless">
          <colgroup>
            <col />
            <template v-for="(col, idx) in inventoryreport" :key="idx">
              <col :id="`col${idx}`" :style="col.style" />
            </template>
          </colgroup>
          <thead class="text-nowrap">
            <tr class="text-center">
              <td style="position: sticky; left: 0px; background:var(--bs-card-bg)"></td>
              <template v-for="(col, idx) in inventoryreport" :key="idx">
                <td data-bs-toggle="tooltip" data-bs-placement="top" data-bs-custom-class="custom-tooltip" :data-bs-title="col.title" style="background: var(--bs-card-bg);">
                  <span v-if="col.italic" class="text-capitalize">{{ col.label }}</span>
                  <b v-else class="text-capitalize">{{ col.label }}</b>
                </td>
              </template>
            </tr>
          </thead>
          <tbody>
            <template v-for="(rowLabel, rIdx) in rowLabels" :key="rIdx">
              <tr>
                <td style="position: sticky; left: 0px; background:var(--bs-card-bg)"><span class="text-capitalize text-nowrap">{{ rowLabel }}</span></td>
                <template v-for="(col, cIdx) in inventoryreport" :key="cIdx">
                  <td class="text-center" :style="(col.isRed && rIdx===0) ? 'color: red; font-weight: bold;' : ''">
                    {{ formatCell(col.values?.[rIdx], rIdx) }}
                  </td>
                </template>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
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