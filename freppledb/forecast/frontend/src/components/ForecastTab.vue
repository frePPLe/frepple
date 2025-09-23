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
import { useForecastsStore } from '@/stores/forecastsStore';

const store = useForecastsStore();
</script>

<template>
  <div class="forecast-tab">
    <h3>Forecast</h3>
    <div class="card">
      <div class="card-body">
        <p>forecast tab</p>
      </div>
    </div>
  </div>
</template>

