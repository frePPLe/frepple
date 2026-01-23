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

<script setup lang="js">
import ForecastEditFormCard from "@/components/ForecastEditFormCard.vue";
import ForecastParametersCard from "@/components/ForecastParametersCard.vue";
import ForecastGraph from "@/components/ForecastGraph.vue";
// import ForecastTable from "@/components/ForecastTable.vue";

</script>

<template>
  <div>
    <ForecastGraph />
    <ForecastTable />
    <div class="row mb-3" data-ng-show="showtab=='forecast'">
      <div class="col-lg-8 col-md-12 mb-3" style="max-width: 900px">
        <ForecastEditFormCard />
      </div>
      <div class="col-md-4 col-md-12 mb-3" style="max-width: 540px">
        <ForecastParametersCard />
      </div>
    </div>
  </div>
</template>

