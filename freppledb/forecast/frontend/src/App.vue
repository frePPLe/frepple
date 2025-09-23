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
import { useForecastsStore } from './stores/forecastsStore.js';

import {inject} from 'vue';
import ForecastSelection from "@/components/ForecastSelection.vue";
import ForecastDetails from "@/components/ForrecastDetails.vue";

const store = useForecastsStore();

const globalVar = inject('getURLprefix');

</script>

<template>
  <main>
    <div id="controller">
      <div class="row mb-3">
        <ForecastSelection />
      </div>
      <div class="row mb-3">
        <ForecastDetails />
      </div>
    </div>
  </main>
</template>
