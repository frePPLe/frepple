/*
* Copyright (C) 2025 by frePPLe bv
*
* All information contained herein is, and remains the property of frePPLe.
* You are allowed to use and modify the source code, as long as the software is used
* within your company.
* You are not allowed to distribute the software, either in the form of source code
* or in the form of compiled binaries.
*/

<script setup>
import { inject, computed, watch, nextTick } from "vue";
import { useForecastsStore } from './stores/forecastsStore.js';
import ForecastSelection from "@/components/ForecastSelection.vue";
import ForcastDetails from "@/components/ForcastDetails.vue";
import ErrorDialog from '@common/components/ErrorDialog.vue';
import { useBootstrapTooltips } from '@common/useBootstrapTooltips.js';

const store = useForecastsStore();

const showErrorDialog = computed({
  get: () => !!store.error && store.error.showError,
  set: (value) => {
    if (!value) {
      store.error = { showError: false, message: '', details: '', type: 'error', title: '' };
    }
  }
});

const globalVar = inject('getURLprefix');

const { initTooltips } = useBootstrapTooltips({ autoDispose: false });

// Reinitialize tooltips when tab changes
watch(() => store.showTab, async () => {
  await nextTick();
  initTooltips();
});

</script>

<template>
  <main>
    <div>
      <div class="row mb-3">
        <ForecastSelection />
      </div>
      <div class="row mb-3">
        <ForcastDetails />
      </div>
      <ErrorDialog
          v-model="showErrorDialog"
          :title="store.error?.title || 'Error'"
          :message="store.error?.message || ''"
          :details="store.error?.details || ''"
          :type="store.error?.type || 'error'"
          :show-details="!!(store.error?.details)"
      />
    </div>
  </main>
</template>

