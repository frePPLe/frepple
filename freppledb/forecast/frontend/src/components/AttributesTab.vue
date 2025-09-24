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
import AttributesCard from "@/components/AttributesCard.vue";
import {computed} from "vue";

const store = useForecastsStore();

const currentSequence = computed(() =>  store.currentSequence);

</script>

<template>
  <div class="attributes-tab row">
    <div class="col-sm-4" v-for="panel in currentSequence" :key="panel">
      <div>
        <AttributesCard v-if="panel" :panelid="panel" />
      </div>
    </div>
  </div>
</template>
