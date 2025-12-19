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

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true
});

const store = useOperationplansStore();

const hasFlowplans = computed(() => {
  const op = store.operationplan.value;
  return op && op.flowplans && Array.isArray(op.flowplans) && op.flowplans.length > 0;
});

const flowplans = computed(() => {
  return store.operationplan.value?.flowplans || [];
});

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
            :class="{ 'border-top': isFirstProducer(index) }"
        >
          <!-- Item column - with or without alternates -->
          <td v-if="!flowplan.alternates" style="white-space: nowrap">
              <span
                  v-if="flowplan.buffer?.description"
                  :title="flowplan.buffer.description"
                  data-bs-toggle="tooltip"
              >
                {{ flowplan.buffer?.item }}
              </span>
            <span v-else>{{ flowplan.buffer?.item }}</span>
            <a
                :href="`${urlPrefix}/detail/input/item/${adminEscape(flowplan.buffer?.item)}/`"
                @click.stop
            >
              <span class="ps-2 fa fa-caret-right"></span>
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
          <td>{{ formatNumber(flowplan.quantity) }}</td>

          <!-- Onhand column -->
          <td>{{ formatNumber(flowplan.onhand) }}</td>

          <!-- Date column -->
<!--          <td style="white-space: nowrap">{{ formatDatetime(flowplan.date) }}</td>-->
          <td style="white-space: nowrap">{{ flowplan.date }}</td>
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

.border-top {
  border-top: 1px solid #dee2e6 !important;
}
</style>
