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
import { computed, ref, onMounted, onUnmounted } from 'vue';
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
  if (store.hasChanges) {
    store.saveOperationplanChanges()
      .catch(error => {
        console.error('Failed to save operation plan:', error);
        // Show error notification to user
        store.error = {
          title: 'Save Failed',
          showError: true,
          message: 'There was an error saving your changes.',
          details: error.message || 'Unknown error',
          type: 'error'
        };
      });
  }
}

// Enhanced undo method
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

  // Special handling for certain widgets
  return widgetName === 'operationplan' ||
      widgetName === 'operationdemandpegging' ||
      (widgetConditions[widgetName] && widgetConditions[widgetName]());
}

onMounted(() => {
  if (!store.operationplan) {
    store.loadOperationplans(1391);
  }
});

onUnmounted(() => {
  store.resetTemporaryState();
});

</script>

<template>
  <div class="row">
    <div
        v-for="col in preferences.widgets"
        :key="col.name"
        class="widget-list col-12"
        :class="`col-lg-${store.numberOfCols}`"
        :data-widget="col.name"
        :data-widget-width="col.cols?.[0]?.width"
    >
      <div v-for="(widget, index) in col.cols?.[0]?.widgets || []" :key="index">
        <div
            v-if="shouldShowWidget(widget[0])"
            class="card widget mb-3"
            :data-widget="widget[0]"
        >
          <component
              :is="getWidgetComponent(widget[0])"
              :operationplan="store.operationplan"
              :is-loading="store.loading"
              :error="store.error"
          />
        </div>
      </div>
    </div>
  </div>

  <!-- Modal -->
  <div
      id="popup2"
      class="modal"
      role="dialog"
      style="z-index: 10000; overflow-y: visible"
      tabindex="-1"
  >
    <div class="modal-dialog" :style="{ width: databaseerrormodal ? '500px' : '300px' }">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title text-capitalize">
            <span v-if="!databaseerrormodal && !rowlimiterrormodal">
              {{ ttt('unsaved changes') }}
            </span>
            <span v-else-if="rowlimiterrormodal">
              {{ ttt('gantt chart rows limit') }}
            </span>
            <span v-else-if="databaseerrormodal">
              {{ ttt('database transaction failed') }}
            </span>
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>

        <div v-if="!databaseerrormodal && !rowlimiterrormodal" class="modal-body">
          <p>{{ ttt('Do you want to save your changes first?') }}</p>
        </div>

        <div v-if="!databaseerrormodal && rowlimiterrormodal" class="modal-body">
          <p>{{ ttt('The Gantt chart is limited to ' + rowlimit + ' rows.') }}</p>
          <p>{{ ttt('Please be patient, the chart may take some time to complete.') }}</p>
        </div>

        <div
            v-if="databaseerrormodal"
            class="modal-body"
            style="height: 350px; overflow: auto;"
        ></div>

        <div class="modal-footer justify-content-between">
          <input
              type="submit"
              id="cancelAbutton"
              role="button"
              @click="modalcallback.resolve('continue'); rowlimiterrormodal = false;"
              class="btn btn-primary"
              data-bs-dismiss="modal"
              :value="ttt('Continue')"
          />
          <input
              v-if="!databaseerrormodal && !rowlimiterrormodal"
              type="submit"
              id="saveAbutton"
              role="button"
              @click="modalcallback.resolve('save')"
              class="btn btn-primary"
              data-bs-dismiss="modal"
              :value="ttt('Save')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.widget-list {
  padding: 0.5rem;
}

.widget {
  transition: all 0.3s ease;
}
</style>