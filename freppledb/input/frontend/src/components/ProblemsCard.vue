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

const { t: ttt } = useI18n({
  useScope: 'global',
  inheritLocale: true
});

const store = useOperationplansStore();

const props = defineProps({
  widget: {
    type: Array,
    default: () => []
  }
});

const isCollapsed = computed(() => props.widget[1]?.collapsed ?? false);

const problems = computed(() => {
  return store.operationplan?.problems || [];
});

const hasProblems = computed(() => {
  return problems.value.length > 0;
});

const info = computed(() => {
  return store.operationplan?.info || '';
});

const infoLines = computed(() => {
  if (!info.value) return [];
  return info.value.split('\n').filter(line => line.trim() !== '');
});

const hasInfo = computed(() => {
  return infoLines.value.length > 0;
});

const hasProblemsOrInfo = computed(() => {
  return hasProblems.value || hasInfo.value;
});

// Save column configuration on collapse/expand
function onCollapseToggle() {
  if (typeof window.grid !== 'undefined' && window.grid.saveColumnConfiguration) {
    window.grid.saveColumnConfiguration();
  }
}

onMounted(() => {
  // Set up Bootstrap collapse listeners
  const collapseElement = document.getElementById('widget_problems');
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
        data-bs-target="#widget_problems"
        aria-expanded="false"
        aria-controls="widget_problems"
    >
      <h5 class="card-title text-capitalize fs-5 me-auto">
        {{ ttt('problems') }}
      </h5>
      <span class="fa fa-arrows align-middle w-auto widget-handle"></span>
    </div>

    <div
        id="widget_problems"
        class="card-body collapse"
        :class="{ 'show': !isCollapsed }"
    >
      <table class="table table-sm table-hover table-borderless">
        <thead>
        <tr>
          <td><b class="text-capitalize">{{ ttt('name') }}</b></td>
          <td><b class="text-capitalize">{{ ttt('start') }}</b></td>
          <td><b class="text-capitalize">{{ ttt('end') }}</b></td>
        </tr>
        </thead>
        <tbody>
        <tr v-if="!hasProblemsOrInfo">
          <td colspan="3">{{ ttt('no problems') }}</td>
        </tr>

        <!-- Display problems -->
        <tr v-for="(problem, index) in problems" :key="`problem-${index}`">
          <td>{{ problem.description }}</td>
          <td>{{ problem.start }}</td>
          <td>{{ problem.end }}</td>
        </tr>

        <!-- Display info lines -->
        <tr v-for="(infoLine, index) in infoLines" :key="`info-${index}`">
          <td colspan="3">{{ infoLine }}</td>
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