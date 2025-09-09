<script setup>
import { useForecastsStore } from './stores/forecastsStore.js';

import {inject, onMounted} from 'vue';
import { getDjangoTemplateVariable  } from '@common/utils.js';
import ForecastSelection from "@/components/ForecastSelection.vue";

const store = useForecastsStore();
// const currentQuote = getDjangoTemplateVariable('vueCurrentQuoteName', {reactive: true});

const globalVar = inject('getURLprefix');

onMounted(() => {
  // document.getElementById('app').addEventListener('external', (e) => {
  //   console.log("Receiving message from django", e);
  //   if (e.detail.execute == "displayInfo") {
  //     store.quote.name = e.detail.name;
  //     store.infoQuote();
  //   }
  // });
});

</script>

<template>
  <main>
    <div id="controller">
      <div class="row mb-3">
        <ForecastSelection />
      </div>
    </div>
  </main>
</template>
