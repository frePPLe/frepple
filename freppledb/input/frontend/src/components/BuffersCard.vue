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
import { useI18n } from 'vue-i18n';
import {useForecastsStore} from "@/stores/forecastsStore.js";

const { t: ttt, locale, availableLocales } = useI18n({
  useScope: 'global',  // This is crucial for reactivity
  inheritLocale: true
});

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
      <h5 class="card-title text-capitalize mb-0" translate=""><span class="">{{ ttt(modelName) }}</span></h5>
    </div>
    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-borderless table-sm table-hover">
          <tbody>
            <tr v-for="(value, key) in store[modelName]" :key="key">
              <td v-if="key === 'Name' && (locale === 'en' || locale === 'de')" style="width: 100px; white-space: nowrap;">{{ key }}:</td>
              <td v-if="key === 'Name' && (locale === 'en' || locale === 'de')">{{value}}</td>
              <td v-if="key !== 'Name'" style="width: 100px; white-space: nowrap;">{{ key }}:</td>
              <td v-if="key !== 'Name'">{{value}}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
