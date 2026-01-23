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

// const globalVar = inject('getURLprefix');

const { initTooltips } = useBootstrapTooltips({ autoDispose: false });

// Reinitialize tooltips when tab changes
watch(() => store.showTab, async () => {
  await nextTick();
  initTooltips();
});

// Reinitialize tooltips when buckets change
watch(() => store.buckets, async (newBuckets) => {
  if (newBuckets && newBuckets.length > 0) {
    await nextTick();
    initTooltips();
  }
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

