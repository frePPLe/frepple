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
import {useForecastsStore} from "@/stores/forecastsStore.js";

const store = useForecastsStore();

const props = defineProps({
  panelid: {
    type: String,
    default: null
  }
});
const modelName = (props.panelid === 'I') ? 'item': (props.panelid === 'L') ? 'location': 'customer';
</script>

<template>
  <div class="card">
    <div class="card-header">
      <h5 class="card-title text-capitalize mb-0" translate=""><span class="">{{ modelName }}</span></h5>
    </div>
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-borderless table-sm table-hover">
          <tbody>
            <tr v-for="(value, key) in store[modelName]" :key="key">
              <td>{{key}}:&nbsp;</td>
              <td>{{value}}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
