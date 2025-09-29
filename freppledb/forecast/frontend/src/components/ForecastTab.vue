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
import ForecastEditFormCard from "@/components/ForecastEditFormCard.vue";
import ForecastParametersCard from "@/components/ForecastParametersCard.vue";
import ForecastGraph from "@/components/ForecastGraph.vue";
import ForecastTable from "@/components/ForecastTable.vue";

</script>

<template>
  <div>
    <ForecastGraph />
    <ForecastTable />
    <div class="row mb-3" data-ng-show="showtab=='forecast'">
      <div class="col-lg-8 col-md-12 mb-3" style="max-width: 900px">
        <ForecastEditFormCard />
      </div>
      <div class="col-md-4 col-md-12 mb-3" style="max-width: 400px">
        <ForecastParametersCard />
      </div>
    </div>
  </div>
</template>

