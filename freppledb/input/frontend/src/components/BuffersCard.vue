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
import { computed, ref } from "vue";
import { useI18n } from 'vue-i18n';
import { useOperationplansStore } from '@/stores/operationplansStore.js';
import OperationplanFormCard from '@/components/OperationplanFormCard.vue';
import InventoryGraphCard from '@/components/InventoryGraphCard.vue';
import InventoryDataCard from '@/components/InventoryDataCard.vue';
import ProblemsCard from '@/components/ProblemsCard.vue';
import ResourcesCard from '@/components/ResourcesCard.vue';
import BuffersCard from '@/components/BuffersCard.vue';
import DemandPeggingCard from '@/components/DemandPeggingCard.vue';
import NetworkStatusCard from '@/components/NetworkStatusCard.vue';
import DownstreamCard from '@/components/DownstreamCard.vue';
import UpstreamCard from '@/components/UpstreamCard.vue';

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true
});

const store = useOperationplansStore();

const database = computed(() => window.database);
const preferences = computed(() => window.preferences || {});

const databaseerrormodal = ref(false);
const rowlimiterrormodal = ref(false);
const modalcallback = ref({ resolve: () => {} });

function save() {
  if (store.hasChanges) store.saveOperationplanChanges();
}

function undo() {
  if (store.hasChanges) {
    store.undo();
  }
}

function getWidgetComponent(widgetName) {
  const componentMap = {
    'operationplan': OperationplanFormCard,
    'inventorygraph': InventoryGraphCard,
    'inventorydata': InventoryDataCard,
    'operationproblems': ProblemsCard,
    'operationresources': ResourcesCard,
    'operationflowplans': BuffersCard,
    'operationdemandpegging': DemandPeggingCard,
    'networkstatus': NetworkStatusCard,
    'downstreamoperationplans': DownstreamCard,
    'upstreamoperationplans': UpstreamCard,
  };
  return componentMap[widgetName] || null;
}

function shouldShowWidget(widgetName) {
  if (!store.operationplan || store.operationplan.id === -1) return false;

  const widgetConditions = {
    'inventorygraph': () => store.operationplan.inventoryreport !== undefined,
    'inventorydata': () => store.operationplan.inventoryreport !== undefined,
    'operationproblems': () => store.operationplan.problems !== undefined || store.operationplan.info !== undefined,
    'operationresources': () => store.operationplan.loadplans !== undefined,
    'operationflowplans': () => store.operationplan.flowplans !== undefined,
    'networkstatus': () => store.operationplan.network !== undefined,
    'downstreamoperationplans': () => store.operationplan.downstreamoperationplans !== undefined,
    'upstreamoperationplans': () => store.operationplan.upstreamoperationplans !== undefined,
  };

  return widgetName === 'operationplan' ||
      widgetName === 'operationdemandpegging' ||
      (widgetConditions[widgetName] && widgetConditions[widgetName]());
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
          <td style="white-space: nowrap">{{ formatDatetime(flowplan.date) }}</td>
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
